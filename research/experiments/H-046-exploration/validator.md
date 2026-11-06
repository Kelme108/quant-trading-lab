# Validator report: H-046 exploration

Checked: `user_data/strategies/LivermorePivotFailFast_H046_v1.py`, `research/proposals/H-046.json`, `research/experiments/H-046-exploration/facts.json`, `crosscheck.json`, and the three trade CSVs (BNB and BTC only the first ~25–40 rows plus exit-reason counts). I did not open `gates.json` or `validation-protocol-v2.md`. I did not read the trade lists in full, and I did not run anything.

## 1. Code vs proposal: no differences found
- Pivot: `high.rolling(240).max().shift(1)` is the highest high of bars t-240..t-1. This matches the proposal.
- Volume: `volume.rolling(48).mean().shift(1)` excludes the current bar. The test is `>= 2.0x`, as in the proposal.
- Entry: `close > 1.002*pivot`, `close > SMA480` (current bar included, which the proposal also specifies), and `volume > 0`. The `volume > 0` check is an extra but harmless guard.
- Fill timing: Freqtrade enters at the next open by default.
- Stop and ROI: `stoploss=-0.04` is native. `minimal_roi={"0":100}` effectively disables ROI. There is no take-profit.
- Cooldown: `CooldownPeriod` with 12 candles, as proposed.
- Warm-up: `startup_candle_count=600`, as proposed.
- Fail-fast exit: in `custom_exit`, `signal_date = open_date - 1h` and `n = last_closed_bar - signal_date`.
  - For n=1..8 it exits if `close < pivot` of the signal bar. The pivot is read from the signal row, so it is fixed for the trade.
  - For n>=9 it exits if `close < trail_low`, where `trail_low` is shifted by 1, so the current bar is excluded.
  - The window is bars t+1..t+8 and the trail starts at t+9. Both match the proposal.
- Only closed candles are used: `date + 1h <= current_time`.
- Exit fills at the next open. This is consistent with the 60-minute minimum duration of `fail_fast_pivot` trades in the CSVs, for example BNB 2017-12-07 13:00→14:00 in `trades-bnb-usdt.csv`.
- **note**: In the proposal, the stop applies to every bar, including bars t+1..t+8. The code does the same through the native stop.

## 2. Look-ahead
- No forward indexing, no centered windows, and no unshifted level in comparisons. All "prior" levels (pivot, vol_avg, trail_low) are shifted by 1.
- `facts.json` reports `lookahead_has_bias=false` and `recursive_is_stable=true` for all three pairs.
- **note**: The `custom_exit` lookup uses `get_analyzed_dataframe` filtered to closed candles. This looks correct. The Freqtrade lookahead check cannot fully test custom_exit logic, so the code reading above is the main evidence.

## 3. Numbers vs crosscheck
- Trade counts match `crosscheck.json`: BTC 130/130, ETH 139/139, BNB 136/136.
- Net profit matches: BTC 44.7758, ETH 45.0423, BNB 63.9606, stored vs trade list. Net profit excluding the best trade also matches the recomputation.
- The CSV row counts (131/140/137 lines including the header) are consistent with these counts.
- Exit reasons are plausible: `stop_loss`, `fail_fast_pivot` and `trail_48_low`.
- Stop-loss exits show about -4.335% (the 4% stop plus fees). Many stop-losses have a duration of 0 minutes, meaning the stop was hit within the entry candle. See `trades-bnb-usdt.csv` rows such as 2017-12-25 and 2018-01-05. This is plausible for a volume-spike breakout bought at the next open.
- **note**: Some fail-fast exits lose 3–3.7%, for example BNB 2017-12-07 (-3.4%) and 2018-10-03 (-3.7%) in `trades-bnb-usdt.csv`. The rationale expected losses of about 0.5–1%. Large gaps between the signal close and the next open, or between the close and the next-open exit, defeat the intended loss cap.
- **note**: `exposure` is 0.2 for all three pairs in `facts.json`. This looks like a placeholder or stake-fraction value rather than a measured time in market. Do not interpret it as exposure.

## 4. Reliability concerns
- **warning**: BNB/USDT profit depends on a single trade. `net_profit_excl_best_trade__base` is 0.73 against `net_profit_quote__base` of 63.96 (`facts.json`).
  - Excluding the best trade, the result is negative in the conservative scenario (-3.24) and in the stress scenario (-14.24).
  - The gate's "profit excluding best trade" test passed only because the base value is marginally above zero (+0.73).
  - Whole-balance compounding amplifies this, as the crosscheck method note says. The BNB trades include a few large winners (+22.9%, +25.0%, +17.0% in the early rows of `trades-bnb-usdt.csv`).
- **warning**: Cost sensitivity. In the stress scenario, BTC net profit is 23.9, ETH 22.6 and BNB 39.3. For BTC (16.3) and ETH (12.3), excluding the best trade leaves stress profit small relative to the 100 start balance. Both are still positive.
- **note**: Trade counts are identical across the four cost scenarios for every pair (130, 139, 136). This is expected because the signals do not depend on cost, and is not itself a defect.
- **note**: Counts of roughly 14–15 trades per pair-year (about 9 years) are consistent with the proposal's 10–30/year. All pairs far exceed the 30-trade minimum.
- **note**: The pairs differ in quality. BNB has a larger net profit but the heaviest concentration and drawdowns (13.6% base, 20.4% stress), against 6.0% (BTC) and 6.1% (ETH) base drawdown.
  - ETH stress drawdown is 13.05%, against 6.06% base.
  - The three pairs share the same market regime, so they are not independent evidence.
- **note**: Many trades are small losses and stop-outs. The profit comes from a minority of trend-following winners, for example BTC 2018-04 +16.1%, 2017-10 +13.2%.
- **note**: Every pair is labelled `candidate_for_portfolio` by the gate. The gate itself only tested base-scenario profit excluding the best trade. I make no recommendation, since the gates decide.

No blocking findings.
