# Revisão de trades: H-024 (exploração)

Fonte dos trades: `research/experiments/20261105T192422Z-h-024-exploration-btc-usdt/raw/backtest-result-2026-11-05_19-25-54.zip`; `research/experiments/20261105T192422Z-h-024-exploration-eth-usdt/raw/backtest-result-2026-11-05_19-28-12.zip`; `research/experiments/20261105T192422Z-h-024-exploration-bnb-usdt/raw/backtest-result-2026-11-05_19-33-02.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 43; lucro líquido: 99.31.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| close_below_sma20 | 42 | 105.12 | 106% | 7.43% | 52% | 406.8 h |
| stop_loss | 1 | -5.81 | -6% | -12.31% | 0% | 94.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 0 | 0.00 | – | – |
| 3 h a 1 dia | 0 | 0.00 | – | – |
| 1 a 7 dias | 13 | -38.57 | -6.89% | 0% |
| 7 a 30 dias | 26 | 53.78 | 5.68% | 69% |
| > 30 dias | 4 | 84.10 | 60.40% | 100% |

### Excursões (antes de custos)

- Vencedores (22): MFE mediano 19.8%, MAE mediano -1.7%, devolução média do melhor ponto 14.5%, captura mediana 0.50.
- Perdedores (21): MAE mediano -6.1%, MFE mediano 2.2%; 13 (62%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 6.17; 6% do lucro antes de custos.
- Trades < 3 h: 0 (lucro 0.00); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = 31% do lucro; top 5 = 99%; top 10 = 139%; lucro sem o melhor = 68.85.
- Lucro por ano de fechamento: 2018: 0.1, 2019: 23.3, 2020: 25.7, 2021: 45.0, 2022: -18.6, 2023: 11.1, 2024: 12.6.

## ETH/USDT

Trades: 36; lucro líquido: 44.53.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| close_below_sma20 | 29 | 70.37 | 158% | 8.56% | 62% | 482.3 h |
| stop_loss | 7 | -25.84 | -58% | -12.31% | 0% | 76.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 0 | 0.00 | – | – |
| 3 h a 1 dia | 2 | -6.85 | -12.31% | 0% |
| 1 a 7 dias | 8 | -25.43 | -9.64% | 0% |
| 7 a 30 dias | 21 | 21.06 | 3.62% | 62% |
| > 30 dias | 5 | 55.75 | 37.58% | 100% |

### Excursões (antes de custos)

- Vencedores (18): MFE mediano 33.1%, MAE mediano -3.7%, devolução média do melhor ponto 19.2%, captura mediana 0.38.
- Perdedores (18): MAE mediano -11.4%, MFE mediano 4.1%; 12 (67%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 3.93; 8% do lucro antes de custos.
- Trades < 3 h: 0 (lucro 0.00); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = 40% do lucro; top 5 = 130%; top 10 = 180%; lucro sem o melhor = 26.87.
- Lucro por ano de fechamento: 2018: 1.5, 2019: -1.4, 2020: 14.8, 2021: 20.9, 2022: 2.9, 2023: 2.4, 2024: 3.6.

## BNB/USDT

Trades: 39; lucro líquido: 189.69.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| close_below_sma20 | 29 | 238.73 | 126% | 22.92% | 52% | 431.8 h |
| stop_loss | 9 | -45.00 | -24% | -12.30% | 0% | 77.4 h |
| force_exit | 1 | -4.04 | -2% | -5.52% | 0% | 126.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 0 | 0.00 | – | – |
| 3 h a 1 dia | 0 | 0.00 | – | – |
| 1 a 7 dias | 17 | -69.60 | -9.03% | 0% |
| 7 a 30 dias | 17 | 26.76 | 5.61% | 59% |
| > 30 dias | 5 | 232.53 | 121.31% | 100% |

### Excursões (antes de custos)

- Vencedores (15): MFE mediano 41.7%, MAE mediano -3.4%, devolução média do melhor ponto 33.2%, captura mediana 0.53.
- Perdedores (24): MAE mediano -10.2%, MFE mediano 4.8%; 19 (79%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 6.39; 3% do lucro antes de custos.
- Trades < 3 h: 0 (lucro 0.00); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = 50% do lucro; top 5 = 123%; top 10 = 139%; lucro sem o melhor = 94.98.
- Lucro por ano de fechamento: 2019: 9.4, 2020: -1.2, 2021: 149.5, 2022: -8.9, 2023: -3.0, 2024: 44.0.
