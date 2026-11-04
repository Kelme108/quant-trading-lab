# Revisão quantitativa do protocolo de validação v3 (rascunho 1)

Escopo: apenas metodologia. Nenhum resultado de estratégia foi calculado e nada aqui recomenda operar. Documento revisado: `docs/protocolo-validacao-v3.md`. Arquivos de apoio lidos: `lab/config/gates.json`, `lab/config/portfolio.json`, `lab/config/splits.json`, `lab/config/holdout.json`, `lab/stats.py`, `lab/walkforward.py`, `lab/bootstrap.py`, `lab/returns.py`, `lab/costs.py`, `research/grids/H-015-report.md`, `docs/relatorio-auditoria-estrategias.md` (trechos). Não li `validator.md`, `risk.md` nem arquivos de resultado de validação.

Aritmética usada abaixo (ilustrativa, não é resultado de estratégia): erro-padrão do Sharpe anual ≈ sqrt((1 + 0,5·SR²)/T), T em anos (aproximação de Lo, 2002, sem correção de autocorrelação nem de caudas). Para SR = 1: T = 7 dá ≈ 0,46; T = 2,3 dá ≈ 0,81.

Legenda: **blocking** = o protocolo não pode ser executado ou concluído de forma não ambígua sem corrigir; **warning** = enfraquece a conclusão ou cria grau de liberdade; **note** = observação.

---

## A. Solidez estatística

**Q-01 (blocking) — N do DSR e a variância entre tentativas não estão definidos (§6.3, §6.4, §8.1 item 4).**
- §6.4 diz que N é "todas as configurações já testadas na família, inclusive variantes anteriores e membros de ensemble", mas §2.2 diz que "o N do DSR é o tamanho real de tentativas da família, não 4". Não fica claro se N é maior ou menor que 4, nem qual número entra no critério. O N de 47 regras é só "sensibilidade relatada", então não decide nada.
- `lab/stats.py:62-71` exige também a **variância dos Sharpes entre as tentativas** (`trial_sharpe_variance`). O protocolo não diz quais séries a compõem. Para ensemble sem grid, essa variância não existe de forma natural. Sem ela, SR0 é arbitrário e o DSR é manipulável pela escolha do conjunto de referência.
- Tentativas ocultas que deveriam contar e hoje não contam: a sensibilidade de SMA (100/150), de σ* (30/50%) e janela (20/60), cada membro isolado (A6), o ensemble sem o membro de 20 dias, as combinações A1 a A5, o grid TSMOM da H-015 (10 células, `research/grids/H-015-report.md`) e a H-016, e a H-002 (Donchian 1h, rejeitada; `docs/relatorio-auditoria-estrategias.md`, linhas 76-78). A H-002 é tratada como "família separada" para o orçamento de variantes (§0 item 6), mas é a mesma ideia de canal de preço e entra no mesmo histórico.
- Correção sugerida: fixar uma única regra numérica de N (por exemplo, N = 47 + células novas) como critério decisório, e declarar de onde vem a variância entre tentativas.

**Q-02 (warning) — O DSR ≥ 0,95 discrimina pouco neste desenho (§8.1 item 4).**
- O H-015 passou com DSR 0,9992 (N = 10) e PBO 0,31 e mesmo assim falhou na validação (`research/grids/H-015-report.md`, tabela IS e seção "Validação"). Com ~7 anos de retornos diários (erro-padrão do Sharpe ≈ 0,46 para SR = 1), qualquer Sharpe acima de ~1 supera SR0 mesmo para N grande. O critério não filtrou o caso concreto mais próximo.
- `probabilistic_sharpe` usa sqrt(n−1) com n = dias (`lab/stats.py:59`) e supõe retornos diários independentes. Regras de tendência mantêm posição por semanas ou meses; os retornos diários são fortemente autocorrelacionados e o n efetivo é muito menor (da ordem do número de episódios, não de dias). O DSR fica inflado. §9.5 menciona o pressuposto mas não o trata.
- Dias fora de posição entram como zeros e alteram assimetria e curtose usadas no denominador; vale relatar o DSR também só sobre dias em posição ou com n efetivo corrigido.

