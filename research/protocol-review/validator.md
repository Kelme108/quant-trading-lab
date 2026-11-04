# Revisão do validator: `docs/protocolo-validacao-v3.md` (rascunho 1)

Escopo: causalidade, consistência com a configuração existente e reprodutibilidade. Li o rascunho, `research/validation-protocol-v2.md`, `lab/config/{gates,splits,holdout,portfolio,budget}.json`, `lab/{strategy_check,costs,returns,stats,walkforward,bootstrap,causality,gates,registry}.py`, `research/tools/validate_once.py`, `docs/harness-fase0.md`, `docs/relatorio-auditoria-estrategias.md`, `user_data/strategies/Sma200Baseline.py` e `DonchianBreakoutBaseline.py`, e `research/audit/H-009-exploration-metrics.json` (só os campos `sma200_trades`). Não li `quant.md` nem `risk.md` nem arquivos de resultado de validação. Nada foi executado.

Resumo: nenhum passo do protocolo, como escrito, introduz vazamento de futuro por si só. Os regras SMA 200d, canal Donchian com `shift(1)` e peso de vol sobre 30 dias fechados são implementáveis de forma causal. Os problemas graves são de consistência com o harness (cap de variantes, gates e `validate_once` não encaixam em ensemble/overlay) e de ambiguidade que muda os números.

## Bloqueantes

**1. [blocking] Ensemble exige várias estratégias, mas o orçamento de família e o contrato de arquivo permitem uma por hipótese.**
- `lab/strategy_check.py:52` (`FILE_STEM`) e `:149-155`: um arquivo, uma classe `IStrategy`, um `H-NNN`. `research/tools/validate_once.py:34` pega um único arquivo `*_H{n}_v*.py` por hipótese.
- Donchian Ensemble tem 4 membros "cada um como uma estratégia Freqtrade separada" (protocolo §2.2, linhas 78-80). TSMOM tem 3 horizontes (§2.4, linha 103).
- `lab/config/budget.json:3`: `max_variants_per_family = 3`; `max_hypotheses_per_cycle = 3` (linha 2). Quatro membros como hipóteses separadas excedem o teto de variantes e o do ciclo. O TSMOM tem "1 variante restante" (protocolo linha 16), mas 3 membros precisariam de 3 hipóteses; D-8 (linha 309) fala em "usar a última variante" para o ensemble inteiro.
- Se os membros forem um único arquivo parametrizado por config, o draft não diz como (a classe não recebe parâmetros por arquivo; `strategy_check` exige constantes de classe, `:171-185`).
- Pede-se definir: 1 hipótese com N membros (e como `count_prior_variants`, `lab/registry.py:189`, e a penalidade de `gates.json:20-25` contam isso) ou N hipóteses (e como o cap é tratado). Hoje o protocolo é inexequível dentro de `budget.json`, que ele diz não alterar (linha 5).

**2. [blocking] Os gates e `validate_once` não conseguem decidir ensemble nem overlay de sizing.**
- §8.1 item 1 (linha 219) exige "gates de `gates.json` em todos os pares". `lab/gates.py:103-116` e `:150-164` operam sobre métricas de um export do Freqtrade (contagem de trades, `max_relative_drawdown_pct__<cenário>`). O ensemble é a soma de curvas por `lab/ensemble.py` e o sizing é pós-trade em `lab/sizing.py` (§1.2, §9.6); nenhum deles tem export nem linha em `metrics`.
- `research/tools/validate_once.py:24-26` exige `candidate_for_portfolio` na exploração em todo par para a hipótese; `:39-42` roda um arquivo com um `--exposure`. Não há caminho para ler a validação do ensemble agregado, só de cada membro.
- Consequência: o membro (200, 100) tem poucos trades e dá `inconclusive` pelo mínimo de 30 (`gates.json:13-16`; ver item 9), logo o ensemble nunca chega à validação. O draft não diz como o "trade count" do ensemble é contado para o gate, nem qual métrica de DD entra no teto de 25%.
- Definir antes: qual objeto recebe `decision` (membro, ensemble, overlay) e com que métricas.

