# Revisão de trades: H-137 (exploração)

Fonte dos trades: `research/experiments/20261114T040132Z-h-137-exploration-btc-usdt/raw/backtest-result-2026-11-14_04-13-54.zip`; `research/experiments/20261114T040132Z-h-137-exploration-eth-usdt/raw/backtest-result-2026-11-14_04-13-54.zip`; `research/experiments/20261114T040132Z-h-137-exploration-bnb-usdt/raw/backtest-result-2026-11-14_04-13-53.zip`; `research/experiments/20261114T040132Z-h-137-exploration-xrp-usdt/raw/backtest-result-2026-11-14_04-22-26.zip`; `research/experiments/20261114T040132Z-h-137-exploration-ada-usdt/raw/backtest-result-2026-11-14_04-22-28.zip`; `research/experiments/20261114T040132Z-h-137-exploration-ltc-usdt/raw/backtest-result-2026-11-14_04-23-17.zip`; `research/experiments/20261114T040132Z-h-137-exploration-link-usdt/raw/backtest-result-2026-11-14_04-31-14.zip`; `research/experiments/20261114T040132Z-h-137-exploration-doge-usdt/raw/backtest-result-2026-11-14_04-31-41.zip`; `research/experiments/20261114T040132Z-h-137-exploration-sol-usdt/raw/backtest-result-2026-11-14_04-32-32.zip`; `research/experiments/20261114T040132Z-h-137-exploration-avax-usdt/raw/backtest-result-2026-11-14_04-38-30.zip`; `research/experiments/20261114T040132Z-h-137-exploration-dot-usdt/raw/backtest-result-2026-11-14_04-39-35.zip`; `research/experiments/20261114T040132Z-h-137-exploration-trx-usdt/raw/backtest-result-2026-11-14_04-40-00.zip`; `research/experiments/20261114T040132Z-h-137-exploration-near-usdt/raw/backtest-result-2026-11-14_04-45-38.zip`; `research/experiments/20261114T040132Z-h-137-exploration-uni-usdt/raw/backtest-result-2026-11-14_04-47-20.zip`; `research/experiments/20261114T040132Z-h-137-exploration-bch-usdt/raw/backtest-result-2026-11-14_04-48-55.zip`; `research/experiments/20261114T040132Z-h-137-exploration-xlm-usdt/raw/backtest-result-2026-11-14_04-52-56.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 66; lucro líquido: -84.85.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 30 | -254.17 | – | -2.47% | 0% | 3.9 h |
| time_exit_8h | 23 | 30.91 | – | 0.40% | 57% | 8.0 h |
| target_1_5R | 13 | 138.40 | – | 3.11% | 100% | 4.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 18 | -41.31 | -0.68% | 28% |
| 3 h a 1 dia | 48 | -43.55 | -0.26% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (26): MFE mediano 2.6%, MAE mediano -0.6%, devolução média do melhor ponto 1.2%, captura mediana 0.66.
- Perdedores (40): MAE mediano -1.7%, MFE mediano 0.6%; 6 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 67.36; – do lucro antes de custos.
- Trades < 3 h: 18 (lucro -41.31); reentradas em < 24 h: 3 (lucro -9.73).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -105.67.
- Lucro por ano de fechamento: 2017: -4.4, 2018: 8.2, 2019: 6.5, 2020: 7.3, 2021: -21.4, 2022: -45.6, 2023: -40.0, 2024: 4.7.

## ETH/USDT

Trades: 56; lucro líquido: 41.04.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_8h | 23 | -0.35 | -1% | -0.00% | 57% | 8.0 h |
| target_1_5R | 17 | 209.41 | 510% | 3.50% | 100% | 2.9 h |
| stop_loss | 16 | -168.01 | -409% | -2.95% | 0% | 2.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 25 | 14.17 | 0.19% | 48% |
| 3 h a 1 dia | 31 | 26.87 | 0.25% | 58% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (30): MFE mediano 3.1%, MAE mediano -0.5%, devolução média do melhor ponto 1.4%, captura mediana 0.68.
- Perdedores (26): MAE mediano -2.4%, MFE mediano 1.6%; 6 (23%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 59.59; 59% do lucro antes de custos.
- Trades < 3 h: 25 (lucro 14.17); reentradas em < 24 h: 3 (lucro -18.75).
- Maior trade = 59% do lucro; top 5 = 233%; top 10 = 391%; lucro sem o melhor = 17.00.
- Lucro por ano de fechamento: 2017: -3.3, 2018: -26.7, 2019: 26.0, 2020: 9.9, 2021: 17.9, 2022: 8.8, 2023: -4.0, 2024: 12.5.

## BNB/USDT

Trades: 63; lucro líquido: -98.17.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 27 | -335.26 | – | -3.64% | 0% | 2.9 h |
| time_exit_8h | 25 | 32.10 | – | 0.38% | 56% | 8.0 h |
| target_1_5R | 11 | 204.99 | – | 5.55% | 100% | 2.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 25 | -58.67 | -0.65% | 36% |
| 3 h a 1 dia | 38 | -39.50 | -0.31% | 42% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (25): MFE mediano 3.7%, MAE mediano -1.5%, devolução média do melhor ponto 1.6%, captura mediana 0.58.
- Perdedores (38): MAE mediano -2.4%, MFE mediano 1.2%; 10 (26%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 62.92; – do lucro antes de custos.
- Trades < 3 h: 25 (lucro -58.67); reentradas em < 24 h: 8 (lucro -97.11).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -143.22.
- Lucro por ano de fechamento: 2017: 14.5, 2018: -61.7, 2019: 22.1, 2020: -2.6, 2021: -26.6, 2022: -15.2, 2023: -35.0, 2024: 6.4.

## XRP/USDT

Trades: 48; lucro líquido: -11.49.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 20 | -202.49 | – | -2.83% | 0% | 2.5 h |
| time_exit_8h | 18 | 25.32 | – | 0.41% | 61% | 8.0 h |
| target_1_5R | 10 | 165.67 | – | 4.70% | 100% | 3.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 18 | -48.42 | -0.73% | 22% |
| 3 h a 1 dia | 30 | 36.92 | 0.36% | 57% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (21): MFE mediano 3.7%, MAE mediano -1.4%, devolução média do melhor ponto 1.5%, captura mediana 0.70.
- Perdedores (27): MAE mediano -2.3%, MFE mediano 1.8%; 12 (44%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 50.91; 129% do lucro antes de custos.
- Trades < 3 h: 18 (lucro -48.42); reentradas em < 24 h: 6 (lucro -24.37).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -56.98.
- Lucro por ano de fechamento: 2018: 23.4, 2019: -4.7, 2020: 28.9, 2021: -54.5, 2022: 5.7, 2023: -8.9, 2024: -1.3.

## ADA/USDT

Trades: 57; lucro líquido: -171.39.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 26 | -361.28 | – | -4.28% | 0% | 2.0 h |
| time_exit_8h | 20 | 24.25 | – | 0.34% | 50% | 8.0 h |
| target_1_5R | 11 | 165.64 | – | 4.79% | 100% | 4.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 22 | -189.78 | -2.60% | 18% |
| 3 h a 1 dia | 35 | 18.39 | 0.16% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (21): MFE mediano 4.3%, MAE mediano -1.3%, devolução média do melhor ponto 2.0%, captura mediana 0.67.
- Perdedores (36): MAE mediano -3.4%, MFE mediano 0.9%; 7 (19%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 54.69; – do lucro antes de custos.
- Trades < 3 h: 22 (lucro -189.78); reentradas em < 24 h: 6 (lucro -49.62).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -203.03.
- Lucro por ano de fechamento: 2018: -22.4, 2019: 25.6, 2020: -7.5, 2021: -163.7, 2022: 19.2, 2023: 3.6, 2024: -26.1.

## LTC/USDT

Trades: 48; lucro líquido: -109.74.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_8h | 21 | -32.31 | – | -0.44% | 48% | 8.0 h |
| stop_loss | 19 | -190.69 | – | -2.94% | 0% | 2.1 h |
| target_1_5R | 8 | 113.26 | – | 4.08% | 100% | 2.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 19 | -57.14 | -0.91% | 26% |
| 3 h a 1 dia | 29 | -52.60 | -0.52% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (18): MFE mediano 3.9%, MAE mediano -0.5%, devolução média do melhor ponto 2.2%, captura mediana 0.43.
- Perdedores (30): MAE mediano -2.9%, MFE mediano 0.8%; 6 (20%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 49.37; – do lucro antes de custos.
- Trades < 3 h: 19 (lucro -57.14); reentradas em < 24 h: 3 (lucro 0.82).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -135.75.
- Lucro por ano de fechamento: 2018: -17.0, 2019: 62.8, 2020: -23.6, 2021: -70.1, 2022: 5.8, 2023: -35.1, 2024: -32.5.

## LINK/USDT

Trades: 56; lucro líquido: -85.72.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 26 | -296.94 | – | -3.37% | 0% | 2.6 h |
| time_exit_8h | 20 | 62.68 | – | 0.97% | 70% | 8.0 h |
| target_1_5R | 10 | 148.54 | – | 4.37% | 100% | 3.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 24 | -89.10 | -1.09% | 25% |
| 3 h a 1 dia | 32 | 3.38 | 0.05% | 56% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (24): MFE mediano 4.8%, MAE mediano -1.5%, devolução média do melhor ponto 2.2%, captura mediana 0.66.
- Perdedores (32): MAE mediano -3.7%, MFE mediano 1.3%; 10 (31%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 56.26; – do lucro antes de custos.
- Trades < 3 h: 24 (lucro -89.10); reentradas em < 24 h: 3 (lucro 0.07).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -113.06.
- Lucro por ano de fechamento: 2019: -26.3, 2020: -4.1, 2021: -27.1, 2022: -10.8, 2023: -6.9, 2024: -10.6.

## DOGE/USDT

Trades: 61; lucro líquido: 191.87.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 28 | -373.27 | -195% | -3.13% | 0% | 1.3 h |
| time_exit_8h | 17 | -5.33 | -3% | -0.03% | 53% | 8.0 h |
| target_1_5R | 16 | 570.47 | 297% | 8.99% | 100% | 3.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 33 | 70.91 | 0.69% | 24% |
| 3 h a 1 dia | 28 | 120.96 | 1.18% | 61% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (25): MFE mediano 6.0%, MAE mediano -1.7%, devolução média do melhor ponto 4.1%, captura mediana 0.67.
- Perdedores (36): MAE mediano -2.9%, MFE mediano 1.1%; 9 (25%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 76.63; 29% do lucro antes de custos.
- Trades < 3 h: 33 (lucro 70.91); reentradas em < 24 h: 12 (lucro 113.76).
- Maior trade = 79% do lucro; top 5 = 202%; top 10 = 261%; lucro sem o melhor = 40.81.
- Lucro por ano de fechamento: 2019: 25.1, 2020: 46.0, 2021: 175.9, 2022: 2.5, 2023: -3.9, 2024: -53.7.

## SOL/USDT

Trades: 39; lucro líquido: -124.85.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 17 | -284.82 | – | -4.99% | 0% | 2.9 h |
| time_exit_8h | 14 | 13.76 | – | 0.34% | 64% | 8.0 h |
| target_1_5R | 7 | 155.42 | – | 6.67% | 100% | 2.3 h |
| trailing_stop_loss | 1 | -9.21 | – | -2.65% | 0% | 0.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 15 | -60.20 | -1.13% | 33% |
| 3 h a 1 dia | 24 | -64.65 | -0.80% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (16): MFE mediano 3.9%, MAE mediano -1.4%, devolução média do melhor ponto 1.6%, captura mediana 0.78.
- Perdedores (23): MAE mediano -4.8%, MFE mediano 1.1%; 6 (26%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 38.04; – do lucro antes de custos.
- Trades < 3 h: 15 (lucro -60.20); reentradas em < 24 h: 2 (lucro 14.15).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -166.86.
- Lucro por ano de fechamento: 2020: -34.9, 2021: -14.2, 2022: -36.3, 2023: -37.4, 2024: -1.9.

## AVAX/USDT

Trades: 45; lucro líquido: -42.92.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_8h | 20 | -6.44 | – | -0.09% | 45% | 8.0 h |
| stop_loss | 16 | -179.41 | – | -3.28% | 0% | 2.4 h |
| target_1_5R | 9 | 142.92 | – | 4.73% | 100% | 3.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 16 | -77.00 | -1.37% | 25% |
| 3 h a 1 dia | 29 | 34.08 | 0.35% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (18): MFE mediano 5.2%, MAE mediano -0.8%, devolução média do melhor ponto 3.1%, captura mediana 0.65.
- Perdedores (27): MAE mediano -3.3%, MFE mediano 1.5%; 10 (37%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 45.79; 1599% do lucro antes de custos.
- Trades < 3 h: 16 (lucro -77.00); reentradas em < 24 h: 6 (lucro 31.45).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -66.95.
- Lucro por ano de fechamento: 2020: -1.3, 2021: -28.9, 2022: 10.6, 2023: -35.5, 2024: 12.1.

## DOT/USDT

Trades: 35; lucro líquido: -2.33.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_8h | 16 | 24.27 | – | 0.43% | 50% | 8.0 h |
| stop_loss | 14 | -148.29 | – | -2.98% | 0% | 1.4 h |
| target_1_5R | 5 | 121.68 | – | 6.97% | 100% | 4.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 14 | -111.24 | -2.23% | 7% |
| 3 h a 1 dia | 21 | 108.91 | 1.49% | 57% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (13): MFE mediano 4.4%, MAE mediano -1.2%, devolução média do melhor ponto 1.6%, captura mediana 0.69.
- Perdedores (22): MAE mediano -3.0%, MFE mediano 0.7%; 3 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 37.25; 107% do lucro antes de custos.
- Trades < 3 h: 14 (lucro -111.24); reentradas em < 24 h: 1 (lucro -11.79).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -32.17.
- Lucro por ano de fechamento: 2020: -5.8, 2021: 14.2, 2022: 41.4, 2023: -49.3, 2024: -2.8.

## TRX/USDT

Trades: 51; lucro líquido: -20.69.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 20 | -266.52 | – | -3.72% | 0% | 2.9 h |
| time_exit_8h | 15 | -7.23 | – | -0.14% | 47% | 8.0 h |
| target_1_5R | 15 | 262.07 | – | 5.00% | 100% | 2.7 h |
| trailing_stop_loss | 1 | -9.01 | – | -2.39% | 0% | 2.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 22 | 46.67 | 0.68% | 41% |
| 3 h a 1 dia | 29 | -67.37 | -0.65% | 45% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (22): MFE mediano 4.3%, MAE mediano -0.8%, devolução média do melhor ponto 1.6%, captura mediana 0.67.
- Perdedores (29): MAE mediano -2.7%, MFE mediano 1.0%; 8 (28%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 53.82; 162% do lucro antes de custos.
- Trades < 3 h: 22 (lucro 46.67); reentradas em < 24 h: 5 (lucro 26.69).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -66.02.
- Lucro por ano de fechamento: 2019: 75.5, 2020: -23.7, 2021: -111.7, 2022: 49.8, 2023: -9.3, 2024: -1.3.

## NEAR/USDT

Trades: 36; lucro líquido: -133.68.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_8h | 16 | 28.02 | – | 0.66% | 69% | 8.0 h |
| stop_loss | 14 | -195.99 | – | -4.15% | 0% | 1.9 h |
| target_1_5R | 5 | 100.38 | – | 5.92% | 100% | 3.8 h |
| trailing_stop_loss | 1 | -66.10 | – | -21.23% | 0% | 7.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 12 | -108.42 | -2.65% | 17% |
| 3 h a 1 dia | 24 | -25.25 | -0.31% | 58% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (16): MFE mediano 4.9%, MAE mediano -1.5%, devolução média do melhor ponto 2.1%, captura mediana 0.63.
- Perdedores (20): MAE mediano -4.8%, MFE mediano 1.9%; 9 (45%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 34.39; – do lucro antes de custos.
- Trades < 3 h: 12 (lucro -108.42); reentradas em < 24 h: 4 (lucro -54.11).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -159.99.
- Lucro por ano de fechamento: 2020: 15.3, 2021: -121.7, 2022: -34.0, 2023: -13.8, 2024: 20.5.

## UNI/USDT

Trades: 34; lucro líquido: 7.82.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_8h | 15 | 50.20 | 642% | 0.94% | 53% | 8.0 h |
| stop_loss | 13 | -163.07 | -2086% | -3.40% | 0% | 1.8 h |
| target_1_5R | 6 | 120.69 | 1544% | 5.53% | 100% | 3.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 13 | -10.82 | -0.18% | 31% |
| 3 h a 1 dia | 21 | 18.63 | 0.26% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (14): MFE mediano 4.6%, MAE mediano -0.7%, devolução média do melhor ponto 2.3%, captura mediana 0.77.
- Perdedores (20): MAE mediano -3.0%, MFE mediano 1.2%; 6 (30%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 37.62; 83% do lucro antes de custos.
- Trades < 3 h: 13 (lucro -10.82); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = 381% do lucro; top 5 = 1451%; top 10 = 2280%; lucro sem o melhor = -21.98.
- Lucro por ano de fechamento: 2020: 42.0, 2021: -10.9, 2022: 51.2, 2023: -31.8, 2024: -42.7.

## BCH/USDT

Trades: 46; lucro líquido: 30.43.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 17 | -172.38 | -566% | -2.76% | 0% | 2.2 h |
| time_exit_8h | 17 | 3.14 | 10% | 0.06% | 53% | 8.0 h |
| target_1_5R | 12 | 199.68 | 656% | 4.60% | 100% | 3.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 17 | 25.48 | 0.46% | 41% |
| 3 h a 1 dia | 29 | 4.96 | 0.06% | 48% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (21): MFE mediano 3.9%, MAE mediano -0.8%, devolução média do melhor ponto 1.7%, captura mediana 0.70.
- Perdedores (25): MAE mediano -2.7%, MFE mediano 1.0%; 7 (28%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 50.36; 62% do lucro antes de custos.
- Trades < 3 h: 17 (lucro 25.48); reentradas em < 24 h: 2 (lucro -18.56).
- Maior trade = 114% do lucro; top 5 = 386%; top 10 = 620%; lucro sem o melhor = -4.22.
- Lucro por ano de fechamento: 2020: 20.4, 2021: 12.3, 2022: -21.3, 2023: 38.0, 2024: -18.9.

## XLM/USDT

Trades: 58; lucro líquido: 25.55.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_8h | 22 | 16.03 | 63% | 0.19% | 59% | 8.0 h |
| stop_loss | 21 | -278.31 | -1089% | -3.57% | 0% | 1.8 h |
| target_1_5R | 15 | 287.83 | 1127% | 5.30% | 100% | 3.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 25 | -37.18 | -0.31% | 36% |
| 3 h a 1 dia | 33 | 62.73 | 0.50% | 58% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (28): MFE mediano 4.3%, MAE mediano -0.8%, devolução média do melhor ponto 2.0%, captura mediana 0.66.
- Perdedores (30): MAE mediano -2.6%, MFE mediano 0.8%; 6 (20%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 63.08; 71% do lucro antes de custos.
- Trades < 3 h: 25 (lucro -37.18); reentradas em < 24 h: 6 (lucro -83.68).
- Maior trade = 190% do lucro; top 5 = 602%; top 10 = 911%; lucro sem o melhor = -23.07.
- Lucro por ano de fechamento: 2018: -17.5, 2019: 33.9, 2020: 74.3, 2021: -50.3, 2022: -9.5, 2023: 2.6, 2024: -7.9.
