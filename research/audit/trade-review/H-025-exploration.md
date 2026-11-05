# Revisão de trades: H-025 (exploração)

Fonte dos trades: `research/experiments/20261105T195545Z-h-025-exploration-btc-usdt/raw/backtest-result-2026-11-05_19-57-37.zip`; `research/experiments/20261105T195545Z-h-025-exploration-eth-usdt/raw/backtest-result-2026-11-05_20-00-15.zip`; `research/experiments/20261105T195545Z-h-025-exploration-bnb-usdt/raw/backtest-result-2026-11-05_20-02-45.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 33; lucro líquido: 56.78.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| close_below_ema20 | 24 | 75.33 | 133% | 13.03% | 71% | 604.9 h |
| stop_loss | 9 | -18.55 | -33% | -8.32% | 0% | 92.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 0 | 0.00 | – | – |
| 3 h a 1 dia | 4 | -5.89 | -6.42% | 0% |
| 1 a 7 dias | 4 | -8.71 | -8.32% | 0% |
| 7 a 30 dias | 18 | 8.73 | 2.13% | 56% |
| > 30 dias | 7 | 62.65 | 36.93% | 100% |

### Excursões (antes de custos)

- Vencedores (17): MFE mediano 28.6%, MAE mediano -0.9%, devolução média do melhor ponto 17.8%, captura mediana 0.47.
- Perdedores (16): MAE mediano -8.6%, MFE mediano 2.1%; 9 (56%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 2.98; 5% do lucro antes de custos.
- Trades < 3 h: 0 (lucro 0.00); reentradas em < 24 h: 3 (lucro -0.48).
- Maior trade = 23% do lucro; top 5 = 97%; top 10 = 134%; lucro sem o melhor = 43.52.
- Lucro por ano de fechamento: 2018: -1.4, 2019: 12.8, 2020: 12.6, 2021: 11.7, 2022: -6.8, 2023: 19.6, 2024: 8.3.

## ETH/USDT

Trades: 33; lucro líquido: 55.71.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| close_below_ema20 | 22 | 78.52 | 141% | 14.80% | 68% | 554.2 h |
| stop_loss | 11 | -22.82 | -41% | -8.32% | 0% | 134.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 0 | 0.00 | – | – |
| 3 h a 1 dia | 2 | -3.64 | -8.32% | 0% |
| 1 a 7 dias | 7 | -13.87 | -7.94% | 0% |
| 7 a 30 dias | 16 | 20.64 | 5.73% | 44% |
| > 30 dias | 8 | 52.57 | 26.82% | 100% |

### Excursões (antes de custos)

- Vencedores (15): MFE mediano 39.4%, MAE mediano -2.6%, devolução média do melhor ponto 21.8%, captura mediana 0.51.
- Perdedores (18): MAE mediano -8.4%, MFE mediano 5.5%; 13 (72%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 3.02; 5% do lucro antes de custos.
- Trades < 3 h: 0 (lucro 0.00); reentradas em < 24 h: 1 (lucro -1.94).
- Maior trade = 26% do lucro; top 5 = 91%; top 10 = 134%; lucro sem o melhor = 41.43.
- Lucro por ano de fechamento: 2019: 2.4, 2020: 13.1, 2021: 28.7, 2022: -4.3, 2023: 9.1, 2024: 6.8.

## BNB/USDT

Trades: 41; lucro líquido: 138.51.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 21 | -52.86 | -38% | -8.32% | 0% | 81.4 h |
| close_below_ema20 | 20 | 191.37 | 138% | 36.75% | 65% | 601.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 0 | 0.00 | – | – |
| 3 h a 1 dia | 4 | -8.79 | -8.32% | 0% |
| 1 a 7 dias | 16 | -40.72 | -8.16% | 0% |
| 7 a 30 dias | 15 | 3.27 | 0.29% | 47% |
| > 30 dias | 6 | 184.75 | 119.97% | 100% |

### Excursões (antes de custos)

- Vencedores (13): MFE mediano 38.4%, MAE mediano -2.8%, devolução média do melhor ponto 35.9%, captura mediana 0.45.
- Perdedores (28): MAE mediano -8.7%, MFE mediano 4.4%; 21 (75%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 4.95; 3% do lucro antes de custos.
- Trades < 3 h: 0 (lucro 0.00); reentradas em < 24 h: 3 (lucro 35.97).
- Maior trade = 61% do lucro; top 5 = 129%; top 10 = 146%; lucro sem o melhor = 53.81.
- Lucro por ano de fechamento: 2018: -5.0, 2019: 14.6, 2020: 2.1, 2021: 121.5, 2022: -3.9, 2023: -9.8, 2024: 19.1.