**3. [blocking] Regra de entrada/reentrada e estado inicial dos canais Donchian não estão especificados; isso muda os trades.**
- Protocolo §2.2 (linhas 76-77): "entra quando o fechamento diário fechado > máxima dos N_k dias anteriores e sai quando < mínima dos M_k dias anteriores", mais stop de 20% (D-3).
- Pontos em aberto: (a) a "máxima" é de `high` diário ou de `close` diário (o `DonchianBreakoutBaseline.py:30-31` usa `high`/`low` com `rolling(N).max().shift(1)`; o draft não diz); (b) a entrada é de nível (condição verdadeira e flat) ou de cruzamento; se de nível, após o stop de 20% o membro reentra na hora seguinte enquanto o fechamento diário seguir acima do canal, o que muda trades e custos; (c) estado na fronteira do split: indicador de nível (SMA) reconstrói o estado do aquecimento, mas um Donchian com saída por mínima depende do caminho. Um split recomeça flat (Freqtrade) e só entra de novo no próximo rompimento; o draft diz só "indicadores usam candles anteriores" (§3, linha 114); (d) posição aberta no fim do split é fechada à força pelo backtest, e para trades de meses isso entra na contagem e no lucro.
- Duas pessoas implementariam resultados diferentes. Fixar (a)-(d) em texto antes do registro.

## Avisos

**4. [warning] TSMOM {60, 120, 240}: dois dos três horizontes já foram vistos no grid da H-015.**
- `research/grids/H-015-report.md:4`: N ∈ {30, 60, 90, 120, 180}, 10 configurações. O draft (linha 103) diz que o ensemble "evita repetir a seleção de célula" e que a variante "não pode reescolher entre os horizontes do grid da H-015" (linha 100), mas 60 e 120 são células desse grid, com Sharpe IS conhecido (N60 1,23; N120 1,08, linha 9 do relatório). Só 240 é novo. A escolha dos horizontes foi feita depois de ver o grid; isso precisa ser declarado e entrar no N do DSR. Também cabe lembrar que a H-016 (N30) já leu a validação.

**5. [warning] "Família separada" do Donchian contradiz a contagem de tentativas e abre brecha na penalidade de múltiplos testes.**
- Protocolo linha 16: `DonchianBreakoutBaseline` (H-002) é "família separada". A penalidade de `gates.json:20-25` usa `count_prior_variants` por string de `family` (`lab/registry.py:189-200`); um nome novo zera a contagem. Mas §6.4 (linha 180) manda o N do DSR incluir "todas as configurações já testadas na família, inclusive variantes anteriores". O H-002 testou o mesmo mecanismo (rompimento de máxima/saída por mínima) em 1h, 20/10, e foi rejeitado com DD de 60-98% (`research/hypothesis-ledger.md`, linha do H-002; `docs/relatorio-auditoria-estrategias.md:76-78`). Recomendo registrar o N pelo mecanismo, não pelo nome da família, e dizer isso.

**6. [warning] O protocolo reutiliza `lab/returns.py` "sem mudança", mas o sizing e o ensemble precisam de mais que ele oferece.**
- Tabela §1.1 (linha 31) e §5 (linha 157): `returns.equity_curve` recebe um `exposure` escalar por chamada (`lab/returns.py:27`, `:49`) e exige trades sem sobreposição (`:39`). O peso por trade `w_i` exige mudança de assinatura; o draft a coloca em `sizing.py`, mas deixa a tabela dizer "sem mudança". Corrigir o texto ou declarar a nova interface.
- A soma de curvas do ensemble ("exposição 1/N", linha 48) não diz se os pesos são rebalanceados diariamente (soma dos retornos diários) ou se cada subconta deriva (soma de equity). Os dois dão curvas, DD e Sharpe diferentes. Escolher um.

