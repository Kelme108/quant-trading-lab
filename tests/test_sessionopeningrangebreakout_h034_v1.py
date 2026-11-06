import importlib.util
import sys
import types
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

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
CLASS_NAME = "SessionOpeningRangeBreakout_H034_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / (CLASS_NAME + ".py")
    spec = importlib.util.spec_from_file_location(CLASS_NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, CLASS_NAME)


Strategy = load_strategy()


def run(frame):
    s = Strategy()
    frame = s.populate_indicators(frame, {})
    frame = s.populate_entry_trend(frame, {})
    return s.populate_exit_trend(frame, {})


def make_frame(n=240, start="2024-01-01 00:00", seed=1):
    rng = np.random.default_rng(seed)
    close = 100 + np.cumsum(rng.normal(0, 0.6, n))
    return pd.DataFrame(
        {
            "date": pd.date_range(start, periods=n, freq="1h", tz="UTC"),
            "open": close,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": 1.0,
        }
    )


def scripted_day():
    """One day: range 100-101 (1%), breakout at 03:00 to 102, then target."""
    n = 24
    close = [100.5] * n
    high = [100.8] * n
    low = [100.2] * n
    high[0], low[0] = 101.0, 100.0
    close[3] = 102.0
    high[3] = 102.1
    close[5] = 103.0  # >= 101 + 1.5 * 1 = 102.5
    high[5] = 103.1
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC"),
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "volume": 1.0,
        }
    )


class H034Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 48)

    def test_binary_signals(self):
        frame = run(make_frame(600))
        for col in ("enter_long", "exit_long"):
            self.assertTrue(set(frame[col].dropna().unique().tolist()).issubset({1}))

    def test_scripted_entry_and_exit(self):
        frame = run(scripted_day())
        self.assertEqual(frame.index[frame["enter_long"] == 1].tolist(), [3])
        self.assertEqual(frame.loc[5, "exit_long"], 1)
        self.assertEqual(frame.loc[19, "exit_long"], 1)

    def test_narrow_range_not_armed(self):
        frame = scripted_day()
        frame.loc[0, "high"] = 100.5
        frame = run(frame)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)

    def test_one_entry_per_day(self):
        frame = scripted_day()
        frame.loc[4:8, "close"] = 102.0
        frame = run(frame)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 1)

    def test_zero_volume_no_signal(self):
        frame = scripted_day()
        frame["volume"] = 0.0
        frame = run(frame)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame["exit_long"].fillna(0).sum()), 0)

    def test_undefined_startup_no_signal(self):
        # Starts at 05:00: no 00:00 range candle until the next day.
        frame = run(make_frame(200, start="2024-01-01 05:00"))
        head = frame.iloc[:19]
        self.assertEqual(int(head["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(head["exit_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self):
        n, k = 300, 70
        full = make_frame(n + k, seed=3)
        a = run(full.iloc[:n].copy())
        b = run(full.copy()).iloc[:n]
        for col in ("enter_long", "exit_long"):
            pd.testing.assert_series_equal(
                a[col].fillna(0), b[col].fillna(0), check_dtype=False
            )


if __name__ == "__main__":
    unittest.main()
