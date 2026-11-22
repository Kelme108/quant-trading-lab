# Strategy and idea sources for intraday futures (WIN/WDO lens), as of Nov 2026

Scope: catalogs, databases, aggregators, academic literature and competition write-ups that supply trading-strategy ideas. Frameworks (Freqtrade, Lean, Nautilus, vectorbt, Qlib, FinRL and others) are excluded because an earlier note set already covers them. Research done 2026-11-21. Items marked "not verified this session" are prior knowledge and need a check before anyone cites them.

## 1. Strategy encyclopedias and databases: what each offers, cost, evidence quality, intraday futures fit

### Takeaway
Most large catalogs (Quantpedia, OSAP, 101 Alphas, 151 Strategies) lean toward cross-sectional equities at daily-to-monthly horizons. They are good for mechanisms and taxonomy and weak as a direct source of 1m/5m futures rules. The few sources with intraday futures content are specific academic papers: intraday momentum across 60+ futures and the SPY intraday momentum/ORB papers. They are better seeds than any catalog.

### Cited Findings

**Quantpedia (paid, academic-paper-backed database)**
- Tiers: PRIME gives about 100 premium strategies and no out-of-sample screening or API. PREMIUM gives all 900+ strategies and thousands of papers. PRO gives all 900+, about 40 reports, API on request, "out-of-sample screening", benchmarking and an AI chatbot. There is no free tier for the database, only a newsletter. The pricing page did not show USD prices in the fetched text. — [Quantpedia pricing](https://quantpedia.com/pricing/)
- About 800 strategies include backtests with equity curves and Python code. The page contradicts itself on update cadence ("5+ new backtests bi-weekly" vs "about 400 strategies updated monthly"). It carries a hypothetical-performance disclaimer and describes no explicit post-publication method on the pricing page. — [Quantpedia pricing](https://quantpedia.com/pricing/)
- Quantpedia's free blog posts are syndicated on Quantocracy (for example "Peak of Everything", Nov 2026). — [Quantocracy](https://quantocracy.com/)

**Open Source Asset Pricing (Chen & Zimmermann), free**
- Data and code reproduce nearly all published cross-sectional stock return predictors. Of 161 predictors that were clearly significant in the original papers, 98% reproduce with t > 1.96. A regression of reproduced on original t-stats gives slope 0.90 and R² 83%. Published in Critical Finance Review (2022). — [SSRN 3604626](https://papers.ssrn.com/abstract=3604626)
- A companion paper, "Publication Bias in Asset Pricing Research", estimates that shrinkage corrects only 10–15% of in-sample mean returns and puts the false discovery rate under 6%. Returns are 30–50% weaker in alternative portfolio tests. Code is on GitHub (chenandrewy/PBR). — [arXiv 2209.13623](https://arxiv.org/abs/2209.13623v3)
- Commentary notes this work reproduces original results and does not test them on new data. — [Alpha Architect on the replication debate](https://alphaarchitect.com/more-on-the-factor-investing-replication-debate/)

**WorldQuant "101 Formulaic Alphas" (Kakushadze 2016), free**
- 101 real-life alphas given as explicit formulas that are also code. Average holding period is about 0.6–6.4 days and average pairwise correlation about 15.9%. Published in Wilmott (2016). The abstract does not report out-of-sample results. — [arXiv 1601.00991](https://arxiv.org/abs/1601.00991)

**"151 Trading Strategies" (Kakushadze & Serur 2018)**
- More than 150 strategies across stocks, options, fixed income, ETFs, indexes, commodities, futures, FX, volatility and crypto. The full text is free on SSRN, with a Spanish edition (SSRN 3402665). — [SSRN 3247865](https://papers.ssrn.com/abstract=3247865)
- Springer/Palgrave lists the book as "RETRACTED BOOK". The chapter notices, including the Futures chapter, give the reason as "copyright issues regarding the images", not a scientific error. — [Palgrave page](https://www.palgrave.com/978-3-030-02791-9); [Futures chapter notice](https://rd.springer.com/content/pdf/10.1007/978-3-030-02792-6_10.pdf)

**QuantConnect Strategy Library / Alpha Streams**
- QuantConnect retired Alpha Streams v1.0 (its crowd-sourced alpha marketplace) to build a 2.0 version and disabled sales in the meantime. Live trading was not affected. — [QC forum: Alpha Streams refactoring 2.0](https://www.quantconnect.com/forum/discussion/13441/alpha-streams-refactoring-2-0/)
- The separate Strategy Library still exists. A community spreadsheet tabulates its implementations by type (mean reversion, ML, DL and so on). — [QC forum: strategy library tabulated](https://www.quantconnect.com/forum/discussion/9642/strategy-library-implementations-tabulated-for-various-attributes-including-algo-framework-mean-reversion-ml-dl-etc/)
- The QC forum hosts replications of intraday papers, for example the 5-minute ORB on "stocks in play", reported at Sharpe 2.4. — [QC forum ORB](https://www.quantconnect.com/forum/discussion/18444/opening-range-breakout-for-stocks-in-play/)

**Robot Wealth (paid education plus community)**
- Offers a "Trade Like a Quant" Bootcamp (6 modules, 4 strategies) and an RW Pro membership (strategies, research, tools, community). The home page lists no prices. — [Robot Wealth](https://robotwealth.com/)
- Explicitly against overfitting. It warns against "the backtest trap" and says to start from the economic mechanism ("who is on the other side and why do they pay you"). Blog topics include stat-arb and energy spreads. — [Robot Wealth](https://robotwealth.com/)

**Quantocracy (free aggregator)**
- "A curated mashup of quantitative trading links" from about 100 blogs. Free via RSS, daily email and social media. Still active, with entries dated 19 Nov 2026 (for example a backtest of a 5-minute opening range breakout by Nullius Research, and Investment Idiocy on AI for systematic traders). Selection criteria are not published, and some sponsor links carry tracking parameters. — [Quantocracy](https://quantocracy.com/)

**Quantified Strategies (free articles plus paid strategy packs)**
- Sells packs such as "10 Futures Strategies" for $1,490. Content is mostly short backtest articles. No independent audit of its backtests was found. — [Quantified Strategies site](https://www.quantifiedstrategies.com/big-reversal-moves-strategy/); [Substack](https://quantifiedstrategies.substack.com/p/best-mean-reversion-strategies-backtested)

**Intraday-futures-specific academic sources (the best fit)**
- Baltussen, Da, Lammers & Martens (JFE 2021): over 60 futures (equity, bond, commodity, FX), 1974–2020. The return over the rest of the day predicts the last-30-minute return in all of them, and this partly reverts over the next days. The proposed mechanism is short-gamma hedging (options market makers, leveraged ETFs). — [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:142:y:2021:i:1:p:377-403); [working paper PDF](https://www3.nd.edu/~zda/intramom.pdf)
- Zarattini, Aziz & Barbon, "Beat the Market: An Effective Intraday Momentum Strategy for SPY" (SFI 24-97). It uses noise boundaries around the open (open × (1 ± average absolute move over the prior 14 days)) plus VWAP. For 2007–early 2024 it reports 19.6% a year net of costs and Sharpe 1.33. These are in-sample results per CXO Advisory. — [SFI](https://www.sfi.ch/de/publications/n-24-97-beat-the-market-an-effective-intraday-momentum-strategy-for-s-p500-etf-spy); [CXO summary](https://www.cxoadvisory.com/?p=45565)
- Zarattini et al., "A Profitable Day Trading Strategy for the U.S. Equity Market" (SFI 24-98, SSRN 4729284): a 5-minute ORB on more than 7,000 stocks. The 5-minute window was the best of the windows tested. — [IDEAS rp2498](https://ideas.repec.org/p/chf/rpseri/rp2498.html)
- Brazil: no peer-reviewed intraday-momentum paper on Ibovespa futures was found. One Brazilian university study on WINFUT day trading concludes that intraday technical rules need rigorous calibration and are sensitive to their parameters. — [Unipampa repository](https://repositorio.unipampa.edu.br/bitstreams/82706f83-804f-40c4-8d01-0d8bb372d1fa/download)

### Inferences
- Fit ranking for 1m/5m WIN/WDO, best first:
  1. Specific intraday futures papers (Baltussen et al.; Zarattini ORB and noise-band). They give a mechanism, are close to the lab's timeframe and are free.
  2. Quantocracy as a free discovery feed.
  3. Robot Wealth for method, plus Quantpedia PRO for search and filtering.
  4. 101 Alphas as a source of feature formulas: daily cross-sectional equity, so the formulas have to be adapted to a single instrument.
  5. 151 Strategies and OSAP as taxonomy only: cross-sectional, monthly horizon.
- WIN is the B3 Ibovespa index future, so intraday momentum and the last-30-minute effect are the most transferable published idea. B3 has a liquid options market on the index and on the dollar, which in principle supports the gamma-hedging mechanism. This has not been tested for WIN/WDO.
- The 151-Strategies retraction is about image copyright. The content is still usable as a catalog, but cite the SSRN version.

### Gaps
- Quantpedia USD prices could not be read from the pricing page. Nor could the number of intraday or futures-specific strategies in Quantpedia, or its out-of-sample screening method.
- Not fetched this session: Alpha Architect (free blog; paid ETF manager, so treat it as an informed but interested party), r/algotrading wiki, the awesome-quant lists, SSRN "top papers" lists. No claims made about them.
- Robot Wealth prices not verified. Whether QuantConnect's Alpha Streams 2.0 ever launched or was shut down for good is not confirmed.

## 2. Post-publication decay and how much to trust published edges

### Takeaway
Published anomalies lose about a quarter of their returns out of sample and about half after publication (McLean & Pontiff). For the lab, any literature rule should be expected to show far less edge than its paper claims, before costs, and must still pass the lab's own locked out-of-sample test.

### Cited Findings
- McLean & Pontiff (JF 2016), 97 predictors: portfolio returns are 26% lower out of sample and 58% lower after publication. The 26% is an upper bound on data mining, and the 32-point gap is attributed to investors trading on the publication. — [Gwern mirror of the paper](https://Www.Gwern.net/doc/economics/2016-mclean.pdf); [Counterpoint PDF](https://counterpointfunds.com/wp-content/uploads/2017/07/PredictabilityMcleanPontiff.pdf)
- Jacobs & Müller: in the U.S., anomaly returns fall 62% after publication equal-weighted and 66% value-weighted. The U.S. is the only country with a reliable post-publication decline in long/short returns. — [Jacobs & Müller](https://www.wiwi.hu-berlin.de/en/Professorships/bwl/finance/seminars/papers-fin-acc-res-seminars/17s/jacobs.pdf)
- Chen & Zimmermann argue that publication bias is small (shrinkage of 10–15%, false discovery rate under 6%). Their evidence is in-sample and they do not measure post-publication decay. — [arXiv 2209.13623](https://arxiv.org/abs/2209.13623v3)
- A search snippet claims "a median validation score of 3.7/100 across 890 backtests of published trading rules". The primary source was not identified, so this is unverified. — [Resonanz Capital article (context)](https://resonanzcapital.com/insights/sow-me-your-back-test-and-i-show-you-your-risk?hsLang=en)

### Inferences
- The decay literature covers cross-sectional stocks, so the figures cannot be carried over to intraday futures as they are. The direction (published edge shrinks) is the safe assumption. Arbitrage capital is probably smaller in B3 mini futures than in U.S. large caps, which would slow decay, but WIN is dominated by retail and HFT, so execution costs and slippage are the binding constraint.
- Not fetched this session: Harvey, Liu & Zhu (RFS 2016) argue for a t-stat hurdle near 3.0 for new factors. Bailey & López de Prado's Deflated Sharpe Ratio is the standard adjustment for many trials. Both support the lab's penalty for multiple tests.

### Gaps
- No decay study specific to intraday futures was found. No independent out-of-sample replication of the Zarattini SPY results was found beyond forum recreations.

## 3. Market microstructure and order flow (relevant to futures with aggressor data)

### Takeaway
Order-flow imbalance at the best bid and ask is the best-documented short-horizon price driver (Cont, Kukanov & Stoikov). VPIN is contested and should not be used as a standalone signal. For WIN/WDO this points to features built from the traded aggressor side and order-book imbalance, not volume-profile or footprint lore, which has no peer-reviewed backing that I found.

### Cited Findings
- Cont, Kukanov & Stoikov, "The Price Impact of Order Book Events" (J. Financial Econometrics 2014, 12(1):47–88). Using TAQ data on 50 U.S. stocks, they find short-interval price changes are mainly driven by OFI (the supply/demand imbalance at the best quotes). The relation is linear, and the slope is inversely proportional to market depth. It holds across time scales and stocks. The volume-based relation is noisier, and the square-root law follows from the OFI relation. — [arXiv 1011.6402](https://arxiv.org/abs/1011.6402)
- VPIN (Easley, López de Prado & O'Hara): Andersen & Bondarenko (Review of Finance 2015) find VPIN a poor predictor of short-run volatility. Its predictive content comes mechanically from trading intensity and from bulk-volume-classification errors. — [Kellogg Insight](https://insight.kellogg.northwestern.edu/article/the_trouble_with_vpin); [Kellogg research page](https://www.kellogg.northwestern.edu/faculty/research/detail/2015/assessing-measures-of-toxic-order-flow-and-early-warning)
- Easley et al. replied that the critics attacked "a methodology we do not advocate". In a later reflection, Andersen & Bondarenko say VPIN is "neither a unique nor reliable crash indicator". — [SSRN 2062450](https://papers.ssrn.com/abstract=2062450); [Kellogg reflection](https://www.kellogg.northwestern.edu/faculty/research/detail/2014/reflecting-on-the-vpin-dispute?p=1)

### Inferences
- With real aggressor flags in the MT5/B3 tick data, signed-volume imbalance is measured directly. That removes the classification-error problem behind the VPIN critique, which concerned bulk volume classification. OFI over 1–5 minute windows, normalized by depth or recent volume, is a well-founded feature family for the conveyor.
- OFI explains price changes over the same interval. Its forecasting power for the next bar is much weaker. Any OFI rule must be tested with a lag and under measured costs.

### Gaps
- No peer-reviewed evidence was found for footprint charts or volume-profile (POC/value area) trading rules. No OFI study on B3 futures was found. Not fetched: Cartea, Jaimungal & Penalva, Bouchaud et al. "Trades, Quotes and Prices", and Kolm, Turiel & Westray on deep-learning OFI forecasting. These are standard references to check.

## 4. What Kaggle market-prediction winners say works

### Takeaway
Across Optiver, Jane Street and G-Research, winners credit feature engineering, time-respecting validation and, recently, online or incremental retraining. The choice of model matters much less: gradient-boosted trees, often blended with small GRU/Transformer models. Several wins exploited dataset artifacts, which does not carry over to live trading.

### Cited Findings
- Optiver "Trading at the Close" (2023–24, closing auction of 200 NASDAQ stocks at 10-second steps), 1st place (hyd). Blend of CatBoost 0.5, GRU 0.3 and Transformer 0.2. Validation trained on the first 400 days and held out the last 81. Score improved from 5.4438 with no online learning to 5.4157 with one retrain and 5.4030 with five. — [Kaggle writeup](https://www.kaggle.com/competitions/optiver-trading-at-the-close/writeups/hyd-1st-place-solution); [Speaker Deck summary of top solutions](https://speakerdeck.com/richwomanbtc/optiver-trading-at-the-close-shang-wei-jie-fa-matome)
- A silver-medal team in the same competition skipped online learning and used rolling statistics with GroupKFold. — [Kaggle discussion 481600](https://www.kaggle.com/competitions/optiver-trading-at-the-close/discussion/481600)
- Jane Street Real-Time Market Data Forecasting (2024–25), a top writeup (Grigoreva). A GRU over one-day sequences, plus per-date/time market averages and rolling statistics over the last 1,000 time IDs. MLPs, transformers and cross-symbol attention did not help, and inference speed was a major constraint. One source calls this the winning approach, but the writeup is labeled 8th on the private leaderboard, so placement is unconfirmed. — [Kaggle writeup](https://www.kaggle.com/c/jane-street-real-time-market-data-forecasting/writeups/evgeniia-grigoreva-private-lb-8th-solution); [YouTube walkthrough](https://www.youtube.com/watch?v=lXYC0c7wJFU)
- Jane Street 2024–25, 162nd place: an online-learning TabM network (70%) blended with LightGBM (30%). It is fine-tuned daily on the last 3–4 days with a small learning rate and some old data mixed in to avoid forgetting. Predictions are clipped. — [Kaggle writeup](https://www.kaggle.com/competitions/jane-street-real-time-market-data-forecasting/writeups/max-abhi-private-lb-162nd-solution)
- G-Research Crypto Forecasting: won by team Meme Lord Capital ($50k). All of the top three used LightGBM. G-Research says "developing and testing different features had a far greater impact… than model development". — [G-Research wrap-up](https://www.gresearch.com/news/wrapping-up-the-g-research-crypto-forecasting-competition/)
- Optiver Realized Volatility Prediction (2021): a secondary source says the winner used the price tick size to reverse-engineer the order of the shuffled time_ids. That is a leak/artifact exploit. — [Chris Miles project page](https://chrisrichardmiles.github.io/chrisrichardmiles/projects/optiver/index_optiver.html)

### Inferences
- Lessons that carry over to the lab:
  1. Features matter more than models. Rolling and market-wide aggregates are the common winners.
  2. Validation must respect time order (forward holdout).
  3. Regime drift is real enough that online retraining measurably helped.
- Kaggle targets are short-horizon returns scored by correlation, MAE or R², with no costs, so a winning model can still lose money after costs. They are useful for feature ideas, not for rules. This is consistent with the lab's D5 decision to use ML only as a meta-label on a rule with proven gross edge.
- Treat any solution built on leaks or reverse-engineering of the dataset as a negative example.

### Gaps
- The official 1st-place writeup for Jane Street 2024–25 and the full text of the G-Research winner's features were not retrieved.

## 5. Sources to avoid or discount (marketing / low quality)

### Takeaway
Discount sources that sell strategy packs or courses backed by backtests without an audit, sources with undisclosed selection, and anything that reports in-sample results only. Prefer peer-reviewed or working papers with a stated mechanism, data period and cost model.

### Cited Findings
- Quantified Strategies sells strategy packs ($1,490 for 10 futures strategies) next to unaudited backtest articles and self-selected testimonials. — [Quantified Strategies](https://www.quantifiedstrategies.com/big-reversal-moves-strategy/)
- Even well-known academic intraday results, such as the SPY intraday momentum paper, are reported as in-sample. — [CXO Advisory](https://www.cxoadvisory.com/?p=45565)
- Robot Wealth itself warns that over-optimised backtests "tortured until the equity curves looked beautiful" produced no profit. — [Robot Wealth](https://robotwealth.com/)
- Daily market commentary on WIN (moving-average "targets" in brokerage media) is not research. — [Money Times example](https://www.moneytimes.com.br/mini-indice-tem-leve-queda-de-011-enquanto-dolar-futuro-sobe-018-vtra/)

### Inferences
- Also low-yield, though not checked in depth this session: TradingView public "ideas" and scripts, YouTube or "guru" ORB variants, vendor blogs selling VPS or signals (for example the QuantVPS guides that appeared in the search results), and Medium re-tellings of Kaggle notebooks. Use them only to find the primary paper they paraphrase.
- A practical triage for the conveyor's idea intake:
  1. Is there a stated counterparty or mechanism?
  2. Is there a primary paper or code?
  3. Is the horizon intraday and the instrument a future or index?
  4. Are costs included?
  5. Is there an out-of-sample or post-publication period?
  Only sources that pass most of these should seed rule families.

### Gaps
- No systematic study rating retail strategy sites was found. The "3.7/100 median validation score across 890 backtests" claim needs its primary source before it can be cited.
