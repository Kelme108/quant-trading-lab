# Protocolo de validação v3: Donchian Ensemble, SMA 200d, Volatility Sizing e TSMOM

Versão: rascunho 2, 2026-11-04. Incorpora as revisões independentes de `research/protocol-review/validator.md`, `quant.md` e `risk.md` (as respostas estão no §13).

Status: **proposta, aguardando aprovação do usuário. Nada aqui foi implementado ou executado.**

Este protocolo complementa `research/validation-protocol-v2.md`, `lab/config/gates.json`, `splits.json`, `holdout.json`, `portfolio.json` e `budget.json`, e não altera nenhum deles. Todo limite novo aparece como **decisão pendente (D-n)**. Um limite só passa a valer depois de duas coisas: o usuário aprova e o critério é pré-registrado em `lab/registry.py`, antes de qualquer execução da hipótese.

**Regra de apresentação (vale para todo relatório gerado sob este protocolo).**
- A primeira linha diz: "Provisório: limites PROPOSED; sem evidência prospectiva; dados históricos semi-contaminados".
- As palavras "pronto", "aprovado" e "validado" nunca aparecem sem essa ressalva.
- O "dry-run congelado" é um experimento de coleta de evidência, não uma etapa de prontidão.
- Nenhum resultado deste protocolo aprova operação real (`gates.json`: "There is no 'approved for live' value").

## 0. Ponto de partida e restrições herdadas

1. **Escopo.** Os pares são BTC/USDT, ETH/USDT e BNB/USDT spot, somente long. A execução é em 1h no candle seguinte ao sinal. O informative diário entra via `merge_informative_pair`. Somente dry-run.
2. **Dados já vistos.**
   - Cerca de 47 regras já usaram a exploração, que vai de 2017-08 a 2024-07 conforme o par (`docs/relatorio-auditoria-estrategias.md` §3).
   - A validação, de 2024-07 a 2026-10-20, é semi-contaminada para tendência: H-008 e H-016 a leram, e os ciclos da `Sma200Baseline` também a cobrem.
   - Só o holdout prospectivo, a partir de 2026-10-21, é virgem.
3. **Métodos proibidos.** `custom_stake_amount` e `adjust_trade_position` são proibidos (`lab/strategy_check.py:48`). Tamanho variável e posição fracionada não são executáveis no Freqtrade sem mudar essa regra (D-1).
4. **Mínimo de 30 trades por par e por split** (`gates.json`). Na exploração, a `Sma200Baseline` tem 19, 18 e 31 trades em BTC, ETH e BNB (`research/audit/H-009-exploration-metrics.json`, campo `sma200_trades`).
5. **Drawdown do gate.** É medido sobre trades fechados. O drawdown marcado a mercado (MTM) é bem maior. Na exploração, a SMA 200d com exposição 1 tem MTM de 66%, 76% e 77% (mesmo arquivo, `sma200_exposure_1.max_drawdown`).
6. **Teto de 3 variantes por família** (`budget.json`). `TimeSeriesMomentum` usou 2 (H-015 e H-016).
7. **`gates.json` e `portfolio.json` estão PROPOSED** (D-7).

## 1. Arquitetura experimental e responsabilidades

### 1.1 Princípio: só decide quem é executável

- **Gates e carteira.** Só recebem decisão objetos que o Freqtrade executa como uma estratégia única, com trades exportados: um arquivo, uma classe, um `H-NNN` (`lab/strategy_check.py`, `research/tools/validate_once.py`).
- **Ensemble.** É implementado como **voto dentro de uma estratégia** (§2.2), e não como soma de várias instâncias.
- **Volatility sizing.** É um **overlay de análise** (§2.3): relatado e nunca decisivo. Enquanto D-1 não for decidido, o rótulo é "teórico: não executável".

### 1.2 Componentes existentes (reutilizados)

