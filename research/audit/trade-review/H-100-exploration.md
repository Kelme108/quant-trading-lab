# Revisão de trades: H-100 (exploração)

Fonte dos trades: `research/experiments/20261110T171419Z-h-100-exploration-btc-usdt/raw/backtest-result-2026-11-10_17-23-38.zip`; `research/experiments/20261110T171419Z-h-100-exploration-eth-usdt/raw/backtest-result-2026-11-10_17-26-52.zip`; `research/experiments/20261110T171419Z-h-100-exploration-bnb-usdt/raw/backtest-result-2026-11-10_17-29-37.zip`; `research/experiments/20261110T171419Z-h-100-exploration-xrp-usdt/raw/backtest-result-2026-11-10_17-32-16.zip`; `research/experiments/20261110T171419Z-h-100-exploration-ada-usdt/raw/backtest-result-2026-11-10_17-34-51.zip`; `research/experiments/20261110T171419Z-h-100-exploration-ltc-usdt/raw/backtest-result-2026-11-10_17-38-59.zip`; `research/experiments/20261110T171419Z-h-100-exploration-link-usdt/raw/backtest-result-2026-11-10_17-43-42.zip`; `research/experiments/20261110T171419Z-h-100-exploration-doge-usdt/raw/backtest-result-2026-11-10_17-47-58.zip`; `research/experiments/20261110T171419Z-h-100-exploration-sol-usdt/raw/backtest-result-2026-11-10_17-50-33.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 321; lucro líquido: 99.73.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 208 | -628.88 | -631% | -1.42% | 12% | 12.6 h |
| take_profit_3pct | 78 | 641.88 | 644% | 3.89% | 100% | 10.4 h |
| time_exit_24h | 35 | 86.73 | 87% | 1.17% | 89% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 20 | -4.44 | -0.08% | 40% |
| 3 h a 1 dia | 260 | 7.53 | 0.02% | 35% |
| 1 a 7 dias | 41 | 96.64 | 1.11% | 88% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (135): MFE mediano 4.2%, MAE mediano -0.5%, devolução média do melhor ponto 1.8%, captura mediana 0.63.
- Perdedores (186): MAE mediano -1.8%, MFE mediano 0.8%; 24 (13%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 204.91; 67% do lucro antes de custos.
- Trades < 3 h: 20 (lucro -4.44); reentradas em < 24 h: 44 (lucro 59.44).
- Maior trade = 21% do lucro; top 5 = 77%; top 10 = 130%; lucro sem o melhor = 78.51.
- Lucro por ano de fechamento: 2017: -3.3, 2018: 75.0, 2019: -40.5, 2020: 21.7, 2021: 27.0, 2022: 19.6, 2023: -24.9, 2024: 25.2.

## ETH/USDT

Trades: 344; lucro líquido: 319.90.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 204 | -809.13 | -253% | -1.71% | 11% | 12.2 h |
| take_profit_3pct | 117 | 1035.82 | 324% | 3.86% | 100% | 9.8 h |
| time_exit_24h | 23 | 93.21 | 29% | 1.70% | 96% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 17 | -4.86 | -0.00% | 41% |
| 3 h a 1 dia | 296 | 236.05 | 0.35% | 43% |
| 1 a 7 dias | 31 | 88.72 | 1.21% | 87% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (161): MFE mediano 4.6%, MAE mediano -0.6%, devolução média do melhor ponto 1.8%, captura mediana 0.69.
- Perdedores (183): MAE mediano -2.2%, MFE mediano 1.1%; 48 (26%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 241.88; 43% do lucro antes de custos.
- Trades < 3 h: 17 (lucro -4.86); reentradas em < 24 h: 59 (lucro -4.17).
- Maior trade = 5% do lucro; top 5 = 24%; top 10 = 43%; lucro sem o melhor = 302.85.
- Lucro por ano de fechamento: 2017: 7.4, 2018: 1.1, 2019: 40.6, 2020: 112.8, 2021: 101.8, 2022: -2.0, 2023: 48.2, 2024: 9.9.

## BNB/USDT

Trades: 297; lucro líquido: 317.09.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 172 | -990.92 | -313% | -2.16% | 4% | 11.1 h |
| take_profit_3pct | 113 | 1263.22 | 398% | 4.39% | 100% | 7.8 h |
| time_exit_24h | 12 | 44.78 | 14% | 1.40% | 92% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 37 | 287.46 | 3.46% | 78% |
| 3 h a 1 dia | 245 | -30.59 | -0.04% | 36% |
| 1 a 7 dias | 15 | 60.22 | 1.51% | 93% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (131): MFE mediano 5.2%, MAE mediano -0.8%, devolução média do melhor ponto 2.0%, captura mediana 0.72.
- Perdedores (166): MAE mediano -2.7%, MFE mediano 1.3%; 42 (25%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 236.69; 43% do lucro antes de custos.
- Trades < 3 h: 37 (lucro 287.46); reentradas em < 24 h: 51 (lucro -58.27).
- Maior trade = 13% do lucro; top 5 = 40%; top 10 = 70%; lucro sem o melhor = 277.35.
- Lucro por ano de fechamento: 2017: 8.0, 2018: 288.7, 2019: 83.4, 2020: 0.0, 2021: 37.8, 2022: -51.1, 2023: -52.5, 2024: 2.8.

## XRP/USDT

Trades: 306; lucro líquido: -271.14.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 202 | -1122.43 | – | -2.92% | 5% | 9.2 h |
| take_profit_3pct | 99 | 832.21 | – | 4.31% | 100% | 7.3 h |
| time_exit_24h | 5 | 19.07 | – | 1.96% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 40 | 82.07 | 0.99% | 62% |
| 3 h a 1 dia | 257 | -382.80 | -0.81% | 31% |
| 1 a 7 dias | 9 | 29.59 | 1.68% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (114): MFE mediano 5.8%, MAE mediano -1.0%, devolução média do melhor ponto 2.8%, captura mediana 0.64.
- Perdedores (192): MAE mediano -3.2%, MFE mediano 1.0%; 47 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 173.36; – do lucro antes de custos.
- Trades < 3 h: 40 (lucro 82.07); reentradas em < 24 h: 58 (lucro -92.26).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -290.60.
- Lucro por ano de fechamento: 2018: 41.4, 2019: -29.0, 2020: 75.8, 2021: -171.7, 2022: -43.6, 2023: -105.7, 2024: -38.3.

## ADA/USDT

Trades: 295; lucro líquido: -12.08.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 179 | -955.85 | – | -2.57% | 4% | 10.5 h |
| take_profit_3pct | 113 | 934.37 | – | 4.02% | 100% | 7.7 h |
| time_exit_24h | 3 | 9.40 | – | 1.51% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 25 | 156.50 | 2.95% | 88% |
| 3 h a 1 dia | 264 | -178.72 | -0.31% | 37% |
| 1 a 7 dias | 6 | 10.15 | 0.85% | 67% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (124): MFE mediano 5.5%, MAE mediano -1.2%, devolução média do melhor ponto 2.3%, captura mediana 0.67.
- Perdedores (171): MAE mediano -3.1%, MFE mediano 1.2%; 57 (33%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 183.18; 107% do lucro antes de custos.
- Trades < 3 h: 25 (lucro 156.50); reentradas em < 24 h: 61 (lucro -37.17).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -27.80.
- Lucro por ano de fechamento: 2018: -35.2, 2019: 10.5, 2020: 60.1, 2021: 42.3, 2022: -7.0, 2023: -51.5, 2024: -31.3.

## LTC/USDT

Trades: 325; lucro líquido: -29.30.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 204 | -1029.32 | – | -2.39% | 6% | 11.0 h |
| take_profit_3pct | 112 | 980.49 | – | 4.17% | 100% | 8.2 h |
| time_exit_24h | 9 | 19.53 | – | 1.03% | 89% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 33 | 48.22 | 0.73% | 64% |
| 3 h a 1 dia | 279 | -98.44 | -0.16% | 36% |
| 1 a 7 dias | 13 | 20.93 | 0.77% | 77% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (132): MFE mediano 5.4%, MAE mediano -0.8%, devolução média do melhor ponto 2.1%, captura mediana 0.69.
- Perdedores (193): MAE mediano -2.8%, MFE mediano 1.2%; 47 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 204.34; 117% do lucro antes de custos.
- Trades < 3 h: 33 (lucro 48.22); reentradas em < 24 h: 59 (lucro -49.94).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -54.58.
- Lucro por ano de fechamento: 2018: 64.6, 2019: 23.3, 2020: 9.4, 2021: -63.1, 2022: -13.2, 2023: -19.0, 2024: -31.3.

## LINK/USDT

Trades: 285; lucro líquido: 140.74.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 167 | -922.24 | -655% | -2.56% | 5% | 10.7 h |
| take_profit_3pct | 114 | 1058.49 | 752% | 4.35% | 100% | 8.0 h |
| time_exit_24h | 4 | 4.49 | 3% | 0.48% | 75% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 27 | 121.19 | 2.11% | 70% |
| 3 h a 1 dia | 253 | 15.20 | 0.04% | 41% |
| 1 a 7 dias | 5 | 4.34 | 0.37% | 60% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (125): MFE mediano 5.6%, MAE mediano -1.4%, devolução média do melhor ponto 2.4%, captura mediana 0.67.
- Perdedores (160): MAE mediano -3.2%, MFE mediano 1.7%; 65 (41%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 185.81; 57% do lucro antes de custos.
- Trades < 3 h: 27 (lucro 121.19); reentradas em < 24 h: 56 (lucro -8.62).
- Maior trade = 15% do lucro; top 5 = 68%; top 10 = 121%; lucro sem o melhor = 119.39.
- Lucro por ano de fechamento: 2019: 40.3, 2020: 28.2, 2021: 55.5, 2022: 12.1, 2023: -13.9, 2024: 18.5.

## DOGE/USDT

Trades: 264; lucro líquido: 160.34.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 164 | -1102.51 | -688% | -2.72% | 4% | 9.2 h |
| take_profit_3pct | 99 | 1258.27 | 785% | 5.29% | 100% | 6.5 h |
| time_exit_24h | 1 | 4.57 | 3% | 2.22% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 39 | 346.43 | 3.68% | 72% |
| 3 h a 1 dia | 224 | -190.66 | -0.29% | 34% |
| 1 a 7 dias | 1 | 4.57 | 2.22% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (106): MFE mediano 7.0%, MAE mediano -1.3%, devolução média do melhor ponto 5.3%, captura mediana 0.59.
- Perdedores (158): MAE mediano -3.3%, MFE mediano 1.3%; 44 (28%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 190.91; 54% do lucro antes de custos.
- Trades < 3 h: 39 (lucro 346.43); reentradas em < 24 h: 68 (lucro 146.25).
- Maior trade = 53% do lucro; top 5 = 128%; top 10 = 191%; lucro sem o melhor = 75.75.
- Lucro por ano de fechamento: 2019: -9.9, 2020: 87.5, 2021: 290.7, 2022: -83.1, 2023: -115.8, 2024: -8.9.

## SOL/USDT

Trades: 206; lucro líquido: 125.91.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 110 | -755.46 | -600% | -3.15% | 4% | 10.0 h |
| take_profit_3pct | 93 | 872.71 | 693% | 4.37% | 100% | 7.1 h |
| time_exit_24h | 3 | 8.66 | 7% | 1.28% | 67% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 26 | 132.37 | 2.49% | 77% |
| 3 h a 1 dia | 176 | -21.78 | -0.05% | 43% |
| 1 a 7 dias | 4 | 15.32 | 1.73% | 75% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (99): MFE mediano 5.6%, MAE mediano -1.1%, devolução média do melhor ponto 2.3%, captura mediana 0.70.
- Perdedores (107): MAE mediano -3.9%, MFE mediano 1.5%; 36 (34%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 134.47; 52% do lucro antes de custos.
- Trades < 3 h: 26 (lucro 132.37); reentradas em < 24 h: 47 (lucro -45.67).
- Maior trade = 16% do lucro; top 5 = 70%; top 10 = 127%; lucro sem o melhor = 105.57.
- Lucro por ano de fechamento: 2020: -4.7, 2021: 92.4, 2022: 1.6, 2023: 61.8, 2024: -25.2.
