# Revisão de trades: H-102 (exploração)

Fonte dos trades: `research/experiments/20261113T051350Z-h-102-exploration-btc-usdt/raw/backtest-result-2026-11-13_05-38-26.zip`; `research/experiments/20261113T051350Z-h-102-exploration-eth-usdt/raw/backtest-result-2026-11-13_05-45-56.zip`; `research/experiments/20261113T051350Z-h-102-exploration-bnb-usdt/raw/backtest-result-2026-11-13_05-53-42.zip`; `research/experiments/20261113T051350Z-h-102-exploration-xrp-usdt/raw/backtest-result-2026-11-13_06-01-06.zip`; `research/experiments/20261113T051350Z-h-102-exploration-ada-usdt/raw/backtest-result-2026-11-13_06-08-05.zip`; `research/experiments/20261113T051350Z-h-102-exploration-ltc-usdt/raw/backtest-result-2026-11-13_06-14-59.zip`; `research/experiments/20261113T051350Z-h-102-exploration-link-usdt/raw/backtest-result-2026-11-13_06-22-03.zip`; `research/experiments/20261113T051350Z-h-102-exploration-doge-usdt/raw/backtest-result-2026-11-13_06-28-10.zip`; `research/experiments/20261113T051350Z-h-102-exploration-sol-usdt/raw/backtest-result-2026-11-13_06-34-24.zip`; `research/experiments/20261113T051350Z-h-102-exploration-avax-usdt/raw/backtest-result-2026-11-13_06-39-57.zip`; `research/experiments/20261113T051350Z-h-102-exploration-dot-usdt/raw/backtest-result-2026-11-13_06-45-42.zip`; `research/experiments/20261113T051350Z-h-102-exploration-trx-usdt/raw/backtest-result-2026-11-13_06-51-43.zip`; `research/experiments/20261113T051350Z-h-102-exploration-near-usdt/raw/backtest-result-2026-11-13_06-57-39.zip`; `research/experiments/20261113T051350Z-h-102-exploration-uni-usdt/raw/backtest-result-2026-11-13_07-02-37.zip`; `research/experiments/20261113T051350Z-h-102-exploration-bch-usdt/raw/backtest-result-2026-11-13_07-08-46.zip`; `research/experiments/20261113T051350Z-h-102-exploration-xlm-usdt/raw/backtest-result-2026-11-13_07-14-59.zip`; `research/experiments/20261113T051350Z-h-102-exploration-fil-usdt/raw/backtest-result-2026-11-13_07-21-18.zip`; `research/experiments/20261113T051350Z-h-102-exploration-aave-usdt/raw/backtest-result-2026-11-13_07-26-38.zip`; `research/experiments/20261113T051350Z-h-102-exploration-inj-usdt/raw/backtest-result-2026-11-13_07-32-47.zip`; `research/experiments/20261113T051350Z-h-102-exploration-hbar-usdt/raw/backtest-result-2026-11-13_07-37-51.zip`; `research/experiments/20261113T051350Z-h-102-exploration-op-usdt/raw/backtest-result-2026-11-13_07-43-20.zip`; `research/experiments/20261113T051350Z-h-102-exploration-apt-usdt/raw/backtest-result-2026-11-13_07-48-30.zip`; `research/experiments/20261113T051350Z-h-102-exploration-arb-usdt/raw/backtest-result-2026-11-13_07-53-17.zip`; `research/experiments/20261113T051350Z-h-102-exploration-sui-usdt/raw/backtest-result-2026-11-13_07-56-51.zip`; `research/experiments/20261113T051350Z-h-102-exploration-atom-usdt/raw/backtest-result-2026-11-13_08-00-31.zip`; `research/experiments/20261113T051350Z-h-102-exploration-etc-usdt/raw/backtest-result-2026-11-13_08-06-55.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 115; lucro líquido: 31.04.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 73 | 288.72 | 930% | 1.56% | 74% | 14.5 h |
| close_below_jump_low | 27 | -132.38 | -427% | -1.91% | 0% | 5.8 h |
| stop_loss | 15 | -125.30 | -404% | -3.29% | 0% | 5.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 19 | -111.84 | -2.31% | 0% |
| 3 h a 1 dia | 96 | 142.88 | 0.60% | 56% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (54): MFE mediano 3.2%, MAE mediano -0.5%, devolução média do melhor ponto 1.8%, captura mediana 0.51.
- Perdedores (61): MAE mediano -2.2%, MFE mediano 0.7%; 9 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 87.73; 74% do lucro antes de custos.
- Trades < 3 h: 19 (lucro -111.84); reentradas em < 24 h: 5 (lucro 34.86).
- Maior trade = 119% do lucro; top 5 = 346%; top 10 = 528%; lucro sem o melhor = -5.78.
- Lucro por ano de fechamento: 2017: -24.5, 2018: 17.1, 2019: -0.1, 2020: 9.3, 2021: 42.6, 2022: -10.4, 2023: -10.6, 2024: 7.8.

## ETH/USDT

Trades: 92; lucro líquido: 202.12.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 66 | 425.86 | 211% | 2.31% | 80% | 14.0 h |
| stop_loss | 18 | -170.58 | -84% | -3.29% | 0% | 8.6 h |
| close_below_jump_low | 8 | -53.17 | -26% | -2.31% | 0% | 7.4 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 9 | -74.22 | -2.83% | 0% |
| 3 h a 1 dia | 83 | 276.33 | 1.21% | 64% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (53): MFE mediano 3.9%, MAE mediano -0.4%, devolução média do melhor ponto 2.4%, captura mediana 0.60.
- Perdedores (39): MAE mediano -3.0%, MFE mediano 1.2%; 11 (28%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 79.13; 28% do lucro antes de custos.
- Trades < 3 h: 9 (lucro -74.22); reentradas em < 24 h: 6 (lucro 5.13).
- Maior trade = 17% do lucro; top 5 = 56%; top 10 = 97%; lucro sem o melhor = 168.55.
- Lucro por ano de fechamento: 2017: 20.0, 2018: 23.2, 2019: 65.6, 2020: 68.5, 2021: 38.4, 2022: -1.3, 2023: -25.3, 2024: 12.9.

## BNB/USDT

Trades: 91; lucro líquido: 139.47.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 61 | 376.69 | 270% | 2.24% | 74% | 14.1 h |
| stop_loss | 17 | -158.75 | -114% | -3.28% | 0% | 4.1 h |
| close_below_jump_low | 13 | -78.47 | -56% | -2.11% | 0% | 5.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 15 | -127.62 | -2.97% | 0% |
| 3 h a 1 dia | 76 | 267.09 | 1.29% | 59% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (45): MFE mediano 4.2%, MAE mediano -0.9%, devolução média do melhor ponto 2.0%, captura mediana 0.52.
- Perdedores (46): MAE mediano -2.6%, MFE mediano 0.8%; 11 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 76.63; 35% do lucro antes de custos.
- Trades < 3 h: 15 (lucro -127.62); reentradas em < 24 h: 5 (lucro 17.23).
- Maior trade = 25% do lucro; top 5 = 100%; top 10 = 161%; lucro sem o melhor = 104.59.
- Lucro por ano de fechamento: 2018: -7.1, 2019: 131.7, 2020: 38.8, 2021: 25.3, 2022: -34.0, 2023: -29.6, 2024: 14.3.

## XRP/USDT

Trades: 105; lucro líquido: -27.05.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 53 | 400.80 | – | 2.85% | 74% | 12.8 h |
| stop_loss | 40 | -352.35 | – | -3.29% | 0% | 4.0 h |
| close_below_jump_low | 12 | -75.51 | – | -2.31% | 0% | 8.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 20 | -175.64 | -3.25% | 0% |
| 3 h a 1 dia | 85 | 148.59 | 0.67% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (39): MFE mediano 5.4%, MAE mediano -1.1%, devolução média do melhor ponto 3.3%, captura mediana 0.50.
- Perdedores (66): MAE mediano -3.1%, MFE mediano 1.2%; 21 (32%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 84.90; 147% do lucro antes de custos.
- Trades < 3 h: 20 (lucro -175.64); reentradas em < 24 h: 3 (lucro -6.65).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -97.42.
- Lucro por ano de fechamento: 2018: 102.8, 2019: 33.2, 2020: -27.5, 2021: -26.8, 2022: -45.0, 2023: -65.5, 2024: 1.7.

## ADA/USDT

Trades: 62; lucro líquido: 102.56.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 35 | 322.58 | 315% | 3.51% | 77% | 13.8 h |
| stop_loss | 20 | -176.79 | -172% | -3.28% | 0% | 5.0 h |
| close_below_jump_low | 7 | -43.23 | -42% | -2.30% | 0% | 3.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 15 | -115.84 | -2.88% | 0% |
| 3 h a 1 dia | 47 | 218.39 | 1.79% | 57% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (27): MFE mediano 4.9%, MAE mediano -0.7%, devolução média do melhor ponto 3.2%, captura mediana 0.58.
- Perdedores (35): MAE mediano -3.1%, MFE mediano 2.2%; 19 (54%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 49.69; 33% do lucro antes de custos.
- Trades < 3 h: 15 (lucro -115.84); reentradas em < 24 h: 2 (lucro -14.42).
- Maior trade = 55% do lucro; top 5 = 185%; top 10 = 266%; lucro sem o melhor = 46.10.
- Lucro por ano de fechamento: 2018: 18.7, 2019: 42.4, 2020: 17.9, 2021: -8.4, 2022: 18.1, 2023: 31.9, 2024: -18.1.

## LTC/USDT

Trades: 103; lucro líquido: 63.07.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 61 | 424.58 | 673% | 2.58% | 70% | 13.7 h |
| stop_loss | 33 | -299.06 | -474% | -3.28% | 0% | 5.8 h |
| close_below_jump_low | 9 | -62.44 | -99% | -2.52% | 0% | 6.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 18 | -161.23 | -3.23% | 0% |
| 3 h a 1 dia | 85 | 224.31 | 1.00% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (43): MFE mediano 4.3%, MAE mediano -0.7%, devolução média do melhor ponto 2.7%, captura mediana 0.55.
- Perdedores (60): MAE mediano -3.1%, MFE mediano 1.2%; 16 (27%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 84.43; 57% do lucro antes de custos.
- Trades < 3 h: 18 (lucro -161.23); reentradas em < 24 h: 7 (lucro -3.52).
- Maior trade = 82% do lucro; top 5 = 271%; top 10 = 421%; lucro sem o melhor = 11.38.
- Lucro por ano de fechamento: 2018: -2.9, 2019: 96.9, 2020: 12.5, 2021: 1.5, 2022: 1.2, 2023: -25.1, 2024: -21.0.

## LINK/USDT

Trades: 46; lucro líquido: 98.97.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 22 | 307.13 | 310% | 5.38% | 77% | 13.0 h |
| stop_loss | 21 | -185.27 | -187% | -3.29% | 0% | 4.9 h |
| close_below_jump_low | 3 | -22.89 | -23% | -2.75% | 0% | 10.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 9 | -80.08 | -3.29% | 0% |
| 3 h a 1 dia | 37 | 179.06 | 1.91% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (17): MFE mediano 6.7%, MAE mediano -0.8%, devolução média do melhor ponto 4.3%, captura mediana 0.65.
- Perdedores (29): MAE mediano -3.3%, MFE mediano 1.4%; 13 (45%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 36.93; 27% do lucro antes de custos.
- Trades < 3 h: 9 (lucro -80.08); reentradas em < 24 h: 4 (lucro 83.80).
- Maior trade = 112% do lucro; top 5 = 210%; top 10 = 278%; lucro sem o melhor = -11.74.
- Lucro por ano de fechamento: 2019: 98.7, 2020: -41.4, 2021: -17.3, 2022: 8.1, 2023: 47.1, 2024: 4.0.

## DOGE/USDT

Trades: 88; lucro líquido: -269.27.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 50 | -363.40 | – | -3.28% | 0% | 3.1 h |
| time_exit_utc_day_close | 29 | 147.70 | – | 2.18% | 59% | 13.7 h |
| close_below_jump_low | 9 | -53.57 | – | -2.54% | 0% | 4.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 35 | -250.74 | -3.26% | 0% |
| 3 h a 1 dia | 53 | -18.54 | -0.18% | 32% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (17): MFE mediano 8.9%, MAE mediano -1.2%, devolução média do melhor ponto 4.1%, captura mediana 0.48.
- Perdedores (71): MAE mediano -3.2%, MFE mediano 1.6%; 32 (45%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 58.64; – do lucro antes de custos.
- Trades < 3 h: 35 (lucro -250.74); reentradas em < 24 h: 8 (lucro -46.06).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -298.87.
- Lucro por ano de fechamento: 2019: -11.7, 2020: 33.5, 2021: -134.6, 2022: -73.1, 2023: -62.7, 2024: -20.6.

## SOL/USDT

Trades: 43; lucro líquido: 212.02.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 23 | 396.04 | 187% | 6.21% | 91% | 13.4 h |
| stop_loss | 17 | -161.05 | -76% | -3.28% | 0% | 5.3 h |
| close_below_jump_low | 3 | -22.98 | -11% | -2.52% | 0% | 6.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 9 | -84.07 | -3.22% | 0% |
| 3 h a 1 dia | 34 | 296.09 | 3.19% | 62% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (21): MFE mediano 8.4%, MAE mediano -1.0%, devolução média do melhor ponto 3.9%, captura mediana 0.61.
- Perdedores (22): MAE mediano -3.3%, MFE mediano 2.3%; 13 (59%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 37.34; 15% do lucro antes de custos.
- Trades < 3 h: 9 (lucro -84.07); reentradas em < 24 h: 6 (lucro 109.78).
- Maior trade = 31% do lucro; top 5 = 108%; top 10 = 156%; lucro sem o melhor = 145.51.
- Lucro por ano de fechamento: 2020: -8.2, 2021: 127.6, 2022: -12.9, 2023: 113.2, 2024: -7.7.

## AVAX/USDT

Trades: 25; lucro líquido: -101.77.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 14 | -109.24 | – | -3.28% | 0% | 1.6 h |
| time_exit_utc_day_close | 9 | 15.03 | – | 0.72% | 56% | 12.3 h |
| close_below_jump_low | 2 | -7.57 | – | -1.63% | 0% | 12.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 10 | -77.22 | -3.28% | 0% |
| 3 h a 1 dia | 15 | -24.56 | -0.66% | 33% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (5): MFE mediano 4.5%, MAE mediano -1.2%, devolução média do melhor ponto 2.3%, captura mediana 0.46.
- Perdedores (20): MAE mediano -3.3%, MFE mediano 1.6%; 7 (35%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 17.47; – do lucro antes de custos.
- Trades < 3 h: 10 (lucro -77.22); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -110.04.
- Lucro por ano de fechamento: 2020: -8.2, 2021: -54.3, 2022: -10.2, 2023: -24.0, 2024: -4.9.

## DOT/USDT

Trades: 31; lucro líquido: 24.63.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 19 | 119.64 | 486% | 2.54% | 74% | 13.5 h |
| stop_loss | 10 | -82.05 | -333% | -3.28% | 0% | 3.8 h |
| close_below_jump_low | 2 | -12.96 | -53% | -2.55% | 0% | 8.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 8 | -63.96 | -3.19% | 0% |
| 3 h a 1 dia | 23 | 88.59 | 1.56% | 61% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (14): MFE mediano 6.0%, MAE mediano -0.9%, devolução média do melhor ponto 3.4%, captura mediana 0.53.
- Perdedores (17): MAE mediano -3.0%, MFE mediano 1.7%; 7 (41%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 23.34; 49% do lucro antes de custos.
- Trades < 3 h: 8 (lucro -63.96); reentradas em < 24 h: 1 (lucro -3.04).
- Maior trade = 144% do lucro; top 5 = 365%; top 10 = 523%; lucro sem o melhor = -10.76.
- Lucro por ano de fechamento: 2020: -18.5, 2021: 40.5, 2022: -16.7, 2023: 5.8, 2024: 13.5.

## TRX/USDT

Trades: 97; lucro líquido: -49.89.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 54 | 234.33 | – | 1.70% | 67% | 11.6 h |
| stop_loss | 24 | -202.85 | – | -3.27% | 0% | 4.1 h |
| close_below_jump_low | 19 | -81.37 | – | -1.71% | 0% | 8.1 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 15 | -113.52 | -2.93% | 0% |
| 3 h a 1 dia | 82 | 63.62 | 0.30% | 44% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (36): MFE mediano 3.5%, MAE mediano -0.6%, devolução média do melhor ponto 2.7%, captura mediana 0.53.
- Perdedores (61): MAE mediano -2.2%, MFE mediano 1.3%; 19 (31%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 73.66; 310% do lucro antes de custos.
- Trades < 3 h: 15 (lucro -113.52); reentradas em < 24 h: 2 (lucro -9.03).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -81.17.
- Lucro por ano de fechamento: 2018: -15.5, 2019: 66.6, 2020: 27.4, 2021: -38.7, 2022: -45.1, 2023: -30.9, 2024: -13.7.

## NEAR/USDT

Trades: 34; lucro líquido: 145.04.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 20 | -166.23 | -115% | -3.28% | 0% | 1.9 h |
| time_exit_utc_day_close | 13 | 317.65 | 219% | 9.58% | 100% | 13.1 h |
| close_below_jump_low | 1 | -6.38 | -4% | -2.31% | 0% | 7.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 15 | -125.64 | -3.28% | 0% |
| 3 h a 1 dia | 19 | 270.69 | 5.57% | 68% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (13): MFE mediano 8.6%, MAE mediano -1.3%, devolução média do melhor ponto 5.0%, captura mediana 0.74.
- Perdedores (21): MAE mediano -3.5%, MFE mediano 1.9%; 9 (43%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 26.40; 15% do lucro antes de custos.
- Trades < 3 h: 15 (lucro -125.64); reentradas em < 24 h: 3 (lucro 42.77).
- Maior trade = 40% do lucro; top 5 = 140%; top 10 = 204%; lucro sem o melhor = 87.19.
- Lucro por ano de fechamento: 2020: -8.2, 2021: 80.8, 2022: 56.8, 2023: 15.6.

## UNI/USDT

Trades: 31; lucro líquido: 15.70.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 17 | -136.35 | -869% | -3.26% | 0% | 2.8 h |
| time_exit_utc_day_close | 12 | 162.98 | 1038% | 5.64% | 83% | 10.8 h |
| close_below_jump_low | 2 | -10.93 | -70% | -2.29% | 0% | 10.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 11 | -88.45 | -3.25% | 0% |
| 3 h a 1 dia | 20 | 104.15 | 2.18% | 50% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (10): MFE mediano 6.4%, MAE mediano -0.9%, devolução média do melhor ponto 4.0%, captura mediana 0.64.
- Perdedores (21): MAE mediano -3.2%, MFE mediano 1.9%; 10 (48%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 22.80; 59% do lucro antes de custos.
- Trades < 3 h: 11 (lucro -88.45); reentradas em < 24 h: 1 (lucro -7.95).
- Maior trade = 395% do lucro; top 5 = 938%; top 10 = 1057%; lucro sem o melhor = -46.24.
- Lucro por ano de fechamento: 2020: 1.6, 2021: -8.0, 2022: -31.9, 2023: -11.6, 2024: 65.5.

## BCH/USDT

Trades: 89; lucro líquido: 118.99.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 47 | 445.92 | 375% | 3.61% | 74% | 14.2 h |
| stop_loss | 24 | -214.72 | -180% | -3.28% | 0% | 4.8 h |
| close_below_jump_low | 18 | -112.20 | -94% | -2.28% | 0% | 5.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 17 | -135.25 | -2.89% | 0% |
| 3 h a 1 dia | 72 | 254.24 | 1.37% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (35): MFE mediano 5.0%, MAE mediano -1.0%, devolução média do melhor ponto 3.0%, captura mediana 0.50.
- Perdedores (54): MAE mediano -3.0%, MFE mediano 1.0%; 16 (30%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 72.44; 38% do lucro antes de custos.
- Trades < 3 h: 17 (lucro -135.25); reentradas em < 24 h: 4 (lucro -0.40).
- Maior trade = 107% do lucro; top 5 = 240%; top 10 = 304%; lucro sem o melhor = -8.56.
- Lucro por ano de fechamento: 2020: 89.8, 2021: -5.8, 2022: 14.3, 2023: -46.3, 2024: 67.0.

## XLM/USDT

Trades: 70; lucro líquido: -42.74.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 32 | -255.95 | – | -3.28% | 0% | 3.8 h |
| time_exit_utc_day_close | 28 | 269.07 | – | 4.09% | 79% | 12.8 h |
| close_below_jump_low | 10 | -55.86 | – | -2.28% | 0% | 7.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 23 | -179.09 | -3.18% | 0% |
| 3 h a 1 dia | 47 | 136.35 | 1.27% | 47% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (22): MFE mediano 5.2%, MAE mediano -1.3%, devolução média do melhor ponto 4.6%, captura mediana 0.55.
- Perdedores (48): MAE mediano -3.4%, MFE mediano 1.0%; 17 (35%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 50.86; 627% do lucro antes de custos.
- Trades < 3 h: 23 (lucro -179.09); reentradas em < 24 h: 4 (lucro 4.19).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -160.83.
- Lucro por ano de fechamento: 2018: 6.5, 2019: -12.2, 2020: -3.2, 2021: -78.8, 2022: -12.9, 2023: 73.4, 2024: -15.5.

## FIL/USDT

Trades: 41; lucro líquido: 201.60.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 21 | -194.13 | -96% | -3.28% | 0% | 6.1 h |
| time_exit_utc_day_close | 16 | 420.93 | 209% | 9.79% | 81% | 15.8 h |
| close_below_jump_low | 4 | -25.20 | -13% | -2.34% | 0% | 4.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 8 | -72.95 | -3.24% | 0% |
| 3 h a 1 dia | 33 | 274.55 | 3.16% | 39% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (13): MFE mediano 11.8%, MAE mediano -1.0%, devolução média do melhor ponto 5.6%, captura mediana 0.66.
- Perdedores (28): MAE mediano -3.2%, MFE mediano 1.5%; 11 (39%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 34.58; 15% do lucro antes de custos.
- Trades < 3 h: 8 (lucro -72.95); reentradas em < 24 h: 1 (lucro -8.81).
- Maior trade = 58% do lucro; top 5 = 158%; top 10 = 208%; lucro sem o melhor = 84.60.
- Lucro por ano de fechamento: 2020: -8.2, 2021: 94.1, 2022: 103.1, 2023: -19.2, 2024: 31.8.

## AAVE/USDT

Trades: 31; lucro líquido: -93.70.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 19 | -152.12 | – | -3.27% | 0% | 4.0 h |
| time_exit_utc_day_close | 11 | 65.72 | – | 2.40% | 64% | 10.8 h |
| close_below_jump_low | 1 | -7.31 | – | -2.92% | 0% | 0.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 11 | -87.91 | -3.23% | 0% |
| 3 h a 1 dia | 20 | -5.80 | -0.15% | 35% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (7): MFE mediano 4.2%, MAE mediano -0.8%, devolução média do melhor ponto 2.6%, captura mediana 0.71.
- Perdedores (24): MAE mediano -3.2%, MFE mediano 2.0%; 12 (50%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 22.57; – do lucro antes de custos.
- Trades < 3 h: 11 (lucro -87.91); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -130.06.
- Lucro por ano de fechamento: 2020: -8.2, 2021: -9.4, 2022: 44.3, 2023: -113.6, 2024: -6.8.

## INJ/USDT

Trades: 52; lucro líquido: -89.36.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 37 | -278.31 | – | -3.28% | 0% | 1.3 h |
| time_exit_utc_day_close | 14 | 194.79 | – | 6.29% | 100% | 12.6 h |
| close_below_jump_low | 1 | -5.85 | – | -2.54% | 0% | 5.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 31 | -232.55 | -3.28% | 0% |
| 3 h a 1 dia | 21 | 143.18 | 3.14% | 67% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (14): MFE mediano 9.3%, MAE mediano -1.0%, devolução média do melhor ponto 5.5%, captura mediana 0.54.
- Perdedores (38): MAE mediano -3.9%, MFE mediano 1.4%; 17 (45%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 35.24; – do lucro antes de custos.
- Trades < 3 h: 31 (lucro -232.55); reentradas em < 24 h: 4 (lucro -20.48).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -126.73.
- Lucro por ano de fechamento: 2020: -24.5, 2021: -86.9, 2022: -23.5, 2023: 54.0, 2024: -8.6.

## HBAR/USDT

Trades: 51; lucro líquido: -50.94.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 32 | -263.82 | – | -3.26% | 0% | 2.5 h |
| time_exit_utc_day_close | 14 | 247.12 | – | 7.16% | 79% | 16.1 h |
| close_below_jump_low | 5 | -34.25 | – | -2.73% | 0% | 5.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 23 | -191.16 | -3.26% | 0% |
| 3 h a 1 dia | 28 | 140.22 | 2.05% | 39% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (11): MFE mediano 7.6%, MAE mediano -0.7%, devolução média do melhor ponto 4.4%, captura mediana 0.63.
- Perdedores (40): MAE mediano -3.4%, MFE mediano 1.5%; 17 (42%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 38.20; – do lucro antes de custos.
- Trades < 3 h: 23 (lucro -191.16); reentradas em < 24 h: 1 (lucro -8.72).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -156.57.
- Lucro por ano de fechamento: 2019: 2.5, 2020: 11.4, 2021: -26.2, 2022: -15.6, 2023: -17.5, 2024: -5.5.

## OP/USDT

Trades: 21; lucro líquido: -5.17.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 11 | -91.83 | – | -3.27% | 0% | 2.6 h |
| time_exit_utc_day_close | 10 | 86.66 | – | 3.44% | 80% | 12.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 7 | -58.16 | -3.27% | 0% |
| 3 h a 1 dia | 14 | 52.99 | 1.52% | 57% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (8): MFE mediano 7.6%, MAE mediano -1.0%, devolução média do melhor ponto 3.8%, captura mediana 0.57.
- Perdedores (13): MAE mediano -3.5%, MFE mediano 2.2%; 8 (62%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 15.97; 148% do lucro antes de custos.
- Trades < 3 h: 7 (lucro -58.16); reentradas em < 24 h: 1 (lucro 1.45).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -31.00.
- Lucro por ano de fechamento: 2022: 1.4, 2023: 26.4, 2024: -33.1.

## APT/USDT

Trades: 18; lucro líquido: 126.09.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 8 | -73.41 | -58% | -3.29% | 0% | 4.2 h |
| time_exit_utc_day_close | 7 | 222.76 | 177% | 12.07% | 86% | 14.6 h |
| close_below_jump_low | 3 | -23.26 | -18% | -2.83% | 0% | 8.9 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 5 | -45.43 | -3.20% | 0% |
| 3 h a 1 dia | 13 | 171.52 | 5.05% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (6): MFE mediano 22.2%, MAE mediano -1.6%, devolução média do melhor ponto 7.5%, captura mediana 0.70.
- Perdedores (12): MAE mediano -3.7%, MFE mediano 2.9%; 7 (58%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 14.99; 11% do lucro antes de custos.
- Trades < 3 h: 5 (lucro -45.43); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = 51% do lucro; top 5 = 177%; top 10 = 158%; lucro sem o melhor = 62.33.
- Lucro por ano de fechamento: 2022: -7.4, 2023: 93.2, 2024: 40.3.

## ARB/USDT

Trades: 8; lucro líquido: 0.94.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 4 | 34.46 | 3681% | 3.43% | 75% | 13.3 h |
| stop_loss | 4 | -33.52 | -3581% | -3.29% | 0% | 4.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 2 | -16.78 | -3.29% | 0% |
| 3 h a 1 dia | 6 | 17.72 | 1.19% | 50% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (3): MFE mediano 7.1%, MAE mediano -1.6%, devolução média do melhor ponto 3.0%, captura mediana 0.64.
- Perdedores (5): MAE mediano -4.5%, MFE mediano 4.4%; 3 (60%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 6.06; 87% do lucro antes de custos.
- Trades < 3 h: 2 (lucro -16.78); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = 2646% do lucro; top 5 = 2793%; top 10 = 100%; lucro sem o melhor = -23.84.
- Lucro por ano de fechamento: 2023: 29.6, 2024: -28.7.

## SUI/USDT

Trades: 3; lucro líquido: 13.98.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 2 | 22.39 | 160% | 4.45% | 100% | 7.4 h |
| stop_loss | 1 | -8.41 | -60% | -3.28% | 0% | 2.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 1 | -8.41 | -3.28% | 0% |
| 3 h a 1 dia | 2 | 22.39 | 4.45% | 100% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (2): MFE mediano 7.0%, MAE mediano -1.0%, devolução média do melhor ponto 2.6%, captura mediana 0.61.
- Perdedores (1): MAE mediano -3.2%, MFE mediano 3.5%; 1 (100%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 2.30; 14% do lucro antes de custos.
- Trades < 3 h: 1 (lucro -8.41); reentradas em < 24 h: 0 (lucro 0.00).
- Maior trade = 118% do lucro; top 5 = 100%; top 10 = 100%; lucro sem o melhor = -2.56.
- Lucro por ano de fechamento: 2023: 16.5, 2024: -2.6.

## ATOM/USDT

Trades: 40; lucro líquido: -12.86.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| time_exit_utc_day_close | 22 | 130.20 | – | 2.38% | 73% | 12.4 h |
| stop_loss | 16 | -132.37 | – | -3.28% | 0% | 5.0 h |
| close_below_jump_low | 2 | -10.69 | – | -2.15% | 0% | 3.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 8 | -64.51 | -3.21% | 0% |
| 3 h a 1 dia | 32 | 51.65 | 0.66% | 50% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (16): MFE mediano 5.2%, MAE mediano -1.3%, devolução média do melhor ponto 4.0%, captura mediana 0.44.
- Perdedores (24): MAE mediano -3.3%, MFE mediano 1.7%; 10 (42%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 30.07; 175% do lucro antes de custos.
- Trades < 3 h: 8 (lucro -64.51); reentradas em < 24 h: 4 (lucro -14.93).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -41.46.
- Lucro por ano de fechamento: 2019: -7.3, 2020: 5.9, 2021: 8.0, 2022: -10.2, 2023: -2.0, 2024: -7.3.

## ETC/USDT

Trades: 106; lucro líquido: -109.96.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 52 | -430.49 | – | -3.28% | 0% | 4.8 h |
| time_exit_utc_day_close | 45 | 367.68 | – | 3.25% | 78% | 14.3 h |
| close_below_jump_low | 9 | -47.15 | – | -2.14% | 0% | 10.7 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 30 | -239.83 | -3.19% | 0% |
| 3 h a 1 dia | 76 | 129.88 | 0.68% | 46% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (35): MFE mediano 5.2%, MAE mediano -1.1%, devolução média do melhor ponto 3.4%, captura mediana 0.51.
- Perdedores (71): MAE mediano -3.3%, MFE mediano 1.6%; 25 (35%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 79.56; – do lucro antes de custos.
- Trades < 3 h: 30 (lucro -239.83); reentradas em < 24 h: 12 (lucro 33.98).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -165.68.
- Lucro por ano de fechamento: 2018: -5.5, 2019: 43.9, 2020: -35.6, 2021: 2.8, 2022: 33.1, 2023: -114.9, 2024: -33.7.
