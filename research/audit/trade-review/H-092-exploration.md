# Revisão de trades: H-092 (exploração)

Fonte dos trades: `research/experiments/20261110T005514Z-h-092-exploration-btc-usdt/raw/backtest-result-2026-11-10_01-02-59.zip`; `research/experiments/20261110T005514Z-h-092-exploration-eth-usdt/raw/backtest-result-2026-11-10_01-06-57.zip`; `research/experiments/20261110T005514Z-h-092-exploration-bnb-usdt/raw/backtest-result-2026-11-10_01-11-03.zip`; `research/experiments/20261110T005514Z-h-092-exploration-xrp-usdt/raw/backtest-result-2026-11-10_01-14-51.zip`; `research/experiments/20261110T005514Z-h-092-exploration-ada-usdt/raw/backtest-result-2026-11-10_01-19-11.zip`; `research/experiments/20261110T005514Z-h-092-exploration-ltc-usdt/raw/backtest-result-2026-11-10_01-23-30.zip`; `research/experiments/20261110T005514Z-h-092-exploration-link-usdt/raw/backtest-result-2026-11-10_01-27-28.zip`; `research/experiments/20261110T005514Z-h-092-exploration-doge-usdt/raw/backtest-result-2026-11-10_01-31-22.zip`; `research/experiments/20261110T005514Z-h-092-exploration-sol-usdt/raw/backtest-result-2026-11-10_01-35-42.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 63; lucro líquido: -58.35.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 28 | -105.67 | – | -2.55% | 0% | 1.5 h |
| exit_signal | 28 | 7.44 | – | 0.18% | 50% | 4.7 h |
| take_profit_2R | 7 | 39.88 | – | 3.82% | 100% | 2.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 29 | -39.91 | -0.93% | 28% |
| 3 h a 1 dia | 34 | -18.44 | -0.38% | 38% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (21): MFE mediano 3.6%, MAE mediano -0.7%, devolução média do melhor ponto 1.8%, captura mediana 0.52.
- Perdedores (42): MAE mediano -2.0%, MFE mediano 0.7%; 4 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 27.65; – do lucro antes de custos.
- Trades < 3 h: 29 (lucro -39.91); reentradas em < 24 h: 7 (lucro 2.04).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -65.55.
- Lucro por ano de fechamento: 2017: 4.7, 2018: -20.9, 2019: -2.9, 2020: -12.8, 2021: -3.8, 2022: -24.9, 2023: 2.3.

## ETH/USDT

Trades: 119; lucro líquido: -141.59.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 65 | -220.87 | – | -2.41% | 0% | 1.6 h |
| exit_signal | 44 | 25.36 | – | 0.40% | 50% | 4.8 h |
| take_profit_2R | 10 | 53.92 | – | 3.79% | 100% | 1.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 67 | -124.37 | -1.32% | 18% |
| 3 h a 1 dia | 52 | -17.22 | -0.24% | 38% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (32): MFE mediano 3.7%, MAE mediano -0.7%, devolução média do melhor ponto 1.7%, captura mediana 0.51.
- Perdedores (87): MAE mediano -2.0%, MFE mediano 0.8%; 15 (17%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 49.70; – do lucro antes de custos.
- Trades < 3 h: 67 (lucro -124.37); reentradas em < 24 h: 16 (lucro -33.54).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -152.78.
- Lucro por ano de fechamento: 2017: -4.1, 2018: -44.9, 2019: 8.4, 2020: -26.5, 2021: -21.4, 2022: -53.3, 2023: 0.4.

## BNB/USDT

Trades: 119; lucro líquido: -127.55.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 62 | -250.85 | – | -2.83% | 0% | 1.0 h |
| exit_signal | 42 | 36.37 | – | 0.59% | 52% | 4.6 h |
| take_profit_2R | 14 | 101.83 | – | 5.09% | 100% | 1.6 h |
| stop_loss | 1 | -14.90 | – | -10.27% | 0% | 0.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 75 | -160.37 | -1.50% | 17% |
| 3 h a 1 dia | 44 | 32.82 | 0.51% | 52% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (36): MFE mediano 4.7%, MAE mediano -1.0%, devolução média do melhor ponto 2.2%, captura mediana 0.56.
- Perdedores (83): MAE mediano -2.4%, MFE mediano 1.0%; 16 (19%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 50.42; – do lucro antes de custos.
- Trades < 3 h: 75 (lucro -160.37); reentradas em < 24 h: 21 (lucro -12.06).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -140.60.
- Lucro por ano de fechamento: 2017: 13.2, 2018: -56.4, 2019: -5.5, 2020: -9.6, 2021: -37.3, 2022: -30.1, 2023: -0.8, 2024: -0.9.

## XRP/USDT

Trades: 100; lucro líquido: -104.14.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 47 | -187.14 | – | -2.81% | 0% | 0.7 h |
| exit_signal | 40 | -1.58 | – | -0.02% | 40% | 4.5 h |
| take_profit_2R | 13 | 84.59 | – | 4.63% | 100% | 2.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 58 | -129.28 | -1.57% | 16% |
| 3 h a 1 dia | 42 | 25.14 | 0.44% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (29): MFE mediano 4.4%, MAE mediano -0.7%, devolução média do melhor ponto 2.2%, captura mediana 0.60.
- Perdedores (71): MAE mediano -2.1%, MFE mediano 0.8%; 14 (20%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 42.08; – do lucro antes de custos.
- Trades < 3 h: 58 (lucro -129.28); reentradas em < 24 h: 12 (lucro -8.50).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -116.21.
- Lucro por ano de fechamento: 2018: -26.2, 2019: -11.3, 2020: 4.1, 2021: -63.1, 2022: -2.6, 2023: -1.3, 2024: -3.8.

## ADA/USDT

Trades: 124; lucro líquido: -103.27.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 60 | -193.70 | – | -2.25% | 0% | 1.3 h |
| exit_signal | 50 | 6.96 | – | 0.09% | 48% | 4.6 h |
| take_profit_2R | 14 | 83.47 | – | 4.17% | 100% | 1.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 69 | -82.61 | -0.84% | 22% |
| 3 h a 1 dia | 55 | -20.66 | -0.26% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (38): MFE mediano 3.7%, MAE mediano -0.9%, devolução média do melhor ponto 2.2%, captura mediana 0.55.
- Perdedores (86): MAE mediano -2.1%, MFE mediano 0.8%; 18 (21%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 53.02; – do lucro antes de custos.
- Trades < 3 h: 69 (lucro -82.61); reentradas em < 24 h: 15 (lucro -23.54).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -114.77.
- Lucro por ano de fechamento: 2018: -19.6, 2019: -0.1, 2020: -0.5, 2021: -41.1, 2022: -39.9, 2023: 5.9, 2024: -7.9.

## LTC/USDT

Trades: 140; lucro líquido: -70.68.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 60 | -207.48 | – | -2.40% | 0% | 1.3 h |
| exit_signal | 58 | 23.91 | – | 0.29% | 47% | 4.7 h |
| take_profit_2R | 21 | 127.77 | – | 4.26% | 100% | 1.6 h |
| stop_loss | 1 | -14.87 | – | -10.27% | 0% | 1.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 75 | -75.19 | -0.68% | 27% |
| 3 h a 1 dia | 65 | 4.51 | 0.05% | 43% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (48): MFE mediano 4.0%, MAE mediano -0.9%, devolução média do melhor ponto 1.9%, captura mediana 0.65.
- Perdedores (92): MAE mediano -1.9%, MFE mediano 1.1%; 24 (26%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 59.93; – do lucro antes de custos.
- Trades < 3 h: 75 (lucro -75.19); reentradas em < 24 h: 18 (lucro -33.48).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -82.03.
- Lucro por ano de fechamento: 2017: -16.6, 2018: -42.1, 2019: 16.4, 2020: 3.5, 2021: -3.5, 2022: -32.2, 2023: 8.8, 2024: -4.9.

## LINK/USDT

Trades: 173; lucro líquido: -144.44.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 89 | -308.08 | – | -2.43% | 0% | 1.5 h |
| exit_signal | 58 | 5.79 | – | 0.06% | 41% | 4.6 h |
| take_profit_2R | 26 | 157.85 | – | 4.22% | 100% | 2.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 96 | -131.14 | -0.97% | 21% |
| 3 h a 1 dia | 77 | -13.30 | -0.12% | 39% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (50): MFE mediano 4.7%, MAE mediano -1.0%, devolução média do melhor ponto 2.2%, captura mediana 0.63.
- Perdedores (123): MAE mediano -2.3%, MFE mediano 1.0%; 35 (28%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 73.17; – do lucro antes de custos.
- Trades < 3 h: 96 (lucro -131.14); reentradas em < 24 h: 29 (lucro -82.81).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -156.65.
- Lucro por ano de fechamento: 2019: -27.4, 2020: 7.7, 2021: -32.2, 2022: -74.6, 2023: -10.2, 2024: -7.8.

## DOGE/USDT

Trades: 100; lucro líquido: -37.73.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 50 | -195.20 | – | -2.59% | 0% | 1.0 h |
| exit_signal | 32 | 14.80 | – | 0.31% | 41% | 4.5 h |
| take_profit_2R | 16 | 174.18 | – | 7.28% | 100% | 2.0 h |
| stop_loss | 2 | -31.52 | – | -10.27% | 0% | 0.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 67 | -51.38 | -0.49% | 22% |
| 3 h a 1 dia | 33 | 13.64 | 0.27% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (29): MFE mediano 4.7%, MAE mediano -0.8%, devolução média do melhor ponto 4.2%, captura mediana 0.59.
- Perdedores (71): MAE mediano -2.2%, MFE mediano 1.0%; 12 (17%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 44.72; 640% do lucro antes de custos.
- Trades < 3 h: 67 (lucro -51.38); reentradas em < 24 h: 19 (lucro -50.51).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -97.79.
- Lucro por ano de fechamento: 2019: 3.1, 2020: -13.5, 2021: 0.1, 2022: -15.6, 2023: -4.6, 2024: -7.2.

## SOL/USDT

Trades: 179; lucro líquido: -140.69.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 91 | -329.65 | – | -2.52% | 0% | 1.2 h |
| exit_signal | 62 | 14.50 | – | 0.17% | 48% | 4.3 h |
| take_profit_2R | 25 | 188.47 | – | 5.18% | 100% | 2.1 h |
| stop_loss | 1 | -14.02 | – | -10.25% | 0% | 0.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 113 | -159.34 | -1.01% | 19% |
| 3 h a 1 dia | 66 | 18.65 | 0.23% | 52% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (55): MFE mediano 4.1%, MAE mediano -0.7%, devolução média do melhor ponto 2.3%, captura mediana 0.60.
- Perdedores (124): MAE mediano -2.2%, MFE mediano 1.1%; 28 (23%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 76.51; – do lucro antes de custos.
- Trades < 3 h: 113 (lucro -159.34); reentradas em < 24 h: 30 (lucro -12.04).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -171.17.
- Lucro por ano de fechamento: 2020: 18.0, 2021: -53.9, 2022: -76.7, 2023: -11.9, 2024: -16.2.
