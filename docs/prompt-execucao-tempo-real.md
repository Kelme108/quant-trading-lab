# Prompt de implementação: camada de execução em tempo real (MT5 para WIN/WDO + cripto do laboratório)

Você é o engenheiro responsável por construir a camada de execução em tempo real do Trading Lab (`D:\Trade-Initial`). O objetivo final do usuário é operar **mini índice (WIN)** e **mini dólar (WDO)** na B3 via **MetaTrader 5**, e também os ativos que o laboratório já pesquisa (BTC/ETH/BNB spot via Freqtrade). Este prompt cobre a infraestrutura, a conta demo e o forward test. **Dinheiro real fica para uma etapa final que só o usuário libera.**

Antes de qualquer alteração, leia `README.md`, `docs/checklist-operacao-real.md`, `docs/config.production.example.json`, `research/hypothesis-ledger.md`, `research/validation-protocol-v2.md`, `research/guidance.md`, `research/engine-crosscheck-2026-11-02.md`, `lab/costs.py`, `lab/guard.py`, `lab/config/*.json` e `tests/test_protected_files.py`.

## Situação de partida (não omita isto nos relatórios)

- **Nenhuma estratégia do laboratório tem evidência fora da amostra.** H-001..H-016 foram rejeitadas ou ficaram inconclusivas. A H-009 é "candidata na exploração", e a validação dela ainda não foi lida. O holdout prospectivo só pode ser avaliado a partir de 2027-04-21.
- **Nenhuma estratégia foi pesquisada em WIN/WDO.** As regras de cripto (spot, só long, 1h, 24/7) não se transferem para futuros B3 (pregão com horário, leilões, vencimentos, ajuste diário, venda a descoberto natural, custo por contrato). Uma estratégia para B3 precisa de hipótese própria registrada no ledger e do mesmo protocolo de validação.
- Por isso, o que se constrói agora é: (1) o motor de execução, (2) o adaptador MT5 operando em **conta demo**, (3) a trilha de pesquisa para B3 e (4) o forward test. Não é um bot para ganhar dinheiro amanhã.

## Regras que não mudam

- **Modo padrão: simulado/demo.** Uma ordem real só sai se **todas** as condições abaixo forem verdadeiras. O código precisa checar cada uma e recusar a ordem, com log, se qualquer uma falhar:
  1. `LIVE_MODE=real` na variável de ambiente;
  2. `live/config/live.json` com `"allow_real": true` e o SHA-256 desse arquivo registrado em `live/config/live.sha256` pelo usuário;
  3. `mt5.account_info().trade_mode` indica conta real e o número da conta é igual a `LIVE_ACCOUNT_ID`;
  4. a estratégia ativa tem hash congelado e decisão de aprovação no registry.
  Em conta demo, a condição 3 inverte: o código recusa a execução se a conta for real e o modo não for `real`.
- Credenciais (login, senha e servidor MT5, chaves de exchange) só em variáveis de ambiente ou num `.env` listado no `.gitignore`. Antes do primeiro commit, confirme que nada sensível entra no git. Nunca imprima credenciais em log.
- Não edite arquivos protegidos (`tests/test_protected_files.py`, `lab/guard.py`), nem `user_data/config.dryrun.json`, nem `lab/config/gates.json`, `splits.json` ou `holdout.json`. A camada nova fica em `live/` e `tests/live/`.
- As regras do laboratório continuam valendo: hipótese registrada antes de rodar, grid pré-declarado, nada de `shift(-n)` nem normalização sobre a série inteira, e validação lida uma vez. Não ajuste uma estratégia olhando o resultado do forward test.
- **A mesma função de sinal roda no backtest e no tempo real.** Proibido reimplementar a regra no caminho live. Um teste de paridade é obrigatório (etapa 3).
- Uma etapa por vez. No fim de cada etapa: liste os arquivos alterados, os testes executados e o resultado, os problemas encontrados e as decisões pendentes do usuário, e **pare aguardando aprovação**. Commits só depois do "sim" do usuário.

## Etapa 0: decisões e ambiente (pare antes de escrever código)

0.1. Pergunte ao usuário e registre as respostas em `live/DECISIONS.md`:
- Corretora e servidor MT5 (precisa oferecer MT5 para B3 e conta demo/simulador de B3; o tipo de conta deve ser netting).
- Capital hipotético da demo, **perda diária máxima** (R$), perda semanal máxima, número máximo de contratos por ativo e número máximo de operações por dia.
- Só day-trade (zerar antes do fim do pregão), ou permitir posição overnight. Recomende só day-trade no início.
- Se vendido (short) é permitido em WIN/WDO. Hoje o laboratório proíbe short. Liberar isso para B3 é decisão do usuário e precisa ficar registrada no ledger como regra nova, não como exceção silenciosa.
- Canal de alerta (Telegram ou equivalente).

