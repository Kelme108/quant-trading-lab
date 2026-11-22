# Repositorios GitHub que usam Claude para trading e investimento (catalogo, 20/nov/2026)

Metodo: estrelas, data do ultimo push, linguagem e licenca vieram da API publica do GitHub (api.github.com/repos/..., e /search/repositories) consultada em 2026-11-20; fonte de cada linha = pagina do repo em https://github.com/<owner>/<repo>. READMEs lidos via WebFetch. A API ficou limitada por rate limit no fim, entao virattt/ai-hedge-fund e TauricResearch/TradingAgents tem estrelas apenas de fontes secundarias.

## 1. Quais repos sao mais notaveis (estrelas/atividade)? Quantos ha?

### Takeaway
Ha bem mais de 25 repos relevantes. O topo e dominado por colecoes de skills para Claude Code (tradermonty, 7,4k), pontes para TradingView (tradesdontlie, 7,3k), o repo oficial da Anthropic para servicos financeiros (41k, mas analitico, sem execucao) e frameworks multi-agente model-agnostic (TradingAgents, ai-hedge-fund, dezenas de milhares segundo fontes secundarias). Quase todos sao educacionais/experimentais e a cauda longa tem 0-40 estrelas.

### Cited Findings
Tabela: repo | estrelas | ultimo push | linguagem | licenca | o que faz / uso de Claude. (Todos os dados numericos: API GitHub, 2026-11-20; link = repo.)

