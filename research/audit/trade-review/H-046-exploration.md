# Revisão de trades: H-046 (exploração)

Fonte dos trades: `research/experiments/20261106T161729Z-h-046-exploration-btc-usdt/raw/backtest-result-2026-11-06_16-20-29.zip`; `research/experiments/20261106T161729Z-h-046-exploration-eth-usdt/raw/backtest-result-2026-11-06_16-24-11.zip`; `research/experiments/20261106T161729Z-h-046-exploration-bnb-usdt/raw/backtest-result-2026-11-06_16-28-06.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 130; lucro líquido: 44.78.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trail_48_low | 61 | 84.18 | 188% | 5.90% | 54% | 163.6 h |
| fail_fast_pivot | 46 | -15.79 | -35% | -1.44% | 0% | 2.8 h |
| stop_loss | 23 | -23.61 | -53% | -4.34% | 0% | 31.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 30 | -13.57 | -1.92% | 0% |
| 3 h a 1 dia | 23 | -8.96 | -1.68% | 0% |
| 1 a 7 dias | 57 | -8.74 | -0.62% | 26% |
| 7 a 30 dias | 20 | 76.05 | 16.28% | 90% |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (33): MFE mediano 19.7%, MAE mediano -0.4%, devolução média do melhor ponto 9.8%, captura mediana 0.54.
- Perdedores (97): MAE mediano -2.6%, MFE mediano 0.9%; 35 (36%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 10.98; 20% do lucro antes de custos.
- Trades < 3 h: 30 (lucro -13.57); reentradas em < 24 h: 8 (lucro -0.67).
- Maior trade = 19% do lucro; top 5 = 78%; top 10 = 127%; lucro sem o melhor = 36.40.
- Lucro por ano de fechamento: 2017: -0.3, 2018: -1.1, 2019: 13.2, 2020: 3.9, 2021: 14.0, 2022: -0.6, 2023: 15.1, 2024: 0.5.

## ETH/USDT

Trades: 139; lucro líquido: 45.04.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| trail_48_low | 57 | 101.98 | 226% | 7.16% | 65% | 153.9 h |
| fail_fast_pivot | 51 | -21.20 | -47% | -1.52% | 0% | 2.3 h |
| stop_loss | 31 | -35.75 | -79% | -4.33% | 0% | 32.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 39 | -18.46 | -1.78% | 0% |
| 3 h a 1 dia | 26 | -18.17 | -2.65% | 0% |
| 1 a 7 dias | 52 | -15.02 | -0.98% | 29% |
| 7 a 30 dias | 22 | 96.69 | 17.53% | 100% |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (37): MFE mediano 17.0%, MAE mediano -1.1%, devolução média do melhor ponto 13.6%, captura mediana 0.43.
- Perdedores (102): MAE mediano -2.8%, MFE mediano 1.3%; 38 (37%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 13.12; 23% do lucro antes de custos.
- Trades < 3 h: 39 (lucro -18.46); reentradas em < 24 h: 8 (lucro 4.36).
- Maior trade = 27% do lucro; top 5 = 91%; top 10 = 152%; lucro sem o melhor = 32.96.
- Lucro por ano de fechamento: 2017: 9.1, 2018: 6.5, 2019: 14.9, 2020: 4.8, 2021: 5.2, 2022: -2.1, 2023: 2.1, 2024: 4.5.

## BNB/USDT

Trades: 136; lucro líquido: 63.96.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| fail_fast_pivot | 54 | -21.91 | -34% | -1.70% | 0% | 2.8 h |
| trail_48_low | 45 | 122.19 | 191% | 12.83% | 62% | 166.1 h |
| stop_loss | 37 | -36.32 | -57% | -4.33% | 0% | 26.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 45 | -23.31 | -2.35% | 0% |
| 3 h a 1 dia | 29 | -16.83 | -2.52% | 0% |
| 1 a 7 dias | 43 | -10.77 | -0.96% | 26% |
| 7 a 30 dias | 19 | 114.87 | 28.70% | 89% |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (28): MFE mediano 20.1%, MAE mediano -1.1%, devolução média do melhor ponto 24.1%, captura mediana 0.43.
- Perdedores (108): MAE mediano -3.8%, MFE mediano 1.6%; 45 (42%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 11.59; 15% do lucro antes de custos.
- Trades < 3 h: 45 (lucro -23.31); reentradas em < 24 h: 11 (lucro -4.09).
- Maior trade = 86% do lucro; top 5 = 138%; top 10 = 173%; lucro sem o melhor = 9.02.
- Lucro por ano de fechamento: 2017: -0.3, 2018: -10.9, 2019: 0.9, 2020: -2.5, 2021: 75.9, 2022: -0.5, 2023: -1.7, 2024: 3.0.
