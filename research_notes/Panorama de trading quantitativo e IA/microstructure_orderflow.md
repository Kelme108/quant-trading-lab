# Microstructure, order-flow and LOB approaches (incl. ML) for short-horizon futures: what is realistic without co-location

Scope note: about 22 searches and fetches. Items marked **[prior knowledge, not verified this session]** come from the researcher's background knowledge and were not re-checked against a source in this session. The report writer should treat them as lower confidence.

## 1. Evidence for OFI, trade-flow imbalance, VPIN, queue imbalance, Hawkes, Kyle lambda, and their horizons

### Takeaway
Order-book signals have the strongest evidence of any family here. OFI and queue imbalance explain or predict price moves very reliably, but mostly at the same moment or one tick ahead. Their predictive reach is about "two average price changes" (seconds, not minutes), which is far below the reaction time of a retail MT5 setup. VPIN is contested and has no reliable evidence that it forecasts volatility. Hawkes-based prediction is still preliminary and small-sample.

### Cited Findings
- **OFI (Cont, Kukanov and Stoikov).** Over short intervals, price changes are driven mainly by order flow imbalance at the best bid and ask. The relation is linear, with a slope inversely proportional to market depth, and it is robust to intraday seasonality and stable across time scales and stocks (NYSE TAQ, 50 US stocks). The paper also says the OFI relation is cleaner than the price-to-volume relation and discusses OFI as a measure of adverse selection for limit orders. Journal of Financial Econometrics 12(1):47–88 — [arXiv 1011.6402](https://arxiv.org/abs/1011.6402); [RePEc](https://ideas.repec.org/a/oup/jfinec/v12y2014i1p47-88..html)
- **Key nuance:** the CKS relation is **contemporaneous**: it explains the price change over the same interval as the flow. It is not a forecast. (This follows from the abstract's wording, "price changes are driven by OFI over short intervals" — [arXiv 1011.6402](https://arxiv.org/abs/1011.6402).) Extensions exist, such as multi-level and "generalized" OFI — [arXiv 2112.02947](https://arxiv.org/pdf/2112.02947).
- **Deep OFI (Kolm, Turiel and Westray, Mathematical Finance 2023).** On 115 Nasdaq stocks, models trained on order-flow features significantly outperform models trained on raw order-book levels. The effective forecast horizon is about **two average price changes**. A follow-up reports that beating a simple LSTM is "surprisingly challenging" — [SSRN 3900141](https://papers.ssrn.com/abstract=3900141); [RePEc](https://ideas.repec.org/a/bla/mathfi/v33y2023i4p1044-1081.html)
- **Trade-flow imbalance (Silantyev 2019, BitMEX).** Trade-flow imbalance (signed aggressor volume) explains **contemporaneous** price changes better than aggregate OFI on BitMEX. The author links this to thin depth and low quote-update rates in crypto. Price change and OFI become strongly linear over long enough intervals — [Digital Finance 2019](https://ideas.repec.org/a/spr/digfin/v1y2019i1d10.1007_s42521-019-00007-w.html)
- **Queue imbalance (Gould and Bonart).** Using logistic regressions on 10 liquid Nasdaq stocks, best-quote queue imbalance strongly predicts the **direction of the next mid-price move** (one tick ahead). The improvement is "considerable" for large-tick stocks and "moderate" for small-tick stocks — [arXiv 1512.03492](https://ar5iv.arxiv.org/html/1512.03492)
- **Imbalance is real but too small to beat taker costs.** A 2025 market-making paper finds that an imbalance **taker** strategy makes about +1 bp per round trip before fees, and taker fees on both legs wipe it out completely (negative mean net return) — [arXiv 2502.18625](https://arxiv.org/pdf/2502.18625). A stochastic-control paper reaches the same conclusion: buying and selling back on accurate best-level size predictions does not beat spread plus fees. Imbalance can still save a few bp for someone who already has to trade — [arXiv 1610.00261](https://arxiv.org/pdf/1610.00261)
- **Latency kills order-book-imbalance profit.** In an agent simulation, latency is inversely related to OBI-trader profit, and **latency rank** among competitors, not absolute latency, decides who gets the returns — [arXiv 2006.08682](https://arxiv.org/abs/2006.08682v1)
- **VPIN is disputed.** Andersen and Bondarenko (JFM 2014) find no incremental predictive power of VPIN for future volatility. They also find that VPIN did not reach unusual extremes before the 2010 Flash Crash and that its behavior depends strongly on the trade-classification method. Easley, López de Prado and O'Hara published a rejoinder, and Wu et al. ("Testing VPIN on Big Data") dispute AB's event criteria — [Reflecting on the VPIN dispute](https://ideas.repec.org/a/eee/finmar/v17y2014icp53-64.html); [working paper](https://repec.econ.au.dk/repec/creates/rp/13/rp13_42.pdf); [ELO rejoinder](https://ideas.repec.org/a/eee/finmar/v17y2014icp47-52.html); [Kellogg summary](https://insight.kellogg.northwestern.edu/article/the_trouble_with_vpin)
- **Hawkes models.** Results are mostly small-sample. One 2023 preprint beats benchmarks on 50 two-minute samples of Tether LOB data [arXiv 2312.16190](https://arxiv.org/html/2312.16190v1). Sjogren and DeLise (2021) show directional potential only with sufficient fine-tuning [arXiv 2110.07075](https://www.arxiv.org/pdf/2110.07075). Queue-reactive Hawkes work on Eurex Bund and DAX Level-I data improves order-flow **description**, not price forecasting [arXiv 1901.08938](https://arxiv.org/pdf/1901.08938). Survey: [Bacry et al. 2015](https://arxiv.org/pdf/1502.04592)
- **Kyle's lambda** (price impact per unit of signed volume) is a standard illiquidity and impact measure in Hasbrouck's *Empirical Market Microstructure* and in Bouchaud et al. *Trades, Quotes and Prices*. Its use is to estimate impact and cost, not to generate directional signals. **[prior knowledge, not verified this session]**
- **Order flow is long-memory and impact is concave (square-root law)**, which is the central theme of Bouchaud, Bonart, Donier and Gould, *Trades, Quotes and Prices* (CUP 2018). Order-flow sign is persistent, but prices stay close to a martingale because liquidity adjusts. **[prior knowledge, not verified this session]**

### Inferences
- Horizon hierarchy: signals that are contemporaneous or one tick ahead (OFI, queue imbalance) are the strongest. Forecasting power decays within a few price changes, which for liquid futures means **sub-second to a few seconds**. At retail round-trip latency of 50–300 ms plus the MT5 order path, a taker that acts on these signals arrives after the move, or competes for it against co-located HFTs with better latency rank.
- Signals that might survive at **minute** horizons come from aggregated flow: cumulative signed volume over many seconds or minutes, and order-flow persistence or meta-orders. Their edge per trade is smaller and slower, and the evidence is that most of it is absorbed by liquidity provision (the near-martingale property).
- Lab-relevant point: if the lab's bar rules fail after 0.4 tick slippage per side, taker OFI or imbalance strategies are even less likely to pass. The literature says these edges are about 1 bp before fees and disappear after taker costs, even in simulations with co-location-like speed.

### Gaps
- No source found that measures OFI or imbalance predictive decay **in wall-clock seconds** for an index future such as ES or WIN. Kolm et al. measure it in price changes.
- No rigorous out-of-sample study of VPIN on B3 was found.
- Kyle lambda's use as a predictive feature at short horizons was not checked.

## 2. Deep learning on the LOB (DeepLOB, FI-2010, LOBCAST, LOBFrame, TLOB): do results survive costs and latency?

### Takeaway
No. The benchmark literature from 2023–2025 shows that headline accuracies (often on FI-2010) do not generalize, collapse at longer horizons for small-tick instruments, and do not turn into trades that pay costs. Even the authors avoid claiming profitability. Predictability is concentrated in **large-tick** instruments at horizons of tens of book events.

### Cited Findings
- **DeepLOB** (Zhang, Zohren and Roberts, IEEE Trans. Signal Processing 2019) uses a CNN and LSTM on 10-level LOB data. It is the reference model, trained on FI-2010 and LSE data — [arXiv 1808.03668](https://arxiv.org/abs/1808.03668) **[paper details from prior knowledge, not re-verified this session]**
- **LOBCAST (Prata et al., Artificial Intelligence Review 2024).** Benchmarks 15 DL LOB models. **All show a significant performance drop on new data**, which indicates a gap between benchmark and real-market performance. Attention-based models do best. The paper releases a backtesting and profit-analysis environment and reproduces FI-2010 claims — [arXiv 2308.01915](https://arxiv.org/abs/2308.01915v2); [Springer](https://link.springer.com/article/10.1007/s10462-024-10715-4)
- **LOBFrame (Briola, Bartolucci and Aste, Quantitative Finance 25(7) 2025).** DeepLOB on LOBSTER 10-level data for 15 Nasdaq stocks, 2017–2019. Horizons are 10, 50 and 100 **book updates** (event time). Average MCC:
  - large-tick stocks: 0.29 / 0.36 / 0.26
  - medium-tick: 0.13 / 0.085 / 0.036
  - small-tick: 0.11 / 0.04 / 0.01 (effectively random at horizon 100)
  - "High forecasting power does not necessarily correspond to actionable trading signals." The proposed probability of a correct transaction is low: for BAC at horizon 10, pT = 0.07 at threshold 0.3 against MCC 0.30.
  - The authors refuse to backtest because it would need perfect execution, zero impact, zero costs and timely processing. Latency is not modeled.
  - [arXiv 2403.09267](https://arxiv.org/html/2403.09267v4); [UCL open copy](https://discovery.ucl.ac.uk/id/eprint/10218102)
- **TLOB (Berti and Kasneci, 2025).** A dual-attention transformer that reports state-of-the-art results on FI-2010, Nasdaq and BTC data across four horizons. When trend labels are set by the **average spread** (the main transaction cost), performance deteriorates, which "underscores the complexity of translating trend classification into profitable trading". The v1 abstract also reported that predictability fell over time (−6.68 F1 points). That figure may not appear in later versions — [arXiv 2502.15757](https://arxiv.org/html/2502.15757v2)
- **Kolm and Westray follow-up:** beating a simple LSTM on LOB return forecasting is "surprisingly challenging" — [SSRN / Deep OFI record](https://papers.ssrn.com/abstract=3900141) (see also [Improving Deep Learning of Alpha Term Structures](https://www.bohrium.com/paper-details/improving-deep-learning-of-alpha-term-structures-from-the-order-book/997218873411371589-16569))

### Inferences
- The DL LOB literature measures classification metrics in **event time**, usually without costs or latency. For WIN and WDO, horizons of 10 to 100 book updates last well under a second to a few seconds in active periods, which is outside what a retail MT5 loop can act on.
- WIN and WDO behave like **large-tick** instruments: deep queues, and the spread is usually one tick. This is the regime where LOBFrame finds the most predictability. But large-tick predictability is mostly "the next mid move follows the thinner queue", the same information as queue imbalance. A logistic regression captures it, and only a fast passive participant can monetize it.
- For the lab: DL on the LOB is not a sensible next lever. It needs full depth, which MT5 or Nelogica tick data may not provide in replayable form. The published evidence shows the gains do not survive execution.

### Gaps
- No DL LOB study with realistic taker costs plus 100 ms or more latency that is still profitable was found. Absence of evidence from about 22 searches is not proof that none exists.
- No DL LOB study on B3 futures was found.

## 3. With only trades plus best bid and ask (MT5): signed volume, delta, footprint, absorption

### Takeaway
Trade-sign imbalance (aggressor volume) has rigorous support as a **contemporaneous** price driver, comparable to or better than OFI in thin markets. Footprint, cumulative delta and "absorption" as trading **signals** rest mostly on discretionary-trader material. No peer-reviewed out-of-sample evidence was found. MT5 on B3 can supply aggressor flags via CopyTicks, though some ticks are ambiguous.

### Cited Findings
- Trade-flow imbalance explains contemporaneous price changes better than OFI on BitMEX — [Silantyev 2019](https://ideas.repec.org/a/spr/digfin/v1y2019i1d10.1007_s42521-019-00007-w.html)
- Best-quote queue sizes alone (Level 1) predict the next mid-price move — [Gould and Bonart](https://ar5iv.arxiv.org/html/1512.03492). Level-I Eurex data is enough for queue-reactive Hawkes modeling — [arXiv 1901.08938](https://arxiv.org/pdf/1901.08938)
- **MT5 aggressor flags on B3.** A B3 futures user reports that `CopyTicks()` returns TICK_FLAG_BUY and TICK_FLAG_SELL, while `SymbolInfoTick()` does not — [MQL5 forum 304098](https://www.mql5.com/en/forum/304098). Some ticks carry **both** flags (flags = 96), which means an undefined direction — [MQL5 forum 212349](https://www.mql5.com/en/forum/212349). Threads report that `COPY_TICKS_TRADE` mode drops the flags, so use `COPY_TICKS_ALL` — [MQL5 forum 224009](https://mql5.com/en/forum/224009). The usual fallback is a quote rule: last == ask means buyer, last == bid means seller — [MQL5 forum 293921](https://www.mql5.com/en/forum/293921). One blog says the flags are never set, probably about OTC forex feeds; this conflicts with the B3 reports — [MQL5 blog 774467](https://www.mql5.com/en/blogs/post/774467)
- Trade-classification choice materially changes flow metrics. In the VPIN dispute, VPIN's properties depend strongly on the classification method — [Andersen and Bondarenko working paper](https://repec.econ.au.dk/repec/creates/rp/13/rp13_42.pdf)

### Inferences
- With trades plus L1, the features a small team can compute rigorously are:
  - signed aggressor volume and trade-sign imbalance over windows
  - L1 queue imbalance (bid size − ask size) / (bid size + ask size)
  - L1 OFI (CKS needs only best-quote price and size changes)
  - trade-arrival intensity
  - an estimate of Kyle lambda for cost and impact
- The literature's main use for these features is **execution timing and cost reduction** (when to cross, when to wait), not standalone alpha at retail speed.
- "Absorption" (large aggressive volume with little price movement) corresponds conceptually to a **low realized impact relative to signed flow**, a time-varying Kyle lambda. A testable version: a rolling regression of Δprice on signed volume, then conditioning on residual or low-lambda states. No study was found that validates it as a signal.
- Before buying Nelogica history, verify on the lab's own recorded ticks how many are ambiguous (flags 96) and whether recorded flags match the quote rule. Data quality limits every flow metric.

### Gaps
- No peer-reviewed study of footprint charts, cumulative delta or absorption with out-of-sample, cost-adjusted results was found.
- Not verified: whether Nelogica's historical feed gives true exchange aggressor side for WIN and WDO, or an inferred one, and at what timestamp resolution.

## 4. Passive (limit-order) execution and market making for retail: economics and adverse selection

### Takeaway
Limit orders remove the taker cost but replace it with adverse selection and missed fills. Empirically, on CME futures, most naive passive fills are adverse: the price keeps moving against the order after the fill. At large-tick, deep-queue instruments such as WIN and WDO, a retail order without good queue priority gets filled mostly when it is "wrong". Passive entry can still cut costs for a strategy whose **edge comes from a slower signal**. The gain must be measured as post-fill drift plus missed-trade cost, not as spread saved.

### Cited Findings
- **Adverse fills on CME futures, naive posting, one day, 1-second data:**

  | Contract | Adverse share of fills |
  |---|---|
  | ES | ~82% (767 / 941) |
  | NQ | ~66% |
  | CL | ~83% |
  | ZN | ~89% |

  In a CL market-making simulation, about 83% of fills were adverse, and the realistic environment performed "much worse" than the naive benchmark. Caveats: a single day and internal inconsistencies in the paper's tables and dates — [arXiv 2409.12721](https://arxiv.org/html/2409.12721v2)
- **"Negative drift of a limit order fill."** Passive fills happen during adverse moves, shown in a simulation on 10-year Treasury futures — [DeLise, arXiv 2407.16527](https://arxiv.org/html/2407.16527v1)
- **Market maker's dilemma.** Fill probability and post-fill return trade off against each other. Maker strategies avoid taker fees but face queue position, fill probability and drift — [arXiv 2502.18625](https://arxiv.org/pdf/2502.18625)
- **Takers also lose to latency.** Takers suffer latency-induced adverse selection, and marketable limit orders often fail to fill immediately — [Oxford ORA paper](https://ora.ox.ac.uk/objects/uuid:cdab1de2-7576-42e2-abae-ab12371eba76/files/rs4655j600)
- **Missed trades can matter more than adverse selection.** For trend followers, the main cost of passive execution is missed opportunity, not adverse selection — [arXiv 2607.01550](https://arxiv.org/pdf/2607.01550)
- Small, consistent losses per fill add up. Practitioners estimate the penalty as the average return over a short window after the fill — [arXiv 1210.1625](https://arxiv.org/pdf/1210.1625)
- Speed protects market makers from adverse selection, and latency erodes the value of imbalance information — [arXiv 1610.00261](https://arxiv.org/pdf/1610.00261)

### Inferences
- For the lab:
  - **Retail market making on WIN/WDO is not realistic.** It means queue priority against B3-registered HFTs (see section 6) with 10–100× worse latency, so the 66–89% adverse-fill profile would apply or be worse.
  - **Passive entry for an existing slow signal is worth testing.** Example: post at the touch, cancel after N seconds, fall back to market order or skip. Measure it with realistic fill rules: fill only when price trades **through** the level, or queue-position modeling. Count post-fill drift and the P&L of missed signals.
  - Rough arithmetic for scale **[contract specs from prior knowledge, not verified this session]**: WIN tick = 5 points = R$1.00 per contract, WDO tick = 0.5 point = R$5.00. Slippage of 0.4 tick per side is about 0.8 tick per round trip. Passive execution could at best recover that plus part of the spread, but at an 80% adverse-fill rate the realized saving may be near zero or negative.
- The DL and OFI evidence suggests the only microstructure edge achievable at retail speed is **cost reduction**, not alpha.

### Gaps
- No B3-specific fill-probability or adverse-selection numbers for retail-latency passive orders were found.
- No study quantifying passive execution savings for minute-horizon strategies on index futures was found.

## 5. Open-source tools for tick and LOB research and their fit

### Takeaway
hftbacktest is the most relevant open tool for testing passive or limit-order logic with latency and queue models. NautilusTrader suits event-driven tick replay with a path to live trading. LOBSTER (Nasdaq, paid) and FI-2010 are the academic data standards. ABIDES suits agent simulation, not edge discovery. None has a native B3 or MT5 adapter, so the lab would need a converter from its recorded ticks.

### Cited Findings
- **hftbacktest** (nkaz001):
  - models feed latency and order latency (entry and response) and queue-position fill models, with built-in or custom versions
  - Python (PyPI) and Rust versions; the Rust version supports multi-asset and multi-exchange backtests
  - live deployment only for Binance Futures and Bybit
  - [GitHub](https://www.Github.com/nkaz001/hftbacktest); [docs](https://hftbacktest.readthedocs.io/)
- **LOBCAST** includes preprocessing, 15 DL models, evaluation and a backtesting environment — [arXiv 2308.01915](https://arxiv.org/abs/2308.01915v2)
- **LOBFrame** is open source, model-agnostic, built on LOBSTER data, from the FinancialComputingUCL GitHub — [arXiv 2403.09267](https://arxiv.org/html/2403.09267v4)
- **LOBSTER** gives reconstructed Nasdaq LOB data, the standard in LOBFrame and other papers — [used in arXiv 2403.09267](https://arxiv.org/html/2403.09267v4)
- **NautilusTrader** is an event-driven Rust/Python platform with tick and order-book replay and live adapters. **ABIDES** (JPMorgan and Georgia Tech) is an agent-based market simulator. **Tardis.dev** provides crypto tick and L2 replay. **[prior knowledge, not verified this session]**
- An undergraduate thesis at UnB built a market simulator for HFT strategies using B3 order-book dynamics (student work, not peer reviewed) — [UnB TCC 2023](https://bdm.unb.br/bitstream/10483/39754/1/2023_MatheusSantosAlves_tcc.pdf)

### Inferences
- Fit for the lab:
  - Use **hftbacktest**, or a small in-house event loop, to test passive-entry variants on recorded WIN/WDO ticks with a conservative fill rule and 100–300 ms latency.
  - Full-depth tools (LOBSTER-style reconstruction, DeepLOB) need MBO or MBP-10 data that MT5 does not stream historically.
  - ABIDES and other simulators cannot validate an edge, because their results depend on the agents' assumptions.

### Gaps
- Not verified: whether NautilusTrader or hftbacktest have community B3 or MT5 data converters, and the current versions and licenses.

## 6. Studies on B3 microstructure (WIN/WDO/IND/DOL) and HFT presence

### Takeaway
B3 runs a formal HFT program with HFT fee tiers on index and other derivative families, so registered HFTs certainly operate there. About 22 searches found **no peer-reviewed intraday order-flow or HFT microstructure study of WIN or WDO**, only student theses and monthly-frequency work. This is a real literature gap. Any edge claim for B3 must come from the lab's own data.

### Cited Findings
- **B3 HFT program.** Registration goes through a trading or settlement participant. Fee tiers are based on contract volume per family. Families listed include Ibovespa, Micro Bovespa, S&P 500 and live cattle. A separate fee schedule applies to approved HFTs — [B3 HFT Program](https://www.b3.com.br/en_us/products-and-services/fee-schedules/listed-equities-and-derivatives/incentive-program/hft-program/)
- HFT in Brazil is regulated by CVM and B3. B3 limits cancelled orders to curb quote stuffing — [B3 glossary](https://borainvestir.b3.com.br/glossario/high-frequency-trading/)
- WIN is the most traded product among day traders, with more than 140,000 investors per month. One day reached a record of 25.6 million contracts — [B3](https://b3.com.br/en_us/news/what-is-mini-index-win-and-why-does-it-attract-day-trade-newcomers.htm); [Bora Investir](https://borainvestir.b3.com.br/tipos-de-investimentos/renda-variavel/day-trade/volume-de-negociacao-do-mini-indice-win-atinge-maior-patamar-em-4-anos-na-b3/)
- **WDO specs and settlement.** WDO is USD 10,000, 20% of the full contract. Settlement is the weighted average of trades from 15:50 to 16:00, a known intraday flow window — [B3 Mini US Dollar Futures](https://b3.com.br/en_us/products-and-services/trading/exchange-rates/mini-u-s-dollar-futures.htm)
- **Academic work found:**
  - a USP thesis on standard and mini dollar open interest and PTAX, monthly 2017–2021, not intraday — [USP](https://www.teses.usp.br/teses/disponiveis/12/12139/tde-03042024-160952/publico/ThalitaRodrigueseSilvaForneOriginal.pdf)
  - a UFC undergraduate thesis on detecting manipulation patterns in mini-Ibovespa futures — [UFC](https://repositorio.ufc.br/bitstream/riufc/84436/1/tcc_aspsantos.pdf)
  - a Unipampa paper finding that intraday technical WINFUT strategies are hurt by volatility, costs and long drawdowns, with buy-and-hold more stable — [Unipampa](https://repositorio.unipampa.edu.br/bitstreams/82706f83-804f-40c4-8d01-0d8bb372d1fa/download)
  - a UFRJ thesis on the advance of HFT in Brazil — [UFRJ](https://pantheon.ufrj.br/bitstream/11422/11837/1/RHCPrelado.pdf)
- A B3 event in March 2026 described structures and incentives for HFT participants and market makers — [B3 news](https://www.b3.com.br/pt_br/noticias/mercado-de-capitais.htm)

### Inferences
- WIN and WDO have registered HFTs plus a very large retail base, a setting where retail flow is likely the "uninformed" side that HFTs and market makers trade against. Short-horizon L1 signals are presumably arbitraged by the faster participants.
- The 15:50–16:00 WDO settlement window and the Ibovespa futures expiry and settlement windows are structural flow events that last minutes, not milliseconds. They are a better fit for retail latency than tick-level signals, though not tested here.
- Recommended framing for the "flow lane":
  1. use flow features as **filters or conditioners** on minute-horizon rules
  2. use them for **execution** (passive versus aggressive entry timing)
  3. pre-register a horizon floor of 30 seconds or more and full taker costs plus 0.4 tick slippage
  4. budget every flow variant as a tested attempt under the lab's multiple-testing rules

### Gaps
- No peer-reviewed estimate was found of the HFT share of WIN or WDO volume, of B3 matching-engine or retail order round-trip latency, or of WIN/WDO queue depth and fill statistics.
- Not found: B3 market-data products or academic access to MBO data (UMDF), and Nelogica history specs such as aggressor flag provenance, timestamp precision and depth availability.
