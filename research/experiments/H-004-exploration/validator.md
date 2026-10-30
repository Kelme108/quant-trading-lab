# Validator report: H-004 exploration

Files read: strategy `user_data/strategies/SlowTimeSeriesMomentum_H004_v1.py`, `research/proposals/H-004.json`, `facts.json`, `crosscheck.json`, the three `trades-*.csv`, `lab/config/gates.json`. I did not read `research/validation-protocol-v2.md`, the manifests, or the Freqtrade export zip.

## Findings

### 1. [warning] The 7-day cooldown looks inactive in the trade lists
- The proposal says there is no re-entry until 168 bars (7 days) after any exit. The strategy declares `CooldownPeriod` with 168 candles (strategy lines 30-32).
- Several re-entries come before 7 days have passed:
  - `trades-btc-usdt.csv`: exit 2023-03-09 19:00, next entry 2023-03-14 13:00 (about 4.75 days).
  - `trades-eth-usdt.csv`: exit 2023-02-13 10:00, next entry 2023-02-16 16:00 (about 3.2 days).
- Backtests only apply protections if the run enables them, so the backtest probably ran without cooldown. I cannot confirm this from the files I read.
- The tested rule therefore differs from the proposal. The affected re-entries: BTC 2023-03-14 (+35.9), ETH 2023-02-16 (-234.0).

### 2. [warning] The "200-day" SMA is not 200 days at the start of the data
- `regime_sma = close.rolling(4800, min_periods=1440).mean()` (strategy line 37). The proposal says SMA(4800 bars).
- Early in the data the filter is really a 60-199 day average.
- The earliest trades probably used this shorter filter (data start inferred from first entry dates, not checked): BTC 2017-10-20 (+79.3), ETH 2017-11-19 (+102.1), BNB 2018-01-05 (-15.3).
- This is likely related to `recursive: FAIL` (`facts.json`, `recursive_is_stable=false` on all three pairs). The indicator value depends on how much history is loaded.
- The strategy comment (lines 26-28) acknowledges the shortcut. It is not in the proposal.

### 3. [warning] The stop is not checked on closed bars, as the proposal says
- The proposal says the 15% hard stop is "checked on closed bars". The code uses Freqtrade's `stoploss = -0.15`, which triggers intrabar.
- Every `stop_loss` exit shows about -15.3% (for example `profit_ratio` -0.15297 in `trades-btc-usdt.csv` row 2). Several stop-outs are very quick (ETH 2018-05-06 to 05-07, 1860 min; BNB 2018-03-24 to 03-26, 2160 min).

### 4. [warning] A few trades carry most of the profit
Trade figures are `profit_abs` from the trades CSVs. Net profit is from `facts.json`.

| Pair | Best trade | Net profit (base) | Share |
|---|---|---|---|
| BTC | 930.26 (+294%, Oct 2020 to Apr 2021) | 1906.2 | 49% |
| ETH | 1398.05 (+332%, Nov 2020 to May 2021) | 1495.8 | 93% |
| BNB | 1472.34 (+1032%, Dec 2020 to May 2021) | 2045.7 | 72% |

- All three big winners fall in the same 2020-21 bull run.
- By simple subtraction, ETH without its best trade is only 97.8 (1495.8 - 1398.05).
- ETH: 8 of 15 trades are losses or flat (`profit_ratio` <= 0.004). BNB: 12 of 16 are. BTC: 4 of 13 are losses.

### 5. [warning] `net_profit_excl_best_trade` does not match simple subtraction
| Pair | Net profit (base) | Best trade | Simple remainder | Stored excl. best (`facts.json`) |
|---|---|---|---|---|
| BTC | 1906.2 | 930.26 | 976.0 | 407.48 |
| ETH | 1495.8 | 1398.05 | 97.8 | 268.08 |
| BNB | 2045.7 | 1472.34 | 573.4 | 89.42 |

- The stored values differ from simple subtraction, in both directions. Compounded stake (the first trades are sized at ~100, later ones at 1000+) could explain this if the metric re-simulates, but I cannot verify the method from the files I read.
- BNB is the largest gap (89.4 stored vs 573.4 simple) and its stored value is close to zero.

### 6. [note] Stored numbers agree with the crosscheck
- `crosscheck.json`: trade counts (13/15/16) and net profit match for all three pairs (`matches: true`).
- CSV row counts match: BTC 13, ETH 15, BNB 16.
- Durations are in minutes and agree with the open and close dates (example: BTC trade 1, 126120 min = 87.6 days, 2017-10-20 20:00 to 2018-01-16 10:00).
- Exit reasons are only `tsmom30_breakdown` and `stop_loss`. No ROI exits (consistent with `minimal_roi` 100).

### 7. [note] No forward-looking indexing found
- `entry_high` uses `.rolling(1440).max().shift(1)` and `exit_low` uses `.rolling(720).min().shift(1)`. The current candle is excluded and no centered windows are used.
- The SMA includes the current close; the proposal says SMA of close, not "prior".
- `lookahead_has_bias=false` for all pairs (`facts.json`).
- Lookbacks match the proposal: 1440, 720, 4800 (with the min_periods caveat), -15% stop, 168-bar cooldown (not visibly applied, finding 1).

### 8. [note] Low trade counts and correlated trades
- Counts are 13, 15 and 16 (`facts.json`), below the 30-trade minimum. They are identical across cost scenarios on each pair, which is expected for fixed signals.
- Several exits fall on the same bar across pairs (2021-09-21 01:00 on BTC, ETH and BNB; 2023-03-09 on BTC and ETH). The pairs are not independent samples.
- Drawdown differs widely: BTC 7.8%, ETH 36.7%, BNB 42.1% (base, `facts.json`).

### 9. [note] Gate outcome
- All three pairs are `rejected` in `facts.json`. Reasons: recursive fail on all three, and drawdown above 25% on ETH and BNB. I make no judgement beyond the evidence above.
- A stray empty-content file `validator.md.tmp` was created in this directory by mistake. It can be deleted.
