# Revisão de trades: H-072 (exploração)

Fonte dos trades: `research/experiments/20261107T185606Z-h-072-exploration-btc-usdt/raw/backtest-result-2026-11-07_19-00-12.zip`; `research/experiments/20261107T185606Z-h-072-exploration-eth-usdt/raw/backtest-result-2026-11-07_19-02-46.zip`; `research/experiments/20261107T185606Z-h-072-exploration-bnb-usdt/raw/backtest-result-2026-11-07_19-05-10.zip`; `research/experiments/20261107T185606Z-h-072-exploration-xrp-usdt/raw/backtest-result-2026-11-07_19-07-33.zip`; `research/experiments/20261107T185606Z-h-072-exploration-ada-usdt/raw/backtest-result-2026-11-07_19-09-50.zip`; `research/experiments/20261107T185606Z-h-072-exploration-ltc-usdt/raw/backtest-result-2026-11-07_19-12-08.zip`; `research/experiments/20261107T185606Z-h-072-exploration-link-usdt/raw/backtest-result-2026-11-07_19-14-24.zip`; `research/experiments/20261107T185606Z-h-072-exploration-doge-usdt/raw/backtest-result-2026-11-07_19-16-38.zip`; `research/experiments/20261107T185606Z-h-072-exploration-sol-usdt/raw/backtest-result-2026-11-07_19-18-45.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 40; lucro líquido: -3.04.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12h | 26 | 1.95 | – | 0.39% | 46% | 12.0 h |
| stop_loss | 9 | -7.60 | – | -4.29% | 0% | 5.7 h |
| residual_gap_closed | 5 | 2.62 | – | 2.68% | 100% | 7.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 3 | -2.54 | -4.29% | 0% |
| 3 h a 1 dia | 37 | -0.50 | -0.06% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (17): MFE mediano 4.2%, MAE mediano -0.6%, devolução média do melhor ponto 1.8%, captura mediana 0.56.
- Perdedores (23): MAE mediano -3.0%, MFE mediano 1.3%; 4 (17%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 2.35; – do lucro antes de custos.
- Trades < 3 h: 3 (lucro -2.54); reentradas em < 24 h: 4 (lucro -0.73).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -4.10.
- Lucro por ano de fechamento: 2017: -0.5, 2018: -0.5, 2019: 0.5, 2020: -0.3, 2021: -0.1, 2022: -0.8, 2023: -0.8, 2024: -0.5.

## ETH/USDT

Trades: 65; lucro líquido: -9.70.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12h | 28 | 1.77 | – | 0.33% | 57% | 12.1 h |
| stop_loss | 24 | -19.69 | – | -4.29% | 0% | 3.3 h |
| residual_gap_closed | 13 | 8.21 | – | 3.33% | 92% | 6.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 13 | -10.71 | -4.29% | 0% |
| 3 h a 1 dia | 52 | 1.00 | 0.10% | 54% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (28): MFE mediano 3.8%, MAE mediano -1.4%, devolução média do melhor ponto 1.9%, captura mediana 0.48.
- Perdedores (37): MAE mediano -4.9%, MFE mediano 1.1%; 4 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 3.65; – do lucro antes de custos.
- Trades < 3 h: 13 (lucro -10.71); reentradas em < 24 h: 11 (lucro 2.12).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -10.77.
- Lucro por ano de fechamento: 2017: -0.9, 2018: -3.0, 2019: -2.0, 2020: -1.7, 2021: 0.7, 2022: -3.3, 2023: -0.3, 2024: 0.9.

## BNB/USDT

Trades: 102; lucro líquido: -13.89.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12h | 39 | 0.19 | – | 0.02% | 49% | 12.0 h |
| stop_loss | 38 | -29.98 | – | -4.28% | 0% | 4.6 h |
| residual_gap_closed | 25 | 15.89 | – | 3.52% | 96% | 5.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 19 | -9.66 | -2.76% | 21% |
| 3 h a 1 dia | 83 | -4.23 | -0.26% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (43): MFE mediano 3.5%, MAE mediano -1.0%, devolução média do melhor ponto 1.8%, captura mediana 0.63.
- Perdedores (59): MAE mediano -4.5%, MFE mediano 1.4%; 20 (34%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 5.57; – do lucro antes de custos.
- Trades < 3 h: 19 (lucro -9.66); reentradas em < 24 h: 24 (lucro -2.23).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -17.15.
- Lucro por ano de fechamento: 2018: -2.8, 2019: -4.8, 2020: -1.0, 2021: 0.6, 2022: -3.5, 2023: -2.3, 2024: -0.1.

## XRP/USDT

Trades: 113; lucro líquido: -15.25.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12h | 48 | 2.79 | – | 0.36% | 54% | 12.0 h |
| stop_loss | 47 | -36.56 | – | -4.28% | 0% | 3.0 h |
| residual_gap_closed | 17 | 18.58 | – | 6.15% | 94% | 4.8 h |
| force_exit | 1 | -0.05 | – | -0.32% | 0% | 7.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 32 | -15.78 | -2.66% | 12% |
| 3 h a 1 dia | 81 | 0.54 | 0.06% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (42): MFE mediano 3.2%, MAE mediano -0.9%, devolução média do melhor ponto 2.0%, captura mediana 0.55.
- Perdedores (71): MAE mediano -4.7%, MFE mediano 1.3%; 31 (44%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 6.04; – do lucro antes de custos.
- Trades < 3 h: 32 (lucro -15.78); reentradas em < 24 h: 36 (lucro -3.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -20.28.
- Lucro por ano de fechamento: 2018: -1.8, 2019: -5.9, 2020: -0.4, 2021: -6.0, 2022: -2.8, 2023: 0.6, 2024: 1.1.

## ADA/USDT

Trades: 110; lucro líquido: -10.06.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12h | 51 | 4.47 | – | 0.43% | 59% | 12.0 h |
| stop_loss | 38 | -32.37 | – | -4.28% | 0% | 3.3 h |
| residual_gap_closed | 21 | 17.83 | – | 4.24% | 95% | 5.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 18 | -15.21 | -4.28% | 0% |
| 3 h a 1 dia | 92 | 5.14 | 0.28% | 54% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (50): MFE mediano 4.0%, MAE mediano -0.8%, devolução média do melhor ponto 1.9%, captura mediana 0.57.
- Perdedores (60): MAE mediano -4.5%, MFE mediano 1.1%; 13 (22%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 6.50; – do lucro antes de custos.
- Trades < 3 h: 18 (lucro -15.21); reentradas em < 24 h: 20 (lucro -0.23).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -12.74.
- Lucro por ano de fechamento: 2018: 1.0, 2019: -1.2, 2020: 2.0, 2021: 2.1, 2022: -5.1, 2023: -6.5, 2024: -2.5.

## LTC/USDT

Trades: 90; lucro líquido: -6.32.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12h | 49 | 4.14 | – | 0.43% | 53% | 12.0 h |
| stop_loss | 24 | -20.16 | – | -4.28% | 0% | 2.9 h |
| residual_gap_closed | 17 | 9.71 | – | 2.93% | 88% | 6.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 15 | -9.26 | -3.13% | 13% |
| 3 h a 1 dia | 75 | 2.95 | 0.20% | 52% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (41): MFE mediano 3.6%, MAE mediano -1.1%, devolução média do melhor ponto 1.8%, captura mediana 0.52.
- Perdedores (49): MAE mediano -4.0%, MFE mediano 0.9%; 7 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 5.24; – do lucro antes de custos.
- Trades < 3 h: 15 (lucro -9.26); reentradas em < 24 h: 11 (lucro 3.85).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -7.99.
- Lucro por ano de fechamento: 2018: -0.0, 2019: -1.4, 2020: -0.0, 2021: -2.4, 2022: 1.5, 2023: -1.4, 2024: -2.4.

## LINK/USDT

Trades: 76; lucro líquido: -13.49.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 34 | -27.25 | – | -4.28% | 0% | 2.9 h |
| time_12h | 33 | 4.43 | – | 0.73% | 61% | 12.0 h |
| residual_gap_closed | 9 | 9.34 | – | 5.55% | 100% | 5.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 20 | -8.90 | -2.40% | 15% |
| 3 h a 1 dia | 56 | -4.59 | -0.42% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (29): MFE mediano 5.0%, MAE mediano -1.0%, devolução média do melhor ponto 2.7%, captura mediana 0.56.
- Perdedores (47): MAE mediano -4.7%, MFE mediano 1.4%; 15 (32%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 4.22; – do lucro antes de custos.
- Trades < 3 h: 20 (lucro -8.90); reentradas em < 24 h: 16 (lucro 1.63).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -15.61.
- Lucro por ano de fechamento: 2019: -4.6, 2020: -0.7, 2021: -2.0, 2022: -1.2, 2023: -3.0, 2024: -1.9.

## DOGE/USDT

Trades: 91; lucro líquido: -6.33.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12h | 38 | -2.03 | – | -0.29% | 39% | 12.0 h |
| stop_loss | 30 | -24.27 | – | -4.28% | 0% | 3.0 h |
| residual_gap_closed | 23 | 19.98 | – | 4.70% | 96% | 5.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 20 | -9.03 | -2.38% | 20% |
| 3 h a 1 dia | 71 | 2.70 | 0.23% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (37): MFE mediano 4.2%, MAE mediano -0.8%, devolução média do melhor ponto 2.3%, captura mediana 0.60.
- Perdedores (54): MAE mediano -4.3%, MFE mediano 1.6%; 22 (41%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 5.11; – do lucro antes de custos.
- Trades < 3 h: 20 (lucro -9.03); reentradas em < 24 h: 18 (lucro 1.58).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -8.75.
- Lucro por ano de fechamento: 2019: -1.4, 2020: -3.5, 2021: -4.9, 2022: 3.8, 2023: -0.6, 2024: 0.3.

## SOL/USDT

Trades: 67; lucro líquido: -7.90.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12h | 31 | 4.56 | – | 0.77% | 65% | 12.0 h |
| stop_loss | 27 | -22.22 | – | -4.28% | 0% | 2.4 h |
| residual_gap_closed | 9 | 9.76 | – | 5.74% | 89% | 4.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 20 | -8.55 | -2.19% | 15% |
| 3 h a 1 dia | 47 | 0.65 | 0.08% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (28): MFE mediano 4.3%, MAE mediano -0.8%, devolução média do melhor ponto 3.9%, captura mediana 0.40.
- Perdedores (39): MAE mediano -5.9%, MFE mediano 1.4%; 17 (44%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 3.82; – do lucro antes de custos.
- Trades < 3 h: 20 (lucro -8.55); reentradas em < 24 h: 20 (lucro -4.20).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -10.52.
- Lucro por ano de fechamento: 2020: 0.6, 2021: -0.4, 2022: -5.0, 2023: -1.6, 2024: -1.5.