**Q-03 (warning) — PBO não é definido para regras fixas e é instável com grids pequenos (§6.3, §8.1 item 5).**
- Para SMA 200, Donchian Ensemble e TSMOM ensemble não há seleção; PBO só se aplicaria a grids, e o protocolo não declara nenhum grid novo. O item 5 de §8.1 fica vazio na prática, e o protocolo não diz isso.
- Com n configurações pequeno, o ranque relativo em `pbo_cscv` é `rank/(n+1)` (`lab/stats.py:132-133`), logo só assume n valores discretos. Com n = 2 a 4 o PBO é grosseiro. Além disso, 16 fatias de ~160 dias com episódios de tendência que cobrem várias fatias tornam as 12.870 combinações altamente dependentes; o PBO é mais estreito do que parece.
- O limite PBO ≤ 0,5 é o nível de um sorteio ao acaso (mediana). Não é uma barra de proteção. O H-015 (0,31) passou nela e falhou fora da amostra.

**Q-04 (warning) — Bootstrap pareado em blocos de 20 dias (§7.2).**
- Não há justificativa para 20. Retornos diários de uma regra de tendência dependem da posição, que dura de dezenas a centenas de dias (SMA 200, Donchian 100/50 e 200/100, TSMOM 240). Bloco de 20 dias é curto para esse tipo de dependência, e o IC resultante tende a ser estreito demais (anti-conservador). Para a validação (~800 dias, ≈ 40 blocos) o IC pareado é ainda menos confiável.
- Pedir: relatar sensibilidade a 10, 20, 40 e 60 dias, ou bootstrap estacionário com bloco ótimo (Politis-White), e escolher a regra antes da execução.
- `lab/stats.py:146` (`block_bootstrap_ci`) trabalha com uma série e uma estatística; o pareamento exige reamostrar índices comuns às duas séries e depois calcular ΔSharpe. Isso é código novo (`lab/marginal.py`, §1.2); a exigência de teste do protocolo ("seed fixa; IC reprodutível") não cobre a corretude do pareamento. Incluir teste: com Y = X o ΔSharpe e o IC devem ser exatamente 0.
- Os blocos são móveis, sem circularidade, e `n_resamples = 4000`, `seed = 1` são adequados. Observação menor.

**Q-05 (warning) — Critério de componente útil (D-5, §7.3) quase não discrimina.**
- "ΔSharpe > 0 e Δdrawdown ≤ 0 em pelo menos 2 de 3 pares" é uma estimativa pontual, sem IC. Sob hipótese nula (componente sem efeito), cada par tem ~50% de chance de ΔSharpe > 0, e os pares têm correlação de 0,64 a 0,79 com o BTC (§9.3), então "2 de 3" passa por acaso com probabilidade acima de 50%.
- Para o vol sizing, Δdrawdown ≤ 0 é quase mecânico: reduzir peso em períodos de volatilidade alta reduz drawdown por construção. Na prática o critério reduz-se a ΔSharpe > 0 sem IC.
- São 7 degraus de ablação (A0 a A6) e vários pares de comparação, sem correção de multiplicidade. O protocolo admite honestamente que nenhum IC deve ficar acima de zero (§7.3, último parágrafo). Isso é correto, mas implica que "componente útil" é uma etiqueta fraca, não evidência. Recomendo que o relatório diga isso explicitamente em cada rótulo.
- "Não piora o Sharpe em mais de 2 dos 5 ciclos": ciclos têm 1 a 3 anos, Sharpe por ciclo tem erro-padrão ≥ 0,5 a 1,0. A contagem é ruído.

