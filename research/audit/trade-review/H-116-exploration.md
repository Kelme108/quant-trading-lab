# Revisão de trades: H-116 (exploração)

Fonte dos trades: `research/experiments/20261112T031706Z-h-116-exploration-btc-usdt/raw/backtest-result-2026-11-12_03-37-26.zip`; `research/experiments/20261112T031706Z-h-116-exploration-eth-usdt/raw/backtest-result-2026-11-12_03-45-35.zip`; `research/experiments/20261112T031706Z-h-116-exploration-bnb-usdt/raw/backtest-result-2026-11-12_03-53-24.zip`; `research/experiments/20261112T031706Z-h-116-exploration-xrp-usdt/raw/backtest-result-2026-11-12_04-00-40.zip`; `research/experiments/20261112T031706Z-h-116-exploration-ada-usdt/raw/backtest-result-2026-11-12_04-06-34.zip`; `research/experiments/20261112T031706Z-h-116-exploration-ltc-usdt/raw/backtest-result-2026-11-12_04-12-49.zip`; `research/experiments/20261112T031706Z-h-116-exploration-link-usdt/raw/backtest-result-2026-11-12_04-19-04.zip`; `research/experiments/20261112T031706Z-h-116-exploration-doge-usdt/raw/backtest-result-2026-11-12_04-24-24.zip`; `research/experiments/20261112T031706Z-h-116-exploration-sol-usdt/raw/backtest-result-2026-11-12_04-29-01.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 1009; lucro líquido: -92.56.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 479 | -344.05 | – | -1.50% | 0% | 3.9 h |
| time_exit_12h | 364 | 36.64 | – | 0.21% | 52% | 12.0 h |
| take_profit_2r | 160 | 224.40 | – | 2.92% | 100% | 5.9 h |
| stop_loss | 6 | -9.56 | – | -3.29% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 236 | -116.97 | -1.04% | 10% |
| 3 h a 1 dia | 773 | 24.41 | 0.07% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (350): MFE mediano 2.7%, MAE mediano -0.4%, devolução média do melhor ponto 1.3%, captura mediana 0.57.
- Perdedores (659): MAE mediano -1.3%, MFE mediano 0.5%; 38 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 144.38; 279% do lucro antes de custos.
- Trades < 3 h: 236 (lucro -116.97); reentradas em < 24 h: 537 (lucro -45.60).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -96.76.
- Lucro por ano de fechamento: 2017: -1.1, 2018: -3.9, 2019: -21.6, 2020: -11.5, 2021: -6.4, 2022: -32.8, 2023: -11.6, 2024: -3.7.

## ETH/USDT

Trades: 888; lucro líquido: -140.33.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 487 | -358.17 | – | -1.57% | 0% | 3.6 h |
| time_exit_12h | 236 | 31.61 | – | 0.28% | 57% | 12.0 h |
| take_profit_2r | 152 | 206.51 | – | 2.89% | 100% | 5.9 h |
| stop_loss | 13 | -20.28 | – | -3.29% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 264 | -157.16 | -1.27% | 9% |
| 3 h a 1 dia | 624 | 16.83 | 0.05% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (287): MFE mediano 3.0%, MAE mediano -0.5%, devolução média do melhor ponto 1.5%, captura mediana 0.57.
- Perdedores (601): MAE mediano -1.5%, MFE mediano 0.6%; 44 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 123.96; – do lucro antes de custos.
- Trades < 3 h: 264 (lucro -157.16); reentradas em < 24 h: 427 (lucro -61.07).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -144.83.
- Lucro por ano de fechamento: 2017: 0.1, 2018: -16.5, 2019: -23.0, 2020: -12.5, 2021: -15.8, 2022: -35.4, 2023: -30.8, 2024: -6.4.

## BNB/USDT

Trades: 977; lucro líquido: -146.89.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 524 | -370.96 | – | -1.53% | 0% | 3.6 h |
| time_exit_12h | 262 | 34.50 | – | 0.28% | 58% | 12.0 h |
| take_profit_2r | 170 | 221.71 | – | 2.83% | 100% | 5.7 h |
| stop_loss | 21 | -32.14 | – | -3.28% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 294 | -169.61 | -1.25% | 10% |
| 3 h a 1 dia | 683 | 22.72 | 0.07% | 43% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (323): MFE mediano 3.0%, MAE mediano -0.5%, devolução média do melhor ponto 1.4%, captura mediana 0.58.
- Perdedores (654): MAE mediano -1.4%, MFE mediano 0.5%; 40 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 134.19; – do lucro antes de custos.
- Trades < 3 h: 294 (lucro -169.61); reentradas em < 24 h: 530 (lucro -90.87).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -150.11.
- Lucro por ano de fechamento: 2017: -5.8, 2018: -37.2, 2019: -20.6, 2020: -14.4, 2021: -2.2, 2022: -36.1, 2023: -23.6, 2024: -7.1.

## XRP/USDT

Trades: 677; lucro líquido: -110.91.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 388 | -293.81 | – | -1.60% | 0% | 3.7 h |
| time_exit_12h | 165 | 13.46 | – | 0.18% | 49% | 12.0 h |
| take_profit_2r | 120 | 175.58 | – | 3.08% | 100% | 5.7 h |
| stop_loss | 4 | -6.14 | – | -3.28% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 210 | -95.48 | -0.96% | 13% |
| 3 h a 1 dia | 467 | -15.42 | -0.07% | 37% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (201): MFE mediano 3.4%, MAE mediano -0.5%, devolução média do melhor ponto 1.7%, captura mediana 0.58.
- Perdedores (476): MAE mediano -1.5%, MFE mediano 0.6%; 41 (9%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 95.95; – do lucro antes de custos.
- Trades < 3 h: 210 (lucro -95.48); reentradas em < 24 h: 291 (lucro -57.28).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -114.75.
- Lucro por ano de fechamento: 2018: -9.7, 2019: -21.2, 2020: -18.9, 2021: -5.4, 2022: -20.2, 2023: -11.6, 2024: -23.8.

## ADA/USDT

Trades: 650; lucro líquido: -84.69.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 376 | -302.94 | – | -1.67% | 0% | 3.4 h |
| take_profit_2r | 133 | 215.71 | – | 3.36% | 100% | 5.9 h |
| time_exit_12h | 129 | 21.46 | – | 0.34% | 63% | 12.0 h |
| stop_loss | 12 | -18.92 | – | -3.28% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 208 | -122.35 | -1.23% | 10% |
| 3 h a 1 dia | 442 | 37.66 | 0.18% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (214): MFE mediano 3.6%, MAE mediano -0.6%, devolução média do melhor ponto 1.6%, captura mediana 0.63.
- Perdedores (436): MAE mediano -1.7%, MFE mediano 0.6%; 42 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 93.67; 1043% do lucro antes de custos.
- Trades < 3 h: 208 (lucro -122.35); reentradas em < 24 h: 262 (lucro -23.61).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -90.97.
- Lucro por ano de fechamento: 2018: -0.8, 2019: -23.1, 2020: 5.5, 2021: -18.0, 2022: -22.7, 2023: -18.9, 2024: -6.6.

## LTC/USDT

Trades: 748; lucro líquido: -103.54.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 418 | -331.64 | – | -1.65% | 0% | 3.1 h |
| time_exit_12h | 184 | 9.60 | – | 0.10% | 51% | 12.0 h |
| take_profit_2r | 139 | 229.73 | – | 3.41% | 100% | 5.9 h |
| stop_loss | 7 | -11.24 | – | -3.29% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 246 | -132.49 | -1.12% | 11% |
| 3 h a 1 dia | 502 | 28.95 | 0.12% | 41% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (232): MFE mediano 3.6%, MAE mediano -0.5%, devolução média do melhor ponto 1.5%, captura mediana 0.62.
- Perdedores (516): MAE mediano -1.6%, MFE mediano 0.6%; 48 (9%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 107.80; 2530% do lucro antes de custos.
- Trades < 3 h: 246 (lucro -132.49); reentradas em < 24 h: 325 (lucro -46.65).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -108.31.
- Lucro por ano de fechamento: 2018: -4.9, 2019: 0.7, 2020: -20.5, 2021: -13.8, 2022: -16.4, 2023: -37.6, 2024: -11.1.

## LINK/USDT

Trades: 580; lucro líquido: -92.74.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 349 | -300.33 | – | -1.78% | 0% | 3.0 h |
| take_profit_2r | 119 | 206.96 | – | 3.58% | 100% | 5.5 h |
| time_exit_12h | 103 | 14.79 | – | 0.29% | 57% | 12.0 h |
| stop_loss | 9 | -14.16 | – | -3.28% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 235 | -142.96 | -1.26% | 10% |
| 3 h a 1 dia | 345 | 50.23 | 0.30% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (178): MFE mediano 4.2%, MAE mediano -0.5%, devolução média do melhor ponto 1.7%, captura mediana 0.64.
- Perdedores (402): MAE mediano -1.8%, MFE mediano 0.8%; 60 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 83.88; – do lucro antes de custos.
- Trades < 3 h: 235 (lucro -142.96); reentradas em < 24 h: 249 (lucro -29.17).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -97.92.
- Lucro por ano de fechamento: 2019: -0.2, 2020: -2.7, 2021: -18.4, 2022: -35.3, 2023: -18.8, 2024: -17.3.

## DOGE/USDT

Trades: 546; lucro líquido: -62.36.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 303 | -237.94 | – | -1.63% | 0% | 3.4 h |
| time_exit_12h | 121 | 6.11 | – | 0.11% | 50% | 12.0 h |
| take_profit_2r | 110 | 188.56 | – | 3.57% | 100% | 4.9 h |
| stop_loss | 12 | -19.09 | – | -3.29% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 196 | -81.89 | -0.86% | 16% |
| 3 h a 1 dia | 350 | 19.53 | 0.12% | 39% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (170): MFE mediano 3.8%, MAE mediano -0.5%, devolução média do melhor ponto 2.0%, captura mediana 0.56.
- Perdedores (376): MAE mediano -1.6%, MFE mediano 0.6%; 46 (12%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 78.70; 482% do lucro antes de custos.
- Trades < 3 h: 196 (lucro -81.89); reentradas em < 24 h: 248 (lucro -21.53).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -70.01.
- Lucro por ano de fechamento: 2019: -14.3, 2020: -25.6, 2021: 6.3, 2022: -9.8, 2023: -10.4, 2024: -8.5.

## SOL/USDT

Trades: 379; lucro líquido: -43.19.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 230 | -199.77 | – | -1.78% | 0% | 3.0 h |
| take_profit_2r | 91 | 167.16 | – | 3.77% | 100% | 4.9 h |
| time_exit_12h | 46 | 8.87 | – | 0.40% | 52% | 12.0 h |
| stop_loss | 12 | -19.44 | – | -3.28% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 160 | -80.29 | -1.03% | 15% |
| 3 h a 1 dia | 219 | 37.10 | 0.35% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (115): MFE mediano 4.9%, MAE mediano -0.5%, devolução média do melhor ponto 2.0%, captura mediana 0.66.
- Perdedores (264): MAE mediano -2.0%, MFE mediano 0.8%; 39 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 55.32; 456% do lucro antes de custos.
- Trades < 3 h: 160 (lucro -80.29); reentradas em < 24 h: 158 (lucro -22.84).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -47.39.
- Lucro por ano de fechamento: 2020: -7.9, 2021: -5.0, 2022: -19.3, 2023: -2.4, 2024: -8.5.
