# Revisão de trades: H-036 (exploração)

Fonte dos trades: `research/experiments/20261106T111416Z-h-036-exploration-btc-usdt/raw/backtest-result-2026-11-06_11-15-48.zip`; `research/experiments/20261106T111416Z-h-036-exploration-eth-usdt/raw/backtest-result-2026-11-06_11-18-04.zip`; `research/experiments/20261106T111416Z-h-036-exploration-bnb-usdt/raw/backtest-result-2026-11-06_11-20-14.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 40; lucro líquido: -7.67.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| hold_4_bars | 24 | 6.43 | – | 0.57% | 54% | 4.0 h |
| stop_loss | 16 | -14.10 | – | -1.84% | 0% | 0.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 16 | -14.10 | -1.84% | 0% |
| 3 h a 1 dia | 24 | 6.43 | 0.57% | 54% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (13): MFE mediano 2.4%, MAE mediano -0.4%, devolução média do melhor ponto 1.4%, captura mediana 0.53.
- Perdedores (27): MAE mediano -1.7%, MFE mediano 0.8%; 3 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 6.58; – do lucro antes de custos.
- Trades < 3 h: 16 (lucro -14.10); reentradas em < 24 h: 1 (lucro -0.23).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -9.82.
- Lucro por ano de fechamento: 2017: -2.7, 2018: -0.9, 2019: 1.0, 2020: -3.6, 2021: -2.3, 2022: -0.2, 2023: 1.7, 2024: -0.7.

## ETH/USDT

Trades: 57; lucro líquido: -12.64.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| hold_4_bars | 35 | 6.39 | – | 0.40% | 57% | 4.0 h |
| stop_loss | 22 | -19.03 | – | -1.84% | 0% | 0.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 20 | -17.37 | -1.84% | 0% |
| 3 h a 1 dia | 37 | 4.73 | 0.27% | 54% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (20): MFE mediano 2.7%, MAE mediano -0.6%, devolução média do melhor ponto 1.7%, captura mediana 0.36.
- Perdedores (37): MAE mediano -1.8%, MFE mediano 0.9%; 4 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 9.25; – do lucro antes de custos.
- Trades < 3 h: 20 (lucro -17.37); reentradas em < 24 h: 2 (lucro -1.73).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -14.91.
- Lucro por ano de fechamento: 2017: -2.7, 2018: -1.3, 2019: -1.1, 2020: -1.0, 2021: -4.2, 2022: -0.6, 2023: 1.0, 2024: -2.7.

## BNB/USDT

Trades: 62; lucro líquido: -0.56.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 31 | -31.08 | – | -1.84% | 0% | 0.6 h |
| hold_4_bars | 31 | 30.51 | – | 1.91% | 55% | 4.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 28 | -27.99 | -1.84% | 0% |
| 3 h a 1 dia | 34 | 27.43 | 1.58% | 50% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (17): MFE mediano 2.2%, MAE mediano -0.8%, devolução média do melhor ponto 2.1%, captura mediana 0.47.
- Perdedores (45): MAE mediano -1.9%, MFE mediano 0.9%; 11 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 11.80; 105% do lucro antes de custos.
- Trades < 3 h: 28 (lucro -27.99); reentradas em < 24 h: 3 (lucro -1.37).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -17.78.
- Lucro por ano de fechamento: 2017: 14.5, 2018: -1.2, 2019: 1.2, 2020: -2.2, 2021: -7.3, 2022: -1.2, 2023: -2.7, 2024: -1.7.