| Componente | Responsabilidade | Não faz |
|---|---|---|
| `lab/dataquality.py`, `research/validate_ohlcv.py` | Integridade dos dados: SHA, lacunas, alinhamento 1d × 1h | Corrigir dados |
| `lab/costs.py` | Cenários de custo (§5) | Medir custo real |
| `lab/runner.py` | Backtest, lookahead e recursive; trava do final test | Decidir |
| `lab/manifest.py` | Manifesto: comando, imagem, hashes | — |
| `lab/registry.py` | Hipótese, regra, critérios, decisões, arquivamento | Alterar regra registrada |
| `lab/gates.py` | Decisão por par × split | Avaliar o holdout |
| `lab/returns.py` | Curva horária MTM e retornos diários a partir dos trades | Re-simular ordens |
| `lab/stats.py` | Sharpe, PSR, DSR, PBO, IC por bootstrap de blocos | — |
| `lab/walkforward.py`, `lab/cycles.py` | Walk-forward ancorado; ciclos; guarda do holdout | — |
| `lab/causality.py` | Invariância a prefixo; corrupção do futuro | — |
| `lab/bootstrap.py` | Calibração de exposição (`choose_exposure`) | Retunar sinais |
| `lab/portfolio.py` | Elegibilidade, consistência e correlação | Ranquear por retorno |
| `research/tools/analysis_checks.py`, `grid_explore.py`, `validate_once.py`, `audit_exploration.py`, `dossier.py` | Checagens, grid, leitura única, métricas padrão, estabilidade por janela | Ler validação ou holdout fora das regras |

### 1.3 Componentes novos (fase de implementação; cada um com teste antes de uso)

| Componente | Função | Teste obrigatório |
|---|---|---|
| `lab/sizing.py` | Overlay: peso por trade `w_i` (§2.3). Exige uma versão de `returns.equity_curve` que aceite uma lista de pesos por trade; a assinatura atual aceita um escalar (`lab/returns.py:27`) | Com `w` constante, a curva é idêntica à atual; `lab/causality.py` aplicado ao peso |
| `lab/marginal.py` | Ganho marginal pareado (§7.2): reamostra os **mesmos índices de bloco** nas duas séries e recalcula os dois Sharpes | Com Y = X, ΔSharpe e o IC são exatamente 0; seed fixa |
| `lab/trials.py` | Tabela de tentativas para o DSR (§6.4): lista de IDs ou configurações e suas séries | Contagem igual ao registro |
| `research/tools/protocol_v3.py` | Orquestra §4 a §8 e escreve um relatório com fonte por célula e a regra de apresentação | Recusa validação repetida e qualquer candle ≥ 2026-10-21 (`cycles.assert_before_holdout`) |
| `research/tools/holdout_eval.py` | Avaliação única do holdout (§8.3) | Recusa avaliar antes de 2027-04-21 ou duas vezes |

### 1.4 Divisão de trabalho

- **Código determinístico:** produz todos os números.
- **`research`:** proposta da família; não vê a validação.
- **`developer`:** estratégia e teste de contrato.
- **`validator`:** fidelidade, causalidade e conferência de números.
- **`quant`:** tabelas, custo e concentração.
- **`risk`:** drawdown, sequências de perda, execução e sobreposição.
- **Orquestrador:** decide pelos gates e por este protocolo.

## 2. Estratégias, parâmetros e variações

### 2.0 Regras gerais

- Parâmetros redondos, fixados antes de executar.
- **Sem grid de seleção nesta rodada.** Toda variação é "sensibilidade relatada" e conta no N do DSR (§6.4). Uma sensibilidade **não pode alterar uma decisão**.
- **Sem stop de catástrofe.** O stop de 20% do rascunho 1 era um parâmetro livre, sem justificativa ex ante e sem regra de reentrada (Q-12). As saídas são por sinal; o risco é controlado pela exposição calibrada (§4.1, passo 4).
- **Convenção comum a todas as regras diárias:**
  - O sinal é calculado no candle **diário fechado**. Canais e médias usam o dia D-1 e anteriores, com `shift(1)` no diário antes do merge.
  - A execução é na abertura do candle de 1h seguinte ao fechamento diário (00:00 UTC).
  - A entrada é **por nível**: entra se o sinal está ligado e a estratégia está fora de posição. Isso inclui o primeiro candle do split, se o sinal já estiver ligado (mesmo comportamento da `Sma200Baseline`).
  - A saída é quando o sinal desliga. No fim do split, a posição aberta é fechada pelo backtest; esse trade é relatado à parte.
  - Para estados que dependem do caminho (Donchian), o warm-up é de **400 candles diários**. A implementação precisa provar, em teste, que o estado no primeiro dia do split é idêntico ao calculado com o histórico inteiro anterior. Se não for, o warm-up aumenta antes do registro.
  - A primeira data de sinal possível por par é relatada. No BNB (dados desde 2017-11), regras de 200+ dias só sinalizam a partir de meados de 2018.

### 2.1 SMA 200d: referência; candidata só prospectiva

