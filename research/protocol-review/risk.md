# Revisão de risco do protocolo de validação v3 (rascunho 1)

Revisor: risco. Escopo: `docs/protocolo-validacao-v3.md`. Não avalia resultado de hipótese, não recomenda dimensionamento nem operação real.
Fontes lidas: o protocolo; `lab/config/gates.json`, `portfolio.json`, `holdout.json`, `scenarios.json`; `lab/costs.py`, `lab/returns.py`, `lab/bootstrap.py`; `docs/harness-fase0.md`; `research/audit/H-009-exploration-metrics.json` (somente a parte de exploração, BTC/ETH/BNB). Não li `validator.md`, `quant.md` nem arquivos de resultado de validação.

Legenda: **blocking** = deve ser corrigido antes de aprovar o protocolo; **warning** = corrigir ou aceitar explicitamente; **note** = informativo.

Limite de leitura: os números abaixo vêm só do JSON de auditoria da H-009 (que traz uma referência SMA 200d na exploração). Não há trades de SMA 200d, Donchian ensemble ou TSMOM para medir diretamente. O que é inferência está marcado.

---

## 1. Drawdown e controles de perda

**R-01 [blocking] Gate de drawdown em trades fechados, sem teto de drawdown marcado a mercado (§0.5, §6.2, §8.1.1, §9.5, D-4).**
`gates.json` (`max_drawdown.max_ratio` = 0,25) mede trades fechados. O protocolo mantém o drawdown marcado a mercado só como informativo. A própria `lab/bootstrap.py` (docstring) diz que o drawdown intratrade não aparece na lista de trades e que o valor real é "pelo menos" o medido. Para estratégia sem stop, a diferença é grande. Referências do JSON de auditoria (exploração, custo base, SMA 200d com exposição 1): drawdown marcado a mercado de 65,7% (BTC), 75,9% (ETH) e 76,9% (BNB) (`research/audit/H-009-exploration-metrics.json`, campo `sma200_exposure_1.max_drawdown`). `docs/harness-fase0.md` §5 mostra 66% no IS do BTC e 35% na validação. Uma SMA 200d pode, portanto, passar o gate de 25% em trades fechados com um drawdown real de várias vezes isso. O protocolo reconhece o problema (§9.5) mas só o relata; ele não impede que o relatório apresente "DD ≤ 25%" sem o outro número ao lado.
Pedido: (a) o relatório de cada candidata deve mostrar as duas medidas lado a lado, em toda tabela onde o gate aparece; (b) o usuário deve decidir explicitamente, e não por omissão, que a decisão de aprovar para dry-run ignora o drawdown marcado a mercado (ou adotar um teto, mesmo largo).

**R-02 [blocking] D-4 admite 40% de drawdown marcado a mercado por ano, contra um teto de 25% (§4.2).**
O critério de estabilidade ("nenhum ano com DD marcado a mercado > 40%") é mais frouxo que o ceiling do gate. Hoje o protocolo contém dois limites de drawdown incompatíveis, e o mais frouxo aparece como condição de passagem. Sem esclarecimento, um leitor pode entender que 40% é tolerável. Pedido: declarar que 40% é só um detector de falha de estabilidade, não uma tolerância de risco; ou alinhar com 25%.

**R-03 [blocking] Calibração de exposição usa drawdown de trades fechados (§4.1 passo 4; `lab/bootstrap.py`, `choose_exposure`).**
`choose_exposure` escolhe a maior exposição cujo p95 do drawdown fechado reamostrado fica ≤ 25% em todos os pares. Por construção ele subestima o drawdown marcado a mercado (docstring) e reamostra trades em blocos de 3, o que não captura a sequência de regimes. No mesmo JSON, a H-009 calibrada em 0,25 de exposição tem drawdown marcado a mercado de 10,6% (BTC), 24,7% (ETH) e 31,8% (BNB) no custo base (campo `equity.max_drawdown`). Ou seja, mesmo depois da calibração, o BNB passou do teto de 25% quando medido a mercado, e o ETH ficou no limite. O protocolo não diz se a SMA 200d e o ensemble recebem exposição calibrada, nem como esta se combina com o overlay de vol sizing (§2.3, `w ≤ 1`). Pedido: dizer se o marcado a mercado entra na calibração (como restrição adicional) ou se o resultado será rotulado "calibrado em trades fechados; marcado a mercado excede o teto" quando for o caso.

