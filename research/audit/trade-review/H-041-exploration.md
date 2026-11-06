# Revisão de trades: H-041 (exploração)

Fonte dos trades: `research/experiments/20261106T134611Z-h-041-exploration-btc-usdt/raw/backtest-result-2026-11-06_13-48-24.zip`; `research/experiments/20261106T134611Z-h-041-exploration-eth-usdt/raw/backtest-result-2026-11-06_13-50-18.zip`; `research/experiments/20261106T134611Z-h-041-exploration-bnb-usdt/raw/backtest-result-2026-11-06_13-52-09.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 210; lucro líquido: -4.49.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| vwap_week_time_exit | 190 | 2.04 | – | 0.11% | 32% | 23.6 h |
| stop_loss | 20 | -6.53 | – | -3.34% | 0% | 6.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 31 | -5.98 | -1.98% | 0% |
| 3 h a 1 dia | 94 | -14.33 | -1.55% | 6% |
| 1 a 7 dias | 85 | 15.83 | 1.89% | 64% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (60): MFE mediano 4.9%, MAE mediano -0.7%, devolução média do melhor ponto 2.1%, captura mediana 0.54.
- Perdedores (150): MAE mediano -2.2%, MFE mediano 0.7%; 27 (18%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 7.19; 266% do lucro antes de custos.
- Trades < 3 h: 31 (lucro -5.98); reentradas em < 24 h: 32 (lucro -1.88).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -5.94.
- Lucro por ano de fechamento: 2017: -1.2, 2018: -1.1, 2019: 1.5, 2020: 1.7, 2021: 0.8, 2022: -2.8, 2023: -1.4, 2024: -2.0.

## ETH/USDT

Trades: 236; lucro líquido: 4.13.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| vwap_week_time_exit | 208 | 13.42 | 325% | 0.65% | 35% | 21.9 h |
| stop_loss | 28 | -9.29 | -225% | -3.34% | 0% | 9.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 40 | -7.65 | -1.91% | 5% |
| 3 h a 1 dia | 110 | -16.25 | -1.47% | 10% |
| 1 a 7 dias | 86 | 28.04 | 3.27% | 69% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (72): MFE mediano 6.3%, MAE mediano -0.8%, devolução média do melhor ponto 2.8%, captura mediana 0.58.
- Perdedores (164): MAE mediano -2.2%, MFE mediano 1.0%; 38 (23%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 8.27; 67% do lucro antes de custos.
- Trades < 3 h: 40 (lucro -7.65); reentradas em < 24 h: 48 (lucro 4.26).
- Maior trade = 41% do lucro; top 5 = 177%; top 10 = 315%; lucro sem o melhor = 2.44.
- Lucro por ano de fechamento: 2017: -2.6, 2018: -0.9, 2019: -2.1, 2020: 7.3, 2021: 3.7, 2022: -0.8, 2023: -0.0, 2024: -0.4.

## BNB/USDT

Trades: 252; lucro líquido: -7.85.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| vwap_week_time_exit | 210 | 5.49 | – | 0.28% | 29% | 20.4 h |
| stop_loss | 42 | -13.34 | – | -3.33% | 0% | 9.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 54 | -11.66 | -2.27% | 2% |
| 3 h a 1 dia | 115 | -18.57 | -1.70% | 6% |
| 1 a 7 dias | 83 | 22.38 | 2.87% | 64% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (61): MFE mediano 7.1%, MAE mediano -0.8%, devolução média do melhor ponto 3.2%, captura mediana 0.63.
- Perdedores (191): MAE mediano -2.4%, MFE mediano 0.9%; 49 (26%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 8.31; 1795% do lucro antes de custos.
- Trades < 3 h: 54 (lucro -11.66); reentradas em < 24 h: 47 (lucro -1.92).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -9.36.
- Lucro por ano de fechamento: 2017: -2.8, 2018: -3.1, 2019: 1.1, 2020: 2.0, 2021: -0.9, 2022: -2.1, 2023: -2.5, 2024: 0.5.
