# Hypothesis ledger

This ledger records research attempts so selection bias remains visible.
It is generated from research/lab.sqlite; the database is the source of
truth. Do not hand-edit the table below, edit the database through
lab/registry.py instead.

| ID | Proposed UTC | Strategy / family | Ex-ante rule | Data visible at proposal | Prior tests | Decision | Notes |
|---|---|---|---|---|---:|---|---|
| H-001 | 2026-10-20T00:00:00Z | SmaTrendBaseline | SMA20/SMA50 cross, close > SMA200, stop -10% | BTC/USDT 1h through 2026-10-20 | 0 | frozen reference | Original result (1 trade) was a harness artifact: fixed stake equal to wallet. Not yet tested under the corrected harness. |
| H-002 | 2026-10-20T00:00:00Z | DonchianBreakoutBaseline | Close > prior 20-candle high; exit below prior 10-candle low; stop -10% | BTC/USDT 1h through 2026-10-20 | 5 | rejected at exploration | Corrected harness, exploration on BTC/ETH/BNB: positive only at the optimistic cost, drawdown 60-98%. Do not select by return alone. |
| H-003 | 2026-10-20T00:00:00Z | BollingerMeanReversionBaseline | Lower 20-band, RSI14 < 30, close > SMA200; exit at middle band; stop -10% | BTC/USDT 1h through 2026-10-20 | 0 | candidate | Not yet tested under the corrected harness. Trend-failure risk. |
| H-004 | 2026-10-30T13:28:34.345485+00:00 | SlowTimeSeriesMomentum | Use closed 1h candles only; signals evaluated at bar close, order executed at next bar open. Long only, one position, whole balance. ENTRY: close > highest high of the prior 1440 bars (60 days, excluding current bar) AND close > SMA(4800 bars, 200 days) of close AND no open position. EXIT: close < lowest low of the prior 720 bars (30 days, excluding current bar), OR close below entry price by 15% (hard stop, checked on closed bars). After any exit, no re-entry until at least 168 bars (7 days) have passed. No other filters, no pyramiding, no take-profit. | BTC, ETH, BNB 1h through 2026-10-30; no result data viewed beyond the context file's exploration summaries | 3 | failed | Slow 60-day breakout with 200-day regime filter and 30-day trend exit |

## Rules

- Add a row before running a new hypothesis.
- Do not edit a rule after observing its result; create a new ID.
- Record rejected and negative hypotheses.
- Count parameter variants and cost scenarios as tests.
- The final test period stays locked until the protocol explicitly permits one read.
