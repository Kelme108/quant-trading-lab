# Validator report: H-007 exploration

Files read: the strategy file `user_data/strategies/RisingTrendBreakoutGate_H007_v1.py`, `research/proposals/H-007.json`, `lab/config/gates.json`, `facts.json`, `crosscheck.json`, `trades-btc-usdt.csv` and `trades-bnb-usdt.csv`. I did not open `trades-eth-usdt.csv`, so I did not check ETH trade durations or exit reasons. I did not read `research/validation-protocol-v2.md`. I did not open the manifests.

## 1. Code against the proposal
No blocking differences. I checked each element:
- **Regime:** the strategy file has SMA1200 > SMA2400, SMA2400 > SMA2400.shift(480), and close > SMA1200 (lines 34-36, 48-50). All three match the proposal.
- **Entry:** `close > high.rolling(480).max().shift(1)` (line 37) excludes the current bar, as the proposal asks. It adds `volume > 0` and notna guards, which are harmless.
- **Exit:** `close < low.rolling(240).min().shift(1)` OR `close < sma_fast` matches the proposal. It also adds `volume > 0`.
- **Stop and cooldown:** `stoploss = -0.06` matches. The `CooldownPeriod` protection uses 120 candles, which matches.
- **Warm-up:** `startup_candle_count = 2880` matches the proposal. `minimal_roi = {"0": 100.0}` is effectively no take-profit.
- **note:** the cooldown is a Freqtrade protection. It applies to stoploss exits and to signal exits, as the proposal says ("after any exit").

## 2. Forward-looking information
- **note:** I found no forward-looking indexing and no centered windows. Both channel levels are shifted by 1 before the comparison. The SMAs include the current close, which the rule allows, since the regime is defined at t.
- **warning:** `facts.json` (BNB/USDT) has `lookahead_has_bias: true`, and the lookahead gate FAILS for BNB. The code gives no cause for this. I could not find the cause from the files alone, so the lookahead-analysis output for BNB needs inspecting.

## 3. Stored numbers against crosscheck and trade lists
- **note:** `crosscheck.json` shows `matches: true` for all three pairs. Trade counts are 23 BTC, 27 ETH and 36 BNB. Net profit is 563.30, 329.51 and 163.34. Net profit excluding the best trade matches too.
- **note:** BTC and BNB trade counts agree with the CSV row counts. The BTC CSV has 23 rows and the BNB CSV has 36.
- **note:** for BTC and BNB, stop_loss exits sit at about -0.0633. That is the 6% stop plus fees, which is consistent. `trade_duration` is in minutes and agrees with the open and close dates. For example, BNB's first trade runs 92 hours, which is 5520 minutes.
- **note:** trade counts are identical across the four cost scenarios on each pair (`facts.json`). That is expected, because costs do not change signals.

## 4. Reliability
- **warning (BNB):** net profit depends on one trade. The 2021-02-01 trade returned +386% (`trades-bnb-usdt.csv`, +211.9 of +163.3 total). Excluding the best trade gives -45.83 (`facts.json`, `net_profit_excl_best_trade__base`), so the profit_excluding_best_trade gate FAILS. Of the 36 BNB trades, 21 end in stop_loss, which is a majority. In the 2019 and 2020 trades there are runs of consecutive stop-losses.
- **warning (BTC):** a few trades carry the profit. The 2020-10-10 to 2021-01-21 trade returned +170.6%, with +365.8 profit_abs. Another trade returned +85.8% in 2019. Excluding the best trade drops net profit from 563 to 144.7 (`crosscheck.json`).
- **warning (ETH):** excluding the best trade drops net profit from 329.5 to 43.4 (`facts.json`). That is a strong dependence on a single trade.
- **warning (rationale not borne out):** the proposal says the regime gate should stop long loss streaks. The BTC list shows 8 consecutive stop-loss trades in 2023: 2023-01-29, 02-16, 03-14, 03-22, 03-30, and then 07-13 after one -5.4% signal exit on 04-10. That is a cluster of repeated failed breakouts. The BNB list has runs of 6 or more stop-losses in 2019 and 2020. Max drawdown is 36.7% BTC, 44.7% ETH and 25.1% BNB at base (`facts.json`). All fail the 25% gate. This mismatch is on the proposal's own prediction.
- **warning (recursive):** `recursive_is_stable` is false for BTC and BNB and true for ETH (`facts.json`). Indicators with 1200 to 2400 bar windows may not settle within the 2880-candle warm-up. That makes results vary with the start of the data. The BTC first trade at 2017-12-15 is only about 4 months after the BTC data starts (inferred, not shown in the files).
- **warning (trade counts):** BTC has 23 and ETH has 27 trades, both under 30 (inconclusive). Results differ widely between pairs: BNB has no robust profit while BTC and ETH do, though both depend on one trade each.
- **note:** the stored decisions are all "rejected" (`facts.json`). Reasons: the drawdown gate fails on all three pairs, lookahead and recursive fail on BNB, and recursive fails on BTC.
