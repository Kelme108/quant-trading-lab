---
tipo: decisao
data: 2026-11-21
atualizado: 2026-11-21
tags: [cerebro, decisao, auditoria, backtest, demo]
---

# Auditoria: o backtest reproduz a demo?

**Data:** 2026-11-21  ·  **Quem pediu:** o dono ("nenhuma estratégia passava... será que as estratégias estão implementadas corretamente nesse backtest?")

## Resposta curta

- **O simulador da esteira está correto.** Refeito nos mesmos dias da demo (19/11, barras de 1 min do contrato WINZ26 gravadas pelo gravador de ticks), ele bateu trade a trade com os robôs da esteira: mesmo horário, lado e motivo de saída, com diferença de poucos ticks no preço.
- **O "nenhuma passa" vem dos critérios do portão das regras P** (`b3/config/gates_b3.json`), não do simulador.
- **O resultado "bom" da demo veio de fechamentos manuais.** Saída `server:0` no diário é `DEAL_REASON_CLIENT` do MT5: uma ordem dada no terminal, não pelo robô.

## Como o backtest implementa as saídas (`b3/p026_lab.simulate`, usado por `b3/exit_menu.py`)

| Item | Regra |
|---|---|
| Entrada | sinal no fechamento da barra; ordem a mercado na abertura do minuto seguinte, mais slippage |
| Unidade | stop e alvo em V (k × V × preço, menu S1–S4) ou em R$ (menu B1–B5), arredondados para cima ao tick |
| Ordem dentro do minuto | stop primeiro; stop e alvo no mesmo minuto contam como **stop** (conservador) |
| Alvo | ordem limitada: só preenche se o preço passar **1 tick além**, e sai no preço do alvo |
| Stop | sai no pior entre o nível e a abertura do minuto (gap), menos slippage |
| Tempo | 60 min; zera no horário de fechamento forçado do calendário |
| Custo medido (WIN) | R$ 0,25 por lado de taxa B3 + 0,4 tick por lado = R$ 1,30 por ida e volta; p90 R$ 3,00 |
| Contrato | 1 ponto = R$ 0,20; tick 5 pontos = R$ 1 |

Stop e alvo no mesmo minuto: **menos de 0,15% dos trades** na exploração (E-225, E-040, E-102, E-160, E-193); trocar todos por alvo muda o resultado em menos de R$ 0,10 por trade.

## Divergências backtest × demo (19/11, robôs da esteira)

| Robô | O que divergiu | Causa | Feito |
|---|---|---|---|
| E-164 | nunca operou; erro em toda barra | a família usa o fechamento do dólar (`other_close`) e o robô ao vivo só recebe barras do índice | não religar; consertar antes (dar barras de WDO ao robô) ou não levar famílias assim à demo |
| E-193 | backtest: 3 trades; demo: 0 | o robô recebia **volume de ticks**; a pesquisa usa **contratos** | **corrigido** em `live/brokers/mt5.py` (`_bar_volume`, usa `real_volume`) + teste |
| E-225 | 1 trade trocado de lugar (15:15 × 19:50) | stop e alvo do robô são medidos do fechamento do sinal; na pesquisa, da abertura do minuto seguinte (25 pontos de diferença mudaram a hora da saída) | pequeno; registrado |
| E-102, E-225 | saídas `server:0` com lucro | fechamento manual pelo terminal | registrado |
| Saída S4 (trailing) | não está em uso | ao vivo o stop sobe a cada barra da estratégia (5 min); na pesquisa, a cada minuto | consertar antes de ligar um robô S4 |

## A demo de 17 a 19/11 sem as mãos

96 trades: **24 fechados manualmente** (todos ganhadores, +R$ 1.405) e **72 fechados pelo robô** (31% de acerto, −R$ 1.839 bruto).

## Por que as regras P nunca passam

| Critério (`gates_b3.json`) | Valor | Efeito |
|---|---|---|
| Custo "base" | 1 tick de slippage por lado + 1 tick extra no stop | 2 a 3 vezes o custo medido (R$ 1,30) |
| Barra de retorno | 1% × (1 + 0,1 × variantes anteriores) = **27,5%** após 265 variantes, em base **e** conservador | inalcançável para qualquer regra |
| Sem o melhor trade > 0, 60% de anos positivos, drawdown ≤ 25% | | reprovam quase todas |

Mesmo no custo otimista (sem slippage), P-020, P-026 e P-028 ficam negativas com as saídas originais. P-014, P-017 e P-030 ficam positivas no otimista e perto de zero no custo medido (estimativa por interpolação). Na triagem da esteira, o critério que mais reprova é o **planalto** (337 de 367 blocos família × mercado), seguido de fatias positivas e resultado médio com a saída padrão R$ 30/R$ 30.

## Propostas (dependem do dono; nada alterado)

1. Portão P: custo base = **custo medido** e p90 como conservador.
2. Trocar a barra linear (0,1 por variante) por **DSR / t mínimo com N efetivo** (grupos de variantes correlacionadas).
3. Manter planalto, comparação com entrada aleatória e validação lida uma vez.

## Mudança feita com o aval do dono

A esteira saiu da pausa em 2026-11-21 e cada lote novo também roda o menu de saídas em reais (`b3/config/exit_brl.json`) em `ops/state/exit_brl/` (`b3/esteira_cycle.py`, função `exit_menu`).

## Depois da aprovação (2026-11-21, noite)

O dono aprovou as propostas 1 e 2; o portão foi trocado (`b3/config/gates_b3.json`, commit `6af910a`).

**Regras P na exploração com o portão novo** (diagnóstico, sem registro no ledger; t mínimo 3,34 com 266 tentativas):

| Regra | Trades/ano | Acerto | Líquido base | Líquido p90 | t | Decisão |
|---|---|---|---|---|---|---|
| P-004 | 246 | 60,5% | +24,4% | +18,6% | 5,96 | **passa** (mas a validação já foi lida em 2026-11-16 e reprovou no portão antigo) |
| P-014 | 225 | 53,3% | +3,5% | −0,9% | 0,64 | reprova |
| P-017, P-030 | 700–1.000 | 44–50% | ≈ 0 | negativo | ≈ 0 | reprova |
| P-020, P-023, P-026, P-028 | 540–930 | 35–55% | −8% a −18% | negativo | < 0 | reprova |
| P-024, P-025 | 500–870 | 31–43% | −25% | negativo | ≈ −3 | reprova |

Conclusão: com custo justo e barra estatística, as regras P continuam sem vantagem nas saídas originais; a exceção é a P-004, cuja validação não pode ser relida.

**Candidatas da esteira (exploração, melhores 30 por acerto com p90 > 0 e acima da entrada aleatória):** nenhuma atinge t ≥ 4,6 (≈ 35 mil versões lidas). Mais perto: E-410 1m com B1 (alvo R$ 35, stop R$ 90): 2.725 trades, acerto 71%, +R$ 4,17 por trade, p90 +R$ 2,88, t 4,48, os 4 anos positivos. Depois: E-303 S2 (t 3,38) e E-286 B5 (t 3,29).
