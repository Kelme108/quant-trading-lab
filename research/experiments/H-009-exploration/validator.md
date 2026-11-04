# Validator report: H-009 exploration

Files read: `facts.json`, `crosscheck.json`, `lab/config/gates.json` and `WeeklyBreakoutRegime_H009_v1.py`, all in the review directory or its usual paths. I also read the first 40 rows of `trades-bnb-usdt.csv`. I did not open the BTC or ETH trade lists, and I did not read `validation-protocol-v2.md`.

## Findings

1. **blocking (cannot verify rule fidelity): the proposal file is missing.**
   - `research/proposals/H-009.json` does not exist. A glob for `research/proposals/H-009*` returned nothing.
   - I therefore could not check item 1 (code against proposal) against the actual proposal.
   - The only statement of the rule I could compare with the code is the strategy docstring. The code matches that docstring:
     - Regime is SMA720 > SMA2160 and close > SMA720.
     - Entry is close > the prior 168-bar high.
     - Exit is close < the prior 72-bar low, or close < SMA720.
     - The stop is -6%, and the cooldown is 24 candles through the `CooldownPeriod` protection.
   - The docstring is not the proposal. Someone must confirm the parameters against the proposal.

2. **note: no look-ahead found in the code.**
   - `entry_high` and `exit_low` are both `.rolling(...).shift(1)`, so the current candle is excluded (strategy lines 37-38).
   - The SMAs use the current close, which is available at the candle close. No centered windows or negative shifts appear.
   - `startup_candle_count` is 2400, which is at least 2160.
   - `facts.json` reports `lookahead_has_bias: false` and `recursive_is_stable: true` for all three pairs.
   - Entry is on `high` for the channel but compares `close`. This is consistent with a "high channel" and is not a bias.

3. **warning: BNB profit is concentrated in a few trades.**
   - BNB base net profit is 133.57 (`facts.json`). Excluding the best trade, it is 25.29 (`net_profit_excl_best_trade__base`). One trade therefore carries about 81% of the profit.
   - That trade is in `trades-bnb-usdt.csv`, line 37: opened 2021-01-29 12:00, closed 2021-02-23, `profit_ratio` 3.452 (+345%), `profit_abs` 106.59.
   - It compounds into later trades, because the stake is the whole balance.
   - The stress scenario excluding the best trade falls to 11.28.
   - Pooled across the two later pairs the pattern repeats less sharply:
     - BTC: 113.80 falls to 71.52 without its best trade.
     - ETH: 61.77 falls to 40.34 without its best trade.
   - The gate's "excluding best trade > 0" check passes, but it is a weak test. Most profit comes from a few 2019-2021 trend legs.

4. **warning: the strategy is mostly stop-outs and small losses, with a few large winners.**
   - In the 39 BNB rows I read, many exits are `stop_loss` at about -6.33%, or small `low72_or_regime_lost` losses. A minority of trades are large winners.
   - There are quick re-entries, for example 2020-05-18 and 2020-05-19, and 2020-11-07 and 2020-11-20.
   - I only read the first 39 rows of the BNB list. I did not look at BTC or ETH trade lists.

5. **warning: a different time slice of the same trade lists is not tested.**
   - All figures come from one exploration split. ETH stress max drawdown is 23.70% against the 25% limit (`max_drawdown_pct__stress`), so the margin is thin.
   - ETH drawdown (18.5% base) is much larger than BTC (7.2% base), and the profit levels differ widely across pairs (BTC 113.8, ETH 61.8, BNB 133.6). The result is not uniform across pairs.

6. **note: stored numbers agree with the cross-check.**
   - `crosscheck.json` shows `matches: true` for all three pairs.
     - Trade counts are 58, 81 and 80 (stored vs export).
     - Net profit is identical to the stored values to the stored precision. BTC is 113.80368874 and BNB is 133.57212431. ETH differs by 1e-8, which is rounding.
     - The excluding-best-trade values are identical to the recomputation.
   - Trade counts are identical across the four cost scenarios for each pair (for example 58 in each). That is plausible for a rule-based strategy whose entries do not depend on cost.
   - The 6% stop exits show realised losses of about -6.33%, which is plausible for a -6% stop with fees and slippage. Durations are in minutes (for example 60 = 1 candle) and are consistent with open and close dates in the rows I read.

7. **note: observed quirk in trade 1 of the BNB list.**
   - The trade opened 2018-02-15 09:00 and closed one hour later with -5.86% (`low72_or_regime_lost`).
   - It exits the next candle, which is a legitimate signal exit, but it is a 1-candle round trip with a large loss, so a gap through the exit level is possible.
   - I could not tell from the files whether the data start date or the 2400-candle warm-up explains why the first trade is in 2018.

8. **note: the gates file is marked PROPOSED.** `lab/config/gates.json` `_status` says its thresholds are not yet user-approved. The `candidate_for_portfolio` decisions for all three pairs depend on those thresholds.

## Not checked
- Whether the split dates are what the proposal specified.
- The BTC and ETH trade lists beyond the summary numbers.
- The manifests under `research/manifests/`.