**Q-06 (warning) — Regra de queda IS → OOS do Sharpe ≤ 50% tem pouco poder e é mal definida (§4.3, §8.2).**
- Poder: com SR = 1 e T = 2,3 anos, o erro-padrão do Sharpe OOS é ≈ 0,81. Uma queda de 50% (de 1,0 para 0,5) está a ~0,6 erro-padrão. Se o Sharpe verdadeiro fosse igual ao do IS, a chance de reprovar só por ruído seria da ordem de um quarto (aproximação normal: P(Z < −0,62) ≈ 27%). Por outro lado, um Sharpe verdadeiro metade do IS passa em cerca de metade das vezes. A regra é ruidosa nos dois sentidos.
- O Sharpe do IS é viesado para cima pelo efeito do vencedor (seleção da família, §9.1; ~47 regras). Uma queda de 50% é esperada sob nulo parcial, então reprovar em 50% não "detecta overfitting"; mede, em parte, regressão à média.
- Indefinições: qual Sharpe (por par, carteira de 3 pares, `base` ou `base_2x`); o que fazer se o Sharpe IS for ≤ 0 ou pequeno (razão sem sentido); como tratar OOS negativo. Em §4.3 a comparação é de "lucro por dia" e Sharpe; em §8.2 só do Sharpe.
- A janela de validação tem um regime específico (por exemplo, o relatório do H-015 mostra BTC e BNB em alta e ETH em queda na validação; `research/grids/H-015-report.md`). Uma queda de Sharpe pode ser regime, não overfitting.

**Q-07 (blocking) — Poder do conjunto de critérios e inviabilidade do holdout (§3, §8.3, §9.2).**
- Poder da validação: para detectar SR = 1 contra 0 com T = 2,3 anos, o teste unilateral a 5% tem poder da ordem de 45% (SE sob nulo ≈ 1/sqrt(2,3) ≈ 0,66; estatística esperada ≈ 1,5 contra corte 1,645). Com 15 a 35 trades por par em 7 anos (§9.2) e 5 a 15 na validação, a decisão "inconclusiva" será o resultado típico, e §8.2 já diz que < 30 trades é inconclusiva.
- Holdout: a SMA 200 teve 19, 18 e 31 trades em ~6,9 anos (`research/audit/H-009-exploration-metrics.json`, citado em §0 item 4); isso soma 68 trades em ~6,9 anos entre os 3 pares, ou cerca de 10 por ano. Em 12 meses (data preferida 2027-10-21, `lab/config/holdout.json`) o total esperado fica longe de 30. Estratégias lentas (SMA 200, Donchian 100/50 e 200/100) quase certamente ficarão "inconclusivas" mesmo na data preferida. O mínimo de 30 trades é "somado entre pares", e os pares têm correlação 0,64 a 0,79 (§9.3), então não são trades independentes. Por isso trades somados superestimam informação.
- §8.3 **não define critério de aprovação do holdout** (qual métrica, qual limiar, qual IC). §4.3 diz que "a aprovação definitiva só pode vir dele". Sem critério pré-registrado do holdout, o protocolo não tem fim verificável. Esse é o ponto que mais precisa ser fechado antes de aprovar o protocolo.
- Há ainda multiplicidade no holdout: várias estratégias congeladas, cada uma avaliada uma vez, sem ajuste.

**Q-08 (blocking) — O gate de ≥ 30 trades por par é incompatível com os candidatos principais (§0 item 4, §8.1 item 2, D-2, §9.2).**
- §9.2 admite que a SMA 200 falha no IS em BTC e ETH (19 e 18 trades). O mesmo vale para Donchian 100/50 e 200/100 e para o TSMOM 240. Com D-2 pendente, o protocolo pode não conseguir aprovar nenhum candidato lento no IS, e o resultado "inconclusiva" é determinado pelo gate, não pelo desempenho.
- Contagem de trades do ensemble não está definida: somar trades dos 4 membros (quase sempre sobrepostos no mesmo episódio) inflaria a contagem sem acrescentar informação independente. Definir a contagem por episódio de posição agregada.
- O critério alternativo sugerido (≥ 500 dias e ≥ 8 episódios, §9.2) é fraco: 8 episódios não sustentam IC útil. Se for adotado, deve vir com a regra de decisão baseada em IC e ser registrado antes de qualquer execução (o protocolo já diz isso; manter).

