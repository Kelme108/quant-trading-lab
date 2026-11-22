# Revisão de trades: H-121 (exploração)

Fonte dos trades: `research/experiments/20261112T131504Z-h-121-exploration-btc-usdt/raw/backtest-result-2026-11-12_13-29-44.zip`; `research/experiments/20261112T131504Z-h-121-exploration-eth-usdt/raw/backtest-result-2026-11-12_13-36-44.zip`; `research/experiments/20261112T131504Z-h-121-exploration-bnb-usdt/raw/backtest-result-2026-11-12_13-42-17.zip`; `research/experiments/20261112T131504Z-h-121-exploration-xrp-usdt/raw/backtest-result-2026-11-12_13-46-55.zip`; `research/experiments/20261112T131504Z-h-121-exploration-ada-usdt/raw/backtest-result-2026-11-12_13-51-45.zip`; `research/experiments/20261112T131504Z-h-121-exploration-ltc-usdt/raw/backtest-result-2026-11-12_13-56-30.zip`; `research/experiments/20261112T131504Z-h-121-exploration-link-usdt/raw/backtest-result-2026-11-12_14-01-08.zip`; `research/experiments/20261112T131504Z-h-121-exploration-doge-usdt/raw/backtest-result-2026-11-12_14-05-41.zip`; `research/experiments/20261112T131504Z-h-121-exploration-sol-usdt/raw/backtest-result-2026-11-12_14-09-57.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 118; lucro líquido: -122.29.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 78 | -284.27 | – | -1.30% | 0% | 1.4 h |
| take_profit_2pct | 19 | 139.45 | – | 2.62% | 100% | 3.0 h |
| time_exit_8h | 15 | 14.52 | – | 0.36% | 67% | 8.0 h |
| time_exit_utc_day_close | 6 | 8.01 | – | 0.48% | 83% | 6.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 72 | -161.17 | -0.79% | 12% |
| 3 h a 1 dia | 46 | 38.88 | 0.30% | 54% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (34): MFE mediano 3.3%, MAE mediano -0.4%, devolução média do melhor ponto 1.2%, captura mediana 0.60.
- Perdedores (84): MAE mediano -1.4%, MFE mediano 0.7%; 8 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 98.80; – do lucro antes de custos.
- Trades < 3 h: 72 (lucro -161.17); reentradas em < 24 h: 20 (lucro -42.22).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -133.64.
- Lucro por ano de fechamento: 2017: -19.2, 2018: -19.6, 2019: -6.8, 2020: -24.3, 2021: -32.5, 2022: -10.3, 2023: 7.5, 2024: -17.2.

## ETH/USDT

Trades: 152; lucro líquido: -108.75.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 99 | -366.42 | – | -1.30% | 0% | 1.5 h |
| take_profit_2pct | 35 | 247.60 | – | 2.49% | 100% | 2.3 h |
| time_exit_8h | 12 | 11.12 | – | 0.32% | 50% | 8.0 h |
| time_exit_utc_day_close | 6 | -1.06 | – | -0.07% | 50% | 5.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 105 | -128.04 | -0.43% | 23% |
| 3 h a 1 dia | 47 | 19.29 | 0.15% | 43% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (44): MFE mediano 3.2%, MAE mediano -0.5%, devolução média do melhor ponto 1.2%, captura mediana 0.70.
- Perdedores (108): MAE mediano -1.3%, MFE mediano 0.7%; 13 (12%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 129.31; 629% do lucro antes de custos.
- Trades < 3 h: 105 (lucro -128.04); reentradas em < 24 h: 33 (lucro -46.26).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -119.20.
- Lucro por ano de fechamento: 2017: 9.0, 2018: -19.0, 2019: -20.0, 2020: -40.1, 2021: -33.3, 2022: 8.6, 2023: 12.3, 2024: -26.2.

## BNB/USDT

Trades: 157; lucro líquido: -69.51.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 104 | -401.34 | – | -1.29% | 0% | 0.9 h |
| take_profit_2pct | 35 | 326.19 | – | 3.12% | 100% | 2.1 h |
| time_exit_8h | 14 | 1.86 | – | 0.05% | 43% | 8.0 h |
| time_exit_utc_day_close | 4 | 3.78 | – | 0.31% | 50% | 6.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 119 | -96.62 | -0.27% | 22% |
| 3 h a 1 dia | 38 | 27.11 | 0.23% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (43): MFE mediano 3.5%, MAE mediano -0.4%, devolução média do melhor ponto 1.9%, captura mediana 0.65.
- Perdedores (114): MAE mediano -1.3%, MFE mediano 0.6%; 15 (13%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 140.26; 198% do lucro antes de custos.
- Trades < 3 h: 119 (lucro -96.62); reentradas em < 24 h: 35 (lucro -52.28).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -96.10.
- Lucro por ano de fechamento: 2017: -21.2, 2018: 46.6, 2019: -4.7, 2020: -34.0, 2021: 5.7, 2022: -7.1, 2023: -38.8, 2024: -16.1.

## XRP/USDT

Trades: 145; lucro líquido: -82.33.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 102 | -396.22 | – | -1.29% | 0% | 1.1 h |
| take_profit_2pct | 35 | 305.82 | – | 2.89% | 100% | 2.4 h |
| time_exit_8h | 7 | 9.30 | – | 0.45% | 71% | 8.0 h |
| time_exit_utc_day_close | 1 | -1.22 | – | -0.39% | 0% | 5.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 110 | -110.47 | -0.33% | 22% |
| 3 h a 1 dia | 35 | 28.14 | 0.25% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (40): MFE mediano 3.7%, MAE mediano -0.4%, devolução média do melhor ponto 1.6%, captura mediana 0.63.
- Perdedores (105): MAE mediano -1.3%, MFE mediano 0.7%; 10 (10%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 130.78; 270% do lucro antes de custos.
- Trades < 3 h: 110 (lucro -110.47); reentradas em < 24 h: 44 (lucro 38.76).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -105.89.
- Lucro por ano de fechamento: 2018: 46.9, 2019: -12.0, 2020: -23.7, 2021: -27.3, 2022: -1.4, 2023: -48.2, 2024: -16.5.

## ADA/USDT

Trades: 180; lucro líquido: -111.41.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 128 | -478.11 | – | -1.29% | 0% | 0.7 h |
| take_profit_2pct | 46 | 361.55 | – | 2.70% | 100% | 1.6 h |
| time_exit_8h | 3 | 5.88 | – | 0.71% | 100% | 8.0 h |
| time_exit_utc_day_close | 3 | -0.72 | – | -0.09% | 33% | 5.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 157 | -162.43 | -0.36% | 23% |
| 3 h a 1 dia | 23 | 51.02 | 0.77% | 61% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (50): MFE mediano 3.7%, MAE mediano -0.5%, devolução média do melhor ponto 1.5%, captura mediana 0.68.
- Perdedores (130): MAE mediano -1.3%, MFE mediano 0.7%; 17 (13%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 156.04; 350% do lucro antes de custos.
- Trades < 3 h: 157 (lucro -162.43); reentradas em < 24 h: 52 (lucro 57.02).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -123.27.
- Lucro por ano de fechamento: 2018: 6.2, 2019: -12.0, 2020: -4.6, 2021: -54.4, 2022: -26.5, 2023: -5.4, 2024: -14.9.

## LTC/USDT

Trades: 154; lucro líquido: -209.52.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 122 | -419.30 | – | -1.29% | 0% | 0.9 h |
| take_profit_2pct | 27 | 205.85 | – | 2.89% | 100% | 1.2 h |
| time_exit_8h | 5 | 3.93 | – | 0.30% | 80% | 8.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 131 | -189.73 | -0.53% | 18% |
| 3 h a 1 dia | 23 | -19.79 | -0.35% | 30% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (31): MFE mediano 3.9%, MAE mediano -0.5%, devolução média do melhor ponto 2.1%, captura mediana 0.65.
- Perdedores (123): MAE mediano -1.3%, MFE mediano 0.7%; 16 (13%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 122.51; – do lucro antes de custos.
- Trades < 3 h: 131 (lucro -189.73); reentradas em < 24 h: 42 (lucro -57.63).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -226.06.
- Lucro por ano de fechamento: 2018: -73.0, 2019: -21.2, 2020: -38.1, 2021: -16.7, 2022: -13.4, 2023: -45.0, 2024: -2.1.

## LINK/USDT

Trades: 179; lucro líquido: -140.01.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 132 | -470.46 | – | -1.29% | 0% | 0.8 h |
| take_profit_2pct | 44 | 327.61 | – | 2.73% | 100% | 1.5 h |
| time_exit_8h | 3 | 2.84 | – | 0.34% | 67% | 8.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 163 | -143.33 | -0.31% | 24% |
| 3 h a 1 dia | 16 | 3.33 | 0.11% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (46): MFE mediano 3.6%, MAE mediano -0.5%, devolução média do melhor ponto 1.7%, captura mediana 0.67.
- Perdedores (133): MAE mediano -1.3%, MFE mediano 0.8%; 17 (13%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 147.12; 2070% do lucro antes de custos.
- Trades < 3 h: 163 (lucro -143.33); reentradas em < 24 h: 51 (lucro -11.70).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -158.59.
- Lucro por ano de fechamento: 2019: -14.4, 2020: -95.8, 2021: -23.3, 2022: 9.3, 2023: -9.9, 2024: -5.9.

## DOGE/USDT

Trades: 134; lucro líquido: -126.11.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 100 | -368.61 | – | -1.29% | 0% | 0.9 h |
| take_profit_2pct | 26 | 234.75 | – | 3.15% | 100% | 1.0 h |
| time_exit_8h | 5 | 1.85 | – | 0.13% | 40% | 8.0 h |
| time_exit_utc_day_close | 3 | 5.90 | – | 0.72% | 100% | 5.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 114 | -99.02 | -0.31% | 22% |
| 3 h a 1 dia | 20 | -27.09 | -0.47% | 30% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (31): MFE mediano 5.0%, MAE mediano -0.3%, devolução média do melhor ponto 2.8%, captura mediana 0.53.
- Perdedores (103): MAE mediano -1.3%, MFE mediano 0.8%; 20 (19%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 114.56; – do lucro antes de custos.
- Trades < 3 h: 114 (lucro -99.02); reentradas em < 24 h: 36 (lucro -21.10).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -144.10.
- Lucro por ano de fechamento: 2019: -19.5, 2020: 19.9, 2021: -28.3, 2022: -60.7, 2023: -38.6, 2024: 1.1.

## SOL/USDT

Trades: 126; lucro líquido: -120.96.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 94 | -342.53 | – | -1.29% | 0% | 0.6 h |
| take_profit_2pct | 29 | 224.28 | – | 2.75% | 100% | 1.2 h |
| time_exit_8h | 3 | -2.71 | – | -0.33% | 0% | 8.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 117 | -119.05 | -0.36% | 23% |
| 3 h a 1 dia | 9 | -1.91 | -0.08% | 22% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (29): MFE mediano 4.0%, MAE mediano -0.6%, devolução média do melhor ponto 1.3%, captura mediana 0.70.
- Perdedores (97): MAE mediano -1.3%, MFE mediano 0.8%; 21 (22%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 106.26; – do lucro antes de custos.
- Trades < 3 h: 117 (lucro -119.05); reentradas em < 24 h: 36 (lucro 3.66).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -135.18.
- Lucro por ano de fechamento: 2020: -30.7, 2021: -32.7, 2022: -4.4, 2023: -23.3, 2024: -29.9.
