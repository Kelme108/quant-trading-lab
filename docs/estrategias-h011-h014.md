# TripleBottomReversal e EMASnapbackATR (H-011 a H-014)

Resultado em uma linha: **nenhuma das duas mostrou vantagem estatística. Recomendação: descartar ambas** (detalhes e limitações abaixo). Tudo rodou na exploração; validação e final test não foram lidos.

## O que foi implementado

| ID | Estratégia | TF | Arquivo |
|---|---|---|---|
| H-011 | TripleBottomReversal | 1h | `user_data/strategies/TripleBottomReversal_H011_v1.py` |
| H-013 | TripleBottomReversal | 4h | `..._H013_v1.py` (mesma regra, mesmas constantes em candles) |
| H-012 | EMASnapbackATR | 1h | `user_data/strategies/EMASnapbackATR_H012_v1.py` |
| H-014 | EMASnapbackATR | 4h | `..._H014_v1.py` |

Testes: `tests/test_triplebottomreversal_h011_v1.py` (17) e `tests/test_emasnapbackatr_h012_v1.py` (9), incluindo o teste de causalidade (sinais de um prefixo da série são idênticos aos do mesmo prefixo da série completa) e a confirmação do pivô só em *i+K*. `lookahead-analysis` do Freqtrade: sem viés em H-012. Ferramentas: `research/tools/calibrate_and_run.py`, `dossier.py`, `dossier_table.py`, `sensitivity.py`, `register_h011_h014.py`.

### TripleBottomReversal: matemática e parâmetros

- **Pivô**: `low[i]` é o menor de `[i-K, i+K]` (empate só à esquerda). Só é conhecido no fechamento de `i+K` (K = 5): nenhum pivô é usado antes disso.
- **Três fundos** `i1<i2<i3`: dispersão `(max L - min L)/mean L <= 2%` (tolerância), separação mínima de 12 candles, padrão com no máximo 150 candles.
- **Recuperações** `H1`, `H2` = máximas entre fundos; cada uma >= 3% acima do fundo médio (evita padrão artificial). **Neckline** = `max(H1,H2)`.
- **Entrada**: primeiro fechamento acima da neckline em até 30 candles após a confirmação de `i3`, antes de um quarto pivô, sem fundo novo abaixo da zona (-2%), com volume >= média dos 20 candles anteriores. RSI (divergência positiva) e EMA200 são opcionais, desligados na regra testada.
- **Stop** = menor fundo - 0,5 x ATR(14), fixo na entrada. **Alvo** = neckline + 1,0 x altura (neckline - fundo médio). Time stop de 150 candles. Sem DCA, sem pirâmide; os mesmos fundos nunca geram um segundo sinal.
- **R/R mínimo** é configurável, mas o padrão é desligado: com stop abaixo do suporte e entrada na neckline o R/R é **menor que 1 por construção** (o risco inclui a altura mais a margem; o ganho é uma altura). Qualquer piso acima de ~0,9 elimina todos os trades. Isso significa que o padrão precisa de taxa de acerto acima de 50% só para empatar, antes dos custos.
- **Dimensionamento por risco**: o lab proíbe `custom_stake_amount` (comparabilidade entre estratégias). A função `risk_position_fraction` existe (testada) e a análise `dossier.py` reaplica 1% de risco por trade sobre os trades exportados (fração = risco / distância do stop, máx. 1,0, sem alavancagem). Os gates usam exposição fixa calibrada pela regra do lab.

### EMASnapbackATR: parâmetros

`z = (close - EMA20)/ATR14`; estiramento = `min z` nos 6 candles anteriores <= -2,0; tendência `close > EMA200`; confirmação `close > high(t-1)` e `close < EMA20`; stop `close - 2,0 x ATR`; saída no primeiro fechamento >= EMA20 ou time stop de 48 candles; cooldown de 6. RSI (<= 35) e volume (>= média 20) são opcionais, desligados. Valores de livro-texto, fixados antes de qualquer resultado.

## Resultados (BTC/USDT, exploração 2017-08 a 2024-07, custo base, buy-and-hold = +1252%)

Gates oficiais (3 pares, 4 cenários de custo, lookahead e recursive):

| Hipótese | Resultado | Motivo |
|---|---|---|
| H-011 (1h) | **descartada pela regra pré-registrada** | só 9 / 5 / 6 trades de calibração (BTC/ETH/BNB); mínimo 30 |
| H-013 (4h) | **descartada** | 5 / 3 / 1 trades |
| H-014 (4h) | **descartada** | 33 / 27 / 32 trades; ETH abaixo de 30 |
| H-012 (1h) | **rejeitada nas 3 paridades** | exposição calibrada 20%; lucro base **-7,3 / -9,5 / -15,4** (por 100), profit-ex-best negativo, drawdown stress 21 / 22 / **28%** na BNB; recursive instável nas 3 |

Dossiê descritivo da BTC/USDT (exposição 100%, custo base), ver `research/dossiers/*.json` e `python research/tools/dossier_table.py h011-btc-1h h012-btc-1h h013-btc-4h h014-btc-4h`:

