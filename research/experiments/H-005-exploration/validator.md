# Validator report: H-005 exploration

Files read: facts.json, crosscheck.json, trades-{btc,eth,bnb}-usdt.csv (all in research/experiments/H-005-exploration/), user_data/strategies/VolatilitySqueezeBreakout_H005_v1.py, research/proposals/H-005.json, lab/config/gates.json. I did not read validation-protocol-v2.md, the manifests, or the raw export zip.

## 1. Code against proposal
No material differences found. Checked each item:
- R(t): `rolling(168)` max(high) − min(low), divided by close. Matches (strategy lines 35-37).
- Squeeze threshold: `rolling(2160).quantile(0.20).shift(1)`. The window ends at t-1 and excludes the current bar. Matches.
- Squeeze in the previous 24 bars: `squeeze.shift(1).rolling(24).max()` covers t-24..t-1. Matches. NaN is propagated, so a bar with any undefined squeeze value in the window cannot enter. This is a conservative warm-up choice, not in the proposal text.
- Breakout level: `high.rolling(168).max().shift(1)`, compared with the current close. Matches "prior 168 bars, excluding current".
- Trend filter: `close.rolling(2400).mean()` includes the current close. The proposal says "close(t) > SMA(2400) of close", so this is consistent.
- Exit: `close < low.rolling(336).min().shift(1)`. Matches.
- Stop: `stoploss = -0.08`. Matches.
- ROI: `minimal_roi = {"0": 100.0}` is effectively disabled. Fine.
- Cooldown: CooldownPeriod with 72 candles. Matches in code.
- Extra condition not in the proposal: `volume > 0` in both entry and exit. It has negligible effect.
- Warm-up: `startup_candle_count = 2400`. Matches.
- note: The cooldown is applied through the `protections` property. I could not confirm from these files that the backtest ran with protections enabled. The shortest exit-to-next-entry gap I saw is about 76h (BNB: 2020-12-11 12:00 exit, 2020-12-14 16:00 entry), which is ≥72h. The trade lists are therefore consistent with the cooldown but do not prove it was active.

## 2. Look-ahead
- No negative shifts, no centered windows, and no `iloc` indexing of future rows. Every level the current close is compared with is shifted by 1.
- The current bar enters only the SMA(2400) and range_ratio(t), both of which are allowed by the rule. range_ratio(t) is used only through `squeeze.shift(1)`, so it cannot leak into the entry on bar t.
- facts.json reports `lookahead_has_bias=false` and `recursive_is_stable=true` for all three pairs (research/experiments/H-005-exploration/facts.json).
- Finding: none.

## 3. Stored numbers against crosscheck and trade lists
- crosscheck.json reports `matches: true` for all three pairs. Trade counts agree: BTC 31, ETH 36, BNB 36. Net profit agrees: BTC 520.369, ETH 507.239, BNB 879.152. Excluding-best-trade figures agree: BTC 129.763, ETH 51.142, BNB 27.076.
- I counted data rows in the CSVs: BTC 31 (lines 2-32), ETH 36 (lines 2-37), BNB 36 (lines 2-37). These match.
- Stop-loss exits show profit_ratio of about −0.0832, not −0.08. That is the 8% stop plus fees and slippage, applied consistently. Plausible.
- Exit reasons are only `stop_loss` and `low336_breakdown`. Durations (in minutes) are consistent with open and close dates. Example: BNB 2018-02-15 06:00 to 2018-02-20 23:00 is 8220 min.
- The trade count is not suspiciously identical across pairs. ETH and BNB both have 36 in every cost scenario. Counts do not vary across cost scenarios in any pair, which is expected because costs do not change signals.
- note: BNB and BTC both have an entry at 2024-02-07 21:00. That is a signal coincidence between correlated pairs, not an error.

## 4. Reliability
- **warning: profit concentration (BNB).** The single best trade is 2020-12-14 to 2021-03-25, profit_ratio +6.70, profit_abs +623.95, out of a total of +879.15 (trades-bnb-usdt.csv, line 21; facts.json). Excluding the best trade, compounded profit falls from 879 to 27.08. In the stress scenario it is 3.01 (facts.json `net_profit_excl_best_trade__stress` = 3.0057). That is barely positive.
- **warning: profit concentration (ETH).** The best trade is 2020-10-09 to 2021-02-23, ratio +3.01, abs +412.36 (trades-eth-usdt.csv, line 14). Excluding it, profit falls from 507.24 to 51.14, and to 22.51 in stress.
- **warning: profit concentration (BTC).** The best trade is 2020-10-08 to 2021-01-22, ratio +1.70, abs +408.09 (trades-btc-usdt.csv, line 14). Excluding it, profit falls from 520.37 to 129.76. This is less extreme, but there is still one dominant trade. In each pair the gain comes from one to three bull-market trades in 2019-2021.
- **warning: win rate and loss pattern.** Win rate is low. Counting profit_ratio > 0: BTC 8 of 31, ETH 12 of 36, BNB 9 of 36. Many trades are 8% stop-outs, and several are repeated in clusters, such as ETH 2022-09 to 2022-11 and BTC 2021-08 to 2021-09. Profit depends on a few very long trades, up to about 197,100 min (about 137 days) for ETH.
- **warning: drawdown.** Max drawdown fails the 25% gate in every scenario on every pair: BTC 49.05-54.27%, ETH 49.55-54.72%, BNB 42.04-46.36% (facts.json). The result is consistent across pairs, so this is not a pair-specific artifact.
- **note: sample size and scale.** Counts are 31, 36 and 36, just above the 30 minimum (lab/config/gates.json). BTC at 31 is a thin margin. Because the whole balance is staked, later trades compound earlier gains. Net profit in quote units is therefore dominated by trades after 2020, when the balance is large. For example, 2021-2022 stop-outs cost 40-85 quote units each, against 5-11 in 2018.
- **note: benchmarks.** Buy-and-hold is BTC +1252.66%, ETH +929.58%, BNB +33023.5% (facts.json). The gate only requires reporting, not beating.
- **note: gate outcome.** The stored decision is `rejected` for all three pairs, solely on the max_drawdown gate. All other gates pass: lookahead, recursive, minimum trades, net profit in base and conservative, profit excluding the best trade. Decisions are left to the gates.

## Blocking findings
None. No mismatch found between stored values, crosscheck and the trade lists, and no forward-looking logic found.
