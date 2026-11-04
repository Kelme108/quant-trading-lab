"""Verify and re-run the original backtest of an archived strategy.

Archived strategy files live in user_data/strategies/_archive/, which Freqtrade does not
load. `verify` checks the file's SHA-256 against the registry and every manifest that
names it. `rerun` copies the file into the strategy path for the duration of one
exploration backtest, then removes the copy. Validation and final-test splits are refused:
a hypothesis's validation is read once, and the holdout is never read here.

    python research/tools/rerun_archived.py verify              # all archived
    python research/tools/rerun_archived.py rerun H-010 --pair BTC/USDT --scenario base
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from lab import registry  # noqa: E402

STRATEGIES = ROOT / "user_data" / "strategies"
MANIFESTS = ROOT / "research" / "manifests"
ALLOWED_SPLITS = ("exploration",)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_hashes(strategy_class: str, manifests_dir: Path = MANIFESTS) -> set[str]:
    """SHA-256 values recorded by manifests that name this strategy file."""
    hashes: set[str] = set()
    pattern = re.compile(r'^\s*strategy_file:\s*"[^"]*/' + re.escape(strategy_class) + r'\.py"', re.M)
    for manifest in sorted(manifests_dir.glob("*.yaml")):
        text = manifest.read_text(encoding="utf-8")
        if pattern.search(text):
            found = re.search(r'^\s*strategy_sha256:\s*"([0-9a-f]{64})"', text, re.M)
            if found:
                hashes.add(found.group(1))
    return hashes


def verify_row(row, root: Path = ROOT, manifests_dir: Path = MANIFESTS) -> list[str]:
    """Return a list of problems (empty when the archived file is byte-identical to the record)."""
    problems = []
    path = root / row["archive_path"]
    if not path.is_file():
        return [f"{row['hypothesis_id']}: missing {row['archive_path']}"]
    actual = sha256_file(path)
    if actual != row["strategy_sha256"]:
        problems.append(f"{row['hypothesis_id']}: file sha {actual} != registry {row['strategy_sha256']}")
    for recorded in manifest_hashes(row["strategy_class"], manifests_dir):
        if recorded != actual:
            problems.append(f"{row['hypothesis_id']}: file sha {actual} != manifest {recorded}")
    return problems


def verify_all(conn) -> list[str]:
    problems: list[str] = []
    for row in registry.list_archived_strategies(conn):
        problems.extend(verify_row(row))
    return problems


def rerun(conn, hypothesis_id: str, *, split: str, pair: str, scenario: str, exposure: float) -> dict:
    from lab import costs, runner

    if split not in ALLOWED_SPLITS:
        raise SystemExit(f"split {split!r} refused: only {ALLOWED_SPLITS} may be re-run from the archive")
    row = next((r for r in registry.list_archived_strategies(conn) if r["hypothesis_id"] == hypothesis_id), None)
    if row is None:
        raise SystemExit(f"{hypothesis_id} is not archived")
    problems = verify_row(row)
    if problems:
        raise SystemExit("SHA-256 check failed, not running:\n" + "\n".join(problems))
    target = STRATEGIES / f"{row['strategy_class']}.py"
    if target.exists():
        raise SystemExit(f"{target} already exists in the strategy path; refusing to overwrite")
    splits = runner.load_splits()
    timerange = runner.resolve_split_timerange(split, splits, pair=pair)
    fee = costs.get_scenario(scenario).effective_fee_per_side
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    experiment_id = f"{stamp}-rerun-{hypothesis_id.lower()}-{pair.replace('/', '-').lower()}"
    shutil.copy2(ROOT / row["archive_path"], target)
    try:
        return runner.run_backtest(
            experiment_id=experiment_id, strategy=row["strategy_class"], timerange=timerange,
            fee=fee, pair=pair, exposure=exposure,
        ) | {"experiment_id": experiment_id}
    finally:
        target.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verify")
    r = sub.add_parser("rerun")
    r.add_argument("hypothesis_id")
    r.add_argument("--split", default="exploration")
    r.add_argument("--pair", default="BTC/USDT")
    r.add_argument("--scenario", default="base")
    r.add_argument("--exposure", type=float, default=1.0)
    args = parser.parse_args()
    conn = registry.connect()
    if args.cmd == "verify":
        problems = verify_all(conn)
        print("\n".join(problems) if problems else f"OK: {len(registry.list_archived_strategies(conn))} archived files match.")
        sys.exit(1 if problems else 0)
    result = rerun(conn, args.hypothesis_id, split=args.split, pair=args.pair, scenario=args.scenario,
                   exposure=args.exposure)
    print({k: result.get(k) for k in ("experiment_id", "status", "total_trades", "profit_total", "artifact_path")})


if __name__ == "__main__":
    main()
