# H-007 exploration: quantitative review

Sources: `research/experiments/H-007-exploration/facts.json` (metrics, gate reasons), `crosscheck.json` (trade-list totals match stored totals for all three pairs), `trades-<pair>.csv` (base scenario), `research/proposals/H-007.json`, `lab/config/gates.json`. Start balance is 100 USDT (crosscheck.json). Profit is in USDT. Shares and counts marked "derived" are my own arithmetic on the trade CSVs, using `profit_abs`.

## 1. Per-pair results (facts.json)

Cells show net profit / max drawdown %.

### BTC/USDT
| Item | Value |
|---|---|
| Trades (all 4 scenarios) | 23 |
| Optimistic | 586.11 / 35.68% |
| Base | 563.30 / 36.75% |
| Conservative | 541.56 / 37.81% |
| Stress | 479.69 / 40.90% |
| Profit without best trade (base; stress) | 144.75; 114.48 |
| Benchmark | cash 0.0%; buy-and-hold 1252.66% |
| Verdict | **rejected**. Recursive FAIL; drawdown FAIL in all 4 scenarios; trades 23 < 30 (inconclusive); lookahead, net profit and ex-best-trade pass |

### ETH/USDT
| Item | Value |
|---|---|
| Trades | 27 |
| Optimistic | 347.07 / 43.69% |
| Base | 329.51 / 44.72% |
| Conservative | 312.69 / 45.73% |
| Stress | 265.91 / 48.67% |
| Profit without best trade (base; stress) | 43.40; 22.69 |
| Benchmark | cash 0.0%; buy-and-hold 929.58% |
| Verdict | **rejected**. Drawdown FAIL in all 4 scenarios; trades 27 < 30 (inconclusive); lookahead, recursive, net profit and ex-best-trade pass |

### BNB/USDT
| Item | Value |
|---|---|
| Trades | 36 |
| Optimistic | 177.89 / 23.87% |
| Base | 163.34 / 25.13% |
| Conservative | 149.53 / 26.42% |
| Stress | 111.97 / 30.98% |
| Profit without best trade (base; stress) | -45.83; -56.09 |
| Benchmark | cash 0.0%; buy-and-hold 33023.53% |
| Verdict | **rejected**. Lookahead FAIL (has_bias=True); recursive FAIL; ex-best-trade FAIL; drawdown FAIL in base, conservative and stress (pass only in optimistic, 23.87% ≤ 25%); trade count passes (36 ≥ 30) |

The ex-best-trade figure is compounded: the best trade by `profit_ratio` is removed and the rest are re-compounded (method in crosscheck.json).

## 2. Cost sensitivity

Derived from facts.json net profits, comparing each scenario with optimistic:

| Pair | Opt → Base | Opt → Conservative | Opt → Stress |
|---|---|---|---|
| BTC | -22.81 (-3.9%) | -44.55 (-7.6%) | -106.42 (-18.2%) |
| ETH | -17.55 (-5.1%) | -34.38 (-9.9%) | -81.15 (-23.4%) |
| BNB | -14.55 (-8.2%) | -28.36 (-15.9%) | -65.92 (-37.1%) |

- Profit stays positive in every scenario on every pair. Cost alone does not turn the result negative, so the average move per trade does cover the round-trip cost on a total basis. The files I read do not state the per-scenario fee and slippage rates, so I cannot say by how many percentage points.
- The cost dependence grows from BTC to ETH to BNB. For BNB, stress removes 37% of optimistic profit, and the profit excluding the best trade is already negative (-42.91 optimistic, -45.83 base). Without that one trade, even the cheapest cost scenario loses money. The profit on BNB therefore does not come from a broad per-trade edge that covers cost.
- For BTC and ETH, ex-best-trade profit shrinks faster under stress than total profit. BTC: 152.96 optimistic → 114.48 stress (-25.2%). ETH: 49.10 → 22.69 (-53.8%). ETH without its best trade has little margin left under stress.
- The drawdown ceiling failure is not a cost effect. BTC and ETH exceed 25% even in the optimistic scenario (35.68%, 43.69%).

## 3. Concentration (derived from the trade CSVs, base scenario)

Share = sum of the N largest `profit_abs` values ÷ total net profit (facts.json base). Shares above 100% mean the remaining trades lost money in net.

| Pair | Total | Best 1 | Best 5 | Best 10 | Winners / trades |
|---|---|---|---|---|---|
| BTC | 563.30 | 365.75 → 64.9% | 864.40 → 153.5% | 971.76 → 172.5% | 8 / 23 (34.8%) |
| ETH | 329.51 | 240.90 → 73.1% | 654.44 → 198.6% | 652.68 → 198.1% | 6 / 27 (22.2%) |
| BNB | 163.34 | 211.93 → 129.7% | 419.21 → 256.7% | 440.56 → 269.7% | 8 / 36 (22.2%) |

