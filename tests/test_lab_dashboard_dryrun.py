"""The dashboard's dry-run block: read-only, no profit aggregated, tolerant of a missing freeze or registry."""
import json
import tempfile
import unittest
from pathlib import Path

from lab import dashboard


class DryrunStateTests(unittest.TestCase):
    def test_empty_root_gives_empty_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            info = dashboard._forward_test(Path(tmp))
        self.assertEqual(info["hypotheses"], [])
        self.assertEqual(info["intake"], {})

    def test_frozen_hypothesis_without_databases_shows_zero_trades_and_the_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "research" / "forward").mkdir(parents=True)
            (root / "research" / "forward" / "H-009-freeze.json").write_text(json.dumps({
                "frozen_at_utc": "2026-11-04T00:00:00+00:00", "git_commit": "abcdef1234567",
                "files": {"missing.py": "0" * 64}, "databases": {"BTC/USDT": "user_data/none.sqlite"}}), encoding="utf-8")
            info = dashboard._forward_test(root)
        entry = info["hypotheses"][0]
        self.assertEqual(entry["id"], "H-009")
        self.assertFalse(entry["freeze_ok"])
        self.assertEqual(entry["pairs"]["BTC/USDT"]["trades"], 0)
        self.assertNotIn("profit_abs", entry["pairs"]["BTC/USDT"])
        self.assertIn("NÃO validada", entry["label"])


if __name__ == "__main__":
    unittest.main()
