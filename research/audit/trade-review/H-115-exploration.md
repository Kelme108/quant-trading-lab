# Revisão de trades: H-115 (exploração)

Fonte dos trades: `research/experiments/20261112T011803Z-h-115-exploration-btc-usdt/raw/backtest-result-2026-11-12_01-40-29.zip`; `research/experiments/20261112T011803Z-h-115-exploration-eth-usdt/raw/backtest-result-2026-11-12_01-49-35.zip`; `research/experiments/20261112T011803Z-h-115-exploration-bnb-usdt/raw/backtest-result-2026-11-12_01-58-36.zip`; `research/experiments/20261112T011803Z-h-115-exploration-xrp-usdt/raw/backtest-result-2026-11-12_02-07-49.zip`; `research/experiments/20261112T011803Z-h-115-exploration-ada-usdt/raw/backtest-result-2026-11-12_02-16-52.zip`; `research/experiments/20261112T011803Z-h-115-exploration-ltc-usdt/raw/backtest-result-2026-11-12_02-25-21.zip`; `research/experiments/20261112T011803Z-h-115-exploration-link-usdt/raw/backtest-result-2026-11-12_02-34-15.zip`; `research/experiments/20261112T011803Z-h-115-exploration-doge-usdt/raw/backtest-result-2026-11-12_02-41-25.zip`; `research/experiments/20261112T011803Z-h-115-exploration-sol-usdt/raw/backtest-result-2026-11-12_02-48-04.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 840; lucro líquido: -212.03.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 424 | -556.31 | – | -1.47% | 0% | 4.3 h |
| time_exit_12h | 260 | 31.42 | – | 0.13% | 53% | 12.0 h |
| take_profit_1_5R | 156 | 312.86 | – | 2.25% | 100% | 5.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 223 | -161.59 | -0.80% | 17% |
| 3 h a 1 dia | 617 | -50.43 | -0.10% | 41% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (294): MFE mediano 2.2%, MAE mediano -0.4%, devolução média do melhor ponto 1.0%, captura mediana 0.63.
- Perdedores (546): MAE mediano -1.3%, MFE mediano 0.6%; 28 (5%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 222.22; 2179% do lucro antes de custos.
- Trades < 3 h: 223 (lucro -161.59); reentradas em < 24 h: 295 (lucro -75.25).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -218.88.
- Lucro por ano de fechamento: 2017: -18.3, 2018: -59.6, 2019: -13.0, 2020: -17.5, 2021: -33.6, 2022: -32.1, 2023: -17.0, 2024: -20.9.

## ETH/USDT

Trades: 718; lucro líquido: -92.54.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 344 | -576.70 | – | -1.74% | 0% | 4.4 h |
| time_exit_12h | 210 | 61.54 | – | 0.30% | 61% | 12.0 h |
| take_profit_1_5R | 164 | 422.62 | – | 2.67% | 100% | 5.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 182 | -97.49 | -0.56% | 25% |
| 3 h a 1 dia | 536 | 4.95 | 0.01% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (292): MFE mediano 2.8%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.65.
- Perdedores (426): MAE mediano -1.6%, MFE mediano 0.6%; 29 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 206.67; 181% do lucro antes de custos.
- Trades < 3 h: 182 (lucro -97.49); reentradas em < 24 h: 233 (lucro -55.20).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -98.86.
- Lucro por ano de fechamento: 2017: 1.1, 2018: -44.7, 2019: 3.0, 2020: 6.6, 2021: -7.0, 2022: -7.1, 2023: -22.2, 2024: -22.3.

## BNB/USDT

Trades: 798; lucro líquido: -100.89.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 377 | -670.53 | – | -1.82% | 0% | 4.3 h |
| time_exit_12h | 231 | 56.44 | – | 0.25% | 57% | 12.0 h |
| take_profit_1_5R | 189 | 513.10 | – | 2.77% | 100% | 5.7 h |
| force_exit | 1 | 0.10 | – | 0.11% | 100% | 1.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 199 | -173.50 | -0.89% | 20% |
| 3 h a 1 dia | 599 | 72.61 | 0.12% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (322): MFE mediano 2.8%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.67.
- Perdedores (476): MAE mediano -1.6%, MFE mediano 0.7%; 46 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 232.18; 177% do lucro antes de custos.
- Trades < 3 h: 199 (lucro -173.50); reentradas em < 24 h: 273 (lucro -55.53).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -111.55.
- Lucro por ano de fechamento: 2017: -6.1, 2018: 23.2, 2019: -31.8, 2020: 9.3, 2021: -35.3, 2022: -15.6, 2023: -3.8, 2024: -40.7.

## XRP/USDT

Trades: 754; lucro líquido: -202.58.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 371 | -615.76 | – | -1.77% | 0% | 4.2 h |
| time_exit_12h | 240 | 26.09 | – | 0.11% | 52% | 12.0 h |
| take_profit_1_5R | 142 | 388.53 | – | 2.87% | 100% | 5.3 h |
| trailing_stop_loss | 1 | -1.44 | – | -1.76% | 0% | 9.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 202 | -170.14 | -0.90% | 17% |
| 3 h a 1 dia | 552 | -32.44 | -0.08% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (266): MFE mediano 2.9%, MAE mediano -0.6%, devolução média do melhor ponto 1.3%, captura mediana 0.62.
- Perdedores (488): MAE mediano -1.7%, MFE mediano 0.6%; 41 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 212.05; 2239% do lucro antes de custos.
- Trades < 3 h: 202 (lucro -170.14); reentradas em < 24 h: 272 (lucro -78.39).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -209.33.
- Lucro por ano de fechamento: 2018: -26.3, 2019: 8.8, 2020: -7.7, 2021: -2.5, 2022: -75.5, 2023: -48.9, 2024: -50.4.

## ADA/USDT

Trades: 652; lucro líquido: -159.42.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 336 | -614.19 | – | -1.92% | 0% | 4.1 h |
| time_exit_12h | 172 | 51.85 | – | 0.32% | 60% | 12.0 h |
| take_profit_1_5R | 144 | 402.93 | – | 2.92% | 100% | 5.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 200 | -149.80 | -0.80% | 20% |
| 3 h a 1 dia | 452 | -9.62 | -0.03% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (247): MFE mediano 2.9%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.66.
- Perdedores (405): MAE mediano -1.8%, MFE mediano 0.7%; 41 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 185.31; 716% do lucro antes de custos.
- Trades < 3 h: 200 (lucro -149.80); reentradas em < 24 h: 199 (lucro -10.05).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -165.41.
- Lucro por ano de fechamento: 2018: -14.1, 2019: 17.8, 2020: -10.2, 2021: -47.6, 2022: -26.2, 2023: -39.6, 2024: -39.5.

## LTC/USDT

Trades: 760; lucro líquido: -122.60.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 364 | -659.02 | – | -1.90% | 0% | 4.2 h |
| time_exit_12h | 225 | 74.19 | – | 0.35% | 64% | 12.0 h |
| take_profit_1_5R | 171 | 462.23 | – | 2.82% | 100% | 5.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 215 | -169.71 | -0.83% | 20% |
| 3 h a 1 dia | 545 | 47.11 | 0.09% | 50% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (314): MFE mediano 2.9%, MAE mediano -0.6%, devolução média do melhor ponto 1.2%, captura mediana 0.65.
- Perdedores (446): MAE mediano -1.8%, MFE mediano 0.7%; 31 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 216.72; 230% do lucro antes de custos.
- Trades < 3 h: 215 (lucro -169.71); reentradas em < 24 h: 237 (lucro -45.77).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -130.52.
- Lucro por ano de fechamento: 2018: -36.3, 2019: 9.3, 2020: -14.2, 2021: -10.8, 2022: -2.9, 2023: -36.5, 2024: -31.2.

## LINK/USDT

Trades: 611; lucro líquido: -41.64.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 312 | -653.80 | – | -2.06% | 0% | 4.1 h |
| take_profit_1_5R | 162 | 540.79 | – | 3.28% | 100% | 5.6 h |
| time_exit_12h | 136 | 74.74 | – | 0.54% | 66% | 12.0 h |
| trailing_stop_loss | 1 | -3.38 | – | -3.26% | 0% | 7.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 182 | -132.58 | -0.71% | 24% |
| 3 h a 1 dia | 429 | 90.94 | 0.20% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (252): MFE mediano 3.5%, MAE mediano -0.6%, devolução média do melhor ponto 1.2%, captura mediana 0.71.
- Perdedores (359): MAE mediano -2.1%, MFE mediano 0.7%; 44 (12%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 185.75; 129% do lucro antes de custos.
- Trades < 3 h: 182 (lucro -132.58); reentradas em < 24 h: 190 (lucro -9.14).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -48.63.
- Lucro por ano de fechamento: 2019: 13.1, 2020: 37.9, 2021: -33.7, 2022: -17.7, 2023: -15.0, 2024: -26.3.

## DOGE/USDT

Trades: 584; lucro líquido: -203.02.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 301 | -492.83 | – | -1.85% | 0% | 4.1 h |
| time_exit_12h | 177 | 40.98 | – | 0.26% | 57% | 12.0 h |
| take_profit_1_5R | 106 | 248.82 | – | 2.69% | 100% | 5.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 168 | -183.41 | -1.23% | 13% |
| 3 h a 1 dia | 416 | -19.61 | -0.05% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (207): MFE mediano 2.6%, MAE mediano -0.6%, devolução média do melhor ponto 1.2%, captura mediana 0.64.
- Perdedores (377): MAE mediano -1.7%, MFE mediano 0.7%; 38 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 154.24; – do lucro antes de custos.
- Trades < 3 h: 168 (lucro -183.41); reentradas em < 24 h: 201 (lucro -81.62).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -211.70.
- Lucro por ano de fechamento: 2019: -31.0, 2020: -39.7, 2021: -49.2, 2022: -49.9, 2023: -9.1, 2024: -24.0.

## SOL/USDT

Trades: 399; lucro líquido: -146.18.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 219 | -449.00 | – | -2.18% | 0% | 3.6 h |
| time_exit_12h | 96 | 41.10 | – | 0.46% | 60% | 12.0 h |
| take_profit_1_5R | 84 | 261.71 | – | 3.28% | 100% | 5.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 134 | -164.07 | -1.31% | 16% |
| 3 h a 1 dia | 265 | 17.89 | 0.07% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (142): MFE mediano 3.5%, MAE mediano -0.7%, devolução média do melhor ponto 1.2%, captura mediana 0.69.
- Perdedores (257): MAE mediano -2.3%, MFE mediano 0.8%; 37 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 111.82; – do lucro antes de custos.
- Trades < 3 h: 134 (lucro -164.07); reentradas em < 24 h: 123 (lucro -64.89).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -152.01.
- Lucro por ano de fechamento: 2020: -2.7, 2021: -38.3, 2022: -28.1, 2023: -37.0, 2024: -39.9.
