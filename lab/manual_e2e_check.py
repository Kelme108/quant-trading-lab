"""Manual end-to-end check: DonchianBreakoutBaseline (H-002) on the exploration
split of every enabled pair, decided with the frozen gates, then one portfolio
snapshot over the result.

A verification script, not part of the orchestrator. Safe to re-run: every run
uses a fresh timestamped experiment id per pair, so it never overwrites a
manifest.
"""

from __future__ import annotations

from datetime import datetime, timezone

from lab import experiment, portfolio, registry, runner

STRATEGY_FILE = "user_data/strategies/DonchianBreakoutBaseline.py"
STRATEGY_NAME = "DonchianBreakoutBaseline"
HYPOTHESIS_ID = "H-002"
SPLIT_NAME = "exploration"


def main() -> int:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    splits = runner.load_splits()
    version = experiment.freqtrade_version()
    conn = registry.connect()

    for pair in runner.enabled_pairs():
        experiment_id = experiment.run_experiment(
            conn,
            hypothesis_id=HYPOTHESIS_ID,
            strategy_name=STRATEGY_NAME,
            strategy_file=STRATEGY_FILE,
            pair=pair,
            split_name=SPLIT_NAME,
            timestamp=timestamp,
            splits=splits,
            version=version,
            notes="Manual end-to-end verification run.",
        )
        decision, reasons = experiment.decide_experiment(conn, experiment_id, HYPOTHESIS_ID)
        print(f"DECISION [{pair}] = {decision}")
        for reason in reasons:
            print(f"  - {reason}")

    snapshot = portfolio.build_portfolio(conn)
    path = portfolio.write_snapshot(snapshot)
    print(f"\nportfolio snapshot: {path}")
    print(f"included: {[e['hypothesis_id'] for e in snapshot['included']] or 'none (empty portfolio)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
