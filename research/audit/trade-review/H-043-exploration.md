# Revisão de trades: H-043 (exploração)

Fonte dos trades: `research/experiments/20261110T112808Z-h-043-exploration-btc-usdt/raw/backtest-result-2026-11-10_11-34-01.zip`; `research/experiments/20261110T112808Z-h-043-exploration-eth-usdt/raw/backtest-result-2026-11-10_11-36-35.zip`; `research/experiments/20261110T112808Z-h-043-exploration-bnb-usdt/raw/backtest-result-2026-11-10_11-39-10.zip`; `research/experiments/20261110T112808Z-h-043-exploration-xrp-usdt/raw/backtest-result-2026-11-10_11-41-41.zip`; `research/experiments/20261110T112808Z-h-043-exploration-ada-usdt/raw/backtest-result-2026-11-10_11-44-11.zip`; `research/experiments/20261110T112808Z-h-043-exploration-ltc-usdt/raw/backtest-result-2026-11-10_11-46-53.zip`; `research/experiments/20261110T112808Z-h-043-exploration-link-usdt/raw/backtest-result-2026-11-10_11-49-36.zip`; `research/experiments/20261110T112808Z-h-043-exploration-doge-usdt/raw/backtest-result-2026-11-10_11-52-01.zip`; `research/experiments/20261110T112808Z-h-043-exploration-sol-usdt/raw/backtest-result-2026-11-10_11-55-00.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 249; lucro líquido: 150.01.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 226 | 338.21 | 225% | 0.92% | 57% | 12.7 h |
| stop_loss | 17 | -147.25 | -98% | -5.28% | 0% | 8.6 h |
| below_open_minus_half_range | 6 | -40.96 | -27% | -4.04% | 0% | 9.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 4 | -30.06 | -4.68% | 0% |
| 3 h a 1 dia | 245 | 180.07 | 0.46% | 52% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (128): MFE mediano 3.3%, MAE mediano -0.7%, devolução média do melhor ponto 1.8%, captura mediana 0.52.
- Perdedores (121): MAE mediano -2.2%, MFE mediano 0.9%; 18 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 124.35; 45% do lucro antes de custos.
- Trades < 3 h: 4 (lucro -30.06); reentradas em < 24 h: 41 (lucro 30.85).
- Maior trade = 11% do lucro; top 5 = 46%; top 10 = 85%; lucro sem o melhor = 133.39.
- Lucro por ano de fechamento: 2017: 22.2, 2018: 27.8, 2019: 26.7, 2020: 72.7, 2021: 9.0, 2022: -35.4, 2023: 8.0, 2024: 19.0.

## ETH/USDT

Trades: 262; lucro líquido: 184.06.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 230 | 459.01 | 249% | 1.22% | 61% | 12.6 h |
| stop_loss | 29 | -254.89 | -138% | -5.28% | 0% | 6.1 h |
| below_open_minus_half_range | 3 | -20.05 | -11% | -3.87% | 0% | 9.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 7 | -57.06 | -5.28% | 0% |
| 3 h a 1 dia | 255 | 241.12 | 0.60% | 55% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (140): MFE mediano 4.1%, MAE mediano -0.8%, devolução média do melhor ponto 2.2%, captura mediana 0.55.
- Perdedores (122): MAE mediano -2.9%, MFE mediano 1.1%; 26 (21%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 133.26; 42% do lucro antes de custos.
- Trades < 3 h: 7 (lucro -57.06); reentradas em < 24 h: 36 (lucro 59.31).
- Maior trade = 18% do lucro; top 5 = 58%; top 10 = 92%; lucro sem o melhor = 150.65.
- Lucro por ano de fechamento: 2017: -9.8, 2018: 7.1, 2019: 4.1, 2020: 154.3, 2021: 68.9, 2022: -15.9, 2023: -14.7, 2024: -9.9.

## BNB/USDT

Trades: 292; lucro líquido: 317.81.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 247 | 741.44 | 233% | 1.68% | 62% | 13.1 h |
| stop_loss | 38 | -376.00 | -118% | -5.28% | 0% | 6.5 h |
| below_open_minus_half_range | 7 | -47.63 | -15% | -3.60% | 0% | 11.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 10 | -102.02 | -5.28% | 0% |
| 3 h a 1 dia | 282 | 419.83 | 0.86% | 54% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (152): MFE mediano 3.6%, MAE mediano -1.0%, devolução média do melhor ponto 2.2%, captura mediana 0.53.
- Perdedores (140): MAE mediano -3.0%, MFE mediano 0.9%; 21 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 163.67; 34% do lucro antes de custos.
- Trades < 3 h: 10 (lucro -102.02); reentradas em < 24 h: 58 (lucro 87.96).
- Maior trade = 26% do lucro; top 5 = 77%; top 10 = 114%; lucro sem o melhor = 235.07.
- Lucro por ano de fechamento: 2018: 86.6, 2019: 105.8, 2020: -3.7, 2021: 144.1, 2022: -11.5, 2023: -29.6, 2024: 26.2.

## XRP/USDT

Trades: 196; lucro líquido: 76.41.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 154 | 436.64 | 571% | 1.77% | 54% | 13.0 h |
| stop_loss | 40 | -348.18 | -456% | -5.28% | 0% | 4.8 h |
| below_open_minus_half_range | 2 | -12.05 | -16% | -3.72% | 0% | 13.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 15 | -131.04 | -5.28% | 0% |
| 3 h a 1 dia | 181 | 207.45 | 0.74% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (83): MFE mediano 4.9%, MAE mediano -1.3%, devolução média do melhor ponto 3.4%, captura mediana 0.46.
- Perdedores (113): MAE mediano -4.2%, MFE mediano 0.9%; 32 (28%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 95.39; 56% do lucro antes de custos.
- Trades < 3 h: 15 (lucro -131.04); reentradas em < 24 h: 28 (lucro -17.33).
- Maior trade = 67% do lucro; top 5 = 273%; top 10 = 429%; lucro sem o melhor = 25.18.
- Lucro por ano de fechamento: 2018: 18.1, 2019: 12.0, 2020: 81.7, 2021: 29.9, 2022: -24.8, 2023: -53.2, 2024: 12.8.

## ADA/USDT

Trades: 217; lucro líquido: 89.07.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 178 | 433.16 | 486% | 1.47% | 54% | 13.3 h |
| stop_loss | 36 | -325.37 | -365% | -5.28% | 0% | 7.8 h |
| below_open_minus_half_range | 3 | -18.72 | -21% | -3.61% | 0% | 6.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 7 | -65.91 | -5.28% | 0% |
| 3 h a 1 dia | 210 | 154.98 | 0.46% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (96): MFE mediano 5.3%, MAE mediano -1.2%, devolução média do melhor ponto 2.9%, captura mediana 0.49.
- Perdedores (121): MAE mediano -3.5%, MFE mediano 1.1%; 36 (30%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 109.36; 55% do lucro antes de custos.
- Trades < 3 h: 7 (lucro -65.91); reentradas em < 24 h: 45 (lucro -21.33).
- Maior trade = 49% do lucro; top 5 = 152%; top 10 = 265%; lucro sem o melhor = 45.56.
- Lucro por ano de fechamento: 2018: -16.2, 2019: 27.9, 2020: 122.5, 2021: 103.2, 2022: -48.9, 2023: -59.8, 2024: -39.6.

## LTC/USDT

Trades: 247; lucro líquido: -47.56.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 193 | 401.55 | – | 1.32% | 54% | 13.7 h |
| stop_loss | 52 | -436.64 | – | -5.28% | 0% | 7.0 h |
| below_open_minus_half_range | 2 | -12.47 | – | -4.14% | 0% | 4.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 8 | -67.58 | -5.28% | 0% |
| 3 h a 1 dia | 239 | 20.03 | 0.06% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (105): MFE mediano 4.6%, MAE mediano -1.2%, devolução média do melhor ponto 2.5%, captura mediana 0.56.
- Perdedores (142): MAE mediano -3.9%, MFE mediano 0.9%; 32 (23%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 115.69; 170% do lucro antes de custos.
- Trades < 3 h: 8 (lucro -67.58); reentradas em < 24 h: 35 (lucro -63.28).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -86.94.
- Lucro por ano de fechamento: 2018: -12.6, 2019: 57.7, 2020: 62.2, 2021: -32.0, 2022: -71.0, 2023: -42.3, 2024: -9.5.

## LINK/USDT

Trades: 257; lucro líquido: -0.05.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 202 | 452.84 | – | 1.43% | 54% | 12.6 h |
| stop_loss | 51 | -428.55 | – | -5.28% | 0% | 5.9 h |
| below_open_minus_half_range | 4 | -24.34 | – | -3.95% | 0% | 8.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 16 | -133.77 | -5.17% | 0% |
| 3 h a 1 dia | 241 | 133.72 | 0.36% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (110): MFE mediano 5.1%, MAE mediano -1.3%, devolução média do melhor ponto 3.0%, captura mediana 0.51.
- Perdedores (147): MAE mediano -4.2%, MFE mediano 1.4%; 53 (36%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 121.73; 100% do lucro antes de custos.
- Trades < 3 h: 16 (lucro -133.77); reentradas em < 24 h: 39 (lucro -54.15).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -30.91.
- Lucro por ano de fechamento: 2019: 36.6, 2020: 96.4, 2021: -85.7, 2022: -43.1, 2023: 32.8, 2024: -37.1.

## DOGE/USDT

Trades: 176; lucro líquido: 102.97.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 121 | 608.67 | 591% | 3.01% | 56% | 14.1 h |
| stop_loss | 54 | -497.25 | -483% | -5.28% | 0% | 4.6 h |
| below_open_minus_half_range | 1 | -8.44 | -8% | -4.47% | 0% | 13.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 20 | -179.99 | -5.28% | 0% |
| 3 h a 1 dia | 156 | 282.97 | 1.15% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (68): MFE mediano 5.5%, MAE mediano -1.2%, devolução média do melhor ponto 5.8%, captura mediana 0.51.
- Perdedores (108): MAE mediano -4.9%, MFE mediano 1.3%; 39 (36%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 90.03; 47% do lucro antes de custos.
- Trades < 3 h: 20 (lucro -179.99); reentradas em < 24 h: 34 (lucro 84.82).
- Maior trade = 93% do lucro; top 5 = 301%; top 10 = 410%; lucro sem o melhor = 7.34.
- Lucro por ano de fechamento: 2019: 5.3, 2020: 33.4, 2021: 233.3, 2022: -46.4, 2023: -86.9, 2024: -35.7.

## SOL/USDT

Trades: 194; lucro líquido: -89.54.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 137 | 332.61 | – | 1.76% | 59% | 12.4 h |
| stop_loss | 56 | -416.09 | – | -5.28% | 0% | 5.7 h |
| below_open_minus_half_range | 1 | -6.06 | – | -4.44% | 0% | 9.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 15 | -113.07 | -5.28% | 0% |
| 3 h a 1 dia | 179 | 23.53 | 0.11% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (81): MFE mediano 5.8%, MAE mediano -1.3%, devolução média do melhor ponto 3.5%, captura mediana 0.54.
- Perdedores (113): MAE mediano -5.2%, MFE mediano 1.3%; 39 (35%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 80.88; – do lucro antes de custos.
- Trades < 3 h: 15 (lucro -113.07); reentradas em < 24 h: 46 (lucro -40.94).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -114.23.
- Lucro por ano de fechamento: 2020: -12.6, 2021: -65.2, 2022: -50.5, 2023: 69.6, 2024: -30.8.
