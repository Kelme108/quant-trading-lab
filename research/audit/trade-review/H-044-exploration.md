# Revisão de trades: H-044 (exploração)

Fonte dos trades: `research/experiments/20261106T151002Z-h-044-exploration-btc-usdt/raw/backtest-result-2026-11-06_15-12-34.zip`; `research/experiments/20261106T151002Z-h-044-exploration-eth-usdt/raw/backtest-result-2026-11-06_15-14-31.zip`; `research/experiments/20261106T151002Z-h-044-exploration-bnb-usdt/raw/backtest-result-2026-11-06_15-16-28.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 432; lucro líquido: 9.10.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| ha4h_bearish | 418 | 26.31 | 289% | 0.29% | 30% | 19.9 h |
| stop_loss | 14 | -17.21 | -189% | -5.33% | 0% | 9.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 4 | -4.94 | -5.33% | 0% |
| 3 h a 1 dia | 287 | -83.46 | -1.29% | 5% |
| 1 a 7 dias | 141 | 97.50 | 3.12% | 80% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (127): MFE mediano 4.9%, MAE mediano -0.5%, devolução média do melhor ponto 3.3%, captura mediana 0.47.
- Perdedores (305): MAE mediano -1.7%, MFE mediano 0.8%; 45 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 33.76; 79% do lucro antes de custos.
- Trades < 3 h: 4 (lucro -4.94); reentradas em < 24 h: 113 (lucro 3.86).
- Maior trade = 84% do lucro; top 5 = 234%; top 10 = 373%; lucro sem o melhor = 1.45.
- Lucro por ano de fechamento: 2017: 12.4, 2018: -2.8, 2019: 11.9, 2020: -2.3, 2021: -9.3, 2022: -4.2, 2023: 1.0, 2024: 2.4.

## ETH/USDT

Trades: 407; lucro líquido: 37.44.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| ha4h_bearish | 382 | 68.78 | 184% | 0.79% | 36% | 20.1 h |
| stop_loss | 25 | -31.34 | -84% | -5.33% | 0% | 10.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 2 | -2.44 | -5.33% | 0% |
| 3 h a 1 dia | 277 | -99.12 | -1.49% | 12% |
| 1 a 7 dias | 128 | 139.00 | 4.62% | 84% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (139): MFE mediano 6.5%, MAE mediano -0.8%, devolução média do melhor ponto 4.0%, captura mediana 0.43.
- Perdedores (268): MAE mediano -2.0%, MFE mediano 0.9%; 52 (19%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 34.44; 48% do lucro antes de custos.
- Trades < 3 h: 2 (lucro -2.44); reentradas em < 24 h: 105 (lucro 4.98).
- Maior trade = 24% do lucro; top 5 = 75%; top 10 = 120%; lucro sem o melhor = 28.41.
- Lucro por ano de fechamento: 2017: 5.5, 2018: 9.9, 2019: -3.3, 2020: 9.0, 2021: 1.9, 2022: 7.2, 2023: -0.0, 2024: 7.2.

## BNB/USDT

Trades: 448; lucro líquido: 37.34.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| ha4h_bearish | 420 | 75.93 | 203% | 0.78% | 35% | 19.8 h |
| stop_loss | 28 | -38.59 | -103% | -5.33% | 0% | 9.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 6 | -8.15 | -5.33% | 0% |
| 3 h a 1 dia | 303 | -111.48 | -1.42% | 13% |
| 1 a 7 dias | 139 | 156.97 | 4.60% | 77% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (147): MFE mediano 6.4%, MAE mediano -1.0%, devolução média do melhor ponto 4.7%, captura mediana 0.37.
- Perdedores (301): MAE mediano -2.2%, MFE mediano 1.1%; 78 (26%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 40.27; 52% do lucro antes de custos.
- Trades < 3 h: 6 (lucro -8.15); reentradas em < 24 h: 115 (lucro -3.26).
- Maior trade = 65% do lucro; top 5 = 142%; top 10 = 193%; lucro sem o melhor = 13.20.
- Lucro por ano de fechamento: 2017: -1.1, 2018: 16.5, 2019: 6.7, 2020: -5.2, 2021: 27.4, 2022: -5.9, 2023: -6.2, 2024: 5.2.