**A. Oficial / grandes colecoes de skills e plugins**
- [anthropics/financial-services](https://github.com/anthropics/financial-services) | 41.420 | 2026-11-12 | Python | Apache-2.0 | Repo oficial da Anthropic: agentes de referencia (Pitch, Market Researcher, Earnings Reviewer, Model Builder, KYC...), plugins por vertical (equity research, IB, PE, fund admin, advisors), conectores MCP (FactSet, S&P, LSEG, Morningstar, PitchBook etc.). README diz que NAO executa transacoes nem faz recomendacao de investimento; saidas ficam para aprovacao humana (leitura do README).
- [tradermonty/claude-trading-skills](https://github.com/tradermonty/claude-trading-skills) | 7.409 | 2026-11-20 (ativo) | Python | MIT | 74 skills em 9 areas (regime de mercado 16, pesquisa de estrategia 15, swing 7, trade planning 7, dividend 5, trade memory 6...). Metodologias: VCP (Minervini), CANSLIM, PEAD, pairs, simulacao de opcoes. Usa FMP (free 250 req/dia), FINVIZ Elite (US$39,50/mes), Alpaca MCP para paper. README: nao e para trading totalmente automatico; exemplos sao ficticios; nenhum resultado/backtest reportado.
- [rkiding/awesome-finance-skills](https://github.com/rkiding/awesome-finance-skills) | 3.133 | 2026-03-29 (parado ~8 meses) | Python | Apache-2.0 | Colecao de skills de analise financeira. (Fonte secundaria Algolia indicava 10,6k; contradiz a API -- usar API.)
- [himself65/finance-skills](https://github.com/himself65/finance-skills) | 3.579 | 2026-11-04 | JavaScript | MIT | Skills de analise financeira (payoff de opcoes, correlacoes, dados de mercado).
- [agiprolabs/claude-trading-skills](https://github.com/agiprolabs/claude-trading-skills) | 579 | 2026-09-03 | Python | MIT | 68 skills cripto/DeFi/quant; multi-agente (Claude Code, Cursor, Codex, Gemini CLI).
- [staskh/trading_skills](https://github.com/staskh/trading_skills) | 416 | 2026-11-17 | Python | MIT | "Claude powered advisor system for option traders".
- [brainbytes-dev/everything-claude-trading](https://github.com/brainbytes-dev/everything-claude-trading) | 368 | 2026-03-14 | JS | MIT | 18 agentes, 82 skills para Claude Code; sem commits ha 8 meses.
- [MobiusQuant/OpenMobius-skill](https://github.com/MobiusQuant/OpenMobius-skill) | 730 | 2026-11-12 | Python | Apache-2.0 | Skill de conhecimento ICT/SMC para Claude Code/Codex.
- [galleonlabs/hypergrok-trading-desk](https://github.com/galleonlabs/hypergrok-trading-desk) | 574 | 2026-11-17 | Python | MIT | Mesa Hyperliquid para agentes: 7 papeis, 17 skills.
- [DaviddTech/ai-trading-agent](https://github.com/DaviddTech/ai-trading-agent) | 99 | 2026-09-11 | -- | MIT | Diretorio de skills "AI hedge fund" para Claude/Codex/Cursor.
- [cubexch/ai-fund](https://github.com/cubexch/ai-fund) | 37 | 2026-04-08 | TypeScript | sem licenca | "Mesa" com 42 agentes estilo hedge fund para Claude Code (cripto e acoes).

**B. Plataformas / agentes de pesquisa e trading**
- [ginlix-ai/LangAlpha](https://github.com/ginlix-ai/LangAlpha) | 2.333 | 2026-11-20 | Python | Apache-2.0 | "Harness for agentic trading": pesquisa persistente, relatorios, agendamento, ordens via Robinhood/IBKR/moomoo/Webull com aprovacao; model-agnostic (Claude via API ou assinatura Claude Code); sandboxes; servico hospedado em beta; self-host com funcoes reduzidas. ~4,6k commits.
- [simonlin1212/Vibe-Research](https://github.com/simonlin1212/Vibe-Research) | 3.827 | 2026-11-12 | TypeScript | MIT | Workbench de pesquisa A-shares/EUA/HK (descricao do repo; nao verifiquei README em detalhe) ; [vibe-astock](https://github.com/simonlin1212/vibe-astock) 1.089 | Apache-2.0 irmao para A-shares.
- [KylinMountain/TradingAgents-AShare](https://github.com/KylinMountain/TradingAgents-AShare) | 909 | 2026-11-13 | Python | NOASSERTION | Variante A-shares de TradingAgents com 15 agentes.
- [Blave-TW/blave-agent](https://github.com/Blave-TW/blave-agent) | 358 | 2026-11-20 | Python | Apache-2.0 | Infra quant para agentes (desktop app).
- [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) | fontes secundarias divergentes: ~32k (mar/2026), >80k (mai/2026), 108k (LinkedIn) -- nao verificado na API | Framework multiagente LLM; suporta Anthropic como provider (changelog v0.2.0 multi-provider incl. Claude) -- [blog](https://ice-ice-bear.github.io/posts/2026-03-17-trading-agents/), [Pinggy](https://pinggy.io/blog/best_ai_trading_agents/). Claude nao e o foco, e um dos LLMs.
- [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) | ~51-59k segundo fontes secundarias (nao verificado) | agentes "investidores lendarios"; aceita ANTHROPIC_API_KEY como um dos providers -- [docsearch](https://docsearch.algolia.com/mcp/docs/repo/virattt/ai-hedge-fund).
- [YizhiSong/FriesTrader](https://github.com/YizhiSong/FriesTrader) | 319 | 2026-11-07 | Python | MIT | Agente que opera ordens reais na Robinhood (MCP "Agentic Trading") com 2 sessoes Claude Code agendadas por dia (tese/conviccao); filtros, ranking, sizing e risco em Python deterministico (risk_rules.json); comeca em dry_run; so o humano liga modo live; roda em assinatura Claude Pro. Sem resultados de P&L; autor admite que nao ha evidencia de que stock-picking por LLM bata indice e que o passo de raciocinio nao pode ser backtestado honestamente (README).
- [Byte-Ventures/claude-trader](https://github.com/Byte-Ventures/claude-trader) | 25 | 2026-10-16 | Python | AGPL-3.0 | Bot BTC (Coinbase/Kraken) com revisao de trades por IA e modo paper; "experimental".
- [JDxus/ClawQuant](https://github.com/JDxus/ClawQuant) | 33 | 2026-04-06 | TypeScript | MIT | Agente que aprende de cada trade (replay, atribuicao); Claude Code CLI ou Vercel AI SDK; CCXT. Parado ~7 meses.
- [Alzarak/trading-bot](https://github.com/Alzarak/trading-bot) | 5 | 2026-03-24 | Python | sem licenca | Plugin Claude Code, day trading de acoes via Alpaca. Abandonado/marginal.
- [pouriamrt/trading-live-claude](https://github.com/pouriamrt/trading-live-claude) | 0 | 2026-05-14 | Python | sem licenca | Framework Questrade, Claude Code como orquestrador, paper-first.
- [pupedator/binance-futures-ai-bot](https://github.com/pupedator/binance-futures-ai-bot) | 1 | 2026-03-17 | Python | MIT | Claude como motor de decisao, filtros ADX/ER, sizing por volatilidade.
- jamesbarlow/AI-Trading-Bot: apareceu em busca com alegacao de retornos 8-27% ao dia (nao verificado, tratar como marketing); a API retornou "Not Found" -- repo removido/renomeado.
- [regardo911/seven-ai-trading-bots](https://github.com/regardo911/seven-ai-trading-bots) | 2 | 2026-07-16 | Python | MIT | Codigo de apoio do livro "Use Claude to Build 7 AI Trading Bots".
- Cauda longa de "AI hedge fund" com Claude, quase todas 0-2 estrelas: [barnel18/ai-hedge-fund](https://github.com/barnel18/ai-hedge-fund) (9 agentes Claude, board vota, Alpaca paper), [GirishVerm/ai-hedge-fund](https://github.com/GirishVerm/ai-hedge-fund), [StanleyChanH/super-hedge-fund-skill](https://github.com/StanleyChanH/super-hedge-fund-skill) (10), [arterorx/crypto-event-bot](https://github.com/arterorx/crypto-event-bot) (Claude como filtro qualitativo, 4 estrategias), [Hafida3/TRADING-BOT](https://github.com/Hafida3/TRADING-BOT) (ReAct loop), [dmrrlc/binance-anthropic-trading-bot](https://github.com/dmrrlc/binance-anthropic-trading-bot) (ultimo push jan/2025 -- abandonado).

**C. Mercados de previsao**
- [ryanfrigo/kalshi-ai-trading-bot](https://github.com/ryanfrigo/kalshi-ai-trading-bot) | 660 | 2026-11-09 | Python | MIT | Kalshi; LLM unico (via OpenRouter) para confianca direcional + Kelly fracionario; skill Claude + servidor MCP com "governor"; etapa adversarial (SKEPTIC). **Resultado reportado honesto:** veredito "NO MEASURED EDGE" em 2026-10-02: n=55 trades, win rate 58% vs 60% implicado (edge -1,9 pp), Brier 0,2356; backtest e placeholder; README corrige alegacao anterior de "ensemble de 5 modelos".
- [caiovicentino/polymarket-mcp-server](https://github.com/caiovicentino/polymarket-mcp-server) | 753 | 2026-09-20 | Python | MIT | MCP Polymarket, 45 tools; limites default US$1.000/ordem, US$5.000 exposicao, confirmacao >US$500; v0.1.0; sem backtest; "enterprise-grade" sem metricas.
- [randomness11/probablyprofit](https://github.com/randomness11/probablyprofit) 40 (jan/2026); [Willy196616/ClaudePolymarketTrader](https://github.com/Willy196616/ClaudePolymarketTrader) 2.

**D. Backtest / pesquisa quant**
- [mnemox-ai/tradememory-protocol](https://github.com/mnemox-ai/tradememory-protocol) | 1.450 | 2026-10-23 | Python | MIT | Memoria local + trilha de auditoria (hash SHA-256, Merkle, RFC 3161) para agentes; 20 tools MCP; "brake" preview entre agente e MCP do broker. Autor admite validacao com n=14 trades, insuficiente para concluir.
- [varrdinc/varrd](https://github.com/varrdinc/varrd) 25 | MIT | pesquisa com event studies; [Jimmy7892/quant-research-skill](https://github.com/Jimmy7892/quant-research-skill) 9 (skill de backtest "honesto"); [jefrnc/quant-llm-skills](https://github.com/jefrnc/quant-llm-skills) 1 (armadilhas: lookahead bias); [RW-git-hub/claude-quant](https://github.com/RW-git-hub/claude-quant) 2; [DonCoyoteS/claude-mt5-trader](https://github.com/DonCoyoteS/claude-mt5-trader) 10 (MT5, walk-forward); [ChampionKerr/sigma-quant-stream](https://github.com/ChampionKerr/sigma-quant-stream) 1 (enxame de agentes Claude Code, AGPL). Todos muito pequenos.

### Inferences
- A categoria tem alto volume e baixa qualidade media: a maior parte esta abaixo de 50 estrelas, sem testes e sem resultados; o sinal de qualidade esta nos repos que publicam limites/negativos (kalshi-bot, FriesTrader, tradememory).
- Estrelas de skills/MCP "ferramenta" crescem mais que as de bots autonomos; ferramentas de analise sao mais seguras de adotar.
- Estrelas de repos grandes sao suscetiveis a inflacao/divergencia entre fontes (ex.: awesome-finance-skills 3,1k na API vs 10,6k em agregador).

### Gaps
- Estrelas exatas de TradingAgents e ai-hedge-fund (rate limit; so fontes secundarias divergentes).
- Nao inspecionei commits/issues em profundidade nem rodei os repos; "maturidade" baseada em README, estrelas, data de push.
- Nao consultei threads do HN/Reddit r/algotrading nem registries (mcp.so, glama, smithery) diretamente.

## 2. Servidores MCP para trading/dados de mercado e maturidade

### Takeaway
Existem MCPs oficiais (Alpaca, Bitget, Kraken CLI, TipRanks, Massive) e uma enorme cauda de servidores comunitarios para Binance, IBKR e TradingView. O Alpaca e o mais maduro; IBKR comunitarios sao pequenos ou arquivados; TradingView MCP funciona via CDP no app desktop, nao e oficial.

### Cited Findings
Execucao / brokers:
- [alpacahq/alpaca-mcp-server](https://github.com/alpacahq/alpaca-mcp-server) | 1.101 | push 2026-11-13 | Python | MIT | Oficial Alpaca; v2 reescrito sobre FastMCP/OpenAPI; ~72 tools (contagem minha a partir do README; docs da Alpaca citam 43 e 65 em momentos diferentes: [docs](https://docs.alpaca.markets/docs/alpaca-mcp-server)); paper por padrao (ALPACA_PAPER_TRADE=true); aviso: revisar propostas do LLM, nao expor 0.0.0.0 sem autenticacao; sem suporte a Claude mobile (precisa MCP remoto). Instalacao: `claude mcp add alpaca ... uvx alpaca-mcp-server`.
- [krakenfx/kraken-cli](https://github.com/krakenfx/kraken-cli) | 813 | 2026-10-29 | Rust | MIT | CLI oficial Kraken (cripto, acoes tokenizadas, forex, futuros) para terminal ou agente de IA.
- [Bitget-AI/agent_hub](https://github.com/Bitget-AI/agent_hub) | 234 | 2026-06-30 | JS | MIT | Toolkit oficial Bitget para Claude/Cursor/Codex/ChatGPT.
- IBKR (todos nao oficiais): [ArjunDivecha/ibkr-mcp-server](https://github.com/ArjunDivecha/ibkr-mcp-server) 35 estrelas, ARQUIVADO (push 2025-07-23; arquivado 2026-04-11 segundo [resultado de busca](https://github.com/ArjunDivecha/ibkr-mcp-server)); [danielkristofik/mcp_claude_ibkr](https://github.com/danielkristofik/mcp_claude_ibkr) 6 (ordens exigem aprovacao explicita); [happy-shine/ibkr_mcp](https://github.com/happy-shine/ibkr_mcp) 18 (skill Claude Code, login TWS automatizado so macOS). LangAlpha tambem integra IBKR.
- Binance: dezenas de servidores com 0-4 estrelas (ex. [KumailQazi/krmaazha-binance-mcp](https://github.com/KumailQazi/krmaazha-binance-mcp) 4, [AlgoVesta/mcp](https://github.com/AlgoVesta/mcp) 4 - 16 exchanges, [danishashko/binance-mcp-server](https://github.com/danishashko/binance-mcp-server) 2). Nenhum com adocao relevante; varios do tipo "security-first" com saques desabilitados.
- Robinhood: MCP "Agentic Trading" oficial da Robinhood e consumido por FriesTrader e LangAlpha (conforme READMEs); nao verifiquei o repo da Robinhood.
- Prediction markets: Polymarket MCP (753) e Kalshi toolkit (660) acima.

TradingView:
- [tradesdontlie/tradingview-mcp](https://github.com/tradesdontlie/tradingview-mcp) | 7.255 | 2026-10-21 | JS | NOASSERTION | Conecta Claude Code ao TradingView Desktop via Chrome DevTools Protocol; exige assinatura TradingView; nao afiliado; dados processados localmente; forks/derivados: greenpeas007 (58), FerroxLabs/tvcontrol (63, 88 tools), coocolab (36), JostQQ (19). Pine Script: [daviddme/tradingview-indicator-search-mcp-server](https://github.com/daviddme/tradingview-indicator-search-mcp-server) 141, [Spoofkapoof/TradingViewMCPServer](https://github.com/Spoofkapoof/TradingViewMCPServer) 64.
- [jackson-video-resources/claude-tradingview-mcp-trading](https://github.com/jackson-video-resources/claude-tradingview-mcp-trading) | 625 | 2026-05-15 (~6 meses sem push) | JS | sem licenca | Estrategia BTC (van de Poppe / Tone Vays) em rules.json, MACD, executa na BitGet; guardrails MAX_TRADE_SIZE_USD, 1% risco/trade, PAPER_TRADING; roda em VPS via cron; sem alegacao de retorno; links aparentemente de afiliados nao declarados (leitura do README). Repo ligado a videos do YouTube (marketing).

Dados de mercado:
- [wshobson/maverick-mcp](https://github.com/wshobson/maverick-mcp) 732 | 2026-11-13 | MIT | Yahoo Finance, analise tecnica, portfolio, backtest.
- [wshobson/mcp-trader](https://github.com/wshobson/mcp-trader) 274 | 2025-08-24 (parado >1 ano).
- [massive-com/mcp_massive](https://github.com/massive-com/mcp_massive) 405 | 2026-11-20 | MIT (ex-Polygon, oficial).
- [Alex2Yang97/yahoo-finance-mcp](https://github.com/Alex2Yang97/yahoo-finance-mcp) 372 | 2026-09-19 | MIT.
- [TickDB](https://github.com/TickDB/tickdb-unified-realtime-marketdata-api) 938 | MIT; [TipRanks/mcp](https://github.com/TipRanks/mcp) 16 (oficial); [tiingo-mcp](https://github.com/major7apps/tiingo-mcp) 12; [CohenD/fin-data-mcp](https://github.com/CohenD/fin-data-mcp) 5 (83 tools sem chave); [BlockRunAI/awesome-finance-mcp](https://github.com/BlockRunAI/awesome-finance-mcp) 263 (lista curada).
- Anthropic: conectores MCP de dados institucionais (FactSet, S&P, LSEG, Morningstar...) em [anthropics/financial-services](https://github.com/anthropics/financial-services).

### Inferences
- Maturidade: Alpaca (oficial, 1,1k, ativo) > TradingView CDP (popular mas dependente de app e ToS) > dados (maverick, massive) > comunitarios de Binance/IBKR (hobby; IBKR principal arquivado).
- Muitos MCPs de cripto sao quase duplicados com 0-4 estrelas -- baixo sinal.

### Gaps
- Nao verifiquei registries (Smithery/Glama/mcp.so) nem numero de instalacoes; sem dados de uso real.
- Repo oficial da Robinhood e de IBKR nao localizados/verificados.
- QuantConnect MCP e Freqtrade+Claude nao checados (rate limit).

## 3. Padroes de arquitetura recorrentes

### Takeaway
Tres padroes: (1) Claude como analista/pesquisador com humano decidindo (anthropics/financial-services, tradermonty, LangAlpha); (2) Claude como gerador de codigo/regras/estrategias (rules.json a partir de transcricoes, quant skills, backtests); (3) Claude como executor semi-autonomo cercado por regras deterministicas (FriesTrader, TradingView+BitGet, Kalshi bot). Os repos mais serios colocam a seguranca em codigo deterministico, nao no julgamento do modelo.

### Cited Findings
- Analista: README da Anthropic diz que agentes produzem material para revisao humana e nao executam transacoes -- [anthropics/financial-services](https://github.com/anthropics/financial-services); tradermonty foca em revisao, risco e journaling, nao em "terceirizar" compra/venda -- [repo](https://github.com/tradermonty/claude-trading-skills).
- Gerador de regras/codigo: claude-tradingview-mcp-trading gera rules.json a partir de transcricoes de YouTube e executa -- [repo](https://github.com/jackson-video-resources/claude-tradingview-mcp-trading).
- Executor com guarda-corpos: FriesTrader (Claude so escreve tese; Python faz filtros, sizing; dry_run; humano liga live; log append-only) -- [repo](https://github.com/YizhiSong/FriesTrader); LangAlpha (ordens como chamadas JSON, credenciais fora do sandbox, aprovacao e execucao unica por ordem) -- [repo](https://github.com/ginlix-ai/LangAlpha); tradememory "brake" proxy entre agente e MCP do broker -- [repo](https://github.com/mnemox-ai/tradememory-protocol).
- Multiagente "firma/hedge fund" (analistas, bull/bear debate, risk manager com veto, board vota): TradingAgents, ai-hedge-fund, barnel18, Maxy-Zou, Abhirup70 (veto do risco) -- links na secao 1.
- Memoria/diario de trades como camada: tradememory, "trade memory loop" do tradermonty.
- Orquestracao agendada: sessoes Claude Code via cron/scheduler (FriesTrader, VPS+cron).
- Model-agnostic: Claude e apenas um provider em LangAlpha, TradingAgents, ai-hedge-fund, kalshi bot (via OpenRouter).

### Inferences
- A tendencia de 2026 e "Claude Code + skills + MCP" substituindo bots monoliticos com chamada de API; assinatura Claude (Pro) viabiliza agentes baratos.
- Separar julgamento (LLM) de execucao/risco (codigo) e a convergencia de design.

### Gaps
- Nao ha comparacao empirica de padroes; nenhum benchmark independente encontrado.

## 4. Riscos e limitacoes documentados / resultados reportados

### Takeaway
Nenhum repo verificado apresenta desempenho auditado positivo. O unico dado quantitativo (Kalshi bot) mostra ausencia de edge. Autores serios documentam: impossibilidade de backtestar o raciocinio do LLM (vazamento de conhecimento), amostras minusculas, riscos de ordens reais e de exposicao de chaves.

### Cited Findings
- Kalshi bot: "NO MEASURED EDGE", n=55, win 58% vs 60% implicado, edge -1,9 pp, Brier 0,2356, dados nao reproduziveis; perdas historicas com dinheiro real em "Beast Mode" -- [repo](https://github.com/ryanfrigo/kalshi-ai-trading-bot).
- FriesTrader: sem track record de stock-picking LLM superando indice; raciocinio nao backtestavel honestamente porque o modelo pode conhecer desfechos historicos; limites (risk_rules.json) sao o mecanismo real de seguranca -- [repo](https://github.com/YizhiSong/FriesTrader).
- tradememory: validacao empirica em n=14 trades, "largura de intervalos impede conclusao"; trilha "tamper-evident, nao tamper-proof"; brake e preview (recusa opcoes/stop-limit) -- [repo](https://github.com/mnemox-ai/tradememory-protocol).
- Alpaca MCP: pode executar trades reais; revisar acoes propostas pelo LLM especialmente opcoes multi-leg; HTTP sem autenticacao se exposto -- [repo](https://github.com/alpacahq/alpaca-mcp-server).
- Polymarket MCP: v0.1.0, sem backtest, "production-ready" sem metricas -- [repo](https://github.com/caiovicentino/polymarket-mcp-server).
- claude-tradingview-mcp-trading: recomenda desabilitar saques e whitelisting de IP nas chaves; links de afiliados; "not financial advice" -- [repo](https://github.com/jackson-video-resources/claude-tradingview-mcp-trading).
- LangAlpha: self-host sem login (qualquer um com acesso age como usuario); servico em beta -- [repo](https://github.com/ginlix-ai/LangAlpha).
- Custo: FriesTrader usa Claude Pro (a partir de ~US$200/ano segundo o README) sem gasto de API medido, sem custos por dia reportados; tradermonty requer FINVIZ Elite US$39,50/mes para varias skills -- [FriesTrader](https://github.com/YizhiSong/FriesTrader), [tradermonty](https://github.com/tradermonty/claude-trading-skills).
- Alegacao de retorno de 8-27% ao dia em jamesbarlow/AI-Trading-Bot aparece em resultado de busca; nao verificavel e o repo nao esta mais disponivel na API.
- Avaliacao geral: [Pinggy "Best AI Trading Agents in 2026: Do They Actually Make Money?"](https://pinggy.io/blog/best_ai_trading_agents/) apareceu nos resultados; nao li o conteudo.

### Inferences
- Latencia: padrao de sessoes diarias agendadas (nao HFT) sugere que LLM so serve a horizontes de horas/dias; nenhum repo reporta latencia mensurada (nao encontrei).
- Alucinacao: mitigada via gates deterministicos, etapas adversariais (SKEPTIC), logs de fontes; nao medida.
- Alegacoes de lucro em README/videos devem ser tratadas como marketing; varios repos ligados a YouTube/afiliados.

### Gaps
- Sem estudos independentes de P&L, custo de tokens por trade ou latencia.
- Threads HN/Reddit com criticas nao consultadas.
- Repos abandonados sinalizados: ArjunDivecha/ibkr-mcp-server (arquivado), wshobson/mcp-trader (ago/2025), dmrrlc/binance-anthropic-trading-bot (jan/2025), rkiding/awesome-finance-skills e everything-claude-trading (mar/2026), ClawQuant (abr/2026), cubexch/ai-fund (abr/2026), jackson-video-resources (mai/2026). "Abandono" baseado so em data do ultimo push.
