"""Archive a rejected or dropped hypothesis' code without losing reproducibility (step 0.2 of the audit).

The strategy file moves to user_data/strategies/_archive/ (Freqtrade does not load subfolders), its unit test to
tests/archive/ with the two paths it uses adjusted, and the SHA-256 goes to the `archived_strategies` table. Nothing is
deleted and no decision or status changes. If the archived test does not pass, everything is moved back and the
hypothesis stays where it was.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from lab import registry

ROOT = Path(__file__).parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _default_test_runner(test_file: Path, root: Path) -> bool:
    done = subprocess.run([sys.executable, "-m", "pytest", "-q", str(test_file)], cwd=root, capture_output=True, text=True)
    return done.returncode == 0


def retarget_test(text: str) -> str:
    """The archived test lives one folder deeper and loads the strategy from _archive/."""
    text = text.replace("Path(__file__).parents[1]", "Path(__file__).parents[2]")
    if '"strategies" / "_archive"' not in text:
        text = text.replace('"user_data" / "strategies" /', '"user_data" / "strategies" / "_archive" /')
    return text


def archive_hypothesis(conn, hypothesis_id: str, *, root: Path = ROOT, run_test=_default_test_runner) -> dict:
    """{'archived': bool, 'reason': str, 'paths': [moved or created paths relative to root]}."""
    number = int(hypothesis_id.split("-")[1])
    strategies = root / "user_data" / "strategies"
    files = sorted(strategies.glob(f"*_H{number:03d}_v*.py"))
    if not files:
        return {"archived": False, "reason": "no strategy file in the strategy path", "paths": []}
    strategy = files[-1]
    tests = sorted((root / "tests").glob(f"test_*_h{number:03d}_v*.py"))
    archive_dir = strategies / "_archive"
    archive_dir.mkdir(exist_ok=True)
    target = archive_dir / strategy.name
    sha = _sha256(strategy)
    shutil.move(str(strategy), str(target))
    moved_test = None
    if tests:
        (root / "tests" / "archive").mkdir(exist_ok=True)
        moved_test = root / "tests" / "archive" / tests[-1].name
        original_bytes = tests[-1].read_bytes()
        shutil.move(str(tests[-1]), str(moved_test))
        moved_test.write_bytes(retarget_test(original_bytes.decode("utf-8")).encode("utf-8"))
        if not run_test(moved_test, root):
            original_test = tests[-1]
            shutil.move(str(moved_test), str(original_test))
            original_test.write_bytes(original_bytes)  # byte-for-byte what it was (line endings included)
            shutil.move(str(target), str(strategy))
            return {"archived": False, "reason": "the archived test did not pass; nothing was moved", "paths": []}
    registry.add_archived_strategy(
        conn, hypothesis_id=hypothesis_id, strategy_class=strategy.stem,
        original_path=f"user_data/strategies/{strategy.name}", archive_path=f"user_data/strategies/_archive/{strategy.name}",
        strategy_sha256=sha, sha256_source="file_at_archive_time", archived_at_utc=datetime.now(timezone.utc).isoformat(),
    )
    paths = [f"user_data/strategies/{strategy.name}", f"user_data/strategies/_archive/{strategy.name}"]
    if moved_test is not None:
        paths += [f"tests/{moved_test.name}", f"tests/archive/{moved_test.name}"]
    return {"archived": True, "reason": "", "paths": paths, "sha256": sha}