**7. [warning] Interação entre a exposição calibrada, o 1/N do ensemble e o peso de vol não está definida.**
- Passo 4 (linha 124) calibra exposição por regra com `bootstrap.choose_exposure` (`lab/bootstrap.py:102-123`, grade de 5%, p95 do DD ≤ 25% em todos os pares). O ensemble fixa 1/4 por membro (§2.2) e o sizing multiplica por `min(1, σ*/σ̂)` (§2.3).
- Não está dito se a exposição final do membro é 1/4, a calibrada, ou o produto. O cap `w ≤ 1` (linha 49) não é o cap de exposição. Como as exposições calibradas já são 0,15-0,30 no lab (`relatorio-auditoria`, tabela A), a diferença é de ordem de grandeza.
- Ligado a isso: o gate de lucro mínimo `gates.json:25` (1,0 USDT em carteira de 100) e o mínimo de trades dependem da exposição.

**8. [warning] Peso de vol sizing: definições faltando.**
- Protocolo linhas 87-91. Não está dito: número de retornos (30 retornos usam 31 fechamentos; 30 fechamentos dão 29); ddof; fator de anualização (`lab/stats.py:33` usa √365); se a janela termina no último fechamento diário antes do candle de sinal ou antes da abertura do trade (diferem em 1 candle, mas o dia D de entrada não pode entrar: se o trade abre às 01:00 do dia D, os 30 dias fechados são D-30..D-1).
- "Exposição constante igual à exposição média do overlay" (linha 94): média sobre trades, sobre horas em posição ou sobre todo o período (incluindo flat)? Os três dão valores diferentes quando a vol se agrupa em picos de alta. Além disso, essa média é calculada com a amostra inteira do IS; é calibração do comparador, não vazamento de sinal, mas deve ser dito.
- σ*=40% com a vol típica de BTC/ETH/BNB deixa `w` quase sempre abaixo de 1 (cap raramente ativo); a justificativa "abaixo da volatilidade histórica do BTC" (linha 91) não tem fonte nos arquivos lidos.

**9. [warning] Mínimo de 30 trades torna a maioria das candidatas deste protocolo inconclusivas por construção, e o draft só trata isso em parte.**
- Fonte confirmada: `research/audit/H-009-exploration-metrics.json` (linhas 100, 395, 690): `sma200_trades` = 19 (BTC), 18 (ETH), 31 (BNB). O draft acerta (linha 14, 254). O BNB passa por 1 trade; qualquer diferença de warm-up muda isso.
- O membro (200, 100) e o L=240 têm menos trades que a SMA 200d. Passo 4 (linha 124) "descarta" com menos de 30 trades por par, mas essa regra não está em `lab/bootstrap.py`; `gates.py:103-116` só devolve `inconclusive`. Se o descarte vive no orquestrador, citar onde.
- §9.2 diz que estratégias de tendência diária têm "15 a 35 trades por par em 7 anos e 5 a 15 na validação" (linha 252). Sem fonte para 5-15; a H-016 (TSMOM N30, também de tendência) teve 89-96 trades IS e 33-43 na validação (`relatorio-auditoria`, tabela A e §5). A faixa vale para SMA/Donchian longos, não para o TSMOM; ajustar o texto.
- O holdout tem o mesmo problema e o draft não o diz: `holdout.json:15` exige 30 trades fechados somados entre pares, em 6 a 12 meses (§3, linha 112). Com ~2-3 trades por par por ano para SMA 200d, 30 trades somados é inalcançável; o resultado será quase sempre "inconclusivo" (`holdout.json:16`). Contar trades de membros do ensemble somados para chegar a 30 inflaria a amostra com trades correlacionados. Declarar a regra de contagem.

**10. [warning] SMA 200d como "candidata" tem critérios circulares e sem mecanismo de decisão.**
- §8.1 item 3 (linha 221) exige Sharpe acima da `Sma200Baseline`. Para a própria SMA 200d isso é impossível por construção (mesma série). O item 2 (30 trades) também a reprova no IS em BTC e ETH.
- `Sma200Baseline` "não recebe decisão de gates" (`relatorio-auditoria:47`). §2.1 a trata como candidata cuja única evidência nova é o holdout; `gates.py` não avalia o holdout e `portfolio.py`/`gates.json:41` não têm esse passo (`holdout.json:17` só diz que `final_test_unlocked` é decisão do usuário). Quem calcula e decide a avaliação do holdout (que código, que tabela de decisão) não está definido; §8.3 (linha 237-239) fala em "aprovação definitiva", mas `gates.json:43-46` só permite `rejected/inconclusive/candidate_for_portfolio`.

