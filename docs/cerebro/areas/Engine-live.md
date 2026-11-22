---
tipo: area
atualizado: 2026-11-19
tags: [cerebro, live, mt5, motor]
---

# Motor de execução (`live/`)

Motor próprio, fora do Freqtrade e fora do Docker, que roda no Windows com o terminal MetaTrader 5 aberto e logado. Especificação original: [../../prompt-execucao-tempo-real.md](../../prompt-execucao-tempo-real.md). Decisões iniciais: [live/DECISIONS.md](../../../live/DECISIONS.md).

## Peças

| Arquivo | Papel |
|---|---|
| `live/run.py` | Ponto de entrada: `python -m live.run --config live/config/<robô>.json` |
| `live/core/engine.py` | Laço: barras, sinal, risco, ordens, journal, comandos |
| `live/core/models.py` | `Signal`, `OrderRequest`, posição |
| `live/core/control.py` | Comandos manuais (fechar, pausar) via arquivo `live/commands/<robô>.json` |
| `live/brokers/mt5.py`, `paper.py` | Adaptador MT5 e corretora simulada |
| `live/strategies/b3_rule.py` | Liga uma regra P-NNN, ou uma família da esteira (`strategy.esteira`), ao motor |
| `live/feed.py` | Alimenta o gráfico do portal (1/5/15m, a cada 5 s) |
| `b3/esteira_live.py` | Regra da esteira com saída do menu ([[Menu-de-saidas]]) |

## Ações do sinal

`ENTER_LONG`, `ENTER_SHORT` (na demo), `EXIT`, `HOLD`, **`MOVE_STOP`** (aperta o stop via `TRADE_ACTION_SLTP`; nunca afrouxa; recusa → saída a mercado reduce-only).

## Guarda-corpos

- Conta **demo** por padrão: se a conta for real, o robô recusa. Ordem real exige `LIVE_MODE=real`, `allow_real: true` com SHA-256 do config registrado pelo dono, conta batendo com `LIVE_ACCOUNT_ID` e estratégia com hash congelado. Nada disso está ativo.
- Limites por robô: perda diária (R$ 300 nos robôs demo), entradas por dia, contratos por ativo (1).
- Zera a posição 10 min antes do fechamento. Entradas só 15 min depois da abertura até 30 min antes do fechamento (`SessionRules(15, 30, 10)`).
- Kill switch: arquivo `live/STOP`.
- Se outra conta logar no terminal, o guarda do robô para sem ordens (aconteceu em 2026-11-17 14:20).

## Controles do portal (conta real, sem robô ainda)

Botões do portal escrevem `live/commands/<robô>.json`; o próprio motor executa e registra no journal. Nunca feche por fora do motor. Decisão: [[2026-11-17-portal-controles-ao-vivo]]. Operação: `docs/runbook-ao-vivo.md` (rascunho, ainda sem commit; ver [[Publicar-no-GitHub]]).

## Journal e MFE/MAE

Cada robô tem `live/journal.<robô>.sqlite` (local) com ordens, trades e MFE/MAE. Logs em `live/logs/`, estado em `live/state/`.

## Testes

`tests/live/` (inclui `fake_mt5.py`, `test_move_stop.py`). Rode da raiz: `python -m pytest tests/live`.

## Pendências de código

`engine.py` e `run.py` têm mudanças não commitadas que misturam MOVE_STOP e controles do portal. Ver [[Pendencias-e-calendario]].
