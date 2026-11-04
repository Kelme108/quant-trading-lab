"""Record the user's approval for an irreversible step. Only the user runs this; no agent has a tool that can.

  python research/tools/approve.py H-019 --stage validation --note "ok to spend the single validation read"
  python research/tools/approve.py H-019 --stage dryrun     --note "freeze in dry-run as evidence collection"

It checks that the hypothesis exists and, for `validation`, that exploration passed on every pair and the
validation was not read before. It never runs anything: it only writes the approval that the orchestrator and
research/tools/validate_once.py require.
"""
import argparse
import getpass
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lab import registry, runner  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("hypothesis_id")
    parser.add_argument("--stage", choices=registry.APPROVAL_STAGES, required=True)
    parser.add_argument("--note", default="")
    args = parser.parse_args()
    conn = registry.connect()
    hid = args.hypothesis_id
    if registry.get_hypothesis(conn, hid) is None:
        print(f"{hid} is not registered")
        return 2
    if args.stage == "validation":
        pairs = runner.enabled_pairs()
        latest = {r["pair"]: r["decision"] for r in registry.list_latest_decisions(conn)
                  if r["hypothesis_id"] == hid and r["split"] == "exploration"}
        if not all(latest.get(p) == "candidate_for_portfolio" for p in pairs):
            print(f"{hid}: exploration is not a candidate on every pair {latest}; nothing to approve")
            return 3
        if registry.latest_experiments(conn, hid, "validation"):
            print(f"{hid}: the validation split was already read; it cannot be read again")
            return 4
    created = registry.add_approval(
        conn, hypothesis_id=hid, stage=args.stage, approved_by=getpass.getuser(), note=args.note,
        created_at_utc=datetime.now(timezone.utc).isoformat(),
    )
    registry.dump_sql(conn)
    print(f"{hid}: {args.stage} approval {'recorded' if created else 'was already recorded'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
