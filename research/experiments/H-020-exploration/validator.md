# Validator report H-020 (exploration)

Files read: facts.json, crosscheck.json, the three trades-*.csv (BTC in full, ETH and BNB first 24 rows), the strategy file, research/proposals/H-020.json. I did not read validation-protocol-v2.md or gates.json, so I have not checked gate thresholds beyond what facts.json quotes.

## 1. Code vs proposal: no differences found
- **Trend filter:** `close_1d > sma200_1d`, with SMA(200) computed on daily closes (strategy file L31, L45). This matches the proposal.
- **Entry channel:** `low7 = close.rolling(7).min()` includes the current day. Entry is `close_1d <= low7_1d` (L32, L46). This matches "lowest close of 7 days INCLUDING current, close <=".
- **Exit:** `high7 = close.rolling(7).max()` includes the current day. Exit is `close_1d >= high7_1d` (L33, L58). This matches.
- **Stop and ROI:** stoploss -0.99, `minimal_roi` {"0": 100.0} (never reached), no cooldown, no time exit, long only. All match "no binding stop". startup_candle_count 400 matches.
- **Volume check:** the extra `volume > 0` condition is not in the proposal. It is harmless and is a note only.
- **Exposure:** it is not set in the strategy, as the proposal says. In facts.json all three pairs show `exposure: 0.1`. I did not check how the lab rule produced 0.1.

## 2. Lookahead: none found
- The daily indicators come from the `@informative("1d")` decorator. Freqtrade's merge makes a daily candle visible only after it closes. For ffill from a coarser timeframe this should be at the 23:00 1h row, which closes at 00:00.
- This is consistent with the trade lists. Every open_date and close_date sits at 00:00 UTC (e.g. trades-btc-usdt.csv L2-L58). That means signal on the last 1h row of a closed day and fill at the next open, as the proposal describes.
- No `shift(-n)`, no centered windows, and no unshifted prior level. The rule uses the current day's channel by design.
- `lookahead_has_bias: false` and `recursive_is_stable: true` for all pairs (facts.json).

## 3. Stored numbers vs crosscheck: all match
| Pair | Trades (stored = export) | Net profit, stored | Net profit, trade list | Net excl. best, stored = recomputed |
|---|---|---|---|---|
| BTC | 58 | 5.72669335 | 5.72669335 | 4.2274 |
| ETH | 66 | 4.96384032 | 4.96384032 | 2.4309 |
| BNB | 64 | 7.130346 | 7.130346 | 4.9226 |

Source: crosscheck.json, all `matches: true`.
- Trade counts are identical across the four cost scenarios on each pair, as expected for the same signals with different fees. They are not equal across pairs.
- Durations are whole multiples of 1440 minutes, and the longest is about 36 days (BTC 51840 min). Plausible.
- In the files read (BTC in full, ETH and BNB first 24 rows), all exits are `daily_high7` except the last BTC trade. That one is a `force_exit` at the end of data (trades-btc-usdt.csv L59, 2024-07-04 19:00, -3.7%).
- Stake size: BTC L2 has profit_abs -1.033 on ratio -0.104, so the stake is about 10 on a 100 balance, consistent with exposure 0.1.

## 4. Reliability concerns
- **warning, thin edge in absolute terms.** Net profit at base is +5.7 (BTC), +5.0 (ETH) and +7.1 (BNB) on a 100 start over about 6.5 years. Buy-and-hold is +1252%, +930% and +33023% (facts.json). The gate says beating the benchmark is not required, but the profit is small.
- **warning, ETH is fragile to costs.** The stress scenario nets +0.84, below the 1.0 net-profit threshold the gate reasons quote for base and conservative. Excluding the best trade, ETH stress is -1.53 (`net_profit_excl_best_trade__stress`). BTC stress nets 2.24 and BNB stress nets 3.09. BTC and BNB stress profit excluding the best trade is about 0.87 and 1.00.
- **warning, unbounded left tail.** There is no stop, and a few large losers offset many small winners:
  - ETH: -51.3% (trades-eth-usdt.csv L2, 2018-03 to 04), -31.9% (L12, 2020-03) and -18.5% (L3).
  - BTC: -23.4% (L33, 2021-11 to 12), -21.0% (L29) and -17.5% (L9).
  - BNB: -28.8% (L15) and -22.7% (L5).
  - Most are in 2018, 2020-03 and 2021, so drawdown depends on the 0.1 exposure. ETH max drawdown is 11.2% at 10% stake (facts.json).
- **note, regime coverage.** BTC has no trades between 2021-12 and 2023-02, consistent with the SMA200 filter during the 2022 bear market (trades-btc-usdt.csv L33-L34). The 2024-07 end of data forces an exit.
- **note, trade count versus expectation.** The proposal expected 80-150 trades per pair. Actual counts are 58, 66 and 64, still above the 30 minimum.
- **note, per-pair profit concentration.** The best trade is about 1.5 of BTC's 5.7 (net 5.73 against 4.23 excluding it), and about 2.5 of ETH's 5.0. Profit is not carried by a single trade on any pair, but ETH's dependence is the largest.
- **note, similar results across pairs.** All three pairs are profitable at base with similar structure (small wins, rare large losses). They trade overlapping crypto regimes, so they are not independent evidence.

No blocking findings.
