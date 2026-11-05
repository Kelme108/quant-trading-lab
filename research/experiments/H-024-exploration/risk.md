# Risk review: H-024 (DailyMaxJumpMomentum), exploration split

Sources: `research/experiments/H-024-exploration/facts.json`, `trades-btc-usdt.csv`, `trades-eth-usdt.csv`, `trades-bnb-usdt.csv`, `research/proposals/H-024.json`, `lab/config/gates.json`, `lab/config/portfolio.json`. Overlap uses `research/experiments/H-009-exploration`, `H-016-exploration` and `H-020-exploration` (BTC trade lists only). I did not read H-004/005/007/008 or any ETH/BNB lists from other hypotheses.

Cumulative-profit figures below are my own running sums of `profit_abs` in the trade CSVs. They are not in facts.json. For BTC, the sum of all 43 trades is about 99.4 and the facts.json base net profit is 99.31, so the CSV appears to be the base scenario. I did not check the same for ETH and BNB.

## 1. Drawdown

Gate ceiling: 25% in every cost scenario (`gates.json`). The exposure is a fixed 0.25 of the account (`facts.json`). All figures are in percent.

| Pair | Scenario | Max DD | Relative DD (gate basis) |
|---|---|---|---|
| BTC | optimistic / base / conservative / stress | 10.40 / 10.78 / 11.12 / 12.24 | same as max DD |
| ETH | optimistic / base / conservative / stress | 5.55 / 5.61 / 5.67 / 6.79 | 6.10 / 6.23 / 6.37 / 6.79 |
| BNB | optimistic / base / conservative / stress | 6.48 / 6.59 / 6.69 / 7.00 | 11.44 / 11.70 / 11.96 / 12.74 |

- Every cell is below 25%. The worst is BNB stress at 12.74% relative, which is about half the ceiling.
- For ETH and BNB, the relative drawdown is larger than the plain one. BNB's relative figure is about 1.8 times its plain figure. I cannot tell from the files how that gap arises. It is probably a drawdown measured on a small early equity base.
- The 25% exposure is already scaled so that a bootstrap drawdown stays under 25% (`H-024.json`). The realized drawdowns are about half that.

**Duration of the worst stretches (from the trade lists):**
- BTC: the equity peak was at the 2021-03-23 close, at a cumulative profit of about 96.9. The trough was about 75.7 at the 2022-10-11 close. That is about 21 quote units, or about 10.8% of the account, which matches the base max DD.
  - The new high came only on 2024-03-17 (about 105.4). That is about three years below the peak, out of a window of about six years.
  - Within that, 2021-10-28 to 2022-10-11 had 7 closed trades with only one winner (+0.90), a net of about −18.6. Four consecutive losers ran from 2022-07-29 to 2022-10-11, about 74 days, for about −11.1.
  - Another cluster ran from 2021-03-31 to 2021-05-12: three consecutive losers, one of them a stop-loss, for about −12.2 in six weeks.
- ETH: after the first winner closed on 2018-05-12 (+4.69), the cumulative profit stayed at or below that level until the 2020-01-07 to 2020-02-26 trade (+17.66). That is about 21 months below the prior peak. It included two stop-losses within 16 days (2018-12-25 and 2019-01-02).
- BNB: stop-loss clusters. For example, 2020-08-31, 2020-09-12 and 2020-11-25 are three stops in three months. 2022-03-02 to 2022-12-08 had mostly losers: −5.65, +3.39, −1.52, +6.15, −7.99, −3.30. I did not compute BNB's peak-to-recover date.
- Across all three pairs, 2022 was the weak year, and 2023 to early 2024 was choppy.

## 2. Cost sensitivity

Base net profit is the left column. Scenario cost levels (fee and slippage values) are not in the files I read. I looked in `lab/config/scenarios.json`, but the grep did not show them.

| Pair | Optimistic | Base | Conservative | Stress | Stress vs optimistic |
|---|---|---|---|---|---|
| BTC | 102.61 | 99.31 | 95.96 | 86.68 | −15.5% |
| ETH | 46.49 | 44.53 | 42.59 | 36.91 | −20.6% |
| BNB | 194.22 | 189.69 | 185.48 | 172.63 | −11.1% |

- Degradation is gradual and roughly linear. Between the optimistic and stress scenarios, BTC loses about 15.9 quote units over 43 trades (about 0.37 per trade). ETH loses about 9.6 over 36 trades. BNB loses about 21.6 over 39 trades.
- Because the cost levels are not known to me, I cannot give a break-even cost in percent. Extrapolating the straight line would multiply the stress step by roughly 5 to 7 before BTC and ETH hit zero. That is only a rough reading of three points and I would not rely on it.
- The strategy trades rarely (36 to 43 trades per pair over about six years), so cost is not the binding risk. The proposal expected 60 to 100 trades per pair. Actual counts were about half that.

## 3. Concentration

Using `net_profit_excl_best_trade` against net profit, both from `facts.json` at base:

