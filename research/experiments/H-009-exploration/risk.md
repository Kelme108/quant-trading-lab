# Risk assessment: H-009 (exploration split)

Sources: `research/experiments/H-009-exploration/facts.json`, `trades-btc-usdt.csv`, `trades-eth-usdt.csv`, `trades-bnb-usdt.csv`, `lab/config/gates.json`, `lab/config/portfolio.json`.

Limits of this review:
- `research/proposals/H-009.json` does not exist. The proposals directory holds only H-004, H-005, H-006 and H-007. I could not check the stated rationale, the family, or the intended exposure.
- Only the exploration split was reviewed. The portfolio rules require the validation split as well (`lab/config/portfolio.json`, `required_splits`).
- I did not read `lab/config/scenarios.json`. I don't know what fee and slippage values each cost scenario uses, so I can't convert scenarios into cost-per-trade figures.
- My streak and date figures were counted by hand from the CSVs. Treat them as approximate. The drawdown percentages come from `facts.json`.

## 1. Drawdown

Gate ceiling: 25% in every cost scenario (`gates.json`, `max_drawdown.max_ratio` 0.25).

| Pair | Optimistic | Base | Conservative | Stress | Room to 25% at stress |
|---|---|---|---|---|---|
| BTC/USDT | 6.83% | 7.20% | 7.60% | 8.72% | 16.3 pts |
| ETH/USDT | 17.15% | 18.51% | 19.83% | 23.70% | 1.3 pts |
| BNB/USDT | 13.61% | 14.51% | 15.36% | 17.87% | 7.1 pts |

All cells pass. ETH at stress, 23.70%, is the closest to the ceiling. Going from optimistic to stress adds about 6.5 points of drawdown on ETH, 4.3 on BNB and 1.9 on BTC.

Worst losing stretches, from the trade lists (profit_abs summed; `trade_duration` is in minutes):
- **BTC:** 9 consecutive losing trades from 2021-03-30 to 2021-09-18, about 172 days, summing to roughly -11.7. Another cluster ran 2024-01-02 to 2024-01-31 (two stop-losses plus a small loss, roughly -7.1). BTC has no trades at all between 2021-11-16 and 2023-01-20.
- **ETH:** 14 consecutive losing trades from 2021-11-08 to 2023-04-09, about 17 months, summing to roughly -20.7. Earlier, 6 of 7 trades from 2021-02-09 to 2021-03-15 lost (about -14.3 over about 34 days). The long stretch is consistent with the 18.5% base drawdown, but I did not rebuild the equity curve to confirm it.
- **BNB:** 11 consecutive losing trades from 2021-11-25 to 2023-02-09, about 14.5 months, summing to roughly -23.9. Before that, 2021-04-21 to 2021-10-27 was mostly losing, with 5 stop-losses of about -4 each.

The stop-loss exit is a near-constant -6.33% per trade (`exit_reason` = `stop_loss`). Because of that, strings of stops cause the drawdowns, and the 2021–2023 stretches are the longest. After 2021 the profit-taking trades are mostly small, so recovery is slow.

## 2. Cost sensitivity

Net profit (quote currency, `facts.json`), by scenario:

| Pair | Optimistic | Base | Conservative | Stress | Stress vs optimistic |
|---|---|---|---|---|---|
| BTC | 118.59 | 113.80 | 109.02 | 95.77 | -19% |
| ETH | 66.85 | 61.77 | 56.92 | 43.17 | -35% |
| BNB | 141.02 | 133.57 | 126.66 | 107.04 | -24% |

- Each step from optimistic to base to conservative costs a roughly constant amount: about 4.8 on BTC, 4.9–5.1 on ETH, and 6.9–7.5 on BNB.
- The conservative-to-stress step is about 2.8 times larger than the earlier steps: 13.2 on BTC, 13.7 on ETH and 19.6 on BNB. Stress is therefore a bigger cost jump than the earlier steps. I can't say more without the scenario definitions.
- Break-even cost cannot be read reliably. No scenario reached zero. A linear extrapolation of the stress step suggests ETH, the thinnest pair, would need roughly two more stress-sized steps to hit zero. That is a rough extrapolation, not a measured break-even.
- ETH and BNB have about 80 trades each (81 and 80), so they are more exposed to per-trade costs than BTC with 58 trades.

## 3. Concentration

Dependence on a single trade (`facts.json`, `net_profit_excl_best_trade__*`):
- **BNB:** base 133.57 falls to 25.29 without the best trade. That trade is the 2021-01-29 to 2021-02-23 position (+345%, profit_abs 106.59), about 80% of base profit. At stress, profit without it is 11.28, against 107.04 with it. The next best trade (2021-03-30, +41.3) is also in the same few months. The gate (profit excluding the best trade above 0) passes, but only narrowly in relative terms.
- **ETH:** base 61.77 falls to 40.34 (the best trade is about 35% of profit). At stress it falls from 43.17 to 24.39.
- **BTC:** base 113.80 falls to 71.52 (about 37%). At stress it falls from 95.77 to 57.16. The best BTC trade is the 2017-11-25 to 2017-12-19 trade (+98%), the first trade in the list.

