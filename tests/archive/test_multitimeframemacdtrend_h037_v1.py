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

ROOT = Path(__file__).parents[2]


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / "_archive" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Strat = load_strategy(
    "MultiTimeframeMACDTrend_H037_v1.py", "MultiTimeframeMACDTrend_H037_v1"
)


def make_frame(n: int, start_offset: int = 0) -> pd.DataFrame:
    idx = np.arange(start_offset, start_offset + n)
    prices = 100.0 + 0.01 * idx + 8 * np.sin(idx / 9.0) + 15 * np.sin(idx / 90.0)
    return pd.DataFrame(
        {
            "date": pd.date_range("2022-01-01", periods=n, freq="1h", tz="UTC"),
            "open": prices,
            "high": prices * 1.01,
            "low": prices * 0.99,
            "close": prices,
            "volume": 1.0,
        }
    )


def run(frame: pd.DataFrame) -> pd.DataFrame:
    s = Strat()
    frame = s.populate_indicators(frame, {})
    frame = s.populate_entry_trend(frame, {})
    return s.populate_exit_trend(frame, {})


class H037Tests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strat.INTERFACE_VERSION, 3)
        self.assertEqual(Strat.timeframe, "1h")
        self.assertFalse(Strat.can_short)
        self.assertEqual(Strat.minimal_roi, {"0": 100.0})
        self.assertLess(Strat.stoploss, 0)
        self.assertGreaterEqual(Strat.startup_candle_count, 4200)

    def test_signals_binary_and_present(self) -> None:
        out = run(make_frame(3000))
        for col in ("enter_long", "exit_long"):
            self.assertTrue(set(out[col].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(out["enter_long"].sum(), 0)
        self.assertGreater(out["exit_long"].sum(), 0)

    def test_zero_volume_no_signal(self) -> None:
        frame = make_frame(3000)
        frame["volume"] = 0.0
        out = run(frame)
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(out["exit_long"].fillna(0).sum()), 0)

    def test_undefined_startup_no_signal(self) -> None:
        out = run(make_frame(3000))
        # no closed daily candle is visible during the first day
        self.assertTrue(out["daily_up"].iloc[:24].isna().all())
        self.assertEqual(int(out["enter_long"].iloc[:24].fillna(0).sum()), 0)
        self.assertEqual(int(out["exit_long"].iloc[:1].fillna(0).sum()), 0)

    def test_no_lookahead(self) -> None:
        n = 2000
        short = run(make_frame(n))
        long = run(make_frame(n + 500))
        cols = ["macd", "macd_signal", "daily_macd", "daily_signal", "daily_up"]
        pd.testing.assert_frame_equal(short[cols], long.loc[: n - 1, cols])
        for col in ("enter_long", "exit_long"):
            a = short[col].fillna(0).to_numpy()
            b = long[col].fillna(0).to_numpy()[:n]
            np.testing.assert_array_equal(a, b)


if __name__ == "__main__":
    unittest.main()
