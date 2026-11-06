# H-046 exploration: quantitative description

Sources: `research/experiments/H-046-exploration/facts.json` (metrics, gate verdicts), `crosscheck.json`, `trades-<pair>.csv`, `research/proposals/H-046.json`, `lab/config/gates.json`. Profit is in quote units on a 100 USDT starting balance (`crosscheck.json`), so 1.0 is 1% of the wallet. Max drawdown is in % of peak balance.

## 1. Per-pair results (facts.json)

Trade count is 130 / 139 / 136 (BTC / ETH / BNB) and is the same in all four cost scenarios.

### BTC/USDT (130 trades)
| Scenario | Net profit | Max drawdown % |
|---|---|---|
| optimistic | 50.60 | 5.61 |
| base | 44.78 | 6.00 |
| conservative | 39.12 | 6.44 |
| stress | 23.89 | 7.77 |

- Profit without the best trade: base 35.79, conservative 30.51, optimistic 41.23, stress 16.35.
- Benchmark: cash 0.0%, buy-and-hold +1252.66%.
- Gate verdict: `candidate_for_portfolio`. Every gate passed: lookahead, recursive, minimum trades, net profit, profit excluding best trade, drawdown.

### ETH/USDT (139 trades)
| Scenario | Net profit | Max drawdown % |
|---|---|---|
| optimistic | 51.20 | 5.68 |
| base | 45.04 | 6.06 |
| conservative | 39.12 | 6.53 |
| stress | 22.60 | 13.05 |

- Profit without the best trade: base 32.72, conservative 27.34, optimistic 38.32, stress 12.34.
- Benchmark: cash 0.0%, buy-and-hold +929.58%.
- Gate verdict: `candidate_for_portfolio`. All gates passed.

### BNB/USDT (136 trades)
| Scenario | Net profit | Max drawdown % |
|---|---|---|
| optimistic | 70.96 | 12.38 |
| base | 63.96 | 13.59 |
| conservative | 57.48 | 15.34 |
| stress | 39.34 | 20.43 |

- Profit without the best trade: base **0.73**, conservative **-3.24**, optimistic 4.94, stress **-14.24**.
- Benchmark: cash 0.0%, buy-and-hold +33023.53%.
- Gate verdict: `candidate_for_portfolio`. The profit-excluding-best-trade gate checks only the base scenario, where 0.73 is above 0. It passes by a very thin margin. The conservative and stress values are negative.

Every strategy return is far below buy-and-hold on all three pairs. The gates say beating the benchmark is not required (`lab/config/gates.json`). Exposure is reported as 0.2 for each pair.

## 2. Cost sensitivity

Derived as differences between the net_profit_quote values in facts.json.

| Pair | Optimistic to base | Optimistic to conservative | Optimistic to stress | Stress as % of optimistic |
|---|---|---|---|---|
| BTC | -5.83 | -11.48 | -26.72 | 47% |
| ETH | -6.16 | -12.08 | -28.60 | 44% |
| BNB | -7.00 | -13.48 | -31.63 | 55% |

- The proposal gives the round-trip cost as 0.35% at base and 0.95% at stress (`H-046.json` rationale). Going from optimistic to stress costs about 0.21 to 0.23 quote per trade: 26.72/130, 28.60/139 and 31.63/136. Stress costs about half the optimistic profit on each pair.
- Profit stays positive in all four scenarios on all three pairs. Aggregate edge per trade therefore covers the round-trip cost on these samples, even at the stress level.
- The margin is not large relative to cost. Cost explains a large part of the spread between scenarios. The BNB result without its best trade turns negative at conservative and stress, so there the cost buffer depends on one trade.

## 3. Concentration (derived from the trade lists)

I summed the `profit_abs` column of the largest trades by hand and divided by the stored net profit in the base scenario. No script was run, so treat the shares as hand-derived approximations. Shares can exceed 100% because the losing trades are net negative.

| Pair | Best trade (profit_abs; profit_ratio) | Top 1 share | Top 5 share | Top 10 share |
|---|---|---|---|---|
| BTC | 8.38; +32.6% (2023-01-09 entry) | about 19% (8.38 / 44.78) | about 78% (about 35.0 / 44.78) | about 118% (about 52.8 / 44.78) |
| ETH | 12.08; +46.1% (2020-07-22 entry) | about 27% (12.08 / 45.04) | about 91% (about 41.0 / 45.04) | about 152% (about 68.6 / 45.04) |
| BNB | 54.95; +314.0% (2021-02-01 entry) | about 86% (54.95 / 63.96) | about 138% (about 88.2 / 63.96) | about 173% (about 110.4 / 63.96) |

Sizing note: the stake is the whole balance, so profit_abs grows with the balance. Later trades are larger in quote terms. The `crosscheck.json` method for "excluding best trade" is therefore compounded, not a subtraction. This is why BNB falls from 63.96 to 0.73 when its one best trade is removed. The 3.14 profit_ratio of that trade also enlarged the stake of every later trade.

**Exit-reason mix and durations.** I did not tally exact counts per exit reason. These are observations from reading the CSVs. `trade_duration` is in minutes.
- Three exit reasons appear: `fail_fast_pivot`, `stop_loss` and `trail_48_low`.
- `fail_fast_pivot` exits are short, mostly 60 to 480 minutes. They lose roughly 0.6% to 3.7% per trade.
- `stop_loss` exits lose about -4.33% each. Several have zero or 60-minute durations, which means an exit within the entry hour or the next hour.
- Nearly all clear winners exit through `trail_48_low`. They hold from days to weeks, for example 31,440 minutes in the BTC best trade and 31,620 minutes in the BNB best trade. Many `trail_48_low` exits are also small losses or near-zero results.
- The overall pattern is many small and medium losses with a few large trail winners. This matches the concentration figures above.

## 4. Consistency and what this does and does not show

- **Consistency.** All three pairs are positive in all four scenarios and pass every deterministic gate. BTC and ETH look similar: about 45 base profit, 6% drawdown at base, and positive profit without the best trade at every cost level. BNB differs: higher headline profit (63.96) but higher drawdown (13.59% base, 20.43% stress), and almost all of its profit comes from one trade.
- **What the data show.** On the exploration split, profit is positive after cost on three pairs. The sample is more than 30 trades per pair, which clears the minimum. The loss per failed breakout is bounded by the fail-fast exit and the 4% stop.
- **What they do not show.**
  - Profit comes from a small number of large trend trades. The top 5 trades account for about 78% (BTC), about 91% (ETH) and about 138% (BNB) of profit, so the results depend on few events.
  - The BNB pass is thin. Without its single best trade, base profit is 0.73 and conservative and stress are negative.
  - 130 to 139 trades, of which only a few dozen are winners, is a modest sample for a payoff that depends on rare large moves.
  - The strategy returns are far below buy-and-hold on every pair, so it did not capture most of the available trend.
  - Nothing here is evidence about the validation split or later data. The gates require clearing them again there (`lab/config/gates.json`, split_progression).
  - This is a first exploration run in a new family (zero prior variants, per the net_profit reason lines in facts.json), so the multiple-testing penalty is currently at its lowest.
- The verdict is the deterministic gates' `candidate_for_portfolio` on exploration for all three pairs. This document only describes the recorded numbers and makes no recommendation.
