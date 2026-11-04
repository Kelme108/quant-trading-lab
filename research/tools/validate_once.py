"""The single validation read of a hypothesis (step 2.8). Refuses to run twice and requires exploration candidate on every pair.

usage: python research/tools/validate_once.py H-016 --exposure 0.15
The exposure must be the one calibrated on the exploration split (stored in the hypothesis notes); nothing else is tuned.
"""
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lab import experiment, orchestrator, registry, runner  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("hypothesis_id")
    parser.add_argument("--exposure", type=float, required=True)
    args = parser.parse_args()
    hid = args.hypothesis_id
    conn = registry.connect()
    pairs = runner.enabled_pairs()
    latest = {r["pair"]: r["decision"] for r in registry.list_latest_decisions(conn)
              if r["hypothesis_id"] == hid and r["split"] == "exploration"}
    if not all(latest.get(p) == "candidate_for_portfolio" for p in pairs):
        print("exploration is not a candidate on every pair; validation not read:", latest)
        return 3
    already = conn.execute("select count(*) n from experiments where hypothesis_id=? and split='validation'", (hid,)).fetchone()["n"]
    if already:
        print(f"{hid}: validation was already read ({already} experiments); not reading it again.")
        return 4
    number = int(hid.split("-")[1])
    found = sorted((ROOT / "user_data" / "strategies").glob(f"*_H{number:03d}_v*.py"))[-1]
    name, strategy_file = found.stem, str(found.relative_to(ROOT)).replace("\\", "/")
    timeframe = orchestrator.strategy_timeframe(found)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    splits, version = runner.load_splits(), experiment.freqtrade_version()
    ids = [experiment.run_experiment(conn, hypothesis_id=hid, strategy_name=name, strategy_file=strategy_file, pair=pair,
                                     split_name="validation", timestamp=stamp, splits=splits, version=version,
                                     notes=f"single validation read, exposure {args.exposure} (calibrated on exploration)",
                                     exposure=args.exposure, timeframe=timeframe) for pair in pairs]
    decisions = {}
    for experiment_id in ids:
        decision, _ = experiment.decide_experiment(conn, experiment_id, hid)
        decisions[experiment_id] = decision
        print(experiment_id, decision)
    values = set(decisions.values())
    status = ("validation: candidate" if values == {"candidate_for_portfolio"}
              else "not approved at validation" if "rejected" in values or "inconclusive" in values else "validation: mixed")
    registry.set_hypothesis_status(conn, hid, status)
    registry.sync_ledger_markdown(conn)
    registry.dump_sql(conn)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
