# Revisão de trades: H-139 (exploração)

Fonte dos trades: `research/experiments/20261114T064922Z-h-139-exploration-btc-usdt/raw/backtest-result-2026-11-14_07-02-08.zip`; `research/experiments/20261114T064922Z-h-139-exploration-eth-usdt/raw/backtest-result-2026-11-14_07-02-09.zip`; `research/experiments/20261114T064922Z-h-139-exploration-bnb-usdt/raw/backtest-result-2026-11-14_07-02-08.zip`; `research/experiments/20261114T064922Z-h-139-exploration-xrp-usdt/raw/backtest-result-2026-11-14_07-07-39.zip`; `research/experiments/20261114T064922Z-h-139-exploration-ada-usdt/raw/backtest-result-2026-11-14_07-07-42.zip`; `research/experiments/20261114T064922Z-h-139-exploration-ltc-usdt/raw/backtest-result-2026-11-14_07-07-43.zip`; `research/experiments/20261114T064922Z-h-139-exploration-link-usdt/raw/backtest-result-2026-11-14_07-13-15.zip`; `research/experiments/20261114T064922Z-h-139-exploration-doge-usdt/raw/backtest-result-2026-11-14_07-13-28.zip`; `research/experiments/20261114T064922Z-h-139-exploration-sol-usdt/raw/backtest-result-2026-11-14_07-13-24.zip`; `research/experiments/20261114T064922Z-h-139-exploration-avax-usdt/raw/backtest-result-2026-11-14_07-18-28.zip`; `research/experiments/20261114T064922Z-h-139-exploration-dot-usdt/raw/backtest-result-2026-11-14_07-18-38.zip`; `research/experiments/20261114T064922Z-h-139-exploration-trx-usdt/raw/backtest-result-2026-11-14_07-19-05.zip`; `research/experiments/20261114T064922Z-h-139-exploration-near-usdt/raw/backtest-result-2026-11-14_07-24-02.zip`; `research/experiments/20261114T064922Z-h-139-exploration-uni-usdt/raw/backtest-result-2026-11-14_07-24-06.zip`; `research/experiments/20261114T064922Z-h-139-exploration-bch-usdt/raw/backtest-result-2026-11-14_07-24-30.zip`; `research/experiments/20261114T064922Z-h-139-exploration-xlm-usdt/raw/backtest-result-2026-11-14_07-29-31.zip`; `research/experiments/20261114T064922Z-h-139-exploration-fil-usdt/raw/backtest-result-2026-11-14_07-29-29.zip`; `research/experiments/20261114T064922Z-h-139-exploration-aave-usdt/raw/backtest-result-2026-11-14_07-29-58.zip`; `research/experiments/20261114T064922Z-h-139-exploration-inj-usdt/raw/backtest-result-2026-11-14_07-34-39.zip`; `research/experiments/20261114T064922Z-h-139-exploration-hbar-usdt/raw/backtest-result-2026-11-14_07-35-07.zip`; `research/experiments/20261114T064922Z-h-139-exploration-op-usdt/raw/backtest-result-2026-11-14_07-35-01.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 231; lucro líquido: 120.15.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 124 | 116.09 | 97% | 0.59% | 53% | 8.8 h |
| time_exit_12h | 98 | 78.62 | 65% | 0.51% | 53% | 12.0 h |
| stop_loss | 9 | -74.56 | -62% | -5.28% | 0% | 5.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 3 | -24.50 | -5.28% | 0% |
| 3 h a 1 dia | 228 | 144.65 | 0.41% | 52% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (118): MFE mediano 3.1%, MAE mediano -0.7%, devolução média do melhor ponto 1.7%, captura mediana 0.49.
- Perdedores (113): MAE mediano -1.7%, MFE mediano 0.8%; 18 (16%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 109.88; 48% do lucro antes de custos.
- Trades < 3 h: 3 (lucro -24.50); reentradas em < 24 h: 30 (lucro -8.74).
- Maior trade = 11% do lucro; top 5 = 48%; top 10 = 82%; lucro sem o melhor = 107.36.
- Lucro por ano de fechamento: 2017: -6.7, 2018: 7.3, 2019: 36.3, 2020: 34.6, 2021: 3.1, 2022: 15.0, 2023: 13.9, 2024: 16.7.

## ETH/USDT

Trades: 231; lucro líquido: 271.56.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 119 | 182.57 | 67% | 0.90% | 61% | 9.0 h |
| time_exit_12h | 97 | 227.89 | 84% | 1.38% | 64% | 12.0 h |
| stop_loss | 15 | -138.90 | -51% | -5.28% | 0% | 3.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 5 | -43.18 | -5.28% | 0% |
| 3 h a 1 dia | 226 | 314.74 | 0.83% | 59% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (134): MFE mediano 3.5%, MAE mediano -0.7%, devolução média do melhor ponto 2.0%, captura mediana 0.54.
- Perdedores (97): MAE mediano -2.4%, MFE mediano 1.0%; 17 (18%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 122.27; 31% do lucro antes de custos.
- Trades < 3 h: 5 (lucro -43.18); reentradas em < 24 h: 25 (lucro 49.64).
- Maior trade = 10% do lucro; top 5 = 32%; top 10 = 54%; lucro sem o melhor = 243.92.
- Lucro por ano de fechamento: 2017: 1.5, 2018: 13.8, 2019: 70.2, 2020: 105.5, 2021: 88.4, 2022: -6.9, 2023: 0.3, 2024: -1.3.

## BNB/USDT

Trades: 258; lucro líquido: 185.37.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 127 | 207.22 | 112% | 1.00% | 63% | 9.1 h |
| time_exit_12h | 105 | 211.73 | 114% | 1.22% | 56% | 12.0 h |
| stop_loss | 26 | -233.58 | -126% | -5.28% | 0% | 4.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 9 | -76.91 | -5.28% | 0% |
| 3 h a 1 dia | 249 | 262.28 | 0.66% | 56% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (139): MFE mediano 3.5%, MAE mediano -1.0%, devolução média do melhor ponto 2.6%, captura mediana 0.46.
- Perdedores (119): MAE mediano -3.0%, MFE mediano 0.9%; 17 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 134.88; 42% do lucro antes de custos.
- Trades < 3 h: 9 (lucro -76.91); reentradas em < 24 h: 29 (lucro 5.75).
- Maior trade = 30% do lucro; top 5 = 92%; top 10 = 139%; lucro sem o melhor = 128.85.
- Lucro por ano de fechamento: 2017: 3.7, 2018: 104.5, 2019: 35.1, 2020: -3.7, 2021: 86.6, 2022: -26.8, 2023: -15.7, 2024: 1.8.

## XRP/USDT

Trades: 204; lucro líquido: 134.36.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 92 | 172.83 | 129% | 1.16% | 47% | 8.8 h |
| time_exit_12h | 80 | 248.02 | 185% | 1.89% | 56% | 12.0 h |
| stop_loss | 32 | -286.49 | -213% | -5.28% | 0% | 3.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 14 | -125.91 | -5.28% | 0% |
| 3 h a 1 dia | 190 | 260.27 | 0.85% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (88): MFE mediano 5.0%, MAE mediano -1.3%, devolução média do melhor ponto 3.7%, captura mediana 0.42.
- Perdedores (116): MAE mediano -3.2%, MFE mediano 0.9%; 23 (20%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 102.32; 43% do lucro antes de custos.
- Trades < 3 h: 14 (lucro -125.91); reentradas em < 24 h: 21 (lucro 7.62).
- Maior trade = 46% do lucro; top 5 = 141%; top 10 = 217%; lucro sem o melhor = 72.89.
- Lucro por ano de fechamento: 2018: 62.4, 2019: 38.8, 2020: 56.6, 2021: -33.8, 2022: -2.3, 2023: 14.2, 2024: -1.5.

## ADA/USDT

Trades: 229; lucro líquido: -17.16.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 109 | 185.90 | – | 1.10% | 55% | 9.0 h |
| time_exit_12h | 82 | 110.64 | – | 0.87% | 59% | 12.0 h |
| stop_loss | 38 | -313.70 | – | -5.28% | 0% | 4.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 15 | -124.79 | -5.28% | 0% |
| 3 h a 1 dia | 214 | 107.63 | 0.33% | 50% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (108): MFE mediano 4.1%, MAE mediano -0.9%, devolução média do melhor ponto 2.6%, captura mediana 0.47.
- Perdedores (121): MAE mediano -3.5%, MFE mediano 1.1%; 33 (27%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 105.99; 119% do lucro antes de custos.
- Trades < 3 h: 15 (lucro -124.79); reentradas em < 24 h: 35 (lucro -53.72).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -38.38.
- Lucro por ano de fechamento: 2018: -12.3, 2019: 28.6, 2020: 71.4, 2021: -64.7, 2022: 5.2, 2023: -42.6, 2024: -2.7.

## LTC/USDT

Trades: 226; lucro líquido: 166.41.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 111 | 169.07 | 102% | 0.89% | 59% | 8.7 h |
| time_exit_12h | 99 | 144.91 | 87% | 0.91% | 49% | 12.0 h |
| stop_loss | 16 | -147.57 | -89% | -5.28% | 0% | 4.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 4 | -36.00 | -5.28% | 0% |
| 3 h a 1 dia | 222 | 202.41 | 0.57% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (114): MFE mediano 3.7%, MAE mediano -0.9%, devolução média do melhor ponto 2.3%, captura mediana 0.42.
- Perdedores (112): MAE mediano -2.5%, MFE mediano 1.2%; 32 (29%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 117.16; 41% do lucro antes de custos.
- Trades < 3 h: 4 (lucro -36.00); reentradas em < 24 h: 27 (lucro -0.17).
- Maior trade = 21% do lucro; top 5 = 66%; top 10 = 106%; lucro sem o melhor = 131.92.
- Lucro por ano de fechamento: 2018: 46.4, 2019: 67.6, 2020: 69.5, 2021: 29.4, 2022: -8.7, 2023: -39.3, 2024: 1.5.

## LINK/USDT

Trades: 210; lucro líquido: -69.52.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 107 | 143.49 | – | 0.89% | 53% | 8.8 h |
| time_exit_12h | 64 | 93.58 | – | 1.01% | 56% | 12.0 h |
| stop_loss | 39 | -306.59 | – | -5.28% | 0% | 3.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 19 | -150.46 | -5.28% | 0% |
| 3 h a 1 dia | 191 | 80.93 | 0.29% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (93): MFE mediano 4.5%, MAE mediano -1.2%, devolução média do melhor ponto 2.5%, captura mediana 0.50.
- Perdedores (117): MAE mediano -3.8%, MFE mediano 1.2%; 38 (32%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 92.73; 400% do lucro antes de custos.
- Trades < 3 h: 19 (lucro -150.46); reentradas em < 24 h: 32 (lucro -31.75).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -96.62.
- Lucro por ano de fechamento: 2019: -14.3, 2020: 33.2, 2021: -23.4, 2022: -42.4, 2023: 11.2, 2024: -33.8.

## DOGE/USDT

Trades: 189; lucro líquido: 18.97.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 80 | 401.62 | 2117% | 3.09% | 55% | 12.0 h |
| day_end | 61 | 53.90 | 284% | 0.48% | 44% | 9.2 h |
| stop_loss | 48 | -436.56 | -2302% | -5.28% | 0% | 2.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 25 | -227.41 | -5.28% | 0% |
| 3 h a 1 dia | 164 | 246.38 | 0.95% | 43% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (71): MFE mediano 5.3%, MAE mediano -1.1%, devolução média do melhor ponto 5.7%, captura mediana 0.39.
- Perdedores (118): MAE mediano -4.0%, MFE mediano 0.9%; 27 (23%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 94.27; 83% do lucro antes de custos.
- Trades < 3 h: 25 (lucro -227.41); reentradas em < 24 h: 27 (lucro 6.42).
- Maior trade = 885% do lucro; top 5 = 1638%; top 10 = 2121%; lucro sem o melhor = -148.86.
- Lucro por ano de fechamento: 2019: 5.7, 2020: 36.5, 2021: 148.6, 2022: 1.0, 2023: -137.5, 2024: -35.4.

## SOL/USDT

Trades: 152; lucro líquido: -81.12.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 64 | 75.12 | – | 0.86% | 58% | 8.7 h |
| time_exit_12h | 51 | 121.38 | – | 1.69% | 51% | 12.0 h |
| stop_loss | 37 | -277.62 | – | -5.28% | 0% | 3.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 15 | -113.53 | -5.28% | 0% |
| 3 h a 1 dia | 137 | 32.41 | 0.18% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (63): MFE mediano 5.5%, MAE mediano -1.3%, devolução média do melhor ponto 4.0%, captura mediana 0.49.
- Perdedores (89): MAE mediano -4.6%, MFE mediano 1.6%; 39 (44%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 63.72; – do lucro antes de custos.
- Trades < 3 h: 15 (lucro -113.53); reentradas em < 24 h: 30 (lucro 13.29).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -101.41.
- Lucro por ano de fechamento: 2020: -37.8, 2021: -34.9, 2022: -12.4, 2023: 28.4, 2024: -24.5.

## AVAX/USDT

Trades: 148; lucro líquido: -224.81.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 55 | 45.86 | – | 0.68% | 51% | 9.0 h |
| time_exit_12h | 48 | 42.27 | – | 0.67% | 52% | 12.0 h |
| stop_loss | 45 | -312.94 | – | -5.28% | 0% | 4.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 20 | -139.66 | -5.28% | 0% |
| 3 h a 1 dia | 128 | -85.15 | -0.49% | 41% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (53): MFE mediano 4.9%, MAE mediano -1.4%, devolução média do melhor ponto 2.9%, captura mediana 0.39.
- Perdedores (95): MAE mediano -5.0%, MFE mediano 1.1%; 32 (34%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 56.39; – do lucro antes de custos.
- Trades < 3 h: 20 (lucro -139.66); reentradas em < 24 h: 15 (lucro -44.13).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -249.02.
- Lucro por ano de fechamento: 2020: -54.6, 2021: -90.7, 2022: -49.0, 2023: -42.0, 2024: 11.5.

## DOT/USDT

Trades: 137; lucro líquido: 16.08.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 75 | 73.73 | 459% | 0.65% | 51% | 8.7 h |
| time_exit_12h | 45 | 79.54 | 495% | 1.17% | 49% | 12.0 h |
| stop_loss | 17 | -137.19 | -853% | -5.27% | 0% | 3.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 7 | -56.79 | -5.27% | 0% |
| 3 h a 1 dia | 130 | 72.87 | 0.38% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (60): MFE mediano 4.2%, MAE mediano -0.9%, devolução média do melhor ponto 2.6%, captura mediana 0.48.
- Perdedores (77): MAE mediano -2.9%, MFE mediano 1.0%; 16 (21%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 62.87; 80% do lucro antes de custos.
- Trades < 3 h: 7 (lucro -56.79); reentradas em < 24 h: 15 (lucro -20.10).
- Maior trade = 120% do lucro; top 5 = 533%; top 10 = 900%; lucro sem o melhor = -3.24.
- Lucro por ano de fechamento: 2020: 9.8, 2021: 48.3, 2022: -34.5, 2023: -15.8, 2024: 8.2.

## TRX/USDT

Trades: 252; lucro líquido: -77.77.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 116 | 67.65 | – | 0.38% | 47% | 9.5 h |
| time_exit_12h | 107 | 82.65 | – | 0.52% | 51% | 12.0 h |
| stop_loss | 28 | -222.58 | – | -5.27% | 0% | 3.9 h |
| close_below_lower | 1 | -5.50 | – | -3.96% | 0% | 7.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 11 | -87.01 | -5.27% | 0% |
| 3 h a 1 dia | 241 | 9.23 | 0.02% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (110): MFE mediano 4.4%, MAE mediano -1.0%, devolução média do melhor ponto 3.0%, captura mediana 0.41.
- Perdedores (142): MAE mediano -2.4%, MFE mediano 0.8%; 28 (20%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 111.51; 330% do lucro antes de custos.
- Trades < 3 h: 11 (lucro -87.01); reentradas em < 24 h: 45 (lucro -49.55).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -97.96.
- Lucro por ano de fechamento: 2018: 2.1, 2019: 21.3, 2020: -6.9, 2021: -2.2, 2022: -81.1, 2023: -9.5, 2024: -1.4.

## NEAR/USDT

Trades: 170; lucro líquido: -66.27.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 64 | 129.63 | – | 1.48% | 55% | 8.5 h |
| time_exit_12h | 56 | 177.73 | – | 2.26% | 54% | 12.0 h |
| stop_loss | 50 | -373.64 | – | -5.28% | 0% | 3.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 17 | -127.81 | -5.28% | 0% |
| 3 h a 1 dia | 153 | 61.53 | 0.31% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (65): MFE mediano 5.8%, MAE mediano -1.1%, devolução média do melhor ponto 3.1%, captura mediana 0.55.
- Perdedores (105): MAE mediano -4.9%, MFE mediano 1.6%; 45 (43%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 71.19; 1448% do lucro antes de custos.
- Trades < 3 h: 17 (lucro -127.81); reentradas em < 24 h: 23 (lucro -46.74).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -105.70.
- Lucro por ano de fechamento: 2020: 10.5, 2021: -70.9, 2022: -12.6, 2023: -33.6, 2024: 40.3.

## UNI/USDT

Trades: 153; lucro líquido: -129.30.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 63 | 27.67 | – | 0.30% | 49% | 8.6 h |
| time_exit_12h | 53 | 123.36 | – | 1.62% | 47% | 12.0 h |
| stop_loss | 37 | -280.33 | – | -5.27% | 0% | 4.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 10 | -77.09 | -5.28% | 0% |
| 3 h a 1 dia | 143 | -52.21 | -0.26% | 39% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (56): MFE mediano 3.9%, MAE mediano -1.1%, devolução média do melhor ponto 3.2%, captura mediana 0.46.
- Perdedores (97): MAE mediano -3.8%, MFE mediano 1.2%; 25 (26%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 64.25; – do lucro antes de custos.
- Trades < 3 h: 10 (lucro -77.09); reentradas em < 24 h: 16 (lucro -30.28).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -169.75.
- Lucro por ano de fechamento: 2020: -10.9, 2021: -18.7, 2022: -42.6, 2023: -45.1, 2024: -11.9.

## BCH/USDT

Trades: 172; lucro líquido: 75.21.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 78 | 121.94 | 162% | 1.03% | 51% | 8.7 h |
| time_exit_12h | 67 | 176.98 | 235% | 1.70% | 48% | 12.0 h |
| stop_loss | 27 | -223.71 | -297% | -5.28% | 0% | 4.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 7 | -58.32 | -5.28% | 0% |
| 3 h a 1 dia | 165 | 133.53 | 0.54% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (72): MFE mediano 5.1%, MAE mediano -0.9%, devolução média do melhor ponto 2.9%, captura mediana 0.51.
- Perdedores (100): MAE mediano -3.2%, MFE mediano 1.2%; 27 (27%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 81.52; 52% do lucro antes de custos.
- Trades < 3 h: 7 (lucro -58.32); reentradas em < 24 h: 16 (lucro -8.67).
- Maior trade = 66% do lucro; top 5 = 195%; top 10 = 295%; lucro sem o melhor = 25.33.
- Lucro por ano de fechamento: 2019: 3.0, 2020: 0.3, 2021: 63.0, 2022: 8.0, 2023: -20.7, 2024: 21.5.

## XLM/USDT

Trades: 189; lucro líquido: -16.58.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 79 | 155.41 | – | 1.35% | 58% | 9.1 h |
| time_exit_12h | 77 | 89.22 | – | 0.76% | 51% | 12.0 h |
| stop_loss | 32 | -255.42 | – | -5.27% | 0% | 3.5 h |
| close_below_lower | 1 | -5.80 | – | -4.04% | 0% | 6.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 16 | -128.01 | -5.26% | 0% |
| 3 h a 1 dia | 173 | 111.42 | 0.44% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (85): MFE mediano 4.6%, MAE mediano -1.0%, devolução média do melhor ponto 3.8%, captura mediana 0.42.
- Perdedores (104): MAE mediano -3.8%, MFE mediano 1.1%; 32 (31%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 84.81; 124% do lucro antes de custos.
- Trades < 3 h: 16 (lucro -128.01); reentradas em < 24 h: 21 (lucro -32.94).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -77.47.
- Lucro por ano de fechamento: 2018: -15.4, 2019: 53.9, 2020: 5.0, 2021: -71.6, 2022: -26.4, 2023: 24.7, 2024: 13.3.

## FIL/USDT

Trades: 129; lucro líquido: 63.68.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 58 | 132.03 | 207% | 1.50% | 57% | 8.8 h |
| time_exit_12h | 46 | 137.59 | 216% | 1.93% | 52% | 12.0 h |
| stop_loss | 25 | -205.94 | -323% | -5.27% | 0% | 4.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 7 | -56.72 | -5.27% | 0% |
| 3 h a 1 dia | 122 | 120.40 | 0.66% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (57): MFE mediano 6.4%, MAE mediano -1.4%, devolução média do melhor ponto 3.7%, captura mediana 0.51.
- Perdedores (72): MAE mediano -3.9%, MFE mediano 1.6%; 30 (42%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 60.71; 49% do lucro antes de custos.
- Trades < 3 h: 7 (lucro -56.72); reentradas em < 24 h: 15 (lucro -20.42).
- Maior trade = 51% do lucro; top 5 = 204%; top 10 = 339%; lucro sem o melhor = 30.99.
- Lucro por ano de fechamento: 2020: -29.4, 2021: 105.8, 2022: -16.7, 2023: 6.6, 2024: -2.7.

## AAVE/USDT

Trades: 153; lucro líquido: -165.26.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 55 | 81.57 | – | 1.13% | 53% | 8.4 h |
| time_exit_12h | 53 | 79.29 | – | 1.07% | 42% | 12.0 h |
| stop_loss | 45 | -326.12 | – | -5.27% | 0% | 4.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 16 | -116.31 | -5.27% | 0% |
| 3 h a 1 dia | 137 | -48.95 | -0.24% | 37% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (51): MFE mediano 5.6%, MAE mediano -1.3%, devolução média do melhor ponto 3.1%, captura mediana 0.52.
- Perdedores (102): MAE mediano -4.5%, MFE mediano 1.2%; 36 (35%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 61.58; – do lucro antes de custos.
- Trades < 3 h: 16 (lucro -116.31); reentradas em < 24 h: 27 (lucro -25.84).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -195.01.
- Lucro por ano de fechamento: 2020: -19.5, 2021: -90.9, 2022: 5.2, 2023: -69.9, 2024: 9.9.

## INJ/USDT

Trades: 159; lucro líquido: -286.25.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 62 | 68.90 | – | 0.94% | 47% | 9.3 h |
| stop_loss | 55 | -367.75 | – | -5.28% | 0% | 2.8 h |
| time_exit_12h | 42 | 12.59 | – | 0.22% | 48% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 33 | -221.55 | -5.28% | 0% |
| 3 h a 1 dia | 126 | -64.70 | -0.38% | 39% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (49): MFE mediano 7.1%, MAE mediano -1.6%, devolução média do melhor ponto 5.1%, captura mediana 0.39.
- Perdedores (110): MAE mediano -5.0%, MFE mediano 2.5%; 62 (56%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 56.67; – do lucro antes de custos.
- Trades < 3 h: 33 (lucro -221.55); reentradas em < 24 h: 25 (lucro -55.62).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -299.49.
- Lucro por ano de fechamento: 2020: -78.0, 2021: -119.8, 2022: -63.3, 2023: -12.8, 2024: -12.3.

## HBAR/USDT

Trades: 176; lucro líquido: -195.80.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 64 | 97.24 | – | 1.31% | 52% | 9.0 h |
| time_exit_12h | 62 | 50.19 | – | 0.60% | 52% | 12.0 h |
| stop_loss | 49 | -338.49 | – | -5.26% | 0% | 3.6 h |
| close_below_lower | 1 | -4.74 | – | -3.97% | 0% | 10.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 25 | -175.40 | -5.26% | 0% |
| 3 h a 1 dia | 151 | -20.40 | -0.06% | 43% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (65): MFE mediano 5.3%, MAE mediano -1.2%, devolução média do melhor ponto 4.2%, captura mediana 0.41.
- Perdedores (111): MAE mediano -4.9%, MFE mediano 1.8%; 47 (42%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 67.38; – do lucro antes de custos.
- Trades < 3 h: 25 (lucro -175.40); reentradas em < 24 h: 30 (lucro -45.76).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -256.42.
- Lucro por ano de fechamento: 2019: -1.2, 2020: -63.7, 2021: -108.7, 2022: -23.7, 2023: -38.2, 2024: 39.6.

## OP/USDT

Trades: 67; lucro líquido: 62.91.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| day_end | 30 | 87.77 | 140% | 1.90% | 60% | 8.6 h |
| time_exit_12h | 25 | 73.48 | 117% | 1.91% | 52% | 12.0 h |
| stop_loss | 12 | -98.34 | -156% | -5.24% | 0% | 4.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 3 | -25.27 | -5.24% | 0% |
| 3 h a 1 dia | 64 | 88.18 | 0.90% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (31): MFE mediano 6.9%, MAE mediano -1.1%, devolução média do melhor ponto 4.2%, captura mediana 0.47.
- Perdedores (36): MAE mediano -4.0%, MFE mediano 1.1%; 12 (33%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 31.59; 33% do lucro antes de custos.
- Trades < 3 h: 3 (lucro -25.27); reentradas em < 24 h: 13 (lucro 13.40).
- Maior trade = 46% do lucro; top 5 = 177%; top 10 = 265%; lucro sem o melhor = 33.97.
- Lucro por ano de fechamento: 2022: 39.2, 2023: 30.5, 2024: -6.8.
