# Hypothesis ledger

This ledger records research attempts so selection bias remains visible.
It is generated from research/lab.sqlite; the database is the source of
truth. Do not hand-edit the table below, edit the database through
lab/registry.py instead.

| ID | Proposed UTC | Strategy / family | Ex-ante rule | Data visible at proposal | Prior tests | Decision | Notes |
|---|---|---|---|---|---:|---|---|
| H-001 | 2026-10-20T00:00:00Z | SmaTrendBaseline | SMA20/SMA50 cross, close > SMA200, stop -10% | BTC/USDT 1h through 2026-10-20 | 0 | frozen reference | One trade; inconclusive |
| H-002 | 2026-10-20T00:00:00Z | DonchianBreakoutBaseline | Close > prior 20-candle high; exit below prior 10-candle low; stop -10% | BTC/USDT 1h through 2026-10-20 | 0 | candidate | Do not select by return alone |
| H-003 | 2026-10-20T00:00:00Z | BollingerMeanReversionBaseline | Lower 20-band, RSI14 < 30, close > SMA200; exit at middle band; stop -10% | BTC/USDT 1h through 2026-10-20 | 0 | candidate | Trend-failure risk |

## Rules

- Add a row before running a new hypothesis.
- Do not edit a rule after observing its result; create a new ID.
- Record rejected and negative hypotheses.
- Count parameter variants and cost scenarios as tests.
- The final test period stays locked until the protocol explicitly permits one read.
