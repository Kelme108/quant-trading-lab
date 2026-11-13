"""Commit exactly a list of paths, and survive a busy git index.

Two defects this module removes (2026-11-13):
1. `git commit -m msg` without paths commits the WHOLE index, so anything another session (or the editor) had staged
   was swept into the pipeline's commit. Here the commit names its paths: other staged files stay staged and out.
2. `git commit` sometimes ended with exit status 128 and the cycle stopped without saying why: the stderr was captured
   and dropped. The usual cause is `.git/index.lock` held for a moment by another git process (the editor's git
   integration, another session). Here a lock error is retried with a short back-off, and any final failure raises
   with git's own message.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Callable

LOCK_MARKERS = ("index.lock", "Unable to create", "cannot lock ref", "Another git process")


class GitError(RuntimeError):
    pass


def _is_lock_error(stderr: str) -> bool:
    return any(marker in stderr for marker in LOCK_MARKERS)


def run_git(args: list[str], root: Path, *, retries: int = 6, delay_s: float = 0.5,
            sleep: Callable[[float], None] = time.sleep) -> subprocess.CompletedProcess:
    """Run git; retry only when it failed because the index or a ref was locked. Raises GitError with stderr."""
    for attempt in range(retries + 1):
        done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
        if done.returncode == 0:
            return done
        if not _is_lock_error(done.stderr or "") or attempt == retries:
            raise GitError(f"git {' '.join(args[:2])} failed (exit {done.returncode}): {(done.stderr or done.stdout).strip()}")
        sleep(delay_s * (2 ** attempt))
    raise AssertionError("unreachable")


def commit_paths(root: Path, paths: list[str], message: str, *, add_all: bool = True, **retry) -> bool:
    """Stage `paths` (creations, changes and, with add_all, removals) and commit ONLY those paths.
    Returns True if a commit was made, False if none of them changed."""
    if not paths:
        return False
    for path in paths:
        if add_all:
            try:
                run_git(["add", "-A", "--", path], root, **retry)
            except GitError as error:
                # a path that never existed, or one .gitignore excludes (results, data): nothing to stage, as before
                if "did not match any files" not in str(error) and "ignored by one of your .gitignore" not in str(error):
                    raise
        elif (Path(root) / path).exists():
            run_git(["add", "--", path], root, **retry)
    staged = run_git(["diff", "--cached", "--no-renames", "--name-only", "-z", "--", *paths], root, **retry).stdout.split("\0")
    staged = [p for p in staged if p]
    if not staged:
        return False
    run_git(["commit", "-q", "-m", message, "--", *staged], root, **retry)
    return True
