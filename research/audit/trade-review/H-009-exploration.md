# Revisão de trades: H-009 (exploração)

Fonte dos trades: `research/experiments/20261103T000056Z-h-009-exploration-btc-usdt/raw/backtest-result-2026-11-03_00-01-21.zip`; `research/experiments/20261103T000056Z-h-009-exploration-eth-usdt/raw/backtest-result-2026-11-03_00-03-20.zip`; `research/experiments/20261103T000056Z-h-009-exploration-bnb-usdt/raw/backtest-result-2026-11-03_00-05-16.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 58; lucro líquido: 113.80.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| low72_or_regime_lost | 49 | 140.15 | 123% | 7.81% | 45% | 207.7 h |
| stop_loss | 9 | -26.35 | -23% | -6.33% | 0% | 55.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 2 | -1.69 | -1.63% | 0% |
| 3 h a 1 dia | 8 | -13.68 | -3.60% | 0% |
| 1 a 7 dias | 26 | -31.92 | -2.67% | 15% |
| 7 a 30 dias | 21 | 147.77 | 18.72% | 81% |
| > 30 dias | 1 | 13.32 | 34.37% | 100% |

### Excursões (antes de custos)

- Vencedores (22): MFE mediano 24.2%, MAE mediano -1.0%, devolução média do melhor ponto 13.8%, captura mediana 0.58.
- Perdedores (36): MAE mediano -4.4%, MFE mediano 1.7%; 17 (47%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 9.20; 7% do lucro antes de custos.
- Trades < 3 h: 2 (lucro -1.69); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = 22% do lucro; top 5 = 71%; top 10 = 116%; lucro sem o melhor = 89.26.
- Lucro por ano de fechamento: 2017: 24.5, 2018: -2.0, 2019: 26.1, 2020: 25.7, 2021: 21.4, 2023: 9.9, 2024: 8.1.

## ETH/USDT

Trades: 81; lucro líquido: 61.77.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| low72_or_regime_lost | 59 | 113.74 | 184% | 5.96% | 42% | 159.3 h |
| stop_loss | 22 | -51.97 | -84% | -6.33% | 0% | 42.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 7 | -7.47 | -3.47% | 0% |
| 3 h a 1 dia | 11 | -16.14 | -3.84% | 0% |
| 1 a 7 dias | 39 | -53.56 | -3.60% | 10% |
| 7 a 30 dias | 23 | 117.89 | 15.69% | 87% |
| > 30 dias | 1 | 21.05 | 58.41% | 100% |

### Excursões (antes de custos)

- Vencedores (25): MFE mediano 20.3%, MAE mediano -2.0%, devolução média do melhor ponto 17.2%, captura mediana 0.36.
- Perdedores (56): MAE mediano -4.8%, MFE mediano 2.0%; 28 (50%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 10.52; 15% do lucro antes de custos.
- Trades < 3 h: 7 (lucro -7.47); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = 38% do lucro; top 5 = 136%; top 10 = 189%; lucro sem o melhor = 38.56.
- Lucro por ano de fechamento: 2017: 1.6, 2018: 9.2, 2019: 10.7, 2020: 31.2, 2021: 12.5, 2022: -3.7, 2023: -15.9, 2024: 16.2.

## BNB/USDT

Trades: 80; lucro líquido: 133.57.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| low72_or_regime_lost | 58 | 200.33 | 150% | 10.16% | 43% | 153.7 h |
| stop_loss | 22 | -66.75 | -50% | -6.32% | 0% | 78.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 3 | -6.41 | -5.17% | 0% |
| 3 h a 1 dia | 15 | -27.97 | -3.45% | 0% |
| 1 a 7 dias | 36 | -45.56 | -2.95% | 19% |
| 7 a 30 dias | 26 | 213.51 | 23.97% | 69% |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (25): MFE mediano 26.4%, MAE mediano -1.9%, devolução média do melhor ponto 27.2%, captura mediana 0.39.
- Perdedores (55): MAE mediano -5.7%, MFE mediano 3.9%; 35 (64%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 13.07; 9% do lucro antes de custos.
- Trades < 3 h: 3 (lucro -6.41); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = 80% do lucro; top 5 = 139%; top 10 = 162%; lucro sem o melhor = 26.98.
- Lucro por ano de fechamento: 2018: -5.3, 2019: 24.6, 2020: 2.9, 2021: 134.3, 2022: -18.3, 2023: -10.6, 2024: 6.0.