- **Regra:** a `Sma200Baseline` existente, congelada por SHA: fechamento diário fechado > SMA(200) diária. Sem stop.
- **Papel no IS e na validação:** é o **benchmark** (§6.1). Não recebe decisão, porque não há comparação possível contra si mesma (V-10). Ela tem 19 e 18 trades em BTC e ETH no IS, abaixo do gate de 30.
- **Papel prospectivo:** pode ir para o dry-run congelado **como referência**, para medir no holdout o mesmo que as candidatas medem (D-9).
- **Sensibilidade relatada:** 100 e 150 dias. Conta no N.

### 2.2 Donchian Ensemble (voto, uma estratégia)

- **Membro k:** estado de dois níveis no diário, para o par (N_k, M_k).
  - Liga quando `close_d > max(high_{d-N_k..d-1})`.
  - Desliga quando `close_d < min(low_{d-M_k..d-1})`.
  - Mantém o estado anterior em qualquer outro caso.
  - O canal usa a máxima e a mínima diárias (como `DonchianBreakoutBaseline.py:30-31`), sempre sem o dia atual.
- **Membros pré-declarados:** (20, 10) e (55, 20), os pares do sistema Turtle, mais (100, 50) e (200, 100), escolha de projeto com M = N/2 e espaçamento aproximadamente geométrico. Os dois últimos **não são canônicos**. O membro (200, 100) fica próximo da SMA 200d (§9.3).
- **Sinal agregado:** em posição quando **pelo menos 2 dos 4** membros estão ligados; sai quando menos de 2 estão ligados.
  - A posição é binária, executável sem `adjust_trade_position`.
  - O limiar 2 de 4 é a maioria não estrita e foi fixado ex ante. Os limiares 1 e 3 entram como sensibilidade e contam no N.
- **Relatado e não decisivo:**
  - cada membro isolado;
  - a versão fracionada (média dos 4 estados, posição de 0 a 1), como overlay;
  - o voto sem o membro (20, 10).
- **Família nova:** `DonchianEnsemble`. Para o N do DSR conta também o mecanismo de canal já testado (H-002), além de H-007, H-009 e H-017 (rompimentos).

### 2.3 Volatility Sizing (overlay, não decisivo)

- **Peso do trade i:** `w_i = min(1, σ*/σ̂_i)`.
  - `σ̂_i` = desvio-padrão amostral (ddof = 1) de 30 log-retornos diários, ou seja, 31 fechamentos diários fechados, dos dias D-31 a D-1, sendo D o dia da abertura do trade.
  - O desvio é anualizado por √365 (`lab/stats.py:33`).
  - O peso fica fixo durante o trade. Isso **não é volatility targeting contínuo**, e os resultados não se transferem para ele (Q-13).
- **Parâmetros:** σ* = 40% ao ano. É um valor redondo, escolhido com conhecimento de que a volatilidade típica do BTC é maior; o efeito dominante é reduzir a exposição média. Sensibilidade: σ* ∈ {30%, 50%} e janela ∈ {20, 60}, variadas uma de cada vez, 4 células. Contam no N.
- **Comparadores obrigatórios** (Q-18):
  1. **Peso embaralhado:** os mesmos valores de w, atribuídos a trades sorteados (seed 1, 1000 permutações). Isola o valor da informação de volatilidade.
  2. **Exposição constante equivalente:** a média de w ponderada pelas horas em posição, calculada no IS. Não é implementável ex ante, e o relatório diz isso.
- **Relatados:** a correlação entre w e o retorno do trade; o w médio por par.
- **Aplicado a:** SMA 200d e Donchian Ensemble. Não é aplicado ao TSMOM.
- **Execução:** depende de D-1. Até lá, os números do overlay são "teóricos" e não podem levar nada ao dry-run.

### 2.4 TSMOM: alternativa com contaminação declarada

- **Regra proposta:** voto dos horizontes L ∈ {60, 120, 240} dias. Está em posição quando o retorno de pelo menos 2 dos 3 é positivo, com `close_d / close_{d-L} − 1` calculado no diário fechado.
- **Contaminação** (Q-15, V-4): esta escolha foi feita **depois** de saber, pela validação da H-016 (N30), que o horizonte curto degradou. Além disso, 60 e 120 são células do grid da H-015, com Sharpe IS já visto. Por isso:
  - o N do DSR inclui as 10 células da H-015, a H-016 e as novas;
  - **a leitura da validação desta variante é só descritiva**: não pode levar a `candidate_for_portfolio` por si; a única evidência que conta é o holdout;
  - é a última variante da família (`budget.json`). Uma falha encerra a família, e os critérios não podem ser afrouxados para evitar isso.
- **Decisão do usuário:** incluir o TSMOM nestes termos ou retirá-lo do protocolo (D-8).

