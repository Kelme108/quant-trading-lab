# H-005 exploration: quant review

Sources: `research/experiments/H-005-exploration/facts.json` (metrics and gates), `trades-<pair>.csv` (base-scenario trades), `crosscheck.json`, `research/proposals/H-005.json`, `lab/config/gates.json`. Money is in USDT on a 100 USDT starting balance (`crosscheck.json`). Net profit of 520 therefore means +520% of the starting balance. Drawdown is a % of peak balance.

## 1. Per-pair results (`facts.json`)

All three pairs were **rejected**. Lookahead, recursive, minimum trades, net profit (base and conservative) and profit excluding the best trade all passed. Max drawdown failed in all four scenarios (gate bar: 25%, `gates.json`).

### BTC/USDT
| Scenario | Trades | Net profit | Max DD % |
|---|---|---|---|
| optimistic | 31 | 549.48 | 49.05 |
| base | 31 | 520.37 | 50.12 |
| conservative | 31 | 492.34 | 51.19 |
| stress | 31 | 415.87 | 54.27 |

- Profit without the best trade: base 129.76, optimistic 140.34, conservative 119.65, stress 91.91.
- Benchmark: cash 0.0%; buy-and-hold +1252.66%.
- Verdict: rejected, on max drawdown only.

### ETH/USDT
| Scenario | Trades | Net profit | Max DD % |
|---|---|---|---|
| optimistic | 36 | 540.67 | 49.55 |
| base | 36 | 507.24 | 50.63 |
| conservative | 36 | 475.48 | 51.68 |
| stress | 36 | 389.85 | 54.72 |

- Profit without the best trade: base 51.14, optimistic 59.29, conservative 43.41, stress 22.51.
- Benchmark: cash 0.0%; buy-and-hold +929.58%.
- Verdict: rejected, on max drawdown only.

### BNB/USDT
| Scenario | Trades | Net profit | Max DD % |
|---|---|---|---|
| optimistic | 36 | 933.09 | 42.04 |
| base | 36 | 879.15 | 42.92 |
| conservative | 36 | 827.89 | 43.80 |
| stress | 36 | 689.49 | 46.36 |

- Profit without the best trade: base 27.08, optimistic 33.93, conservative 20.58, stress 3.01.
- Benchmark: cash 0.0%; buy-and-hold +33023.53%.
- Verdict: rejected, on max drawdown only.

`crosscheck.json` shows the stored profit and the excluding-best figure match the recomputation from the trade lists for all pairs. The excluding-best figure is compounded, as `crosscheck.json` explains.

## 2. Cost sensitivity

Ratios below are my own division of the `facts.json` `net_profit_quote` values.

| Pair | Optimistic | Base | Conservative | Stress | Stress ÷ optimistic |
|---|---|---|---|---|---|
| BTC | 549.48 | 520.37 | 492.34 | 415.87 | 0.757 |
| ETH | 540.67 | 507.24 | 475.48 | 389.85 | 0.721 |
| BNB | 933.09 | 879.15 | 827.89 | 689.49 | 0.739 |

- Total profit stays positive in every scenario on every pair. In aggregate, the move captured by the winning trades covers the round-trip cost under all four assumptions.
- Moving from optimistic to stress removes roughly a quarter to a little over a quarter of profit.
- The cost effect on the total is modest next to the dependence on a few trades (section 3). Cost does not explain the drawdown failure.
- With the best trade removed, the cushion is thin at stress cost:
  - BNB 3.01 (`facts.json`, `net_profit_excl_best_trade__stress`).
  - ETH 22.51.
  - BTC 91.91.
- The stress-scenario BNB result without its best trade is nearly zero. That is where cost starts to matter.
- Cost per trade is not in the files I read, so I do not state a per-trade cost coverage figure.

## 3. Concentration, durations and exit reasons

