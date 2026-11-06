# Validator report: H-040 exploration

Files checked: `user_data/strategies/DailyNR7Breakout_H040_v1.py`, `research/proposals/H-040.json`, `research/experiments/H-040-exploration/facts.json`, `crosscheck.json`, `trades-bnb-usdt.csv` (first 29 trades read), a count of `trades-btc-usdt.csv`, and `lab/config/gates.json`. I did not read `research/validation-protocol-v2.md`. I did not open the ETH trade list, and I read the BTC list only as a count (95 lines), not its contents.

## Findings

1. **warning: signals that fire while a position is open reset the exit state. This differs from the proposal.**
   - Evidence: `DailyNR7Breakout_H040_v1.py` lines 56-63. `first_of_day` is computed for every NR7 breakout day, whether or not a position is open.
   - `bars_since_signal` and `entry_nr7_low` are re-marked and forward-filled at each such signal.
   - Freqtrade ignores the entry, but the strategy still moves the 48-bar clock and the NR7-low exit level to the newer signal.
   - The proposal says the exit uses "the NR7 day that triggered the entry" and "48 1h bars elapsed since entry". The code departs from both whenever a new signal occurs during a trade.
   - Trade list evidence in `trades-bnb-usdt.csv`: exit reason `time_exit_48` with durations far above 2880 min (48 h).
     - 2019-01-05: 5220 min.
     - 2019-05-13: 14940 min, about 10 days, profit_ratio +0.397.
     - 2019-06-19: 4620 min.
     - 2020-05-17: 3960 min.
   - Normal trades show exactly 2880 min.
   - These stretched holds contradict the "at most 2 days" claim in the proposal's `novelty_vs_tried`.
   - The stretched holds can also include exit-level changes that were not specified.
   - I did not check how many trades are affected on BTC or ETH.

2. **warning: BNB profit depends on one trade.**
   - `facts.json` BNB: `net_profit_quote__base` = 39.38, but `net_profit_excl_best_trade__base` = 5.36 (compounded, per `crosscheck.json`).
   - The best trade is probably the 10-day, +39.7% trade from finding 1. It is the largest `profit_ratio` in the rows I read, but I did not scan the whole list.
   - Stress scenario: `net_profit_excl_best_trade__stress` = -11.97.
   - Conservative scenario: excl-best = 0.71, only marginally positive.
   - The gate passes (5.36 > 0), but only narrowly.
   - BTC (36.76 of 58.05) and ETH (27.86 of 37.70) hold up much better without their best trade.

3. **note: stored numbers match the recomputation.**
   - `crosscheck.json` reports `matches: true` for all three pairs.
   - Trade counts agree: BTC 95, ETH 80, BNB 87.
   - Net profit agrees: BTC 58.0539, ETH 37.6956, BNB 39.3806.
   - Excl-best agrees: BTC 36.7606, ETH 27.8619, BNB 5.3576.
   - Trade counts are identical across the four cost scenarios on each pair (`facts.json`). This is expected for a fixed-signal strategy with no cost-dependent logic.
   - Counts are well above the 30-trade floor in `gates.json`.

4. **note: the rest of the logic matches the proposal, and I found no forward-looking code.**
   - NR7 (lines 34-40): strict `<` against the 6 prior days (`shift(1)` to `shift(6)`), and it requires history.
   - SMA50 is the rolling mean of daily closes. It includes day D, which the proposal allows ("computed at D").
   - Informative 1d data uses Freqtrade's `@informative` merge. Day D+1 sees day D's values only after D has closed.
   - Entry:
     - Close above `high_1d`.
     - Hour <= 19.
     - Close above SMA50.
     - First qualifying bar per day.
     - Entry executes at the next open.
   - Exits:
     - Close below `low_1d`.
     - Bar 48 after the signal bar. This equals 48 bars after entry, and normal trades show exactly 2880 min.
   - Stop is -3%. Stop-loss trades show about -3.34% after fees and slippage (`trades-bnb-usdt.csv`). This is consistent.
   - `minimal_roi` is set to 100 (inactive). `can_short` is False.
   - Lookahead and recursive checks both pass in `facts.json`.

5. **note: exposure is 0.35 for all pairs in `facts.json`.**
   - I did not verify it against the proposal's bootstrap rule, because the derivation is not in these files.

6. **note: the time exit and the NR7-low exit are written as separate `loc` assignments.**
   - If both coincide on one bar, the exit tag reads `time_exit_48`. This is cosmetic.
   - Several BNB trades in the first rows show a negative return on `time_exit_48` (2018-05-03, -1.5%), which is plausible.
