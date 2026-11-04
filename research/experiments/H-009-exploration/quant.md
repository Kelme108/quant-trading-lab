# H-009 exploration split: quantitative read

Sources: `research/experiments/H-009-exploration/facts.json` (metrics, gate verdicts), `crosscheck.json`, `trades-<pair>.csv`, `lab/config/gates.json`.
Note: the proposal `research/proposals/H-009.json` does not exist at that path (Glob `research/proposals/H-009*` found nothing), so I could not read the stated hypothesis. Nothing below relies on it. The strategy file was not read either.
Profits are in USDT on a 100 USDT starting balance (`crosscheck.json` `starting_balance`). A "profit %" here is profit/100.

## 1. Per-pair tables (all from `facts.json`)

Gate verdict for all three pairs: `candidate_for_portfolio`. Lookahead and recursive checks passed and every minimum-trades check passed (30 required, `gates.json`). Net profit was above the 1.0 bar in base and conservative, profit excluding the best trade was above 0, and drawdown was at most 25% in all four scenarios. The proposal gives no further decision logic, so this is the gates' output only. The exploration split alone does not make a candidate (`gates.json` `split_progression`: it must clear again on validation).

### BTC/USDT
| Scenario | Trades | Net profit | Max DD % |
|---|---|---|---|
| optimistic | 58 | 118.589 | 6.83 |
| base | 58 | 113.804 | 7.20 |
| conservative | 58 | 109.017 | 7.60 |
| stress | 58 | 95.773 | 8.72 |

Profit without the best trade (base): 71.522. Other scenarios: 75.346 optimistic, 67.703 conservative, 57.164 stress.
Benchmark: cash 0.0%, buy-and-hold +1252.66%. The strategy's base return is +113.8%, from net profit 113.804 on a 100 start. Exposure is 0.25.

### ETH/USDT
| Scenario | Trades | Net profit | Max DD % |
|---|---|---|---|
| optimistic | 81 | 66.854 | 17.15 |
| base | 81 | 61.769 | 18.51 |
| conservative | 81 | 56.919 | 19.83 |
| stress | 81 | 43.174 | 23.70 |

Profit without the best trade (base): 40.344. Other scenarios: 44.734 optimistic, 36.196 conservative, 24.386 stress.
Benchmark: cash 0.0%, buy-and-hold +929.58%. Base return is +61.8%. Exposure is 0.25.

### BNB/USDT
| Scenario | Trades | Net profit | Max DD % |
|---|---|---|---|
| optimistic | 80 | 141.017 | 13.61 |
| base | 80 | 133.572 | 14.51 |
| conservative | 80 | 126.663 | 15.36 |
| stress | 80 | 107.039 | 17.87 |

Profit without the best trade (base): 25.288. Other scenarios: 29.174 optimistic, 21.620 conservative, 11.278 stress.
Benchmark: cash 0.0%, buy-and-hold +33023.53%. Base return is +133.6%. Exposure is 0.25.

The "without best trade" figures were recomputed by compounding all other trades' `profit_ratio` (`crosscheck.json`, `matches: true` for all three pairs). The stored profit also matches the trade-list sum.

## 2. Cost sensitivity

Optimistic minus stress, as a share of optimistic profit (my arithmetic on `facts.json` values):

| Pair | Optimistic | Base | Conservative | Stress | Drop optimistic→stress |
|---|---|---|---|---|---|
| BTC | 118.589 | 113.804 | 109.017 | 95.773 | 22.816 (19.2%) |
| ETH | 66.854 | 61.769 | 56.919 | 43.174 | 23.680 (35.4%) |
| BNB | 141.017 | 133.572 | 126.663 | 107.039 | 33.978 (24.1%) |

