import subprocess
import tempfile
import unittest
from pathlib import Path

from lab import guard


def _run_git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


class TemporaryGitRepo:
    """A throwaway git repo so guard.py's git-backed checks can be tested
    without touching the real project repository."""

    def __enter__(self) -> Path:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _run_git(["init", "-q"], self.root)
        _run_git(["config", "user.email", "test@example.com"], self.root)
        _run_git(["config", "user.name", "Test"], self.root)

        for relative in (
            "user_data/strategies/SmaTrendBaseline.py",
            "user_data/strategies/DonchianBreakoutBaseline.py",
            "user_data/strategies/BollingerMeanReversionBaseline.py",
            "user_data/config.dryrun.json",
            "docker-compose.yml",
            "research/validation-protocol-v2.md",
            "lab/config/gates.json",
            "research/proposals/.gitkeep",
            "tests/.gitkeep",
            "research/experiments/exp-001/quant.md",
            "research/experiments/exp-001/risk.md",
            "research/experiments/exp-001/validator.md",
        ):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("original\n", encoding="utf-8")

        _run_git(["add", "-A", "."], self.root)
        _run_git(["commit", "-q", "-m", "initial"], self.root)
        return self.root

    def __exit__(self, *exc_info) -> None:
        self._tmp.cleanup()


class ChangedFilesTests(unittest.TestCase):
    def test_no_changes_reports_empty(self) -> None:
        with TemporaryGitRepo() as root:
            self.assertEqual(guard.changed_files(root), [])

    def test_tracked_edit_is_detected(self) -> None:
        with TemporaryGitRepo() as root:
            (root / "docker-compose.yml").write_text("changed\n", encoding="utf-8")
            self.assertIn("docker-compose.yml", guard.changed_files(root))

    def test_new_untracked_file_is_detected(self) -> None:
        with TemporaryGitRepo() as root:
            new_file = root / "research" / "proposals" / "H-099.json"
            new_file.write_text("{}", encoding="utf-8")
            self.assertIn("research/proposals/H-099.json", guard.changed_files(root))


class ProtectedFilesGuardTests(unittest.TestCase):
    def test_unchanged_protected_files_pass(self) -> None:
        with TemporaryGitRepo() as root:
            self.assertEqual(guard.check_protected_files_unchanged(root), [])

    def test_editing_a_baseline_is_flagged(self) -> None:
        with TemporaryGitRepo() as root:
            strategy = root / "user_data" / "strategies" / "SmaTrendBaseline.py"
            strategy.write_text("# tampered\n", encoding="utf-8")
            hits = guard.check_protected_files_unchanged(root)
            self.assertIn("user_data/strategies/SmaTrendBaseline.py", hits)

    def test_editing_gates_json_is_flagged(self) -> None:
        with TemporaryGitRepo() as root:
            (root / "lab" / "config" / "gates.json").write_text("{}", encoding="utf-8")
            hits = guard.check_protected_files_unchanged(root)
            self.assertIn("lab/config/gates.json", hits)


class AgentAllowedPathsTests(unittest.TestCase):
    def test_developer_may_write_strategies_and_tests(self) -> None:
        with TemporaryGitRepo() as root:
            new_strategy = root / "user_data" / "strategies" / "DonchianBreakoutBaseline_H005_v1.py"
            new_strategy.write_text("# new variant\n", encoding="utf-8")
            new_test = root / "tests" / "test_new_strategy.py"
            new_test.write_text("# test\n", encoding="utf-8")

            allowed, disallowed = guard.check_agent_wrote_only_allowed_paths("developer", root)
            self.assertIn("user_data/strategies/DonchianBreakoutBaseline_H005_v1.py", allowed)
            self.assertIn("tests/test_new_strategy.py", allowed)
            self.assertEqual(disallowed, [])

    def test_developer_editing_a_frozen_baseline_is_disallowed(self) -> None:
        with TemporaryGitRepo() as root:
            strategy = root / "user_data" / "strategies" / "SmaTrendBaseline.py"
            strategy.write_text("# tampered\n", encoding="utf-8")
            # This path *is* within developer's glob (user_data/strategies/*),
            # so the path-allowlist alone would pass it; only the protected-file
            # hash check in enforce() can catch this. Confirmed below via enforce().
            allowed, disallowed = guard.check_agent_wrote_only_allowed_paths("developer", root)
            self.assertIn("user_data/strategies/SmaTrendBaseline.py", allowed)
            self.assertEqual(disallowed, [])

    def test_research_writing_outside_proposals_is_disallowed(self) -> None:
        with TemporaryGitRepo() as root:
            stray_file = root / "user_data" / "strategies" / "SneakyStrategy.py"
            stray_file.write_text("# should not be here", encoding="utf-8")
            allowed, disallowed = guard.check_agent_wrote_only_allowed_paths("research", root)
            self.assertIn("user_data/strategies/SneakyStrategy.py", disallowed)
            self.assertEqual(allowed, [])

    def test_quant_may_only_write_its_own_report(self) -> None:
        with TemporaryGitRepo() as root:
            (root / "research" / "experiments" / "exp-001" / "quant.md").write_text(
                "analysis\n", encoding="utf-8"
            )
            allowed, disallowed = guard.check_agent_wrote_only_allowed_paths("quant", root)
            self.assertIn("research/experiments/exp-001/quant.md", allowed)
            self.assertEqual(disallowed, [])

    def test_quant_writing_risk_report_is_disallowed(self) -> None:
        with TemporaryGitRepo() as root:
            (root / "research" / "experiments" / "exp-001" / "risk.md").write_text(
                "should not write this\n", encoding="utf-8"
            )
            allowed, disallowed = guard.check_agent_wrote_only_allowed_paths("quant", root)
            self.assertIn("research/experiments/exp-001/risk.md", disallowed)

    def test_unknown_agent_raises(self) -> None:
        with TemporaryGitRepo() as root:
            with self.assertRaises(ValueError):
                guard.check_agent_wrote_only_allowed_paths("mystery-agent", root)


