# Revisão de trades: H-053 (exploração)

Fonte dos trades: `research/experiments/20261106T210107Z-h-053-exploration-btc-usdt/raw/backtest-result-2026-11-06_21-04-31.zip`; `research/experiments/20261106T210107Z-h-053-exploration-eth-usdt/raw/backtest-result-2026-11-06_21-08-10.zip`; `research/experiments/20261106T210107Z-h-053-exploration-bnb-usdt/raw/backtest-result-2026-11-06_21-11-58.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 243; lucro líquido: -9.17.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12_bars | 189 | -10.06 | – | -0.58% | 38% | 12.0 h |
| retrace_to_pre_drop_close | 35 | 10.22 | – | 3.23% | 100% | 6.8 h |
| stop_loss | 19 | -9.33 | – | -5.28% | 0% | 5.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 7 | -0.96 | -1.58% | 43% |
| 3 h a 1 dia | 236 | -8.21 | -0.36% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (107): MFE mediano 2.5%, MAE mediano -0.7%, devolução média do melhor ponto 1.3%, captura mediana 0.54.
- Perdedores (136): MAE mediano -2.6%, MFE mediano 0.8%; 20 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 6.70; – do lucro antes de custos.
- Trades < 3 h: 7 (lucro -0.96); reentradas em < 24 h: 27 (lucro -1.82).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -9.66.
- Lucro por ano de fechamento: 2017: -0.0, 2018: -3.8, 2019: -1.5, 2020: -0.4, 2021: -2.7, 2022: 0.6, 2023: -1.2, 2024: -0.2.

## ETH/USDT

Trades: 287; lucro líquido: -14.71.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12_bars | 194 | -1.35 | – | -0.08% | 47% | 12.0 h |
| stop_loss | 55 | -26.31 | – | -5.28% | 0% | 5.8 h |
| retrace_to_pre_drop_close | 38 | 12.94 | – | 3.90% | 100% | 7.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 11 | -4.36 | -4.41% | 9% |
| 3 h a 1 dia | 276 | -10.35 | -0.40% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (130): MFE mediano 3.4%, MAE mediano -0.7%, devolução média do melhor ponto 1.6%, captura mediana 0.54.
- Perdedores (157): MAE mediano -3.7%, MFE mediano 0.9%; 24 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 7.57; – do lucro antes de custos.
- Trades < 3 h: 11 (lucro -4.36); reentradas em < 24 h: 49 (lucro -1.06).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -15.40.
- Lucro por ano de fechamento: 2017: -0.4, 2018: -7.6, 2019: -2.1, 2020: -1.8, 2021: -0.5, 2022: -0.6, 2023: -0.6, 2024: -1.2.

## BNB/USDT

Trades: 401; lucro líquido: -13.09.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_12_bars | 292 | -0.60 | – | -0.02% | 50% | 12.0 h |
| stop_loss | 61 | -29.01 | – | -5.28% | 0% | 5.5 h |
| retrace_to_pre_drop_close | 47 | 16.70 | – | 4.07% | 100% | 7.7 h |
| force_exit | 1 | -0.19 | – | -2.21% | 0% | 7.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 18 | -7.74 | -4.78% | 6% |
| 3 h a 1 dia | 383 | -5.35 | -0.14% | 50% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (194): MFE mediano 3.0%, MAE mediano -0.8%, devolução média do melhor ponto 1.4%, captura mediana 0.58.
- Perdedores (207): MAE mediano -3.7%, MFE mediano 0.9%; 35 (17%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 10.52; – do lucro antes de custos.
- Trades < 3 h: 18 (lucro -7.74); reentradas em < 24 h: 118 (lucro -3.86).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -14.04.
- Lucro por ano de fechamento: 2018: -9.6, 2019: -5.0, 2020: -0.9, 2021: 4.6, 2022: -1.6, 2023: -0.7, 2024: 0.1.
