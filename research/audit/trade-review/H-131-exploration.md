# Revisão de trades: H-131 (exploração)

Fonte dos trades: `research/experiments/20261113T194938Z-h-131-exploration-btc-usdt/raw/backtest-result-2026-11-13_20-20-33.zip`; `research/experiments/20261113T194938Z-h-131-exploration-eth-usdt/raw/backtest-result-2026-11-13_20-20-35.zip`; `research/experiments/20261113T194938Z-h-131-exploration-bnb-usdt/raw/backtest-result-2026-11-13_20-20-40.zip`; `research/experiments/20261113T194938Z-h-131-exploration-xrp-usdt/raw/backtest-result-2026-11-13_20-29-15.zip`; `research/experiments/20261113T194938Z-h-131-exploration-ada-usdt/raw/backtest-result-2026-11-13_20-29-38.zip`; `research/experiments/20261113T194938Z-h-131-exploration-ltc-usdt/raw/backtest-result-2026-11-13_20-29-33.zip`; `research/experiments/20261113T194938Z-h-131-exploration-link-usdt/raw/backtest-result-2026-11-13_20-37-22.zip`; `research/experiments/20261113T194938Z-h-131-exploration-doge-usdt/raw/backtest-result-2026-11-13_20-37-29.zip`; `research/experiments/20261113T194938Z-h-131-exploration-sol-usdt/raw/backtest-result-2026-11-13_20-37-43.zip`; `research/experiments/20261113T194938Z-h-131-exploration-avax-usdt/raw/backtest-result-2026-11-13_20-44-48.zip`; `research/experiments/20261113T194938Z-h-131-exploration-dot-usdt/raw/backtest-result-2026-11-13_20-44-52.zip`; `research/experiments/20261113T194938Z-h-131-exploration-trx-usdt/raw/backtest-result-2026-11-13_20-45-27.zip`; `research/experiments/20261113T194938Z-h-131-exploration-near-usdt/raw/backtest-result-2026-11-13_20-52-13.zip`; `research/experiments/20261113T194938Z-h-131-exploration-uni-usdt/raw/backtest-result-2026-11-13_20-52-12.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 454; lucro líquido: -96.49.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 209 | -300.64 | – | -1.50% | 0% | 1.8 h |
| take_profit_1_5pct | 110 | 212.22 | – | 2.00% | 100% | 2.8 h |
| trend_lost | 106 | -9.14 | – | -0.09% | 37% | 2.1 h |
| time_exit_12h | 29 | 1.07 | – | 0.04% | 48% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 312 | -94.18 | -0.32% | 32% |
| 3 h a 1 dia | 142 | -2.31 | -0.02% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (163): MFE mediano 2.4%, MAE mediano -0.4%, devolução média do melhor ponto 1.0%, captura mediana 0.62.
- Perdedores (291): MAE mediano -1.4%, MFE mediano 0.7%; 8 (3%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 130.37; 385% do lucro antes de custos.
- Trades < 3 h: 312 (lucro -94.18); reentradas em < 24 h: 308 (lucro -75.29).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -103.76.
- Lucro por ano de fechamento: 2017: -5.0, 2018: -4.3, 2019: -15.6, 2020: -17.1, 2021: -22.2, 2022: 0.5, 2023: -24.6, 2024: -8.1.

## ETH/USDT

Trades: 574; lucro líquido: -115.13.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 308 | -436.53 | – | -1.49% | 0% | 1.5 h |
| take_profit_1_5pct | 172 | 324.02 | – | 1.99% | 100% | 3.0 h |
| trend_lost | 81 | -0.55 | – | -0.01% | 46% | 1.6 h |
| time_exit_12h | 13 | -2.07 | – | -0.18% | 31% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 430 | -166.56 | -0.41% | 31% |
| 3 h a 1 dia | 144 | 51.43 | 0.38% | 54% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (213): MFE mediano 2.6%, MAE mediano -0.4%, devolução média do melhor ponto 1.0%, captura mediana 0.66.
- Perdedores (361): MAE mediano -1.6%, MFE mediano 0.6%; 9 (2%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 162.42; 343% do lucro antes de custos.
- Trades < 3 h: 430 (lucro -166.56); reentradas em < 24 h: 424 (lucro -92.88).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -118.96.
- Lucro por ano de fechamento: 2017: -15.1, 2018: -11.2, 2019: -26.7, 2020: -12.8, 2021: -16.3, 2022: -12.5, 2023: -10.9, 2024: -9.7.

## BNB/USDT

Trades: 735; lucro líquido: -191.29.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 409 | -562.44 | – | -1.49% | 0% | 1.3 h |
| take_profit_1_5pct | 200 | 381.94 | – | 2.06% | 100% | 2.3 h |
| trend_lost | 120 | -13.62 | – | -0.14% | 34% | 1.5 h |
| time_exit_12h | 6 | 2.84 | – | 0.54% | 83% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 594 | -188.25 | -0.35% | 31% |
| 3 h a 1 dia | 141 | -3.04 | -0.02% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (246): MFE mediano 2.6%, MAE mediano -0.4%, devolução média do melhor ponto 1.2%, captura mediana 0.65.
- Perdedores (489): MAE mediano -1.6%, MFE mediano 0.6%; 26 (5%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 201.39; 1994% do lucro antes de custos.
- Trades < 3 h: 594 (lucro -188.25); reentradas em < 24 h: 578 (lucro -156.67).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -198.00.
- Lucro por ano de fechamento: 2017: 2.5, 2018: -18.5, 2019: -42.7, 2020: -47.2, 2021: -35.9, 2022: -10.1, 2023: -21.7, 2024: -17.6.

## XRP/USDT

Trades: 687; lucro líquido: -106.30.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 363 | -521.33 | – | -1.49% | 0% | 1.2 h |
| take_profit_1_5pct | 204 | 417.82 | – | 2.12% | 100% | 2.2 h |
| trend_lost | 116 | -2.79 | – | -0.03% | 43% | 1.6 h |
| time_exit_12h | 4 | -0.01 | – | 0.00% | 50% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 563 | -144.82 | -0.27% | 34% |
| 3 h a 1 dia | 124 | 38.52 | 0.33% | 54% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (256): MFE mediano 2.7%, MAE mediano -0.4%, devolução média do melhor ponto 1.2%, captura mediana 0.64.
- Perdedores (431): MAE mediano -1.5%, MFE mediano 0.6%; 37 (9%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 197.70; 216% do lucro antes de custos.
- Trades < 3 h: 563 (lucro -144.82); reentradas em < 24 h: 531 (lucro -66.35).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -112.62.
- Lucro por ano de fechamento: 2018: -25.9, 2019: -23.0, 2020: 25.3, 2021: -11.5, 2022: -19.2, 2023: -45.9, 2024: -6.1.

## ADA/USDT

Trades: 790; lucro líquido: -113.60.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 433 | -608.20 | – | -1.49% | 0% | 1.3 h |
| take_profit_1_5pct | 257 | 498.87 | – | 2.06% | 100% | 1.9 h |
| trend_lost | 96 | -7.13 | – | -0.08% | 39% | 1.3 h |
| time_exit_12h | 4 | 2.86 | – | 0.74% | 100% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 655 | -114.46 | -0.18% | 36% |
| 3 h a 1 dia | 135 | 0.86 | 0.01% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (298): MFE mediano 2.7%, MAE mediano -0.4%, devolução média do melhor ponto 1.1%, captura mediana 0.66.
- Perdedores (492): MAE mediano -1.5%, MFE mediano 0.6%; 27 (5%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 222.76; 204% do lucro antes de custos.
- Trades < 3 h: 655 (lucro -114.46); reentradas em < 24 h: 629 (lucro -86.24).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -121.70.
- Lucro por ano de fechamento: 2018: -10.9, 2019: -32.3, 2020: -23.9, 2021: 13.6, 2022: -23.2, 2023: -40.5, 2024: 3.7.

## LTC/USDT

Trades: 591; lucro líquido: -132.65.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 325 | -455.27 | – | -1.49% | 0% | 1.4 h |
| take_profit_1_5pct | 168 | 334.00 | – | 2.11% | 100% | 2.2 h |
| trend_lost | 94 | -12.79 | – | -0.15% | 35% | 1.4 h |
| time_exit_12h | 4 | 1.41 | – | 0.39% | 75% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 486 | -131.15 | -0.29% | 33% |
| 3 h a 1 dia | 105 | -1.50 | -0.02% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (204): MFE mediano 2.7%, MAE mediano -0.4%, devolução média do melhor ponto 1.0%, captura mediana 0.66.
- Perdedores (387): MAE mediano -1.5%, MFE mediano 0.6%; 19 (5%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 166.28; 494% do lucro antes de custos.
- Trades < 3 h: 486 (lucro -131.15); reentradas em < 24 h: 453 (lucro -126.12).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -137.96.
- Lucro por ano de fechamento: 2018: -11.0, 2019: -20.0, 2020: -30.4, 2021: -24.0, 2022: -18.0, 2023: -14.1, 2024: -15.1.

## LINK/USDT

Trades: 752; lucro líquido: -177.38.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 435 | -608.07 | – | -1.49% | 0% | 1.1 h |
| take_profit_1_5pct | 211 | 426.88 | – | 2.14% | 100% | 1.8 h |
| trend_lost | 104 | 4.62 | – | 0.04% | 50% | 1.4 h |
| time_exit_12h | 2 | -0.81 | – | -0.47% | 50% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 657 | -195.46 | -0.32% | 33% |
| 3 h a 1 dia | 95 | 18.08 | 0.19% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (264): MFE mediano 2.8%, MAE mediano -0.3%, devolução média do melhor ponto 1.2%, captura mediana 0.65.
- Perdedores (488): MAE mediano -1.5%, MFE mediano 0.7%; 34 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 210.46; 636% do lucro antes de custos.
- Trades < 3 h: 657 (lucro -195.46); reentradas em < 24 h: 620 (lucro -127.64).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -186.98.
- Lucro por ano de fechamento: 2019: -21.6, 2020: -14.2, 2021: -69.9, 2022: -41.9, 2023: -22.2, 2024: -7.5.

## DOGE/USDT

Trades: 674; lucro líquido: -110.14.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 386 | -544.41 | – | -1.49% | 0% | 1.0 h |
| take_profit_1_5pct | 196 | 421.46 | – | 2.28% | 100% | 1.6 h |
| trend_lost | 90 | 13.67 | – | 0.16% | 50% | 1.1 h |
| time_exit_12h | 2 | -0.86 | – | -0.42% | 50% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 596 | -110.90 | -0.20% | 35% |
| 3 h a 1 dia | 78 | 0.76 | 0.02% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (242): MFE mediano 3.0%, MAE mediano -0.3%, devolução média do melhor ponto 1.5%, captura mediana 0.59.
- Perdedores (432): MAE mediano -1.6%, MFE mediano 0.7%; 49 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 190.54; 237% do lucro antes de custos.
- Trades < 3 h: 596 (lucro -110.90); reentradas em < 24 h: 540 (lucro -111.29).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -127.21.
- Lucro por ano de fechamento: 2019: -17.1, 2020: -24.4, 2021: 4.7, 2022: -28.3, 2023: -49.1, 2024: 4.1.

## SOL/USDT

Trades: 615; lucro líquido: -154.83.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 377 | -512.28 | – | -1.49% | 0% | 0.7 h |
| take_profit_1_5pct | 173 | 355.34 | – | 2.26% | 100% | 1.9 h |
| trend_lost | 63 | 1.98 | – | 0.04% | 56% | 0.9 h |
| time_exit_12h | 2 | 0.12 | – | 0.06% | 50% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 548 | -188.92 | -0.38% | 31% |
| 3 h a 1 dia | 67 | 34.08 | 0.58% | 57% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (209): MFE mediano 2.9%, MAE mediano -0.4%, devolução média do melhor ponto 1.3%, captura mediana 0.66.
- Perdedores (406): MAE mediano -1.6%, MFE mediano 0.8%; 42 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 167.27; 1345% do lucro antes de custos.
- Trades < 3 h: 548 (lucro -188.92); reentradas em < 24 h: 517 (lucro -164.80).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -160.90.
- Lucro por ano de fechamento: 2020: -14.7, 2021: -77.5, 2022: -17.0, 2023: -44.2, 2024: -1.5.

## AVAX/USDT

Trades: 464; lucro líquido: -67.15.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 275 | -403.50 | – | -1.49% | 0% | 0.9 h |
| take_profit_1_5pct | 139 | 326.38 | – | 2.37% | 100% | 1.5 h |
| trend_lost | 46 | 9.03 | – | 0.20% | 50% | 1.2 h |
| time_exit_12h | 4 | 0.95 | – | 0.24% | 75% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 413 | -68.01 | -0.17% | 34% |
| 3 h a 1 dia | 51 | 0.86 | 0.02% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (165): MFE mediano 3.3%, MAE mediano -0.4%, devolução média do melhor ponto 1.4%, captura mediana 0.65.
- Perdedores (299): MAE mediano -1.6%, MFE mediano 0.7%; 21 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 137.09; 196% do lucro antes de custos.
- Trades < 3 h: 413 (lucro -68.01); reentradas em < 24 h: 374 (lucro -65.02).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -73.66.
- Lucro por ano de fechamento: 2020: 2.3, 2021: -2.2, 2022: -18.3, 2023: -37.6, 2024: -11.3.

## DOT/USDT

Trades: 396; lucro líquido: -134.29.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 237 | -326.81 | – | -1.49% | 0% | 1.1 h |
| take_profit_1_5pct | 100 | 193.51 | – | 2.10% | 100% | 1.9 h |
| trend_lost | 55 | -0.98 | – | -0.02% | 45% | 1.3 h |
| time_exit_12h | 4 | -0.01 | – | -0.00% | 50% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 335 | -129.86 | -0.41% | 30% |
| 3 h a 1 dia | 61 | -4.43 | -0.08% | 41% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (127): MFE mediano 2.6%, MAE mediano -0.4%, devolução média do melhor ponto 1.1%, captura mediana 0.67.
- Perdedores (269): MAE mediano -1.6%, MFE mediano 0.7%; 17 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 109.36; – do lucro antes de custos.
- Trades < 3 h: 335 (lucro -129.86); reentradas em < 24 h: 312 (lucro -119.36).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -140.08.
- Lucro por ano de fechamento: 2020: -11.6, 2021: -79.8, 2022: -11.2, 2023: -30.0, 2024: -1.6.

## TRX/USDT

Trades: 623; lucro líquido: -189.42.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 360 | -489.44 | – | -1.48% | 0% | 1.1 h |
| take_profit_1_5pct | 160 | 315.20 | – | 2.14% | 100% | 2.1 h |
| trend_lost | 96 | -13.34 | – | -0.16% | 32% | 1.7 h |
| time_exit_12h | 7 | -1.84 | – | -0.31% | 14% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 538 | -195.56 | -0.40% | 28% |
| 3 h a 1 dia | 85 | 6.13 | 0.08% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (192): MFE mediano 2.7%, MAE mediano -0.3%, devolução média do melhor ponto 1.2%, captura mediana 0.67.
- Perdedores (431): MAE mediano -1.5%, MFE mediano 0.7%; 19 (4%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 170.58; – do lucro antes de custos.
- Trades < 3 h: 538 (lucro -195.56); reentradas em < 24 h: 476 (lucro -154.99).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -196.97.
- Lucro por ano de fechamento: 2018: -13.3, 2019: -33.9, 2020: -30.4, 2021: -68.4, 2022: -28.6, 2023: -12.7, 2024: -1.9.

## NEAR/USDT

Trades: 560; lucro líquido: -118.45.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 340 | -469.23 | – | -1.49% | 0% | 0.8 h |
| take_profit_1_5pct | 167 | 342.12 | – | 2.22% | 100% | 1.6 h |
| trend_lost | 53 | 8.66 | – | 0.17% | 47% | 1.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 514 | -138.81 | -0.29% | 32% |
| 3 h a 1 dia | 46 | 20.36 | 0.48% | 57% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (192): MFE mediano 3.1%, MAE mediano -0.4%, devolução média do melhor ponto 1.4%, captura mediana 0.65.
- Perdedores (368): MAE mediano -1.5%, MFE mediano 0.7%; 27 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 154.92; 425% do lucro antes de custos.
- Trades < 3 h: 514 (lucro -138.81); reentradas em < 24 h: 456 (lucro -103.06).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -126.84.
- Lucro por ano de fechamento: 2020: -10.9, 2021: -72.9, 2022: -11.4, 2023: -14.6, 2024: -8.7.

## UNI/USDT

Trades: 388; lucro líquido: -63.82.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 215 | -307.27 | – | -1.48% | 0% | 1.1 h |
| take_profit_1_5pct | 120 | 243.50 | – | 2.12% | 100% | 1.8 h |
| trend_lost | 51 | 1.31 | – | 0.02% | 41% | 1.0 h |
| time_exit_12h | 2 | -1.36 | – | -0.73% | 0% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 335 | -71.76 | -0.22% | 35% |
| 3 h a 1 dia | 53 | 7.94 | 0.16% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (141): MFE mediano 2.8%, MAE mediano -0.4%, devolução média do melhor ponto 1.2%, captura mediana 0.64.
- Perdedores (247): MAE mediano -1.5%, MFE mediano 0.7%; 18 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 111.50; 234% do lucro antes de custos.
- Trades < 3 h: 335 (lucro -71.76); reentradas em < 24 h: 315 (lucro -50.31).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -69.71.
- Lucro por ano de fechamento: 2020: 4.2, 2021: -43.6, 2022: -20.8, 2023: -6.0, 2024: 2.3.
