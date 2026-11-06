# Revisão de trades: H-039 (exploração)

Fonte dos trades: `research/experiments/20261106T122555Z-h-039-exploration-btc-usdt/raw/backtest-result-2026-11-06_12-28-57.zip`; `research/experiments/20261106T122555Z-h-039-exploration-eth-usdt/raw/backtest-result-2026-11-06_12-31-04.zip`; `research/experiments/20261106T122555Z-h-039-exploration-bnb-usdt/raw/backtest-result-2026-11-06_12-33-05.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 365; lucro líquido: -9.96.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| session_end | 330 | 7.38 | – | 0.14% | 40% | 8.0 h |
| stop_loss | 35 | -17.34 | – | -3.34% | 0% | 3.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 16 | -8.02 | -3.34% | 0% |
| 3 h a 1 dia | 349 | -1.94 | -0.05% | 38% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (133): MFE mediano 2.0%, MAE mediano -0.3%, devolução média do melhor ponto 1.3%, captura mediana 0.41.
- Perdedores (232): MAE mediano -1.1%, MFE mediano 0.5%; 9 (4%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 18.36; 219% do lucro antes de custos.
- Trades < 3 h: 16 (lucro -8.02); reentradas em < 24 h: 176 (lucro -4.20).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -11.51.
- Lucro por ano de fechamento: 2017: 3.1, 2018: -1.3, 2019: -2.1, 2020: -0.7, 2021: -4.0, 2022: -0.5, 2023: -2.7, 2024: -1.6.

## ETH/USDT

Trades: 367; lucro líquido: -4.05.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| session_end | 321 | 19.30 | – | 0.40% | 47% | 8.0 h |
| stop_loss | 46 | -23.35 | – | -3.34% | 0% | 3.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 20 | -10.17 | -3.34% | 0% |
| 3 h a 1 dia | 347 | 6.12 | 0.12% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (152): MFE mediano 2.7%, MAE mediano -0.5%, devolução média do melhor ponto 1.5%, captura mediana 0.46.
- Perdedores (215): MAE mediano -1.7%, MFE mediano 0.6%; 14 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 19.21; 127% do lucro antes de custos.
- Trades < 3 h: 20 (lucro -10.17); reentradas em < 24 h: 176 (lucro -0.48).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -6.11.
- Lucro por ano de fechamento: 2017: -0.5, 2018: 2.3, 2019: -1.3, 2020: 1.6, 2021: 0.9, 2022: -2.0, 2023: -4.3, 2024: -0.8.

## BNB/USDT

Trades: 368; lucro líquido: -13.33.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| session_end | 312 | 13.70 | – | 0.30% | 45% | 8.0 h |
| stop_loss | 56 | -27.03 | – | -3.34% | 0% | 2.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 32 | -15.70 | -3.34% | 0% |
| 3 h a 1 dia | 336 | 2.37 | 0.04% | 41% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (139): MFE mediano 2.3%, MAE mediano -0.5%, devolução média do melhor ponto 1.5%, captura mediana 0.44.
- Perdedores (229): MAE mediano -1.7%, MFE mediano 0.5%; 14 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 18.03; 384% do lucro antes de custos.
- Trades < 3 h: 32 (lucro -15.70); reentradas em < 24 h: 172 (lucro -10.16).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -18.50.
- Lucro por ano de fechamento: 2017: -1.0, 2018: 0.9, 2019: -3.4, 2020: -0.9, 2021: -3.2, 2022: -2.2, 2023: -2.0, 2024: -1.6.
