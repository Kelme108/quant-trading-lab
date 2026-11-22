---
tipo: area
atualizado: 2026-11-19
tags: [cerebro, b3, win, wdo]
---

# Linha B3: WIN e WDO

Linha principal desde 2026-11-16. Decisão em [[2026-11-16-b3-win-wdo-plano]]; planos em [../../plano-b3-win-wdo.md](../../plano-b3-win-wdo.md) e [../../plano-b3-reuso.md](../../plano-b3-reuso.md).

## Mercados e custos

- **WIN** (mini índice): custo de ida e volta ~0,011% do nocional; o slippage é ~80% do custo. **WDO** (mini dólar): ~0,0235%, mercado difícil.
- Medição de execução nos ticks da Clear: ordem a mercado 0,39 tick por lado contra a abertura da barra; stop executa no nível; limite no toque piora (seleção adversa). Ver `research/b3/execution_cost.json`.
- Timeframes de trabalho: **1, 5 e 15 min**, foco em 1 e 5 ([[2026-11-16-timeframes-1-5-15]]).

## Dados e divisões

- 5 anos de WIN$N/WDO$N (1m/5m/15m/D1) desde 2021-11-16 da Clear demo. Detalhes em [[Dados]].
- **Splits A** aprovados: exploração 2021-11-16..2024-07-01, validação ..2025-10-01, teste final depois (trancado). Arquivo: `b3/config/splits_b3.json`.
- Gates da B3: `b3/config/gates_b3.json` (portões de proxies). Escopo: `b3/config/scope_b3.json`.

## Código

| Arquivo | Papel |
|---|---|
| `b3/b3_data.py` | Rolagem, back-adjust, calendário do histórico |
| `b3/markets.py` | `B3Market` (stop paga 1 tick extra na base) e `ProxyStrategy` |
| `b3/costs.py`, `b3/instruments.py`, `b3/calendar.py` | Custos, instrumentos, sessões e feriados |
| `b3/backtest.py`, `b3/metrics.py` | Motor de backtest e métricas |
| `b3/proxy_pipeline.py`, `proxy_research.py`, `proxy_program.py` | Pipeline de regras por agente (P-NNN) |
| `b3/pattern_search.py`, `tick_search.py` | Busca de padrões e programa de ticks |
| `b3/esteira*.py` | [[Esteira]] |
| `b3/exit_menu.py`, `p026_lab.py`, `exit_study.py` | [[Menu-de-saidas]] |

## Programa de agentes

`b3/config/b3_program.json`: linha `b3`, a partir da P-013, alterna 1m/5m, até 2026-12-16, teto de regras por semana alto (decisão do dono em 2026-11-16). Piso de **500 trades/ano por mercado** para propostas novas. Pausa: `ops/state/STOP_PROXY_CYCLES`.

## Resultados

Ver [[Resultados-B3]]. Resumo: nenhuma regra com evidência fora da amostra; o gargalo é o custo contra movimentos pequenos.

## Armadilhas

- Relógio de ticks: [[2026-11-16-relogio-tick-mt5]].
- Rolagem de contrato: [[Pendencias-e-calendario]].
- O programa de ticks tem splits próprios (exploração até 2026-12-31). Ler antes disso só como leitura **interina**.
