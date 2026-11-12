# Revisão de trades: H-123 (exploração)

Fonte dos trades: `research/experiments/20261112T205114Z-h-123-exploration-btc-usdt/raw/backtest-result-2026-11-12_21-14-22.zip`; `research/experiments/20261112T205114Z-h-123-exploration-eth-usdt/raw/backtest-result-2026-11-12_21-23-18.zip`; `research/experiments/20261112T205114Z-h-123-exploration-bnb-usdt/raw/backtest-result-2026-11-12_21-35-00.zip`; `research/experiments/20261112T205114Z-h-123-exploration-xrp-usdt/raw/backtest-result-2026-11-12_21-48-22.zip`; `research/experiments/20261112T205114Z-h-123-exploration-ada-usdt/raw/backtest-result-2026-11-12_22-03-40.zip`; `research/experiments/20261112T205114Z-h-123-exploration-ltc-usdt/raw/backtest-result-2026-11-12_22-21-04.zip`; `research/experiments/20261112T205114Z-h-123-exploration-link-usdt/raw/backtest-result-2026-11-12_22-39-55.zip`; `research/experiments/20261112T205114Z-h-123-exploration-doge-usdt/raw/backtest-result-2026-11-12_22-54-03.zip`; `research/experiments/20261112T205114Z-h-123-exploration-sol-usdt/raw/backtest-result-2026-11-12_23-08-34.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 451; lucro líquido: -156.27.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| block_end_loser | 181 | -125.12 | – | -0.75% | 0% | 2.1 h |
| take_profit | 138 | 148.72 | – | 1.17% | 99% | 3.4 h |
| stop_loss | 97 | -171.49 | – | -1.91% | 0% | 2.9 h |
| time_exit_12h | 35 | -8.39 | – | -0.28% | 34% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 323 | -164.49 | -0.55% | 23% |
| 3 h a 1 dia | 128 | 8.21 | 0.06% | 58% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (148): MFE mediano 1.8%, MAE mediano -0.4%, devolução média do melhor ponto 0.9%, captura mediana 0.57.
- Perdedores (303): MAE mediano -1.2%, MFE mediano 0.4%; 1 (0%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 123.55; – do lucro antes de custos.
- Trades < 3 h: 323 (lucro -164.49); reentradas em < 24 h: 58 (lucro -25.36).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -162.19.
- Lucro por ano de fechamento: 2017: -4.0, 2018: -36.9, 2019: -21.3, 2020: -25.0, 2021: -42.1, 2022: -14.3, 2023: -7.3, 2024: -5.3.

## ETH/USDT

Trades: 574; lucro líquido: -160.45.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| take_profit | 210 | 234.10 | – | 1.25% | 99% | 3.1 h |
| block_end_loser | 201 | -158.71 | – | -0.88% | 0% | 2.1 h |
| stop_loss | 128 | -232.00 | – | -2.00% | 0% | 2.6 h |
| time_exit_12h | 35 | -3.84 | – | -0.13% | 49% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 422 | -186.71 | -0.48% | 31% |
| 3 h a 1 dia | 152 | 26.26 | 0.20% | 62% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (224): MFE mediano 1.9%, MAE mediano -0.4%, devolução média do melhor ponto 1.0%, captura mediana 0.59.
- Perdedores (350): MAE mediano -1.3%, MFE mediano 0.4%; 1 (0%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 153.39; – do lucro antes de custos.
- Trades < 3 h: 422 (lucro -186.71); reentradas em < 24 h: 100 (lucro -38.99).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -164.53.
- Lucro por ano de fechamento: 2017: -21.7, 2018: -57.4, 2019: -14.6, 2020: -14.2, 2021: -27.2, 2022: -25.7, 2023: -0.3, 2024: 0.8.

## BNB/USDT

Trades: 550; lucro líquido: -176.18.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| take_profit | 202 | 217.16 | – | 1.22% | 99% | 2.8 h |
| block_end_loser | 185 | -146.98 | – | -0.89% | 0% | 2.0 h |
| stop_loss | 136 | -246.85 | – | -2.02% | 0% | 2.8 h |
| time_exit_12h | 26 | 0.82 | – | 0.04% | 65% | 12.0 h |
| force_exit | 1 | -0.33 | – | -0.41% | 0% | 0.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 403 | -177.79 | -0.49% | 31% |
| 3 h a 1 dia | 147 | 1.61 | 0.02% | 63% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (216): MFE mediano 1.9%, MAE mediano -0.4%, devolução média do melhor ponto 0.9%, captura mediana 0.60.
- Perdedores (334): MAE mediano -1.3%, MFE mediano 0.4%; 1 (0%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 144.94; – do lucro antes de custos.
- Trades < 3 h: 403 (lucro -177.79); reentradas em < 24 h: 87 (lucro -19.04).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -179.04.
- Lucro por ano de fechamento: 2017: -5.9, 2018: -62.3, 2019: -39.8, 2020: -13.1, 2021: -33.7, 2022: -13.1, 2023: -8.2, 2024: -0.2.

## XRP/USDT

Trades: 520; lucro líquido: -133.44.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| block_end_loser | 185 | -142.54 | – | -0.82% | 0% | 2.2 h |
| take_profit | 173 | 221.07 | – | 1.37% | 97% | 2.8 h |
| stop_loss | 127 | -205.76 | – | -1.74% | 0% | 3.0 h |
| time_exit_12h | 35 | -6.20 | – | -0.19% | 43% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 384 | -131.68 | -0.36% | 29% |
| 3 h a 1 dia | 136 | -1.76 | -0.02% | 52% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (183): MFE mediano 2.1%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.58.
- Perdedores (337): MAE mediano -1.2%, MFE mediano 0.4%; 2 (1%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 145.29; 1226% do lucro antes de custos.
- Trades < 3 h: 384 (lucro -131.68); reentradas em < 24 h: 88 (lucro -33.30).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -137.71.
- Lucro por ano de fechamento: 2018: -1.0, 2019: -30.0, 2020: -17.6, 2021: -26.5, 2022: -32.4, 2023: -21.8, 2024: -4.2.

## ADA/USDT

Trades: 587; lucro líquido: -128.06.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| take_profit | 239 | 284.01 | – | 1.28% | 97% | 2.5 h |
| block_end_loser | 214 | -188.21 | – | -0.94% | 0% | 2.1 h |
| stop_loss | 120 | -222.44 | – | -1.99% | 0% | 2.3 h |
| time_exit_12h | 14 | -1.41 | – | -0.10% | 36% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 474 | -146.31 | -0.33% | 35% |
| 3 h a 1 dia | 113 | 18.25 | 0.18% | 65% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (238): MFE mediano 2.1%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.58.
- Perdedores (349): MAE mediano -1.3%, MFE mediano 0.4%; 2 (1%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 163.55; 461% do lucro antes de custos.
- Trades < 3 h: 474 (lucro -146.31); reentradas em < 24 h: 93 (lucro -38.24).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -132.74.
- Lucro por ano de fechamento: 2018: -14.9, 2019: -33.9, 2020: -7.8, 2021: -36.9, 2022: -12.8, 2023: -9.3, 2024: -12.4.

## LTC/USDT

Trades: 559; lucro líquido: -147.81.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| take_profit | 220 | 242.18 | – | 1.22% | 96% | 2.7 h |
| block_end_loser | 174 | -147.66 | – | -0.93% | 0% | 2.1 h |
| stop_loss | 135 | -231.65 | – | -1.89% | 0% | 2.6 h |
| time_exit_12h | 29 | -9.02 | – | -0.34% | 28% | 12.0 h |
| trailing_stop_loss | 1 | -1.66 | – | -1.70% | 0% | 1.2 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 420 | -160.48 | -0.41% | 34% |
| 3 h a 1 dia | 139 | 12.66 | 0.11% | 57% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (220): MFE mediano 2.0%, MAE mediano -0.4%, devolução média do melhor ponto 1.0%, captura mediana 0.59.
- Perdedores (339): MAE mediano -1.4%, MFE mediano 0.4%; 2 (1%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 151.49; 4124% do lucro antes de custos.
- Trades < 3 h: 420 (lucro -160.48); reentradas em < 24 h: 77 (lucro -21.76).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -153.25.
- Lucro por ano de fechamento: 2018: -35.7, 2019: -46.7, 2020: 7.4, 2021: -53.6, 2022: -5.6, 2023: -15.7, 2024: 2.1.

## LINK/USDT

Trades: 549; lucro líquido: -161.98.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| take_profit | 234 | 259.60 | – | 1.21% | 97% | 2.4 h |
| block_end_loser | 179 | -184.34 | – | -1.11% | 0% | 2.2 h |
| stop_loss | 129 | -234.24 | – | -1.99% | 0% | 2.7 h |
| time_exit_12h | 7 | -2.99 | – | -0.48% | 14% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 445 | -169.04 | -0.41% | 37% |
| 3 h a 1 dia | 104 | 7.06 | 0.06% | 60% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (228): MFE mediano 2.0%, MAE mediano -0.5%, devolução média do melhor ponto 1.0%, captura mediana 0.58.
- Perdedores (321): MAE mediano -1.6%, MFE mediano 0.5%; 6 (2%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 150.22; – do lucro antes de custos.
- Trades < 3 h: 445 (lucro -169.04); reentradas em < 24 h: 97 (lucro -26.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -168.40.
- Lucro por ano de fechamento: 2019: -45.8, 2020: -31.4, 2021: -20.3, 2022: -24.1, 2023: -22.7, 2024: -17.7.

## DOGE/USDT

Trades: 440; lucro líquido: -134.46.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| take_profit | 170 | 187.71 | – | 1.22% | 96% | 2.7 h |
| block_end_loser | 135 | -111.83 | – | -0.89% | 0% | 2.2 h |
| stop_loss | 111 | -203.23 | – | -2.00% | 0% | 3.2 h |
| time_exit_12h | 23 | -5.90 | – | -0.27% | 35% | 12.0 h |
| trailing_stop_loss | 1 | -1.21 | – | -1.40% | 0% | 4.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 321 | -125.38 | -0.42% | 34% |
| 3 h a 1 dia | 119 | -9.08 | -0.08% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (172): MFE mediano 1.9%, MAE mediano -0.4%, devolução média do melhor ponto 1.1%, captura mediana 0.55.
- Perdedores (268): MAE mediano -1.5%, MFE mediano 0.5%; 3 (1%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 120.58; – do lucro antes de custos.
- Trades < 3 h: 321 (lucro -125.38); reentradas em < 24 h: 81 (lucro -31.64).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -139.97.
- Lucro por ano de fechamento: 2019: -22.5, 2020: -31.8, 2021: -48.9, 2022: -22.2, 2023: 5.9, 2024: -14.9.

## SOL/USDT

Trades: 385; lucro líquido: -80.98.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| take_profit | 171 | 219.44 | – | 1.30% | 96% | 1.9 h |
| block_end_loser | 112 | -110.86 | – | -1.01% | 0% | 2.1 h |
| stop_loss | 96 | -189.72 | – | -2.02% | 0% | 2.6 h |
| time_exit_12h | 6 | 0.16 | – | 0.04% | 33% | 12.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 318 | -93.54 | -0.30% | 40% |
| 3 h a 1 dia | 67 | 12.56 | 0.18% | 61% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (167): MFE mediano 2.1%, MAE mediano -0.5%, devolução média do melhor ponto 1.1%, captura mediana 0.61.
- Perdedores (218): MAE mediano -1.5%, MFE mediano 0.5%; 3 (1%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 112.67; 356% do lucro antes de custos.
- Trades < 3 h: 318 (lucro -93.54); reentradas em < 24 h: 62 (lucro -18.00).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -85.24.
- Lucro por ano de fechamento: 2020: 14.1, 2021: -16.4, 2022: -27.8, 2023: -42.1, 2024: -8.7.
