"""lab/gitops.py: a commit carries only its own paths, survives a briefly held index.lock, and reports git's error."""

import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path

from lab import gitops


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout


class GitOpsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "lab@example.invalid")
        git(self.root, "config", "user.name", "lab")
        (self.root / ".gitignore").write_text("ignored/\n")
        (self.root / "a.txt").write_text("a\n")
        (self.root / "old.txt").write_text("old\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "init")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_only_the_given_paths_are_committed_and_other_staged_files_stay_staged(self) -> None:
        (self.root / "mine.txt").write_text("mine\n")
        (self.root / "theirs.txt").write_text("theirs\n")
        git(self.root, "add", "theirs.txt")                      # another session staged this
        (self.root / "old.txt").unlink()
        self.assertTrue(gitops.commit_paths(self.root, ["mine.txt", "old.txt", "never.txt", "ignored/x"], "mine"))
        self.assertEqual(sorted(git(self.root, "show", "--name-only", "--format=", "HEAD").split()), ["mine.txt", "old.txt"])
        self.assertEqual(git(self.root, "diff", "--cached", "--name-only").split(), ["theirs.txt"])
        self.assertFalse(gitops.commit_paths(self.root, ["mine.txt"], "nothing changed"))

    def test_add_without_removals_skips_missing_paths(self) -> None:
        (self.root / "a.txt").write_text("changed\n")
        self.assertTrue(gitops.commit_paths(self.root, ["a.txt"], "a", add_all=False))
        self.assertEqual(git(self.root, "status", "--porcelain").strip(), "")

    def test_a_briefly_held_index_lock_is_waited_out(self) -> None:
        lock = self.root / ".git" / "index.lock"
        lock.write_text("")
        threading.Thread(target=lambda: (time.sleep(0.4), lock.unlink())).start()
        (self.root / "b.txt").write_text("b\n")
        self.assertTrue(gitops.commit_paths(self.root, ["b.txt"], "b", delay_s=0.1))
        self.assertIn("b.txt", git(self.root, "show", "--name-only", "--format=", "HEAD"))

    def test_a_lock_that_stays_fails_with_gits_message(self) -> None:
        (self.root / ".git" / "index.lock").write_text("")
        (self.root / "c.txt").write_text("c\n")
        slept = []
        with self.assertRaises(gitops.GitError) as caught:
            gitops.commit_paths(self.root, ["c.txt"], "c", retries=2, sleep=slept.append)
        self.assertIn("index.lock", str(caught.exception))
        self.assertEqual(slept, [0.5, 1.0])

    def test_a_real_error_is_not_retried(self) -> None:
        slept = []
        with self.assertRaises(gitops.GitError):
            gitops.run_git(["no-such-command"], self.root, sleep=slept.append)
        self.assertEqual(slept, [])


if __name__ == "__main__":
    unittest.main()
