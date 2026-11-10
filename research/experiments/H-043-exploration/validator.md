# Validator report: H-043 exploration (HourlyWilliamsVolBreakout_H043_v1)

Files read: `user_data/strategies/HourlyWilliamsVolBreakout_H043_v1.py`, `research/proposals/H-043.json`, `research/experiments/H-043-exploration/facts.json`, `crosscheck.json`, `trades-*.csv` (9 pairs; read the first 40 BTC rows, plus grep counts and large-winner lines for all pairs), `lab/config/gates.json`, `lab/config/splits.json`, `research/validation-protocol-v2.md` (cost section only). I did not read `quant.md` or `risk.md`. I could not re-run the backtest. Checks of the code against the rule are by reading only.

## 1. Code vs. proposal rule

The code matches the proposal on every parameter I could compare:
- Trigger: `level = day_open + 0.6 * prev_range` (strategy lines 80-82; `trigger_multiple` 0.6).
- Range filter: `prev_range / day_open >= 0.02` (line 86 and the entry condition).
- Entry window: hours 01:00-18:00 inclusive (`first_hour=1`, `last_hour=18`).
- Stop-exit level: `O - 0.5 * R` on a bar close (lines 83-84, 111-113).
- Midnight exit: the signal on the 23:00 bar fills at the 00:00 open (`time_exit_hour=23`). The proposal's own parameter table says `time_exit_hour_utc: 0`, but its rule text says the 23:00 bar signals and the sale is at the 00:00 open. The code follows the rule text. This is a labelling inconsistency in the proposal JSON, not a behavioural difference.
- Native stop: `stoploss = -0.05`, `minimal_roi = {"0": 100.0}`, so the ROI never fires. Warm-up is 1300 bars.
- Trade durations of 300-1320 minutes with `midnight_flat` exits at 00:00 are consistent with the rule.

Small deviations and items to note:
- **note.** The completeness filter is stricter than the proposal. Days without all 24 bars are NaN (`complete = daily["n"] == 24`). The SMA(50) is a rolling window over a calendar-day index, so any incomplete day among the last 50 gives NaN and no entries. This can only remove signals, never add them. The proposal does not mention it.
- **note.** One entry per day is `first = cond & (order == 1)`, where `cond` does not include "no open position". Because every position is closed by midnight, this is equivalent to the rule. After an exit on the same day there is no re-entry, as the proposal says.
- **note.** The `volume > 0` condition on entry and exit is not in the proposal. It is harmless.
- **note.** `stop_hit` takes priority over `time_exit` for the exit tag only. The bar at which the position closes is the same either way.

## 2. Look-ahead / information available at signal time

I found no forward-looking use of data in the code.
- `prev_range` and `prev_trend` are `.shift(1)` on the calendar-day index. The prior day's high/low and 23:00 close are used only from the next day onward.
- The SMA(50) of 23:00 closes includes day D-1, not day D, because the shift happens after the rolling mean.
- `day_open` is the 00:00 bar open of the current day, which is known from 00:00. It is used only on bars with hour >= 1.
- There are no centered windows, no negative shifts, and no `.shift(-n)`. The current candle's own close is compared with a level built only from earlier information (`day_open` and `prev_range`).
- The `groupby` over the whole dataframe computes the current day's high/low/n. These values are used only after the one-day shift, so the current day's aggregates never reach a signal.
- Freqtrade's own lookahead and recursive checks report `has_bias=false` and `is_stable=true` for all 9 pairs (`facts.json`, `metrics.lookahead_has_bias` and `recursive_is_stable`).

Execution-time caveat (**note**): the stop-loss exits with `duration 0` (for example BTC 2017-11-02 11:00 -> 11:00, -5.28%, and 2017-12-07 11:00 -> 11:00, `trades-btc-usdt.csv` lines 7 and 19) are entry-candle intrabar stop hits. This is the engine's normal behaviour for a native stop. The realised loss is about -5.28%, which is the 5% stop plus costs, so the stop is filled at its level, with no gap slippage beyond the cost model.

## 3. Stored numbers vs. crosscheck and trade lists

