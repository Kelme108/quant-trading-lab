# Revisão de trades: H-103 (exploração)

Fonte dos trades: `research/experiments/20261110T202254Z-h-103-exploration-btc-usdt/raw/backtest-result-2026-11-10_20-33-18.zip`; `research/experiments/20261110T202254Z-h-103-exploration-eth-usdt/raw/backtest-result-2026-11-10_20-37-58.zip`; `research/experiments/20261110T202254Z-h-103-exploration-bnb-usdt/raw/backtest-result-2026-11-10_20-42-17.zip`; `research/experiments/20261110T202254Z-h-103-exploration-xrp-usdt/raw/backtest-result-2026-11-10_20-46-06.zip`; `research/experiments/20261110T202254Z-h-103-exploration-ada-usdt/raw/backtest-result-2026-11-10_20-50-05.zip`; `research/experiments/20261110T202254Z-h-103-exploration-ltc-usdt/raw/backtest-result-2026-11-10_20-54-07.zip`; `research/experiments/20261110T202254Z-h-103-exploration-link-usdt/raw/backtest-result-2026-11-10_20-58-18.zip`; `research/experiments/20261110T202254Z-h-103-exploration-doge-usdt/raw/backtest-result-2026-11-10_21-02-05.zip`; `research/experiments/20261110T202254Z-h-103-exploration-sol-usdt/raw/backtest-result-2026-11-10_21-05-36.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 266; lucro líquido: 111.81.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24_bars | 202 | 359.06 | 321% | 1.67% | 63% | 24.0 h |
| stop_loss | 36 | -164.90 | -147% | -4.29% | 0% | 9.9 h |
| failure_below_day_open | 28 | -82.35 | -74% | -2.68% | 0% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 9 | -39.82 | -4.13% | 0% |
| 3 h a 1 dia | 53 | -201.18 | -3.52% | 0% |
| 1 a 7 dias | 204 | 352.82 | 1.63% | 62% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (127): MFE mediano 4.6%, MAE mediano -0.7%, devolução média do melhor ponto 2.5%, captura mediana 0.52.
- Perdedores (139): MAE mediano -2.9%, MFE mediano 1.0%; 31 (22%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 85.80; 43% do lucro antes de custos.
- Trades < 3 h: 9 (lucro -39.82); reentradas em < 24 h: 29 (lucro 22.46).
- Maior trade = 20% do lucro; top 5 = 69%; top 10 = 119%; lucro sem o melhor = 89.99.
- Lucro por ano de fechamento: 2017: 12.1, 2018: -5.1, 2019: 27.3, 2020: 60.0, 2021: 13.8, 2022: 9.4, 2023: -10.8, 2024: 5.1.

## ETH/USDT

Trades: 288; lucro líquido: 131.02.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24_bars | 209 | 459.66 | 351% | 2.11% | 67% | 24.0 h |
| stop_loss | 61 | -270.32 | -206% | -4.29% | 0% | 9.3 h |
| failure_below_day_open | 18 | -58.33 | -45% | -3.03% | 0% | 11.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 19 | -82.39 | -4.15% | 0% |
| 3 h a 1 dia | 59 | -241.99 | -3.95% | 0% |
| 1 a 7 dias | 210 | 455.40 | 2.08% | 67% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (140): MFE mediano 5.3%, MAE mediano -0.8%, devolução média do melhor ponto 2.7%, captura mediana 0.57.
- Perdedores (148): MAE mediano -3.7%, MFE mediano 1.4%; 47 (32%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 90.65; 41% do lucro antes de custos.
- Trades < 3 h: 19 (lucro -82.39); reentradas em < 24 h: 37 (lucro -21.26).
- Maior trade = 17% do lucro; top 5 = 55%; top 10 = 97%; lucro sem o melhor = 108.59.
- Lucro por ano de fechamento: 2017: -15.2, 2018: -16.2, 2019: 15.7, 2020: 49.5, 2021: 34.0, 2022: 71.6, 2023: -22.6, 2024: 14.2.

## BNB/USDT

Trades: 253; lucro líquido: 78.11.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24_bars | 170 | 406.24 | 520% | 2.34% | 67% | 24.0 h |
| stop_loss | 57 | -247.64 | -317% | -4.28% | 0% | 6.9 h |
| failure_below_day_open | 26 | -80.49 | -103% | -2.92% | 0% | 12.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 22 | -94.71 | -4.28% | 0% |
| 3 h a 1 dia | 57 | -221.72 | -3.77% | 0% |
| 1 a 7 dias | 174 | 394.55 | 2.23% | 66% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (114): MFE mediano 5.3%, MAE mediano -1.0%, devolução média do melhor ponto 3.1%, captura mediana 0.56.
- Perdedores (139): MAE mediano -3.8%, MFE mediano 1.3%; 43 (31%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 78.44; 50% do lucro antes de custos.
- Trades < 3 h: 22 (lucro -94.71); reentradas em < 24 h: 36 (lucro 33.05).
- Maior trade = 43% do lucro; top 5 = 138%; top 10 = 200%; lucro sem o melhor = 44.55.
- Lucro por ano de fechamento: 2017: -25.5, 2018: -35.0, 2019: 60.8, 2020: 0.8, 2021: 103.2, 2022: -2.2, 2023: -35.6, 2024: 11.6.

## XRP/USDT

Trades: 234; lucro líquido: 29.76.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24_bars | 131 | 455.03 | 1529% | 3.33% | 61% | 24.0 h |
| stop_loss | 77 | -350.84 | -1179% | -4.28% | 0% | 7.6 h |
| failure_below_day_open | 26 | -74.42 | -250% | -2.73% | 0% | 11.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 29 | -128.32 | -4.12% | 0% |
| 3 h a 1 dia | 71 | -288.26 | -3.84% | 0% |
| 1 a 7 dias | 134 | 446.34 | 3.19% | 60% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (80): MFE mediano 6.7%, MAE mediano -1.4%, devolução média do melhor ponto 4.7%, captura mediana 0.49.
- Perdedores (154): MAE mediano -4.1%, MFE mediano 1.1%; 51 (33%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 73.85; 71% do lucro antes de custos.
- Trades < 3 h: 29 (lucro -128.32); reentradas em < 24 h: 28 (lucro -15.41).
- Maior trade = 179% do lucro; top 5 = 645%; top 10 = 970%; lucro sem o melhor = -23.49.
- Lucro por ano de fechamento: 2018: 35.5, 2019: 6.7, 2020: 28.5, 2021: -2.9, 2022: -1.6, 2023: 0.3, 2024: -36.7.

## ADA/USDT

Trades: 248; lucro líquido: 9.43.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24_bars | 147 | 429.45 | 4553% | 2.87% | 67% | 24.0 h |
| stop_loss | 83 | -364.00 | -3859% | -4.28% | 0% | 9.1 h |
| failure_below_day_open | 18 | -56.02 | -594% | -2.99% | 0% | 9.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 19 | -79.98 | -4.10% | 0% |
| 3 h a 1 dia | 82 | -340.04 | -4.04% | 0% |
| 1 a 7 dias | 147 | 429.45 | 2.87% | 67% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (98): MFE mediano 7.7%, MAE mediano -1.0%, devolução média do melhor ponto 4.0%, captura mediana 0.50.
- Perdedores (150): MAE mediano -4.1%, MFE mediano 1.5%; 55 (37%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 76.12; 89% do lucro antes de custos.
- Trades < 3 h: 19 (lucro -79.98); reentradas em < 24 h: 26 (lucro 33.89).
- Maior trade = 243% do lucro; top 5 = 930%; top 10 = 1611%; lucro sem o melhor = -13.48.
- Lucro por ano de fechamento: 2018: 10.3, 2019: -41.0, 2020: 61.7, 2021: 44.7, 2022: -26.1, 2023: -10.6, 2024: -29.6.

## LTC/USDT

Trades: 301; lucro líquido: -24.26.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24_bars | 181 | 474.27 | – | 2.57% | 69% | 24.0 h |
| stop_loss | 97 | -427.11 | – | -4.28% | 0% | 9.8 h |
| failure_below_day_open | 23 | -71.42 | – | -3.06% | 0% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 20 | -88.09 | -4.28% | 0% |
| 3 h a 1 dia | 100 | -410.44 | -4.00% | 0% |
| 1 a 7 dias | 181 | 474.27 | 2.57% | 69% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (125): MFE mediano 5.8%, MAE mediano -1.0%, devolução média do melhor ponto 3.3%, captura mediana 0.49.
- Perdedores (176): MAE mediano -4.2%, MFE mediano 1.3%; 60 (34%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 92.25; 136% do lucro antes de custos.
- Trades < 3 h: 20 (lucro -88.09); reentradas em < 24 h: 42 (lucro -69.77).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -56.61.
- Lucro por ano de fechamento: 2018: -2.4, 2019: 45.0, 2020: 6.1, 2021: -29.6, 2022: -14.6, 2023: -5.2, 2024: -23.5.

## LINK/USDT

Trades: 245; lucro líquido: -19.41.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24_bars | 134 | 462.08 | – | 3.36% | 72% | 24.0 h |
| stop_loss | 102 | -451.82 | – | -4.28% | 0% | 8.9 h |
| failure_below_day_open | 9 | -29.67 | – | -3.26% | 0% | 15.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 21 | -90.91 | -4.23% | 0% |
| 3 h a 1 dia | 89 | -388.96 | -4.22% | 0% |
| 1 a 7 dias | 135 | 460.47 | 3.32% | 72% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (97): MFE mediano 7.1%, MAE mediano -1.3%, devolução média do melhor ponto 3.5%, captura mediana 0.57.
- Perdedores (148): MAE mediano -4.5%, MFE mediano 1.6%; 60 (41%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 75.68; 134% do lucro antes de custos.
- Trades < 3 h: 21 (lucro -90.91); reentradas em < 24 h: 38 (lucro 41.42).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -75.63.
- Lucro por ano de fechamento: 2019: 13.8, 2020: 53.0, 2021: 1.6, 2022: -38.0, 2023: -33.6, 2024: -16.2.

## DOGE/USDT

Trades: 220; lucro líquido: -121.73.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24_bars | 103 | 330.08 | – | 3.38% | 70% | 24.0 h |
| stop_loss | 100 | -408.96 | – | -4.28% | 0% | 7.0 h |
| failure_below_day_open | 17 | -42.85 | – | -2.69% | 0% | 8.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 43 | -171.13 | -4.14% | 0% |
| 3 h a 1 dia | 74 | -280.67 | -4.00% | 0% |
| 1 a 7 dias | 103 | 330.08 | 3.38% | 70% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (72): MFE mediano 7.4%, MAE mediano -1.3%, devolução média do melhor ponto 4.6%, captura mediana 0.50.
- Perdedores (148): MAE mediano -4.5%, MFE mediano 1.6%; 66 (45%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 62.50; – do lucro antes de custos.
- Trades < 3 h: 43 (lucro -171.13); reentradas em < 24 h: 36 (lucro -51.80).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -163.28.
- Lucro por ano de fechamento: 2019: 9.3, 2020: -20.1, 2021: -41.4, 2022: 9.9, 2023: -84.4, 2024: 4.9.

## SOL/USDT

Trades: 175; lucro líquido: -4.48.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24_bars | 90 | 346.54 | – | 3.98% | 74% | 24.0 h |
| stop_loss | 82 | -342.41 | – | -4.28% | 0% | 8.1 h |
| failure_below_day_open | 3 | -8.61 | – | -2.90% | 0% | 3.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 27 | -111.07 | -4.23% | 0% |
| 3 h a 1 dia | 58 | -239.95 | -4.23% | 0% |
| 1 a 7 dias | 90 | 346.54 | 3.98% | 74% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (67): MFE mediano 8.3%, MAE mediano -1.5%, devolução média do melhor ponto 4.0%, captura mediana 0.59.
- Perdedores (108): MAE mediano -4.4%, MFE mediano 2.1%; 58 (54%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 51.25; 110% do lucro antes de custos.
- Trades < 3 h: 27 (lucro -111.07); reentradas em < 24 h: 27 (lucro 17.73).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -33.62.
- Lucro por ano de fechamento: 2020: -48.3, 2021: 39.8, 2022: -15.0, 2023: 18.8, 2024: 0.2.
