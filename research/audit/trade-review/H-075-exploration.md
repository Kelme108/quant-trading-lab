# Revisão de trades: H-075 (exploração)

Fonte dos trades: `research/experiments/20261107T211759Z-h-075-exploration-btc-usdt/raw/backtest-result-2026-11-07_21-22-55.zip`; `research/experiments/20261107T211759Z-h-075-exploration-eth-usdt/raw/backtest-result-2026-11-07_21-25-23.zip`; `research/experiments/20261107T211759Z-h-075-exploration-bnb-usdt/raw/backtest-result-2026-11-07_21-27-52.zip`; `research/experiments/20261107T211759Z-h-075-exploration-xrp-usdt/raw/backtest-result-2026-11-07_21-30-16.zip`; `research/experiments/20261107T211759Z-h-075-exploration-ada-usdt/raw/backtest-result-2026-11-07_21-32-39.zip`; `research/experiments/20261107T211759Z-h-075-exploration-ltc-usdt/raw/backtest-result-2026-11-07_21-35-06.zip`; `research/experiments/20261107T211759Z-h-075-exploration-link-usdt/raw/backtest-result-2026-11-07_21-37-30.zip`; `research/experiments/20261107T211759Z-h-075-exploration-doge-usdt/raw/backtest-result-2026-11-07_21-39-48.zip`; `research/experiments/20261107T211759Z-h-075-exploration-sol-usdt/raw/backtest-result-2026-11-07_21-42-02.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 107; lucro líquido: -7.80.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| roi | 49 | 16.98 | – | 1.46% | 96% | 6.3 h |
| close_below_flag_low | 33 | -18.18 | – | -2.31% | 0% | 9.2 h |
| time_exit_24_bars | 18 | -0.28 | – | -0.07% | 33% | 24.0 h |
| stop_loss | 6 | -6.24 | – | -4.29% | 0% | 6.0 h |
| target_flag_low_plus_pole | 1 | -0.07 | – | -0.30% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 25 | 3.75 | 0.65% | 72% |
| 3 h a 1 dia | 64 | -11.27 | -0.73% | 45% |
| 1 a 7 dias | 18 | -0.28 | -0.07% | 33% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (53): MFE mediano 2.1%, MAE mediano -0.7%, devolução média do melhor ponto 1.0%, captura mediana 0.67.
- Perdedores (54): MAE mediano -2.7%, MFE mediano 0.6%; 3 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 7.61; – do lucro antes de custos.
- Trades < 3 h: 25 (lucro 3.75); reentradas em < 24 h: 1 (lucro 0.35).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -8.93.
- Lucro por ano de fechamento: 2017: 0.1, 2018: -4.5, 2019: 0.9, 2020: 0.4, 2021: -2.5, 2022: -2.8, 2023: 0.2, 2024: 0.4.

## ETH/USDT

Trades: 135; lucro líquido: -13.94.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| roi | 61 | 24.94 | – | 1.75% | 95% | 6.8 h |
| close_below_flag_low | 41 | -21.24 | – | -2.24% | 0% | 9.3 h |
| time_exit_24_bars | 16 | -3.15 | – | -0.84% | 25% | 24.0 h |
| stop_loss | 14 | -14.28 | – | -4.29% | 0% | 8.1 h |
| target_flag_low_plus_pole | 3 | -0.21 | – | -0.30% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 31 | -2.40 | -0.33% | 52% |
| 3 h a 1 dia | 87 | -7.73 | -0.37% | 48% |
| 1 a 7 dias | 17 | -3.80 | -0.97% | 24% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (62): MFE mediano 2.6%, MAE mediano -0.8%, devolução média do melhor ponto 1.2%, captura mediana 0.62.
- Perdedores (73): MAE mediano -2.8%, MFE mediano 0.9%; 10 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 9.41; – do lucro antes de custos.
- Trades < 3 h: 31 (lucro -2.40); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -15.43.
- Lucro por ano de fechamento: 2017: 2.1, 2018: -6.3, 2019: -1.8, 2020: -1.0, 2021: -2.6, 2022: 2.1, 2023: -3.2, 2024: -3.3.

## BNB/USDT

Trades: 126; lucro líquido: -11.70.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| roi | 58 | 25.71 | – | 1.86% | 97% | 4.7 h |
| close_below_flag_low | 32 | -16.60 | – | -2.21% | 0% | 8.8 h |
| stop_loss | 19 | -19.67 | – | -4.29% | 0% | 8.7 h |
| time_exit_24_bars | 12 | -0.79 | – | -0.27% | 42% | 24.0 h |
| target_flag_low_plus_pole | 5 | -0.36 | – | -0.30% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 36 | 5.55 | 0.65% | 61% |
| 3 h a 1 dia | 78 | -16.46 | -0.88% | 44% |
| 1 a 7 dias | 12 | -0.79 | -0.27% | 42% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (61): MFE mediano 2.5%, MAE mediano -0.7%, devolução média do melhor ponto 1.3%, captura mediana 0.63.
- Perdedores (65): MAE mediano -2.8%, MFE mediano 1.0%; 13 (20%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 8.89; – do lucro antes de custos.
- Trades < 3 h: 36 (lucro 5.55); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -14.38.
- Lucro por ano de fechamento: 2017: -0.3, 2018: -1.0, 2019: -3.4, 2020: -0.0, 2021: -1.6, 2022: -2.2, 2023: -1.6, 2024: -1.7.

## XRP/USDT

Trades: 102; lucro líquido: -20.28.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| roi | 41 | 15.32 | – | 1.66% | 93% | 4.0 h |
| close_below_flag_low | 30 | -15.98 | – | -2.39% | 0% | 9.5 h |
| stop_loss | 18 | -17.59 | – | -4.28% | 0% | 6.7 h |
| time_exit_24_bars | 9 | -1.73 | – | -0.88% | 11% | 24.0 h |
| target_flag_low_plus_pole | 4 | -0.29 | – | -0.30% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 37 | 1.25 | 0.16% | 59% |
| 3 h a 1 dia | 56 | -19.81 | -1.57% | 29% |
| 1 a 7 dias | 9 | -1.73 | -0.88% | 11% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (39): MFE mediano 3.1%, MAE mediano -0.9%, devolução média do melhor ponto 1.7%, captura mediana 0.53.
- Perdedores (63): MAE mediano -2.9%, MFE mediano 1.0%; 9 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 6.88; – do lucro antes de custos.
- Trades < 3 h: 37 (lucro 1.25); reentradas em < 24 h: 1 (lucro -0.68).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -22.03.
- Lucro por ano de fechamento: 2018: -0.8, 2019: -1.9, 2020: -3.7, 2021: -6.9, 2022: -1.3, 2023: -5.8, 2024: 0.2.

## ADA/USDT

Trades: 115; lucro líquido: -2.39.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| roi | 56 | 33.56 | – | 2.38% | 96% | 5.7 h |
| close_below_flag_low | 27 | -15.23 | – | -2.24% | 0% | 9.5 h |
| stop_loss | 18 | -19.63 | – | -4.28% | 0% | 7.9 h |
| time_exit_24_bars | 11 | -0.87 | – | -0.31% | 27% | 24.0 h |
| target_flag_low_plus_pole | 3 | -0.23 | – | -0.30% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 33 | 5.23 | 0.63% | 70% |
| 3 h a 1 dia | 71 | -6.75 | -0.36% | 44% |
| 1 a 7 dias | 11 | -0.87 | -0.31% | 27% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (57): MFE mediano 3.3%, MAE mediano -1.3%, devolução média do melhor ponto 1.5%, captura mediana 0.66.
- Perdedores (58): MAE mediano -2.9%, MFE mediano 0.9%; 15 (26%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 8.68; 138% do lucro antes de custos.
- Trades < 3 h: 33 (lucro 5.23); reentradas em < 24 h: 2 (lucro -1.62).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -5.12.
- Lucro por ano de fechamento: 2018: 3.3, 2019: -3.3, 2020: 2.6, 2021: -4.3, 2022: 2.5, 2023: -0.7, 2024: -2.5.

## LTC/USDT

Trades: 128; lucro líquido: -10.23.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| roi | 62 | 30.79 | – | 2.06% | 97% | 5.1 h |
| close_below_flag_low | 32 | -17.57 | – | -2.29% | 0% | 10.3 h |
| stop_loss | 23 | -24.10 | – | -4.28% | 0% | 7.8 h |
| time_exit_24_bars | 11 | 0.64 | – | 0.22% | 27% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 36 | 4.28 | 0.50% | 75% |
| 3 h a 1 dia | 81 | -15.16 | -0.77% | 41% |
| 1 a 7 dias | 11 | 0.64 | 0.22% | 27% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (63): MFE mediano 3.0%, MAE mediano -1.0%, devolução média do melhor ponto 1.6%, captura mediana 0.64.
- Perdedores (65): MAE mediano -3.0%, MFE mediano 0.8%; 5 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 9.20; – do lucro antes de custos.
- Trades < 3 h: 36 (lucro 4.28); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -12.21.
- Lucro por ano de fechamento: 2018: -3.9, 2019: 5.3, 2020: -2.3, 2021: -5.5, 2022: -1.6, 2023: -2.1, 2024: -0.1.

## LINK/USDT

Trades: 112; lucro líquido: -10.20.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| roi | 54 | 20.21 | – | 1.66% | 96% | 4.8 h |
| close_below_flag_low | 24 | -13.76 | – | -2.50% | 0% | 8.8 h |
| stop_loss | 16 | -15.81 | – | -4.28% | 0% | 8.3 h |
| time_exit_24_bars | 13 | -0.49 | – | -0.15% | 31% | 24.0 h |
| target_flag_low_plus_pole | 5 | -0.34 | – | -0.30% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 37 | -2.39 | -0.27% | 57% |
| 3 h a 1 dia | 62 | -7.32 | -0.48% | 50% |
| 1 a 7 dias | 13 | -0.49 | -0.15% | 31% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (56): MFE mediano 2.5%, MAE mediano -1.1%, devolução média do melhor ponto 1.2%, captura mediana 0.59.
- Perdedores (56): MAE mediano -3.3%, MFE mediano 1.2%; 17 (30%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 7.62; – do lucro antes de custos.
- Trades < 3 h: 37 (lucro -2.39); reentradas em < 24 h: 1 (lucro 1.13).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -11.56.
- Lucro por ano de fechamento: 2019: -5.0, 2020: -6.9, 2021: -0.0, 2022: 2.3, 2023: 1.0, 2024: -1.6.

## DOGE/USDT

Trades: 91; lucro líquido: -7.76.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| roi | 38 | 21.07 | – | 2.31% | 97% | 4.2 h |
| close_below_flag_low | 23 | -12.21 | – | -2.20% | 0% | 8.9 h |
| stop_loss | 16 | -16.63 | – | -4.28% | 0% | 3.6 h |
| time_exit_24_bars | 11 | 0.23 | – | 0.08% | 55% | 24.0 h |
| target_flag_low_plus_pole | 3 | -0.22 | – | -0.30% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 37 | 0.59 | 0.09% | 54% |
| 3 h a 1 dia | 43 | -8.58 | -0.82% | 40% |
| 1 a 7 dias | 11 | 0.23 | 0.08% | 55% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (43): MFE mediano 3.3%, MAE mediano -0.9%, devolução média do melhor ponto 2.0%, captura mediana 0.58.
- Perdedores (48): MAE mediano -2.9%, MFE mediano 0.7%; 11 (23%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 6.57; – do lucro antes de custos.
- Trades < 3 h: 37 (lucro 0.59); reentradas em < 24 h: 1 (lucro 0.11).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -9.71.
- Lucro por ano de fechamento: 2019: -1.6, 2020: -0.9, 2021: -1.8, 2022: 2.9, 2023: -6.8, 2024: 0.4.

## SOL/USDT

Trades: 82; lucro líquido: -7.92.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| roi | 42 | 23.61 | – | 2.41% | 95% | 4.0 h |
| stop_loss | 23 | -23.35 | – | -4.28% | 0% | 6.6 h |
| close_below_flag_low | 12 | -7.68 | – | -2.70% | 0% | 9.7 h |
| time_exit_24_bars | 3 | -0.35 | – | -0.52% | 33% | 24.0 h |
| target_flag_low_plus_pole | 2 | -0.14 | – | -0.30% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 33 | 0.10 | 0.03% | 58% |
| 3 h a 1 dia | 46 | -7.66 | -0.68% | 46% |
| 1 a 7 dias | 3 | -0.35 | -0.52% | 33% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (41): MFE mediano 3.4%, MAE mediano -0.7%, devolução média do melhor ponto 1.6%, captura mediana 0.63.
- Perdedores (41): MAE mediano -4.3%, MFE mediano 1.1%; 13 (32%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 5.74; – do lucro antes de custos.
- Trades < 3 h: 33 (lucro 0.10); reentradas em < 24 h: 1 (lucro -1.04).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -10.07.
- Lucro por ano de fechamento: 2020: -4.3, 2021: -0.4, 2022: -2.1, 2023: -3.9, 2024: 2.7.
