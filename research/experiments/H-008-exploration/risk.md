# Risk assessment: H-008, exploration split

Sources: `research/experiments/H-008-exploration/facts.json`, `trades-btc-usdt.csv`, `trades-eth-usdt.csv`, `trades-bnb-usdt.csv`, `lab/config/gates.json`, `lab/config/portfolio.json`, `user_data/strategies/_archive/VolatilitySqueezeBreakout_H008_v1.py`, and the trade lists in `research/experiments/H-004/H-005/H-007/H-009-exploration/`.

Notes on the inputs:
- `research/proposals/H-008.json` does not exist. The proposals folder holds only H-004 to H-007. Nothing in the proposal could be checked.
- The strategy docstring says H-008 is "the H-005 rule, unchanged, traded with 20% of the account per trade". `facts.json` shows exposure of 0.2 for every pair.
- The profit_abs figures in the CSVs differ slightly from the best-trade effect implied by facts.json (see section 3). I did not resolve the difference.

## 1. Drawdown

The gate ceiling is 25% (`gates.json`, max_drawdown.max_ratio 0.25). Values below are from `facts.json` and use the relative drawdown, which is what the decision reasons cite.

| Pair | optimistic | base | conservative | stress |
|---|---|---|---|---|
| BTC/USDT | 11.75% | 12.20% | 12.47% | 13.56% |
| ETH/USDT | 12.14% | 12.51% | 12.87% | 13.92% |
| BNB/USDT (relative) | 12.93% | 13.16% | 13.39% | 14.08% |

- BNB also reports a lower `max_drawdown_pct` of 10.02% to 11.35%. The gate used the higher relative figure. I can't tell from the files why the two measures differ.
- The worst case, stress on BNB at 14.08%, is about 11 points under the ceiling. Drawdown is limited partly because only 20% of the account is in a trade at a time.
- The drawdown figures are for the account, not per trade. Each stop-loss exit loses about 8.3% of the stake (profit_ratio about -0.0832), which is about 1.4 to 3.4 quote per trade on a 100 USDT wallet.

