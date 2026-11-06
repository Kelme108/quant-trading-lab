# Revisão de trades: H-043 (exploração)

Fonte dos trades: `research/experiments/20261106T142459Z-h-043-exploration-btc-usdt/raw/backtest-result-2026-11-06_14-27-52.zip`; `research/experiments/20261106T142459Z-h-043-exploration-eth-usdt/raw/backtest-result-2026-11-06_14-30-29.zip`; `research/experiments/20261106T142459Z-h-043-exploration-bnb-usdt/raw/backtest-result-2026-11-06_14-33-10.zip`. Janela: exploração. Cenário de custo: base.

## BTC/USDT

Trades: 249; lucro líquido: 26.67.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 226 | 67.68 | 254% | 0.87% | 55% | 12.7 h |
| stop_loss | 17 | -31.97 | -120% | -5.33% | 0% | 8.6 h |
| below_open_minus_half_range | 6 | -9.04 | -34% | -4.09% | 0% | 9.0 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 4 | -6.45 | -4.73% | 0% |
| 3 h a 1 dia | 245 | 33.12 | 0.41% | 51% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (125): MFE mediano 3.3%, MAE mediano -0.7%, devolução média do melhor ponto 1.8%, captura mediana 0.52.
- Perdedores (124): MAE mediano -2.2%, MFE mediano 0.9%; 19 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 31.39; 54% do lucro antes de custos.
- Trades < 3 h: 4 (lucro -6.45); reentradas em < 24 h: 41 (lucro 5.73).
- Maior trade = 12% do lucro; top 5 = 54%; top 10 = 100%; lucro sem o melhor = 23.38.
- Lucro por ano de fechamento: 2017: 4.1, 2018: 5.5, 2019: 4.9, 2020: 14.9, 2021: 0.8, 2022: -8.1, 2023: 1.0, 2024: 3.6.

## ETH/USDT

Trades: 262; lucro líquido: 33.82.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 230 | 94.54 | 280% | 1.17% | 60% | 12.6 h |
| stop_loss | 29 | -56.16 | -166% | -5.33% | 0% | 6.1 h |
| below_open_minus_half_range | 3 | -4.56 | -13% | -3.92% | 0% | 9.3 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 7 | -11.74 | -5.33% | 0% |
| 3 h a 1 dia | 255 | 45.56 | 0.55% | 54% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (138): MFE mediano 4.1%, MAE mediano -0.8%, devolução média do melhor ponto 2.2%, captura mediana 0.54.
- Perdedores (124): MAE mediano -2.9%, MFE mediano 1.1%; 26 (21%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 34.36; 50% do lucro antes de custos.
- Trades < 3 h: 7 (lucro -11.74); reentradas em < 24 h: 36 (lucro 12.00).
- Maior trade = 22% do lucro; top 5 = 68%; top 10 = 107%; lucro sem o melhor = 26.27.
- Lucro por ano de fechamento: 2017: -2.2, 2018: 1.1, 2019: 0.2, 2020: 31.7, 2021: 14.5, 2022: -4.2, 2023: -4.4, 2024: -2.8.

## BNB/USDT

Trades: 292; lucro líquido: 63.27.

### Por motivo de saída

| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |
|---|--:|--:|--:|--:|--:|--:|
| midnight_flat | 247 | 167.13 | 264% | 1.63% | 61% | 13.1 h |
| stop_loss | 38 | -92.19 | -146% | -5.33% | 0% | 6.5 h |
| below_open_minus_half_range | 7 | -11.66 | -18% | -3.65% | 0% | 11.6 h |

### Por duração

| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |
|---|--:|--:|--:|--:|
| < 3 h | 10 | -25.64 | -5.33% | 0% |
| 3 h a 1 dia | 282 | 88.91 | 0.81% | 53% |
| 1 a 7 dias | 0 | 0.00 | – | – |
| 7 a 30 dias | 0 | 0.00 | – | – |
| > 30 dias | 0 | 0.00 | – | – |

### Excursões (antes de custos)

- Vencedores (150): MFE mediano 3.7%, MAE mediano -1.0%, devolução média do melhor ponto 2.3%, captura mediana 0.52.
- Perdedores (142): MAE mediano -2.9%, MFE mediano 0.9%; 21 (15%) já estavam ≥ 2% no lucro antes de perder.

### Custo, trades curtos e concentração

- Taxas pagas: 45.94; 42% do lucro antes de custos.
- Trades < 3 h: 10 (lucro -25.64); reentradas em < 24 h: 58 (lucro 18.33).
- Maior trade = 32% do lucro; top 5 = 90%; top 10 = 131%; lucro sem o melhor = 42.92.
- Lucro por ano de fechamento: 2018: 17.0, 2019: 22.7, 2020: -2.3, 2021: 32.1, 2022: -3.5, 2023: -8.2, 2024: 5.6.
