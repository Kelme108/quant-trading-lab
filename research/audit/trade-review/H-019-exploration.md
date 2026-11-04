# Revisão de trades: H-019 (exploração)

Fonte dos trades: `research/experiments/20261104T220739Z-h-019-exploration-btc-usdt/raw/backtest-result-2026-11-04_22-10-24.zip`; `research/experiments/20261104T220739Z-h-019-exploration-eth-usdt/raw/backtest-result-2026-11-04_22-14-30.zip`; `research/experiments/20261104T220739Z-h-019-exploration-bnb-usdt/raw/backtest-result-2026-11-04_22-19-18.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 53; lucro líquido: 4.68.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| above_sma5_or_below_sma200 | 53 | 4.68 | 100% | 0.47% | 72% | 85.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 0 | 0.00 | – | – |
| 3 h a 1 dia | 0 | 0.00 | – | – |
| 1 a 7 dias | 47 | 12.51 | 1.34% | 79% |
| 7 a 30 dias | 6 | -7.83 | -6.39% | 17% |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (38): MFE mediano 4.6%, MAE mediano -1.7%, devolução média do melhor ponto 1.9%, captura mediana 0.64.
- Perdedores (15): MAE mediano -10.5%, MFE mediano 1.9%; 7 (47%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 3.69; 44% do lucro antes de custos.
- Trades < 3 h: 0 (lucro 0.00); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = 41% do lucro; top 5 = 173%; top 10 = 275%; lucro sem o melhor = 2.74.
- Lucro por ano de fechamento: 2018: -2.4, 2019: -2.2, 2020: 3.9, 2021: -1.8, 2023: 4.0, 2024: 3.1.

## ETH/USDT

Trades: 54; lucro líquido: -0.15.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| above_sma5_or_below_sma200 | 54 | -0.15 | – | 0.02% | 65% | 82.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 0 | 0.00 | – | – |
| 3 h a 1 dia | 0 | 0.00 | – | – |
| 1 a 7 dias | 50 | 11.94 | 1.18% | 70% |
| 7 a 30 dias | 4 | -12.09 | -14.51% | 0% |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (35): MFE mediano 4.9%, MAE mediano -3.4%, devolução média do melhor ponto 1.8%, captura mediana 0.67.
- Perdedores (19): MAE mediano -13.3%, MFE mediano 2.0%; 9 (47%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 3.82; 104% do lucro antes de custos.
- Trades < 3 h: 0 (lucro 0.00); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -3.68.
- Lucro por ano de fechamento: 2018: -4.3, 2019: 0.8, 2020: 8.1, 2021: -1.9, 2022: -2.2, 2023: 2.5, 2024: -3.1.

## BNB/USDT

Trades: 57; lucro líquido: 12.72.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| above_sma5_or_below_sma200 | 57 | 12.72 | 100% | 1.10% | 67% | 71.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 0 | 0.00 | – | – |
| 3 h a 1 dia | 0 | 0.00 | – | – |
| 1 a 7 dias | 56 | 20.11 | 1.70% | 68% |
| 7 a 30 dias | 1 | -7.39 | -32.74% | 0% |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (38): MFE mediano 5.8%, MAE mediano -3.0%, devolução média do melhor ponto 2.1%, captura mediana 0.69.
- Perdedores (19): MAE mediano -9.1%, MFE mediano 1.6%; 9 (47%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 4.29; 25% do lucro antes de custos.
- Trades < 3 h: 0 (lucro 0.00); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = 25% do lucro; top 5 = 94%; top 10 = 148%; lucro sem o melhor = 9.55.
- Lucro por ano de fechamento: 2018: -0.2, 2019: 6.0, 2020: 4.2, 2021: -1.2, 2022: -2.3, 2023: 2.3, 2024: 4.0.