**Q-09 (warning) — Walk-forward para regras fixas é estabilidade por subperíodo, não validação (§4.2, D-4).**
- O protocolo reconhece que não há reotimização (§4.2) e que as famílias foram escolhidas depois de ver que tendência funciona (§9.1). Então "4 de 6 anos com Sharpe > 0" não é evidência fora da amostra; é uma descrição do IS. Deve ser rotulado assim nos relatórios.
- Com `lab/walkforward.py:18-29`, os folds vão de 2019 a 2024; o último ano termina em 2024-07 (≈ 0,5 ano), e o primeiro treino (2017-08 a 2018-12) tem só um ano de baixa. "6 anos" inclui um semestre. Para TSMOM 240 e Donchian 200/100 o aquecimento de 200-240 dias consome parte de 2017-18 (BNB começa em 2017-11).
- "Sharpe anual > 0": uma regra de tendência em caixa o ano todo tem retorno 0 e Sharpe 0 (`stats.sharpe` devolve 0,0 para série constante, `lab/stats.py:30`), que não é > 0. Anos de baixa (2018, 2022) deixam a estimativa em torno de zero; a contagem 4 de 6 depende de anos em torno de zero. Definir tratamento de Sharpe = 0.
- "Nenhum ano com drawdown marcado a mercado > 40%": depende da exposição escolhida (ver Q-14). Em exposição 100%, o H-015 tinha drawdown de 74-85% por par (`research/grids/H-015-report.md`); com exposição calibrada o número muda. O critério mede a calibração tanto quanto a regra.
- Para os grids (se houver), `walk_forward` escolhe a célula por Sharpe de treino, sem embargo, e o treino do primeiro fold é curto. Adequado como procedimento; só atentar para que o OOS concatenado inclua os anos de baixa.

**Q-10 (warning) — Dependência de ciclo (D-6, §8.1 item 7).**
- "Nenhum ciclo responsável por mais de 60% do lucro" não é bem definido quando há ciclos negativos (a participação pode passar de 100%) e quando o lucro é composto (a ordem importa). Usar soma de retornos logarítmicos ou lucro aditivo por ciclo, e tratar ciclos negativos.
- Regras de tendência em cripto concentram o lucro em poucos ciclos (por exemplo, no H-015 a diferença se concentra em 2019 e 2020-21; `research/grids/H-015-report.md`). Um limite de 60% pode eliminar quase toda tendência por construção. Se for essa a intenção, dizer. Se não, calibrar antes de ver resultados.

---

## B. Parâmetros e graus de liberdade ocultos

**Q-11 (warning) — Membros do Donchian Ensemble: "clássicos" é só parcialmente verdadeiro (§2.2).**
- (20, 10) e (55, 20) são os pares clássicos do sistema Turtle. (100, 50) e (200, 100) não são pares canônicos; seguem uma razão M ≈ N/2 e espaçamento aproximadamente geométrico, escolhas do autor. A afirmação "são os horizontes clássicos" deve ser reformulada como decisão de projeto.
- A decisão foi tomada depois de ver o histórico (§9.1), logo não está livre de seleção. O que mitiga é ser pré-declarada e contar como tentativa; mas §6.4 não diz quantas.
- O membro (200, 100) tem comportamento muito próximo ao da SMA 200 (tendência de longo prazo). Isso tem duas consequências: o passo A2 contra A1 mede pouco além de ruído e diversificação de horizonte, e o critério de correlação ≤ 0,7 com a `Sma200Baseline` (§8.2, `portfolio.json`) pode reprovar o ensemble por desenho. Vale prever essa colisão.
- A sensibilidade "sem o membro de 20 dias" e A6 ("algum membro é o único responsável?") são, na prática, um grid de 5 a 9 células sobre o qual alguém pode comentar. Se qualquer decisão depender delas, é seleção. Declarar que não podem alterar a decisão.

