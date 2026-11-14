# Veredito do dry-run (por número de trades e por todas as métricas)

Regra: lab/config/dryrun.json (decisão do dono em 10/11/2026). Aprovação aqui = vale uma análise humana para dinheiro real, nunca uma ordem. O holdout formal (>= 2027-04-21) continua separado e inalterado.

Mínimo para decidir: 60 trades fechados e 14 dias; reprova cedo com 30+ trades e fator de lucro < 0.7.
Day trade precisa operar, comparado com a própria exploração (decisão do dono D1, 13/11/2026): o bot é descartado (`inactive`) se, depois de T dias, fechou menos trades que o percentil 1 do que a exploração dos mesmos pares fechou em janelas de T dias, ou se ficou mais tempo sem trade que o maior intervalo da exploração; aviso abaixo do percentil 5. O registro é gravado no congelamento, antes de o bot rodar. Congelamentos sem esse registro seguem a regra anterior: descarte com 2+ dias e menos de 1 trade(s), ou sem trade há mais de 2 dias. O relógio começa no congelamento. O descarte é automático: o bot é parado e o congelamento vai para research/forward/retired/.

| Hipótese | Veredito | Rodando (dias) | Trades | Trades/dia | Sem trade há (dias) | Dias até o mínimo | Acerto | Payoff | Fator de lucro | Expectativa/trade | Lucro (USDT) | Sem o melhor | Drawdown | P(média>0) |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|

## Retirados do dry-run

| Hipótese | Estratégia | Congelado em | Retirado em | Motivo |
|---|---|---|---|---|
| H-001 | SmaTrendBaseline_H001_v1 | 2026-11-10T15:01 | 2026-11-12T16:45 | INACTIVE: 0 closed trades in 2.1 days (needs 1 within 2 days) |
| H-009 | WeeklyBreakoutRegime_H009_v1 | 2026-11-04T21:39 | 2026-11-12T16:45 | INACTIVE: 0 closed trades in 7.8 days (needs 1 within 2 days) |
| H-016 | TimeSeriesMomentum_H016_v1 | 2026-11-05T17:29 | 2026-11-12T16:45 | INACTIVE: 0 closed trades in 7.0 days (needs 1 within 2 days) |
| H-043 | HourlyWilliamsVolBreakout_H043_v1 | 2026-11-10T15:08 | 2026-11-12T16:45 | INACTIVE: 0 closed trades in 2.1 days (needs 1 within 2 days) |
| H-047 | RelativeStrengthRatioRotation_H047_v1 | 2026-11-06T17:22 | 2026-11-12T16:45 | INACTIVE: 0 closed trades in 6.0 days (needs 1 within 2 days) |
| H-100 | RSIOverboughtMomentumRVol_H100_v1 | 2026-11-10T23:44 | 2026-11-13T00:32 | INACTIVE: 0 closed trades in 2.0 days (needs 1 within 2 days) |
| H-101 | HourlyIchimokuTrendRVol_H101_v1 | 2026-11-10T23:44 | 2026-11-13T00:32 | INACTIVE: 0 closed trades in 2.0 days (needs 1 within 2 days) |
| H-102 | IntradayJumpContinuationStrong_H102_v1 | 2026-11-10T23:44 | 2026-11-13T00:33 | INACTIVE: 0 closed trades in 2.0 days (needs 1 within 2 days) |
| H-103 | AbnormalDayContinuationRVol_H103_v1 | 2026-11-10T23:44 | 2026-11-13T00:33 | INACTIVE: 0 closed trades in 2.0 days (needs 1 within 2 days) |
| H-104 | HourlyWilliamsVolBreakoutRVol_H104_v1 | 2026-11-10T23:44 | 2026-11-13T00:33 | INACTIVE: 0 closed trades in 2.0 days (needs 1 within 2 days) |
