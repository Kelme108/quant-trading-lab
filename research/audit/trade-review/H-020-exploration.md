# Revisão de trades: H-020 (exploração)

Fonte dos trades: `research/experiments/20261105T181137Z-h-020-exploration-btc-usdt/raw/backtest-result-2026-11-05_18-13-11.zip`; `research/experiments/20261105T181137Z-h-020-exploration-eth-usdt/raw/backtest-result-2026-11-05_18-15-51.zip`; `research/experiments/20261105T181137Z-h-020-exploration-bnb-usdt/raw/backtest-result-2026-11-05_18-18-23.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 58; lucro líquido: 5.73.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| daily_high7 | 57 | 6.11 | 107% | 1.08% | 68% | 227.8 h |
| force_exit | 1 | -0.38 | -7% | -3.73% | 0% | 19.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 0 | 0.00 | – | – |
| 3 h a 1 dia | 1 | -0.38 | -3.73% | 0% |
| 1 a 7 dias | 21 | 10.35 | 4.87% | 95% |
| 7 a 30 dias | 35 | -1.86 | -0.50% | 54% |
| > 30 dias | 1 | -2.39 | -23.41% | 0% |

### Excursões (antes de custos)

- Vencedores (39): MFE mediano 6.2%, MAE mediano -2.7%, devolução média do melhor ponto 2.2%, captura mediana 0.66.
- Perdedores (19): MAE mediano -11.3%, MFE mediano 1.9%; 9 (47%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 2.05; 26% do lucro antes de custos.
- Trades < 3 h: 0 (lucro 0.00); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = 25% do lucro; top 5 = 97%; top 10 = 153%; lucro sem o melhor = 4.29.
- Lucro por ano de fechamento: 2018: -1.0, 2019: -0.4, 2020: 3.9, 2021: -1.7, 2023: 3.1, 2024: 1.9.

## ETH/USDT

Trades: 66; lucro líquido: 4.96.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| daily_high7 | 65 | 6.79 | 137% | 1.09% | 68% | 230.4 h |
| force_exit | 1 | -1.83 | -37% | -17.11% | 0% | 648.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 0 | 0.00 | – | – |
| 3 h a 1 dia | 0 | 0.00 | – | – |
| 1 a 7 dias | 23 | 20.90 | 9.19% | 100% |
| 7 a 30 dias | 41 | -7.43 | -1.79% | 51% |
| > 30 dias | 2 | -8.51 | -42.20% | 0% |

### Excursões (antes de custos)

- Vencedores (44): MFE mediano 7.7%, MAE mediano -4.1%, devolução média do melhor ponto 2.5%, captura mediana 0.76.
- Perdedores (22): MAE mediano -18.9%, MFE mediano 2.9%; 14 (64%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 2.29; 32% do lucro antes de custos.
- Trades < 3 h: 0 (lucro 0.00); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = 49% do lucro; top 5 = 180%; top 10 = 302%; lucro sem o melhor = 2.51.
- Lucro por ano de fechamento: 2018: -6.9, 2019: -0.9, 2020: 5.9, 2021: 7.1, 2022: -3.4, 2023: 3.9, 2024: -0.8.

## BNB/USDT

Trades: 64; lucro líquido: 7.13.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| daily_high7 | 64 | 7.13 | 100% | 1.13% | 64% | 240.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 0 | 0.00 | – | – |
| 3 h a 1 dia | 0 | 0.00 | – | – |
| 1 a 7 dias | 28 | 26.62 | 9.27% | 100% |
| 7 a 30 dias | 35 | -16.46 | -4.52% | 37% |
| > 30 dias | 1 | -3.03 | -28.84% | 0% |

### Excursões (antes de custos)

- Vencedores (41): MFE mediano 9.0%, MAE mediano -3.6%, devolução média do melhor ponto 2.5%, captura mediana 0.72.
- Perdedores (23): MAE mediano -18.3%, MFE mediano 2.2%; 12 (52%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 2.33; 25% do lucro antes de custos.
- Trades < 3 h: 0 (lucro 0.00); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = 32% do lucro; top 5 = 136%; top 10 = 227%; lucro sem o melhor = 4.86.
- Lucro por ano de fechamento: 2018: -0.8, 2019: 2.7, 2020: 1.9, 2021: 4.1, 2022: -4.1, 2023: -0.1, 2024: 3.5.
