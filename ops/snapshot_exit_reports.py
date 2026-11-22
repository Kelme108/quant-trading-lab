"""Copy the exit-menu reports and ledgers from the conveyor's work area (ops/state/, git-ignored) into research/b3/ (tracked).

Why: a clone only sees what is tracked. The conveyor writes every run to ops/state/exit_menu and ops/state/exit_brl; without
this snapshot the repository holds a handful of old reports, the count of versions read (multiple testing) is incomplete and the
portal's Esteira page shows far fewer picks than the machine that ran them.

Safe by construction: the tracked ledger must be a byte-prefix of the work one (it is only ever extended, never rewritten), a
report that already exists with different content stops the run, and nothing is copied while a conveyor cycle holds its lock.

    python ops/snapshot_exit_reports.py --dry-run     # show what would be copied
    python ops/snapshot_exit_reports.py               # copy, then `git add research/b3/exit_menu research/b3/exit_brl`
"""
from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = Path(tempfile.gettempdir()) / "trade-initial-esteira-cycle.lock"
PAIRS = [("ops/state/exit_menu", "research/b3/exit_menu"), ("ops/state/exit_brl", "research/b3/exit_brl")]


def snapshot(root: Path = ROOT, dry_run: bool = False, lock: Path | None = LOCK) -> dict:
    """Returns {"copied": [...], "ledgers": [...]} or raises RuntimeError with the reason nothing was touched."""
    if lock is not None and lock.exists():
        raise RuntimeError(f"a conveyor cycle holds {lock}; wait for it to finish")
    plan_reports: list[tuple[Path, Path]] = []
    plan_ledgers: list[tuple[Path, Path]] = []
    for src_rel, dst_rel in PAIRS:
        src, dst = root / src_rel, root / dst_rel
        if not src.is_dir():
            continue
        dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(src.glob("2*.json")):
            target = dst / f.name
            if not target.exists():
                plan_reports.append((f, target))
            elif not filecmp.cmp(f, target, shallow=False):
                raise RuntimeError(f"{target} already exists with different content; not overwriting")
        s_led, d_led = src / "ledger.jsonl", dst / "ledger.jsonl"
        if s_led.exists():
            work = s_led.read_bytes()
            tracked = d_led.read_bytes() if d_led.exists() else b""
            if not work.startswith(tracked):
                raise RuntimeError(f"{d_led} is not a prefix of {s_led}; the ledger was rewritten, resolve by hand")
            if len(work) != len(tracked):
                plan_ledgers.append((s_led, d_led))
    if not dry_run:
        for s, t in plan_reports + plan_ledgers:
            shutil.copy2(s, t)
    return {"copied": [t.relative_to(root).as_posix() for _, t in plan_reports],
            "ledgers": [t.relative_to(root).as_posix() for _, t in plan_ledgers]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    try:
        out = snapshot(dry_run=a.dry_run)
    except RuntimeError as e:
        print(f"nothing copied: {e}", file=sys.stderr)
        return 2
    verb = "would copy" if a.dry_run else "copied"
    print(f"{verb} {len(out['copied'])} report(s) and extend {len(out['ledgers'])} ledger(s)")
    if out["copied"] and not a.dry_run:
        print("next: git add research/b3/exit_menu research/b3/exit_brl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