## 3. Períodos

| Janela | Definição por par (`splits.json`) | Uso |
|---|---|---|
| IS (exploração) | início dos dados até 2024-07-04 (BTC e ETH) ou 2024-07-25 (BNB) | Toda escolha: regra, exposição, sensibilidades |
| Validação (OOS) | até 2026-10-20 | Uma leitura por hipótese, com a configuração do IS; descritiva para TSMOM e SMA 200d |
| Últimos 12 meses | 2025-10-21 a 2026-10-20 (dentro da validação) | Rotulado semi-contaminado; nunca usado para escolha |
| Holdout prospectivo | a partir de 2026-10-21 | Só a avaliação de §8.3; nenhum backtest, sensibilidade ou relatório histórico o toca |

- **Datas por par:** a fronteira é a de `splits.json`, em segundos e por par. Métricas "por dia" usam os dias reais de cada janela.
- **Warm-up:** usa candles anteriores ao split. É causal, mas os trades contam só dentro do split.
- **Candles pós-corte:** os candles ≥ 2026-10-21 já baixados ficam fora de qualquer execução histórica (`assert_before_holdout`, com teste em `protocol_v3.py`).

## 4. Sequência de testes, walk-forward e OOS

### 4.1 Ordem obrigatória por hipótese

1. **Registro:** regra (§2), sensibilidades, N (§6.4), warm-up, critérios de §8 com números e a versão deste protocolo.
2. **Implementação:** contrato, `lab/causality.py` (inclui o caso de omitir `shift(1)` no canal) e o teste de estado de §2.0.
3. **Checagens:** smoke, `lookahead-analysis` e `recursive-analysis` nos 3 pares.
4. **Exposição:** `bootstrap.choose_exposure`, a regra atual do lab, com DD de trades fechados.
   - O DD MTM resultante é relatado ao lado. Se passar de 25%, o rótulo é "calibrado em trades fechados; MTM excede o teto" (D-10).
   - Menos de 30 trades em algum par na calibração: inconclusiva, sem retunar.
5. **IS:** 4 cenários mais `base_2x`; métricas de §6; ciclos; estabilidade por ano (§4.2); ganho marginal (§7).
6. **Revisão:** `orchestrator review --split exploration`.
7. **Decisão IS** (§8.1). Se passar: uma leitura com `validate_once.py`.
8. **Decisão final** (§8.2). Se passar: dry-run congelado com hash registrado e avaliação do holdout (§8.3).

### 4.2 Estabilidade por ano (rótulo: "descrição do IS, não OOS")

- **Regras fixas:** não há seleção, então não há walk-forward verdadeiro. É relatado o Sharpe e o DD MTM por ano, de 2018 a 2024; o ano de 2024 vai só até o corte, cerca de meio ano, e é marcado assim.
- **Anos inteiros fora de posição** (Sharpe 0 por construção, `lab/stats.py:30`) são relatados como "fora do mercado" e não entram na contagem.
- **D-4 (detector de instabilidade, não tolerância de risco):** Sharpe anual > 0 em pelo menos 2/3 dos anos com posição. O limite de risco continua o de 25%.
- **Grids:** não há nesta rodada. Se uma rodada futura tiver grid, aplica-se `lab/walkforward.py`.

### 4.3 OOS

- Uma leitura, com a regra e a exposição do IS.
- Relatados: IS → OOS do Sharpe da carteira de 3 pares em `base_2x` e o lucro por dia, com IC por bootstrap.
- A queda é **informativa** (Q-06): com cerca de 2,3 anos, o erro-padrão do Sharpe é ≈ 0,8, então a razão IS/OOS é ruído nos dois sentidos. Quem decide são os gates. Se o Sharpe IS for ≤ 0, a razão não é calculada.

## 5. Custos padronizados

Fonte: `lab/costs.py`. Cada lado paga taxa + slippage + spread/2, aplicado uma vez na entrada e uma na saída (`docs/harness-fase0.md` §2).

| Cenário | Taxa/lado | Slippage/lado | Spread total | Efetivo/lado | Ida e volta | Uso |
|---|--:|--:|--:|--:|--:|---|
| optimistic | 0,10% | 0 | 0 | 0,100% | 0,200% | Gates |
| base | 0,10% | 0,05% | 0,05% | 0,175% | 0,349% | Gates; principal |
| conservative | 0,10% | 0,10% | 0,10% | 0,250% | 0,499% | Gates |
| stress | 0,10% | 0,25% | 0,25% | 0,475% | 0,946% | Gates |
| base_2x | 0,20% | 0,10% | 0,10% | 0,350% | 0,698% | Comparação com benchmarks (§8.1) |

