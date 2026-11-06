# H-047 exploration – quant read-out

Sources: `research/experiments/H-047-exploration/facts.json` (metrics and gate verdicts), `trades-<pair>.csv` (base scenario), `crosscheck.json`, `research/proposals/H-047.json`, `lab/config/gates.json`. Profits are in quote units on a 100 USDT starting balance (`crosscheck.json`: starting_balance 100), so they read as % of the start. Drawdowns are in %. This note describes the recorded numbers. The deterministic gates decide.

## 1. Per-pair tables (facts.json, `pairs.<pair>.metrics`)

### BTC/USDT
| Scenario | Trades | Net profit | Max DD % |
|---|---|---|---|
| optimistic | 174 | 28.88 | 6.65 |
| base | 174 | 22.27 | 7.99 |
| conservative | 174 | 16.06 | 9.44 |
| stress | 174 | -0.63 | 13.79 |

- Profit without the best trade: optimistic 23.45, base 17.15, conservative 11.23, stress -4.64.
- Benchmark: cash 0.0%, buy-and-hold +1252.66%.
- Gate verdict: `candidate_for_portfolio`. Every listed gate passed (lookahead, recursive, ≥30 trades, net profit in base and conservative, excl-best base, drawdown ≤25% in all four scenarios).

### ETH/USDT
| Scenario | Trades | Net profit | Max DD % |
|---|---|---|---|
| optimistic | 223 | 23.75 | 7.35 (relative 7.41) |
| base | 223 | 15.83 | 8.00 (relative 8.62) |
| conservative | 223 | 8.28 | 10.00 |
| stress | 223 | -11.32 | 14.05 |

- Profit without the best trade: optimistic 16.68, base 9.23, conservative 2.19, stress -16.16.
- Benchmark: cash 0.0%, buy-and-hold +929.58%.
- Gate verdict: `candidate_for_portfolio`. The decision_reasons cite the relative drawdown (8.62% base), which is slightly above the plain max drawdown.

### BNB/USDT
| Scenario | Trades | Net profit | Max DD % |
|---|---|---|---|
| optimistic | 211 | 93.07 | 8.67 |
| base | 211 | 81.29 | 9.60 |
| conservative | 211 | 70.17 | 10.58 |
| stress | 211 | 40.57 | 15.19 |

- Profit without the best trade: optimistic 66.03, base 55.93, conservative 46.34, stress 21.05.
- Benchmark: cash 0.0%, buy-and-hold +33023.53%.
- Gate verdict: `candidate_for_portfolio`.

The gates require no benchmark win (`gates.json`, benchmark_comparison). The strategy is far below buy-and-hold on all three pairs. The metrics show exposure 0.2 for each pair. The "excl. best trade" figures are compounded recomputations, not total minus the best trade's profit (`crosscheck.json` excl_best_method). `crosscheck.json` reports all three matching the stored values.

## 2. Cost sensitivity

Numbers from facts.json. Differences are my subtraction.

| Pair | Opt → Base | Base → Cons | Cons → Stress | Base → Stress |
|---|---|---|---|---|
| BTC | -6.61 | -6.21 | -16.69 | -22.90 |
| ETH | -7.92 | -7.54 | -19.61 | -27.15 |
| BNB | -11.79 | -11.11 | -29.60 | -40.72 |

- Base round-trip cost is 0.35% and stress is 0.95% (`research/proposals/H-047.json`, rationale). I did not check the scenario cost definitions elsewhere.
- Average net profit per trade at base (net profit ÷ trades, simple division, ignoring compounding) is about 0.13 for BTC (22.27/174), 0.07 for ETH (15.83/223) and 0.39 for BNB (81.29/211). That is, a fraction of a percent of the start per trade, about the same size as the 0.35% round-trip cost.
- BTC and ETH turn negative at stress (-0.63 and -11.32). For BTC the base-to-stress loss (22.90) is larger than the whole base profit. The margin over cost is thin there and mostly consumed by the stress cost.
- ETH is close to zero at conservative with the best trade removed (2.19). BNB stays positive in every scenario, including stress with the best trade removed (21.05).
- On BTC and ETH, the result depends on the cost assumption. The average move per trade covers a 0.35–0.6% round trip only slightly, and does not cover the stress cost. BNB's average per-trade move covers all four.

