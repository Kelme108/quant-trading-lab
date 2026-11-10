# Revisão de trades: H-102 (exploração)

Fonte dos trades: `research/experiments/20261110T191952Z-h-102-exploration-btc-usdt/raw/backtest-result-2026-11-10_19-28-22.zip`; `research/experiments/20261110T191952Z-h-102-exploration-eth-usdt/raw/backtest-result-2026-11-10_19-34-46.zip`; `research/experiments/20261110T191952Z-h-102-exploration-bnb-usdt/raw/backtest-result-2026-11-10_19-41-01.zip`; `research/experiments/20261110T191952Z-h-102-exploration-xrp-usdt/raw/backtest-result-2026-11-10_19-46-47.zip`; `research/experiments/20261110T191952Z-h-102-exploration-ada-usdt/raw/backtest-result-2026-11-10_19-52-03.zip`; `research/experiments/20261110T191952Z-h-102-exploration-ltc-usdt/raw/backtest-result-2026-11-10_19-57-24.zip`; `research/experiments/20261110T191952Z-h-102-exploration-link-usdt/raw/backtest-result-2026-11-10_20-02-59.zip`; `research/experiments/20261110T191952Z-h-102-exploration-doge-usdt/raw/backtest-result-2026-11-10_20-07-38.zip`; `research/experiments/20261110T191952Z-h-102-exploration-sol-usdt/raw/backtest-result-2026-11-10_20-12-50.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 115; lucro líquido: 56.85.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 73 | 581.96 | 1024% | 1.56% | 74% | 14.5 h |
| close_below_jump_low | 27 | -271.36 | -477% | -1.91% | 0% | 5.8 h |
| stop_loss | 15 | -253.76 | -446% | -3.29% | 0% | 5.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 19 | -227.44 | -2.31% | 0% |
| 3 h a 1 dia | 96 | 284.29 | 0.60% | 56% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (54): MFE mediano 3.2%, MAE mediano -0.5%, devolução média do melhor ponto 1.8%, captura mediana 0.51.
- Perdedores (61): MAE mediano -2.2%, MFE mediano 0.7%; 9 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 178.01; 76% do lucro antes de custos.
- Trades < 3 h: 19 (lucro -227.44); reentradas em < 24 h: 5 (lucro 69.53).
- Maior trade = 129% do lucro; top 5 = 379%; top 10 = 579%; lucro sem o melhor = -16.73.
- Lucro por ano de fechamento: 2017: -48.6, 2018: 33.3, 2019: -1.6, 2020: 17.5, 2021: 84.9, 2022: -21.7, 2023: -22.4, 2024: 15.5.

## ETH/USDT

Trades: 92; lucro líquido: 435.57.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 66 | 949.77 | 218% | 2.31% | 80% | 14.0 h |
| stop_loss | 18 | -392.45 | -90% | -3.29% | 0% | 8.6 h |
| close_below_jump_low | 8 | -121.75 | -28% | -2.31% | 0% | 7.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 9 | -172.61 | -2.83% | 0% |
| 3 h a 1 dia | 83 | 608.18 | 1.21% | 64% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (53): MFE mediano 3.9%, MAE mediano -0.4%, devolução média do melhor ponto 2.4%, captura mediana 0.60.
- Perdedores (39): MAE mediano -3.0%, MFE mediano 1.2%; 11 (28%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 180.59; 29% do lucro antes de custos.
- Trades < 3 h: 9 (lucro -172.61); reentradas em < 24 h: 6 (lucro 8.59).
- Maior trade = 16% do lucro; top 5 = 56%; top 10 = 98%; lucro sem o melhor = 365.01.
- Lucro por ano de fechamento: 2017: 40.0, 2018: 46.8, 2019: 138.6, 2020: 154.3, 2021: 90.8, 2022: -3.9, 2023: -61.7, 2024: 30.6.

## BNB/USDT

Trades: 91; lucro líquido: 289.04.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 61 | 828.18 | 287% | 2.24% | 74% | 14.1 h |
| stop_loss | 17 | -360.16 | -125% | -3.28% | 0% | 4.1 h |
| close_below_jump_low | 13 | -178.98 | -62% | -2.11% | 0% | 5.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 15 | -291.47 | -2.97% | 0% |
| 3 h a 1 dia | 76 | 580.51 | 1.29% | 59% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (45): MFE mediano 4.2%, MAE mediano -0.9%, devolução média do melhor ponto 2.0%, captura mediana 0.52.
- Perdedores (46): MAE mediano -2.6%, MFE mediano 0.8%; 11 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 171.33; 37% do lucro antes de custos.
- Trades < 3 h: 15 (lucro -291.47); reentradas em < 24 h: 5 (lucro 39.37).
- Maior trade = 28% do lucro; top 5 = 104%; top 10 = 171%; lucro sem o melhor = 208.87.
- Lucro por ano de fechamento: 2018: -14.3, 2019: 275.0, 2020: 87.6, 2021: 56.6, 2022: -79.8, 2023: -67.6, 2024: 31.4.

## XRP/USDT

Trades: 105; lucro líquido: -66.85.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 53 | 844.35 | – | 2.85% | 74% | 12.8 h |
| stop_loss | 40 | -748.63 | – | -3.29% | 0% | 4.0 h |
| close_below_jump_low | 12 | -162.58 | – | -2.31% | 0% | 8.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 20 | -375.49 | -3.25% | 0% |
| 3 h a 1 dia | 85 | 308.64 | 0.67% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (39): MFE mediano 5.4%, MAE mediano -1.1%, devolução média do melhor ponto 3.3%, captura mediana 0.50.
- Perdedores (66): MAE mediano -3.1%, MFE mediano 1.2%; 21 (32%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 181.85; 158% do lucro antes de custos.
- Trades < 3 h: 20 (lucro -375.49); reentradas em < 24 h: 3 (lucro -12.33).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -208.29.
- Lucro por ano de fechamento: 2018: 210.5, 2019: 70.5, 2020: -62.3, 2021: -63.3, 2022: -94.7, 2023: -130.7, 2024: 3.1.

## ADA/USDT

Trades: 62; lucro líquido: 203.68.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 35 | 674.92 | 331% | 3.51% | 77% | 13.8 h |
| stop_loss | 20 | -378.84 | -186% | -3.28% | 0% | 5.0 h |
| close_below_jump_low | 7 | -92.39 | -45% | -2.30% | 0% | 3.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 15 | -246.97 | -2.88% | 0% |
| 3 h a 1 dia | 47 | 450.66 | 1.79% | 57% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (27): MFE mediano 4.9%, MAE mediano -0.7%, devolução média do melhor ponto 3.2%, captura mediana 0.58.
- Perdedores (35): MAE mediano -3.1%, MFE mediano 2.2%; 19 (54%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 105.49; 34% do lucro antes de custos.
- Trades < 3 h: 15 (lucro -246.97); reentradas em < 24 h: 2 (lucro -29.71).
- Maior trade = 59% do lucro; top 5 = 194%; top 10 = 280%; lucro sem o melhor = 83.80.
- Lucro por ano de fechamento: 2018: 37.4, 2019: 86.2, 2020: 35.7, 2021: -20.2, 2022: 38.1, 2023: 66.6, 2024: -40.1.

## LTC/USDT

Trades: 103; lucro líquido: 117.99.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 61 | 909.62 | 771% | 2.58% | 70% | 13.7 h |
| stop_loss | 33 | -655.27 | -555% | -3.28% | 0% | 5.8 h |
| close_below_jump_low | 9 | -136.36 | -116% | -2.52% | 0% | 6.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 18 | -354.28 | -3.23% | 0% |
| 3 h a 1 dia | 85 | 472.27 | 1.00% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (43): MFE mediano 4.3%, MAE mediano -0.7%, devolução média do melhor ponto 2.7%, captura mediana 0.55.
- Perdedores (60): MAE mediano -3.1%, MFE mediano 1.2%; 16 (27%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 183.27; 61% do lucro antes de custos.
- Trades < 3 h: 18 (lucro -354.28); reentradas em < 24 h: 7 (lucro -9.01).
- Maior trade = 95% do lucro; top 5 = 308%; top 10 = 482%; lucro sem o melhor = 6.06.
- Lucro por ano de fechamento: 2018: -6.1, 2019: 196.2, 2020: 24.6, 2021: 1.4, 2022: 1.6, 2023: -55.0, 2024: -44.8.

## LINK/USDT

Trades: 46; lucro líquido: 189.87.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 22 | 633.27 | 334% | 5.38% | 77% | 13.0 h |
| stop_loss | 21 | -393.47 | -207% | -3.29% | 0% | 4.9 h |
| close_below_jump_low | 3 | -49.93 | -26% | -2.75% | 0% | 10.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 9 | -171.58 | -3.29% | 0% |
| 3 h a 1 dia | 37 | 361.45 | 1.91% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (17): MFE mediano 6.7%, MAE mediano -0.8%, devolução média do melhor ponto 4.3%, captura mediana 0.65.
- Perdedores (29): MAE mediano -3.3%, MFE mediano 1.4%; 13 (45%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 78.02; 29% do lucro antes de custos.
- Trades < 3 h: 9 (lucro -171.58); reentradas em < 24 h: 4 (lucro 162.01).
- Maior trade = 116% do lucro; top 5 = 224%; top 10 = 298%; lucro sem o melhor = -30.16.
- Lucro por ano de fechamento: 2019: 193.7, 2020: -89.8, 2021: -36.1, 2022: 16.2, 2023: 97.5, 2024: 8.3.

## DOGE/USDT

Trades: 88; lucro líquido: -470.06.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 50 | -646.67 | – | -3.28% | 0% | 3.1 h |
| time_exit_utc_day_close | 29 | 277.79 | – | 2.18% | 59% | 13.7 h |
| close_below_jump_low | 9 | -101.18 | – | -2.54% | 0% | 4.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 35 | -443.20 | -3.26% | 0% |
| 3 h a 1 dia | 53 | -26.86 | -0.18% | 32% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (17): MFE mediano 8.9%, MAE mediano -1.2%, devolução média do melhor ponto 4.1%, captura mediana 0.48.
- Perdedores (71): MAE mediano -3.2%, MFE mediano 1.6%; 32 (45%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 105.78; – do lucro antes de custos.
- Trades < 3 h: 35 (lucro -443.20); reentradas em < 24 h: 8 (lucro -78.71).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -529.71.
- Lucro por ano de fechamento: 2019: -23.4, 2020: 64.6, 2021: -257.5, 2022: -124.8, 2023: -98.6, 2024: -30.5.

## SOL/USDT

Trades: 43; lucro líquido: 450.52.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 23 | 875.35 | 194% | 6.21% | 91% | 13.4 h |
| stop_loss | 17 | -369.74 | -82% | -3.28% | 0% | 5.3 h |
| close_below_jump_low | 3 | -55.09 | -12% | -2.52% | 0% | 6.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 9 | -193.65 | -3.22% | 0% |
| 3 h a 1 dia | 34 | 644.17 | 3.19% | 62% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (21): MFE mediano 8.4%, MAE mediano -1.0%, devolução média do melhor ponto 3.9%, captura mediana 0.61.
- Perdedores (22): MAE mediano -3.3%, MFE mediano 2.3%; 13 (59%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 85.32; 16% do lucro antes de custos.
- Trades < 3 h: 9 (lucro -193.65); reentradas em < 24 h: 6 (lucro 237.18).
- Maior trade = 31% do lucro; top 5 = 110%; top 10 = 162%; lucro sem o melhor = 311.75.
- Lucro por ano de fechamento: 2020: -16.5, 2021: 260.6, 2022: -28.7, 2023: 253.7, 2024: -18.6.