- **Break-even de custo:** interpolação linear entre os cenários, **só dentro do intervalo coberto**. Fora dele: "não atingido até stress".
- **Ordens:** a mercado, na abertura do 1h seguinte, sem preenchimento parcial, sem latência e sem modelar indisponibilidade da exchange (§9.4).
- **Natureza dos cenários:** são sensibilidade, não medidas.
- **BNB:** é relatado também sem o primeiro ano de dados e em stress isolado (R-10).

## 6. Benchmarks e métricas

### 6.1 Benchmarks (mesma janela, par e custo)

1. Caixa (0%).
2. Buy-and-hold do par, com exposição 1.
3. `Sma200Baseline` na **mesma exposição** da estratégia: os trades da baseline com o mesmo peso constante `w` em `returns.equity_curve`, definição de `audit_exploration.py`.
4. **Carteiras de 3 pares:** estratégia e buy-and-hold agregados do **mesmo modo**, com média diária de pesos iguais dos retornos por par (rebalanceamento diário teórico, sem custo de rebalanceamento para nenhum dos dois, Q-17).

### 6.2 Métricas padrão (por par, split e cenário)

- **Resultado:** trades, lucro e ROI, lucro sem o melhor trade, concentração (top 1, top 5, top 10).
- **Drawdown:** DD do gate **e DD MTM lado a lado em toda tabela**, mais a duração do pior drawdown (do pico ao novo recorde, em dias).
- **Qualidade dos trades:** win rate com IC de Wilson (só relatado), profit factor, expectância, payoff, maior sequência de perdas em trades e em dias.
- **Risco/retorno:** Sharpe, Sortino e Calmar diários anualizados; CVaR diário de 95%.
- **Comportamento:** tempo em posição; retorno por ciclo; IC por bootstrap do retorno médio por trade e do retorno total; break-even de custo.
- **Relação com outras regras:** correlação diária e sobreposição em posição com a `Sma200Baseline`, com a H-009 e com as outras candidatas.

### 6.3 DSR e contagem de tentativas (N)

- **N decisório:** total de regras distintas do lab no momento do registro (≈ 47 hoje), mais todas as células novas desta rodada, incluindo sensibilidades.
  - A lista de IDs fica em `lab/trials.py` (V-13, Q-01).
  - O N por mecanismo (canais: H-002, H-007, H-009, H-017; TSMOM: H-015 com 10 células, H-016) é relatado ao lado.
- **Variância entre tentativas:** a dos Sharpes anualizados da carteira de 3 pares (`base`, exposição 1) de todas as tentativas com série disponível. Tentativas sem série são listadas, entram no N e ficam fora da variância.
- **Séries:** o DSR decisório usa **retornos semanais** (sem sobreposição), para reduzir a autocorrelação de posições longas. O DSR diário é relatado (Q-02).
- **Limite do método:** o DSR discrimina pouco aqui. A H-015 teve DSR de 0,999 e falhou na validação. Ele funciona como filtro mínimo, não como evidência.
- **PBO:** não se aplica, porque não há grid de seleção (Q-03).

## 7. Ganho marginal dos componentes

### 7.1 Escada de ablação (IS, mesmos custos e pares)

| Passo | Configuração | Pergunta |
|---|---|---|
| A0 | Buy-and-hold | Referência |
| A1 | SMA 200d | O filtro de tendência agrega sobre o B&H? |
| A2 | Donchian voto 2/4 | O voto de canais agrega sobre a SMA 200d? |
| A3 | A1 + sizing, contra A1 com peso embaralhado | A informação de volatilidade agrega? |
| A4 | A2 + sizing, contra A2 com peso embaralhado | Idem, no ensemble |
| A5 | 50% A2 + 50% TSMOM voto | Há diversificação entre famílias? |
| A6 | Membros isolados e voto sem (20, 10) | Algum membro é o único responsável? (só relatado) |

### 7.2 Medida

- **Estatísticas:** ΔSharpe, ΔSortino, ΔDD MTM, ΔCVaR95, Δturnover e Δcusto pago.
- **IC:** IC95% de ΔSharpe por bootstrap pareado de blocos (mesmos índices nas duas séries).
  - O bloco **decisório é de 60 dias**, coerente com posições de semanas a meses.
  - Relatados: 10, 20 e 40 dias (Q-04).
  - 4000 reamostras, seed 1.

### 7.3 Rótulo "componente útil" (D-5)

