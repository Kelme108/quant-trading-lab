# Revisão de trades: H-114 (exploração)

Fonte dos trades: `research/experiments/20261111T225601Z-h-114-exploration-btc-usdt/raw/backtest-result-2026-11-11_23-23-46.zip`; `research/experiments/20261111T225601Z-h-114-exploration-eth-usdt/raw/backtest-result-2026-11-11_23-37-40.zip`; `research/experiments/20261111T225601Z-h-114-exploration-bnb-usdt/raw/backtest-result-2026-11-11_23-47-41.zip`; `research/experiments/20261111T225601Z-h-114-exploration-xrp-usdt/raw/backtest-result-2026-11-12_00-05-08.zip`; `research/experiments/20261111T225601Z-h-114-exploration-ada-usdt/raw/backtest-result-2026-11-12_00-13-47.zip`; `research/experiments/20261111T225601Z-h-114-exploration-ltc-usdt/raw/backtest-result-2026-11-12_00-23-05.zip`; `research/experiments/20261111T225601Z-h-114-exploration-link-usdt/raw/backtest-result-2026-11-12_00-32-22.zip`; `research/experiments/20261111T225601Z-h-114-exploration-doge-usdt/raw/backtest-result-2026-11-12_00-43-34.zip`; `research/experiments/20261111T225601Z-h-114-exploration-sol-usdt/raw/backtest-result-2026-11-12_00-50-19.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 30; lucro líquido: 2039.88.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 28 | -67.48 | -3% | -1.66% | 0% | 35.7 h |
| trailing_stop_loss | 1 | -2.42 | -0% | -1.67% | 0% | 10217.0 h |
| force_exit | 1 | 2109.77 | 103% | 1510.28% | 100% | 47211.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 8 | -18.79 | -1.61% | 0% |
| 3 h a 1 dia | 14 | -34.25 | -1.70% | 0% |
| 1 a 7 dias | 5 | -12.25 | -1.67% | 0% |
| 7 a 30 dias | 1 | -2.18 | -1.53% | 0% |
| > 30 dias | 2 | 2107.36 | 754.31% | 50% |

### Excursões (antes de custos)

- Vencedores (1): MFE mediano 1948.5%, MAE mediano -0.8%, devolução média do melhor ponto 438.2%, captura mediana 0.78.
- Perdedores (29): MAE mediano -1.7%, MFE mediano 1.1%; 9 (31%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 16.05; 1% do lucro antes de custos.
- Trades < 3 h: 8 (lucro -18.79); reentradas em < 24 h: 16 (lucro 2071.34).
- Maior trade = 103% do lucro; top 5 = 103%; top 10 = 103%; lucro sem o melhor = -69.89.
- Lucro por ano de fechamento: 2017: -34.3, 2018: -18.6, 2019: -17.1, 2024: 2109.8.

## ETH/USDT

Trades: 94; lucro líquido: 2393.32.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 92 | -190.34 | -8% | -1.53% | 0% | 186.2 h |
| trailing_stop_loss | 1 | -2.53 | -0% | -1.99% | 0% | 893.0 h |
| force_exit | 1 | 2586.19 | 108% | 2133.02% | 100% | 37313.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 25 | -52.22 | -1.54% | 0% |
| 3 h a 1 dia | 52 | -107.33 | -1.53% | 0% |
| 1 a 7 dias | 10 | -20.97 | -1.52% | 0% |
| 7 a 30 dias | 2 | -4.79 | -1.68% | 0% |
| > 30 dias | 5 | 2578.62 | 425.43% | 20% |

### Excursões (antes de custos)

- Vencedores (1): MFE mediano 3463.4%, MAE mediano -0.4%, devolução média do melhor ponto 1330.4%, captura mediana 0.62.
- Perdedores (93): MAE mediano -1.5%, MFE mediano 1.3%; 33 (35%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 41.64; 2% do lucro antes de custos.
- Trades < 3 h: 25 (lucro -52.22); reentradas em < 24 h: 58 (lucro -120.60).
- Maior trade = 108% do lucro; top 5 = 108%; top 10 = 107%; lucro sem o melhor = -192.87.
- Lucro por ano de fechamento: 2017: -77.7, 2018: -76.3, 2019: -12.3, 2020: -26.6, 2024: 2586.2.

## BNB/USDT

Trades: 89; lucro líquido: 15381.62.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 84 | -2302.92 | -15% | -1.53% | 0% | 109.6 h |
| trailing_stop_loss | 3 | -110.86 | -1% | -1.64% | 0% | 2894.5 h |
| roi | 1 | 14530.23 | 94% | 10000.00% | 100% | 28182.8 h |
| force_exit | 1 | 3265.16 | 21% | 165.71% | 100% | 6712.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 28 | -756.28 | -1.60% | 0% |
| 3 h a 1 dia | 41 | -1115.90 | -1.50% | 0% |
| 1 a 7 dias | 11 | -319.20 | -1.48% | 0% |
| 7 a 30 dias | 3 | -94.10 | -1.47% | 0% |
| > 30 dias | 6 | 17667.10 | 1693.29% | 33% |

### Excursões (antes de custos)

- Vencedores (2): MFE mediano 5168.5%, MAE mediano -0.9%, devolução média do melhor ponto 85.7%, captura mediana 0.84.
- Perdedores (87): MAE mediano -1.5%, MFE mediano 1.1%; 26 (30%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 508.26; 3% do lucro antes de custos.
- Trades < 3 h: 28 (lucro -756.28); reentradas em < 24 h: 55 (lucro 16309.43).
- Maior trade = 94% do lucro; top 5 = 116%; top 10 = 116%; lucro sem o melhor = 851.39.
- Lucro por ano de fechamento: 2017: -32.8, 2021: 13301.2, 2022: -611.8, 2023: -540.2, 2024: 3265.2.

## XRP/USDT

Trades: 117; lucro líquido: -1.83.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 116 | -213.47 | – | -1.38% | 0% | 70.2 h |
| force_exit | 1 | 211.64 | – | 179.13% | 100% | 37537.5 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 33 | -59.78 | -1.35% | 0% |
| 3 h a 1 dia | 51 | -94.94 | -1.39% | 0% |
| 1 a 7 dias | 24 | -44.74 | -1.40% | 0% |
| 7 a 30 dias | 5 | -8.96 | -1.34% | 0% |
| > 30 dias | 4 | 206.59 | 43.81% | 25% |

### Excursões (antes de custos)

- Vencedores (1): MFE mediano 1139.1%, MAE mediano -1.6%, devolução média do melhor ponto 960.0%, captura mediana 0.16.
- Perdedores (116): MAE mediano -1.4%, MFE mediano 0.8%; 38 (33%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 46.76; 104% do lucro antes de custos.
- Trades < 3 h: 33 (lucro -59.78); reentradas em < 24 h: 61 (lucro -112.48).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -213.47.
- Lucro por ano de fechamento: 2018: -72.2, 2019: -134.0, 2020: -7.2, 2024: 211.6.

## ADA/USDT

Trades: 151; lucro líquido: 11383.05.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 143 | -3151.94 | -28% | -1.47% | 0% | 64.6 h |
| trailing_stop_loss | 6 | -168.63 | -1% | -1.69% | 0% | 2132.8 h |
| roi | 1 | 13827.49 | 121% | 10000.01% | 100% | 12494.2 h |
| force_exit | 1 | 876.13 | 8% | 50.68% | 100% | 6212.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 48 | -1129.94 | -1.42% | 0% |
| 3 h a 1 dia | 64 | -1400.74 | -1.51% | 0% |
| 1 a 7 dias | 23 | -551.28 | -1.49% | 0% |
| 7 a 30 dias | 10 | -150.43 | -1.52% | 0% |
| > 30 dias | 6 | 14615.44 | 1674.09% | 33% |

### Excursões (antes de custos)

- Vencedores (2): MFE mediano 5154.0%, MAE mediano -0.3%, devolução média do melhor ponto 128.7%, captura mediana 0.61.
- Perdedores (149): MAE mediano -1.4%, MFE mediano 1.1%; 52 (35%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 711.49; 6% do lucro antes de custos.
- Trades < 3 h: 48 (lucro -1129.94); reentradas em < 24 h: 82 (lucro -1884.18).
- Maior trade = 121% do lucro; top 5 = 129%; top 10 = 129%; lucro sem o melhor = -2444.44.
- Lucro por ano de fechamento: 2018: -65.9, 2020: -13.7, 2021: 12863.8, 2022: -1624.7, 2023: -652.7, 2024: 876.1.

## LTC/USDT

Trades: 74; lucro líquido: -46.17.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 71 | -146.28 | – | -1.49% | 0% | 180.2 h |
| trailing_stop_loss | 2 | -5.41 | – | -1.95% | 0% | 581.9 h |
| force_exit | 1 | 105.51 | – | 82.80% | 100% | 37547.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 22 | -43.33 | -1.41% | 0% |
| 3 h a 1 dia | 38 | -79.21 | -1.50% | 0% |
| 1 a 7 dias | 7 | -14.58 | -1.52% | 0% |
| 7 a 30 dias | 4 | -10.51 | -1.91% | 0% |
| > 30 dias | 3 | 101.45 | 26.61% | 33% |

### Excursões (antes de custos)

- Vencedores (1): MFE mediano 1032.2%, MAE mediano -1.5%, devolução média do melhor ponto 949.4%, captura mediana 0.08.
- Perdedores (73): MAE mediano -1.5%, MFE mediano 1.2%; 25 (34%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 30.57; – do lucro antes de custos.
- Trades < 3 h: 22 (lucro -43.33); reentradas em < 24 h: 41 (lucro 27.88).
- Maior trade = – do lucro; top 5 = –; top 10 = –; lucro sem o melhor = -151.69.
- Lucro por ano de fechamento: 2018: -146.1, 2020: -5.6, 2024: 105.5.

## LINK/USDT

Trades: 18; lucro líquido: 637.14.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 17 | -38.01 | -6% | -1.52% | 0% | 553.0 h |
| force_exit | 1 | 675.15 | 106% | 467.25% | 100% | 37224.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 5 | -9.47 | -1.29% | 0% |
| 3 h a 1 dia | 7 | -17.52 | -1.69% | 0% |
| 1 a 7 dias | 3 | -7.23 | -1.64% | 0% |
| 7 a 30 dias | 1 | -1.90 | -1.28% | 0% |
| > 30 dias | 2 | 673.25 | 232.98% | 50% |

### Excursões (antes de custos)

- Vencedores (1): MFE mediano 2233.8%, MAE mediano -0.5%, devolução média do melhor ponto 1766.5%, captura mediana 0.21.
- Perdedores (17): MAE mediano -1.6%, MFE mediano 3.0%; 9 (53%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 8.90; 1% do lucro antes de custos.
- Trades < 3 h: 5 (lucro -9.47); reentradas em < 24 h: 10 (lucro 656.24).
- Maior trade = 106% do lucro; top 5 = 105%; top 10 = 103%; lucro sem o melhor = -38.01.
- Lucro por ano de fechamento: 2019: -17.1, 2020: -20.9, 2024: 675.1.

## DOGE/USDT

Trades: 208; lucro líquido: 10532.08.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 201 | -3423.79 | -33% | -1.42% | 0% | 49.1 h |
| trailing_stop_loss | 5 | -171.44 | -2% | -1.78% | 0% | 842.4 h |
| roi | 1 | 12881.49 | 122% | 10000.00% | 100% | 9048.2 h |
| force_exit | 1 | 1245.81 | 12% | 80.62% | 100% | 6211.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 68 | -1152.62 | -1.42% | 0% |
| 3 h a 1 dia | 84 | -1377.96 | -1.43% | 0% |
| 1 a 7 dias | 44 | -849.82 | -1.46% | 0% |
| 7 a 30 dias | 6 | -136.85 | -1.45% | 0% |
| > 30 dias | 6 | 14049.33 | 1679.22% | 33% |

### Excursões (antes de custos)

- Vencedores (2): MFE mediano 5235.9%, MAE mediano -0.5%, devolução média do melhor ponto 195.5%, captura mediana 0.63.
- Perdedores (206): MAE mediano -1.4%, MFE mediano 1.0%; 75 (36%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 767.07; 7% do lucro antes de custos.
- Trades < 3 h: 68 (lucro -1152.62); reentradas em < 24 h: 124 (lucro 10836.09).
- Maior trade = 122% do lucro; top 5 = 134%; top 10 = 134%; lucro sem o melhor = -2349.41.
- Lucro por ano de fechamento: 2019: -115.3, 2020: -27.2, 2021: 12232.1, 2022: -1491.0, 2023: -1312.4, 2024: 1245.8.

## SOL/USDT

Trades: 47; lucro líquido: 4436.78.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| stop_loss | 45 | -118.74 | -3% | -1.87% | 0% | 14.7 h |
| trailing_stop_loss | 1 | -2.65 | -0% | -1.78% | 0% | 157.2 h |
| force_exit | 1 | 4558.18 | 103% | 3453.54% | 100% | 30059.8 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 23 | -61.06 | -1.87% | 0% |
| 3 h a 1 dia | 16 | -42.23 | -1.88% | 0% |
| 1 a 7 dias | 6 | -15.47 | -1.85% | 0% |
| 7 a 30 dias | 1 | -2.64 | -1.79% | 0% |
| > 30 dias | 1 | 4558.18 | 3453.54% | 100% |

### Excursões (antes de custos)

- Vencedores (1): MFE mediano 6893.9%, MAE mediano -0.4%, devolução média do melhor ponto 3440.3%, captura mediana 0.50.
- Perdedores (46): MAE mediano -2.0%, MFE mediano 1.7%; 22 (48%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 26.48; 1% do lucro antes de custos.
- Trades < 3 h: 23 (lucro -61.06); reentradas em < 24 h: 27 (lucro 4488.31).
- Maior trade = 103% do lucro; top 5 = 103%; top 10 = 102%; lucro sem o melhor = -121.39.
- Lucro por ano de fechamento: 2020: -90.3, 2021: -31.1, 2024: 4558.2.