class EnforceTests(unittest.TestCase):
    def test_enforce_passes_on_clean_allowed_change(self) -> None:
        with TemporaryGitRepo() as root:
            (root / "research" / "proposals" / "H-099.json").write_text("{}", encoding="utf-8")
            guard.enforce("research", root)  # must not raise

    def test_enforce_raises_on_protected_file_change(self) -> None:
        with TemporaryGitRepo() as root:
            strategy = root / "user_data" / "strategies" / "SmaTrendBaseline.py"
            strategy.write_text("# tampered\n", encoding="utf-8")
            with self.assertRaises(guard.GuardViolation):
                guard.enforce("developer", root)

    def test_enforce_raises_on_disallowed_path(self) -> None:
        with TemporaryGitRepo() as root:
            (root / "user_data" / "strategies" / "Sneaky.py").write_text("x", encoding="utf-8")
            with self.assertRaises(guard.GuardViolation):
                guard.enforce("research", root)


class BaselineTests(unittest.TestCase):
    """Work that was already uncommitted before an agent step must not be
    blamed on that step; only what the step itself changed is judged."""

    def test_preexisting_uncommitted_work_is_not_a_violation(self) -> None:
        with TemporaryGitRepo() as root:
            (root / "lab" / "config").mkdir(parents=True, exist_ok=True)
            (root / "lab" / "orchestrator_leftover.py").write_text("x", encoding="utf-8")
            baseline = guard.snapshot(root)
            (root / "research" / "proposals" / "H-099.json").write_text("{}", encoding="utf-8")
            guard.enforce("research", root, baseline)  # must not raise

    def test_without_a_baseline_the_same_leftover_is_a_violation(self) -> None:
        with TemporaryGitRepo() as root:
            (root / "lab" / "orchestrator_leftover.py").parent.mkdir(parents=True, exist_ok=True)
            (root / "lab" / "orchestrator_leftover.py").write_text("x", encoding="utf-8")
            (root / "research" / "proposals" / "H-099.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(guard.GuardViolation):
                guard.enforce("research", root)

    def test_a_step_that_writes_outside_its_paths_is_caught_despite_the_baseline(self) -> None:
        with TemporaryGitRepo() as root:
            (root / "lab").mkdir(exist_ok=True)
            (root / "lab" / "leftover.py").write_text("x", encoding="utf-8")
            baseline = guard.snapshot(root)
            (root / "user_data" / "strategies" / "Sneaky.py").write_text("x", encoding="utf-8")
            with self.assertRaises(guard.GuardViolation):
                guard.enforce("research", root, baseline)

    def test_editing_an_already_dirty_file_again_counts_as_a_change(self) -> None:
        with TemporaryGitRepo() as root:
            target = root / "lab" / "leftover.py"
            target.parent.mkdir(exist_ok=True)
            target.write_text("first", encoding="utf-8")
            baseline = guard.snapshot(root)
            target.write_text("second", encoding="utf-8")
            self.assertEqual(guard.changed_since(baseline, root), ["lab/leftover.py"])

    def test_a_dirty_file_reverted_to_head_counts_as_a_change(self) -> None:
        with TemporaryGitRepo() as root:
            tracked = root / "tests" / ".gitkeep"
            tracked.write_text("dirty" + chr(10), encoding="utf-8")
            baseline = guard.snapshot(root)
            tracked.write_text("original" + chr(10), encoding="utf-8")
            self.assertEqual(guard.changed_since(baseline, root), ["tests/.gitkeep"])

    def test_a_step_that_changes_nothing_reports_nothing(self) -> None:
        with TemporaryGitRepo() as root:
            baseline = guard.snapshot(root)
            self.assertEqual(guard.changed_since(baseline, root), [])

    def test_a_brand_new_directory_is_listed_file_by_file(self) -> None:
        with TemporaryGitRepo() as root:
            baseline = guard.snapshot(root)
            new_dir = root / "research" / "experiments" / "H-005-exploration"
            new_dir.mkdir(parents=True)
            (new_dir / "quant.md").write_text("report", encoding="utf-8")
            self.assertEqual(
                guard.changed_since(baseline, root),
                ["research/experiments/H-005-exploration/quant.md"],
            )
            guard.enforce("quant", root, baseline)  # allowed for quant; must not raise


if __name__ == "__main__":
    unittest.main()
