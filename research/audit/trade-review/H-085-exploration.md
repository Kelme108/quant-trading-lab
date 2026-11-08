# Revisão de trades: H-085 (exploração)

Fonte dos trades: `research/experiments/20261108T155434Z-h-085-exploration-btc-usdt/raw/backtest-result-2026-11-08_16-02-01.zip`; `research/experiments/20261108T155434Z-h-085-exploration-eth-usdt/raw/backtest-result-2026-11-08_16-04-23.zip`; `research/experiments/20261108T155434Z-h-085-exploration-bnb-usdt/raw/backtest-result-2026-11-08_16-06-39.zip`; `research/experiments/20261108T155434Z-h-085-exploration-xrp-usdt/raw/backtest-result-2026-11-08_16-08-48.zip`; `research/experiments/20261108T155434Z-h-085-exploration-ada-usdt/raw/backtest-result-2026-11-08_16-10-57.zip`; `research/experiments/20261108T155434Z-h-085-exploration-ltc-usdt/raw/backtest-result-2026-11-08_16-13-09.zip`; `research/experiments/20261108T155434Z-h-085-exploration-link-usdt/raw/backtest-result-2026-11-08_16-15-17.zip`; `research/experiments/20261108T155434Z-h-085-exploration-doge-usdt/raw/backtest-result-2026-11-08_16-17-19.zip`; `research/experiments/20261108T155434Z-h-085-exploration-sol-usdt/raw/backtest-result-2026-11-08_16-19-19.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 554; lucro líquido: 243.36.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 354 | -872.84 | -359% | -1.41% | 11% | 11.8 h |
| take_profit_3pct | 149 | 1002.90 | 412% | 3.92% | 100% | 10.5 h |
| time_exit_24h | 51 | 113.30 | 47% | 1.27% | 94% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 41 | 11.17 | 0.25% | 41% |
| 3 h a 1 dia | 455 | 107.62 | 0.15% | 36% |
| 1 a 7 dias | 58 | 124.57 | 1.23% | 91% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (236): MFE mediano 4.3%, MAE mediano -0.6%, devolução média do melhor ponto 1.7%, captura mediana 0.65.
- Perdedores (318): MAE mediano -1.9%, MFE mediano 0.8%; 46 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 289.88; 54% do lucro antes de custos.
- Trades < 3 h: 41 (lucro 11.17); reentradas em < 24 h: 150 (lucro 163.78).
- Maior trade = 7% do lucro; top 5 = 29%; top 10 = 50%; lucro sem o melhor = 226.74.
- Lucro por ano de fechamento: 2017: 52.8, 2018: 41.0, 2019: 37.0, 2020: 48.7, 2021: 40.4, 2022: 17.9, 2023: -5.4, 2024: 10.9.

## ETH/USDT

Trades: 610; lucro líquido: -31.90.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 399 | -1115.54 | – | -1.92% | 8% | 10.9 h |
| take_profit_3pct | 182 | 1013.05 | – | 3.85% | 100% | 9.7 h |
| time_exit_24h | 29 | 70.59 | – | 1.67% | 97% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 34 | 2.87 | 0.08% | 44% |
| 3 h a 1 dia | 541 | -101.72 | -0.12% | 36% |
| 1 a 7 dias | 35 | 66.94 | 1.31% | 89% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (243): MFE mediano 4.7%, MAE mediano -0.7%, devolução média do melhor ponto 1.8%, captura mediana 0.69.
- Perdedores (367): MAE mediano -2.3%, MFE mediano 1.1%; 87 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 264.98; 114% do lucro antes de custos.
- Trades < 3 h: 34 (lucro 2.87); reentradas em < 24 h: 211 (lucro -85.32).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -41.60.
- Lucro por ano de fechamento: 2017: -17.5, 2018: -25.2, 2019: -24.0, 2020: 22.7, 2021: 39.6, 2022: -32.6, 2023: 18.1, 2024: -13.1.

## BNB/USDT

Trades: 555; lucro líquido: 264.43.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 342 | -1285.78 | -486% | -2.01% | 5% | 10.5 h |
| take_profit_3pct | 189 | 1486.07 | 562% | 4.31% | 100% | 7.9 h |
| time_exit_24h | 24 | 64.14 | 24% | 1.43% | 96% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 48 | 270.48 | 3.34% | 75% |
| 3 h a 1 dia | 478 | -80.40 | -0.08% | 35% |
| 1 a 7 dias | 29 | 74.35 | 1.37% | 90% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (230): MFE mediano 5.0%, MAE mediano -0.9%, devolução média do melhor ponto 2.2%, captura mediana 0.70.
- Perdedores (325): MAE mediano -2.4%, MFE mediano 1.2%; 83 (26%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 311.31; 54% do lucro antes de custos.
- Trades < 3 h: 48 (lucro 270.48); reentradas em < 24 h: 183 (lucro 126.34).
- Maior trade = 11% do lucro; top 5 = 44%; top 10 = 73%; lucro sem o melhor = 234.23.
- Lucro por ano de fechamento: 2017: 21.6, 2018: 176.4, 2019: 34.0, 2020: 14.0, 2021: 97.0, 2022: -69.1, 2023: -21.5, 2024: 12.2.

## XRP/USDT

Trades: 471; lucro líquido: -243.49.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 319 | -1225.36 | – | -2.64% | 5% | 9.3 h |
| take_profit_3pct | 142 | 956.47 | – | 4.54% | 100% | 7.3 h |
| time_exit_24h | 10 | 25.40 | – | 1.77% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 59 | 79.43 | 0.84% | 59% |
| 3 h a 1 dia | 397 | -353.95 | -0.63% | 30% |
| 1 a 7 dias | 15 | 31.03 | 1.42% | 93% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (169): MFE mediano 5.7%, MAE mediano -1.0%, devolução média do melhor ponto 2.7%, captura mediana 0.66.
- Perdedores (302): MAE mediano -3.0%, MFE mediano 1.0%; 66 (22%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 203.07; – do lucro antes de custos.
- Trades < 3 h: 59 (lucro 79.43); reentradas em < 24 h: 131 (lucro -57.30).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -271.06.
- Lucro por ano de fechamento: 2018: 48.7, 2019: -26.9, 2020: 27.4, 2021: -87.9, 2022: -58.1, 2023: -119.0, 2024: -27.7.

## ADA/USDT

Trades: 472; lucro líquido: 55.98.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 288 | -1066.22 | -1905% | -2.42% | 5% | 9.8 h |
| take_profit_3pct | 180 | 1112.55 | 1987% | 4.06% | 100% | 7.4 h |
| time_exit_24h | 4 | 9.65 | 17% | 1.52% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 46 | 211.11 | 2.94% | 83% |
| 3 h a 1 dia | 418 | -170.82 | -0.25% | 37% |
| 1 a 7 dias | 8 | 15.69 | 1.24% | 75% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (197): MFE mediano 5.3%, MAE mediano -1.0%, devolução média do melhor ponto 2.2%, captura mediana 0.70.
- Perdedores (275): MAE mediano -2.9%, MFE mediano 1.2%; 87 (32%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 216.61; 79% do lucro antes de custos.
- Trades < 3 h: 46 (lucro 211.11); reentradas em < 24 h: 151 (lucro -4.90).
- Maior trade = 25% do lucro; top 5 = 106%; top 10 = 195%; lucro sem o melhor = 41.93.
- Lucro por ano de fechamento: 2018: -58.5, 2019: -32.6, 2020: 73.0, 2021: 102.8, 2022: -2.7, 2023: 0.2, 2024: -26.2.

## LTC/USDT

Trades: 501; lucro líquido: -138.69.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 331 | -1120.22 | – | -2.28% | 5% | 10.6 h |
| take_profit_3pct | 154 | 952.43 | – | 4.16% | 100% | 8.2 h |
| time_exit_24h | 16 | 29.10 | – | 1.26% | 94% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 41 | 35.68 | 0.56% | 59% |
| 3 h a 1 dia | 439 | -202.90 | -0.31% | 33% |
| 1 a 7 dias | 21 | 28.52 | 0.95% | 81% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (187): MFE mediano 5.0%, MAE mediano -0.7%, devolução média do melhor ponto 2.0%, captura mediana 0.70.
- Perdedores (314): MAE mediano -2.6%, MFE mediano 1.2%; 84 (27%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 220.14; 270% do lucro antes de custos.
- Trades < 3 h: 41 (lucro 35.68); reentradas em < 24 h: 140 (lucro -58.28).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -155.58.
- Lucro por ano de fechamento: 2018: 22.3, 2019: 25.0, 2020: 6.7, 2021: -133.0, 2022: -6.9, 2023: -21.7, 2024: -31.1.

## LINK/USDT

Trades: 458; lucro líquido: 49.22.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 277 | -1130.63 | -2297% | -2.58% | 5% | 9.9 h |
| take_profit_3pct | 171 | 1164.65 | 2366% | 4.34% | 100% | 8.1 h |
| time_exit_24h | 10 | 15.19 | 31% | 0.95% | 90% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 36 | 76.64 | 1.42% | 64% |
| 3 h a 1 dia | 411 | -47.97 | -0.07% | 39% |
| 1 a 7 dias | 11 | 20.55 | 1.17% | 91% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (195): MFE mediano 5.3%, MAE mediano -1.2%, devolução média do melhor ponto 2.3%, captura mediana 0.67.
- Perdedores (263): MAE mediano -3.1%, MFE mediano 1.3%; 99 (38%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 217.68; 82% do lucro antes de custos.
- Trades < 3 h: 36 (lucro 76.64); reentradas em < 24 h: 144 (lucro -2.25).
- Maior trade = 54% do lucro; top 5 = 172%; top 10 = 293%; lucro sem o melhor = 22.75.
- Lucro por ano de fechamento: 2019: 1.7, 2020: 99.4, 2021: -28.7, 2022: 8.8, 2023: -35.2, 2024: 3.3.

## DOGE/USDT

Trades: 355; lucro líquido: 132.07.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 221 | -1052.93 | -797% | -2.66% | 4% | 9.2 h |
| take_profit_3pct | 133 | 1183.05 | 896% | 5.07% | 100% | 6.5 h |
| time_exit_24h | 1 | 1.95 | 1% | 1.14% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 52 | 277.54 | 3.01% | 67% |
| 3 h a 1 dia | 302 | -147.43 | -0.23% | 35% |
| 1 a 7 dias | 1 | 1.95 | 1.14% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (142): MFE mediano 6.7%, MAE mediano -1.2%, devolução média do melhor ponto 5.0%, captura mediana 0.62.
- Perdedores (213): MAE mediano -3.0%, MFE mediano 1.3%; 60 (28%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 187.03; 59% do lucro antes de custos.
- Trades < 3 h: 52 (lucro 277.54); reentradas em < 24 h: 109 (lucro 46.78).
- Maior trade = 47% do lucro; top 5 = 113%; top 10 = 170%; lucro sem o melhor = 70.63.
- Lucro por ano de fechamento: 2019: 7.6, 2020: 47.4, 2021: 236.8, 2022: -77.9, 2023: -73.4, 2024: -8.4.

## SOL/USDT

Trades: 346; lucro líquido: 17.99.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 196 | -921.94 | -5125% | -3.12% | 3% | 9.0 h |
| take_profit_3pct | 145 | 929.86 | 5169% | 4.29% | 100% | 7.5 h |
| time_exit_24h | 5 | 10.07 | 56% | 1.32% | 80% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 41 | 121.52 | 2.02% | 71% |
| 3 h a 1 dia | 298 | -118.34 | -0.26% | 40% |
| 1 a 7 dias | 7 | 14.81 | 1.39% | 86% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (154): MFE mediano 5.4%, MAE mediano -1.3%, devolução média do melhor ponto 2.1%, captura mediana 0.71.
- Perdedores (192): MAE mediano -3.9%, MFE mediano 1.4%; 65 (34%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 156.36; 90% do lucro antes de custos.
- Trades < 3 h: 41 (lucro 121.52); reentradas em < 24 h: 115 (lucro -52.20).
- Maior trade = 93% do lucro; top 5 = 377%; top 10 = 678%; lucro sem o melhor = 1.23.
- Lucro por ano de fechamento: 2020: -13.9, 2021: 13.9, 2022: -4.1, 2023: 82.8, 2024: -60.7.
