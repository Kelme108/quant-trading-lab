# Risk assessment: H-020 (Double7ChannelDip), exploration split

Sources: `research/experiments/H-020-exploration/facts.json` (metrics), `trades-btc-usdt.csv`, `trades-eth-usdt.csv`, `trades-bnb-usdt.csv` (same folder), `research/proposals/H-020.json`, `lab/config/gates.json`, `lab/config/portfolio.json`, `lab/config/scenarios.json`. This is an assessment of what could go wrong, not a decision. Sums of trade `profit_abs` below are my own additions from the CSVs, rounded; they are approximate.

## 1. Drawdown

Gate ceiling: 25% (`gates.json`). Maximum drawdown in % (`facts.json`):

| Pair | optimistic | base | conservative | stress |
|---|---|---|---|---|
| BTC/USDT | 3.46 | 3.56 | 3.65 | 3.65 |
| ETH/USDT | 11.05 | 11.19 | 11.33 | 11.76 |
| BNB/USDT | 6.76 | 7.00 | 7.28 | 8.19 |

All cells are under the ceiling. The largest value is ETH at stress (11.76% against 25%).

Context for the numbers:
- Exposure is 0.1 (`facts.json`). The strategy has no stop-loss (`stoploss = -0.99`, never binding, per the proposal), so a single trade can lose a lot. Largest single-trade losses (`profit_ratio`, from the trade CSVs):
  - ETH: -51.3% (2018-03-06 to 2018-04-11, abs -5.11); -33.1% (2021-12-29 to 2022-01-29); -31.9% (2020-03-09 to 03-20).
  - BNB: -32.7% (2021-05-13 to 06-03); -28.8% (2019-08-14 to 09-18).
  - BTC: -23.4% (2021-11-16 to 12-22); -21.0% (2021-05-13 to 06-04); -17.5% (2019-09-11 to 10-03).
- ETH's drawdown (11.19% of the account at base) is large next to its total base profit (4.96).
- Drawdown changes little with cost on BTC (3.46 to 3.65). It grows more on BNB (6.76 to 8.19) and ETH (11.05 to 11.76).

Longest losing stretches, read from the trade lists (sums approximate, base cost):
- **BTC**: the worst single episodes are 2021-11-16 to 2021-12-22 (-2.39, a 36-day hold), 2021-05-13 to 2021-06-04 (-2.19) and 2019-09-11 to 2019-10-03 (-1.75). No deep multi-trade losing run appears.
- **ETH**:
  - 2018-03-06 to 2018-06-03: two consecutive losers (-5.11, -1.75), about -6.9 over about 89 days with no winner between.
  - 2021-05-16 to 2021-07-22: three consecutive losers, about -4.8 over about 67 days.
  - 2021-12-29 to 2022-01-29: -3.40 in one trade.
  - 2020-02-20 to 2020-03-20: about -3.4 over about 29 days.
  - The last ETH trade (2024-06-08 to 2024-07-05, -1.83) is a `force_exit` at the end of the data, so it was closed by the backtest end, not by the rule.
- **BNB**:
  - 2021-05-13 to 2021-07-26: three losers in a row (-3.50, -1.49, -0.25), about -5.2 over about 74 days.
  - 2018-06-23 to 2018-08-25: about -3.8 over about 63 days.
  - 2021-12-04 to 2022-01-28: about -3.3 over about 55 days.
  - Single trades: 2019-08-14 to 09-18 (-3.03) and 2023-06-02 to 06-18 (-2.09).

I did not compute drawdown duration (time to recover a peak). Only the stretches above come from the trade lists. The BTC last trade (2024-07-04, -0.38) is also a `force_exit`.

## 2. Cost sensitivity

Net profit by scenario (`facts.json`, quote units):

| Pair | optimistic | base | conservative | stress | optimistic to stress |
|---|---|---|---|---|---|
| BTC | 6.62 | 5.73 | 4.71 | 2.24 | -66% |
| ETH | 6.04 | 4.96 | 3.95 | 0.84 | -86% |
| BNB | 8.14 | 7.13 | 6.11 | 3.09 | -62% |

- Per-trade erosion from optimistic to stress is about 0.075 (BTC, 58 trades), 0.079 (ETH, 66) and 0.079 (BNB, 64). Trade counts are identical in every scenario.
- ETH is the thinnest. Its stress profit (0.84) is below the 1.0 base threshold in `gates.json`, and without its best trade it is -1.53. The profit gate only requires base and conservative, so stress is informational.
- Break-even cost cannot be read from the files. They give results per scenario, but I did not find the cost value of each scenario (the proposal mentions only 0.35%/0.50% round-trip). All three pairs are still positive at stress, so break-even lies beyond the stress cost. I do not extrapolate a number.
- The edge per trade is small: base profit is about 0.09 (BTC), 0.08 (ETH) and 0.11 (BNB) per trade, against a per-trade cost step of about 0.08 between the cost extremes. Extra costs would remove a large share of it.

