# H-020 exploration: quantitative reading

Sources: `research/experiments/H-020-exploration/facts.json` (metrics and gate verdicts), `trades-<pair>.csv`, `crosscheck.json`, `research/proposals/H-020.json`, `lab/config/gates.json`. Profits are in quote currency on the 100 USDT wallet. `exposure` is 0.1 in facts.json for every pair. Trade-list figures are derived by me from the CSVs, and each derivation is stated.

## 1. Per-pair tables (facts.json, `metrics`)

Net profit / max drawdown % by cost scenario. Trade count is 58 (BTC), 66 (ETH) and 64 (BNB) in all four scenarios.

| BTC/USDT | optimistic | base | conservative | stress |
|---|---|---|---|---|
| trades | 58 | 58 | 58 | 58 |
| net profit | 6.617 | 5.727 | 4.710 | 2.241 |
| max drawdown % | 3.457 | 3.565 | 3.648 | 3.650 |

- Profit without the best trade: base 4.227, conservative 3.236, optimistic 5.095, stress 0.866. In the crosscheck the best trade is removed by compounding, not by subtracting its profit (`crosscheck.json`).
- Benchmarks: cash 0.0%, buy-and-hold +1252.66%.
- Gate verdict: `candidate_for_portfolio`. All listed gates pass: lookahead, recursive, minimum trades, net profit at base and conservative, profit excluding best trade, and drawdown.

| ETH/USDT | optimistic | base | conservative | stress |
|---|---|---|---|---|
| trades | 66 | 66 | 66 | 66 |
| net profit | 6.041 | 4.964 | 3.946 | 0.835 |
| max drawdown % | 11.045 | 11.188 | 11.327 | 11.757 |

- Profit without the best trade: base 2.431, conservative 1.445, optimistic 3.475, **stress -1.530**.
- Benchmarks: cash 0.0%, buy-and-hold +929.58%.
- Gate verdict: `candidate_for_portfolio`.

| BNB/USDT | optimistic | base | conservative | stress |
|---|---|---|---|---|
| trades | 64 | 64 | 64 | 64 |
| net profit | 8.143 | 7.130 | 6.106 | 3.090 |
| max drawdown % | 6.755 | 6.998 | 7.282 | 8.185 |

- Profit without the best trade: base 4.923, conservative 3.926, optimistic 5.910, stress 0.998.
- Benchmarks: cash 0.0%, buy-and-hold +33023.53%. The benchmark is reported as given. I have not checked what start price produces it.
- Gate verdict: `candidate_for_portfolio`.

Gate bars (`lab/config/gates.json`): at least 30 trades, net profit above 1.0 at base and conservative (0 prior variants in the family, per `facts.json`), positive profit excluding the best trade at base, and drawdown of 25% or less in every scenario. Beating the benchmark is not required. This is an exploration-split verdict only. `gates.json` requires the gates to be cleared again on the validation split before the decision can be `candidate_for_portfolio`.

The net profit bar is cleared by a thin margin in places: ETH at stress is 0.835, and the base bar is 1.0.

## 2. Cost sensitivity (derived from the tables above)

Differences are scenario profit minus base profit, in quote currency.

| pair | optimistic − base | conservative − base | stress − base | stress as % of base |
|---|---|---|---|---|
| BTC | +0.890 | −1.017 | −3.486 | 39% |
| ETH | +1.077 | −1.018 | −4.128 | 17% |
| BNB | +1.012 | −1.024 | −4.041 | 43% |

- Each step costs about 1 quote of profit. Stress removes 3.5 to 4.1, which is roughly 0.06 per trade (stress − base divided by trade count: 3.486/58, 4.128/66, 4.041/64).
- Average net profit per trade at base is 0.099 (BTC), 0.075 (ETH) and 0.111 (BNB). I got these by dividing base net profit by trade count. With a stake of about 10 (10% exposure) that is roughly 0.8% to 1.1% of the stake per trade after base cost. This stake figure is my inference from `exposure = 0.1` and the CSV `profit_abs` / `profit_ratio` ratio.
- The proposal states round-trip costs of 0.35% (base) and 0.50% (conservative) (`H-020.json`, rationale). It does not state the stress or optimistic figures, so I do not quote them.
- The average move per trade covers base and conservative cost, but not by a wide margin. ETH is the weakest: at stress its profit is 0.835 and its profit excluding the best trade turns negative (−1.530). The edge on ETH is not robust to the stress cost.
- BTC and BNB stay positive at stress, including without the best trade (0.866 and 0.998). Both are barely above zero on that measure.

