import unittest

import numpy as np
import pandas as pd

from lab import causality, dataquality


def prices(n=400, seed=4):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    return pd.DataFrame({"close": close, "high": close * 1.01, "low": close * 0.99, "volume": rng.uniform(1, 2, n)})


def clean(frame):
    out = pd.DataFrame(index=frame.index)
    out["sma"] = frame["close"].rolling(20).mean()
    out["breakout"] = (frame["close"] > frame["high"].rolling(30).max().shift(1)).astype(float)
    out["z"] = (frame["close"] - frame["close"].rolling(50).mean()) / frame["close"].rolling(50).std()
    return out


def leaky_shift(frame):
    out = clean(frame)
    out["leak"] = frame["close"].shift(-1) / frame["close"] - 1  # looks one candle ahead
    return out


def leaky_normalisation(frame):
    out = clean(frame)
    out["leak"] = (frame["close"] - frame["close"].min()) / (frame["close"].max() - frame["close"].min())  # whole series
    return out


def leaky_unwindowed_max(frame):
    out = clean(frame)
    out["leak"] = frame["close"].expanding().max() / frame["close"].max()  # uses the global max
    return out


class CausalityToolTests(unittest.TestCase):
    cuts = (60, 150, 333)

    def test_clean_function_passes_both_checks(self):
        frame = prices()
        self.assertEqual(causality.prefix_invariance(clean, frame, self.cuts), [])
        self.assertEqual(causality.future_corruption(clean, frame, 200), [])

    def test_shift_minus_one_is_caught(self):
        frame = prices()
        self.assertTrue(causality.prefix_invariance(leaky_shift, frame, self.cuts))
        self.assertTrue(causality.future_corruption(leaky_shift, frame, 200))

    def test_full_series_normalisation_is_caught(self):
        frame = prices()
        self.assertTrue(causality.prefix_invariance(leaky_normalisation, frame, self.cuts))
        self.assertTrue(causality.future_corruption(leaky_normalisation, frame, 200))

    def test_global_max_is_caught(self):
        self.assertTrue(causality.prefix_invariance(leaky_unwindowed_max, prices(), self.cuts))


def daily_frame(days=10, start="2022-01-01"):
    dates = pd.date_range(start, periods=days, freq="D", tz="UTC")
    return pd.DataFrame({"date": dates, "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 1.0})


class DataQualityTests(unittest.TestCase):
    def test_clean_daily_frame(self):
        frame = daily_frame()
        self.assertEqual(dataquality.check_daily(frame, as_of=pd.Timestamp("2022-01-20", tz="UTC")), [])

    def test_off_midnight_duplicates_and_unclosed_candles_are_reported(self):
        frame = daily_frame()
        frame.loc[3, "date"] += pd.Timedelta(hours=1)
        problems = dataquality.check_daily(frame, as_of=pd.Timestamp("2022-01-09 12:00", tz="UTC"))
        self.assertTrue(any("00:00 UTC" in p for p in problems))
        self.assertTrue(any("not closed" in p for p in problems))  # candle of 2022-01-09 is still open at 12:00
        dup = pd.concat([daily_frame(3), daily_frame(3)], ignore_index=True)
        self.assertTrue(any("duplicated" in p for p in dataquality.check_daily(dup, as_of=pd.Timestamp("2023-01-01", tz="UTC"))))

    def test_naive_dates_are_rejected(self):
        frame = daily_frame()
        frame["date"] = frame["date"].dt.tz_localize(None)
        self.assertTrue(dataquality.check_daily(frame, as_of=pd.Timestamp("2023-01-01", tz="UTC")))

    def test_daily_matches_its_hourly_aggregate(self):
        hours = pd.date_range("2022-01-01", periods=72, freq="h", tz="UTC")
        rng = np.random.default_rng(1)
        close = 100 + np.cumsum(rng.normal(0, 1, 72))
        hourly = pd.DataFrame({"date": hours, "open": close - 0.1, "high": close + 1, "low": close - 1, "close": close})
        grouped = hourly.groupby(hourly["date"].dt.floor("D"))
        daily = pd.DataFrame({"open": grouped["open"].first(), "high": grouped["high"].max(), "low": grouped["low"].min(),
                              "close": grouped["close"].last()}).reset_index()
        self.assertEqual(dataquality.compare_with_hourly(daily, hourly)["mismatches"], {"open": 0, "high": 0, "low": 0, "close": 0})
        daily.loc[1, "high"] += 5
        self.assertEqual(dataquality.compare_with_hourly(daily, hourly)["mismatches"]["high"], 1)


if __name__ == "__main__":
    unittest.main()