**Q-12 (warning) — Stop de catástrofe de 20% (D-3, §2.2) é um parâmetro novo sem justificativa ex ante nem regra de reentrada.**
- 20% está longe do que o canal já limita para membros rápidos (20, 10), e atua principalmente nos lentos (100/50, 200/100), onde as perdas por trade são maiores. O valor não vem de nenhuma teoria e é, na prática, um parâmetro livre.
- Não está dito o que ocorre após o stop com o preço ainda acima da máxima de N dias: reentrada imediata no candle seguinte (whipsaw com custo) ou espera por novo sinal. Isso muda o número de trades e o custo.
- §9.4 reconhece que stops preenchem sem gap; em cripto, quedas de 20% em um dia com gaps de execução ocorrem, e o stop subestima a perda.
- A sensibilidade ao stop não está prevista. Se o stop for decisivo para o gate de drawdown, é parâmetro ajustado ao resultado; se não for, pode ser removido.

**Q-13 (warning) — Vol sizing: parâmetros "redondos", mas escolhidos com conhecimento dos dados, e a grade de sensibilidade é uma grade oculta (§2.3).**
- "σ* = 40%, abaixo da volatilidade histórica do BTC" usa conhecimento do histórico. Com σ* abaixo da volatilidade típica, w = min(1, σ*/σ̂) fica abaixo de 1 na maior parte do tempo; o efeito é sobretudo redução de exposição média. Para ETH e BNB (volatilidade maior que a do BTC) w médio será menor, então o mesmo σ* implica exposições diferentes por par, o que prejudica a comparação entre pares.
- Sensibilidade relatada: σ* ∈ {30, 50%} e janela ∈ {20, 60}. Se for 3 × 3 = 9 células (ou 5 se variadas uma por vez), aplicadas a SMA e ao ensemble, são de 10 a 18 configurações que o protocolo declara "não selecionáveis" mas que serão lidas. Elas devem contar em N (Q-01) ou não ser executadas.
- Peso fixo durante o trade (§2.3) é uma limitação importante, não detalhe: trades de tendência duram dezenas a centenas de dias, e a volatilidade na abertura é um estimador defasado para boa parte do trade. O que se testa não é volatility targeting no sentido da literatura (reescalonamento contínuo), e os resultados não se transferem a ele. Além disso, entradas por rompimento ocorrem com frequência em períodos de volatilidade em expansão, de modo que σ̂ no momento da entrada tende a ser alta e w baixo exatamente nos trades de maior movimento. Isso pode produzir redução sistemática de lucro, atribuída ao "sizing". Relatar a correlação entre w e o retorno do trade.
- Janela de 30 dias com 30 observações: erro relativo de ≈ 13% no σ̂ (1/sqrt(2·30)); aceitável, mas gera ruído de peso entre trades parecidos.

**Q-14 (blocking) — Convenção de exposição indefinida (§4.1 passo 4, §2.2, §2.3, §6.1 item 3, §8.1).**
- O passo 4 calibra a exposição por regra (`bootstrap.choose_exposure`, `lab/bootstrap.py:102-123`, p95 do drawdown de trades fechados ≤ 25% em todos os pares ao mesmo tempo). O protocolo não diz como isso se combina com: o ensemble (cada membro a 1/4), o sizing (w ≤ 1) e a SMA 200 de referência "com a mesma exposição da estratégia".
- Cada regra recebe uma exposição diferente (o H-015 ficou em 15%, H-008 em 20%, H-016 em 15%, `docs/relatorio-auditoria-estrategias.md`). Lucro em moeda, drawdown, gate de lucro mínimo (1,0 em 100 USDT, `gates.json`) e "DD ≤ 25%" dependem diretamente desse número. O Sharpe diário é quase invariante à escala (resto em caixa a 0%), mas drawdown, CVaR, lucro líquido e a distância ao limiar de custo não são.
- Comparações cruzadas entre estratégias (A1 contra A2, ensemble contra TSMOM) só são comparáveis se a convenção for única e declarada, por exemplo: todas avaliadas a exposição 100% para métricas de risco e ao nível calibrado só para os gates. Hoje isso não está escrito.
- Também falta dizer **qual objeto os gates recebem** para ensemble e overlay: `lab/gates.py` lê backtests Freqtrade, e §9.6 diz que o ensemble e o sizing são "overlays de análise", não executados pelo Freqtrade. Então "gates em todos os pares" (§8.1 item 1) para esses objetos não tem entrada definida (lucro em moeda, contagem de trades, lucro sem o melhor trade). Defini-lo antes de registrar.

