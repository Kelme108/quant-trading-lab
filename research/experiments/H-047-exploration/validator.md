# Validator report: H-047 exploration

Files checked: `facts.json`, `crosscheck.json`, `trades-btc-usdt.csv` (first 25 rows read), the exit-reason counts in all three trade CSVs, the strategy file `user_data/strategies/RelativeStrengthRatioRotation_H047_v1.py`, `research/proposals/H-047.json`, and `lab/config/gates.json` (only a grep of it). I did not read `validation-protocol-v2.md` in full.

## 1. Code against proposal
- **note** No substantive differences. The strategy file matches the proposal:
  - Basket: `sqrt(closeA*closeB)` of the other two pairs, and R = close/basket.
  - Entry: R > SMA(480) of R, R >= rolling(120).max() of R including t, and close > SMA(480) of close.
  - Exit: R < SMA(48) of R, or close < SMA(480) of close.
  - Stop: `stoploss=-0.06`.
  - Cooldown: `CooldownPeriod` with 12 candles.
  - Other settings: `startup_candle_count=500`, `minimal_roi={"0":100}` (effectively disabled), long only.
- **note** One addition that the proposal does not list: `volume > 0` in both the entry and the exit condition. It is a Freqtrade convention and is very unlikely to change results.
- **note** One addition: the code requires the indicator values to be non-NaN. This is a warm-up guard.
- **note** `ratio_high` is computed on R itself with a trailing window. The code uses `>=` against it, as the proposal says.

## 2. Look-ahead
- **note** I found no forward-looking indexing. There is no `shift(-n)`, no centered window, and no use of future rows.
  - All windows are trailing `rolling()` calls.
  - Signals use the closed candle at t, and Freqtrade fills at the next open.
  - The "highest of the last 120 bars including t" rule is specified to include t, so using the current candle there is intended and not a leak.
- **note** Informative data are fetched with `dp.get_pair_dataframe` and mapped by exact `date`. This is a same-timestamp alignment of closed candles, so it does not look ahead.
  - Missing timestamps give NaN, and the NaN guard blocks signals there.
- **note** `lookahead_has_bias=false` and `recursive_is_stable=true` for all three pairs (`facts.json`).

## 3. Stored numbers against crosscheck and trade lists
- **note** `crosscheck.json` reports `matches: true` for all three pairs.
  - Trade counts: BTC 174, ETH 223, BNB 211.
  - Net profit: BTC 22.27322524, ETH 15.82644588, BNB 81.28662947.
  - Net profit excluding the best trade: BTC 17.1466, ETH 9.2317, BNB 55.9279, all recomputed identically.
- **note** The first rows of `trades-btc-usdt.csv` look plausible.
  - Durations are consistent with the dates: 2017-11-28 12:00 to 2017-11-29 19:00 is 31 h, which is 1860 min.
  - Stop-loss exits show a profit_ratio of about -0.0633, which is the 6% stop plus costs.
- **note** Exit-reason grep counts for "stop_loss|roi" (these lines can include both words): BTC 12 of 174, ETH 27 of 223, BNB 28 of 211.
  - Most exits are therefore the `ratio_weak_or_regime_lost` signal exit.

## 4. Reliability
- **warning** The result is cost-sensitive. Stress-scenario net profit is negative for BTC (-0.63) and ETH (-11.32), and only BNB stays positive (40.57) (`facts.json`).
  - ETH conservative profit is thin at 8.28, and 2.19 after excluding the best trade.
  - The gates do not test the stress scenario for profit, so the `candidate_for_portfolio` decision does not reflect this.
- **warning** BNB dominates. Its base profit of 81.29 is about 3.6 times BTC's 22.27 and about 5 times ETH's 15.83 (all from `facts.json`).
  - The BNB benchmark buy-and-hold is 33023%, which suggests a very low starting price or a long, favourable history.
  - The pairs differ widely in profit, so the edge looks pair-specific.
- **warning** Profit is small compared with the number of trades. Net profit is 15.8 to 81.3 on a 100 wallet over a multi-year, 174 to 223 trade sample.
  - The profit is small next to the buy-and-hold benchmarks (929% to 33023%).
  - BTC excluding its best trade drops from 22.27 to 17.15 (the best trade carries about 5 of the 22). The early BTC list shows a single +21.8% trade in 2017-12.
- **note** `exposure` is exactly 0.2 for all three pairs and `trades` is identical across the four cost scenarios (`facts.json`). Identical trade counts across cost scenarios are expected, since only costs change.
  - The identical exposure value across pairs is unusual, so I would check whether the stored field is a placeholder. I cannot confirm that from the files I read.
- **note** The proposal expected 15 to 40 trades per year per pair. The actual 174 to 223 trades over the sample is not directly comparable without the split's date range. I did not verify the range.