Shares are derived from `profit_abs` in the trade CSVs. Share = sum of the N largest `profit_abs` ÷ total (the same total as the base `net_profit_quote`). Shares above 100% occur because losing trades subtract from the total. Stakes compound on a whole balance, so `profit_abs` for later trades is inflated by earlier wins. These shares therefore overstate how much later trades matter in absolute terms. The best trade is the same by `profit_ratio` and by `profit_abs`.

| Pair | Best 1 | Best 5 | Best 10 | Winners / losers |
|---|---|---|---|---|
| BTC | 408.09 → 78.4% | 997.33 → 191.7% | 1096.12 → 210.6% | 9 / 22 |
| ETH | 412.36 → 81.3% | 1175.78 → 231.8% | 1390.94 → 274.2% | 11 / 25 |
| BNB | 623.95 → 71.0% | 1343.65 → 152.8% | 1414.32 → 160.9% | 8 / 28 |

- BTC has only 9 winning trades, so its best 10 includes one loser (−7.20). BNB has only 8 winners, so its best 10 includes two losers (−1.82 and −2.69).
- Excluding the single best trade removes about 75.1% of BTC profit (520.37 → 129.76), 89.9% of ETH profit (507.24 → 51.14) and 96.9% of BNB profit (879.15 → 27.08). These are my calculations from `facts.json`.
- The best trades are:
  - BTC: 2020-10-08 to 2021-01-22, +169.6%.
  - ETH: 2020-10-09 to 2021-02-23, +301.2%.
  - BNB: 2020-12-14 to 2021-03-25, +669.8%.
  - All three come from the same 2020–21 rally.

**Exit reasons (counted from the CSVs):**

| Pair | `low336_breakdown` | `stop_loss` |
|---|---|---|
| BTC | 19 | 12 |
| ETH | 18 | 18 |
| BNB | 19 | 17 |

- Every stop-loss trade is a loss of about 8.3%, which is the 8% stop plus costs.
- All winners exit via `low336_breakdown`. Some `low336_breakdown` exits are small losses.

**Durations** (`trade_duration` is in minutes; 38940 min = 649 h, which matches the open and close timestamps):
- Winners are long holds. Every BTC winner lasted at least 38940 min (about 27 days).
- Longest and shortest trades:
  - BTC: longest 212700 min (about 148 days), shortest 1860 min (31 h).
  - ETH: longest 197100 min (about 137 days), shortest 1080 min (18 h).
  - BNB: longest 145260 min (about 101 days), shortest 240 min (4 h).
- The stop-loss trades are mostly short, from hours to a few weeks.

## 4. Consistency and what this does and does not show

- **Consistent across pairs:**
  - Net profit is positive in all four cost scenarios on all three pairs.
  - Drawdown is 42–55% on all of them, and every pair fails the 25% drawdown gate in every scenario.
  - All three show the same pattern: a low win rate (BTC 9/31, ETH 11/36, BNB 8/36), many fixed-size losses, and a few very large winners.
- **Trades overlap in time.** Entries in the same windows recur across pairs (for example 2020-07-06 on all three, and 2024-02-07 on BTC and BNB). The three pairs are therefore not independent confirmations. Profit depends on a small number of trending episodes, mainly 2020–21.
- **What it shows:** within this exploration split, the strategy was profitable after all four cost assumptions. The profit came from rare, long trend captures. The drawdown (42–55%) is far above the 25% bar.
- **What it does not show:**
  - Trade counts are 31, 36 and 36, just above the 30-trade minimum, and profit rests on 1–5 trades per pair. That is a small effective sample.
  - A positive result that depends this heavily on one trade (71–81% of profit) is not evidence of a repeatable edge.
  - The results say nothing about the validation split, which the gates require independently.
  - The proposal expected about 4–8 trades per pair per year with 8–20% winners (`H-005.json`). The recorded trades show a low win rate and a few much larger winners, with some `low336_breakdown` exits well below that range.
- **Cost does not explain the result.** The drawdown failure holds even at optimistic cost (42.0–49.6%). Cost lowers profit by roughly a quarter at stress.
- **Decision:** the deterministic gates decide, and the result is **rejected** for all three pairs (`facts.json`). This note does not alter that.
