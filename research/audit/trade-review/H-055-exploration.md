# Revisão de trades: H-055 (exploração)

Fonte dos trades: `research/experiments/20261106T214758Z-h-055-exploration-btc-usdt/raw/backtest-result-2026-11-06_21-51-35.zip`; `research/experiments/20261106T214758Z-h-055-exploration-eth-usdt/raw/backtest-result-2026-11-06_21-55-20.zip`; `research/experiments/20261106T214758Z-h-055-exploration-bnb-usdt/raw/backtest-result-2026-11-06_21-59-14.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 183; lucro líquido: -11.47.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| roi | 89 | 22.51 | – | 0.90% | 100% | 3.2 h |
| sweep_low_exit | 45 | -17.38 | – | -1.38% | 0% | 4.5 h |
| time_exit_48_bars | 25 | -0.84 | – | -0.12% | 56% | 12.0 h |
| stop_loss | 24 | -15.76 | – | -2.29% | 0% | 2.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 82 | -0.91 | -0.04% | 65% |
| 3 h a 1 dia | 101 | -10.57 | -0.37% | 50% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (103): MFE mediano 1.3%, MAE mediano -0.4%, devolução média do melhor ponto 0.6%, captura mediana 0.65.
- Perdedores (80): MAE mediano -1.7%, MFE mediano 0.4%; 0 (0%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 15.38; 394% do lucro antes de custos.
- Trades < 3 h: 82 (lucro -0.91); reentradas em < 24 h: 15 (lucro -0.20).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -11.74.
- Lucro por ano de fechamento: 2017: -0.9, 2018: -4.6, 2019: 1.1, 2020: -0.9, 2021: -2.8, 2022: -2.2, 2023: -0.3, 2024: -0.8.

## ETH/USDT

Trades: 177; lucro líquido: -12.44.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| roi | 91 | 22.18 | – | 0.90% | 100% | 3.1 h |
| sweep_low_exit | 38 | -14.63 | – | -1.40% | 0% | 3.3 h |
| stop_loss | 29 | -18.42 | – | -2.29% | 0% | 2.5 h |
| time_exit_48_bars | 19 | -1.58 | – | -0.30% | 16% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 94 | -8.22 | -0.31% | 55% |
| 3 h a 1 dia | 83 | -4.22 | -0.18% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (94): MFE mediano 1.4%, MAE mediano -0.5%, devolução média do melhor ponto 0.6%, captura mediana 0.64.
- Perdedores (83): MAE mediano -1.7%, MFE mediano 0.4%; 0 (0%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 14.46; 716% do lucro antes de custos.
- Trades < 3 h: 94 (lucro -8.22); reentradas em < 24 h: 19 (lucro -0.45).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -12.71.
- Lucro por ano de fechamento: 2017: -0.1, 2018: -3.4, 2019: -5.7, 2020: -1.7, 2021: -0.7, 2022: -2.7, 2023: 2.5, 2024: -0.7.

## BNB/USDT

Trades: 193; lucro líquido: -14.40.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| roi | 97 | 23.50 | – | 0.90% | 100% | 2.9 h |
| sweep_low_exit | 46 | -18.47 | – | -1.51% | 0% | 3.6 h |
| stop_loss | 30 | -19.28 | – | -2.29% | 0% | 1.8 h |
| time_exit_48_bars | 20 | -0.15 | – | -0.02% | 55% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 110 | -9.77 | -0.31% | 57% |
| 3 h a 1 dia | 83 | -4.63 | -0.20% | 54% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (108): MFE mediano 1.3%, MAE mediano -0.5%, devolução média do melhor ponto 0.6%, captura mediana 0.65.
- Perdedores (85): MAE mediano -1.9%, MFE mediano 0.3%; 0 (0%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 15.58; 1320% do lucro antes de custos.
- Trades < 3 h: 110 (lucro -9.77); reentradas em < 24 h: 21 (lucro 0.45).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -14.67.
- Lucro por ano de fechamento: 2017: -0.5, 2018: -2.8, 2019: -6.5, 2020: -3.1, 2021: 0.5, 2022: -1.0, 2023: -0.7, 2024: -0.4.
