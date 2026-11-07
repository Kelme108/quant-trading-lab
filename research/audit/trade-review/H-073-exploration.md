# Revisão de trades: H-073 (exploração)

Fonte dos trades: `research/experiments/20261107T194919Z-h-073-exploration-btc-usdt/raw/backtest-result-2026-11-07_19-59-21.zip`; `research/experiments/20261107T194919Z-h-073-exploration-eth-usdt/raw/backtest-result-2026-11-07_20-02-29.zip`; `research/experiments/20261107T194919Z-h-073-exploration-bnb-usdt/raw/backtest-result-2026-11-07_20-05-33.zip`; `research/experiments/20261107T194919Z-h-073-exploration-xrp-usdt/raw/backtest-result-2026-11-07_20-08-32.zip`; `research/experiments/20261107T194919Z-h-073-exploration-ada-usdt/raw/backtest-result-2026-11-07_20-11-27.zip`; `research/experiments/20261107T194919Z-h-073-exploration-ltc-usdt/raw/backtest-result-2026-11-07_20-14-23.zip`; `research/experiments/20261107T194919Z-h-073-exploration-link-usdt/raw/backtest-result-2026-11-07_20-17-41.zip`; `research/experiments/20261107T194919Z-h-073-exploration-doge-usdt/raw/backtest-result-2026-11-07_20-20-29.zip`; `research/experiments/20261107T194919Z-h-073-exploration-sol-usdt/raw/backtest-result-2026-11-07_20-23-15.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 932; lucro líquido: -10.71.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| breadth_collapse | 577 | -24.58 | – | -0.46% | 24% | 11.8 h |
| time_24h | 229 | 53.33 | – | 2.49% | 80% | 24.0 h |
| stop_loss | 126 | -39.45 | – | -3.29% | 0% | 7.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 40 | -12.56 | -3.29% | 0% |
| 3 h a 1 dia | 663 | -51.47 | -0.83% | 21% |
| 1 a 7 dias | 229 | 53.33 | 2.49% | 80% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (324): MFE mediano 3.7%, MAE mediano -0.6%, devolução média do melhor ponto 2.0%, captura mediana 0.49.
- Perdedores (608): MAE mediano -1.7%, MFE mediano 0.7%; 84 (14%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 26.05; 170% do lucro antes de custos.
- Trades < 3 h: 40 (lucro -12.56); reentradas em < 24 h: 336 (lucro -4.19).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -12.87.
- Lucro por ano de fechamento: 2017: 0.7, 2018: -5.1, 2019: -0.8, 2020: 3.2, 2021: -5.4, 2022: -4.2, 2023: 1.3, 2024: -0.4.

## ETH/USDT

Trades: 956; lucro líquido: -7.90.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| breadth_collapse | 529 | -21.71 | – | -0.43% | 29% | 12.1 h |
| time_24h | 230 | 76.52 | – | 3.47% | 85% | 24.0 h |
| stop_loss | 197 | -62.70 | – | -3.29% | 0% | 5.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 71 | -22.85 | -3.29% | 0% |
| 3 h a 1 dia | 654 | -61.25 | -0.98% | 23% |
| 1 a 7 dias | 231 | 76.20 | 3.44% | 85% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (348): MFE mediano 4.6%, MAE mediano -0.7%, devolução média do melhor ponto 2.5%, captura mediana 0.48.
- Perdedores (608): MAE mediano -2.4%, MFE mediano 0.9%; 116 (19%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 27.42; 140% do lucro antes de custos.
- Trades < 3 h: 71 (lucro -22.85); reentradas em < 24 h: 353 (lucro -4.21).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -10.40.
- Lucro por ano de fechamento: 2017: 1.6, 2018: -8.3, 2019: -1.9, 2020: 5.7, 2021: 1.1, 2022: -3.5, 2023: -1.0, 2024: -1.6.

## BNB/USDT

Trades: 896; lucro líquido: -1.92.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| breadth_collapse | 512 | -12.39 | – | -0.24% | 30% | 12.1 h |
| time_24h | 209 | 69.62 | – | 3.27% | 82% | 24.0 h |
| stop_loss | 175 | -59.15 | – | -3.29% | 0% | 5.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 58 | -19.62 | -3.29% | 0% |
| 3 h a 1 dia | 629 | -51.92 | -0.80% | 25% |
| 1 a 7 dias | 209 | 69.62 | 3.27% | 82% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (327): MFE mediano 4.3%, MAE mediano -0.7%, devolução média do melhor ponto 2.6%, captura mediana 0.47.
- Perdedores (569): MAE mediano -2.3%, MFE mediano 0.9%; 108 (19%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 27.42; 108% do lucro antes de custos.
- Trades < 3 h: 58 (lucro -19.62); reentradas em < 24 h: 329 (lucro -4.18).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -5.28.
- Lucro por ano de fechamento: 2017: 0.7, 2018: -1.5, 2019: 3.6, 2020: 0.2, 2021: 3.4, 2022: -3.6, 2023: -4.7, 2024: -0.0.

## XRP/USDT

Trades: 832; lucro líquido: -25.52.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| breadth_collapse | 470 | -17.92 | – | -0.44% | 25% | 12.1 h |
| stop_loss | 189 | -53.45 | – | -3.29% | 0% | 6.2 h |
| time_24h | 173 | 45.84 | – | 3.10% | 79% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 68 | -19.45 | -3.29% | 0% |
| 3 h a 1 dia | 591 | -51.91 | -1.02% | 20% |
| 1 a 7 dias | 173 | 45.84 | 3.10% | 79% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (256): MFE mediano 4.6%, MAE mediano -0.8%, devolução média do melhor ponto 3.1%, captura mediana 0.43.
- Perdedores (576): MAE mediano -2.4%, MFE mediano 0.8%; 118 (20%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 21.20; – do lucro antes de custos.
- Trades < 3 h: 68 (lucro -19.45); reentradas em < 24 h: 302 (lucro -12.79).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -27.77.
- Lucro por ano de fechamento: 2018: -4.9, 2019: -7.4, 2020: 1.2, 2021: -8.0, 2022: -0.3, 2023: -3.8, 2024: -2.4.

## ADA/USDT

Trades: 834; lucro líquido: -20.20.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| breadth_collapse | 421 | -17.79 | – | -0.48% | 25% | 12.2 h |
| stop_loss | 224 | -67.01 | – | -3.28% | 0% | 6.4 h |
| time_24h | 189 | 64.60 | – | 3.79% | 81% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 79 | -24.00 | -3.28% | 0% |
| 3 h a 1 dia | 566 | -60.80 | -1.20% | 19% |
| 1 a 7 dias | 189 | 64.60 | 3.79% | 81% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (260): MFE mediano 5.6%, MAE mediano -0.8%, devolução média do melhor ponto 3.1%, captura mediana 0.46.
- Perdedores (574): MAE mediano -2.8%, MFE mediano 1.1%; 156 (27%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 22.42; 1011% do lucro antes de custos.
- Trades < 3 h: 79 (lucro -24.00); reentradas em < 24 h: 282 (lucro -9.40).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -22.14.
- Lucro por ano de fechamento: 2018: -5.3, 2019: -5.2, 2020: 7.4, 2021: -7.6, 2022: -5.0, 2023: -2.2, 2024: -2.3.

## LTC/USDT

Trades: 885; lucro líquido: -20.15.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| breadth_collapse | 462 | -15.99 | – | -0.38% | 29% | 12.4 h |
| stop_loss | 224 | -68.50 | – | -3.28% | 0% | 5.9 h |
| time_24h | 199 | 64.34 | – | 3.47% | 87% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 78 | -24.02 | -3.28% | 0% |
| 3 h a 1 dia | 608 | -60.47 | -1.08% | 22% |
| 1 a 7 dias | 199 | 64.34 | 3.47% | 87% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (308): MFE mediano 4.6%, MAE mediano -0.8%, devolução média do melhor ponto 2.8%, captura mediana 0.49.
- Perdedores (577): MAE mediano -2.7%, MFE mediano 0.9%; 119 (21%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 24.42; 572% do lucro antes de custos.
- Trades < 3 h: 78 (lucro -24.02); reentradas em < 24 h: 328 (lucro -11.99).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -22.99.
- Lucro por ano de fechamento: 2017: -0.3, 2018: -3.5, 2019: -0.7, 2020: 1.2, 2021: -5.2, 2022: -5.0, 2023: -4.9, 2024: -1.9.

## LINK/USDT

Trades: 733; lucro líquido: 4.20.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| breadth_collapse | 353 | 7.32 | 174% | 0.19% | 34% | 12.3 h |
| stop_loss | 211 | -75.91 | -1806% | -3.28% | 0% | 6.0 h |
| time_24h | 169 | 72.79 | 1732% | 3.96% | 86% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 76 | -27.46 | -3.28% | 0% |
| 3 h a 1 dia | 488 | -41.13 | -0.77% | 25% |
| 1 a 7 dias | 169 | 72.79 | 3.96% | 86% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (266): MFE mediano 5.9%, MAE mediano -0.8%, devolução média do melhor ponto 3.2%, captura mediana 0.51.
- Perdedores (467): MAE mediano -3.0%, MFE mediano 1.2%; 140 (30%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 23.80; 85% do lucro antes de custos.
- Trades < 3 h: 76 (lucro -27.46); reentradas em < 24 h: 265 (lucro -9.78).
- Maior trade = 67% do lucro; top 5 = 246%; top 10 = 431%; lucro sem o melhor = 1.39.
- Lucro por ano de fechamento: 2019: 3.6, 2020: 14.1, 2021: -5.0, 2022: -8.6, 2023: 0.5, 2024: -0.3.

## DOGE/USDT

Trades: 660; lucro líquido: 85.43.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| breadth_collapse | 364 | -18.31 | -21% | -0.35% | 27% | 12.3 h |
| stop_loss | 149 | -90.54 | -106% | -3.28% | 0% | 5.2 h |
| time_24h | 147 | 194.28 | 227% | 10.37% | 83% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 60 | -37.10 | -3.28% | 0% |
| 3 h a 1 dia | 453 | -71.75 | -0.93% | 22% |
| 1 a 7 dias | 147 | 194.28 | 10.37% | 83% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (221): MFE mediano 4.6%, MAE mediano -0.8%, devolução média do melhor ponto 3.8%, captura mediana 0.41.
- Perdedores (439): MAE mediano -2.5%, MFE mediano 0.9%; 88 (20%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 34.05; 28% do lucro antes de custos.
- Trades < 3 h: 60 (lucro -37.10); reentradas em < 24 h: 233 (lucro -9.94).
- Maior trade = 119% do lucro; top 5 = 148%; top 10 = 168%; lucro sem o melhor = -16.54.
- Lucro por ano de fechamento: 2019: -0.9, 2020: 1.2, 2021: 103.0, 2022: -9.7, 2023: -7.8, 2024: -0.4.

## SOL/USDT

Trades: 555; lucro líquido: -7.34.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| breadth_collapse | 234 | 13.60 | – | 0.59% | 43% | 12.3 h |
| stop_loss | 222 | -68.99 | – | -3.28% | 0% | 5.3 h |
| time_24h | 99 | 48.05 | – | 5.24% | 85% | 24.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 81 | -25.25 | -3.28% | 0% |
| 3 h a 1 dia | 375 | -30.14 | -0.86% | 27% |
| 1 a 7 dias | 99 | 48.05 | 5.24% | 85% |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (185): MFE mediano 7.3%, MAE mediano -0.9%, devolução média do melhor ponto 4.1%, captura mediana 0.52.
- Perdedores (370): MAE mediano -3.2%, MFE mediano 1.1%; 109 (29%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 15.54; 190% do lucro antes de custos.
- Trades < 3 h: 81 (lucro -25.25); reentradas em < 24 h: 188 (lucro -3.37).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -10.35.
- Lucro por ano de fechamento: 2020: -7.5, 2021: 1.0, 2022: -5.2, 2023: 2.9, 2024: 1.5.
