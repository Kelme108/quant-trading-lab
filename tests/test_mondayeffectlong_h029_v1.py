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
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)

ROOT = Path(__file__).parents[1]
path = ROOT / "user_data" / "strategies" / "MondayEffectLong_H029_v1.py"
spec = importlib.util.spec_from_file_location("MondayEffectLong_H029_v1", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Strat = module.MondayEffectLong_H029_v1


def make_frame(n: int, volume: float = 1.0) -> pd.DataFrame:
    # starts on a Monday 00:00 UTC (2024-01-01)
    dates = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
    prices = 100.0 + np.arange(n) * 0.05 + 3 * np.sin(np.arange(n) / 50.0)
    return pd.DataFrame(
        {"date": dates, "open": prices, "high": prices * 1.01, "low": prices * 0.99,
         "close": prices, "volume": [volume] * n}
    )


def run(frame: pd.DataFrame) -> pd.DataFrame:
    s = Strat()
    frame = s.populate_indicators(frame, {})
    frame = s.populate_entry_trend(frame, {})
    return s.populate_exit_trend(frame, {})


class MondayEffectTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strat.INTERFACE_VERSION, 3)
        self.assertEqual(Strat.timeframe, "1h")
        self.assertFalse(Strat.can_short)
        self.assertEqual(Strat.minimal_roi, {"0": 100.0})
        self.assertEqual(Strat.stoploss, -0.03)
        self.assertGreaterEqual(Strat.startup_candle_count, 1200)

    def test_signals_binary_and_timed(self) -> None:
        f = run(make_frame(24 * 7 * 20))
        for col in ("enter_long", "exit_long"):
            self.assertTrue(set(f[col].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(int(f["enter_long"].fillna(0).sum()), 0)
        self.assertGreater(int(f["exit_long"].fillna(0).sum()), 0)
        e = f[f["enter_long"] == 1]
        self.assertTrue(((e["weekday_utc"] == 6) & (e["hour_utc"] == 23)).all())
        x = f[f["exit_long"] == 1]
        self.assertTrue(((x["weekday_utc"] == 0) & (x["hour_utc"] == 23)).all())

    def test_zero_volume_no_signal(self) -> None:
        f = run(make_frame(24 * 7 * 20, volume=0.0))
        self.assertEqual(int(f["enter_long"].fillna(0).sum()) if "enter_long" in f else 0, 0)
        self.assertEqual(int(f["exit_long"].fillna(0).sum()) if "exit_long" in f else 0, 0)

    def test_nan_startup_no_entry(self) -> None:
        # fewer than 50 daily closes -> SMA undefined -> no entry
        f = run(make_frame(24 * 49))
        self.assertEqual(int(f["enter_long"].fillna(0).sum()) if "enter_long" in f else 0, 0)

    def test_no_lookahead(self) -> None:
        full = make_frame(24 * 7 * 20 + 5)
        n = 24 * 7 * 15 + 7
        a = run(full.iloc[:n].copy().reset_index(drop=True))
        b = run(full.copy())
        cols = ["daily_sma", "enter_long", "exit_long"]
        # compare only rows whose day is complete in the short frame
        m = n - (n % 24)
        pd.testing.assert_frame_equal(
            a.loc[: m - 1, cols], b.loc[: m - 1, cols], check_dtype=False
        )


if __name__ == "__main__":
    unittest.main()
