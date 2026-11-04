"""Calibration -> exposure by rule -> official exploration experiment, for one hypothesis.

1. Calibration (exploration split, base cost, full exposure): the trade list of each pair. Fewer than 30 trades on any
   pair drops the hypothesis (recorded, nothing is retuned).
2. Exposure = lab.bootstrap.choose_exposure on those trades (seeded; exploration data only).
3. Official experiment: 4 cost scenarios, lookahead, recursive, gates; exploration only.

The validation split is never touched here. Shared by research/tools/calibrate_and_run.py and the weekly pipeline.
`backtest`, `read_trades` and `experiments` are injectable so the flow can be tested without Docker.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from lab import bootstrap, costs, experiment, registry, runner

ROOT = Path(__file__).parents[1]
MIN_TRADES = 30


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def calibrate_and_explore(
    conn, hypothesis_id: str, *, strategy_name: str, strategy_file: str, timeframe: str = "1h",
    root: Path = ROOT, splits: dict | None = None, backtest=runner.run_backtest, read_trades=runner.read_trades,
    experiments=experiment, pairs: list[str] | None = None,
) -> dict:
    """{'outcome': 'explored'|'dropped_trades'|'dropped_exposure'|'failed', 'counts', 'exposure', 'status', 'decisions'}."""
    splits = splits if splits is not None else runner.load_splits()
    pairs = pairs or runner.enabled_pairs()
    stamp = _stamp()
    base = costs.get_scenario("base")
    ratios, counts = {}, {}
    for pair in pairs:
        timerange = runner.resolve_split_timerange("exploration", splits, pair=pair)
        result = backtest(
            experiment_id=f"calib-{hypothesis_id.lower()}-{stamp}-{pair.replace('/', '-').lower()}",
            strategy=strategy_name, timerange=timerange, fee=base.effective_fee_per_side, pair=pair, timeframe=timeframe,
        )
        if result.get("status") != "completed":
            return {"outcome": "failed", "counts": counts, "exposure": None, "status": None,
                    "reason": f"calibration backtest failed on {pair}"}
        trades = read_trades(root / result["artifact_path"])
        ratios[pair] = [float(t["profit_ratio"]) for t in sorted(trades, key=lambda t: t["open_date"])]
        counts[pair] = len(trades)
    if min(counts.values()) < MIN_TRADES:
        status = "dropped: fewer than 30 trades"
        note = f"DROPPED by the pre-registered rule: calibration trades {counts} (< 30 on at least one pair); not retuned."
        registry.set_hypothesis_status(conn, hypothesis_id, status)
        _append_note(conn, hypothesis_id, note)
        return {"outcome": "dropped_trades", "counts": counts, "exposure": None, "status": status}
    chosen = bootstrap.choose_exposure(ratios)
    exposure = chosen["exposure"]
    if exposure is None:
        status = "dropped: no exposure meets the 25% bootstrap drawdown"
        registry.set_hypothesis_status(conn, hypothesis_id, status)
        _append_note(conn, hypothesis_id, f"No exposure on the 5% grid keeps the bootstrap p95 drawdown within 25% on every pair; calibration trades {counts}.")
        return {"outcome": "dropped_exposure", "counts": counts, "exposure": None, "status": status}
    version = experiments.freqtrade_version()
    ids = [
        experiments.run_experiment(
            conn, hypothesis_id=hypothesis_id, strategy_name=strategy_name, strategy_file=strategy_file, pair=pair,
            split_name="exploration", timestamp=stamp, splits=splits, version=version,
            notes=f"exposure {exposure} (p95 {chosen['p95_by_pair']}); calibration trades {counts}",
            exposure=exposure, timeframe=timeframe,
        )
        for pair in pairs
    ]
    decisions, failed_gates = {}, {}
    for pair, experiment_id in zip(pairs, ids):
        decision, reasons = experiments.decide_experiment(conn, experiment_id, hypothesis_id)
        decisions[experiment_id] = decision
        failing = [r.split(":", 1)[0] for r in reasons if ": FAIL" in r or ": inconclusive" in r]
        if failing:
            failed_gates[pair] = failing
    values = set(decisions.values())
    status = (
        "exploration: candidate" if values == {"candidate_for_portfolio"}
        else "rejected at exploration" if "rejected" in values else "inconclusive at exploration"
    )
    registry.set_hypothesis_status(conn, hypothesis_id, status)
    _append_note(conn, hypothesis_id, f"Calibrated exposure: {exposure} (p95 by pair {chosen['p95_by_pair']}). Calibration trades: {counts}.")
    return {"outcome": "explored", "counts": counts, "exposure": exposure, "status": status, "decisions": decisions,
            "failed_gates": failed_gates}


def _append_note(conn, hypothesis_id: str, note: str) -> None:
    conn.execute("UPDATE hypotheses SET notes = COALESCE(notes, '') || ' ' || ? WHERE id = ?", (note, hypothesis_id))
    conn.commit()