- **No mismatch.** All 9 pairs have `matches: true` in `crosscheck.json`. Trade counts agree (BTC 249, ETH 262, BNB 292, XRP 196, ADA 217, LTC 247, LINK 257, DOGE 176, SOL 194). Net profit stored equals net profit from the trade list; differences are floating-point only (for example LINK -0.0516755 vs -0.0516755). Net profit excluding the best trade, recomputed by compounding, equals the stored value.
- Exit-reason counts from grep of `trades-*.csv` sum exactly to the trade counts, for example BTC 6 (`below_open_minus_half_range`) + 17 (`stop_loss`) + 226 (`midnight_flat`) = 249. The same holds for ETH 3+29+230, BNB 7+38+247, XRP 2+40+154, ADA 3+36+178, LTC 2+52+193, LINK 4+51+202, DOGE 1+54+121, SOL 1+56+137.
- The trade count is identical across the four cost scenarios on every pair (`facts.json`, `trades__*`). This is expected, because costs do not change signals in this strategy. It is not a defect.
- **note.** `below_open_minus_half_range` accounts for only 1-7 trades per pair. A close at or above 0.6R over the open followed by a close below 0.5R under the open on the same day is rare, and the 5% stop usually triggers first. The 0.5R exit is therefore almost inert, and the strategy is effectively "breakout, then 5% stop or midnight".
- **note.** The stored `exposure` is 0.15 for every pair (`facts.json`). I did not verify it against the trade list.

## 4. Reliability of the result

- **warning: results differ strongly between pairs.** Base net profit in USDT on 1000 USDT: BNB +317.8, ETH +184.1, BTC +150.0, DOGE +103.0, ADA +89.1, XRP +76.4, LINK -0.05, LTC -47.6, SOL -89.5 (`facts.json`). Three of nine pairs are `rejected` (LTC, LINK, SOL), each failing net-profit and excl-best-trade gates. The six candidates are not uniformly strong (see next item). The SOL stop-loss share is 56/194 and LTC 52/247, which is much higher than BTC (17/249).
- **warning: single-trade dependence on the weaker candidate pairs.** The gate threshold is only "excl-best > 0".
  - DOGE: base 102.97 falls to 14.35 without the best trade (`facts.json`). Three trades of +30%, +58%, +56% (2020-07-08, 2021-01-02, 2021-04-16) drive the result (`trades-doge-usdt.csv` lines 31, 57, 77).
  - XRP: 76.4 falls to 26.3. The best trade is +32% on 2021-04-05 (`trades-xrp-usdt.csv` line 103).
  - ADA: 89.1 falls to 50.2. The best trade is +24.6% on 2021-02-10 (`trades-ada-usdt.csv` line 107).
  - BNB: the +47% (2018-01-05) and +43% (2021-02-19) trades are large (`trades-bnb-usdt.csv` lines 2 and 151). Excluding only the single best leaves 230 of 317.8.
  - Removing the best trade does not give a full picture. Removing the second and third best on DOGE would very likely turn it negative, but I did not compute that, so treat it as unverified.
  - The profit is concentrated in the Nov 2020 - Apr 2021 bull-market episode, and in Jan 2018 for BNB. I did not compute a by-year breakdown for all pairs.
- **warning: thin cost margin.** At conservative cost, excl-best is -17.8 (XRP), -24.7 (DOGE), +0.33 (ADA), and positive for BTC +69.4, ETH +85.0, BNB +151.9 (`facts.json`). At stress, 8 of 9 pairs have negative net profit; only BNB is +12.4. Stress is reported, not gating (`gates.json` `max_drawdown` amendment). Round-trip costs bite on a strategy that trades 176-292 times with roughly 0.35% base round-trip cost.
- **warning: drawdown versus win-rate shape.** The base drawdown is moderate (BTC 5.3%, ETH 4.4%, BNB 8.9%, XRP 12.4%, ADA 13.4%, DOGE 16.0%), all under the 25% gate in optimistic, base and conservative. The drawdown gate does not distinguish the pairs here.
- **note: trade count and distribution.** Trade counts (176-292 over about 6.9 years) are well above 30. They are not suspiciously equal across pairs. BTC has 216 of 249 trades dated 2019 or later, so BTC is not dominated by the 2017 start.
- **note: the proposal expected 60-100 trades per year per pair.** The actual count is roughly 25-45 per year, about a third to half of that. This is a difference between expectation and outcome and does not affect validity.
- **note: benchmark.** Buy-and-hold over the split is +1253% (BTC), +930% (ETH), +33024% (BNB), -53% (XRP), +36% (ADA), -76% (LTC), +2375% (LINK), +2576% (DOGE), +4232% (SOL). The strategy trails buy-and-hold on every pair except XRP and LTC (where the benchmark is negative). Beating the benchmark is not a gate.
- **note: multiple testing.** The decision text reports 0 prior variants in the family, so the bar is 10.0. This was not examined here beyond the `facts.json` text.

## Summary

No blocking finding. The code implements the proposal's rule with no look-ahead that I can find, and the stored numbers agree with the crosscheck and the trade lists on all 9 pairs. The warnings above are about robustness. These are mixed results across pairs, profit concentrated in a few large bull-market winners on DOGE, XRP and ADA, and negative results at stress cost on 8 of 9 pairs. The gates decide.
