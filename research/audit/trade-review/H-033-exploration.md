# Revisão de trades: H-033 (exploração)

Fonte dos trades: `research/experiments/20261106T095933Z-h-033-exploration-btc-usdt/raw/backtest-result-2026-11-06_10-01-22.zip`; `research/experiments/20261106T095933Z-h-033-exploration-eth-usdt/raw/backtest-result-2026-11-06_10-03-08.zip`; `research/experiments/20261106T095933Z-h-033-exploration-bnb-usdt/raw/backtest-result-2026-11-06_10-04-58.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 99; lucro líquido: -3.70.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| regain_or_time | 65 | 13.81 | – | 2.21% | 71% | 20.4 h |
| stop_loss | 34 | -17.51 | – | -5.33% | 0% | 6.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 12 | -4.61 | -3.96% | 8% |
| 3 h a 1 dia | 39 | -3.09 | -0.80% | 41% |
| 1 a 7 dias | 48 | 3.99 | 0.87% | 60% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (46): MFE mediano 5.5%, MAE mediano -1.8%, devolução média do melhor ponto 2.1%, captura mediana 0.62.
- Perdedores (53): MAE mediano -5.8%, MFE mediano 1.4%; 23 (43%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 3.32; – do lucro antes de custos.
- Trades < 3 h: 12 (lucro -4.61); reentradas em < 24 h: 10 (lucro -1.67).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -4.75.
- Lucro por ano de fechamento: 2017: -1.2, 2018: -0.8, 2019: -3.3, 2020: -0.1, 2021: 1.6, 2022: -0.5, 2023: 1.4, 2024: -0.9.

## ETH/USDT

Trades: 171; lucro líquido: -8.17.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| regain_or_time | 100 | 27.77 | – | 2.95% | 85% | 18.8 h |
| stop_loss | 71 | -35.93 | – | -5.33% | 0% | 7.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 26 | -10.37 | -4.18% | 12% |
| 3 h a 1 dia | 86 | -4.18 | -0.51% | 44% |
| 1 a 7 dias | 59 | 6.39 | 1.17% | 75% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (85): MFE mediano 5.5%, MAE mediano -1.5%, devolução média do melhor ponto 1.8%, captura mediana 0.72.
- Perdedores (86): MAE mediano -6.2%, MFE mediano 1.6%; 39 (45%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 5.61; – do lucro antes de custos.
- Trades < 3 h: 26 (lucro -10.37); reentradas em < 24 h: 16 (lucro -0.65).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -9.27.
- Lucro por ano de fechamento: 2017: -1.7, 2018: -3.5, 2019: 0.5, 2020: -0.2, 2021: -3.0, 2022: -0.6, 2023: 1.5, 2024: -1.2.

## BNB/USDT

Trades: 190; lucro líquido: -8.20.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| regain_or_time | 108 | 33.80 | – | 3.28% | 78% | 18.5 h |
| stop_loss | 82 | -42.00 | – | -5.33% | 0% | 8.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 24 | -7.13 | -3.09% | 17% |
| 3 h a 1 dia | 105 | -6.72 | -0.64% | 41% |
| 1 a 7 dias | 61 | 5.65 | 0.96% | 61% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (84): MFE mediano 6.2%, MAE mediano -1.4%, devolução média do melhor ponto 2.2%, captura mediana 0.73.
- Perdedores (106): MAE mediano -5.9%, MFE mediano 2.3%; 59 (56%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 6.33; – do lucro antes de custos.
- Trades < 3 h: 24 (lucro -7.13); reentradas em < 24 h: 20 (lucro -2.96).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -9.87.
- Lucro por ano de fechamento: 2017: -0.4, 2018: -5.3, 2019: 4.6, 2020: -1.9, 2021: -3.7, 2022: 0.4, 2023: -0.5, 2024: -1.3.
