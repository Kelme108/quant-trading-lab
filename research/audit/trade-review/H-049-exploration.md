# Revisão de trades: H-049 (exploração)

Fonte dos trades: `research/experiments/20261106T180441Z-h-049-exploration-btc-usdt/raw/backtest-result-2026-11-06_18-07-24.zip`; `research/experiments/20261106T180441Z-h-049-exploration-eth-usdt/raw/backtest-result-2026-11-06_18-09-37.zip`; `research/experiments/20261106T180441Z-h-049-exploration-bnb-usdt/raw/backtest-result-2026-11-06_18-11-49.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 371; lucro líquido: 3.08.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| kama4h_close_below | 364 | 8.92 | 289% | 0.25% | 32% | 45.5 h |
| stop_loss | 7 | -5.84 | -189% | -8.32% | 0% | 21.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 0 | 0.00 | – | – |
| 3 h a 1 dia | 101 | -35.02 | -3.46% | 0% |
| 1 a 7 dias | 266 | 31.12 | 1.18% | 42% |
| 7 a 30 dias | 4 | 6.98 | 17.46% | 100% |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (117): MFE mediano 9.0%, MAE mediano -0.9%, devolução média do melhor ponto 5.3%, captura mediana 0.49.
- Perdedores (254): MAE mediano -2.9%, MFE mediano 1.4%; 94 (37%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 12.96; 81% do lucro antes de custos.
- Trades < 3 h: 0 (lucro 0.00); reentradas em < 24 h: 68 (lucro -0.01).
- Maior trade = 76% do lucro; top 5 = 328%; top 10 = 602%; lucro sem o melhor = 0.74.
- Lucro por ano de fechamento: 2018: -2.9, 2019: 1.7, 2020: 4.6, 2021: 0.0, 2022: -5.8, 2023: 3.5, 2024: 2.0.

## ETH/USDT

Trades: 437; lucro líquido: 8.45.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| kama4h_close_below | 425 | 19.46 | 230% | 0.44% | 35% | 44.1 h |
| stop_loss | 12 | -11.01 | -130% | -8.32% | 0% | 21.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 0 | 0.00 | – | – |
| 3 h a 1 dia | 131 | -52.58 | -3.71% | 1% |
| 1 a 7 dias | 299 | 45.55 | 1.43% | 47% |
| 7 a 30 dias | 7 | 15.49 | 20.68% | 100% |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (149): MFE mediano 9.3%, MAE mediano -1.1%, devolução média do melhor ponto 6.2%, captura mediana 0.42.
- Perdedores (288): MAE mediano -3.4%, MFE mediano 1.8%; 130 (45%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 16.42; 66% do lucro antes de custos.
- Trades < 3 h: 0 (lucro 0.00); reentradas em < 24 h: 108 (lucro -6.19).
- Maior trade = 70% do lucro; top 5 = 202%; top 10 = 315%; lucro sem o melhor = 2.51.
- Lucro por ano de fechamento: 2018: 0.1, 2019: 0.1, 2020: 14.1, 2021: 0.3, 2022: -6.1, 2023: 0.7, 2024: -0.7.

## BNB/USDT

Trades: 426; lucro líquido: 18.55.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| kama4h_close_below | 411 | 32.62 | 176% | 0.75% | 33% | 44.8 h |
| stop_loss | 15 | -14.08 | -76% | -8.31% | 0% | 23.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 1 | -0.97 | -8.31% | 0% |
| 3 h a 1 dia | 126 | -47.11 | -3.33% | 0% |
| 1 a 7 dias | 294 | 57.03 | 1.79% | 45% |
| 7 a 30 dias | 5 | 9.59 | 17.14% | 100% |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (137): MFE mediano 10.6%, MAE mediano -1.2%, devolução média do melhor ponto 7.3%, captura mediana 0.44.
- Perdedores (289): MAE mediano -3.2%, MFE mediano 1.7%; 131 (45%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 16.60; 47% do lucro antes de custos.
- Trades < 3 h: 1 (lucro -0.97); reentradas em < 24 h: 119 (lucro 18.28).
- Maior trade = 62% do lucro; top 5 = 171%; top 10 = 230%; lucro sem o melhor = 7.02.
- Lucro por ano de fechamento: 2018: -4.2, 2019: 4.5, 2020: 2.4, 2021: 22.4, 2022: -2.5, 2023: -4.3, 2024: 0.3.
