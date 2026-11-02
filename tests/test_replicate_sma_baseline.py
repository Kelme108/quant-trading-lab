import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1] / "research" / "tools"))
import replicate_sma_baseline as rep  # noqa: E402


class FillMissingCandlesTests(unittest.TestCase):
    def test_missing_hour_is_filled_with_previous_close_and_zero_volume(self) -> None:
        dates = pd.to_datetime(["2020-01-01 00:00", "2020-01-01 01:00", "2020-01-01 03:00"], utc=True)
        df = pd.DataFrame({"date": dates, "open": [1.0, 2.0, 4.0], "high": [1.5, 2.5, 4.5],
                           "low": [0.5, 1.5, 3.5], "close": [1.2, 2.2, 4.2], "volume": [10.0, 10.0, 10.0]})
        out = rep.fill_missing_candles(df)
        self.assertEqual(len(out), 4)
        filled = out.iloc[2]
        self.assertEqual((filled["open"], filled["high"], filled["low"], filled["close"]), (2.2, 2.2, 2.2, 2.2))
        self.assertEqual(filled["volume"], 0.0)


class CloseTests(unittest.TestCase):
    def test_round_trip_fee_is_charged_on_both_sides(self) -> None:
        pos = {"open_date": pd.Timestamp("2020-01-01", tz="UTC"), "open_rate": 100.0}
        row = pd.Series({"date": pd.Timestamp("2020-01-02", tz="UTC")})
        trade = rep._close(pos, row, 100.0, "exit_signal", 0.001)
        self.assertAlmostEqual(trade["profit_ratio"], (1 - 0.001) / (1 + 0.001) - 1)


if __name__ == "__main__":
    unittest.main()
