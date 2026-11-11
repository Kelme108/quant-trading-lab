# Revisão de trades: H-108 (exploração)

Fonte dos trades: `research/experiments/20261111T145108Z-h-108-exploration-btc-usdt/raw/backtest-result-2026-11-11_15-01-59.zip`; `research/experiments/20261111T145108Z-h-108-exploration-eth-usdt/raw/backtest-result-2026-11-11_15-05-52.zip`; `research/experiments/20261111T145108Z-h-108-exploration-bnb-usdt/raw/backtest-result-2026-11-11_15-09-54.zip`; `research/experiments/20261111T145108Z-h-108-exploration-xrp-usdt/raw/backtest-result-2026-11-11_15-13-40.zip`; `research/experiments/20261111T145108Z-h-108-exploration-ada-usdt/raw/backtest-result-2026-11-11_15-17-36.zip`; `research/experiments/20261111T145108Z-h-108-exploration-ltc-usdt/raw/backtest-result-2026-11-11_15-23-15.zip`; `research/experiments/20261111T145108Z-h-108-exploration-link-usdt/raw/backtest-result-2026-11-11_15-30-37.zip`; `research/experiments/20261111T145108Z-h-108-exploration-doge-usdt/raw/backtest-result-2026-11-11_15-38-07.zip`; `research/experiments/20261111T145108Z-h-108-exploration-sol-usdt/raw/backtest-result-2026-11-11_15-45-51.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 559; lucro líquido: -46.23.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| max_hold_12h | 140 | 222.20 | – | 1.58% | 69% | 12.0 h |
| session_flat_2300 | 134 | 133.85 | – | 1.00% | 68% | 8.2 h |
| trail_4_low | 119 | -92.80 | – | -0.78% | 13% | 6.9 h |
| stop_loss | 103 | -237.61 | – | -2.29% | 0% | 2.9 h |
| fail_fast_pivot | 63 | -71.87 | – | -1.16% | 0% | 1.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 116 | -194.07 | -1.68% | 0% |
| 3 h a 1 dia | 443 | 147.85 | 0.33% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (203): MFE mediano 3.1%, MAE mediano -0.4%, devolução média do melhor ponto 1.7%, captura mediana 0.52.
- Perdedores (356): MAE mediano -1.6%, MFE mediano 0.7%; 38 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 167.09; 138% do lucro antes de custos.
- Trades < 3 h: 116 (lucro -194.07); reentradas em < 24 h: 124 (lucro -15.59).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -59.45.
- Lucro por ano de fechamento: 2017: 15.4, 2018: -9.6, 2019: 18.0, 2020: 6.4, 2021: -37.8, 2022: -18.0, 2023: -31.8, 2024: 11.1.

## ETH/USDT

Trades: 628; lucro líquido: -32.93.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| max_hold_12h | 142 | 318.66 | – | 2.25% | 80% | 12.0 h |
| stop_loss | 140 | -320.54 | – | -2.29% | 0% | 3.0 h |
| session_flat_2300 | 137 | 171.49 | – | 1.25% | 71% | 8.2 h |
| trail_4_low | 116 | -101.40 | – | -0.87% | 14% | 7.1 h |
| fail_fast_pivot | 93 | -101.14 | – | -1.08% | 0% | 1.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 164 | -263.67 | -1.61% | 0% |
| 3 h a 1 dia | 464 | 230.73 | 0.50% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (227): MFE mediano 3.5%, MAE mediano -0.5%, devolução média do melhor ponto 1.9%, captura mediana 0.54.
- Perdedores (401): MAE mediano -1.8%, MFE mediano 0.7%; 48 (12%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 188.47; 121% do lucro antes de custos.
- Trades < 3 h: 164 (lucro -263.67); reentradas em < 24 h: 165 (lucro -52.99).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -47.32.
- Lucro por ano de fechamento: 2017: -29.4, 2018: -6.7, 2019: 9.8, 2020: 24.0, 2021: 45.3, 2022: -17.9, 2023: -38.4, 2024: -19.6.

## BNB/USDT

Trades: 607; lucro líquido: -57.76.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 180 | -405.79 | – | -2.29% | 0% | 2.0 h |
| max_hold_12h | 131 | 373.81 | – | 2.91% | 79% | 12.0 h |
| trail_4_low | 110 | -56.51 | – | -0.52% | 21% | 7.2 h |
| fail_fast_pivot | 95 | -109.80 | – | -1.17% | 0% | 1.4 h |
| session_flat_2300 | 91 | 140.53 | – | 1.57% | 69% | 8.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 214 | -378.34 | -1.79% | 0% |
| 3 h a 1 dia | 393 | 320.58 | 0.83% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (190): MFE mediano 4.0%, MAE mediano -0.6%, devolução média do melhor ponto 2.4%, captura mediana 0.52.
- Perdedores (417): MAE mediano -2.0%, MFE mediano 0.7%; 65 (16%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 178.69; 148% do lucro antes de custos.
- Trades < 3 h: 214 (lucro -378.34); reentradas em < 24 h: 147 (lucro -66.33).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -85.59.
- Lucro por ano de fechamento: 2017: -11.6, 2018: -22.2, 2019: 39.6, 2020: -45.5, 2021: 51.8, 2022: -34.1, 2023: -32.5, 2024: -3.2.

## XRP/USDT

Trades: 505; lucro líquido: -135.28.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 184 | -401.08 | – | -2.29% | 0% | 2.2 h |
| max_hold_12h | 87 | 241.54 | – | 2.89% | 70% | 12.0 h |
| session_flat_2300 | 85 | 167.10 | – | 2.11% | 69% | 8.2 h |
| fail_fast_pivot | 77 | -83.17 | – | -1.14% | 0% | 1.3 h |
| trail_4_low | 72 | -59.67 | – | -0.88% | 14% | 7.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 199 | -349.70 | -1.85% | 0% |
| 3 h a 1 dia | 306 | 214.42 | 0.74% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (130): MFE mediano 4.2%, MAE mediano -0.7%, devolução média do melhor ponto 3.2%, captura mediana 0.44.
- Perdedores (375): MAE mediano -2.1%, MFE mediano 0.8%; 67 (18%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 143.43; 1760% do lucro antes de custos.
- Trades < 3 h: 199 (lucro -349.70); reentradas em < 24 h: 109 (lucro -52.45).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -174.65.
- Lucro por ano de fechamento: 2018: 7.1, 2019: -34.2, 2020: -2.3, 2021: -47.6, 2022: -8.7, 2023: -25.3, 2024: -24.3.

## ADA/USDT

Trades: 589; lucro líquido: -147.68.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 203 | -435.56 | – | -2.29% | 0% | 2.5 h |
| max_hold_12h | 112 | 322.47 | – | 3.08% | 86% | 12.0 h |
| trail_4_low | 95 | -64.34 | – | -0.75% | 16% | 7.0 h |
| fail_fast_pivot | 91 | -102.86 | – | -1.22% | 0% | 1.3 h |
| session_flat_2300 | 88 | 132.62 | – | 1.64% | 73% | 8.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 213 | -365.88 | -1.83% | 0% |
| 3 h a 1 dia | 376 | 218.20 | 0.62% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (175): MFE mediano 4.3%, MAE mediano -0.7%, devolução média do melhor ponto 2.7%, captura mediana 0.48.
- Perdedores (414): MAE mediano -2.1%, MFE mediano 0.9%; 79 (19%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 163.38; 1040% do lucro antes de custos.
- Trades < 3 h: 213 (lucro -365.88); reentradas em < 24 h: 151 (lucro -49.87).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -163.49.
- Lucro por ano de fechamento: 2018: -24.8, 2019: -46.4, 2020: 7.2, 2021: -5.0, 2022: -37.9, 2023: -22.3, 2024: -18.4.

## LTC/USDT

Trades: 615; lucro líquido: -140.46.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 207 | -456.16 | – | -2.28% | 0% | 2.5 h |
| max_hold_12h | 113 | 353.77 | – | 3.24% | 85% | 12.0 h |
| trail_4_low | 110 | -78.29 | – | -0.75% | 15% | 7.2 h |
| session_flat_2300 | 100 | 132.23 | – | 1.37% | 66% | 8.2 h |
| fail_fast_pivot | 85 | -92.01 | – | -1.13% | 0% | 1.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 207 | -361.91 | -1.81% | 0% |
| 3 h a 1 dia | 408 | 221.45 | 0.55% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (179): MFE mediano 4.0%, MAE mediano -0.6%, devolução média do melhor ponto 2.3%, captura mediana 0.51.
- Perdedores (436): MAE mediano -2.1%, MFE mediano 0.8%; 63 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 176.26; 492% do lucro antes de custos.
- Trades < 3 h: 207 (lucro -361.91); reentradas em < 24 h: 142 (lucro -122.40).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -167.59.
- Lucro por ano de fechamento: 2017: -8.3, 2018: -2.2, 2019: 10.4, 2020: -5.2, 2021: -46.7, 2022: -46.9, 2023: -37.3, 2024: -4.3.

## LINK/USDT

Trades: 545; lucro líquido: -156.51.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 202 | -432.35 | – | -2.29% | 0% | 2.3 h |
| fail_fast_pivot | 95 | -104.78 | – | -1.20% | 0% | 1.3 h |
| max_hold_12h | 93 | 258.77 | – | 3.00% | 86% | 12.0 h |
| session_flat_2300 | 83 | 163.32 | – | 2.10% | 69% | 7.8 h |
| trail_4_low | 72 | -41.47 | – | -0.63% | 19% | 7.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 225 | -384.45 | -1.83% | 0% |
| 3 h a 1 dia | 320 | 227.94 | 0.76% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (151): MFE mediano 4.8%, MAE mediano -0.7%, devolução média do melhor ponto 2.6%, captura mediana 0.57.
- Perdedores (394): MAE mediano -2.1%, MFE mediano 1.0%; 87 (22%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 151.13; – do lucro antes de custos.
- Trades < 3 h: 225 (lucro -384.45); reentradas em < 24 h: 143 (lucro -111.88).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -175.42.
- Lucro por ano de fechamento: 2019: -65.8, 2020: 7.2, 2021: -8.5, 2022: -41.8, 2023: -12.0, 2024: -35.6.

## DOGE/USDT

Trades: 453; lucro líquido: -224.64.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 200 | -408.21 | – | -2.29% | 0% | 1.9 h |
| fail_fast_pivot | 77 | -76.61 | – | -1.12% | 0% | 1.3 h |
| trail_4_low | 65 | -21.08 | – | -0.39% | 28% | 7.6 h |
| max_hold_12h | 62 | 203.51 | – | 3.65% | 84% | 12.0 h |
| session_flat_2300 | 49 | 77.75 | – | 1.84% | 80% | 8.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 216 | -363.32 | -1.87% | 0% |
| 3 h a 1 dia | 237 | 138.69 | 0.64% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (109): MFE mediano 4.9%, MAE mediano -0.6%, devolução média do melhor ponto 3.8%, captura mediana 0.39.
- Perdedores (344): MAE mediano -2.2%, MFE mediano 0.8%; 77 (22%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 120.44; – do lucro antes de custos.
- Trades < 3 h: 216 (lucro -363.32); reentradas em < 24 h: 106 (lucro -52.08).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -256.54.
- Lucro por ano de fechamento: 2019: -8.9, 2020: -34.7, 2021: -78.3, 2022: -12.3, 2023: -78.4, 2024: -11.9.

## SOL/USDT

Trades: 395; lucro líquido: -74.31.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 167 | -375.19 | – | -2.29% | 0% | 2.0 h |
| max_hold_12h | 65 | 216.65 | – | 3.41% | 89% | 12.0 h |
| fail_fast_pivot | 60 | -73.29 | – | -1.25% | 0% | 1.3 h |
| session_flat_2300 | 58 | 162.37 | – | 2.85% | 83% | 8.0 h |
| trail_4_low | 45 | -4.85 | – | -0.12% | 27% | 7.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 170 | -320.78 | -1.92% | 0% |
| 3 h a 1 dia | 225 | 246.47 | 1.12% | 52% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (118): MFE mediano 5.8%, MAE mediano -0.9%, devolução média do melhor ponto 3.4%, captura mediana 0.50.
- Perdedores (277): MAE mediano -2.3%, MFE mediano 1.0%; 75 (27%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 115.56; 280% do lucro antes de custos.
- Trades < 3 h: 170 (lucro -320.78); reentradas em < 24 h: 107 (lucro 0.48).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -92.46.
- Lucro por ano de fechamento: 2020: -3.0, 2021: 18.5, 2022: -65.0, 2023: -2.4, 2024: -22.5.
