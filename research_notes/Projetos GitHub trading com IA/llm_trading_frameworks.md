# Open-source LLM/AI trading frameworks and agent systems (state as of 2026-11-20)

Method note: star counts and last-push dates below were pulled from the GitHub REST API (api.github.com/repos/...) on 2026-11-20. "Last push" = pushed_at field (may include branch pushes, not only default-branch commits). The API rate-limited me partway through, so several repos have no numbers (listed under Gaps).

## 1. What are the top 25+ repos and what distinguishes them?

### Takeaway
The field splits into (a) LLM multi-agent "trading firm" simulators (TradingAgents, ai-hedge-fund, FinRobot, TradingAgents-CN, QuantAgent), (b) memory/RL research agents (FinMem, FinCon, FinRL-DeepSeek), (c) classic RL and quant platforms that LLMs are bolted onto (FinRL, Qlib, RD-Agent), (d) factor-mining agents (RD-Agent(Q), AlphaAgent, QuantaAlpha), (e) agent platforms/benchmarks (AI-Trader, AgenticTrading, StockBench, FINSABER, Alpha Arena). Stars track marketing/education appeal, not demonstrated trading edge.

### Cited Findings (repo catalog; stars / last push checked 2026-11-20 via GitHub API)
Multi-agent LLM "firm" frameworks
- TradingAgents (TauricResearch) — 123,277 stars, 23,636 forks, last push 2026-11-17, Apache-2.0. LangGraph; analyst team (fundamentals, sentiment, news, technical) -> bull/bear researcher debate -> trader -> risk team -> portfolio manager; "quick" and "deep" model tiers; memory log of past decisions. Supports Anthropic (Claude), Bedrock, OpenAI, Gemini, xAI, DeepSeek, Qwen, GLM, Kimi, Mistral, Ollama, OpenAI-compatible endpoints. v0.7.1 (2026-10); separate early-access Trading-R1 v0.1.0 (2026-11). README disclaims research-only use and says results vary with model, temperature, date range. — [API](https://api.github.com/repos/TauricResearch/TradingAgents), [README](https://github.com/TauricResearch/TradingAgents), paper [arXiv 2412.20138](https://arxiv.org/abs/2412.20138)
- ai-hedge-fund (virattt) — 64,776 stars, last push 2026-11-09, MIT. Educational multi-persona (investor-style agents) proof of concept; no verified performance evidence found. — [API](https://api.github.com/repos/virattt/ai-hedge-fund)
- dexter (virattt) — 27,961 stars, last push 2026-09-23, license not detected by API. (Financial research agent; I did not read its README.) — [API](https://api.github.com/repos/virattt/dexter)
- TradingAgents-CN (hsliuping) — 33,022 stars, last push 2026-11-14, license NOASSERTION. Chinese-market fork/adaptation of TradingAgents (name-based; README not read). — [API](https://api.github.com/repos/hsliuping/TradingAgents-CN)
- FinRobot (AI4Finance-Foundation) — 8,457 stars, last push 2026-10-24, Apache-2.0. Finance AI-agent platform (equity research, forecasting, reports). — [API](https://api.github.com/repos/AI4Finance-Foundation/FinRobot)
- QuantAgent (Y-Research-SBU, Stony Brook) — repo URL redirects (moved/renamed; README header now "QuantHarness"), so stats not captured. Four agents (Indicator, Pattern, Trend, Risk) on price/chart data only via LangChain/LangGraph; requires a vision-capable LLM; default config gpt-4o-mini/gpt-4o; paper claims zero-shot results on 9-10 instruments incl. BTC and Nasdaq futures over 4-hour intervals. — [arXiv 2509.09995](https://arxiv.org/abs/2509.09995), [project page](https://y-research-sbu.github.io/QuantAgent), [search summary](https://github.com/Y-Research-SBU/QuantAgent)
- AI-Trader (HKUDS) — 23,341 stars, last push 2026-06-11 (5 months stale), README shows MIT badge (API: no license detected). "Agent-native trading platform": agents register, publish signals, copy trades; supports Claude Code, Codex, Cursor, etc. Offers $100K simulated paper trading; page gives no performance data and "zero risk" framing. — [API](https://api.github.com/repos/HKUDS/AI-Trader), [README](https://github.com/HKUDS/AI-Trader)
- AgenticTrading (Open-Finance-Lab) — 902 stars, last push 2026-11-05, license NOASSERTION. — [API](https://api.github.com/repos/Open-Finance-Lab/AgenticTrading)

Memory / RL research agents
- FinMem (pipiku915) — 974 stars, last push 2024-08-18 (dormant 27+ months), MIT. Layered memory (working + long-term layers, ranked by recency/relevance/importance) and "character design". — [API](https://api.github.com/repos/pipiku915/FinMem-LLM-StockTrading), [arXiv 2311.13743](https://arxiv.org/pdf/2311.13743)
- FinCon — manager/analyst hierarchy with conceptual verbal reinforcement and a risk-control self-critique; I did not find its repo (guessed paths returned 404). — [arXiv 2407.06567](https://arxiv.org/html/2407.06567v2)
- FinRL-DeepSeek (benstaf) — CVaR-PPO extended with LLM-derived news risk/recommendation scores (DeepSeek V3, Qwen 2.5, Llama 3.3) on Nasdaq-100 with FNSPID news; reported as later integrated into AI4Finance FinRL. Repo stats not captured (rate limit). — [arXiv 2502.07393](https://arxiv.org/abs/2502.07393)

RL / quant platforms
- FinRL — 17,152 stars, last push 2026-11-18, MIT. Deep-RL trading library (not LLM-native). — [API](https://api.github.com/repos/AI4Finance-Foundation/FinRL)
- FinRL-Trading (formerly "FinRL-X" per task prompt; name mapping not verified) — 3,955 stars, last push 2026-09-18, Apache-2.0. — [API](https://api.github.com/repos/AI4Finance-Foundation/FinRL-Trading)
- FinRL-Meta — 1,966 stars, last push 2026-10-12, MIT. Market environments/data layer. — [API](https://api.github.com/repos/AI4Finance-Foundation/FinRL-Meta)
- FinGPT — 21,596 stars, last push 2026-11-18, MIT. Open financial LLMs (sentiment, forecaster; fine-tuning focus). — [API](https://api.github.com/repos/AI4Finance-Foundation/FinGPT)
- Qlib (Microsoft) — 50,453 stars, last push 2026-11-04, MIT. Quant research platform with ML models; base for RD-Agent(Q). — [API](https://api.github.com/repos/microsoft/qlib)
- RD-Agent (Microsoft; includes RD-Agent(Q) factor/model co-optimization) — 15,439 stars, last push 2026-10-21, MIT. — [API](https://api.github.com/repos/microsoft/RD-Agent)
- Kronos (shiyu-coder) — 48,030 stars, last push 2026-04-13, MIT. Foundation model for candlestick/K-line series (not an LLM agent; relevant as a forecasting component). — [API](https://api.github.com/repos/shiyu-coder/Kronos)
- Freqtrade — 57,109 stars, last push 2026-11-19, GPL-3.0. Mature crypto bot; includes FreqAI ML module; not LLM-native but the dominant execution/backtest base people wire LLMs into. — [API](https://api.github.com/repos/freqtrade/freqtrade)

Factor mining
- AlphaAgent (RndmVariableQ) — 441 stars, last push 2026-07-03, no license detected. LLM alpha-factor mining. — [API](https://api.github.com/repos/RndmVariableQ/AlphaAgent)
- QuantaAlpha — 1,679 stars, last push 2026-06-29, no license detected. (Factor-mining agent by name; README not read.) — [API](https://api.github.com/repos/QuantaAlpha/QuantaAlpha)

Benchmarks / evaluation / lists
- StockBench — code at github.com/ChenYXxxx/stockbench (stats not captured). 82 trading days (2025-03-03 to 2025-06-30), DJIA stocks, $100k start; models incl. GPT-5, Claude-4, Qwen3, Kimi-K2, GLM-4.5; most fail to beat buy-and-hold; no trading costs/slippage modeled. — [arXiv 2510.02209](https://arxiv.org/abs/2510.02209), [site](https://stockbench.github.io)
- FINSABER (waylonli) — 155 stars, last push 2026-09-17, Apache-2.0. Long-horizon (about 20 years, 100+ symbols) backtester for LLM timing strategies. — [API](https://api.github.com/repos/waylonli/FINSABER), [arXiv 2505.07078](https://arxiv.org/abs/2505.07078)
- Alpha Arena (nof1) — live-money LLM competition; no repo located (guessed path 404). Season 1 (Oct-Nov 2025, crypto perps, $10k each): Qwen3 Max first (+22.32% reported by one outlet), GPT-5 about -29% / weak, majority of models lost money. Season 1.5 (US stocks, four modes): Grok 4.20 won (about +12%), GPT-5.1 second, Gemini 3 third; Claude reported as hesitant/long-biased and a sole early loser (-0.9% at one point). Season 2 announced with web search/more steps; no results found. Source quality: crypto news outlets (secondary), figures differ between outlets. — [Forklog S1.5](https://forklog.com/en/ai-model-grok-4-2-triumphs-in-trading-tournament/), [Forklog](https://forklog.com/en/four-out-of-six-ai-models-suffer-losses-in-trading-tournament/), [Decrypt](https://decrypt.co/345006/ai-crypto-trading-showdown-deepseek-grok-winning-gemini-implodes), [Benzinga](https://benzinga.com/crypto/cryptocurrency/25/11/48651974/chatgpt-lost-63-trying-to-trade-crypto-but-one-china-ai-made-a-healthy-profit)
- LLMQuant/awesome-trading-agents — 1,023 stars, last push 2026-08-13, CC0-1.0 curated list. — [API](https://api.github.com/repos/LLMQuant/awesome-trading-agents)
- Surveys: [LLM Agent in Financial Trading survey](https://arxiv.org/html/2408.06361v2); [InvestorBench](https://arxiv.org/html/2412.18174v1).

### Inferences
- Star counts are extremely top-heavy: TradingAgents (123k) > ai-hedge-fund (65k) > Freqtrade (57k) > Qlib (50k) > Kronos (48k). The rigorous evaluation repos (FINSABER 155, StockBench unknown) are tiny by comparison; popularity is inversely related to evidence quality.
- Claude support is explicit in TradingAgents and AI-Trader; most academic repos default to OpenAI/DeepSeek/Qwen, but are model-agnostic via LangChain/LangGraph (inferred, not verified per repo).
- The older research repos (FinMem) are dormant; maintained ones are those backed by an organization (TauricResearch, AI4Finance, Microsoft, HKUDS).

### Gaps
- No GitHub numbers captured for QuantAgent (moved), StockBench, FinCon, FinRL-DeepSeek, nof1/Alpha Arena, FinBen/InvestorBench, FinSearchComp, FinGPT-Forecaster paths (rate limit / 404 on guessed paths). A dev.to and Pinggy listicle gave different ai-hedge-fund and TradingAgents counts (stale snapshots) and I disregarded them.
- Alpha-GPT repo, Alpha-GPT-like and LLM sentiment-trading repos (beyond FinGPT) not catalogued; FinSearchComp (a search benchmark, not trading) not located. I did not reach 25 fully-documented repos with licenses/last-commit for each; about 20 are documented above.
- Licenses for AlphaAgent, QuantaAlpha, dexter, AI-Trader per API are blank (no license = all rights reserved by default).

## 2. Which have credible backtest/live evidence vs marketing claims?

### Takeaway
No LLM-agent framework has convincing live, net-of-cost, out-of-sample evidence. Headline paper results come from short windows, few tickers, and no frictions; independent long-horizon or friction-adjusted re-tests show the edge shrinking to or below buy-and-hold. Live-money Alpha Arena shows large dispersion and mostly losses, consistent with noise.

### Cited Findings
- TradingAgents paper claims improvements in cumulative return, Sharpe and drawdown over baselines (abstract shows no numbers); README itself warns results are not guaranteed to match published figures. — [arXiv 2412.20138](https://arxiv.org/abs/2412.20138), [README](https://github.com/TauricResearch/TradingAgents)
- FINSABER summary table lists TradingAgents as evaluated over 3 months and 3 symbols; FINSABER finds LLM advantages "deteriorate significantly" over 20 years / 100+ symbols; strategies are too conservative in bull markets and too aggressive in bear markets; authors cite survivorship and data-snooping bias. — [arXiv 2505.07078](https://arxiv.org/abs/2505.07078), search summary of [FINSABER v1](https://arxiv.org/html/2505.07078v1)
- "The Alpha Illusion" (arXiv 2605.16895, May 2026, preprint): own one-year, five-ticker reproduction: TradingAgents Sharpe 0.43 -> 0.22 after frictions, ending $102.3K net vs buy-and-hold $104.8K; QuantAgent Sharpe -0.96 -> -1.15, ending $77.9K net. Cites Li et al.: FinMem total return drops about 71.85% and QuantAgent Sharpe about 51.48% once the window crosses the model's knowledge cutoff. Headline claims cited: FinCon portfolio Sharpe 3.27; QuantAgent 50.7-63.7% directional accuracy. Only commissions are modeled by all five audited systems (FinMem, TradingAgents, FinAgent, FinCon, QuantAgent); 35 of 40 system-by-friction cells unmodeled. — [alphaxiv](https://www.alphaxiv.org/abs/2605.16895.md)
- StockBench (82 days, DJIA, 2025): most LLM agents (incl. Claude-4, GPT-5) struggle to beat buy-and-hold; no costs modeled so it is, if anything, generous. — [arXiv 2510.02209](https://arxiv.org/abs/2510.02209)
- Reproducibility audit of 30 LLM trading studies (arXiv 2606.08285): architecture reporting is clearer than evaluation assumptions (point-in-time controls, splits, costs). Only search snippet read. — [arXiv 2606.08285](https://arxiv.org/pdf/2606.08285.pdf)
- AI-Trader (HKUDS): 23k stars but README publishes no returns; "live" platform with simulated $100K paper trading. — [README](https://github.com/HKUDS/AI-Trader)
- Alpha Arena Season 1: majority of the six models lost money in the two-week live-money run; Season 1.5 winner Grok 4.20 about +12%; nof1 founder cautioned handing money to an LLM is not yet feasible. Short windows, single runs, so not statistically conclusive. — [Forklog](https://forklog.com/en/four-out-of-six-ai-models-suffer-losses-in-trading-tournament/), [search summary above](https://forklog.com/en/ai-model-grok-4-2-triumphs-in-trading-tournament/)
- FinRL-DeepSeek: backtest on Nasdaq-100 with FNSPID news; a May 2026 Cambridge Engage preprint reports max drawdown moving only from -58.37% to -56.09% with risk-first constraints (snippet only, unverified). — [arXiv 2502.07393](https://arxiv.org/abs/2502.07393), [Cambridge Engage](https://www.cambridge.org/engage/coe/article-details/6a071d88d1922e37d57d1470)
- Lopez-Lira & Tang: ChatGPT headline scores positively predict next-day returns (stronger in small caps and bad news); in v6, using post-cutoff headlines, returns decline as LLM adoption rises, consistent with efficiency gains. — [arXiv 2304.07619](https://arxiv.org/abs/2304.07619)

### Inferences
- The most credible "evidence" is negative evidence (FINSABER, StockBench, Alpha Illusion). The most credible positive evidence is narrow: LLM-as-sentiment/news-feature extractor (Lopez-Lira & Tang), with alpha decaying as adoption grows.
- Alpha Illusion and Li et al. (FINSABER authors) are themselves preprints with a skeptical thesis; treat as strong but not definitive.

### Gaps
- No independent live track record (audited, multi-month, real money, net of costs) found for any open-source framework.
- Did not verify FinCon/FinMem original headline numbers from primary papers; they are quoted second-hand via Alpha Illusion.
- Alpha Arena official leaderboard (nof1.ai) not fetched; no Season 2 outcome found.

## 3. What are the dominant architectures?

### Takeaway
Five patterns: multi-agent role-play with bull/bear debate (TradingAgents, FinCon, ai-hedge-fund personas), single-agent with memory/reflection (FinMem), price/technical-only multimodal agents (QuantAgent), LLM-signal-into-RL (FinRL-DeepSeek, FLAG-Trader), and LLM-driven factor/model R&D loops on classical quant stacks (RD-Agent(Q) on Qlib, AlphaAgent). Emerging: agent marketplaces and live arenas.

### Cited Findings
- Debate/role-play: TradingAgents analysts -> bull/bear debate -> trader -> risk -> PM on LangGraph. — [README](https://github.com/TauricResearch/TradingAgents)
- Hierarchical + verbal reinforcement: FinCon manager-analyst with risk-control self-critique. — [arXiv 2407.06567](https://arxiv.org/html/2407.06567v2)
- Layered memory: FinMem. — [arXiv 2311.13743](https://arxiv.org/pdf/2311.13743)
- Price-only multi-agent: QuantAgent (Indicator/Pattern/Trend/Risk, chart images). — [arXiv 2509.09995](https://arxiv.org/abs/2509.09995)
- RL + LLM news signals: FinRL-DeepSeek (CVaR-PPO). — [arXiv 2502.07393](https://arxiv.org/abs/2502.07393)
- Does debate help? Alpha Illusion cites Zhang et al.: multi-agent debate won in under 20% of 36 configurations versus single-agent baselines (second-hand). Proposes LLMs as auditable information extractors upstream of independent calibration, risk, execution modules. — [alphaxiv](https://www.alphaxiv.org/abs/2605.16895.md)
- Survey of the field: [arXiv 2408.06361](https://arxiv.org/html/2408.06361v2), [agentic trading survey 2605.19337](https://arxiv.org/pdf/2605.19337).

### Inferences
- RAG over news is a component of nearly all of these rather than a separate architecture; factor-mining and RL variants keep the LLM away from direct order decisions, which is structurally more defensible against LLM-specific biases (inference, consistent with Alpha Illusion's recommendation).

### Gaps
- Factor-mining internals (RD-Agent(Q), AlphaAgent, Alpha-GPT) and their evidence were not read in detail; no independent evaluation of them found in this pass.

## 4. Academic papers and independent evaluations (look-ahead bias, leakage, overfitting)

### Takeaway
Independent work converges: LLM backtests are contaminated by parametric memory (look-ahead), survivorship, short windows and ignored costs; once corrected, LLM trading agents typically fail to beat buy-and-hold.

### Cited Findings
- "Evaluating LLMs in Finance Requires Explicit Bias Consideration" (arXiv 2602.14233): reviewed 164 papers (2023-2025); five biases (look-ahead, survivorship, narrative, objective, cost); a search snippet says look-ahead appeared in 44 (26.8%), the paper page says no single bias exceeded 28%; biases compound into "an illusion of validity". — [arXiv 2602.14233](https://arxiv.org/abs/2602.14233)
- Look-Ahead-Bench (arXiv 2601.13770): standard LLMs (Llama 3.1 8B/70B, DeepSeek 3.2) show significant look-ahead bias measured via alpha decay across regimes vs point-in-time models; no exact numbers retrieved. — [arXiv 2601.13770](https://arxiv.org/abs/2601.13770)
- "Summoning the Oracle to Slay It" (arXiv 2605.24564): parametric look-ahead bias; FinCAD decoding cuts in-sample backtest returns by up to 67.1% on memorized dates while 2025 out-of-sample stays near baseline (snippet only). — [arXiv 2605.24564](https://arxiv.org/abs/2605.24564)
- TradingAgents GitHub issue #805 raises base-model leakage and proposes matching backtest periods to model cutoffs (a question, not a result). — [issue 805](https://github.com/TauricResearch/TradingAgents/issues/805)
- FINSABER (see Q2), StockBench (see Q2), Alpha Illusion (see Q2).
- Prior-lock-in finding cited second-hand: at 60% counter-evidence, Llama4-Scout reverses its view about 8% vs about 30% for GPT-4.1. — [alphaxiv](https://www.alphaxiv.org/abs/2605.16895.md)

### Inferences
- Any LLM-agent backtest on dates before the model's training cutoff (e.g., 2023-2025 mega-caps with Claude/GPT of 2025-26) should be treated as potentially contaminated; only post-cutoff forward/live tests are informative. Alpha Arena style live runs and StockBench's post-cutoff windows are methodologically stronger but short.

### Gaps
- Zhang and Stadie (2026) temporal-leakage paper cited in the agentic trading survey was not opened.
- Did not search Reddit r/algotrading or practitioner critiques; no community-sentiment evidence collected. Listicles (Pinggy, dev.to) found were low-quality and not used for facts.
- Several arXiv figures above are from search snippets or a secondary summary (alphaxiv); verify against full text before quoting.
