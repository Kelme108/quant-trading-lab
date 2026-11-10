# Revisão de trades: H-104 (exploração)

Fonte dos trades: `research/experiments/20261110T211157Z-h-104-exploration-btc-usdt/raw/backtest-result-2026-11-10_21-17-18.zip`; `research/experiments/20261110T211157Z-h-104-exploration-eth-usdt/raw/backtest-result-2026-11-10_21-20-11.zip`; `research/experiments/20261110T211157Z-h-104-exploration-bnb-usdt/raw/backtest-result-2026-11-10_21-22-51.zip`; `research/experiments/20261110T211157Z-h-104-exploration-xrp-usdt/raw/backtest-result-2026-11-10_21-26-01.zip`; `research/experiments/20261110T211157Z-h-104-exploration-ada-usdt/raw/backtest-result-2026-11-10_21-29-13.zip`; `research/experiments/20261110T211157Z-h-104-exploration-ltc-usdt/raw/backtest-result-2026-11-10_21-32-22.zip`; `research/experiments/20261110T211157Z-h-104-exploration-link-usdt/raw/backtest-result-2026-11-10_21-35-22.zip`; `research/experiments/20261110T211157Z-h-104-exploration-doge-usdt/raw/backtest-result-2026-11-10_21-38-07.zip`; `research/experiments/20261110T211157Z-h-104-exploration-sol-usdt/raw/backtest-result-2026-11-10_21-40-29.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 166; lucro líquido: 173.47.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 152 | 377.23 | 217% | 0.91% | 53% | 12.1 h |
| stop_loss | 12 | -177.22 | -102% | -5.28% | 0% | 8.2 h |
| below_open_minus_half_range | 2 | -26.53 | -15% | -4.66% | 0% | 11.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 1 | -13.50 | -5.28% | 0% |
| 3 h a 1 dia | 165 | 186.96 | 0.43% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (81): MFE mediano 3.7%, MAE mediano -0.6%, devolução média do melhor ponto 1.9%, captura mediana 0.54.
- Perdedores (85): MAE mediano -1.8%, MFE mediano 0.8%; 8 (9%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 140.24; 45% do lucro antes de custos.
- Trades < 3 h: 1 (lucro -13.50); reentradas em < 24 h: 17 (lucro 97.06).
- Maior trade = 17% do lucro; top 5 = 66%; top 10 = 120%; lucro sem o melhor = 144.09.
- Lucro por ano de fechamento: 2017: 22.6, 2018: 35.1, 2019: 22.4, 2020: 89.3, 2021: -6.7, 2022: -17.5, 2023: -6.7, 2024: 35.0.

## ETH/USDT

Trades: 182; lucro líquido: 263.63.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 163 | 563.49 | 214% | 1.20% | 62% | 12.1 h |
| stop_loss | 18 | -287.40 | -109% | -5.28% | 0% | 5.7 h |
| below_open_minus_half_range | 1 | -12.46 | -5% | -3.82% | 0% | 6.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 5 | -70.54 | -5.28% | 0% |
| 3 h a 1 dia | 177 | 334.16 | 0.69% | 57% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (101): MFE mediano 4.0%, MAE mediano -0.6%, devolução média do melhor ponto 2.3%, captura mediana 0.52.
- Perdedores (81): MAE mediano -2.9%, MFE mediano 1.0%; 18 (22%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 165.78; 39% do lucro antes de custos.
- Trades < 3 h: 5 (lucro -70.54); reentradas em < 24 h: 19 (lucro 80.90).
- Maior trade = 23% do lucro; top 5 = 64%; top 10 = 97%; lucro sem o melhor = 202.93.
- Lucro por ano de fechamento: 2017: -22.2, 2018: 18.0, 2019: 26.5, 2020: 234.4, 2021: 103.8, 2022: -34.7, 2023: -37.4, 2024: -24.8.

## BNB/USDT

Trades: 186; lucro líquido: 543.72.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 161 | 970.58 | 179% | 1.92% | 63% | 13.3 h |
| stop_loss | 22 | -385.78 | -71% | -5.28% | 0% | 4.5 h |
| below_open_minus_half_range | 3 | -41.08 | -8% | -3.95% | 0% | 12.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 10 | -182.03 | -5.28% | 0% |
| 3 h a 1 dia | 176 | 725.75 | 1.33% | 58% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (102): MFE mediano 3.7%, MAE mediano -1.2%, devolução média do melhor ponto 2.3%, captura mediana 0.54.
- Perdedores (84): MAE mediano -2.9%, MFE mediano 0.9%; 13 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 191.06; 26% do lucro antes de custos.
- Trades < 3 h: 10 (lucro -182.03); reentradas em < 24 h: 22 (lucro 148.29).
- Maior trade = 27% do lucro; top 5 = 77%; top 10 = 110%; lucro sem o melhor = 395.32.
- Lucro por ano de fechamento: 2018: 56.2, 2019: 204.3, 2020: 2.4, 2021: 309.0, 2022: -48.8, 2023: -37.9, 2024: 58.5.

## XRP/USDT

Trades: 146; lucro líquido: 148.21.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 115 | 639.93 | 432% | 1.95% | 52% | 12.1 h |
| stop_loss | 30 | -478.04 | -323% | -5.28% | 0% | 4.2 h |
| below_open_minus_half_range | 1 | -13.67 | -9% | -4.31% | 0% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 12 | -191.45 | -5.28% | 0% |
| 3 h a 1 dia | 134 | 339.66 | 0.94% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (60): MFE mediano 5.4%, MAE mediano -1.6%, devolução média do melhor ponto 3.7%, captura mediana 0.49.
- Perdedores (86): MAE mediano -4.2%, MFE mediano 1.1%; 27 (31%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 128.45; 46% do lucro antes de custos.
- Trades < 3 h: 12 (lucro -191.45); reentradas em < 24 h: 19 (lucro -126.26).
- Maior trade = 62% do lucro; top 5 = 235%; top 10 = 353%; lucro sem o melhor = 56.97.
- Lucro por ano de fechamento: 2018: 45.3, 2019: 40.9, 2020: 132.9, 2021: 67.6, 2022: -21.9, 2023: -126.9, 2024: 10.4.

## ADA/USDT

Trades: 161; lucro líquido: 142.50.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 127 | 675.24 | 474% | 1.85% | 61% | 12.5 h |
| stop_loss | 33 | -522.87 | -367% | -5.28% | 0% | 6.7 h |
| below_open_minus_half_range | 1 | -9.87 | -7% | -3.29% | 0% | 4.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 7 | -116.10 | -5.28% | 0% |
| 3 h a 1 dia | 154 | 258.60 | 0.61% | 50% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (77): MFE mediano 5.3%, MAE mediano -1.3%, devolução média do melhor ponto 3.0%, captura mediana 0.50.
- Perdedores (84): MAE mediano -4.0%, MFE mediano 1.4%; 33 (39%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 141.36; 50% do lucro antes de custos.
- Trades < 3 h: 7 (lucro -116.10); reentradas em < 24 h: 30 (lucro -70.66).
- Maior trade = 31% do lucro; top 5 = 139%; top 10 = 258%; lucro sem o melhor = 98.71.
- Lucro por ano de fechamento: 2018: -17.8, 2019: 53.9, 2020: 153.0, 2021: 115.8, 2022: -33.1, 2023: -78.6, 2024: -50.8.

## LTC/USDT

Trades: 181; lucro líquido: 61.02.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 143 | 612.33 | 1004% | 1.59% | 57% | 13.4 h |
| stop_loss | 37 | -540.72 | -886% | -5.28% | 0% | 6.3 h |
| below_open_minus_half_range | 1 | -10.59 | -17% | -4.08% | 0% | 4.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 9 | -132.57 | -5.28% | 0% |
| 3 h a 1 dia | 172 | 193.59 | 0.44% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (82): MFE mediano 4.8%, MAE mediano -1.1%, devolução média do melhor ponto 2.7%, captura mediana 0.58.
- Perdedores (99): MAE mediano -4.0%, MFE mediano 1.1%; 25 (25%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 147.98; 71% do lucro antes de custos.
- Trades < 3 h: 9 (lucro -132.57); reentradas em < 24 h: 17 (lucro -41.26).
- Maior trade = 75% do lucro; top 5 = 304%; top 10 = 529%; lucro sem o melhor = 15.17.
- Lucro por ano de fechamento: 2018: -20.2, 2019: 91.4, 2020: 53.6, 2021: 53.2, 2022: -69.7, 2023: -49.3, 2024: 2.0.

## LINK/USDT

Trades: 180; lucro líquido: 52.28.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 141 | 585.65 | 1120% | 1.62% | 58% | 11.3 h |
| stop_loss | 38 | -524.84 | -1004% | -5.28% | 0% | 6.2 h |
| below_open_minus_half_range | 1 | -8.54 | -16% | -3.41% | 0% | 2.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 14 | -186.22 | -5.15% | 0% |
| 3 h a 1 dia | 166 | 238.50 | 0.58% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (82): MFE mediano 5.2%, MAE mediano -1.4%, devolução média do melhor ponto 2.9%, captura mediana 0.49.
- Perdedores (98): MAE mediano -4.0%, MFE mediano 1.7%; 40 (41%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 140.52; 73% do lucro antes de custos.
- Trades < 3 h: 14 (lucro -186.22); reentradas em < 24 h: 24 (lucro -8.53).
- Maior trade = 67% do lucro; top 5 = 307%; top 10 = 557%; lucro sem o melhor = 17.36.
- Lucro por ano de fechamento: 2019: -20.8, 2020: 105.3, 2021: 12.9, 2022: -81.6, 2023: 78.2, 2024: -41.6.

## DOGE/USDT

Trades: 140; lucro líquido: 193.82.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 91 | 1014.18 | 523% | 3.77% | 54% | 13.8 h |
| stop_loss | 48 | -804.39 | -415% | -5.28% | 0% | 4.6 h |
| below_open_minus_half_range | 1 | -15.97 | -8% | -4.47% | 0% | 13.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 17 | -269.60 | -5.28% | 0% |
| 3 h a 1 dia | 123 | 463.43 | 1.42% | 40% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (49): MFE mediano 8.4%, MAE mediano -1.5%, devolução média do melhor ponto 7.0%, captura mediana 0.55.
- Perdedores (91): MAE mediano -5.1%, MFE mediano 1.3%; 32 (35%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 129.19; 40% do lucro antes de custos.
- Trades < 3 h: 17 (lucro -269.60); reentradas em < 24 h: 22 (lucro 225.57).
- Maior trade = 88% do lucro; top 5 = 278%; top 10 = 382%; lucro sem o melhor = 23.95.
- Lucro por ano de fechamento: 2019: -5.3, 2020: 55.7, 2021: 412.5, 2022: -84.3, 2023: -161.7, 2024: -23.1.

## SOL/USDT

Trades: 136; lucro líquido: -91.65.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 94 | 438.27 | – | 1.99% | 62% | 11.4 h |
| stop_loss | 42 | -529.93 | – | -5.28% | 0% | 5.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 14 | -178.25 | -5.28% | 0% |
| 3 h a 1 dia | 122 | 86.60 | 0.32% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (58): MFE mediano 5.9%, MAE mediano -1.6%, devolução média do melhor ponto 3.8%, captura mediana 0.53.
- Perdedores (78): MAE mediano -5.2%, MFE mediano 1.5%; 30 (38%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 96.11; 2155% do lucro antes de custos.
- Trades < 3 h: 14 (lucro -178.25); reentradas em < 24 h: 28 (lucro -48.63).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -130.84.
- Lucro por ano de fechamento: 2020: -10.6, 2021: -12.0, 2022: -88.5, 2023: 49.9, 2024: -30.5.
