# Revisão de trades: H-045 (exploração)

Fonte dos trades: `research/experiments/20261106T153852Z-h-045-exploration-btc-usdt/raw/backtest-result-2026-11-06_15-42-21.zip`; `research/experiments/20261106T153852Z-h-045-exploration-eth-usdt/raw/backtest-result-2026-11-06_15-45-18.zip`; `research/experiments/20261106T153852Z-h-045-exploration-bnb-usdt/raw/backtest-result-2026-11-06_15-48-15.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 285; lucro líquido: 12.84.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| swing_low_break | 224 | 41.75 | 325% | 1.74% | 46% | 56.8 h |
| stop_loss | 61 | -28.91 | -225% | -4.34% | 0% | 16.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 9 | -4.28 | -4.28% | 0% |
| 3 h a 1 dia | 87 | -30.00 | -3.16% | 6% |
| 1 a 7 dias | 183 | 34.21 | 1.74% | 50% |
| 7 a 30 dias | 6 | 12.91 | 20.30% | 100% |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (103): MFE mediano 10.0%, MAE mediano -0.8%, devolução média do melhor ponto 5.9%, captura mediana 0.47.
- Perdedores (182): MAE mediano -3.4%, MFE mediano 1.5%; 67 (37%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 10.90; 46% do lucro antes de custos.
- Trades < 3 h: 9 (lucro -4.28); reentradas em < 24 h: 26 (lucro 2.65).
- Maior trade = 34% do lucro; top 5 = 111%; top 10 = 178%; lucro sem o melhor = 8.42.
- Lucro por ano de fechamento: 2017: 7.0, 2018: -1.6, 2019: 4.8, 2020: 3.4, 2021: -1.3, 2022: -3.4, 2023: 3.5, 2024: 0.4.

## ETH/USDT

Trades: 364; lucro líquido: 8.81.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| swing_low_break | 279 | 46.31 | 526% | 1.65% | 47% | 44.0 h |
| stop_loss | 85 | -37.50 | -426% | -4.33% | 0% | 14.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 15 | -6.18 | -4.05% | 0% |
| 3 h a 1 dia | 146 | -39.90 | -2.67% | 11% |
| 1 a 7 dias | 198 | 49.40 | 2.47% | 56% |
| 7 a 30 dias | 5 | 5.49 | 10.73% | 100% |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (132): MFE mediano 9.5%, MAE mediano -1.1%, devolução média do melhor ponto 6.3%, captura mediana 0.40.
- Perdedores (232): MAE mediano -3.7%, MFE mediano 1.7%; 100 (43%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 13.08; 60% do lucro antes de custos.
- Trades < 3 h: 15 (lucro -6.18); reentradas em < 24 h: 66 (lucro -2.40).
- Maior trade = 39% do lucro; top 5 = 162%; top 10 = 262%; lucro sem o melhor = 5.35.
- Lucro por ano de fechamento: 2017: -0.7, 2018: 0.0, 2019: -2.1, 2020: 2.6, 2021: 9.5, 2022: -4.0, 2023: 2.6, 2024: 0.9.

## BNB/USDT

Trades: 362; lucro líquido: 7.49.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| swing_low_break | 279 | 44.43 | 593% | 1.59% | 43% | 43.9 h |
| stop_loss | 83 | -36.93 | -493% | -4.33% | 0% | 15.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 11 | -5.00 | -4.33% | 0% |
| 3 h a 1 dia | 149 | -41.91 | -2.75% | 11% |
| 1 a 7 dias | 199 | 45.35 | 2.24% | 51% |
| 7 a 30 dias | 3 | 9.06 | 32.15% | 67% |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (120): MFE mediano 9.3%, MAE mediano -1.4%, devolução média do melhor ponto 6.8%, captura mediana 0.37.
- Perdedores (242): MAE mediano -3.7%, MFE mediano 1.6%; 99 (41%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 12.98; 63% do lucro antes de custos.
- Trades < 3 h: 11 (lucro -5.00); reentradas em < 24 h: 57 (lucro 19.35).
- Maior trade = 141% do lucro; top 5 = 393%; top 10 = 498%; lucro sem o melhor = -3.10.
- Lucro por ano de fechamento: 2018: -5.4, 2019: 0.1, 2020: 1.2, 2021: 16.5, 2022: -2.4, 2023: -3.5, 2024: 1.0.
