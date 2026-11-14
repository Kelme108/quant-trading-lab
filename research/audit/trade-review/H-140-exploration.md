# Revisão de trades: H-140 (exploração)

Fonte dos trades: `research/experiments/20261114T080357Z-h-140-exploration-btc-usdt/raw/backtest-result-2026-11-14_08-18-00.zip`; `research/experiments/20261114T080357Z-h-140-exploration-eth-usdt/raw/backtest-result-2026-11-14_08-18-01.zip`; `research/experiments/20261114T080357Z-h-140-exploration-bnb-usdt/raw/backtest-result-2026-11-14_08-18-01.zip`; `research/experiments/20261114T080357Z-h-140-exploration-xrp-usdt/raw/backtest-result-2026-11-14_08-25-48.zip`; `research/experiments/20261114T080357Z-h-140-exploration-ada-usdt/raw/backtest-result-2026-11-14_08-25-48.zip`; `research/experiments/20261114T080357Z-h-140-exploration-ltc-usdt/raw/backtest-result-2026-11-14_08-26-03.zip`; `research/experiments/20261114T080357Z-h-140-exploration-link-usdt/raw/backtest-result-2026-11-14_08-33-47.zip`; `research/experiments/20261114T080357Z-h-140-exploration-doge-usdt/raw/backtest-result-2026-11-14_08-33-48.zip`; `research/experiments/20261114T080357Z-h-140-exploration-sol-usdt/raw/backtest-result-2026-11-14_08-33-42.zip`; `research/experiments/20261114T080357Z-h-140-exploration-avax-usdt/raw/backtest-result-2026-11-14_08-40-31.zip`; `research/experiments/20261114T080357Z-h-140-exploration-dot-usdt/raw/backtest-result-2026-11-14_08-41-30.zip`; `research/experiments/20261114T080357Z-h-140-exploration-trx-usdt/raw/backtest-result-2026-11-14_08-42-01.zip`; `research/experiments/20261114T080357Z-h-140-exploration-near-usdt/raw/backtest-result-2026-11-14_08-47-42.zip`; `research/experiments/20261114T080357Z-h-140-exploration-uni-usdt/raw/backtest-result-2026-11-14_08-48-49.zip`; `research/experiments/20261114T080357Z-h-140-exploration-bch-usdt/raw/backtest-result-2026-11-14_08-50-12.zip`; `research/experiments/20261114T080357Z-h-140-exploration-xlm-usdt/raw/backtest-result-2026-11-14_08-55-22.zip`; `research/experiments/20261114T080357Z-h-140-exploration-fil-usdt/raw/backtest-result-2026-11-14_08-56-10.zip`; `research/experiments/20261114T080357Z-h-140-exploration-aave-usdt/raw/backtest-result-2026-11-14_08-58-10.zip`; `research/experiments/20261114T080357Z-h-140-exploration-inj-usdt/raw/backtest-result-2026-11-14_09-04-04.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 151; lucro líquido: 162.34.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 124 | 356.53 | 220% | 0.88% | 55% | 12.0 h |
| stop_loss | 17 | -191.75 | -118% | -3.34% | 0% | 6.1 h |
| day_end_exit | 9 | 17.01 | 10% | 0.61% | 67% | 12.0 h |
| trailing_stop_loss | 1 | -19.46 | -12% | -6.48% | 0% | 10.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 4 | -38.13 | -2.81% | 0% |
| 3 h a 1 dia | 147 | 200.46 | 0.43% | 50% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (74): MFE mediano 3.3%, MAE mediano -0.7%, devolução média do melhor ponto 1.5%, captura mediana 0.58.
- Perdedores (77): MAE mediano -1.7%, MFE mediano 0.6%; 6 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 153.64; 49% do lucro antes de custos.
- Trades < 3 h: 4 (lucro -38.13); reentradas em < 24 h: 1 (lucro 4.79).
- Maior trade = 17% do lucro; top 5 = 70%; top 10 = 126%; lucro sem o melhor = 134.80.
- Lucro por ano de fechamento: 2017: 68.2, 2018: 46.5, 2019: 13.9, 2020: 9.6, 2021: -18.1, 2022: 68.1, 2023: -13.8, 2024: -12.0.

## ETH/USDT

Trades: 158; lucro líquido: 174.63.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 128 | 385.23 | 221% | 0.92% | 54% | 12.0 h |
| stop_loss | 19 | -264.05 | -151% | -4.09% | 0% | 6.9 h |
| day_end_exit | 11 | 53.44 | 31% | 1.43% | 64% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 2 | -21.56 | -3.42% | 0% |
| 3 h a 1 dia | 156 | 196.18 | 0.40% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (76): MFE mediano 3.7%, MAE mediano -0.6%, devolução média do melhor ponto 1.8%, captura mediana 0.60.
- Perdedores (82): MAE mediano -2.0%, MFE mediano 0.8%; 9 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 159.81; 48% do lucro antes de custos.
- Trades < 3 h: 2 (lucro -21.56); reentradas em < 24 h: 3 (lucro 23.54).
- Maior trade = 21% do lucro; top 5 = 87%; top 10 = 142%; lucro sem o melhor = 137.78.
- Lucro por ano de fechamento: 2017: -2.2, 2018: 74.1, 2019: -2.7, 2020: 73.1, 2021: 47.8, 2022: 11.1, 2023: -30.0, 2024: 3.4.

## BNB/USDT

Trades: 168; lucro líquido: 193.02.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 128 | 369.22 | 191% | 0.84% | 55% | 12.0 h |
| stop_loss | 21 | -276.27 | -143% | -3.74% | 0% | 7.0 h |
| day_end_exit | 19 | 100.06 | 52% | 1.72% | 58% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 1 | -9.23 | -2.80% | 0% |
| 3 h a 1 dia | 167 | 202.25 | 0.39% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (81): MFE mediano 3.7%, MAE mediano -0.7%, devolução média do melhor ponto 2.4%, captura mediana 0.50.
- Perdedores (87): MAE mediano -2.6%, MFE mediano 0.7%; 6 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 175.07; 48% do lucro antes de custos.
- Trades < 3 h: 1 (lucro -9.23); reentradas em < 24 h: 9 (lucro -2.41).
- Maior trade = 46% do lucro; top 5 = 123%; top 10 = 189%; lucro sem o melhor = 103.89.
- Lucro por ano de fechamento: 2017: 4.0, 2018: 49.2, 2019: 70.3, 2020: -9.8, 2021: 161.2, 2022: -59.1, 2023: -31.8, 2024: 9.0.

## XRP/USDT

Trades: 133; lucro líquido: -19.38.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 105 | 303.64 | – | 0.97% | 46% | 12.0 h |
| stop_loss | 23 | -319.14 | – | -4.50% | 0% | 6.8 h |
| day_end_exit | 5 | -3.89 | – | -0.26% | 40% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 3 | -57.83 | -6.29% | 0% |
| 3 h a 1 dia | 130 | 38.45 | 0.12% | 38% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (50): MFE mediano 4.7%, MAE mediano -0.9%, devolução média do melhor ponto 2.4%, captura mediana 0.54.
- Perdedores (83): MAE mediano -2.7%, MFE mediano 1.0%; 22 (27%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 123.47; 119% do lucro antes de custos.
- Trades < 3 h: 3 (lucro -57.83); reentradas em < 24 h: 3 (lucro 19.55).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -80.44.
- Lucro por ano de fechamento: 2018: 17.1, 2019: 30.3, 2020: -24.3, 2021: 102.3, 2022: -52.9, 2023: -93.7, 2024: 1.8.

## ADA/USDT

Trades: 130; lucro líquido: 89.43.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 103 | 260.61 | 291% | 0.77% | 54% | 12.0 h |
| stop_loss | 15 | -217.57 | -243% | -4.24% | 0% | 7.1 h |
| day_end_exit | 12 | 46.39 | 52% | 1.35% | 50% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 2 | -41.75 | -6.14% | 0% |
| 3 h a 1 dia | 128 | 131.17 | 0.34% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (62): MFE mediano 4.9%, MAE mediano -0.7%, devolução média do melhor ponto 2.4%, captura mediana 0.57.
- Perdedores (68): MAE mediano -2.8%, MFE mediano 0.8%; 10 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 130.93; 59% do lucro antes de custos.
- Trades < 3 h: 2 (lucro -41.75); reentradas em < 24 h: 3 (lucro -9.22).
- Maior trade = 58% do lucro; top 5 = 227%; top 10 = 339%; lucro sem o melhor = 37.13.
- Lucro por ano de fechamento: 2018: 2.4, 2019: 29.0, 2020: 164.6, 2021: 15.5, 2022: -52.9, 2023: -34.8, 2024: -34.3.

## LTC/USDT

Trades: 157; lucro líquido: 18.93.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 130 | 328.42 | 1735% | 0.78% | 45% | 12.0 h |
| stop_loss | 19 | -328.18 | -1734% | -5.10% | 0% | 7.3 h |
| day_end_exit | 8 | 18.70 | 99% | 0.72% | 75% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 1 | -6.86 | -1.91% | 0% |
| 3 h a 1 dia | 156 | 25.79 | 0.08% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (65): MFE mediano 4.0%, MAE mediano -0.7%, devolução média do melhor ponto 1.9%, captura mediana 0.59.
- Perdedores (92): MAE mediano -3.2%, MFE mediano 0.9%; 17 (18%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 153.70; 89% do lucro antes de custos.
- Trades < 3 h: 1 (lucro -6.86); reentradas em < 24 h: 3 (lucro 10.70).
- Maior trade = 470% do lucro; top 5 = 1366%; top 10 = 1940%; lucro sem o melhor = -69.96.
- Lucro por ano de fechamento: 2018: 70.4, 2019: 54.0, 2020: 6.0, 2021: -61.1, 2022: -22.7, 2023: -20.2, 2024: -7.4.

## LINK/USDT

Trades: 131; lucro líquido: 85.33.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 106 | 303.82 | 356% | 0.86% | 52% | 12.0 h |
| stop_loss | 15 | -280.37 | -329% | -5.13% | 0% | 7.4 h |
| day_end_exit | 10 | 61.88 | 73% | 1.72% | 80% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 0 | 0.00 | – | – |
| 3 h a 1 dia | 131 | 85.33 | 0.24% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (63): MFE mediano 4.5%, MAE mediano -0.8%, devolução média do melhor ponto 2.8%, captura mediana 0.50.
- Perdedores (68): MAE mediano -3.3%, MFE mediano 1.2%; 18 (26%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 138.78; 62% do lucro antes de custos.
- Trades < 3 h: 0 (lucro 0.00); reentradas em < 24 h: 3 (lucro -4.97).
- Maior trade = 103% do lucro; top 5 = 302%; top 10 = 480%; lucro sem o melhor = -2.50.
- Lucro por ano de fechamento: 2019: 162.7, 2020: 94.1, 2021: -48.2, 2022: -62.1, 2023: -28.6, 2024: -32.6.

## DOGE/USDT

Trades: 125; lucro líquido: -351.10.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 93 | 71.70 | – | 0.26% | 42% | 12.0 h |
| stop_loss | 27 | -407.00 | – | -5.92% | 0% | 6.8 h |
| day_end_exit | 5 | -15.81 | – | -1.13% | 20% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 3 | -58.46 | -7.01% | 0% |
| 3 h a 1 dia | 122 | -292.64 | -0.98% | 33% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (40): MFE mediano 4.9%, MAE mediano -1.0%, devolução média do melhor ponto 3.1%, captura mediana 0.44.
- Perdedores (85): MAE mediano -3.7%, MFE mediano 0.9%; 16 (19%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 95.66; – do lucro antes de custos.
- Trades < 3 h: 3 (lucro -58.46); reentradas em < 24 h: 4 (lucro -33.92).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -387.31.
- Lucro por ano de fechamento: 2019: 10.7, 2020: -8.2, 2021: -161.5, 2022: -54.9, 2023: -47.5, 2024: -89.6.

## SOL/USDT

Trades: 95; lucro líquido: 76.82.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 84 | 233.96 | 305% | 0.92% | 51% | 12.0 h |
| stop_loss | 6 | -131.71 | -171% | -7.00% | 0% | 7.6 h |
| day_end_exit | 5 | -25.42 | -33% | -1.56% | 40% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 1 | -11.34 | -3.47% | 0% |
| 3 h a 1 dia | 94 | 88.16 | 0.33% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (45): MFE mediano 5.1%, MAE mediano -1.7%, devolução média do melhor ponto 2.6%, captura mediana 0.53.
- Perdedores (50): MAE mediano -3.5%, MFE mediano 1.3%; 15 (30%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 89.79; 54% do lucro antes de custos.
- Trades < 3 h: 1 (lucro -11.34); reentradas em < 24 h: 4 (lucro -28.70).
- Maior trade = 45% do lucro; top 5 = 200%; top 10 = 341%; lucro sem o melhor = 42.35.
- Lucro por ano de fechamento: 2020: -10.2, 2021: 106.3, 2022: -63.6, 2023: 68.5, 2024: -24.2.

## AVAX/USDT

Trades: 98; lucro líquido: 91.79.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 82 | 381.35 | 415% | 1.53% | 52% | 12.0 h |
| stop_loss | 13 | -278.27 | -303% | -6.69% | 0% | 7.5 h |
| day_end_exit | 3 | -11.28 | -12% | -1.21% | 33% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 1 | -27.21 | -8.67% | 0% |
| 3 h a 1 dia | 97 | 119.01 | 0.45% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (44): MFE mediano 5.3%, MAE mediano -1.0%, devolução média do melhor ponto 3.3%, captura mediana 0.59.
- Perdedores (54): MAE mediano -3.9%, MFE mediano 1.7%; 23 (43%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 92.60; 50% do lucro antes de custos.
- Trades < 3 h: 1 (lucro -27.21); reentradas em < 24 h: 6 (lucro 48.80).
- Maior trade = 106% do lucro; top 5 = 308%; top 10 = 447%; lucro sem o melhor = -5.21.
- Lucro por ano de fechamento: 2020: -4.7, 2021: 7.1, 2022: 37.8, 2023: 97.6, 2024: -46.0.

## DOT/USDT

Trades: 82; lucro líquido: -77.43.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 59 | 73.73 | – | 0.41% | 51% | 12.0 h |
| stop_loss | 13 | -199.70 | – | -5.06% | 0% | 8.5 h |
| day_end_exit | 10 | 48.53 | – | 1.65% | 40% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 0 | 0.00 | – | – |
| 3 h a 1 dia | 82 | -77.43 | -0.30% | 41% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (34): MFE mediano 3.6%, MAE mediano -1.1%, devolução média do melhor ponto 2.0%, captura mediana 0.51.
- Perdedores (48): MAE mediano -3.0%, MFE mediano 1.1%; 11 (23%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 74.32; – do lucro antes de custos.
- Trades < 3 h: 0 (lucro 0.00); reentradas em < 24 h: 2 (lucro -3.62).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -131.40.
- Lucro por ano de fechamento: 2020: 0.3, 2021: 88.8, 2022: -84.9, 2023: -72.5, 2024: -9.1.

## TRX/USDT

Trades: 187; lucro líquido: 93.22.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 152 | 306.22 | 328% | 0.64% | 49% | 12.0 h |
| stop_loss | 18 | -238.37 | -256% | -3.96% | 0% | 8.0 h |
| day_end_exit | 17 | 25.37 | 27% | 0.45% | 47% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 1 | -9.28 | -2.72% | 0% |
| 3 h a 1 dia | 186 | 102.50 | 0.19% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (83): MFE mediano 3.6%, MAE mediano -0.6%, devolução média do melhor ponto 2.2%, captura mediana 0.46.
- Perdedores (104): MAE mediano -2.0%, MFE mediano 0.6%; 6 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 183.36; 66% do lucro antes de custos.
- Trades < 3 h: 1 (lucro -9.28); reentradas em < 24 h: 9 (lucro 44.04).
- Maior trade = 56% do lucro; top 5 = 230%; top 10 = 352%; lucro sem o melhor = 41.12.
- Lucro por ano de fechamento: 2018: 31.6, 2019: 20.6, 2020: 10.8, 2021: 86.1, 2022: -24.8, 2023: -28.2, 2024: -2.9.

## NEAR/USDT

Trades: 98; lucro líquido: -103.51.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 72 | 277.36 | – | 1.42% | 49% | 12.0 h |
| stop_loss | 18 | -380.96 | – | -7.44% | 0% | 7.7 h |
| day_end_exit | 8 | 0.09 | – | -0.05% | 38% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 2 | -54.04 | -9.54% | 0% |
| 3 h a 1 dia | 96 | -49.47 | -0.13% | 40% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (38): MFE mediano 7.0%, MAE mediano -1.9%, devolução média do melhor ponto 4.4%, captura mediana 0.55.
- Perdedores (60): MAE mediano -4.0%, MFE mediano 1.8%; 28 (47%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 80.98; – do lucro antes de custos.
- Trades < 3 h: 2 (lucro -54.04); reentradas em < 24 h: 3 (lucro -17.25).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -167.28.
- Lucro por ano de fechamento: 2020: 28.5, 2021: -59.4, 2022: -91.7, 2023: -14.6, 2024: 33.6.

## UNI/USDT

Trades: 90; lucro líquido: -143.29.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 66 | 121.37 | – | 0.64% | 53% | 12.0 h |
| stop_loss | 17 | -290.88 | – | -5.89% | 0% | 8.0 h |
| day_end_exit | 7 | 26.22 | – | 1.26% | 71% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 1 | -19.90 | -6.69% | 0% |
| 3 h a 1 dia | 89 | -123.40 | -0.48% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (40): MFE mediano 4.9%, MAE mediano -1.5%, devolução média do melhor ponto 2.7%, captura mediana 0.41.
- Perdedores (50): MAE mediano -3.2%, MFE mediano 1.2%; 12 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 76.18; – do lucro antes de custos.
- Trades < 3 h: 1 (lucro -19.90); reentradas em < 24 h: 3 (lucro -31.82).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -202.70.
- Lucro por ano de fechamento: 2020: 17.0, 2021: -74.6, 2022: -39.5, 2023: -42.1, 2024: -4.2.

## BCH/USDT

Trades: 108; lucro líquido: -134.31.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 84 | 108.35 | – | 0.50% | 46% | 12.0 h |
| stop_loss | 17 | -231.69 | – | -4.88% | 0% | 7.3 h |
| day_end_exit | 7 | -10.97 | – | -0.53% | 29% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 2 | -27.55 | -4.63% | 0% |
| 3 h a 1 dia | 106 | -106.76 | -0.34% | 39% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (41): MFE mediano 4.3%, MAE mediano -0.5%, devolução média do melhor ponto 2.1%, captura mediana 0.57.
- Perdedores (67): MAE mediano -2.9%, MFE mediano 0.8%; 9 (13%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 88.20; – do lucro antes de custos.
- Trades < 3 h: 2 (lucro -27.55); reentradas em < 24 h: 3 (lucro 5.99).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -207.81.
- Lucro por ano de fechamento: 2020: -60.5, 2021: -1.3, 2022: -81.9, 2023: -47.4, 2024: 56.8.

## XLM/USDT

Trades: 157; lucro líquido: -210.73.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 121 | 19.97 | – | 0.07% | 44% | 12.0 h |
| stop_loss | 21 | -247.39 | – | -4.32% | 0% | 6.6 h |
| day_end_exit | 15 | 16.69 | – | 0.42% | 73% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 2 | -19.11 | -3.76% | 0% |
| 3 h a 1 dia | 155 | -191.63 | -0.44% | 41% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (64): MFE mediano 3.9%, MAE mediano -1.0%, devolução média do melhor ponto 2.2%, captura mediana 0.52.
- Perdedores (93): MAE mediano -3.0%, MFE mediano 0.8%; 19 (20%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 128.54; – do lucro antes de custos.
- Trades < 3 h: 2 (lucro -19.11); reentradas em < 24 h: 7 (lucro -29.95).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -234.03.
- Lucro por ano de fechamento: 2018: -17.4, 2019: -50.4, 2020: 41.3, 2021: -83.0, 2022: -29.9, 2023: -45.5, 2024: -25.8.

## FIL/USDT

Trades: 79; lucro líquido: 75.69.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 71 | 183.88 | 243% | 0.87% | 46% | 12.0 h |
| stop_loss | 6 | -113.14 | -149% | -5.99% | 0% | 6.2 h |
| day_end_exit | 2 | 4.95 | 7% | 0.84% | 50% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 1 | -19.33 | -6.27% | 0% |
| 3 h a 1 dia | 78 | 95.02 | 0.43% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (34): MFE mediano 4.9%, MAE mediano -0.8%, devolução média do melhor ponto 2.9%, captura mediana 0.47.
- Perdedores (45): MAE mediano -2.4%, MFE mediano 1.4%; 12 (27%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 73.24; 49% do lucro antes de custos.
- Trades < 3 h: 1 (lucro -19.33); reentradas em < 24 h: 1 (lucro -4.33).
- Maior trade = 106% do lucro; top 5 = 296%; top 10 = 401%; lucro sem o melhor = -4.51.
- Lucro por ano de fechamento: 2020: -10.3, 2021: 63.9, 2022: -12.9, 2023: 23.2, 2024: 11.8.

## AAVE/USDT

Trades: 84; lucro líquido: 223.13.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 74 | 348.91 | 156% | 1.43% | 55% | 12.0 h |
| stop_loss | 7 | -141.97 | -64% | -5.80% | 0% | 7.7 h |
| day_end_exit | 3 | 16.19 | 7% | 1.41% | 33% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 0 | 0.00 | – | – |
| 3 h a 1 dia | 84 | 223.13 | 0.83% | 50% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (42): MFE mediano 4.7%, MAE mediano -1.1%, devolução média do melhor ponto 2.4%, captura mediana 0.65.
- Perdedores (42): MAE mediano -3.5%, MFE mediano 1.3%; 15 (36%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 91.17; 29% do lucro antes de custos.
- Trades < 3 h: 0 (lucro 0.00); reentradas em < 24 h: 2 (lucro 18.22).
- Maior trade = 30% do lucro; top 5 = 88%; top 10 = 144%; lucro sem o melhor = 155.87.
- Lucro por ano de fechamento: 2020: 89.7, 2021: 137.3, 2022: -17.0, 2023: 39.6, 2024: -26.5.

## INJ/USDT

Trades: 100; lucro líquido: -241.98.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12h | 71 | 80.53 | – | 0.37% | 46% | 12.0 h |
| stop_loss | 19 | -377.32 | – | -7.05% | 0% | 7.6 h |
| day_end_exit | 10 | 54.81 | – | 1.95% | 70% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 1 | -17.80 | -7.05% | 0% |
| 3 h a 1 dia | 99 | -224.18 | -0.82% | 40% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (40): MFE mediano 7.1%, MAE mediano -2.0%, devolução média do melhor ponto 4.0%, captura mediana 0.47.
- Perdedores (60): MAE mediano -5.0%, MFE mediano 1.1%; 21 (35%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 82.36; – do lucro antes de custos.
- Trades < 3 h: 1 (lucro -17.80); reentradas em < 24 h: 7 (lucro -55.16).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -297.83.
- Lucro por ano de fechamento: 2020: 109.1, 2021: -128.8, 2022: -128.1, 2023: -76.4, 2024: -17.9.
