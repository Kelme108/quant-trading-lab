"""The single validation read of a hypothesis (step 2.8). Refuses to run twice and requires exploration candidate on every pair.

usage: python research/tools/validate_once.py H-016 --exposure 0.15
The exposure must be the one calibrated on the exploration split (stored in the hypothesis notes); nothing else is tuned.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lab import autopilot, registry, runner  # noqa: E402


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
    if not registry.has_approval(conn, hid, "validation"):
        print(f"{hid}: the validation split is read once and only with the user's approval; none is recorded. "
              f"Run: python research/tools/approve.py {hid} --stage validation")
        return 5
    already = conn.execute("select count(*) n from experiments where hypothesis_id=? and split='validation'", (hid,)).fetchone()["n"]
    if already:
        print(f"{hid}: validation was already read ({already} experiments); not reading it again.")
        return 4
    # the same single read the autopilot policy uses (lab/autopilot.py)
    decisions = autopilot.read_validation(conn, hid, args.exposure, root=ROOT, pairs=pairs)
    for pair, decision in decisions.items():
        print(pair, decision)
    registry.sync_ledger_markdown(conn)
    registry.dump_sql(conn)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
