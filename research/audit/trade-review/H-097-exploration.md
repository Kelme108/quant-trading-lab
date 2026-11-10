# Revisão de trades: H-097 (exploração)

Fonte dos trades: `research/experiments/20261110T075321Z-h-097-exploration-btc-usdt/raw/backtest-result-2026-11-10_08-01-47.zip`; `research/experiments/20261110T075321Z-h-097-exploration-eth-usdt/raw/backtest-result-2026-11-10_08-06-14.zip`; `research/experiments/20261110T075321Z-h-097-exploration-bnb-usdt/raw/backtest-result-2026-11-10_08-10-40.zip`; `research/experiments/20261110T075321Z-h-097-exploration-xrp-usdt/raw/backtest-result-2026-11-10_08-14-56.zip`; `research/experiments/20261110T075321Z-h-097-exploration-ada-usdt/raw/backtest-result-2026-11-10_08-19-05.zip`; `research/experiments/20261110T075321Z-h-097-exploration-ltc-usdt/raw/backtest-result-2026-11-10_08-23-03.zip`; `research/experiments/20261110T075321Z-h-097-exploration-link-usdt/raw/backtest-result-2026-11-10_08-27-10.zip`; `research/experiments/20261110T075321Z-h-097-exploration-doge-usdt/raw/backtest-result-2026-11-10_08-31-11.zip`; `research/experiments/20261110T075321Z-h-097-exploration-sol-usdt/raw/backtest-result-2026-11-10_08-34-44.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 209; lucro líquido: -195.92.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 96 | -301.94 | – | -1.76% | 0% | 4.2 h |
| time_12h | 69 | -19.40 | – | -0.17% | 28% | 12.0 h |
| rsi70 | 41 | 114.73 | – | 1.63% | 98% | 5.3 h |
| take_profit_2R | 2 | 9.58 | – | 2.71% | 100% | 6.0 h |
| force_exit | 1 | 1.11 | – | 0.70% | 100% | 3.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 54 | -100.83 | -1.06% | 17% |
| 3 h a 1 dia | 155 | -95.10 | -0.33% | 34% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (62): MFE mediano 1.8%, MAE mediano -0.4%, devolução média do melhor ponto 0.8%, captura mediana 0.61.
- Perdedores (147): MAE mediano -1.5%, MFE mediano 0.5%; 6 (4%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 109.03; – do lucro antes de custos.
- Trades < 3 h: 54 (lucro -100.83); reentradas em < 24 h: 26 (lucro -34.10).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -205.48.
- Lucro por ano de fechamento: 2017: 2.3, 2018: -64.1, 2019: -50.1, 2020: -35.7, 2021: -10.1, 2022: -7.1, 2023: -22.6, 2024: -8.6.

## ETH/USDT

Trades: 216; lucro líquido: -165.15.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 98 | -354.45 | – | -1.94% | 0% | 4.9 h |
| time_12h | 70 | 14.08 | – | 0.10% | 47% | 12.0 h |
| rsi70 | 46 | 164.78 | – | 1.92% | 98% | 6.6 h |
| take_profit_2R | 2 | 10.44 | – | 2.85% | 100% | 7.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 41 | -80.14 | -1.05% | 22% |
| 3 h a 1 dia | 175 | -85.01 | -0.27% | 41% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (80): MFE mediano 2.3%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.58.
- Perdedores (136): MAE mediano -1.7%, MFE mediano 0.7%; 8 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 119.58; – do lucro antes de custos.
- Trades < 3 h: 41 (lucro -80.14); reentradas em < 24 h: 30 (lucro -23.63).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -173.39.
- Lucro por ano de fechamento: 2017: -7.8, 2018: -29.5, 2019: 16.6, 2020: -20.3, 2021: -24.2, 2022: -66.5, 2023: -1.6, 2024: -31.9.

## BNB/USDT

Trades: 211; lucro líquido: -143.04.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 99 | -341.32 | – | -1.87% | 0% | 4.3 h |
| time_12h | 69 | 23.53 | – | 0.19% | 54% | 12.0 h |
| rsi70 | 39 | 150.20 | – | 2.12% | 100% | 6.9 h |
| take_profit_2R | 4 | 24.55 | – | 3.21% | 100% | 4.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 50 | -102.97 | -1.13% | 16% |
| 3 h a 1 dia | 161 | -40.07 | -0.12% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (80): MFE mediano 2.2%, MAE mediano -0.5%, devolução média do melhor ponto 1.0%, captura mediana 0.65.
- Perdedores (131): MAE mediano -1.8%, MFE mediano 0.5%; 7 (5%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 115.24; – do lucro antes de custos.
- Trades < 3 h: 50 (lucro -102.97); reentradas em < 24 h: 31 (lucro -39.17).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -155.99.
- Lucro por ano de fechamento: 2018: -12.7, 2019: -61.7, 2020: -11.7, 2021: -31.3, 2022: -13.9, 2023: -1.7, 2024: -10.2.

## XRP/USDT

Trades: 181; lucro líquido: -34.84.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 71 | -281.30 | – | -2.04% | 0% | 4.8 h |
| time_12h | 62 | 38.95 | – | 0.33% | 63% | 12.0 h |
| rsi70 | 41 | 158.01 | – | 1.98% | 100% | 6.3 h |
| take_profit_2R | 7 | 49.50 | – | 3.69% | 100% | 8.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 31 | -94.09 | -1.57% | 13% |
| 3 h a 1 dia | 150 | 59.25 | 0.21% | 55% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (87): MFE mediano 2.5%, MAE mediano -0.6%, devolução média do melhor ponto 1.1%, captura mediana 0.60.
- Perdedores (94): MAE mediano -1.8%, MFE mediano 0.6%; 8 (9%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 105.41; 149% do lucro antes de custos.
- Trades < 3 h: 31 (lucro -94.09); reentradas em < 24 h: 9 (lucro 5.91).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -43.89.
- Lucro por ano de fechamento: 2018: -1.8, 2019: -21.6, 2020: -23.4, 2021: -3.0, 2022: 17.3, 2023: 4.3, 2024: -6.5.

## ADA/USDT

Trades: 209; lucro líquido: -160.76.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 106 | -416.10 | – | -2.13% | 0% | 4.1 h |
| time_12h | 53 | 24.57 | – | 0.25% | 62% | 12.0 h |
| rsi70 | 46 | 205.35 | – | 2.43% | 100% | 6.4 h |
| take_profit_2R | 4 | 25.41 | – | 3.47% | 100% | 6.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 53 | -159.33 | -1.62% | 11% |
| 3 h a 1 dia | 156 | -1.43 | -0.00% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (83): MFE mediano 2.7%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.70.
- Perdedores (126): MAE mediano -2.0%, MFE mediano 0.7%; 11 (9%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 114.56; – do lucro antes de custos.
- Trades < 3 h: 53 (lucro -159.33); reentradas em < 24 h: 24 (lucro -8.94).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -170.56.
- Lucro por ano de fechamento: 2018: -46.3, 2019: -22.8, 2020: -1.4, 2021: -20.3, 2022: -10.0, 2023: -16.1, 2024: -43.8.

## LTC/USDT

Trades: 200; lucro líquido: -71.86.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 88 | -338.83 | – | -1.97% | 0% | 3.9 h |
| time_12h | 61 | 33.11 | – | 0.28% | 59% | 12.0 h |
| rsi70 | 48 | 217.02 | – | 2.31% | 100% | 5.8 h |
| take_profit_2R | 3 | 16.84 | – | 2.89% | 100% | 6.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 52 | -137.50 | -1.35% | 15% |
| 3 h a 1 dia | 148 | 65.64 | 0.23% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (87): MFE mediano 2.6%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.63.
- Perdedores (113): MAE mediano -1.8%, MFE mediano 0.6%; 9 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 117.00; 259% do lucro antes de custos.
- Trades < 3 h: 52 (lucro -137.50); reentradas em < 24 h: 22 (lucro 5.92).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -82.22.
- Lucro por ano de fechamento: 2018: -7.2, 2019: -14.4, 2020: -9.1, 2021: 11.7, 2022: 3.7, 2023: -45.0, 2024: -11.5.

## LINK/USDT

Trades: 192; lucro líquido: -106.88.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 93 | -380.25 | – | -2.12% | 0% | 4.0 h |
| time_12h | 52 | 32.08 | – | 0.32% | 54% | 12.0 h |
| rsi70 | 42 | 206.49 | – | 2.55% | 100% | 5.8 h |
| take_profit_2R | 5 | 34.80 | – | 3.56% | 100% | 2.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 49 | -102.56 | -1.07% | 22% |
| 3 h a 1 dia | 143 | -4.33 | -0.02% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (75): MFE mediano 2.9%, MAE mediano -0.7%, devolução média do melhor ponto 0.9%, captura mediana 0.71.
- Perdedores (117): MAE mediano -2.1%, MFE mediano 0.7%; 13 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 110.78; 2840% do lucro antes de custos.
- Trades < 3 h: 49 (lucro -102.56); reentradas em < 24 h: 30 (lucro -10.90).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -118.39.
- Lucro por ano de fechamento: 2019: -21.9, 2020: 0.1, 2021: -27.7, 2022: 34.3, 2023: -37.9, 2024: -53.7.

## DOGE/USDT

Trades: 146; lucro líquido: -147.76.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 77 | -278.87 | – | -1.97% | 0% | 3.8 h |
| time_12h | 50 | 38.92 | – | 0.43% | 62% | 12.0 h |
| rsi70 | 17 | 78.94 | – | 2.58% | 100% | 6.2 h |
| take_profit_2R | 2 | 13.25 | – | 3.46% | 100% | 9.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 44 | -106.19 | -1.32% | 11% |
| 3 h a 1 dia | 102 | -41.57 | -0.21% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (50): MFE mediano 2.4%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.55.
- Perdedores (96): MAE mediano -1.8%, MFE mediano 0.5%; 3 (3%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 80.15; – do lucro antes de custos.
- Trades < 3 h: 44 (lucro -106.19); reentradas em < 24 h: 14 (lucro -26.40).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -157.36.
- Lucro por ano de fechamento: 2019: -13.5, 2020: -34.4, 2021: -31.6, 2022: -44.1, 2023: -5.9, 2024: -18.3.

## SOL/USDT

Trades: 121; lucro líquido: -82.10.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 56 | -250.13 | – | -2.31% | 0% | 4.2 h |
| time_12h | 37 | 7.04 | – | 0.11% | 49% | 12.0 h |
| rsi70 | 24 | 132.44 | – | 2.84% | 100% | 6.3 h |
| take_profit_2R | 4 | 28.55 | – | 3.72% | 100% | 6.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 30 | -97.83 | -1.68% | 13% |
| 3 h a 1 dia | 91 | 15.73 | 0.09% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (46): MFE mediano 2.8%, MAE mediano -0.6%, devolução média do melhor ponto 1.0%, captura mediana 0.71.
- Perdedores (75): MAE mediano -2.2%, MFE mediano 0.9%; 18 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 70.04; – do lucro antes de custos.
- Trades < 3 h: 30 (lucro -97.83); reentradas em < 24 h: 22 (lucro 21.60).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -95.28.
- Lucro por ano de fechamento: 2020: -26.1, 2021: 25.8, 2022: -48.2, 2023: 4.2, 2024: -37.7.
