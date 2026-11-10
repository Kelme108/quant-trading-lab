# Revisão de trades: H-091 (exploração)

Fonte dos trades: `research/experiments/20261109T235200Z-h-091-exploration-btc-usdt/raw/backtest-result-2026-11-10_00-10-34.zip`; `research/experiments/20261109T235200Z-h-091-exploration-eth-usdt/raw/backtest-result-2026-11-10_00-14-06.zip`; `research/experiments/20261109T235200Z-h-091-exploration-bnb-usdt/raw/backtest-result-2026-11-10_00-16-43.zip`; `research/experiments/20261109T235200Z-h-091-exploration-xrp-usdt/raw/backtest-result-2026-11-10_00-19-19.zip`; `research/experiments/20261109T235200Z-h-091-exploration-ada-usdt/raw/backtest-result-2026-11-10_00-22-09.zip`; `research/experiments/20261109T235200Z-h-091-exploration-ltc-usdt/raw/backtest-result-2026-11-10_00-24-48.zip`; `research/experiments/20261109T235200Z-h-091-exploration-link-usdt/raw/backtest-result-2026-11-10_00-27-32.zip`; `research/experiments/20261109T235200Z-h-091-exploration-doge-usdt/raw/backtest-result-2026-11-10_00-29-56.zip`; `research/experiments/20261109T235200Z-h-091-exploration-sol-usdt/raw/backtest-result-2026-11-10_00-32-10.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 590; lucro líquido: -164.60.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| above_sma5_or_below_sma200 | 397 | 173.54 | – | 0.47% | 71% | 5.2 h |
| stop_loss | 151 | -321.05 | – | -2.29% | 0% | 2.8 h |
| time_2300 | 34 | -9.91 | – | -0.33% | 26% | 7.6 h |
| time_12h | 8 | -7.19 | – | -1.00% | 0% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 177 | -133.15 | -0.81% | 41% |
| 3 h a 1 dia | 413 | -31.45 | -0.09% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (292): MFE mediano 1.4%, MAE mediano -0.5%, devolução média do melhor ponto 0.9%, captura mediana 0.41.
- Perdedores (298): MAE mediano -2.1%, MFE mediano 0.5%; 17 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 161.12; – do lucro antes de custos.
- Trades < 3 h: 177 (lucro -133.15); reentradas em < 24 h: 212 (lucro -83.12).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -170.17.
- Lucro por ano de fechamento: 2017: -3.8, 2018: -43.3, 2019: -21.1, 2020: -16.0, 2021: -28.5, 2022: -22.3, 2023: -17.3, 2024: -12.3.

## ETH/USDT

Trades: 626; lucro líquido: -182.40.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| above_sma5_or_below_sma200 | 381 | 279.06 | – | 0.78% | 78% | 5.3 h |
| stop_loss | 210 | -448.58 | – | -2.29% | 0% | 2.3 h |
| time_2300 | 28 | -5.89 | – | -0.25% | 25% | 7.9 h |
| time_12h | 7 | -6.99 | – | -1.15% | 0% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 211 | -216.65 | -1.10% | 32% |
| 3 h a 1 dia | 415 | 34.25 | 0.08% | 58% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (306): MFE mediano 1.7%, MAE mediano -0.5%, devolução média do melhor ponto 1.0%, captura mediana 0.45.
- Perdedores (320): MAE mediano -2.3%, MFE mediano 0.6%; 28 (9%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 172.61; – do lucro antes de custos.
- Trades < 3 h: 211 (lucro -216.65); reentradas em < 24 h: 244 (lucro -119.75).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -191.55.
- Lucro por ano de fechamento: 2017: 6.6, 2018: -12.5, 2019: -24.6, 2020: -27.9, 2021: -58.4, 2022: -22.9, 2023: -27.7, 2024: -15.0.

## BNB/USDT

Trades: 691; lucro líquido: -155.97.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| above_sma5_or_below_sma200 | 409 | 366.92 | – | 1.00% | 83% | 5.0 h |
| stop_loss | 246 | -512.05 | – | -2.29% | 0% | 2.2 h |
| time_2300 | 30 | -3.58 | – | -0.13% | 40% | 7.9 h |
| time_12h | 6 | -7.27 | – | -1.33% | 0% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 268 | -222.98 | -0.91% | 34% |
| 3 h a 1 dia | 423 | 67.01 | 0.18% | 61% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (351): MFE mediano 1.8%, MAE mediano -0.6%, devolução média do melhor ponto 1.1%, captura mediana 0.50.
- Perdedores (340): MAE mediano -2.3%, MFE mediano 0.7%; 39 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 185.27; 632% do lucro antes de custos.
- Trades < 3 h: 268 (lucro -222.98); reentradas em < 24 h: 280 (lucro -67.85).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -170.76.
- Lucro por ano de fechamento: 2017: -0.4, 2018: -62.0, 2019: -30.7, 2020: -27.2, 2021: -11.4, 2022: 3.0, 2023: -15.1, 2024: -12.2.

## XRP/USDT

Trades: 479; lucro líquido: -89.14.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| above_sma5_or_below_sma200 | 310 | 254.86 | – | 0.85% | 80% | 5.3 h |
| stop_loss | 153 | -339.63 | – | -2.29% | 0% | 2.1 h |
| time_2300 | 13 | -3.04 | – | -0.25% | 38% | 7.8 h |
| time_12h | 3 | -1.33 | – | -0.46% | 0% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 166 | -185.28 | -1.15% | 29% |
| 3 h a 1 dia | 313 | 96.14 | 0.31% | 65% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (252): MFE mediano 1.9%, MAE mediano -0.5%, devolução média do melhor ponto 1.2%, captura mediana 0.45.
- Perdedores (227): MAE mediano -2.3%, MFE mediano 0.6%; 29 (13%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 138.64; 280% do lucro antes de custos.
- Trades < 3 h: 166 (lucro -185.28); reentradas em < 24 h: 177 (lucro -29.18).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -97.26.
- Lucro por ano de fechamento: 2018: 0.4, 2019: -2.1, 2020: -5.8, 2021: -49.6, 2022: -23.9, 2023: -5.3, 2024: -3.0.

## ADA/USDT

Trades: 559; lucro líquido: -99.24.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| above_sma5_or_below_sma200 | 317 | 398.03 | – | 1.30% | 88% | 5.1 h |
| stop_loss | 223 | -492.29 | – | -2.29% | 0% | 2.3 h |
| time_2300 | 11 | -0.57 | – | -0.04% | 36% | 7.9 h |
| time_12h | 8 | -4.41 | – | -0.58% | 25% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 218 | -204.75 | -0.97% | 32% |
| 3 h a 1 dia | 341 | 105.51 | 0.32% | 63% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (286): MFE mediano 2.3%, MAE mediano -0.6%, devolução média do melhor ponto 1.3%, captura mediana 0.52.
- Perdedores (273): MAE mediano -2.5%, MFE mediano 0.7%; 36 (13%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 161.12; 260% do lucro antes de custos.
- Trades < 3 h: 218 (lucro -204.75); reentradas em < 24 h: 244 (lucro -34.10).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -109.09.
- Lucro por ano de fechamento: 2018: 0.6, 2019: -9.6, 2020: -11.3, 2021: -32.9, 2022: -29.4, 2023: -5.8, 2024: -10.9.

## LTC/USDT

Trades: 541; lucro líquido: -93.83.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| above_sma5_or_below_sma200 | 309 | 342.92 | – | 1.18% | 84% | 5.0 h |
| stop_loss | 198 | -427.88 | – | -2.28% | 0% | 2.4 h |
| time_2300 | 28 | -4.26 | – | -0.16% | 32% | 7.8 h |
| time_12h | 6 | -4.61 | – | -0.81% | 17% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 184 | -163.69 | -0.93% | 31% |
| 3 h a 1 dia | 357 | 69.86 | 0.21% | 60% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (270): MFE mediano 2.1%, MAE mediano -0.6%, devolução média do melhor ponto 1.2%, captura mediana 0.51.
- Perdedores (271): MAE mediano -2.4%, MFE mediano 0.7%; 20 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 152.60; 260% do lucro antes de custos.
- Trades < 3 h: 184 (lucro -163.69); reentradas em < 24 h: 221 (lucro -42.54).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -104.37.
- Lucro por ano de fechamento: 2018: -34.9, 2019: -15.9, 2020: -13.9, 2021: 4.0, 2022: -12.5, 2023: -20.8, 2024: 0.2.

## LINK/USDT

Trades: 546; lucro líquido: -65.70.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| above_sma5_or_below_sma200 | 297 | 452.79 | – | 1.55% | 90% | 4.9 h |
| stop_loss | 227 | -512.39 | – | -2.29% | 0% | 2.2 h |
| time_2300 | 19 | -2.33 | – | -0.12% | 32% | 7.8 h |
| time_12h | 3 | -3.77 | – | -1.30% | 0% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 223 | -202.14 | -0.92% | 31% |
| 3 h a 1 dia | 323 | 136.44 | 0.43% | 63% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (274): MFE mediano 2.5%, MAE mediano -0.7%, devolução média do melhor ponto 1.4%, captura mediana 0.55.
- Perdedores (272): MAE mediano -2.4%, MFE mediano 0.8%; 45 (17%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 160.36; 169% do lucro antes de custos.
- Trades < 3 h: 223 (lucro -202.14); reentradas em < 24 h: 249 (lucro 29.10).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -78.02.
- Lucro por ano de fechamento: 2019: 4.4, 2020: 1.0, 2021: -26.7, 2022: -5.2, 2023: -40.2, 2024: 1.1.

## DOGE/USDT

Trades: 404; lucro líquido: -105.13.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| above_sma5_or_below_sma200 | 217 | 267.27 | – | 1.36% | 82% | 4.9 h |
| stop_loss | 175 | -368.27 | – | -2.29% | 0% | 1.9 h |
| time_2300 | 8 | -0.24 | – | -0.03% | 50% | 7.5 h |
| time_12h | 4 | -3.89 | – | -1.05% | 0% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 171 | -147.35 | -0.93% | 25% |
| 3 h a 1 dia | 233 | 42.21 | 0.21% | 60% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (182): MFE mediano 2.3%, MAE mediano -0.7%, devolução média do melhor ponto 1.4%, captura mediana 0.52.
- Perdedores (222): MAE mediano -2.6%, MFE mediano 0.7%; 37 (17%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 111.07; 1872% do lucro antes de custos.
- Trades < 3 h: 171 (lucro -147.35); reentradas em < 24 h: 163 (lucro -26.56).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -124.13.
- Lucro por ano de fechamento: 2019: -14.0, 2020: -42.6, 2021: -44.2, 2022: -8.0, 2023: -0.2, 2024: 3.9.

## SOL/USDT

Trades: 420; lucro líquido: -124.95.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| above_sma5_or_below_sma200 | 211 | 291.13 | – | 1.49% | 89% | 4.7 h |
| stop_loss | 192 | -409.62 | – | -2.29% | 0% | 1.9 h |
| time_2300 | 13 | -3.35 | – | -0.29% | 31% | 7.6 h |
| time_12h | 4 | -3.11 | – | -0.86% | 0% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 184 | -198.77 | -1.16% | 24% |
| 3 h a 1 dia | 236 | 73.82 | 0.34% | 62% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (191): MFE mediano 2.7%, MAE mediano -0.7%, devolução média do melhor ponto 1.4%, captura mediana 0.55.
- Perdedores (229): MAE mediano -2.5%, MFE mediano 0.8%; 40 (17%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 115.97; – do lucro antes de custos.
- Trades < 3 h: 184 (lucro -198.77); reentradas em < 24 h: 202 (lucro -42.85).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -137.17.
- Lucro por ano de fechamento: 2020: -21.0, 2021: -57.9, 2022: -33.5, 2023: -1.1, 2024: -11.4.
