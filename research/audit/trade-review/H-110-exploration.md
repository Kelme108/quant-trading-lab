# Revisão de trades: H-110 (exploração)

Fonte dos trades: `research/experiments/20261111T174334Z-h-110-exploration-btc-usdt/raw/backtest-result-2026-11-11_18-03-51.zip`; `research/experiments/20261111T174334Z-h-110-exploration-eth-usdt/raw/backtest-result-2026-11-11_18-11-32.zip`; `research/experiments/20261111T174334Z-h-110-exploration-bnb-usdt/raw/backtest-result-2026-11-11_18-20-15.zip`; `research/experiments/20261111T174334Z-h-110-exploration-xrp-usdt/raw/backtest-result-2026-11-11_18-29-34.zip`; `research/experiments/20261111T174334Z-h-110-exploration-ada-usdt/raw/backtest-result-2026-11-11_18-38-49.zip`; `research/experiments/20261111T174334Z-h-110-exploration-ltc-usdt/raw/backtest-result-2026-11-11_18-47-41.zip`; `research/experiments/20261111T174334Z-h-110-exploration-link-usdt/raw/backtest-result-2026-11-11_18-56-38.zip`; `research/experiments/20261111T174334Z-h-110-exploration-doge-usdt/raw/backtest-result-2026-11-11_19-04-53.zip`; `research/experiments/20261111T174334Z-h-110-exploration-sol-usdt/raw/backtest-result-2026-11-11_19-12-07.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 391; lucro líquido: -100.42.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 162 | -378.48 | – | -2.38% | 0% | 4.4 h |
| time_exit_12h | 150 | 29.89 | – | 0.20% | 53% | 12.0 h |
| take_profit_1_5R | 77 | 255.66 | – | 3.36% | 100% | 6.0 h |
| stop_loss | 2 | -7.49 | – | -3.79% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 83 | -83.82 | -1.06% | 23% |
| 3 h a 1 dia | 308 | -16.60 | -0.06% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (157): MFE mediano 3.2%, MAE mediano -0.8%, devolução média do melhor ponto 1.2%, captura mediana 0.67.
- Perdedores (234): MAE mediano -2.4%, MFE mediano 0.9%; 40 (17%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 113.69; 857% do lucro antes de custos.
- Trades < 3 h: 83 (lucro -83.82); reentradas em < 24 h: 119 (lucro 1.44).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -106.82.
- Lucro por ano de fechamento: 2017: 30.4, 2018: -37.3, 2019: 0.1, 2020: -20.7, 2021: -45.2, 2022: -30.6, 2023: 0.3, 2024: 2.4.

## ETH/USDT

Trades: 592; lucro líquido: -63.46.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 250 | -591.06 | – | -2.43% | 0% | 4.2 h |
| time_exit_12h | 190 | 23.49 | – | 0.13% | 49% | 12.0 h |
| take_profit_1_5R | 152 | 504.11 | – | 3.41% | 100% | 5.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 154 | -58.50 | -0.38% | 34% |
| 3 h a 1 dia | 438 | -4.96 | -0.01% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (245): MFE mediano 3.6%, MAE mediano -0.8%, devolução média do melhor ponto 1.3%, captura mediana 0.70.
- Perdedores (347): MAE mediano -2.4%, MFE mediano 0.8%; 55 (16%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 172.07; 158% do lucro antes de custos.
- Trades < 3 h: 154 (lucro -58.50); reentradas em < 24 h: 199 (lucro -5.07).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -71.03.
- Lucro por ano de fechamento: 2017: -11.8, 2018: -30.5, 2019: 0.4, 2020: 5.0, 2021: -1.4, 2022: -10.7, 2023: 0.6, 2024: -15.1.

## BNB/USDT

Trades: 609; lucro líquido: -71.66.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 290 | -676.27 | – | -2.40% | 0% | 4.0 h |
| take_profit_1_5R | 168 | 559.70 | – | 3.43% | 100% | 5.5 h |
| time_exit_12h | 149 | 52.48 | – | 0.37% | 58% | 12.0 h |
| stop_loss | 2 | -7.57 | – | -3.79% | 0% | 0.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 182 | -141.27 | -0.79% | 27% |
| 3 h a 1 dia | 427 | 69.61 | 0.17% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (254): MFE mediano 3.8%, MAE mediano -0.7%, devolução média do melhor ponto 1.1%, captura mediana 0.74.
- Perdedores (355): MAE mediano -2.4%, MFE mediano 0.7%; 49 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 176.49; 168% do lucro antes de custos.
- Trades < 3 h: 182 (lucro -141.27); reentradas em < 24 h: 224 (lucro -21.73).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -82.65.
- Lucro por ano de fechamento: 2017: 12.6, 2018: -41.9, 2019: -2.9, 2020: -0.9, 2021: -23.3, 2022: -19.1, 2023: -4.7, 2024: 8.5.

## XRP/USDT

Trades: 448; lucro líquido: -62.79.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 185 | -441.70 | – | -2.48% | 0% | 4.1 h |
| time_exit_12h | 160 | 30.15 | – | 0.20% | 57% | 12.0 h |
| take_profit_1_5R | 101 | 352.41 | – | 3.63% | 100% | 5.0 h |
| stop_loss | 1 | -3.53 | – | -3.77% | 0% | 0.0 h |
| force_exit | 1 | -0.11 | – | -0.12% | 0% | 2.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 131 | -75.11 | -0.60% | 31% |
| 3 h a 1 dia | 317 | 12.33 | 0.05% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (193): MFE mediano 3.5%, MAE mediano -0.9%, devolução média do melhor ponto 1.4%, captura mediana 0.66.
- Perdedores (255): MAE mediano -2.5%, MFE mediano 0.9%; 48 (19%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 128.75; 195% do lucro antes de custos.
- Trades < 3 h: 131 (lucro -75.11); reentradas em < 24 h: 115 (lucro -30.06).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -72.69.
- Lucro por ano de fechamento: 2018: -13.9, 2019: -8.7, 2020: 9.2, 2021: -34.9, 2022: -39.9, 2023: 10.8, 2024: 14.5.

## ADA/USDT

Trades: 645; lucro líquido: -114.55.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 317 | -751.47 | – | -2.40% | 0% | 4.0 h |
| take_profit_1_5R | 178 | 612.41 | – | 3.46% | 100% | 5.2 h |
| time_exit_12h | 150 | 24.51 | – | 0.17% | 51% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 193 | -187.73 | -0.99% | 24% |
| 3 h a 1 dia | 452 | 73.18 | 0.16% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (254): MFE mediano 4.0%, MAE mediano -0.9%, devolução média do melhor ponto 1.3%, captura mediana 0.72.
- Perdedores (391): MAE mediano -2.4%, MFE mediano 0.9%; 67 (17%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 190.35; 251% do lucro antes de custos.
- Trades < 3 h: 193 (lucro -187.73); reentradas em < 24 h: 226 (lucro -7.66).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -122.75.
- Lucro por ano de fechamento: 2018: 1.3, 2019: 13.1, 2020: -4.8, 2021: -32.8, 2022: -68.1, 2023: -5.4, 2024: -17.8.

## LTC/USDT

Trades: 623; lucro líquido: -180.96.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 307 | -692.38 | – | -2.47% | 0% | 4.2 h |
| time_exit_12h | 177 | 68.72 | – | 0.43% | 60% | 12.0 h |
| take_profit_1_5R | 139 | 442.70 | – | 3.49% | 100% | 5.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 183 | -175.65 | -1.06% | 24% |
| 3 h a 1 dia | 440 | -5.31 | -0.01% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (245): MFE mediano 3.6%, MAE mediano -0.8%, devolução média do melhor ponto 1.3%, captura mediana 0.69.
- Perdedores (378): MAE mediano -2.6%, MFE mediano 0.9%; 67 (18%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 169.42; – do lucro antes de custos.
- Trades < 3 h: 183 (lucro -175.65); reentradas em < 24 h: 203 (lucro -75.24).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -188.26.
- Lucro por ano de fechamento: 2017: -9.8, 2018: -45.3, 2019: -1.9, 2020: -31.3, 2021: -35.4, 2022: -23.6, 2023: -21.2, 2024: -12.6.

## LINK/USDT

Trades: 679; lucro líquido: -154.93.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 358 | -828.63 | – | -2.49% | 0% | 3.7 h |
| take_profit_1_5R | 195 | 641.30 | – | 3.55% | 100% | 5.0 h |
| time_exit_12h | 125 | 32.87 | – | 0.29% | 62% | 12.0 h |
| force_exit | 1 | -0.47 | – | -0.55% | 0% | 7.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 240 | -197.93 | -0.89% | 26% |
| 3 h a 1 dia | 439 | 43.00 | 0.11% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (273): MFE mediano 4.1%, MAE mediano -0.9%, devolução média do melhor ponto 1.4%, captura mediana 0.72.
- Perdedores (406): MAE mediano -2.6%, MFE mediano 0.8%; 95 (23%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 188.11; 567% do lucro antes de custos.
- Trades < 3 h: 240 (lucro -197.93); reentradas em < 24 h: 260 (lucro -22.76).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -164.60.
- Lucro por ano de fechamento: 2019: -18.0, 2020: -56.4, 2021: -46.7, 2022: -8.7, 2023: 1.4, 2024: -26.5.

## DOGE/USDT

Trades: 447; lucro líquido: -77.50.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 216 | -497.28 | – | -2.45% | 0% | 4.0 h |
| take_profit_1_5R | 119 | 411.35 | – | 3.70% | 100% | 4.8 h |
| time_exit_12h | 111 | 12.10 | – | 0.12% | 49% | 12.0 h |
| stop_loss | 1 | -3.67 | – | -3.79% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 150 | -62.40 | -0.43% | 33% |
| 3 h a 1 dia | 297 | -15.09 | -0.05% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (173): MFE mediano 3.9%, MAE mediano -0.7%, devolução média do melhor ponto 1.5%, captura mediana 0.71.
- Perdedores (274): MAE mediano -2.4%, MFE mediano 0.7%; 47 (17%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 125.47; 262% do lucro antes de custos.
- Trades < 3 h: 150 (lucro -62.40); reentradas em < 24 h: 150 (lucro -29.91).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -91.03.
- Lucro por ano de fechamento: 2019: -21.9, 2020: -10.9, 2021: -46.5, 2022: -2.2, 2023: 1.9, 2024: 2.1.

## SOL/USDT

Trades: 593; lucro líquido: -95.20.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 325 | -797.02 | – | -2.50% | 0% | 3.4 h |
| take_profit_1_5R | 184 | 671.56 | – | 3.72% | 100% | 4.7 h |
| time_exit_12h | 83 | 31.04 | – | 0.39% | 61% | 12.0 h |
| force_exit | 1 | -0.79 | – | -0.87% | 0% | 9.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 235 | -208.17 | -0.91% | 25% |
| 3 h a 1 dia | 358 | 112.97 | 0.32% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (235): MFE mediano 4.4%, MAE mediano -0.8%, devolução média do melhor ponto 1.4%, captura mediana 0.74.
- Perdedores (358): MAE mediano -2.7%, MFE mediano 1.0%; 83 (23%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 173.80; 221% do lucro antes de custos.
- Trades < 3 h: 235 (lucro -208.17); reentradas em < 24 h: 247 (lucro -57.67).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -102.52.
- Lucro por ano de fechamento: 2020: 2.9, 2021: -48.5, 2022: 24.8, 2023: -20.7, 2024: -53.8.
