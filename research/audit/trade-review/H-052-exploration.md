# Revisão de trades: H-052 (exploração)

Fonte dos trades: `research/experiments/20261108T204538Z-h-052-exploration-btc-usdt/raw/backtest-result-2026-11-08_21-38-44.zip`; `research/experiments/20261108T204538Z-h-052-exploration-eth-usdt/raw/backtest-result-2026-11-08_22-02-18.zip`; `research/experiments/20261108T204538Z-h-052-exploration-bnb-usdt/raw/backtest-result-2026-11-08_22-27-58.zip`; `research/experiments/20261108T204538Z-h-052-exploration-xrp-usdt/raw/backtest-result-2026-11-08_22-46-44.zip`; `research/experiments/20261108T204538Z-h-052-exploration-ada-usdt/raw/backtest-result-2026-11-08_23-02-19.zip`; `research/experiments/20261108T204538Z-h-052-exploration-ltc-usdt/raw/backtest-result-2026-11-08_23-20-14.zip`; `research/experiments/20261108T204538Z-h-052-exploration-link-usdt/raw/backtest-result-2026-11-08_23-39-18.zip`; `research/experiments/20261108T204538Z-h-052-exploration-doge-usdt/raw/backtest-result-2026-11-08_23-53-45.zip`; `research/experiments/20261108T204538Z-h-052-exploration-sol-usdt/raw/backtest-result-2026-11-09_00-05-26.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 1186; lucro líquido: -144.90.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| below_band_or_vwap | 978 | -285.31 | – | -0.64% | 9% | 3.3 h |
| time_exit_utc_midnight | 165 | 206.96 | – | 2.75% | 92% | 13.8 h |
| stop_loss | 43 | -66.54 | – | -3.29% | 0% | 3.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 621 | -254.87 | -0.89% | 1% |
| 3 h a 1 dia | 565 | 109.98 | 0.43% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (243): MFE mediano 3.3%, MAE mediano -0.3%, devolução média do melhor ponto 1.9%, captura mediana 0.45.
- Perdedores (943): MAE mediano -0.8%, MFE mediano 0.4%; 54 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 161.39; 978% do lucro antes de custos.
- Trades < 3 h: 621 (lucro -254.87); reentradas em < 24 h: 416 (lucro -73.62).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -152.63.
- Lucro por ano de fechamento: 2017: -23.3, 2018: -32.7, 2019: -20.0, 2020: -11.4, 2021: -20.7, 2022: -19.2, 2023: -10.0, 2024: -7.6.

## ETH/USDT

Trades: 1199; lucro líquido: -125.72.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| below_band_or_vwap | 978 | -323.36 | – | -0.71% | 9% | 3.4 h |
| time_exit_utc_midnight | 172 | 274.52 | – | 3.42% | 92% | 13.6 h |
| stop_loss | 49 | -76.89 | – | -3.29% | 0% | 2.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 612 | -291.27 | -1.02% | 1% |
| 3 h a 1 dia | 587 | 165.55 | 0.60% | 41% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (250): MFE mediano 4.0%, MAE mediano -0.3%, devolução média do melhor ponto 2.4%, captura mediana 0.41.
- Perdedores (949): MAE mediano -1.0%, MFE mediano 0.6%; 97 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 167.18; 403% do lucro antes de custos.
- Trades < 3 h: 612 (lucro -291.27); reentradas em < 24 h: 402 (lucro -70.09).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -136.92.
- Lucro por ano de fechamento: 2017: -14.8, 2018: -35.8, 2019: -6.5, 2020: -12.5, 2021: -12.5, 2022: -5.0, 2023: -23.7, 2024: -14.9.

## BNB/USDT

Trades: 1184; lucro líquido: -93.91.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| below_band_or_vwap | 956 | -294.16 | – | -0.64% | 12% | 3.5 h |
| time_exit_utc_midnight | 149 | 327.19 | – | 4.55% | 97% | 14.7 h |
| stop_loss | 79 | -126.93 | – | -3.29% | 0% | 1.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 626 | -347.92 | -1.15% | 1% |
| 3 h a 1 dia | 558 | 254.01 | 0.94% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (263): MFE mediano 4.2%, MAE mediano -0.4%, devolução média do melhor ponto 2.8%, captura mediana 0.40.
- Perdedores (921): MAE mediano -1.2%, MFE mediano 0.6%; 107 (12%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 169.71; 224% do lucro antes de custos.
- Trades < 3 h: 626 (lucro -347.92); reentradas em < 24 h: 404 (lucro -54.16).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -117.27.
- Lucro por ano de fechamento: 2017: -13.3, 2018: -24.5, 2019: 4.7, 2020: -16.8, 2021: 15.4, 2022: -17.0, 2023: -39.7, 2024: -2.7.

## XRP/USDT

Trades: 1006; lucro líquido: -98.17.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| below_band_or_vwap | 832 | -245.63 | – | -0.62% | 11% | 3.3 h |
| time_exit_utc_midnight | 113 | 243.19 | – | 4.53% | 93% | 12.9 h |
| stop_loss | 61 | -95.72 | – | -3.29% | 0% | 1.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 542 | -295.69 | -1.14% | 2% |
| 3 h a 1 dia | 464 | 197.52 | 0.90% | 40% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (195): MFE mediano 4.4%, MAE mediano -0.4%, devolução média do melhor ponto 4.1%, captura mediana 0.36.
- Perdedores (811): MAE mediano -1.1%, MFE mediano 0.6%; 96 (12%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 143.42; 317% do lucro antes de custos.
- Trades < 3 h: 542 (lucro -295.69); reentradas em < 24 h: 319 (lucro -39.99).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -115.62.
- Lucro por ano de fechamento: 2018: -10.8, 2019: -18.4, 2020: -26.5, 2021: -8.1, 2022: -3.0, 2023: -7.8, 2024: -23.5.

## ADA/USDT

Trades: 1063; lucro líquido: -148.42.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| below_band_or_vwap | 866 | -311.61 | – | -0.78% | 11% | 3.2 h |
| time_exit_utc_midnight | 121 | 278.10 | – | 5.03% | 93% | 14.2 h |
| stop_loss | 76 | -114.91 | – | -3.28% | 0% | 2.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 583 | -323.96 | -1.21% | 2% |
| 3 h a 1 dia | 480 | 175.54 | 0.80% | 41% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (205): MFE mediano 4.8%, MAE mediano -0.5%, devolução média do melhor ponto 3.0%, captura mediana 0.41.
- Perdedores (858): MAE mediano -1.3%, MFE mediano 0.6%; 130 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 145.34; – do lucro antes de custos.
- Trades < 3 h: 583 (lucro -323.96); reentradas em < 24 h: 354 (lucro -59.19).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -159.76.
- Lucro por ano de fechamento: 2018: -40.2, 2019: -42.3, 2020: -5.6, 2021: -0.7, 2022: -18.9, 2023: -21.8, 2024: -18.8.

## LTC/USDT

Trades: 1156; lucro líquido: -190.08.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| below_band_or_vwap | 964 | -321.56 | – | -0.73% | 11% | 3.3 h |
| time_exit_utc_midnight | 126 | 232.63 | – | 3.97% | 93% | 13.4 h |
| stop_loss | 66 | -101.15 | – | -3.28% | 0% | 2.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 637 | -328.62 | -1.12% | 1% |
| 3 h a 1 dia | 519 | 138.54 | 0.57% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (225): MFE mediano 4.0%, MAE mediano -0.4%, devolução média do melhor ponto 2.8%, captura mediana 0.35.
- Perdedores (931): MAE mediano -1.2%, MFE mediano 0.6%; 101 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 157.26; – do lucro antes de custos.
- Trades < 3 h: 637 (lucro -328.62); reentradas em < 24 h: 403 (lucro -106.75).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -203.17.
- Lucro por ano de fechamento: 2017: -0.2, 2018: -27.7, 2019: -10.1, 2020: -26.0, 2021: -57.5, 2022: -23.0, 2023: -35.4, 2024: -10.2.

## LINK/USDT

Trades: 1007; lucro líquido: -127.73.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| below_band_or_vwap | 831 | -263.98 | – | -0.67% | 15% | 3.7 h |
| time_exit_utc_midnight | 98 | 259.40 | – | 5.54% | 94% | 14.3 h |
| stop_loss | 78 | -123.16 | – | -3.28% | 0% | 2.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 524 | -318.20 | -1.28% | 2% |
| 3 h a 1 dia | 483 | 190.47 | 0.82% | 43% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (215): MFE mediano 5.3%, MAE mediano -0.5%, devolução média do melhor ponto 3.5%, captura mediana 0.32.
- Perdedores (792): MAE mediano -1.5%, MFE mediano 0.7%; 155 (20%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 142.37; 973% do lucro antes de custos.
- Trades < 3 h: 524 (lucro -318.20); reentradas em < 24 h: 342 (lucro -100.55).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -141.20.
- Lucro por ano de fechamento: 2019: -29.0, 2020: 0.2, 2021: -16.5, 2022: -41.9, 2023: -16.0, 2024: -24.5.

## DOGE/USDT

Trades: 863; lucro líquido: -129.83.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| below_band_or_vwap | 724 | -161.93 | – | -0.48% | 16% | 3.4 h |
| stop_loss | 75 | -117.23 | – | -3.29% | 0% | 1.2 h |
| time_exit_utc_midnight | 64 | 149.33 | – | 4.95% | 98% | 13.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 502 | -282.68 | -1.19% | 3% |
| 3 h a 1 dia | 361 | 152.85 | 0.89% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (180): MFE mediano 4.6%, MAE mediano -0.4%, devolução média do melhor ponto 4.6%, captura mediana 0.25.
- Perdedores (683): MAE mediano -1.2%, MFE mediano 0.6%; 92 (13%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 121.91; – do lucro antes de custos.
- Trades < 3 h: 502 (lucro -282.68); reentradas em < 24 h: 305 (lucro -35.47).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -148.76.
- Lucro por ano de fechamento: 2019: -1.5, 2020: -20.8, 2021: -35.0, 2022: -10.5, 2023: -45.9, 2024: -16.1.

## SOL/USDT

Trades: 729; lucro líquido: -96.19.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| below_band_or_vwap | 565 | -189.14 | – | -0.70% | 14% | 3.6 h |
| stop_loss | 85 | -135.07 | – | -3.28% | 0% | 1.4 h |
| time_exit_utc_midnight | 79 | 228.02 | – | 6.02% | 95% | 13.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 389 | -273.81 | -1.46% | 2% |
| 3 h a 1 dia | 340 | 177.62 | 1.08% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (153): MFE mediano 6.1%, MAE mediano -0.6%, devolução média do melhor ponto 4.4%, captura mediana 0.36.
- Perdedores (576): MAE mediano -1.7%, MFE mediano 0.8%; 108 (19%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 104.31; 1284% do lucro antes de custos.
- Trades < 3 h: 389 (lucro -273.81); reentradas em < 24 h: 269 (lucro -31.58).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -108.19.
- Lucro por ano de fechamento: 2020: -28.6, 2021: 8.2, 2022: -41.0, 2023: -7.0, 2024: -27.8.