**Q-15 (blocking) — TSMOM {60, 120, 240}: o desenho foi influenciado pela validação (§2.4, D-8).**
- O próprio protocolo afirma que a H-016 (N30) leu a validação e o lucro por dia caiu de 63% a 96%. Escolher horizontes mais lentos **depois** dessa leitura usa o resultado da validação para desenhar a regra. É a forma mais direta de vazamento de seleção do documento. A cláusula "não pode reescolher entre os horizontes do grid da H-015" não resolve: 60 e 120 são células desse grid, cujos Sharpes no IS já foram vistos (N60 1,23, N120 1,08; `research/grids/H-015-report.md`), e 240 está fora do grid, nunca testado, mas escolhido com a informação de que o rápido falhou.
- Efeito prático: a validação desta variante é contaminada de duas formas, pelo histórico e pelo desenho. §9.1 reconhece o primeiro; o segundo precisa ser dito. Consequência para o DSR: N deve incluir as 10 células de H-015, a H-016 e as novas.
- O aquecimento de 240 dias encurta o IS efetivo (2017-08 a 2018-04 sem sinal), e o primeiro fold do walk-forward (2019) treina com pouco histórico.
- A ordem do orçamento de família (1 variante restante) significa que, se esta falhar, a família se encerra; isto pressiona a favor de afrouxar critérios. Registrar que isso não é permitido.

**Q-16 (note) — SMA 200 como candidata (§2.1).**
- O protocolo diz que a validação da SMA 200 já foi vista e que a única evidência nova é o holdout. Mas o fluxo de §4.1 e §8.2 prevê ler a validação da SMA 200 como se fosse uma leitura única. Dizer explicitamente que, para SMA 200, o passo de validação é só descritivo.
- Sensibilidade 100/150: escolha de dois valores a mais, é tentativa para o DSR (Q-01).

---

## C. Comparabilidade

**Q-17 (warning) — Benchmark de carteira de 3 pares e rebalanceamento (§6.1 item 4, §8.1 item 3).**
- §8.1 item 3 pede Sharpe (base_2x) acima de buy-and-hold e da SMA 200 "na carteira de 3 pares com pesos iguais". O relatório do H-015 usa carteira de pesos iguais "com rebalanceamento diário" (`research/grids/H-015-report.md`, ressalvas), e o §6.1 item 4 descreve o benchmark como buy-and-hold, sem rebalanceamento. Rebalancear diariamente cria um ganho de diversificação (e um custo de rebalanceamento) que o buy-and-hold sem rebalanceamento não tem. Estratégia e benchmark precisam do mesmo esquema de rebalanceamento e do mesmo custo de rebalanceamento.
- Comparar o Sharpe de uma carteira que fica parte do tempo em caixa com o de buy-and-hold 100% investido é válido (caixa a 0%) mas ignora o retorno do caixa e o risco de cauda diferente; relatar também Calmar e CVaR (já listados em §6.2).
- "Sharpe acima do buy-and-hold" no IS 2017-2024 é uma barra baixa para tendência porque buy-and-hold teve drawdowns de 70-85% no período; a estratégia ganha em Sharpe e Calmar por estar em caixa nesses períodos. Isso é fato histórico, não indicação de alfa; o protocolo já cita o caso da ETH no H-016, mas §8.1 não incorpora.