## 3. Concentration (derived from the trade CSVs)

Method: sort `profit_abs` descending and sum the top 1, 5 and 10. Divide by the base net profit from facts.json. Shares can exceed 100% because the losing trades subtract. Because the stake is the whole balance, later trade sizes depend on earlier results, so these are approximate shares of the quote total.

| Pair | Net profit (base) | Top 1 | Top 5 | Top 10 |
|---|---|---|---|---|
| BTC | 22.27 | 4.34 → 19.5% | 17.96 → 80.7% | 30.37 → 136.4% |
| ETH | 15.83 | 6.30 → 39.8% | 23.04 → 145.6% | 38.01 → 240.2% |
| BNB | 81.29 | 24.93 → 30.7% | 71.69 → 88.2% | 100.41 → 123.5% |

- Top-5 trades make up 81–146% of profit and the top 10 make up 123–240%. The rest of the trades together are net negative on each pair. This is a few large winners offsetting many small and moderate losers.
- ETH: the top 5 alone are 146% of profit. Its best trade (2022-07-14, about +30.1%) is 39.8% of profit.
- BNB: the three largest trades are +80.0% (2017-12-24), +81.1% (2021-02-17) and +49.5% (2017-12-15), all in the 2017–2021 run-ups. BNB's profit is mainly those 2017–2021 trades.

Exit-reason mix (hand-counted from the `exit_reason` column; treat as approximate):

| Pair | stop_loss | ratio_weak_or_regime_lost | force_exit |
|---|---|---|---|
| BTC | 12 of 174 | 162 | 0 |
| ETH | 27 of 223 | 196 | 0 |
| BNB | 28 of 211 | 182 | 1 |

- Stop-loss trades are all about -6.33% (profit_ratio ≈ -0.0633). Winners come almost entirely from the ratio/regime exit.
- Duration (`trade_duration`, minutes): there is a wide spread. Several trades last 0–60 minutes, mostly losers at the stop or small ratio-exit losses. The largest winners last about 2–6 days (for example BTC 8160 min, 2023-06-19, +15.6%). I did not compute medians or histograms.

## 4. Consistency and limits

- All three pairs pass every gate in facts.json, and all three are positive at optimistic, base and conservative. Sign and rank are consistent: BNB > BTC > ETH in profit, and drawdowns are 8–10% base on all of them.
- The agreement is not as strong as it looks:
  - Two of the three pairs (BTC, ETH) are negative at stress, and ETH's profit excluding the best trade is only 2.19 at conservative.
  - BNB supplies most of the evidence. Its buy-and-hold is +33,023% and its three largest trades are 2017–2021 moves.
  - The three pairs are not independent. Each pair's signal uses the other two as its basket (`H-047.json` ex_ante_rule), so they share the same history and market regimes.
  - Pair profit is concentrated: the top 5 trades are 81–146% of base profit.
- Trade count is not small: 174, 223 and 211, all above the 30-trade bar (`gates.json`). This is one exploration split (about 2017–2024), so it shows nothing about out-of-sample behaviour. `gates.json` requires the validation split to be cleared independently.
- It shows: with a 0.35% round-trip cost, the rule had positive net profit on all three pairs in this split, with drawdown ≤15.2% in every scenario. It does not show that the edge survives higher costs (BTC and ETH do not), that it comes from relative-strength persistence rather than a few large trends, or that it holds out of sample. The proposal states the edge is a hypothesis.
- The strategy returned a small fraction of buy-and-hold on every pair. This note makes no trading recommendation. The gate output in facts.json is the decision record.
