# Revisão de trades: H-057 (exploração)

Fonte dos trades: `research/experiments/20261106T224933Z-h-057-exploration-btc-usdt/raw/backtest-result-2026-11-06_22-56-25.zip`; `research/experiments/20261106T224933Z-h-057-exploration-eth-usdt/raw/backtest-result-2026-11-06_23-02-02.zip`; `research/experiments/20261106T224933Z-h-057-exploration-bnb-usdt/raw/backtest-result-2026-11-06_23-07-41.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 499; lucro líquido: -0.95.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24_bars | 350 | 82.07 | – | 1.58% | 65% | 24.0 h |
| stop_loss | 93 | -59.62 | – | -4.29% | 0% | 9.2 h |
| failure_below_day_open | 56 | -23.40 | – | -2.81% | 0% | 11.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 23 | -13.79 | -4.03% | 0% |
| 3 h a 1 dia | 124 | -68.40 | -3.69% | 0% |
| 1 a 7 dias | 352 | 81.24 | 1.56% | 64% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (226): MFE mediano 4.2%, MAE mediano -0.8%, devolução média do melhor ponto 2.3%, captura mediana 0.51.
- Perdedores (273): MAE mediano -3.2%, MFE mediano 1.0%; 65 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 22.16; 104% do lucro antes de custos.
- Trades < 3 h: 23 (lucro -13.79); reentradas em < 24 h: 96 (lucro -9.78).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -4.01.
- Lucro por ano de fechamento: 2017: 2.5, 2018: -8.4, 2019: 1.3, 2020: 7.7, 2021: -1.5, 2022: -0.7, 2023: -1.5, 2024: -0.4.

## ETH/USDT

Trades: 516; lucro líquido: 10.44.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24_bars | 351 | 113.17 | 1084% | 2.06% | 66% | 24.0 h |
| stop_loss | 120 | -81.04 | -776% | -4.29% | 0% | 9.0 h |
| failure_below_day_open | 45 | -21.69 | -208% | -3.04% | 0% | 10.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 38 | -24.59 | -4.10% | 0% |
| 3 h a 1 dia | 126 | -77.46 | -3.90% | 0% |
| 1 a 7 dias | 352 | 112.49 | 2.05% | 66% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (231): MFE mediano 5.0%, MAE mediano -0.9%, devolução média do melhor ponto 2.7%, captura mediana 0.57.
- Perdedores (285): MAE mediano -3.9%, MFE mediano 1.4%; 92 (32%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 24.46; 70% do lucro antes de custos.
- Trades < 3 h: 38 (lucro -24.59); reentradas em < 24 h: 100 (lucro 0.75).
- Maior trade = 31% do lucro; top 5 = 124%; top 10 = 215%; lucro sem o melhor = 7.24.
- Lucro por ano de fechamento: 2017: 5.3, 2018: -6.9, 2019: 4.2, 2020: 6.1, 2021: -0.6, 2022: 3.5, 2023: 1.7, 2024: -2.7.

## BNB/USDT

Trades: 516; lucro líquido: 22.04.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24_bars | 339 | 138.51 | 628% | 2.42% | 68% | 24.0 h |
| stop_loss | 121 | -88.23 | -400% | -4.28% | 0% | 8.5 h |
| failure_below_day_open | 56 | -28.24 | -128% | -2.85% | 0% | 11.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 38 | -26.30 | -4.16% | 0% |
| 3 h a 1 dia | 135 | -88.26 | -3.77% | 0% |
| 1 a 7 dias | 343 | 136.60 | 2.36% | 67% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (229): MFE mediano 5.2%, MAE mediano -1.1%, devolução média do melhor ponto 3.0%, captura mediana 0.52.
- Perdedores (287): MAE mediano -3.8%, MFE mediano 1.0%; 75 (26%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 26.68; 55% do lucro antes de custos.
- Trades < 3 h: 38 (lucro -26.30); reentradas em < 24 h: 135 (lucro 9.47).
- Maior trade = 25% do lucro; top 5 = 105%; top 10 = 171%; lucro sem o melhor = 16.47.
- Lucro por ano de fechamento: 2017: 0.1, 2018: 0.2, 2019: 4.8, 2020: 4.9, 2021: 17.5, 2022: -1.1, 2023: -6.2, 2024: 1.7.
