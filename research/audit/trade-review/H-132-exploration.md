# Revisão de trades: H-132 (exploração)

Fonte dos trades: `research/experiments/20261113T212835Z-h-132-exploration-btc-usdt/raw/backtest-result-2026-11-13_22-05-01.zip`; `research/experiments/20261113T212835Z-h-132-exploration-eth-usdt/raw/backtest-result-2026-11-13_22-05-52.zip`; `research/experiments/20261113T212835Z-h-132-exploration-bnb-usdt/raw/backtest-result-2026-11-13_22-05-15.zip`; `research/experiments/20261113T212835Z-h-132-exploration-xrp-usdt/raw/backtest-result-2026-11-13_22-16-33.zip`; `research/experiments/20261113T212835Z-h-132-exploration-ada-usdt/raw/backtest-result-2026-11-13_22-17-29.zip`; `research/experiments/20261113T212835Z-h-132-exploration-ltc-usdt/raw/backtest-result-2026-11-13_22-18-49.zip`; `research/experiments/20261113T212835Z-h-132-exploration-link-usdt/raw/backtest-result-2026-11-13_22-28-28.zip`; `research/experiments/20261113T212835Z-h-132-exploration-doge-usdt/raw/backtest-result-2026-11-13_22-28-59.zip`; `research/experiments/20261113T212835Z-h-132-exploration-sol-usdt/raw/backtest-result-2026-11-13_22-30-39.zip`; `research/experiments/20261113T212835Z-h-132-exploration-avax-usdt/raw/backtest-result-2026-11-13_22-39-33.zip`; `research/experiments/20261113T212835Z-h-132-exploration-dot-usdt/raw/backtest-result-2026-11-13_22-39-51.zip`; `research/experiments/20261113T212835Z-h-132-exploration-trx-usdt/raw/backtest-result-2026-11-13_22-41-39.zip`; `research/experiments/20261113T212835Z-h-132-exploration-near-usdt/raw/backtest-result-2026-11-13_22-49-10.zip`; `research/experiments/20261113T212835Z-h-132-exploration-uni-usdt/raw/backtest-result-2026-11-13_22-49-30.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 702; lucro líquido: -101.50.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 444 | -274.81 | – | -1.31% | 0% | 2.6 h |
| take_profit_1p5R | 187 | 172.03 | – | 1.95% | 100% | 4.3 h |
| time_exit_12h | 71 | 1.28 | – | 0.04% | 52% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 397 | -115.89 | -0.62% | 20% |
| 3 h a 1 dia | 305 | 14.39 | 0.10% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (224): MFE mediano 2.4%, MAE mediano -0.4%, devolução média do melhor ponto 0.9%, captura mediana 0.69.
- Perdedores (478): MAE mediano -1.2%, MFE mediano 0.5%; 22 (5%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 98.87; – do lucro antes de custos.
- Trades < 3 h: 397 (lucro -115.89); reentradas em < 24 h: 253 (lucro -51.34).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -103.98.
- Lucro por ano de fechamento: 2017: -9.5, 2018: -30.8, 2019: -8.9, 2020: -6.6, 2021: -33.6, 2022: -11.9, 2023: 1.0, 2024: -1.2.

## ETH/USDT

Trades: 1004; lucro líquido: -158.44.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 677 | -402.57 | – | -1.29% | 0% | 2.8 h |
| take_profit_1p5R | 264 | 242.56 | – | 2.00% | 100% | 3.9 h |
| time_exit_12h | 62 | 2.17 | – | 0.08% | 48% | 12.0 h |
| trailing_stop_loss | 1 | -0.60 | – | -1.38% | 0% | 1.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 557 | -150.83 | -0.59% | 22% |
| 3 h a 1 dia | 447 | -7.61 | -0.04% | 38% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (294): MFE mediano 2.7%, MAE mediano -0.4%, devolução média do melhor ponto 1.0%, captura mediana 0.67.
- Perdedores (710): MAE mediano -1.2%, MFE mediano 0.5%; 28 (4%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 137.46; – do lucro antes de custos.
- Trades < 3 h: 557 (lucro -150.83); reentradas em < 24 h: 412 (lucro -55.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -160.60.
- Lucro por ano de fechamento: 2017: -1.6, 2018: -40.9, 2019: -30.2, 2020: -22.2, 2021: -30.5, 2022: -22.8, 2023: -3.8, 2024: -6.5.

## BNB/USDT

Trades: 826; lucro líquido: -113.85.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 534 | -346.52 | – | -1.37% | 0% | 2.5 h |
| take_profit_1p5R | 243 | 231.13 | – | 2.01% | 100% | 3.8 h |
| time_exit_12h | 49 | 1.54 | – | 0.07% | 45% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 483 | -116.10 | -0.51% | 25% |
| 3 h a 1 dia | 343 | 2.26 | 0.01% | 43% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (265): MFE mediano 2.6%, MAE mediano -0.4%, devolução média do melhor ponto 0.9%, captura mediana 0.70.
- Perdedores (561): MAE mediano -1.3%, MFE mediano 0.5%; 26 (5%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 116.56; 4290% do lucro antes de custos.
- Trades < 3 h: 483 (lucro -116.10); reentradas em < 24 h: 316 (lucro -63.85).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -117.05.
- Lucro por ano de fechamento: 2017: -10.6, 2018: -14.6, 2019: -9.4, 2020: -30.4, 2021: -7.5, 2022: -22.8, 2023: -13.1, 2024: -5.3.

## XRP/USDT

Trades: 811; lucro líquido: -151.16.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 558 | -350.28 | – | -1.36% | 0% | 2.5 h |
| take_profit_1p5R | 201 | 199.28 | – | 2.15% | 100% | 3.4 h |
| time_exit_12h | 52 | -0.16 | – | -0.01% | 50% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 490 | -124.19 | -0.55% | 22% |
| 3 h a 1 dia | 321 | -26.98 | -0.18% | 37% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (227): MFE mediano 2.7%, MAE mediano -0.4%, devolução média do melhor ponto 1.3%, captura mediana 0.68.
- Perdedores (584): MAE mediano -1.3%, MFE mediano 0.5%; 29 (5%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 111.74; – do lucro antes de custos.
- Trades < 3 h: 490 (lucro -124.19); reentradas em < 24 h: 285 (lucro -51.68).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -154.01.
- Lucro por ano de fechamento: 2018: -29.2, 2019: -29.7, 2020: -14.0, 2021: -25.6, 2022: -25.6, 2023: -20.9, 2024: -6.2.

## ADA/USDT

Trades: 970; lucro líquido: -109.47.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 647 | -421.30 | – | -1.37% | 0% | 2.4 h |
| take_profit_1p5R | 289 | 312.35 | – | 2.28% | 100% | 3.3 h |
| time_exit_12h | 34 | -0.52 | – | -0.02% | 44% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 628 | -110.13 | -0.37% | 27% |
| 3 h a 1 dia | 342 | 0.66 | 0.00% | 39% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (304): MFE mediano 3.0%, MAE mediano -0.4%, devolução média do melhor ponto 1.1%, captura mediana 0.69.
- Perdedores (666): MAE mediano -1.3%, MFE mediano 0.6%; 37 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 137.50; 491% do lucro antes de custos.
- Trades < 3 h: 628 (lucro -110.13); reentradas em < 24 h: 393 (lucro -27.80).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -112.01.
- Lucro por ano de fechamento: 2018: -25.2, 2019: -15.9, 2020: -20.5, 2021: -5.8, 2022: -14.8, 2023: -16.9, 2024: -10.4.

## LTC/USDT

Trades: 1024; lucro líquido: -232.76.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 752 | -450.21 | – | -1.34% | 0% | 2.5 h |
| take_profit_1p5R | 224 | 218.53 | – | 2.16% | 100% | 3.4 h |
| time_exit_12h | 47 | -0.15 | – | -0.01% | 47% | 12.0 h |
| trailing_stop_loss | 1 | -0.93 | – | -2.14% | 0% | 9.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 628 | -192.09 | -0.69% | 18% |
| 3 h a 1 dia | 396 | -40.67 | -0.24% | 33% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (246): MFE mediano 2.8%, MAE mediano -0.5%, devolução média do melhor ponto 1.2%, captura mediana 0.68.
- Perdedores (778): MAE mediano -1.2%, MFE mediano 0.6%; 41 (5%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 136.39; – do lucro antes de custos.
- Trades < 3 h: 628 (lucro -192.09); reentradas em < 24 h: 393 (lucro -88.90).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -236.31.
- Lucro por ano de fechamento: 2017: -1.7, 2018: -29.6, 2019: -34.3, 2020: -39.0, 2021: -47.8, 2022: -41.2, 2023: -24.4, 2024: -14.9.

## LINK/USDT

Trades: 930; lucro líquido: -143.23.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 629 | -429.44 | – | -1.45% | 0% | 2.3 h |
| take_profit_1p5R | 259 | 282.19 | – | 2.29% | 100% | 3.4 h |
| time_exit_12h | 41 | 4.69 | – | 0.24% | 54% | 12.0 h |
| trailing_stop_loss | 1 | -0.68 | – | -1.56% | 0% | 5.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 590 | -149.05 | -0.54% | 24% |
| 3 h a 1 dia | 340 | 5.82 | 0.03% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (281): MFE mediano 2.9%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.70.
- Perdedores (649): MAE mediano -1.4%, MFE mediano 0.6%; 53 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 131.06; – do lucro antes de custos.
- Trades < 3 h: 590 (lucro -149.05); reentradas em < 24 h: 368 (lucro -62.56).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -145.98.
- Lucro por ano de fechamento: 2019: -20.4, 2020: -7.3, 2021: -47.4, 2022: -30.2, 2023: -20.1, 2024: -17.8.

## DOGE/USDT

Trades: 649; lucro líquido: -105.04.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 438 | -288.37 | – | -1.40% | 0% | 2.5 h |
| take_profit_1p5R | 169 | 185.83 | – | 2.34% | 100% | 3.7 h |
| time_exit_12h | 42 | -2.50 | – | -0.12% | 36% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 400 | -96.90 | -0.51% | 23% |
| 3 h a 1 dia | 249 | -8.13 | -0.07% | 37% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (184): MFE mediano 2.9%, MAE mediano -0.4%, devolução média do melhor ponto 1.3%, captura mediana 0.67.
- Perdedores (465): MAE mediano -1.3%, MFE mediano 0.6%; 25 (5%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 91.39; – do lucro antes de custos.
- Trades < 3 h: 400 (lucro -96.90); reentradas em < 24 h: 218 (lucro -47.46).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -109.47.
- Lucro por ano de fechamento: 2019: -19.4, 2020: -27.7, 2021: -12.1, 2022: -22.6, 2023: -13.6, 2024: -9.5.

## SOL/USDT

Trades: 726; lucro líquido: -76.58.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 478 | -337.77 | – | -1.45% | 0% | 2.0 h |
| take_profit_1p5R | 234 | 260.41 | – | 2.28% | 100% | 2.6 h |
| time_exit_12h | 13 | 1.37 | – | 0.21% | 62% | 12.0 h |
| trailing_stop_loss | 1 | -0.59 | – | -1.26% | 0% | 3.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 514 | -84.43 | -0.34% | 30% |
| 3 h a 1 dia | 212 | 7.85 | 0.08% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (242): MFE mediano 3.0%, MAE mediano -0.4%, devolução média do melhor ponto 1.2%, captura mediana 0.69.
- Perdedores (484): MAE mediano -1.4%, MFE mediano 0.6%; 43 (9%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 105.66; 363% do lucro antes de custos.
- Trades < 3 h: 514 (lucro -84.43); reentradas em < 24 h: 303 (lucro -38.90).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -80.15.
- Lucro por ano de fechamento: 2020: -1.2, 2021: -11.0, 2022: -31.4, 2023: -13.8, 2024: -19.2.

## AVAX/USDT

Trades: 591; lucro líquido: -67.87.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 399 | -291.87 | – | -1.51% | 0% | 1.9 h |
| take_profit_1p5R | 176 | 222.85 | – | 2.61% | 100% | 3.2 h |
| time_exit_12h | 16 | 1.15 | – | 0.15% | 62% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 418 | -90.90 | -0.45% | 24% |
| 3 h a 1 dia | 173 | 23.03 | 0.28% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (186): MFE mediano 3.4%, MAE mediano -0.5%, devolução média do melhor ponto 1.3%, captura mediana 0.72.
- Perdedores (405): MAE mediano -1.4%, MFE mediano 0.6%; 29 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 85.59; 483% do lucro antes de custos.
- Trades < 3 h: 418 (lucro -90.90); reentradas em < 24 h: 245 (lucro -3.76).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -71.73.
- Lucro por ano de fechamento: 2020: -9.2, 2021: -10.9, 2022: -21.1, 2023: -15.4, 2024: -11.3.

## DOT/USDT

Trades: 556; lucro líquido: -107.62.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 386 | -261.98 | – | -1.43% | 0% | 2.2 h |
| take_profit_1p5R | 144 | 155.64 | – | 2.28% | 100% | 3.6 h |
| time_exit_12h | 26 | -1.28 | – | -0.10% | 42% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 367 | -116.38 | -0.67% | 20% |
| 3 h a 1 dia | 189 | 8.76 | 0.09% | 43% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (155): MFE mediano 2.7%, MAE mediano -0.5%, devolução média do melhor ponto 1.0%, captura mediana 0.72.
- Perdedores (401): MAE mediano -1.4%, MFE mediano 0.5%; 21 (5%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 78.54; – do lucro antes de custos.
- Trades < 3 h: 367 (lucro -116.38); reentradas em < 24 h: 219 (lucro -46.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -110.50.
- Lucro por ano de fechamento: 2020: -13.0, 2021: -36.6, 2022: -29.7, 2023: -11.6, 2024: -16.7.

## TRX/USDT

Trades: 636; lucro líquido: -79.03.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 408 | -271.97 | – | -1.39% | 0% | 2.5 h |
| take_profit_1p5R | 186 | 192.27 | – | 2.17% | 100% | 4.0 h |
| time_exit_12h | 42 | 0.67 | – | 0.03% | 57% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 371 | -80.83 | -0.45% | 25% |
| 3 h a 1 dia | 265 | 1.80 | 0.02% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (210): MFE mediano 2.6%, MAE mediano -0.4%, devolução média do melhor ponto 1.1%, captura mediana 0.68.
- Perdedores (426): MAE mediano -1.2%, MFE mediano 0.5%; 34 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 90.95; 763% do lucro antes de custos.
- Trades < 3 h: 371 (lucro -80.83); reentradas em < 24 h: 230 (lucro -36.53).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -82.39.
- Lucro por ano de fechamento: 2018: -18.3, 2019: -18.9, 2020: -19.9, 2021: -19.4, 2022: -4.4, 2023: 2.3, 2024: -0.5.

## NEAR/USDT

Trades: 614; lucro líquido: -90.35.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 418 | -305.15 | – | -1.54% | 0% | 1.8 h |
| take_profit_1p5R | 184 | 212.09 | – | 2.43% | 100% | 3.0 h |
| time_exit_12h | 12 | 2.72 | – | 0.48% | 92% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 448 | -107.86 | -0.51% | 26% |
| 3 h a 1 dia | 166 | 17.51 | 0.22% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (195): MFE mediano 3.1%, MAE mediano -0.4%, devolução média do melhor ponto 1.1%, captura mediana 0.69.
- Perdedores (419): MAE mediano -1.6%, MFE mediano 0.6%; 38 (9%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 87.03; – do lucro antes de custos.
- Trades < 3 h: 448 (lucro -107.86); reentradas em < 24 h: 258 (lucro -58.76).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -92.72.
- Lucro por ano de fechamento: 2020: -8.2, 2021: -29.3, 2022: -27.2, 2023: -14.3, 2024: -11.3.

## UNI/USDT

Trades: 548; lucro líquido: -92.20.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 377 | -267.80 | – | -1.48% | 0% | 2.1 h |
| take_profit_1p5R | 155 | 172.46 | – | 2.31% | 100% | 3.4 h |
| time_exit_12h | 16 | 3.15 | – | 0.40% | 69% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 357 | -109.85 | -0.64% | 22% |
| 3 h a 1 dia | 191 | 17.65 | 0.19% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (166): MFE mediano 2.8%, MAE mediano -0.4%, devolução média do melhor ponto 1.0%, captura mediana 0.71.
- Perdedores (382): MAE mediano -1.4%, MFE mediano 0.5%; 31 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 78.49; – do lucro antes de custos.
- Trades < 3 h: 357 (lucro -109.85); reentradas em < 24 h: 194 (lucro -26.96).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -94.97.
- Lucro por ano de fechamento: 2020: 3.8, 2021: -53.3, 2022: -1.9, 2023: -17.8, 2024: -23.1.
