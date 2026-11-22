# Quant Trading Infrastructure and Strategy Repos (state as of 2026-11-20)

Method note: stars and pushed_at come from GitHub Search API results fetched 2026-11-20 (topic searches: backtesting, algorithmic-trading, portfolio-optimization, quantitative-finance, plus a direct repo query). "pushed_at" is last push to any branch, not necessarily a release. The API became rate-limited (403) midway, so some repos (zipline-reloaded, Jesse details, LEAN details, Riskfolio features) lack extra detail. Search API results were truncated to the first ~17 per topic, so repos beyond the cut-off may be missing.

## Which are the top 30+ repos by stars and activity, grouped by category?

### Takeaway
The big, active ecosystems are freqtrade (57k), Qlib (50k), NautilusTrader (31.7k), LEAN (22.6k), hummingbot (21k), FinRL (17k), vectorbt (9.9k), Jesse (8.8k). Backtrader (23.8k) and Quantopian zipline (20k) are popular but stale (last push 2024). mlfinlab is stale since 2023, Stock-Prediction-Models is archived. A new wave of LLM-agent repos (Vibe-Trading 38.6k, QuantDinger, daily_stock_analysis) is very active.

### Cited Findings
Backtesting engines and live-capable platforms
- freqtrade/freqtrade — 57,109 stars, Python, pushed 2026-11-19 (crypto bot, backtest + hyperopt + live) — [GitHub API topic search](https://api.github.com/search/repositories?q=topic:algorithmic-trading&sort=stars&per_page=30)
- nautechsystems/nautilus_trader — 31,709 stars, Rust core + Python control plane, LGPL-3.0, pushed 2026-11-20; same strategy code in backtest and live; nanosecond-resolution backtests; many venue adapters (crypto CEX/DEX, FX, equities, futures, options, betting); v2 release candidates flagged "not recommended for production" on README — [GitHub](https://github.com/nautechsystems/nautilus_trader); stats via [API query](https://api.github.com/search/repositories?q=repo:nautechsystems/nautilus_trader+repo:QuantConnect/Lean)
- QuantConnect/Lean — 22,633 stars, C#, Apache-2.0, pushed 2026-11-20 — [API](https://api.github.com/search/repositories?q=repo:nautechsystems/nautilus_trader+repo:QuantConnect/Lean)
- mementum/backtrader — 23,766 stars, Python, last push 2024-08-19 (effectively stalled) — [API backtesting topic](https://api.github.com/search/repositories?q=topic:backtesting&sort=stars&per_page=30); a 2026 blog comparison calls it "mostly stalled" and another says unmaintained since 2019 (blog claims, inconsistent with 2024 push) — [DEV comparison search](https://dev.to/pickuma/python-backtesting-frameworks-compared-backtrader-vectorbt-and-zipline-reloaded-41l8)
- quantopian/zipline — 20,258 stars, last push 2024-02-13 (original unmaintained; use zipline-reloaded fork) — [API algorithmic-trading topic](https://api.github.com/search/repositories?q=topic:algorithmic-trading&sort=stars&per_page=30)
- polakowo/vectorbt — 9,902 stars, Python, pushed 2026-11-11; open-source edition of VectorBT PRO; Numba/NumPy vectorized; walk-forward optimization; fees param; parallelization, limit orders, leverage, portfolio optimization are PRO-only — [GitHub](https://github.com/polakowo/vectorbt)
- kernc/backtesting.py — 9,268 stars (GitHub page shows 9.3k), Python, pushed 2026-08-05 — [API](https://api.github.com/search/repositories?q=topic:backtesting&sort=stars&per_page=30)
- jesse-ai/jesse — 8,824 stars, Python, pushed 2026-11-17 (crypto) — [API](https://api.github.com/search/repositories?q=topic:algorithmic-trading&sort=stars&per_page=30)
- nkaz001/hftbacktest — 5,122 stars, Rust, pushed 2025-12-23 (~11 months stale; flag as slowing); backtests in Python 3.11+ with Numba, models queue position and feed/order latency, L2/L3 order book; live bot Rust-only, Binance Futures and Bybit — [API](https://api.github.com/search/repositories?q=topic:backtesting&sort=stars&per_page=30), [GitHub](https://github.com/nkaz001/hftbacktest)
- hummingbot/hummingbot — 21,315 stars, Python, pushed 2026-11-20 (market making/arbitrage bot framework) — [API](https://api.github.com/search/repositories?q=topic:backtesting&sort=stars&per_page=30)
- StockSharp/StockSharp — 11,139 stars, C#, pushed 2026-11-19 — same API
- edtechre/pybroker — 3,724 stars, Python, pushed 2026-11-16 (ML-oriented backtesting) — same API
- pmorissette/bt — 3,045 stars, Python, MIT, pushed 2026-11-20 — [API](https://api.github.com/search/repositories?q=repo:nautechsystems/nautilus_trader+repo:pmorissette/bt)
- zvtvz/zvt 4,338 (pushed 2026-07-01); fasiondog/hikyuu 3,733 (C++, pushed 2026-11-20) — [API](https://api.github.com/search/repositories?q=topic:backtesting&sort=stars&per_page=30)
- zipline-reloaded: not retrieved (403); appears in awesome-quant's Trading and Backtesting list — [awesome-quant](https://github.com/wilsonfreitas/awesome-quant)
- ccxt/ccxt — 44,937 stars, Python/JS exchange connectivity library, MIT, pushed 2026-11-20 — [API](https://api.github.com/search/repositories?q=repo:ccxt/ccxt+repo:Drakkar-Software/OctoBot)
- Drakkar-Software/OctoBot — 6,963 stars, GPL-3.0, pushed 2026-11-19 — same

Portfolio optimization / analytics
- PyPortfolio/PyPortfolioOpt — 6,174 stars, pushed 2026-07-07 — [API](https://api.github.com/search/repositories?q=topic:portfolio-optimization&sort=stars&per_page=15)
- dcajasn/Riskfolio-Lib — 4,616 stars, pushed 2026-11-04 — same
- skfolio/skfolio — 2,662 stars, pushed 2026-11-20 (scikit-learn-style API) — same
- cvxgrp/cvxportfolio — 1,327 stars, pushed 2026-04-27 — same
- ranaroussi/quantstats — 7,900 stars, pushed 2026-11-02 — [API](https://api.github.com/search/repositories?q=topic:algorithmic-trading&sort=stars&per_page=30)
- jankrepl/deepdow 1,202 (last push 2024-01); tradytics/eiten 3,329 (last push 2022, stale) — API portfolio-optimization link above

ML / AI for trading
- microsoft/qlib — 50,453 stars, pushed 2026-11-04; full ML pipeline (data, model zoo incl. GBDT/LSTM/Transformer/TFT, backtest, RL order execution), Alpha158/Alpha360, `qrun` workflow, RD-Agent LLM automation of factor/model R&D; official dataset temporarily disabled; recent breaking change requires `trusted=True` to load recorder artifacts — [GitHub](https://github.com/microsoft/qlib)
- AI4Finance-Foundation/FinRL — 17,152 stars, pushed 2026-11-18 (deep RL) — [API](https://api.github.com/search/repositories?q=topic:algorithmic-trading&sort=stars&per_page=30)
- stefan-jansen/machine-learning-for-trading — 21,920 stars, pushed 2026-11-18 (book notebooks) — same
- hudson-and-thames/mlfinlab — 4,972 stars, last push 2023-10-02, license "Other" (went closed/commercial; flag unmaintained as open source) — [API](https://api.github.com/search/repositories?q=topic:quantitative-finance&sort=stars&per_page=30)
- huseinzol05/Stock-Prediction-Models — 9,520 stars, ARCHIVED, last push 2023-04-16 — [API](https://api.github.com/search/repositories?q=repo:huseinzol05/Stock-Prediction-Models+repo:hudson-and-thames/mlfinlab)
- firmai/financial-machine-learning 8,841 (pushed 2025-01-03) — algorithmic-trading topic API
- HKUDS/Vibe-Trading — 38,611 stars, MIT, pushed 2026-11-20; AI agent turning finance questions into reports/backtests/paper portfolios; MCP server over stdio (`vibe-trading-mcp`); market-specific engines (A-share limits, crypto funding, futures margin, options multi-leg/Greeks); Alpha Zoo of 478 alphas (Qlib, Alpha101, GTJA); 30 preset agent teams; optional live broker trading — [GitHub](https://github.com/HKUDS/Vibe-Trading)
- OpenByteInc/QuantDinger 13,889; ZhuLinsen/daily_stock_analysis 73,562; Fincept Terminal 34,011; OpenBB 75,605 (data platform) — [API quant-finance topic](https://api.github.com/search/repositories?q=topic:quantitative-finance&sort=stars&per_page=30). Not vetted for quality.

Strategy collections / lists
- wilsonfreitas/awesome-quant — 30,752 stars, pushed 2026-11-20; categories: indicators, pricing, trading and backtesting, portfolio/risk, factor analysis, sentiment/alt data, time series, market data, prediction markets, historical/archived — [GitHub](https://github.com/wilsonfreitas/awesome-quant)
- paperswithbacktest/awesome-systematic-trading — 15,466 stars, pushed 2026-09-28; wangzhe3224/awesome-systematic-trading 5,409 — API links above
- je-suis-tm/quant-trading — 11,323 stars, pushed 2026-06-20 (strategy collection) — API links above
- Pairs-trading repos on GitHub are small: top search hit has only 201 stars (tibkiss/huba-v1, last push 2022); most are stale hobby notebooks — [API](https://api.github.com/search/repositories?q=pairs+trading+statistical+arbitrage&sort=stars&per_page=10)
- Funding-rate arbitrage/market-making keyword search returned only tiny repos (top 392 stars) — [API](https://api.github.com/search/repositories?q=funding+rate+arbitrage+market+making&sort=stars&per_page=12)

### Inferences
- Star counts for AI-agent repos (Vibe-Trading, daily_stock_analysis, QuantDinger) are very high relative to age; hype/promotion may inflate them, so treat as unvetted.
- Classic statistical-arbitrage/pairs code lives mostly in notebooks and book repos (je-suis-tm, ML4T) and inside engines, not in standalone popular repos.

### Gaps
- No verified data for zipline-reloaded, LEAN features, Riskfolio-Lib/skfolio details, Jesse features (rate limited/time).
- Ecosystem coverage beyond top ~17 per topic not retrieved; options/volatility repos not surveyed.

## What quantitative strategies are implemented/documented most?

### Takeaway
Documented families visible in sources: moving-average/trend crossover (default tutorial), ML factor/alpha models (Qlib, Alpha Zoo), portfolio optimization/risk parity, market making and HFT (hftbacktest, hummingbot, Nautilus), pairs/stat-arb (small repos), options multi-leg, and crypto funding strategies. Evidence is thin; this is from READMEs, not a systematic count.

### Cited Findings
- Moving-average crossover is the worked example in Vibe-Trading — [GitHub](https://github.com/HKUDS/Vibe-Trading)
- Factor/alpha: Qlib Alpha158/Alpha360 and model zoo; Vibe-Trading Alpha Zoo 478 alphas across five libraries including Alpha101 — [Qlib](https://github.com/microsoft/qlib), [Vibe-Trading](https://github.com/HKUDS/Vibe-Trading)
- Market making / HFT: hftbacktest targets MM with L2/L3 order book, queue and latency — [GitHub](https://github.com/nkaz001/hftbacktest); Nautilus supports market-making across venues — [GitHub](https://github.com/nautechsystems/nautilus_trader)
- Options multi-leg payoff/Greeks and crypto funding modelled in Vibe-Trading engines — [GitHub](https://github.com/HKUDS/Vibe-Trading)
- RL execution (TWAP, PPO, OPDS) in Qlib; deep RL portfolio in FinRL — [Qlib](https://github.com/microsoft/qlib)
- Portfolio optimization: PyPortfolioOpt, Riskfolio-Lib, skfolio, cvxportfolio (repos listed above)
- Pairs trading/stat-arb: small repos (201 stars max) — [API](https://api.github.com/search/repositories?q=pairs+trading+statistical+arbitrage&sort=stars&per_page=10)

### Inferences
- Representative repos per family: trend/momentum -> freqtrade/Jesse sample strategies, je-suis-tm/quant-trading (not verified in detail); ML alpha -> Qlib; MM -> hftbacktest/hummingbot; portfolio -> skfolio/Riskfolio.

### Gaps
- Could not confirm contents of je-suis-tm/quant-trading, freqtrade strategy repos, or mean-reversion/factor-investing libraries; no ranking by frequency.

## Which engines are best suited for being driven by an LLM/Claude?

### Takeaway
Best fits: QuantConnect (official hosted MCP server covering project creation, file edits, backtests, optimization, paper deployment; needs paid node), Vibe-Trading (built-in MCP stdio server), and Python-first engines with compact APIs (vectorbt, backtesting.py, bt) for fast iteration. NautilusTrader and hftbacktest are fast with live support but have a steeper API.

### Cited Findings
- QuantConnect Remote MCP server at https://www.quantconnect.com/api/v2/mcp: hosted, needs paid agent node (A1-1 or larger; free A-MICRO can't connect); tools to read projects, create/edit files, run backtests, optimize, deploy to paper; works with Claude Desktop, claude.ai, Claude Code — [QuantConnect/mcp-server](https://github.com/QuantConnect/mcp-server) (80 stars, pushed 2026-10-26)
- Community quantconnect-mcp (taylorwilsdon) 125 stars, MIT, pushed 2026-11-11 — [API](https://api.github.com/search/repositories?q=repo:taylorwilsdon/quantconnect-mcp+repo:QuantConnect/mcp-server)
- Other MCP servers surfaced by search (unverified, maintenance not checked): zw008/quant-trader (39 tools, IBKR execution), whchien/ai-trader (Backtrader-based), manifoldbt-mcp (Rust engine), QuantContext, MT5-Quant (87 tools), pineforge-backtest-mcp — [search result list](https://github.com/taylorwilsdon/quantconnect-mcp), [PyPI manifoldbt-mcp](https://pypi.org/project/manifoldbt-mcp/)
- Vibe-Trading MCP stdio server `vibe-trading-mcp`, Claude Desktop config supported — [GitHub](https://github.com/HKUDS/Vibe-Trading)
- A DEV post describes Claude Code driving a backtester via Vibe-Trading MCP — [DEV](https://dev.to/creeta/claude-code-can-drive-a-quant-backtester-via-vibe-trading-mcp-3701) (title only seen)
- Nautilus: same strategy code backtest/live, Rust core, Python control plane — [GitHub](https://github.com/nautechsystems/nautilus_trader)
- vectorbt fast vectorized sweeps; blogs recommend vectorbt for ideation, backtrader for execution validation, QuantConnect for live — [DEV comparison](https://dev.to/pickuma/quantconnect-vs-backtrader-vs-vectorbt-which-to-start-with-in-2026-4954) (blog, unverified speed claims)
- freqtrade has CLI-driven backtesting/hyperopt and lookahead-analysis command, scriptable by an agent — [docs](https://www.freqtrade.io/en/stable/lookahead-analysis/)
- Qlib `qrun` YAML-driven workflow plus RD-Agent LLM integration — [GitHub](https://github.com/microsoft/qlib)

### Inferences
- LLM-friendliness correlates with: declarative config (qrun, freqtrade CLI), small Python API (backtesting.py, vectorbt), and hosted MCP. Event-driven C#/Rust engines need more boilerplate but give live parity.
- Avoid backtrader/zipline (stale) as new LLM targets.

### Gaps
- No benchmarks verified; speed claims in blogs are single tests. No hands-on test of MCP servers' quality or security.

## What pitfalls (overfitting, survivorship bias, transaction costs) are addressed?

### Takeaway
Handling is uneven. Freqtrade ships lookahead-bias detection; vectorbt offers walk-forward/cross-validation and fees; hftbacktest models queue/latency; Qlib reports returns with and without costs. Survivorship bias handling was not found in any fetched source.

### Cited Findings
- Freqtrade lookahead-analysis reruns backtests per entry/exit and compares dataframes to flag biased indicators; may miss never-triggered signals and can false-flag — [docs](https://www.freqtrade.io/en/stable/lookahead-analysis/)
- vectorbt: walk-forward optimization; cross-validation tutorial in PRO; fees parameter; slippage not covered on README; README disclaimer "educational purposes only"; does not mention overfitting — [GitHub](https://github.com/polakowo/vectorbt)
- Qlib sample output: annualized excess return ~0.178 without costs vs ~0.129 with costs; Yahoo data may be imperfect — [GitHub](https://github.com/microsoft/qlib)
- hftbacktest: queue-position fills and feed/order latency to avoid optimistic fills — [GitHub](https://github.com/nkaz001/hftbacktest)
- Nautilus warns live execution can differ from simulation (venue, transport, timing, reconciliation) — [GitHub](https://github.com/nautechsystems/nautilus_trader)
- mlfinlab (López de Prado methods e.g. purged CV) is no longer open maintained (last push 2023, "Other" license) — [API](https://api.github.com/search/repositories?q=topic:quantitative-finance&sort=stars&per_page=30)

### Inferences
- Open-source López de Prado tooling (purged K-fold, deflated Sharpe) has lost its main project; skfolio (has model-selection/CV tools, not verified here) and Riskfolio are the active alternatives.
- Survivorship bias is mostly a data problem (point-in-time universes), which open-source engines largely leave to the user; LEAN's hosted data is the notable exception (not verified).

### Gaps
- No source found on survivorship-bias support, backtesting.py slippage/commission docs (503), Jesse/LEAN overfitting guards, or purged CV in current maintained libraries.
