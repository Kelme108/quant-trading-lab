# Revisão de trades: H-120 (exploração)

Fonte dos trades: `research/experiments/20261112T113118Z-h-120-exploration-btc-usdt/raw/backtest-result-2026-11-12_11-44-22.zip`; `research/experiments/20261112T113118Z-h-120-exploration-eth-usdt/raw/backtest-result-2026-11-12_11-50-02.zip`; `research/experiments/20261112T113118Z-h-120-exploration-bnb-usdt/raw/backtest-result-2026-11-12_11-56-12.zip`; `research/experiments/20261112T113118Z-h-120-exploration-xrp-usdt/raw/backtest-result-2026-11-12_12-02-01.zip`; `research/experiments/20261112T113118Z-h-120-exploration-ada-usdt/raw/backtest-result-2026-11-12_12-08-11.zip`; `research/experiments/20261112T113118Z-h-120-exploration-ltc-usdt/raw/backtest-result-2026-11-12_12-15-35.zip`; `research/experiments/20261112T113118Z-h-120-exploration-link-usdt/raw/backtest-result-2026-11-12_12-21-41.zip`; `research/experiments/20261112T113118Z-h-120-exploration-doge-usdt/raw/backtest-result-2026-11-12_12-30-45.zip`; `research/experiments/20261112T113118Z-h-120-exploration-sol-usdt/raw/backtest-result-2026-11-12_12-39-42.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 304; lucro líquido: -143.33.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 159 | -321.25 | – | -2.19% | 0% | 3.4 h |
| target_mid_range | 87 | 174.67 | – | 2.19% | 100% | 4.1 h |
| time_exit_48_bars | 58 | 3.24 | – | 0.06% | 47% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 136 | -97.05 | -0.78% | 32% |
| 3 h a 1 dia | 168 | -46.28 | -0.29% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (114): MFE mediano 2.5%, MAE mediano -0.7%, devolução média do melhor ponto 1.0%, captura mediana 0.64.
- Perdedores (190): MAE mediano -1.9%, MFE mediano 0.7%; 16 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 83.06; – do lucro antes de custos.
- Trades < 3 h: 136 (lucro -97.05); reentradas em < 24 h: 35 (lucro -9.97).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -149.92.
- Lucro por ano de fechamento: 2017: -26.0, 2018: -34.2, 2019: -23.3, 2020: 0.4, 2021: -23.8, 2022: -18.3, 2023: -4.8, 2024: -13.5.

## ETH/USDT

Trades: 338; lucro líquido: -89.65.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 168 | -417.80 | – | -2.60% | 0% | 3.8 h |
| target_mid_range | 114 | 326.67 | – | 3.00% | 100% | 4.2 h |
| time_exit_48_bars | 56 | 1.47 | – | 0.04% | 54% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 137 | -62.96 | -0.47% | 38% |
| 3 h a 1 dia | 201 | -26.69 | -0.14% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (144): MFE mediano 2.9%, MAE mediano -0.8%, devolução média do melhor ponto 1.2%, captura mediana 0.69.
- Perdedores (194): MAE mediano -2.4%, MFE mediano 0.9%; 35 (18%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 96.01; 1511% do lucro antes de custos.
- Trades < 3 h: 137 (lucro -62.96); reentradas em < 24 h: 54 (lucro -12.04).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -101.60.
- Lucro por ano de fechamento: 2017: 24.2, 2018: -56.5, 2019: -27.0, 2020: -10.5, 2021: -3.7, 2022: 2.2, 2023: -8.3, 2024: -10.1.

## BNB/USDT

Trades: 377; lucro líquido: -150.19.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 192 | -466.92 | – | -2.57% | 0% | 3.4 h |
| target_mid_range | 129 | 314.39 | – | 2.56% | 100% | 3.9 h |
| time_exit_48_bars | 56 | 2.35 | – | 0.05% | 52% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 167 | -127.07 | -0.80% | 37% |
| 3 h a 1 dia | 210 | -23.11 | -0.13% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (158): MFE mediano 2.6%, MAE mediano -0.8%, devolução média do melhor ponto 1.1%, captura mediana 0.69.
- Perdedores (219): MAE mediano -2.2%, MFE mediano 0.8%; 21 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 105.72; – do lucro antes de custos.
- Trades < 3 h: 167 (lucro -127.07); reentradas em < 24 h: 64 (lucro 1.17).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -164.46.
- Lucro por ano de fechamento: 2017: 39.7, 2018: -54.2, 2019: -28.8, 2020: -12.4, 2021: -26.7, 2022: -41.8, 2023: -14.0, 2024: -11.9.

## XRP/USDT

Trades: 283; lucro líquido: -124.19.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 130 | -358.14 | – | -2.96% | 0% | 3.7 h |
| target_mid_range | 96 | 230.38 | – | 2.60% | 100% | 4.2 h |
| time_exit_48_bars | 56 | 3.95 | – | 0.08% | 54% | 12.0 h |
| force_exit | 1 | -0.38 | – | -0.43% | 0% | 9.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 113 | -70.48 | -0.67% | 37% |
| 3 h a 1 dia | 170 | -53.71 | -0.33% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (126): MFE mediano 2.6%, MAE mediano -0.8%, devolução média do melhor ponto 1.1%, captura mediana 0.67.
- Perdedores (157): MAE mediano -2.6%, MFE mediano 0.9%; 29 (18%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 78.06; – do lucro antes de custos.
- Trades < 3 h: 113 (lucro -70.48); reentradas em < 24 h: 38 (lucro -1.61).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -138.65.
- Lucro por ano de fechamento: 2018: -27.0, 2019: -31.8, 2020: -7.5, 2021: -32.8, 2022: -28.0, 2023: 9.9, 2024: -6.9.

## ADA/USDT

Trades: 334; lucro líquido: -181.63.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 173 | -417.60 | – | -2.69% | 0% | 3.4 h |
| target_mid_range | 111 | 242.09 | – | 2.46% | 100% | 3.9 h |
| time_exit_48_bars | 50 | -6.11 | – | -0.13% | 42% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 158 | -133.29 | -0.93% | 36% |
| 3 h a 1 dia | 176 | -48.34 | -0.30% | 43% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (132): MFE mediano 2.9%, MAE mediano -0.8%, devolução média do melhor ponto 1.0%, captura mediana 0.70.
- Perdedores (202): MAE mediano -2.4%, MFE mediano 0.8%; 33 (16%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 88.78; – do lucro antes de custos.
- Trades < 3 h: 158 (lucro -133.29); reentradas em < 24 h: 47 (lucro -3.56).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -188.77.
- Lucro por ano de fechamento: 2018: -31.8, 2019: -42.1, 2020: -26.9, 2021: -36.5, 2022: -33.3, 2023: -10.6, 2024: -0.5.

## LTC/USDT

Trades: 339; lucro líquido: -144.00.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 163 | -426.67 | – | -2.82% | 0% | 4.0 h |
| target_mid_range | 108 | 276.41 | – | 2.77% | 100% | 4.1 h |
| time_exit_48_bars | 68 | 6.25 | – | 0.11% | 53% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 129 | -93.56 | -0.78% | 37% |
| 3 h a 1 dia | 210 | -50.44 | -0.25% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (144): MFE mediano 2.9%, MAE mediano -0.7%, devolução média do melhor ponto 1.2%, captura mediana 0.68.
- Perdedores (195): MAE mediano -2.7%, MFE mediano 0.8%; 27 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 93.17; – do lucro antes de custos.
- Trades < 3 h: 129 (lucro -93.56); reentradas em < 24 h: 48 (lucro -4.35).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -157.46.
- Lucro por ano de fechamento: 2018: -30.4, 2019: -38.5, 2020: -5.7, 2021: -22.8, 2022: -36.6, 2023: -4.6, 2024: -5.5.

## LINK/USDT

Trades: 284; lucro líquido: -48.15.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 131 | -366.01 | – | -2.78% | 0% | 3.5 h |
| target_mid_range | 99 | 307.48 | – | 3.09% | 100% | 3.8 h |
| time_exit_48_bars | 53 | 10.62 | – | 0.20% | 51% | 12.0 h |
| force_exit | 1 | -0.24 | – | -0.25% | 0% | 9.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 125 | -24.26 | -0.19% | 43% |
| 3 h a 1 dia | 159 | -23.89 | -0.15% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (126): MFE mediano 3.2%, MAE mediano -1.1%, devolução média do melhor ponto 1.3%, captura mediana 0.70.
- Perdedores (158): MAE mediano -2.8%, MFE mediano 0.8%; 25 (16%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 85.09; 230% do lucro antes de custos.
- Trades < 3 h: 125 (lucro -24.26); reentradas em < 24 h: 39 (lucro -17.59).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -70.00.
- Lucro por ano de fechamento: 2019: 2.9, 2020: 19.0, 2021: -17.4, 2022: -5.3, 2023: -35.0, 2024: -12.4.

## DOGE/USDT

Trades: 227; lucro líquido: -56.05.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trailing_stop_loss | 93 | -270.20 | – | -3.01% | 0% | 3.3 h |
| target_mid_range | 86 | 232.47 | – | 2.81% | 100% | 4.1 h |
| time_exit_48_bars | 46 | 11.55 | – | 0.26% | 59% | 12.0 h |
| stop_loss | 2 | -29.86 | – | -15.25% | 0% | 3.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 85 | -39.64 | -0.46% | 42% |
| 3 h a 1 dia | 142 | -16.41 | -0.12% | 54% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (113): MFE mediano 3.2%, MAE mediano -0.7%, devolução média do melhor ponto 1.3%, captura mediana 0.68.
- Perdedores (114): MAE mediano -2.7%, MFE mediano 0.9%; 21 (18%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 65.33; 704% do lucro antes de custos.
- Trades < 3 h: 85 (lucro -39.64); reentradas em < 24 h: 28 (lucro -23.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -70.46.
- Lucro por ano de fechamento: 2019: 5.6, 2020: -1.3, 2021: -61.6, 2022: -8.1, 2023: 3.7, 2024: 5.6.

## SOL/USDT

Trades: 210; lucro líquido: 69.31.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| target_mid_range | 87 | 351.85 | 508% | 3.84% | 100% | 4.4 h |
| trailing_stop_loss | 87 | -292.08 | -421% | -3.16% | 0% | 3.3 h |
| time_exit_48_bars | 35 | 10.47 | 15% | 0.29% | 51% | 12.0 h |
| force_exit | 1 | -0.93 | -1% | -0.87% | 0% | 9.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 81 | -9.32 | -0.09% | 40% |
| 3 h a 1 dia | 129 | 78.63 | 0.59% | 57% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (105): MFE mediano 4.2%, MAE mediano -1.1%, devolução média do melhor ponto 1.7%, captura mediana 0.72.
- Perdedores (105): MAE mediano -3.0%, MFE mediano 1.0%; 25 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 66.83; 49% do lucro antes de custos.
- Trades < 3 h: 81 (lucro -9.32); reentradas em < 24 h: 18 (lucro 12.03).
- Maior trade = 18% do lucro; top 5 = 76%; top 10 = 125%; lucro sem o melhor = 56.81.
- Lucro por ano de fechamento: 2020: 55.0, 2021: 15.4, 2022: -11.1, 2023: 31.6, 2024: -21.6.
