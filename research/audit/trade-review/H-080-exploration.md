# Revisão de trades: H-080 (exploração)

Fonte dos trades: `research/experiments/20261107T235513Z-h-080-exploration-btc-usdt/raw/backtest-result-2026-11-08_00-03-15.zip`; `research/experiments/20261107T235513Z-h-080-exploration-eth-usdt/raw/backtest-result-2026-11-08_00-07-02.zip`; `research/experiments/20261107T235513Z-h-080-exploration-bnb-usdt/raw/backtest-result-2026-11-08_00-10-30.zip`; `research/experiments/20261107T235513Z-h-080-exploration-xrp-usdt/raw/backtest-result-2026-11-08_00-14-22.zip`; `research/experiments/20261107T235513Z-h-080-exploration-ada-usdt/raw/backtest-result-2026-11-08_00-18-00.zip`; `research/experiments/20261107T235513Z-h-080-exploration-ltc-usdt/raw/backtest-result-2026-11-08_00-21-40.zip`; `research/experiments/20261107T235513Z-h-080-exploration-link-usdt/raw/backtest-result-2026-11-08_00-25-17.zip`; `research/experiments/20261107T235513Z-h-080-exploration-doge-usdt/raw/backtest-result-2026-11-08_00-28-23.zip`; `research/experiments/20261107T235513Z-h-080-exploration-sol-usdt/raw/backtest-result-2026-11-08_00-31-20.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 541; lucro líquido: -23.71.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_16 | 355 | -23.73 | – | -0.39% | 27% | 4.0 h |
| catchup_target | 132 | 28.34 | – | 1.22% | 100% | 1.6 h |
| stop_loss | 37 | -21.99 | – | -3.29% | 0% | 1.4 h |
| catchup_fail_level | 17 | -6.34 | – | -2.19% | 0% | 2.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 145 | 0.99 | 0.05% | 72% |
| 3 h a 1 dia | 396 | -24.70 | -0.36% | 31% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (227): MFE mediano 1.5%, MAE mediano -0.3%, devolução média do melhor ponto 0.9%, captura mediana 0.45.
- Perdedores (314): MAE mediano -1.0%, MFE mediano 0.4%; 4 (1%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 28.31; 616% do lucro antes de custos.
- Trades < 3 h: 145 (lucro 0.99); reentradas em < 24 h: 207 (lucro -10.41).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -24.86.
- Lucro por ano de fechamento: 2017: -3.8, 2018: -4.4, 2019: -2.1, 2020: -1.2, 2021: -7.4, 2022: -0.6, 2023: -1.9, 2024: -2.3.

## ETH/USDT

Trades: 196; lucro líquido: -3.17.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| catchup_target | 87 | 21.88 | – | 1.28% | 100% | 1.5 h |
| time_exit_16 | 74 | -6.82 | – | -0.47% | 14% | 4.0 h |
| stop_loss | 19 | -12.36 | – | -3.29% | 0% | 1.1 h |
| catchup_fail_level | 16 | -5.88 | – | -1.86% | 0% | 1.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 98 | 4.90 | 0.26% | 73% |
| 3 h a 1 dia | 98 | -8.07 | -0.42% | 26% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (97): MFE mediano 1.9%, MAE mediano -0.4%, devolução média do melhor ponto 1.1%, captura mediana 0.50.
- Perdedores (99): MAE mediano -1.5%, MFE mediano 0.5%; 2 (2%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 11.51; 138% do lucro antes de custos.
- Trades < 3 h: 98 (lucro 4.90); reentradas em < 24 h: 50 (lucro 2.43).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -4.22.
- Lucro por ano de fechamento: 2017: 1.6, 2018: -1.3, 2019: -0.7, 2020: -3.0, 2021: -1.9, 2022: 0.9, 2023: 0.9, 2024: 0.3.

## BNB/USDT

Trades: 396; lucro líquido: -13.06.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_16 | 186 | -16.31 | – | -0.47% | 20% | 4.0 h |
| catchup_target | 144 | 33.59 | – | 1.24% | 100% | 1.7 h |
| catchup_fail_level | 41 | -14.56 | – | -1.89% | 0% | 1.8 h |
| stop_loss | 25 | -15.78 | – | -3.29% | 0% | 1.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 167 | -0.91 | -0.02% | 67% |
| 3 h a 1 dia | 229 | -12.15 | -0.29% | 30% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (181): MFE mediano 1.7%, MAE mediano -0.4%, devolução média do melhor ponto 0.9%, captura mediana 0.54.
- Perdedores (215): MAE mediano -1.5%, MFE mediano 0.4%; 3 (1%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 22.09; 245% do lucro antes de custos.
- Trades < 3 h: 167 (lucro -0.91); reentradas em < 24 h: 129 (lucro -4.47).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -14.71.
- Lucro por ano de fechamento: 2017: -0.0, 2018: -1.9, 2019: -2.2, 2020: -4.6, 2021: -0.5, 2022: -1.5, 2023: -0.0, 2024: -2.3.

## XRP/USDT

Trades: 372; lucro líquido: -16.64.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_16 | 155 | -15.18 | – | -0.53% | 17% | 4.0 h |
| catchup_target | 149 | 30.69 | – | 1.12% | 100% | 1.4 h |
| catchup_fail_level | 41 | -15.59 | – | -2.07% | 0% | 2.2 h |
| stop_loss | 27 | -16.56 | – | -3.29% | 0% | 1.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 186 | -0.02 | 0.00% | 72% |
| 3 h a 1 dia | 186 | -16.61 | -0.49% | 23% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (175): MFE mediano 1.6%, MAE mediano -0.3%, devolução média do melhor ponto 1.0%, captura mediana 0.50.
- Perdedores (197): MAE mediano -1.5%, MFE mediano 0.5%; 8 (4%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 20.47; 534% do lucro antes de custos.
- Trades < 3 h: 186 (lucro -0.02); reentradas em < 24 h: 116 (lucro -9.41).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -17.90.
- Lucro por ano de fechamento: 2018: -1.2, 2019: -4.2, 2020: -3.0, 2021: -1.8, 2022: -2.2, 2023: -2.3, 2024: -1.9.

## ADA/USDT

Trades: 309; lucro líquido: -7.50.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| catchup_target | 149 | 33.91 | – | 1.21% | 100% | 1.5 h |
| time_exit_16 | 87 | -7.93 | – | -0.48% | 25% | 4.0 h |
| catchup_fail_level | 48 | -18.00 | – | -1.98% | 0% | 1.7 h |
| stop_loss | 25 | -15.48 | – | -3.28% | 0% | 1.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 187 | -0.50 | -0.01% | 68% |
| 3 h a 1 dia | 122 | -7.00 | -0.30% | 35% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (171): MFE mediano 1.8%, MAE mediano -0.4%, devolução média do melhor ponto 1.0%, captura mediana 0.51.
- Perdedores (138): MAE mediano -2.0%, MFE mediano 0.5%; 3 (2%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 17.45; 175% do lucro antes de custos.
- Trades < 3 h: 187 (lucro -0.50); reentradas em < 24 h: 105 (lucro -2.75).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -8.86.
- Lucro por ano de fechamento: 2018: -2.0, 2019: -3.3, 2020: -4.2, 2021: 2.3, 2022: 0.1, 2023: -0.9, 2024: 0.5.

## LTC/USDT

Trades: 239; lucro líquido: -1.04.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| catchup_target | 119 | 31.38 | – | 1.35% | 100% | 1.4 h |
| time_exit_16 | 71 | -7.96 | – | -0.57% | 18% | 4.0 h |
| catchup_fail_level | 26 | -9.64 | – | -1.89% | 0% | 1.5 h |
| stop_loss | 23 | -14.82 | – | -3.28% | 0% | 0.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 145 | 3.97 | 0.14% | 71% |
| 3 h a 1 dia | 94 | -5.01 | -0.26% | 31% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (132): MFE mediano 1.9%, MAE mediano -0.4%, devolução média do melhor ponto 1.1%, captura mediana 0.49.
- Perdedores (107): MAE mediano -1.7%, MFE mediano 0.5%; 1 (1%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 14.07; 108% do lucro antes de custos.
- Trades < 3 h: 145 (lucro 3.97); reentradas em < 24 h: 73 (lucro 0.48).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -2.45.
- Lucro por ano de fechamento: 2018: -1.1, 2019: -2.3, 2020: -3.2, 2021: 5.7, 2022: 0.2, 2023: 1.0, 2024: -1.4.

## LINK/USDT

Trades: 316; lucro líquido: -12.01.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| catchup_target | 138 | 39.43 | – | 1.47% | 100% | 1.4 h |
| time_exit_16 | 81 | -6.23 | – | -0.39% | 28% | 4.0 h |
| catchup_fail_level | 64 | -24.13 | – | -1.96% | 0% | 1.5 h |
| stop_loss | 33 | -21.07 | – | -3.29% | 0% | 1.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 201 | -5.43 | -0.14% | 58% |
| 3 h a 1 dia | 115 | -6.58 | -0.30% | 38% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (161): MFE mediano 1.9%, MAE mediano -0.6%, devolução média do melhor ponto 1.1%, captura mediana 0.53.
- Perdedores (155): MAE mediano -2.1%, MFE mediano 0.5%; 10 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 18.17; 295% do lucro antes de custos.
- Trades < 3 h: 201 (lucro -5.43); reentradas em < 24 h: 113 (lucro 2.34).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -14.95.
- Lucro por ano de fechamento: 2019: -0.9, 2020: -2.2, 2021: -2.8, 2022: -4.2, 2023: -1.7, 2024: -0.2.

## DOGE/USDT

Trades: 271; lucro líquido: -2.36.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| catchup_target | 130 | 32.58 | – | 1.28% | 98% | 1.4 h |
| time_exit_16 | 84 | -7.22 | – | -0.44% | 20% | 4.0 h |
| catchup_fail_level | 37 | -14.61 | – | -2.00% | 0% | 1.8 h |
| stop_loss | 20 | -13.11 | – | -3.28% | 0% | 0.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 160 | 5.21 | 0.17% | 69% |
| 3 h a 1 dia | 111 | -7.57 | -0.35% | 32% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (145): MFE mediano 1.5%, MAE mediano -0.3%, devolução média do melhor ponto 1.1%, captura mediana 0.47.
- Perdedores (126): MAE mediano -1.6%, MFE mediano 0.5%; 8 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 15.94; 117% do lucro antes de custos.
- Trades < 3 h: 160 (lucro 5.21); reentradas em < 24 h: 76 (lucro 2.59).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -7.74.
- Lucro por ano de fechamento: 2019: -1.4, 2020: -3.5, 2021: 5.2, 2022: -2.7, 2023: -0.8, 2024: 0.8.

## SOL/USDT

Trades: 200; lucro líquido: -13.75.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| catchup_target | 94 | 27.40 | – | 1.57% | 100% | 1.4 h |
| catchup_fail_level | 40 | -15.44 | – | -2.05% | 0% | 1.4 h |
| stop_loss | 34 | -20.76 | – | -3.29% | 0% | 1.2 h |
| time_exit_16 | 32 | -4.95 | – | -0.84% | 12% | 4.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 149 | -7.01 | -0.25% | 56% |
| 3 h a 1 dia | 51 | -6.75 | -0.71% | 27% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (98): MFE mediano 2.1%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.55.
- Perdedores (102): MAE mediano -2.9%, MFE mediano 0.6%; 7 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 11.08; – do lucro antes de custos.
- Trades < 3 h: 149 (lucro -7.01); reentradas em < 24 h: 72 (lucro -4.22).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -15.09.
- Lucro por ano de fechamento: 2020: -3.8, 2021: -5.2, 2022: -4.0, 2023: 0.2, 2024: -0.9.
