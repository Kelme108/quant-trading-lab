"""One-off: register H-015 (TimeSeriesMomentum family) BEFORE any run of it (protocol rule)."""
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lab import registry  # noqa: E402

RULE = (
    "Closed DAILY candles (Freqtrade informative 1d merged with merge_informative_pair), executed on 1h at the next open. Long only, one "
    "position, whole allowed balance, no stop-loss, no sizing hooks. mom(d) = close(d)/close(d-N days) - 1. ENTRY while mom > 0 (and, with the "
    "regime, regime_on() true = daily close > SMA(200); vol_regime off per the step-1.4 ablation). EXIT when mom <= 0 (or the regime turns off). "
    "GRID (pre-declared, complete): N in {30, 60, 90, 120, 180} x regime in {off, on} = 10 configurations; N_trials for the DSR = 10. "
    "Each configuration is also a test at costs base and base_2x on each of BTC, ETH, BNB. Warm-up 400 bars (daily and 1h). "
    "PASS CRITERIA TO READ VALIDATION (fixed before running, all required): DSR of the best configuration (N=10) >= 0.95; PBO (CSCV, 16 slices) "
    "<= 0.5; plateau (neighbouring N with the same regime flag reach >= 70% of the best Sharpe); Sharpe above buy-and-hold AND above Sma200Baseline "
    "at base_2x in the IS; >= 30 trades per pair; lab/config/gates.json clear on exploration. Fail = family rejected and archived. The validation "
    "split is then read ONCE, for the configuration chosen in the IS. Final test / prospective holdout not read."
)
VISIBLE = (
    "BTC, ETH, BNB 1h/4h/1d candles through 2026-11-02; results of H-001..H-014 known, including the one-time validation read of H-008 and the "
    "Sma200Baseline cycle table (so the validation window is not blind for trend-following ideas). No result of THIS rule seen. Regime-filter ablation "
    "(IS only) known."
)
conn = registry.connect()
if registry.get_hypothesis(conn, "H-015") is None:
    registry.add_hypothesis(
        conn, hypothesis_id="H-015", family="TimeSeriesMomentum", ex_ante_rule=RULE,
        proposed_at_utc=datetime.now(timezone.utc).isoformat(), data_visible_at_proposal=VISIBLE, status="proposed",
        notes="Step 2, family 1 of 3 (TSMOM). Pre-registered grid of 10; textbook horizons.")
    print("registered H-015")
registry.sync_ledger_markdown(conn)
registry.dump_sql(conn)
