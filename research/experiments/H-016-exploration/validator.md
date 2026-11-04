# Validator report: H-016 exploration

Files read: facts.json, crosscheck.json, trades-btc-usdt.csv (first 24 rows), trades-bnb-usdt.csv (all rows), the strategy file `user_data/strategies/_archive/TimeSeriesMomentum_H016_v1.py`, and lab/config/gates.json. I did not open trades-eth-usdt.csv or the manifests. I did not read research/validation-protocol-v2.md. I did not run any analysis myself.

## Findings

1. **warning: the proposal could not be compared with the code.**
   - `research/proposals/H-016.json` does not exist. Glob `research/proposals/H-016*` returned nothing.
   - Check 1 (code vs proposal) is therefore incomplete. The only statement of the rule I had is the strategy docstring (lines 1-17).

2. **note: the code matches its own docstring, with one inconsistency.**
   - Rule: long when close(d)/close(d-30) - 1 > 0 on a closed daily candle; exit when that is no longer true (`N_DAYS = 30`, `USE_REGIME = False`, lines 25-26).
   - The ROI and stop never act: `minimal_roi = {"0": 100.0}` and `stoploss = -0.99`. Exit reasons in the BNB list are all `tsmom_not_positive`, except the last trade (finding 7).
   - The docstring (lines 11-12) says "Regime (USE_REGIME = True)", but the constant is False. The regime branch is inactive. The regime column is still computed and merged.
   - `volume > 0` is added to entry and exit. This is not in the stated rule and is harmless.

3. **note: I found no look-ahead in the code.**
   - `shift(n_days)` looks only backward.
   - `merge_informative_pair(..., ffill=True)` shifts the daily candle so it is usable only after it closes.
   - Every trade in trades-btc-usdt.csv and trades-bnb-usdt.csv opens and closes at 00:00 UTC, or at an hourly boundary on the force-exit. Durations are multiples of 1440 minutes. That fits a daily signal executed at the next 1h open.
   - facts.json shows `lookahead_has_bias` false and `recursive_is_stable` true for all pairs. I did not re-run these.

4. **note: stored numbers agree with the recomputation.**
   - crosscheck.json has `matches: true` for all pairs.
   - BTC: 94 trades, net profit 150.239 stored and from the trade list; excluding the best trade 77.886.
   - ETH: 89 trades, 115.186; excluding the best trade 69.742.
   - BNB: 96 trades, 516.959; excluding the best trade 201.538.
   - BNB's trade list has 96 data rows, matching the stored count.
   - The net-profit bar of 1.1 is gates.json's 1.0 × (1 + 0.1 × 1 prior variant), as the facts.json reason strings say.

5. **warning: profit is concentrated in a few large trend trades.**
   - BTC: the best trade is +209% (2017-10-09 to 2018-01-10, profit_abs 31.5, in trades-btc-usdt.csv). Without it, profit falls from 150.2 to 77.9.
   - BNB: the 2021-03-22 trade is +695% (profit_abs 233.3) and the 2019-07-01 trade is +437% (81.3), in trades-bnb-usdt.csv. Without the best trade, profit falls from 517 to 202.
   - ETH: profit falls from 115.2 to 69.7 without its best trade.
   - The excluding-best gate passes, but most of the profit comes from a handful of trades. Most short trades are small losses (whipsaws), as in the BTC rows 3-24.

6. **warning: results differ a lot between pairs, and the strategy earns far less than buy-and-hold.**
   - BNB's profit is 3.4 times BTC's (517 vs 150, facts.json). The buy-and-hold figures are 33,023% for BNB, 1,253% for BTC and 930% for ETH.
   - `exposure` is 0.15 for all three pairs and all scenarios in facts.json. It looks like a constant and not a measured value. I could not verify it.
   - Trade counts are identical across the four cost scenarios (94, 89, 96). That is expected for a signal-only exit. The base-to-stress profit gap is small (BTC 150.2 to 129.5).

7. **note: large single-day losses and a forced exit.**
   - BNB 2021-05-19 to 2021-05-20 lost 34.3% in one day (profit_abs -28.5). BNB 2021-06-21 lost 20.4%. With no stop, a daily-close exit can take large gaps.
   - The last BNB trade (2024-07-24 to 2024-07-25 06:00) has exit reason `force_exit`. It is an open position closed at the end of the data, not a signal exit.
   - Reported max drawdowns are 9.7% to 15.5% in facts.json, well under the 25% gate.

8. **warning: selection and the multiple-testing count.**
   - The docstring says N = 30 was chosen from a 10-variant grid (H-015) on this same exploration split. This exploration result is therefore partly in-sample for the selection.
   - The gate reasons count only 1 prior variant in the family (facts.json). I could not confirm how the family count is defined, so the penalty may be under-counted.
   - Validation experiments for H-016 (`research/experiments/20261104T004354Z-h-016-validation-*`) already exist, about 9 minutes after these exploration runs (003454Z). I did not read them.

## Blocking

None found from the files I read. Finding 1 (no proposal file) is the main gap in this review.
