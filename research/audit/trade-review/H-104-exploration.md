# Revisão de trades: H-104 (exploração)

Fonte dos trades: `research/experiments/20261113T011331Z-h-104-exploration-btc-usdt/raw/backtest-result-2026-11-13_01-35-54.zip`; `research/experiments/20261113T011331Z-h-104-exploration-eth-usdt/raw/backtest-result-2026-11-13_01-39-35.zip`; `research/experiments/20261113T011331Z-h-104-exploration-bnb-usdt/raw/backtest-result-2026-11-13_01-43-24.zip`; `research/experiments/20261113T011331Z-h-104-exploration-xrp-usdt/raw/backtest-result-2026-11-13_01-47-03.zip`; `research/experiments/20261113T011331Z-h-104-exploration-ada-usdt/raw/backtest-result-2026-11-13_01-50-44.zip`; `research/experiments/20261113T011331Z-h-104-exploration-ltc-usdt/raw/backtest-result-2026-11-13_01-54-30.zip`; `research/experiments/20261113T011331Z-h-104-exploration-link-usdt/raw/backtest-result-2026-11-13_01-58-29.zip`; `research/experiments/20261113T011331Z-h-104-exploration-doge-usdt/raw/backtest-result-2026-11-13_02-01-51.zip`; `research/experiments/20261113T011331Z-h-104-exploration-sol-usdt/raw/backtest-result-2026-11-13_02-05-25.zip`; `research/experiments/20261113T011331Z-h-104-exploration-avax-usdt/raw/backtest-result-2026-11-13_02-08-47.zip`; `research/experiments/20261113T011331Z-h-104-exploration-dot-usdt/raw/backtest-result-2026-11-13_02-12-02.zip`; `research/experiments/20261113T011331Z-h-104-exploration-trx-usdt/raw/backtest-result-2026-11-13_02-15-29.zip`; `research/experiments/20261113T011331Z-h-104-exploration-near-usdt/raw/backtest-result-2026-11-13_02-18-50.zip`; `research/experiments/20261113T011331Z-h-104-exploration-uni-usdt/raw/backtest-result-2026-11-13_02-22-18.zip`; `research/experiments/20261113T011331Z-h-104-exploration-bch-usdt/raw/backtest-result-2026-11-13_02-25-36.zip`; `research/experiments/20261113T011331Z-h-104-exploration-xlm-usdt/raw/backtest-result-2026-11-13_02-29-01.zip`; `research/experiments/20261113T011331Z-h-104-exploration-fil-usdt/raw/backtest-result-2026-11-13_02-32-29.zip`; `research/experiments/20261113T011331Z-h-104-exploration-aave-usdt/raw/backtest-result-2026-11-13_02-35-53.zip`; `research/experiments/20261113T011331Z-h-104-exploration-inj-usdt/raw/backtest-result-2026-11-13_02-39-07.zip`; `research/experiments/20261113T011331Z-h-104-exploration-hbar-usdt/raw/backtest-result-2026-11-13_02-42-26.zip`; `research/experiments/20261113T011331Z-h-104-exploration-op-usdt/raw/backtest-result-2026-11-13_02-45-47.zip`; `research/experiments/20261113T011331Z-h-104-exploration-apt-usdt/raw/backtest-result-2026-11-13_02-49-08.zip`; `research/experiments/20261113T011331Z-h-104-exploration-arb-usdt/raw/backtest-result-2026-11-13_02-52-24.zip`; `research/experiments/20261113T011331Z-h-104-exploration-sui-usdt/raw/backtest-result-2026-11-13_02-55-34.zip`; `research/experiments/20261113T011331Z-h-104-exploration-atom-usdt/raw/backtest-result-2026-11-13_02-58-49.zip`; `research/experiments/20261113T011331Z-h-104-exploration-etc-usdt/raw/backtest-result-2026-11-13_03-02-35.zip`. Janela: exploração. Cenário de custo: base.

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

## AVAX/USDT

