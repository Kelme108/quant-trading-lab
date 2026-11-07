# Revisão de trades: H-078 (exploração)

Fonte dos trades: `research/experiments/20261107T225104Z-h-078-exploration-btc-usdt/raw/backtest-result-2026-11-07_22-55-46.zip`; `research/experiments/20261107T225104Z-h-078-exploration-eth-usdt/raw/backtest-result-2026-11-07_22-57-59.zip`; `research/experiments/20261107T225104Z-h-078-exploration-bnb-usdt/raw/backtest-result-2026-11-07_23-00-51.zip`; `research/experiments/20261107T225104Z-h-078-exploration-xrp-usdt/raw/backtest-result-2026-11-07_23-03-32.zip`; `research/experiments/20261107T225104Z-h-078-exploration-ada-usdt/raw/backtest-result-2026-11-07_23-06-07.zip`; `research/experiments/20261107T225104Z-h-078-exploration-ltc-usdt/raw/backtest-result-2026-11-07_23-08-31.zip`; `research/experiments/20261107T225104Z-h-078-exploration-link-usdt/raw/backtest-result-2026-11-07_23-11-09.zip`; `research/experiments/20261107T225104Z-h-078-exploration-doge-usdt/raw/backtest-result-2026-11-07_23-13-41.zip`; `research/experiments/20261107T225104Z-h-078-exploration-sol-usdt/raw/backtest-result-2026-11-07_23-16-18.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 10; lucro líquido: -0.06.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| target_pre_drop | 4 | 1.37 | – | 3.45% | 100% | 3.5 h |
| time_12h | 3 | -0.15 | – | -0.50% | 33% | 12.0 h |
| stop_loss | 3 | -1.28 | – | -4.29% | 0% | 5.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 3 | 0.22 | 0.72% | 67% |
| 3 h a 1 dia | 7 | -0.27 | -0.39% | 43% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (5): MFE mediano 4.3%, MAE mediano -0.4%, devolução média do melhor ponto 1.2%, captura mediana 0.71.
- Perdedores (5): MAE mediano -4.2%, MFE mediano 1.1%; 2 (40%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 0.30; 123% do lucro antes de custos.
- Trades < 3 h: 3 (lucro 0.22); reentradas em < 24 h: 2 (lucro 0.64).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -0.46.
- Lucro por ano de fechamento: 2019: 0.3, 2021: -0.4.

## ETH/USDT

Trades: 22; lucro líquido: 1.07.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12h | 10 | 0.48 | 45% | 0.48% | 70% | 12.0 h |
| target_pre_drop | 8 | 2.31 | 215% | 2.91% | 100% | 5.9 h |
| stop_loss | 4 | -1.71 | -160% | -4.29% | 0% | 2.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 2 | -0.86 | -4.29% | 0% |
| 3 h a 1 dia | 20 | 1.93 | 0.97% | 75% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (15): MFE mediano 3.5%, MAE mediano -1.2%, devolução média do melhor ponto 1.6%, captura mediana 0.60.
- Perdedores (7): MAE mediano -4.4%, MFE mediano 1.8%; 3 (43%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 0.66; 38% do lucro antes de custos.
- Trades < 3 h: 2 (lucro -0.86); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = 47% do lucro; top 5 = 157%; top 10 = 253%; lucro sem o melhor = 0.57.
- Lucro por ano de fechamento: 2018: 0.1, 2019: -0.1, 2020: 0.2, 2021: 1.3, 2022: -0.3.

## BNB/USDT

Trades: 126; lucro líquido: 9.68.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12h | 55 | 0.09 | 1% | 0.01% | 51% | 12.0 h |
| target_pre_drop | 48 | 19.80 | 204% | 3.99% | 100% | 6.2 h |
| stop_loss | 23 | -10.20 | -105% | -4.29% | 0% | 4.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 15 | -3.11 | -2.03% | 27% |
| 3 h a 1 dia | 111 | 12.79 | 1.11% | 65% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (76): MFE mediano 4.2%, MAE mediano -1.2%, devolução média do melhor ponto 2.0%, captura mediana 0.66.
- Perdedores (50): MAE mediano -3.7%, MFE mediano 1.3%; 12 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 3.92; 29% do lucro antes de custos.
- Trades < 3 h: 15 (lucro -3.11); reentradas em < 24 h: 20 (lucro -0.56).
- Maior trade = 11% do lucro; top 5 = 42%; top 10 = 70%; lucro sem o melhor = 8.63.
- Lucro por ano de fechamento: 2018: -0.4, 2019: 3.4, 2020: 3.1, 2021: 3.5, 2022: -0.3, 2024: 0.5.

## XRP/USDT

Trades: 117; lucro líquido: -4.21.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 43 | -18.02 | – | -4.28% | 0% | 3.5 h |
| time_12h | 39 | -0.10 | – | -0.02% | 51% | 12.0 h |
| target_pre_drop | 35 | 13.91 | – | 4.08% | 100% | 6.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 24 | -5.94 | -2.53% | 25% |
| 3 h a 1 dia | 93 | 1.73 | 0.20% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (55): MFE mediano 4.1%, MAE mediano -1.0%, devolução média do melhor ponto 2.6%, captura mediana 0.54.
- Perdedores (62): MAE mediano -4.9%, MFE mediano 1.4%; 20 (32%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 3.41; – do lucro antes de custos.
- Trades < 3 h: 24 (lucro -5.94); reentradas em < 24 h: 36 (lucro -0.04).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -5.15.
- Lucro por ano de fechamento: 2018: -0.7, 2019: -0.1, 2020: 0.6, 2021: -4.0, 2022: 0.3, 2023: -0.2.

## ADA/USDT

Trades: 153; lucro líquido: -9.42.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12h | 59 | -1.28 | – | -0.22% | 42% | 12.0 h |
| stop_loss | 54 | -21.54 | – | -4.28% | 0% | 4.5 h |
| target_pre_drop | 40 | 13.39 | – | 3.65% | 100% | 6.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 20 | -2.71 | -1.40% | 35% |
| 3 h a 1 dia | 133 | -6.71 | -0.53% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (65): MFE mediano 4.0%, MAE mediano -1.0%, devolução média do melhor ponto 1.8%, captura mediana 0.61.
- Perdedores (88): MAE mediano -4.2%, MFE mediano 1.1%; 21 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 4.23; – do lucro antes de custos.
- Trades < 3 h: 20 (lucro -2.71); reentradas em < 24 h: 26 (lucro 0.02).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -10.34.
- Lucro por ano de fechamento: 2018: -5.1, 2019: -2.9, 2020: -1.1, 2021: 0.2, 2022: 0.6, 2023: -0.3, 2024: -0.8.

## LTC/USDT

Trades: 77; lucro líquido: -1.35.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| target_pre_drop | 27 | 8.77 | – | 3.30% | 100% | 6.8 h |
| time_12h | 27 | -0.38 | – | -0.15% | 44% | 12.0 h |
| stop_loss | 23 | -9.73 | – | -4.28% | 0% | 4.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 13 | -1.23 | -0.94% | 38% |
| 3 h a 1 dia | 64 | -0.11 | -0.01% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (39): MFE mediano 3.6%, MAE mediano -1.0%, devolução média do melhor ponto 1.6%, captura mediana 0.67.
- Perdedores (38): MAE mediano -4.1%, MFE mediano 1.9%; 16 (42%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 2.27; 246% do lucro antes de custos.
- Trades < 3 h: 13 (lucro -1.23); reentradas em < 24 h: 5 (lucro -0.39).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -1.92.
- Lucro por ano de fechamento: 2018: 0.3, 2019: -0.7, 2020: 0.2, 2021: -2.4, 2022: 0.8, 2023: 0.2, 2024: 0.3.

## LINK/USDT

Trades: 372; lucro líquido: -12.22.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12h | 148 | -5.38 | – | -0.38% | 37% | 12.0 h |
| stop_loss | 116 | -48.97 | – | -4.28% | 0% | 4.6 h |
| target_pre_drop | 108 | 42.13 | – | 3.92% | 100% | 5.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 59 | -8.56 | -1.47% | 32% |
| 3 h a 1 dia | 313 | -3.66 | -0.14% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (163): MFE mediano 4.6%, MAE mediano -1.1%, devolução média do melhor ponto 2.1%, captura mediana 0.59.
- Perdedores (209): MAE mediano -4.3%, MFE mediano 1.3%; 59 (28%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 10.95; – do lucro antes de custos.
- Trades < 3 h: 59 (lucro -8.56); reentradas em < 24 h: 145 (lucro -2.58).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -13.56.
- Lucro por ano de fechamento: 2019: 2.2, 2020: -1.8, 2021: -7.5, 2022: -2.9, 2023: -0.7, 2024: -1.4.

## DOGE/USDT

Trades: 180; lucro líquido: -2.33.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 69 | -29.24 | – | -4.29% | 0% | 3.6 h |
| target_pre_drop | 58 | 28.96 | – | 5.07% | 100% | 5.6 h |
| time_12h | 53 | -2.05 | – | -0.39% | 43% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 47 | -11.12 | -2.41% | 23% |
| 3 h a 1 dia | 133 | 8.79 | 0.68% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (81): MFE mediano 5.1%, MAE mediano -1.1%, devolução média do melhor ponto 2.8%, captura mediana 0.61.
- Perdedores (99): MAE mediano -4.6%, MFE mediano 1.4%; 34 (34%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 5.32; 178% do lucro antes de custos.
- Trades < 3 h: 47 (lucro -11.12); reentradas em < 24 h: 68 (lucro -2.06).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -4.93.
- Lucro por ano de fechamento: 2019: 0.2, 2020: -0.2, 2021: -2.2, 2022: 1.1, 2023: 0.1, 2024: -1.4.

## SOL/USDT

Trades: 458; lucro líquido: -18.91.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 175 | -64.62 | – | -4.28% | 0% | 4.5 h |
| time_12h | 146 | 0.54 | – | 0.05% | 53% | 12.0 h |
| target_pre_drop | 137 | 45.18 | – | 3.91% | 100% | 5.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 78 | -14.43 | -2.12% | 26% |
| 3 h a 1 dia | 380 | -4.48 | -0.11% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (215): MFE mediano 4.3%, MAE mediano -1.2%, devolução média do melhor ponto 2.1%, captura mediana 0.62.
- Perdedores (243): MAE mediano -4.5%, MFE mediano 1.2%; 63 (26%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 11.56; – do lucro antes de custos.
- Trades < 3 h: 78 (lucro -14.43); reentradas em < 24 h: 225 (lucro -9.72).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -19.97.
- Lucro por ano de fechamento: 2020: -13.4, 2021: -6.2, 2022: -0.7, 2023: 1.3, 2024: 0.1.
