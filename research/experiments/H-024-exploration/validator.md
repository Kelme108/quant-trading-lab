# Validator report: H-024 exploration

Files checked: `user_data/strategies/DailyMaxJumpMomentum_H024_v1.py`, `research/proposals/H-024.json`, `research/experiments/H-024-exploration/facts.json`, `crosscheck.json`, `trades-btc-usdt.csv`. I read only the first 12 rows of `trades-eth-usdt.csv`. I did not open `trades-bnb-usdt.csv`, `lab/config/gates.json` or `research/validation-protocol-v2.md`.

## Findings

1. **warning: entry is level-triggered, but the proposal says edge-triggered.**
   - The proposal says to enter "when a daily candle closes with" the conditions true. The code (`populate_entry_trend`) sets `enter_long` on every 1h row where the forward-filled daily conditions hold.
   - So a daily signal that was blocked by the 72-candle cooldown can still fire later, up to about 24h after the day's close. In the BTC list, `trades-btc-usdt.csv` shows entries at 01:00 on 2019-03-08, 2020-01-29 and 2023-04-11. These are one hour after the cooldown expired, not at a daily close.
   - Entries are otherwise at 00:00 UTC, as expected. The effect is small, and I found no lookahead from it.

2. **note: everything else matches the proposal.**
   - 30-day MAX is `rolling(30)` of daily returns, including day d.
   - The median of the 150 prior MAX values is `max30.shift(1).rolling(150).median()`, which excludes today.
   - SMA50 and SMA20 include d.
   - The 10-day high is `close.shift(1).rolling(10).max()`, which excludes d.
   - The stop is a native `stoploss = -0.12`, ROI is effectively off, the cooldown is 72 candles, and `startup_candle_count` is 4400.
   - I found no parameter added or missing.

3. **note: no forward-looking indexing found.**
   - There are no negative shifts and no centered windows.
   - The `@informative("1d")` merge makes the daily value visible only after the day closes.
   - Trade open times fall at 00:00 UTC, which is the open after the daily close.
   - `lookahead_has_bias=false` and `recursive_is_stable=true` for all three pairs (`facts.json`).

4. **note: stored and recomputed numbers agree.**
   - `crosscheck.json` reports `matches: true` for all three pairs.
   - Trade counts are BTC 43, ETH 36 and BNB 39. Net profit is BTC 99.31, ETH 44.53 and BNB 189.69, identical to the trade-list totals.
   - Trade counts are the same across the four cost scenarios in `facts.json`, which is expected for a fixed signal rule.
   - Trade counts differ across pairs, so they are not suspiciously equal.
   - Durations in the BTC trade list are multiples of 60 minutes, and the exit reasons are only `close_below_sma20` and `stop_loss`.
   - The stop-loss exits show ratios of about -0.123 (e.g. BTC 2021-05-12 and ETH 2018-12-25), which is consistent with a 12% stop plus fees.

5. **warning: the excl-best-trade method string does not obviously fit the 25% exposure.**
   - `crosscheck.json` describes the metric as `starting_balance * product(1+profit_ratio)` and says it assumes a whole-balance stake.
   - The trade lists look like a fixed 25% stake. BTC trade 1 has a profit_ratio of 0.0332 and a profit_abs of 0.83, which implies a stake of about 25 on a balance of 100.
   - Compounding the BTC profit ratios at full size by eye would give a total well above the stored 99.31 net. The stored `net_profit_excl_best_trade__base` is 65.38.
   - I could not reproduce that figure without running code, so I do not know whether the ratios were rescaled. Someone should confirm the method matches the 25% stake.

6. **warning: profit is concentrated in a few large trades.**
   - BTC: `profit_ratio` is 0.665 on 2019-04-03, 0.82 on 2020-12-16, 0.50 on 2024-01-30 and 0.43 on 2020-10-22. Most of the other 39 trades are small or negative.
   - Excluding the best trade, BTC profit falls from 99.31 to 65.38, ETH from 44.53 to 22.80 and BNB from 189.69 to 56.75 (`facts.json`).
   - BNB loses about 70% of its profit without its best trade.
   - The gate passes because it only requires the excl-best value to be positive. This matches the hit-rate risk the proposal itself notes.

7. **note: results differ across pairs but all are positive.**
   - BNB (189.69) is much larger than BTC (99.31) and ETH (44.53).
   - All pairs are positive at all four cost scenarios, and the drawdown is at most 12.7%.

8. **note: the exposure of 0.25 is stored for all pairs.** I did not verify the exposure rule's bootstrap derivation. I only confirm that `facts.json` shows 0.25 for each pair.