Trades: 115; lucro líquido: -265.99.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 60 | 399.11 | – | 2.83% | 62% | 11.7 h |
| stop_loss | 54 | -657.65 | – | -5.28% | 0% | 4.6 h |
| below_open_minus_half_range | 1 | -7.45 | – | -3.66% | 0% | 4.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 23 | -288.31 | -5.28% | 0% |
| 3 h a 1 dia | 92 | 22.32 | 0.03% | 40% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (37): MFE mediano 6.8%, MAE mediano -1.9%, devolução média do melhor ponto 4.0%, captura mediana 0.59.
- Perdedores (78): MAE mediano -5.5%, MFE mediano 1.2%; 30 (38%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 76.67; – do lucro antes de custos.
- Trades < 3 h: 23 (lucro -288.31); reentradas em < 24 h: 24 (lucro -151.11).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -324.66.
- Lucro por ano de fechamento: 2020: -5.8, 2021: -105.2, 2022: -63.9, 2023: -73.1, 2024: -17.9.

## DOT/USDT

Trades: 93; lucro líquido: 62.32.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 74 | 333.36 | 535% | 1.70% | 53% | 12.0 h |
| stop_loss | 18 | -260.31 | -418% | -5.28% | 0% | 5.4 h |
| below_open_minus_half_range | 1 | -10.73 | -17% | -3.80% | 0% | 17.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 7 | -102.93 | -5.28% | 0% |
| 3 h a 1 dia | 86 | 165.25 | 0.74% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (39): MFE mediano 5.7%, MAE mediano -0.9%, devolução média do melhor ponto 3.7%, captura mediana 0.51.
- Perdedores (54): MAE mediano -4.0%, MFE mediano 1.5%; 20 (37%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 76.08; 55% do lucro antes de custos.
- Trades < 3 h: 7 (lucro -102.93); reentradas em < 24 h: 16 (lucro 64.91).
- Maior trade = 76% do lucro; top 5 = 304%; top 10 = 488%; lucro sem o melhor = 14.92.
- Lucro por ano de fechamento: 2020: 36.1, 2021: 82.2, 2022: -18.2, 2023: 8.3, 2024: -46.2.

## TRX/USDT

Trades: 156; lucro líquido: 142.78.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 130 | 532.14 | 373% | 1.49% | 56% | 12.7 h |
| stop_loss | 25 | -377.98 | -265% | -5.27% | 0% | 5.3 h |
| below_open_minus_half_range | 1 | -11.38 | -8% | -3.83% | 0% | 14.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 10 | -148.93 | -5.27% | 0% |
| 3 h a 1 dia | 146 | 291.71 | 0.76% | 50% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (73): MFE mediano 5.7%, MAE mediano -1.5%, devolução média do melhor ponto 4.0%, captura mediana 0.46.
- Perdedores (83): MAE mediano -3.8%, MFE mediano 1.0%; 24 (29%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 132.92; 48% do lucro antes de custos.
- Trades < 3 h: 10 (lucro -148.93); reentradas em < 24 h: 30 (lucro -144.31).
- Maior trade = 71% do lucro; top 5 = 168%; top 10 = 252%; lucro sem o melhor = 41.84.
- Lucro por ano de fechamento: 2018: 35.0, 2019: 27.2, 2020: 79.5, 2021: 97.1, 2022: -63.0, 2023: -28.7, 2024: -4.3.

## NEAR/USDT

Trades: 127; lucro líquido: -272.85.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 78 | 255.64 | – | 1.72% | 62% | 12.3 h |
| stop_loss | 48 | -520.07 | – | -5.28% | 0% | 4.4 h |
| below_open_minus_half_range | 1 | -8.42 | – | -4.79% | 0% | 9.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 16 | -179.37 | -5.28% | 0% |
| 3 h a 1 dia | 111 | -93.48 | -0.35% | 43% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (48): MFE mediano 6.7%, MAE mediano -1.7%, devolução média do melhor ponto 3.9%, captura mediana 0.51.
- Perdedores (79): MAE mediano -5.3%, MFE mediano 1.8%; 36 (46%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 74.36; – do lucro antes de custos.
- Trades < 3 h: 16 (lucro -179.37); reentradas em < 24 h: 19 (lucro -20.02).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -310.13.
- Lucro por ano de fechamento: 2020: -32.1, 2021: -193.3, 2022: -23.1, 2023: -59.4, 2024: 35.0.

## UNI/USDT

Trades: 112; lucro líquido: -111.43.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 80 | 293.98 | – | 1.57% | 49% | 11.9 h |
| stop_loss | 32 | -405.41 | – | -5.27% | 0% | 6.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 8 | -101.08 | -5.27% | 0% |
| 3 h a 1 dia | 104 | -10.35 | -0.01% | 38% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (39): MFE mediano 5.1%, MAE mediano -1.2%, devolução média do melhor ponto 3.4%, captura mediana 0.50.
- Perdedores (73): MAE mediano -4.9%, MFE mediano 1.6%; 30 (41%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 78.97; – do lucro antes de custos.
- Trades < 3 h: 8 (lucro -101.08); reentradas em < 24 h: 13 (lucro -62.14).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -185.65.
- Lucro por ano de fechamento: 2020: -47.5, 2021: -2.2, 2022: -21.9, 2023: -33.4, 2024: -6.4.

## BCH/USDT

Trades: 120; lucro líquido: 68.07.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 94 | 426.87 | 627% | 1.80% | 47% | 13.2 h |
| stop_loss | 25 | -346.46 | -509% | -5.28% | 0% | 7.0 h |
| below_open_minus_half_range | 1 | -12.35 | -18% | -5.06% | 0% | 13.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 4 | -53.81 | -5.28% | 0% |
| 3 h a 1 dia | 116 | 121.87 | 0.46% | 38% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (44): MFE mediano 6.4%, MAE mediano -1.0%, devolução média do melhor ponto 3.6%, captura mediana 0.55.
- Perdedores (76): MAE mediano -3.8%, MFE mediano 1.2%; 23 (30%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 93.85; 58% do lucro antes de custos.
- Trades < 3 h: 4 (lucro -53.81); reentradas em < 24 h: 13 (lucro 57.43).
- Maior trade = 140% do lucro; top 5 = 435%; top 10 = 592%; lucro sem o melhor = -27.22.
- Lucro por ano de fechamento: 2020: -53.4, 2021: 157.9, 2022: 11.1, 2023: -66.4, 2024: 18.9.

## XLM/USDT

Trades: 135; lucro líquido: 67.77.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 102 | 510.74 | 754% | 1.99% | 61% | 12.9 h |
| stop_loss | 31 | -423.36 | -625% | -5.28% | 0% | 3.4 h |
| below_open_minus_half_range | 2 | -19.61 | -29% | -4.01% | 0% | 9.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 18 | -246.28 | -5.28% | 0% |
| 3 h a 1 dia | 117 | 314.05 | 1.08% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (62): MFE mediano 5.3%, MAE mediano -1.5%, devolução média do melhor ponto 4.3%, captura mediana 0.45.
- Perdedores (73): MAE mediano -4.2%, MFE mediano 1.5%; 28 (38%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 103.99; 61% do lucro antes de custos.
- Trades < 3 h: 18 (lucro -246.28); reentradas em < 24 h: 24 (lucro -173.68).
- Maior trade = 155% do lucro; top 5 = 373%; top 10 = 546%; lucro sem o melhor = -37.16.
- Lucro por ano de fechamento: 2018: 36.5, 2019: 23.1, 2020: -18.9, 2021: -59.3, 2022: -10.6, 2023: 102.3, 2024: -5.4.

## FIL/USDT

Trades: 78; lucro líquido: 421.42.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 55 | 805.72 | 191% | 4.89% | 71% | 13.4 h |
| stop_loss | 23 | -384.30 | -91% | -5.28% | 0% | 4.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 8 | -128.40 | -5.28% | 0% |
| 3 h a 1 dia | 70 | 549.82 | 2.71% | 56% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (39): MFE mediano 9.2%, MAE mediano -1.7%, devolução média do melhor ponto 5.5%, captura mediana 0.52.
- Perdedores (39): MAE mediano -5.3%, MFE mediano 2.0%; 19 (49%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 74.41; 15% do lucro antes de custos.
- Trades < 3 h: 8 (lucro -128.40); reentradas em < 24 h: 16 (lucro 159.48).
- Maior trade = 25% do lucro; top 5 = 94%; top 10 = 139%; lucro sem o melhor = 315.86.
- Lucro por ano de fechamento: 2020: -16.1, 2021: 252.1, 2022: 57.8, 2023: 88.1, 2024: 39.5.

## AAVE/USDT

Trades: 103; lucro líquido: -240.91.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 66 | 198.66 | – | 1.33% | 55% | 11.6 h |
| stop_loss | 37 | -439.57 | – | -5.27% | 0% | 5.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 9 | -107.50 | -5.27% | 0% |
| 3 h a 1 dia | 94 | -133.41 | -0.63% | 38% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (36): MFE mediano 4.8%, MAE mediano -1.2%, devolução média do melhor ponto 3.6%, captura mediana 0.51.
- Perdedores (67): MAE mediano -5.2%, MFE mediano 1.4%; 27 (40%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 68.33; – do lucro antes de custos.
- Trades < 3 h: 9 (lucro -107.50); reentradas em < 24 h: 19 (lucro -80.48).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -293.39.
- Lucro por ano de fechamento: 2020: -26.3, 2021: -76.4, 2022: 41.8, 2023: -128.2, 2024: -51.8.

## INJ/USDT

Trades: 132; lucro líquido: -243.50.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 86 | 276.62 | – | 1.57% | 55% | 11.2 h |
| stop_loss | 46 | -520.12 | – | -5.28% | 0% | 3.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 23 | -267.31 | -5.28% | 0% |
| 3 h a 1 dia | 109 | 23.81 | 0.13% | 43% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (47): MFE mediano 7.3%, MAE mediano -2.0%, devolução média do melhor ponto 4.9%, captura mediana 0.48.
- Perdedores (85): MAE mediano -5.0%, MFE mediano 2.2%; 45 (53%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 81.01; – do lucro antes de custos.
- Trades < 3 h: 23 (lucro -267.31); reentradas em < 24 h: 22 (lucro -59.02).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -276.35.
- Lucro por ano de fechamento: 2020: -39.2, 2021: -84.5, 2022: -83.8, 2023: -26.8, 2024: -9.2.

## HBAR/USDT

Trades: 112; lucro líquido: -190.07.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 68 | 357.32 | – | 2.22% | 65% | 14.1 h |
| stop_loss | 44 | -547.39 | – | -5.26% | 0% | 3.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 23 | -291.32 | -5.26% | 0% |
| 3 h a 1 dia | 89 | 101.25 | 0.46% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (44): MFE mediano 6.7%, MAE mediano -2.0%, devolução média do melhor ponto 5.8%, captura mediana 0.43.
- Perdedores (68): MAE mediano -5.3%, MFE mediano 2.7%; 43 (63%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 77.36; – do lucro antes de custos.
- Trades < 3 h: 23 (lucro -291.32); reentradas em < 24 h: 18 (lucro -30.84).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -254.04.
- Lucro por ano de fechamento: 2020: -26.4, 2021: -53.6, 2022: -12.2, 2023: -81.8, 2024: -16.0.

## OP/USDT

Trades: 46; lucro líquido: 74.00.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 30 | 306.84 | 415% | 3.84% | 73% | 9.5 h |
| stop_loss | 16 | -232.84 | -315% | -5.26% | 0% | 4.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 6 | -88.83 | -5.26% | 0% |
| 3 h a 1 dia | 40 | 162.84 | 1.56% | 55% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (22): MFE mediano 9.6%, MAE mediano -1.1%, devolução média do melhor ponto 4.6%, captura mediana 0.38.
- Perdedores (24): MAE mediano -5.4%, MFE mediano 2.0%; 12 (50%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 37.63; 34% do lucro antes de custos.
- Trades < 3 h: 6 (lucro -88.83); reentradas em < 24 h: 9 (lucro 19.50).
- Maior trade = 91% do lucro; top 5 = 258%; top 10 = 372%; lucro sem o melhor = 6.56.
- Lucro por ano de fechamento: 2022: 77.3, 2023: 79.4, 2024: -82.6.

## APT/USDT

Trades: 36; lucro líquido: -12.38.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 23 | 163.06 | – | 2.84% | 70% | 11.0 h |
| stop_loss | 13 | -175.44 | – | -5.28% | 0% | 5.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 6 | -81.72 | -5.28% | 0% |
| 3 h a 1 dia | 30 | 69.34 | 0.95% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (16): MFE mediano 5.7%, MAE mediano -0.9%, devolução média do melhor ponto 3.5%, captura mediana 0.39.
- Perdedores (20): MAE mediano -5.6%, MFE mediano 1.9%; 10 (50%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 27.14; 184% do lucro antes de custos.
- Trades < 3 h: 6 (lucro -81.72); reentradas em < 24 h: 2 (lucro -26.48).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -63.37.
- Lucro por ano de fechamento: 2023: 4.9, 2024: -17.2.

## ARB/USDT

Trades: 31; lucro líquido: -130.89.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 17 | 39.92 | – | 1.02% | 59% | 11.8 h |
| stop_loss | 13 | -161.11 | – | -5.28% | 0% | 7.5 h |
| below_open_minus_half_range | 1 | -9.70 | – | -3.93% | 0% | 16.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 4 | -48.40 | -5.28% | 0% |
| 3 h a 1 dia | 27 | -82.48 | -1.27% | 37% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (10): MFE mediano 5.1%, MAE mediano -1.0%, devolução média do melhor ponto 2.5%, captura mediana 0.47.
- Perdedores (21): MAE mediano -5.9%, MFE mediano 1.2%; 8 (38%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 21.37; – do lucro antes de custos.
- Trades < 3 h: 4 (lucro -48.40); reentradas em < 24 h: 2 (lucro 25.20).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -154.38.
- Lucro por ano de fechamento: 2023: -79.8, 2024: -51.0.

## SUI/USDT

Trades: 30; lucro líquido: -8.22.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 18 | 152.51 | – | 3.41% | 67% | 10.5 h |
| stop_loss | 12 | -160.73 | – | -5.28% | 0% | 5.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 2 | -26.56 | -5.28% | 0% |
| 3 h a 1 dia | 28 | 18.34 | 0.30% | 43% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (12): MFE mediano 8.0%, MAE mediano -1.2%, devolução média do melhor ponto 3.7%, captura mediana 0.57.
- Perdedores (18): MAE mediano -5.2%, MFE mediano 1.1%; 5 (28%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 22.60; 157% do lucro antes de custos.
- Trades < 3 h: 2 (lucro -26.56); reentradas em < 24 h: 3 (lucro -39.86).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -54.29.
- Lucro por ano de fechamento: 2023: -10.7, 2024: 2.5.

## ATOM/USDT

Trades: 137; lucro líquido: -125.89.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 97 | 367.17 | – | 1.66% | 59% | 11.3 h |
| stop_loss | 40 | -493.06 | – | -5.28% | 0% | 5.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 13 | -160.83 | -5.28% | 0% |
| 3 h a 1 dia | 124 | 34.94 | 0.15% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (57): MFE mediano 5.7%, MAE mediano -1.3%, devolução média do melhor ponto 3.6%, captura mediana 0.47.
- Perdedores (80): MAE mediano -5.0%, MFE mediano 1.6%; 33 (41%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 96.38; – do lucro antes de custos.
- Trades < 3 h: 13 (lucro -160.83); reentradas em < 24 h: 17 (lucro -107.44).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -179.13.
- Lucro por ano de fechamento: 2019: 5.4, 2020: -74.0, 2021: -3.7, 2022: -0.2, 2023: -29.9, 2024: -23.6.

## ETC/USDT

Trades: 177; lucro líquido: -62.96.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 131 | 542.46 | – | 1.70% | 53% | 12.5 h |
| stop_loss | 46 | -605.42 | – | -5.28% | 0% | 5.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 14 | -186.50 | -5.28% | 0% |
| 3 h a 1 dia | 163 | 123.54 | 0.33% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (69): MFE mediano 4.6%, MAE mediano -1.3%, devolução média do melhor ponto 4.5%, captura mediana 0.48.
- Perdedores (108): MAE mediano -4.6%, MFE mediano 1.5%; 40 (37%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 131.21; 192% do lucro antes de custos.
- Trades < 3 h: 14 (lucro -186.50); reentradas em < 24 h: 29 (lucro 63.44).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -120.68.
- Lucro por ano de fechamento: 2018: -13.2, 2019: -30.9, 2020: -18.5, 2021: 160.3, 2022: -66.2, 2023: -72.4, 2024: -22.0.
