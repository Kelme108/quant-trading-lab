# H-024 exploration: quantitative review (DailyMaxJumpMomentum)

Sources: `research/experiments/H-024-exploration/facts.json` (metrics, decisions), `trades-<pair>.csv` (base trades), `crosscheck.json`, `research/proposals/H-024.json`, `lab/config/gates.json`. Net profit is in quote currency on a 100 USDT start (`crosscheck.json`: starting_balance 100.0). Shares and ratios marked "derived" are my arithmetic on those files. The deterministic gates decide; this file only describes.

## 1. Per-pair tables

Source for all cells: `facts.json`, `pairs.<pair>.metrics`. Drawdown is `max_drawdown_pct__<scenario>`. Profit without the best trade is `net_profit_excl_best_trade__<scenario>` (compounded recomputation, method in `crosscheck.json`; it matched for all three pairs).

### BTC/USDT (43 trades in every scenario)
| Scenario | Net profit | Max DD % | Profit excl. best trade |
|---|---|---|---|
| optimistic | 102.61 | 10.40 | 67.96 |
| base | 99.31 | 10.78 | 65.38 |
| conservative | 95.96 | 11.12 | 62.61 |
| stress | 86.68 | 12.24 | 54.95 |

Benchmarks: cash 0.0%, buy-and-hold +1252.66%. Gate verdict: `candidate_for_portfolio`; all listed gates pass (lookahead, recursive, trades >= 30, net profit > 1.0 at base and conservative, profit excl. best trade > 0, DD <= 25%).

### ETH/USDT (36 trades in every scenario)
| Scenario | Net profit | Max DD % | Profit excl. best trade |
|---|---|---|---|
| optimistic | 46.49 | 5.55 (relative 6.10) | 24.43 |
| base | 44.53 | 5.61 (relative 6.23) | 22.80 |
| conservative | 42.59 | 5.67 (relative 6.37) | 21.19 |
| stress | 36.91 | 6.79 | 16.49 |

Benchmarks: cash 0.0%, buy-and-hold +929.58%. Gate verdict: `candidate_for_portfolio`. The gate reasons use the relative drawdown figures (6.10 / 6.23 / 6.37 / 6.79).

### BNB/USDT (39 trades in every scenario)
| Scenario | Net profit | Max DD % | Profit excl. best trade |
|---|---|---|---|
| optimistic | 194.22 | 6.48 (relative 11.44) | 59.16 |
| base | 189.69 | 6.59 (relative 11.70) | 56.75 |
| conservative | 185.48 | 6.69 (relative 11.96) | 54.51 |
| stress | 172.63 | 7.00 (relative 12.74) | 47.81 |

Benchmarks: cash 0.0%, buy-and-hold +33023.53%. Gate verdict: `candidate_for_portfolio`. The gate reasons use the relative drawdown figures.

Context: `facts.json` shows exposure 0.25 on all pairs, and the benchmark comparison is reported but not required to be beaten (`gates.json` benchmark_comparison). In every pair, buy-and-hold return is far above the strategy's net profit. Buy-and-hold is a different return basis (full exposure, whole period), so I only report the gap and do not rank on it. This is the exploration split only. `gates.json` split_progression requires the validation split to be cleared independently before a candidate can enter a portfolio.

## 2. Cost sensitivity

Derived from the net profit rows above (`facts.json`).

| Pair | Optimistic | Base | Conservative | Stress | Stress as % of optimistic (derived) |
|---|---|---|---|---|---|
| BTC | 102.61 | 99.31 | 95.96 | 86.68 | 84.5% |
| ETH | 46.49 | 44.53 | 42.59 | 36.91 | 79.4% |
| BNB | 194.22 | 189.69 | 185.48 | 172.63 | 88.9% |

- Going from optimistic to stress removes about 15.9 (BTC), 9.6 (ETH) and 21.6 (BNB) quote of profit (derived by subtraction). Across 43, 36 and 39 trades, that is roughly 0.37, 0.27 and 0.55 quote per trade.
- Profit stays positive in every scenario on every pair. The result is not explained by cost within the scenarios tested: the strategy trades only 36 to 43 times in the window, so even the stress scenario costs less than a quarter of the optimistic-cost profit on each pair.
- The per-scenario fee and slippage assumptions are not in the files I read, so I cannot state the round-trip cost in percent. What the files do show is that the average gross move per trade is well above the cost difference between scenarios. Many individual trades are small, though. For example, BTC trades 2019-02-09 and 2019-03-08 return about +1.2% and +1.1% (`trades-btc-usdt.csv`), and ETH 2019-10-28 returns +0.24% (`trades-eth-usdt.csv`). Trades of this size are comparable to a plausible round-trip cost, and I did not model that here.
- The proposal expected winners of 10 to 30% against a 0.35 to 0.5% round-trip cost and a hit rate under 50% (`H-024.json` rationale). The base trade lists agree on hit rate (see section 3).

