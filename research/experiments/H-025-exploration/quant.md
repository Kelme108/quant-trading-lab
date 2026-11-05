# H-025 exploration: quantitative reading

Sources: `research/experiments/H-025-exploration/facts.json` (metrics, verdicts), `trades-<pair>.csv` (base-scenario trades), `crosscheck.json`, `research/proposals/H-025.json`, `lab/config/gates.json`. Profit is in USDT on a 100 USDT starting balance (crosscheck.json: starting_balance 100). Shares and ratios below are my own arithmetic on the recorded numbers; the method is stated each time. The gate verdicts are the deterministic ones in facts.json.

## 1. Per-pair tables (facts.json)

Max drawdown is `max_drawdown_pct__*` (the gate reads the relative figure; for BTC and ETH the two are identical, for BNB the relative one is higher and is shown in brackets).

### BTC/USDT
| Scenario | Trades | Net profit | Max DD % |
|---|---|---|---|
| optimistic | 33 | 58.32 | 6.44 |
| base | 33 | 56.78 | 6.53 |
| conservative | 33 | 55.05 | 6.68 |
| stress | 33 | 50.60 | 7.09 |

Profit without the best trade (base, compounded per crosscheck.json): 39.93 (conservative 38.42, optimistic 41.26, stress 34.51). Benchmarks: cash 0.0%, buy-and-hold +1252.66%. Verdict: `candidate_for_portfolio`; every gate passed.

### ETH/USDT
| Scenario | Trades | Net profit | Max DD % |
|---|---|---|---|
| optimistic | 33 | 57.23 | 4.83 |
| base | 33 | 55.71 | 4.92 |
| conservative | 33 | 53.96 | 5.00 |
| stress | 33 | 49.45 | 5.24 |

Profit without the best trade (base): 38.49 (conservative 36.99, optimistic 39.85, stress 33.03). Benchmarks: cash 0.0%, buy-and-hold +929.58%. Verdict: `candidate_for_portfolio`; every gate passed.

### BNB/USDT
| Scenario | Trades | Net profit | Max DD % (relative) |
|---|---|---|---|
| optimistic | 41 | 141.44 | 6.76 (8.35) |
| base | 41 | 138.51 | 7.05 (8.54) |
| conservative | 41 | 135.35 | 7.34 (8.73) |
| stress | 41 | 126.47 | 8.26 (9.29) |

Profit without the best trade (base): 35.26 (conservative 33.56, optimistic 36.85, stress 28.65). Benchmarks: cash 0.0%, buy-and-hold +33023.53%. Verdict: `candidate_for_portfolio`; every gate passed.

Gate bars (gates.json): at least 30 trades, net profit above 1.0 USDT in base and conservative (no prior variants in the family), positive profit without the best trade in base, max drawdown at most 25% in all four scenarios. Lookahead and recursive checks reported no bias or instability on all three pairs (facts.json). Beating buy-and-hold is not required; the strategy returned far less than buy-and-hold on every pair (exposure is 0.2 in facts.json).

Note: the exploration split is this strategy's only evidence so far. gates.json says a candidate must clear the gates again on the validation split and then meet the portfolio criteria. The verdict here is therefore an exploration-stage result only.

## 2. Cost sensitivity

Derived as differences between the `net_profit_quote__*` values in facts.json.

| Pair | Optimistic minus base | Optimistic minus conservative | Optimistic minus stress | Stress as % of optimistic |
|---|---|---|---|---|
| BTC | 1.54 | 3.27 | 7.72 | 86.8% |
| ETH | 1.52 | 3.27 | 7.78 | 86.4% |
| BNB | 2.93 | 6.09 | 14.97 | 89.4% |

