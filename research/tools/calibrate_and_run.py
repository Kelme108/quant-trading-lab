"""Calibration -> exposure by rule -> official experiment, for one hypothesis (the H-009/H-010 procedure).

1. Calibration (exploration split, base cost, full exposure): trade lists per pair. Fewer than 30 trades on any
   pair drops the hypothesis (reported, nothing is retuned).
2. Exposure = lab.bootstrap.choose_exposure on those trades (seeded; exploration data only).
3. Official experiment: 4 cost scenarios, lookahead, recursive, gates; exploration only. Validation is NOT run here.

usage: python research/tools/calibrate_and_run.py H-011
The work is done by lab/calibrate.py (shared with the weekly pipeline).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lab import calibrate, orchestrator, registry  # noqa: E402

EXIT_CODES = {"explored": 0, "failed": 2, "dropped_trades": 3, "dropped_exposure": 4}


def main(hypothesis_id: str) -> int:
    conn = registry.connect()
    number = int(hypothesis_id.split("-")[1])
    found = sorted((ROOT / "user_data" / "strategies").glob(f"*_H{number:03d}_v*.py"))[-1]
    result = calibrate.calibrate_and_explore(
        conn, hypothesis_id, strategy_name=found.stem,
        strategy_file=str(found.relative_to(ROOT)).replace("\\", "/"),
        timeframe=orchestrator.strategy_timeframe(found),
    )
    print(result)
    registry.sync_ledger_markdown(conn)
    registry.dump_sql(conn)
    return EXIT_CODES[result["outcome"]]


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