## 3. Concentration, duration, exit reasons

Shares are derived: sum of the N largest `profit_abs` in the trade CSV divided by the pair's base net profit (`facts.json`). Because the trades compound on a growing balance (`crosscheck.json`), later trades are larger in quote terms, so these shares are not a pure per-trade comparison. A share above 100% means the remaining trades net negative.

| Pair | Total (base) | Best 1 | Best 5 | Best 10 |
|---|---|---|---|---|
| BTC | 99.31 | 30.46 = 30.7% | 98.53 = 99.2% | 138.38 = 139.3% |
| ETH | 44.53 | 17.66 = 39.7% | 57.87 = 130.0% | 80.17 = 180.0% |
| BNB | 189.69 | 94.71 = 49.9% | 232.53 = 122.6% | 260.68 = 137.4% |

- Removing the best trade (compounded, `facts.json`) leaves 65.38 of 99.31 on BTC (about 66%), 22.80 of 44.53 on ETH (about 51%) and 56.75 of 189.69 on BNB (about 30%). The gate only requires this to be > 0, and it is.
- In all three pairs the five best trades account for about the whole profit or more. The remaining trades net to zero or negative. BNB is the most concentrated: the 2021-02-02 trade (+338%, 94.71) and the 2021-03-30 trade (+115%, 57.45) are 80% of its base profit (derived: 152.16/189.69). Both fall inside the early-2021 rally.
- Hit rate (counted from the CSVs): BTC 22 winners of 43 (51%), ETH 18 of 36 (50%), BNB 15 of 39 (38%).
- Exit reasons (`trades-<pair>.csv`, `exit_reason`):
  - BTC: 42 `close_below_sma20`, 1 `stop_loss`.
  - ETH: 29 `close_below_sma20`, 7 `stop_loss`.
  - BNB: 29 `close_below_sma20`, 9 `stop_loss`, 1 `force_exit` (2024-07-20, the end of the window, -5.5%).
  - Stop-loss trades all return about -12.3%. These are the largest per-trade losses, and on BNB a few of them also come in at larger quote size late in the run (for example -9.54 on 2024-04-11 and -7.99 on 2022-11-05).
- Duration (`trade_duration` in minutes; 1440 = 1 day):
  - BTC: 1 to 62 days.
  - ETH: 0.2 to 50 days.
  - BNB: 1 to 53 days.
  - The large winners are the long holds. The five largest BTC winners last 23 to 62 days (33120 to 89280 minutes). The BNB trades of 2021-02-02 and 2021-03-30 last 33 and 44 days, and the 2024-02-09 trade lasts 53 days.
  - Losers are mostly short, with many held 1 to 7 days.

## 4. Consistency across pairs, and what this does and does not show

- All three pairs pass every listed gate in all four cost scenarios, with 36 to 43 trades each, so the pairs agree on the gate verdict. All three profit curves are positive at stress cost.
- The shape of the result is the same on each pair: a roughly even or sub-even hit rate, many small losers, and a handful of long trend trades that carry the profit. The result therefore rests on a few multi-week trends (the 2019, 2020 to 2021 and early-2024 runs recur as the top trades across pairs, per the open dates in the CSVs). It is not a steady stream of positive trades.
- Profit excluding the best trade is positive, but the top 5 trades exceed 100% of profit on all pairs and the top 10 exceed 100% on all pairs. The remaining trades together lose money.
- Because the trades on the three pairs are on overlapping dates (several open on the same days, for example 2020-01-07 on all three pairs and 2024-02 on BNB and ETH), I treat the three pairs as correlated observations, not three independent confirmations. I did not compute a correlation.
- What the numbers show: under the recorded cost scenarios the strategy had positive net profit and drawdown within the 25% limit on exploration BTC, ETH and BNB, and the gate script returned `candidate_for_portfolio` for each pair.
- What they do not show:
  - Anything about the validation split or the final test (not read).
  - That the profit is anything but a few large trend captures. Each pair's trade count of 36 to 43 clears the 30-trade minimum but is a small sample for a strategy whose profit sits in about 5 trades.
  - Any multiple-testing or robustness measure (DSR, PBO, plateau, Sharpe vs. buy-and-hold at 2x costs) named in the proposal's success criteria. None of these is in the files I read.
  - Superiority to buy-and-hold: the strategy's profit is far below buy-and-hold on every pair in the same period (section 1), though the gates do not require it to be higher.
- Cost does not explain the result at the scenarios tested (section 2), and I make no claim beyond that, since the per-scenario cost values were not in the files read.
