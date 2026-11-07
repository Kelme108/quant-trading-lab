import importlib.util
import math
import sys
import types
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


# Keep the tests runnable without installing Freqtrade or TA-Lib on the host.
freqtrade = types.ModuleType("freqtrade")
strategy_module = types.ModuleType("freqtrade.strategy")
strategy_module.IStrategy = object
freqtrade.strategy = strategy_module
sys.modules.setdefault("freqtrade", freqtrade)
sys.modules.setdefault("freqtrade.strategy", strategy_module)

talib = types.ModuleType("talib")
talib_abstract = types.ModuleType("talib.abstract")
talib_abstract.SMA = lambda dataframe, timeperiod: dataframe["close"].rolling(timeperiod).mean()
talib_abstract.RSI = lambda dataframe, timeperiod: pd.Series(50.0, index=dataframe.index)
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)


ROOT = Path(__file__).parents[1]


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Strategy = load_strategy("RealizedSkewnessDay_H070_v1.py", "RealizedSkewnessDay_H070_v1")


def make_frame(n: int, seed: int = 7) -> pd.DataFrame:
    """15m bars from 00:00 UTC with occasional sharp down-bursts (negative skew days)."""
    rng = np.random.default_rng(seed)
    rets = rng.normal(0.0, 0.002, n)
    jumps = rng.random(n) < 0.01
    rets[jumps] -= 0.03
    close = 100.0 * np.exp(np.cumsum(rets))
    dates = pd.date_range("2024-01-01 00:00", periods=n, freq="15min", tz="UTC")
    return pd.DataFrame(
        {
            "date": dates,
            "open": close,
            "high": close * 1.002,
            "low": close * 0.998,
            "close": close,
            "volume": np.full(n, 10.0),
        }
    )


def run(strategy, frame: pd.DataFrame) -> pd.DataFrame:
    frame = strategy.populate_indicators(frame, {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    return frame


class RealizedSkewnessDayTests(unittest.TestCase):
    def test_class_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.99)
        self.assertGreaterEqual(Strategy.startup_candle_count, 192)

    def test_signals_are_binary_and_on_clock(self) -> None:
        frame = run(Strategy(), make_frame(96 * 30))
        self.assertGreater(int(frame["enter_long"].fillna(0).sum()), 0)
        for column in ("enter_long", "exit_long"):
            values = frame[column].dropna().unique().tolist()
            self.assertTrue(set(values).issubset({1}))
        entries = frame[frame["enter_long"] == 1]
        self.assertTrue(((entries["date"].dt.hour == 23) & (entries["date"].dt.minute == 45)).all())
        exits = frame[frame["exit_long"] == 1]
        self.assertTrue(((exits["date"].dt.hour == 23) & (exits["date"].dt.minute == 30)).all())

    def test_rsk_matches_direct_formula(self) -> None:
        raw = make_frame(96 * 5)
        frame = run(Strategy(), raw.copy())
        row = 96 * 3 - 1  # 23:45 bar of the third day
        closes = raw["close"].to_numpy()[row - 96: row + 1]
        r = np.log(closes[1:] / closes[:-1])
        rv = float(np.sum(r ** 2))
        expected = math.sqrt(96) * float(np.sum(r ** 3)) / rv ** 1.5
        self.assertAlmostEqual(frame.loc[row, "rsk"], expected, places=10)
        self.assertEqual(
            frame.loc[row, "enter_long"] == 1, expected <= -0.25
        )

    def test_missing_bar_gives_no_signal(self) -> None:
        raw = make_frame(96 * 5)
        # Remove one bar of day 3; that day's 23:45 statistic must be undefined.
        dropped = raw.drop(index=96 * 2 + 40).reset_index(drop=True)
        frame = run(Strategy(), dropped)
        day3_end = frame[frame["date"] == pd.Timestamp("2024-01-03 23:45", tz="UTC")].index[0]
        self.assertTrue(pd.isna(frame.loc[day3_end, "rsk"]))
        self.assertNotEqual(frame.loc[day3_end, "enter_long"], 1)

    def test_flat_day_gives_no_signal(self) -> None:
        raw = make_frame(96 * 3)
        raw["close"] = 100.0
        frame = run(Strategy(), raw)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)

    def test_zero_volume_does_not_create_signals(self) -> None:
        raw = make_frame(96 * 10)
        raw["volume"] = 0.0
        frame = run(Strategy(), raw)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame["exit_long"].fillna(0).sum()), 0)

    def test_nan_startup_values_do_not_create_signals(self) -> None:
        strategy = Strategy()
        frame = run(strategy, make_frame(96 * 10))
        self.assertTrue(frame.loc[:95, "rsk"].isna().all())
        startup = strategy.startup_candle_count
        self.assertEqual(int(frame.iloc[:96]["enter_long"].fillna(0).sum()), 0)
        self.assertTrue(frame.loc[frame["enter_long"] == 1, "rsk"].notna().all())
        self.assertLessEqual(96, startup)

    def test_signals_do_not_change_when_future_candles_are_appended(self) -> None:
        full = make_frame(96 * 20 + 37)
        n = 96 * 12 + 50
        before = run(Strategy(), full.iloc[:n].copy())
        after = run(Strategy(), full.copy())
        columns = ["rv", "rsk", "enter_long", "exit_long"]
        pd.testing.assert_frame_equal(
            before.loc[: n - 1, columns].reset_index(drop=True),
            after.loc[: n - 1, columns].reset_index(drop=True),
            check_dtype=False,
        )


if __name__ == "__main__":
    unittest.main()
