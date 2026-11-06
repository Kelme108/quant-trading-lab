# Revisão de trades: H-030 (exploração)

Fonte dos trades: `research/experiments/20261106T001313Z-h-030-exploration-btc-usdt/raw/backtest-result-2026-11-06_00-15-12.zip`; `research/experiments/20261106T001313Z-h-030-exploration-eth-usdt/raw/backtest-result-2026-11-06_00-17-20.zip`; `research/experiments/20261106T001313Z-h-030-exploration-bnb-usdt/raw/backtest-result-2026-11-06_00-19-11.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 153; lucro líquido: -8.06.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_16 | 109 | 5.92 | – | 0.57% | 51% | 8.0 h |
| stop_loss | 44 | -13.99 | – | -3.34% | 0% | 2.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 27 | -8.59 | -3.34% | 0% |
| 3 h a 1 dia | 126 | 0.52 | 0.04% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (56): MFE mediano 3.1%, MAE mediano -0.8%, devolução média do melhor ponto 1.8%, captura mediana 0.48.
- Perdedores (97): MAE mediano -3.0%, MFE mediano 0.8%; 10 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 5.03; – do lucro antes de custos.
- Trades < 3 h: 27 (lucro -8.59); reentradas em < 24 h: 21 (lucro -1.90).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -9.44.
- Lucro por ano de fechamento: 2017: -1.3, 2018: -1.6, 2019: -1.0, 2020: -0.8, 2021: -0.7, 2023: -1.3, 2024: -1.3.

## ETH/USDT

Trades: 235; lucro líquido: -8.23.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_16 | 148 | 20.08 | – | 1.39% | 64% | 8.0 h |
| stop_loss | 87 | -28.31 | – | -3.34% | 0% | 3.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 46 | -14.97 | -3.34% | 0% |
| 3 h a 1 dia | 189 | 6.74 | 0.36% | 50% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (95): MFE mediano 3.4%, MAE mediano -0.8%, devolução média do melhor ponto 1.8%, captura mediana 0.51.
- Perdedores (140): MAE mediano -3.4%, MFE mediano 0.8%; 21 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 7.97; – do lucro antes de custos.
- Trades < 3 h: 46 (lucro -14.97); reentradas em < 24 h: 38 (lucro -3.84).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -10.93.
- Lucro por ano de fechamento: 2017: -0.4, 2018: 1.8, 2019: -0.8, 2020: -3.5, 2021: -1.5, 2022: -0.4, 2023: -0.9, 2024: -2.6.

## BNB/USDT

Trades: 260; lucro líquido: -11.35.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_16 | 171 | 16.34 | – | 1.03% | 61% | 8.0 h |
| stop_loss | 89 | -27.69 | – | -3.34% | 0% | 3.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 40 | -12.35 | -3.34% | 0% |
| 3 h a 1 dia | 220 | 1.00 | 0.06% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (104): MFE mediano 3.2%, MAE mediano -0.8%, devolução média do melhor ponto 1.9%, captura mediana 0.52.
- Perdedores (156): MAE mediano -3.3%, MFE mediano 1.1%; 32 (21%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 8.42; – do lucro antes de custos.
- Trades < 3 h: 40 (lucro -12.35); reentradas em < 24 h: 42 (lucro 0.43).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -12.63.
- Lucro por ano de fechamento: 2018: -2.4, 2019: -2.3, 2020: -1.8, 2021: -2.8, 2022: -0.7, 2023: 0.0, 2024: -1.4.
