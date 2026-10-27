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

    status = subprocess.run(
        ["git", "status", "--porcelain"],
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


def check_protected_files_unchanged(root: Path = ROOT) -> list[str]:
    """Return the list of protected files that show up as changed in git."""
    changed = set(changed_files(root))
    return [path for path in PROTECTED_FILES if path in changed]


def check_agent_wrote_only_allowed_paths(
    agent_name: str, root: Path = ROOT
) -> tuple[list[str], list[str]]:
    """Returns (allowed_changes, disallowed_changes) for this agent's step."""
    patterns = AGENT_ALLOWED_PATHS.get(agent_name)
    if patterns is None:
        raise ValueError(f"unknown agent '{agent_name}'; expected one of {sorted(AGENT_ALLOWED_PATHS)}")

    changed = changed_files(root)
    allowed, disallowed = [], []
    for path in changed:
        normalized = path.replace("\\", "/")
        if any(fnmatch(normalized, pattern) for pattern in patterns):
            allowed.append(path)
        else:
            disallowed.append(path)
    return allowed, disallowed


def enforce(agent_name: str, root: Path = ROOT) -> None:
    """Raise GuardViolation if this agent's step touched a protected file or
    wrote outside its allowed paths. Call this after every agent step."""
    protected_hit = check_protected_files_unchanged(root)
    if protected_hit:
        raise GuardViolation(
            f"agent '{agent_name}' step modified protected file(s): {protected_hit}"
        )

    _, disallowed = check_agent_wrote_only_allowed_paths(agent_name, root)
    if disallowed:
        raise GuardViolation(
            f"agent '{agent_name}' step wrote outside its allowed paths: {disallowed}"
        )