0.2. Ambiente:
- O pacote Python `MetaTrader5` só funciona no **Windows**, com o terminal MT5 aberto e logado no mesmo host. Ele não roda no Docker/WSL onde está o Freqtrade. Os dois processos ficam separados e só se integram por arquivos e bancos.
- O Python do host é 3.14, e `MetaTrader5` não está instalado. Verifique no PyPI quais versões de Python têm wheel. Se 3.14 não tiver, crie um venv dedicado (`live/.venv`, fora do git) com a versão mais recente suportada. Fixe as versões em `live/requirements.txt`.
- Registre no relatório: versão do terminal MT5, build, corretora, servidor e tipo de conta (demo).

## Etapa 1: núcleo de execução independente de corretora (sem rede)

Estrutura sugerida (ajuste se houver motivo, e explique):

```text
live/
  core/
    models.py       # Bar, Signal, OrderRequest, Fill, Position, AccountState (dataclasses imutáveis)
    broker.py       # Protocol Broker: bars(), symbol_spec(), positions(), account(), send(), cancel(), close_all()
    risk.py         # RiskManager: veta ou aprova cada OrderRequest e devolve o motivo
    engine.py       # loop: candle fechado -> sinal -> risco -> ordem -> journal
    journal.py      # SQLite append-only: cada sinal, veto, ordem, fill, erro, com hash da estratégia
    clock.py        # calendário/horário de pregão B3 e 24/7 cripto; relógio injetável para testes
    killswitch.py   # arquivo-sentinela + comando: zera posições, cancela ordens, para o loop
  brokers/
    paper.py        # PaperBroker determinístico (fills no próximo open, slippage em ticks, custo por contrato)
  config/live.example.json
tests/live/
```

Requisitos:
- **Só candles fechados.** O engine nunca decide com o candle em formação. Teste: dado o mesmo histórico, o sinal não muda se o candle atual for corrompido.
- **RiskManager** com vetos testados um a um: fora do horário permitido; janela de não-entrada perto da abertura/leilão e do fechamento; perda diária ou semanal atingida (trava até o próximo dia ou semana, não volta sozinho no mesmo dia); limite de contratos; limite de operações por dia; ordem sem stop; volume fora de `volume_min`/`volume_step`; preço fora do tick; kill switch ativo; dados velhos (último candle mais antigo que 2× o timeframe); divergência entre a posição no journal e na corretora.
- **Zeragem do day-trade:** fecha a posição N minutos antes do horário-limite da corretora (configurável), com teste.
- **Reconciliação ao iniciar:** lê posições e ordens abertas na corretora, compara com o journal e, se divergir, entra em modo seguro (não abre posição nova e alerta). Teste: o processo morre com posição aberta e reinicia.
- **Idempotência:** cada ordem leva um id do cliente (no MT5, `magic` + `comment`). Reenvio após timeout não duplica a posição.
- Testes com `PaperBroker` e relógio falso cobrindo um pregão inteiro, sem rede.

## Etapa 2: adaptador MT5 em conta demo

2.1. `live/brokers/mt5.py`, implementando `Broker`:
- `initialize`/`login` com credenciais do ambiente; `shutdown` garantido. Reconecta com backoff e alerta após N falhas.
- **Especificações do contrato lidas do servidor, nunca fixas no código:** `symbol_info()` → `trade_tick_size`, `trade_tick_value`, `volume_min`, `volume_step`, `filling_mode`, `trade_mode`, sessões. Registre os valores lidos no relatório e compare com a especificação publicada pela B3.
- Ordens: `order_check` antes de cada `order_send`; `TRADE_ACTION_DEAL` para mercado; stop-loss no servidor (SL da posição ou ordem stop pendente), **nunca só no processo Python**; `type_filling` escolhido a partir de `filling_mode` do símbolo; trate todos os `retcode` (requote, rejeição, mercado fechado, sem margem) com log e teste via mock.
- Dados: `copy_rates_from_pos`/`copy_rates_range` para M1/M5/M15/H1. Meça e registre quanto histórico a corretora entrega por timeframe (costuma ser limitado).

2.2. **Vencimentos e símbolos:**
- WIN vence nos meses pares e WDO todo mês. Confirme as regras e datas no calendário oficial da B3, sem hard-code de memória. Implemente `live/b3/contracts.py`, que resolve o contrato vigente (ex.: `WINZ26`, `WDOX26`) e a data de rolagem, com testes de borda (feriado, véspera de vencimento).
- Série contínua para pesquisa (`WIN$N`/`WDO$N` ou o nome usado pela corretora; descubra via `symbols_get`) versus contrato vigente para operar. Documente como a série contínua é ajustada, porque isso afeta o backtest.
- Proibido carregar posição através do vencimento.

