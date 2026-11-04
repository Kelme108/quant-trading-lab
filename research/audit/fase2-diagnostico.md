# Fase 2 — Diagnóstico individual (somente exploração)

**Status: decisões PROVISÓRIAS.** `lab/config/gates.json` e `portfolio.json` continuam `PROPOSED`, sem aprovação do usuário.
Nenhuma validação foi lida nesta fase e o holdout prospectivo não foi tocado. Nenhuma regra registrada foi alterada.

## Fontes
- Métricas padrão: `research/audit/H-<id>-exploration-metrics.json`, gerado por `research/tools/audit_exploration.py`.
  - Lê só a janela de exploração de cada par (`runner.resolve_split_timerange("exploration")`).
  - Usa `lab/analytics.py`, `lab/returns.py` e `lab/stats.py`.
  - Cenários `base` e `base_2x` (2x os custos do base). O 2x foi recalculado nesta auditoria.
  - Referências na mesma janela: buy-and-hold e `Sma200Baseline`, com a mesma exposição da estratégia.
- Decisões dos gates e lucros dos cenários optimistic, conservative e stress: tabela `decisions` e `facts.json` em `research/experiments/H-<id>-exploration/`.
- Revisões dos agentes: `research/experiments/H-005-…`, `H-007-…`, `H-008-…`, `H-009-…`, `H-016-…` (`validator.md`, `quant.md`, `risk.md`).
- Reprodução: os `net_profit` de base recalculados batem com os do registro (H-008: 78,3 / 87,4 / 171,5; H-009: 113,8 / 61,8 / 133,6).

## Achados transversais
1. **O drawdown dos gates ignora a posição aberta.** O `max_drawdown_pct` vem de `max_drawdown_account` do Freqtrade, que é calculado sobre trades fechados (`lab/runner.py:365`).
   - O drawdown marcado a mercado (curva horária de `lab/returns.py`) é maior nas candidatas:

     | Hipótese (par) | DD gate (base) | DD marcado a mercado (base) |
     |---|---:|---:|
     | H-009 BTC | 7,2% | 11% |
     | H-009 ETH | 18,5% | 25% |
     | H-009 BNB | 14,5% | 32% |
     | H-008 BTC / ETH / BNB | 12,2% / 12,5% / 10,3% | 25% / 20% / 30% |
     | H-016 BTC / ETH / BNB | 14,0% / 11,4% / 9,7% | 24% / 25% / 48% |

   - Fontes: `facts.json` e `audit/*-metrics.json` (`equity.max_drawdown`).
   - Não altero o gate. É uma decisão sua se o teto de 25% deve valer também para o drawdown marcado a mercado (critério extra, só com pré-registro e aprovação).
2. **Win rate não decide nada.** As reprovadas por H-003 e H-012 têm win rate de 50–64%, com profit factor < 1 (H-012: 0,42–0,65). As aprovadas têm 29–42%.
3. **O custo 2x não derruba H-009, H-008 nem H-016** (lucro positivo nas três). Derruba H-001 no BTC (+186,5 no base → −25,1 no 2x).
4. **Três pares não são três amostras independentes.** Em `scenarios.json`, a correlação diária é 0,787 (ETH) e 0,635 (BNB) com o BTC.
5. **`research/proposals/H-008.json`, `H-009.json` e `H-016.json` não existem.** Os validators apontaram isso. A regra está só no registro e na docstring da estratégia. É lacuna de rastreabilidade.

## Classificação (provisória)