The trade count does not change across scenarios, so only the per-trade cost changes. Going from the optimistic to the stress cost removes about 11–14% of profit on each pair. Profit stays well above the 1.0 USDT bar at stress cost. The cost per trade is small next to the move per trade. The proposal estimates round-trip cost at 0.35–0.50% (H-025.json). Winners in the trade lists gain several percent to tens of percent (for example +57.7%, +44.1% and +43.7% on BTC), while the small winners are barely above zero (+1.1%, +1.2%, +1.4% on BTC; +0.01% on BNB). Cost is not what explains the profit here. It does take away what little edge the many marginal trades have.

## 3. Concentration (from trades-*.csv)

Method: sort `profit_abs` descending, sum the top N, divide by the net profit in the base scenario (facts.json). Shares above 100% mean the remaining trades together lost money. The trades are compounded on the whole balance, so these are shares of recorded profit, not independent contributions.

| Pair | Net profit | Best 1 | Best 5 | Best 10 |
|---|---|---|---|---|
| BTC | 56.78 | 13.26 = 23.4% | 55.23 = 97.3% | 75.89 = 133.7% |
| ETH | 55.71 | 14.28 = 25.6% | 50.54 = 90.7% | 74.87 = 134.4% |
| BNB | 138.51 | 84.71 = 61.2% | 178.43 = 128.8% | 202.42 = 146.1% |

- On all three pairs, the best five trades account for roughly all of the profit or more. The rest of the trades net to roughly zero or negative.
- BNB depends on one trade (2021-02-02 to 2021-03-25, +381%, 84.71 USDT). The excl-best figure (35.26) is far below the total (138.51). The gate is still passed because the figure is above zero.
- The excl-best numbers in facts.json are compounded (crosscheck.json): removing the best trade also removes its enlarging effect on later trades. They are lower than total minus best `profit_abs`, as expected.

Trade outcomes and exits:
- BTC: 33 trades, 16 positive. Exit reasons: 24 `close_below_ema20`, 9 `stop_loss`.
- ETH: 33 trades, 15 positive. Exit reasons: 22 `close_below_ema20`, 11 `stop_loss`.
- BNB: 41 trades, 13 positive. Exit reasons: 20 `close_below_ema20`, 21 `stop_loss`.
- Stop-loss exits all lose about 8.3%. They are short: under about 11,000 minutes (about 8 days) on BTC, with many under a day on all pairs (`trade_duration` in minutes).
- The winners are long holds. For example BTC 90,720 min (about 63 days), ETH 60,480 min (about 42 days), BNB 93,600 min (about 65 days). Many `close_below_ema20` exits are small losses of 1–7%.
- On BNB, stops are about half of all trades (21 of 41). There are several repeat stop-outs within a day or two, including three entries on 2021-10 to 2021-11 and 2024-03 to 2024-07. On BTC and ETH, some stops are re-entries within hours of a prior stop. The owner's concern about runs of stopped-out breakouts is visible in the lists (for example BNB 2020-09-13 to 2020-12-22 has five stops in a row).

## 4. Consistency and limits

- All three pairs show the same pattern: roughly 45% win rate or less (16/33, 15/33, 13/41), small drawdowns in the base case (4.9–8.5%), profit that comes from a handful of long trend trades, and a mid-sized loss for the rest. The proposal itself expected profit to rely on a few large trends (H-025.json rationale).
- The three pairs trade the same crypto trends and overlapping dates (for example winners in late 2020 to early 2021, 2023 Q1 and 2024 Q1), so this is not three independent confirmations.
- Samples are small: 33, 33 and 41 trades, only slightly above the 30-trade minimum. With the top five trades about equal to total profit, a different handful of trades would change the picture a lot. The result does not show that the edge is stable. It shows that, in this window, a few big trends paid for many small losses.
- Cost does not explain the result: profit stays high at stress cost (section 2).
- Max drawdowns are low partly because exposure is 0.2 (facts.json); they do not describe the full-exposure risk.
- All figures are from the exploration split. Nothing here speaks to the validation split or the final test.
- This is a description of the recorded numbers. The gate verdict (`candidate_for_portfolio` on all three pairs, exploration split only) is the deterministic output in facts.json, and this note makes no recommendation.