- Profit stays positive in all four scenarios on every pair. In aggregate, the average move per trade covers the modelled round-trip cost, including stress.
- ETH is the most cost-sensitive. Its stress profit is about 65% of its optimistic profit, against about 81% for BTC and about 76% for BNB.
- The cost parameters behind each scenario (fee and slippage rates) are not in the files I read, so I cannot state the cost per trade or a break-even cost.
- The movement across scenarios is modest next to total profit. The result is not explained by cost alone. Cost does take a visible share of ETH's profit.

## 3. Concentration (from `trades-<pair>.csv`, base scenario)

Method: sort `profit_abs` descending, sum the top 1, 5 and 10, and divide by the total (the sum of `profit_abs`, which equals the stored net profit). The stake is the whole balance, so profits compound. Later `profit_abs` values are therefore inflated by earlier wins, which overstates the weight of late trades in an absolute-profit share. Shares above 100% occur because the remaining trades net negative.

| Pair | Total | Top 1 | Top 5 | Top 10 |
|---|---|---|---|---|
| BTC | 113.804 | 24.539 (21.6%) | 81.275 (71.4%) | 132.374 (116.3%) |
| ETH | 61.769 | 23.212 (37.6%) | 84.194 (136.3%) | 116.911 (189.3%) |
| BNB | 133.572 | 106.592 (79.8%) | 185.186 (138.6%) | 216.384 (162.0%) |

- BNB: one trade (opened 2021-01-29, closed 2021-02-23, profit_ratio +3.45) gives about 80% of profit. Without it, profit falls from 133.572 to 25.288 (down 81%, `facts.json`). It passes the "excluding best trade > 0" gate, but the profit is very concentrated.
- BTC: dropping the best trade (the 2017-11-25 trade, +98%) cuts profit by about 37%. ETH loses about 35%.
- On all three pairs, the 10 best trades earn more than the whole total, so the many small losses and stop-outs net negative.

Exit reasons (counted from the csv):

| Pair | stop_loss | low72_or_regime_lost | Winners (profit_ratio>0) |
|---|---|---|---|
| BTC (58) | 9 | 49 | 22 (38%) |
| ETH (81) | 22 | 59 | 25 (31%) |
| BNB (80) | 22 | 58 | 25 (31%) |

- Stop-loss exits all sit at about −6.33% (profit_ratio ≈ −0.0633). Every non-stop exit is `low72_or_regime_lost`, and no other exit reasons appear.
- Duration (`trade_duration`, minutes): the longest trades are the large winners. BTC's longest is 46,080 min (about 32 days) and the +98% trade lasted 34,440 min. ETH's longest is 51,960 min (about 36 days), and BNB's longest is 35,820 min (about 25 days), which is the +345% trade. Many stop-outs and small losses last minutes to a few days, and some are 0 to 120 min. I did not compute medians.
- The pattern is a low win rate of 31–38%, with a few long trades carrying the profit.

## 4. Consistency and limits

- All three pairs are positive in every scenario, pass every gate, and have the same shape: a low win rate, fixed-size stops, and a few long winners. In that sense the result is consistent across pairs.
- Sizes differ widely: base profit is 61.8 (ETH), 113.8 (BTC) and 133.6 (BNB), and BNB's depends mostly on one trade. Drawdown ranges from 7.2% (BTC) to 18.5% (ETH) at base, and ETH reaches 23.7% at stress, close to the 25% limit.
- Every pair has far less return than buy-and-hold (+929% to +33,024%) over the same period. The strategy is exposed 25% of the time. Beating buy-and-hold is not a gate.
- The trade counts (58, 81, 80) clear the 30-trade minimum. But the profit rests on roughly 5–10 large winners per pair, and the trades cluster in the 2017–2021 bull phases (few or none in 2022 on BTC), so the effective independent sample is small. The three pairs are crypto assets that move together, so the evidence is not three independent confirmations.
- This is an exploration split, with `0 prior variant(s) in family` in the net-profit gate reasons. It shows the gates were passed here. It does not show out-of-sample performance, and validation is still required.
- It does not show that the edge persists, that it is not a few large-trend captures, or what costs are in live conditions.
