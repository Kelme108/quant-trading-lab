# Revisão de trades: H-063 (exploração)

Fonte dos trades: `research/experiments/20261107T140523Z-h-063-exploration-btc-usdt/raw/backtest-result-2026-11-07_14-11-08.zip`; `research/experiments/20261107T140523Z-h-063-exploration-eth-usdt/raw/backtest-result-2026-11-07_14-15-48.zip`; `research/experiments/20261107T140523Z-h-063-exploration-bnb-usdt/raw/backtest-result-2026-11-07_14-19-34.zip`; `research/experiments/20261107T140523Z-h-063-exploration-xrp-usdt/raw/backtest-result-2026-11-07_14-23-48.zip`; `research/experiments/20261107T140523Z-h-063-exploration-ada-usdt/raw/backtest-result-2026-11-07_14-27-23.zip`; `research/experiments/20261107T140523Z-h-063-exploration-ltc-usdt/raw/backtest-result-2026-11-07_14-31-30.zip`; `research/experiments/20261107T140523Z-h-063-exploration-link-usdt/raw/backtest-result-2026-11-07_14-35-04.zip`; `research/experiments/20261107T140523Z-h-063-exploration-doge-usdt/raw/backtest-result-2026-11-07_14-39-28.zip`; `research/experiments/20261107T140523Z-h-063-exploration-sol-usdt/raw/backtest-result-2026-11-07_14-43-26.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 92; lucro líquido: -11.48.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| close_below_low16 | 81 | -17.40 | – | -0.93% | 17% | 8.7 h |
| time_exit_96_bars | 10 | 7.16 | – | 3.27% | 90% | 24.0 h |
| stop_loss | 1 | -1.24 | – | -5.28% | 0% | 0.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 8 | -4.11 | -2.22% | 0% |
| 3 h a 1 dia | 74 | -14.53 | -0.85% | 19% |
| 1 a 7 dias | 10 | 7.16 | 3.27% | 90% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (23): MFE mediano 3.6%, MAE mediano -0.5%, devolução média do melhor ponto 2.7%, captura mediana 0.47.
- Perdedores (69): MAE mediano -1.7%, MFE mediano 0.7%; 6 (9%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 6.24; – do lucro antes de custos.
- Trades < 3 h: 8 (lucro -4.11); reentradas em < 24 h: 20 (lucro -3.99).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -13.79.
- Lucro por ano de fechamento: 2018: -3.6, 2019: -1.1, 2020: -0.1, 2021: -6.1, 2022: -0.2, 2023: -2.5, 2024: 2.1.

## ETH/USDT

Trades: 132; lucro líquido: -1.28.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| close_below_low16 | 118 | -11.97 | – | -0.39% | 31% | 9.2 h |
| time_exit_96_bars | 11 | 14.79 | – | 5.21% | 91% | 24.0 h |
| stop_loss | 3 | -4.09 | – | -5.28% | 0% | 7.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 9 | -5.17 | -2.29% | 0% |
| 3 h a 1 dia | 112 | -10.90 | -0.36% | 32% |
| 1 a 7 dias | 11 | 14.79 | 5.21% | 91% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (46): MFE mediano 5.1%, MAE mediano -1.0%, devolução média do melhor ponto 3.7%, captura mediana 0.41.
- Perdedores (86): MAE mediano -2.0%, MFE mediano 0.8%; 20 (23%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 10.14; 114% do lucro antes de custos.
- Trades < 3 h: 9 (lucro -5.17); reentradas em < 24 h: 42 (lucro -1.33).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -3.94.
- Lucro por ano de fechamento: 2017: -1.7, 2018: 5.5, 2019: 3.8, 2020: -3.6, 2021: 0.9, 2022: -2.4, 2023: -0.6, 2024: -3.2.

## BNB/USDT

Trades: 74; lucro líquido: -14.56.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| close_below_low16 | 65 | -10.00 | – | -0.68% | 25% | 8.7 h |
| stop_loss | 5 | -6.40 | – | -5.28% | 0% | 4.5 h |
| time_exit_96_bars | 4 | 1.84 | – | 2.11% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 12 | -8.72 | -3.11% | 0% |
| 3 h a 1 dia | 58 | -7.68 | -0.58% | 28% |
| 1 a 7 dias | 4 | 1.84 | 2.11% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (20): MFE mediano 5.1%, MAE mediano -0.7%, devolução média do melhor ponto 3.5%, captura mediana 0.40.
- Perdedores (54): MAE mediano -1.8%, MFE mediano 0.9%; 6 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 5.05; – do lucro antes de custos.
- Trades < 3 h: 12 (lucro -8.72); reentradas em < 24 h: 13 (lucro -3.63).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -16.58.
- Lucro por ano de fechamento: 2018: -3.8, 2019: 1.3, 2020: -4.6, 2021: 0.4, 2022: -6.6, 2023: 0.1, 2024: -1.3.

## XRP/USDT

Trades: 72; lucro líquido: 0.11.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| close_below_low16 | 59 | -0.35 | -312% | 0.03% | 27% | 9.1 h |
| stop_loss | 10 | -13.23 | -11738% | -5.28% | 0% | 3.8 h |
| time_exit_96_bars | 3 | 13.69 | 12149% | 18.71% | 67% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 7 | -8.13 | -4.57% | 0% |
| 3 h a 1 dia | 62 | -5.44 | -0.30% | 26% |
| 1 a 7 dias | 3 | 13.69 | 18.71% | 67% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (18): MFE mediano 6.2%, MAE mediano -0.9%, devolução média do melhor ponto 10.3%, captura mediana 0.35.
- Perdedores (54): MAE mediano -2.8%, MFE mediano 1.1%; 16 (30%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 5.36; 98% do lucro antes de custos.
- Trades < 3 h: 7 (lucro -8.13); reentradas em < 24 h: 12 (lucro -4.71).
- Maior trade = 8434% do lucro; top 5 = 25750%; top 10 = 29706%; lucro sem o melhor = -9.39.
- Lucro por ano de fechamento: 2018: 5.2, 2019: -9.8, 2020: -2.5, 2021: 4.9, 2022: 2.1, 2023: 1.7, 2024: -1.6.

## ADA/USDT

Trades: 66; lucro líquido: -15.88.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| close_below_low16 | 54 | -9.94 | – | -0.83% | 26% | 8.4 h |
| stop_loss | 8 | -9.88 | – | -5.28% | 0% | 2.6 h |
| time_exit_96_bars | 4 | 3.95 | – | 4.67% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 6 | -6.67 | -4.77% | 0% |
| 3 h a 1 dia | 56 | -13.15 | -1.04% | 25% |
| 1 a 7 dias | 4 | 3.95 | 4.67% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (18): MFE mediano 5.8%, MAE mediano -1.0%, devolução média do melhor ponto 4.0%, captura mediana 0.39.
- Perdedores (48): MAE mediano -2.8%, MFE mediano 0.9%; 11 (23%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 4.36; – do lucro antes de custos.
- Trades < 3 h: 6 (lucro -6.67); reentradas em < 24 h: 15 (lucro -4.96).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -18.42.
- Lucro por ano de fechamento: 2018: -2.9, 2019: -5.3, 2020: -0.3, 2021: -4.6, 2022: -1.1, 2023: -2.1, 2024: 0.5.

## LTC/USDT

Trades: 97; lucro líquido: -5.91.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| close_below_low16 | 88 | -4.51 | – | -0.21% | 26% | 10.3 h |
| stop_loss | 5 | -6.66 | – | -5.28% | 0% | 8.7 h |
| time_exit_96_bars | 4 | 5.26 | – | 5.41% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 3 | -3.21 | -4.30% | 0% |
| 3 h a 1 dia | 90 | -7.96 | -0.36% | 26% |
| 1 a 7 dias | 4 | 5.26 | 5.41% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (27): MFE mediano 6.4%, MAE mediano -0.5%, devolução média do melhor ponto 3.9%, captura mediana 0.35.
- Perdedores (70): MAE mediano -1.6%, MFE mediano 1.4%; 21 (30%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 7.17; 571% do lucro antes de custos.
- Trades < 3 h: 3 (lucro -3.21); reentradas em < 24 h: 21 (lucro 0.35).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -8.80.
- Lucro por ano de fechamento: 2018: 0.0, 2019: 2.1, 2020: -2.5, 2021: -0.2, 2022: -1.9, 2023: -1.5, 2024: -1.9.

## LINK/USDT

Trades: 71; lucro líquido: -14.16.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| close_below_low16 | 66 | -10.12 | – | -0.67% | 29% | 8.6 h |
| stop_loss | 4 | -5.15 | – | -5.28% | 0% | 4.1 h |
| time_exit_96_bars | 1 | 1.12 | – | 5.11% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 7 | -6.06 | -3.61% | 0% |
| 3 h a 1 dia | 63 | -9.22 | -0.64% | 30% |
| 1 a 7 dias | 1 | 1.12 | 5.11% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (20): MFE mediano 6.6%, MAE mediano -1.2%, devolução média do melhor ponto 4.4%, captura mediana 0.45.
- Perdedores (51): MAE mediano -2.6%, MFE mediano 1.0%; 10 (20%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 4.96; – do lucro antes de custos.
- Trades < 3 h: 7 (lucro -6.06); reentradas em < 24 h: 20 (lucro -8.41).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -16.39.
- Lucro por ano de fechamento: 2019: 2.0, 2020: -1.4, 2021: -4.3, 2022: -6.8, 2023: -3.5, 2024: -0.0.

## DOGE/USDT

Trades: 41; lucro líquido: -0.41.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| close_below_low16 | 29 | 9.01 | – | 1.37% | 31% | 8.7 h |
| stop_loss | 10 | -12.92 | – | -5.28% | 0% | 2.1 h |
| time_exit_96_bars | 2 | 3.50 | – | 7.09% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 9 | -11.23 | -5.12% | 0% |
| 3 h a 1 dia | 30 | 7.32 | 1.10% | 30% |
| 1 a 7 dias | 2 | 3.50 | 7.09% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (11): MFE mediano 14.7%, MAE mediano -0.9%, devolução média do melhor ponto 23.8%, captura mediana 0.37.
- Perdedores (30): MAE mediano -4.0%, MFE mediano 2.1%; 15 (50%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 2.96; 116% do lucro antes de custos.
- Trades < 3 h: 9 (lucro -11.23); reentradas em < 24 h: 8 (lucro 10.44).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -8.28.
- Lucro por ano de fechamento: 2020: -1.8, 2021: -4.3, 2022: 4.4, 2023: -3.3, 2024: 4.6.

## SOL/USDT

Trades: 70; lucro líquido: 3.22.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| close_below_low16 | 56 | 1.26 | 39% | 0.08% | 38% | 9.7 h |
| stop_loss | 9 | -12.60 | -391% | -5.28% | 0% | 2.8 h |
| time_exit_96_bars | 5 | 14.56 | 452% | 11.67% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 7 | -8.31 | -4.44% | 0% |
| 3 h a 1 dia | 58 | -3.03 | -0.20% | 36% |
| 1 a 7 dias | 5 | 14.56 | 11.67% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (26): MFE mediano 9.0%, MAE mediano -1.1%, devolução média do melhor ponto 6.0%, captura mediana 0.38.
- Perdedores (44): MAE mediano -3.2%, MFE mediano 1.7%; 20 (45%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 5.53; 63% do lucro antes de custos.
- Trades < 3 h: 7 (lucro -8.31); reentradas em < 24 h: 21 (lucro -1.94).
- Maior trade = 257% do lucro; top 5 = 616%; top 10 = 838%; lucro sem o melhor = -5.06.
- Lucro por ano de fechamento: 2020: 7.4, 2021: -3.4, 2022: -3.6, 2023: 3.8, 2024: -1.0.