**11. [warning] Critério D-4 de walk-forward: anos sem posição.**
- Linha 134: "Sharpe anual > 0 em pelo menos 4 dos 6 anos-teste". `lab/stats.py:24-30` devolve Sharpe 0,0 para série constante (ano inteiro flat). Regras de tendência com filtro longo ficam flat em anos de baixa (a Tabela C do relatório mostra retornos 0% em 2022 para H-007 e H-009 BTC). Um ano flat conta como falha de "> 0"; o draft deve dizer se isso é intencional.
- `lab/walkforward.py:18-29`: os anos-teste são 2019 a 2024; o de 2024 termina em 2024-07/08 (corte da exploração), logo é meio ano, e o draft fala em "6 anos-teste" (certo em contagem, incompleto em duração). Para regras sem seleção, o "walk-forward" é só estabilidade por ano dentro do IS, com a exposição calibrada no IS inteiro: não é fora da amostra, e o texto deveria rotular assim (linha 133 diz apenas "estabilidade").

**12. [warning] Ganho marginal: ΔSharpe pareado não é a estatística da série `d_t`.**
- §7.2 (linhas 201-203) define `d_t = r_Y,t - r_X,t` e IC95% de ΔSharpe por bootstrap pareado de blocos. `lab/stats.py:146-170` (`block_bootstrap_ci`) reamostra uma série 1-D e aplica `statistic(sample)`; Sharpe de `d_t` (média/desvio de d) não é Sharpe(Y)-Sharpe(X). É necessário reamostrar os índices de blocos das duas séries juntas e recalcular os dois Sharpes. Está implícito em `lab/marginal.py` (a criar), mas a definição exata não está no texto. Também: bloco de 20 dias vs. `block=5` default; reamostras 4000 em `choose_exposure` mas `bootstrap.main` usa 10000 (`lab/bootstrap.py:130`), e a linha 293 do draft diz "reamostras = 4000".

**13. [warning] N do DSR e variância dos trials não estão fixados.**
- §6.4 (linhas 180-181): N = "todas as configurações já testadas na família", mais um N≈47 como sensibilidade. `lab/stats.py:74-88` precisa também de `variance_of_trial_sharpes`: as 47 regras têm séries em exposições e janelas diferentes; qual série e qual variância entram não está escrito. Com N=1 (SMA 200d sem grid) `expected_max_sharpe` devolve 0 (`stats.py:66-67`), e o DSR vira o PSR; o critério DSR ≥ 0,95 (linha 223) então é o do PSR sem desconto. Dizer como contar sensibilidades relatadas (`budget.json:7`: "each parameter variant and each cost scenario counts as a test") e cenários de custo.
- A tentativa "N=47" mistura famílias; declarar uma tabela de entrada (lista de IDs).

## Notas

