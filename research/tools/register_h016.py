"""One-off: register H-016 (the configuration of the H-015 grid chosen in the exploration split) BEFORE running it."""
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lab import registry  # noqa: E402

RULE = (
    "Same rule as H-015 with N_DAYS = 30 and no regime filter (the H-015 grid winner at base_2x in the exploration split: pooled Sharpe 1.49 vs "
    "buy-and-hold 1.15 and Sma200Baseline 1.05; DSR(N=10) 0.999; PBO 0.31; plateau 0.83 of the best at N=60). Closed daily candles via "
    "merge_informative_pair, executed on 1h at the next open; long only, one position, no stop-loss, no sizing hooks. ENTRY while close(d)/close(d-30) > 1; "
    "EXIT when it is <= 1. N_trials inherited from H-015 = 10 (this is not a new draw: it is the selected cell of that grid; the family counts 11 "
    "registered hypotheses). Exposure: fixed share chosen by the lab rule (largest 5% value with block-bootstrap p95 closed-trade drawdown <= 25% on "
    "all pairs, from this rule's own exploration trades at base cost and full exposure). Gates of lab/config/gates.json on exploration; only if all clear, "
    "the validation split is read ONCE. Final test / prospective holdout not read."
)
VISIBLE = (
    "Same as H-015 plus the full exploration grid of H-015 (which is where this configuration was chosen). The validation split has not been read for "
    "this rule; it was read once for H-008 (a different rule)."
)
conn = registry.connect()
if registry.get_hypothesis(conn, "H-016") is None:
    registry.add_hypothesis(
        conn, hypothesis_id="H-016", family="TimeSeriesMomentum", ex_ante_rule=RULE,
        proposed_at_utc=datetime.now(timezone.utc).isoformat(), data_visible_at_proposal=VISIBLE, status="proposed",
        notes="Child of H-015. Winner at the grid edge (N=30, the shortest horizon): the plateau test has one neighbour only.")
    print("registered H-016")
note = (" [2026-11-03 grid explored on the IS (research/grids/H-015-exploration.json): best N30_noreg; DSR 0.999, PBO 0.31, plateau pass, beats B&H "
        "and Sma200 at base_2x, >= 89 trades per pair; selected cell registered as H-016.]")
row = conn.execute("select notes, status from hypotheses where id='H-015'").fetchone()
if "grid explored" not in (row["notes"] or ""):
    conn.execute("update hypotheses set notes=?, status=? where id='H-015'", ((row["notes"] or "") + note, "exploration grid passed pre-gate criteria; see H-016"))
    conn.commit()
registry.sync_ledger_markdown(conn)
registry.dump_sql(conn)
