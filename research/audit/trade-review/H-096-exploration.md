# Revisão de trades: H-096 (exploração)

Fonte dos trades: `research/experiments/20261110T061429Z-h-096-exploration-btc-usdt/raw/backtest-result-2026-11-10_06-33-51.zip`; `research/experiments/20261110T061429Z-h-096-exploration-eth-usdt/raw/backtest-result-2026-11-10_06-40-23.zip`; `research/experiments/20261110T061429Z-h-096-exploration-bnb-usdt/raw/backtest-result-2026-11-10_06-47-03.zip`; `research/experiments/20261110T061429Z-h-096-exploration-xrp-usdt/raw/backtest-result-2026-11-10_06-53-49.zip`; `research/experiments/20261110T061429Z-h-096-exploration-ada-usdt/raw/backtest-result-2026-11-10_07-00-26.zip`; `research/experiments/20261110T061429Z-h-096-exploration-ltc-usdt/raw/backtest-result-2026-11-10_07-07-19.zip`; `research/experiments/20261110T061429Z-h-096-exploration-link-usdt/raw/backtest-result-2026-11-10_07-13-54.zip`; `research/experiments/20261110T061429Z-h-096-exploration-doge-usdt/raw/backtest-result-2026-11-10_07-19-51.zip`; `research/experiments/20261110T061429Z-h-096-exploration-sol-usdt/raw/backtest-result-2026-11-10_07-25-08.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 786; lucro líquido: -115.83.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 375 | -267.42 | – | -1.50% | 0% | 2.1 h |
| time_exit | 304 | 29.42 | – | 0.20% | 56% | 5.7 h |
| take_profit_rh | 103 | 128.67 | – | 2.61% | 100% | 3.6 h |
| stop_loss | 4 | -6.50 | – | -3.29% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 311 | -161.53 | -1.09% | 11% |
| 3 h a 1 dia | 475 | 45.71 | 0.19% | 50% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (274): MFE mediano 1.9%, MAE mediano -0.4%, devolução média do melhor ponto 1.0%, captura mediana 0.53.
- Perdedores (512): MAE mediano -1.2%, MFE mediano 0.5%; 16 (3%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 111.89; – do lucro antes de custos.
- Trades < 3 h: 311 (lucro -161.53); reentradas em < 24 h: 243 (lucro -36.51).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -123.95.
- Lucro por ano de fechamento: 2017: -4.1, 2018: -6.3, 2019: -12.9, 2020: -21.6, 2021: -24.8, 2022: -21.9, 2023: -11.3, 2024: -13.0.

## ETH/USDT

Trades: 889; lucro líquido: -121.75.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 455 | -325.26 | – | -1.52% | 0% | 1.9 h |
| time_exit | 319 | 76.69 | – | 0.51% | 62% | 5.8 h |
| take_profit_rh | 114 | 128.33 | – | 2.40% | 100% | 3.5 h |
| stop_loss | 1 | -1.51 | – | -3.29% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 379 | -202.30 | -1.13% | 11% |
| 3 h a 1 dia | 510 | 80.55 | 0.33% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (313): MFE mediano 2.2%, MAE mediano -0.4%, devolução média do melhor ponto 1.0%, captura mediana 0.58.
- Perdedores (576): MAE mediano -1.4%, MFE mediano 0.5%; 33 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 124.84; 4045% do lucro antes de custos.
- Trades < 3 h: 379 (lucro -202.30); reentradas em < 24 h: 314 (lucro -75.78).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -127.58.
- Lucro por ano de fechamento: 2017: -3.1, 2018: -16.9, 2019: -31.3, 2020: -26.3, 2021: -7.4, 2022: -12.0, 2023: -9.1, 2024: -15.8.

## BNB/USDT

Trades: 881; lucro líquido: -132.67.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 434 | -305.62 | – | -1.52% | 0% | 1.9 h |
| time_exit | 350 | 74.22 | – | 0.45% | 61% | 5.8 h |
| take_profit_rh | 93 | 104.98 | – | 2.47% | 100% | 3.2 h |
| stop_loss | 4 | -6.25 | – | -3.29% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 374 | -193.06 | -1.11% | 12% |
| 3 h a 1 dia | 507 | 60.39 | 0.26% | 52% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (306): MFE mediano 2.1%, MAE mediano -0.4%, devolução média do melhor ponto 1.1%, captura mediana 0.54.
- Perdedores (575): MAE mediano -1.4%, MFE mediano 0.5%; 28 (5%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 121.28; – do lucro antes de custos.
- Trades < 3 h: 374 (lucro -193.06); reentradas em < 24 h: 297 (lucro -43.90).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -138.35.
- Lucro por ano de fechamento: 2017: -5.0, 2018: -21.3, 2019: -30.0, 2020: -36.8, 2021: -16.3, 2022: -3.5, 2023: -10.1, 2024: -9.6.

## XRP/USDT

Trades: 877; lucro líquido: -137.39.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 438 | -303.93 | – | -1.50% | 0% | 1.9 h |
| time_exit | 335 | 67.07 | – | 0.44% | 67% | 5.9 h |
| take_profit_rh | 101 | 104.14 | – | 2.24% | 100% | 3.7 h |
| stop_loss | 3 | -4.67 | – | -3.29% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 375 | -202.27 | -1.17% | 10% |
| 3 h a 1 dia | 502 | 64.88 | 0.28% | 57% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (325): MFE mediano 1.9%, MAE mediano -0.4%, devolução média do melhor ponto 1.1%, captura mediana 0.53.
- Perdedores (552): MAE mediano -1.3%, MFE mediano 0.4%; 15 (3%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 120.96; – do lucro antes de custos.
- Trades < 3 h: 375 (lucro -202.27); reentradas em < 24 h: 302 (lucro -39.53).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -141.73.
- Lucro por ano de fechamento: 2018: -21.6, 2019: -24.2, 2020: -16.9, 2021: -28.5, 2022: -31.8, 2023: -9.8, 2024: -4.6.

## ADA/USDT

Trades: 961; lucro líquido: -169.99.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 515 | -359.54 | – | -1.53% | 0% | 1.8 h |
| time_exit | 327 | 58.26 | – | 0.39% | 63% | 5.9 h |
| take_profit_rh | 116 | 135.91 | – | 2.59% | 100% | 3.5 h |
| stop_loss | 3 | -4.62 | – | -3.28% | 0% | 0.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 439 | -223.81 | -1.12% | 10% |
| 3 h a 1 dia | 522 | 53.82 | 0.23% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (322): MFE mediano 2.3%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.56.
- Perdedores (639): MAE mediano -1.4%, MFE mediano 0.5%; 37 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 130.22; – do lucro antes de custos.
- Trades < 3 h: 439 (lucro -223.81); reentradas em < 24 h: 334 (lucro -63.46).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -178.49.
- Lucro por ano de fechamento: 2018: -32.3, 2019: -33.4, 2020: -32.9, 2021: -10.7, 2022: -27.1, 2023: -15.6, 2024: -18.0.

## LTC/USDT

Trades: 998; lucro líquido: -162.21.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 537 | -395.27 | – | -1.59% | 0% | 1.9 h |
| time_exit | 323 | 95.93 | – | 0.63% | 68% | 5.8 h |
| take_profit_rh | 130 | 149.59 | – | 2.49% | 100% | 3.5 h |
| stop_loss | 8 | -12.46 | – | -3.28% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 457 | -240.12 | -1.13% | 12% |
| 3 h a 1 dia | 541 | 77.91 | 0.30% | 55% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (350): MFE mediano 2.3%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.57.
- Perdedores (648): MAE mediano -1.5%, MFE mediano 0.5%; 45 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 137.87; – do lucro antes de custos.
- Trades < 3 h: 457 (lucro -240.12); reentradas em < 24 h: 373 (lucro -79.46).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -171.77.
- Lucro por ano de fechamento: 2017: -5.9, 2018: -10.1, 2019: -24.3, 2020: -39.5, 2021: -21.0, 2022: -19.9, 2023: -20.9, 2024: -20.6.

## LINK/USDT

Trades: 905; lucro líquido: -131.19.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 520 | -387.47 | – | -1.59% | 0% | 1.8 h |
| time_exit | 244 | 72.52 | – | 0.63% | 62% | 5.8 h |
| take_profit_rh | 137 | 189.85 | – | 2.96% | 100% | 3.0 h |
| stop_loss | 4 | -6.09 | – | -3.27% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 483 | -213.33 | -0.94% | 15% |
| 3 h a 1 dia | 422 | 82.14 | 0.42% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (288): MFE mediano 2.8%, MAE mediano -0.5%, devolução média do melhor ponto 1.3%, captura mediana 0.65.
- Perdedores (617): MAE mediano -1.5%, MFE mediano 0.5%; 44 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 126.47; – do lucro antes de custos.
- Trades < 3 h: 483 (lucro -213.33); reentradas em < 24 h: 347 (lucro -64.10).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -138.60.
- Lucro por ano de fechamento: 2019: -20.6, 2020: -43.0, 2021: -7.6, 2022: -3.6, 2023: -38.6, 2024: -17.9.

## DOGE/USDT

Trades: 698; lucro líquido: -116.39.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 370 | -267.41 | – | -1.54% | 0% | 1.9 h |
| time_exit | 241 | 50.83 | – | 0.45% | 64% | 5.7 h |
| take_profit_rh | 85 | 103.29 | – | 2.59% | 100% | 3.3 h |
| stop_loss | 2 | -3.11 | – | -3.27% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 314 | -156.00 | -1.06% | 12% |
| 3 h a 1 dia | 384 | 39.61 | 0.22% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (239): MFE mediano 2.2%, MAE mediano -0.4%, devolução média do melhor ponto 1.3%, captura mediana 0.53.
- Perdedores (459): MAE mediano -1.3%, MFE mediano 0.6%; 27 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 98.21; – do lucro antes de custos.
- Trades < 3 h: 314 (lucro -156.00); reentradas em < 24 h: 246 (lucro -41.64).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -120.77.
- Lucro por ano de fechamento: 2019: -6.5, 2020: -28.1, 2021: -26.3, 2022: -22.3, 2023: -22.9, 2024: -10.2.

## SOL/USDT

Trades: 634; lucro líquido: -96.94.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 381 | -302.23 | – | -1.65% | 0% | 1.8 h |
| time_exit | 161 | 68.83 | – | 0.88% | 73% | 5.8 h |
| take_profit_rh | 91 | 138.10 | – | 3.14% | 100% | 3.3 h |
| stop_loss | 1 | -1.64 | – | -3.29% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 336 | -174.65 | -1.08% | 12% |
| 3 h a 1 dia | 298 | 77.71 | 0.53% | 56% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (208): MFE mediano 2.9%, MAE mediano -0.5%, devolução média do melhor ponto 1.4%, captura mediana 0.60.
- Perdedores (426): MAE mediano -1.6%, MFE mediano 0.6%; 47 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 91.30; – do lucro antes de custos.
- Trades < 3 h: 336 (lucro -174.65); reentradas em < 24 h: 254 (lucro -52.60).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -103.39.
- Lucro por ano de fechamento: 2020: -10.6, 2021: -1.8, 2022: -25.9, 2023: -33.9, 2024: -24.7.