| Pair | Net profit | Excl. best trade | Best trade share |
|---|---|---|---|
| BTC | 99.31 | 65.38 | about 34% |
| ETH | 44.53 | 22.80 | about 49% |
| BNB | 189.69 | 56.75 | about 70% |

- The gate passes on every pair, but BNB is dominated by one trade. In the BNB CSV, the 2021-02-02 to 2021-03-07 trade made +3.38 (+338%), or +94.7 quote units. The next trade, 2021-03-30 to 2021-05-13, made +57.4. Those two trades total about 152 of the roughly 190 base profit, and both fall in Feb–May 2021.
- The removed amount in facts.json (for example BTC 33.9) is slightly larger than the CSV's largest `profit_abs` (30.5). I think the metric recomputes the equity path without the trade, but I can't confirm it from the files.
- BTC's profit also clusters. The 2019-04 to 2021-02 run of big winners (+16.3, +10.7, +6.6, +14.4, +30.5, +14.4) accounts for most of the total. Since 2021-03 the cumulative figure moved from about 96.9 to 99.4.
- ETH's profit is concentrated in 2020-01 to 2021-08. 2018, 2022 and 2024 were net flat or negative on the CSV figures.
- Hit rate is low. By counting `profit_abs`, BTC has about 18 winners in 43 trades, and a majority of ETH and BNB trades also lose. This is what the proposal's rationale warned about ("profit depends on a few large moves").
- Loss structure: ETH has 7 stop-loss exits and BNB has 9 (BTC 1). Each stop realizes about −12.3% on the trade.
- The pairs are not independent. `scenarios.json` notes BNB's correlation with BTC at 0.635 over all common days and 0.813 over the last 365 days. In H-024, many entries line up (see section 4).

## 4. Overlap with other hypotheses

I only compared BTC. I did not compute a correlation, and the numbers below are examples of date overlap, not a full measure.

- **H-009 (BTC):** the two are in the market in similar windows during rallies.
  - 2019-04-03 to 06-04 (H-024) against 2019-03-29 to 04-12 and 05-02 to 05-17 (H-009).
  - 2020-12-16 to 2021-01-21 against 2020-12-15 to 12-21 and 12-25 to 2021-01-11.
  - 2021-02-03 to 02-26 against 2021-02-06 to 02-22.
  - 2023-10-24 to 11-22 against 2023-10-23 to 11-13.
  - 2024-01-30 to 03-17 against 2024-02-07 to 02-17 and 02-20 to 03-17.
  - Losses coincide too. 2024-01-09 to 01-13 is a loss in H-024, and 2024-01-08 to 01-12 is a loss in H-009.
  - H-009 had no trades from 2021-11-16 to 2023-01-20, while H-024 was losing in 2022. So they diverge in that period.
- **H-016 (BTC, time-series momentum):** it has long holds. 2020-10-04 to 2021-02-07 spans both H-024 trades of 2020-10-22 to 12-09 and 2020-12-16 to 2021-01-21. 2023-10-01 to 2024-01-08 spans two H-024 trades. 2024-02-10 to 04-04 overlaps with 2024-01-30 to 03-17. H-016 is in the market on more days than H-024, so most H-024 days are covered by H-016.
- **H-020 (BTC, 7-day-high exit):** it has about 50 short trades. Its dates overlap with H-024's in rallies such as 2020-05, 2021-03 and 2023-03, but H-020's profits are small, because its position sizes are small (about 1 per trade).
- Overall, it looks like the same BTC trend exposure. The `portfolio.json` correlation test (|r| ≤ 0.7, base scenario, using daily returns spread over holding days, across all pairs) has not been computed here, so I cannot say whether H-024 passes it.

## 5. Execution realism

- **Entries and exits** happen at the 1h open right after the daily close (00:00 UTC, as seen in the open dates). Everyone running daily-close signals trades at that time. The backtest fills at the open without slippage beyond the cost scenarios. That is likely fine for BTC and ETH sizes in the backtest. BNB/USDT was far less liquid early in the data, so fills are less certain there.
- **Stop-loss** is a native intrabar stop at 12%, and the stop trades realized about −12.31% in the CSVs (for example ETH 2018-12-25, BNB 2022-11-05). That means the backtest fills at the stop level every time. In a fast gap or flash crash, or an exchange outage, a live stop may fill materially worse, and a stop order may not execute at all during downtime. The sample has 17 stop exits, and I cannot tell from the files how bad the tail could be.
- **Frequency:** at about 6 to 7 trades per pair per year, a missed or delayed order has a visible effect. With big winners carrying the profit (section 3), missing one entry, for example because of an outage at 00:00 UTC, could change the result a lot. Exits that fire on a daily close below SMA20 can also be missed.
- **Open trade at end:** BNB's last trade is a `force_exit` on 2024-07-25 at −5.5%. It is an artifact of the backtest end, not a signal exit.
- **Data and history:** the signals need about 180 days of warm-up (4400 bars), which was met. Lookahead and recursive checks passed (`facts.json`). The 2018 BTC and ETH trades come at the start of the usable data; I cannot judge data quality there.
- Single exploration split only. The gates require a second, independent pass on validation, which has not been read here. This review makes no statement on that.
