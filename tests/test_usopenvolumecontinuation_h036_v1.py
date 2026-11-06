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


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.__dict__[class_name]


S = load_strategy(
    "USOpenVolumeContinuation_H036_v1.py", "USOpenVolumeContinuation_H036_v1"
)


def make_frame(days: int = 40, surge_day: int = 35) -> pd.DataFrame:
    n = days * 24
    dates = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    close = 100.0 + np.arange(n) * 0.01
    openp = close.copy()
    volume = np.full(n, 10.0)
    frame = pd.DataFrame(
        {"date": dates, "open": openp, "high": close * 1.01, "low": close * 0.99,
         "close": close, "volume": volume}
    )
    if surge_day is not None:
        i = surge_day * 24 + 14
        frame.loc[i, "close"] = frame.loc[i, "open"] * 1.02
        frame.loc[i, "volume"] = 25.0
    return frame


def run(frame: pd.DataFrame) -> pd.DataFrame:
    s = S()
    frame = s.populate_indicators(frame, {})
    frame = s.populate_entry_trend(frame, {})
    return s.populate_exit_trend(frame, {})


class H036Tests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(S.INTERFACE_VERSION, 3)
        self.assertEqual(S.timeframe, "1h")
        self.assertFalse(S.can_short)
        self.assertEqual(S.minimal_roi, {"0": 100.0})
        self.assertLess(S.stoploss, 0)
        self.assertGreaterEqual(S.startup_candle_count, 480)

    def test_entry_and_exit_on_expected_bars(self) -> None:
        out = run(make_frame())
        entries = out.index[out["enter_long"] == 1].tolist()
        self.assertEqual(entries, [35 * 24 + 14])
        exits = out.loc[out["exit_long"] == 1, "date"].dt.hour.unique().tolist()
        self.assertEqual(exits, [18])

    def test_binary_columns(self) -> None:
        out = run(make_frame())
        for col in ("enter_long", "exit_long"):
            self.assertTrue(set(out[col].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_no_signal(self) -> None:
        frame = make_frame()
        frame["volume"] = 0.0
        out = run(frame)
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(out["exit_long"].fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self) -> None:
        # surge before 20 prior 14:00 bars / SMA200 exist
        out = run(make_frame(days=40, surge_day=10))
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self) -> None:
        full = make_frame(days=45, surge_day=35)
        n = 40 * 24
        a = run(full.iloc[:n].copy())
        b = run(full.copy()).iloc[:n]
        for col in ("sma200", "vref", "enter_long", "exit_long"):
            pd.testing.assert_series_equal(
                a[col].reset_index(drop=True), b[col].reset_index(drop=True),
                check_dtype=False,
            )


if __name__ == "__main__":
    unittest.main()
