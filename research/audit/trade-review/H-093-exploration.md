# Revisão de trades: H-093 (exploração)

Fonte dos trades: `research/experiments/20261110T034852Z-h-093-exploration-btc-usdt/raw/backtest-result-2026-11-10_03-58-28.zip`; `research/experiments/20261110T034852Z-h-093-exploration-eth-usdt/raw/backtest-result-2026-11-10_04-02-02.zip`; `research/experiments/20261110T034852Z-h-093-exploration-bnb-usdt/raw/backtest-result-2026-11-10_04-05-41.zip`; `research/experiments/20261110T034852Z-h-093-exploration-xrp-usdt/raw/backtest-result-2026-11-10_04-09-24.zip`; `research/experiments/20261110T034852Z-h-093-exploration-ada-usdt/raw/backtest-result-2026-11-10_04-12-55.zip`; `research/experiments/20261110T034852Z-h-093-exploration-ltc-usdt/raw/backtest-result-2026-11-10_04-16-30.zip`; `research/experiments/20261110T034852Z-h-093-exploration-link-usdt/raw/backtest-result-2026-11-10_04-19-55.zip`; `research/experiments/20261110T034852Z-h-093-exploration-doge-usdt/raw/backtest-result-2026-11-10_04-23-16.zip`; `research/experiments/20261110T034852Z-h-093-exploration-sol-usdt/raw/backtest-result-2026-11-10_04-26-21.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 364; lucro líquido: -166.28.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 193 | -324.41 | – | -1.84% | 0% | 2.3 h |
| td_time_exit | 94 | 22.70 | – | 0.27% | 54% | 8.0 h |
| td_take_profit | 75 | 141.62 | – | 2.07% | 100% | 3.7 h |
| stop_loss | 2 | -6.19 | – | -3.29% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 163 | -176.03 | -1.18% | 17% |
| 3 h a 1 dia | 201 | 9.75 | 0.05% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (126): MFE mediano 2.3%, MAE mediano -0.6%, devolução média do melhor ponto 1.1%, captura mediana 0.63.
- Perdedores (238): MAE mediano -1.7%, MFE mediano 0.5%; 16 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 98.66; – do lucro antes de custos.
- Trades < 3 h: 163 (lucro -176.03); reentradas em < 24 h: 84 (lucro -57.08).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -173.32.
- Lucro por ano de fechamento: 2017: -13.8, 2018: -61.5, 2019: -8.3, 2020: -14.0, 2021: -31.6, 2022: -23.8, 2023: -5.3, 2024: -8.0.

## ETH/USDT

Trades: 498; lucro líquido: -147.41.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 260 | -428.13 | – | -1.78% | 0% | 2.4 h |
| td_time_exit | 126 | 47.03 | – | 0.40% | 69% | 8.0 h |
| td_take_profit | 111 | 236.95 | – | 2.32% | 100% | 3.9 h |
| stop_loss | 1 | -3.26 | – | -3.29% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 213 | -200.60 | -1.01% | 19% |
| 3 h a 1 dia | 285 | 53.19 | 0.20% | 55% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (198): MFE mediano 2.4%, MAE mediano -0.5%, devolução média do melhor ponto 1.0%, captura mediana 0.64.
- Perdedores (300): MAE mediano -1.7%, MFE mediano 0.6%; 20 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 136.62; – do lucro antes de custos.
- Trades < 3 h: 213 (lucro -200.60); reentradas em < 24 h: 116 (lucro -26.98).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -155.20.
- Lucro por ano de fechamento: 2017: -14.5, 2018: -44.8, 2019: -31.3, 2020: -1.3, 2021: -10.3, 2022: -23.7, 2023: -10.5, 2024: -11.1.

## BNB/USDT

Trades: 528; lucro líquido: -184.82.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 281 | -456.87 | – | -1.82% | 0% | 2.3 h |
| td_time_exit | 126 | 33.11 | – | 0.30% | 58% | 8.0 h |
| td_take_profit | 120 | 242.19 | – | 2.30% | 100% | 3.8 h |
| stop_loss | 1 | -3.25 | – | -3.29% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 242 | -219.97 | -1.01% | 19% |
| 3 h a 1 dia | 286 | 35.16 | 0.15% | 52% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (193): MFE mediano 2.4%, MAE mediano -0.5%, devolução média do melhor ponto 1.0%, captura mediana 0.66.
- Perdedores (335): MAE mediano -1.8%, MFE mediano 0.6%; 30 (9%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 139.49; – do lucro antes de custos.
- Trades < 3 h: 242 (lucro -219.97); reentradas em < 24 h: 142 (lucro -35.85).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -191.99.
- Lucro por ano de fechamento: 2017: -9.3, 2018: -82.5, 2019: -21.7, 2020: -28.0, 2021: -19.9, 2022: -25.1, 2023: 4.1, 2024: -2.4.

## XRP/USDT

Trades: 410; lucro líquido: -98.56.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 202 | -354.10 | – | -1.85% | 0% | 2.6 h |
| td_time_exit | 108 | 35.75 | – | 0.35% | 65% | 8.0 h |
| td_take_profit | 100 | 219.79 | – | 2.32% | 100% | 3.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 164 | -145.62 | -0.94% | 22% |
| 3 h a 1 dia | 246 | 47.06 | 0.21% | 54% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (170): MFE mediano 2.5%, MAE mediano -0.5%, devolução média do melhor ponto 1.2%, captura mediana 0.61.
- Perdedores (240): MAE mediano -1.7%, MFE mediano 0.7%; 20 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 116.04; 664% do lucro antes de custos.
- Trades < 3 h: 164 (lucro -145.62); reentradas em < 24 h: 95 (lucro -19.96).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -105.71.
- Lucro por ano de fechamento: 2018: -25.7, 2019: -21.9, 2020: -17.9, 2021: 12.5, 2022: -34.8, 2023: -6.8, 2024: -3.8.

## ADA/USDT

Trades: 565; lucro líquido: -178.01.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 312 | -509.50 | – | -1.83% | 0% | 2.4 h |
| td_take_profit | 143 | 290.59 | – | 2.31% | 100% | 3.5 h |
| td_time_exit | 110 | 40.89 | – | 0.42% | 60% | 8.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 272 | -208.24 | -0.85% | 25% |
| 3 h a 1 dia | 293 | 30.23 | 0.13% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (209): MFE mediano 2.7%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.67.
- Perdedores (356): MAE mediano -1.7%, MFE mediano 0.6%; 32 (9%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 149.72; – do lucro antes de custos.
- Trades < 3 h: 272 (lucro -208.24); reentradas em < 24 h: 145 (lucro -24.23).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -183.08.
- Lucro por ano de fechamento: 2018: -86.0, 2019: -27.7, 2020: -2.2, 2021: -16.5, 2022: -29.0, 2023: -3.5, 2024: -13.2.

## LTC/USDT

Trades: 497; lucro líquido: -151.16.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 266 | -445.87 | – | -1.83% | 0% | 2.3 h |
| td_take_profit | 115 | 244.48 | – | 2.33% | 100% | 3.7 h |
| td_time_exit | 115 | 53.51 | – | 0.51% | 63% | 8.0 h |
| stop_loss | 1 | -3.27 | – | -3.29% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 225 | -202.10 | -0.97% | 20% |
| 3 h a 1 dia | 272 | 50.94 | 0.20% | 52% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (187): MFE mediano 2.7%, MAE mediano -0.6%, devolução média do melhor ponto 1.1%, captura mediana 0.66.
- Perdedores (310): MAE mediano -1.7%, MFE mediano 0.6%; 26 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 135.66; – do lucro antes de custos.
- Trades < 3 h: 225 (lucro -202.10); reentradas em < 24 h: 131 (lucro -34.10).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -157.91.
- Lucro por ano de fechamento: 2017: -1.5, 2018: -65.1, 2019: -16.2, 2020: -1.7, 2021: -19.7, 2022: -21.5, 2023: -20.6, 2024: -4.8.

## LINK/USDT

Trades: 573; lucro líquido: -185.96.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 324 | -521.84 | – | -1.81% | 0% | 2.2 h |
| td_take_profit | 149 | 303.60 | – | 2.32% | 100% | 3.4 h |
| td_time_exit | 99 | 35.44 | – | 0.41% | 53% | 8.0 h |
| stop_loss | 1 | -3.16 | – | -3.29% | 0% | 3.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 286 | -213.07 | -0.83% | 23% |
| 3 h a 1 dia | 287 | 27.11 | 0.11% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (201): MFE mediano 2.8%, MAE mediano -0.6%, devolução média do melhor ponto 1.0%, captura mediana 0.71.
- Perdedores (372): MAE mediano -1.8%, MFE mediano 0.7%; 31 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 151.49; – do lucro antes de custos.
- Trades < 3 h: 286 (lucro -213.07); reentradas em < 24 h: 168 (lucro -54.57).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -192.22.
- Lucro por ano de fechamento: 2019: -77.8, 2020: -49.5, 2021: -15.9, 2022: -4.8, 2023: -21.6, 2024: -16.5.

## DOGE/USDT

Trades: 367; lucro líquido: -91.87.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 191 | -333.41 | – | -1.82% | 0% | 2.6 h |
| td_time_exit | 99 | 44.51 | – | 0.46% | 68% | 8.0 h |
| td_take_profit | 76 | 200.13 | – | 2.75% | 100% | 3.5 h |
| stop_loss | 1 | -3.10 | – | -3.24% | 0% | 7.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 153 | -126.05 | -0.86% | 22% |
| 3 h a 1 dia | 214 | 34.18 | 0.17% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (143): MFE mediano 2.8%, MAE mediano -0.6%, devolução média do melhor ponto 1.4%, captura mediana 0.58.
- Perdedores (224): MAE mediano -1.7%, MFE mediano 0.7%; 18 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 105.38; 780% do lucro antes de custos.
- Trades < 3 h: 153 (lucro -126.05); reentradas em < 24 h: 91 (lucro -3.90).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -100.29.
- Lucro por ano de fechamento: 2019: -5.7, 2020: -17.4, 2021: -19.1, 2022: -33.0, 2023: 6.9, 2024: -23.6.

## SOL/USDT

Trades: 476; lucro líquido: -147.15.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 281 | -478.29 | – | -1.82% | 0% | 2.2 h |
| td_take_profit | 115 | 286.43 | – | 2.66% | 100% | 3.4 h |
| td_time_exit | 79 | 47.86 | – | 0.65% | 65% | 8.0 h |
| stop_loss | 1 | -3.15 | – | -3.29% | 0% | 0.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 263 | -225.35 | -0.92% | 21% |
| 3 h a 1 dia | 213 | 78.19 | 0.39% | 52% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (166): MFE mediano 3.1%, MAE mediano -0.6%, devolução média do melhor ponto 1.3%, captura mediana 0.67.
- Perdedores (310): MAE mediano -1.8%, MFE mediano 0.7%; 47 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 132.84; – do lucro antes de custos.
- Trades < 3 h: 263 (lucro -225.35); reentradas em < 24 h: 157 (lucro -35.48).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -156.44.
- Lucro por ano de fechamento: 2020: -32.6, 2021: -12.5, 2022: -59.8, 2023: -7.9, 2024: -34.3.
