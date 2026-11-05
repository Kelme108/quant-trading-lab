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


Strat = load_strategy(
    "IntradayEarlySessionMomentum_H028_v1.py", "IntradayEarlySessionMomentum_H028_v1"
)


def make_frame(n=24 * 30, seed=1):
    rng = np.random.default_rng(seed)
    close = 100 * np.cumprod(1 + rng.normal(0, 0.006, n))
    open_ = np.concatenate([[100.0], close[:-1]])
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC"),
            "open": open_,
            "high": np.maximum(open_, close) * 1.002,
            "low": np.minimum(open_, close) * 0.998,
            "close": close,
            "volume": 1.0,
        }
    )


def run(frame):
    s = Strat()
    frame = s.populate_indicators(frame, {})
    frame = s.populate_entry_trend(frame, {})
    return s.populate_exit_trend(frame, {})


def rally_frame():
    frame = make_frame(48)
    frame["open"] = 100.0
    frame["close"] = 100.0
    frame.loc[3, "close"] = 101.5  # day 0, 03:00 bar
    frame.loc[27, "close"] = 100.5  # day 1: +0.5% only
    return frame


class H028Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strat.INTERFACE_VERSION, 3)
        self.assertEqual(Strat.timeframe, "1h")
        self.assertFalse(Strat.can_short)
        self.assertEqual(Strat.minimal_roi, {"0": 100.0})
        self.assertLess(Strat.stoploss, 0)
        self.assertGreaterEqual(Strat.startup_candle_count, 24)

    def test_rule(self):
        out = run(rally_frame())
        self.assertEqual(out.index[out["enter_long"] == 1].tolist(), [3])
        self.assertEqual(out.index[out["exit_long"] == 1].tolist(), [15, 39])

    def test_binary(self):
        out = run(make_frame())
        for col in ("enter_long", "exit_long"):
            self.assertTrue(set(out[col].dropna().unique()).issubset({1}))

    def test_zero_volume(self):
        frame = rally_frame()
        frame["volume"] = 0.0
        out = run(frame)
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(out["exit_long"].fillna(0).sum()), 0)

    def test_nan_startup(self):
        frame = rally_frame()
        frame.loc[0, "open"] = np.nan  # undefined 00:00 open
        out = run(frame)
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)

    def test_missing_bar_no_signal(self):
        frame = rally_frame().drop(index=1).reset_index(drop=True)
        out = run(frame)
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self):
        full = make_frame(24 * 40)
        n = 24 * 25
        a = run(full.iloc[:n].copy())
        b = run(full.copy()).iloc[:n]
        cols = ["early_return", "enter_long", "exit_long"]
        pd.testing.assert_frame_equal(a[cols], b[cols], check_dtype=False)


if __name__ == "__main__":
    unittest.main()
