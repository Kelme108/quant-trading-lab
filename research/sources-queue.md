# Source queue for the scout (open-source trading and AI-trading projects)

Built 2026-11-10 from a GitHub survey of about 200 repositories (topics: trading-bot, algorithmic-trading, freqtrade-strategies, ai-trading, quantitative-trading, day-trading, reinforcement-learning, llm trading). Only projects with strategy rules or methods the lab can reuse are listed; execution libraries, data tools and chat-only LLM agents were left out.

How to use it: take the sources top to bottom, skip any whose URL already appears among the collected ideas, read the README or the strategy description, and restate the RULE in your own words. Never copy code, never report the project's advertised results, and record the licence in `source.license`. A project may yield several ideas, but each must pass the lab's limits (spot, long only, 15m/1h, intraday exit, average gross move of at least 0.45% per trade, an activity filter). Strategies written for stocks, FX or futures are welcome if the mechanism carries to crypto.

## A. Strategy rule sources (mine these first)

| Source | What to read | Why it matters |
|---|---|---|
| https://github.com/freqtrade/freqtrade-strategies (GPL-3.0; rules only) | `user_data/strategies/`: Bandtastic, Diamond, HourBasedStrategy, PowerTower, Supertrend, SwingHighToSky, TrendRiderStrategy, UniversalMACD, MultiMa, PatternRecognition, hlhb, multi_tf, Heracles | Rules that already run in Freqtrade bots, the lab's own engine. Read the docstring and the indicator conditions. |
| https://github.com/je-suis-tm/quant-trading (Apache-2.0) | README plus: London Breakout, Dual Thrust, Heikin-Ashi, Parabolic SAR, Awesome Oscillator, Bollinger Bands Pattern Recognition, RSI Pattern Recognition, Shooting Star, MACD Oscillator | Intraday breakout and pattern rules with explicit entry and exit text. London Breakout and Dual Thrust are session or range breakouts. |
| https://github.com/MobiusQuant/OpenMobius-skill (Apache-2.0) | `knowledge_base/`, `docs/`, `workflows/` | ICT and smart-money concepts (liquidity sweeps, fair value gaps, order blocks, killzones) written as rules for AI agents. Extract only rules that can be stated with candles. |
| https://github.com/Jakeschincariol/day-trader-skill (MIT) | already mined (opening-range bracket, day limits); skip unless a new rule appears | Reference for the bracket and the day limits. |
| https://github.com/alpacahq/example-scalping | README and the algorithm description | A scalping rule with explicit entry and exit; stock market, check the mechanism for crypto. |
| https://github.com/hummingbot/hummingbot (Apache-2.0) | documentation of the directional strategy controllers (v2 controllers) | Directional controllers with signals and triple-barrier style exits (take profit, stop loss, time limit). Skip market making: the lab only trades at market. |
| https://github.com/jesse-ai/jesse (MIT) and https://jesse.trade strategy articles | strategy examples in the docs | Crypto-first bot framework; practical rule write-ups. |
| https://github.com/QuantConnect/Lean (Apache-2.0) | `Algorithm.Python` examples, alpha models | Compact intraday and momentum examples. |
| https://github.com/paperswithbacktest/awesome-systematic-trading and https://github.com/wangzhe3224/awesome-systematic-trading | the strategy and paper lists | A map to papers and rules by theme; open the original papers and restate the rule. |
| https://github.com/whittlem/pycryptobot, https://github.com/chrisleekr/binance-trading-bot, https://github.com/CryptoSignal/Crypto-Signal, https://github.com/Haehnchen/crypto-trading-bot | strategy and indicator descriptions in the READMEs and wikis | Common retail-bot rules (breakout, pivot reversal, volume spike, DCA dips). Treat as hypotheses: popularity is not evidence. |

## B. AI and machine-learning projects (rules and methods, not products)

| Source | What to extract | Why it matters |
|---|---|---|
| https://github.com/asavinov/intelligent-trading-bot (MIT) | `docs/`, `configs/`: the feature set (rolling windows, volume, volatility) and the signal-generation scheme | A working ML signal pipeline for crypto. Extract the FEATURES and the label design as a rule filter; the lab does not train models yet. |
| https://github.com/stefan-jansen/machine-learning-for-trading (MIT) | chapters on features, triple-barrier labels, meta-labeling and intraday strategies | Source of the meta-labeling idea (an ML filter over a rule's own signals) planned as a later pilot. |
| https://github.com/hudson-and-thames/mlfinlab | triple barrier, meta-labeling descriptions only (licence is restrictive: read the public docs, restate in words) | Same method, for the pilot. |
| https://github.com/AI4Finance-Foundation/FinRL (MIT), https://github.com/TradeMaster-NTU/TradeMaster, https://github.com/ClementPerroud/Gym-Trading-Env | state, action and reward design for reinforcement learning on crypto | Reference for a future RL study; not a rule source today. |
| https://github.com/TauricResearch/TradingAgents (Apache-2.0), https://github.com/HKUDS/Vibe-Trading, https://github.com/51bitquant/ai-hedge-fund-crypto, https://github.com/wquguru/nof0 | how LLM agents decide (inputs, roles, risk checks) | Architecture ideas for an AI layer over the lab (for example a news or regime filter). They do not publish testable rules; do not write ideas from them unless a rule is stated. |
| https://github.com/microsoft/qlib (MIT) | the alpha factor lists (Alpha158) | Large lists of price and volume factors that can inspire intraday filters. |

## C. Not worth mining now
Pure execution or data libraries (ccxt-style wrappers, MCP servers for brokers), prediction-market bots, A-share (China) analysis tools, and market-making engines (hftbacktest, tribeca, Krypto-trading-bot): the lab trades spot at market only.