**Q-18 (warning) — Exposição média equivalente para o sizing (§2.3 "Comparação obrigatória", §7.3).**
- "Exposição constante igual à exposição média do overlay" admite pelo menos três definições: média de w por trade, média de w ponderada pela duração, ou média diária de capital alocado (incluindo dias fora de posição). Os resultados diferem, porque w é correlacionado com duração e retorno (Q-13). Declarar uma única, por par e por janela, e medir o caso.
- Como o Sharpe é invariante à escala (resto em caixa), a comparação com exposição constante equivalente muda quase nada no ΔSharpe e só afeta drawdown e CVaR. Ou seja, o teste "o ganho permanece contra a exposição equivalente" é satisfeito quase automaticamente para Sharpe. O teste informativo é comparar ΔSharpe e Δdrawdown contra o sizing com **peso embaralhado** (mesmos w, atribuídos a trades diferentes), isso isola o valor da informação de volatilidade. Sugerido.
- Calcular a média sobre a janela inteira usa informação posterior ao início, o que é aceitável para um benchmark de comparação, mas deve ser dito que o benchmark não é implementável ex ante.

**Q-19 (note) — Custos (§5).**
- A tabela de custos confere com `lab/costs.py` (efetivo por lado 0,100, 0,175, 0,250, 0,475, 0,350%; ida e volta ≈ 0,20, 0,35, 0,50, 0,95, 0,70%). Em `base_2x` o "spread total" de 0,10% e slippage de 0,10% batem com `SCENARIOS["base_2x"]`.
- O break-even de custo por interpolação entre cenários é uma aproximação; o lucro líquido é aproximadamente linear no custo por lado multiplicado pelo número de trades, então a interpolação linear é razoável, mas a extrapolação além de `stress` não. Relatar apenas dentro do intervalo coberto.
- Custo por trade do ensemble: cada membro paga em 1/4; trocas simultâneas não se compensam entre instâncias (4 bots). Se um dia o ensemble for executado numa só estratégia com netting, o custo muda; já está reconhecido em §9.6.
- O custo de ida e volta (0,35% no base) deve ser comparado com o movimento médio por trade; membros rápidos (20/10) e TSMOM 60 fazem mais trades e são os mais sensíveis. O relatório `quant` já deve apresentar essa comparação por membro (A6).

**Q-20 (note) — Coerência entre §3 e `splits.json`.**
- Datas de §3 e de `lab/config/splits.json` coincidem (exploração até 2024-07-04/05/25 conforme o par; validação até 2026-10-20; holdout a partir de 2026-10-21). A validação de BNB começa em 2024-07-25 e a de BTC em 2024-07-04; o "2024-07" do texto é aproximado. Os períodos por par diferem em até ~3 semanas, o que não afeta a lógica mas afeta a comparabilidade de "lucro por dia" entre pares (usar dias reais da janela, como `portfolio.json` faz).
- Os "últimos 12 meses" estão dentro da validação e rotulados semi-contaminados, correto segundo `holdout.json`.

---

## D. Resumo

| Tag | Achados |
|---|---|
| blocking | Q-01 (N e variância do DSR), Q-07 (poder e holdout sem critério de aprovação), Q-08 (gate de 30 trades contra candidatos lentos; contagem do ensemble), Q-14 (convenção de exposição e objeto dos gates), Q-15 (TSMOM desenhado após leitura da validação) |
| warning | Q-02, Q-03, Q-04, Q-05, Q-06, Q-09, Q-10, Q-11, Q-12, Q-13, Q-17, Q-18 |
| note | Q-16, Q-19, Q-20 |

O que o protocolo **permite concluir** se corrigido: reprovações fortes (sinal de que a regra não cobre custo, depende de um trade ou de um ciclo, ou reverte fora da amostra) e descrição de estabilidade por subperíodo.

O que **não permite concluir**, mesmo se todos os critérios forem cumpridos: evidência de que uma regra tem Sharpe positivo fora da amostra. Os motivos: família escolhida depois de ver o histórico (§9.1), ~47 regras sobre o mesmo histórico, validação já lida para ideias de tendência, 15 a 35 trades por par, pares correlacionados, DSR/PBO com baixo poder discriminativo (Q-02, Q-03), e holdout provavelmente inconclusivo em 12 meses para regras lentas (Q-07).