## 3. Concentration

Dependence on the best trade (`net_profit_excl_best_trade__base` against `net_profit_quote__base`):
- BTC: 4.23 of 5.73 remains (best trade about 26% of profit).
- ETH: 2.43 of 4.96 remains (about 51%). At stress, ETH goes negative without its best trade (-1.53).
- BNB: 4.92 of 7.13 remains (about 31%).
- Only the single best trade was removed in the files. The effect of removing the top few is unknown. The largest ETH winners are 2021-01-22 (+2.45), 2020-11-28 (+1.73), 2021-04-20 (+1.70) and 2020-12-24 (+1.60).

Time concentration:
- No trades open in 2022 on BTC and ETH, and BNB opens only in 2022-01 and 2022-12. The list shows this; I assume the 200-day filter is the reason. Trades opened in late 2021 closed in January 2022. The bear market of 2022 is therefore barely tested.
- The big winners cluster in Q4 2020 to Q1 2021 on all three pairs.
- The big losers also fall in the same weeks across pairs: Feb–Mar 2020 (entries BTC 02-18, ETH 02-20, BNB 02-16), May–June 2021 (BTC 05-13, ETH 05-16, BNB 05-13), Aug–Sep 2019, and Dec 2021 to Jan 2022. The pairs fail together, so three pairs are not three independent samples. `scenarios.json` reports daily-return correlation with BTC of 0.787 (ETH) and 0.635 (BNB) over all common days.

Pair concentration: base net profit is positive on all three pairs (4.96 to 7.13), so no single pair carries the result. ETH has the highest drawdown, the lowest base profit and is the weakest at stress.

Sample caveat: one exploration window (about 2018–2024) and one parameter set. Exploration is not validation.

## 4. Overlap with other hypotheses

I compared BTC trade lists of H-016 (`research/experiments/H-016-exploration/trades-btc-usdt.csv`, exit reason `tsmom_not_positive`) and H-009 (`.../H-009-exploration/trades-btc-usdt.csv`, exit reasons `low72_or_regime_lost` and `stop_loss`). H-004, H-005, H-007 and H-008 trade lists exist, but I did not read them. I computed no correlations. This is a date comparison only.

- **H-016**:
  - Long 2020-10-04 to 2021-02-07. H-020 BTC trades 2020-11-27 to 12-01, 2020-12-09 to 12-14 and 2021-01-13 to 01-29 sit inside it.
  - Long 2024-02-10 to 2024-04-04, which contains H-020's 2024-02-23 to 02-27 and 03-17 to 03-26 trades.
  - Long 2023-01-10 to 03-01 and 2023-03-13 to 04-23, overlapping H-020's February–March 2023 trades.
  - H-016 has many short trades in 2022 where H-020 BTC has none.
- **H-009**:
  - Long 2020-10-25 to 2020-11-26. H-020 BTC entered 2020-11-27, the day after.
  - Long 2020-12-25 to 2021-01-11, next to H-020's 2020-12-09 to 12-14 and 2021-01-13 trades.
  - H-020's 2021-11-16 to 12-22 loser comes after H-009's losing trades in 2021-11-02 to 11-16.
- The winning stretches coincide in bull periods, and both strategies are long-only crypto. H-020 is in the market only part of the time (exposure 0.1; holds of 1 to 36 days on BTC), so the overlap is partial.
- `portfolio.json` requires |daily correlation| ≤ 0.7. I did not compute it, so I cannot say whether H-020 would pass it.

## 5. Execution realism

- **Fills**: signals use closed daily candles and orders fill at the next 1h open (00:00 UTC). The backtest fills at the open price. Live, a daily-roll fill may be slower or worse, and entries occur after a 7-day closing low, i.e. a falling market, where slippage is likely higher. Frequency is low (58–66 trades per pair over about 6.5 years, roughly 9–10 per year), so the effect is limited per year but each trade carries it.
- **Gaps and outages**: `scenarios.json` notes 28 gaps in the BTC 1h history (largest 33 hours), consistent with exchange downtime. A missed or delayed order at the roll is possible live. A delayed exit during a fast fall is costly because there is no stop.
- **No stop-loss**: the rule holds through trend breaks until the channel exit. Single trades have lost up to 51% (ETH 2018). A halt, delisting or quote-currency problem would not be bounded by the backtest.
- **Forced exits**: the last BTC and ETH trades are `force_exit` marks at the end of the data, not rule exits.
- **Costs**: the cost scenarios are assumptions. Real fees and spreads (BNB/USDT may differ from BTC/USDT) are not in the files, so I cannot say which scenario matches real trading.
- **Data**: one exchange's history, with gaps tolerated and not filled (limit 48 hours).
- **Look-ahead and recursion**: both checks passed (`lookahead_has_bias` false, `recursive_is_stable` true). They do not test live behavior.

This lab never approves live trading, and nothing here is a sizing or going-live recommendation.