## 3. Concentration, duration and exit reasons

Method: I sorted `profit_abs` in the base trades CSVs. Share = sum of the top N trades divided by base net profit (`facts.json`). The shares can exceed 100% because the remaining trades net to a loss.

| pair | best 1 | best 5 | best 10 |
|---|---|---|---|
| BTC | 1.440 → 25% | 5.529 → 97% | 8.739 → 153% |
| ETH | 2.455 → 49% | 8.921 → 180% | 15.000 → 302% |
| BNB | 2.269 → 32% | 9.678 → 136% | 16.186 → 227% |

- In all three pairs the five best trades equal or exceed total profit, and the other trades together lose money or net to about zero.
- The single best trade is 25%, 49% and 32% of base profit.
- Removing the best trade by compounding (`crosscheck.json`) leaves base profit at 4.227 (BTC), 2.431 (ETH) and 4.923 (BNB). ETH loses about half of its profit this way.
- Losses are large relative to typical wins. There is no stop (stoploss −0.99 by design, `H-020.json`).
  - Worst single trades by `profit_ratio`: BTC −23.4% (−2.39) and −21.0% (−2.19); ETH −51.3% (−5.11), −33.1% and −31.9%; BNB −32.7% (−3.50) and −28.8%.
  - Those losses all fall in 2018 to 2022 stretches, mostly around the 2018, 2020 and 2021 to 2022 drawdowns. The largest ETH loss is 5.1 on a 4.96 total profit.
- Exit reasons:
  - BTC: 57 `daily_high7` and 1 `force_exit` (open at the end of the data, −0.38).
  - ETH: 65 `daily_high7` and 1 `force_exit` (−1.83).
  - BNB: 64 `daily_high7` and no force exit.
  - There are no other exit types. This follows from the rule: no stop, no target and no time exit.
- Duration (`trade_duration` is in minutes in the CSVs; 1440 minutes = 1 day):
  - Most trades last 5 to 20 days (7,200 to 28,800 minutes).
  - The shortest are 1 day for ETH and BNB and 0.8 day for the BTC force exit; the longest are 36 days (51,840 minutes) for BTC and ETH and 35 days for BNB.
  - The longest trades are mostly the large losers: BTC 51,840 minutes at −23.4%, ETH 51,840 minutes at −51.3%, BNB 50,400 minutes at −28.8%.
  - I did not compute a mean or median.
- Timing: the BTC and ETH lists have no trades in 2022 and the first 2023 trades start in February. BNB has a late-2022 trade (2022-12-02, −15.9%).

## 4. Consistency across pairs, and what this does and does not show

- All three pairs are positive at all four costs, except ETH profit excluding the best trade at stress. All three pass every gate on exploration. The sign of the result is the same on each pair.
- The profile is the same across the pairs. There are many small to medium wins of a few percent each, and a handful of large winners dominate net profit. A few large losses on a no-stop rule offset part of that, and drawdown stays moderate only because exposure is 10%.
- Drawdown differs by pair (about 3.5% BTC, 11.2% ETH, 7.0% BNB at base). All are within the 25% limit.
- Buy-and-hold beat the strategy by a wide margin on every pair (+1252.66%, +929.58% and +33023.53% versus profit of 5.7, 5.0 and 7.1 on 100). The gate does not require beating it. The result is not evidence that the strategy beats holding. The strategy sits in cash most of the time, with 10% exposure.

What the numbers do not show:

- The sample is 58 to 66 trades per pair. That clears the 30-trade minimum, but profit depends on a few trades: the top 5 produce 97% to 180% of profit. The three pairs share the same signal days (several 2019 to 2021 and 2024-04-03 entries appear on all three), so they are not independent samples.
- The margin over cost is thin at the stress level, and ETH does not hold up there. Most of the cost sensitivity is that stress costs remove 60% to 83% of base profit.
- The gates are evaluated on the exploration split only. The metrics in `facts.json` say nothing about the validation split or about the tail risk of a no-stop rule outside this window.
- `facts.json` has no figures for Sharpe, the deflated Sharpe ratio, PBO or plateau tests. The proposal lists them as success criteria, so I cannot comment on them.
- The deterministic gates give `candidate_for_portfolio` on exploration for all three pairs. This note describes the numbers and does not change that verdict.
