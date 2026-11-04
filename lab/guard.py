"""After each agent step, check that it only touched files it was allowed to,
and that no protected (frozen) file changed.

This never trusts an agent's own report of what it did; it inspects the
actual working tree via `git diff`/`git status`, and re-hashes the files
listed in tests/test_protected_files.py.
"""

from __future__ import annotations

import hashlib
import subprocess
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).parents[1]

# Mirrors tests/test_protected_files.py; kept in sync manually since both
# express the same invariant from different angles (one is a unit test, one
# is a runtime guard invoked between agent steps).
PROTECTED_FILES = (
    "user_data/strategies/SmaTrendBaseline.py",
    "user_data/strategies/DonchianBreakoutBaseline.py",
    "user_data/strategies/BollingerMeanReversionBaseline.py",
    "user_data/config.dryrun.json",
    "docker-compose.yml",
    "research/validation-protocol-v2.md",
    "lab/config/gates.json",
)

# Allowed write paths per agent, as glob patterns relative to the repo root.
AGENT_ALLOWED_PATHS = {
    "research": ("research/proposals/*",),
    "scout": ("research/intake/*",),
    "developer": ("user_data/strategies/*", "tests/*"),
    "quant": ("research/experiments/*/quant.md",),
    "risk": ("research/experiments/*/risk.md",),
    "validator": ("research/experiments/*/validator.md",),
}


class GuardViolation(RuntimeError):
    """Raised when an agent step touched a disallowed or protected file."""


def changed_files(root: Path = ROOT) -> list[str]:
    """Files changed in the working tree, tracked or not, relative to root.

    Combines `git diff --name-only` (tracked changes) with
    `git status --porcelain` untracked entries, since a new file an agent
    creates would not show up in `git diff` alone.
    """
    tracked = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()

    # -uall lists every untracked FILE; without it git collapses a brand-new
    # directory into a single "dir/" entry that no per-file pattern matches.
    status = subprocess.run(
        ["git", "status", "--porcelain", "-uall"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    untracked = [line[3:] for line in status if line[:2] == "??"]

    return sorted(set(tracked) | set(untracked))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


Baseline = dict[str, str | None]


def snapshot(root: Path = ROOT) -> Baseline:
    """Content hash of every file that differs from HEAD right now (None if
    it was deleted). Take one before an agent step and pass it to enforce()."""
    return {
        path: (sha256_file(root / path) if (root / path).is_file() else None)
        for path in changed_files(root)
    }


def changed_since(baseline: Baseline, root: Path = ROOT) -> list[str]:
    """Files whose content differs from `baseline`, i.e. what a step changed.

    A path that was clean before and is dirty now counts, as does one that was
    dirty before and has since changed again or been reverted to HEAD. Work
    that was already uncommitted before the step does not count against it.
    """
    now = snapshot(root)
    missing = object()
    changed = {path for path, digest in now.items() if baseline.get(path, missing) != digest}
    changed |= {path for path in baseline if path not in now}
    return sorted(changed)


def check_protected_files_unchanged(root: Path = ROOT) -> list[str]:
    """Return the list of protected files that show up as changed in git."""
    changed = set(changed_files(root))
    return [path for path in PROTECTED_FILES if path in changed]


def check_agent_wrote_only_allowed_paths(
    agent_name: str, root: Path = ROOT, baseline: Baseline | None = None
) -> tuple[list[str], list[str]]:
    """Returns (allowed_changes, disallowed_changes) for this agent's step.

    With a `baseline` only what changed since it is judged; without one, every
    file that differs from HEAD is (the tree must then have been clean).
    """
    patterns = AGENT_ALLOWED_PATHS.get(agent_name)
    if patterns is None:
        raise ValueError(f"unknown agent '{agent_name}'; expected one of {sorted(AGENT_ALLOWED_PATHS)}")

    changed = changed_files(root) if baseline is None else changed_since(baseline, root)
    allowed, disallowed = [], []
    for path in changed:
        normalized = path.replace("\\", "/")
        if any(fnmatch(normalized, pattern) for pattern in patterns):
            allowed.append(path)
        else:
            disallowed.append(path)
    return allowed, disallowed


def enforce(agent_name: str, root: Path = ROOT, baseline: Baseline | None = None) -> None:
    """Raise GuardViolation if this agent's step touched a protected file or
    wrote outside its allowed paths. Call this after every agent step, with
    the snapshot() taken just before it."""
    protected_hit = check_protected_files_unchanged(root)
    if protected_hit:
        raise GuardViolation(
            f"agent '{agent_name}' step modified protected file(s): {protected_hit}"
        )

    _, disallowed = check_agent_wrote_only_allowed_paths(agent_name, root, baseline)
    if disallowed:
        raise GuardViolation(
            f"agent '{agent_name}' step wrote outside its allowed paths: {disallowed}"
        )
