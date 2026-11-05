# Risk assessment: H-025 (DailyKeltnerBreakout), exploration split

Sources: `research/experiments/H-025-exploration/facts.json` (metrics), `trades-btc-usdt.csv`, `trades-eth-usdt.csv`, `trades-bnb-usdt.csv`, `research/proposals/H-025.json`, `lab/config/gates.json` (max drawdown ceiling 0.25 = 25%), `lab/config/portfolio.json`. This is an assessment of recorded results only. It is not a decision, and it makes no recommendation on sizing or going live.

Caveat on the trade CSVs: they do not say which cost scenario they come from. Their `profit_abs` values do not exactly match the "best trade removed" figures in facts.json (see section 3). I treat CSV amounts as approximate. Every trade runs on a stake of about 20 USDT early on, and the stake grows later (BNB reaches about 50 USDT), so profits are compounded.

## 1. Drawdown

Maximum drawdown, % (facts.json, `max_relative_drawdown_pct__*`, the series the gate uses; the absolute series is shown only where it differs):

| Pair | optimistic | base | conservative | stress | Gate ceiling |
|---|---|---|---|---|---|
| BTC/USDT | 6.44 | 6.53 | 6.68 | 7.09 | 25 |
| ETH/USDT | 4.83 | 4.92 | 5.00 | 5.24 | 25 |
| BNB/USDT (relative) | 8.35 | 8.54 | 8.73 | 9.29 | 25 |
| BNB/USDT (absolute, `max_drawdown_pct__*`) | 6.76 | 7.05 | 7.34 | 8.26 | 25 |

- Every pair and scenario is far below the 25% ceiling. The worst figure is BNB stress at 9.29%.
- Drawdown rises only about 0.6 to 1.7 points from optimistic to stress.
- Exposure is 0.2 (a fixed share of the account). These percentages are therefore account-level drawdowns, not per-trade drawdowns. Each stopped trade loses about 8.3% of its stake, about 1.7% of the account.
- Drawdown is not the weak point. The long losing stretches below are the weak point.

Longest losing stretches, read from the trade lists (profit_abs in USDT, CSV scenario):

- **BTC:** 5 consecutive losers (4 stop-losses plus 1 small EMA20 exit), from 2021-11-09 to 2022-11-08, about 12 months. They total about -9.0 USDT. The next winner closed 2023-02-10. The earlier 2020-04-30 to 2020-06-12 cluster had 4 consecutive losers, about -4.8, over roughly 6 weeks.
- **ETH:** at most 3 consecutive losers in a row. The largest is 2020-09-02 to 2020-10-28 (3 stops, about -5.8). There were also 2 stops in 2022-08 and 2022-11 (about -4.8), with no trades from 2022-04-07 to 2023-01-10.
- **BNB:**
  - 2018-04-25 to 2019-01-28: 5 consecutive losers (about -6.6), about 9 months.
  - 2020-09-02 to 2020-12-22: 5 consecutive losers (about -9.8), about 3.5 months.
  - 2022-10-29 to 2023-12-18: about 13 months containing 5 losers and one trade at roughly zero (+0.005), totalling about -13.7. The next real winner opened 2023-12-21.
  - The last 3 trades in the data (2024-03-30, 2024-06-05, 2024-07-22) are all stop-losses, about -12.2 in total. The data ends without a recovery.
- Win rate, from my count of the CSVs, is about 51% for BTC (17 of 33). Stop-loss exits number 9 of 33 for BTC, 11 of 33 for ETH and 21 of 41 for BNB. I counted the ETH and BNB win rates less carefully, so treat them as indicative. The proposal itself expected a win rate below 50%.
- The owner's stated concern (long streaks of stopped-out breakouts) is visible in these data. Streaks of 5 losers and year-long flat-or-down periods occurred on both BTC and BNB.

## 2. Cost sensitivity

Net profit in USDT (facts.json `net_profit_quote__*`):

| Pair | optimistic | base | conservative | stress | Optimistic to stress | Base to stress |
|---|---|---|---|---|---|---|
| BTC | 58.32 | 56.78 | 55.05 | 50.60 | -7.72 (-13.2%) | -6.18 (-10.9%) |
| ETH | 57.23 | 55.71 | 53.96 | 49.45 | -7.78 (-13.6%) | -6.26 (-11.2%) |
| BNB | 141.44 | 138.51 | 135.35 | 126.47 | -14.97 (-10.6%) | -12.04 (-8.7%) |

- Degradation is gentle and roughly linear, because trades are infrequent. That is about 0.23 USDT per trade across the whole range on BTC and ETH.
- A linear extrapolation gives a rough break-even. BTC stress profit (50.6) is about 6.6 times the optimistic-to-stress loss (7.7). ETH is about 6.4 times and BNB about 8.4 times. Costs would have to go well beyond the stress scenario to erase profit, if the relation stays linear.
- I did not read the scenario cost definitions, so I cannot convert this into a percentage cost. The proposal quotes a 0.35 to 0.50% round-trip cost, which is a different statement from the scenario definitions.
- Cost is not the main fragility here. Dependence on a few trades (next section) is the larger one.

## 3. Concentration

- **Best-trade dependence.** facts.json gives profit with the best trade removed (base):
  - BTC: 56.78 to 39.93. The best trade accounts for about 16.9 (30%).
  - ETH: 55.71 to 38.49. The best trade accounts for about 17.2 (31%).
  - BNB: 138.51 to 35.26. The best trade accounts for about 103.3 (75%).
  - The gate (positive without the best trade) is passed on all three. The BNB margin comes from a single trade.
  - The CSV's largest `profit_abs` is smaller than these implied amounts (BTC 13.26, ETH 14.28, BNB 84.71). I cannot reconcile this from the files read, so the scenario or compounding basis behind the CSV is unknown.
