# Risk assessment: H-046 (LivermorePivotFailFast, 1h), exploration split

Sources: `research/experiments/H-046-exploration/facts.json`, `trades-btc-usdt.csv`, `trades-eth-usdt.csv`, `trades-bnb-usdt.csv`, `research/proposals/H-046.json`, `lab/config/gates.json`, `lab/config/portfolio.json`, `lab/config/scenarios.json`. For overlap I also used `research/experiments/H-005-exploration/trades-btc-usdt.csv` and `research/experiments/H-007-exploration/trades-btc-usdt.csv`.

I counted trades and streaks by reading the CSVs by eye, with no calculation tool. Treat counts as approximate. Dollar figures and drawdowns come straight from `facts.json`.

## 1. Drawdown

The gate ceiling is 25% in every required cost scenario (`gates.json`, `max_drawdown.max_ratio` = 0.25). Values are from `facts.json`.

| Pair | Optimistic | Base | Conservative | Stress | Stress as share of ceiling |
|---|---|---|---|---|---|
| BTC | 5.61% | 6.00% | 6.44% | 7.77% | about 31% |
| ETH | 5.68% | 6.06% | 6.53% | 13.05% | about 52% |
| BNB | 12.38% | 13.59% | 15.34% | 20.43% | about 82% |

- Every cell is under the ceiling.
- BNB stress is 20.43%, the closest to the limit. Its drawdown also rises more steeply with cost than BTC's.
- ETH stress (13.05%) is about double its base figure (6.06%). The jump from conservative to stress is much larger than the earlier steps. This suggests many losses are small relative to costs.

**Worst losing stretches.** These are consecutive losing trades in the trade lists. A trade with a profit ratio ≤ 0 counts as a loss, and the profit figures are base.
- **BTC:** about 12 consecutive losses, from 2018-08-22 to 2019-03-16. That is roughly 7 months between winners (the last prior winner closed 2018-07-26, the next opened 2019-03-29). Another run of about 6 losses runs from 2022-05-30 to 2022-09-12.
- **ETH:** about 12 consecutive losses, from 2020-08-30 to 2020-12-01, followed by a +3.5% winner on 2020-12-16. A run of about 8 losses runs from 2019-10-09 to 2020-02-04.
- **BNB:** about 19 consecutive losses, from 2019-05-15 to 2020-01-31. That is roughly 8.5 months with no winning trade. There is also an 11-loss run from 2017-12-25 to 2018-05-18 and a 12-loss run from 2023-07-13 to 2024-02-08.

The 4% stop is not a hard cap. Stop-loss exits realise about -4.33% in the CSVs.

Many `stop_loss` trades have duration 0 (opened and stopped within the same hourly candle). Examples: BTC 2018-10-15, 2020-04-02 and 2024-01-11; ETH 2018-01-10, 2018-10-15, 2019-10-26 and 2020-12-01. BNB has about 10, mostly in Jan–Mar 2018. This points to entries at or near a spike top. It is a weakness for live fills (see section 5).

The drawdown figures are modest partly because each position is small. The ratio of `profit_abs` to `profit_ratio` implies a stake of about 20 USDT early in the split (BTC 2017: -0.868 / -0.0434), growing to about 29 USDT later. I did not verify the staking rule beyond that.

## 2. Cost sensitivity

Net profit in quote currency (`facts.json`):

| Pair | Optimistic | Base | Conservative | Stress | Drop, optimistic to stress |
|---|---|---|---|---|---|
| BTC | 50.60 | 44.78 | 39.12 | 23.89 | about 53% |
| ETH | 51.20 | 45.04 | 39.12 | 22.60 | about 56% |
| BNB | 70.96 | 63.96 | 57.48 | 39.34 | about 45% |

- Degradation is steeper at the stress end. BTC loses about 5.8 and then about 5.7 over the first two steps, then about 15.2 from conservative to stress. ETH and BNB show the same shape.
- The proposal text gives the base round-trip cost as 0.35% and the stress cost as 0.95% (`H-046.json`, rationale). I could not find the conservative or optimistic cost in the files I read, so I did not use them.
- **Rough break-even.** I extrapolated linearly from base to stress, which gives about 35–41 quote units lost per extra 1 percentage point of round-trip cost. This puts break-even at roughly 1.6% (BTC), 1.5% (ETH) and 1.9% (BNB). Profit does not fall exactly linearly (the stake compounds), so these are crude estimates.
- The BNB break-even is not trustworthy. Without its single best trade, BNB is already negative at conservative cost (-3.24) and at stress cost (-14.24). The base-only check passes at +0.73.
- The strategy has many short fail-fast trades (about 1-hour holds with 0.7–3% losses). Each pays round-trip costs, so cost drag grows with trade count (130–139 per pair).

## 3. Concentration

- **BNB depends on one trade.** The trade opened 2021-02-01 and closed 2021-02-23 returned +314% (+54.95 quote). That is about 86% of the 63.96 base net profit. Without the best trade, base profit is 0.73, which is barely above zero. Conservative is -3.24, and stress is -14.24 (`facts.json`). The gate only tests the base case (`gates.json`: `profit_excluding_best_trade`), so BNB passes narrowly. The next two BNB winners are +11.64 (2021-04-05) and +8.43 (2021-08-10), also in 2021. BNB profit is concentrated in the early-2021 rally.
- **BTC and ETH are less dependent on one trade.** BTC excluding the best trade is 35.79 (base) and 16.35 (stress); ETH is 32.72 (base) and 12.34 (stress). Both stay positive in all four scenarios.
  - The implied best-trade size from `facts.json` (BTC 44.78 - 35.79 = about 8.98; ETH 45.04 - 32.72 = about 12.33) is slightly larger than the largest `profit_abs` in the CSVs (BTC 8.38, ETH 12.08). I could not explain the gap. It may reflect a different cost scenario or rounding, and I am flagging it as unverified.
