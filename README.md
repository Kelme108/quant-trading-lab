# Quant Trading Lab

Laboratório **reproduzível e auditável** para pesquisar, validar e (futuramente) executar estratégias de trading quantitativo. Combina um motor de backtest ([Freqtrade](https://www.freqtrade.io/)), um pipeline automatizado de hipóteses com *gates* estatísticos rígidos, um painel de monitoramento local e uma camada de execução em tempo real (MetaTrader 5) em modo demo.

> ## ⚠️ Estado de segurança
> - O projeto opera **somente em `dry_run` / conta demo**. Não há ordens reais, chaves privadas, margem ou alavancagem no repositório.
> - **Nenhuma estratégia do laboratório tem evidência fora da amostra.** Das 19 hipóteses registradas, nenhuma foi aprovada para operação real; uma é "candidata na exploração" e ainda não passou pela validação.
> - O laboratório **nunca aprova operação real**. Isso é uma decisão exclusiva do usuário.
> - Isto não é recomendação de investimento. Resultados negativos são esperados e preservados de propósito.

> **Segundo cérebro do projeto:** o mapa completo (estado atual, decisões do dono, regras invioláveis, robôs, como reconstruir o ambiente) está em [docs/cerebro/](docs/cerebro/00-LEIA-PRIMEIRO.md), um cofre Markdown que abre no Obsidian. O [CLAUDE.md](CLAUDE.md) aponta para ele. Comece por lá, sobretudo a linha atual de WIN/WDO; o resto deste README descreve principalmente a linha cripto original.
>
> **Clonou agora?** Clone sempre com `git clone -c core.autocrlf=true https://github.com/Kelme108/quant-trading-lab.git`. Os hashes das regras dependem do fim de linha CRLF.
> - **Windows:** `ops\windows\install.cmd` instala o `.venv` com os testes, o `live\.venv` com MetaTrader5 e o MT5 da Clear e o normal.
> - **Linux:** `ops/linux/install.sh` instala o mesmo, com o MT5 no Wine. Guia em [docs/instalacao-linux.md](docs/instalacao-linux.md).
> - **Diagnóstico:** `python bootstrap.py --check` mostra o que falta.
> - Regras de colaboração: [CONTRIBUTING.md](CONTRIBUTING.md). A linha cripto tem manual próprio: [docs/migracao-linux.md](docs/migracao-linux.md).

---

## Sumário

- [Filosofia](#filosofia)
- [Arquitetura](#arquitetura)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Requisitos](#requisitos)
- [Início rápido](#início-rápido)
- [Laboratório multiagente (`lab/`)](#laboratório-multiagente-lab)
- [Gates de validação](#gates-de-validação)
- [Painel de monitoramento](#painel-de-monitoramento)
- [Camada de execução em tempo real (`live/`)](#camada-de-execução-em-tempo-real-live)
- [Skills `trader-*`](#skills-trader-)
- [Testes](#testes)
- [Segurança e boas práticas](#segurança-e-boas-práticas)
- [Documentação](#documentação)
- [Status e resultados](#status-e-resultados)
- [Fontes](#fontes)

---

## Filosofia

O maior risco em pesquisa quantitativa não é falta de ideias, e sim **enganar-se com o próprio backtest**. O laboratório existe para tornar isso difícil:

1. **Hipótese registrada antes de rodar** (regra *ex-ante*, dados visíveis, número de testes anteriores).
2. **Divisão cronológica** em exploração, validação e teste final trancado.
3. **Penalidade por múltiplos testes**: a barra de lucro sobe a cada variante testada na mesma família.
4. **Custos conservadores** em quatro cenários (otimista, base, conservador, estresse).
5. **Determinismo**: o fluxo e toda aprovação são código Python; agentes de IA só escrevem texto (propostas, código, revisões) e **nunca decidem**.
6. **Resultado negativo é resultado.** Hipóteses rejeitadas ficam no registro.

## Arquitetura

```text
        ┌─────────────┐   ideias    ┌──────────────┐  proposta   ┌─────────────┐
        │  scout      │───────────▶ │   research   │───────────▶ │  developer  │
        │ (agente)    │             │   (agente)   │             │  (agente)   │
        └─────────────┘             └──────────────┘             └──────┬──────┘
                                                                        │ estratégia + teste
                                                                        ▼
 ┌───────────────────────── lab/ (Python determinístico) ──────────────────────────┐
 │ guard ▸ strategy_check ▸ runner (Freqtrade/Docker) ▸ gates ▸ registry (SQLite)  │
 │ lookahead/recursive ▸ 4 cenários de custo ▸ benchmarks ▸ portfólio              │
 └───────────────┬───────────────────────────────────────────┬─────────────────────┘
                 │ revisões (texto)                          │ estado (somente leitura)
                 ▼                                           ▼
     validator · quant · risk (agentes)              Painel local (lab.dashboard)

        ┌────────────────── live/ (Windows, fora do Docker) ──────────────────┐
        │ engine ▸ risk ▸ killswitch ▸ journal ▸ broker (paper / MT5 demo)    │
        └──────────────────────────────────────────────────────────────────────┘
```

Um ciclo completo: **propor → implementar → testar → decidir → revisar → portfólio**.

## Estrutura do repositório

```text
.
├── lab/                    # Orquestrador, gates, runner, registro, painel (Python)
│   ├── config/             # gates, splits, holdout, cenários, orçamento, portfólio
│   └── dashboard_assets/   # HTML/JS do painel (lightweight-charts, Apache-2.0)
├── live/                   # Execução em tempo real (MT5 demo, kill switch, risco)
│   ├── core/               # engine, risk, journal, killswitch, realguard
│   ├── brokers/            # adaptador paper (simulado)
│   ├── config/             # live.example.json (live.json é local e ignorado)
│   └── tools/              # probe_mt5.py (verificação somente leitura)
├── user_data/
│   ├── strategies/         # Estratégias Freqtrade (+ _archive/ das rejeitadas)
│   └── config.dryrun.json  # Sem credenciais; dry_run=true
├── research/               # Ledger de hipóteses, manifestos, decisões, auditorias
├── tests/                  # Suíte de testes (lab, estratégias, segurança, live)
├── docs/                   # Protocolos, guias, checklist de operação real
├── reports/                # Relatórios interpretados
├── forward/                # Configs de forward test (dry-run)
├── .claude/                # Agentes e skills (trader-*)
├── docker-compose.yml          # Freqtrade (versão fixa)
├── docker-compose.forward.yml  # Forward test em dry-run
└── bot.py                  # Script experimental legado (fora do laboratório)
```

## Requisitos

| Componente | Uso | Observação |
|---|---|---|
| Python 3.13+ | `lab/`, testes, painel | Biblioteca padrão para o painel |
| Docker + Compose v2 | Freqtrade (backtest, dry-run) | No Windows, rode a partir do **WSL** |
| Freqtrade `2026.9` | Imagem `freqtradeorg/freqtrade:2026.9` | Versão fixa no compose |
| MetaTrader 5 + pacote `MetaTrader5` | `live/` | Só Windows; venv dedicado `live/.venv` (ignorado) |
| Claude Code | Agentes do ciclo (`.claude/agents/`) | Opcional; custo limitado por `lab/config/budget.json` |

Ambiente de referência: Windows 11 + WSL 2 (Kali), Docker 28, Compose v2, Python 3.13.

## Início rápido

```bash
git clone https://github.com/Kelme108/quant-trading-lab.git
cd quant-trading-lab
```

Execute os comandos do Docker a partir do **WSL** (Docker Engine Linux):

```bash
docker compose version
docker compose pull
docker compose run --rm freqtrade list-strategies --config user_data/config.dryrun.json
```

### Baixar dados públicos

A Binance é só a origem dos candles (endpoint público, sem conta nem saldo):

```bash
docker compose run --rm freqtrade download-data \
  --config user_data/config.dryrun.json \
  --exchange binance --pairs BTC/USDT --timeframes 1h \
  --timerange 20251020-20261020 --data-format-ohlcv feather
```

### Backtest de referência

```bash
docker compose run --rm freqtrade backtesting \
  --config user_data/config.dryrun.json \
  --strategy SmaTrendBaseline --strategy-path user_data/strategies \
  --timeframe 1h --pairs BTC/USDT --timerange 20251020-20261020 \
  --dry-run-wallet 100 --fee 0.001 --export trades
```

A baseline `SmaTrendBaseline` (SMA20/SMA50, filtro SMA200, stop de 10%) é uma **referência de infraestrutura congelada**, não uma recomendação. Mudanças de regra exigem uma nova estratégia versionada.

Para análise de *look-ahead* e *recursive*, comandos completos e interpretação, veja o [guia de uso do Freqtrade](docs/guia-utilizacao-freqtrade.md).

## Laboratório multiagente (`lab/`)

```bash
python -m lab.orchestrator expand-data                 # baixa/estende candles dos pares habilitados
python -m lab.orchestrator cycle --max-experiments 1   # um ciclo completo
python -m lab.orchestrator status                      # hipóteses, status e gasto com agentes
python -m lab.orchestrator propose
python -m lab.orchestrator implement H-004
python -m lab.orchestrator run H-004 --split exploration
python -m lab.orchestrator decide H-004
python -m lab.orchestrator review H-004
python -m lab.orchestrator portfolio
```

- **Dados e splits:** BTC/USDT, ETH/USDT e BNB/USDT em 1h ([scenarios.json](lab/config/scenarios.json)). Por par, 75% do histórico é exploração e 25% validação, com limites em timestamps exatos ([splits.json](lab/config/splits.json)). O **teste final** usa apenas dados posteriores a 21/10/2026 e está trancado (`final_test_unlocked: false`); só o usuário destranca.
- **Agentes** ([.claude/agents/](.claude/agents/)): `scout` (coleta ideias de fontes públicas), `research` (propõe uma hipótese), `developer` (implementa), `validator`, `quant` e `risk` (revisões). Cada um só pode criar os arquivos esperados naquele passo.
- **Guard** ([lab/guard.py](lab/guard.py)): verifica por hash antes/depois; violação interrompe o ciclo e arquivos protegidos voltam do `HEAD`.
- **Triagem de código:** estratégias geradas passam por análise estática ([strategy_check.py](lab/strategy_check.py)), pela suíte de testes e por um backtest curto no Freqtrade real.
- **Portfólio** ([portfolio.json](lab/config/portfolio.json)): entra quem é candidato em todos os pares e splits, com lucro por dia consistente e baixa correlação com os já incluídos, considerado por ordem de registro (nunca por desempenho). Portfólio vazio é um resultado válido.
- **Custo:** o único custo variável são as chamadas aos agentes; [budget.json](lab/config/budget.json) limita cada chamada e cada ciclo, e o gasto fica em `agent_runs` no banco.
- **Registro:** `research/lab.sqlite` é a fonte da verdade e **não é versionado**; o contador de hipóteses testadas vive nele. **Faça backup**: perder o arquivo apaga a penalidade por múltiplos testes. O [ledger](research/hypothesis-ledger.md) é gerado a partir dele.

## Gates de validação

Definidos em [lab/config/gates.json](lab/config/gates.json). O hash SHA-256 do arquivo é gravado com cada decisão, tornando alterações detectáveis. Valores ainda marcados como *propostos*.

| Gate | Regra |
|---|---|
| Look-ahead | Sem viés detectado em todos os cenários e splits |
| Recursive | Indicadores estáveis após o `startup_candle_count` |
| Mínimo de trades | ≥ 30 por split; abaixo disso a decisão é *inconclusiva* |
| Lucro líquido | Positivo nos cenários base e conservador, acima de uma barra que **sobe 10% por variante** testada na família |
| Sem melhor trade | Lucro continua positivo removendo o maior trade |
| Drawdown | ≤ 25% em todos os cenários de custo |
| Benchmarks | Reporta contra caixa e comprar-e-manter (não é obrigatório vencer) |
| Progressão | Exploração → validação (lida uma vez) → teste final trancado |

## Painel de monitoramento

```bash
python -m lab.dashboard serve --open   # http://127.0.0.1:8765 (atualiza a cada 15 s)
python -m lab.dashboard export         # HTML autônomo em research/dashboard.html
```

Mostra o **funil de pesquisa**, quais gates mais barram, hipóteses por par e etapa com o motivo de cada decisão, retorno por cenário de custo, curva de saldo, tentativas por família, gasto com agentes, ciclos recentes, saúde/defasagem dos dados e o estado de segurança. Há também página de dry-run (status do congelamento, qualidade de execução e intake de ideias). Cada gráfico tem visão em tabela.

- **Somente leitura:** escuta só em `127.0.0.1`, abre o banco com `mode=ro`, aceita só GET/HEAD, recusa `Host` desconhecido (contra DNS rebinding) e usa CSP com nonce por requisição. Texto vindo de agentes e da web entra como texto puro.
- **Sem dependências novas:** biblioteca padrão + HTML/JS/SVG, sem CDN.
- Para trades e saldo em tempo real do bot, use o FreqUI (`http://127.0.0.1:8080`).

## Camada de execução em tempo real (`live/`)

Motor de execução separado do Freqtrade (o pacote `MetaTrader5` só roda no Windows, com o terminal aberto e logado). O objetivo é operar mini índice (WIN) e mini dólar (WDO) da B3 — **hoje apenas em conta demo e sem nenhuma estratégia aprovada**. O que existe é infraestrutura: motor, gestão de risco, *kill switch*, diário de operações e adaptador simulado.

**Limites iniciais** ([live/DECISIONS.md](live/DECISIONS.md), [live.example.json](live/config/live.example.json)):

| Item | Valor |
|---|---|
| Modalidade | Day-trade, somente comprado, sem overnight |
| Perda diária / semanal máxima | R$ 300 / R$ 900 |
| Contratos por ativo | 2 |
| Operações por dia | 10 |
| Stop obrigatório | Sim |
| Kill switch | Arquivo-sentinela `live/STOP` |
| Dinheiro real | **Bloqueado** (`allow_real=false`) |

Uma ordem real só sai se **todas** as condições forem verdadeiras: `LIVE_MODE=real`; `allow_real: true` com SHA-256 do `live.json` registrado pelo usuário; conta real cujo número bate com `LIVE_ACCOUNT_ID`; e estratégia ativa com hash congelado e aprovação no registry. Em conta demo, a lógica inverte: recusa-se a execução se a conta for real. A mesma função de sinal deve rodar no backtest e no tempo real (teste de paridade).

```bash
cp live/config/live.example.json live/config/live.json   # local, ignorado pelo git
python live/tools/probe_mt5.py                           # verificação somente leitura da conta
```

Credenciais (login, senha, servidor) ficam **somente em variáveis de ambiente ou `.env` ignorado**, nunca no repositório.

## Skills `trader-*`

Em [.claude/skills/](.claude/skills/) há skills independentes do Claude Code para um fluxo de investimento discricionário, todas gerando **propostas** e nunca ordens sem confirmação explícita:

`trader-copycat` (13F) · `trader-analyst` (SEC EDGAR) · `trader-screener` · `trader-budget` · `trader-risk` · `trader-broker` · `trader-rebalance` · `trader-tax` · `trader-news` · `trader-alerts` · `trader-pelosi`

## Testes

```bash
python -m unittest discover -s tests -v
python research/validate_ohlcv.py user_data/data/binance/BTC_USDT-1h.feather
```

A suíte cobre gates, estatística, custos, splits, guard, runner, orquestrador, painel, estratégias e a configuração de segurança. Testes em `tests/live/` cobrem o motor de execução. [tests/test_protected_files.py](tests/test_protected_files.py) e [lab/guard.py](lab/guard.py) protegem arquivos críticos (gates, splits, holdout, config de dry-run).

## Segurança e boas práticas

- `dry_run=true`, `trading_mode=spot`, `can_short=false`; sem chaves e sem permissão de saque.
- O `.gitignore` mantém fora do git: credenciais, bancos SQLite, logs, dados de mercado, resultados brutos, `.env`, ambientes virtuais, `live/config/live.json` e `live/STOP`.
- FreqUI desabilitado por padrão; ao usar, publique apenas em `127.0.0.1` e nunca na LAN/Internet.
- Antes de qualquer decisão: compare exploração, validação e teste final, inclua taxas e *slippage* conservadores, benchmarks, regimes distintos, sensibilidade e *walk-forward*.

## Documentação

| Documento | Conteúdo |
|---|---|
| [guia-utilizacao-freqtrade.md](docs/guia-utilizacao-freqtrade.md) | Guia para iniciantes: backtest, lookahead, recursive, dry-run |
| [protocolo-validacao-v3.md](docs/protocolo-validacao-v3.md) | Protocolo de validação vigente |
| [procedimento-validacao-aprimoramento.md](docs/procedimento-validacao-aprimoramento.md) | Melhorias do procedimento |
| [relatorio-auditoria-estrategias.md](docs/relatorio-auditoria-estrategias.md) | Auditoria das estratégias |
| [estrategias-h011-h014.md](docs/estrategias-h011-h014.md) | Estratégias H-011 a H-014 |
| [checklist-operacao-real.md](docs/checklist-operacao-real.md) | Checklist para qualquer operação real |
| [prompt-execucao-tempo-real.md](docs/prompt-execucao-tempo-real.md) | Especificação da camada `live/` |
| [portal-redesign.md](docs/portal-redesign.md) | Redesenho do painel |
| [research-decision.md](docs/research-decision.md) | Decisões de pesquisa |
| [hypothesis-ledger.md](research/hypothesis-ledger.md) | Registro de todas as hipóteses |
| [command-log.md](research/command-log.md) | Log de comandos e invalidações |

## Status e resultados

Das 19 hipóteses registradas (H-001 a H-019):

- 1 referência congelada (`SmaTrendBaseline`);
- a grande maioria **rejeitada na exploração** ou descartada por menos de 30 trades (códigos arquivados em `user_data/strategies/_archive/`);
- 1 **candidata na exploração** (H-009, `WeeklyBreakoutRegime`), ainda sem validação e em forward test congelado (`research/forward/`);
- 1 inválida por desvio entre implementação e regra.

Resultados anteriores a 30/10/2026 que mostravam "1 operação" eram um defeito do ambiente de teste e foram invalidados (veja [command-log.md](research/command-log.md)). Para números atualizados consulte o ledger e o painel — este README não reproduz métricas para não envelhecê-las.

## Fontes

- [Freqtrade](https://www.freqtrade.io/en/stable/) · [Backtesting](https://docs.freqtrade.io/en/latest/backtesting/) · [Data download](https://docs.freqtrade.io/en/stable/data-download/) · [FreqUI](https://docs.freqtrade.io/en/latest/freq-ui/)
- [Binance Spot API](https://github.com/binance/binance-spot-api-docs)
- Bailey & López de Prado, *The Deflated Sharpe Ratio* (2014) e Bailey, Borwein, López de Prado & Zhu, *Pseudo-Mathematics and Financial Charlatanism* (2014) — base da penalidade por múltiplos testes.
- [MetaTrader 5 Python](https://www.mql5.com/en/docs/python_metatrader5)
- [Lightweight Charts](https://github.com/tradingview/lightweight-charts) (Apache-2.0)

## Licença

Nenhuma licença foi definida ainda; todos os direitos reservados ao autor até que uma seja adicionada.
