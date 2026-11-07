# Revisão de trades: H-064 (exploração)

Fonte dos trades: `research/experiments/20261107T150054Z-h-064-exploration-btc-usdt/raw/backtest-result-2026-11-07_15-09-17.zip`; `research/experiments/20261107T150054Z-h-064-exploration-eth-usdt/raw/backtest-result-2026-11-07_15-11-12.zip`; `research/experiments/20261107T150054Z-h-064-exploration-bnb-usdt/raw/backtest-result-2026-11-07_15-13-08.zip`; `research/experiments/20261107T150054Z-h-064-exploration-xrp-usdt/raw/backtest-result-2026-11-07_15-15-08.zip`; `research/experiments/20261107T150054Z-h-064-exploration-ada-usdt/raw/backtest-result-2026-11-07_15-17-02.zip`; `research/experiments/20261107T150054Z-h-064-exploration-ltc-usdt/raw/backtest-result-2026-11-07_15-18-58.zip`; `research/experiments/20261107T150054Z-h-064-exploration-link-usdt/raw/backtest-result-2026-11-07_15-20-55.zip`; `research/experiments/20261107T150054Z-h-064-exploration-doge-usdt/raw/backtest-result-2026-11-07_15-22-46.zip`; `research/experiments/20261107T150054Z-h-064-exploration-sol-usdt/raw/backtest-result-2026-11-07_15-24-33.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 603; lucro líquido: -14.93.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| same_slot_time_exit | 558 | -1.43 | – | -0.03% | 42% | 4.0 h |
| stop_loss | 45 | -13.50 | – | -3.29% | 0% | 1.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 34 | -10.24 | -3.29% | 0% |
| 3 h a 1 dia | 569 | -4.70 | -0.09% | 41% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (233): MFE mediano 1.7%, MAE mediano -0.4%, devolução média do melhor ponto 1.2%, captura mediana 0.38.
- Perdedores (370): MAE mediano -1.3%, MFE mediano 0.5%; 13 (4%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 16.37; 1140% do lucro antes de custos.
- Trades < 3 h: 34 (lucro -10.24); reentradas em < 24 h: 84 (lucro -1.94).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -15.70.
- Lucro por ano de fechamento: 2018: -2.9, 2019: -1.8, 2020: -2.3, 2021: -3.8, 2022: -2.2, 2023: -0.9, 2024: -1.0.

## ETH/USDT

Trades: 866; lucro líquido: -21.42.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| same_slot_time_exit | 757 | 9.92 | – | 0.16% | 47% | 4.0 h |
| stop_loss | 109 | -31.35 | – | -3.29% | 0% | 1.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 85 | -24.50 | -3.29% | 0% |
| 3 h a 1 dia | 781 | 3.07 | 0.05% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (357): MFE mediano 2.2%, MAE mediano -0.5%, devolução média do melhor ponto 1.4%, captura mediana 0.43.
- Perdedores (509): MAE mediano -1.6%, MFE mediano 0.6%; 26 (5%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 22.34; 2431% do lucro antes de custos.
- Trades < 3 h: 85 (lucro -24.50); reentradas em < 24 h: 226 (lucro -5.48).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -22.13.
- Lucro por ano de fechamento: 2018: -5.4, 2019: -4.8, 2020: -5.2, 2021: -0.2, 2022: -2.9, 2023: -1.5, 2024: -1.5.

## BNB/USDT

Trades: 856; lucro líquido: -11.59.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| same_slot_time_exit | 746 | 21.94 | – | 0.32% | 52% | 4.0 h |
| stop_loss | 110 | -33.53 | – | -3.29% | 0% | 1.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 82 | -25.05 | -3.29% | 0% |
| 3 h a 1 dia | 773 | 12.55 | 0.18% | 50% |
| 1 a 7 dias | 1 | 0.91 | 9.83% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (385): MFE mediano 2.0%, MAE mediano -0.5%, devolução média do melhor ponto 1.3%, captura mediana 0.41.
- Perdedores (471): MAE mediano -1.7%, MFE mediano 0.6%; 24 (5%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 23.67; 196% do lucro antes de custos.
- Trades < 3 h: 82 (lucro -25.05); reentradas em < 24 h: 243 (lucro -1.76).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -12.95.
- Lucro por ano de fechamento: 2018: -2.9, 2019: -2.9, 2020: -3.9, 2021: 1.9, 2022: -1.6, 2023: -1.5, 2024: -0.6.

## XRP/USDT

Trades: 780; lucro líquido: -15.45.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| same_slot_time_exit | 689 | 11.24 | – | 0.19% | 51% | 4.0 h |
| stop_loss | 91 | -26.69 | – | -3.28% | 0% | 1.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 65 | -19.02 | -3.28% | 0% |
| 3 h a 1 dia | 715 | 3.57 | 0.07% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (350): MFE mediano 1.8%, MAE mediano -0.4%, devolução média do melhor ponto 1.3%, captura mediana 0.42.
- Perdedores (430): MAE mediano -1.7%, MFE mediano 0.6%; 34 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 20.73; 392% do lucro antes de custos.
- Trades < 3 h: 65 (lucro -19.02); reentradas em < 24 h: 190 (lucro -2.67).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -16.50.
- Lucro por ano de fechamento: 2018: -0.6, 2019: -2.3, 2020: -6.5, 2021: -4.7, 2022: -0.5, 2023: -0.3, 2024: -0.5.

## ADA/USDT

Trades: 828; lucro líquido: -20.26.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| same_slot_time_exit | 711 | 14.26 | – | 0.22% | 48% | 4.0 h |
| stop_loss | 117 | -34.52 | – | -3.28% | 0% | 1.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 90 | -26.64 | -3.28% | 0% |
| 3 h a 1 dia | 738 | 6.39 | 0.10% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (343): MFE mediano 2.3%, MAE mediano -0.6%, devolução média do melhor ponto 1.6%, captura mediana 0.40.
- Perdedores (485): MAE mediano -1.9%, MFE mediano 0.7%; 35 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 22.02; 1250% do lucro antes de custos.
- Trades < 3 h: 90 (lucro -26.64); reentradas em < 24 h: 213 (lucro -2.93).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -21.31.
- Lucro por ano de fechamento: 2018: -0.5, 2019: -3.4, 2020: -5.5, 2021: -4.1, 2022: -2.5, 2023: -2.7, 2024: -1.6.

## LTC/USDT

Trades: 767; lucro líquido: -15.14.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| same_slot_time_exit | 667 | 15.47 | – | 0.25% | 50% | 4.0 h |
| stop_loss | 100 | -30.62 | – | -3.28% | 0% | 1.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 76 | -23.21 | -3.28% | 0% |
| 3 h a 1 dia | 691 | 8.07 | 0.12% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (336): MFE mediano 2.3%, MAE mediano -0.5%, devolução média do melhor ponto 1.5%, captura mediana 0.43.
- Perdedores (431): MAE mediano -1.8%, MFE mediano 0.6%; 34 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 21.30; 346% do lucro antes de custos.
- Trades < 3 h: 76 (lucro -23.21); reentradas em < 24 h: 143 (lucro -2.63).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -16.00.
- Lucro por ano de fechamento: 2018: -0.8, 2019: -0.3, 2020: -3.7, 2021: -4.6, 2022: -1.7, 2023: -2.1, 2024: -1.8.

## LINK/USDT

Trades: 821; lucro líquido: -20.01.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| same_slot_time_exit | 685 | 20.65 | – | 0.33% | 51% | 4.0 h |
| stop_loss | 136 | -40.66 | – | -3.28% | 0% | 1.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 111 | -33.27 | -3.28% | 0% |
| 3 h a 1 dia | 710 | 13.26 | 0.20% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (346): MFE mediano 2.5%, MAE mediano -0.6%, devolução média do melhor ponto 1.5%, captura mediana 0.44.
- Perdedores (475): MAE mediano -2.2%, MFE mediano 0.7%; 48 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 22.06; 1080% do lucro antes de custos.
- Trades < 3 h: 111 (lucro -33.27); reentradas em < 24 h: 229 (lucro -4.10).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -20.90.
- Lucro por ano de fechamento: 2019: -2.4, 2020: -4.3, 2021: -2.8, 2022: -4.0, 2023: -3.1, 2024: -3.3.

## DOGE/USDT

Trades: 612; lucro líquido: -15.02.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| same_slot_time_exit | 527 | 10.48 | – | 0.22% | 46% | 4.1 h |
| stop_loss | 85 | -25.50 | – | -3.28% | 0% | 1.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 70 | -21.04 | -3.28% | 0% |
| 3 h a 1 dia | 541 | 5.83 | 0.12% | 44% |
| 1 a 7 dias | 1 | 0.18 | 2.00% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (240): MFE mediano 2.1%, MAE mediano -0.5%, devolução média do melhor ponto 1.8%, captura mediana 0.41.
- Perdedores (372): MAE mediano -1.7%, MFE mediano 0.7%; 30 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 16.79; 950% do lucro antes de custos.
- Trades < 3 h: 70 (lucro -21.04); reentradas em < 24 h: 150 (lucro -6.72).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -16.28.
- Lucro por ano de fechamento: 2020: -4.3, 2021: -4.4, 2022: -0.8, 2023: -2.5, 2024: -3.1.

## SOL/USDT

Trades: 540; lucro líquido: -11.15.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| same_slot_time_exit | 438 | 20.45 | – | 0.50% | 55% | 4.0 h |
| stop_loss | 102 | -31.61 | – | -3.28% | 0% | 1.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 79 | -24.54 | -3.28% | 0% |
| 3 h a 1 dia | 461 | 13.38 | 0.31% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (243): MFE mediano 2.8%, MAE mediano -0.6%, devolução média do melhor ponto 1.7%, captura mediana 0.42.
- Perdedores (297): MAE mediano -2.4%, MFE mediano 0.8%; 38 (13%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 15.03; 388% do lucro antes de custos.
- Trades < 3 h: 79 (lucro -24.54); reentradas em < 24 h: 138 (lucro -3.55).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -12.48.
- Lucro por ano de fechamento: 2021: -6.8, 2022: -0.5, 2023: -0.7, 2024: -3.1.
