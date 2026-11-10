# Revisão de trades: H-101 (exploração)

Fonte dos trades: `research/experiments/20261110T183600Z-h-101-exploration-btc-usdt/raw/backtest-result-2026-11-10_18-45-40.zip`; `research/experiments/20261110T183600Z-h-101-exploration-eth-usdt/raw/backtest-result-2026-11-10_18-48-51.zip`; `research/experiments/20261110T183600Z-h-101-exploration-bnb-usdt/raw/backtest-result-2026-11-10_18-51-51.zip`; `research/experiments/20261110T183600Z-h-101-exploration-xrp-usdt/raw/backtest-result-2026-11-10_18-54-40.zip`; `research/experiments/20261110T183600Z-h-101-exploration-ada-usdt/raw/backtest-result-2026-11-10_18-57-24.zip`; `research/experiments/20261110T183600Z-h-101-exploration-ltc-usdt/raw/backtest-result-2026-11-10_18-59-57.zip`; `research/experiments/20261110T183600Z-h-101-exploration-link-usdt/raw/backtest-result-2026-11-10_19-02-30.zip`; `research/experiments/20261110T183600Z-h-101-exploration-doge-usdt/raw/backtest-result-2026-11-10_19-05-01.zip`; `research/experiments/20261110T183600Z-h-101-exploration-sol-usdt/raw/backtest-result-2026-11-10_19-07-37.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 109; lucro líquido: 58.59.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 67 | 308.67 | 527% | 1.50% | 72% | 24.0 h |
| kijun_exit | 29 | -117.17 | -200% | -1.29% | 10% | 10.0 h |
| stop_loss | 13 | -132.91 | -227% | -3.29% | 0% | 10.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 11 | -44.62 | -1.30% | 9% |
| 3 h a 1 dia | 30 | -199.41 | -2.13% | 7% |
| 1 a 7 dias | 68 | 302.62 | 1.45% | 71% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (51): MFE mediano 3.7%, MAE mediano -0.5%, devolução média do melhor ponto 2.5%, captura mediana 0.42.
- Perdedores (58): MAE mediano -1.9%, MFE mediano 0.9%; 9 (16%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 101.32; 63% do lucro antes de custos.
- Trades < 3 h: 11 (lucro -44.62); reentradas em < 24 h: 1 (lucro -3.82).
- Maior trade = 77% do lucro; top 5 = 236%; top 10 = 361%; lucro sem o melhor = 13.37.
- Lucro por ano de fechamento: 2018: -15.0, 2019: 67.5, 2020: -9.0, 2021: -18.6, 2022: 0.8, 2023: -6.1, 2024: 39.0.

## ETH/USDT

Trades: 124; lucro líquido: 466.91.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 80 | 822.26 | 176% | 2.77% | 78% | 24.0 h |
| kijun_exit | 29 | -164.83 | -35% | -1.44% | 3% | 13.2 h |
| stop_loss | 15 | -190.53 | -41% | -3.29% | 0% | 12.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 4 | -28.13 | -2.24% | 0% |
| 3 h a 1 dia | 38 | -307.30 | -2.03% | 3% |
| 1 a 7 dias | 82 | 802.35 | 2.65% | 76% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (63): MFE mediano 4.7%, MAE mediano -0.8%, devolução média do melhor ponto 2.6%, captura mediana 0.51.
- Perdedores (61): MAE mediano -2.2%, MFE mediano 1.2%; 15 (25%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 146.00; 24% do lucro antes de custos.
- Trades < 3 h: 4 (lucro -28.13); reentradas em < 24 h: 5 (lucro 2.58).
- Maior trade = 17% do lucro; top 5 = 54%; top 10 = 90%; lucro sem o melhor = 389.55.
- Lucro por ano de fechamento: 2017: -9.5, 2018: 27.9, 2019: 117.6, 2020: 182.2, 2021: 65.3, 2022: 82.5, 2023: -2.7, 2024: 3.6.

## BNB/USDT

Trades: 131; lucro líquido: 15.42.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 65 | 520.74 | 3376% | 2.73% | 75% | 24.0 h |
| stop_loss | 36 | -351.86 | -2281% | -3.29% | 0% | 6.1 h |
| kijun_exit | 30 | -153.45 | -995% | -1.72% | 0% | 10.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 21 | -175.67 | -2.79% | 0% |
| 3 h a 1 dia | 45 | -329.64 | -2.47% | 0% |
| 1 a 7 dias | 65 | 520.74 | 2.73% | 75% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (49): MFE mediano 4.7%, MAE mediano -0.7%, devolução média do melhor ponto 2.4%, captura mediana 0.59.
- Perdedores (82): MAE mediano -3.0%, MFE mediano 1.2%; 24 (29%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 116.45; 88% do lucro antes de custos.
- Trades < 3 h: 21 (lucro -175.67); reentradas em < 24 h: 2 (lucro -9.46).
- Maior trade = 236% do lucro; top 5 = 1046%; top 10 = 1849%; lucro sem o melhor = -20.99.
- Lucro por ano de fechamento: 2017: -29.4, 2018: 0.0, 2019: -23.9, 2020: 83.4, 2021: -68.7, 2022: 29.8, 2023: 40.7, 2024: -16.6.

## XRP/USDT

Trades: 135; lucro líquido: -37.22.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 65 | 452.79 | – | 2.47% | 75% | 24.0 h |
| stop_loss | 35 | -331.32 | – | -3.29% | 0% | 6.9 h |
| kijun_exit | 35 | -158.69 | – | -1.57% | 9% | 8.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 18 | -138.66 | -2.69% | 0% |
| 3 h a 1 dia | 52 | -351.36 | -2.34% | 6% |
| 1 a 7 dias | 65 | 452.79 | 2.47% | 75% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (52): MFE mediano 5.8%, MAE mediano -0.8%, devolução média do melhor ponto 4.0%, captura mediana 0.38.
- Perdedores (83): MAE mediano -2.8%, MFE mediano 1.2%; 27 (33%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 115.98; 147% do lucro antes de custos.
- Trades < 3 h: 18 (lucro -138.66); reentradas em < 24 h: 4 (lucro -25.60).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -123.83.
- Lucro por ano de fechamento: 2018: 4.3, 2019: -66.9, 2020: 41.2, 2021: -66.7, 2022: 33.7, 2023: 76.9, 2024: -59.7.

## ADA/USDT

Trades: 121; lucro líquido: 112.06.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 61 | 637.38 | 569% | 3.19% | 69% | 24.0 h |
| stop_loss | 36 | -397.10 | -354% | -3.28% | 0% | 8.5 h |
| kijun_exit | 24 | -128.21 | -114% | -1.58% | 0% | 11.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 13 | -129.87 | -2.92% | 0% |
| 3 h a 1 dia | 45 | -389.60 | -2.58% | 0% |
| 1 a 7 dias | 63 | 631.53 | 3.06% | 67% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (42): MFE mediano 6.9%, MAE mediano -1.1%, devolução média do melhor ponto 3.8%, captura mediana 0.62.
- Perdedores (79): MAE mediano -3.0%, MFE mediano 1.2%; 28 (35%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 119.79; 52% do lucro antes de custos.
- Trades < 3 h: 13 (lucro -129.87); reentradas em < 24 h: 7 (lucro -21.72).
- Maior trade = 57% do lucro; top 5 = 204%; top 10 = 330%; lucro sem o melhor = 48.08.
- Lucro por ano de fechamento: 2018: -51.7, 2019: 55.0, 2020: 146.7, 2021: 37.6, 2022: -41.1, 2023: -14.1, 2024: -20.3.

## LTC/USDT

Trades: 148; lucro líquido: 163.64.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 69 | 804.92 | 492% | 3.64% | 77% | 24.0 h |
| stop_loss | 51 | -545.37 | -333% | -3.28% | 0% | 6.9 h |
| kijun_exit | 28 | -95.91 | -59% | -1.03% | 21% | 12.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 19 | -196.28 | -3.20% | 0% |
| 3 h a 1 dia | 58 | -462.02 | -2.43% | 9% |
| 1 a 7 dias | 71 | 821.94 | 3.62% | 76% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (59): MFE mediano 6.5%, MAE mediano -0.8%, devolução média do melhor ponto 3.6%, captura mediana 0.55.
- Perdedores (89): MAE mediano -3.2%, MFE mediano 1.2%; 20 (22%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 144.96; 47% do lucro antes de custos.
- Trades < 3 h: 19 (lucro -196.28); reentradas em < 24 h: 9 (lucro 26.22).
- Maior trade = 42% do lucro; top 5 = 156%; top 10 = 251%; lucro sem o melhor = 94.63.
- Lucro por ano de fechamento: 2018: -99.7, 2019: 84.4, 2020: 164.8, 2021: -15.3, 2022: 13.2, 2023: 59.0, 2024: -42.7.

## LINK/USDT

Trades: 128; lucro líquido: 565.59.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 65 | 1362.55 | 241% | 5.46% | 89% | 24.0 h |
| stop_loss | 56 | -758.51 | -134% | -3.28% | 0% | 8.2 h |
| kijun_exit | 7 | -38.45 | -7% | -1.44% | 0% | 9.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 11 | -132.76 | -3.29% | 0% |
| 3 h a 1 dia | 52 | -664.20 | -3.04% | 0% |
| 1 a 7 dias | 65 | 1362.55 | 5.46% | 89% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (58): MFE mediano 7.5%, MAE mediano -1.0%, devolução média do melhor ponto 3.2%, captura mediana 0.64.
- Perdedores (70): MAE mediano -3.4%, MFE mediano 1.8%; 29 (41%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 159.98; 22% do lucro antes de custos.
- Trades < 3 h: 11 (lucro -132.76); reentradas em < 24 h: 4 (lucro 49.01).
- Maior trade = 40% do lucro; top 5 = 80%; top 10 = 112%; lucro sem o melhor = 341.14.
- Lucro por ano de fechamento: 2019: 234.9, 2020: 234.7, 2021: 0.2, 2022: 18.4, 2023: 32.2, 2024: 45.1.

## DOGE/USDT

Trades: 124; lucro líquido: -180.02.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 46 | -406.17 | – | -3.28% | 0% | 5.3 h |
| time_exit_24h | 42 | 380.31 | – | 3.44% | 71% | 24.0 h |
| kijun_exit | 36 | -154.16 | – | -1.57% | 6% | 9.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 33 | -259.06 | -2.85% | 0% |
| 3 h a 1 dia | 47 | -293.54 | -2.35% | 4% |
| 1 a 7 dias | 44 | 372.57 | 3.23% | 68% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (32): MFE mediano 7.9%, MAE mediano -0.9%, devolução média do melhor ponto 4.0%, captura mediana 0.47.
- Perdedores (92): MAE mediano -3.1%, MFE mediano 1.2%; 24 (26%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 100.77; – do lucro antes de custos.
- Trades < 3 h: 33 (lucro -259.06); reentradas em < 24 h: 2 (lucro -9.74).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -225.69.
- Lucro por ano de fechamento: 2019: 27.4, 2020: -15.5, 2021: -115.3, 2022: -105.0, 2023: -54.2, 2024: 82.5.

## SOL/USDT

Trades: 83; lucro líquido: 54.79.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 46 | -491.63 | -897% | -3.28% | 0% | 5.0 h |
| time_exit_24h | 26 | 604.75 | 1104% | 7.42% | 88% | 24.0 h |
| kijun_exit | 11 | -58.33 | -106% | -1.64% | 9% | 13.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 23 | -236.12 | -3.16% | 0% |
| 3 h a 1 dia | 34 | -313.83 | -2.83% | 3% |
| 1 a 7 dias | 26 | 604.75 | 7.42% | 88% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (24): MFE mediano 9.7%, MAE mediano -1.1%, devolução média do melhor ponto 5.1%, captura mediana 0.64.
- Perdedores (59): MAE mediano -3.6%, MFE mediano 1.7%; 26 (44%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 80.51; 60% do lucro antes de custos.
- Trades < 3 h: 23 (lucro -236.12); reentradas em < 24 h: 7 (lucro -37.56).
- Maior trade = 237% do lucro; top 5 = 625%; top 10 = 863%; lucro sem o melhor = -75.17.
- Lucro por ano de fechamento: 2020: 76.7, 2021: 62.4, 2022: -51.9, 2023: -53.9, 2024: 21.6.
