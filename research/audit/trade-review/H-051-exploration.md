# Revisão de trades: H-051 (exploração)

Fonte dos trades: `research/experiments/20261106T193126Z-h-051-exploration-btc-usdt/raw/backtest-result-2026-11-06_19-33-17.zip`; `research/experiments/20261106T193126Z-h-051-exploration-eth-usdt/raw/backtest-result-2026-11-06_19-35-31.zip`; `research/experiments/20261106T193126Z-h-051-exploration-bnb-usdt/raw/backtest-result-2026-11-06_19-37-38.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 68; lucro líquido: -3.16.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_23utc | 40 | 21.68 | – | 1.11% | 68% | 7.0 h |
| stop_loss | 28 | -24.84 | – | -1.80% | 0% | 1.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 23 | -20.42 | -1.80% | 0% |
| 3 h a 1 dia | 45 | 17.26 | 0.79% | 60% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (27): MFE mediano 3.1%, MAE mediano -0.5%, devolução média do melhor ponto 1.7%, captura mediana 0.45.
- Perdedores (41): MAE mediano -1.8%, MFE mediano 0.6%; 5 (12%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 10.01; 146% do lucro antes de custos.
- Trades < 3 h: 23 (lucro -20.42); reentradas em < 24 h: 7 (lucro -3.03).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -5.63.
- Lucro por ano de fechamento: 2017: -1.1, 2018: -1.6, 2019: 2.8, 2020: -1.7, 2021: -1.5, 2022: 0.5, 2023: -2.6, 2024: 2.1.

## ETH/USDT

Trades: 72; lucro líquido: -5.78.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_23utc | 38 | 23.98 | – | 1.31% | 82% | 7.0 h |
| stop_loss | 34 | -29.77 | – | -1.79% | 0% | 1.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 27 | -23.69 | -1.79% | 0% |
| 3 h a 1 dia | 45 | 17.91 | 0.82% | 69% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (31): MFE mediano 2.8%, MAE mediano -0.3%, devolução média do melhor ponto 1.9%, captura mediana 0.44.
- Perdedores (41): MAE mediano -1.9%, MFE mediano 0.9%; 9 (22%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 10.45; 224% do lucro antes de custos.
- Trades < 3 h: 27 (lucro -23.69); reentradas em < 24 h: 7 (lucro -1.62).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -7.97.
- Lucro por ano de fechamento: 2017: -1.7, 2018: -0.8, 2019: 2.9, 2020: -2.5, 2021: -3.3, 2022: 1.2, 2023: -1.1, 2024: -0.4.

## BNB/USDT

Trades: 61; lucro líquido: -10.69.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 32 | -27.20 | – | -1.79% | 0% | 1.7 h |
| time_exit_23utc | 29 | 16.51 | – | 1.23% | 66% | 7.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 24 | -20.38 | -1.79% | 0% |
| 3 h a 1 dia | 37 | 9.70 | 0.57% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (19): MFE mediano 2.3%, MAE mediano -0.4%, devolução média do melhor ponto 1.6%, captura mediana 0.50.
- Perdedores (42): MAE mediano -2.0%, MFE mediano 0.9%; 9 (21%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 8.60; – do lucro antes de custos.
- Trades < 3 h: 24 (lucro -20.38); reentradas em < 24 h: 4 (lucro -3.36).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -16.60.
- Lucro por ano de fechamento: 2017: 0.1, 2018: -4.4, 2019: -0.7, 2020: -5.3, 2021: 3.5, 2022: -1.1, 2023: -2.8, 2024: -0.0.
