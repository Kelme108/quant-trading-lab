# Revisão de trades: H-068 (exploração)

Fonte dos trades: `research/experiments/20261110T015551Z-h-068-exploration-btc-usdt/raw/backtest-result-2026-11-10_02-13-37.zip`; `research/experiments/20261110T015551Z-h-068-exploration-eth-usdt/raw/backtest-result-2026-11-10_02-19-17.zip`; `research/experiments/20261110T015551Z-h-068-exploration-bnb-usdt/raw/backtest-result-2026-11-10_02-24-52.zip`; `research/experiments/20261110T015551Z-h-068-exploration-xrp-usdt/raw/backtest-result-2026-11-10_02-30-02.zip`; `research/experiments/20261110T015551Z-h-068-exploration-ada-usdt/raw/backtest-result-2026-11-10_02-35-11.zip`; `research/experiments/20261110T015551Z-h-068-exploration-ltc-usdt/raw/backtest-result-2026-11-10_02-40-36.zip`; `research/experiments/20261110T015551Z-h-068-exploration-link-usdt/raw/backtest-result-2026-11-10_02-45-53.zip`; `research/experiments/20261110T015551Z-h-068-exploration-doge-usdt/raw/backtest-result-2026-11-10_02-50-39.zip`; `research/experiments/20261110T015551Z-h-068-exploration-sol-usdt/raw/backtest-result-2026-11-10_02-55-05.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 890; lucro líquido: -102.25.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12_bars | 485 | 312.65 | – | 1.39% | 63% | 12.0 h |
| stop_loss | 351 | -376.30 | – | -2.29% | 0% | 3.1 h |
| close_below_signal_low | 53 | -38.49 | – | -1.57% | 0% | 5.8 h |
| force_exit | 1 | -0.11 | – | -0.25% | 0% | 3.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 193 | -203.33 | -2.24% | 0% |
| 3 h a 1 dia | 697 | 101.08 | 0.31% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (307): MFE mediano 3.6%, MAE mediano -0.5%, devolução média do melhor ponto 1.9%, captura mediana 0.52.
- Perdedores (583): MAE mediano -2.2%, MFE mediano 0.9%; 109 (19%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 123.42; 583% do lucro antes de custos.
- Trades < 3 h: 193 (lucro -203.33); reentradas em < 24 h: 405 (lucro -95.15).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -108.56.
- Lucro por ano de fechamento: 2017: -27.9, 2018: -29.4, 2019: -2.4, 2020: -18.8, 2021: -15.2, 2022: -12.4, 2023: 0.4, 2024: 3.5.

## ETH/USDT

Trades: 1033; lucro líquido: -118.04.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 516 | -549.04 | – | -2.29% | 0% | 2.6 h |
| time_exit_12_bars | 481 | 457.10 | – | 2.06% | 74% | 12.0 h |
| close_below_signal_low | 36 | -26.11 | – | -1.61% | 0% | 6.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 335 | -355.87 | -2.28% | 0% |
| 3 h a 1 dia | 698 | 237.83 | 0.74% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (354): MFE mediano 4.2%, MAE mediano -0.6%, devolução média do melhor ponto 2.2%, captura mediana 0.55.
- Perdedores (679): MAE mediano -2.4%, MFE mediano 1.0%; 162 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 142.42; 584% do lucro antes de custos.
- Trades < 3 h: 335 (lucro -355.87); reentradas em < 24 h: 561 (lucro -129.32).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -128.71.
- Lucro por ano de fechamento: 2017: -24.2, 2018: -53.2, 2019: 6.2, 2020: -6.0, 2021: -15.6, 2022: -10.9, 2023: -7.3, 2024: -7.0.

## BNB/USDT

Trades: 965; lucro líquido: -179.78.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 511 | -511.89 | – | -2.29% | 0% | 2.4 h |
| time_exit_12_bars | 401 | 368.52 | – | 2.15% | 72% | 12.0 h |
| close_below_signal_low | 53 | -36.40 | – | -1.63% | 0% | 4.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 348 | -347.62 | -2.27% | 0% |
| 3 h a 1 dia | 617 | 167.85 | 0.64% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (287): MFE mediano 4.0%, MAE mediano -0.8%, devolução média do melhor ponto 2.5%, captura mediana 0.51.
- Perdedores (678): MAE mediano -2.5%, MFE mediano 1.0%; 192 (28%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 124.32; – do lucro antes de custos.
- Trades < 3 h: 348 (lucro -347.62); reentradas em < 24 h: 514 (lucro -141.35).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -194.27.
- Lucro por ano de fechamento: 2017: -63.6, 2018: -77.9, 2019: -2.4, 2020: -19.1, 2021: 21.9, 2022: -22.0, 2023: -17.0, 2024: 0.3.

## XRP/USDT

Trades: 860; lucro líquido: -153.53.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 514 | -544.83 | – | -2.29% | 0% | 2.5 h |
| time_exit_12_bars | 320 | 410.89 | – | 2.78% | 79% | 12.0 h |
| close_below_signal_low | 26 | -19.58 | – | -1.65% | 0% | 6.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 331 | -351.65 | -2.29% | 0% |
| 3 h a 1 dia | 529 | 198.12 | 0.81% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (253): MFE mediano 4.8%, MAE mediano -0.7%, devolução média do melhor ponto 3.3%, captura mediana 0.49.
- Perdedores (607): MAE mediano -2.5%, MFE mediano 1.0%; 196 (32%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 118.56; – do lucro antes de custos.
- Trades < 3 h: 331 (lucro -351.65); reentradas em < 24 h: 481 (lucro -92.45).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -173.17.
- Lucro por ano de fechamento: 2018: -32.4, 2019: -22.3, 2020: -10.3, 2021: -43.6, 2022: -20.2, 2023: -13.1, 2024: -11.5.

## ADA/USDT

Trades: 990; lucro líquido: -102.54.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 594 | -635.00 | – | -2.28% | 0% | 2.6 h |
| time_exit_12_bars | 375 | 546.99 | – | 3.14% | 80% | 12.0 h |
| close_below_signal_low | 21 | -14.53 | – | -1.51% | 0% | 5.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 358 | -382.67 | -2.28% | 0% |
| 3 h a 1 dia | 632 | 280.13 | 0.95% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (301): MFE mediano 5.4%, MAE mediano -0.9%, devolução média do melhor ponto 2.7%, captura mediana 0.57.
- Perdedores (689): MAE mediano -2.6%, MFE mediano 1.1%; 208 (30%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 138.22; 387% do lucro antes de custos.
- Trades < 3 h: 358 (lucro -382.67); reentradas em < 24 h: 575 (lucro -108.52).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -114.27.
- Lucro por ano de fechamento: 2018: -28.3, 2019: -15.8, 2020: -7.1, 2021: -38.9, 2022: -31.1, 2023: 20.2, 2024: -1.7.

## LTC/USDT

Trades: 988; lucro líquido: -174.28.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 551 | -570.40 | – | -2.28% | 0% | 2.8 h |
| time_exit_12_bars | 396 | 425.55 | – | 2.39% | 76% | 12.0 h |
| close_below_signal_low | 41 | -29.42 | – | -1.63% | 0% | 5.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 338 | -349.68 | -2.27% | 0% |
| 3 h a 1 dia | 650 | 175.40 | 0.60% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (302): MFE mediano 4.4%, MAE mediano -0.8%, devolução média do melhor ponto 2.5%, captura mediana 0.50.
- Perdedores (686): MAE mediano -2.5%, MFE mediano 1.0%; 155 (23%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 132.95; – do lucro antes de custos.
- Trades < 3 h: 338 (lucro -349.68); reentradas em < 24 h: 519 (lucro -134.41).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -186.87.
- Lucro por ano de fechamento: 2018: -75.8, 2019: -0.4, 2020: -19.1, 2021: -24.2, 2022: -27.5, 2023: -21.5, 2024: -5.8.

## LINK/USDT

Trades: 925; lucro líquido: -130.87.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 587 | -627.16 | – | -2.29% | 0% | 2.6 h |
| time_exit_12_bars | 313 | 514.79 | – | 3.53% | 85% | 12.0 h |
| close_below_signal_low | 25 | -18.50 | – | -1.61% | 0% | 4.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 384 | -410.17 | -2.27% | 0% |
| 3 h a 1 dia | 541 | 279.30 | 1.10% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (266): MFE mediano 5.7%, MAE mediano -0.8%, devolução média do melhor ponto 3.0%, captura mediana 0.56.
- Perdedores (659): MAE mediano -2.6%, MFE mediano 1.3%; 214 (32%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 128.76; – do lucro antes de custos.
- Trades < 3 h: 384 (lucro -410.17); reentradas em < 24 h: 535 (lucro -91.50).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -148.75.
- Lucro por ano de fechamento: 2019: -23.5, 2020: -37.0, 2021: -29.2, 2022: -14.9, 2023: -19.7, 2024: -6.6.

## DOGE/USDT

Trades: 718; lucro líquido: 49.22.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 428 | -520.16 | -1057% | -2.29% | 0% | 2.1 h |
| time_exit_12_bars | 258 | 596.05 | 1211% | 4.42% | 76% | 12.0 h |
| close_below_signal_low | 32 | -26.68 | -54% | -1.64% | 0% | 4.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 306 | -370.02 | -2.27% | 0% |
| 3 h a 1 dia | 412 | 419.24 | 1.95% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (197): MFE mediano 5.6%, MAE mediano -0.8%, devolução média do melhor ponto 5.7%, captura mediana 0.47.
- Perdedores (521): MAE mediano -2.6%, MFE mediano 1.2%; 173 (33%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 113.32; 70% do lucro antes de custos.
- Trades < 3 h: 306 (lucro -370.02); reentradas em < 24 h: 414 (lucro 108.64).
- Maior trade = 194% do lucro; top 5 = 408%; top 10 = 563%; lucro sem o melhor = -46.19.
- Lucro por ano de fechamento: 2019: -4.8, 2020: -8.1, 2021: 87.1, 2022: -1.5, 2023: -16.4, 2024: -7.2.

## SOL/USDT

Trades: 699; lucro líquido: -79.56.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 466 | -508.84 | – | -2.29% | 0% | 2.0 h |
| time_exit_12_bars | 227 | 434.40 | – | 4.02% | 84% | 12.0 h |
| close_below_signal_low | 6 | -5.13 | – | -1.82% | 0% | 4.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 324 | -353.72 | -2.28% | 0% |
| 3 h a 1 dia | 375 | 274.16 | 1.54% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (190): MFE mediano 6.7%, MAE mediano -0.9%, devolução média do melhor ponto 3.6%, captura mediana 0.53.
- Perdedores (509): MAE mediano -2.7%, MFE mediano 1.4%; 179 (35%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 99.57; 498% do lucro antes de custos.
- Trades < 3 h: 324 (lucro -353.72); reentradas em < 24 h: 422 (lucro -74.40).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -90.36.
- Lucro por ano de fechamento: 2020: -31.1, 2021: 3.2, 2022: -52.9, 2023: 14.5, 2024: -13.3.
