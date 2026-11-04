"""Calibration -> exposure by rule -> official experiment, for one hypothesis (the H-009/H-010 procedure).

1. Calibration (exploration split, base cost, full exposure): trade lists per pair. Fewer than 30 trades on any
   pair drops the hypothesis (reported, nothing is retuned).
2. Exposure = lab.bootstrap.choose_exposure on those trades (seeded; exploration data only).
3. Official experiment: 4 cost scenarios, lookahead, recursive, gates; exploration only. Validation is NOT run here.

usage: python research/tools/calibrate_and_run.py H-011
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lab import bootstrap, costs, experiment, orchestrator, registry, runner  # noqa: E402


def main(hypothesis_id: str) -> int:
    conn = registry.connect()
    splits = runner.load_splits()
    pairs = runner.enabled_pairs()
    number = int(hypothesis_id.split("-")[1])
    found = sorted((ROOT / "user_data" / "strategies").glob(f"*_H{number:03d}_v*.py"))[-1]
    name, strategy_file = found.stem, str(found.relative_to(ROOT)).replace("\\", "/")
    timeframe = orchestrator.strategy_timeframe(found)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = costs.get_scenario("base")

    ratios, counts = {}, {}
    for pair in pairs:
        timerange = runner.resolve_split_timerange("exploration", splits, pair=pair)
        result = runner.run_backtest(
            experiment_id=f"calib-{hypothesis_id.lower()}-{stamp}-{pair.replace('/', '-').lower()}",
            strategy=name, timerange=timerange, fee=base.effective_fee_per_side, pair=pair, timeframe=timeframe,
        )
        if result.get("status") != "completed":
            print("calibration backtest failed", pair, result)
            return 2
        trades = runner.read_trades(ROOT / result["artifact_path"])
        ratios[pair] = [float(t["profit_ratio"]) for t in sorted(trades, key=lambda t: t["open_date"])]
        counts[pair] = len(trades)
    print("calibration trades:", counts)
    if min(counts.values()) < 30:
        note = f"DROPPED by the pre-registered rule: calibration trades {counts} (< 30 on at least one pair); not retuned."
        print(note)
        registry.set_hypothesis_status(conn, hypothesis_id, "dropped: fewer than 30 trades")
        conn.execute("UPDATE hypotheses SET notes = notes || ' ' || ? WHERE id = ?", (note, hypothesis_id))
        conn.commit()
        registry.sync_ledger_markdown(conn)
        registry.dump_sql(conn)
        return 3
    chosen = bootstrap.choose_exposure(ratios)
    exposure = chosen["exposure"]
    print("exposure:", chosen)
    if exposure is None:
        registry.set_hypothesis_status(conn, hypothesis_id, "dropped: no exposure meets the 25% bootstrap drawdown")
        registry.sync_ledger_markdown(conn)
        registry.dump_sql(conn)
        return 4
    ids = []
    version = experiment.freqtrade_version()
    for pair in pairs:
        ids.append(experiment.run_experiment(
            conn, hypothesis_id=hypothesis_id, strategy_name=name, strategy_file=strategy_file, pair=pair,
            split_name="exploration", timestamp=stamp, splits=splits, version=version,
            notes=f"exposure {exposure} (p95 {chosen['p95_by_pair']}); calibration trades {counts}",
            exposure=exposure, timeframe=timeframe,
        ))
    decisions = {}
    for experiment_id in ids:
        decision, reasons = experiment.decide_experiment(conn, experiment_id, hypothesis_id)
        decisions[experiment_id] = decision
        print(experiment_id, decision)
    values = set(decisions.values())
    status = "exploration: candidate" if values == {"candidate_for_portfolio"} else (
        "rejected at exploration" if "rejected" in values else "inconclusive at exploration")
    registry.set_hypothesis_status(conn, hypothesis_id, status)
    conn.execute("UPDATE hypotheses SET notes = notes || ? WHERE id = ?",
                 (f" Calibrated exposure: {exposure} (p95 by pair {chosen['p95_by_pair']}). Calibration trades: {counts}.", hypothesis_id))
    conn.commit()
    registry.sync_ledger_markdown(conn)
    registry.dump_sql(conn)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
