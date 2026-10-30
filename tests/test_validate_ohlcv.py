import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1] / "research"))
import validate_ohlcv  # noqa: E402


class GapToleranceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "candles.feather"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, hours: list[int]) -> None:
        base = pd.Timestamp("2026-01-01T00:00:00Z")
        frame = pd.DataFrame(
            {
                "date": [base + pd.Timedelta(hours=h) for h in hours],
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1.0,
            }
        )
        frame.to_feather(self.path)

    def test_clean_file_is_valid(self) -> None:
        self.write(list(range(10)))
        report = validate_ohlcv.validate(self.path, "1h")
        self.assertTrue(report["valid"])
        self.assertEqual(report["gaps"], 0)

    def test_any_gap_is_invalid_by_default(self) -> None:
        self.write([0, 1, 2, 5, 6])  # candles 3 and 4 missing
        report = validate_ohlcv.validate(self.path, "1h")
        self.assertFalse(report["valid"])
        self.assertEqual(report["gaps"], 1)
        self.assertEqual(report["largest_gap_missing_hours"], 2.0)

    def test_a_gap_within_tolerance_is_valid_but_still_counted(self) -> None:
        self.write([0, 1, 2, 5, 6])
        report = validate_ohlcv.validate(self.path, "1h", max_gap_hours=2)
        self.assertTrue(report["valid"])
        self.assertEqual(report["gaps"], 1)
        self.assertEqual(report["gaps_over_tolerance"], 0)
        self.assertEqual(report["max_gap_hours_tolerated"], 2)

    def test_a_gap_longer_than_tolerance_is_invalid(self) -> None:
        self.write([0, 1, 2, 5, 6])
        report = validate_ohlcv.validate(self.path, "1h", max_gap_hours=1)
        self.assertFalse(report["valid"])
        self.assertEqual(report["gaps_over_tolerance"], 1)

    def test_tolerance_does_not_excuse_duplicates(self) -> None:
        self.write([0, 1, 1, 2])
        report = validate_ohlcv.validate(self.path, "1h", max_gap_hours=48)
        self.assertFalse(report["valid"])
        self.assertEqual(report["duplicate_timestamps"], 1)


if __name__ == "__main__":
    unittest.main()
