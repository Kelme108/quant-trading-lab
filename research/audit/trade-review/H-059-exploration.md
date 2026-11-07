# Revisão de trades: H-059 (exploração)

Fonte dos trades: `research/experiments/20261107T112416Z-h-059-exploration-btc-usdt/raw/backtest-result-2026-11-07_11-36-06.zip`; `research/experiments/20261107T112416Z-h-059-exploration-eth-usdt/raw/backtest-result-2026-11-07_11-42-34.zip`; `research/experiments/20261107T112416Z-h-059-exploration-bnb-usdt/raw/backtest-result-2026-11-07_11-48-53.zip`; `research/experiments/20261107T112416Z-h-059-exploration-xrp-usdt/raw/backtest-result-2026-11-07_11-54-38.zip`; `research/experiments/20261107T112416Z-h-059-exploration-ada-usdt/raw/backtest-result-2026-11-07_12-00-25.zip`; `research/experiments/20261107T112416Z-h-059-exploration-ltc-usdt/raw/backtest-result-2026-11-07_12-06-27.zip`; `research/experiments/20261107T112416Z-h-059-exploration-link-usdt/raw/backtest-result-2026-11-07_12-12-23.zip`; `research/experiments/20261107T112416Z-h-059-exploration-doge-usdt/raw/backtest-result-2026-11-07_12-17-09.zip`; `research/experiments/20261107T112416Z-h-059-exploration-sol-usdt/raw/backtest-result-2026-11-07_12-21-42.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 304; lucro líquido: -1.25.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 173 | 55.24 | – | 1.61% | 74% | 14.0 h |
| close_below_jump_low | 98 | -34.54 | – | -1.77% | 0% | 5.1 h |
| stop_loss | 33 | -21.95 | – | -3.29% | 0% | 3.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 64 | -29.03 | -2.26% | 0% |
| 3 h a 1 dia | 240 | 27.77 | 0.59% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (128): MFE mediano 3.0%, MAE mediano -0.4%, devolução média do melhor ponto 1.7%, captura mediana 0.53.
- Perdedores (176): MAE mediano -2.0%, MFE mediano 0.7%; 26 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 18.18; 107% do lucro antes de custos.
- Trades < 3 h: 64 (lucro -29.03); reentradas em < 24 h: 49 (lucro 1.53).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -4.16.
- Lucro por ano de fechamento: 2017: 0.5, 2018: 1.4, 2019: -3.9, 2020: 3.0, 2021: 1.0, 2022: -2.3, 2023: -1.8, 2024: 0.9.

## ETH/USDT

Trades: 298; lucro líquido: 17.74.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 165 | 92.83 | 523% | 2.49% | 79% | 13.7 h |
| close_below_jump_low | 84 | -38.36 | -216% | -1.95% | 0% | 5.2 h |
| stop_loss | 49 | -36.72 | -207% | -3.29% | 0% | 5.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 56 | -30.38 | -2.36% | 0% |
| 3 h a 1 dia | 242 | 48.12 | 0.90% | 54% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (130): MFE mediano 4.2%, MAE mediano -0.5%, devolução média do melhor ponto 2.2%, captura mediana 0.60.
- Perdedores (168): MAE mediano -2.5%, MFE mediano 1.0%; 31 (18%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 20.67; 54% do lucro antes de custos.
- Trades < 3 h: 56 (lucro -30.38); reentradas em < 24 h: 49 (lucro 2.55).
- Maior trade = 23% do lucro; top 5 = 87%; top 10 = 147%; lucro sem o melhor = 13.66.
- Lucro por ano de fechamento: 2017: 5.9, 2018: -0.0, 2019: 1.3, 2020: 10.0, 2021: 6.4, 2022: 2.3, 2023: -8.8, 2024: 0.7.

## BNB/USDT

Trades: 269; lucro líquido: 7.20.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 151 | 73.18 | 1016% | 2.19% | 75% | 13.6 h |
| close_below_jump_low | 70 | -30.43 | -423% | -1.94% | 0% | 5.8 h |
| stop_loss | 48 | -35.55 | -494% | -3.29% | 0% | 3.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 54 | -32.83 | -2.70% | 0% |
| 3 h a 1 dia | 215 | 40.03 | 0.85% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (113): MFE mediano 3.8%, MAE mediano -0.7%, devolução média do melhor ponto 1.9%, captura mediana 0.56.
- Perdedores (156): MAE mediano -2.4%, MFE mediano 0.9%; 39 (25%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 18.01; 71% do lucro antes de custos.
- Trades < 3 h: 54 (lucro -32.83); reentradas em < 24 h: 40 (lucro 2.09).
- Maior trade = 51% do lucro; top 5 = 189%; top 10 = 330%; lucro sem o melhor = 3.56.
- Lucro por ano de fechamento: 2017: 0.2, 2018: -1.3, 2019: 15.5, 2020: 6.1, 2021: -3.0, 2022: -4.4, 2023: -4.3, 2024: -1.7.

## XRP/USDT

Trades: 253; lucro líquido: -6.22.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 120 | 68.11 | – | 2.75% | 74% | 13.5 h |
| stop_loss | 68 | -46.50 | – | -3.29% | 0% | 4.3 h |
| close_below_jump_low | 65 | -27.83 | – | -2.05% | 0% | 4.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 60 | -33.57 | -2.70% | 0% |
| 3 h a 1 dia | 193 | 27.36 | 0.70% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (89): MFE mediano 4.7%, MAE mediano -0.9%, devolução média do melhor ponto 3.0%, captura mediana 0.50.
- Perdedores (164): MAE mediano -2.8%, MFE mediano 1.0%; 40 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 15.81; 165% do lucro antes de custos.
- Trades < 3 h: 60 (lucro -33.57); reentradas em < 24 h: 41 (lucro -6.68).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -14.05.
- Lucro por ano de fechamento: 2018: 10.8, 2019: -0.6, 2020: -9.3, 2021: 5.8, 2022: -6.6, 2023: -6.8, 2024: 0.4.

## ADA/USDT

Trades: 209; lucro líquido: 2.57.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 94 | 70.56 | 2742% | 3.56% | 78% | 14.9 h |
| stop_loss | 61 | -42.97 | -1670% | -3.28% | 0% | 4.5 h |
| close_below_jump_low | 54 | -25.01 | -972% | -2.17% | 0% | 5.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 49 | -29.33 | -2.80% | 0% |
| 3 h a 1 dia | 160 | 31.91 | 0.97% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (73): MFE mediano 5.2%, MAE mediano -0.7%, devolução média do melhor ponto 2.8%, captura mediana 0.60.
- Perdedores (136): MAE mediano -3.0%, MFE mediano 1.1%; 49 (36%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 13.31; 84% do lucro antes de custos.
- Trades < 3 h: 49 (lucro -29.33); reentradas em < 24 h: 31 (lucro -7.79).
- Maior trade = 228% do lucro; top 5 = 824%; top 10 = 1379%; lucro sem o melhor = -3.30.
- Lucro por ano de fechamento: 2018: -1.1, 2019: 2.4, 2020: 5.1, 2021: 6.0, 2022: -4.1, 2023: -3.1, 2024: -2.5.

## LTC/USDT

Trades: 290; lucro líquido: -2.69.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 152 | 72.70 | – | 2.35% | 71% | 13.6 h |
| close_below_jump_low | 74 | -31.75 | – | -2.13% | 0% | 5.9 h |
| stop_loss | 64 | -43.63 | – | -3.28% | 0% | 5.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 54 | -31.04 | -2.76% | 0% |
| 3 h a 1 dia | 236 | 28.35 | 0.59% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (108): MFE mediano 4.3%, MAE mediano -0.6%, devolução média do melhor ponto 2.3%, captura mediana 0.55.
- Perdedores (182): MAE mediano -2.7%, MFE mediano 1.0%; 44 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 17.71; 118% do lucro antes de custos.
- Trades < 3 h: 54 (lucro -31.04); reentradas em < 24 h: 46 (lucro -10.48).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -6.52.
- Lucro por ano de fechamento: 2018: -5.2, 2019: 6.7, 2020: 8.4, 2021: -6.5, 2022: -0.5, 2023: -7.4, 2024: 2.0.

## LINK/USDT

Trades: 189; lucro líquido: 4.59.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 95 | 63.14 | 1377% | 3.23% | 78% | 12.6 h |
| stop_loss | 63 | -43.52 | -949% | -3.29% | 0% | 4.8 h |
| close_below_jump_low | 31 | -15.03 | -328% | -2.34% | 0% | 5.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 44 | -28.15 | -3.07% | 0% |
| 3 h a 1 dia | 145 | 32.73 | 1.12% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (74): MFE mediano 5.0%, MAE mediano -0.8%, devolução média do melhor ponto 2.8%, captura mediana 0.58.
- Perdedores (115): MAE mediano -3.1%, MFE mediano 1.2%; 40 (35%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 11.82; 72% do lucro antes de custos.
- Trades < 3 h: 44 (lucro -28.15); reentradas em < 24 h: 23 (lucro 8.66).
- Maior trade = 184% do lucro; top 5 = 418%; top 10 = 645%; lucro sem o melhor = -3.87.
- Lucro por ano de fechamento: 2019: 7.7, 2020: -2.7, 2021: -2.1, 2022: -2.5, 2023: 2.3, 2024: 2.0.

## DOGE/USDT

Trades: 205; lucro líquido: -26.88.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 85 | -50.64 | – | -3.28% | 0% | 3.6 h |
| time_exit_utc_day_close | 76 | 41.23 | – | 2.91% | 71% | 14.1 h |
| close_below_jump_low | 44 | -17.47 | – | -2.18% | 0% | 4.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 67 | -36.68 | -3.04% | 0% |
| 3 h a 1 dia | 138 | 9.80 | 0.36% | 39% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (54): MFE mediano 5.9%, MAE mediano -1.0%, devolução média do melhor ponto 4.1%, captura mediana 0.54.
- Perdedores (151): MAE mediano -3.1%, MFE mediano 1.3%; 54 (36%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 11.17; – do lucro antes de custos.
- Trades < 3 h: 67 (lucro -36.68); reentradas em < 24 h: 36 (lucro 1.08).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -29.98.
- Lucro por ano de fechamento: 2019: -4.1, 2020: 2.1, 2021: -4.8, 2022: -7.3, 2023: -10.0, 2024: -2.8.

## SOL/USDT

Trades: 147; lucro líquido: 27.96.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 62 | 92.75 | 332% | 6.24% | 84% | 14.0 h |
| stop_loss | 62 | -50.93 | -182% | -3.28% | 0% | 4.5 h |
| close_below_jump_low | 23 | -13.86 | -50% | -2.28% | 0% | 3.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 45 | -33.65 | -2.95% | 0% |
| 3 h a 1 dia | 102 | 61.61 | 2.58% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (52): MFE mediano 7.6%, MAE mediano -0.9%, devolução média do melhor ponto 3.3%, captura mediana 0.61.
- Perdedores (95): MAE mediano -3.2%, MFE mediano 1.1%; 37 (39%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 11.26; 29% do lucro antes de custos.
- Trades < 3 h: 45 (lucro -33.65); reentradas em < 24 h: 27 (lucro 5.41).
- Maior trade = 38% do lucro; top 5 = 121%; top 10 = 180%; lucro sem o melhor = 17.22.
- Lucro por ano de fechamento: 2020: -2.4, 2021: 40.7, 2022: -9.4, 2023: 4.8, 2024: -5.7.