**14. [note] Causalidade: itens verificados, sem achado.**
- SMA 200d: `Sma200Baseline.py:34-35,37-49` usa `merge_informative_pair(..., ffill=True)`, `close_1d > sma_1d`, executa no candle seguinte; o rascunho descreve a mesma regra (§2.1). O `startup_candle_count = 210` (linha 27) cobre 200 dias; o texto "warm-up 200 candles diários ... Abaixo de 4500 no 1h" (linha 83) mistura o limite de 1h (`strategy_check.py:45`) com o de candles diários; para um membro (200, 100) basta ~210 diário, o teto 4500 só importa se o canal fosse calculado em 1h (como a H-006, 5520).
- Donchian: "máxima dos N_k dias anteriores (sem o dia atual)" está correta se for `rolling(N).max().shift(1)` no diário antes do merge, e comparada ao fechamento diário já fechado (o mesmo padrão do `DonchianBreakoutBaseline.py:30-31`). Se `shift(1)` for omitido, o fechamento do dia entra no próprio canal (vazamento por uso do candle atual). O contrato de teste (passo 2, linha 122) deve incluir um caso para isso; `lab/causality.py:32-59` testa invariância a prefixo e corrupção do futuro e pegaria a omissão se aplicado ao canal diário.
- Peso de vol: "30 dias fechados antes da abertura" (§2.3) é causal desde que o dia da abertura fique fora (item 8). O overlay em `sizing.py` é calculado sobre trades exportados: nenhum sinal usa o peso, então o peso não afeta quais trades existem.
- TSMOM: "retorno do fechamento diário fechado nos últimos L dias" = `close(d)/close(d-L)`, igual à H-015 (`H-015-report.md:4`); causal.
- Fronteiras de split: os cortes são em segundos, por par, no meio do dia (`splits.json:20-22,38-40,56-58`; ex.: BTC exploração termina 19:00 UTC). O draft usa "2024-07" como data comum; BNB termina 2024-07-25. Isso não vaza futuro, mas as métricas por ano/ciclo do walk-forward devem usar os cortes por par, e o candle diário da fronteira contém horas dos dois splits.

**15. [note] Fatos citados que conferem.**
- Tabela de custos (§5, linhas 149-153) bate com `lab/costs.py:49-86`: efetivos por lado 0,100/0,175/0,250/0,475/0,350%; ida e volta 0,200/0,349/0,499/0,946/0,698% (fórmula `1-(1-f)/(1+f)`, `costs.py:104-110`). `base_2x` fora dos 4 cenários requeridos (`costs.py:88`, `gates.json:4`) está de acordo com o texto.
- `custom_stake_amount` e `adjust_trade_position` proibidos em `lab/strategy_check.py:48` (a mesma linha também proíbe `leverage`).
- Holdout: início 2026-10-21, avaliação não antes de 2027-04-21, preferida 2027-10-21, 30 trades somados (`lab/config/holdout.json:13-16`, `splits.json:3-7`). Janela semi-contaminada 2025-10-21 a 2026-10-20 idem (`holdout.json:5-8`).
- Teto de 3 variantes (`budget.json:3`); TSMOM com 2 (H-015, H-016; `relatorio-auditoria:43-44`); ≈ 47 regras (`relatorio-auditoria:59`); correlação 0,787 ETH e 0,635 BNB (`relatorio-auditoria:281`); queda do lucro/dia da H-016 de 63% a 96% (`relatorio-auditoria:234-236`); ~0,14% do arredondamento de stake (`harness-fase0.md:31`).
- Os gates e o `portfolio.json` continuam PROPOSED (`gates.json:2`, `portfolio.json:2`): coerente com a linha 17 do draft. O draft não altera nenhum arquivo congelado.

**16. [note] Detalhes menores.**
- Rascunho cita `lab/dossier.py` (linha 133 só diz "`dossier.py`"); o arquivo existe em `research/tools/dossier.py`, não em `lab/`.
- D-1 propõe sizing "só como overlay". O overlay ignora o stake mínimo e o arredondamento da exchange para pesos pequenos (w baixo × exposição baixa × carteira de 100 USDT); o draft já cita o arredondamento de ~0,14% em §9.4, mas não o efeito de stake mínimo na dry-run.
- §3: "Janela de exploração ... 2017-08 a 2024-07" para BNB começa em 2017-11 (dito na tabela), mas a SMA de 200 dias e os canais de 200 dias fazem com que o primeiro sinal do BNB só apareça no meio de 2018; os ciclos "2018" da Tabela C ficam quase sem trades para as regras de 200 dias. Relatar a data do primeiro sinal por membro e par.
- A afirmação "BNB foi escolhido por baixa correlação medida (`scenarios.json`)" (linha 260) não foi verificada: não li `lab/config/scenarios.json`.
