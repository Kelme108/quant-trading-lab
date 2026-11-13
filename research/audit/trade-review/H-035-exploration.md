# Revisão de trades: H-035 (exploração)

Fonte dos trades: `research/experiments/20261113T093435Z-h-035-exploration-btc-usdt/raw/backtest-result-2026-11-13_09-51-56.zip`; `research/experiments/20261113T093435Z-h-035-exploration-eth-usdt/raw/backtest-result-2026-11-13_09-56-08.zip`; `research/experiments/20261113T093435Z-h-035-exploration-bnb-usdt/raw/backtest-result-2026-11-13_10-00-01.zip`; `research/experiments/20261113T093435Z-h-035-exploration-xrp-usdt/raw/backtest-result-2026-11-13_10-03-48.zip`; `research/experiments/20261113T093435Z-h-035-exploration-ada-usdt/raw/backtest-result-2026-11-13_10-07-38.zip`; `research/experiments/20261113T093435Z-h-035-exploration-ltc-usdt/raw/backtest-result-2026-11-13_10-11-35.zip`; `research/experiments/20261113T093435Z-h-035-exploration-link-usdt/raw/backtest-result-2026-11-13_10-15-33.zip`; `research/experiments/20261113T093435Z-h-035-exploration-doge-usdt/raw/backtest-result-2026-11-13_10-19-32.zip`; `research/experiments/20261113T093435Z-h-035-exploration-sol-usdt/raw/backtest-result-2026-11-13_10-23-23.zip`; `research/experiments/20261113T093435Z-h-035-exploration-avax-usdt/raw/backtest-result-2026-11-13_10-26-54.zip`; `research/experiments/20261113T093435Z-h-035-exploration-dot-usdt/raw/backtest-result-2026-11-13_10-30-37.zip`; `research/experiments/20261113T093435Z-h-035-exploration-trx-usdt/raw/backtest-result-2026-11-13_10-34-28.zip`; `research/experiments/20261113T093435Z-h-035-exploration-near-usdt/raw/backtest-result-2026-11-13_10-38-32.zip`; `research/experiments/20261113T093435Z-h-035-exploration-uni-usdt/raw/backtest-result-2026-11-13_10-42-01.zip`; `research/experiments/20261113T093435Z-h-035-exploration-bch-usdt/raw/backtest-result-2026-11-13_10-45-41.zip`; `research/experiments/20261113T093435Z-h-035-exploration-xlm-usdt/raw/backtest-result-2026-11-13_10-49-29.zip`; `research/experiments/20261113T093435Z-h-035-exploration-fil-usdt/raw/backtest-result-2026-11-13_10-53-29.zip`; `research/experiments/20261113T093435Z-h-035-exploration-aave-usdt/raw/backtest-result-2026-11-13_10-57-06.zip`; `research/experiments/20261113T093435Z-h-035-exploration-inj-usdt/raw/backtest-result-2026-11-13_11-00-45.zip`; `research/experiments/20261113T093435Z-h-035-exploration-hbar-usdt/raw/backtest-result-2026-11-13_11-04-26.zip`; `research/experiments/20261113T093435Z-h-035-exploration-op-usdt/raw/backtest-result-2026-11-13_11-07-56.zip`; `research/experiments/20261113T093435Z-h-035-exploration-apt-usdt/raw/backtest-result-2026-11-13_11-11-22.zip`; `research/experiments/20261113T093435Z-h-035-exploration-arb-usdt/raw/backtest-result-2026-11-13_11-14-41.zip`; `research/experiments/20261113T093435Z-h-035-exploration-sui-usdt/raw/backtest-result-2026-11-13_11-18-15.zip`; `research/experiments/20261113T093435Z-h-035-exploration-atom-usdt/raw/backtest-result-2026-11-13_11-21-38.zip`; `research/experiments/20261113T093435Z-h-035-exploration-etc-usdt/raw/backtest-result-2026-11-13_11-25-32.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 136; lucro líquido: 31.95.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 90 | 459.14 | 1437% | 1.68% | 72% | 24.0 h |
| below_signal_low | 34 | -231.18 | -724% | -2.20% | 6% | 13.8 h |
| stop_loss | 12 | -196.01 | -614% | -5.28% | 0% | 9.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 4 | -30.06 | -2.43% | 0% |
| 3 h a 1 dia | 39 | -390.27 | -3.24% | 3% |
| 1 a 7 dias | 93 | 452.28 | 1.60% | 71% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (67): MFE mediano 4.6%, MAE mediano -0.7%, devolução média do melhor ponto 2.6%, captura mediana 0.50.
- Perdedores (69): MAE mediano -3.0%, MFE mediano 1.0%; 12 (17%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 125.04; 80% do lucro antes de custos.
- Trades < 3 h: 4 (lucro -30.06); reentradas em < 24 h: 7 (lucro 30.31).
- Maior trade = 111% do lucro; top 5 = 408%; top 10 = 652%; lucro sem o melhor = -3.51.
- Lucro por ano de fechamento: 2017: 10.1, 2018: 34.5, 2019: -36.1, 2020: -4.8, 2021: -3.5, 2022: 40.4, 2023: -16.1, 2024: 7.4.

## ETH/USDT

Trades: 123; lucro líquido: 354.28.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 92 | 731.91 | 207% | 2.27% | 65% | 24.0 h |
| below_signal_low | 19 | -159.02 | -45% | -2.13% | 11% | 11.0 h |
| stop_loss | 12 | -218.61 | -62% | -5.28% | 0% | 9.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 5 | -71.66 | -4.01% | 0% |
| 3 h a 1 dia | 26 | -305.98 | -3.22% | 8% |
| 1 a 7 dias | 92 | 731.91 | 2.27% | 65% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (62): MFE mediano 5.7%, MAE mediano -0.8%, devolução média do melhor ponto 3.1%, captura mediana 0.42.
- Perdedores (61): MAE mediano -2.7%, MFE mediano 1.4%; 19 (31%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 135.36; 28% do lucro antes de custos.
- Trades < 3 h: 5 (lucro -71.66); reentradas em < 24 h: 9 (lucro 67.28).
- Maior trade = 19% do lucro; top 5 = 70%; top 10 = 115%; lucro sem o melhor = 287.21.
- Lucro por ano de fechamento: 2017: 135.2, 2018: -33.6, 2019: 28.1, 2020: 80.1, 2021: 33.9, 2022: 88.7, 2023: -38.1, 2024: 60.0.

## BNB/USDT

Trades: 98; lucro líquido: 26.62.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 57 | 469.61 | 1764% | 2.93% | 77% | 24.0 h |
| below_signal_low | 23 | -173.79 | -653% | -2.57% | 9% | 12.4 h |
| stop_loss | 18 | -269.20 | -1011% | -5.28% | 0% | 4.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 12 | -180.48 | -5.28% | 0% |
| 3 h a 1 dia | 27 | -250.57 | -3.22% | 7% |
| 1 a 7 dias | 59 | 457.66 | 2.77% | 75% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (46): MFE mediano 5.9%, MAE mediano -1.3%, devolução média do melhor ponto 3.2%, captura mediana 0.54.
- Perdedores (52): MAE mediano -3.9%, MFE mediano 1.3%; 19 (37%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 85.52; 76% do lucro antes de custos.
- Trades < 3 h: 12 (lucro -180.48); reentradas em < 24 h: 5 (lucro -43.84).
- Maior trade = 372% do lucro; top 5 = 707%; top 10 = 1005%; lucro sem o melhor = -72.34.
- Lucro por ano de fechamento: 2017: -46.9, 2018: -100.6, 2019: 110.6, 2020: -58.6, 2021: 98.3, 2022: 1.5, 2023: 45.4, 2024: -23.3.

## XRP/USDT

Trades: 90; lucro líquido: 15.69.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 50 | 711.13 | 4533% | 4.13% | 58% | 24.0 h |
| stop_loss | 30 | -572.31 | -3648% | -5.28% | 0% | 7.9 h |
| below_signal_low | 10 | -123.14 | -785% | -3.40% | 0% | 11.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 10 | -194.89 | -5.28% | 0% |
| 3 h a 1 dia | 30 | -500.55 | -4.65% | 0% |
| 1 a 7 dias | 50 | 711.13 | 4.13% | 58% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (29): MFE mediano 7.3%, MAE mediano -1.3%, devolução média do melhor ponto 4.2%, captura mediana 0.58.
- Perdedores (61): MAE mediano -5.0%, MFE mediano 1.5%; 26 (43%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 96.31; 86% do lucro antes de custos.
- Trades < 3 h: 10 (lucro -194.89); reentradas em < 24 h: 1 (lucro -21.40).
- Maior trade = 959% do lucro; top 5 = 2896%; top 10 = 3956%; lucro sem o melhor = -134.69.
- Lucro por ano de fechamento: 2018: 171.9, 2019: 124.3, 2020: 30.7, 2021: -153.1, 2022: -21.0, 2023: -136.4, 2024: -0.8.

## ADA/USDT

Trades: 78; lucro líquido: 211.67.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 53 | 595.82 | 281% | 3.41% | 74% | 24.0 h |
| stop_loss | 15 | -268.03 | -127% | -5.28% | 0% | 8.4 h |
| below_signal_low | 10 | -116.12 | -55% | -3.37% | 0% | 13.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 5 | -87.95 | -5.28% | 0% |
| 3 h a 1 dia | 20 | -296.21 | -4.33% | 0% |
| 1 a 7 dias | 53 | 595.82 | 3.41% | 74% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (39): MFE mediano 8.1%, MAE mediano -1.5%, devolução média do melhor ponto 4.1%, captura mediana 0.46.
- Perdedores (39): MAE mediano -4.6%, MFE mediano 2.3%; 21 (54%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 80.33; 28% do lucro antes de custos.
- Trades < 3 h: 5 (lucro -87.95); reentradas em < 24 h: 3 (lucro 57.38).
- Maior trade = 26% do lucro; top 5 = 112%; top 10 = 183%; lucro sem o melhor = 156.63.
- Lucro por ano de fechamento: 2018: 26.4, 2019: 3.2, 2020: 139.0, 2021: -0.0, 2022: 63.2, 2023: 11.6, 2024: -31.7.

## LTC/USDT

Trades: 113; lucro líquido: 5.07.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 69 | 659.69 | 13013% | 3.09% | 71% | 24.0 h |
| stop_loss | 30 | -502.59 | -9914% | -5.28% | 0% | 8.7 h |
| below_signal_low | 14 | -152.03 | -2999% | -3.39% | 0% | 15.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 6 | -101.38 | -5.28% | 0% |
| 3 h a 1 dia | 37 | -542.35 | -4.62% | 0% |
| 1 a 7 dias | 70 | 648.80 | 3.00% | 70% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (49): MFE mediano 5.8%, MAE mediano -1.0%, devolução média do melhor ponto 3.3%, captura mediana 0.53.
- Perdedores (64): MAE mediano -5.0%, MFE mediano 1.4%; 18 (28%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 106.57; 95% do lucro antes de custos.
- Trades < 3 h: 6 (lucro -101.38); reentradas em < 24 h: 7 (lucro -80.64).
- Maior trade = 1289% do lucro; top 5 = 5769%; top 10 = 8882%; lucro sem o melhor = -60.28.
- Lucro por ano de fechamento: 2018: -32.3, 2019: 19.4, 2020: 143.1, 2021: -36.3, 2022: -22.4, 2023: -6.9, 2024: -59.5.

## LINK/USDT

Trades: 79; lucro líquido: 123.16.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 51 | 536.94 | 436% | 3.40% | 78% | 24.0 h |
| stop_loss | 21 | -351.81 | -286% | -5.28% | 0% | 8.0 h |
| below_signal_low | 7 | -61.98 | -50% | -2.86% | 0% | 11.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 5 | -79.68 | -5.28% | 0% |
| 3 h a 1 dia | 23 | -334.10 | -4.55% | 0% |
| 1 a 7 dias | 51 | 536.94 | 3.40% | 78% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (40): MFE mediano 7.1%, MAE mediano -1.9%, devolução média do melhor ponto 4.3%, captura mediana 0.56.
- Perdedores (39): MAE mediano -5.2%, MFE mediano 2.1%; 22 (56%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 75.14; 38% do lucro antes de custos.
- Trades < 3 h: 5 (lucro -79.68); reentradas em < 24 h: 4 (lucro 13.70).
- Maior trade = 46% do lucro; top 5 = 171%; top 10 = 271%; lucro sem o melhor = 66.05.
- Lucro por ano de fechamento: 2019: -3.6, 2020: 135.5, 2021: -102.3, 2022: 36.1, 2023: 28.7, 2024: 28.8.

## DOGE/USDT

Trades: 76; lucro líquido: -98.92.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 36 | 521.63 | – | 4.64% | 72% | 24.0 h |
| stop_loss | 31 | -519.83 | – | -5.28% | 0% | 4.7 h |
| below_signal_low | 9 | -100.72 | – | -3.53% | 0% | 10.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 16 | -266.91 | -5.16% | 0% |
| 3 h a 1 dia | 24 | -353.64 | -4.70% | 0% |
| 1 a 7 dias | 36 | 521.63 | 4.64% | 72% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (26): MFE mediano 7.7%, MAE mediano -2.3%, devolução média do melhor ponto 8.4%, captura mediana 0.42.
- Perdedores (50): MAE mediano -5.3%, MFE mediano 2.2%; 26 (52%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 71.01; – do lucro antes de custos.
- Trades < 3 h: 16 (lucro -266.91); reentradas em < 24 h: 6 (lucro 18.50).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -210.11.
- Lucro por ano de fechamento: 2019: 21.0, 2020: 104.8, 2021: -103.4, 2022: -62.1, 2023: -72.1, 2024: 12.9.

## SOL/USDT

Trades: 56; lucro líquido: 232.42.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 29 | 633.47 | 273% | 6.79% | 79% | 24.0 h |
| stop_loss | 21 | -360.02 | -155% | -5.28% | 0% | 8.8 h |
| below_signal_low | 6 | -41.03 | -18% | -1.82% | 17% | 10.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 4 | -67.94 | -5.28% | 0% |
| 3 h a 1 dia | 23 | -333.11 | -4.38% | 4% |
| 1 a 7 dias | 29 | 633.47 | 6.79% | 79% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (24): MFE mediano 12.0%, MAE mediano -2.0%, devolução média do melhor ponto 5.7%, captura mediana 0.62.
- Perdedores (32): MAE mediano -5.3%, MFE mediano 2.4%; 17 (53%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 55.68; 19% do lucro antes de custos.
- Trades < 3 h: 4 (lucro -67.94); reentradas em < 24 h: 1 (lucro 0.07).
- Maior trade = 39% do lucro; top 5 = 138%; top 10 = 213%; lucro sem o melhor = 141.02.
- Lucro por ano de fechamento: 2020: -31.5, 2021: 178.7, 2022: -40.9, 2023: 80.8, 2024: 45.4.

## AVAX/USDT

Trades: 48; lucro líquido: 367.95.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 34 | 622.19 | 169% | 5.37% | 74% | 24.0 h |
| stop_loss | 12 | -227.15 | -62% | -5.28% | 0% | 6.3 h |
| below_signal_low | 2 | -27.09 | -7% | -3.49% | 0% | 9.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 4 | -68.91 | -5.28% | 0% |
| 3 h a 1 dia | 10 | -185.32 | -4.92% | 0% |
| 1 a 7 dias | 34 | 622.19 | 5.37% | 74% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (25): MFE mediano 7.1%, MAE mediano -1.6%, devolução média do melhor ponto 5.1%, captura mediana 0.55.
- Perdedores (23): MAE mediano -5.2%, MFE mediano 2.3%; 13 (57%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 54.54; 13% do lucro antes de custos.
- Trades < 3 h: 4 (lucro -68.91); reentradas em < 24 h: 4 (lucro -53.92).
- Maior trade = 52% do lucro; top 5 = 112%; top 10 = 147%; lucro sem o melhor = 177.48.
- Lucro por ano de fechamento: 2020: -15.2, 2021: 263.6, 2022: 39.1, 2023: 62.8, 2024: 17.6.

## DOT/USDT

Trades: 47; lucro líquido: -59.83.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 26 | 244.53 | – | 3.17% | 85% | 24.0 h |
| stop_loss | 16 | -253.72 | – | -5.28% | 0% | 7.4 h |
| below_signal_low | 5 | -50.63 | – | -3.41% | 0% | 10.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 3 | -46.73 | -5.28% | 0% |
| 3 h a 1 dia | 18 | -257.62 | -4.76% | 0% |
| 1 a 7 dias | 26 | 244.53 | 3.17% | 85% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (22): MFE mediano 6.7%, MAE mediano -1.7%, devolução média do melhor ponto 3.9%, captura mediana 0.52.
- Perdedores (25): MAE mediano -5.5%, MFE mediano 1.4%; 11 (44%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 42.03; – do lucro antes de custos.
- Trades < 3 h: 3 (lucro -46.73); reentradas em < 24 h: 2 (lucro -32.69).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -89.84.
- Lucro por ano de fechamento: 2020: 12.2, 2021: -14.2, 2022: 16.8, 2023: -43.3, 2024: -31.3.

## TRX/USDT

Trades: 106; lucro líquido: -136.28.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 58 | 353.32 | – | 2.13% | 66% | 24.0 h |
| below_signal_low | 26 | -149.95 | – | -2.04% | 12% | 13.1 h |
| stop_loss | 22 | -339.65 | – | -5.27% | 0% | 7.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 9 | -127.03 | -4.84% | 0% |
| 3 h a 1 dia | 36 | -373.76 | -3.59% | 6% |
| 1 a 7 dias | 61 | 364.51 | 2.09% | 64% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (41): MFE mediano 6.6%, MAE mediano -1.4%, devolução média do melhor ponto 5.7%, captura mediana 0.45.
- Perdedores (65): MAE mediano -4.4%, MFE mediano 1.2%; 22 (34%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 90.40; – do lucro antes de custos.
- Trades < 3 h: 9 (lucro -127.03); reentradas em < 24 h: 7 (lucro -52.96).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -192.03.
- Lucro por ano de fechamento: 2018: -56.1, 2019: 2.7, 2020: 62.1, 2021: -42.8, 2022: -12.6, 2023: -58.1, 2024: -31.5.

## NEAR/USDT

Trades: 47; lucro líquido: 57.30.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 22 | 393.45 | 687% | 5.98% | 91% | 24.0 h |
| stop_loss | 22 | -354.78 | -619% | -5.28% | 0% | 6.3 h |
| below_signal_low | 3 | 18.63 | 33% | 2.06% | 100% | 17.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 9 | -146.66 | -5.28% | 0% |
| 3 h a 1 dia | 15 | -194.02 | -4.27% | 13% |
| 1 a 7 dias | 23 | 397.98 | 5.79% | 91% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (23): MFE mediano 11.9%, MAE mediano -1.4%, devolução média do melhor ponto 8.7%, captura mediana 0.48.
- Perdedores (24): MAE mediano -5.5%, MFE mediano 2.2%; 13 (54%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 42.91; 43% do lucro antes de custos.
- Trades < 3 h: 9 (lucro -146.66); reentradas em < 24 h: 1 (lucro -15.71).
- Maior trade = 89% do lucro; top 5 = 346%; top 10 = 570%; lucro sem o melhor = 6.03.
- Lucro por ano de fechamento: 2020: 26.6, 2021: -17.4, 2022: -1.7, 2023: 56.6, 2024: -6.7.

## UNI/USDT

Trades: 56; lucro líquido: 44.77.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 31 | 379.08 | 847% | 4.24% | 74% | 24.0 h |
| stop_loss | 17 | -266.02 | -594% | -5.28% | 0% | 8.2 h |
| below_signal_low | 8 | -68.29 | -153% | -3.00% | 0% | 16.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 4 | -61.67 | -5.28% | 0% |
| 3 h a 1 dia | 21 | -272.64 | -4.41% | 0% |
| 1 a 7 dias | 31 | 379.08 | 4.24% | 74% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (23): MFE mediano 10.1%, MAE mediano -1.3%, devolução média do melhor ponto 4.8%, captura mediana 0.48.
- Perdedores (33): MAE mediano -5.0%, MFE mediano 3.2%; 24 (73%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 49.04; 52% do lucro antes de custos.
- Trades < 3 h: 4 (lucro -61.67); reentradas em < 24 h: 1 (lucro 9.36).
- Maior trade = 124% do lucro; top 5 = 478%; top 10 = 717%; lucro sem o melhor = -10.90.
- Lucro por ano de fechamento: 2020: -73.1, 2021: -18.2, 2022: 26.8, 2023: 107.0, 2024: 2.2.

## BCH/USDT

Trades: 80; lucro líquido: 158.52.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 47 | 600.60 | 379% | 4.12% | 66% | 24.0 h |
| stop_loss | 20 | -337.20 | -213% | -5.27% | 0% | 8.6 h |
| below_signal_low | 13 | -104.88 | -66% | -2.49% | 0% | 13.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 4 | -63.95 | -5.28% | 0% |
| 3 h a 1 dia | 28 | -370.49 | -4.08% | 0% |
| 1 a 7 dias | 48 | 592.96 | 3.99% | 65% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (31): MFE mediano 7.6%, MAE mediano -1.4%, devolução média do melhor ponto 4.6%, captura mediana 0.59.
- Perdedores (49): MAE mediano -4.4%, MFE mediano 1.4%; 19 (39%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 76.71; 33% do lucro antes de custos.
- Trades < 3 h: 4 (lucro -63.95); reentradas em < 24 h: 5 (lucro -55.36).
- Maior trade = 93% do lucro; top 5 = 221%; top 10 = 294%; lucro sem o melhor = 11.55.
- Lucro por ano de fechamento: 2020: -32.0, 2021: 105.2, 2022: -5.2, 2023: 21.3, 2024: 69.3.

## XLM/USDT

Trades: 71; lucro líquido: 136.84.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 40 | 595.66 | 435% | 4.29% | 85% | 24.0 h |
| stop_loss | 20 | -391.05 | -286% | -5.28% | 0% | 6.2 h |
| below_signal_low | 11 | -67.77 | -50% | -1.73% | 18% | 12.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 8 | -158.68 | -5.28% | 0% |
| 3 h a 1 dia | 23 | -300.14 | -3.58% | 9% |
| 1 a 7 dias | 40 | 595.66 | 4.29% | 85% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (36): MFE mediano 7.4%, MAE mediano -1.2%, devolução média do melhor ponto 7.0%, captura mediana 0.49.
- Perdedores (35): MAE mediano -5.4%, MFE mediano 1.6%; 16 (46%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 76.13; 36% do lucro antes de custos.
- Trades < 3 h: 8 (lucro -158.68); reentradas em < 24 h: 2 (lucro -32.36).
- Maior trade = 60% do lucro; top 5 = 223%; top 10 = 316%; lucro sem o melhor = 54.46.
- Lucro por ano de fechamento: 2018: 129.9, 2019: 111.3, 2020: 106.0, 2021: -190.4, 2022: -19.8, 2023: 13.1, 2024: -13.2.

## FIL/USDT

Trades: 46; lucro líquido: 268.48.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 20 | 617.44 | 230% | 9.16% | 65% | 24.0 h |
| stop_loss | 18 | -354.95 | -132% | -5.27% | 0% | 7.8 h |
| below_signal_low | 8 | 5.98 | 2% | -0.19% | 50% | 11.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 6 | -95.36 | -4.49% | 0% |
| 3 h a 1 dia | 19 | -255.90 | -3.68% | 16% |
| 1 a 7 dias | 21 | 619.75 | 8.75% | 67% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (17): MFE mediano 14.9%, MAE mediano -1.5%, devolução média do melhor ponto 8.0%, captura mediana 0.57.
- Perdedores (29): MAE mediano -5.2%, MFE mediano 2.4%; 15 (52%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 51.33; 16% do lucro antes de custos.
- Trades < 3 h: 6 (lucro -95.36); reentradas em < 24 h: 5 (lucro 123.09).
- Maior trade = 44% do lucro; top 5 = 170%; top 10 = 242%; lucro sem o melhor = 150.06.
- Lucro por ano de fechamento: 2020: -67.7, 2021: 366.1, 2022: 87.7, 2023: -88.4, 2024: -29.2.

## AAVE/USDT

Trades: 46; lucro líquido: -172.66.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 21 | -299.76 | – | -5.27% | 0% | 7.9 h |
| time_exit_24h | 20 | 161.01 | – | 3.14% | 75% | 24.0 h |
| below_signal_low | 5 | -33.91 | – | -2.65% | 0% | 11.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 7 | -99.01 | -5.26% | 0% |
| 3 h a 1 dia | 19 | -234.65 | -4.58% | 0% |
| 1 a 7 dias | 20 | 161.01 | 3.14% | 75% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (15): MFE mediano 8.5%, MAE mediano -1.1%, devolução média do melhor ponto 4.4%, captura mediana 0.46.
- Perdedores (31): MAE mediano -5.8%, MFE mediano 3.0%; 19 (61%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 36.25; – do lucro antes de custos.
- Trades < 3 h: 7 (lucro -99.01); reentradas em < 24 h: 3 (lucro -24.59).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -217.17.
- Lucro por ano de fechamento: 2020: 6.7, 2021: -129.7, 2022: 0.9, 2023: -67.3, 2024: 16.7.

## INJ/USDT

Trades: 61; lucro líquido: 166.75.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 31 | 640.73 | 384% | 6.43% | 87% | 24.0 h |
| stop_loss | 27 | -472.78 | -284% | -5.27% | 0% | 5.5 h |
| below_signal_low | 3 | -1.20 | -1% | -0.11% | 33% | 14.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 13 | -226.75 | -5.28% | 0% |
| 3 h a 1 dia | 17 | -247.23 | -4.36% | 6% |
| 1 a 7 dias | 31 | 640.73 | 6.43% | 87% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (28): MFE mediano 14.6%, MAE mediano -3.0%, devolução média do melhor ponto 7.1%, captura mediana 0.51.
- Perdedores (33): MAE mediano -5.5%, MFE mediano 2.2%; 17 (52%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 60.37; 27% do lucro antes de custos.
- Trades < 3 h: 13 (lucro -226.75); reentradas em < 24 h: 1 (lucro 56.33).
- Maior trade = 42% do lucro; top 5 = 174%; top 10 = 286%; lucro sem o melhor = 96.08.
- Lucro por ano de fechamento: 2020: 60.4, 2021: 73.9, 2022: -115.2, 2023: 176.8, 2024: -29.2.

## HBAR/USDT

Trades: 54; lucro líquido: -59.64.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 25 | -395.04 | – | -5.26% | 0% | 3.6 h |
| time_exit_24h | 15 | 338.61 | – | 7.52% | 67% | 24.0 h |
| below_signal_low | 14 | -3.21 | – | 0.31% | 21% | 14.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 14 | -225.84 | -5.26% | 0% |
| 3 h a 1 dia | 24 | -160.81 | -2.09% | 12% |
| 1 a 7 dias | 16 | 327.01 | 6.83% | 62% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (13): MFE mediano 14.0%, MAE mediano -1.5%, devolução média do melhor ponto 10.3%, captura mediana 0.55.
- Perdedores (41): MAE mediano -5.2%, MFE mediano 3.1%; 25 (61%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 48.25; – do lucro antes de custos.
- Trades < 3 h: 14 (lucro -225.84); reentradas em < 24 h: 2 (lucro 86.39).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -146.36.
- Lucro por ano de fechamento: 2019: -7.6, 2020: 55.5, 2021: -113.7, 2022: -5.1, 2023: -41.3, 2024: 52.5.

## OP/USDT

Trades: 43; lucro líquido: 257.59.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 26 | 580.77 | 225% | 6.56% | 69% | 24.0 h |
| stop_loss | 16 | -308.49 | -120% | -5.26% | 0% | 5.6 h |
| below_signal_low | 1 | -14.70 | -6% | -3.85% | 0% | 7.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 6 | -113.22 | -5.25% | 0% |
| 3 h a 1 dia | 11 | -209.96 | -5.13% | 0% |
| 1 a 7 dias | 26 | 580.77 | 6.56% | 69% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (18): MFE mediano 13.3%, MAE mediano -1.1%, devolução média do melhor ponto 6.9%, captura mediana 0.54.
- Perdedores (25): MAE mediano -5.7%, MFE mediano 2.2%; 13 (52%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 47.51; 16% do lucro antes de custos.
- Trades < 3 h: 6 (lucro -113.22); reentradas em < 24 h: 2 (lucro -26.06).
- Maior trade = 55% do lucro; top 5 = 150%; top 10 = 206%; lucro sem o melhor = 116.16.
- Lucro por ano de fechamento: 2022: 126.7, 2023: 241.7, 2024: -110.9.

## APT/USDT

Trades: 17; lucro líquido: -42.28.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 9 | -142.04 | – | -5.28% | 0% | 7.1 h |
| time_exit_24h | 7 | 105.19 | – | 5.17% | 57% | 24.0 h |
| below_signal_low | 1 | -5.42 | – | -1.85% | 0% | 9.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 4 | -62.46 | -5.28% | 0% |
| 3 h a 1 dia | 6 | -85.00 | -4.71% | 0% |
| 1 a 7 dias | 7 | 105.19 | 5.17% | 57% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (4): MFE mediano 18.8%, MAE mediano -1.1%, devolução média do melhor ponto 7.3%, captura mediana 0.61.
- Perdedores (13): MAE mediano -5.4%, MFE mediano 2.4%; 9 (69%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 14.92; – do lucro antes de custos.
- Trades < 3 h: 4 (lucro -62.46); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -91.33.
- Lucro por ano de fechamento: 2022: -15.9, 2023: -57.6, 2024: 31.2.

## ARB/USDT

Trades: 21; lucro líquido: -38.74.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 10 | 119.76 | – | 4.03% | 100% | 24.0 h |
| stop_loss | 8 | -126.77 | – | -5.28% | 0% | 8.4 h |
| below_signal_low | 3 | -31.73 | – | -3.45% | 0% | 10.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 2 | -31.45 | -5.28% | 0% |
| 3 h a 1 dia | 9 | -127.05 | -4.67% | 0% |
| 1 a 7 dias | 10 | 119.76 | 4.03% | 100% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (10): MFE mediano 9.3%, MAE mediano -1.5%, devolução média do melhor ponto 5.6%, captura mediana 0.28.
- Perdedores (11): MAE mediano -6.4%, MFE mediano 1.5%; 5 (45%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 18.87; – do lucro antes de custos.
- Trades < 3 h: 2 (lucro -31.45); reentradas em < 24 h: 1 (lucro -16.04).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -72.44.
- Lucro por ano de fechamento: 2023: 8.8, 2024: -47.5.

## SUI/USDT

Trades: 11; lucro líquido: 15.40.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 8 | 63.52 | 413% | 2.69% | 62% | 24.0 h |
| stop_loss | 3 | -48.12 | -313% | -5.28% | 0% | 5.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 1 | -16.19 | -5.28% | 0% |
| 3 h a 1 dia | 2 | -31.93 | -5.28% | 0% |
| 1 a 7 dias | 8 | 63.52 | 2.69% | 62% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (5): MFE mediano 9.7%, MAE mediano -2.1%, devolução média do melhor ponto 4.2%, captura mediana 0.54.
- Perdedores (6): MAE mediano -5.2%, MFE mediano 2.7%; 5 (83%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 10.03; 39% do lucro antes de custos.
- Trades < 3 h: 1 (lucro -16.19); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = 277% do lucro; top 5 = 604%; top 10 = 205%; lucro sem o melhor = -27.29.
- Lucro por ano de fechamento: 2023: -17.5, 2024: 32.9.

## ATOM/USDT

Trades: 61; lucro líquido: 37.42.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 31 | 507.77 | 1357% | 4.98% | 84% | 24.0 h |
| stop_loss | 25 | -447.11 | -1195% | -5.28% | 0% | 9.4 h |
| below_signal_low | 5 | -23.25 | -62% | -1.22% | 20% | 15.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 7 | -124.74 | -5.28% | 0% |
| 3 h a 1 dia | 23 | -345.61 | -4.40% | 4% |
| 1 a 7 dias | 31 | 507.77 | 4.98% | 84% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (27): MFE mediano 8.6%, MAE mediano -1.9%, devolução média do melhor ponto 4.3%, captura mediana 0.62.
- Perdedores (34): MAE mediano -5.7%, MFE mediano 2.3%; 19 (56%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 60.78; 62% do lucro antes de custos.
- Trades < 3 h: 7 (lucro -124.74); reentradas em < 24 h: 1 (lucro -0.25).
- Maior trade = 177% do lucro; top 5 = 710%; top 10 = 1065%; lucro sem o melhor = -28.95.
- Lucro por ano de fechamento: 2019: 95.7, 2020: 64.1, 2021: -58.5, 2022: -20.1, 2023: -18.0, 2024: -25.8.

## ETC/USDT

Trades: 90; lucro líquido: 296.01.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_24h | 54 | 868.72 | 293% | 4.88% | 65% | 24.0 h |
| stop_loss | 25 | -448.46 | -152% | -5.28% | 0% | 8.6 h |
| below_signal_low | 11 | -124.25 | -42% | -3.38% | 0% | 14.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 7 | -114.36 | -5.03% | 0% |
| 3 h a 1 dia | 28 | -443.45 | -4.65% | 0% |
| 1 a 7 dias | 55 | 853.82 | 4.73% | 64% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (35): MFE mediano 12.2%, MAE mediano -1.9%, devolução média do melhor ponto 5.4%, captura mediana 0.52.
- Perdedores (55): MAE mediano -5.0%, MFE mediano 2.0%; 29 (53%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 91.84; 24% do lucro antes de custos.
- Trades < 3 h: 7 (lucro -114.36); reentradas em < 24 h: 2 (lucro 54.27).
- Maior trade = 30% do lucro; top 5 = 136%; top 10 = 218%; lucro sem o melhor = 208.58.
- Lucro por ano de fechamento: 2018: -20.0, 2019: 38.2, 2020: -8.5, 2021: 36.7, 2022: 257.0, 2023: -53.4, 2024: 45.9.
