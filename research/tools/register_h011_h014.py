"""One-off: register H-011..H-014 in the hypothesis registry BEFORE any run (protocol rule)."""
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lab import registry  # noqa: E402

TB = (
    "Closed candles only; signal at candle close, order at next open. Long only, one position, no averaging down. "
    "Pivot low at i = lowest low of [i-5,i+5] (ties allowed on the left only), KNOWN only at the close of candle i+5. "
    "Three consecutive pivot lows L1,L2,L3 (i1<i2<i3) form the support zone if (max L - min L)/mean L <= 2%, consecutive bottoms "
    ">= 12 candles apart, i3-i1 <= 150 candles. Recoveries: H1 = highest high in (i1,i2), H2 = highest high in (i2,i3); both must be "
    ">= mean bottom * 1.03. Neckline = max(H1,H2). ENTRY at the first close above the neckline at t in [i3+5, i3+5+30] and before a fourth "
    "pivot is confirmed, if no earlier close since i3 was above it, no low since i3 is below min bottom * 0.98, volume(t) >= mean volume of the "
    "previous 20 candles. Optional filters OFF in the tested rule: RSI14 higher at i3 than at i1 (positive divergence), close > EMA200. "
    "STOP at min bottom - 0.5*ATR14(t) (fixed at entry, via custom_stoploss from the signal candle). TARGET neckline + 1.0*(neckline - mean bottom). "
    "TIME STOP 150 candles. Min R/R filter configurable, OFF (0.0) because stop below support and entry at the neckline make R/R < 1 by construction. "
    "A pattern signals once and a later pattern must start after the previous signalled pattern's last bottom (no duplicate entries). "
    "Warm-up: 800 bars. EXPOSURE: fixed share of the account chosen by the lab rule (largest 5% grid value with block-bootstrap p95 closed-trade "
    "drawdown <= 25% on all pairs, computed from this rule's own exploration trades at base cost and full exposure; calibration run; fewer than 30 "
    "trades on a pair drops the hypothesis, no retuning). Validation and final test not read. Parameters are textbook values fixed before any result."
)
SN = (
    "Closed candles only; signal at candle close, order at next open. Long only, one position, no DCA, no martingale. "
    "z(t) = (close - EMA20)/ATR14. STRETCH: min z over the previous 6 candles (t-6..t-1) <= -2.0. ENTRY at close of t when stretch AND "
    "close(t) > EMA200(t) AND close(t) > high(t-1) (recovery confirmation) AND close(t) < EMA20(t) AND no open position AND cooldown. "
    "Optional RSI (min RSI14 over the lookback <= 35) and volume (>= mean of previous 20 candles) filters are OFF in the tested rule. "
    "STOP close(t) - 2.0*ATR14(t), fixed at entry. EXIT first close >= EMA20 (executed next open); time stop after 48 candles; alternative exit "
    "'rr' (1.5R target) exists as a documented option and is only an ablation. COOLDOWN 6 candles after any exit. Warm-up: 800 bars. "
    "EXPOSURE: fixed share of the account chosen by the lab rule (largest 5% grid value with block-bootstrap p95 closed-trade drawdown <= 25% on all pairs, "
    "from this rule's own exploration trades at base cost and full exposure; fewer than 30 trades on a pair drops the hypothesis, no retuning). "
    "Validation and final test not read. Parameters are textbook values fixed before any result."
)
VISIBLE = (
    "BTC, ETH, BNB 1h and 4h candles through 2026-10-30 (4h downloaded 2026-11-03); results of H-001..H-010 known, including the one-time "
    "validation read of H-008 (a different rule on the same 2024-07..2026-10 window) - the validation split is therefore not blind for this "
    "family of ideas. No result of THIS rule seen."
)
ROWS = [
    ("H-011", "TripleBottomReversal", TB, "Triple bottom reversal, 1h. User-requested; reversal pattern, structurally R/R<1."),
    ("H-012", "EMASnapbackATR", SN, "EMA20 ATR-normalised snapback inside an EMA200 uptrend, 1h. User-requested; mean reversion, a family that failed before (H-003)."),
    ("H-013", "TripleBottomReversal", TB.replace("Warm-up: 800 bars.", "Timeframe 4h, same constants in candles. Warm-up: 800 bars."), "Same rule as H-011 on 4h candles (counts as a variant of the family)."),
    ("H-014", "EMASnapbackATR", SN.replace("Warm-up: 800 bars.", "Timeframe 4h, same constants in candles. Warm-up: 800 bars."), "Same rule as H-012 on 4h candles (counts as a variant of the family)."),
]
conn = registry.connect()
for hid, family, rule, note in ROWS:
    if registry.get_hypothesis(conn, hid) is None:
        registry.add_hypothesis(conn, hypothesis_id=hid, family=family, ex_ante_rule=rule,
                                proposed_at_utc=datetime.now(timezone.utc).isoformat(),
                                data_visible_at_proposal=VISIBLE, status="proposed", notes=note)
        print("registered", hid)
registry.sync_ledger_markdown(conn)
registry.dump_sql(conn)
