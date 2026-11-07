# Revisão de trades: H-065 (exploração)

Fonte dos trades: `research/experiments/20261107T153959Z-h-065-exploration-btc-usdt/raw/backtest-result-2026-11-07_15-44-45.zip`; `research/experiments/20261107T153959Z-h-065-exploration-eth-usdt/raw/backtest-result-2026-11-07_15-46-53.zip`; `research/experiments/20261107T153959Z-h-065-exploration-bnb-usdt/raw/backtest-result-2026-11-07_15-49-01.zip`; `research/experiments/20261107T153959Z-h-065-exploration-xrp-usdt/raw/backtest-result-2026-11-07_15-51-06.zip`; `research/experiments/20261107T153959Z-h-065-exploration-ada-usdt/raw/backtest-result-2026-11-07_15-53-10.zip`; `research/experiments/20261107T153959Z-h-065-exploration-ltc-usdt/raw/backtest-result-2026-11-07_15-55-12.zip`; `research/experiments/20261107T153959Z-h-065-exploration-link-usdt/raw/backtest-result-2026-11-07_15-57-15.zip`; `research/experiments/20261107T153959Z-h-065-exploration-doge-usdt/raw/backtest-result-2026-11-07_15-59-10.zip`; `research/experiments/20261107T153959Z-h-065-exploration-sol-usdt/raw/backtest-result-2026-11-07_16-01-06.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 211; lucro líquido: -13.48.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit | 83 | 5.29 | – | 0.68% | 52% | 24.0 h |
| stop_loss | 70 | -21.44 | – | -3.29% | 0% | 8.7 h |
| range_rsi_exit | 36 | 6.33 | – | 1.90% | 100% | 11.6 h |
| trend_ema_exit | 22 | -3.66 | – | -1.82% | 0% | 15.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 19 | -5.26 | -2.93% | 5% |
| 3 h a 1 dia | 109 | -13.51 | -1.34% | 32% |
| 1 a 7 dias | 83 | 5.29 | 0.68% | 52% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (79): MFE mediano 2.7%, MAE mediano -0.9%, devolução média do melhor ponto 1.6%, captura mediana 0.56.
- Perdedores (132): MAE mediano -3.1%, MFE mediano 0.8%; 14 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 5.80; – do lucro antes de custos.
- Trades < 3 h: 19 (lucro -5.26); reentradas em < 24 h: 13 (lucro -0.64).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -14.08.
- Lucro por ano de fechamento: 2017: -1.6, 2018: -3.4, 2019: 0.6, 2020: -1.2, 2021: 0.2, 2022: -3.2, 2023: -3.1, 2024: -1.7.

## ETH/USDT

Trades: 193; lucro líquido: -8.95.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 78 | -24.49 | – | -3.29% | 0% | 6.8 h |
| time_exit | 54 | 10.44 | – | 2.04% | 69% | 24.0 h |
| range_rsi_exit | 41 | 8.85 | – | 2.28% | 100% | 12.6 h |
| trend_ema_exit | 20 | -3.75 | – | -2.03% | 0% | 15.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 25 | -7.86 | -3.29% | 0% |
| 3 h a 1 dia | 114 | -11.53 | -1.06% | 36% |
| 1 a 7 dias | 54 | 10.44 | 2.04% | 69% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (78): MFE mediano 3.4%, MAE mediano -1.0%, devolução média do melhor ponto 2.0%, captura mediana 0.54.
- Perdedores (115): MAE mediano -3.2%, MFE mediano 0.9%; 22 (19%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 5.45; – do lucro antes de custos.
- Trades < 3 h: 25 (lucro -7.86); reentradas em < 24 h: 12 (lucro -0.84).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -10.19.
- Lucro por ano de fechamento: 2017: 0.8, 2018: -3.4, 2019: -0.8, 2020: -2.3, 2021: -1.2, 2022: -0.8, 2023: -1.4, 2024: 0.2.

## BNB/USDT

Trades: 168; lucro líquido: -14.40.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 73 | -21.83 | – | -3.29% | 0% | 6.4 h |
| time_exit | 56 | 5.33 | – | 1.09% | 57% | 24.0 h |
| range_rsi_exit | 26 | 4.53 | – | 1.95% | 96% | 11.4 h |
| trend_ema_exit | 13 | -2.44 | – | -2.11% | 0% | 13.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 31 | -8.72 | -3.06% | 3% |
| 3 h a 1 dia | 81 | -11.01 | -1.50% | 30% |
| 1 a 7 dias | 56 | 5.33 | 1.09% | 57% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (57): MFE mediano 3.2%, MAE mediano -0.9%, devolução média do melhor ponto 1.5%, captura mediana 0.58.
- Perdedores (111): MAE mediano -3.4%, MFE mediano 1.1%; 28 (25%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 4.49; – do lucro antes de custos.
- Trades < 3 h: 31 (lucro -8.72); reentradas em < 24 h: 5 (lucro 0.88).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -15.35.
- Lucro por ano de fechamento: 2018: -5.1, 2019: -3.1, 2020: -0.9, 2021: -2.6, 2022: -1.3, 2023: -0.4, 2024: -0.9.

## XRP/USDT

Trades: 182; lucro líquido: -13.85.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 90 | -26.99 | – | -3.29% | 0% | 7.3 h |
| time_exit | 50 | 13.03 | – | 2.94% | 68% | 24.0 h |
| range_rsi_exit | 22 | 3.85 | – | 1.93% | 100% | 13.9 h |
| trend_ema_exit | 20 | -3.74 | – | -2.08% | 0% | 12.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 30 | -8.99 | -3.29% | 0% |
| 3 h a 1 dia | 102 | -17.89 | -1.92% | 22% |
| 1 a 7 dias | 50 | 13.03 | 2.94% | 68% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (56): MFE mediano 3.8%, MAE mediano -1.4%, devolução média do melhor ponto 2.7%, captura mediana 0.57.
- Perdedores (126): MAE mediano -3.3%, MFE mediano 1.0%; 27 (21%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 4.92; – do lucro antes de custos.
- Trades < 3 h: 30 (lucro -8.99); reentradas em < 24 h: 11 (lucro -2.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -16.50.
- Lucro por ano de fechamento: 2018: -5.3, 2019: -2.1, 2020: -0.4, 2021: -3.2, 2022: -2.5, 2023: 0.3, 2024: -0.6.

## ADA/USDT

Trades: 160; lucro líquido: -15.61.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 84 | -25.36 | – | -3.28% | 0% | 6.4 h |
| time_exit | 50 | 6.93 | – | 1.53% | 64% | 24.0 h |
| range_rsi_exit | 17 | 4.59 | – | 2.98% | 100% | 11.5 h |
| trend_ema_exit | 9 | -1.77 | – | -2.24% | 0% | 17.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 29 | -8.91 | -3.29% | 0% |
| 3 h a 1 dia | 81 | -13.63 | -1.85% | 21% |
| 1 a 7 dias | 50 | 6.93 | 1.53% | 64% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (49): MFE mediano 4.2%, MAE mediano -1.3%, devolução média do melhor ponto 2.9%, captura mediana 0.44.
- Perdedores (111): MAE mediano -3.4%, MFE mediano 1.1%; 24 (22%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 4.31; – do lucro antes de custos.
- Trades < 3 h: 29 (lucro -8.91); reentradas em < 24 h: 6 (lucro 0.89).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -16.57.
- Lucro por ano de fechamento: 2018: -1.3, 2019: -6.1, 2020: -2.6, 2021: -2.7, 2022: -1.7, 2023: 0.6, 2024: -1.7.

## LTC/USDT

Trades: 173; lucro líquido: -9.23.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 80 | -25.38 | – | -3.28% | 0% | 8.0 h |
| time_exit | 43 | 9.71 | – | 2.33% | 79% | 24.0 h |
| range_rsi_exit | 37 | 8.67 | – | 2.43% | 97% | 12.4 h |
| trend_ema_exit | 13 | -2.23 | – | -1.83% | 0% | 16.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 22 | -7.00 | -3.28% | 0% |
| 3 h a 1 dia | 108 | -11.93 | -1.15% | 33% |
| 1 a 7 dias | 43 | 9.71 | 2.33% | 79% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (70): MFE mediano 3.6%, MAE mediano -1.2%, devolução média do melhor ponto 2.0%, captura mediana 0.60.
- Perdedores (103): MAE mediano -3.6%, MFE mediano 0.9%; 22 (21%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 4.97; – do lucro antes de custos.
- Trades < 3 h: 22 (lucro -7.00); reentradas em < 24 h: 9 (lucro -0.93).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -11.22.
- Lucro por ano de fechamento: 2018: -0.8, 2019: -2.1, 2020: -0.0, 2021: -1.9, 2022: -0.9, 2023: -2.8, 2024: -0.7.

## LINK/USDT

Trades: 139; lucro líquido: -4.95.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 70 | -22.29 | – | -3.28% | 0% | 6.1 h |
| time_exit | 39 | 10.48 | – | 2.79% | 72% | 24.0 h |
| range_rsi_exit | 22 | 8.43 | – | 3.96% | 100% | 10.1 h |
| trend_ema_exit | 8 | -1.56 | – | -2.01% | 0% | 16.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 22 | -7.06 | -3.28% | 0% |
| 3 h a 1 dia | 78 | -8.37 | -1.11% | 28% |
| 1 a 7 dias | 39 | 10.48 | 2.79% | 72% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (50): MFE mediano 5.1%, MAE mediano -1.1%, devolução média do melhor ponto 2.2%, captura mediana 0.63.
- Perdedores (89): MAE mediano -3.5%, MFE mediano 1.2%; 29 (33%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 4.02; – do lucro antes de custos.
- Trades < 3 h: 22 (lucro -7.06); reentradas em < 24 h: 8 (lucro 1.80).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -6.74.
- Lucro por ano de fechamento: 2019: -2.1, 2020: -3.5, 2021: 2.7, 2022: -0.1, 2023: -1.9, 2024: -0.2.

## DOGE/USDT

Trades: 130; lucro líquido: -10.50.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 67 | -20.38 | – | -3.28% | 0% | 6.6 h |
| time_exit | 31 | 8.74 | – | 3.12% | 65% | 24.0 h |
| range_rsi_exit | 20 | 3.30 | – | 1.80% | 100% | 10.5 h |
| trend_ema_exit | 12 | -2.16 | – | -1.88% | 0% | 11.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 23 | -7.00 | -3.28% | 0% |
| 3 h a 1 dia | 76 | -12.23 | -1.72% | 26% |
| 1 a 7 dias | 31 | 8.74 | 3.12% | 65% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (40): MFE mediano 4.3%, MAE mediano -0.9%, devolução média do melhor ponto 3.0%, captura mediana 0.48.
- Perdedores (90): MAE mediano -3.4%, MFE mediano 1.1%; 27 (30%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 3.59; – do lucro antes de custos.
- Trades < 3 h: 23 (lucro -7.00); reentradas em < 24 h: 2 (lucro -0.30).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -12.99.
- Lucro por ano de fechamento: 2019: -2.5, 2020: -3.2, 2021: -3.1, 2022: 1.0, 2023: -1.1, 2024: -1.7.

## SOL/USDT

Trades: 102; lucro líquido: -6.63.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 55 | -17.37 | – | -3.28% | 0% | 6.5 h |
| range_rsi_exit | 21 | 5.85 | – | 2.91% | 100% | 12.9 h |
| time_exit | 21 | 5.73 | – | 2.86% | 81% | 24.0 h |
| trend_ema_exit | 5 | -0.84 | – | -1.74% | 0% | 12.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 18 | -5.72 | -3.28% | 0% |
| 3 h a 1 dia | 63 | -6.64 | -1.10% | 33% |
| 1 a 7 dias | 21 | 5.73 | 2.86% | 81% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (38): MFE mediano 5.2%, MAE mediano -1.7%, devolução média do melhor ponto 3.0%, captura mediana 0.54.
- Perdedores (64): MAE mediano -3.6%, MFE mediano 1.3%; 21 (33%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 2.92; – do lucro antes de custos.
- Trades < 3 h: 18 (lucro -5.72); reentradas em < 24 h: 7 (lucro 0.84).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -8.10.
- Lucro por ano de fechamento: 2020: -0.5, 2021: -2.2, 2022: -2.2, 2023: -0.5, 2024: -1.3.
