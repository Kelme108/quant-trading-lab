import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

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

ROOT = Path(__file__).parents[2]


def load_strategy(filename, class_name):
    path = ROOT / "user_data" / "strategies" / "_archive" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


S = load_strategy("WeeklyBreakoutRegime_H089_v1.py", "WeeklyBreakoutRegime_H089_v1")


class FakeTrade:
    def __init__(self, open_date_utc):
        self.open_date_utc = open_date_utc


def make_frame(n, volume=1.0):
    # steady uptrend with a pullback pattern so breakouts and exits occur
    prices = [100.0 + 0.3 * i + (3.0 if i % 20 > 14 else 0.0) for i in range(n)]
    dates = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
    return pd.DataFrame(
        {
            "date": dates,
            "open": prices,
            "high": [p * 1.002 for p in prices],
            "low": [p * 0.998 for p in prices],
            "close": prices,
            "volume": [volume] * n,
        }
    )


def run(strategy, frame):
    frame = strategy.populate_indicators(frame, {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


class H089Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(S.INTERFACE_VERSION, 3)
        self.assertEqual(S.timeframe, "1h")
        self.assertFalse(S.can_short)
        self.assertEqual(S.minimal_roi, {"0": 100.0})
        self.assertEqual(S.stoploss, -0.02)
        self.assertGreaterEqual(S.startup_candle_count, 180)
        self.assertEqual(S().protections[0]["stop_duration_candles"], 2)

    def test_binary_and_hour_window(self):
        frame = run(S(), make_frame(400))
        for col in ("enter_long", "exit_long"):
            self.assertTrue(set(frame[col].dropna().unique().tolist()).issubset({1}))
        entries = frame[frame["enter_long"] == 1]
        self.assertGreater(len(entries), 0)
        self.assertTrue((entries["date"].dt.hour <= 15).all())

    def test_zero_volume_no_signal(self):
        frame = run(S(), make_frame(400, volume=0.0))
        self.assertEqual(int(frame.get("enter_long", pd.Series()).fillna(0).sum()), 0)
        self.assertEqual(int(frame.get("exit_long", pd.Series()).fillna(0).sum()), 0)

    def test_startup_nan_no_signal(self):
        frame = run(S(), make_frame(400))
        self.assertEqual(int(frame.iloc[:179]["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame.iloc[:179]["exit_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self):
        n = 300
        a = run(S(), make_frame(n))
        b = run(S(), make_frame(n + 50).iloc[:n + 50].copy())
        for col in ("enter_long", "exit_long", "sma_fast", "sma_slow", "entry_high", "exit_low"):
            pd.testing.assert_series_equal(
                a[col].iloc[:n].reset_index(drop=True),
                b[col].iloc[:n].reset_index(drop=True),
                check_dtype=False,
                check_names=False,
            )

    def test_time_exits(self):
        s = S()
        t0 = datetime(2024, 1, 1, 5, tzinfo=timezone.utc)
        trade = FakeTrade(t0)
        self.assertIsNone(s.custom_exit("X", trade, t0 + timedelta(hours=5), 1, 0.0))
        self.assertEqual(
            s.custom_exit("X", trade, t0 + timedelta(hours=12), 1, 0.0), "time_12h"
        )
        self.assertEqual(
            s.custom_exit("X", trade, t0.replace(hour=23), 1, 0.0), "time_2300"
        )


if __name__ == "__main__":
    unittest.main()
