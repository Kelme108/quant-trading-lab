# H-008 exploration: quantitative description

Sources: `research/experiments/H-008-exploration/facts.json` (metrics and verdicts), `crosscheck.json`, `trades-<pair>.csv`, and `lab/config/gates.json` (bars). The proposal `research/proposals/H-008.json` does not exist (the read failed and a glob for `research/proposals/H-008*` found nothing). I therefore describe nothing about the stated hypothesis. I did not read `validator.md`.

Profit is in quote currency (USDT) on a 100 USDT start (`crosscheck.json`: `starting_balance` 100.0). So a profit of 78 means about +78%. Each trade uses the whole balance (`crosscheck.json`, `excl_best_method`).

## 1. Per-pair tables (`facts.json`)

Cells show net profit / max drawdown %.

### BTC/USDT
| Scenario | Trades | Net profit / Max DD % |
|---|---|---|
| optimistic | 31 | 80.30 / 11.75 |
| base | 31 | 78.34 / 12.20 |
| conservative | 31 | 77.07 / 12.47 |
| stress | 31 | 71.92 / 13.56 |

- Profit without the best trade (base): 33.19. Optimistic 34.61, conservative 32.16, stress 28.48.
- Benchmark: cash 0.0%, buy-and-hold +1252.66%.
- Verdict: `candidate_for_portfolio`. All listed gates pass: lookahead, recursive, trades ≥30, net profit above 1.1 in base and conservative, ex-best profit above 0, drawdown ≤25%.

### ETH/USDT
| Scenario | Trades | Net profit / Max DD % |
|---|---|---|
| optimistic | 36 | 89.61 / 12.14 |
| base | 36 | 87.35 / 12.51 |
| conservative | 36 | 85.48 / 12.87 |
| stress | 36 | 79.52 / 13.92 |

- Profit without the best trade (base): 16.88. Optimistic 18.19, conservative 15.74, stress 12.13.
- Benchmark: cash 0.0%, buy-and-hold +929.58%.
- Verdict: `candidate_for_portfolio`.

### BNB/USDT
| Scenario | Trades | Net profit / Max DD % (relative DD, which the gate used) |
|---|---|---|
| optimistic | 36 | 174.67 / 12.93 |
| base | 36 | 171.54 / 13.16 |
| conservative | 36 | 168.40 / 13.39 |
| stress | 36 | 159.77 / 14.08 |

- `max_drawdown_pct` is lower (10.02 / 10.30 / 10.56 / 11.35). The gate reasons quote the relative figures above.
- Profit without the best trade (base): 15.96. Optimistic 17.25, conservative 14.67, stress 11.17.
- Benchmark: cash 0.0%, buy-and-hold +33023.53%. That figure is very large and I cannot explain it from these files.
- Verdict: `candidate_for_portfolio`.

Other recorded facts for all three pairs:
- Exposure is 0.2.
- Lookahead has no bias and the recursive check is stable.
- The net-profit bar is 1.1, which is 1.0 × (1 + 0.1 × 1 prior variant).
- This is the exploration split only. `gates.json` (`split_progression`) says a candidate must also clear the validation split independently.

## 2. Cost sensitivity (derived from `facts.json`)

| Pair | Optimistic | Stress | Drop (opt − stress) | Drop as % of optimistic |
|---|---|---|---|---|
| BTC | 80.30 | 71.92 | 8.38 | 10.4% |
| ETH | 89.61 | 79.52 | 10.08 | 11.3% |
| BNB | 174.67 | 159.77 | 14.91 | 8.5% |

- Going from optimistic to base costs about 2 to 3 quote units per pair (BTC 1.96, ETH 2.25, BNB 3.14). Base to conservative costs about 1 to 3 more. These are subtractions of the `facts.json` values.
- Trade counts are identical across scenarios, so cost only reduces per-trade profit.
- Cost shaves roughly a tenth off total profit and does not turn any pair negative. On these numbers the cost is not what explains the positive result.
- The result is carried by a few very large winners (section 3), so the average move per trade covers cost mainly because of those trades. The typical trade does not: most trades are losers or small winners, with 12 to 17 stop-outs per pair.
- I read no fee or slippage values, so I cannot state the cost per round trip in percent.

## 3. Concentration (derived from `trades-<pair>.csv`, using `profit_abs` against the sum of `profit_abs`)

Shares are simple sums of `profit_abs` divided by the total. They are not the compounded ex-best method, so shares above 100% are possible. The totals match `crosscheck.json`.

| Pair | Total | Winning trades | Best 1 | Best 5 | Best 10 |
|---|---|---|---|---|---|
| BTC | 78.34 | 9 of 31 | 44.13 = 56% | 109.11 = 139% | 122.12 = 156% |
| ETH | 87.35 | 15 of 36 | 65.97 = 76% | 123.44 = 141% | 152.27 = 174% |
| BNB | 171.54 | 8 of 36 | 141.01 = 82% | 213.79 = 125% | 225.85 = 132% |

- Best-5 and best-10 shares above 100% mean the remaining trades sum to a net loss.
- Compounded ex-best profit falls from 78.34 to 33.19 for BTC, 87.35 to 16.88 for ETH, and 171.54 to 15.96 for BNB (`facts.json`, base). It stays positive, so the gate passes. But for BNB and ETH roughly 80 to 90% of base profit disappears when one trade is removed.
- The best trades are very long holds:
  - BTC: 2020-10-08 to 2021-01-22 and 2019-02-19 to 2019-07-16.
  - ETH: 2020-10-09 to 2021-02-23.
  - BNB: 2020-12-14 to 2021-03-25.
  - `trade_duration` is in minutes, which is consistent with the dates.
  - Several of these hold windows overlap the late-2020 to early-2021 period.

Exit-reason mix (counts from the CSVs):

| Pair | `stop_loss` | `low336_breakdown` |
|---|---|---|
| BTC | 12 | 19 |
| ETH | 18 | 18 |
| BNB | 17 | 19 |

- Stop-loss exits are all about −8.3% (profit_ratio around −0.0832).
- `low336_breakdown` exits are mixed. They include every large winner and also many small losses of about −0.5% to −7%.
- Stop-losses are generally shorter holds than the big winners. Some durations are only about 1 to 4 hours, for example BNB 240 minutes and ETH 1080 minutes.
- The pattern is many small stopped-out or breakdown losses and a few huge, long trend holds.

## 4. Consistency and what this does and does not show

- Direction is consistent: all three pairs are positive in all four cost scenarios, with drawdown of about 10 to 14%. The shape is also consistent: low win rate (9/31, 15/36, 8/36) and profit dominated by a few trades in the same stretch of history, 2019 to early 2021 plus 2024.
- The three pairs are not independent evidence. The large winners cluster in the same bull period, and the 8.3% stop and the exit rule are shared. This looks like one effect seen three times.
- Benchmark: the strategy's return is far below buy-and-hold on every pair (for example BTC 78% against 1253%). It was out of the market most of the time (exposure 0.2). Beating it is not required by the gates, and the comparison is only reported.
- Sample: 31 to 36 trades each, just over the minimum of 30. The profit rests on 1 to 2 trades per pair, which is a very small effective sample. The pass on profit-excluding-best-trade only requires a value above 0.
- Cost does not explain the result (section 2). Concentration in a few trades does limit what it shows.
- The deterministic gates give `candidate_for_portfolio` for all three pairs on the exploration split. This describes that outcome. It is not a validation-split result, and nothing here measures how the strategy would behave outside the sampled history.