| Estratégia | Trades | Win rate | Profit factor | Expectancy (razão/trade) | Sharpe | Sortino | Max DD | Retorno |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| H-011 TripleBottom 1h | 9 | 11% | 1,56 | +0,50 | 0,01 | 0,09 | 43,4% | +24,3% |
| H-013 TripleBottom 4h | 5 | 20% | 0,88 | -0,10 | 0,00 | -0,02 | 25,9% | -3,2% |
| H-012 EMASnapback 1h | 121 | 56% | 0,66 | -0,15 | -0,13 | -0,16 | 42,6% | -33,2% |
| H-014 EMASnapback 4h | 33 | 58% | 0,52 | -0,20 | -0,07 | -0,12 | 23,7% | -23,7% |

Walk-forward por ano (regra fixa em janelas de calendário, sem ajuste): H-012 perde em 7 de 8 janelas anuais (só 2017 é positivo, +10%); H-014 perde em 5 de 8, ganha em 2 (2021 +6%, 2023 +0,7%) e perde na janela completa. Com menos de ~10 trades por janela, Sharpe/Sortino/PF do Freqtrade não têm significado (ele devolve valores sentinela como -100). Sizing por risco de 1% por trade: H-012 -1,3% (DD 1,8%), H-011 +2,1% (DD 1,8%). Mesmo reduzindo o risco, o sinal de H-012 continua negativo.

Comparação com o que já existia (BTC, exploração, custo base, lucro por 100): H-001 SMA baseline +186 (DD 50%), H-009 WeeklyBreakout +114 (DD 7%, exposição 25%), H-010 -1,7, H-012 -7,3. As duas novas não superam nenhuma das estratégias de tendência e nem o buy-and-hold.

Sensibilidade pré-declarada (BTC 1h, todas as variantes, nenhuma escolhida; contam como testes extras das famílias):

- EMASnapback: `Z_ENTRY` 1,5/2,5/3,0, RSI, volume, saída 1,5R, stop 1,5/3 ATR: **todas com expectancy negativa** (de -0,05 a -0,38); a melhor, saída 1,5R, ainda perde (-14,8%). Win rate de 47-59% com payoff ruim: a perda média é maior que o ganho médio. Alto win rate não é vantagem.
- TripleBottom: variantes mais frouxas dão 5 a 11 trades. Os "+507%" e "+1060%" de algumas são **um único trade vencedor entre 5 ou 6** com saldo inteiro composto, não evidência (win rate 17-20%).

## Limitações e falhas possíveis

1. **Poucos padrões**: o Triple Bottom, com tolerância e confirmação rigorosas, aparece cerca de 1 vez por ano na BTC 1h. Não há amostra para provar nem refutar vantagem; afrouxar até ter trades suficientes é ajuste ao resultado, o que o protocolo proíbe sem novo ID e penalidade.
2. **R/R estruturalmente < 1** no Triple Bottom (ver acima) e na H-011 8 dos 9 trades saíram no stop; o único trade positivo foi uma saída forçada no fim da janela de dados (`force_exit`), não um alvo atingido.
3. **Take-profit no backtest** (`custom_exit`) é avaliado na abertura do candle seguinte, não intrabar: subestima alvos tocados por pavio. Isso não explica as perdas do H-012 (a saída principal é por sinal).
4. **H-012 recursive instável**: `startup_candle_count = 800` não estabiliza as EMAs/ATR/RSI; teria de ser maior antes de qualquer reuso.
5. **Validação já contaminada**: a janela 2024-07..2026-10 foi lida uma vez para a H-008. Por isso, e porque nenhuma hipótese passou na exploração, ela não foi lida.
6. Walk-forward aqui é de **regra fixa** (sem parâmetros ajustados), logo mede estabilidade entre regimes, não reotimização. Ativos cripto correlacionados: BTC/ETH/BNB não são três amostras independentes.
7. Os Sharpe/Sortino do Freqtrade vêm de retornos por trade e não anualizados; usá-los só como comparação relativa.

## Recomendação

**Descartar as duas famílias.** EMASnapbackATR tem expectativa negativa em todas as 9 variações testadas e nos 3 pares (reversão à média já havia falhado em H-003/H-010); o custo de transação a 1h consome o pouco que o snapback recupera. TripleBottomReversal é inviável por falta de amostra com a regra rigorosa e, com a frouxa, o resultado é um ou dois trades. Não vale gastar variantes (limite de 3 por família) nem a validação. Se quiser retomar o Triple Bottom no futuro, a única via honesta é universo maior (dezenas de pares) ou timeframe diário com histórico de mais pares, definido ex ante.

## Limpeza realizada

Removidas as estratégias que estavam paradas **e** mal implementadas: `SlowTimeSeriesMomentum_H004_v1` (a implementação desviava da regra e a SMA de 4800 barras excede o warm-up carregável) e `RegimeGatedPullbackTrend_H006_v1` (nunca rodou: warm-up 5520 > 4500; a ideia foi refeita em H-010), com seus testes. Os registros de experimento e as notas no ledger foram mantidos e os arquivos estão no histórico git (commit 544a3d5). As demais estratégias (baselines H-001..003 protegidas por SHA, H-005, H-007..H-010) foram bem implementadas e rejeitadas pela evidência: ficam, porque são o registro reprodutível dessas decisões.

## Mudança de infraestrutura

`lab/experiment.py` e `lab/orchestrator.py` agora aceitam `timeframe` (lido do arquivo da estratégia; padrão 1h, sem mudar as hipóteses antigas). Dados 4h de BTC/ETH/BNB baixados e validados. `lab/config/scenarios.json` não foi alterado (4h continua desabilitado para a geração automática de hipóteses).
