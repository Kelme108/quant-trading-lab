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

ROOT = Path(__file__).parents[2]
CLASS_NAME = "VolumeProfileValueAreaReject_H048_v1"


def load_module():
    path = ROOT / "user_data" / "strategies" / "_archive" / (CLASS_NAME + ".py")
    spec = importlib.util.spec_from_file_location(CLASS_NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()
Strategy = getattr(MODULE, CLASS_NAME)


def make_frame(n=480, seed=1):
    rng = np.random.default_rng(seed)
    close = 100 + np.cumsum(rng.normal(0, 0.6, n))
    close = np.abs(close) + 20
    high = close * (1 + rng.uniform(0.001, 0.01, n))
    low = close * (1 - rng.uniform(0.001, 0.01, n))
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC"),
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "volume": rng.uniform(1, 10, n),
        }
    )


def run(strategy, frame):
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


class H048Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 200)
        self.assertEqual(Strategy().protections[0]["stop_duration_candles"], 6)

    def test_profile_poc_and_value_area(self):
        # Volume concentrated in a narrow band near 110 within range 100..120.
        high = np.array([120.0, 111.0, 111.0, 111.0, 105.0])
        low = np.array([100.0, 109.0, 109.0, 109.0, 104.0])
        vol = np.array([1.0, 50.0, 50.0, 50.0, 1.0])
        val, poc = MODULE.compute_profile(high, low, vol)
        self.assertTrue(108.0 <= poc <= 112.0)
        self.assertTrue(100.0 < val <= 110.0)
        self.assertLess(val, poc)

    def test_binary_signals(self):
        out = run(Strategy(), make_frame())
        for col in ("enter_long", "exit_long"):
            if col in out:
                self.assertTrue(set(out[col].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_no_signals(self):
        frame = make_frame()
        frame["volume"] = 0.0
        out = run(Strategy(), frame)
        for col in ("enter_long", "exit_long"):
            self.assertEqual(int(out.get(col, pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_nan_startup_no_signals(self):
        frame = make_frame()
        out = run(Strategy(), frame)
        self.assertTrue(out["va_low"].iloc[:168].isna().all())
        self.assertTrue(out["poc"].iloc[:168].isna().all())
        for col in ("enter_long", "exit_long"):
            self.assertEqual(int(out.get(col, pd.Series(dtype=float)).iloc[:168].fillna(0).sum()), 0)

    def test_signals_use_no_future_candles(self):
        strategy = Strategy()
        full = make_frame(600, seed=3)
        n = 400
        short = run(strategy, full.iloc[:n])
        long = run(strategy, full)
        cols = ["va_low", "poc", "sweep_low"]
        pd.testing.assert_frame_equal(
            short[cols].iloc[:n].reset_index(drop=True),
            long[cols].iloc[:n].reset_index(drop=True),
            check_dtype=False,
        )
        for col in ("enter_long", "exit_long"):
            a = short[col].iloc[:n].fillna(0) if col in short else pd.Series(0, index=range(n))
            b = long[col].iloc[:n].fillna(0) if col in long else pd.Series(0, index=range(n))
            self.assertEqual(a.tolist(), b.tolist())


if __name__ == "__main__":
    unittest.main()
