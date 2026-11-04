# Família TSMOM (H-015 grade, H-016 configuração escolhida), etapa 2.1 (2026-11-04)

## Regra e grade (registradas antes de rodar)
Momentum de série temporal em candles diários fechados, execução 1h: long enquanto close(d)/close(d-N) > 1. N ∈ {30, 60, 90, 120, 180} × regime {desligado, SMA200 diária} = **10 configurações (N_trials = 10)**, sem stop. Três pares, custos `base` e `base_2x`.

Verificações de código: 9 testes de regra/causalidade (invariância a prefixo e corrupção do futuro), screen estático limpo, lookahead sem viés e recursive estável em BTC, ETH, BNB (`research/baselines/checks-TimeSeriesMomentum_H015_v1.json`). A curva reconstruída a partir dos trades reproduz o backtest real a `base_2x` (22,7200 vs 22,7200).

## Exploração (IS, `base_2x`, 2017-11 a 2024-07, média igual dos 3 pares)
Sharpe anualizado por configuração: N30 1,49 · N60 1,23 · N90 1,06 · N120 1,08 · N180 0,92 (sem regime); com regime 1,33 · 1,27 · 1,11 · 1,08 · 0,94.

| Critério (fixado antes) | Resultado | Passou |
|---|--:|:-:|
| DSR da melhor (N=10) ≥ 0,95 | 0,9992 | sim |
| PBO (CSCV 16 fatias) ≤ 0,5 | 0,31 | sim |
| Platô (vizinha ≥ 70% da melhor) | N60 = 83% | sim (só 1 vizinha: a melhor está na borda do grid) |
| Sharpe > buy-and-hold (1,15) | 1,49 | sim |
| Sharpe > Sma200Baseline (1,05) | 1,49 | sim |
| ≥ 30 trades por par | 94 / 89 / 96 | sim |
| Gates (`gates.json`), exposição 15% | todos | sim (DD 14% base; lucro sem o melhor trade positivo) |

Walk-forward ancorado 2020-2024: Sharpe OOS 1,21; ano a ano 0,63 / 2,69 / **−1,00 (2022)** / 1,45 / 1,89. IC (bootstrap de blocos) do retorno médio por trade: 0,103 [0,041; 0,179], n = 279. Por ciclo (Sharpe, melhor vs B&H): 2018 −0,66 vs −0,48 · 2019 1,66 vs 1,15 · 2020-21 2,61 vs 2,20 · 2022 −1,00 vs −0,96 · 2023+ 1,61 vs 1,73.

Exposição calibrada pela regra do laboratório: 15% (p95 de drawdown 19 / 16 / 20%). A 100% o drawdown por par era 74-85%.

## Validação (lida UMA vez, config escolhida no IS, exposição 15%)
| Par | Trades | Lucro base (de 100) | Lucro conservative | Lucro sem o melhor trade | DD base | B&H | Decisão |
|---|--:|--:|--:|--:|--:|--:|---|
| BTC | 43 | +1,9 | +1,09 (exigido 1,10) | **−5,2** | 5,2% | +41,8% | rejeitada |
| ETH | 33 | +14,3 | +13,5 | positivo | 6,7% | −20,9% | candidata |
| BNB | 43 | +6,2 | +4,7 | **−3,2** | 4,3% | +32,0% | rejeitada |

Lookahead e recursive limpos. Em stress, o lucro do BTC é −1,7.

## Conclusão
**H-016 não aprovada na validação; a família TSMOM não tem evidência OOS.** O lucro em BTC caiu de +150 (exploração) para +1,9, e em BNB de +517 para +6,2; em BTC e BNB o resultado depende do melhor trade. Só a ETH passou, num período em que a ETH caiu 21% (a estratégia, em caixa durante quedas, evitou perdas, não gerou alfa). Código arquivado; hipótese, grade e resultados preservados.

## Ressalvas
- O melhor N é o menor da grade (borda): o platô tem uma só vizinha. Isso, com a queda OOS, indica que o sinal rápido capturou o regime de 2017-2021 (bull de alta volatilidade, que o IS enfatiza).
- O Sharpe do IS é de uma carteira de pesos iguais com rebalanceamento diário; por par ele é menor (1,16 / 1,01 / 1,35).
- A penalização do gate por "variantes na família" conta hipóteses (aqui 1), não células da grade; o DSR, sim, usa N = 10.
- A validação já tinha sido lida para a H-008 (outra regra) e o ciclo da Sma200Baseline é conhecido: a janela de validação não é cega para ideias de tendência.