- **Critério:** no IS e em `base_2x`, ΔSharpe > 0 na carteira de 3 pares **e** IC95% de ΔSharpe com limite inferior > −0,10, **e**, para o sizing, ΔSharpe > 0 também contra o peso embaralhado.
- **Interpretação:** é um rótulo fraco (Q-05). Os pares são correlacionados (§9.3), há 7 comparações sem correção de multiplicidade e a redução de DD pelo sizing é quase mecânica. O relatório diz isso ao lado de cada rótulo.
- **Uso:** um componente sem o rótulo não é usado nas hipóteses seguintes.

## 8. Critérios de decisão

### 8.1 Passar no IS (pré-requisito para ler a validação)

Todos são obrigatórios e pré-registrados. O objeto avaliado é **uma estratégia executável** (§1.1).

1. Gates de `gates.json` em todos os pares (provisórios enquanto D-7 estiver aberto).
2. ≥ 30 trades por par, ou o critério de D-2, se aprovado antes do registro.
3. Sharpe em `base_2x` acima do buy-and-hold **e** da `Sma200Baseline` na mesma exposição (§6.1), na carteira de 3 pares.
4. DSR semanal ≥ 0,95 com o N de §6.3.
5. Estabilidade de §4.2 (D-4).
6. Lucro sem o melhor trade > 0 em todos os pares. Top 5 trades ≤ 100% do lucro em pelo menos 2 pares (D-6).
7. Dependência de ciclo, relatada (D-6): soma dos log-retornos por ciclo, com a participação calculada sobre a soma dos ciclos positivos. Ciclos negativos aparecem separados.

### 8.2 Depois da validação

- **Candidata para dry-run congelado** (experimento, não prontidão), quando:
  - houver `candidate_for_portfolio` em todo par × split;
  - a consistência for ≥ 0,25 e a correlação ≤ 0,7 (`portfolio.json`);
  - **e** a hipótese não for de "validação descritiva" (TSMOM, §2.4; SMA 200d, §2.1).
- **Exclusão por correlação:** é registrada como informação de risco, não como falha da estratégia. É provável entre regras de tendência (§9.3, R-12).
- **Aprimorar:** só com o mecanismo de falha identificado **no IS**, uma variante disponível e uma hipótese nova cujo N inclui a anterior. A hipótese nova cita qual a motivou (R-16).
- **Reprovar:** qualquer gate falho na validação, ou dependência de um trade ou de um ciclo. Arquivar; nada é apagado.
- **Inconclusiva:** menos de 30 trades com os gates positivos. É relatada com IC e **não é aprovação provisória**.

### 8.3 Holdout prospectivo (critério que faltava, Q-07)

- **Quando:** avaliação única, não antes de 2027-04-21, com ≥ 30 trades fechados somados entre os pares (`holdout.json`).
- **Quem é avaliado:** cada estratégia congelada e a `Sma200Baseline` de referência.
- **Medida:** retorno líquido da carteira de 3 pares em custo base e DD MTM.
- **Classificação pré-registrada:**
  - **Consistente:** DD MTM ≤ 25% e retorno dentro da faixa de 5% a 95% da distribuição bootstrap do IS para o mesmo número de dias (blocos de 60 dias, seed 1).
  - **Inconsistente:** retorno abaixo do percentil 5 ou DD MTM > 25%.
  - **Inconclusiva:** menos de 30 trades. Para regras lentas é o resultado mais provável em 6 a 12 meses: a SMA 200d faz cerca de 10 trades por ano somando os 3 pares.
  - D-9 decide se estratégias lentas podem estender a avaliação até 2028-10-21.
- **Leitura:** "consistente" quer dizer que o comportamento ao vivo simulado não contradiz o backtest. **Não é aprovação para operação real.** Essa passagem é uma decisão separada do usuário, fora do lab.

## 9. Limitações estatísticas e vieses

1. **Data snooping.** Cerca de 47 regras usaram a mesma exploração, e as famílias desta rodada foram escolhidas depois de ver que tendência funcionou. A validação é semi-contaminada, e o desenho do TSMOM usa informação dela. Consequência: IS e validação podem **reprovar** com força, mas não demonstrar edge. O protocolo produz reprovações fortes, descrições de estabilidade e uma checagem prospectiva de consistência (`quant.md` §D).
2. **Poder.** O erro-padrão do Sharpe é ≈ 0,46 com 7 anos e ≈ 0,81 com 2,3 anos (aproximação de Lo, 2002). Detectar um Sharpe de 1 contra 0 na validação tem poder ≈ 45%. Regras lentas têm de 15 a 35 trades por par no IS. O gate de 30 trades torna a SMA 200d inelegível no IS para BTC e ETH, e possivelmente o voto Donchian.
   - **D-2:** o usuário decide antes de executar.
   - O alerta do risco (R-17): baixar a barra favorece exatamente as estratégias preferidas. Se houver critério alternativo, o gate original é relatado ao lado.
