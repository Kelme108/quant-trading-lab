# Revisão de trades: H-050 (exploração)

Fonte dos trades: `research/experiments/20261106T185212Z-h-050-exploration-btc-usdt/raw/backtest-result-2026-11-06_18-57-48.zip`; `research/experiments/20261106T185212Z-h-050-exploration-eth-usdt/raw/backtest-result-2026-11-06_19-03-55.zip`; `research/experiments/20261106T185212Z-h-050-exploration-bnb-usdt/raw/backtest-result-2026-11-06_19-10-16.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 191; lucro líquido: -10.74.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_48_bars | 93 | 3.61 | – | 0.41% | 54% | 12.1 h |
| stop_loss | 78 | -24.37 | – | -3.29% | 0% | 3.9 h |
| retrace_to_pre_drop_close | 20 | 10.03 | – | 5.17% | 100% | 4.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 47 | -8.94 | -2.01% | 15% |
| 3 h a 1 dia | 144 | -1.80 | -0.14% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (70): MFE mediano 3.3%, MAE mediano -0.8%, devolução média do melhor ponto 1.5%, captura mediana 0.58.
- Perdedores (121): MAE mediano -3.2%, MFE mediano 0.9%; 28 (23%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 5.39; – do lucro antes de custos.
- Trades < 3 h: 47 (lucro -8.94); reentradas em < 24 h: 46 (lucro 1.71).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -11.66.
- Lucro por ano de fechamento: 2017: -0.1, 2018: 0.1, 2019: -2.4, 2020: -1.6, 2021: -4.0, 2022: -1.2, 2023: -0.3, 2024: -1.2.

## ETH/USDT

Trades: 297; lucro líquido: -9.93.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 131 | -41.83 | – | -3.29% | 0% | 3.0 h |
| time_exit_48_bars | 117 | 8.30 | – | 0.74% | 66% | 12.0 h |
| retrace_to_pre_drop_close | 49 | 23.60 | – | 4.91% | 100% | 5.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 90 | -20.18 | -2.30% | 12% |
| 3 h a 1 dia | 207 | 10.25 | 0.50% | 56% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (126): MFE mediano 3.9%, MAE mediano -0.9%, devolução média do melhor ponto 1.3%, captura mediana 0.69.
- Perdedores (171): MAE mediano -3.4%, MFE mediano 1.3%; 43 (25%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 8.55; – do lucro antes de custos.
- Trades < 3 h: 90 (lucro -20.18); reentradas em < 24 h: 97 (lucro 0.03).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -11.22.
- Lucro por ano de fechamento: 2017: 0.8, 2018: -1.4, 2019: 0.1, 2020: -2.2, 2021: -1.9, 2022: -2.2, 2023: -0.2, 2024: -2.9.

## BNB/USDT

Trades: 212; lucro líquido: -11.55.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 94 | -28.82 | – | -3.29% | 0% | 3.4 h |
| time_exit_48_bars | 87 | 3.65 | – | 0.43% | 59% | 12.0 h |
| retrace_to_pre_drop_close | 31 | 13.62 | – | 4.76% | 100% | 6.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 57 | -13.08 | -2.45% | 11% |
| 3 h a 1 dia | 155 | 1.53 | 0.10% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (82): MFE mediano 4.2%, MAE mediano -0.9%, devolução média do melhor ponto 1.6%, captura mediana 0.60.
- Perdedores (130): MAE mediano -3.3%, MFE mediano 1.2%; 39 (30%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 5.86; – do lucro antes de custos.
- Trades < 3 h: 57 (lucro -13.08); reentradas em < 24 h: 53 (lucro -4.77).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -12.85.
- Lucro por ano de fechamento: 2018: -1.7, 2019: -0.1, 2020: -2.0, 2021: -8.3, 2022: -1.2, 2023: 1.2, 2024: 0.6.
