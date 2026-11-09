# Revisão de trades: H-058 (exploração)

Fonte dos trades: `research/experiments/20261109T005940Z-h-058-exploration-btc-usdt/raw/backtest-result-2026-11-09_01-14-24.zip`; `research/experiments/20261109T005940Z-h-058-exploration-eth-usdt/raw/backtest-result-2026-11-09_01-17-38.zip`; `research/experiments/20261109T005940Z-h-058-exploration-bnb-usdt/raw/backtest-result-2026-11-09_01-20-30.zip`; `research/experiments/20261109T005940Z-h-058-exploration-xrp-usdt/raw/backtest-result-2026-11-09_01-23-55.zip`; `research/experiments/20261109T005940Z-h-058-exploration-ada-usdt/raw/backtest-result-2026-11-09_01-27-33.zip`; `research/experiments/20261109T005940Z-h-058-exploration-ltc-usdt/raw/backtest-result-2026-11-09_01-31-07.zip`; `research/experiments/20261109T005940Z-h-058-exploration-link-usdt/raw/backtest-result-2026-11-09_01-34-33.zip`; `research/experiments/20261109T005940Z-h-058-exploration-doge-usdt/raw/backtest-result-2026-11-09_01-38-01.zip`; `research/experiments/20261109T005940Z-h-058-exploration-sol-usdt/raw/backtest-result-2026-11-09_01-41-16.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 1065; lucro líquido: -128.89.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_13utc | 840 | 217.51 | – | 0.55% | 53% | 17.0 h |
| stop_loss | 224 | -347.54 | – | -3.29% | 0% | 6.1 h |
| time_backstop_17h | 1 | 1.14 | – | 2.39% | 100% | 17.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 74 | -115.20 | -3.29% | 0% |
| 3 h a 1 dia | 991 | -13.69 | -0.03% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (447): MFE mediano 2.6%, MAE mediano -0.6%, devolução média do melhor ponto 1.5%, captura mediana 0.47.
- Perdedores (618): MAE mediano -2.3%, MFE mediano 0.7%; 64 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 147.66; 787% do lucro antes de custos.
- Trades < 3 h: 74 (lucro -115.20); reentradas em < 24 h: 488 (lucro -78.71).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -135.91.
- Lucro por ano de fechamento: 2017: 1.3, 2018: -54.3, 2019: -21.6, 2020: 1.5, 2021: 1.4, 2022: -32.5, 2023: -17.9, 2024: -6.7.

## ETH/USDT

Trades: 1044; lucro líquido: -137.57.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_13utc | 738 | 325.82 | – | 0.95% | 57% | 17.0 h |
| stop_loss | 304 | -466.05 | – | -3.29% | 0% | 5.7 h |
| time_backstop_17h | 1 | 3.81 | – | 8.11% | 100% | 17.0 h |
| force_exit | 1 | -1.14 | – | -2.66% | 0% | 4.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 107 | -164.57 | -3.29% | 0% |
| 3 h a 1 dia | 937 | 27.00 | 0.06% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (420): MFE mediano 3.4%, MAE mediano -0.7%, devolução média do melhor ponto 1.8%, captura mediana 0.52.
- Perdedores (624): MAE mediano -3.0%, MFE mediano 0.9%; 99 (16%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 142.96; 2650% do lucro antes de custos.
- Trades < 3 h: 107 (lucro -164.57); reentradas em < 24 h: 462 (lucro -97.77).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -145.18.
- Lucro por ano de fechamento: 2017: -25.8, 2018: -40.5, 2019: -24.9, 2020: 9.3, 2021: -5.2, 2022: -31.8, 2023: -14.5, 2024: -4.0.

## BNB/USDT

Trades: 1054; lucro líquido: -69.11.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_13utc | 746 | 416.98 | – | 1.15% | 61% | 17.0 h |
| stop_loss | 307 | -490.78 | – | -3.29% | 0% | 6.2 h |
| time_backstop_17h | 1 | 4.70 | – | 9.67% | 100% | 17.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 87 | -139.58 | -3.29% | 0% |
| 3 h a 1 dia | 967 | 70.47 | 0.15% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (458): MFE mediano 3.4%, MAE mediano -0.7%, devolução média do melhor ponto 2.0%, captura mediana 0.50.
- Perdedores (596): MAE mediano -3.0%, MFE mediano 0.9%; 110 (18%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 151.81; 184% do lucro antes de custos.
- Trades < 3 h: 87 (lucro -139.58); reentradas em < 24 h: 482 (lucro -32.43).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -84.15.
- Lucro por ano de fechamento: 2017: 14.1, 2018: -31.6, 2019: -28.2, 2020: -7.7, 2021: 21.7, 2022: -24.6, 2023: -13.5, 2024: 0.6.

## XRP/USDT

Trades: 891; lucro líquido: -192.65.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_13utc | 601 | 241.17 | – | 0.87% | 54% | 17.0 h |
| stop_loss | 289 | -434.00 | – | -3.29% | 0% | 6.0 h |
| force_exit | 1 | 0.19 | – | 0.47% | 100% | 3.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 93 | -140.29 | -3.29% | 0% |
| 3 h a 1 dia | 798 | -52.36 | -0.15% | 41% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (325): MFE mediano 3.2%, MAE mediano -0.7%, devolução média do melhor ponto 2.2%, captura mediana 0.47.
- Perdedores (566): MAE mediano -3.1%, MFE mediano 1.0%; 114 (20%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 120.33; – do lucro antes de custos.
- Trades < 3 h: 93 (lucro -140.29); reentradas em < 24 h: 371 (lucro -88.45).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -210.92.
- Lucro por ano de fechamento: 2018: -50.7, 2019: -31.1, 2020: 1.4, 2021: -20.2, 2022: -40.8, 2023: -33.8, 2024: -17.4.

## ADA/USDT

Trades: 920; lucro líquido: -206.49.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_13utc | 554 | 325.23 | – | 1.32% | 63% | 17.0 h |
| stop_loss | 365 | -535.49 | – | -3.28% | 0% | 6.2 h |
| time_backstop_17h | 1 | 3.77 | – | 7.98% | 100% | 17.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 102 | -150.60 | -3.28% | 0% |
| 3 h a 1 dia | 818 | -55.89 | -0.15% | 43% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (348): MFE mediano 3.9%, MAE mediano -0.8%, devolução média do melhor ponto 2.2%, captura mediana 0.49.
- Perdedores (572): MAE mediano -3.2%, MFE mediano 1.0%; 121 (21%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 121.06; – do lucro antes de custos.
- Trades < 3 h: 102 (lucro -150.60); reentradas em < 24 h: 402 (lucro -109.05).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -215.14.
- Lucro por ano de fechamento: 2018: -69.8, 2019: -14.3, 2020: -10.6, 2021: -33.2, 2022: -49.9, 2023: -16.3, 2024: -12.3.

## LTC/USDT

Trades: 985; lucro líquido: -92.50.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_13utc | 642 | 440.30 | – | 1.45% | 66% | 17.0 h |
| stop_loss | 342 | -534.19 | – | -3.28% | 0% | 6.3 h |
| time_backstop_17h | 1 | 1.39 | – | 2.90% | 100% | 17.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 100 | -156.86 | -3.28% | 0% |
| 3 h a 1 dia | 885 | 64.36 | 0.15% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (426): MFE mediano 3.6%, MAE mediano -0.8%, devolução média do melhor ponto 1.9%, captura mediana 0.52.
- Perdedores (559): MAE mediano -3.2%, MFE mediano 1.1%; 126 (23%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 139.10; 299% do lucro antes de custos.
- Trades < 3 h: 100 (lucro -156.86); reentradas em < 24 h: 441 (lucro -83.58).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -102.00.
- Lucro por ano de fechamento: 2017: -5.3, 2018: -58.4, 2019: -13.3, 2020: 14.6, 2021: 21.6, 2022: -34.8, 2023: -7.6, 2024: -9.4.

## LINK/USDT

Trades: 804; lucro líquido: -89.28.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_13utc | 478 | 427.04 | – | 1.85% | 67% | 17.0 h |
| stop_loss | 326 | -516.32 | – | -3.28% | 0% | 6.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 93 | -147.67 | -3.28% | 0% |
| 3 h a 1 dia | 711 | 58.39 | 0.17% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (322): MFE mediano 4.7%, MAE mediano -0.9%, devolução média do melhor ponto 2.3%, captura mediana 0.58.
- Perdedores (482): MAE mediano -3.3%, MFE mediano 1.2%; 114 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 115.54; 440% do lucro antes de custos.
- Trades < 3 h: 93 (lucro -147.67); reentradas em < 24 h: 345 (lucro -46.13).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -98.61.
- Lucro por ano de fechamento: 2019: -16.5, 2020: -20.4, 2021: 3.8, 2022: -32.4, 2023: -0.8, 2024: -23.1.

## DOGE/USDT

Trades: 803; lucro líquido: -116.72.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_13utc | 536 | 300.68 | – | 1.18% | 60% | 17.0 h |
| stop_loss | 267 | -417.40 | – | -3.28% | 0% | 6.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 89 | -139.63 | -3.28% | 0% |
| 3 h a 1 dia | 714 | 22.91 | 0.07% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (321): MFE mediano 3.5%, MAE mediano -0.7%, devolução média do melhor ponto 2.5%, captura mediana 0.45.
- Perdedores (482): MAE mediano -3.2%, MFE mediano 1.0%; 113 (23%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 113.81; – do lucro antes de custos.
- Trades < 3 h: 89 (lucro -139.63); reentradas em < 24 h: 363 (lucro -53.25).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -144.93.
- Lucro por ano de fechamento: 2019: -29.1, 2020: -6.4, 2021: -2.3, 2022: -42.8, 2023: -16.4, 2024: -19.7.

## SOL/USDT

Trades: 578; lucro líquido: -127.98.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_13utc | 298 | 303.11 | – | 2.17% | 73% | 17.0 h |
| stop_loss | 280 | -431.09 | – | -3.28% | 0% | 5.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 101 | -156.24 | -3.28% | 0% |
| 3 h a 1 dia | 477 | 28.26 | 0.13% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (218): MFE mediano 4.4%, MAE mediano -1.0%, devolução média do melhor ponto 2.4%, captura mediana 0.54.
- Perdedores (360): MAE mediano -3.5%, MFE mediano 1.1%; 96 (27%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 80.08; – do lucro antes de custos.
- Trades < 3 h: 101 (lucro -156.24); reentradas em < 24 h: 239 (lucro -80.88).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -136.55.
- Lucro por ano de fechamento: 2020: -25.8, 2021: -16.8, 2022: -56.3, 2023: -18.6, 2024: -10.4.
