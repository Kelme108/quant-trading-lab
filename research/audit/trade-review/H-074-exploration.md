# Revisão de trades: H-074 (exploração)

Fonte dos trades: `research/experiments/20261107T203841Z-h-074-exploration-btc-usdt/raw/backtest-result-2026-11-07_20-44-32.zip`; `research/experiments/20261107T203841Z-h-074-exploration-eth-usdt/raw/backtest-result-2026-11-07_20-46-46.zip`; `research/experiments/20261107T203841Z-h-074-exploration-bnb-usdt/raw/backtest-result-2026-11-07_20-49-03.zip`; `research/experiments/20261107T203841Z-h-074-exploration-xrp-usdt/raw/backtest-result-2026-11-07_20-51-13.zip`; `research/experiments/20261107T203841Z-h-074-exploration-ada-usdt/raw/backtest-result-2026-11-07_20-53-18.zip`; `research/experiments/20261107T203841Z-h-074-exploration-ltc-usdt/raw/backtest-result-2026-11-07_20-55-30.zip`; `research/experiments/20261107T203841Z-h-074-exploration-link-usdt/raw/backtest-result-2026-11-07_20-57-39.zip`; `research/experiments/20261107T203841Z-h-074-exploration-doge-usdt/raw/backtest-result-2026-11-07_20-59-41.zip`; `research/experiments/20261107T203841Z-h-074-exploration-sol-usdt/raw/backtest-result-2026-11-07_21-01-38.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 383; lucro líquido: -3.84.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12_bars | 298 | 38.95 | – | 0.86% | 57% | 13.0 h |
| stop_loss | 85 | -42.78 | – | -3.29% | 0% | 4.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 33 | -16.69 | -3.29% | 0% |
| 3 h a 1 dia | 350 | 12.85 | 0.24% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (170): MFE mediano 2.9%, MAE mediano -0.6%, devolução média do melhor ponto 1.6%, captura mediana 0.52.
- Perdedores (213): MAE mediano -2.3%, MFE mediano 0.8%; 23 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 17.39; 128% do lucro antes de custos.
- Trades < 3 h: 33 (lucro -16.69); reentradas em < 24 h: 44 (lucro -1.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -5.28.
- Lucro por ano de fechamento: 2017: 2.5, 2018: 2.4, 2019: -1.9, 2020: 2.9, 2021: -5.8, 2022: -3.1, 2023: -0.8, 2024: 0.0.

## ETH/USDT

Trades: 401; lucro líquido: -8.22.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12_bars | 287 | 46.63 | – | 1.12% | 61% | 13.0 h |
| stop_loss | 114 | -54.85 | – | -3.29% | 0% | 4.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 43 | -20.72 | -3.29% | 0% |
| 3 h a 1 dia | 358 | 12.50 | 0.24% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (176): MFE mediano 3.4%, MAE mediano -0.7%, devolução média do melhor ponto 1.9%, captura mediana 0.49.
- Perdedores (225): MAE mediano -3.1%, MFE mediano 0.9%; 41 (18%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 17.26; 191% do lucro antes de custos.
- Trades < 3 h: 43 (lucro -20.72); reentradas em < 24 h: 55 (lucro -5.81).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -10.42.
- Lucro por ano de fechamento: 2017: -0.9, 2018: -1.8, 2019: -1.1, 2020: 2.7, 2021: -0.8, 2022: -6.7, 2023: -0.9, 2024: 1.3.

## BNB/USDT

Trades: 374; lucro líquido: 7.69.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12_bars | 266 | 65.09 | 846% | 1.53% | 70% | 13.0 h |
| stop_loss | 108 | -57.40 | -746% | -3.29% | 0% | 4.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 42 | -22.47 | -3.29% | 0% |
| 3 h a 1 dia | 332 | 30.16 | 0.57% | 56% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (186): MFE mediano 3.1%, MAE mediano -1.0%, devolução média do melhor ponto 2.0%, captura mediana 0.50.
- Perdedores (188): MAE mediano -3.1%, MFE mediano 0.9%; 30 (16%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 18.06; 70% do lucro antes de custos.
- Trades < 3 h: 42 (lucro -22.47); reentradas em < 24 h: 48 (lucro 0.45).
- Maior trade = 72% do lucro; top 5 = 215%; top 10 = 308%; lucro sem o melhor = 2.13.
- Lucro por ano de fechamento: 2017: 3.0, 2018: 4.0, 2019: 0.5, 2020: 3.0, 2021: -5.4, 2022: 0.2, 2023: 0.1, 2024: 2.2.

## XRP/USDT

Trades: 285; lucro líquido: -17.11.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12_bars | 197 | 22.21 | – | 0.84% | 56% | 13.0 h |
| stop_loss | 88 | -39.32 | – | -3.29% | 0% | 4.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 41 | -18.31 | -3.29% | 0% |
| 3 h a 1 dia | 244 | 1.20 | 0.05% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (111): MFE mediano 3.7%, MAE mediano -0.6%, devolução média do melhor ponto 2.2%, captura mediana 0.44.
- Perdedores (174): MAE mediano -3.0%, MFE mediano 1.1%; 42 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 11.48; – do lucro antes de custos.
- Trades < 3 h: 41 (lucro -18.31); reentradas em < 24 h: 28 (lucro -0.58).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -19.15.
- Lucro por ano de fechamento: 2018: -3.5, 2019: -4.5, 2020: -2.1, 2021: -1.6, 2022: -3.0, 2023: -0.4, 2024: -2.0.

## ADA/USDT

Trades: 320; lucro líquido: -15.36.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12_bars | 198 | 41.06 | – | 1.47% | 62% | 13.0 h |
| stop_loss | 122 | -56.42 | – | -3.28% | 0% | 4.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 48 | -22.39 | -3.28% | 0% |
| 3 h a 1 dia | 272 | 7.03 | 0.18% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (122): MFE mediano 4.0%, MAE mediano -1.0%, devolução média do melhor ponto 2.3%, captura mediana 0.55.
- Perdedores (198): MAE mediano -3.2%, MFE mediano 1.0%; 54 (27%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 13.41; – do lucro antes de custos.
- Trades < 3 h: 48 (lucro -22.39); reentradas em < 24 h: 32 (lucro -2.72).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -17.40.
- Lucro por ano de fechamento: 2018: -5.5, 2019: -3.7, 2020: 9.1, 2021: -6.2, 2022: -3.1, 2023: -5.4, 2024: -0.7.

## LTC/USDT

Trades: 368; lucro líquido: -1.43.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12_bars | 258 | 53.63 | – | 1.38% | 58% | 13.0 h |
| stop_loss | 110 | -55.05 | – | -3.28% | 0% | 4.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 46 | -23.11 | -3.28% | 0% |
| 3 h a 1 dia | 322 | 21.68 | 0.45% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (150): MFE mediano 3.6%, MAE mediano -0.9%, devolução média do melhor ponto 2.2%, captura mediana 0.54.
- Perdedores (218): MAE mediano -3.0%, MFE mediano 1.0%; 40 (18%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 16.77; 109% do lucro antes de custos.
- Trades < 3 h: 46 (lucro -23.11); reentradas em < 24 h: 40 (lucro -4.69).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -4.74.
- Lucro por ano de fechamento: 2018: -3.0, 2019: 0.1, 2020: 4.8, 2021: 1.2, 2022: 1.2, 2023: -2.1, 2024: -3.6.

## LINK/USDT

Trades: 295; lucro líquido: 1.42.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12_bars | 196 | 50.73 | 3582% | 1.72% | 68% | 13.0 h |
| stop_loss | 99 | -49.32 | -3482% | -3.28% | 0% | 4.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 38 | -18.89 | -3.28% | 0% |
| 3 h a 1 dia | 257 | 20.31 | 0.53% | 52% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (134): MFE mediano 4.3%, MAE mediano -1.0%, devolução média do melhor ponto 2.2%, captura mediana 0.50.
- Perdedores (161): MAE mediano -3.2%, MFE mediano 1.2%; 43 (27%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 13.34; 90% do lucro antes de custos.
- Trades < 3 h: 38 (lucro -18.89); reentradas em < 24 h: 39 (lucro -3.10).
- Maior trade = 215% do lucro; top 5 = 732%; top 10 = 1268%; lucro sem o melhor = -1.63.
- Lucro por ano de fechamento: 2019: 0.4, 2020: 2.9, 2021: -1.4, 2022: -5.2, 2023: 3.7, 2024: 1.0.

## DOGE/USDT

Trades: 216; lucro líquido: 3.13.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12_bars | 150 | 36.89 | 1177% | 1.60% | 57% | 13.0 h |
| stop_loss | 66 | -33.76 | -1077% | -3.28% | 0% | 3.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 33 | -16.90 | -3.28% | 0% |
| 3 h a 1 dia | 183 | 20.03 | 0.72% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (85): MFE mediano 4.4%, MAE mediano -0.9%, devolução média do melhor ponto 2.7%, captura mediana 0.52.
- Perdedores (131): MAE mediano -3.0%, MFE mediano 1.1%; 32 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 10.08; 76% do lucro antes de custos.
- Trades < 3 h: 33 (lucro -16.90); reentradas em < 24 h: 22 (lucro -4.64).
- Maior trade = 112% do lucro; top 5 = 351%; top 10 = 555%; lucro sem o melhor = -0.39.
- Lucro por ano de fechamento: 2019: 0.4, 2020: 3.7, 2021: 0.4, 2022: 0.2, 2023: 4.3, 2024: -5.8.

## SOL/USDT

Trades: 211; lucro líquido: -10.31.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_12_bars | 116 | 33.59 | – | 2.08% | 67% | 13.0 h |
| stop_loss | 95 | -43.90 | – | -3.28% | 0% | 4.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 29 | -13.40 | -3.28% | 0% |
| 3 h a 1 dia | 182 | 3.09 | 0.14% | 43% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (78): MFE mediano 5.1%, MAE mediano -0.7%, devolução média do melhor ponto 3.0%, captura mediana 0.48.
- Perdedores (133): MAE mediano -3.3%, MFE mediano 1.4%; 48 (36%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 8.82; – do lucro antes de custos.
- Trades < 3 h: 29 (lucro -13.40); reentradas em < 24 h: 34 (lucro -5.30).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -12.73.
- Lucro por ano de fechamento: 2020: -5.0, 2021: 2.5, 2022: -7.7, 2023: 1.0, 2024: -1.1.
