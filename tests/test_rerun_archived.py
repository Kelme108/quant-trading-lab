import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from lab import registry  # noqa: E402

_spec = importlib.util.spec_from_file_location("rerun_archived", ROOT / "research" / "tools" / "rerun_archived.py")
rerun_archived = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rerun_archived)

EXPECTED = {"H-005", "H-007", "H-008", "H-010", "H-011", "H-012", "H-013", "H-014", "H-015", "H-016"}
KEPT = {"SmaTrendBaseline", "DonchianBreakoutBaseline", "BollingerMeanReversionBaseline",
        "WeeklyBreakoutRegime_H009_v1", "Sma200Baseline"}


class ArchiveRecordTests(unittest.TestCase):
    def setUp(self):
        self.conn = registry.connect()

    def tearDown(self):
        self.conn.close()

    def test_all_rejected_families_are_archived(self):
        rows = registry.list_archived_strategies(self.conn)
        self.assertEqual({r["hypothesis_id"] for r in rows}, EXPECTED)

    def test_recorded_sha_matches_file_and_manifests_for_every_archived_strategy(self):
        self.assertEqual(rerun_archived.verify_all(self.conn), [])

    def test_archiving_does_not_change_hypothesis_status(self):
        for row in registry.list_archived_strategies(self.conn):
            status = self.conn.execute(
                "SELECT status FROM hypotheses WHERE id = ?", (row["hypothesis_id"],)
            ).fetchone()["status"]
            self.assertNotIn("archived", status)

    def test_baselines_and_candidate_stay_in_strategy_path(self):
        present = {p.stem for p in (ROOT / "user_data" / "strategies").glob("*.py")}
        self.assertTrue(KEPT <= present)
        for row in registry.list_archived_strategies(self.conn):
            self.assertFalse((ROOT / row["original_path"]).exists())
            self.assertTrue((ROOT / row["archive_path"]).is_file())


class VerifyRowTests(unittest.TestCase):
    def test_detects_modified_file_and_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a").mkdir()
            file = root / "a" / "S.py"
            file.write_text("x = 1\n")
            good = rerun_archived.sha256_file(file)
            row = {"hypothesis_id": "H-999", "strategy_class": "S", "archive_path": "a/S.py",
                   "strategy_sha256": good}
            empty = root / "manifests"
            empty.mkdir()
            self.assertEqual(rerun_archived.verify_row(row, root, empty), [])
            file.write_text("x = 2\n")
            self.assertEqual(len(rerun_archived.verify_row(row, root, empty)), 1)
            file.unlink()
            self.assertIn("missing", rerun_archived.verify_row(row, root, empty)[0])

    def test_manifest_mismatch_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file = root / "S.py"
            file.write_text("x = 1\n")
            sha = rerun_archived.sha256_file(file)
            manifests = root / "m"
            manifests.mkdir()
            (manifests / "e.yaml").write_text(
                f'code:\n  strategy_file: "user_data/strategies/S.py"\n  strategy_sha256: "{"0" * 64}"\n'
            )
            row = {"hypothesis_id": "H-999", "strategy_class": "S", "archive_path": "S.py", "strategy_sha256": sha}
            self.assertEqual(len(rerun_archived.verify_row(row, root, manifests)), 1)


class RerunGuardTests(unittest.TestCase):
    def test_validation_and_final_test_splits_are_refused(self):
        conn = registry.connect()
        try:
            for split in ("validation", "final_test"):
                with self.assertRaises(SystemExit):
                    rerun_archived.rerun(conn, "H-010", split=split, pair="BTC/USDT", scenario="base", exposure=1.0)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
