# Prompt de implementação: retomar a validação de estratégias no Trading Lab

Você é o engenheiro responsável pela próxima etapa do Trading Lab (`D:\Trade-Initial`): Freqtrade 2026.9 em Docker, BTC/ETH/BNB spot, somente long, somente dry-run. Antes de qualquer alteração, leia `README.md`, `research/hypothesis-ledger.md`, `research/guidance.md`, `research/validation-protocol-v2.md`, `docs/harness-fase0.md` e `docs/estrategias-h011-h014.md`.

## Regras que não mudam

- Nada de trading real, chaves de API ou segredos. `user_data/config.dryrun.json` e as baselines protegidas por SHA (`tests/test_protected_files.py`) não podem ser editadas.
- Toda hipótese é registrada no ledger (`lab/registry.py`) **antes** de rodar, com regra ex-ante, parâmetros, grid completo e warm-up. Não edite uma regra depois de ver o resultado: crie um novo ID. Cada configuração do grid e cada cenário de custo conta como teste.
- A validação é lida uma única vez por hipótese, e só se a exploração passar nos 3 pares. O final test / holdout prospectivo (a partir de 2026-10-21, `lab/config/holdout.json`) não é lido: `final_test_unlocked` só o usuário altera.
- Proibido: `shift(-n)`; normalização ou `fit_transform` sobre a série inteira; `.min()`/`.max()` sem janela; `iloc[-1]` em `populate_*`; merge direto de informative (use `merge_informative_pair`); copiar código GPL ou sem licença; `custom_stake_amount`, `adjust_trade_position`, alavancagem, short.
- Não apague hipóteses, resultados, manifestos ou decisões. Código experimental de uma família nova que falhar pode ser arquivado (etapa 0.2), com ledger e motivos preservados.
- Uma etapa por vez. No fim de cada etapa: liste arquivos alterados, testes executados e resultado, problemas encontrados, e **pare aguardando aprovação**.

## Etapa 0: higiene (pré-requisito)

0.1. A árvore de trabalho tem ~126 alterações não commitadas (Fase 0, H-011..H-014, dashboard). Rode `python -m pytest tests -q`. Se passar, proponha ao usuário commits separados por tema (dashboard; H-011..H-014 + limpeza H-004/H-006; Fase 0 harness) e só commite após o "sim" dele. Não commite `dashboard-files.txt` sem perguntar.

0.2. Arquivamento sem perda de reprodutibilidade:
- Crie `user_data/strategies/_archive/` e mova para lá os arquivos das hipóteses **rejeitadas** H-005, H-007, H-008, H-010, H-011, H-012, H-013 e H-014, com seus testes movidos para `tests/archive/`. Os testes continuam rodando.
- Confirme no container que o Freqtrade **não** carrega subpastas por padrão (`list-strategies`; opção `recursive_strategy_search`). Se carregar, use outro diretório fora de `--strategy-path`.
- Adicione um status `archived` no registro (sem alterar decisões) e um `research/tools/rerun_archived.py` que copia temporariamente um arquivo arquivado para o strategy path, confere o SHA-256 gravado no manifesto e roda o backtest original. Teste: o SHA confere para todas as arquivadas.
- **Não arquive:** H-001, H-002, H-003 (baselines protegidas), H-009 (candidata ativa) e `Sma200Baseline`.

0.3. Defeitos conhecidos a resolver ou registrar:
- **H-007, lookahead `has_bias=True` só em BNB/USDT.** O código usa `shift(1)` nos canais e parece causal. Reproduza com `lookahead-analysis` isolado em BNB, leia o CSV (quais colunas e sinais divergem) e cruze com o salto de preço de 23,5% nos dados da BNB. Registre a causa (dado, analisador ou código) em `research/` e no ledger. Não reabra a hipótese.
- **Warm-up insuficiente para indicadores recursivos:** H-003 (RSI com 200 candles) e H-012/H-014 (EMA200/ATR com 800) falharam no `recursive-analysis`. Adicione ao `lab/strategy_check.py` um aviso: se a estratégia usa EMA/RSI/ATR (Wilder) de período P, `startup_candle_count >= 3*P` (e no mínimo 400). Teste com as estratégias existentes.

## Etapa 1: filtro de regime (`regime_filter.py`) e imports controlados

1.1. `lab/strategy_check.py`: além das raízes atuais, permita **somente** imports de uma lista explícita `ALLOWED_LOCAL_MODULES = {"regime_filter"}` (módulo irmão em `user_data/strategies/`). Qualquer outro import local continua proibido. Testes: aceita `from regime_filter import ...`; rejeita `import os`, `from lab import ...` e qualquer outro módulo local. O próprio `regime_filter.py` passa pelo mesmo screen de AST.

1.2. `user_data/strategies/regime_filter.py`: funções puras e causais, sem estado, sobre colunas já mescladas do informative diário.
- `vol_regime(close_1d, window, ratio)`: vol realizada (desvio de log-retornos diários em `window` dias) **<=** `ratio` x mediana rolling de 365 dias da própria vol.
- `trend_regime(close_1d, sma_days)`: fechamento diário fechado > SMA(sma_days).
- `regime_on(...)`: AND dos dois, com flags para ligar cada um.
- Máximo 3 parâmetros. Valores ex-ante: `window=30`, `ratio=1.5`, `sma_days=200`.
- Confirme no container que o Freqtrade importa o módulo irmão (smoke backtest).