- **BNB.** One trade (2021-02-02 to 2021-03-25, profit ratio +3.81) and the next (2021-03-31 to 2021-05-13, +0.98) together make about 122.7 of the 138.5 base profit (about 89%, mixing CSV amounts with the facts total). Without the first trade, BNB contributes far less and is much closer to the other pairs. The 2019-02-06 trade (+1.23) adds about 23. Most of the other 38 BNB trades are small winners or 8.3% stops.
- **BTC and ETH.** Four BTC trades (2019-04-03, 2020-10-12, 2020-12-17 and 2024-02-09 openings) sum to about 48.2, close to the 56.8 total. Four ETH trades (2020-12-28, 2020-07-23, 2020-01-15 and 2024-02-13 openings) sum to about 43.7. Profit is therefore a small set of large trend captures. The proposal says the same.
- **Pair dependence.** BNB's base profit is about 2.4 times BTC's and ETH's (138.5 vs 56.8 and 55.7). BNB's buy-and-hold return of 33,023% suggests an extreme early-price starting point. That makes BNB a poor base for expecting typical results, and I cannot say how much of its profit is a one-off feature of that history.
- **Time dependence.**
  - Profits cluster in 2019 (spring), 2020-07 to 2021-05, 2023 and 2024-02/03.
  - 2022 has almost no gain on any pair, and 2022-03 to 2022-11 consists mostly of stops and small losses.
  - There are long gaps with no trades on all pairs, for example 2021-11 to 2023-01 on BTC and ETH.
  - Trade counts are modest (33, 33 and 41 over about 6.5 years, roughly 5 to 6 per year per pair), against the proposal's expectation of 10 to 25 per year. The sample is thin for judging stability.
- Exit mix: most large winners exit via `close_below_ema20`, and most stops are exactly at about -8.32%.

## 4. Overlap with other candidates

I compared H-025 BTC trades with H-024 (`research/experiments/H-024-exploration/trades-btc-usdt.csv`) and H-009 (`research/experiments/H-009-exploration/trades-btc-usdt.csv`). I did not compute a correlation, so this is a description only; `portfolio.py` is the source for the formal figure.

- **H-024 (daily trend, SMA20 exit).** Overlap is high in the big trends:
  - 2019-04-03 to 2019-06-04/05: both enter on the same day.
  - 2020-10-12 vs 2020-10-22 start, both ending about 2020-12-09/11.
  - 2020-12-17 vs 2020-12-16 start, both ending 2021-01-21/22.
  - 2023-01-12 vs 2023-01-14, ending 2023-02-10 vs 2023-02-07.
  - 2023-10-17 vs 2023-10-24, both ending 2023-11-22.
  - 2024-02-09 vs 2024-01-30, both ending 2024-03-17.
  - The 2023-02-16 to 2023-02-25 trade is the same trade in both (-5.0%).
  - H-024 trades more often in other periods (for example 2018, 2021-05, 2022), where H-025 is mostly flat. H-025 is in the market on a subset of the days H-024 is.
- **H-009 (1h Donchian-type, `low72_or_regime_lost` exit).** Overlap is partial. Both are long in the 2019-04/05, 2020-10 to 2021-01, 2021-02 and 2024-02/03 rallies. H-009 trades much more often (more than 60 trades vs 33) and has many short trades in periods where H-025 is out.
- The proposal itself states it shares the daily-signal pattern and trend gate with H-019/H-020/H-024. I did not compare ETH or BNB lists, or H-019/H-020 (H-020 files exist but I did not read them).
- Because H-025's profit comes from the same few large trends that trend-following peers also catch, holding it alongside them gives much less diversification in drawdown periods than the strategy count suggests. This is an inference from the dates above, not a measured correlation.

## 5. Execution realism

- **Entry.** Signals come from a closed daily candle and orders execute at the next 1h open, typically at 00:00 UTC. That is the daily open, when spreads are often wider and a gap away from the close can already exist. Backtest fills at the open price will differ live.
- **Stop-loss.** Nearly every stop exits at a ratio of about -8.32%, i.e. exactly at the stop level plus fees, with no slippage beyond it. A native intrabar stop on spot needs the order to rest on the exchange or be monitored. In fast crashes or exchange outages it may fill worse than -8%, or not at all for a time. The backtest shows no such cases, which suggests the simulation fills stops at the level, not at the gap price. This is an assumption, not a measured result.
- **Re-entry after stops.** Several trades re-enter within an hour of a stop (BTC 2018-04-25 15:00, 2020-06-02 16:00, 2022-09-13 19:00; BNB 2020-11-25 23:00; ETH 2020-09-02 12:00). These come from the daily-signal logic acting on the next 1h bar. They imply extra fees and order-timing sensitivity that live may not reproduce.
- **Frequency.** Roughly 5 to 6 trades per year per pair means few orders. Slippage and fee differences cost little in aggregate (see section 2), but each missed or late order matters a lot: missing one of the four big trades per pair would materially cut profit. An outage, API failure or manual miss around a daily-close entry has an outsized effect.
- **Data and sample.** The first BTC and BNB trades on 2018-04-25 sit right at the start of the data. The warm-up (3,700 bars) is satisfied, but the first trades are close to the edge of the available history. The split runs about 2018 to mid-2024 and contains one regime of strong crypto uptrends; I cannot judge how the rule behaves outside it.
- **Whole-balance, fixed exposure.** The strategy uses a fixed 0.2 share of the account and compounds. Live trade size depends on exchange minimums and balance. I take no position on sizing.
- This lab never approves live trading, and nothing here changes that.
