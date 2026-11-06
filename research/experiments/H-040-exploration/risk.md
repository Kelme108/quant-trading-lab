# Risk assessment: H-040 (DailyNR7Breakout), exploration split

Sources: `research/experiments/H-040-exploration/facts.json`, `trades-btc-usdt.csv`, `trades-eth-usdt.csv`, `trades-bnb-usdt.csv`, `research/proposals/H-040.json`, `lab/config/gates.json` (max drawdown 25%), `lab/config/portfolio.json`. For overlap I also read `research/experiments/H-025-exploration/trades-btc-usdt.csv` and `research/experiments/H-020-exploration/trades-btc-usdt.csv`.
Trade-list arithmetic below is mine, done by hand from the CSVs, so small errors are possible. Profit figures are in quote currency (100 USDT wallet per gates.json).

## 1. Drawdown

Max drawdown % from facts.json, gate ceiling 25%:

| Pair | optimistic | base | conservative | stress |
|---|---|---|---|---|
| BTC | 6.09 | 7.62 | 9.16 | 13.62 |
| ETH | 3.25 (relative 4.39) | 3.60 (relative 4.60) | 4.00 (relative 4.80) | 6.28 |
| BNB | 9.29 (relative 10.51) | 10.28 (relative 11.12) | 11.83 | 16.41 |

- Every cell is under 25%. The tightest is BNB at stress, 16.41%, which leaves about 8.6 points of headroom.
- For ETH and BNB the plain and relative drawdowns differ. The decision reasons use the relative figure.
- facts.json does not say whether these drawdowns are measured at the 0.35 exposure. I won't assume either way.

Longest losing stretches, counted from the trade lists (consecutive losing trades, then the time span):
- BTC: 6 straight losses from 2018-07-29 to 2019-03-23, about 8 months, summing to about -7.0. There were few trades in that stretch. It ended with a win on 2019-03-29. A second stretch of 5 losses ran from 2021-08-23 to 2021-10-03, about 6 weeks, summing to about -9.4.
- ETH: 4 straight stop-outs from 2017-11-29 to 2018-01-24 (about 8 weeks, about -4.8), and 3 in a row from 2020-02-21 to 2020-03-02. I did not scan the ETH list exhaustively for longer runs.
- BNB: the worst run is 7 straight losses from 2020-11-02 to 2021-01-25, about 12 weeks, summing to about -9.8. It was broken by the one huge winner on 2021-02-17. Before that, 5 straight losses ran from 2020-08-24 to 2020-10-04 (4 stops in the first 3 weeks of that run). The first 6 BNB trades (2018-01-20 to 2018-08-04) were all losses, about -6.2.
- Nearly all losing runs are 3.3–3.4% stop-outs. The fixed stop caps each loss but does not stop clustering.

## 2. Cost sensitivity

Net profit (facts.json):

| Pair | optimistic | base | conservative | stress |
|---|---|---|---|---|
| BTC | 66.11 | 58.05 | 50.33 | 29.38 |
| ETH | 43.60 | 37.70 | 32.06 | 16.35 |
| BNB | 45.86 | 39.38 | 33.20 | 16.13 |

- Stress keeps about 49% (BTC), 43% (ETH) and 41% (BNB) of base profit. Every pair stays positive at stress.
- The base-to-stress step is the steepest part. For BTC it is -7.7 from base to conservative, then -20.9 from conservative to stress.
- The proposal says round trip is 0.35% at base and 0.95% at stress (`research/proposals/H-040.json`). Reading profit against that, a linear extrapolation gives break-even at about 1.5% round trip for BTC, 1.4% for ETH and 1.4% for BNB. This is a rough extrapolation from two points, assuming a straight line. The fixed trade count (95, 80 and 87) makes linearity plausible, but I can't verify it. The conservative cost level is not stated in the files I read.
- BNB is the fragile one. Its net profit excluding the best trade is already -11.97 at stress (facts.json), and only +0.71 at conservative.

## 3. Concentration

