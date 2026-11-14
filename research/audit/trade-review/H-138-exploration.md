# Revisão de trades: H-138 (exploração)

Fonte dos trades: `research/experiments/20261114T052433Z-h-138-exploration-btc-usdt/raw/backtest-result-2026-11-14_05-54-48.zip`; `research/experiments/20261114T052433Z-h-138-exploration-eth-usdt/raw/backtest-result-2026-11-14_05-54-56.zip`; `research/experiments/20261114T052433Z-h-138-exploration-bnb-usdt/raw/backtest-result-2026-11-14_05-54-54.zip`; `research/experiments/20261114T052433Z-h-138-exploration-xrp-usdt/raw/backtest-result-2026-11-14_06-01-51.zip`; `research/experiments/20261114T052433Z-h-138-exploration-ada-usdt/raw/backtest-result-2026-11-14_06-02-27.zip`; `research/experiments/20261114T052433Z-h-138-exploration-ltc-usdt/raw/backtest-result-2026-11-14_06-02-30.zip`; `research/experiments/20261114T052433Z-h-138-exploration-link-usdt/raw/backtest-result-2026-11-14_06-09-02.zip`; `research/experiments/20261114T052433Z-h-138-exploration-doge-usdt/raw/backtest-result-2026-11-14_06-09-41.zip`; `research/experiments/20261114T052433Z-h-138-exploration-sol-usdt/raw/backtest-result-2026-11-14_06-09-40.zip`; `research/experiments/20261114T052433Z-h-138-exploration-avax-usdt/raw/backtest-result-2026-11-14_06-15-53.zip`; `research/experiments/20261114T052433Z-h-138-exploration-dot-usdt/raw/backtest-result-2026-11-14_06-16-12.zip`; `research/experiments/20261114T052433Z-h-138-exploration-trx-usdt/raw/backtest-result-2026-11-14_06-16-54.zip`; `research/experiments/20261114T052433Z-h-138-exploration-near-usdt/raw/backtest-result-2026-11-14_06-22-35.zip`; `research/experiments/20261114T052433Z-h-138-exploration-uni-usdt/raw/backtest-result-2026-11-14_06-22-45.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 903; lucro líquido: -93.53.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_session_end | 818 | 38.31 | – | 0.10% | 41% | 4.3 h |
| stop_loss | 78 | -123.55 | – | -3.29% | 0% | 2.2 h |
| close_below_gsv_dn | 7 | -8.29 | – | -2.54% | 0% | 3.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 268 | -96.23 | -0.75% | 31% |
| 3 h a 1 dia | 635 | 2.69 | 0.01% | 40% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (337): MFE mediano 2.1%, MAE mediano -0.4%, devolução média do melhor ponto 1.3%, captura mediana 0.49.
- Perdedores (566): MAE mediano -1.4%, MFE mediano 0.5%; 34 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 128.15; 370% do lucro antes de custos.
- Trades < 3 h: 268 (lucro -96.23); reentradas em < 24 h: 511 (lucro -51.97).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -98.70.
- Lucro por ano de fechamento: 2017: -1.1, 2018: -27.7, 2019: -16.6, 2020: -15.7, 2021: -10.3, 2022: -18.4, 2023: 2.8, 2024: -6.5.

## ETH/USDT

Trades: 1164; lucro líquido: -156.76.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_session_end | 996 | 98.33 | – | 0.20% | 44% | 4.6 h |
| stop_loss | 151 | -234.86 | – | -3.29% | 0% | 2.6 h |
| close_below_gsv_dn | 17 | -20.23 | – | -2.58% | 0% | 4.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 305 | -129.04 | -0.90% | 32% |
| 3 h a 1 dia | 859 | -27.72 | -0.08% | 40% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (438): MFE mediano 2.7%, MAE mediano -0.4%, devolução média do melhor ponto 1.6%, captura mediana 0.48.
- Perdedores (726): MAE mediano -1.7%, MFE mediano 0.6%; 64 (9%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 162.52; 2824% do lucro antes de custos.
- Trades < 3 h: 305 (lucro -129.04); reentradas em < 24 h: 727 (lucro -117.58).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -162.34.
- Lucro por ano de fechamento: 2017: -0.4, 2018: -34.0, 2019: -19.8, 2020: -14.6, 2021: -7.2, 2022: -43.5, 2023: -16.9, 2024: -20.4.

## BNB/USDT

Trades: 1193; lucro líquido: -172.57.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_session_end | 957 | 176.99 | – | 0.40% | 47% | 4.5 h |
| stop_loss | 213 | -323.14 | – | -3.29% | 0% | 2.2 h |
| close_below_gsv_dn | 23 | -26.42 | – | -2.58% | 0% | 3.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 372 | -217.57 | -1.26% | 25% |
| 3 h a 1 dia | 821 | 45.00 | 0.11% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (454): MFE mediano 2.7%, MAE mediano -0.6%, devolução média do melhor ponto 1.6%, captura mediana 0.49.
- Perdedores (739): MAE mediano -1.9%, MFE mediano 0.6%; 78 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 160.52; – do lucro antes de custos.
- Trades < 3 h: 372 (lucro -217.57); reentradas em < 24 h: 762 (lucro -120.67).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -185.69.
- Lucro por ano de fechamento: 2017: -22.6, 2018: -43.3, 2019: -16.3, 2020: -39.7, 2021: 7.4, 2022: -33.4, 2023: -21.6, 2024: -3.0.

## XRP/USDT

Trades: 908; lucro líquido: -155.02.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_session_end | 722 | 127.59 | – | 0.37% | 42% | 4.5 h |
| stop_loss | 172 | -266.33 | – | -3.29% | 0% | 2.5 h |
| close_below_gsv_dn | 14 | -16.29 | – | -2.53% | 0% | 3.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 291 | -194.21 | -1.42% | 18% |
| 3 h a 1 dia | 617 | 39.19 | 0.13% | 41% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (305): MFE mediano 2.9%, MAE mediano -0.6%, devolução média do melhor ponto 2.3%, captura mediana 0.41.
- Perdedores (603): MAE mediano -2.1%, MFE mediano 0.7%; 92 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 126.36; – do lucro antes de custos.
- Trades < 3 h: 291 (lucro -194.21); reentradas em < 24 h: 537 (lucro -103.61).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -167.56.
- Lucro por ano de fechamento: 2018: 8.7, 2019: -40.9, 2020: -29.6, 2021: -27.0, 2022: -22.4, 2023: -19.3, 2024: -24.4.

## ADA/USDT

Trades: 1146; lucro líquido: -182.80.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_session_end | 909 | 166.19 | – | 0.40% | 46% | 4.6 h |
| stop_loss | 221 | -331.50 | – | -3.28% | 0% | 2.4 h |
| close_below_gsv_dn | 16 | -17.49 | – | -2.49% | 0% | 4.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 328 | -222.66 | -1.50% | 22% |
| 3 h a 1 dia | 818 | 39.86 | 0.11% | 43% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (421): MFE mediano 3.2%, MAE mediano -0.7%, devolução média do melhor ponto 1.9%, captura mediana 0.45.
- Perdedores (725): MAE mediano -2.3%, MFE mediano 0.7%; 105 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 154.93; – do lucro antes de custos.
- Trades < 3 h: 328 (lucro -222.66); reentradas em < 24 h: 755 (lucro -155.08).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -188.42.
- Lucro por ano de fechamento: 2018: -40.5, 2019: -39.2, 2020: -9.4, 2021: -23.7, 2022: -27.2, 2023: -19.0, 2024: -23.8.

## LTC/USDT

Trades: 1043; lucro líquido: -168.49.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_session_end | 849 | 122.68 | – | 0.31% | 45% | 4.6 h |
| stop_loss | 183 | -278.16 | – | -3.28% | 0% | 2.4 h |
| close_below_gsv_dn | 11 | -13.01 | – | -2.60% | 0% | 4.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 300 | -196.78 | -1.42% | 23% |
| 3 h a 1 dia | 743 | 28.28 | 0.08% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (379): MFE mediano 2.8%, MAE mediano -0.6%, devolução média do melhor ponto 1.7%, captura mediana 0.45.
- Perdedores (664): MAE mediano -2.0%, MFE mediano 0.7%; 74 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 143.23; – do lucro antes de custos.
- Trades < 3 h: 300 (lucro -196.78); reentradas em < 24 h: 622 (lucro -143.36).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -176.46.
- Lucro por ano de fechamento: 2018: -15.3, 2019: -25.4, 2020: -40.3, 2021: -35.9, 2022: -31.8, 2023: -12.7, 2024: -7.2.

## LINK/USDT

Trades: 1106; lucro líquido: -127.72.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_session_end | 852 | 264.09 | – | 0.65% | 51% | 4.5 h |
| stop_loss | 243 | -378.39 | – | -3.29% | 0% | 2.3 h |
| close_below_gsv_dn | 11 | -13.41 | – | -2.69% | 0% | 3.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 368 | -244.81 | -1.41% | 22% |
| 3 h a 1 dia | 738 | 117.09 | 0.33% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (431): MFE mediano 3.3%, MAE mediano -0.7%, devolução média do melhor ponto 1.9%, captura mediana 0.49.
- Perdedores (675): MAE mediano -2.4%, MFE mediano 0.8%; 102 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 154.52; 576% do lucro antes de custos.
- Trades < 3 h: 368 (lucro -244.81); reentradas em < 24 h: 740 (lucro -124.14).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -149.50.
- Lucro por ano de fechamento: 2019: -37.7, 2020: -25.1, 2021: -6.7, 2022: -24.7, 2023: -18.3, 2024: -15.3.

## DOGE/USDT

Trades: 771; lucro líquido: -100.13.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_session_end | 572 | 210.38 | – | 0.77% | 46% | 4.7 h |
| stop_loss | 192 | -301.99 | – | -3.28% | 0% | 1.9 h |
| close_below_gsv_dn | 7 | -8.51 | – | -2.53% | 0% | 4.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 257 | -232.06 | -1.89% | 17% |
| 3 h a 1 dia | 514 | 131.94 | 0.54% | 43% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (262): MFE mediano 3.5%, MAE mediano -0.7%, devolução média do melhor ponto 2.9%, captura mediana 0.45.
- Perdedores (509): MAE mediano -2.4%, MFE mediano 0.7%; 100 (20%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 110.29; 1085% do lucro antes de custos.
- Trades < 3 h: 257 (lucro -232.06); reentradas em < 24 h: 488 (lucro -28.32).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -123.02.
- Lucro por ano de fechamento: 2019: -4.5, 2020: -36.7, 2021: 7.6, 2022: -18.2, 2023: -23.9, 2024: -24.3.

## SOL/USDT

Trades: 793; lucro líquido: -81.80.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_session_end | 569 | 271.09 | – | 0.99% | 53% | 4.4 h |
| stop_loss | 220 | -347.74 | – | -3.28% | 0% | 2.1 h |
| close_below_gsv_dn | 4 | -5.15 | – | -2.69% | 0% | 2.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 312 | -228.15 | -1.52% | 21% |
| 3 h a 1 dia | 481 | 146.35 | 0.63% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (304): MFE mediano 3.9%, MAE mediano -0.8%, devolução média do melhor ponto 2.2%, captura mediana 0.52.
- Perdedores (489): MAE mediano -2.8%, MFE mediano 0.9%; 83 (17%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 113.52; 358% do lucro antes de custos.
- Trades < 3 h: 312 (lucro -228.15); reentradas em < 24 h: 539 (lucro -55.01).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -97.26.
- Lucro por ano de fechamento: 2020: -36.8, 2021: 16.5, 2022: -38.3, 2023: 5.4, 2024: -28.6.

## AVAX/USDT

Trades: 657; lucro líquido: -37.14.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_session_end | 480 | 247.80 | – | 1.05% | 55% | 4.5 h |
| stop_loss | 175 | -282.43 | – | -3.28% | 0% | 2.0 h |
| close_below_gsv_dn | 2 | -2.51 | – | -2.63% | 0% | 0.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 240 | -190.19 | -1.61% | 22% |
| 3 h a 1 dia | 417 | 153.04 | 0.75% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (265): MFE mediano 3.5%, MAE mediano -0.8%, devolução média do melhor ponto 2.2%, captura mediana 0.50.
- Perdedores (392): MAE mediano -2.9%, MFE mediano 0.9%; 74 (19%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 95.76; 163% do lucro antes de custos.
- Trades < 3 h: 240 (lucro -190.19); reentradas em < 24 h: 443 (lucro -47.59).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -51.69.
- Lucro por ano de fechamento: 2020: -4.7, 2021: -18.2, 2022: -33.2, 2023: 28.0, 2024: -9.0.

## DOT/USDT

Trades: 687; lucro líquido: -122.52.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_session_end | 537 | 108.54 | – | 0.42% | 45% | 4.5 h |
| stop_loss | 145 | -225.72 | – | -3.28% | 0% | 2.4 h |
| close_below_gsv_dn | 5 | -5.34 | – | -2.37% | 0% | 3.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 227 | -167.94 | -1.56% | 21% |
| 3 h a 1 dia | 460 | 45.42 | 0.20% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (242): MFE mediano 3.1%, MAE mediano -0.8%, devolução média do melhor ponto 1.6%, captura mediana 0.52.
- Perdedores (445): MAE mediano -2.3%, MFE mediano 0.6%; 50 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 96.04; – do lucro antes de custos.
- Trades < 3 h: 227 (lucro -167.94); reentradas em < 24 h: 436 (lucro -125.67).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -129.44.
- Lucro por ano de fechamento: 2020: -12.6, 2021: -40.0, 2022: -37.1, 2023: -17.6, 2024: -15.2.

## TRX/USDT

Trades: 914; lucro líquido: -199.67.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_session_end | 723 | 79.40 | – | 0.25% | 45% | 4.5 h |
| stop_loss | 185 | -272.32 | – | -3.27% | 0% | 2.5 h |
| close_below_gsv_dn | 6 | -6.76 | – | -2.58% | 0% | 2.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 287 | -175.99 | -1.37% | 23% |
| 3 h a 1 dia | 627 | -23.68 | -0.08% | 41% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (325): MFE mediano 2.6%, MAE mediano -0.6%, devolução média do melhor ponto 1.9%, captura mediana 0.42.
- Perdedores (589): MAE mediano -2.1%, MFE mediano 0.7%; 85 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 120.92; – do lucro antes de custos.
- Trades < 3 h: 287 (lucro -175.99); reentradas em < 24 h: 587 (lucro -122.26).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -205.51.
- Lucro por ano de fechamento: 2018: -30.1, 2019: -55.1, 2020: -39.2, 2021: -55.4, 2022: -11.8, 2023: -5.4, 2024: -2.5.

## NEAR/USDT

Trades: 759; lucro líquido: -76.29.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_session_end | 512 | 315.15 | – | 1.27% | 57% | 4.6 h |
| stop_loss | 245 | -388.87 | – | -3.28% | 0% | 2.2 h |
| close_below_gsv_dn | 2 | -2.57 | – | -2.67% | 0% | 3.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 278 | -258.19 | -1.92% | 17% |
| 3 h a 1 dia | 481 | 181.90 | 0.78% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (290): MFE mediano 4.0%, MAE mediano -0.8%, devolução média do melhor ponto 2.6%, captura mediana 0.48.
- Perdedores (469): MAE mediano -3.0%, MFE mediano 0.8%; 81 (17%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 109.42; 330% do lucro antes de custos.
- Trades < 3 h: 278 (lucro -258.19); reentradas em < 24 h: 527 (lucro -49.71).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -91.63.
- Lucro por ano de fechamento: 2020: 0.1, 2021: -46.3, 2022: 8.8, 2023: -11.6, 2024: -27.2.

## UNI/USDT

Trades: 709; lucro líquido: -150.22.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_session_end | 522 | 134.53 | – | 0.55% | 48% | 4.5 h |
| stop_loss | 183 | -280.23 | – | -3.27% | 0% | 2.3 h |
| close_below_gsv_dn | 4 | -4.52 | – | -2.54% | 0% | 4.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 241 | -165.05 | -1.47% | 26% |
| 3 h a 1 dia | 468 | 14.83 | 0.06% | 41% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (252): MFE mediano 3.3%, MAE mediano -0.5%, devolução média do melhor ponto 1.9%, captura mediana 0.46.
- Perdedores (457): MAE mediano -2.5%, MFE mediano 0.8%; 72 (16%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 97.44; – do lucro antes de custos.
- Trades < 3 h: 241 (lucro -165.05); reentradas em < 24 h: 472 (lucro -149.71).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -156.81.
- Lucro por ano de fechamento: 2020: -26.2, 2021: -35.8, 2022: -40.1, 2023: -34.0, 2024: -14.0.
