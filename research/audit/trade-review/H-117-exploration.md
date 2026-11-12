# Revisão de trades: H-117 (exploração)

Fonte dos trades: `research/experiments/20261112T045600Z-h-117-exploration-btc-usdt/raw/backtest-result-2026-11-12_05-31-44.zip`; `research/experiments/20261112T045600Z-h-117-exploration-eth-usdt/raw/backtest-result-2026-11-12_05-43-32.zip`; `research/experiments/20261112T045600Z-h-117-exploration-bnb-usdt/raw/backtest-result-2026-11-12_05-57-08.zip`; `research/experiments/20261112T045600Z-h-117-exploration-xrp-usdt/raw/backtest-result-2026-11-12_06-09-19.zip`; `research/experiments/20261112T045600Z-h-117-exploration-ada-usdt/raw/backtest-result-2026-11-12_06-21-50.zip`; `research/experiments/20261112T045600Z-h-117-exploration-ltc-usdt/raw/backtest-result-2026-11-12_06-36-23.zip`; `research/experiments/20261112T045600Z-h-117-exploration-link-usdt/raw/backtest-result-2026-11-12_06-51-15.zip`; `research/experiments/20261112T045600Z-h-117-exploration-doge-usdt/raw/backtest-result-2026-11-12_07-04-08.zip`; `research/experiments/20261112T045600Z-h-117-exploration-sol-usdt/raw/backtest-result-2026-11-12_07-15-32.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 880; lucro líquido: -125.08.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 524 | -342.08 | – | -1.38% | 0% | 3.3 h |
| take_profit_2r | 186 | 209.52 | – | 2.35% | 100% | 5.1 h |
| time_exit_12h | 170 | 7.49 | – | 0.09% | 51% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 368 | -132.96 | -0.77% | 16% |
| 3 h a 1 dia | 512 | 7.88 | 0.03% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (273): MFE mediano 2.6%, MAE mediano -0.4%, devolução média do melhor ponto 1.0%, captura mediana 0.68.
- Perdedores (607): MAE mediano -1.2%, MFE mediano 0.5%; 22 (4%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 124.61; – do lucro antes de custos.
- Trades < 3 h: 368 (lucro -132.96); reentradas em < 24 h: 303 (lucro -60.55).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -130.55.
- Lucro por ano de fechamento: 2017: 15.0, 2018: -23.2, 2019: -19.6, 2020: -12.5, 2021: -46.0, 2022: -21.5, 2023: -12.3, 2024: -5.0.

## ETH/USDT

Trades: 1228; lucro líquido: -147.26.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 762 | -498.94 | – | -1.40% | 0% | 2.8 h |
| take_profit_2r | 300 | 339.68 | – | 2.42% | 100% | 4.5 h |
| time_exit_12h | 166 | 12.00 | – | 0.15% | 55% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 600 | -195.84 | -0.70% | 18% |
| 3 h a 1 dia | 628 | 48.58 | 0.16% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (391): MFE mediano 2.8%, MAE mediano -0.4%, devolução média do melhor ponto 1.0%, captura mediana 0.70.
- Perdedores (837): MAE mediano -1.3%, MFE mediano 0.5%; 45 (5%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 170.72; 728% do lucro antes de custos.
- Trades < 3 h: 600 (lucro -195.84); reentradas em < 24 h: 553 (lucro -57.75).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -151.24.
- Lucro por ano de fechamento: 2017: -18.7, 2018: -5.1, 2019: -24.6, 2020: -22.0, 2021: -18.7, 2022: -33.9, 2023: -18.7, 2024: -5.5.

## BNB/USDT

Trades: 1137; lucro líquido: -99.71.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 685 | -491.03 | – | -1.50% | 0% | 2.4 h |
| take_profit_2r | 310 | 381.26 | – | 2.58% | 100% | 4.0 h |
| time_exit_12h | 141 | 15.13 | – | 0.23% | 53% | 12.0 h |
| stop_loss | 1 | -5.07 | – | -10.27% | 0% | 0.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 619 | -155.98 | -0.53% | 24% |
| 3 h a 1 dia | 518 | 56.26 | 0.23% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (385): MFE mediano 2.8%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.72.
- Perdedores (752): MAE mediano -1.3%, MFE mediano 0.7%; 60 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 161.67; 261% do lucro antes de custos.
- Trades < 3 h: 619 (lucro -155.98); reentradas em < 24 h: 481 (lucro -69.83).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -111.15.
- Lucro por ano de fechamento: 2017: -22.6, 2018: -19.0, 2019: -0.9, 2020: -2.1, 2021: -12.6, 2022: -18.7, 2023: -14.0, 2024: -9.8.

## XRP/USDT

Trades: 1047; lucro líquido: -185.05.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 678 | -466.75 | – | -1.51% | 0% | 2.6 h |
| take_profit_2r | 235 | 282.91 | – | 2.62% | 100% | 4.4 h |
| time_exit_12h | 133 | 3.64 | – | 0.06% | 52% | 12.0 h |
| stop_loss | 1 | -4.84 | – | -10.27% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 565 | -199.24 | -0.77% | 18% |
| 3 h a 1 dia | 482 | 14.19 | 0.06% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (304): MFE mediano 2.8%, MAE mediano -0.5%, devolução média do melhor ponto 1.2%, captura mediana 0.67.
- Perdedores (743): MAE mediano -1.3%, MFE mediano 0.6%; 59 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 142.74; – do lucro antes de custos.
- Trades < 3 h: 565 (lucro -199.24); reentradas em < 24 h: 424 (lucro -81.10).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -192.70.
- Lucro por ano de fechamento: 2018: -14.2, 2019: -29.5, 2020: -36.9, 2021: -42.5, 2022: -28.1, 2023: -23.8, 2024: -10.2.

## ADA/USDT

Trades: 1249; lucro líquido: -172.13.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 830 | -537.15 | – | -1.41% | 0% | 2.5 h |
| take_profit_2r | 316 | 360.87 | – | 2.49% | 100% | 3.8 h |
| time_exit_12h | 102 | 8.92 | – | 0.20% | 52% | 12.0 h |
| stop_loss | 1 | -4.77 | – | -10.27% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 726 | -190.08 | -0.57% | 22% |
| 3 h a 1 dia | 523 | 17.95 | 0.07% | 41% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (369): MFE mediano 2.9%, MAE mediano -0.4%, devolução média do melhor ponto 1.1%, captura mediana 0.71.
- Perdedores (880): MAE mediano -1.3%, MFE mediano 0.7%; 60 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 170.49; – do lucro antes de custos.
- Trades < 3 h: 726 (lucro -190.08); reentradas em < 24 h: 567 (lucro -59.90).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -178.16.
- Lucro por ano de fechamento: 2018: -37.1, 2019: -22.2, 2020: -26.8, 2021: -24.7, 2022: -28.1, 2023: -22.8, 2024: -10.4.

## LTC/USDT

Trades: 1355; lucro líquido: -250.08.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 935 | -586.55 | – | -1.44% | 0% | 2.7 h |
| take_profit_2r | 298 | 327.65 | – | 2.52% | 100% | 3.9 h |
| time_exit_12h | 122 | 8.82 | – | 0.17% | 59% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 761 | -226.89 | -0.69% | 19% |
| 3 h a 1 dia | 594 | -23.19 | -0.09% | 38% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (370): MFE mediano 3.0%, MAE mediano -0.4%, devolução média do melhor ponto 1.2%, captura mediana 0.69.
- Perdedores (985): MAE mediano -1.3%, MFE mediano 0.7%; 75 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 174.97; – do lucro antes de custos.
- Trades < 3 h: 761 (lucro -226.89); reentradas em < 24 h: 634 (lucro -149.54).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -254.13.
- Lucro por ano de fechamento: 2017: -10.0, 2018: -45.8, 2019: -54.9, 2020: -36.0, 2021: -33.4, 2022: -28.8, 2023: -29.7, 2024: -11.4.

## LINK/USDT

Trades: 1279; lucro líquido: -168.64.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 863 | -585.39 | – | -1.47% | 0% | 2.1 h |
| take_profit_2r | 353 | 411.33 | – | 2.53% | 100% | 3.6 h |
| time_exit_12h | 63 | 5.41 | – | 0.20% | 62% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 835 | -212.95 | -0.55% | 23% |
| 3 h a 1 dia | 444 | 44.30 | 0.21% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (392): MFE mediano 3.1%, MAE mediano -0.4%, devolução média do melhor ponto 1.1%, captura mediana 0.71.
- Perdedores (887): MAE mediano -1.4%, MFE mediano 0.6%; 84 (9%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 175.61; 2519% do lucro antes de custos.
- Trades < 3 h: 835 (lucro -212.95); reentradas em < 24 h: 660 (lucro -119.95).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -174.03.
- Lucro por ano de fechamento: 2019: -51.9, 2020: -22.7, 2021: -16.1, 2022: -25.4, 2023: -28.9, 2024: -23.6.

## DOGE/USDT

Trades: 1058; lucro líquido: -162.67.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 689 | -491.80 | – | -1.55% | 0% | 2.3 h |
| take_profit_2r | 231 | 322.61 | – | 3.02% | 100% | 4.0 h |
| time_exit_12h | 136 | 16.30 | – | 0.26% | 60% | 12.0 h |
| stop_loss | 2 | -9.78 | – | -10.27% | 0% | 0.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 614 | -187.81 | -0.66% | 19% |
| 3 h a 1 dia | 444 | 25.14 | 0.12% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (313): MFE mediano 3.1%, MAE mediano -0.4%, devolução média do melhor ponto 1.4%, captura mediana 0.63.
- Perdedores (745): MAE mediano -1.3%, MFE mediano 0.6%; 81 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 146.07; – do lucro antes de custos.
- Trades < 3 h: 614 (lucro -187.81); reentradas em < 24 h: 522 (lucro -71.67).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -172.60.
- Lucro por ano de fechamento: 2019: -28.9, 2020: -27.9, 2021: -14.0, 2022: -47.7, 2023: -29.4, 2024: -14.7.

## SOL/USDT

Trades: 1041; lucro líquido: -121.30.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 722 | -520.55 | – | -1.51% | 0% | 1.9 h |
| take_profit_2r | 285 | 387.00 | – | 2.82% | 100% | 3.1 h |
| time_exit_12h | 34 | 12.25 | – | 0.75% | 65% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 725 | -164.92 | -0.48% | 23% |
| 3 h a 1 dia | 316 | 43.62 | 0.29% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (307): MFE mediano 3.2%, MAE mediano -0.4%, devolução média do melhor ponto 1.2%, captura mediana 0.72.
- Perdedores (734): MAE mediano -1.4%, MFE mediano 0.7%; 100 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 148.55; 545% do lucro antes de custos.
- Trades < 3 h: 725 (lucro -164.92); reentradas em < 24 h: 586 (lucro -63.19).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -132.51.
- Lucro por ano de fechamento: 2020: -4.3, 2021: -22.8, 2022: -50.7, 2023: -20.4, 2024: -23.1.