**R-04 [warning] SMA 200d sem stop (§2.1).**
Sem stop, a perda por trade é limitada só pela saída por cruzamento diário. A tabela de `harness-fase0.md` §5 mostra drawdown de 37% (2018), 45% (2019) e 65% (2020-21) a mercado no BTC. Aceitável como referência/benchmark; como candidata, depende de R-01. Em exposição constante igual à da H-009, o benchmark da própria auditoria (`sma200_same_exposure`) ainda tem 38,7% (BTC), 53,4% (ETH), 62,6% (BNB) de drawdown marcado a mercado. Não está claro, nos arquivos lidos, como esse "same exposure" é definido; não extrapolo. O ponto vale como alerta: mesmo reduzida em exposição, a SMA 200d sem stop pode ficar acima de 25% marcado a mercado.

**R-05 [warning] Stop de catástrofe de 20% no Donchian (§2.2, D-3).**
Com cada membro a 1/4 da carteira, uma perda de 20% por membro custa cerca de 5% da carteira por membro, e até 20% se os 4 forem parados juntos (inferência aritmética, ver R-07). É compatível com o teto de 25% apenas se o stop for preenchido a 20%. O backtest assume preenchimento no preço do stop, sem gap (§9.4). Em crashes de cripto (movimentos de 20% a 40% em horas existem em dados reais, como março de 2020 e o colapso FTX de 2022; conhecimento externo, não conferido nos arquivos), o preenchimento real ficaria abaixo do stop. O p95 dessa perda extra não é medido. Além disso, o stop de 20% fica distante frente à saída por canal de 10 a 100 dias: o stop só atua em quedas rápidas, e é justamente onde o backtest é mais otimista. Pedido: relatar quantas saídas foram por stop e a distribuição do slippage nessas saídas num cenário stress; reconhecer que o stop não é uma garantia de perda máxima.

**R-06 [warning] Sequência de perdas e break-even de custo (§5, §6.2).**
O protocolo pede maior sequência de perdas e break-even por interpolação, mas não define:
- a sequência de perdas em número de trades, não em duração (dias em drawdown, tempo de recuperação). O pedido mínimo da função de risco é a duração do pior trecho perdedor, não só a contagem. Para tendência diária, 9 perdas seguidas (H-009 BTC, `streaks.max_loss`) podem ocupar muitos meses.
- o break-even com 5 cenários dá apenas 5 pontos (0,10% a 0,475% por lado); com lucro negativo no stress a interpolação linear é aproximação. Dizer que é aproximada.
Pedido: incluir "dias do pior drawdown, do pico ao recorde seguinte", e extrapolar o break-even só dentro do intervalo observado, rotulando "fora do intervalo" quando ele não for atingido.

## 2. Realismo de execução

**R-07 [blocking] Ensemble de 4 instâncias e sizing pós-trade não correspondem ao que o Freqtrade executa (§1.2, §2.2, §2.3, §9.6, D-1).**
Os números do ensemble e do overlay vêm de `lab/ensemble.py` e `lab/sizing.py`, que somam curvas de `lab/returns.py` (`equity_curve` reconstrói a curva e exige que trades não se sobreponham, uma posição por par). Isso não é uma simulação de carteira. Diferenças reais que o overlay não captura:
- 4 instâncias Freqtrade têm 4 carteiras independentes, com saldo, rounding de stake (≈0,14% medido, `harness-fase0.md` §4) e `max_open_trades` próprios. O "1/4 de exposição" depende de configurar `stake_amount`/`tradable_balance_ratio` de cada instância, algo que o protocolo não especifica.
- Se duas instâncias operarem o mesmo par no mesmo dia, a posição agregada no mesmo par é um acúmulo de trades; `equity_curve` assume uma posição por par por estratégia, o que vale para cada membro, mas a soma exige verificação cuidadosa de que o stake de 1/4 foi mesmo usado.
- O sizing exige `custom_stake_amount`, proibido em `lab/strategy_check.py:48` (§0.3). Até D-1 ser decidido, todo número de A3 e A4 é teórico.
- O protocolo diz que "a diferença entre overlay e execução precisa ser medida no dry-run" (§9.6), mas dry-run só começa depois do §8.2. Logo, o §8.2 pode aprovar uma configuração cuja execução nunca foi medida. Pedido: marcar no relatório e na decisão, de forma explícita, "resultado de overlay, não executável sem D-1", e proibir que o §8.2 aprove um ensemble/sizing não executável como "pronto para dry-run" sem uma verificação de equivalência (backtest de 4 instâncias reais contra o overlay, no mesmo período do IS).

