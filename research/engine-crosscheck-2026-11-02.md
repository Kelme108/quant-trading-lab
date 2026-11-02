# Backtest engine cross-check — 2026-11-02

Question: does the Freqtrade backtest in this harness do what the documentation says? Method: re-implement
SmaTrendBaseline (H-001) in plain pandas (`research/tools/replicate_sma_baseline.py`, no Freqtrade, no
TA-Lib) and compare its trade list with the one Freqtrade exported, exploration split, optimistic cost
(fee 0.1% per side), experiments `20261102T224114Z-h-001-exploration-*`.

| Pair | Freqtrade trades | Replica trades | Same entry time | Same exit time | Median profit diff per trade |
|---|---:|---:|---:|---:|---|
| BTC/USDT | 383 | 383 | 383 | 383 | 6e-12 |
| ETH/USDT | 388 | 388 | 388 | 388 | 3e-12 |
| BNB/USDT | 366 | 364 | 364 | 364 | 4e-16 |

Max per-trade profit difference: 1e-7 (BTC), 3e-5 (ETH), 1e-4 (BNB). The residue is Freqtrade rounding the stop
price to the pair's price precision.

What the check established:
- Signals use closed candles and fill at the next candle's open.
- Fees are charged on both sides and the compounding arithmetic is exact.
- A pending exit signal fills at the open of the candle, before an intrabar stop; the 10% stop fills at the
  stop price, or at the open when the candle gaps below it; a stop also applies on the entry candle; a slot freed
  on a candle can be refilled on the same candle.
- Missing hourly candles are filled by Freqtrade (previous close, volume 0), so indicator windows count the
  filled bars and `volume > 0` blocks signals on them. A replica that ignores this diverges around the gaps.

Two BNB trades exist only in Freqtrade (2022-04-05 00:00 and 2023-03-20 21:00). At 2022-04-04 23:00 the 20- and
50-bar means are exactly equal (8886/20 = 22215/50 = 444.3); TA-Lib's running sum leaves 5.7e-14 of floating-point
noise that makes `fast > slow` true, while pandas gives exactly 0. It is a numerical tie, not an engine defect, but
it means a strict comparison between two equal means is decided by summation noise.

Not covered: strategies other than H-001, cost scenarios other than optimistic, the validation split, and the
real-exchange behavior that no backtest models (partial fills, queue position, latency).
