# Revisão de trades: H-113 (exploração)

Fonte dos trades: `research/experiments/20261111T204620Z-h-113-exploration-btc-usdt/raw/backtest-result-2026-11-11_21-00-58.zip`; `research/experiments/20261111T204620Z-h-113-exploration-eth-usdt/raw/backtest-result-2026-11-11_21-06-02.zip`; `research/experiments/20261111T204620Z-h-113-exploration-bnb-usdt/raw/backtest-result-2026-11-11_21-12-41.zip`; `research/experiments/20261111T204620Z-h-113-exploration-xrp-usdt/raw/backtest-result-2026-11-11_21-21-19.zip`; `research/experiments/20261111T204620Z-h-113-exploration-ada-usdt/raw/backtest-result-2026-11-11_21-31-17.zip`; `research/experiments/20261111T204620Z-h-113-exploration-ltc-usdt/raw/backtest-result-2026-11-11_21-42-11.zip`; `research/experiments/20261111T204620Z-h-113-exploration-link-usdt/raw/backtest-result-2026-11-11_21-52-32.zip`; `research/experiments/20261111T204620Z-h-113-exploration-doge-usdt/raw/backtest-result-2026-11-11_21-58-43.zip`; `research/experiments/20261111T204620Z-h-113-exploration-sol-usdt/raw/backtest-result-2026-11-11_22-04-18.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 422; lucro líquido: -18.13.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 189 | -121.11 | – | -1.30% | 0% | 1.3 h |
| time_exit_6h | 169 | 9.97 | – | 0.12% | 51% | 6.0 h |
| take_profit_1p8 | 64 | 93.01 | – | 2.94% | 100% | 2.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 184 | -57.57 | -0.63% | 16% |
| 3 h a 1 dia | 238 | 39.44 | 0.34% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (150): MFE mediano 2.5%, MAE mediano -0.3%, devolução média do melhor ponto 1.5%, captura mediana 0.48.
- Perdedores (272): MAE mediano -1.2%, MFE mediano 0.5%; 16 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 62.37; 141% do lucro antes de custos.
- Trades < 3 h: 184 (lucro -57.57); reentradas em < 24 h: 138 (lucro -12.98).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -22.42.
- Lucro por ano de fechamento: 2018: -1.3, 2019: -2.4, 2020: -5.8, 2021: -7.2, 2022: -2.5, 2023: 1.7, 2024: -0.7.

## ETH/USDT

Trades: 529; lucro líquido: -69.47.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 311 | -194.89 | – | -1.30% | 0% | 1.2 h |
| time_exit_6h | 143 | 17.54 | – | 0.26% | 57% | 6.0 h |
| take_profit_1p8 | 75 | 107.87 | – | 2.97% | 100% | 3.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 284 | -108.02 | -0.79% | 11% |
| 3 h a 1 dia | 245 | 38.54 | 0.32% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (157): MFE mediano 2.8%, MAE mediano -0.4%, devolução média do melhor ponto 1.5%, captura mediana 0.54.
- Perdedores (372): MAE mediano -1.3%, MFE mediano 0.6%; 31 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 76.46; 1095% do lucro antes de custos.
- Trades < 3 h: 284 (lucro -108.02); reentradas em < 24 h: 196 (lucro -36.68).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -73.70.
- Lucro por ano de fechamento: 2018: -14.2, 2019: -0.9, 2020: -10.4, 2021: -17.0, 2022: -14.9, 2023: -10.6, 2024: -1.5.

## BNB/USDT

Trades: 597; lucro líquido: -126.02.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 397 | -239.79 | – | -1.29% | 0% | 1.0 h |
| time_exit_6h | 117 | 5.93 | – | 0.11% | 50% | 6.0 h |
| take_profit_1p8 | 83 | 107.84 | – | 2.78% | 100% | 2.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 391 | -133.07 | -0.72% | 14% |
| 3 h a 1 dia | 206 | 7.04 | 0.07% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (141): MFE mediano 2.9%, MAE mediano -0.5%, devolução média do melhor ponto 1.6%, captura mediana 0.53.
- Perdedores (456): MAE mediano -1.3%, MFE mediano 0.6%; 44 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 83.08; – do lucro antes de custos.
- Trades < 3 h: 391 (lucro -133.07); reentradas em < 24 h: 238 (lucro -51.69).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -130.82.
- Lucro por ano de fechamento: 2018: -17.5, 2019: -37.6, 2020: -20.9, 2021: -4.6, 2022: -24.2, 2023: -14.3, 2024: -6.9.

## XRP/USDT

Trades: 594; lucro líquido: -144.76.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 437 | -262.60 | – | -1.29% | 0% | 0.7 h |
| take_profit_1p8 | 85 | 113.91 | – | 2.88% | 100% | 2.3 h |
| time_exit_6h | 72 | 3.93 | – | 0.11% | 53% | 6.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 447 | -163.92 | -0.79% | 12% |
| 3 h a 1 dia | 147 | 19.16 | 0.28% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (123): MFE mediano 3.6%, MAE mediano -0.5%, devolução média do melhor ponto 1.9%, captura mediana 0.52.
- Perdedores (471): MAE mediano -1.5%, MFE mediano 0.7%; 76 (16%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 82.57; – do lucro antes de custos.
- Trades < 3 h: 447 (lucro -163.92); reentradas em < 24 h: 273 (lucro -62.09).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -148.14.
- Lucro por ano de fechamento: 2018: -10.1, 2019: -30.6, 2020: -28.9, 2021: -27.7, 2022: -10.2, 2023: -19.9, 2024: -17.3.

## ADA/USDT

Trades: 667; lucro líquido: -108.59.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 466 | -282.05 | – | -1.29% | 0% | 0.8 h |
| take_profit_1p8 | 121 | 168.28 | – | 2.97% | 100% | 2.4 h |
| time_exit_6h | 80 | 5.18 | – | 0.14% | 51% | 6.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 493 | -136.78 | -0.59% | 16% |
| 3 h a 1 dia | 174 | 28.19 | 0.35% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (162): MFE mediano 3.9%, MAE mediano -0.4%, devolução média do melhor ponto 2.0%, captura mediana 0.57.
- Perdedores (505): MAE mediano -1.4%, MFE mediano 0.7%; 72 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 93.54; – do lucro antes de custos.
- Trades < 3 h: 493 (lucro -136.78); reentradas em < 24 h: 325 (lucro -58.93).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -112.61.
- Lucro por ano de fechamento: 2018: -20.4, 2019: -37.4, 2020: 6.5, 2021: -25.2, 2022: -10.3, 2023: -12.6, 2024: -9.1.

## LTC/USDT

Trades: 597; lucro líquido: -85.81.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 383 | -236.35 | – | -1.29% | 0% | 1.1 h |
| time_exit_6h | 122 | 10.28 | – | 0.17% | 50% | 6.0 h |
| take_profit_1p8 | 92 | 140.26 | – | 3.18% | 100% | 2.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 361 | -93.91 | -0.54% | 16% |
| 3 h a 1 dia | 236 | 8.11 | 0.07% | 41% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (153): MFE mediano 3.7%, MAE mediano -0.5%, devolução média do melhor ponto 2.1%, captura mediana 0.50.
- Perdedores (444): MAE mediano -1.3%, MFE mediano 0.7%; 46 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 85.48; – do lucro antes de custos.
- Trades < 3 h: 361 (lucro -93.91); reentradas em < 24 h: 256 (lucro -41.38).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -90.82.
- Lucro por ano de fechamento: 2018: -8.3, 2019: -13.0, 2020: -21.0, 2021: -10.9, 2022: -15.5, 2023: -8.9, 2024: -8.3.

## LINK/USDT

Trades: 641; lucro líquido: -143.22.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 466 | -278.76 | – | -1.29% | 0% | 0.6 h |
| take_profit_1p8 | 94 | 125.37 | – | 2.87% | 100% | 2.4 h |
| time_exit_6h | 81 | 10.17 | – | 0.27% | 64% | 6.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 485 | -175.75 | -0.78% | 11% |
| 3 h a 1 dia | 156 | 32.53 | 0.46% | 58% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (146): MFE mediano 3.6%, MAE mediano -0.5%, devolução média do melhor ponto 2.1%, captura mediana 0.52.
- Perdedores (495): MAE mediano -1.6%, MFE mediano 0.9%; 93 (19%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 88.52; – do lucro antes de custos.
- Trades < 3 h: 485 (lucro -175.75); reentradas em < 24 h: 312 (lucro -81.59).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -146.92.
- Lucro por ano de fechamento: 2019: -32.7, 2020: -31.9, 2021: -37.6, 2022: -20.2, 2023: -11.3, 2024: -9.5.

## DOGE/USDT

Trades: 618; lucro líquido: -71.38.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 432 | -269.75 | – | -1.29% | 0% | 0.8 h |
| take_profit_1p8 | 103 | 193.50 | – | 3.89% | 100% | 2.1 h |
| time_exit_6h | 83 | 4.88 | – | 0.12% | 53% | 6.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 447 | -74.53 | -0.34% | 17% |
| 3 h a 1 dia | 171 | 3.15 | 0.04% | 43% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (147): MFE mediano 3.9%, MAE mediano -0.5%, devolução média do melhor ponto 2.6%, captura mediana 0.51.
- Perdedores (471): MAE mediano -1.5%, MFE mediano 0.7%; 95 (20%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 89.41; 496% do lucro antes de custos.
- Trades < 3 h: 447 (lucro -74.53); reentradas em < 24 h: 300 (lucro 6.11).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -104.35.
- Lucro por ano de fechamento: 2019: -10.2, 2020: -21.8, 2021: 2.4, 2022: -11.1, 2023: -23.7, 2024: -6.8.

## SOL/USDT

Trades: 517; lucro líquido: -77.54.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 375 | -232.73 | – | -1.29% | 0% | 0.6 h |
| take_profit_1p8 | 102 | 149.42 | – | 3.04% | 100% | 2.5 h |
| time_exit_6h | 40 | 5.77 | – | 0.31% | 62% | 6.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 406 | -123.50 | -0.63% | 15% |
| 3 h a 1 dia | 111 | 45.96 | 0.86% | 61% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (127): MFE mediano 4.0%, MAE mediano -0.4%, devolução média do melhor ponto 2.2%, captura mediana 0.57.
- Perdedores (390): MAE mediano -1.7%, MFE mediano 1.0%; 83 (21%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 74.32; – do lucro antes de custos.
- Trades < 3 h: 406 (lucro -123.50); reentradas em < 24 h: 261 (lucro -41.16).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -81.17.
- Lucro por ano de fechamento: 2020: -8.0, 2021: -27.3, 2022: -23.6, 2023: -8.4, 2024: -10.3.