**R-08 [warning] Execução no candle seguinte, stops dentro do candle (§0.1, §5, §9.4).**
Ordens a mercado no preço de abertura do candle seguinte, sem fills parciais nem latência (§5, §9.4). Em estratégia de tendência diária o número de trades é baixo (15 a 35 por par em 7 anos, §9.2), então o custo total é pouco sensível ao slippage por trade, mas o risco está nos poucos trades grandes: a decisão do dia fecha às 00:00 UTC e a execução é na abertura da hora seguinte, justamente numa hora de volume típico baixo. O slippage do cenário base (0,05% por lado) é um palpite do protocolo, não uma medida (§5). `lab/costs.py` lembra que o backtest do Freqtrade não modela slippage nem spread: tudo entra via `--fee`, portanto uniforme e simétrico. O custo real é assimétrico em dias de estresse (spread aumenta quando a tendência quebra). O cenário stress (0,475% por lado, 0,946% ida e volta) é a única cobertura disso.

**R-09 [warning] Interrupções da exchange e lacunas de dados (§9.4; `lab/config/scenarios.json`).**
`scenarios.json` registra 28 lacunas no BTC 1h entre 2017-09 e 2023-03 (maior: 33 horas), toleradas e não preenchidas. O protocolo lista "sem latência" mas não menciona indisponibilidade da exchange. Para uma estratégia que só age em cruzamentos diários, uma janela de manutenção ou queda de 33 horas num dia de sinal de saída pode atrasar a saída em um dia ou mais, num momento de volatilidade alta. Em dry-run a execução depende da disponibilidade do bot (4 processos no ensemble, R-07). Não há medida desse risco; relatar como limitação.

**R-10 [warning] Liquidez do BNB nos dados iniciais (§9.3, `scenarios.json`).**
O protocolo reconhece que o BNB tinha liquidez e spread que não representam o mercado atual no início de 2017-18. O custo do cenário base é uniforme no tempo e no par. Consequência para o risco: os trades de BNB do início da exploração (a SMA 200d teve 31 trades no BNB, o maior número dos três pares, `H-009-exploration-metrics.json`) são os mais baratos no modelo e os mais caros na realidade, e o BNB é o par com maior drawdown marcado a mercado no JSON de auditoria (31,8% a 32,8% com exposição 0,25). Pedido: relatar BNB sem o primeiro ano (ou separado em duas metades) como sensibilidade, e o resultado em custo stress para esse par separadamente.

**R-11 [note] Fronteira diária e arredondamento (§9.4).** O corte às 00:00 UTC é arbitrário e o arredondamento do stake é de cerca de 0,14% (`harness-fase0.md` §4). Ambos pequenos frente aos outros itens.

## 3. Sobreposição e concentração