3. **Pares dependentes.** A correlação diária com o BTC é 0,79 (ETH) e 0,64 (BNB), e chega a 0,91 e 0,81 nos últimos 365 dias (`scenarios.json`). "2 de 3 pares" é, em boa parte, uma observação só. Os pares são sobreviventes, e o BNB foi escolhido por baixa correlação.
4. **Execução.** Stops e saídas são preenchidos no preço do backtest, sem gap. Não há fills parciais nem latência. A exchange tem 28 lacunas de até 33 h no BTC 1h, toleradas. O corte diário às 00:00 UTC é arbitrário e cai numa hora de volume baixo. O stake é arredondado em ~0,14%. O overlay de sizing ignora o stake mínimo da exchange.
5. **Métricas.** O DD do gate ignora a posição aberta: a calibração pode deixar o DD MTM acima de 25%. Na exploração, a H-009 calibrada tem MTM de 32% no BNB (R-03). DSR e PBO têm pouco poder discriminativo. O bootstrap com menos de 100 observações gera ICs largos.
6. **Correlação entre candidatas.** SMA 200d, Donchian, TSMOM e H-009 são todas de tendência. A H-009 fica 89% a 93% do tempo em posição junto com a SMA 200d, e a correlação diária no BNB é 0,71. A regra de ≤ 0,7, por ordem de ID, provavelmente deixa no máximo uma estratégia de tendência na carteira. **Antes de registrar, mede-se a correlação no IS** entre a SMA 200d, a H-009 e o voto Donchian, para saber se uma carteira vazia é o resultado esperado (R-12).
7. **Não estacionariedade.** Mudanças de microestrutura (ETFs de BTC em 2024, derivativos) podem invalidar padrões de 2017-21. O ciclo 2023+ é relatado à parte.

## 10. Reprodutibilidade

- **Manifesto por execução:** imagem e versão do Freqtrade, comando, SHA-256 de dados, estratégia e configuração, cenário, exposição, seed e commit git.
- **Parâmetros fixos:** seed 1; 4000 reamostras (1000 permutações para o peso embaralhado); blocos de 3 trades (calibração, regra atual) e de 60 dias (ICs diários).
- **Registro antes de executar:** regra, sensibilidades, N, warm-up, critérios com números e a versão do protocolo.
- **Rastreabilidade:** cada célula de relatório cita o arquivo de origem. Nada é sobrescrito; decisões antigas viram `decision.superseded-*`.
- **Comparabilidade:** as mesmas janelas por par, os mesmos 5 cenários, as mesmas convenções de exposição (§4.1, passo 4; §6.1) e as mesmas definições de métrica (`lab/analytics.py`, `lab/returns.py`).

## 11. Decisões pendentes do usuário

| ID | Decisão | Proposta |
|---|---|---|
| D-1 | Liberar `custom_stake_amount` para executar o sizing? | Não por ora: overlay teórico; decidir só se §7.3 der o rótulo |
| D-2 | Mínimo de trades para regras diárias | Manter o gate; regras lentas ficam inconclusivas |
| D-3 | Stop de catástrofe | Removido nesta versão (§2.0) |
| D-4 | Estabilidade por ano | Sharpe > 0 em ≥ 2/3 dos anos com posição; detector, não tolerância |
| D-5 | Rótulo "componente útil" | §7.3 |
| D-6 | Concentração | Top 5 ≤ 100% do lucro em ≥ 2 pares; ciclo só relatado |
| D-7 | Aprovar os limites PROPOSED de `gates.json` e `portfolio.json` | Pendente |
| D-8 | Incluir o TSMOM voto {60, 120, 240} com validação descritiva | Incluir, como alternativa contaminada |
| D-9 | Dry-run de referência da `Sma200Baseline`; avaliação estendida até 2028-10-21 para regras lentas | Sim e sim |
| D-10 | Teto de DD MTM (além do gate) | Relatar sempre; opcional: MTM ≤ 35% como critério pré-registrado |

## 12. Fluxo resumido

Registro → implementação e causalidade → checagens → exposição → IS (métricas, ablação, estabilidade) → revisão → decisão IS → **uma** leitura da validação → decisão → dry-run congelado (experimento) → holdout (≥ 2027-04-21) → classificação consistente / inconsistente / inconclusiva.

