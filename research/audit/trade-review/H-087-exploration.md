# Revisão de trades: H-087 (exploração)

Fonte dos trades: `research/experiments/20261108T172612Z-h-087-exploration-btc-usdt/raw/backtest-result-2026-11-08_17-40-03.zip`; `research/experiments/20261108T172612Z-h-087-exploration-eth-usdt/raw/backtest-result-2026-11-08_17-44-02.zip`; `research/experiments/20261108T172612Z-h-087-exploration-bnb-usdt/raw/backtest-result-2026-11-08_17-47-32.zip`; `research/experiments/20261108T172612Z-h-087-exploration-xrp-usdt/raw/backtest-result-2026-11-08_17-50-43.zip`; `research/experiments/20261108T172612Z-h-087-exploration-ada-usdt/raw/backtest-result-2026-11-08_17-54-36.zip`; `research/experiments/20261108T172612Z-h-087-exploration-ltc-usdt/raw/backtest-result-2026-11-08_17-58-37.zip`; `research/experiments/20261108T172612Z-h-087-exploration-link-usdt/raw/backtest-result-2026-11-08_18-02-06.zip`; `research/experiments/20261108T172612Z-h-087-exploration-doge-usdt/raw/backtest-result-2026-11-08_18-05-21.zip`; `research/experiments/20261108T172612Z-h-087-exploration-sol-usdt/raw/backtest-result-2026-11-08_18-08-17.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 814; lucro líquido: -130.21.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| accel_z_below_0 | 649 | 46.23 | – | 0.15% | 38% | 3.0 h |
| stop_loss | 164 | -176.21 | – | -2.29% | 0% | 1.0 h |
| force_exit | 1 | -0.23 | – | -0.53% | 0% | 2.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 425 | -225.71 | -1.14% | 12% |
| 3 h a 1 dia | 389 | 95.50 | 0.53% | 50% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (247): MFE mediano 2.3%, MAE mediano -0.5%, devolução média do melhor ponto 1.6%, captura mediana 0.42.
- Perdedores (567): MAE mediano -1.3%, MFE mediano 0.5%; 42 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 112.44; – do lucro antes de custos.
- Trades < 3 h: 425 (lucro -225.71); reentradas em < 24 h: 348 (lucro -57.64).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -133.76.
- Lucro por ano de fechamento: 2017: -27.6, 2018: -10.6, 2019: -8.3, 2020: -26.0, 2021: -28.0, 2022: -14.6, 2023: -8.6, 2024: -6.6.

## ETH/USDT

Trades: 935; lucro líquido: -183.50.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| accel_z_below_0 | 692 | 64.04 | – | 0.20% | 45% | 3.0 h |
| stop_loss | 242 | -252.70 | – | -2.29% | 0% | 1.1 h |
| time_exit_8h | 1 | 5.16 | – | 10.82% | 100% | 8.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 524 | -298.64 | -1.26% | 14% |
| 3 h a 1 dia | 411 | 115.14 | 0.62% | 57% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (309): MFE mediano 2.5%, MAE mediano -0.5%, devolução média do melhor ponto 1.7%, captura mediana 0.42.
- Perdedores (626): MAE mediano -1.7%, MFE mediano 0.6%; 60 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 124.71; – do lucro antes de custos.
- Trades < 3 h: 524 (lucro -298.64); reentradas em < 24 h: 435 (lucro -102.86).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -188.66.
- Lucro por ano de fechamento: 2017: -20.9, 2018: -40.8, 2019: -22.8, 2020: -12.8, 2021: -52.1, 2022: -30.9, 2023: -2.0, 2024: -1.2.

## BNB/USDT

Trades: 971; lucro líquido: -165.89.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| accel_z_below_0 | 693 | 127.29 | – | 0.38% | 45% | 3.0 h |
| stop_loss | 277 | -296.37 | – | -2.29% | 0% | 1.0 h |
| time_exit_8h | 1 | 3.19 | – | 6.72% | 100% | 8.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 561 | -338.58 | -1.30% | 12% |
| 3 h a 1 dia | 410 | 172.70 | 0.90% | 59% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (310): MFE mediano 2.5%, MAE mediano -0.5%, devolução média do melhor ponto 1.9%, captura mediana 0.42.
- Perdedores (661): MAE mediano -1.7%, MFE mediano 0.6%; 59 (9%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 132.87; – do lucro antes de custos.
- Trades < 3 h: 561 (lucro -338.58); reentradas em < 24 h: 491 (lucro -91.76).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -174.75.
- Lucro por ano de fechamento: 2017: -3.7, 2018: -43.8, 2019: -16.6, 2020: -7.9, 2021: -35.5, 2022: -29.0, 2023: -22.5, 2024: -6.9.

## XRP/USDT

Trades: 829; lucro líquido: -194.43.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| accel_z_below_0 | 557 | 87.08 | – | 0.34% | 44% | 3.0 h |
| stop_loss | 272 | -281.51 | – | -2.29% | 0% | 0.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 482 | -322.20 | -1.48% | 10% |
| 3 h a 1 dia | 347 | 127.77 | 0.82% | 56% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (245): MFE mediano 3.1%, MAE mediano -0.5%, devolução média do melhor ponto 2.4%, captura mediana 0.36.
- Perdedores (584): MAE mediano -2.0%, MFE mediano 0.6%; 81 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 111.27; – do lucro antes de custos.
- Trades < 3 h: 482 (lucro -322.20); reentradas em < 24 h: 416 (lucro -106.18).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -204.16.
- Lucro por ano de fechamento: 2018: -24.2, 2019: -26.1, 2020: -39.0, 2021: -55.3, 2022: -11.5, 2023: -21.6, 2024: -16.8.

## ADA/USDT

Trades: 986; lucro líquido: -173.75.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| accel_z_below_0 | 678 | 142.44 | – | 0.47% | 50% | 3.0 h |
| stop_loss | 307 | -318.09 | – | -2.29% | 0% | 1.0 h |
| time_exit_8h | 1 | 1.89 | – | 3.98% | 100% | 8.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 588 | -344.17 | -1.30% | 15% |
| 3 h a 1 dia | 398 | 170.41 | 0.96% | 62% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (339): MFE mediano 2.9%, MAE mediano -0.6%, devolução média do melhor ponto 2.0%, captura mediana 0.41.
- Perdedores (647): MAE mediano -2.0%, MFE mediano 0.7%; 83 (13%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 131.80; – do lucro antes de custos.
- Trades < 3 h: 588 (lucro -344.17); reentradas em < 24 h: 526 (lucro -101.79).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -180.92.
- Lucro por ano de fechamento: 2018: -33.5, 2019: -36.5, 2020: -22.8, 2021: -40.8, 2022: -24.6, 2023: -15.0, 2024: -0.6.

## LTC/USDT

Trades: 939; lucro líquido: -194.21.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| accel_z_below_0 | 689 | 62.73 | – | 0.20% | 43% | 2.9 h |
| stop_loss | 250 | -256.94 | – | -2.28% | 0% | 1.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 529 | -309.46 | -1.31% | 12% |
| 3 h a 1 dia | 410 | 115.25 | 0.64% | 57% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (298): MFE mediano 2.6%, MAE mediano -0.6%, devolução média do melhor ponto 1.8%, captura mediana 0.41.
- Perdedores (641): MAE mediano -1.8%, MFE mediano 0.6%; 65 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 123.54; – do lucro antes de custos.
- Trades < 3 h: 529 (lucro -309.46); reentradas em < 24 h: 463 (lucro -116.53).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -198.64.
- Lucro por ano de fechamento: 2018: -53.6, 2019: -31.2, 2020: -21.2, 2021: -59.3, 2022: -15.1, 2023: -11.6, 2024: -2.1.

## LINK/USDT

Trades: 889; lucro líquido: -169.63.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| accel_z_below_0 | 583 | 140.99 | – | 0.52% | 48% | 2.9 h |
| stop_loss | 304 | -319.11 | – | -2.29% | 0% | 1.0 h |
| time_exit_8h | 2 | 8.49 | – | 10.00% | 100% | 8.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 555 | -345.57 | -1.36% | 14% |
| 3 h a 1 dia | 334 | 175.94 | 1.15% | 63% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (284): MFE mediano 3.0%, MAE mediano -0.6%, devolução média do melhor ponto 2.2%, captura mediana 0.43.
- Perdedores (605): MAE mediano -2.0%, MFE mediano 0.7%; 84 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 120.17; – do lucro antes de custos.
- Trades < 3 h: 555 (lucro -345.57); reentradas em < 24 h: 461 (lucro -112.06).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -189.19.
- Lucro por ano de fechamento: 2019: -24.0, 2020: -56.7, 2021: -36.4, 2022: -31.4, 2023: -12.0, 2024: -9.1.

## DOGE/USDT

Trades: 707; lucro líquido: -108.37.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| accel_z_below_0 | 425 | 160.68 | – | 0.78% | 44% | 2.9 h |
| stop_loss | 280 | -310.49 | – | -2.29% | 0% | 0.8 h |
| time_exit_8h | 2 | 41.44 | – | 42.41% | 100% | 8.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 475 | -313.10 | -1.36% | 13% |
| 3 h a 1 dia | 232 | 204.73 | 1.82% | 56% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (191): MFE mediano 3.7%, MAE mediano -0.6%, devolução média do melhor ponto 3.9%, captura mediana 0.39.
- Perdedores (516): MAE mediano -2.1%, MFE mediano 0.8%; 114 (22%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 101.84; – do lucro antes de custos.
- Trades < 3 h: 475 (lucro -313.10); reentradas em < 24 h: 374 (lucro -2.63).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -148.96.
- Lucro por ano de fechamento: 2019: -12.4, 2020: -14.3, 2021: 0.5, 2022: -27.9, 2023: -33.9, 2024: -20.3.

## SOL/USDT

Trades: 599; lucro líquido: -81.45.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| accel_z_below_0 | 360 | 181.87 | – | 1.05% | 59% | 3.2 h |
| stop_loss | 239 | -263.32 | – | -2.29% | 0% | 0.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 369 | -261.51 | -1.47% | 14% |
| 3 h a 1 dia | 230 | 180.06 | 1.63% | 70% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (212): MFE mediano 3.4%, MAE mediano -0.6%, devolução média do melhor ponto 2.4%, captura mediana 0.39.
- Perdedores (387): MAE mediano -2.1%, MFE mediano 0.7%; 62 (16%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 85.49; 2121% do lucro antes de custos.
- Trades < 3 h: 369 (lucro -261.51); reentradas em < 24 h: 318 (lucro -77.41).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -90.93.
- Lucro por ano de fechamento: 2020: -8.4, 2021: -36.3, 2022: -28.6, 2023: 1.2, 2024: -9.4.
