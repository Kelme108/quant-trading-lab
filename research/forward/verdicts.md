# Veredito do dry-run (por número de trades e por todas as métricas)

Regra: lab/config/dryrun.json (decisão do dono em 10/11/2026). Aprovação aqui = vale uma análise humana para dinheiro real, nunca uma ordem. O holdout formal (>= 2027-04-21) continua separado e inalterado.

Mínimo para decidir: 60 trades fechados e 14 dias; reprova cedo com 30+ trades e fator de lucro < 0.7.
Day trade precisa operar: o bot é descartado (`inactive`) com 7+ dias rodando e menos de 5 trades fechados, ou sem nenhum trade há mais de 5 dias (decisão do dono, 11/11/2026). O relógio começa no congelamento.

| Hipótese | Veredito | Rodando (dias) | Trades | Trades/dia | Sem trade há (dias) | Dias até o mínimo | Acerto | Payoff | Fator de lucro | Expectativa/trade | Lucro (USDT) | Sem o melhor | Drawdown | P(média>0) |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| H-001 | collecting | 0.9 | 0 | 0.00 | – | – | – | – | – | – | 0.00 | – | 0.0% | 0.00 |
| H-009 | collecting | 6.6 | 0 | 0.00 | – | – | – | – | – | – | 0.00 | – | 0.0% | 0.00 |
| H-016 | collecting | 5.8 | 0 | 0.00 | – | – | – | – | – | – | 0.00 | – | 0.0% | 0.00 |
| H-043 | collecting | 0.9 | 0 | 0.00 | – | – | – | – | – | – | 0.00 | – | 0.0% | 0.00 |
| H-047 | collecting | 4.8 | 0 | 0.00 | – | – | – | – | – | – | 0.00 | – | 0.0% | 0.00 |
| H-100 | collecting | 0.5 | 0 | 0.00 | – | – | – | – | – | – | 0.00 | – | 0.0% | 0.00 |
| H-101 | collecting | 0.5 | 0 | 0.00 | – | – | – | – | – | – | 0.00 | – | 0.0% | 0.00 |
| H-102 | collecting | 0.5 | 0 | 0.00 | – | – | – | – | – | – | 0.00 | – | 0.0% | 0.00 |
| H-103 | collecting | 0.5 | 0 | 0.00 | – | – | – | – | – | – | 0.00 | – | 0.0% | 0.00 |
| H-104 | collecting | 0.5 | 0 | 0.00 | – | – | – | – | – | – | 0.00 | – | 0.0% | 0.00 |

## H-001: collecting
- 0/60 closed trades, 0.0/14 days
- running 0.9 days, 0.00 trades/day

## H-009: collecting
- 0/60 closed trades, 0.0/14 days
- running 6.6 days, 0.00 trades/day
- warning: no closed trade yet after 6.6 days (discard at 7 days with < 5 trades)

## H-016: collecting
- 0/60 closed trades, 0.0/14 days
- running 5.8 days, 0.00 trades/day
- warning: no closed trade yet after 5.8 days (discard at 7 days with < 5 trades)

## H-043: collecting
- 0/60 closed trades, 0.0/14 days
- running 0.9 days, 0.00 trades/day

## H-047: collecting
- 0/60 closed trades, 0.0/14 days
- running 4.8 days, 0.00 trades/day
- warning: no closed trade yet after 4.8 days (discard at 7 days with < 5 trades)

## H-100: collecting
- 0/60 closed trades, 0.0/14 days
- running 0.5 days, 0.00 trades/day

## H-101: collecting
- 0/60 closed trades, 0.0/14 days
- running 0.5 days, 0.00 trades/day

## H-102: collecting
- 0/60 closed trades, 0.0/14 days
- running 0.5 days, 0.00 trades/day

## H-103: collecting
- 0/60 closed trades, 0.0/14 days
- running 0.5 days, 0.00 trades/day

## H-104: collecting
- 0/60 closed trades, 0.0/14 days
- running 0.5 days, 0.00 trades/day
