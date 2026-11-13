# Revisão de trades: H-100 (exploração)

Fonte dos trades: `research/experiments/20261113T113655Z-h-100-exploration-btc-usdt/raw/backtest-result-2026-11-13_12-01-04.zip`; `research/experiments/20261113T113655Z-h-100-exploration-eth-usdt/raw/backtest-result-2026-11-13_12-05-41.zip`; `research/experiments/20261113T113655Z-h-100-exploration-bnb-usdt/raw/backtest-result-2026-11-13_12-10-05.zip`; `research/experiments/20261113T113655Z-h-100-exploration-xrp-usdt/raw/backtest-result-2026-11-13_12-15-16.zip`; `research/experiments/20261113T113655Z-h-100-exploration-ada-usdt/raw/backtest-result-2026-11-13_12-20-15.zip`; `research/experiments/20261113T113655Z-h-100-exploration-ltc-usdt/raw/backtest-result-2026-11-13_12-26-41.zip`; `research/experiments/20261113T113655Z-h-100-exploration-link-usdt/raw/backtest-result-2026-11-13_12-33-41.zip`; `research/experiments/20261113T113655Z-h-100-exploration-doge-usdt/raw/backtest-result-2026-11-13_12-40-51.zip`; `research/experiments/20261113T113655Z-h-100-exploration-sol-usdt/raw/backtest-result-2026-11-13_12-46-56.zip`; `research/experiments/20261113T113655Z-h-100-exploration-avax-usdt/raw/backtest-result-2026-11-13_12-53-28.zip`; `research/experiments/20261113T113655Z-h-100-exploration-dot-usdt/raw/backtest-result-2026-11-13_12-59-35.zip`; `research/experiments/20261113T113655Z-h-100-exploration-trx-usdt/raw/backtest-result-2026-11-13_13-03-42.zip`; `research/experiments/20261113T113655Z-h-100-exploration-near-usdt/raw/backtest-result-2026-11-13_13-07-31.zip`; `research/experiments/20261113T113655Z-h-100-exploration-uni-usdt/raw/backtest-result-2026-11-13_13-11-44.zip`; `research/experiments/20261113T113655Z-h-100-exploration-bch-usdt/raw/backtest-result-2026-11-13_13-15-49.zip`; `research/experiments/20261113T113655Z-h-100-exploration-xlm-usdt/raw/backtest-result-2026-11-13_13-20-12.zip`; `research/experiments/20261113T113655Z-h-100-exploration-fil-usdt/raw/backtest-result-2026-11-13_13-23-59.zip`; `research/experiments/20261113T113655Z-h-100-exploration-aave-usdt/raw/backtest-result-2026-11-13_13-27-46.zip`; `research/experiments/20261113T113655Z-h-100-exploration-inj-usdt/raw/backtest-result-2026-11-13_13-31-33.zip`; `research/experiments/20261113T113655Z-h-100-exploration-hbar-usdt/raw/backtest-result-2026-11-13_13-35-28.zip`; `research/experiments/20261113T113655Z-h-100-exploration-op-usdt/raw/backtest-result-2026-11-13_13-39-46.zip`; `research/experiments/20261113T113655Z-h-100-exploration-apt-usdt/raw/backtest-result-2026-11-13_13-44-02.zip`; `research/experiments/20261113T113655Z-h-100-exploration-arb-usdt/raw/backtest-result-2026-11-13_13-47-38.zip`; `research/experiments/20261113T113655Z-h-100-exploration-sui-usdt/raw/backtest-result-2026-11-13_13-51-01.zip`; `research/experiments/20261113T113655Z-h-100-exploration-atom-usdt/raw/backtest-result-2026-11-13_13-55-08.zip`; `research/experiments/20261113T113655Z-h-100-exploration-etc-usdt/raw/backtest-result-2026-11-13_13-58-51.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 321; lucro líquido: 74.80.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 208 | -464.14 | -621% | -1.42% | 12% | 12.6 h |
| take_profit_3pct | 78 | 474.81 | 635% | 3.89% | 100% | 10.4 h |
| time_exit_24h | 35 | 64.14 | 86% | 1.17% | 89% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 20 | -3.14 | -0.08% | 40% |
| 3 h a 1 dia | 260 | 6.53 | 0.02% | 35% |
| 1 a 7 dias | 41 | 71.41 | 1.11% | 88% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (135): MFE mediano 4.2%, MAE mediano -0.5%, devolução média do melhor ponto 1.8%, captura mediana 0.63.
- Perdedores (186): MAE mediano -1.8%, MFE mediano 0.8%; 24 (13%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 151.36; 67% do lucro antes de custos.
- Trades < 3 h: 20 (lucro -3.14); reentradas em < 24 h: 44 (lucro 44.10).
- Maior trade = 21% do lucro; top 5 = 76%; top 10 = 128%; lucro sem o melhor = 58.99.
- Lucro por ano de fechamento: 2017: -2.4, 2018: 55.9, 2019: -29.8, 2020: 16.2, 2021: 20.0, 2022: 14.5, 2023: -18.1, 2024: 18.6.

## ETH/USDT

Trades: 344; lucro líquido: 232.83.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 204 | -584.78 | -251% | -1.71% | 11% | 12.2 h |
| take_profit_3pct | 117 | 750.69 | 322% | 3.86% | 100% | 9.8 h |
| time_exit_24h | 23 | 66.93 | 29% | 1.70% | 96% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 17 | -2.67 | -0.00% | 41% |
| 3 h a 1 dia | 296 | 171.64 | 0.35% | 43% |
| 1 a 7 dias | 31 | 63.86 | 1.21% | 87% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (161): MFE mediano 4.6%, MAE mediano -0.6%, devolução média do melhor ponto 1.8%, captura mediana 0.69.
- Perdedores (183): MAE mediano -2.2%, MFE mediano 1.1%; 48 (26%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 174.36; 43% do lucro antes de custos.
- Trades < 3 h: 17 (lucro -2.67); reentradas em < 24 h: 59 (lucro -4.11).
- Maior trade = 5% do lucro; top 5 = 23%; top 10 = 43%; lucro sem o melhor = 220.83.
- Lucro por ano de fechamento: 2017: 5.6, 2018: 1.0, 2019: 30.5, 2020: 82.8, 2021: 73.0, 2022: -1.2, 2023: 34.2, 2024: 7.0.

## BNB/USDT

Trades: 297; lucro líquido: 231.39.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 172 | -691.82 | -299% | -2.16% | 4% | 11.1 h |
| take_profit_3pct | 113 | 891.91 | 385% | 4.39% | 100% | 7.8 h |
| time_exit_24h | 12 | 31.31 | 14% | 1.40% | 92% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 37 | 209.30 | 3.46% | 78% |
| 3 h a 1 dia | 245 | -20.01 | -0.04% | 36% |
| 1 a 7 dias | 15 | 42.11 | 1.51% | 93% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (131): MFE mediano 5.2%, MAE mediano -0.8%, devolução média do melhor ponto 2.0%, captura mediana 0.72.
- Perdedores (166): MAE mediano -2.7%, MFE mediano 1.3%; 42 (25%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 165.50; 42% do lucro antes de custos.
- Trades < 3 h: 37 (lucro 209.30); reentradas em < 24 h: 51 (lucro -38.78).
- Maior trade = 13% do lucro; top 5 = 41%; top 10 = 70%; lucro sem o melhor = 201.65.
- Lucro por ano de fechamento: 2017: 6.1, 2018: 209.7, 2019: 58.5, 2020: 0.3, 2021: 26.3, 2022: -35.1, 2023: -36.5, 2024: 2.1.

## XRP/USDT

Trades: 306; lucro líquido: -209.66.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 202 | -852.57 | – | -2.92% | 5% | 9.2 h |
| take_profit_3pct | 99 | 628.49 | – | 4.31% | 100% | 7.3 h |
| time_exit_24h | 5 | 14.42 | – | 1.96% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 40 | 61.13 | 0.99% | 62% |
| 3 h a 1 dia | 257 | -293.10 | -0.81% | 31% |
| 1 a 7 dias | 9 | 22.31 | 1.68% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (114): MFE mediano 5.8%, MAE mediano -1.0%, devolução média do melhor ponto 2.8%, captura mediana 0.64.
- Perdedores (192): MAE mediano -3.2%, MFE mediano 1.0%; 47 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 131.82; – do lucro antes de custos.
- Trades < 3 h: 40 (lucro 61.13); reentradas em < 24 h: 58 (lucro -71.28).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -224.18.
- Lucro por ano de fechamento: 2018: 31.1, 2019: -21.4, 2020: 56.5, 2021: -128.1, 2022: -33.5, 2023: -83.3, 2024: -30.9.

## ADA/USDT

Trades: 295; lucro líquido: -7.69.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 179 | -711.05 | – | -2.57% | 4% | 10.5 h |
| take_profit_3pct | 113 | 696.36 | – | 4.02% | 100% | 7.7 h |
| time_exit_24h | 3 | 6.99 | – | 1.51% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 25 | 115.81 | 2.95% | 88% |
| 3 h a 1 dia | 264 | -131.13 | -0.31% | 37% |
| 1 a 7 dias | 6 | 7.63 | 0.85% | 67% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (124): MFE mediano 5.5%, MAE mediano -1.2%, devolução média do melhor ponto 2.3%, captura mediana 0.67.
- Perdedores (171): MAE mediano -3.1%, MFE mediano 1.2%; 57 (33%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 136.29; 106% do lucro antes de custos.
- Trades < 3 h: 25 (lucro 115.81); reentradas em < 24 h: 61 (lucro -27.42).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -19.48.
- Lucro por ano de fechamento: 2018: -26.3, 2019: 8.1, 2020: 45.4, 2021: 31.7, 2022: -5.1, 2023: -38.1, 2024: -23.4.

## LTC/USDT

Trades: 325; lucro líquido: -20.47.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 204 | -762.05 | – | -2.39% | 6% | 11.0 h |
| take_profit_3pct | 112 | 727.12 | – | 4.17% | 100% | 8.2 h |
| time_exit_24h | 9 | 14.46 | – | 1.03% | 89% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 33 | 36.17 | 0.73% | 64% |
| 3 h a 1 dia | 279 | -72.18 | -0.16% | 36% |
| 1 a 7 dias | 13 | 15.54 | 0.77% | 77% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (132): MFE mediano 5.4%, MAE mediano -0.8%, devolução média do melhor ponto 2.1%, captura mediana 0.69.
- Perdedores (193): MAE mediano -2.8%, MFE mediano 1.2%; 47 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 151.56; 116% do lucro antes de custos.
- Trades < 3 h: 33 (lucro 36.17); reentradas em < 24 h: 59 (lucro -36.88).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -39.49.
- Lucro por ano de fechamento: 2018: 48.3, 2019: 17.5, 2020: 7.3, 2021: -46.3, 2022: -9.6, 2023: -14.1, 2024: -23.5.

## LINK/USDT

Trades: 285; lucro líquido: 105.48.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 167 | -679.17 | -644% | -2.56% | 5% | 10.7 h |
| take_profit_3pct | 114 | 781.41 | 741% | 4.35% | 100% | 8.0 h |
| time_exit_24h | 4 | 3.24 | 3% | 0.48% | 75% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 27 | 89.55 | 2.11% | 70% |
| 3 h a 1 dia | 253 | 12.81 | 0.04% | 41% |
| 1 a 7 dias | 5 | 3.13 | 0.37% | 60% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (125): MFE mediano 5.6%, MAE mediano -1.4%, devolução média do melhor ponto 2.4%, captura mediana 0.67.
- Perdedores (160): MAE mediano -3.2%, MFE mediano 1.7%; 65 (41%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 136.59; 56% do lucro antes de custos.
- Trades < 3 h: 27 (lucro 89.55); reentradas em < 24 h: 56 (lucro -5.77).
- Maior trade = 15% do lucro; top 5 = 68%; top 10 = 120%; lucro sem o melhor = 89.41.
- Lucro por ano de fechamento: 2019: 30.6, 2020: 21.3, 2021: 41.0, 2022: 9.0, 2023: -9.9, 2024: 13.6.

## DOGE/USDT

Trades: 264; lucro líquido: 120.52.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 164 | -784.60 | -651% | -2.72% | 4% | 9.2 h |
| take_profit_3pct | 99 | 901.71 | 748% | 5.29% | 100% | 6.5 h |
| time_exit_24h | 1 | 3.41 | 3% | 2.22% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 39 | 247.97 | 3.68% | 72% |
| 3 h a 1 dia | 224 | -130.86 | -0.29% | 34% |
| 1 a 7 dias | 1 | 3.41 | 2.22% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (106): MFE mediano 7.0%, MAE mediano -1.3%, devolução média do melhor ponto 5.3%, captura mediana 0.59.
- Perdedores (158): MAE mediano -3.3%, MFE mediano 1.3%; 44 (28%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 136.73; 53% do lucro antes de custos.
- Trades < 3 h: 39 (lucro 247.97); reentradas em < 24 h: 68 (lucro 108.37).
- Maior trade = 51% do lucro; top 5 = 122%; top 10 = 182%; lucro sem o melhor = 58.90.
- Lucro por ano de fechamento: 2019: -7.4, 2020: 65.3, 2021: 209.1, 2022: -57.7, 2023: -82.5, 2024: -6.3.

## SOL/USDT

Trades: 206; lucro líquido: 94.55.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 110 | -555.14 | -587% | -3.15% | 4% | 10.0 h |
| take_profit_3pct | 93 | 643.38 | 680% | 4.37% | 100% | 7.1 h |
| time_exit_24h | 3 | 6.31 | 7% | 1.28% | 67% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 26 | 98.79 | 2.49% | 77% |
| 3 h a 1 dia | 176 | -15.45 | -0.05% | 43% |
| 1 a 7 dias | 4 | 11.22 | 1.73% | 75% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (99): MFE mediano 5.6%, MAE mediano -1.1%, devolução média do melhor ponto 2.3%, captura mediana 0.70.
- Perdedores (107): MAE mediano -3.9%, MFE mediano 1.5%; 36 (34%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 98.85; 51% do lucro antes de custos.
- Trades < 3 h: 26 (lucro 98.79); reentradas em < 24 h: 47 (lucro -32.53).
- Maior trade = 16% do lucro; top 5 = 69%; top 10 = 125%; lucro sem o melhor = 79.64.
- Lucro por ano de fechamento: 2020: -3.4, 2021: 69.3, 2022: 1.4, 2023: 45.4, 2024: -18.2.

## AVAX/USDT

Trades: 195; lucro líquido: -91.66.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 119 | -556.89 | – | -3.23% | 3% | 10.1 h |
| take_profit_3pct | 73 | 464.63 | – | 4.43% | 100% | 5.9 h |
| time_exit_24h | 3 | 0.61 | – | 0.11% | 67% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 24 | 131.98 | 3.72% | 83% |
| 3 h a 1 dia | 168 | -224.25 | -0.90% | 33% |
| 1 a 7 dias | 3 | 0.61 | 0.11% | 67% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (78): MFE mediano 5.3%, MAE mediano -1.2%, devolução média do melhor ponto 2.6%, captura mediana 0.70.
- Perdedores (117): MAE mediano -3.7%, MFE mediano 1.4%; 42 (36%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 83.31; – do lucro antes de custos.
- Trades < 3 h: 24 (lucro 131.98); reentradas em < 24 h: 41 (lucro 3.59).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -119.56.
- Lucro por ano de fechamento: 2020: -47.8, 2021: 40.8, 2022: -78.0, 2023: -1.9, 2024: -4.8.

## DOT/USDT

Trades: 175; lucro líquido: -127.22.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 119 | -438.17 | – | -2.56% | 7% | 10.8 h |
| take_profit_3pct | 52 | 305.17 | – | 4.07% | 100% | 7.3 h |
| time_exit_24h | 4 | 5.77 | – | 1.10% | 75% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 17 | 58.33 | 2.33% | 76% |
| 3 h a 1 dia | 152 | -192.87 | -0.88% | 30% |
| 1 a 7 dias | 6 | 7.31 | 0.92% | 83% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (63): MFE mediano 5.2%, MAE mediano -0.9%, devolução média do melhor ponto 2.1%, captura mediana 0.69.
- Perdedores (112): MAE mediano -3.1%, MFE mediano 1.3%; 35 (31%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 74.44; – do lucro antes de custos.
- Trades < 3 h: 17 (lucro 58.33); reentradas em < 24 h: 35 (lucro -90.68).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -138.37.
- Lucro por ano de fechamento: 2020: 15.3, 2021: -60.9, 2022: -26.0, 2023: -25.9, 2024: -29.7.

## TRX/USDT

Trades: 273; lucro líquido: 81.79.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 172 | -644.98 | -789% | -2.31% | 6% | 9.7 h |
| take_profit_3pct | 87 | 701.29 | 857% | 5.03% | 100% | 8.5 h |
| time_exit_24h | 14 | 25.48 | 31% | 1.12% | 86% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 30 | 47.99 | 0.96% | 53% |
| 3 h a 1 dia | 228 | 10.26 | 0.06% | 36% |
| 1 a 7 dias | 15 | 23.54 | 0.96% | 80% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (109): MFE mediano 5.5%, MAE mediano -1.0%, devolução média do melhor ponto 2.4%, captura mediana 0.67.
- Perdedores (164): MAE mediano -2.6%, MFE mediano 0.8%; 37 (23%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 132.76; 62% do lucro antes de custos.
- Trades < 3 h: 30 (lucro 47.99); reentradas em < 24 h: 56 (lucro -88.83).
- Maior trade = 62% do lucro; top 5 = 153%; top 10 = 230%; lucro sem o melhor = 30.86.
- Lucro por ano de fechamento: 2018: 20.6, 2019: 77.6, 2020: -7.6, 2021: 3.2, 2022: -23.7, 2023: 12.6, 2024: -0.9.

## NEAR/USDT

Trades: 190; lucro líquido: -160.50.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 114 | -615.73 | – | -3.89% | 4% | 9.1 h |
| take_profit_3pct | 74 | 452.26 | – | 4.43% | 100% | 6.3 h |
| time_exit_24h | 2 | 2.97 | – | 1.09% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 31 | 92.09 | 2.10% | 74% |
| 3 h a 1 dia | 157 | -255.56 | -1.15% | 35% |
| 1 a 7 dias | 2 | 2.97 | 1.09% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (80): MFE mediano 6.1%, MAE mediano -1.3%, devolução média do melhor ponto 3.0%, captura mediana 0.65.
- Perdedores (110): MAE mediano -4.8%, MFE mediano 1.6%; 44 (40%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 77.87; – do lucro antes de custos.
- Trades < 3 h: 31 (lucro 92.09); reentradas em < 24 h: 44 (lucro -103.49).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -176.58.
- Lucro por ano de fechamento: 2020: 16.0, 2021: -103.9, 2022: 5.7, 2023: -69.9, 2024: -8.4.

## UNI/USDT

Trades: 202; lucro líquido: -128.22.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 130 | -525.84 | – | -2.85% | 4% | 9.9 h |
| take_profit_3pct | 69 | 393.51 | – | 4.03% | 100% | 7.4 h |
| time_exit_24h | 3 | 4.11 | – | 1.04% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 27 | 24.91 | 0.72% | 63% |
| 3 h a 1 dia | 170 | -162.33 | -0.68% | 32% |
| 1 a 7 dias | 5 | 9.19 | 1.31% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (77): MFE mediano 5.1%, MAE mediano -1.1%, devolução média do melhor ponto 2.5%, captura mediana 0.63.
- Perdedores (125): MAE mediano -3.6%, MFE mediano 1.3%; 35 (28%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 84.89; – do lucro antes de custos.
- Trades < 3 h: 27 (lucro 24.91); reentradas em < 24 h: 45 (lucro -73.81).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -145.87.
- Lucro por ano de fechamento: 2020: -13.9, 2021: -1.9, 2022: -74.9, 2023: -50.1, 2024: 12.5.

## BCH/USDT

Trades: 243; lucro líquido: -100.08.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 163 | -577.21 | – | -2.45% | 10% | 10.4 h |
| take_profit_3pct | 75 | 470.93 | – | 4.37% | 100% | 9.0 h |
| time_exit_24h | 5 | 6.20 | – | 0.87% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 27 | -21.15 | -0.48% | 48% |
| 3 h a 1 dia | 206 | -92.11 | -0.31% | 36% |
| 1 a 7 dias | 10 | 13.18 | 0.93% | 90% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (96): MFE mediano 5.1%, MAE mediano -1.0%, devolução média do melhor ponto 2.6%, captura mediana 0.65.
- Perdedores (147): MAE mediano -3.3%, MFE mediano 1.1%; 37 (25%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 104.68; 2272% do lucro antes de custos.
- Trades < 3 h: 27 (lucro -21.15); reentradas em < 24 h: 45 (lucro -31.89).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -127.88.
- Lucro por ano de fechamento: 2019: 2.4, 2020: -42.2, 2021: -0.4, 2022: -31.6, 2023: -4.9, 2024: -23.3.

## XLM/USDT

Trades: 280; lucro líquido: 38.58.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 168 | -708.46 | -1836% | -2.67% | 7% | 9.9 h |
| take_profit_3pct | 106 | 732.59 | 1899% | 4.42% | 100% | 8.1 h |
| time_exit_24h | 6 | 14.45 | 37% | 1.54% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 29 | 71.18 | 1.60% | 66% |
| 3 h a 1 dia | 239 | -51.01 | -0.12% | 40% |
| 1 a 7 dias | 12 | 18.41 | 0.97% | 83% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (124): MFE mediano 5.7%, MAE mediano -1.1%, devolução média do melhor ponto 3.0%, captura mediana 0.64.
- Perdedores (156): MAE mediano -2.9%, MFE mediano 1.4%; 52 (33%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 131.82; 77% do lucro antes de custos.
- Trades < 3 h: 29 (lucro 71.18); reentradas em < 24 h: 70 (lucro -43.59).
- Maior trade = 78% do lucro; top 5 = 220%; top 10 = 358%; lucro sem o melhor = 8.39.
- Lucro por ano de fechamento: 2018: 40.2, 2019: -31.5, 2020: 9.0, 2021: 60.3, 2022: -5.0, 2023: -23.6, 2024: -10.8.

## FIL/USDT

Trades: 200; lucro líquido: -124.69.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 129 | -574.31 | – | -3.13% | 2% | 9.5 h |
| take_profit_3pct | 67 | 441.18 | – | 4.66% | 100% | 5.4 h |
| time_exit_24h | 4 | 8.43 | – | 1.55% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 30 | 125.75 | 2.93% | 80% |
| 3 h a 1 dia | 164 | -260.25 | -1.10% | 27% |
| 1 a 7 dias | 6 | 9.81 | 1.20% | 83% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (74): MFE mediano 6.0%, MAE mediano -1.0%, devolução média do melhor ponto 3.0%, captura mediana 0.63.
- Perdedores (126): MAE mediano -3.3%, MFE mediano 1.3%; 39 (31%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 84.20; – do lucro antes de custos.
- Trades < 3 h: 30 (lucro 125.75); reentradas em < 24 h: 47 (lucro -22.49).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -142.07.
- Lucro por ano de fechamento: 2020: -5.4, 2021: -43.6, 2022: -14.7, 2023: -65.5, 2024: 4.5.

## AAVE/USDT

Trades: 193; lucro líquido: 24.74.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 114 | -535.05 | -2163% | -2.98% | 7% | 10.2 h |
| take_profit_3pct | 76 | 549.55 | 2222% | 4.64% | 100% | 6.4 h |
| time_exit_24h | 3 | 10.24 | 41% | 2.20% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 28 | 181.23 | 4.19% | 89% |
| 3 h a 1 dia | 162 | -166.73 | -0.65% | 36% |
| 1 a 7 dias | 3 | 10.24 | 2.20% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (87): MFE mediano 5.6%, MAE mediano -1.0%, devolução média do melhor ponto 2.6%, captura mediana 0.66.
- Perdedores (106): MAE mediano -3.1%, MFE mediano 1.2%; 30 (28%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 90.85; 79% do lucro antes de custos.
- Trades < 3 h: 28 (lucro 181.23); reentradas em < 24 h: 37 (lucro -15.82).
- Maior trade = 77% do lucro; top 5 = 337%; top 10 = 575%; lucro sem o melhor = 5.81.
- Lucro por ano de fechamento: 2020: -13.6, 2021: 81.6, 2022: 12.6, 2023: -39.0, 2024: -16.8.

## INJ/USDT

Trades: 233; lucro líquido: -106.18.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 133 | -855.00 | – | -4.60% | 0% | 8.2 h |
| take_profit_3pct | 96 | 742.83 | – | 5.62% | 100% | 6.0 h |
| time_exit_24h | 4 | 5.99 | – | 1.13% | 75% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 45 | 181.59 | 2.92% | 69% |
| 3 h a 1 dia | 184 | -293.76 | -1.11% | 35% |
| 1 a 7 dias | 4 | 5.99 | 1.13% | 75% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (99): MFE mediano 7.9%, MAE mediano -2.1%, devolução média do melhor ponto 4.6%, captura mediana 0.60.
- Perdedores (134): MAE mediano -4.7%, MFE mediano 2.2%; 73 (54%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 95.42; – do lucro antes de custos.
- Trades < 3 h: 45 (lucro 181.59); reentradas em < 24 h: 60 (lucro -37.81).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -140.62.
- Lucro por ano de fechamento: 2020: -23.2, 2021: -33.9, 2022: -84.9, 2023: 38.4, 2024: -2.6.

## HBAR/USDT

Trades: 222; lucro líquido: -224.49.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 140 | -717.65 | – | -3.85% | 3% | 8.5 h |
| take_profit_3pct | 81 | 493.68 | – | 4.61% | 100% | 6.7 h |
| time_exit_24h | 1 | -0.51 | – | -0.43% | 0% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 30 | 22.82 | 0.55% | 60% |
| 3 h a 1 dia | 190 | -247.13 | -0.96% | 35% |
| 1 a 7 dias | 2 | -0.17 | -0.07% | 50% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (85): MFE mediano 6.6%, MAE mediano -2.1%, devolução média do melhor ponto 3.8%, captura mediana 0.61.
- Perdedores (137): MAE mediano -4.6%, MFE mediano 1.7%; 60 (44%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 86.34; – do lucro antes de custos.
- Trades < 3 h: 30 (lucro 22.82); reentradas em < 24 h: 52 (lucro -23.95).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -251.28.
- Lucro por ano de fechamento: 2019: -1.6, 2020: -73.3, 2021: -76.6, 2022: -52.9, 2023: 5.2, 2024: -25.2.

## OP/USDT

Trades: 112; lucro líquido: 15.15.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 63 | -320.07 | -2113% | -3.32% | 3% | 9.5 h |
| take_profit_3pct | 48 | 333.95 | 2205% | 4.58% | 100% | 7.9 h |
| time_exit_24h | 1 | 1.26 | 8% | 0.85% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 18 | 104.09 | 3.81% | 89% |
| 3 h a 1 dia | 93 | -90.21 | -0.62% | 37% |
| 1 a 7 dias | 1 | 1.26 | 0.85% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (51): MFE mediano 7.0%, MAE mediano -1.4%, devolução média do melhor ponto 4.0%, captura mediana 0.56.
- Perdedores (61): MAE mediano -3.7%, MFE mediano 2.0%; 30 (49%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 51.15; 77% do lucro antes de custos.
- Trades < 3 h: 18 (lucro 104.09); reentradas em < 24 h: 34 (lucro 52.57).
- Maior trade = 106% do lucro; top 5 = 451%; top 10 = 774%; lucro sem o melhor = -0.85.
- Lucro por ano de fechamento: 2022: -15.4, 2023: 60.6, 2024: -30.1.

## APT/USDT

Trades: 86; lucro líquido: -8.20.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 50 | -234.14 | – | -3.13% | 8% | 9.5 h |
| take_profit_3pct | 34 | 224.02 | – | 4.43% | 100% | 7.4 h |
| time_exit_24h | 2 | 1.92 | – | 0.65% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 11 | 2.56 | 0.19% | 55% |
| 3 h a 1 dia | 72 | -9.50 | -0.08% | 44% |
| 1 a 7 dias | 3 | -1.26 | -0.29% | 67% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (40): MFE mediano 5.6%, MAE mediano -1.0%, devolução média do melhor ponto 2.5%, captura mediana 0.64.
- Perdedores (46): MAE mediano -3.6%, MFE mediano 1.4%; 17 (37%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 38.41; 127% do lucro antes de custos.
- Trades < 3 h: 11 (lucro 2.56); reentradas em < 24 h: 16 (lucro -26.32).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -22.60.
- Lucro por ano de fechamento: 2022: -19.4, 2023: 25.9, 2024: -14.7.

## ARB/USDT

Trades: 58; lucro líquido: -47.09.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 41 | -149.95 | – | -2.52% | 5% | 9.7 h |
| take_profit_3pct | 15 | 101.16 | – | 4.70% | 100% | 5.1 h |
| time_exit_24h | 2 | 1.70 | – | 0.60% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 11 | 26.60 | 1.68% | 64% |
| 3 h a 1 dia | 44 | -74.36 | -1.15% | 23% |
| 1 a 7 dias | 3 | 0.67 | 0.16% | 67% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (19): MFE mediano 5.3%, MAE mediano -1.1%, devolução média do melhor ponto 2.0%, captura mediana 0.64.
- Perdedores (39): MAE mediano -3.2%, MFE mediano 1.1%; 11 (28%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 25.09; – do lucro antes de custos.
- Trades < 3 h: 11 (lucro 26.60); reentradas em < 24 h: 12 (lucro -32.36).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -59.35.
- Lucro por ano de fechamento: 2023: -44.7, 2024: -2.4.

## SUI/USDT

Trades: 61; lucro líquido: -63.78.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 40 | -203.67 | – | -3.50% | 0% | 7.6 h |
| take_profit_3pct | 21 | 139.89 | – | 4.62% | 100% | 8.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 10 | -4.11 | -0.23% | 40% |
| 3 h a 1 dia | 51 | -59.67 | -0.80% | 33% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (21): MFE mediano 6.2%, MAE mediano -1.6%, devolução média do melhor ponto 2.2%, captura mediana 0.70.
- Perdedores (40): MAE mediano -4.2%, MFE mediano 1.2%; 13 (32%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 26.42; – do lucro antes de custos.
- Trades < 3 h: 10 (lucro -4.11); reentradas em < 24 h: 13 (lucro -20.43).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -77.01.
- Lucro por ano de fechamento: 2023: -43.0, 2024: -20.8.

## ATOM/USDT

Trades: 245; lucro líquido: -125.13.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 151 | -649.01 | – | -3.06% | 5% | 10.1 h |
| take_profit_3pct | 91 | 519.33 | – | 4.10% | 100% | 6.5 h |
| time_exit_24h | 3 | 4.56 | – | 1.12% | 100% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 27 | 90.04 | 2.37% | 78% |
| 3 h a 1 dia | 213 | -218.79 | -0.72% | 36% |
| 1 a 7 dias | 5 | 3.62 | 0.54% | 80% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (101): MFE mediano 5.2%, MAE mediano -1.5%, devolução média do melhor ponto 2.2%, captura mediana 0.68.
- Perdedores (144): MAE mediano -3.8%, MFE mediano 1.6%; 59 (41%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 102.01; – do lucro antes de custos.
- Trades < 3 h: 27 (lucro 90.04); reentradas em < 24 h: 45 (lucro -119.50).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -138.63.
- Lucro por ano de fechamento: 2019: -60.5, 2020: -22.2, 2021: 5.9, 2022: -22.6, 2023: -12.1, 2024: -13.5.

## ETC/USDT

Trades: 322; lucro líquido: -116.19.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| rsi_below_55 | 204 | -851.52 | – | -2.87% | 5% | 9.9 h |
| take_profit_3pct | 110 | 721.89 | – | 4.52% | 100% | 7.7 h |
| time_exit_24h | 8 | 13.45 | – | 1.18% | 75% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 40 | 173.33 | 3.02% | 72% |
| 3 h a 1 dia | 272 | -301.98 | -0.76% | 33% |
| 1 a 7 dias | 10 | 12.46 | 0.87% | 70% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (126): MFE mediano 5.7%, MAE mediano -1.1%, devolução média do melhor ponto 3.0%, captura mediana 0.63.
- Perdedores (196): MAE mediano -3.3%, MFE mediano 1.1%; 62 (32%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 139.35; 602% do lucro antes de custos.
- Trades < 3 h: 40 (lucro 173.33); reentradas em < 24 h: 77 (lucro -14.22).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -147.76.
- Lucro por ano de fechamento: 2018: -37.0, 2019: 17.3, 2020: -6.7, 2021: 11.8, 2022: -37.6, 2023: -43.4, 2024: -20.6.
