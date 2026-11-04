# Risk assessment: H-016, exploration split

Sources: `research/experiments/H-016-exploration/facts.json`, `trades-btc-usdt.csv`, `trades-eth-usdt.csv`, `trades-bnb-usdt.csv`, `lab/config/gates.json`, `lab/config/portfolio.json`, and the BTC trade lists of H-004, H-005, H-007, H-008 and H-009 (exploration).

Not available:
- `research/proposals/H-016.json` does not exist. A glob for `research/proposals/*016*` found nothing, so I could not check the stated intent or parameters.
- I did not read the strategy file.
- I did not read the cost-scenario definitions, so cost levels (fee and slippage percentages) are unknown to me.
- Figures marked "approx." were summed by hand from `profit_abs`, because the files give no drawdown dates or equity curve.

## 1. Drawdown

Gate ceiling: 25% in every cost scenario (`lab/config/gates.json`, `max_drawdown.max_ratio` = 0.25). Values are max drawdown % from `facts.json`.

| Pair | optimistic | base | conservative | stress | Headroom to 25% at stress |
|---|---|---|---|---|---|
| BTC/USDT | 13.62 | 14.00 | 14.39 | 15.49 | 9.5 pts |
| ETH/USDT | 11.18 | 11.43 | 11.66 | 12.35 | 12.7 pts |
| BNB/USDT | 9.63 | 9.70 | 9.76 | 10.01 | 15.0 pts |

- All twelve cells pass. The gap between optimistic and stress is small: BTC +1.9 pts, ETH +1.2 pts, BNB +0.4 pts.
- `exposure` is reported as 0.15 for every pair. The drawdowns are therefore for a position of about 15% of the wallet.
  - Stake size grows through the run: `profit_abs / profit_ratio` is about 15 early and about 22 (BTC) or about 34 (BNB) late.
  - This suggests the position compounds with the wallet. I have not confirmed that.
- Single-trade losses are large relative to the drawdown figure. `exit_reason` is `tsmom_not_positive` on every trade except one BNB `force_exit`, and the file shows no intermediate stop-loss exits.
  - BTC: -25.3% on 2018-03-02 to 2018-03-15.
  - ETH: -19.4% on 2022-10-24 to 2022-11-10.
  - BNB: -34.3% in one day on 2021-05-19, and -25.6% on 2018-03-04 to 2018-03-11.
- Longest losing stretches (approx., from `profit_abs` sums; dates are trade open and close):
  - BTC: about 17 months with no new equity high, from the 2021-11-17 close to about the 2023-04-23 close. 2022 alone nets about -15.6 quote across 18 trades, nearly all small losses. There is also a 2018 stretch of about 12 consecutive losing or flat trades between March and November 2018.
  - ETH: a similar flat or negative stretch from late 2021 through about the first half of 2023. 2022 is almost all losers apart from the 2022-07-17 to 2022-08-27 trade (+3.27) and a -5.98 loss on 2022-10-24.
  - BNB: from the Dec 2021 peak the trades are mostly losers through 2022 and 2023, with recovery only partial until the +77.5 trade of 2024-02-07 to 2024-04-13. This could be a stretch of more than two years. I am less sure of the start date here because the stake size changes the arithmetic.
- The largest drawdown date is not in the files, so I cannot confirm that the 2021 to 2023 stretch is the one that produced the figures above.

## 2. Cost sensitivity

Net profit in quote units (`net_profit_quote__*`):

| Pair | optimistic | base | conservative | stress | Optimistic to stress | Base to stress |
|---|---|---|---|---|---|---|
| BTC | 155.62 | 150.24 | 144.78 | 129.48 | -26.14 (-16.8%) | -20.76 (-13.8%) |
| ETH | 119.78 | 115.19 | 110.90 | 98.42 | -21.36 (-17.8%) | -16.77 (-14.6%) |
| BNB | 530.96 | 516.96 | 503.49 | 463.86 | -67.10 (-12.6%) | -53.10 (-10.3%) |

- Trade counts are identical across scenarios (94, 89, 96), so the loss comes from cost per trade, not from changed behaviour.
- Degradation is gentle and roughly linear in the scenario steps. Every pair stays well above the required threshold of 1.1 quote at stress. The gate only tests base and conservative.
- Break-even cost cannot be read in fee or percentage units, since I don't have the scenario definitions.
  - Extrapolating linearly in scenario steps, stress profit is about 6.2 times the base-to-stress loss for BTC, 5.9 times for ETH and 8.7 times for BNB.
  - That is only an extrapolation. Compounding makes the true relationship non-linear, and I cannot say what cost level it corresponds to.
- Many trades last only 1 to 3 days (1440 to 4320 minutes) and end in small losses. Cost per round trip matters more for those than for the multi-month winners.

## 3. Concentration

Dependence on a few trades, as profit with the single best trade removed (`net_profit_excl_best_trade__base` against `net_profit_quote__base`):
- BTC: 150.24 falls to 77.89, a loss of 48%.
- ETH: 115.19 falls to 69.74, a loss of 39%.
- BNB: 516.96 falls to 201.54, a loss of 61%.
- The gate only requires the remaining profit to be positive (`gates.json`, `profit_excluding_best_trade`), and it is. The drop is larger than the best trade's own `profit_abs`, which is consistent with compounding: removing an early big winner also shrinks later stakes.

