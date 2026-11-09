# Revisão de trades: H-060 (exploração)

Fonte dos trades: `research/experiments/20261109T185004Z-h-060-exploration-btc-usdt/raw/backtest-result-2026-11-09_18-59-51.zip`; `research/experiments/20261109T185004Z-h-060-exploration-eth-usdt/raw/backtest-result-2026-11-09_19-02-04.zip`; `research/experiments/20261109T185004Z-h-060-exploration-bnb-usdt/raw/backtest-result-2026-11-09_19-04-20.zip`; `research/experiments/20261109T185004Z-h-060-exploration-xrp-usdt/raw/backtest-result-2026-11-09_19-06-33.zip`; `research/experiments/20261109T185004Z-h-060-exploration-ada-usdt/raw/backtest-result-2026-11-09_19-08-49.zip`; `research/experiments/20261109T185004Z-h-060-exploration-ltc-usdt/raw/backtest-result-2026-11-09_19-11-04.zip`; `research/experiments/20261109T185004Z-h-060-exploration-link-usdt/raw/backtest-result-2026-11-09_19-13-15.zip`; `research/experiments/20261109T185004Z-h-060-exploration-doge-usdt/raw/backtest-result-2026-11-09_19-15-23.zip`; `research/experiments/20261109T185004Z-h-060-exploration-sol-usdt/raw/backtest-result-2026-11-09_19-17-32.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 644; lucro líquido: -86.01.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| same_slot_block_end | 567 | 36.91 | – | 0.13% | 45% | 4.0 h |
| stop_loss | 77 | -122.91 | – | -3.29% | 0% | 1.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 60 | -96.04 | -3.29% | 0% |
| 3 h a 1 dia | 583 | 8.40 | 0.02% | 43% |
| 1 a 7 dias | 1 | 1.64 | 3.34% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (254): MFE mediano 2.0%, MAE mediano -0.5%, devolução média do melhor ponto 1.3%, captura mediana 0.41.
- Perdedores (390): MAE mediano -1.6%, MFE mediano 0.5%; 25 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 91.91; 1556% do lucro antes de custos.
- Trades < 3 h: 60 (lucro -96.04); reentradas em < 24 h: 506 (lucro -75.56).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -92.01.
- Lucro por ano de fechamento: 2017: -1.4, 2018: -18.9, 2019: -17.3, 2020: -10.4, 2021: -21.4, 2022: -7.0, 2023: -4.6, 2024: -5.0.

## ETH/USDT

Trades: 813; lucro líquido: -126.05.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| same_slot_block_end | 679 | 82.19 | – | 0.25% | 48% | 4.1 h |
| stop_loss | 134 | -208.23 | – | -3.29% | 0% | 1.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 104 | -161.62 | -3.29% | 0% |
| 3 h a 1 dia | 707 | 23.96 | 0.07% | 46% |
| 1 a 7 dias | 2 | 11.61 | 12.08% | 50% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (323): MFE mediano 2.4%, MAE mediano -0.5%, devolução média do melhor ponto 1.6%, captura mediana 0.42.
- Perdedores (490): MAE mediano -2.0%, MFE mediano 0.7%; 40 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 113.98; – do lucro antes de custos.
- Trades < 3 h: 104 (lucro -161.62); reentradas em < 24 h: 623 (lucro -92.20).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -137.70.
- Lucro por ano de fechamento: 2017: -4.9, 2018: -37.4, 2019: -7.2, 2020: -21.1, 2021: -13.2, 2022: -17.8, 2023: -11.6, 2024: -12.9.

## BNB/USDT

Trades: 970; lucro líquido: -85.97.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| same_slot_block_end | 816 | 162.50 | – | 0.40% | 52% | 4.0 h |
| stop_loss | 154 | -248.47 | – | -3.29% | 0% | 1.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 118 | -190.90 | -3.29% | 0% |
| 3 h a 1 dia | 851 | 99.91 | 0.23% | 49% |
| 1 a 7 dias | 1 | 5.01 | 10.50% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (421): MFE mediano 2.2%, MAE mediano -0.6%, devolução média do melhor ponto 1.6%, captura mediana 0.42.
- Perdedores (549): MAE mediano -2.1%, MFE mediano 0.6%; 45 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 141.55; 255% do lucro antes de custos.
- Trades < 3 h: 118 (lucro -190.90); reentradas em < 24 h: 777 (lucro -50.18).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -95.10.
- Lucro por ano de fechamento: 2017: 14.3, 2018: -11.3, 2019: -22.0, 2020: -24.9, 2021: -7.0, 2022: -17.1, 2023: -9.2, 2024: -8.8.

## XRP/USDT

Trades: 928; lucro líquido: -65.25.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| same_slot_block_end | 798 | 137.59 | – | 0.37% | 50% | 4.0 h |
| stop_loss | 130 | -202.84 | – | -3.29% | 0% | 1.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 102 | -159.38 | -3.29% | 0% |
| 3 h a 1 dia | 826 | 94.12 | 0.24% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (397): MFE mediano 2.1%, MAE mediano -0.5%, devolução média do melhor ponto 1.7%, captura mediana 0.42.
- Perdedores (531): MAE mediano -1.8%, MFE mediano 0.7%; 52 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 131.15; 199% do lucro antes de custos.
- Trades < 3 h: 102 (lucro -159.38); reentradas em < 24 h: 778 (lucro -46.98).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -83.29.
- Lucro por ano de fechamento: 2018: -22.3, 2019: -13.2, 2020: -17.1, 2021: -12.2, 2022: -10.9, 2023: 20.9, 2024: -10.5.

## ADA/USDT

Trades: 984; lucro líquido: -97.38.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| same_slot_block_end | 827 | 148.44 | – | 0.38% | 51% | 4.0 h |
| stop_loss | 157 | -245.83 | – | -3.28% | 0% | 1.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 126 | -197.32 | -3.28% | 0% |
| 3 h a 1 dia | 858 | 99.93 | 0.25% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (418): MFE mediano 2.5%, MAE mediano -0.5%, devolução média do melhor ponto 1.7%, captura mediana 0.44.
- Perdedores (566): MAE mediano -2.0%, MFE mediano 0.7%; 47 (8%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 139.91; 329% do lucro antes de custos.
- Trades < 3 h: 126 (lucro -197.32); reentradas em < 24 h: 795 (lucro -88.48).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -102.16.
- Lucro por ano de fechamento: 2018: -22.5, 2019: -7.7, 2020: -10.5, 2021: -23.1, 2022: -25.2, 2023: -9.8, 2024: 1.5.

## LTC/USDT

Trades: 820; lucro líquido: -146.34.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| same_slot_block_end | 666 | 86.71 | – | 0.29% | 50% | 4.0 h |
| stop_loss | 154 | -233.05 | – | -3.28% | 0% | 1.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 122 | -184.92 | -3.28% | 0% |
| 3 h a 1 dia | 697 | 38.43 | 0.12% | 48% |
| 1 a 7 dias | 1 | 0.15 | 0.30% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (335): MFE mediano 2.5%, MAE mediano -0.6%, devolução média do melhor ponto 1.7%, captura mediana 0.44.
- Perdedores (485): MAE mediano -2.4%, MFE mediano 0.6%; 29 (6%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 111.76; – do lucro antes de custos.
- Trades < 3 h: 122 (lucro -184.92); reentradas em < 24 h: 648 (lucro -110.48).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -150.40.
- Lucro por ano de fechamento: 2018: -20.7, 2019: -22.0, 2020: -30.2, 2021: -41.4, 2022: -18.7, 2023: -8.9, 2024: -4.4.

## LINK/USDT

Trades: 1021; lucro líquido: -136.64.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| same_slot_block_end | 839 | 143.28 | – | 0.36% | 51% | 4.0 h |
| stop_loss | 182 | -279.92 | – | -3.28% | 0% | 1.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 143 | -220.54 | -3.28% | 0% |
| 3 h a 1 dia | 877 | 82.18 | 0.20% | 49% |
| 1 a 7 dias | 1 | 1.73 | 3.50% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (431): MFE mediano 2.7%, MAE mediano -0.7%, devolução média do melhor ponto 1.8%, captura mediana 0.46.
- Perdedores (590): MAE mediano -2.4%, MFE mediano 0.7%; 61 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 141.20; 3093% do lucro antes de custos.
- Trades < 3 h: 143 (lucro -220.54); reentradas em < 24 h: 826 (lucro -122.78).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -143.11.
- Lucro por ano de fechamento: 2019: -27.2, 2020: -20.9, 2021: -34.5, 2022: -34.3, 2023: -9.6, 2024: -10.1.

## DOGE/USDT

Trades: 596; lucro líquido: -91.08.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| same_slot_block_end | 487 | 79.52 | – | 0.35% | 49% | 4.0 h |
| stop_loss | 109 | -170.60 | – | -3.28% | 0% | 1.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 90 | -141.16 | -3.29% | 0% |
| 3 h a 1 dia | 506 | 50.08 | 0.21% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (238): MFE mediano 2.3%, MAE mediano -0.5%, devolução média do melhor ponto 1.9%, captura mediana 0.37.
- Perdedores (358): MAE mediano -2.0%, MFE mediano 0.7%; 49 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 84.35; – do lucro antes de custos.
- Trades < 3 h: 90 (lucro -141.16); reentradas em < 24 h: 454 (lucro -62.41).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -102.41.
- Lucro por ano de fechamento: 2019: -5.7, 2020: -9.4, 2021: -32.7, 2022: -29.4, 2023: -17.7, 2024: 3.9.

## SOL/USDT

Trades: 763; lucro líquido: -72.76.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| same_slot_block_end | 592 | 205.03 | – | 0.70% | 55% | 4.0 h |
| stop_loss | 171 | -277.79 | – | -3.28% | 0% | 1.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 133 | -216.24 | -3.28% | 0% |
| 3 h a 1 dia | 630 | 143.48 | 0.46% | 52% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (327): MFE mediano 2.9%, MAE mediano -0.7%, devolução média do melhor ponto 1.9%, captura mediana 0.45.
- Perdedores (436): MAE mediano -2.9%, MFE mediano 0.8%; 59 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 111.77; 287% do lucro antes de custos.
- Trades < 3 h: 133 (lucro -216.24); reentradas em < 24 h: 599 (lucro -49.79).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -87.38.
- Lucro por ano de fechamento: 2020: -11.9, 2021: 17.5, 2022: -44.4, 2023: -22.1, 2024: -11.8.
