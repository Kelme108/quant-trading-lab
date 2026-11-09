# Revisão de trades: H-061 (exploração)

Fonte dos trades: `research/experiments/20261109T192319Z-h-061-exploration-btc-usdt/raw/backtest-result-2026-11-09_19-35-43.zip`; `research/experiments/20261109T192319Z-h-061-exploration-eth-usdt/raw/backtest-result-2026-11-09_19-39-44.zip`; `research/experiments/20261109T192319Z-h-061-exploration-bnb-usdt/raw/backtest-result-2026-11-09_19-43-52.zip`; `research/experiments/20261109T192319Z-h-061-exploration-xrp-usdt/raw/backtest-result-2026-11-09_19-47-07.zip`; `research/experiments/20261109T192319Z-h-061-exploration-ada-usdt/raw/backtest-result-2026-11-09_19-50-15.zip`; `research/experiments/20261109T192319Z-h-061-exploration-ltc-usdt/raw/backtest-result-2026-11-09_19-53-27.zip`; `research/experiments/20261109T192319Z-h-061-exploration-link-usdt/raw/backtest-result-2026-11-09_19-56-37.zip`; `research/experiments/20261109T192319Z-h-061-exploration-doge-usdt/raw/backtest-result-2026-11-09_19-59-31.zip`; `research/experiments/20261109T192319Z-h-061-exploration-sol-usdt/raw/backtest-result-2026-11-09_20-02-16.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 665; lucro líquido: -141.64.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| pivot_target_or_structure_or_time | 613 | -61.25 | – | -0.22% | 37% | 4.8 h |
| stop_loss | 52 | -80.39 | – | -3.29% | 0% | 3.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 315 | -141.69 | -0.98% | 16% |
| 3 h a 1 dia | 350 | 0.05 | 0.01% | 50% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (225): MFE mediano 1.9%, MAE mediano -0.4%, devolução média do melhor ponto 0.9%, captura mediana 0.60.
- Perdedores (440): MAE mediano -1.5%, MFE mediano 0.5%; 24 (5%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 90.31; – do lucro antes de custos.
- Trades < 3 h: 315 (lucro -141.69); reentradas em < 24 h: 139 (lucro -38.70).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -146.43.
- Lucro por ano de fechamento: 2017: -9.0, 2018: -43.4, 2019: -25.3, 2020: -13.9, 2021: -27.2, 2022: -12.5, 2023: -6.0, 2024: -4.3.

## ETH/USDT

Trades: 753; lucro líquido: -93.64.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| pivot_target_or_structure_or_time | 680 | 22.50 | – | 0.07% | 37% | 5.0 h |
| stop_loss | 73 | -116.14 | – | -3.29% | 0% | 2.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 378 | -208.74 | -1.15% | 12% |
| 3 h a 1 dia | 375 | 115.10 | 0.64% | 55% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (253): MFE mediano 2.5%, MAE mediano -0.5%, devolução média do melhor ponto 1.0%, captura mediana 0.66.
- Perdedores (500): MAE mediano -1.7%, MFE mediano 0.5%; 34 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 107.05; 798% do lucro antes de custos.
- Trades < 3 h: 378 (lucro -208.74); reentradas em < 24 h: 143 (lucro -6.86).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -110.53.
- Lucro por ano de fechamento: 2017: 9.1, 2018: -38.8, 2019: -9.8, 2020: -23.0, 2021: -6.6, 2022: -7.1, 2023: -7.9, 2024: -9.6.

## BNB/USDT

Trades: 721; lucro líquido: -128.09.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| pivot_target_or_structure_or_time | 653 | -23.45 | – | -0.08% | 39% | 5.0 h |
| stop_loss | 68 | -104.63 | – | -3.29% | 0% | 2.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 352 | -194.77 | -1.20% | 15% |
| 3 h a 1 dia | 369 | 66.68 | 0.40% | 55% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (255): MFE mediano 2.2%, MAE mediano -0.4%, devolução média do melhor ponto 0.9%, captura mediana 0.67.
- Perdedores (466): MAE mediano -1.7%, MFE mediano 0.5%; 40 (9%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 98.46; – do lucro antes de custos.
- Trades < 3 h: 352 (lucro -194.77); reentradas em < 24 h: 134 (lucro -22.99).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -132.80.
- Lucro por ano de fechamento: 2017: -14.6, 2018: -41.1, 2019: -28.8, 2020: -2.1, 2021: -17.7, 2022: -11.3, 2023: -8.1, 2024: -4.4.

## XRP/USDT

Trades: 691; lucro líquido: -83.30.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| pivot_target_or_structure_or_time | 625 | 20.82 | – | 0.07% | 40% | 5.5 h |
| stop_loss | 66 | -104.12 | – | -3.29% | 0% | 2.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 310 | -174.30 | -1.17% | 14% |
| 3 h a 1 dia | 381 | 91.01 | 0.50% | 54% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (247): MFE mediano 2.2%, MAE mediano -0.4%, devolução média do melhor ponto 1.1%, captura mediana 0.63.
- Perdedores (444): MAE mediano -1.6%, MFE mediano 0.4%; 40 (9%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 98.99; 631% do lucro antes de custos.
- Trades < 3 h: 310 (lucro -174.30); reentradas em < 24 h: 153 (lucro 21.19).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -102.11.
- Lucro por ano de fechamento: 2018: -15.8, 2019: -25.6, 2020: 1.8, 2021: -12.8, 2022: -6.8, 2023: -15.5, 2024: -8.6.

## ADA/USDT

Trades: 726; lucro líquido: -119.46.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| pivot_target_or_structure_or_time | 659 | -14.80 | – | -0.05% | 34% | 4.8 h |
| stop_loss | 67 | -104.66 | – | -3.28% | 0% | 2.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 365 | -199.30 | -1.15% | 13% |
| 3 h a 1 dia | 361 | 79.84 | 0.46% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (225): MFE mediano 2.8%, MAE mediano -0.5%, devolução média do melhor ponto 1.0%, captura mediana 0.68.
- Perdedores (501): MAE mediano -1.6%, MFE mediano 0.6%; 49 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 102.46; – do lucro antes de custos.
- Trades < 3 h: 365 (lucro -199.30); reentradas em < 24 h: 152 (lucro -24.62).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -125.61.
- Lucro por ano de fechamento: 2018: -12.2, 2019: -23.0, 2020: -7.9, 2021: -24.3, 2022: -26.1, 2023: -5.7, 2024: -20.3.

## LTC/USDT

Trades: 751; lucro líquido: -96.08.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| pivot_target_or_structure_or_time | 661 | 44.60 | – | 0.14% | 43% | 5.6 h |
| stop_loss | 90 | -140.68 | – | -3.28% | 0% | 2.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 331 | -181.37 | -1.15% | 18% |
| 3 h a 1 dia | 420 | 85.29 | 0.43% | 54% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (286): MFE mediano 2.5%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.64.
- Perdedores (465): MAE mediano -1.8%, MFE mediano 0.6%; 51 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 106.17; 1052% do lucro antes de custos.
- Trades < 3 h: 331 (lucro -181.37); reentradas em < 24 h: 153 (lucro -8.50).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -101.95.
- Lucro por ano de fechamento: 2017: -1.8, 2018: -19.3, 2019: -8.4, 2020: -18.5, 2021: -28.5, 2022: -3.4, 2023: -8.1, 2024: -8.1.

## LINK/USDT

Trades: 629; lucro líquido: -143.57.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| pivot_target_or_structure_or_time | 550 | -22.55 | – | -0.09% | 34% | 4.5 h |
| stop_loss | 79 | -121.03 | – | -3.28% | 0% | 2.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 324 | -184.70 | -1.23% | 14% |
| 3 h a 1 dia | 305 | 41.12 | 0.30% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (185): MFE mediano 3.0%, MAE mediano -0.6%, devolução média do melhor ponto 1.2%, captura mediana 0.69.
- Perdedores (444): MAE mediano -2.0%, MFE mediano 0.7%; 55 (12%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 85.88; – do lucro antes de custos.
- Trades < 3 h: 324 (lucro -184.70); reentradas em < 24 h: 118 (lucro -34.76).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -148.44.
- Lucro por ano de fechamento: 2019: -42.7, 2020: -25.0, 2021: -34.8, 2022: -16.1, 2023: -12.1, 2024: -12.8.

## DOGE/USDT

Trades: 549; lucro líquido: -52.71.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| pivot_target_or_structure_or_time | 498 | 29.12 | – | 0.12% | 39% | 5.1 h |
| stop_loss | 51 | -81.84 | – | -3.28% | 0% | 3.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 246 | -132.68 | -1.10% | 15% |
| 3 h a 1 dia | 303 | 79.97 | 0.54% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (196): MFE mediano 2.3%, MAE mediano -0.4%, devolução média do melhor ponto 1.1%, captura mediana 0.65.
- Perdedores (353): MAE mediano -1.6%, MFE mediano 0.6%; 35 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 80.45; 290% do lucro antes de custos.
- Trades < 3 h: 246 (lucro -132.68); reentradas em < 24 h: 118 (lucro 6.01).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -71.03.
- Lucro por ano de fechamento: 2019: -5.1, 2020: -0.8, 2021: -18.8, 2022: -7.4, 2023: -3.6, 2024: -17.1.

## SOL/USDT

Trades: 451; lucro líquido: -83.64.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| pivot_target_or_structure_or_time | 389 | 15.20 | – | 0.08% | 31% | 4.5 h |
| stop_loss | 62 | -98.84 | – | -3.28% | 0% | 3.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 239 | -143.46 | -1.24% | 13% |
| 3 h a 1 dia | 212 | 59.82 | 0.58% | 43% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (121): MFE mediano 4.1%, MAE mediano -0.6%, devolução média do melhor ponto 1.4%, captura mediana 0.75.
- Perdedores (330): MAE mediano -2.1%, MFE mediano 0.7%; 54 (16%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 64.86; – do lucro antes de custos.
- Trades < 3 h: 239 (lucro -143.46); reentradas em < 24 h: 89 (lucro 1.59).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -91.79.
- Lucro por ano de fechamento: 2020: -32.4, 2021: 7.1, 2022: -21.9, 2023: -13.7, 2024: -22.7.
