# Revisão de trades: H-062 (exploração)

Fonte dos trades: `research/experiments/20261109T200935Z-h-062-exploration-btc-usdt/raw/backtest-result-2026-11-09_20-30-38.zip`; `research/experiments/20261109T200935Z-h-062-exploration-eth-usdt/raw/backtest-result-2026-11-09_20-38-10.zip`; `research/experiments/20261109T200935Z-h-062-exploration-bnb-usdt/raw/backtest-result-2026-11-09_20-45-21.zip`; `research/experiments/20261109T200935Z-h-062-exploration-xrp-usdt/raw/backtest-result-2026-11-09_20-51-55.zip`; `research/experiments/20261109T200935Z-h-062-exploration-ada-usdt/raw/backtest-result-2026-11-09_20-59-34.zip`; `research/experiments/20261109T200935Z-h-062-exploration-ltc-usdt/raw/backtest-result-2026-11-09_21-08-01.zip`; `research/experiments/20261109T200935Z-h-062-exploration-link-usdt/raw/backtest-result-2026-11-09_21-16-33.zip`; `research/experiments/20261109T200935Z-h-062-exploration-doge-usdt/raw/backtest-result-2026-11-09_21-24-09.zip`; `research/experiments/20261109T200935Z-h-062-exploration-sol-usdt/raw/backtest-result-2026-11-09_21-31-10.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 955; lucro líquido: -185.47.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_16_bars | 416 | -14.63 | – | -0.08% | 41% | 4.0 h |
| full_retrace | 227 | 165.50 | – | 1.62% | 100% | 1.8 h |
| breakdown_below_floor | 212 | -185.64 | – | -1.95% | 0% | 1.6 h |
| stop_loss | 100 | -150.71 | – | -3.29% | 0% | 0.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 453 | -158.37 | -0.77% | 41% |
| 3 h a 1 dia | 502 | -27.10 | -0.13% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (398): MFE mediano 1.8%, MAE mediano -0.5%, devolução média do melhor ponto 0.9%, captura mediana 0.56.
- Perdedores (557): MAE mediano -1.9%, MFE mediano 0.5%; 20 (4%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 127.73; – do lucro antes de custos.
- Trades < 3 h: 453 (lucro -158.37); reentradas em < 24 h: 350 (lucro -51.01).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -190.91.
- Lucro por ano de fechamento: 2017: -19.7, 2018: -41.8, 2019: -19.8, 2020: -23.3, 2021: -24.8, 2022: -29.9, 2023: -10.8, 2024: -15.4.

## ETH/USDT

Trades: 1040; lucro líquido: -209.68.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_16_bars | 375 | -2.49 | – | -0.02% | 48% | 4.0 h |
| full_retrace | 269 | 225.75 | – | 1.93% | 100% | 1.8 h |
| breakdown_below_floor | 247 | -215.63 | – | -2.00% | 0% | 1.5 h |
| stop_loss | 148 | -217.05 | – | -3.29% | 0% | 0.6 h |
| force_exit | 1 | -0.27 | – | -0.69% | 0% | 0.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 567 | -219.09 | -0.86% | 37% |
| 3 h a 1 dia | 473 | 9.41 | 0.04% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (450): MFE mediano 1.9%, MAE mediano -0.5%, devolução média do melhor ponto 0.9%, captura mediana 0.59.
- Perdedores (590): MAE mediano -2.4%, MFE mediano 0.6%; 42 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 135.17; – do lucro antes de custos.
- Trades < 3 h: 567 (lucro -219.09); reentradas em < 24 h: 394 (lucro -60.94).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -214.14.
- Lucro por ano de fechamento: 2017: -16.3, 2018: -66.1, 2019: -26.8, 2020: -26.0, 2021: -29.3, 2022: -17.0, 2023: -15.3, 2024: -13.0.

## BNB/USDT

Trades: 877; lucro líquido: -121.46.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_16_bars | 283 | 7.15 | – | 0.05% | 49% | 4.0 h |
| full_retrace | 257 | 255.12 | – | 2.11% | 100% | 1.6 h |
| breakdown_below_floor | 210 | -185.29 | – | -1.89% | 0% | 1.5 h |
| stop_loss | 127 | -198.44 | – | -3.29% | 0% | 0.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 514 | -118.52 | -0.49% | 42% |
| 3 h a 1 dia | 363 | -2.94 | -0.02% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (395): MFE mediano 2.0%, MAE mediano -0.5%, devolução média do melhor ponto 1.0%, captura mediana 0.62.
- Perdedores (482): MAE mediano -2.3%, MFE mediano 0.6%; 48 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 122.41; 12984% do lucro antes de custos.
- Trades < 3 h: 514 (lucro -118.52); reentradas em < 24 h: 335 (lucro -5.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -127.23.
- Lucro por ano de fechamento: 2017: -14.1, 2018: -7.0, 2019: -22.8, 2020: -9.4, 2021: -27.5, 2022: -30.7, 2023: -2.1, 2024: -7.7.

## XRP/USDT

Trades: 881; lucro líquido: -106.90.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_16_bars | 343 | 14.50 | – | 0.09% | 52% | 4.0 h |
| full_retrace | 232 | 258.07 | – | 2.38% | 100% | 1.7 h |
| stop_loss | 157 | -242.41 | – | -3.29% | 0% | 0.7 h |
| breakdown_below_floor | 149 | -137.06 | – | -1.96% | 0% | 1.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 464 | -120.19 | -0.55% | 41% |
| 3 h a 1 dia | 417 | 13.29 | 0.07% | 52% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (409): MFE mediano 2.0%, MAE mediano -0.6%, devolução média do melhor ponto 1.1%, captura mediana 0.59.
- Perdedores (472): MAE mediano -2.5%, MFE mediano 0.6%; 49 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 123.27; 753% do lucro antes de custos.
- Trades < 3 h: 464 (lucro -120.19); reentradas em < 24 h: 337 (lucro -35.01).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -112.88.
- Lucro por ano de fechamento: 2018: -15.9, 2019: -28.0, 2020: -21.8, 2021: -9.8, 2022: -13.5, 2023: -18.1, 2024: 0.2.

## ADA/USDT

Trades: 951; lucro líquido: -129.67.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_16_bars | 317 | 10.96 | – | 0.08% | 49% | 4.0 h |
| full_retrace | 274 | 276.90 | – | 2.20% | 100% | 1.7 h |
| breakdown_below_floor | 211 | -192.21 | – | -1.97% | 0% | 1.5 h |
| stop_loss | 149 | -225.32 | – | -3.28% | 0% | 0.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 554 | -149.88 | -0.58% | 40% |
| 3 h a 1 dia | 397 | 20.22 | 0.11% | 52% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (430): MFE mediano 2.3%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.62.
- Perdedores (521): MAE mediano -2.4%, MFE mediano 0.8%; 55 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 130.69; 12753% do lucro antes de custos.
- Trades < 3 h: 554 (lucro -149.88); reentradas em < 24 h: 378 (lucro -52.37).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -134.27.
- Lucro por ano de fechamento: 2018: -21.6, 2019: -33.7, 2020: -42.4, 2021: -1.4, 2022: -24.4, 2023: -2.2, 2024: -3.9.

## LTC/USDT

Trades: 1037; lucro líquido: -133.19.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_16_bars | 397 | 25.44 | – | 0.14% | 53% | 4.0 h |
| full_retrace | 280 | 267.64 | – | 2.09% | 100% | 1.8 h |
| breakdown_below_floor | 199 | -181.87 | – | -2.00% | 0% | 1.5 h |
| stop_loss | 161 | -244.41 | – | -3.28% | 0% | 0.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 555 | -170.36 | -0.66% | 41% |
| 3 h a 1 dia | 482 | 37.17 | 0.17% | 55% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (491): MFE mediano 2.0%, MAE mediano -0.6%, devolução média do melhor ponto 1.1%, captura mediana 0.59.
- Perdedores (546): MAE mediano -2.5%, MFE mediano 0.7%; 49 (9%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 141.43; 1717% do lucro antes de custos.
- Trades < 3 h: 555 (lucro -170.36); reentradas em < 24 h: 419 (lucro -32.51).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -141.17.
- Lucro por ano de fechamento: 2017: -6.6, 2018: -37.7, 2019: -26.5, 2020: -31.3, 2021: -1.8, 2022: -16.3, 2023: -5.3, 2024: -7.9.

## LINK/USDT

Trades: 789; lucro líquido: -63.07.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_16_bars | 246 | 17.41 | – | 0.15% | 54% | 4.0 h |
| full_retrace | 244 | 287.01 | – | 2.44% | 100% | 1.6 h |
| breakdown_below_floor | 164 | -152.62 | – | -1.94% | 0% | 1.4 h |
| stop_loss | 135 | -214.86 | – | -3.28% | 0% | 0.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 488 | -93.47 | -0.39% | 43% |
| 3 h a 1 dia | 301 | 30.40 | 0.21% | 55% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (377): MFE mediano 2.4%, MAE mediano -0.6%, devolução média do melhor ponto 1.1%, captura mediana 0.63.
- Perdedores (412): MAE mediano -2.6%, MFE mediano 0.8%; 63 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 113.40; 225% do lucro antes de custos.
- Trades < 3 h: 488 (lucro -93.47); reentradas em < 24 h: 317 (lucro -9.73).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -68.69.
- Lucro por ano de fechamento: 2019: -14.9, 2020: -18.7, 2021: -14.6, 2022: -7.1, 2023: -7.9, 2024: 0.1.

## DOGE/USDT

Trades: 765; lucro líquido: -125.96.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_16_bars | 257 | 15.05 | – | 0.13% | 56% | 4.0 h |
| full_retrace | 216 | 211.75 | – | 2.11% | 100% | 1.6 h |
| breakdown_below_floor | 151 | -136.88 | – | -1.95% | 0% | 1.5 h |
| stop_loss | 141 | -215.88 | – | -3.28% | 0% | 0.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 454 | -142.61 | -0.67% | 41% |
| 3 h a 1 dia | 311 | 16.64 | 0.12% | 56% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (358): MFE mediano 2.1%, MAE mediano -0.5%, devolução média do melhor ponto 1.2%, captura mediana 0.57.
- Perdedores (407): MAE mediano -2.6%, MFE mediano 0.8%; 64 (16%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 106.23; – do lucro antes de custos.
- Trades < 3 h: 454 (lucro -142.61); reentradas em < 24 h: 328 (lucro -92.79).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -131.63.
- Lucro por ano de fechamento: 2019: -10.0, 2020: -18.8, 2021: -50.5, 2022: -29.4, 2023: -9.7, 2024: -7.6.

## SOL/USDT

Trades: 553; lucro líquido: -47.22.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| full_retrace | 165 | 236.19 | – | 2.90% | 100% | 1.6 h |
| time_exit_16_bars | 148 | 20.83 | – | 0.29% | 57% | 4.0 h |
| breakdown_below_floor | 134 | -132.59 | – | -2.01% | 0% | 1.4 h |
| stop_loss | 106 | -171.64 | – | -3.28% | 0% | 0.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 362 | -72.62 | -0.41% | 39% |
| 3 h a 1 dia | 191 | 25.40 | 0.27% | 57% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (250): MFE mediano 2.9%, MAE mediano -0.7%, devolução média do melhor ponto 1.3%, captura mediana 0.65.
- Perdedores (303): MAE mediano -2.9%, MFE mediano 0.9%; 50 (17%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 81.41; 238% do lucro antes de custos.
- Trades < 3 h: 362 (lucro -72.62); reentradas em < 24 h: 196 (lucro 6.53).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -55.20.
- Lucro por ano de fechamento: 2020: -10.3, 2021: 1.9, 2022: -16.0, 2023: -11.3, 2024: -11.6.