| Hipótese | Classe | Motivo (fato e fonte) |
|---|---|---|
| H-001 SmaTrend | `rejeitada` | Rejeitada nos 3 pares em exploração. DD marcado a mercado 48–62%; 2x custo leva BTC a −25,1. Consistência 0,07. |
| H-002 Donchian | `rejeitada` | Lucro base negativo no BTC (−51,7) e no ETH (−28,8); DD marcado a mercado 80–90%. |
| H-003 Bollinger | `rejeitada` | Base negativo no BTC (−14,8) e no ETH (−19,9). Só o BNB é positivo (+48,7), com 50 trades. |
| H-004 SlowTSMOM | `inválida` | Implementação desviou da regra (SMA com `min_periods=1440`, sem cooldown). A regra não foi testada. |
| H-005 VolSqueeze | `rejeitada` | Falha em drawdown (gate). Maior trade = 71–81% do lucro. Exposição 1,0: DD marcado a mercado 59–67%. |
| H-006 RegimeGatedPullback | `inválida` | Nunca rodou: warm-up 5520 > 4500. |
| H-007 RisingTrendBreakout | `rejeitada` | Falha em drawdown. BNB: lucro sem o melhor trade = −48,6. Maior trade do BNB = 130% do lucro. |
| H-008 VolSqueeze (20%) | `rejeitada` (validação lida) | Ver IS→OOS abaixo. Validação: 2 rejeitadas e 1 inconclusiva; 8–12 trades; lucro sem o melhor trade negativo em BTC e BNB. |
| H-009 WeeklyBreakout | `candidata_exploração` | Passa os gates nos 3 pares. Com ressalvas abaixo. Validação não lida. |
| H-010 UptrendPullback | `rejeitada` | Lucro base negativo nos 3 pares (−1,7 / −9,1 / −1,6). Profit factor 0,84–0,97. |
| H-011, H-013, H-014 | `inconclusiva` (descartadas pela regra pré-registrada) | Menos de 30 trades na calibração; não retunadas. Sem resultado de gates. |
| H-012 EMASnapback | `rejeitada` | Negativa em todos os pares (base −7,3 / −9,5 / −15,4). Profit factor 0,42–0,65. |
| H-015 TSMOM (grid) | `rejeitada` (família) | Célula escolhida (H-016) não foi aprovada na validação. |
| H-016 TSMOM N30 | `rejeitada` (validação lida) | Validação: BTC rejeitada, ETH candidata, BNB rejeitada. Exige todos os pares. |

## Diagnóstico de overfitting

### IS → OOS (só onde a validação já foi lida)
Lucro base por dia, exploração vs validação. Fonte: `lab.sqlite`, tabela `metrics`; dias de `splits.json`.

| Hipótese (par) | Exploração (por dia) | Validação (por dia) | Variação |
|---|---:|---:|---:|
| H-008 BTC | 0,0312 | 0,0075 | −76% |
| H-008 ETH | 0,0348 | 0,0082 | −76% |
| H-008 BNB | 0,0699 | 0,0126 | −82% |
| H-016 BTC | 0,0598 | 0,0023 | −96% |
| H-016 ETH | 0,0458 | 0,0170 | −63% |
| H-016 BNB | 0,2108 | 0,0076 | −96% |

- Os lucros por dia usam as mesmas regras e exposições, mas as validações têm 8–43 trades, então os números são ruidosos.
- Nos dois casos, a exploração superestimou o desempenho em 63–96%.
- Há contaminação parcial: a janela de validação já foi vista pela H-008, pela H-016 e pelos ciclos da `Sma200Baseline`.

### Dependência de 1 trade, 1 par ou 1 ciclo (exploração, base)

| Hipótese | Maior trade / lucro (BTC / ETH / BNB) | Lucro sem o melhor trade (BTC / ETH / BNB) | CI95 do retorno total (BTC / ETH / BNB) |
|---|---|---|---|
| H-009 | 22% / 38% / 80% | 89,3 / 38,6 / 27,0 | [0,21; 2,20] / [−0,00; 1,95] / [−0,08; 9,16] |
| H-008 | 56% / 76% / 82% | 34,2 / 21,4 / 30,5 | [−0,10; 2,92] / [−0,15; 6,13] / [−0,16; 17,46] |
| H-016 | 39% / 28% / 45% | 91,1 / 83,0 / 283,7 | [0,04; 5,68] / [0,11; 3,83] / [0,15; 43,65] |

- O CI é bootstrap de blocos dos trades (`lab/stats.py`, bloco 3, semente fixa).
- **H-009:** o IC do retorno total de ETH e BNB inclui zero; só o BTC o exclui.
- **H-016:** a exploração é a mais robusta das três (IC > 0 nos 3 pares). A validação mostrou queda forte.
- **Por ciclo, H-009** (`equity`, base, exposição 0,25; retorno do ciclo):

  | Par | 2018 | 2019 | 2020–21 | 2022 | 2023+ |
  |---|---:|---:|---:|---:|---:|
  | BTC | −2% | +21% | +32% | 0% (0 trades) | +9% |
  | ETH | +9% | +10% | +36% | −2% | 0% |
  | BNB | −5% | +26% | +115% | −7% | −2% |

  Em ETH e BNB, o ciclo 2023+ rende de −2% a 0%. O BNB concentra o ganho em 2020–21.