Longest losing stretches from the trade lists (consecutive losing trades, base scenario):
- **BTC:** 7 losses in a row, from the 2022-03-22 open to the 2023-08-17 close. They sum to about -13.8 quote. No winning trade closed between 2021-11-18 and 2023-10-02 (the next win's open date), about 22 months. An earlier run of 6 losses spans 2021-02-17 to 2021-09-20 and sums to about -14.8.
- **ETH:** 8 losses in a row, from 2021-11-25 to the 2022-11-08 close, about 12 months. They sum to about -23.2 quote. Four more losses followed in 2023-04 to 2023-07 (about -7.95).
- **BNB:** 10 losses in a row, from 2021-12-23 to the 2023-11-21 close, about 23 months. They sum to about -26.2 quote. Early in 2018 there were also 8 consecutive losses (7 stop-losses and 1 breakdown exit, 2018-02-15 to 2018-07-06), about -11.7.

The strategy wins only 22% to 35% of the time, so long flat or losing periods are normal for it.
- Win counts, counted by hand from the CSVs: BTC 9 of 31, ETH 11 of 36, BNB 8 of 36.
- Stop-losses are frequent. All three pairs show many rows with exit_reason `stop_loss`.

## 2. Cost sensitivity

Net profit in quote currency (`facts.json`, net_profit_quote):

| Pair | optimistic | base | conservative | stress | optimistic to stress |
|---|---|---|---|---|---|
| BTC | 80.30 | 78.34 | 77.07 | 71.92 | -10.4% |
| ETH | 89.61 | 87.35 | 85.48 | 79.52 | -11.3% |
| BNB | 174.67 | 171.54 | 168.40 | 159.77 | -8.5% |

- Profit falls by about 0.27 quote per trade across the scenario range for BTC. That is (80.30 - 71.92) / 31, and I derived it myself. The pattern is similar for ETH and BNB.
- Costs therefore take only a small share of net profit. The strategy trades about 31 to 36 times in the whole split, so fees and slippage don't add up quickly.
- A break-even cost can't be read reliably. All four scenarios stay clearly positive, and I did not read the scenario definitions. Extrapolating the line would be a guess.
- Costs matter more once the best trade is removed. In the stress scenario the profit excluding the best trade is BTC 28.48, ETH 12.13 and BNB 11.17 (`net_profit_excl_best_trade__stress`). Costs are not the main risk here. The reliance on a few trades (section 3) is.

## 3. Concentration

Profit leans heavily on a few trades. The best trade's share is computed from facts.json as (net_profit_quote__base - net_profit_excl_best_trade__base) / net_profit_quote__base.

| Pair | Net profit, base | Excluding best trade | Best trade's share of profit |
|---|---|---|---|
| BTC | 78.34 | 33.19 | about 58% |
| ETH | 87.35 | 16.88 | about 81% |
| BNB | 171.54 | 15.96 | about 91% |

The CSV profit_abs values for those best trades are lower than the difference implied by facts.json: BTC 44.13, ETH 65.97, BNB 141.01. I could not tell why they differ.

- BTC: the two largest trades are +44.13 (2020-10-08 to 2021-01-22) and +29.98 (2019-02-19 to 2019-07-16). Together they are about 74 of the 78 net. The other seven winners add little, and the 22 losing trades roughly cancel them.
- ETH: the largest trade is +65.97 (2020-10-09 to 2021-02-23). The second is +24.98 (2021-03-29 to 2021-05-19).
- BNB: the largest trade is +141.01 (2020-12-14 to 2021-03-25). Others are +33.56 (2024-02-07 to 2024-04-13) and +18.43 (2019-02-19 to 2019-05-08).
- **Time concentration:** the largest winner on each pair falls in the same bull run, from October 2020 to March 2021. The 2020-07-06 trade is also a winner on all three pairs, and a 2024-02 trade is a winner on all three. The three pairs are therefore not independent evidence. Profit on all of them depends on a few trending periods in 2019, 2020 to 2021 and 2024.
- **Pair concentration:** BNB gives about half of the combined base profit (171.54 of about 337). BNB buy-and-hold returned 33,023% (`benchmark_buy_and_hold_return_pct`), so BNB's history in this split is unusual.
- The profit comes from rare, long trades. The longest are about 212,700 minutes (148 days) on BTC and 197,100 minutes (137 days) on ETH.

## 4. Overlap

**H-005 (same rule).** The H-008 strategy file states that it is the H-005 rule with 20% exposure. Comparing the trade lists:
- BTC: all 31 trades in `H-005-exploration/trades-btc-usdt.csv` have the same open dates, close dates, exit reasons and profit_ratio as H-008. Only profit_abs differs, because the stake is different. For example, both open 2017-11-25 13:00 and close 2017-12-22 14:00 with profit_ratio 0.4093.
- BNB: the 36 trades in `H-005-exploration/trades-bnb-usdt.csv` match H-008's trade for trade (same open dates and ratios).
- ETH: I did not open H-005's ETH file, so that comparison is not made.
- H-008 and H-005 are therefore the same market positions at a different size. Their daily-return correlation would be about 1.0. I did not compute it. Under `portfolio.json` (max_abs_correlation 0.7) they could not both be included. Also, `facts.json` counts only "1 prior variant(s) in family" for the net-profit threshold. I can't confirm whether this size-only change should count as a separate draw.

**H-004 (BTC, tsmom30 breakdown exit).** It has 13 trades, and the stretches in the market overlap with H-008 BTC:
- 2017-10-20 to 2018-01-16 against H-008's 2017-11-25 to 2017-12-22
- 2019-04-03 to 2019-08-29 against 2019-02-19 to 2019-07-16
- 2020-10-21 to 2021-04-23 against 2020-10-08 to 2021-01-22
- 2023-10-23 to 2024-01-19 against 2023-10-02 to 2024-01-18
- 2024-02-12 to 2024-04-17 against 2024-02-07 to 2024-03-20

These are the same big trend legs. H-004 holds longer.

**H-007 (BTC).** It opens on 2024-02-07 21:00, the same hour as H-008. It also covers 2019-03-29 to 2019-06-04, 2020-10-10 to 2021-01-21 and 2023-11-01 to 2024-01-14, which sit inside H-008's trades.

**H-009 (BTC).** Many entries are at the same hour as H-008 BTC, such as 2017-11-25 13:00, 2020-01-27 19:00, 2021-03-30 10:00, 2021-08-13 21:00, 2021-10-01 11:00, 2023-04-10 17:00 and 2024-02-07 21:00. H-009 exits much sooner, so its holding time is shorter.

I did not compute correlations for these. I only compared dates by eye. I did not compare ETH or BNB for H-004, H-007 or H-009. There is no H-006 trade list and no H-004 to H-009 validation-split trade list to compare.

## 5. Execution realism

- **Trade frequency.** There are 31 to 36 trades per pair over the whole split, which is a few per year. This is low frequency, so latency and per-trade slippage matter little. The bigger risks are how rare the winners are (section 3) and a live period with no big trend.
- **Stop-loss fills.** Stop-loss rows show a profit_ratio of almost exactly -0.0832 (a stop of 8% plus fees) on every pair. The backtest appears to fill stops at the stop price with no extra slippage. In live trading a fast move or gap can fill below the stop. The strategy has a hard 8% stop and does not trade every candle. Overnight crypto gaps are usually small, but I can't measure them from these files. The stop-loss rows contain no worse-than-stop fills.
- **Exits at closes.** The `low336_breakdown` exit is decided on a closed candle and executed on the next one (docstring). Live fills may be worse than backtest fills, in either direction. These exits are a large share of the profit and loss. Exit fills are the result of price gaps between candles, and the backtest data can't show their size.
- **Order type.** I did not read the order type, fee or slippage configuration. I cannot say whether the fills assume limit or market orders. If limit orders are assumed, some entries or exits may not fill live.
- **Outages.** Exchange outages or API failures would matter most when a stop or breakdown exit falls inside them. The strategy holds trades for days to months, so most outages would have little effect. A missed exit during a sharp fall could cost more than the 8% stop.
- **Sample.** BTC, ETH and BNB all lose and win in the same periods, so the realized results rest on a few independent market episodes. The exploration split contains 31 to 36 trades per pair, just above the 30-trade minimum in `gates.json` (BTC: 31).