Nada disso aprova operação real.

## 13. Resposta às revisões independentes

| Achado | Tema | Resposta nesta versão |
|---|---|---|
| V-1, V-2, Q-14, R-07 | Ensemble e overlay não cabem no harness (um arquivo por hipótese; gates leem exports) | Ensemble virou voto numa estratégia (§2.2); sizing virou overlay não decisivo (§1.1, §2.3) |
| V-3 | Regra do Donchian ambígua | Máxima e mínima diárias com `shift(1)`, estado de dois níveis, entrada por nível, teste de estado no warm-up, sem stop (§2.0, §2.2) |
| V-4, Q-15 | TSMOM desenhado após a validação da H-016 | Contaminação declarada; validação descritiva; N inclui a H-015 e a H-016; D-8 |
| V-5 | "Família separada" zera a penalidade | N por mecanismo relatado; N decisório = total do lab (§6.3) |
| V-6, V-7, Q-14 | Assinatura de `returns`; convenção de exposição | Nova interface declarada (§1.3); exposição única calibrada por estratégia; benchmark na mesma exposição (§6.1) |
| V-8, Q-13, Q-18 | Definições do peso de vol; comparador | Definições exatas; peso embaralhado como comparador principal (§2.3) |
| V-9, Q-08, R-17 | Gate de 30 trades contra regras lentas | Explicitado; D-2; gate original sempre relatado |
| V-10, Q-16 | SMA 200d candidata de si mesma | Referência no IS e na validação; candidata só prospectiva (§2.1) |
| V-11, Q-09 | Walk-forward de regra fixa; anos sem posição; 2024 parcial | Rotulado como descrição do IS; anos fora de posição excluídos; 2024 marcado (§4.2) |
| V-12, Q-04 | Bootstrap pareado e bloco de 20 dias | Mesmos índices nas duas séries; bloco de 60 dias decisório; teste Y = X (§1.3, §7.2) |
| V-13, Q-01, Q-02 | N e variância do DSR; autocorrelação | N decisório total; variância definida; DSR semanal (§6.3) |
| Q-03 | PBO sem grid | Declarado não aplicável |
| Q-05 | Critério de componente fraco | IC com limite inferior; peso embaralhado; ressalva obrigatória (§7.3) |
| Q-06 | Regra IS→OOS ≤ 50% sem poder | Tornada informativa (§4.3) |
| Q-07 | Holdout sem critério | Critério consistente / inconsistente / inconclusiva (§8.3); D-9 |
| Q-10, R-13 | Dependência de ciclo mal definida | Log-retornos; denominador explícito; só relatado; top 5 decisório (§8.1) |
| Q-11 | Membros "clássicos" | Reescrito: só (20,10) e (55,20) são Turtle |
| Q-12, R-05 | Stop de 20% sem justificativa | Removido |
| Q-17 | Rebalanceamento do benchmark | O mesmo esquema para estratégia e B&H (§6.1) |
| R-01, R-03 | DD MTM fora dos limites e da calibração | Sempre lado a lado; rótulo quando passar de 25%; D-10 |
| R-02 | 40% no D-4 | Removido; o D-4 é só detector |
| R-06 | Duração do drawdown; break-even fora do intervalo | Incluídos (§5, §6.2) |
| R-08, R-09, R-11 | Execução, lacunas, fronteira | §9.4 |
| R-10 | Liquidez inicial do BNB | Sensibilidade sem o primeiro ano e stress isolado (§5) |
| R-12 | Correlação ≤ 0,7 exclui as tendências | Medição prévia no IS; exclusão registrada como risco (§8.2, §9.6) |
| R-14 | Pares como votos independentes | §9.3 |
| R-15 | Linguagem de prontidão; candles pós-corte | Regra de apresentação no topo; teste contra o holdout (§1.3, §3) |
| R-16 | Aprimoramento infla o N | N inclui a anterior; citação obrigatória (§8.2) |
| R-18, R-19, Q-19, Q-20, V-14 a V-16 | Notas | Incorporadas onde aplicável (break-even do membro 20/10 em A6; datas por par; `dossier.py` em `research/tools/`) |

Conclusão dos revisores, mantida aqui sem atenuar: mesmo cumprido à risca, este protocolo **não pode demonstrar** que uma regra tem Sharpe positivo fora da amostra com os dados históricos. Ele pode reprovar com força, descrever estabilidade e, a partir de 2027, checar a consistência prospectiva.
