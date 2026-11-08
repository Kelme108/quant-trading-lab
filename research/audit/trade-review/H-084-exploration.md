# Revisão de trades: H-084 (exploração)

Fonte dos trades: `research/experiments/20261108T015312Z-h-084-exploration-btc-usdt/raw/backtest-result-2026-11-08_02-00-13.zip`; `research/experiments/20261108T015312Z-h-084-exploration-eth-usdt/raw/backtest-result-2026-11-08_02-02-24.zip`; `research/experiments/20261108T015312Z-h-084-exploration-bnb-usdt/raw/backtest-result-2026-11-08_02-04-35.zip`; `research/experiments/20261108T015312Z-h-084-exploration-xrp-usdt/raw/backtest-result-2026-11-08_02-06-43.zip`; `research/experiments/20261108T015312Z-h-084-exploration-ada-usdt/raw/backtest-result-2026-11-08_02-08-51.zip`; `research/experiments/20261108T015312Z-h-084-exploration-ltc-usdt/raw/backtest-result-2026-11-08_02-11-00.zip`; `research/experiments/20261108T015312Z-h-084-exploration-link-usdt/raw/backtest-result-2026-11-08_02-13-09.zip`; `research/experiments/20261108T015312Z-h-084-exploration-doge-usdt/raw/backtest-result-2026-11-08_02-15-09.zip`; `research/experiments/20261108T015312Z-h-084-exploration-sol-usdt/raw/backtest-result-2026-11-08_02-17-06.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 512; lucro líquido: -0.30.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 260 | 46.23 | – | 1.77% | 72% | 24.0 h |
| kijun_exit | 183 | -23.72 | – | -1.28% | 2% | 9.0 h |
| stop_loss | 69 | -22.81 | – | -3.29% | 0% | 9.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 53 | -8.94 | -1.67% | 2% |
| 3 h a 1 dia | 196 | -36.89 | -1.87% | 2% |
| 1 a 7 dias | 263 | 45.53 | 1.72% | 71% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (191): MFE mediano 4.0%, MAE mediano -0.7%, devolução média do melhor ponto 2.0%, captura mediana 0.56.
- Perdedores (321): MAE mediano -1.8%, MFE mediano 0.7%; 59 (18%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 15.44; 102% do lucro antes de custos.
- Trades < 3 h: 53 (lucro -8.94); reentradas em < 24 h: 93 (lucro -0.85).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -1.80.
- Lucro por ano de fechamento: 2017: 1.2, 2018: -1.1, 2019: -0.2, 2020: 2.0, 2021: 1.8, 2022: -1.8, 2023: -1.3, 2024: -1.1.

## ETH/USDT

Trades: 525; lucro líquido: 18.82.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 258 | 80.55 | 428% | 2.83% | 80% | 24.0 h |
| kijun_exit | 162 | -23.78 | -126% | -1.29% | 2% | 9.0 h |
| stop_loss | 105 | -37.95 | -202% | -3.29% | 0% | 9.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 58 | -10.92 | -1.74% | 0% |
| 3 h a 1 dia | 207 | -50.25 | -2.17% | 1% |
| 1 a 7 dias | 260 | 80.00 | 2.79% | 80% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (210): MFE mediano 4.9%, MAE mediano -0.8%, devolução média do melhor ponto 2.4%, captura mediana 0.57.
- Perdedores (315): MAE mediano -2.4%, MFE mediano 1.0%; 74 (23%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 17.59; 48% do lucro antes de custos.
- Trades < 3 h: 58 (lucro -10.92); reentradas em < 24 h: 97 (lucro -0.09).
- Maior trade = 14% do lucro; top 5 = 56%; top 10 = 91%; lucro sem o melhor = 16.22.
- Lucro por ano de fechamento: 2017: 1.0, 2018: 1.7, 2019: 2.0, 2020: 7.7, 2021: 6.3, 2022: 0.0, 2023: -0.5, 2024: 0.6.

## BNB/USDT

Trades: 562; lucro líquido: -4.25.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 247 | 66.27 | – | 2.66% | 75% | 24.0 h |
| kijun_exit | 184 | -26.88 | – | -1.46% | 1% | 9.3 h |
| stop_loss | 131 | -43.64 | – | -3.29% | 0% | 7.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 77 | -18.39 | -2.35% | 0% |
| 3 h a 1 dia | 233 | -51.52 | -2.20% | 1% |
| 1 a 7 dias | 252 | 65.66 | 2.59% | 74% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (188): MFE mediano 4.7%, MAE mediano -0.9%, devolução média do melhor ponto 2.3%, captura mediana 0.60.
- Perdedores (374): MAE mediano -2.5%, MFE mediano 0.9%; 74 (20%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 16.89; 134% do lucro antes de custos.
- Trades < 3 h: 77 (lucro -18.39); reentradas em < 24 h: 130 (lucro 7.15).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -8.05.
- Lucro por ano de fechamento: 2017: -1.8, 2018: 5.7, 2019: -3.0, 2020: 4.3, 2021: -3.3, 2022: -2.7, 2023: -1.9, 2024: -1.6.

## XRP/USDT

Trades: 509; lucro líquido: -9.03.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 207 | 49.49 | – | 2.49% | 72% | 24.0 h |
| kijun_exit | 192 | -23.54 | – | -1.28% | 5% | 8.8 h |
| stop_loss | 110 | -34.98 | – | -3.29% | 0% | 7.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 73 | -14.99 | -2.12% | 0% |
| 3 h a 1 dia | 227 | -43.19 | -1.98% | 4% |
| 1 a 7 dias | 209 | 49.16 | 2.45% | 71% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (159): MFE mediano 5.0%, MAE mediano -0.9%, devolução média do melhor ponto 3.4%, captura mediana 0.46.
- Perdedores (350): MAE mediano -2.3%, MFE mediano 0.9%; 81 (23%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 14.59; 262% do lucro antes de custos.
- Trades < 3 h: 73 (lucro -14.99); reentradas em < 24 h: 108 (lucro -3.62).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -13.22.
- Lucro por ano de fechamento: 2018: -3.0, 2019: -0.8, 2020: 1.0, 2021: 0.1, 2022: -2.6, 2023: -0.5, 2024: -3.3.

## ADA/USDT

Trades: 491; lucro líquido: 0.49.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 206 | 72.15 | 14839% | 3.34% | 74% | 24.0 h |
| stop_loss | 146 | -50.62 | -10410% | -3.28% | 0% | 7.3 h |
| kijun_exit | 139 | -21.04 | -4328% | -1.44% | 3% | 9.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 80 | -19.73 | -2.32% | 0% |
| 3 h a 1 dia | 200 | -51.33 | -2.43% | 2% |
| 1 a 7 dias | 211 | 71.55 | 3.23% | 73% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (156): MFE mediano 6.4%, MAE mediano -1.0%, devolução média do melhor ponto 3.2%, captura mediana 0.56.
- Perdedores (335): MAE mediano -3.0%, MFE mediano 1.1%; 97 (29%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 15.46; 97% do lucro antes de custos.
- Trades < 3 h: 80 (lucro -19.73); reentradas em < 24 h: 110 (lucro -1.70).
- Maior trade = 656% do lucro; top 5 = 2367%; top 10 = 4125%; lucro sem o melhor = -2.70.
- Lucro por ano de fechamento: 2018: -2.0, 2019: 1.6, 2020: 6.0, 2021: 4.7, 2022: -2.0, 2023: -4.3, 2024: -3.5.

## LTC/USDT

Trades: 508; lucro líquido: 4.44.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 228 | 70.78 | 1595% | 3.01% | 77% | 24.0 h |
| stop_loss | 148 | -50.17 | -1130% | -3.28% | 0% | 7.3 h |
| kijun_exit | 132 | -16.18 | -365% | -1.16% | 11% | 9.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 69 | -16.96 | -2.37% | 0% |
| 3 h a 1 dia | 206 | -49.97 | -2.34% | 6% |
| 1 a 7 dias | 233 | 71.37 | 2.97% | 76% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (191): MFE mediano 5.5%, MAE mediano -0.9%, devolução média do melhor ponto 3.0%, captura mediana 0.55.
- Perdedores (317): MAE mediano -3.0%, MFE mediano 0.9%; 69 (22%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 15.90; 78% do lucro antes de custos.
- Trades < 3 h: 69 (lucro -16.96); reentradas em < 24 h: 90 (lucro 3.92).
- Maior trade = 72% do lucro; top 5 = 231%; top 10 = 380%; lucro sem o melhor = 1.25.
- Lucro por ano de fechamento: 2017: -0.4, 2018: -5.2, 2019: 6.0, 2020: 5.6, 2021: 3.8, 2022: -0.1, 2023: -0.3, 2024: -4.9.

## LINK/USDT

Trades: 461; lucro líquido: 5.84.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 186 | 83.29 | 1426% | 4.35% | 84% | 24.0 h |
| stop_loss | 182 | -61.92 | -1060% | -3.28% | 0% | 7.4 h |
| kijun_exit | 93 | -15.53 | -266% | -1.60% | 2% | 8.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 70 | -18.61 | -2.60% | 0% |
| 3 h a 1 dia | 204 | -58.58 | -2.75% | 1% |
| 1 a 7 dias | 187 | 83.04 | 4.32% | 84% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (159): MFE mediano 7.0%, MAE mediano -1.1%, devolução média do melhor ponto 3.0%, captura mediana 0.61.
- Perdedores (302): MAE mediano -3.2%, MFE mediano 1.2%; 98 (32%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 14.37; 71% do lucro antes de custos.
- Trades < 3 h: 70 (lucro -18.61); reentradas em < 24 h: 97 (lucro -3.58).
- Maior trade = 121% do lucro; top 5 = 266%; top 10 = 390%; lucro sem o melhor = -1.24.
- Lucro por ano de fechamento: 2019: -3.6, 2020: 12.5, 2021: -3.1, 2022: 4.7, 2023: -3.2, 2024: -1.4.

## DOGE/USDT

Trades: 389; lucro líquido: -12.79.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| kijun_exit | 144 | -17.98 | – | -1.33% | 7% | 10.1 h |
| time_exit_24h | 135 | 38.98 | – | 3.10% | 75% | 24.0 h |
| stop_loss | 110 | -33.79 | – | -3.28% | 0% | 6.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 72 | -17.58 | -2.59% | 0% |
| 3 h a 1 dia | 178 | -33.83 | -2.04% | 6% |
| 1 a 7 dias | 139 | 38.63 | 2.99% | 73% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (111): MFE mediano 6.6%, MAE mediano -0.9%, devolução média do melhor ponto 3.7%, captura mediana 0.49.
- Perdedores (278): MAE mediano -2.8%, MFE mediano 1.1%; 85 (31%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 10.91; – do lucro antes de custos.
- Trades < 3 h: 72 (lucro -17.58); reentradas em < 24 h: 86 (lucro -7.30).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -16.13.
- Lucro por ano de fechamento: 2019: 1.3, 2020: -2.4, 2021: -6.4, 2022: -2.9, 2023: -2.2, 2024: -0.2.

## SOL/USDT

Trades: 319; lucro líquido: -1.15.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 151 | -48.97 | – | -3.29% | 0% | 6.1 h |
| time_exit_24h | 111 | 56.08 | – | 5.15% | 87% | 24.0 h |
| kijun_exit | 57 | -8.26 | – | -1.47% | 5% | 9.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 69 | -20.41 | -3.00% | 0% |
| 3 h a 1 dia | 137 | -36.40 | -2.69% | 2% |
| 1 a 7 dias | 113 | 55.65 | 5.03% | 86% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (100): MFE mediano 8.0%, MAE mediano -1.1%, devolução média do melhor ponto 3.8%, captura mediana 0.61.
- Perdedores (219): MAE mediano -3.4%, MFE mediano 1.4%; 85 (39%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 9.41; 114% do lucro antes de custos.
- Trades < 3 h: 69 (lucro -20.41); reentradas em < 24 h: 78 (lucro -1.68).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -5.62.
- Lucro por ano de fechamento: 2020: 0.3, 2021: -3.7, 2022: 1.4, 2023: 2.6, 2024: -1.8.
