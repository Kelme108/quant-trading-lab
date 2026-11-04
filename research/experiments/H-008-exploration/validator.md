# Validator report: H-008 exploration

Files checked: `research/experiments/H-008-exploration/facts.json`, `crosscheck.json`, the three `trades-*.csv` files, `user_data/strategies/_archive/VolatilitySqueezeBreakout_H008_v1.py`, `research/validation-protocol-v2.md`, `lab/config/gates.json`, `research/proposals/H-005.json`.

## Findings

1. **warning: `research/proposals/H-008.json` does not exist.**
   - `research/proposals/` contains only H-004, H-005, H-006 and H-007.
   - I could not compare the code with an H-008 proposal.
   - The strategy docstring says "the H-005 rule, unchanged, traded with 20% of the account per trade", so I compared the code with `research/proposals/H-005.json` instead.
   - The H-008 exposure rule (20% of account) and its place in the family are unverified against any proposal text.

2. **note: the code matches the H-005 rule.**
   - Range: 168-bar range ratio R = (high max − low min) / close, as in the rule.
   - Squeeze: R ≤ rolling 0.20 quantile over 2160 bars, `.shift(1)`, so it ends at t-1. This matches.
   - Recent squeeze: `squeeze.shift(1).rolling(24).max()` covers t-24..t-1. This matches.
   - Breakout: close > 168-bar high, shifted by 1, which excludes the current bar. This matches.
   - Trend: close > SMA(2400). The SMA includes the current close, as the rule says ("SMA(2400) of close").
   - Exit: close < 336-bar low, shifted by 1. This matches.
   - Stop: `stoploss = -0.08`, matching the 8% hard stop.
   - Cooldown: `CooldownPeriod` with 72 candles. This matches.
   - Warm-up: `startup_candle_count = 2400`. This matches.
   - `minimal_roi = {"0": 100.0}` is effectively no take-profit, which matches.
   - Differences:
     - `volume > 0` is an extra condition in the entry and exit. It is minor and not in the rule.
     - The rule says "whole balance", and H-008 deliberately changes this to 20% via `tradable_balance_ratio`. The code does not set it (`exposure: 0.2` in facts.json).

3. **note: no lookahead found in the code.**
   - Every comparison level is shifted by one candle.
   - There are no centered windows or negative shifts.
   - The `lookahead_has_bias: false` and `recursive_is_stable: true` results in facts.json agree with this.

4. **note: stored numbers match the crosscheck.**
   - Trade counts match: BTC 31/31, ETH 36/36, BNB 36/36.
   - Net profit matches `crosscheck.json`:

     | Pair | Stored | From trade list |
     |---|---|---|
     | BTC | 78.3386 | 78.3386 |
     | ETH | 87.3535 | 87.3535 |
     | BNB | 171.5367 | 171.5367 |

   - Excluding the best trade also matches: 33.19, 16.88 and 15.96.
   - The trade CSV rows are consistent with these numbers.
   - Stake sizing looks like about 20% of the balance. For example, BTC trade 1 has 8.19 / 0.4093 ≈ 20.0, and a later trade has 44.13 / 1.696 ≈ 26.
   - Stop-loss exits show about −8.32% (−8% plus costs). The other exits are `low336_breakdown`. There are no other exit reasons.
   - Durations are plausible: `trade_duration` is in minutes, for example 38940 min ≈ 27 days.

5. **warning: profit is concentrated in a few trades.**
   - BNB (`trades-bnb-usdt.csv`): the single best trade (2020-12-14 to 2021-03-25, ratio +6.70) gives +141.01 of the 171.54 net profit. Without it, net profit falls to 15.96 (`facts.json`), about 9% of the total.
   - ETH (`trades-eth-usdt.csv`): the best trade (2020-10-09 to 2021-02-23, +65.97) is 75% of the 87.35 total. Without it, net profit is 16.88.
   - BTC (`trades-btc-usdt.csv`): three trades (+29.98, +44.13 and +13.6) carry most of the profit. Excluding the best leaves 33.19, which is less concentrated.
   - Most trades lose. By stop-loss count, BTC has 11 of 31, ETH 14 of 36 and BNB 14 of 36.
   - The gate only requires profit excluding the best trade to be > 0. It passes, but the result rests on a handful of 2019–2021 and 2024 trend episodes.

6. **warning: trade counts are marginal.**
   - BTC has 31 trades against the minimum of 30, so one fewer trade would give `inconclusive`.
   - ETH and BNB both have exactly 36.
   - Counts are identical across all four cost scenarios on every pair (`facts.json`). That is expected, because costs change fills but not signals.

7. **note: BNB drawdown fields differ.**
   - `max_drawdown_pct__base` is 10.30 and `max_relative_drawdown_pct__base` is 13.16 (`facts.json`).
   - For BTC and ETH the two fields are equal.
   - The gate reasons use the relative figure (13.16). Both are far below the 25% limit.

8. **note: the pairs are correlated.**
   - Several exits fall on the same dates across pairs: 2020-03-08 15:00 for BTC and ETH, 2022-04-25 for all three, 2024-03-20 for BTC and ETH, and 2021-09-07 15:00 for BNB and ETH.
   - The three results are not independent evidence.

9. **note: multiple-testing context.**
   - The gate cites 1 prior variant and a required profit of 1.10 quote. All three pairs clear this by a wide margin.
   - H-008 is described as the H-005 rule with a different exposure. I did not check whether this counts as a new variant of the family.
