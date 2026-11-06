# Revisão de trades: H-038 (exploração)

Fonte dos trades: `research/experiments/20261106T120241Z-h-038-exploration-btc-usdt/raw/backtest-result-2026-11-06_12-04-22.zip`; `research/experiments/20261106T120241Z-h-038-exploration-eth-usdt/raw/backtest-result-2026-11-06_12-06-44.zip`; `research/experiments/20261106T120241Z-h-038-exploration-bnb-usdt/raw/backtest-result-2026-11-06_12-09-01.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 42; lucro líquido: -11.19.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 26 | -16.11 | – | -3.34% | 0% | 11.1 h |
| time_stop_48 | 9 | 0.68 | – | 0.42% | 67% | 48.0 h |
| target_24h_high | 7 | 4.25 | – | 3.38% | 100% | 15.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 4 | -2.49 | -3.34% | 0% |
| 3 h a 1 dia | 24 | -8.88 | -1.97% | 21% |
| 1 a 7 dias | 14 | 0.18 | 0.10% | 57% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (13): MFE mediano 3.1%, MAE mediano -0.6%, devolução média do melhor ponto 1.5%, captura mediana 0.71.
- Perdedores (29): MAE mediano -3.5%, MFE mediano 0.7%; 5 (17%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 2.69; – do lucro antes de custos.
- Trades < 3 h: 4 (lucro -2.49); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -12.23.
- Lucro por ano de fechamento: 2018: -4.8, 2019: -2.0, 2020: -0.4, 2021: -2.3, 2022: 1.0, 2023: -1.3, 2024: -1.4.

## ETH/USDT

Trades: 54; lucro líquido: -15.18.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 34 | -20.94 | – | -3.34% | 0% | 10.3 h |
| time_stop_48 | 14 | 1.80 | – | 0.70% | 57% | 48.0 h |
| target_24h_high | 6 | 3.97 | – | 3.61% | 100% | 24.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 10 | -6.24 | -3.34% | 0% |
| 3 h a 1 dia | 21 | -10.18 | -2.65% | 10% |
| 1 a 7 dias | 23 | 1.25 | 0.30% | 52% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (14): MFE mediano 4.7%, MAE mediano -1.4%, devolução média do melhor ponto 2.3%, captura mediana 0.61.
- Perdedores (40): MAE mediano -3.6%, MFE mediano 1.6%; 14 (35%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 3.42; – do lucro antes de custos.
- Trades < 3 h: 10 (lucro -6.24); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -16.35.
- Lucro por ano de fechamento: 2017: -1.3, 2018: -4.9, 2019: -0.6, 2020: 0.1, 2021: -3.1, 2022: -2.7, 2023: -0.9, 2024: -1.8.

## BNB/USDT

Trades: 44; lucro líquido: -4.71.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 22 | -14.33 | – | -3.33% | 0% | 7.5 h |
| time_stop_48 | 17 | 5.72 | – | 1.73% | 71% | 48.0 h |
| target_24h_high | 5 | 3.90 | – | 4.02% | 100% | 28.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 6 | -3.89 | -3.33% | 0% |
| 3 h a 1 dia | 16 | -9.09 | -2.90% | 6% |
| 1 a 7 dias | 22 | 8.26 | 1.94% | 73% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (17): MFE mediano 5.3%, MAE mediano -1.3%, devolução média do melhor ponto 2.5%, captura mediana 0.49.
- Perdedores (27): MAE mediano -3.2%, MFE mediano 1.1%; 9 (33%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 2.97; – do lucro antes de custos.
- Trades < 3 h: 6 (lucro -3.89); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -6.29.
- Lucro por ano de fechamento: 2018: 0.1, 2019: -2.7, 2020: -0.2, 2021: -1.7, 2022: -0.1, 2023: -0.4, 2024: 0.2.
