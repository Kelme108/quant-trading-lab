import hashlib
import re
import unittest
from pathlib import Path

STRATEGIES = Path(__file__).parents[1] / "user_data" / "strategies"


class H001WrapperTests(unittest.TestCase):
    def test_the_recorded_baseline_hash_matches_the_protected_baseline(self) -> None:
        wrapper = (STRATEGIES / "SmaTrendBaseline_H001_v1.py").read_text(encoding="utf-8")
        recorded = re.search(r'_BASELINE_SHA256 = "([0-9a-f]{64})"', wrapper).group(1)
        self.assertEqual(recorded, hashlib.sha256((STRATEGIES / "SmaTrendBaseline.py").read_bytes()).hexdigest())

    def test_the_wrapper_adds_no_rule_of_its_own(self) -> None:
        wrapper = (STRATEGIES / "SmaTrendBaseline_H001_v1.py").read_text(encoding="utf-8")
        for forbidden in ("populate_", "stoploss =", "timeframe =", "minimal_roi"):
            self.assertNotIn(forbidden, wrapper)
        self.assertIn("class SmaTrendBaseline_H001_v1(SmaTrendBaseline):", wrapper)


if __name__ == "__main__":
    unittest.main()