### Consistência entre pares (`min_over_max`, lucro por dia no base)
H-001 0,07; H-002 0,00; H-003 0,00; H-005 0,56; H-007 0,30; H-008 0,45; H-009 0,45; H-010 0,00; H-012 0,00; H-016 0,22.
O mínimo exigido é 0,25 (`portfolio.json`). Abaixo de 0,25 só na exploração: H-001, H-002, H-003, H-010, H-012 e H-016. O critério do portfólio usa exploração e validação juntas, então isto é indicativo; a H-016 (0,22) já nasce abaixo do limite.

### Tamanho da família e borda do grid
- Todas as famílias têm 1 ou 2 variantes (limite 3). Só a H-015 tem grid (10 células); H-016 é a célula N30, **na borda do grid** (plateau com um vizinho só). O DSR (0,999) e o PBO (0,31) são de `research/grids/H-015-exploration.json`.
- H-009 não tem grid: horizontes de livro-texto (7d de rompimento, 30d/90d de regime), sem ajuste. Não há seleção dentro da família.

### Custo
Nenhuma aprovada em exploração é explicada só pelo custo otimista: H-009, H-008 e H-016 seguem positivas no 2x.

## H-009 contra as referências (exploração, base_2x, mesma exposição de 0,25)

| Par | Sharpe H-009 | Sharpe buy-and-hold | Sharpe Sma200Baseline | Correlação diária com Sma200 | Sobreposição em posição com Sma200 |
|---|---:|---:|---:|---:|---:|
| BTC | 1,11 | 0,89 | 0,66 | 0,48 | 90% |
| ETH | 0,58 | 0,83 | 0,71 | 0,43 | 89% |
| BNB | 0,59 | 1,32 | 0,81 | 0,71 | 93% |

- A H-009 vence o buy-and-hold e a `Sma200Baseline` em Sharpe só no BTC.
- No ETH e no BNB perde para os dois. Fonte: `audit/H-009-exploration-metrics.json`.
- No BNB a correlação diária com a `Sma200Baseline` é 0,71 (> 0,7).
- Esses critérios de Sharpe são os da Fase 4 (grid explorado), não gates; aqui são informativos.
- Exposição em mercado: 17–18% do tempo.
- Revisão dos agentes: sem erro de lookahead ou de fidelidade. Ressalvas: arquivo de proposta ausente; maior trade do BNB responde por 80% do lucro; DD do ETH no stress = 23,7% (limite 25%).

## Mecanismos de falha das rejeitadas (material da Fase 4; só exploração)

| Hipótese | Mecanismo observado |
|---|---|
| H-005 / H-007 (exposição 1,0) | O perfil de ganho é bom (profit factor 1,6–2,6) mas o tamanho da posição gerava DD de 54–67% marcado a mercado. H-008 corrigiu isso reduzindo a exposição, e o ganho não persistiu fora da amostra (−76% a −82% por dia). Poucos trades (31–36) e 70–80% do lucro em um trade. |
| H-010 | Entrar em recuperação de pullback numa tendência de alta não tem expectância: profit factor ≈ 0,9 em todos os pares, antes de qualquer ajuste. |
| H-012 / H-003 | Reversão à média: win rate de 50–64% mas payoff baixo, profit factor 0,72–0,82 (H-003 BTC/ETH) e 0,42–0,65 (H-012). Muitos ganhos pequenos e poucas perdas grandes. Falha em tendência. |
| H-001 / H-002 | Cruzamentos e rompimentos de 1h sem filtro de regime: 366–835 trades, profit factor 0,96–1,26, DD marcado a mercado 48–90%. Custo domina (H-001 BTC: +186,5 no base → −25,1 no 2x). |
| H-016 | Seguimento de tendência N30: edge existe na exploração e se dissolve na validação (−63% a −96% por dia). Mecanismo plausível: o benefício veio de poucos ciclos de tendência forte (2020–21), mas isto é hipótese, não medida. |

## Pendências que dependem de você
1. Decidir se o drawdown marcado a mercado passa a ser critério (hoje só informativo).
2. H-009 passou nos gates em exploração, mas ainda não há melhoria registrada. Pela regra da Fase 4, ela é "promissora" (passa em ≥ 2 pares). As outras candidatas (H-008 e H-016) já consumiram a validação.
3. Os arquivos `research/proposals/H-008|H-009|H-016.json` não existem. Registro como lacuna documentada, sem criar arquivos retroativos.