- **Few trades carry the profit.** Across all pairs, almost every winner is a `trail_48_low` exit, and most trades lose (fail-fast and stop-loss exits). For BTC I count about 17 trades with profit ≥ 10%, out of 130, and these produce nearly all the gain. The strategy is a low-hit-rate, large-winner pattern. A different sequence of rallies could flip the outcome.
- **Time clustering.** Large winners cluster in rally periods: 2019 (Mar–Jun), 2020 H2, early 2021, 2023 January and early 2024 (all pairs). Long barren stretches follow (see section 1). The split covers 2017–2024, so the result depends on how many bull rallies fall inside it.
- **Three pairs are not independent.** `scenarios.json` notes daily-return correlation with BTC of 0.787 (ETH) and 0.635 (BNB) over all common days. Several entry times are identical across pairs, for example 2018-04-12 12:00 (BTC and ETH), 2019-03-29 10:00 (BTC and ETH), 2020-07-22 23:00 (BTC and ETH) and 2018-10-15 07:00 (stopped out in the same hour on all three... BTC and ETH both, BNB not checked). So three pairs give fewer than three independent samples.
- **Portfolio consistency.** `portfolio.json` requires the smallest profit per day to be at least 0.25 of the largest. Base profits are 44.78, 45.04 and 63.96, and the pair date ranges differ slightly, so this should pass on exploration. I did not compute it. BNB's profit is the one most exposed to a single trade.

## 4. Overlap

Other hypotheses with trade lists under `research/experiments/` are H-004, H-005, H-007, H-008, H-009, H-016, H-020, H-024, H-025 and H-040. I compared the two nearest in style, both long-only breakout strategies, on BTC/USDT. I did not compare the others or ETH/BNB, and I computed no correlation coefficient.

- **H-007** (`H-007-exploration/trades-btc-usdt.csv`), 20-day breakout in a rising trend with slow exits:
  - It opened at identical timestamps to H-046 on 2019-03-29 10:00, 2020-07-22 23:00, 2023-03-30 03:00, 2023-07-13 20:00, 2024-02-07 21:00, 2024-04-08 09:00 and 2024-05-15 19:00. That is 7 of its 20 BTC trades.
  - H-007 holds for weeks: 2020-10-10 to 2021-01-21, 2019-03-29 to 2019-06-04 and 2021-10-03 to 2021-11-18. H-046 BTC makes several entries inside those windows (for example 2020-10-27 to 2020-12-26 and 2019-04-22 to 2019-05-26). So H-046 was in the market on many of the same days as H-007's long holds.
- **H-005** (`H-005-exploration/trades-btc-usdt.csv`), volatility-squeeze breakout:
  - It opened at identical times on 2018-09-01 16:00, 2021-03-09 02:00, 2021-05-03 08:00, 2021-08-13 21:00, 2021-10-01 11:00, 2023-04-10 17:00, 2023-05-28 19:00 and 2024-02-07 21:00. That is 8 of its 31 BTC trades.
  - H-005 holds for weeks: 2019-02-19 to 2019-07-16, and 2020-10-08 to 2021-01-22. These cover many H-046 entries.
- The three strategies enter on the same breakout bars in several cases, and both of the others hold through the big rallies that also drive H-046's winners. Day overlap with these two is therefore high in rally periods. H-046 sits flat or churns small fail-fast losses outside them.
- Whether the daily-return correlation exceeds the 0.7 limit in `portfolio.json` is not measurable from what I read. I did not compute it, and I make no claim about it.

## 5. Execution realism

- **Fills.** The backtest assumes an entry at the next bar's open (bar t+1) after a close above the 10-day high on 2x volume. Those are the bars with the widest spreads, fastest moves and heaviest order flow, so live fills would likely be worse than the open price. A stop at 4% is modelled as a native intrabar stop, yet many CSV stops realise -4.33% and about 10 BNB trades stopped within the entry hour. That suggests gap or spike behaviour that live slippage could make worse.
- **Costs.** About 130–139 trades per pair in about 6.5–7 years (roughly 20 per pair per year) is a moderate frequency, so costs and slippage add up. The stress scenario (0.95% round trip, per the proposal) cuts profit by about 45–56% from optimistic. If real slippage on breakout bars exceeds the stress assumption, profit approaches zero (section 2).
- **Fail-fast exits.** Fail-fast exits fire at the open of the bar after a close below the pivot, typically 1–8 hours after entry. On a fast reversal the live exit fill can be well below the pivot, so losses of 2–4% on "fail-fast" trades, which already appear in the CSVs (for example BTC 2018-12-19 at -2.6% and ETH 2020-04-02 at -3.8%), could be larger live.
- **Outages and gaps.** `scenarios.json` notes 28 BTC data gaps from 2017-09 to 2023-03 (largest 33 missing hours, consistent with exchange downtime). Breakout and stop events during downtime are not representable in the backtest. A volume-spike strategy is more likely to meet exchange instability and API throttling at exactly the moments it trades.
- **Data and history.** Results rest on one sample of 2017–2024 with a few huge rallies. Prices from 2017–2018 may not reflect current liquidity or fee tiers. The BNB result especially rests on one 2021 move.
- This lab does not approve live trading, and nothing here is a recommendation on size or deployment.
