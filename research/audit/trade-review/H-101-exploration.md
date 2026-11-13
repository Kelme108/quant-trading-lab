# Revisão de trades: H-101 (exploração)

Fonte dos trades: `research/experiments/20261113T031250Z-h-101-exploration-btc-usdt/raw/backtest-result-2026-11-13_03-30-05.zip`; `research/experiments/20261113T031250Z-h-101-exploration-eth-usdt/raw/backtest-result-2026-11-13_03-33-52.zip`; `research/experiments/20261113T031250Z-h-101-exploration-bnb-usdt/raw/backtest-result-2026-11-13_03-37-41.zip`; `research/experiments/20261113T031250Z-h-101-exploration-xrp-usdt/raw/backtest-result-2026-11-13_03-41-23.zip`; `research/experiments/20261113T031250Z-h-101-exploration-ada-usdt/raw/backtest-result-2026-11-13_03-44-56.zip`; `research/experiments/20261113T031250Z-h-101-exploration-ltc-usdt/raw/backtest-result-2026-11-13_03-48-41.zip`; `research/experiments/20261113T031250Z-h-101-exploration-link-usdt/raw/backtest-result-2026-11-13_03-52-24.zip`; `research/experiments/20261113T031250Z-h-101-exploration-doge-usdt/raw/backtest-result-2026-11-13_03-55-56.zip`; `research/experiments/20261113T031250Z-h-101-exploration-sol-usdt/raw/backtest-result-2026-11-13_03-59-22.zip`; `research/experiments/20261113T031250Z-h-101-exploration-avax-usdt/raw/backtest-result-2026-11-13_04-02-46.zip`; `research/experiments/20261113T031250Z-h-101-exploration-dot-usdt/raw/backtest-result-2026-11-13_04-06-15.zip`; `research/experiments/20261113T031250Z-h-101-exploration-trx-usdt/raw/backtest-result-2026-11-13_04-09-45.zip`; `research/experiments/20261113T031250Z-h-101-exploration-near-usdt/raw/backtest-result-2026-11-13_04-13-21.zip`; `research/experiments/20261113T031250Z-h-101-exploration-uni-usdt/raw/backtest-result-2026-11-13_04-17-08.zip`; `research/experiments/20261113T031250Z-h-101-exploration-bch-usdt/raw/backtest-result-2026-11-13_04-20-48.zip`; `research/experiments/20261113T031250Z-h-101-exploration-xlm-usdt/raw/backtest-result-2026-11-13_04-24-23.zip`; `research/experiments/20261113T031250Z-h-101-exploration-fil-usdt/raw/backtest-result-2026-11-13_04-27-57.zip`; `research/experiments/20261113T031250Z-h-101-exploration-aave-usdt/raw/backtest-result-2026-11-13_04-31-35.zip`; `research/experiments/20261113T031250Z-h-101-exploration-inj-usdt/raw/backtest-result-2026-11-13_04-35-09.zip`; `research/experiments/20261113T031250Z-h-101-exploration-hbar-usdt/raw/backtest-result-2026-11-13_04-38-29.zip`; `research/experiments/20261113T031250Z-h-101-exploration-op-usdt/raw/backtest-result-2026-11-13_04-41-50.zip`; `research/experiments/20261113T031250Z-h-101-exploration-apt-usdt/raw/backtest-result-2026-11-13_04-45-02.zip`; `research/experiments/20261113T031250Z-h-101-exploration-arb-usdt/raw/backtest-result-2026-11-13_04-48-15.zip`; `research/experiments/20261113T031250Z-h-101-exploration-sui-usdt/raw/backtest-result-2026-11-13_04-51-31.zip`; `research/experiments/20261113T031250Z-h-101-exploration-atom-usdt/raw/backtest-result-2026-11-13_04-54-49.zip`; `research/experiments/20261113T031250Z-h-101-exploration-etc-usdt/raw/backtest-result-2026-11-13_04-58-24.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 109; lucro líquido: 58.59.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 67 | 308.67 | 527% | 1.50% | 72% | 24.0 h |
| kijun_exit | 29 | -117.17 | -200% | -1.29% | 10% | 10.0 h |
| stop_loss | 13 | -132.91 | -227% | -3.29% | 0% | 10.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 11 | -44.62 | -1.30% | 9% |
| 3 h a 1 dia | 30 | -199.41 | -2.13% | 7% |
| 1 a 7 dias | 68 | 302.62 | 1.45% | 71% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (51): MFE mediano 3.7%, MAE mediano -0.5%, devolução média do melhor ponto 2.5%, captura mediana 0.42.
- Perdedores (58): MAE mediano -1.9%, MFE mediano 0.9%; 9 (16%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 101.32; 63% do lucro antes de custos.
- Trades < 3 h: 11 (lucro -44.62); reentradas em < 24 h: 1 (lucro -3.82).
- Maior trade = 77% do lucro; top 5 = 236%; top 10 = 361%; lucro sem o melhor = 13.37.
- Lucro por ano de fechamento: 2018: -15.0, 2019: 67.5, 2020: -9.0, 2021: -18.6, 2022: 0.8, 2023: -6.1, 2024: 39.0.

## ETH/USDT

Trades: 124; lucro líquido: 466.91.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 80 | 822.26 | 176% | 2.77% | 78% | 24.0 h |
| kijun_exit | 29 | -164.83 | -35% | -1.44% | 3% | 13.2 h |
| stop_loss | 15 | -190.53 | -41% | -3.29% | 0% | 12.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 4 | -28.13 | -2.24% | 0% |
| 3 h a 1 dia | 38 | -307.30 | -2.03% | 3% |
| 1 a 7 dias | 82 | 802.35 | 2.65% | 76% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (63): MFE mediano 4.7%, MAE mediano -0.8%, devolução média do melhor ponto 2.6%, captura mediana 0.51.
- Perdedores (61): MAE mediano -2.2%, MFE mediano 1.2%; 15 (25%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 146.00; 24% do lucro antes de custos.
- Trades < 3 h: 4 (lucro -28.13); reentradas em < 24 h: 5 (lucro 2.58).
- Maior trade = 17% do lucro; top 5 = 54%; top 10 = 90%; lucro sem o melhor = 389.55.
- Lucro por ano de fechamento: 2017: -9.5, 2018: 27.9, 2019: 117.6, 2020: 182.2, 2021: 65.3, 2022: 82.5, 2023: -2.7, 2024: 3.6.

## BNB/USDT

Trades: 131; lucro líquido: 15.42.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 65 | 520.74 | 3376% | 2.73% | 75% | 24.0 h |
| stop_loss | 36 | -351.86 | -2281% | -3.29% | 0% | 6.1 h |
| kijun_exit | 30 | -153.45 | -995% | -1.72% | 0% | 10.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 21 | -175.67 | -2.79% | 0% |
| 3 h a 1 dia | 45 | -329.64 | -2.47% | 0% |
| 1 a 7 dias | 65 | 520.74 | 2.73% | 75% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (49): MFE mediano 4.7%, MAE mediano -0.7%, devolução média do melhor ponto 2.4%, captura mediana 0.59.
- Perdedores (82): MAE mediano -3.0%, MFE mediano 1.2%; 24 (29%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 116.45; 88% do lucro antes de custos.
- Trades < 3 h: 21 (lucro -175.67); reentradas em < 24 h: 2 (lucro -9.46).
- Maior trade = 236% do lucro; top 5 = 1046%; top 10 = 1849%; lucro sem o melhor = -20.99.
- Lucro por ano de fechamento: 2017: -29.4, 2018: 0.0, 2019: -23.9, 2020: 83.4, 2021: -68.7, 2022: 29.8, 2023: 40.7, 2024: -16.6.

## XRP/USDT

Trades: 135; lucro líquido: -37.22.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 65 | 452.79 | – | 2.47% | 75% | 24.0 h |
| stop_loss | 35 | -331.32 | – | -3.29% | 0% | 6.9 h |
| kijun_exit | 35 | -158.69 | – | -1.57% | 9% | 8.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 18 | -138.66 | -2.69% | 0% |
| 3 h a 1 dia | 52 | -351.36 | -2.34% | 6% |
| 1 a 7 dias | 65 | 452.79 | 2.47% | 75% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (52): MFE mediano 5.8%, MAE mediano -0.8%, devolução média do melhor ponto 4.0%, captura mediana 0.38.
- Perdedores (83): MAE mediano -2.8%, MFE mediano 1.2%; 27 (33%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 115.98; 147% do lucro antes de custos.
- Trades < 3 h: 18 (lucro -138.66); reentradas em < 24 h: 4 (lucro -25.60).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -123.83.
- Lucro por ano de fechamento: 2018: 4.3, 2019: -66.9, 2020: 41.2, 2021: -66.7, 2022: 33.7, 2023: 76.9, 2024: -59.7.

## ADA/USDT

Trades: 121; lucro líquido: 112.06.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 61 | 637.38 | 569% | 3.19% | 69% | 24.0 h |
| stop_loss | 36 | -397.10 | -354% | -3.28% | 0% | 8.5 h |
| kijun_exit | 24 | -128.21 | -114% | -1.58% | 0% | 11.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 13 | -129.87 | -2.92% | 0% |
| 3 h a 1 dia | 45 | -389.60 | -2.58% | 0% |
| 1 a 7 dias | 63 | 631.53 | 3.06% | 67% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (42): MFE mediano 6.9%, MAE mediano -1.1%, devolução média do melhor ponto 3.8%, captura mediana 0.62.
- Perdedores (79): MAE mediano -3.0%, MFE mediano 1.2%; 28 (35%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 119.79; 52% do lucro antes de custos.
- Trades < 3 h: 13 (lucro -129.87); reentradas em < 24 h: 7 (lucro -21.72).
- Maior trade = 57% do lucro; top 5 = 204%; top 10 = 330%; lucro sem o melhor = 48.08.
- Lucro por ano de fechamento: 2018: -51.7, 2019: 55.0, 2020: 146.7, 2021: 37.6, 2022: -41.1, 2023: -14.1, 2024: -20.3.

## LTC/USDT

Trades: 148; lucro líquido: 163.64.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 69 | 804.92 | 492% | 3.64% | 77% | 24.0 h |
| stop_loss | 51 | -545.37 | -333% | -3.28% | 0% | 6.9 h |
| kijun_exit | 28 | -95.91 | -59% | -1.03% | 21% | 12.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 19 | -196.28 | -3.20% | 0% |
| 3 h a 1 dia | 58 | -462.02 | -2.43% | 9% |
| 1 a 7 dias | 71 | 821.94 | 3.62% | 76% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (59): MFE mediano 6.5%, MAE mediano -0.8%, devolução média do melhor ponto 3.6%, captura mediana 0.55.
- Perdedores (89): MAE mediano -3.2%, MFE mediano 1.2%; 20 (22%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 144.96; 47% do lucro antes de custos.
- Trades < 3 h: 19 (lucro -196.28); reentradas em < 24 h: 9 (lucro 26.22).
- Maior trade = 42% do lucro; top 5 = 156%; top 10 = 251%; lucro sem o melhor = 94.63.
- Lucro por ano de fechamento: 2018: -99.7, 2019: 84.4, 2020: 164.8, 2021: -15.3, 2022: 13.2, 2023: 59.0, 2024: -42.7.

## LINK/USDT

Trades: 128; lucro líquido: 565.59.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 65 | 1362.55 | 241% | 5.46% | 89% | 24.0 h |
| stop_loss | 56 | -758.51 | -134% | -3.28% | 0% | 8.2 h |
| kijun_exit | 7 | -38.45 | -7% | -1.44% | 0% | 9.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 11 | -132.76 | -3.29% | 0% |
| 3 h a 1 dia | 52 | -664.20 | -3.04% | 0% |
| 1 a 7 dias | 65 | 1362.55 | 5.46% | 89% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (58): MFE mediano 7.5%, MAE mediano -1.0%, devolução média do melhor ponto 3.2%, captura mediana 0.64.
- Perdedores (70): MAE mediano -3.4%, MFE mediano 1.8%; 29 (41%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 159.98; 22% do lucro antes de custos.
- Trades < 3 h: 11 (lucro -132.76); reentradas em < 24 h: 4 (lucro 49.01).
- Maior trade = 40% do lucro; top 5 = 80%; top 10 = 112%; lucro sem o melhor = 341.14.
- Lucro por ano de fechamento: 2019: 234.9, 2020: 234.7, 2021: 0.2, 2022: 18.4, 2023: 32.2, 2024: 45.1.

## DOGE/USDT

Trades: 124; lucro líquido: -180.02.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 46 | -406.17 | – | -3.28% | 0% | 5.3 h |
| time_exit_24h | 42 | 380.31 | – | 3.44% | 71% | 24.0 h |
| kijun_exit | 36 | -154.16 | – | -1.57% | 6% | 9.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 33 | -259.06 | -2.85% | 0% |
| 3 h a 1 dia | 47 | -293.54 | -2.35% | 4% |
| 1 a 7 dias | 44 | 372.57 | 3.23% | 68% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (32): MFE mediano 7.9%, MAE mediano -0.9%, devolução média do melhor ponto 4.0%, captura mediana 0.47.
- Perdedores (92): MAE mediano -3.1%, MFE mediano 1.2%; 24 (26%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 100.77; – do lucro antes de custos.
- Trades < 3 h: 33 (lucro -259.06); reentradas em < 24 h: 2 (lucro -9.74).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -225.69.
- Lucro por ano de fechamento: 2019: 27.4, 2020: -15.5, 2021: -115.3, 2022: -105.0, 2023: -54.2, 2024: 82.5.

## SOL/USDT

Trades: 83; lucro líquido: 54.79.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 46 | -491.63 | -897% | -3.28% | 0% | 5.0 h |
| time_exit_24h | 26 | 604.75 | 1104% | 7.42% | 88% | 24.0 h |
| kijun_exit | 11 | -58.33 | -106% | -1.64% | 9% | 13.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 23 | -236.12 | -3.16% | 0% |
| 3 h a 1 dia | 34 | -313.83 | -2.83% | 3% |
| 1 a 7 dias | 26 | 604.75 | 7.42% | 88% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (24): MFE mediano 9.7%, MAE mediano -1.1%, devolução média do melhor ponto 5.1%, captura mediana 0.64.
- Perdedores (59): MAE mediano -3.6%, MFE mediano 1.7%; 26 (44%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 80.51; 60% do lucro antes de custos.
- Trades < 3 h: 23 (lucro -236.12); reentradas em < 24 h: 7 (lucro -37.56).
- Maior trade = 237% do lucro; top 5 = 625%; top 10 = 863%; lucro sem o melhor = -75.17.
- Lucro por ano de fechamento: 2020: 76.7, 2021: 62.4, 2022: -51.9, 2023: -53.9, 2024: 21.6.

## AVAX/USDT

Trades: 77; lucro líquido: 55.21.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 34 | -321.80 | -583% | -3.28% | 0% | 8.1 h |
| time_exit_24h | 33 | 429.31 | 778% | 4.57% | 85% | 24.0 h |
| kijun_exit | 10 | -52.31 | -95% | -1.84% | 0% | 8.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 14 | -120.43 | -3.02% | 0% |
| 3 h a 1 dia | 30 | -253.68 | -2.92% | 0% |
| 1 a 7 dias | 33 | 429.31 | 4.57% | 85% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (28): MFE mediano 8.8%, MAE mediano -0.9%, devolução média do melhor ponto 3.4%, captura mediana 0.56.
- Perdedores (49): MAE mediano -3.4%, MFE mediano 1.5%; 19 (39%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 66.40; 55% do lucro antes de custos.
- Trades < 3 h: 14 (lucro -120.43); reentradas em < 24 h: 1 (lucro -3.66).
- Maior trade = 134% do lucro; top 5 = 360%; top 10 = 530%; lucro sem o melhor = -19.02.
- Lucro por ano de fechamento: 2020: -9.6, 2021: -98.2, 2022: 76.4, 2023: 65.8, 2024: 20.8.

## DOT/USDT

Trades: 77; lucro líquido: 124.66.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 40 | 441.44 | 354% | 3.42% | 85% | 24.0 h |
| stop_loss | 21 | -226.47 | -182% | -3.27% | 0% | 6.0 h |
| kijun_exit | 16 | -90.30 | -72% | -1.69% | 0% | 10.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 8 | -79.46 | -3.13% | 0% |
| 3 h a 1 dia | 27 | -226.96 | -2.51% | 0% |
| 1 a 7 dias | 42 | 431.08 | 3.18% | 81% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (34): MFE mediano 7.1%, MAE mediano -0.9%, devolução média do melhor ponto 3.4%, captura mediana 0.57.
- Perdedores (43): MAE mediano -3.1%, MFE mediano 1.3%; 11 (26%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 76.42; 38% do lucro antes de custos.
- Trades < 3 h: 8 (lucro -79.46); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = 32% do lucro; top 5 = 123%; top 10 = 209%; lucro sem o melhor = 84.76.
- Lucro por ano de fechamento: 2020: 74.4, 2021: 52.3, 2022: -0.1, 2023: -20.3, 2024: 18.3.

## TRX/USDT

Trades: 97; lucro líquido: 19.64.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 50 | 324.21 | 1651% | 2.15% | 80% | 24.0 h |
| kijun_exit | 24 | -74.21 | -378% | -1.00% | 21% | 11.8 h |
| stop_loss | 23 | -230.36 | -1173% | -3.27% | 0% | 9.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 10 | -66.40 | -2.15% | 0% |
| 3 h a 1 dia | 36 | -230.46 | -2.09% | 14% |
| 1 a 7 dias | 51 | 316.50 | 2.06% | 78% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (45): MFE mediano 4.0%, MAE mediano -1.0%, devolução média do melhor ponto 2.9%, captura mediana 0.38.
- Perdedores (52): MAE mediano -2.7%, MFE mediano 0.8%; 14 (27%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 89.01; 82% do lucro antes de custos.
- Trades < 3 h: 10 (lucro -66.40); reentradas em < 24 h: 2 (lucro -1.51).
- Maior trade = 243% do lucro; top 5 = 838%; top 10 = 1119%; lucro sem o melhor = -28.15.
- Lucro por ano de fechamento: 2018: -10.1, 2019: -17.7, 2020: 92.4, 2021: -30.0, 2022: -33.3, 2023: 12.5, 2024: 5.9.

## NEAR/USDT

Trades: 79; lucro líquido: 177.17.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 39 | -415.43 | -234% | -3.28% | 0% | 6.7 h |
| time_exit_24h | 31 | 571.50 | 323% | 5.76% | 94% | 24.0 h |
| kijun_exit | 9 | 21.10 | 12% | 0.87% | 22% | 5.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 23 | -218.61 | -2.92% | 0% |
| 3 h a 1 dia | 25 | -175.72 | -2.11% | 8% |
| 1 a 7 dias | 31 | 571.50 | 5.76% | 94% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (31): MFE mediano 7.8%, MAE mediano -0.9%, devolução média do melhor ponto 5.6%, captura mediana 0.57.
- Perdedores (48): MAE mediano -3.5%, MFE mediano 1.9%; 24 (50%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 76.76; 30% do lucro antes de custos.
- Trades < 3 h: 23 (lucro -218.61); reentradas em < 24 h: 2 (lucro 93.73).
- Maior trade = 50% do lucro; top 5 = 162%; top 10 = 237%; lucro sem o melhor = 88.73.
- Lucro por ano de fechamento: 2020: 44.5, 2021: 4.8, 2022: 15.8, 2023: 36.5, 2024: 75.6.

## UNI/USDT

Trades: 87; lucro líquido: -74.63.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 37 | -346.10 | – | -3.27% | 0% | 6.9 h |
| time_exit_24h | 31 | 365.49 | – | 4.25% | 81% | 24.0 h |
| kijun_exit | 19 | -94.01 | – | -1.78% | 0% | 10.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 15 | -126.67 | -2.96% | 0% |
| 3 h a 1 dia | 40 | -309.12 | -2.72% | 0% |
| 1 a 7 dias | 32 | 361.17 | 4.06% | 78% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (25): MFE mediano 8.7%, MAE mediano -1.0%, devolução média do melhor ponto 3.9%, captura mediana 0.56.
- Perdedores (62): MAE mediano -3.2%, MFE mediano 1.4%; 24 (39%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 73.24; – do lucro antes de custos.
- Trades < 3 h: 15 (lucro -126.67); reentradas em < 24 h: 6 (lucro -20.55).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -132.56.
- Lucro por ano de fechamento: 2020: -14.1, 2021: -20.3, 2022: -35.4, 2023: 11.5, 2024: -16.4.

## BCH/USDT

Trades: 130; lucro líquido: 262.22.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 57 | 957.66 | 365% | 4.85% | 86% | 24.0 h |
| stop_loss | 41 | -484.00 | -185% | -3.28% | 0% | 8.9 h |
| kijun_exit | 32 | -211.44 | -81% | -1.83% | 3% | 11.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 13 | -137.33 | -2.90% | 0% |
| 3 h a 1 dia | 57 | -543.67 | -2.64% | 2% |
| 1 a 7 dias | 60 | 943.22 | 4.53% | 82% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (50): MFE mediano 6.9%, MAE mediano -1.0%, devolução média do melhor ponto 3.6%, captura mediana 0.55.
- Perdedores (80): MAE mediano -3.1%, MFE mediano 1.1%; 24 (30%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 139.47; 35% do lucro antes de custos.
- Trades < 3 h: 13 (lucro -137.33); reentradas em < 24 h: 4 (lucro 9.92).
- Maior trade = 38% do lucro; top 5 = 141%; top 10 = 207%; lucro sem o melhor = 162.50.
- Lucro por ano de fechamento: 2019: 0.9, 2020: 74.7, 2021: 107.7, 2022: 30.6, 2023: 45.4, 2024: 2.9.

## XLM/USDT

Trades: 115; lucro líquido: 63.80.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 53 | 547.81 | 859% | 3.55% | 77% | 24.0 h |
| stop_loss | 38 | -367.36 | -576% | -3.28% | 0% | 7.7 h |
| kijun_exit | 24 | -116.65 | -183% | -1.64% | 4% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 10 | -93.26 | -3.19% | 0% |
| 3 h a 1 dia | 50 | -380.92 | -2.57% | 2% |
| 1 a 7 dias | 55 | 537.97 | 3.35% | 75% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (42): MFE mediano 6.0%, MAE mediano -0.7%, devolução média do melhor ponto 3.6%, captura mediana 0.57.
- Perdedores (73): MAE mediano -3.2%, MFE mediano 1.5%; 31 (42%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 101.61; 61% do lucro antes de custos.
- Trades < 3 h: 10 (lucro -93.26); reentradas em < 24 h: 5 (lucro 41.54).
- Maior trade = 69% do lucro; top 5 = 316%; top 10 = 505%; lucro sem o melhor = 19.49.
- Lucro por ano de fechamento: 2018: -48.0, 2019: -22.5, 2020: 30.8, 2021: 25.9, 2022: 17.6, 2023: 33.2, 2024: 26.9.

## FIL/USDT

Trades: 76; lucro líquido: -174.02.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 39 | -345.61 | – | -3.28% | 0% | 5.2 h |
| time_exit_24h | 29 | 195.67 | – | 2.58% | 72% | 24.0 h |
| kijun_exit | 8 | -24.08 | – | -1.15% | 12% | 17.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 18 | -163.22 | -3.29% | 0% |
| 3 h a 1 dia | 28 | -208.85 | -2.82% | 0% |
| 1 a 7 dias | 30 | 198.05 | 2.53% | 73% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (22): MFE mediano 6.7%, MAE mediano -0.4%, devolução média do melhor ponto 3.1%, captura mediana 0.60.
- Perdedores (54): MAE mediano -3.3%, MFE mediano 0.9%; 15 (28%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 60.31; – do lucro antes de custos.
- Trades < 3 h: 18 (lucro -163.22); reentradas em < 24 h: 2 (lucro -1.86).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -202.10.
- Lucro por ano de fechamento: 2020: -41.5, 2021: -77.5, 2022: -45.7, 2023: 9.1, 2024: -18.5.

## AAVE/USDT

Trades: 86; lucro líquido: 39.65.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 43 | -441.47 | -1113% | -3.27% | 0% | 5.5 h |
| time_exit_24h | 35 | 523.63 | 1321% | 4.84% | 91% | 24.0 h |
| kijun_exit | 8 | -42.50 | -107% | -1.63% | 12% | 11.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 23 | -231.06 | -3.18% | 0% |
| 3 h a 1 dia | 27 | -248.71 | -2.93% | 4% |
| 1 a 7 dias | 36 | 519.42 | 4.67% | 89% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (33): MFE mediano 8.5%, MAE mediano -0.8%, devolução média do melhor ponto 4.0%, captura mediana 0.58.
- Perdedores (53): MAE mediano -3.3%, MFE mediano 1.2%; 24 (45%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 80.97; 67% do lucro antes de custos.
- Trades < 3 h: 23 (lucro -231.06); reentradas em < 24 h: 2 (lucro 32.56).
- Maior trade = 132% do lucro; top 5 = 494%; top 10 = 785%; lucro sem o melhor = -12.87.
- Lucro por ano de fechamento: 2020: -29.4, 2021: 38.5, 2022: 72.5, 2023: -20.6, 2024: -21.4.

## INJ/USDT

Trades: 98; lucro líquido: -212.43.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 61 | -552.64 | – | -3.28% | 0% | 4.2 h |
| time_exit_24h | 20 | 270.43 | – | 4.96% | 95% | 24.0 h |
| kijun_exit | 17 | 69.79 | – | 1.53% | 24% | 7.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 42 | -341.74 | -2.91% | 2% |
| 3 h a 1 dia | 36 | -141.12 | -1.44% | 8% |
| 1 a 7 dias | 20 | 270.43 | 4.96% | 95% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (23): MFE mediano 9.2%, MAE mediano -1.1%, devolução média do melhor ponto 7.1%, captura mediana 0.43.
- Perdedores (75): MAE mediano -3.6%, MFE mediano 1.8%; 32 (43%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 80.67; – do lucro antes de custos.
- Trades < 3 h: 42 (lucro -341.74); reentradas em < 24 h: 12 (lucro -67.75).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -325.13.
- Lucro por ano de fechamento: 2020: -38.9, 2021: -82.7, 2022: 68.8, 2023: -86.9, 2024: -72.7.

## HBAR/USDT

Trades: 110; lucro líquido: 66.12.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 51 | -469.97 | -711% | -3.27% | 0% | 3.8 h |
| time_exit_24h | 37 | 452.01 | 684% | 4.48% | 84% | 24.0 h |
| kijun_exit | 22 | 84.08 | 127% | 1.28% | 23% | 10.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 36 | -305.42 | -3.00% | 0% |
| 3 h a 1 dia | 37 | -80.46 | -0.83% | 14% |
| 1 a 7 dias | 37 | 452.01 | 4.48% | 84% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (36): MFE mediano 9.3%, MAE mediano -1.4%, devolução média do melhor ponto 7.0%, captura mediana 0.46.
- Perdedores (74): MAE mediano -3.4%, MFE mediano 1.2%; 23 (31%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 91.73; 58% do lucro antes de custos.
- Trades < 3 h: 36 (lucro -305.42); reentradas em < 24 h: 7 (lucro -38.83).
- Maior trade = 177% do lucro; top 5 = 424%; top 10 = 602%; lucro sem o melhor = -50.86.
- Lucro por ano de fechamento: 2019: -17.7, 2020: -59.4, 2021: -33.5, 2022: -31.8, 2023: 76.9, 2024: 131.6.

## OP/USDT

Trades: 56; lucro líquido: 230.56.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 26 | -303.51 | -132% | -3.25% | 0% | 6.0 h |
| time_exit_24h | 23 | 577.15 | 250% | 7.37% | 78% | 24.0 h |
| kijun_exit | 7 | -43.08 | -19% | -1.68% | 0% | 12.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 11 | -122.66 | -3.07% | 0% |
| 3 h a 1 dia | 22 | -223.93 | -2.84% | 0% |
| 1 a 7 dias | 23 | 577.15 | 7.37% | 78% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (18): MFE mediano 12.4%, MAE mediano -0.9%, devolução média do melhor ponto 3.3%, captura mediana 0.75.
- Perdedores (38): MAE mediano -3.3%, MFE mediano 1.3%; 15 (39%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 60.19; 21% do lucro antes de custos.
- Trades < 3 h: 11 (lucro -122.66); reentradas em < 24 h: 2 (lucro -24.36).
- Maior trade = 32% do lucro; top 5 = 138%; top 10 = 223%; lucro sem o melhor = 157.42.
- Lucro por ano de fechamento: 2022: 93.5, 2023: 155.3, 2024: -18.2.

## APT/USDT

Trades: 37; lucro líquido: -24.76.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 18 | -185.13 | – | -3.29% | 0% | 6.6 h |
| time_exit_24h | 12 | 178.15 | – | 4.87% | 75% | 24.0 h |
| kijun_exit | 7 | -17.78 | – | -0.78% | 29% | 11.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 8 | -77.43 | -3.07% | 0% |
| 3 h a 1 dia | 17 | -125.48 | -2.36% | 12% |
| 1 a 7 dias | 12 | 178.15 | 4.87% | 75% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (11): MFE mediano 8.7%, MAE mediano -1.1%, devolução média do melhor ponto 5.5%, captura mediana 0.36.
- Perdedores (26): MAE mediano -3.5%, MFE mediano 1.1%; 8 (31%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 34.78; 347% do lucro antes de custos.
- Trades < 3 h: 8 (lucro -77.43); reentradas em < 24 h: 1 (lucro -10.25).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -118.51.
- Lucro por ano de fechamento: 2022: -25.2, 2023: 52.1, 2024: -51.6.

## ARB/USDT

Trades: 31; lucro líquido: -3.67.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 14 | 163.78 | – | 3.84% | 71% | 24.0 h |
| stop_loss | 13 | -132.84 | – | -3.29% | 0% | 6.0 h |
| kijun_exit | 4 | -34.61 | – | -2.78% | 0% | 16.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 3 | -30.77 | -3.29% | 0% |
| 3 h a 1 dia | 14 | -136.68 | -3.14% | 0% |
| 1 a 7 dias | 14 | 163.78 | 3.84% | 71% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (10): MFE mediano 7.3%, MAE mediano -0.6%, devolução média do melhor ponto 3.4%, captura mediana 0.64.
- Perdedores (21): MAE mediano -3.3%, MFE mediano 1.7%; 8 (38%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 28.73; 115% do lucro antes de custos.
- Trades < 3 h: 3 (lucro -30.77); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -63.63.
- Lucro por ano de fechamento: 2023: 62.2, 2024: -65.9.

## SUI/USDT

Trades: 32; lucro líquido: 17.80.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 16 | 158.70 | 891% | 3.26% | 81% | 24.0 h |
| stop_loss | 12 | -122.03 | -685% | -3.28% | 0% | 3.9 h |
| kijun_exit | 4 | -18.86 | -106% | -1.52% | 0% | 7.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 7 | -59.39 | -2.74% | 0% |
| 3 h a 1 dia | 9 | -81.50 | -2.92% | 0% |
| 1 a 7 dias | 16 | 158.70 | 3.26% | 81% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (13): MFE mediano 9.6%, MAE mediano -1.6%, devolução média do melhor ponto 4.9%, captura mediana 0.47.
- Perdedores (19): MAE mediano -3.0%, MFE mediano 2.2%; 10 (53%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 29.56; 62% do lucro antes de custos.
- Trades < 3 h: 7 (lucro -59.39); reentradas em < 24 h: 2 (lucro 40.95).
- Maior trade = 182% do lucro; top 5 = 607%; top 10 = 919%; lucro sem o melhor = -14.53.
- Lucro por ano de fechamento: 2023: 64.1, 2024: -46.3.

## ATOM/USDT

Trades: 95; lucro líquido: -121.17.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 52 | -504.32 | – | -3.28% | 0% | 6.2 h |
| time_exit_24h | 34 | 435.23 | – | 4.38% | 82% | 24.0 h |
| kijun_exit | 9 | -52.08 | – | -2.03% | 0% | 15.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 18 | -173.65 | -3.29% | 0% |
| 3 h a 1 dia | 43 | -382.76 | -3.02% | 0% |
| 1 a 7 dias | 34 | 435.23 | 4.38% | 82% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (28): MFE mediano 7.7%, MAE mediano -1.4%, devolução média do melhor ponto 3.8%, captura mediana 0.50.
- Perdedores (67): MAE mediano -3.5%, MFE mediano 1.6%; 30 (45%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 82.96; – do lucro antes de custos.
- Trades < 3 h: 18 (lucro -173.65); reentradas em < 24 h: 5 (lucro -42.67).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -184.61.
- Lucro por ano de fechamento: 2019: -7.0, 2020: 88.8, 2021: -68.5, 2022: -63.1, 2023: -70.8, 2024: -0.6.

## ETC/USDT

Trades: 156; lucro líquido: 134.71.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 67 | 804.69 | 597% | 3.85% | 79% | 24.0 h |
| stop_loss | 53 | -552.72 | -410% | -3.28% | 0% | 7.4 h |
| kijun_exit | 36 | -117.25 | -87% | -1.02% | 17% | 13.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 18 | -177.37 | -3.05% | 0% |
| 3 h a 1 dia | 71 | -492.60 | -2.19% | 8% |
| 1 a 7 dias | 67 | 804.69 | 3.85% | 79% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (59): MFE mediano 6.8%, MAE mediano -0.9%, devolução média do melhor ponto 4.1%, captura mediana 0.48.
- Perdedores (97): MAE mediano -3.1%, MFE mediano 1.3%; 32 (33%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 148.52; 52% do lucro antes de custos.
- Trades < 3 h: 18 (lucro -177.37); reentradas em < 24 h: 6 (lucro -25.19).
- Maior trade = 64% do lucro; top 5 = 225%; top 10 = 334%; lucro sem o melhor = 47.85.
- Lucro por ano de fechamento: 2018: -56.9, 2019: 41.9, 2020: 71.9, 2021: -51.0, 2022: 107.9, 2023: 51.1, 2024: -30.2.
