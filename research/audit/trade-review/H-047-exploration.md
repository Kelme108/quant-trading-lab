# Revisão de trades: H-047 (exploração)

Fonte dos trades: `research/experiments/20261106T170340Z-h-047-exploration-btc-usdt/raw/backtest-result-2026-11-06_17-06-39.zip`; `research/experiments/20261106T170340Z-h-047-exploration-eth-usdt/raw/backtest-result-2026-11-06_17-09-40.zip`; `research/experiments/20261106T170340Z-h-047-exploration-bnb-usdt/raw/backtest-result-2026-11-06_17-12-37.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 174; lucro líquido: 22.27.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| ratio_weak_or_regime_lost | 162 | 38.82 | 174% | 1.12% | 44% | 34.0 h |
| stop_loss | 12 | -16.54 | -74% | -6.33% | 0% | 19.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 15 | -5.22 | -1.59% | 7% |
| 3 h a 1 dia | 67 | -24.25 | -1.60% | 24% |
| 1 a 7 dias | 92 | 51.74 | 2.57% | 59% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (71): MFE mediano 6.5%, MAE mediano -0.8%, devolução média do melhor ponto 3.3%, captura mediana 0.56.
- Perdedores (103): MAE mediano -2.8%, MFE mediano 0.8%; 25 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 13.69; 38% do lucro antes de custos.
- Trades < 3 h: 15 (lucro -5.22); reentradas em < 24 h: 38 (lucro -2.83).
- Maior trade = 19% do lucro; top 5 = 81%; top 10 = 136%; lucro sem o melhor = 17.94.
- Lucro por ano de fechamento: 2017: 4.0, 2018: -5.1, 2019: 6.4, 2020: 10.4, 2021: 6.9, 2022: -6.8, 2023: 4.4, 2024: 2.1.

## ETH/USDT

Trades: 223; lucro líquido: 15.83.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| ratio_weak_or_regime_lost | 196 | 50.99 | 322% | 1.28% | 45% | 32.4 h |
| stop_loss | 27 | -35.16 | -222% | -6.33% | 0% | 18.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 18 | -7.84 | -2.24% | 6% |
| 3 h a 1 dia | 93 | -37.17 | -1.94% | 16% |
| 1 a 7 dias | 112 | 60.84 | 2.68% | 64% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (88): MFE mediano 7.5%, MAE mediano -1.1%, devolução média do melhor ponto 4.1%, captura mediana 0.49.
- Perdedores (135): MAE mediano -3.2%, MFE mediano 1.4%; 48 (36%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 16.17; 51% do lucro antes de custos.
- Trades < 3 h: 18 (lucro -7.84); reentradas em < 24 h: 31 (lucro 2.00).
- Maior trade = 40% do lucro; top 5 = 146%; top 10 = 240%; lucro sem o melhor = 9.52.
- Lucro por ano de fechamento: 2017: -1.9, 2018: -3.3, 2019: -1.0, 2020: 12.7, 2021: -2.9, 2022: 7.9, 2023: 3.2, 2024: 1.1.

## BNB/USDT

Trades: 211; lucro líquido: 81.29.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| ratio_weak_or_regime_lost | 182 | 134.69 | 166% | 2.73% | 48% | 32.7 h |
| stop_loss | 28 | -53.36 | -66% | -6.33% | 0% | 12.2 h |
| force_exit | 1 | -0.04 | -0% | -0.12% | 0% | 1.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 23 | -23.16 | -3.42% | 0% |
| 3 h a 1 dia | 81 | -50.92 | -2.03% | 21% |
| 1 a 7 dias | 107 | 155.37 | 5.26% | 66% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (88): MFE mediano 8.4%, MAE mediano -1.3%, devolução média do melhor ponto 7.5%, captura mediana 0.50.
- Perdedores (123): MAE mediano -3.6%, MFE mediano 1.5%; 47 (38%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 23.09; 22% do lucro antes de custos.
- Trades < 3 h: 23 (lucro -23.16); reentradas em < 24 h: 33 (lucro 9.47).
- Maior trade = 31% do lucro; top 5 = 88%; top 10 = 124%; lucro sem o melhor = 56.35.
- Lucro por ano de fechamento: 2017: 26.7, 2018: 3.7, 2019: 11.9, 2020: -4.9, 2021: 41.5, 2022: -3.7, 2023: 5.8, 2024: 0.2.