Top trades in the lists:
- BTC: 59.10 (2020-10-04 to 2021-02-07), 31.52 (2017-10-09 to 2018-01-10), 27.77 (2019-03-27 to 2019-07-23), 20.55 (2023-10-01 to 2024-01-08).
- ETH: 32.19 (2020-12-25 to 2021-03-06), 25.55 (2017-11-17 to 2018-02-03), 13.62, 11.81.
- BNB: 233.30 (2020-12-26 to 2021-03-22), 104.75 (2021-03-26 to 2021-05-13), 81.25 (2019-01-06 to 2019-07-01), 77.47 (2024-02-07 to 2024-04-13), 34.51. Together the top three come to about 419 of 517 quote.

Dependence on one pair: BNB contributes 517 of the combined 782 quote at base (150.24 + 115.19 + 516.96), about two thirds. Its buy-and-hold benchmark is 33,023% (`facts.json`), which suggests the BNB history includes a very low-priced early period.

Dependence on time:
- Profit comes from a handful of multi-month trend legs, all in bull phases: late 2017, 2019 (Q1 to Q2), Oct 2020 to spring 2021, and Oct 2023 to spring 2024.
- Most of the 1 to 5 day trades in the three lists are small losses.
- The three pairs lose together in 2022 and in 2018.
- All pairs share the same exit rule, so the pairs are not independent evidence.

## 4. Overlap with other hypotheses

Only BTC trade lists were compared. I did not read the ETH or BNB lists of other hypotheses, and I did not compute a correlation. `portfolio.json` uses a daily-return correlation with a limit of 0.7; I cannot say whether H-016 would pass it.

H-016 BTC holds were compared with the same hypotheses' BTC holds. H-004, H-005, H-007, H-008 and H-009 had trade lists:

| H-016 BTC hold | Overlapping holds in other hypotheses |
|---|---|
| 2017-10-09 to 2018-01-10 | H-004 2017-10-20 to 2018-01-16; H-005, H-008 and H-009 start 2017-11-25 and end 2017-12-22 or 12-19, inside the window |
| 2019-03-27 to 2019-07-23 | H-004 2019-04-03 to 2019-08-29; H-005 and H-008 2019-02-19 to 2019-07-16; H-007 2019-03-29 to 2019-06-04 |
| 2020-10-04 to 2021-02-07 | H-004 2020-10-21 to 2021-04-23; H-005 and H-008 2020-10-08 to 2021-01-22; H-007 2020-10-10 to 2021-01-21 |
| 2023-10-01 to 2024-01-08 | H-004 2023-10-23 to 2024-01-19; H-005 and H-008 2023-10-02 to 2024-01-18; H-007 2023-11-01 to 2024-01-14 |
| 2024-02-10 to 2024-04-04 | H-004 2024-02-12 to 2024-04-17; H-005 and H-008 2024-02-07 to 2024-03-20; H-007 2024-02-07 to 2024-03-17 |

- The main profit-making holds coincide closely with those of the other hypotheses. Their wins and their risk come from the same BTC trends.
- H-016 is also in the market on many days when the others are flat, mainly short trades in 2018 and 2022. Those days add losses the other strategies mostly avoided. On the overlapping days the two are co-moving, but on those extra days they are not.
- H-005 and H-008 have identical entries and exits on BTC and differ only in `profit_abs` scale, so they are effectively one set of trades. That matters if they are ever counted as two independent candidates.

## 5. Execution realism

- The trades open and close at 00:00 UTC (1-day candles). The backtest assumes fills at the bar open after a signal, at the simulated price, with the scenario cost applied. Live fills at the daily rollover are subject to slippage and a wider spread at a time when many other daily-signal strategies trade. The stress scenario shows the effect is modest only if its cost is as large as the live cost. I have not checked that.
- There are 94, 89 and 96 trades over roughly 7 years, about 13 per year per pair. Fill-rate problems from limit orders would be rare in count but costly: the profit sits in a few trades, and missing one entry on a multi-month trend would remove a large share of the result (section 3).
- Exits are signal-based at the daily boundary, with no intrabar stop visible in the exit reasons. A real position can be hit by a gap or a flash move within the day. The listed losses of -19% to -34% on a single trade are what the backtest records; live results could be worse if the exit fill is worse than the simulated price.
- Exchange outages, maintenance windows, or API failure at the rollover could delay an exit. The trade list assumes none. With daily bars the risk is small in frequency but falls on the exit, which is when it hurts most.
- BNB's early history (2017 to 2018, after listing) was thinly traded. Historical fills there may not be repeatable, and BNB provides most of the profit.
- The last BNB trade is a `force_exit` on 2024-07-25 06:00 (-3.40 quote), an artifact of the end of the data, not a strategy signal.
- Backtests assume the 15% stake can always be filled in full. I have no data on order-book depth.