1.3. Testes: `lab/causality.py` (invariância a prefixo e corrupção do futuro) para cada função e para uma estratégia que a usa; um teste de que o regime calculado no 1h via `merge_informative_pair` usa só dias fechados (reaproveite `research/tools/check_informative.py`).

1.4. Ablation (o filtro precisa provar benefício; não é vantajoso por definição):
- Rode `Sma200Baseline` e a `DonchianBreakoutBaseline` em 4h/1d com e sem `vol_regime` (o `trend_regime` já é a própria SMA200), via `research/tools/baseline_cycles.py`, custos `base` e `base_2x`, só nas janelas IS (exploração).
- Critério de benefício, fixado antes: Sharpe anualizado maior **e** max drawdown menor no IS com custo `base_2x`, em pelo menos 2 dos 3 pares, sem piorar o Sharpe em mais de 2 dos 5 ciclos.
- Se não houver benefício, o filtro fica disponível mas **desligado por padrão**, e o resultado é registrado.

## Etapa 2: estratégias TSMOM, Donchian (TF superior) e Pullback MTF

Para cada uma, nesta ordem:

1. Registre a família no ledger com o grid **inteiro** pré-declarado e o N total de configurações (usado no DSR):
   - TSMOM: N ∈ {30, 60, 90, 120, 180}.
   - Donchian 4h: (N, M) ∈ {20, 40, 55, 100} × {10, 20, 30}, com M < N.
   - Pullback: no máximo 3 parâmetros e no máximo 12 configurações.
   - Cada família com e sem regime.
2. Implemente uma classe por arquivo `<Família>_H<NNN>_v1.py`, com sinais do timeframe superior via `merge_informative_pair`, execução em 1h e parâmetros como constantes de módulo. Configurações do grid são geradas como cópias temporárias, como em `research/tools/sensitivity.py`, nunca editando o arquivo registrado.
3. Testes por estratégia: regra em dados sintéticos, invariância a prefixo, corrupção do futuro e contrato.
4. Smoke backtest no container; `lookahead-analysis` e `recursive-analysis` em BTC, ETH e BNB.
5. **Exploração (IS)** para todo o grid, custos `base` e `base_2x`, por ciclo e por janela. Calcule:
   - PBO (CSCV, 16 fatias) sobre a matriz de retornos diários do grid;
   - DSR da melhor configuração com N = tamanho do grid;
   - platô: Sharpe das vizinhas >= 70% da melhor;
   - IC por bootstrap de blocos do retorno médio por trade, com a ressalva "< 100 trades";
   - walk-forward ancorado (`lab/walkforward.py`) dentro do IS.
6. Critério para seguir à validação, fixado antes de rodar:
   - DSR >= 0,95;
   - PBO <= 0,5;
   - platô presente;
   - Sharpe acima do buy-and-hold **e** da `Sma200Baseline` com custo `base_2x` no IS;
   - >= 30 trades por par;
   - gates de `lab/config/gates.json`.
   Se falhar, a família é rejeitada e o código arquivado.
7. **Donchian:** compare com a H-009 (rompimento de 7 dias + regime 30d/90d): correlação dos retornos diários, sobreposição de períodos em posição (% de horas em comum) e ganho incremental de uma carteira 50/50 sobre a H-009 sozinha. Se a correlação for > 0,7 e não houver ganho, registre como redundante.
8. Só então, uma única leitura da validação (OOS) para a **configuração escolhida no IS**, sem reescolher depois.

Pare após cada família, não após as três.

## Etapa 3: RSI(2) de Connors (pesquisa)

- Entrada: SMA(200) diária fechada < fechamento, e RSI(2) em 1h < limiar ∈ {5, 10}.
- Saída: fechamento > SMA(5) ou RSI(2) > 70.
- Stop de 8% e saída por tempo de 48 candles, ambos obrigatórios.
- Mesmo processo da etapa 2. Reporte explicitamente o comportamento em mar/2020, mai/2021 e nov/2022.

## Etapa 4: relatório comparativo

Gere `docs/relatorio-comparativo.md` com:
- IS / OOS / últimos 12 meses (rotulado como semi-contaminado), custos 1x e 2x, por ciclo;
- comparação com buy-and-hold e `Sma200Baseline`;
- Monte Carlo (bootstrap de trades), DSR, PBO, número total de configurações testadas e número de trades com IC.

Conclua com quais estratégias têm evidência OOS e quais são descartadas. Não declare sucesso sem evidência OOS. As candidatas sobreviventes vão para dry-run congelado (hash registrado); o holdout prospectivo só é avaliado a partir de 2027-04-21 e com >= 30 trades fechados.

## Critérios de pronto, por etapa

Testes verdes (`python -m pytest tests -q`), `lookahead` e `recursive` limpos para todo código novo, ledger e `research/registry-dump.sql` atualizados, entrada em `research/command-log.md`, e nenhuma leitura de validação ou holdout fora das regras acima.
