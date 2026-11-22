# Pesquisa: como direcionar o laboratório para day trade (12/11/2026)

Pedido do dono: investigar como melhorar e direcionar o projeto para day trade; trazer pesquisas, exemplos, estratégias e métodos; entender por que nada passou até agora; levantar o que se sabe sobre bots, bots de IA, agentes autônomos (Grok, Claude e outros) e quem realmente ganha dinheiro com day trade.

Complementa [2026-11-12-revisao-day-trade.md](2026-11-12-revisao-day-trade.md). Nada aqui muda o protocolo, os gates ou a configuração: as mudanças estruturais continuam sendo decisão do dono.

## 1. Resumo em cinco linhas

1. **O problema do lab não é falta de ideias, é custo.** Foram 123 hipóteses. As regras de day trade frequentes têm movimento bruto de 0,0% a 0,35% por trade, e a ida e volta em spot custa 0,30%.
2. **Com o custo de futuros, parte do placar muda de sinal** (seção 4). Com 0,15% de ida e volta, 9 regras de day trade com 40 ou mais trades por ano por par ficariam com líquido positivo nos trades da exploração. Hoje são 6, todas com margem pequena.
3. **Quem ganha dinheiro com day trade de forma consistente são formadores de mercado, arbitradores e HFT.** O lucro deles vem de spread, rebates, arbitragem e infraestrutura, não de padrão de gráfico. Entre pessoas físicas, o estudo brasileiro mais citado achou que 97% dos que persistiram no mini-índice perderam dinheiro.
4. **Agentes autônomos de IA (Grok, Claude, GPT, Qwen, DeepSeek) ainda não mostram vantagem verificável.** Nas competições ao vivo, a maioria perdeu, e os resultados mudam de uma temporada para outra. O maior estudo com dados de produção (6 meses, centenas de agentes) não achou vantagem direcional.
5. **A arquitetura do lab já está do lado certo da evidência.** A IA pesquisa e escreve, e código determinístico decide. O que falta é atacar o custo e a frequência pela estrutura: futuros, mais pares, ordem maker, ou outro mercado.

## 2. Por que nada passou (diagnóstico do próprio projeto)

Fonte: [scoreboard.md](../knowledge/scoreboard.md) (80 hipóteses com trades de exploração) e o histórico git (H-001 a H-123).

| Fato | Consequência |
|---|---|
| Spot, só compra, 0,30% de ida e volta (base) | Uma regra precisa de mais de 0,30% de movimento bruto médio só para empatar |
| Regras com 100+ trades/ano/par: bruto máximo 0,29% | O gatilho frequente dispara em barras comuns, onde o preço quase não anda |
| Regras com bruto de 0,45% a 0,70% (H-104, H-101, H-043, H-100) fazem 20 a 50 trades/ano/par | São raras demais para a regra de 2 dias do dry-run com 9 pares |
| Todo momentum só-compra perdeu em 2022-2024 | Sem venda a descoberto, o bot fica exposto ou parado no mercado de baixa |
| ICT/SMC (FVG, order block, SMT, Judas sweep), pivôs, periodicidade de horário | Todos viraram ruído depois do custo |

