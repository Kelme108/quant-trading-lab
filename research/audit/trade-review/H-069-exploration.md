# Revisão de trades: H-069 (exploração)

Fonte dos trades: `research/experiments/20261108T184953Z-h-069-exploration-btc-usdt/raw/backtest-result-2026-11-08_19-05-16.zip`; `research/experiments/20261108T184953Z-h-069-exploration-eth-usdt/raw/backtest-result-2026-11-08_19-11-25.zip`; `research/experiments/20261108T184953Z-h-069-exploration-bnb-usdt/raw/backtest-result-2026-11-08_19-17-56.zip`; `research/experiments/20261108T184953Z-h-069-exploration-xrp-usdt/raw/backtest-result-2026-11-08_19-24-57.zip`; `research/experiments/20261108T184953Z-h-069-exploration-ada-usdt/raw/backtest-result-2026-11-08_19-32-05.zip`; `research/experiments/20261108T184953Z-h-069-exploration-ltc-usdt/raw/backtest-result-2026-11-08_19-38-53.zip`; `research/experiments/20261108T184953Z-h-069-exploration-link-usdt/raw/backtest-result-2026-11-08_19-46-06.zip`; `research/experiments/20261108T184953Z-h-069-exploration-doge-usdt/raw/backtest-result-2026-11-08_19-51-53.zip`; `research/experiments/20261108T184953Z-h-069-exploration-sol-usdt/raw/backtest-result-2026-11-08_19-56-06.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 919; lucro líquido: -92.30.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit | 563 | 171.05 | – | 0.65% | 57% | 5.0 h |
| close_below_orl | 325 | -216.75 | – | -1.42% | 0% | 2.0 h |
| stop_loss | 30 | -47.05 | – | -3.29% | 0% | 1.3 h |
| force_exit | 1 | 0.45 | – | 1.00% | 100% | 5.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 326 | -204.61 | -1.33% | 6% |
| 3 h a 1 dia | 593 | 112.31 | 0.41% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (324): MFE mediano 2.1%, MAE mediano -0.4%, devolução média do melhor ponto 1.2%, captura mediana 0.49.
- Perdedores (595): MAE mediano -1.2%, MFE mediano 0.5%; 24 (4%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 128.76; 353% do lucro antes de custos.
- Trades < 3 h: 326 (lucro -204.61); reentradas em < 24 h: 371 (lucro -48.74).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -96.34.
- Lucro por ano de fechamento: 2017: -16.5, 2018: -31.1, 2019: -8.5, 2020: -6.0, 2021: -21.1, 2022: -11.7, 2023: 3.4, 2024: -0.9.

## ETH/USDT

Trades: 1022; lucro líquido: -79.05.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit | 612 | 246.64 | – | 0.85% | 62% | 4.9 h |
| close_below_orl | 370 | -262.82 | – | -1.49% | 0% | 2.0 h |
| stop_loss | 40 | -62.88 | – | -3.29% | 0% | 2.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 381 | -241.41 | -1.33% | 8% |
| 3 h a 1 dia | 641 | 162.36 | 0.54% | 55% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (380): MFE mediano 2.4%, MAE mediano -0.5%, devolução média do melhor ponto 1.4%, captura mediana 0.48.
- Perdedores (642): MAE mediano -1.3%, MFE mediano 0.6%; 33 (5%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 145.30; 219% do lucro antes de custos.
- Trades < 3 h: 381 (lucro -241.41); reentradas em < 24 h: 447 (lucro -39.18).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -86.20.
- Lucro por ano de fechamento: 2017: -7.1, 2018: -32.9, 2019: -0.9, 2020: -10.6, 2021: -10.9, 2022: -10.6, 2023: 1.8, 2024: -8.0.

## BNB/USDT

Trades: 988; lucro líquido: -174.67.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit | 562 | 160.30 | – | 0.61% | 56% | 5.0 h |
| close_below_orl | 375 | -256.42 | – | -1.49% | 0% | 2.0 h |
| stop_loss | 51 | -78.55 | – | -3.29% | 0% | 1.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 373 | -250.18 | -1.45% | 5% |
| 3 h a 1 dia | 615 | 75.51 | 0.26% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (316): MFE mediano 2.1%, MAE mediano -0.5%, devolução média do melhor ponto 1.3%, captura mediana 0.50.
- Perdedores (672): MAE mediano -1.4%, MFE mediano 0.5%; 43 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 135.44; – do lucro antes de custos.
- Trades < 3 h: 373 (lucro -250.18); reentradas em < 24 h: 430 (lucro -80.72).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -180.72.
- Lucro por ano de fechamento: 2017: 0.7, 2018: -29.7, 2019: -23.2, 2020: -21.4, 2021: -35.3, 2022: -28.4, 2023: -22.4, 2024: -15.0.

## XRP/USDT

Trades: 940; lucro líquido: -77.92.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit | 558 | 219.86 | – | 0.84% | 65% | 4.7 h |
| close_below_orl | 335 | -224.82 | – | -1.42% | 0% | 1.8 h |
| stop_loss | 47 | -72.97 | – | -3.29% | 0% | 1.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 385 | -233.66 | -1.28% | 12% |
| 3 h a 1 dia | 555 | 155.74 | 0.60% | 57% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (363): MFE mediano 2.1%, MAE mediano -0.4%, devolução média do melhor ponto 1.4%, captura mediana 0.47.
- Perdedores (577): MAE mediano -1.2%, MFE mediano 0.5%; 45 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 132.72; 242% do lucro antes de custos.
- Trades < 3 h: 385 (lucro -233.66); reentradas em < 24 h: 401 (lucro -42.13).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -86.58.
- Lucro por ano de fechamento: 2018: -12.1, 2019: -15.8, 2020: -23.6, 2021: -30.5, 2022: -0.1, 2023: -6.9, 2024: 11.2.

## ADA/USDT

Trades: 1012; lucro líquido: -119.51.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit | 577 | 253.69 | – | 0.93% | 64% | 4.9 h |
| close_below_orl | 379 | -285.82 | – | -1.59% | 0% | 1.9 h |
| stop_loss | 56 | -87.38 | – | -3.28% | 0% | 1.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 396 | -263.50 | -1.40% | 10% |
| 3 h a 1 dia | 616 | 143.99 | 0.49% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (368): MFE mediano 2.7%, MAE mediano -0.5%, devolução média do melhor ponto 1.5%, captura mediana 0.49.
- Perdedores (644): MAE mediano -1.5%, MFE mediano 0.6%; 48 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 143.40; 600% do lucro antes de custos.
- Trades < 3 h: 396 (lucro -263.50); reentradas em < 24 h: 458 (lucro -85.57).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -127.60.
- Lucro por ano de fechamento: 2018: -18.4, 2019: -6.6, 2020: -12.0, 2021: -24.9, 2022: -41.6, 2023: -4.9, 2024: -11.1.

## LTC/USDT

Trades: 1019; lucro líquido: -146.27.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit | 572 | 229.03 | – | 0.86% | 60% | 4.9 h |
| close_below_orl | 373 | -261.02 | – | -1.51% | 0% | 2.0 h |
| stop_loss | 74 | -114.27 | – | -3.28% | 0% | 1.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 385 | -266.71 | -1.48% | 6% |
| 3 h a 1 dia | 634 | 120.45 | 0.40% | 50% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (344): MFE mediano 2.6%, MAE mediano -0.5%, devolução média do melhor ponto 1.5%, captura mediana 0.47.
- Perdedores (675): MAE mediano -1.4%, MFE mediano 0.5%; 52 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 141.45; – do lucro antes de custos.
- Trades < 3 h: 385 (lucro -266.71); reentradas em < 24 h: 451 (lucro -80.22).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -151.04.
- Lucro por ano de fechamento: 2017: 0.9, 2018: -31.6, 2019: -9.0, 2020: -23.2, 2021: -30.4, 2022: -17.8, 2023: -24.6, 2024: -10.6.

## LINK/USDT

Trades: 897; lucro líquido: -118.69.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit | 478 | 270.61 | – | 1.17% | 64% | 4.9 h |
| close_below_orl | 352 | -282.12 | – | -1.67% | 0% | 1.8 h |
| stop_loss | 67 | -107.18 | – | -3.28% | 0% | 1.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 384 | -284.19 | -1.54% | 6% |
| 3 h a 1 dia | 513 | 165.51 | 0.66% | 55% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (304): MFE mediano 3.2%, MAE mediano -0.6%, devolução média do melhor ponto 1.9%, captura mediana 0.50.
- Perdedores (593): MAE mediano -1.7%, MFE mediano 0.7%; 72 (12%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 128.85; 1268% do lucro antes de custos.
- Trades < 3 h: 384 (lucro -284.19); reentradas em < 24 h: 415 (lucro -59.14).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -137.91.
- Lucro por ano de fechamento: 2019: 5.5, 2020: -10.7, 2021: -35.1, 2022: -35.6, 2023: -22.8, 2024: -20.0.

## DOGE/USDT

Trades: 701; lucro líquido: -107.57.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit | 375 | 156.43 | – | 0.90% | 59% | 4.9 h |
| close_below_orl | 282 | -196.27 | – | -1.48% | 0% | 1.9 h |
| stop_loss | 44 | -67.73 | – | -3.29% | 0% | 1.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 294 | -191.28 | -1.39% | 7% |
| 3 h a 1 dia | 407 | 83.71 | 0.44% | 50% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (223): MFE mediano 2.6%, MAE mediano -0.5%, devolução média do melhor ponto 1.8%, captura mediana 0.46.
- Perdedores (478): MAE mediano -1.4%, MFE mediano 0.5%; 48 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 98.35; – do lucro antes de custos.
- Trades < 3 h: 294 (lucro -191.28); reentradas em < 24 h: 281 (lucro -48.59).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -114.27.
- Lucro por ano de fechamento: 2019: -14.5, 2020: -26.8, 2021: -30.1, 2022: -18.4, 2023: -6.8, 2024: -11.0.

## SOL/USDT

Trades: 610; lucro líquido: -37.42.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit | 311 | 266.60 | – | 1.74% | 68% | 4.9 h |
| close_below_orl | 245 | -216.26 | – | -1.79% | 0% | 1.9 h |
| stop_loss | 54 | -87.75 | – | -3.29% | 0% | 1.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 270 | -227.54 | -1.71% | 8% |
| 3 h a 1 dia | 340 | 190.13 | 1.13% | 56% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (211): MFE mediano 4.1%, MAE mediano -0.6%, devolução média do melhor ponto 2.0%, captura mediana 0.59.
- Perdedores (399): MAE mediano -2.0%, MFE mediano 0.8%; 65 (16%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 90.10; 171% do lucro antes de custos.
- Trades < 3 h: 270 (lucro -227.54); reentradas em < 24 h: 273 (lucro -29.90).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -48.82.
- Lucro por ano de fechamento: 2020: -12.9, 2021: 8.3, 2022: -16.6, 2023: 6.5, 2024: -22.7.
