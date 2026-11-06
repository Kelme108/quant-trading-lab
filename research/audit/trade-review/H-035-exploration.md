# Revisão de trades: H-035 (exploração)

Fonte dos trades: `research/experiments/20261106T104439Z-h-035-exploration-btc-usdt/raw/backtest-result-2026-11-06_10-46-35.zip`; `research/experiments/20261106T104439Z-h-035-exploration-eth-usdt/raw/backtest-result-2026-11-06_10-48-39.zip`; `research/experiments/20261106T104439Z-h-035-exploration-bnb-usdt/raw/backtest-result-2026-11-06_10-50-39.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 136; lucro líquido: 1.08.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 90 | 36.58 | 3399% | 1.63% | 72% | 24.0 h |
| below_signal_low | 34 | -19.24 | -1788% | -2.25% | 6% | 13.8 h |
| stop_loss | 12 | -16.26 | -1511% | -5.33% | 0% | 9.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 4 | -2.50 | -2.48% | 0% |
| 3 h a 1 dia | 39 | -32.41 | -3.28% | 3% |
| 1 a 7 dias | 93 | 35.99 | 1.55% | 71% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (67): MFE mediano 4.6%, MAE mediano -0.7%, devolução média do melhor ponto 2.6%, captura mediana 0.48.
- Perdedores (69): MAE mediano -3.0%, MFE mediano 1.0%; 12 (17%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 11.95; 92% do lucro antes de custos.
- Trades < 3 h: 4 (lucro -2.50); reentradas em < 24 h: 7 (lucro 2.39).
- Maior trade = 272% do lucro; top 5 = 987%; top 10 = 1574%; lucro sem o melhor = -1.85.
- Lucro por ano de fechamento: 2017: 0.8, 2018: 2.8, 2019: -3.2, 2020: -0.7, 2021: -0.5, 2022: 3.2, 2023: -1.6, 2024: 0.4.

## ETH/USDT

Trades: 123; lucro líquido: 26.95.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 92 | 57.64 | 214% | 2.22% | 63% | 24.0 h |
| below_signal_low | 19 | -12.78 | -47% | -2.18% | 11% | 11.0 h |
| stop_loss | 12 | -17.90 | -66% | -5.33% | 0% | 9.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 5 | -5.84 | -4.06% | 0% |
| 3 h a 1 dia | 26 | -24.85 | -3.27% | 8% |
| 1 a 7 dias | 92 | 57.64 | 2.22% | 63% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (60): MFE mediano 5.9%, MAE mediano -0.8%, devolução média do melhor ponto 3.2%, captura mediana 0.42.
- Perdedores (63): MAE mediano -2.7%, MFE mediano 1.5%; 19 (30%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 12.61; 32% do lucro antes de custos.
- Trades < 3 h: 5 (lucro -5.84); reentradas em < 24 h: 9 (lucro 5.17).
- Maior trade = 21% do lucro; top 5 = 75%; top 10 = 122%; lucro sem o melhor = 21.40.
- Lucro por ano de fechamento: 2017: 11.1, 2018: -2.9, 2019: 2.1, 2020: 6.2, 2021: 2.5, 2022: 6.8, 2023: -3.5, 2024: 4.6.

## BNB/USDT

Trades: 98; lucro líquido: 1.15.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 57 | 38.55 | 3353% | 2.88% | 77% | 24.0 h |
| below_signal_low | 23 | -14.62 | -1272% | -2.62% | 9% | 12.4 h |
| stop_loss | 18 | -22.78 | -1981% | -5.33% | 0% | 4.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 12 | -15.26 | -5.33% | 0% |
| 3 h a 1 dia | 27 | -21.13 | -3.26% | 7% |
| 1 a 7 dias | 59 | 37.54 | 2.71% | 75% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (46): MFE mediano 5.9%, MAE mediano -1.3%, devolução média do melhor ponto 3.3%, captura mediana 0.53.
- Perdedores (52): MAE mediano -3.9%, MFE mediano 1.3%; 19 (37%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 8.28; 88% do lucro antes de custos.
- Trades < 3 h: 12 (lucro -15.26); reentradas em < 24 h: 5 (lucro -3.70).
- Maior trade = 726% do lucro; top 5 = 1371%; top 10 = 1941%; lucro sem o melhor = -7.19.
- Lucro por ano de fechamento: 2017: -4.0, 2018: -8.6, 2019: 9.2, 2020: -5.1, 2021: 8.1, 2022: 0.0, 2023: 3.5, 2024: -2.0.