2.3. Dados para pesquisa: `live/b3/download.py` grava OHLCV em `user_data/data/b3/<símbolo>-<tf>.feather` com manifesto (corretora, servidor, data da coleta, hash) e roda as checagens de `lab/dataquality.py` (lacunas fora do pregão não contam como lacuna, então adapte o calendário).

2.4. Smoke test na **demo**, com o usuário acompanhando: conectar, ler a conta (confirmar que é demo), enviar 1 contrato WIN com stop, conferir a posição, fechar e conferir no journal. Repetir para WDO. Depois, os testes de falha: matar o processo com posição aberta e reiniciar; desligar a rede; ordem rejeitada por volume inválido; kill switch com posição aberta.

## Etapa 3: trilha de pesquisa para B3

3.1. **Custos B3 em `lab/costs.py`, sem mexer nos cenários de cripto:** custo por contrato e por lado (emolumentos e taxa de registro B3, corretagem da corretora escolhida) e slippage em **ticks**, com cenários `base`/`base_2x`/`stress`. Os valores vêm da tabela vigente da B3 e da corretora, com fonte e data registradas. Se não houver número medido, marque como hipótese.

3.2. **Backtester de futuros:** o runner do laboratório é Freqtrade, que não cobre B3. Avalie reaproveitar o simulador independente usado em `research/engine-crosscheck-2026-11-02.md`. O backtester precisa respeitar sessão, horário de zeragem, multiplicador por ponto, tick, custo por contrato e fill no próximo open.
- **Teste de paridade obrigatório:** reproduza um dia de candles no `engine` com `PaperBroker` e no backtester. As ordens e os fills precisam ser idênticos.

3.3. Defina, com aprovação do usuário, splits e holdout próprios para B3 (`lab/config/splits_b3.json`) **antes** de rodar qualquer hipótese. A área de "dados visíveis na proposta" do ledger precisa dizer que é B3.

3.4. Primeira hipótese B3, registrada no ledger antes de rodar: uma baseline simples e textual, com parâmetros ex-ante (ex.: rompimento da faixa de abertura ou tendência intradiária com filtro de horário). Mesmo protocolo: exploração em WIN e WDO, gates, DSR/PBO se houver grid, validação lida uma vez. Se falhar, registre e pare. **Não tente variantes até "dar certo".**

## Etapa 4: forward test (sem dinheiro real)

- **B3:** só uma estratégia que passou na validação da etapa 3, com hash congelado, roda na conta demo por no mínimo 4 a 8 semanas (defina o mínimo de operações com o usuário antes). Relatório semanal: operações da demo vs. replay do backtest no mesmo período, slippage medido em ticks, rejeições e incidentes. Ajustes de regra viram hipótese nova; o forward test recomeça do zero.
- **Cripto:** Freqtrade em `trade` dry-run (o motor já existe; não reescreva) com a estratégia que tiver evidência OOS. Hoje nenhuma tem: a H-009 só entra se passar na leitura única da validação, seguindo o [prompt-proxima-etapa.md](prompt-proxima-etapa.md). Cumpra os itens C e D de `docs/checklist-operacao-real.md`.
- **Painel único:** um leitor somente leitura que junta o journal do `live/` e o banco do Freqtrade (PnL, posições, vetos, alertas) e integra ao dashboard existente (`lab/dashboard.py`). Sem botões que enviem ordem.

## Etapa 5: piloto real (bloqueada; só o usuário libera)

Pré-requisitos, todos com evidência registrada: estratégia com validação OOS aprovada e forward demo concluído dentro do esperado; itens A–D do checklist marcados; perda máxima do piloto e critério de parada escritos antes; servidor/VPS Windows 24/5 para o MT5 (não o PC pessoal), com relógio sincronizado, logs com rotação e backup do journal. Piloto com **1 contrato** e escala só por regra escrita. Registre que a tributação de day-trade em futuros (alíquota e IRRF) é responsabilidade do usuário; o sistema só exporta o histórico de operações. Nenhum código desta etapa é escrito antes da autorização explícita.

## Critérios de pronto, por etapa

`python -m pytest tests -q` verde (o laboratório existente não pode quebrar) e `tests/live` verde; nenhuma credencial no git (`git grep` por login/senha/servidor no relatório); kill switch e reconciliação testados; entrada em `research/command-log.md`; ledger e `research/registry-dump.sql` atualizados quando houver hipótese nova; relatório da etapa com decisões pendentes do usuário em lista.
