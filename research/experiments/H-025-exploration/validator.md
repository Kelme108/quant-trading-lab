# Validator report: H-025 exploration

Checked: the strategy `user_data/strategies/DailyKeltnerBreakout_H025_v1.py`, `research/proposals/H-025.json`, `facts.json`, `crosscheck.json`, and the BTC and BNB trade lists. I did not open `trades-eth-usdt.csv`, `research/validation-protocol-v2.md` or `lab/config/gates.json`. The ETH numbers below come from `facts.json` and `crosscheck.json` only.

## 1. Code vs. proposal
- **note**: Every parameter matches the proposal.
  - EMA alpha 2/21 with `adjust=False` (seeded with the first close).
  - Wilder ATR20 seeded with the mean of the first 20 TRs.
  - TR uses the previous close.
  - Band = EMA20 + 1.5 ATR20.
  - SMA100 includes day d.
  - Fresh-cross condition as specified.
  - Exit when daily close < EMA20.
  - `stoploss` = -0.08.
  - `minimal_roi` = 100 (effectively off).
  - `startup_candle_count` = 3700.
- **warning**: Re-entry after a stop-out on the same signal day. This is not in the proposal.
  - `fresh_cross_1d` stays 1.0 on every 1h candle of the day after the signal day. After a stop-loss, the entry condition is still true and the strategy re-enters at the next hour.
  - Evidence in `trades-btc-usdt.csv`:
    - 2018-04-25 00:00 stop at 14:00, then re-entry at 15:00.
    - 2020-06-02 00:00 stop at 15:00, then re-entry at 16:00.
    - 2022-09-13 00:00 stop at 18:00, then re-entry at 19:00. That trade exited on 2022-09-14 00:00 via `close_below_ema20` after 5 hours (300 min).
  - Evidence in `trades-bnb-usdt.csv`:
    - 2018-04-25 00:00 stop, then re-entry at 11:00.
    - 2020-11-25 22:00 stop, then re-entry at 23:00 (stopped again at 03:00).
    - 2021-03-31 00:00 stop at 08:00, then re-entry at 09:00. This became the +98% trade.
  - The rule describes one entry per fresh daily cross. The code lets one signal produce several entries.
  - These extra entries add to the trade counts. BTC has 33 trades, so counting each signal once would leave about 29 to 30 against the 30-trade gate. This needs checking.
- **note**: Exit tags use the same daily flag. Daily-driven exits close at 00:00, as expected for a signal on a closed day.

## 2. Look-ahead
- **note**: No forward indexing or centered windows.
  - All shifts are positive (`shift(1)`).
  - The previous band is compared against the previous close.
  - The 1d values come through the `@informative` decorator, which merges with a lag.
  - Entry timestamps are all 00:00, i.e. the first hour after the signal day closed.
  - `facts.json` reports `lookahead_has_bias=false` and `recursive_is_stable=true` for all three pairs.
- **note**: The first trade on both BTC and BNB opens on the same bar, 2018-04-25 00:00 (the same calendar day on two pairs). This is plausibly the start of the data or warm-up window rather than a bug, but I did not verify it. Both of those trades were stopped out within hours.

## 3. Stored numbers vs. crosscheck
- **note**: Trade counts, net profit and net profit excluding the best trade all match, with `matches: true` for all three pairs.
  - BTC: 33 trades, 56.778 (`crosscheck.json`).
  - ETH: 33 trades, 55.709 (`crosscheck.json`).
  - BNB: 41 trades, 138.513 (`crosscheck.json`).
- **note**: Exit reasons and durations are plausible.
  - Only `stop_loss` and `close_below_ema20` appear.
  - Stop trades realise about -8.32%, which is the 8% stop plus fees and slippage.
  - A few BNB stops are slightly different (-8.305% to -8.320%), consistent with gaps.
  - `trade_duration` is consistent with the open and close dates.
- **note**: The BNB drawdown fields differ. `max_drawdown_pct__base` is 7.05 and `max_relative_drawdown_pct__base` is 8.54 (`facts.json`). The gate used the 8.54 figure, which is the more conservative of the two. Both are well under 25%.

## 4. Reliability
- **warning**: BNB profit is concentrated in a few trades.
  - The best trade is +381% (2021-02-02 to 2021-03-25), +84.7 of the 138.5 total.
  - The next trade is +98% (+38.0).
  - Excluding the best trade, BNB falls to 35.26 (`facts.json`), versus 39.9 for BTC and 38.5 for ETH.
  - BNB's headline profit is about 4 times the other pairs' only because of that one trade and the one after it.
- **warning**: Low hit rate with a trend-dependent profile.
  - BTC: 13 of 33 trades are losses, and 8 of those are stop-losses.
  - BNB: 22 of 41 trades are losses, and 18 of those are stop-losses.
  - The profit comes from a few large trades, e.g. BTC +58%, +60% and +44%. This matches the proposal's own caveat.
- **note**: Trade counts are identical across the four cost scenarios (33, 33, 33, 33 on BTC and ETH; 41 on BNB). This is expected for a fixed signal with only fee and slippage changes. BTC and ETH both have exactly 33 trades, which is a coincidence worth noting but is not shown to be an error.
- **note**: Exposure is 0.2 for all pairs, and the stake in the trade lists is about 20% of the balance.
  - Evidence: BTC's first trade has profit_abs -1.66 for a -8.32% result.
  - The exposure rule itself (bootstrap p95 drawdown) was not checked, since I did not read the protocol or gates files.
- **note**: The stored buy-and-hold benchmarks are very large (BTC 1253%, ETH 930%, BNB 33024%). The strategy trails them by a large margin, but the gates say beating the benchmark is not required.
