# Revisão de trades: H-118 (exploração)

Fonte dos trades: `research/experiments/20261112T074927Z-h-118-exploration-btc-usdt/raw/backtest-result-2026-11-12_08-21-48.zip`; `research/experiments/20261112T074927Z-h-118-exploration-eth-usdt/raw/backtest-result-2026-11-12_08-32-35.zip`; `research/experiments/20261112T074927Z-h-118-exploration-bnb-usdt/raw/backtest-result-2026-11-12_08-47-21.zip`; `research/experiments/20261112T074927Z-h-118-exploration-xrp-usdt/raw/backtest-result-2026-11-12_09-03-47.zip`; `research/experiments/20261112T074927Z-h-118-exploration-ada-usdt/raw/backtest-result-2026-11-12_09-15-30.zip`; `research/experiments/20261112T074927Z-h-118-exploration-ltc-usdt/raw/backtest-result-2026-11-12_09-28-34.zip`; `research/experiments/20261112T074927Z-h-118-exploration-link-usdt/raw/backtest-result-2026-11-12_09-41-36.zip`; `research/experiments/20261112T074927Z-h-118-exploration-doge-usdt/raw/backtest-result-2026-11-12_09-52-59.zip`; `research/experiments/20261112T074927Z-h-118-exploration-sol-usdt/raw/backtest-result-2026-11-12_10-02-30.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 842; lucro líquido: -123.54.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 507 | -323.98 | – | -1.37% | 0% | 2.7 h |
| take_profit_displacement_high | 218 | 193.47 | – | 1.91% | 100% | 5.0 h |
| time_exit_12h | 117 | 6.98 | – | 0.13% | 58% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 416 | -152.03 | -0.78% | 19% |
| 3 h a 1 dia | 426 | 28.49 | 0.14% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (286): MFE mediano 2.3%, MAE mediano -0.4%, devolução média do melhor ponto 1.0%, captura mediana 0.65.
- Perdedores (556): MAE mediano -1.3%, MFE mediano 0.6%; 25 (4%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 117.03; – do lucro antes de custos.
- Trades < 3 h: 416 (lucro -152.03); reentradas em < 24 h: 345 (lucro -43.40).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -126.78.
- Lucro por ano de fechamento: 2017: -10.3, 2018: -24.5, 2019: -18.5, 2020: -20.1, 2021: -38.4, 2022: -6.8, 2023: 0.3, 2024: -5.3.

## ETH/USDT

Trades: 1047; lucro líquido: -132.89.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 665 | -426.57 | – | -1.38% | 0% | 2.5 h |
| take_profit_displacement_high | 290 | 279.45 | – | 2.09% | 100% | 4.3 h |
| time_exit_12h | 92 | 14.24 | – | 0.34% | 62% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 575 | -190.53 | -0.72% | 21% |
| 3 h a 1 dia | 472 | 57.64 | 0.27% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (347): MFE mediano 2.4%, MAE mediano -0.4%, devolução média do melhor ponto 1.0%, captura mediana 0.69.
- Perdedores (700): MAE mediano -1.3%, MFE mediano 0.6%; 42 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 144.81; 1215% do lucro antes de custos.
- Trades < 3 h: 575 (lucro -190.53); reentradas em < 24 h: 467 (lucro -58.55).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -137.07.
- Lucro por ano de fechamento: 2017: -19.2, 2018: -14.8, 2019: -21.6, 2020: -17.0, 2021: -36.0, 2022: -7.9, 2023: -7.3, 2024: -9.2.

## BNB/USDT

Trades: 1136; lucro líquido: -138.54.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 721 | -489.11 | – | -1.45% | 0% | 2.4 h |
| take_profit_displacement_high | 314 | 329.96 | – | 2.24% | 100% | 4.2 h |
| time_exit_12h | 101 | 20.61 | – | 0.43% | 64% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 637 | -203.55 | -0.68% | 21% |
| 3 h a 1 dia | 499 | 65.01 | 0.27% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (379): MFE mediano 2.5%, MAE mediano -0.4%, devolução média do melhor ponto 1.1%, captura mediana 0.69.
- Perdedores (757): MAE mediano -1.3%, MFE mediano 0.5%; 46 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 158.32; 800% do lucro antes de custos.
- Trades < 3 h: 637 (lucro -203.55); reentradas em < 24 h: 514 (lucro -93.35).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -151.52.
- Lucro por ano de fechamento: 2017: -7.1, 2018: -23.1, 2019: -26.2, 2020: -15.7, 2021: -27.2, 2022: -24.9, 2023: -4.5, 2024: -9.8.

## XRP/USDT

Trades: 937; lucro líquido: -136.48.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 615 | -412.69 | – | -1.45% | 0% | 2.4 h |
| take_profit_displacement_high | 225 | 254.29 | – | 2.45% | 100% | 4.2 h |
| time_exit_12h | 97 | 21.91 | – | 0.49% | 61% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 521 | -171.51 | -0.71% | 20% |
| 3 h a 1 dia | 416 | 35.03 | 0.18% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (284): MFE mediano 2.6%, MAE mediano -0.4%, devolução média do melhor ponto 1.2%, captura mediana 0.67.
- Perdedores (653): MAE mediano -1.3%, MFE mediano 0.6%; 52 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 129.37; – do lucro antes de custos.
- Trades < 3 h: 521 (lucro -171.51); reentradas em < 24 h: 400 (lucro -66.58).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -143.09.
- Lucro por ano de fechamento: 2018: -35.7, 2019: -20.7, 2020: -32.3, 2021: 4.3, 2022: -31.0, 2023: -17.6, 2024: -3.5.

## ADA/USDT

Trades: 1165; lucro líquido: -174.75.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 818 | -520.93 | – | -1.37% | 0% | 2.2 h |
| take_profit_displacement_high | 299 | 334.59 | – | 2.38% | 100% | 4.2 h |
| time_exit_12h | 48 | 11.58 | – | 0.51% | 65% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 721 | -239.59 | -0.72% | 18% |
| 3 h a 1 dia | 444 | 64.84 | 0.30% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (330): MFE mediano 2.7%, MAE mediano -0.4%, devolução média do melhor ponto 1.0%, captura mediana 0.70.
- Perdedores (835): MAE mediano -1.3%, MFE mediano 0.6%; 56 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 161.90; – do lucro antes de custos.
- Trades < 3 h: 721 (lucro -239.59); reentradas em < 24 h: 512 (lucro -76.17).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -183.50.
- Lucro por ano de fechamento: 2018: 2.2, 2019: -26.7, 2020: -35.2, 2021: -42.6, 2022: -31.9, 2023: -22.2, 2024: -18.3.

## LTC/USDT

Trades: 1169; lucro líquido: -171.61.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 792 | -505.84 | – | -1.39% | 0% | 2.4 h |
| take_profit_displacement_high | 303 | 320.09 | – | 2.29% | 100% | 4.2 h |
| time_exit_12h | 74 | 14.13 | – | 0.41% | 68% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 684 | -232.25 | -0.74% | 19% |
| 3 h a 1 dia | 485 | 60.64 | 0.27% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (353): MFE mediano 2.6%, MAE mediano -0.4%, devolução média do melhor ponto 1.1%, captura mediana 0.69.
- Perdedores (816): MAE mediano -1.3%, MFE mediano 0.6%; 73 (9%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 160.34; – do lucro antes de custos.
- Trades < 3 h: 684 (lucro -232.25); reentradas em < 24 h: 510 (lucro -78.45).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -175.82.
- Lucro por ano de fechamento: 2017: -2.0, 2018: -22.3, 2019: -29.6, 2020: -33.2, 2021: -33.4, 2022: -10.3, 2023: -31.6, 2024: -9.2.

## LINK/USDT

Trades: 1125; lucro líquido: -130.34.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 753 | -507.91 | – | -1.44% | 0% | 2.0 h |
| take_profit_displacement_high | 318 | 363.76 | – | 2.45% | 100% | 3.7 h |
| time_exit_12h | 54 | 13.82 | – | 0.54% | 69% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 731 | -219.38 | -0.64% | 21% |
| 3 h a 1 dia | 394 | 89.04 | 0.48% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (355): MFE mediano 2.9%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.69.
- Perdedores (770): MAE mediano -1.3%, MFE mediano 0.6%; 77 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 156.81; 592% do lucro antes de custos.
- Trades < 3 h: 731 (lucro -219.38); reentradas em < 24 h: 527 (lucro -53.86).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -138.21.
- Lucro por ano de fechamento: 2019: -35.7, 2020: -24.0, 2021: -29.7, 2022: -15.0, 2023: -10.4, 2024: -15.4.

## DOGE/USDT

Trades: 859; lucro líquido: -89.90.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 567 | -419.11 | – | -1.53% | 0% | 2.4 h |
| take_profit_displacement_high | 210 | 310.56 | – | 3.07% | 100% | 4.0 h |
| time_exit_12h | 82 | 18.65 | – | 0.47% | 50% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 500 | -143.06 | -0.59% | 20% |
| 3 h a 1 dia | 359 | 53.15 | 0.31% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (251): MFE mediano 2.7%, MAE mediano -0.5%, devolução média do melhor ponto 1.6%, captura mediana 0.69.
- Perdedores (608): MAE mediano -1.3%, MFE mediano 0.6%; 61 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 123.61; 367% do lucro antes de custos.
- Trades < 3 h: 500 (lucro -143.06); reentradas em < 24 h: 378 (lucro -24.01).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -124.19.
- Lucro por ano de fechamento: 2019: -19.5, 2020: -11.5, 2021: 5.0, 2022: -37.0, 2023: -12.3, 2024: -14.6.

## SOL/USDT

Trades: 896; lucro líquido: -108.20.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 626 | -432.95 | – | -1.45% | 0% | 1.8 h |
| take_profit_displacement_high | 230 | 312.76 | – | 2.85% | 100% | 3.5 h |
| time_exit_12h | 40 | 12.00 | – | 0.64% | 60% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 610 | -183.48 | -0.63% | 20% |
| 3 h a 1 dia | 286 | 75.29 | 0.55% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (254): MFE mediano 3.4%, MAE mediano -0.4%, devolução média do melhor ponto 1.3%, captura mediana 0.70.
- Perdedores (642): MAE mediano -1.4%, MFE mediano 0.6%; 71 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 127.17; 670% do lucro antes de custos.
- Trades < 3 h: 610 (lucro -183.48); reentradas em < 24 h: 441 (lucro -73.32).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -115.67.
- Lucro por ano de fechamento: 2020: -10.8, 2021: -16.1, 2022: -45.2, 2023: -28.3, 2024: -7.8.