**R-12 [blocking] A regra de correlação ≤ 0,7 do `portfolio.json` pode tornar as candidatas mutuamente exclusivas, e o protocolo não trata disso (§8.2).**
A regra do `portfolio.json` calcula Pearson diário sobre o `profit_ratio` de cada trade espalhado igualmente pelos dias de posição, em todas as células pares×splits, com exclusão se |ρ| > 0,7, sem opção de peso reduzido, e fail closed se a série for indefinida ou sem trades exportados. Considerações:
- Ordem de consideração é por ID de hipótese ascendente; quem entra primeiro bloqueia os seguintes. Nenhuma candidata é escolhida por mérito.
- Duas estratégias de tendência que seguram o mesmo rali terão séries espalhadas muito parecidas por construção (é o objetivo do desenho, `portfolio.json` `series`). Dados observáveis: na exploração, a H-009 e a SMA 200d estavam em posição no mesmo momento 89,6% do tempo (BTC), 89,4% (ETH), 92,5% (BNB) das vezes em que a H-009 estava posicionada (`overlap_in_position_with_sma200`, e a correlação diária de equity foi 0,48, 0,43 e 0,71 (`corr_daily_vs_sma200`). O BNB já está acima de 0,7 (0,714 no custo base, 0,713 no conservador) numa medida de equity, que não é exatamente a do `portfolio.py`, mas indica o risco.
- O Donchian ensemble (membros 20 a 200 dias) e a TSMOM (60, 120, 240 dias) entram no mesmo regime de tendência, e a SMA 200d tem ligação direta com o membro (200, 100). Não há dados de correlação deles no que li; é inferência que a sobreposição seja alta. Se a SMA 200d (ou H-009) for considerada antes por ID, as outras podem ser excluídas, e a "diversificação" que o §7.1 A5 espera não existiria para o portfólio.
- O ensemble e o overlay de sizing não geram trades exportados por uma única estratégia Freqtrade (R-07). Pela regra "no exported trades to read → excluded", `portfolio.py` pode excluí-los por construção, ou calcular sobre `profit_ratio` não ponderado por `w`, mascarando o efeito do sizing. O protocolo não cobre isso.
Pedido: (a) medir antes de começar a correlação trade-spread entre SMA 200d, H-009 e um ensemble preliminar só no IS (leitura permitida), para saber se o resultado "portfólio vazio" é esperado; (b) definir como ensemble e overlay entram em `portfolio.py`; (c) declarar o resultado "excluída por correlação" como informação de risco, não como falha da estratégia, e registrar que um portfólio com 1 só estratégia de tendência tem exposição concentrada em um fator.
O estado atual do repositório (commit `dd0289b`, "final report and empty portfolio") é compatível com isso, mas não li o motivo; não afirmo causa.

**R-13 [warning] Dependência de ciclo, D-6 (§8.1.7, §9.2).**
O critério é "nenhum ciclo responsável por mais de 60% do lucro". Problemas:
- Os ciclos de `harness-fase0.md` §5 são 2018, 2019, 2020-21, 2022 e 2023+: apenas 5. Com 2022 tipicamente sem trades (0 trades na SMA 200d) e 2018 negativo, o lucro se divide em 3 ciclos positivos. Um limite de 60% é fácil de violar: 2020-21 sozinho dá 113% e 2023+ 241% de retorno na SMA 200d, e a soma real depende do composto. (Não calculei a fração; dado insuficiente.)
- "Lucro" em ciclos de sinal diferente (perdas em 2018) torna a fração ambígua: definir se o denominador é lucro bruto positivo ou líquido.
- A regra se aplica ao IS (§8.1.7), mas a validação inclui só o ciclo 2023+ parcial e o último ano (semi-contaminado), então uma segunda checagem de ciclo na validação não é possível.
- O limite não cobre concentração em poucos trades dentro do ciclo. O JSON mostra `top5` = 71% e `top10` = 116% do lucro na H-009 BTC (`concentration`, onde top10 > 100% indica que o resto perde). Pedido: acrescentar uma checagem em top-5 trades, e relatar concentração por par e por ano (os três pares têm correlação de 0,64 a 0,79 com o BTC, `scenarios.json`).

**R-14 [warning] Pares não independentes (§9.3).** O critério "pelo menos 2 dos 3 pares" (§7.3, §8.1.3) trata os pares como votos independentes. As correlações medidas são 0,79 (ETH) e 0,64 (BNB) no histórico e 0,91 e 0,81 nos últimos 365 dias (`scenarios.json`). Dois dos três pares concordando é, em boa parte, uma única observação. Relatar como tal.

## 4. Caminhos para parecer pronto sem evidência prospectiva

**R-15 [blocking] O §8.2 usa a expressão "Aprovar para dry-run congelado" e o §4.1 passo 8 liga a aprovação ao congelamento, mas o protocolo não bloqueia linguagem de prontidão antes do holdout.**
O protocolo é correto em §8.3 e em `gates.json` ("There is no 'approved for live' value"). Pontos de vazamento:
- `candidate_for_portfolio` + "aprovar" + "portfólio" pode ser lido como pronto. Exigir que todo relatório e toda tabela tragam o rótulo fixo: "sem evidência prospectiva; dados históricos semi-contaminados". O §9.1 já afirma que a evidência que conta é o holdout, mas é uma limitação, não uma regra de apresentação.
- A SMA 200d como "candidata" já teve a validação lida (§2.1). Se passar o §8.1 e o §8.2 com a mesma validação, o protocolo deveria dizer que o §8.2 não é uma segunda leitura independente. Hoje o texto diz que a única evidência nova é o holdout, mas o §8.2 ainda prevê aprovação.
- O holdout exige ≥ 30 trades fechados somados entre os pares (§3, §8.3, `holdout.json`). Estratégias de tendência diária produzem 5 a 15 trades por par na validação (§9.2); o resultado provável na data preferida é "inconclusiva". O protocolo precisa deixar claro que "inconclusiva" não é "passou": nenhum estado intermediário deve aparecer como "aprovada provisoriamente".
- Todos os limites de gates e portfólio estão PROPOSED (§0.7, D-7). Qualquer "aprovação" sob eles é provisória, e isso deve aparecer na primeira linha dos relatórios.
- Contabilidade de dados já vistos: o holdout inicia em 2026-10-21, mas o `docs/harness-fase0.md` indica dados baixados em 2026-10-30 e último candle fechado em 2026-11-02. O protocolo não proíbe explicitamente que os candles de 2026-10-21 em diante entrem em backtests ou em tuning, além de dizer "nunca usado para otimização" (`holdout.json`). `assert_before_holdout` protege janelas históricas (`harness-fase0.md` §4), mas o `protocol_v3.py` novo (§1.2) é código novo que precisa de teste de que recusa o holdout. Conferir que os candles pós-corte já baixados não vazam para sensibilidades como "últimos 12 meses".
- A cláusula "Aprimorar" (§8.2) permite criar nova hipótese depois de uma reprovação; com a família TSMOM e a SMA 200d, a repetição de ciclos de tentativa e erro erode o N (§6.4). O contador de tentativas já cobre isso se for seguido.
Pedido: incluir no §8 uma regra de apresentação ("nenhum relatório pode usar 'pronto', 'aprovado' ou 'validado' sem a expressão 'sem evidência prospectiva'") e dizer que "dry-run congelado" é um experimento de coleta de evidência, não uma etapa de prontidão.

**R-16 [warning] Aprimoramento sobre validação já lida (§8.2 "Aprimorar", §9.1).** O protocolo já reconhece que a validação do aprimoramento fica ainda mais contaminada. Do ponto de risco, o efeito é que o número de configurações tentadas efetivamente cresce sem que o DSR do §6.4 o contabilize, se o aprimoramento for formalmente uma "hipótese nova" mas inspirada na validação. Exigir que o N inclua a hipótese anterior e que o relatório cite a hipótese que a motivou.

**R-17 [warning] Critério alternativo de D-2 (§9.2).** "IC95% do Sharpe diário com ≥ 500 dias e ≥ 8 episódios" seria uma redução do mínimo de trades. Isso reduz a barreira justamente para as estratégias que o protocolo pretende favorecer. Do lado de risco: 8 episódios é pouco para qualquer inferência sobre cauda; e Sharpe diário de estratégia que passa a maior parte do tempo em caixa é inflado em dias parados. Se adotado, manter também o gate original como informação ao lado, nunca substituí-lo no relatório.

**R-18 [note] Custo e ensemble (§5).** O custo por membro sobre 1/4 do stake significa que o custo agregado do ensemble é de fato a soma das partes; o membro de 20 dias tem o maior turnover. O protocolo já prevê a sensibilidade sem esse membro. Vale também mostrar o break-even do membro de 20 dias isolado, pois ele define a inclinação da degradação no cenário stress.

**R-19 [note] Gate de lucro mínimo (`gates.json` `net_profit`).** O limite base é 1,0 USDT em carteira de 100 (1%), crescendo 10% por variante prévia. É um piso muito baixo comparado com um drawdown de 25%: a razão lucro/drawdown pode ser pequena e o gate ainda passa. Isso é característica do gate, não do protocolo, mas o protocolo se apoia nele para §8.1.1 sem reforço.

---

## Resumo

Bloqueantes: R-01, R-02, R-03 (drawdown fechado versus marcado a mercado e calibração), R-07 (ensemble e sizing não executáveis como descritos), R-12 (correlação ≤ 0,7 e tratamento de ensemble/overlay no portfólio), R-15 (linguagem de prontidão e uso da validação já lida).
Avisos: R-04, R-05, R-06, R-08, R-09, R-10, R-13, R-14, R-16, R-17.
Notas: R-11, R-18, R-19.

Incertezas declaradas: não há trades de SMA 200d, Donchian ensemble ou TSMOM nos arquivos lidos, então sobreposição entre esses três é inferida a partir da H-009 versus SMA 200d; não calculei fração de lucro por ciclo; a definição exata de `sma200_same_exposure` não está nos arquivos que li.
