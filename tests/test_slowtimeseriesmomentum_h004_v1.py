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
NAME = "SlowTimeSeriesMomentum_H004_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, NAME)


Strategy = load()


def make_frame(prices):
    prices = list(prices)
    return pd.DataFrame(
        {
            "open": prices,
            "high": [p * 1.01 for p in prices],
            "low": [p * 0.99 for p in prices],
            "close": prices,
            "volume": [1.0] * len(prices),
        }
    )


def run(frame):
    s = Strategy()
    frame = s.populate_indicators(frame, {})
    frame = s.populate_entry_trend(frame, {})
    return s.populate_exit_trend(frame, {})


def series(n):
    rng = np.random.default_rng(1)
    return 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, n)))


class Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 1440)

    def test_signals_binary_and_present(self):
        out = run(make_frame(series(7000)))
        for col in ("enter_long", "exit_long"):
            self.assertTrue(set(out[col].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(out["enter_long"].fillna(0).sum(), 0)
        self.assertGreater(out["exit_long"].fillna(0).sum(), 0)

    def test_zero_volume_no_signal(self):
        frame = make_frame(series(7000))
        frame["volume"] = 0.0
        out = run(frame)
        self.assertEqual(out["enter_long"].fillna(0).sum(), 0)
        self.assertEqual(out["exit_long"].fillna(0).sum(), 0)

    def test_nan_startup_no_signal(self):
        out = run(make_frame(series(7000)))
        self.assertEqual(out.iloc[:1440]["enter_long"].fillna(0).sum(), 0)
        self.assertEqual(out.iloc[:720]["exit_long"].fillna(0).sum(), 0)

    def test_no_lookahead(self):
        prices = series(7000)
        n = 6000
        a = run(make_frame(prices[:n]))
        b = run(make_frame(prices))
        cols = [c for c in a.columns if c != "enter_tag" and c != "exit_tag"]
        pd.testing.assert_frame_equal(
            a[cols].reset_index(drop=True),
            b.loc[: n - 1, cols].reset_index(drop=True),
            check_dtype=False,
        )


if __name__ == "__main__":
    unittest.main()