Dependence on one stretch of time:
- Profit is concentrated in bull phases: late 2017 and early 2018 (BTC, ETH), 2019, and 2020-10 to 2021-05. Trades from 2020-12 to 2021-05 provide the large winners on all three pairs (BTC +14.5 and +15.7, ETH +23.2 and +11.3, BNB +106.6 and +41.3).
- 2022 is nearly absent. BTC has zero trades in 2022, ETH has three small losers, and BNB has several losers. The strategy's behaviour in the 2022 bear market is essentially untested here, and it is not in the market at all for BTC.
- The pairs are not independent evidence. The three pairs' winners fall on the same stretches (for example 2020-12-25 to 2021-01-11 on BTC, ETH and BNB, and 2024-02 to 2024-03).

Dependence on a single pair: BNB provides the largest base profit (133.57), mostly from one trade. BTC has the highest profit per unit of drawdown. No one pair is the whole result, but the pairs share winners and losers in time.

## 4. Overlap with other candidates

I compared H-009 BTC with the BTC trade lists of H-004, H-005 and H-007 (`research/experiments/H-00{4,5,7}-exploration/trades-btc-usdt.csv`). I did not read the ETH or BNB files of those hypotheses, and I did not compute the daily-return correlation that `portfolio.json` uses. That calculation has not been done here.

- **Identical entry timestamps with H-005:** H-009 BTC and H-005 BTC open at the same hour on 2017-11-25 13:00, 2020-01-27 19:00, 2020-05-28 13:00, 2020-06-22 21:00, 2021-08-13 21:00, 2021-10-01 11:00, 2024-02-07 21:00 and 2024-04-08 08:00. H-009's own exits come earlier.
- **Identical entry timestamps with H-007:** 2019-03-29 10:00, 2023-03-30 03:00 and 2024-02-07 21:00 (H-007's 2024-04-08 entry is one hour later, 09:00).
- **Holding days:** H-004 and H-005 hold some trades for months, for example H-004 from 2020-10-21 to 2021-04-23 and H-005 from 2020-10-08 to 2021-01-22. Several H-009 BTC trades fall inside those windows (2020-10-25 to 2020-11-26, 2020-12-25 to 2021-01-11, 2021-02-06 to 2021-02-22). H-007 held from 2020-10-10 to 2021-01-21, which also covers them. In these stretches the strategies hold the same rally and lose on the same reversals, such as the March–April 2023 stop-outs shared with H-007.
- Because H-009 is in the market only 25% of the time (`exposure` 0.25), most of its in-market days appear to sit inside the in-market days of the longer-holding candidates. The overlap looks high on the days I checked. The measured daily correlation could still differ, and I cannot state a value.

## 5. Execution realism

- **Fill assumption on stops:** Most `stop_loss` trades close at almost exactly -6.328%, including two with zero duration (ETH 2020-12-01 11:00, BNB 2022-11-08 17:00 at -6.320%). That suggests fills at the stop price within the same hourly candle. Live stops can fill worse than that in fast markets or gaps (BNB's 2022-11-08 date is a known high-volatility day; the file does not show how it fills). The strategy has many stop-loss exits (for example 9 of 58 on BTC), so any slippage on stops multiplies. The stress scenario partly covers this, but I don't know how much.
- **Frequency:** BTC averages roughly 9 trades per year and ETH and BNB about 12 per year, over 2017–2024. That is low enough that live results over a year or two would be a small sample, and a streak like the 11–14 losers above could last more than a year.
- **Entry and exit orders:** I can't see from the CSVs whether entries use limit or market orders. If limit orders, the many short, quickly stopped trades (60-minute to 3-hour holds in the lists) depend on fills at the backtest price. A missed entry would more likely drop a winner than a loser, but that is unmeasured here.
- **Early BNB data:** BNB's buy-and-hold return is 33,023% (`facts.json`), which reflects a very low initial price in 2017. Liquidity and spreads then were different from today, so early BNB trades may not represent live conditions.
- **Exchange outages and halts:** The backtest assumes the exchange is always reachable, and stops execute when hit. Outages or withdrawals during a volatile stretch would break that assumption, and the data say nothing about it.
- **Compounding:** Stake size appears to grow with the wallet (the same -6.33% loss is about -1.5 early and about -4 late on BNB). The late-2021 BNB losses are therefore larger in absolute terms, so the profit path depends on when the large winner occurs.