- BNB depends on one trade. The 2021-02-17 trade returned +0.924 (+36.80), against base net profit of 39.38. Subtracting it by hand leaves about +2.6; facts.json reports 5.36 for `net_profit_excl_best_trade__base`. I can't explain the difference (possibly compounding), but both are barely positive. Removing the second-best trade too (2019-05-13, +14.64) would take it below zero (about -12 by simple subtraction). The gate passes only because it tests removal of a single trade.
- BTC: the 2017-10 to 2017-12 trades alone sum to about +29, roughly half of base profit (58.05). The best trade is 2017-12-06 at +16.86. After 2021 the trade count thins out: 4 trades in 2022, and a mix of small winners and stops in 2023–2024.
- ETH is the most evenly spread. Its best trade is 2022-07-27 at +8.13, and facts.json gives 27.86 ex-best against 37.70.
- Trades are absent for long periods: for example BTC has none between 2018-05-05 and 2018-07-23, and almost none through 2022. Profit arrives in short bursts during strong uptrends, mostly 2017, 2019–2021 and early 2024.
- Pair concentration: the three pairs are not independent samples (see section 4), so 262 trades overstate the independent evidence.

## 4. Overlap

Within H-040, same-day entries across pairs:
- 2020-02-23: all three pairs entered within two hours and all three were stopped out the next day.
- 2020-08-24: all three entered (07:00–08:00) and all lost (BTC close-below-low, ETH and BNB stop).
- 2023-03-26: all three entered; all lost (BNB via close-below-low).
- 2023-04-30: all three entered; all lost.
- 2022-03-27: all three entered and all won.
- 2024-03-10: all three entered; BTC and BNB won, ETH stopped.
- Other shared days include 2019-04-18 (BTC, BNB), 2020-04-29 (BTC, BNB), 2021-04-26 (ETH, BNB), 2022-11-04 (BTC, ETH).
- So several losing and winning days are shared across pairs. Losses are likely to arrive on all three at once.

Against other hypotheses (BTC trade lists only; I did not compute a correlation, and `portfolio.json` defines one on daily returns spread over holding periods):
- H-025 (long holds, `close_below_ema20`/stop): H-040 BTC trades fall inside H-025's holds, for example inside 2019-04-03 to 2019-06-05 (H-040 entries 2019-04-18, 05-19, 05-26, 06-02), 2020-10-12 to 2020-12-11 (2020-10-18, 11-11, 12-06), and 2024-02-09 to 2024-03-17 (2024-02-20, 02-26, 03-10). Both are long-only and trend-following, so they are in the market in the same rallies. H-040's holds are at most 48 bars, so H-040 is a short slice of those periods.
- H-020 (daily-high breakout, multi-day holds): some H-040 BTC trades fall inside its holds, for example 2020-08-24 and 2020-08-30 inside 2020-08-20 to 2020-09-02. The overlap is partial.
- I did not read the ETH or BNB lists of other hypotheses, nor the other H-0xx directories. The overlap check is partial; the correlation gate in `portfolio.json` is the proper test and its result is not in the files I read.

## 5. Execution realism

- Stop-outs fill at about -3.34% in nearly every stop trade (profit_ratio around -0.0334, e.g. BTC 2017-10-27, ETH 2017-11-29, BNB 2018-01-20). The backtest assumes the 3% stop fills at its level plus costs. A fast move through the level, a weekend gap, or a thin 1h bar would give a larger loss. The tight clustering suggests no gap/slippage is modelled in these exports.
- Exits on `close_below_nr7_low` and time exits execute at the next 1h open. Moves between the signal close and the next open are not captured beyond that.
- Entries are on the close of a 1h bar and executed at the next open, so a breakout that is already running is bought after the move. If live fills differ by even 0.3–0.5%, that is comparable to the whole base round-trip cost (0.35%) and close to the stress step.
- Trade frequency: about 80–95 trades per pair over roughly 7 years, so about 12–14 per pair per year. Outages or missed signals would have a visible effect, because each winner matters (see section 3). A missed trade on a day like 2021-02-17 (BNB) would remove most of that pair's profit.
- Entries cluster on the same days across pairs (section 4), so a single outage or API problem can hit all three pairs at once.
- Fee tier, spread and slippage in the cost scenarios are the lab's assumptions; I can't tell from the files how they were set, and real conditions during the exploration years (including early BNB liquidity) may differ.
- BNB buy-and-hold of +33,023% shows the data begin at a very low price; liquidity in the earliest BNB period is uncertain.

Nothing here is a recommendation on sizing, leverage or going live.
