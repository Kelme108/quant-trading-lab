"""Freeze (or check) a strategy for dry-run evidence collection.

  python research/tools/forward_freeze.py H-009            # write research/forward/H-009-freeze.json
  python research/tools/forward_freeze.py H-009 --check    # exit 1 if any frozen file changed

Freezing needs the user's recorded approval for the stage `dryrun` (research/tools/approve.py H-009 --stage dryrun)
and every frozen file committed in git, so the recorded commit contains exactly the hashed bytes. It does not start
anything: the user starts the bots with `docker compose -f docker-compose.forward.yml up -d`.
The work is lab/forward.py.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lab import forward, registry  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("hypothesis_id")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    hid = args.hypothesis_id
    if args.check:
        problems = forward.check_freeze(hid)
        for problem in problems:
            print(problem)
        print("freeze OK: every file is byte-identical to the record" if not problems else f"{len(problems)} problem(s)")
        return 1 if problems else 0
    conn = registry.connect()
    if registry.get_hypothesis(conn, hid) is None:
        print(f"{hid} is not registered")
        return 2
    if not registry.has_approval(conn, hid, "dryrun"):
        print(f"{hid}: freezing for dry-run needs the user's approval. Run: python research/tools/approve.py {hid} --stage dryrun")
        return 5
    path = forward.freeze_path(hid)
    if path.exists():
        print(f"{hid}: already frozen ({path.relative_to(ROOT)}); a change of rule, parameter or exposure is a new hypothesis")
        return 4
    try:
        frozen = forward.build_freeze(hid)
    except (FileNotFoundError, ValueError) as error:
        print(error)
        return 3
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(frozen, indent=2, ensure_ascii=False), encoding="utf-8")
    conn.execute("UPDATE hypotheses SET notes = COALESCE(notes, '') || ' ' || ? WHERE id = ?", (
        f"[Frozen for dry-run evidence collection {frozen['frozen_at_utc']}, commit {frozen['git_commit'][:10]}, strategy sha256 "
        f"{frozen['strategy']['sha256'][:12]}; {forward.LABEL}]", hid))
    conn.commit()
    registry.sync_ledger_markdown(conn)
    registry.dump_sql(conn)
    print(f"wrote {path.relative_to(ROOT)}; commit it, then start the bots yourself:")
    print("  docker compose -f docker-compose.forward.yml up -d")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
