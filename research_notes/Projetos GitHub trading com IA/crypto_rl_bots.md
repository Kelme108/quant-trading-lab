# Crypto / multi-asset trading bots with AI (LLM, FreqAI, RL, DL) on GitHub - state as of Nov 2026

Method note: star counts were read from GitHub repo pages or the GitHub search API via WebFetch on 2026-11-20 (the API was rate-limited/403 partway, and per-repo pages rarely show commit dates). Last-push dates exist only for repos returned by the search API. Everything else has "last commit: not verified".

## Which are the top 25+ repos and how active are they?

### Takeaway
The ecosystem splits into (a) mature execution frameworks with some ML hooks (freqtrade, Hummingbot, OctoBot, Jesse, Nautilus-type engines), (b) very high-star LLM-agent research demos (TradingAgents, ai-hedge-fund, Kronos) that explicitly disclaim real trading, and (c) older RL gyms/libraries (FinRL, gym-anytrading, TensorTrade, TradingGym) that are research/education-grade and in several cases stale. Star counts are not a reliable quality signal (see the fake-star finding below).

### Cited Findings (catalog; stars as of fetch date)

Production-style bots / frameworks
- freqtrade/freqtrade - ~57.1k stars, 11.8k forks, 33,453 commits on develop; spot exchanges Binance, BingX, Bitget, Bybit, Gate, HTX, Hyperliquid, Kraken, OKX; futures on Binance, Bitget, Bybit, Gate, Hyperliquid, Kraken, OKX; FreqAI module self-trains ML models adaptively. Last commit date not shown. Earlier snapshots: 48.7k (Apr 2026), 50.7k (May 2026) - [GitHub](https://github.com/freqtrade/freqtrade); [Star History](https://www.star-history.com/freqtrade/freqtrade/)
- hummingbot/hummingbot - ~21.3k stars, 5.2k forks; market-making/arbitrage framework; 11 sponsored connectors (Binance, Bitget, Gate.io, Hyperliquid, KuCoin, OKX, Backpack, Derive, Meteora, Orca, XRPL) plus 34 more including Foxbit (a Brazilian exchange), Mercado-type BR exchanges not listed; AI layer is "Condor", a separate harness linking LLM decisions to deterministic execution via the Hummingbot API (Telegram/web) - [GitHub](https://github.com/hummingbot/hummingbot)
- Drakkar-Software/OctoBot - 6,963 stars, last push 2026-11-19, described as free crypto bot for AI, grid, DCA, TradingView strategies on Binance, Hyperliquid and 15+ exchanges - [GitHub search API result](https://api.github.com/search/repositories?q=crypto+trading+bot+AI+in:description&sort=stars&per_page=30)
- jesse-ai/jesse - ~8.8k stars, MIT; live/paper trading spot/futures/DEX; Jesse MCP server for AI assistants (Claude, Codex, Cursor), scikit-learn ML pipeline from backtest labels; RL listed as "Coming Soon" - [GitHub](https://github.com/jesse-ai/jesse)
- Superalgos/Superalgos - ~5.8k stars, 6.0k forks, Apache-2.0, 23k+ commits, v1.6.1; visual no-code bot design, backtesting, paper trading, token-incentivized "social trading network"; tutorials use Binance; no explicit last-commit date, no first-class AI component found - [GitHub](https://github.com/Superalgos/Superalgos)
- elizaOS/eliza (ai16z lineage) - ~19.9k stars, 5.9k forks, MIT; general agent framework; the fetched page listed no trading plugins, so trading use is via third-party plugins (unverified) - [GitHub](https://github.com/elizaOS/eliza)
- richkuo/go-trader - 369 stars, pushed 2026-11-20; "AI-enabled" bot with backtest/paper/live - [GitHub API search](https://api.github.com/search/repositories?q=crypto+trading+bot+AI+in:description&sort=stars&per_page=30)
- binance/ai-trading-prototype - 150 stars, last push 2023-12-30 (stale prototype from the exchange itself) - same search result
- vadiminshakov/marti (Go, DCA + AI strategies, Binance/Bybit, 21 stars, pushed 2026-10-30); web3spreads/quant-flow (Hyperliquid perps, 42 stars); stefanoviana/deepalpha (DNN across 25 coins, 57 stars, pushed 2026-05-12); motshepula333/crypto-ai-trading-bot (154 stars, pushed 2026-11-20); OfficialZapret/AI-Trade-Bot (DEX contracts, 38 stars) - same search result. These are small/hobby tier; I did not audit code.

LLM agents / decision layers
- TauricResearch/TradingAgents - ~123.3k stars, 23.6k forks, v0.7.1 (Oct 2026); LangGraph multi-agent (analysts, bull/bear researchers, trader, risk team, PM); any Yahoo Finance ticker incl. crypto pairs like BTC-USD; "designed for research purposes", performance varies by LLM - [GitHub](https://github.com/TauricResearch/TradingAgents). Other blogs cite 40k/80k stars at earlier dates (growth, not conflict).
- virattt/ai-hedge-fund - ~64.8k stars, 11.4k forks, 964 commits; "proof of concept"; does not place trades; educational only - [GitHub](https://github.com/virattt/ai-hedge-fund)
- AI4Finance-Foundation/FinGPT - ~21.6k stars; LoRA fine-tuned finance LLMs (sentiment, forecaster); newest "What's New" entry on the page is Nov 2023, suggesting slowed activity (page may be stale) - [GitHub](https://github.com/AI4Finance-Foundation/FinGPT)
- AI4Finance FinRobot ~7k stars (equity research reports, not trade signals); Open Finance Lab AgenticTrading 218 stars, early-stage - [Pinggy](https://pinggy.io/blog/best_ai_trading_agents/) (vendor blog, secondary)
- alex-jb/orallexa-ai-trading-agent (72 stars, pushed 2026-11-11, bull/bear/judge debate), reunios2024/cortex-sentinel-trading-nexus (125 stars, pushed 2026-11-20, "Kronos model" fusion) - [GitHub search API](https://api.github.com/search/repositories?q=topic:trading-bot+topic:reinforcement-learning&sort=stars&per_page=15). Hobby tier, unaudited.
- okx-agent-trade-kit (126 stars) and mcp-metatrader5-server (245 stars, pushed 2026-11-16) are MCP toolkits letting LLM assistants place orders - search API results (see MT5 section).

Deep-learning forecasting
- shiyu-coder/Kronos - ~48.0k stars, 7.9k forks; decoder-only foundation model on tokenized candlesticks, claims training on 45+ exchanges; mini/small/base open, large closed; authors say fine-tune pipeline is "not a production-ready quantitative trading system" and backtest ignores costs/slippage - [GitHub](https://github.com/shiyu-coder/Kronos)

RL gyms / libraries
- AI4Finance-Foundation/FinRL - ~17.2k stars, 3.7k forks, 3,296 commits; A2C/DDPG/PPO/TD3/SAC via Stable-Baselines3; education/research positioning, points to successor FinRL-X/FinRL-Trading (~3.2k stars per [Pinggy](https://pinggy.io/blog/best_ai_trading_agents/)); only "basic" Alpaca live support; data includes Binance, CCXT, Yahoo - [GitHub](https://github.com/AI4Finance-Foundation/FinRL)
- tensortrade-org/tensortrade - ~7.3k stars, 1,093 commits, 39 open issues; Ray RLlib + Optuna; README admits "commission costs currently exceed prediction profits" (PPO on BTC/USD: +$239 at 0% fee vs -$650 at 0.1% fee vs buy-and-hold -$355, self-reported); install/version inconsistencies and an outdated community link - [GitHub](https://github.com/tensortrade-org/tensortrade)
- AminHP/gym-anytrading - ~2.4k stars, only 42 commits; minimal Buy/Sell Long/Short env; author points experts to gym-mtsim - [GitHub](https://github.com/AminHP/gym-anytrading)
- Yvictor/TradingGym - 1,932 stars, last push 2024-02-11; pskrunner14/trading-bot (DQN) 1,192 stars, last push 2023-12-03 (stale); javifalces/HFTFramework 312 stars, pushed 2026-11-17 (RL market making, Avellaneda-Stoikov); hugocen/freqtrade-gym 229 stars, pushed 2026-01-08; DQN-Trading 189 stars, last push 2021 (abandoned); NeuroEvolution-BTC-Trader 165 stars, last push 2021 (abandoned); TheDoctorAI/AI-Trader 80 stars, last push 2020 (abandoned); satoshimars last push 2019 (abandoned) - [GitHub search API](https://api.github.com/search/repositories?q=topic:trading-bot+topic:reinforcement-learning&sort=stars&per_page=15)
- AminHP/gym-mtsim - 528 stars, last push 2024-11-14; MT5 simulator + Gym env - MT5 search result below

Count: roughly 35 named repos above (including the stale and hobby ones).

### Inferences
- Activity as of Nov 2026: freqtrade, Hummingbot, OctoBot, TradingAgents, HFTFramework, go-trader are visibly active; the classic RL gym repos (TradingGym, pskrunner14, DQN-Trading, TradzQAI) have not been pushed since 2021-2024 and should be treated as abandoned reference code.
- TradingAgents/ai-hedge-fund/Kronos star counts (tens of thousands) reflect research/hype interest, not trading deployments, since each states it is not for real trading.

### Gaps
- Last-commit dates for freqtrade, Hummingbot, Jesse, Superalgos, Eliza, FinRL, FinGPT, TradingAgents, TensorTrade, gym-anytrading were not retrievable (GitHub API rate-limited; repo page fetch omits dates). Not found: Qlib, Nautilus Trader, FinRL-X exact stats, Hummingbot MCP status, OctoBot AI feature details, Eliza trading plugins.

## Which are production-grade vs hobby/demo? How is AI integrated?

### Takeaway
Only the execution frameworks (freqtrade, Hummingbot, OctoBot, Jesse, Superalgos) are operational tools; their AI is an add-on (ML-signal module in freqtrade/Jesse, LLM harness/MCP in Hummingbot/Jesse). LLM-agent and RL repos are research or demo grade by their own disclaimers.

### Cited Findings
- ML signal: FreqAI self-trains adaptive models inside freqtrade strategies - [GitHub](https://github.com/freqtrade/freqtrade); Jesse trains scikit-learn models from backtest-labelled data - [GitHub](https://github.com/jesse-ai/jesse)
- LLM decision layer with deterministic execution: Hummingbot Condor - [GitHub](https://github.com/hummingbot/hummingbot); LLM multi-agent debate: TradingAgents - [GitHub](https://github.com/TauricResearch/TradingAgents)
- MCP tool-bridging (LLM issues orders through a standard tool server): Jesse MCP; mcp-metatrader5-server; okx-agent-trade-kit - [Jesse](https://github.com/jesse-ai/jesse), [search result](https://api.github.com/search/repositories?q=metatrader5+brazil+OR+B3+OR+bovespa+OR+mini-indice&sort=stars&per_page=15)
- RL policy: FinRL (SB3 agents), TensorTrade (RLlib), gym-anytrading, freqtrade-gym; Jesse RL still "coming soon" - respective GitHub links above
- Sentiment/LLM fine-tuning: FinGPT (LoRA) - [GitHub](https://github.com/AI4Finance-Foundation/FinGPT)
- Foundation-model price prediction: Kronos - [GitHub](https://github.com/shiyu-coder/Kronos)
- FinRL maintainers position FinRL for education/research and point to FinRL-X for production - [GitHub](https://github.com/AI4Finance-Foundation/FinRL)

### Inferences
- Common practical architecture: ML/LLM generates a signal or analysis; a deterministic engine (freqtrade/Hummingbot) enforces risk and order logic. Direct LLM-to-order setups (MCP bridges) have no built-in risk layer unless added.

### Gaps
- No independent maturity audits or user-count/uptime data for any of these projects.

## Evidence on real-world profitability and common failure modes (overfitting, slippage, scam repos, key security)

### Takeaway
No credible independent evidence of sustained live profitability for the open-source AI bots was found; published numbers are self-reported backtests or single short runs. Security is a concrete, documented risk: fake "trading bot" repos have stolen wallet keys in 2025-2026.

### Cited Findings
- Backtests vs live: a FinRL PPO crypto portfolio reportedly returned 103% vs 93% BTC buy-and-hold; a 30-day TradingAgents run returned ~7% vs S&P 4.5% with 22% drawdown; the article calls these single runs, and the blog is a vendor blog; it lists costs of 15-40 bps per round trip, regime shift, overfitting, and the TradingAgents team reportedly advising against real money - [Pinggy](https://pinggy.io/blog/best_ai_trading_agents/)
- TensorTrade's own README shows profit turning to loss when 0.1% commission is added - [GitHub](https://github.com/tensortrade-org/tensortrade)
- Kronos, ai-hedge-fund, TradingAgents all disclaim real-trading suitability - [Kronos](https://github.com/shiyu-coder/Kronos), [ai-hedge-fund](https://github.com/virattt/ai-hedge-fund), [TradingAgents](https://github.com/TauricResearch/TradingAgents)
- A freqtrade tutorial headline claiming a 67.9% win rate exists on DEV; win rate is not profitability and this is promotional - [DEV](https://dev.to/trendrider/freqtrade-tutorial-2026-how-i-set-up-a-crypto-bot-that-hits-679-win-rate-18i5) (title only, not read)
- Malicious repos: SlowMist flagged a fake Polymarket bot asking users to put a wallet private key in .env, with a never-imported npm dependency ("clob-client-math") harvesting SSH keys, cloud logins and tokens; star/fork counts appeared inflated; StepSecurity found a copy-trading bot in a hijacked dev-protocol GitHub org with typosquatted npm packages; a popular Polymarket copy-trading bot reportedly exfiltrated private keys (Dec 2025); a Solana bot scam on GitHub - [search summary with sources incl. StepSecurity](https://www.stepsecurity.io/blog/malicious-polymarket-bot-hides-in-hijacked-dev-protocol-github-org-and-steals-wallet-keys), [Cointelegraph](https://cointelegraph.com/news/solana-trading-bot-github-malware-scam), [SafeDep](https://safedep.io/malicious-polymarket-npm-crypto-wallet-drainer/)
- Suspicious-listing signal: several small "AI crypto bot" repos in the search results have keyword-stuffed or repetitive descriptions (e.g. Kalshi-crypto-15m-trading-bot, gpt-trade-bot/chatgpt-trading-agent, okx-agent-trade-kit) per the fetch tool's description of the API results; not proven malicious - [GitHub search API](https://api.github.com/search/repositories?q=crypto+trading+bot+AI+in:description&sort=stars&per_page=30)

### Inferences
- Treat any repo that asks for a private key (rather than a trade-only, no-withdrawal API key with IP whitelist) as high risk; the most dangerous category observed is prediction-market/DEX/Solana bots with npm dependencies, less so established Python frameworks.
- Reasonable red flags: low-star repos with keyword-stuffed descriptions, recent star spikes, unused dependencies, instructions to paste wallet keys.
- Do not flag specific repos above as scams; none were verified malicious.

### Gaps
- No Reddit r/algotrading or r/freqtrade threads were retrieved, so no community-reported live PnL. No independent academic out-of-sample evaluation of FreqAI or FinRL live results found. No CVE/GHSA entries for freqtrade/Hummingbot/OctoBot checked.

## B3 / MetaTrader 5 / Brazil-focused AI trading repos

### Takeaway
No B3-specific AI trading repo was found. MT5-Python tooling exists (MCP servers, Gym env, Docker/Linux bridges) and could be used with a Brazilian broker offering B3 via MT5, but this is unverified; Foxbit is the only Brazilian exchange spotted (Hummingbot connector).

### Cited Findings
- MT5 ecosystem (stars, last push): TheSnowGuru/PyTrader connector 1,077 (2025-05); vdemydiuk/mtapi 711 (2026-11-17); isaiahbjork/Auto-GPT-MetaTrader-Plugin 568 (2023-11, stale); AminHP/gym-mtsim 528 (2024-11); gmag11/MetaTrader5-Docker 422 (2025-12); francomascareloai/EA_SCALPER_XAUUSD 302 (2026-11-19, WIP gold research, Brazilian-looking author name but unverified); Qoyyuum/mcp-metatrader5-server 245 (2026-11-16); lucas-campagna/mt5linux 241 (2026-10-27); Joaopeuko/Mql5-Python-Integration 217 (2025-12-15); landim32/LadinoBot 206 (archived, 2024-09; MQL5 robot, author possibly Brazilian, unverified) - [GitHub search API](https://api.github.com/search/repositories?q=metatrader5+brazil+OR+B3+OR+bovespa+OR+mini-indice&sort=stars&per_page=15)
- triqbit/tradingbot: DRL bot for XAUUSD with PyTorch (MIT) - [GitHub](https://github.com/triqbit/tradingbot); jblanked/metatrader-ai (OpenAI/DeepSeek assistant, PyPI) - [PyPI](https://pypi.org/project/metatrader-ai/1.2.1/); MQL5 article on LLM + MT5 bot - [MQL5](https://www.mql5.com/en/articles/20354)
- Search for "no B3 repos": web search found none specifically for B3 - [search results](https://pypi.org/project/metatrader-ai/1.2.1/); Hummingbot lists a Foxbit connector - [GitHub](https://github.com/hummingbot/hummingbot)

### Inferences
- The MetaTrader5 Python package works only on Windows (not verified here; mt5linux/Docker repos exist precisely to work around this), so B3 + AI work is likely done in private or Portuguese-language repos that my English-keyword searches did not surface.

### Gaps
- Not found: Profit/Nelogica repos with AI, Binance BR/Mercado Bitcoin/Foxbit-specific AI bots, B3 mini-index/mini-dollar ML repos, Portuguese-language search. Recommend a follow-up search with Portuguese terms (robô de investimento, mini índice, WIN$/WDO, ProfitDLL, backtrader B3).
