# Revisão de trades: H-040 (exploração)

Fonte dos trades: `research/experiments/20261106T125054Z-h-040-exploration-btc-usdt/raw/backtest-result-2026-11-06_12-52-52.zip`; `research/experiments/20261106T125054Z-h-040-exploration-eth-usdt/raw/backtest-result-2026-11-06_12-55-08.zip`; `research/experiments/20261106T125054Z-h-040-exploration-bnb-usdt/raw/backtest-result-2026-11-06_12-57-17.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 95; lucro líquido: 58.05.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_48 | 49 | 128.72 | 222% | 5.59% | 84% | 49.8 h |
| stop_loss | 31 | -53.60 | -92% | -3.34% | 0% | 24.0 h |
| close_below_nr7_low | 15 | -17.06 | -29% | -2.11% | 0% | 20.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 2 | -3.33 | -2.96% | 0% |
| 3 h a 1 dia | 25 | -37.44 | -2.95% | 0% |
| 1 a 7 dias | 68 | 98.83 | 3.21% | 60% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (41): MFE mediano 7.3%, MAE mediano -0.6%, devolução média do melhor ponto 2.7%, captura mediana 0.65.
- Perdedores (54): MAE mediano -3.1%, MFE mediano 0.8%; 11 (20%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 17.27; 23% do lucro antes de custos.
- Trades < 3 h: 2 (lucro -3.33); reentradas em < 24 h: 2 (lucro 10.36).
- Maior trade = 29% do lucro; top 5 = 80%; top 10 = 127%; lucro sem o melhor = 41.19.
- Lucro por ano de fechamento: 2017: 29.3, 2018: 3.2, 2019: 11.8, 2020: 10.2, 2021: 4.7, 2022: 1.7, 2023: -3.7, 2024: 1.0.

## ETH/USDT

Trades: 80; lucro líquido: 37.70.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_48 | 43 | 89.42 | 237% | 5.05% | 84% | 48.0 h |
| stop_loss | 34 | -48.24 | -128% | -3.34% | 0% | 17.1 h |
| close_below_nr7_low | 3 | -3.48 | -9% | -2.62% | 0% | 45.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 1 | -1.21 | -3.34% | 0% |
| 3 h a 1 dia | 23 | -32.38 | -3.32% | 0% |
| 1 a 7 dias | 56 | 71.29 | 3.14% | 64% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (36): MFE mediano 8.4%, MAE mediano -0.7%, devolução média do melhor ponto 3.5%, captura mediana 0.56.
- Perdedores (44): MAE mediano -3.5%, MFE mediano 1.4%; 16 (36%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 11.90; 24% do lucro antes de custos.
- Trades < 3 h: 1 (lucro -1.21); reentradas em < 24 h: 5 (lucro 5.03).
- Maior trade = 22% do lucro; top 5 = 83%; top 10 = 139%; lucro sem o melhor = 29.57.
- Lucro por ano de fechamento: 2017: 0.1, 2018: 0.6, 2019: 8.1, 2020: 18.5, 2021: 3.8, 2022: 7.8, 2023: -1.2, 2024: 0.1.

## BNB/USDT

Trades: 87; lucro líquido: 39.38.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 43 | -64.92 | -165% | -3.33% | 0% | 19.9 h |
| time_exit_48 | 37 | 112.07 | 285% | 7.36% | 76% | 58.7 h |
| close_below_nr7_low | 7 | -7.77 | -20% | -2.31% | 0% | 32.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 2 | -3.23 | -3.33% | 0% |
| 3 h a 1 dia | 29 | -42.32 | -3.29% | 0% |
| 1 a 7 dias | 55 | 70.29 | 3.18% | 49% |
| 7 a 30 dias | 1 | 14.64 | 39.74% | 100% |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (28): MFE mediano 7.9%, MAE mediano -0.8%, devolução média do melhor ponto 3.3%, captura mediana 0.69.
- Perdedores (59): MAE mediano -3.3%, MFE mediano 1.4%; 25 (42%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 13.84; 26% do lucro antes de custos.
- Trades < 3 h: 2 (lucro -3.23); reentradas em < 24 h: 5 (lucro -3.51).
- Maior trade = 93% do lucro; top 5 = 176%; top 10 = 225%; lucro sem o melhor = 2.58.
- Lucro por ano de fechamento: 2018: -6.2, 2019: 29.8, 2020: -5.5, 2021: 33.7, 2022: -1.1, 2023: -9.6, 2024: -1.7.