- The ETH best-10 sum is slightly lower than best-5 because only 6 trades are positive, so ranks 7 to 10 are small losses.
- BNB's best trade (2021-02-01 to 2021-03-25, profit_ratio 3.86) is larger than the entire net profit. BTC's best (2020-10-10 to 2021-01-21, ratio 1.71) is about two thirds of it.
- ETH's two largest winners, 2020-11-17 (ratio 1.99) and 2021-04-02 (0.62), together give 464.87 of 329.51 net. They are both in the 2020–2021 bull market.

**Exit-reason mix** (counted from the CSVs):

| Pair | stop_loss | low240_or_regime_lost |
|---|---|---|
| BTC | 11 | 12 |
| ETH | 13 | 14 |
| BNB | 19 | 17 |

- Stop-loss exits all close at about -6.33% (profit_ratio ≈ -0.0633, which is the 6% stop plus cost).
- The channel/regime exits include every large winner, but also many small losers (for example BTC -5.4%, ETH -4.2%, BNB -5.2%).

**Duration** (`trade_duration` is in minutes, so 1440 = 1 day):
- Winners are long. BTC's winners run from 22,980 min (about 16 days) to 149,520 min (about 104 days). ETH's run from 38,760 min to 140,640 min, apart from one 31,200-min winner. BNB's best two run 75,000 and 60,060 min (52 and 42 days).
- Stop-loss trades are short, mostly under about 10 days. Examples are BTC 240 and 360 min, ETH 780 min, and BNB 420 min.
- Several exits in each pair are within one day, e.g. BTC 2023-03-14 and 2023-03-22 (240–360 min).

**Time clustering** (from open dates):
- Trades come in clusters. Losing streaks are visible in 2023 for BTC (stop-loss entries from 2023-01-29 to 2023-04-20, 7 straight losses, ending with a regime-lost exit at -5.4%, then another stop in July).
- ETH has 4 straight stop-losses in Oct–Nov 2021 and 3 more in Feb–Mar 2023. It then has further small losses in 2023.
- BNB has 6 stop-losses in 2019 (Apr–Jun) and a further run in 2020.
- All three pairs have large profits only in the 2019–2021 and early-2024 trend phases. This is the type of loss streak the proposal said the regime gate should prevent.

## 4. Consistency across pairs and what this does and does not show

**Consistent across pairs:**
- All three pairs are rejected.
- All have positive net profit in all four cost scenarios, and all have a win rate between 22% and 35%.
- All depend heavily on a few trades from the 2019–2021 and 2024 bull phases. For all three, the top 5 trades are more than 150% of total profit.
- Max drawdown is above the 25% bar in the base scenario on all three: BTC 36.75%, ETH 44.72%, BNB 25.13%. BNB only just misses.

**Not consistent:**
- BNB fails lookahead and ex-best-trade; BTC and BNB fail recursive; ETH passes both integrity gates.
- BNB is the only pair with at least 30 trades.

**What it shows:**
- The proposal's own drawdown arithmetic (a streak of 3–4 losses, about 18–24%) did not hold in the data. Streaks of 5 to 7 stops or small losses happen, as in the BTC 2023 sequence, and the drawdowns run well above the ceiling.
- The proposal's expectation that trades would be rare enough to make cost small is partly met, since profit stays positive under stress. It does not show that the edge is broad.

**What it does not show:**
- BTC (23) and ETH (27) are below the 30-trade minimum (facts.json), so the gates class them as inconclusive on that count. They are also rejected on drawdown, so the sample size does not rescue them. With 6 to 8 winners per pair, the profit rests on a handful of events, and any statistic from so few winners is fragile.
- Nothing here is a validation-split result. This is the exploration split only.
- For BNB, the lookahead bias flag means its trade list is not reliable as evidence in any case. The positive total there is explained by a single trade (ex-best is negative in all scenarios), not by a repeatable edge.
- The buy-and-hold figures are far larger than the strategy returns in the same period (BTC 1252.66% vs profit of 563.30 on a 100 start, which is 563.30%; ETH 929.58% vs 329.51%; BNB 33023.53% vs 163.34%). Beating the benchmark is not required by gates.json, but the strategy captured only part of the move while still suffering drawdowns of 25–49%.

**Gate result:** all three pairs are `rejected` by the deterministic gates (facts.json). This review describes the numbers only and does not change that decision.
