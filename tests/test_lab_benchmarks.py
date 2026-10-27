import unittest
from pathlib import Path

import pandas as pd

from lab import benchmarks


class BenchmarksTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(self._get_tmp_dir())
        self.feather_path = self.tmp_dir / "fake.feather"
        dates = pd.date_range("2026-01-01", periods=5, freq="1h", tz="UTC")
        frame = pd.DataFrame(
            {
                "date": dates,
                "open": [100.0, 110.0, 90.0, 95.0, 120.0],
                "high": [105.0, 115.0, 95.0, 100.0, 125.0],
                "low": [95.0, 85.0, 80.0, 90.0, 115.0],
                "close": [100.0, 110.0, 90.0, 95.0, 120.0],
                "volume": [1.0, 1.0, 1.0, 1.0, 1.0],
            }
        )
        frame.to_feather(self.feather_path)

    def _get_tmp_dir(self) -> str:
        import tempfile

        self._tmp_context = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_context.cleanup)
        return self._tmp_context.name

    def test_cash_benchmark_is_always_zero(self) -> None:
        result = benchmarks.cash_benchmark("2026-01-01T00:00:00Z", "2026-01-01T04:00:00Z")
        self.assertEqual(result["return_pct"], 0.0)
        self.assertEqual(result["max_drawdown_pct"], 0.0)

    def test_buy_and_hold_return_matches_first_to_last_close(self) -> None:
        result = benchmarks.buy_and_hold_benchmark(
            self.feather_path, "2026-01-01T00:00:00Z", "2026-01-01T04:00:00Z"
        )
        # close goes 100 -> 120 across the full window
        self.assertAlmostEqual(result["return_pct"], 20.0)
        self.assertEqual(result["candle_count"], 5)

    def test_buy_and_hold_drawdown_reflects_the_dip(self) -> None:
        result = benchmarks.buy_and_hold_benchmark(
            self.feather_path, "2026-01-01T00:00:00Z", "2026-01-01T04:00:00Z"
        )
        # peak 110 at hour 1, trough 90 at hour 2 -> drawdown ~18.18%
        self.assertAlmostEqual(result["max_drawdown_pct"], (110 - 90) / 110 * 100, places=4)

    def test_window_outside_data_raises(self) -> None:
        with self.assertRaises(ValueError):
            benchmarks.buy_and_hold_benchmark(
                self.feather_path, "2030-01-01T00:00:00Z", "2030-01-02T00:00:00Z"
            )

    def test_compute_benchmarks_returns_both(self) -> None:
        result = benchmarks.compute_benchmarks(
            self.feather_path, "2026-01-01T00:00:00Z", "2026-01-01T04:00:00Z"
        )
        self.assertEqual(set(result), {"cash", "buy_and_hold"})


if __name__ == "__main__":
    unittest.main()
