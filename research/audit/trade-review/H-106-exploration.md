# Revisão de trades: H-106 (exploração)

Fonte dos trades: `research/experiments/20261111T132501Z-h-106-exploration-btc-usdt/raw/backtest-result-2026-11-11_13-41-20.zip`; `research/experiments/20261111T132501Z-h-106-exploration-eth-usdt/raw/backtest-result-2026-11-11_13-44-52.zip`; `research/experiments/20261111T132501Z-h-106-exploration-bnb-usdt/raw/backtest-result-2026-11-11_13-48-37.zip`; `research/experiments/20261111T132501Z-h-106-exploration-xrp-usdt/raw/backtest-result-2026-11-11_13-52-14.zip`; `research/experiments/20261111T132501Z-h-106-exploration-ada-usdt/raw/backtest-result-2026-11-11_13-55-49.zip`; `research/experiments/20261111T132501Z-h-106-exploration-ltc-usdt/raw/backtest-result-2026-11-11_13-59-26.zip`; `research/experiments/20261111T132501Z-h-106-exploration-link-usdt/raw/backtest-result-2026-11-11_14-02-47.zip`; `research/experiments/20261111T132501Z-h-106-exploration-doge-usdt/raw/backtest-result-2026-11-11_14-06-12.zip`; `research/experiments/20261111T132501Z-h-106-exploration-sol-usdt/raw/backtest-result-2026-11-11_14-09-26.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 1114; lucro líquido: -113.19.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| block_close_at_high7 | 358 | 237.93 | – | 1.39% | 92% | 7.1 h |
| stop_loss | 298 | -327.70 | – | -2.29% | 0% | 3.3 h |
| clock_exit_23utc | 258 | 18.72 | – | 0.14% | 48% | 7.6 h |
| time_exit_12h | 200 | -42.14 | – | -0.45% | 21% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 197 | -152.91 | -1.61% | 19% |
| 3 h a 1 dia | 917 | 39.72 | 0.08% | 50% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (498): MFE mediano 1.8%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.48.
- Perdedores (616): MAE mediano -2.0%, MFE mediano 0.5%; 41 (7%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 158.51; 350% do lucro antes de custos.
- Trades < 3 h: 197 (lucro -152.91); reentradas em < 24 h: 697 (lucro -74.94).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -121.37.
- Lucro por ano de fechamento: 2017: 11.4, 2018: -21.0, 2019: -30.5, 2020: 1.0, 2021: -18.6, 2022: -22.0, 2023: -22.0, 2024: -11.5.

## ETH/USDT

Trades: 1177; lucro líquido: -144.61.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 448 | -490.28 | – | -2.29% | 0% | 3.1 h |
| block_close_at_high7 | 310 | 293.45 | – | 1.99% | 99% | 7.1 h |
| clock_exit_23utc | 256 | 60.97 | – | 0.48% | 57% | 7.5 h |
| time_exit_12h | 163 | -8.75 | – | -0.14% | 37% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 282 | -234.24 | -1.73% | 13% |
| 3 h a 1 dia | 895 | 89.63 | 0.20% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (511): MFE mediano 2.4%, MAE mediano -0.5%, devolução média do melhor ponto 1.3%, captura mediana 0.53.
- Perdedores (666): MAE mediano -2.3%, MFE mediano 0.7%; 74 (11%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 166.84; 750% do lucro antes de custos.
- Trades < 3 h: 282 (lucro -234.24); reentradas em < 24 h: 742 (lucro -97.08).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -149.64.
- Lucro por ano de fechamento: 2017: 13.0, 2018: -12.8, 2019: -23.8, 2020: -10.5, 2021: -48.3, 2022: -22.4, 2023: -26.3, 2024: -13.5.

## BNB/USDT

Trades: 1258; lucro líquido: -189.97.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 532 | -558.25 | – | -2.29% | 0% | 2.7 h |
| block_close_at_high7 | 312 | 321.86 | – | 2.26% | 97% | 7.1 h |
| clock_exit_23utc | 243 | 46.57 | – | 0.40% | 56% | 7.3 h |
| time_exit_12h | 170 | -0.19 | – | -0.02% | 45% | 12.0 h |
| force_exit | 1 | 0.04 | – | 0.11% | 100% | 4.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 355 | -302.76 | -1.85% | 10% |
| 3 h a 1 dia | 903 | 112.79 | 0.26% | 54% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (519): MFE mediano 2.4%, MAE mediano -0.6%, devolução média do melhor ponto 1.4%, captura mediana 0.52.
- Perdedores (739): MAE mediano -2.4%, MFE mediano 0.8%; 104 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 169.83; – do lucro antes de custos.
- Trades < 3 h: 355 (lucro -302.76); reentradas em < 24 h: 839 (lucro -140.67).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -203.57.
- Lucro por ano de fechamento: 2017: 3.5, 2018: -34.5, 2019: -41.7, 2020: -20.3, 2021: -56.6, 2022: -2.7, 2023: -16.3, 2024: -21.4.

## XRP/USDT

Trades: 904; lucro líquido: -95.13.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 366 | -402.19 | – | -2.29% | 0% | 3.1 h |
| block_close_at_high7 | 248 | 260.35 | – | 2.19% | 99% | 6.9 h |
| clock_exit_23utc | 179 | 52.15 | – | 0.60% | 68% | 7.4 h |
| time_exit_12h | 111 | -5.45 | – | -0.10% | 37% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 233 | -176.60 | -1.58% | 15% |
| 3 h a 1 dia | 671 | 81.47 | 0.25% | 56% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (409): MFE mediano 2.4%, MAE mediano -0.5%, devolução média do melhor ponto 1.5%, captura mediana 0.55.
- Perdedores (495): MAE mediano -2.5%, MFE mediano 0.8%; 78 (16%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 129.54; 376% do lucro antes de custos.
- Trades < 3 h: 233 (lucro -176.60); reentradas em < 24 h: 583 (lucro -49.07).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -106.66.
- Lucro por ano de fechamento: 2018: -3.2, 2019: -24.8, 2020: 2.3, 2021: -30.4, 2022: -11.8, 2023: -17.7, 2024: -9.5.

## ADA/USDT

Trades: 1046; lucro líquido: -143.46.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 481 | -520.37 | – | -2.29% | 0% | 3.1 h |
| block_close_at_high7 | 255 | 305.84 | – | 2.52% | 100% | 7.1 h |
| clock_exit_23utc | 198 | 65.85 | – | 0.70% | 67% | 7.1 h |
| time_exit_12h | 112 | 5.23 | – | 0.10% | 45% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 298 | -254.59 | -1.80% | 10% |
| 3 h a 1 dia | 748 | 111.14 | 0.31% | 54% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (437): MFE mediano 3.0%, MAE mediano -0.6%, devolução média do melhor ponto 1.5%, captura mediana 0.54.
- Perdedores (609): MAE mediano -2.5%, MFE mediano 0.9%; 95 (16%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 147.54; 3610% do lucro antes de custos.
- Trades < 3 h: 298 (lucro -254.59); reentradas em < 24 h: 703 (lucro -103.26).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -149.80.
- Lucro por ano de fechamento: 2018: 5.3, 2019: -15.1, 2020: -15.4, 2021: -68.5, 2022: -18.6, 2023: -19.2, 2024: -11.9.

## LTC/USDT

Trades: 1106; lucro líquido: -113.73.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 473 | -509.36 | – | -2.28% | 0% | 3.1 h |
| block_close_at_high7 | 278 | 339.18 | – | 2.60% | 100% | 6.9 h |
| clock_exit_23utc | 227 | 59.67 | – | 0.56% | 65% | 7.4 h |
| time_exit_12h | 128 | -3.21 | – | -0.05% | 40% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 277 | -218.75 | -1.67% | 13% |
| 3 h a 1 dia | 829 | 105.02 | 0.27% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (475): MFE mediano 2.8%, MAE mediano -0.7%, devolução média do melhor ponto 1.4%, captura mediana 0.56.
- Perdedores (631): MAE mediano -2.4%, MFE mediano 0.8%; 88 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 155.79; 370% do lucro antes de custos.
- Trades < 3 h: 277 (lucro -218.75); reentradas em < 24 h: 761 (lucro -76.78).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -119.16.
- Lucro por ano de fechamento: 2018: -28.5, 2019: -30.8, 2020: -15.8, 2021: 20.5, 2022: -3.7, 2023: -34.7, 2024: -20.7.

## LINK/USDT

Trades: 1088; lucro líquido: -134.92.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 551 | -596.93 | – | -2.29% | 0% | 2.7 h |
| block_close_at_high7 | 268 | 391.52 | – | 3.08% | 100% | 6.7 h |
| clock_exit_23utc | 179 | 71.64 | – | 0.84% | 59% | 7.0 h |
| time_exit_12h | 90 | -1.16 | – | -0.04% | 44% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 364 | -291.02 | -1.69% | 10% |
| 3 h a 1 dia | 724 | 156.09 | 0.45% | 52% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (414): MFE mediano 3.5%, MAE mediano -0.7%, devolução média do melhor ponto 1.7%, captura mediana 0.59.
- Perdedores (674): MAE mediano -2.4%, MFE mediano 0.9%; 130 (19%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 153.35; 832% do lucro antes de custos.
- Trades < 3 h: 364 (lucro -291.02); reentradas em < 24 h: 778 (lucro -74.91).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -162.57.
- Lucro por ano de fechamento: 2019: 0.8, 2020: -34.6, 2021: -55.2, 2022: 0.0, 2023: -34.1, 2024: -11.9.

## DOGE/USDT

Trades: 812; lucro líquido: -177.29.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 418 | -432.47 | – | -2.29% | 0% | 2.6 h |
| block_close_at_high7 | 175 | 222.72 | – | 2.83% | 98% | 6.7 h |
| clock_exit_23utc | 147 | 29.92 | – | 0.46% | 59% | 7.1 h |
| time_exit_12h | 72 | 2.53 | – | 0.08% | 46% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 271 | -221.34 | -1.79% | 9% |
| 3 h a 1 dia | 541 | 44.04 | 0.18% | 49% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (291): MFE mediano 2.9%, MAE mediano -0.7%, devolução média do melhor ponto 1.7%, captura mediana 0.55.
- Perdedores (521): MAE mediano -2.6%, MFE mediano 0.9%; 114 (22%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 109.78; – do lucro antes de custos.
- Trades < 3 h: 271 (lucro -221.34); reentradas em < 24 h: 557 (lucro -102.56).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -186.49.
- Lucro por ano de fechamento: 2019: -10.3, 2020: -25.8, 2021: -76.7, 2022: -26.7, 2023: -18.2, 2024: -19.6.

## SOL/USDT

Trades: 788; lucro líquido: -127.70.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 435 | -473.24 | – | -2.29% | 0% | 2.7 h |
| block_close_at_high7 | 174 | 309.34 | – | 3.72% | 99% | 7.0 h |
| clock_exit_23utc | 128 | 29.04 | – | 0.48% | 59% | 6.8 h |
| time_exit_12h | 51 | 7.17 | – | 0.28% | 49% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 278 | -259.02 | -1.95% | 6% |
| 3 h a 1 dia | 510 | 131.32 | 0.53% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (274): MFE mediano 3.7%, MAE mediano -0.7%, devolução média do melhor ponto 1.9%, captura mediana 0.58.
- Perdedores (514): MAE mediano -2.5%, MFE mediano 1.1%; 124 (24%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 111.18; – do lucro antes de custos.
- Trades < 3 h: 278 (lucro -259.02); reentradas em < 24 h: 549 (lucro -68.28).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -140.85.
- Lucro por ano de fechamento: 2020: -9.5, 2021: -39.3, 2022: -31.0, 2023: -34.9, 2024: -13.1.