Isso bate com a literatura: regras técnicas intraday em cripto em geral não sobrevivem ao custo (Svogun e Bazán-Palomino 2022, já em [evidence.md](../knowledge/evidence.md)). Um estudo novo sobre o "efeito quarto de hora" nos perpétuos da Binance diz o mesmo. Os movimentos nas viradas de 15 minutos são previsíveis estatisticamente, mas o ganho médio fica muito abaixo da taxa ([Kim e Hansen, arXiv 2607.09426](https://arxiv.org/pdf/2607.09426); [resumo na CryptoSlate](https://cryptoslate.com/the-invisible-opening-bell-inside-cryptos-endless-trading-day/)). Isso confirma o que o lab viu com H-060 e H-064.

## 3. Quem ganha dinheiro com day trade, de verdade

### Profissionais

- **Formadores de mercado (Wintermute, Jump e outros).** Ganham com o spread entre compra e venda, com rebates de taxa, com arbitragem e com contratos de liquidez com projetos ([crypto.news](https://crypto.news/how-crypto-market-makers-work-firms-behind-every-trade/), [DWF Labs](https://www.dwf-labs.com/news/types-of-crypto-market-makers)). A Wintermute disse ter tido seus "melhores dias" em semanas de pânico ([The Block](https://www.theblock.co/post/58781/crypto-market-maker-wintermute-trading-says-it-saw-its-best-performing-days-amid-last-weeks-turmoil)). Ganham com volume e volatilidade, não com direção. A margem do setor caiu depois de 2022 ([BNN Bloomberg](https://www.bnnbloomberg.ca/a-year-after-ftx-crypto-market-makers-adapt-to-survive-1.1991778)).
- **Arbitragem de funding e base (cash and carry).** Comprado no spot, vendido no perpétuo, para receber o funding. Estimativas de mercado vão de um dígito alto a dezenas de por cento ao ano, conforme a época ([Sharpe](https://sharpe.ai/blog/basis-trading-crypto), [BitMEX](https://blog.bitmex.com/2025q2-derivatives-report), [índice da 1Token com 11 mesas](https://blog.1token.tech/crypto-quant-strategy-index-viii-nov-2025/)). O rendimento cai quando muita gente entra ([KuCoin/BitMEX](https://www.kucoin.com/news/flash/bitmex-reports-collapse-of-crypto-arbitrage-strategy-amid-market-saturation)). Não é day trade direcional, mas é a estratégia "de bot" com retorno mais documentado.
- **Fluxo de ordens de curtíssimo prazo.** A literatura acha previsibilidade no desequilíbrio do livro e do fluxo agressor. O maior obstáculo para quem executa a mercado é a taxa ([arXiv 2502.18625](https://arxiv.org/html/2502.18625v1); [Bieganowski e Ślepaczuk, arXiv 2602.00776](https://arxiv.org/abs/2602.00776)). Um estudo de 2026 com o volume agressor comprador da Binance acha **reversão**, não continuação, depois de barras empurradas pelo fluxo ([arXiv 2608.21888](https://arxiv.org/pdf/2608.21888)).

### Pessoas físicas

- **Brasil, mini-índice (WIN).** Chague, De-Losso e Giovannetti ("Day Trading for a Living?") acompanharam 19.646 pessoas que começaram em 2013-2015. Das 1.551 que persistiram por mais de 300 pregões, 97% perderam dinheiro e cerca de 1% ganhou mais que um salário mínimo. Não houve sinal de aprendizado ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3423101), [resumo CXO](https://www.cxoadvisory.com/?p=32819), [Bloomberg](https://www.bloombergquint.com/onweb/day-traders-in-brazil-study-would-ve-done-better-with-9-to-5-job)).
- **Bots de varejo (Freqtrade/NostalgiaForInfinity, FreqAI, Hummingbot, Jesse).** São boas ferramentas. Nenhum publica histórico ao vivo auditado: o NFI aponta para os backtests nos commits ([ecosyste.ms](https://awesome.ecosyste.ms/projects/github.com%2Fiterativv%2FNostalgiaForInfinity)), e o FreqAI é uma interface de ML, não uma estratégia ([JOSS](https://joss.theoj.org/papers/10.21105/joss.04864.pdf)). Na formação de mercado de varejo, o risco de estoque e a seleção adversa comem o spread ([Hummingbot](https://hummingbot.org/blog/what-is-inventory-risk/)).

**Lição:** o dinheiro consistente do day trade vem de **vantagem estrutural** (custo menor, rebate, acesso, velocidade, ficar do lado passivo), não de um indicador melhor. Para o lab, isso significa mexer no custo e no tipo de ordem, não só no gatilho.

## 4. A conta que muda o jogo: custo por ida e volta

Recalculei o líquido médio por trade das **56 regras de day trade do placar**, mantendo o bruto da exploração e trocando apenas o custo. É uma conta de sensibilidade sobre dados já vistos, **não um resultado**: qualquer regra que entrar por causa dela precisa ser registrada de novo e passar pela validação, com a penalidade de múltiplos testes.

| Ida e volta | Cenário de referência | Day trade com líquido > 0 | Destas, com 40+ trades/ano/par |
|---|---|--:|--:|
| 0,30% | spot hoje (base do lab) | 11 | 6 (melhor: +0,14%) |
| 0,20% | futuros taker com derrapagem alta | 12 | 7 |
| 0,15% | futuros taker (0,05% por lado) + derrapagem moderada | 14 | 9 (H-073 com 135 trades/ano/par: +0,14%) |
| 0,10% | futuros taker sem derrapagem | 17 | 11 |
| 0,04% | futuros maker nos dois lados | 27 | 19 |

Taxas de referência (base, sem VIP): spot 0,10% por lado; futuros USDT-M 0,02% maker e 0,05% taker, cerca de 10% menos pagando com BNB ([Binance FAQ](https://www.binance.com/support/faq/360033544231), [CoinPerps](https://www.coinperps.com/learn/bybit-vs-binance-perpetual-futures-fees)). **Confirmar na tabela oficial antes de fixar o cenário.**

Limites honestos dessa conta:
- A linha de 0,04% é otimista. Ordem maker não executa sempre, e as que executam tendem a ser as piores (seleção adversa), então o bruto cai.
- Em futuros entra o funding, pago a cada 8 h. Em posições intraday é pequeno, mas tem que entrar no custo.
- As regras positivas a 0,15% têm em média 0,03% a 0,29% de líquido: pouca folga. Várias perderam em 2022-2024. Em futuros, a versão vendida pode ser testada como hipótese própria, e não como espelho automático da comprada.

## 5. Agentes autônomos de IA que operam (Grok, Claude e outros)

### Como funcionam

O desenho mais comum, usado no Alpha Arena e nos frameworks abertos (TradingAgents, nof0, ai-hedge-fund-crypto), é este:
1. A cada poucos minutos, o modelo recebe um prompt com preços, indicadores, a carteira e, às vezes, notícias.
2. Ele responde com uma decisão estruturada: ativo, lado, tamanho, alavancagem, alvo, stop e às vezes uma "condição de invalidação".
3. Uma camada de código executa a ordem na corretora (Hyperliquid, nas competições de cripto).

Em alguns produtos, o usuário ajusta um "controle de risco" que define a alavancagem.

### Resultados

| Teste | O que aconteceu |
|---|---|
| Alpha Arena T1 (nof1, out-nov/2025, perpétuos cripto, US$ 10 mil por modelo) | 4 de 6 modelos fecharam no prejuízo. Qwen 3 Max venceu; GPT-5 e Gemini 2.5 Pro perderam bastante. A própria nof1 disse que, no começo, o resultado foi dominado pelo custo, porque os agentes operavam demais ([Forklog](https://forklog.com/en/four-out-of-six-ai-models-suffer-losses-in-trading-tournament/), [Decrypt](https://decrypt.co/345006/ai-crypto-trading-showdown-deepseek-grok-winning-gemini-implodes), [Protos](https://protos.com/llm-crypto-trading-contest-finds-llms-cant-trade-crypto)) |
| Alpha Arena T1.5 (ações dos EUA) | Grok 4.20 venceu com cerca de 10-12% em duas semanas. Num retrato do meio da temporada, Claude Sonnet 4.5 estava em -35% e Grok 4 em -53% ([gncrypto](https://www.gncrypto.news/news/mystery-model-alpha-arena-season-1-5-winner/), [Bitget/BlockBeats](https://www.bitget.com/news/detail/12560605099629)). O mesmo fornecedor foi do pior ao melhor em versões diferentes: isso indica variância, não habilidade comprovada |
| Fundador da nof1 | "Ainda não é viável entregar dinheiro a um LLM e deixá-lo operar sozinho" ([KuCoin](https://www.kucoin.com/news/flash/ai-trading-models-struggle-in-live-market-tests-majority-of-systems-report-losses)) |
| **Frotas em produção, 6 meses** ([arXiv 2609.05663](https://arxiv.org/abs/2609.05663)) | Cerca de 3.500 cofres e mais de 500 agentes, com dinheiro real, em memecoins e perpétuos da Hyperliquid. **Nenhuma vantagem direcional.** A frota de perpétuos perdeu e ficou atrás do varejo comum (41% contra 50% de acerto). O tamanho da posição ignorava a volatilidade (alavancagem mediana de 5x em qualquer regime). 43% das posições chegaram a +3% a favor em 24 h, e metade delas fechou no prejuízo. Um bracket mecânico de alvo e stop recuperaria +0,39% por posição. Modelos de ponta tiveram qualidade de decisão estatisticamente igual |
| FINSABER ([arXiv 2505.07078](https://arxiv.org/html/2505.07078v5)) | Em 20 anos e 100+ ações, a vantagem relatada dos LLMs some. Estratégias tradicionais ganham. Os LLMs são conservadores demais na alta e agressivos demais na baixa |
| LiveTradeBench, StockBench, AI-Trader | Em testes ao vivo, a maioria não bate o buy-and-hold, e nota alta em ranking geral de IA não prevê resultado em trade ([LiveTradeBench](https://www.arxiv.org/pdf/2511.03628), [Agent Market Arena](https://fugumt.com/fugumt/paper_check/2510.11695v2_enmode)) |
| Bots "feitos com Claude" (vídeos, Medium) | Relatos isolados, sem conta auditada; títulos de ganho enorme são marketing ([Medium](https://medium.com/@info_38412/claude-didnt-earn-10k-overnight-and-that-isn-t-how-markets-work-b2bb2717aa76)). Um levantamento de maio/2026 não achou nenhum histórico ao vivo verificado de bot de IA de varejo |

### O que isso ensina ao lab

1. **Não pôr um LLM para decidir ordens.** A evidência é contra, e o lab já proíbe isso por princípio: os agentes escrevem, o Python decide. Manter.
2. **A camada de operação pesa mais que o "cérebro".** No estudo das frotas, o controle de risco, o tamanho da posição e a saída mecânica explicaram mais do que o modelo. O lab já tem saída por tempo, stop fixo e gates, que é o lado certo.
3. **Onde a IA ajuda de fato:** pesquisa (ler artigos e transformar em regra testável), revisão de código e, mais à frente, um filtro de ML treinado nos sinais das próprias regras (meta-labeling). Esse filtro é uma hipótese a testar, não um ganho garantido; a evidência específica para cripto ainda é fina ([Alpaca](https://alpaca.markets/learn/alternative-bars-03), [Springer 2025](https://link.springer.com/article/10.1186/s40854-025-00866-w)).

## 6. Recomendações, em ordem

Cada item diz se dá para fazer dentro das regras atuais ou se depende de decisão do dono.

### A. Baixar o custo: dry-run em futuros perpétuos (decisão do dono)
- **Por quê:** é a única alavanca que, nos dados do próprio lab, transforma regras frequentes em candidatas (seção 4). Também permite vender a descoberto, o que ataca a perda de 2022-2024.
- **Como:** o Freqtrade suporta `trading_mode: futures` com `margin_mode: isolated` e `can_short` em dry-run. Usar alavancagem 1x para que a única diferença seja a taxa e a possibilidade de vender. Criar cenários de custo de futuros (por exemplo 0,15% base e 0,25% conservador, mais funding), baixar o histórico dos perpétuos e cortar novas divisões.
- **Risco:** com alavancagem de verdade, existe liquidação. O protocolo deve fixar 1x até haver evidência.

### B. Mais pares: 25 a 30 (decisão do dono, já levantada)
- Com 30 pares, uma regra de 28 trades por ano por par (H-104) dá cerca de 2,3 trades por dia, e a regra de 2 dias deixa de matar bots bons. É a alavanca mais barata.

### C. Dados novos, de graça, que o lab ainda não usa (dá para fazer sem mudar o mercado)
- **Volume agressor comprador.** Cada candle oficial da Binance (data.binance.vision e API de klines) traz o "taker buy base asset volume". Com ele dá para medir o fluxo agressor (delta) por barra sem livro de ofertas, e o estudo [arXiv 2608.21888](https://arxiv.org/pdf/2608.21888) dá um mecanismo testável: reversão depois de barra empurrada pelo fluxo. Exige um passo de dados novo, porque o OHLCV do Freqtrade não guarda essa coluna. Precisa checar como entra sem viés de antecipação.
- **Em futuros:** funding e open interest. Hoje o [evidence.md](../knowledge/evidence.md) proíbe isso porque o lab é spot.

### D. Outro mercado: mini-índice e mini-dólar na B3 (decisão do dono; a camada MT5 já existe em `live/`)
- **Custo:** a Genial estima cerca de R$ 0,50 de ida e volta por contrato de WIN na primeira faixa de volume ([Genial](https://www.genialinvestimentos.com.br/artigos/custo-real-day-trade/)). O ponto vale R$ 0,20 ([B3](https://b3.com.br/en_us/news/what-is-mini-index-win-and-why-does-it-attract-day-trade-newcomers.htm)). Exemplo: com o índice perto de 150 mil pontos, um contrato vale cerca de R$ 30 mil. Somando 1 tick de derrapagem por lado, a ida e volta fica perto de **0,01% a 0,02%**, contra 0,30% no spot cripto. O WIN anda menos por dia que as altcoins, mas, mesmo medindo o custo contra o tamanho do dia, ele sai algumas vezes mais barato. A venda é natural. Conferir na [tabela de tarifação da B3](https://www.b3.com.br/data/files/8F/A2/65/D5/A78DF91094DCD8F9AC094EA8/Tarifacao_V4.6_PT.pdf) e na corretora.
- **Contra:** é exatamente o mercado do estudo dos 97%, cheio de HFT. Lucro de day trade paga 20% de IR. Há alta alavancagem embutida. O Freqtrade não faz backtest de B3, então seria preciso um motor próprio ou outro (por exemplo o testador do MT5) e o histórico de barras via MT5.
- **Opinião:** é a maior mudança de todas. Faz sentido só depois de A ou B, ou se o objetivo final for operar na B3 de qualquer forma.

### E. Filtro de ML sobre as regras que chegaram perto (dentro das regras, como piloto)
- Pegar os sinais de H-104, H-101, H-100 e H-057 e treinar um classificador que só aprova o sinal quando a chance de passar do custo é alta (meta-labeling). O treino usa só a exploração, e a avaliação usa a validação. O FreqAI já está no Freqtrade.
- Mexe na precisão, não na frequência: em spot ajuda pouco com a regra de 2 dias. Combina melhor com A ou B.

### F. Como trazer mais pesquisa (melhoria do loop)
1. **Seguir a fonte primária, não o repositório de bot.** Varredura semanal no arXiv `q-fin.TR` e `q-fin.ST` e no SSRN com "cryptocurrency intraday", "perpetual", "order flow", "high-frequency", e o [Quantpedia](https://quantpedia.com/periodicity-in-cryptocurrencies-recurrent-patterns-in-volatility-and-volume/) como índice. Só entra no lab o artigo que testa fora da amostra **e** informa custo.
2. **Fontes novas para a seção 0 da fila:** Kim e Hansen 2026 (quarto de hora: o que não fazer), arXiv 2608.21888 (reversão por fluxo agressor), arXiv 2602.00776 (microestrutura com árvores), arXiv 2609.05663 (agentes de IA em produção: brackets mecânicos), Caporale e Plastun 2020 (momentum horário depois de dia anormal: base de H-057 e H-103).
3. **Regra para o scout:** toda ideia declara de onde vem o movimento acima do custo (quem está do outro lado e por que perde). Isso corta automaticamente o material de "indicador da moda".

## 7. O que não fazer

- Não comprar bot, sinal ou curso com resultado anunciado. Nenhum tem histórico auditado (seção 3).
- Não deixar um LLM decidir ordens ao vivo (seção 5).
- Não insistir em scalp de movimento pequeno no spot a mercado: a conta da seção 4 mostra por que não fecha.
- Não afrouxar gates para "fazer passar". O placar mostra que o problema é estrutural, não de rigor demais.

## 8. Decisões que são do dono

1. Abrir uma pista de **futuros perpétuos em dry-run**, a 1x, com venda a descoberto e cenários de custo próprios. Recomendação: sim, é a alavanca com mais suporte nos dados do lab.
2. **Ampliar para 25 a 30 pares.** Recomendação: sim, junto com o item 1.
3. Adicionar o **volume agressor comprador** como dado novo. Recomendação: sim, depois do 1.
4. **B3 (WIN/WDO)** como segundo mercado. Recomendação: depois; só se o objetivo final for a B3.
5. Piloto de **meta-labeling** nas regras que chegaram perto. Recomendação: depois de 1 ou 2.

Nada disso aprova operação real. Dinheiro real continua manual e fora do lab.
