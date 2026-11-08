import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
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
PATH = ROOT / "user_data" / "strategies" / "_archive" / "HourlyTenDayExtreme_H082_v1.py"
spec = importlib.util.spec_from_file_location("HourlyTenDayExtreme_H082_v1", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Strategy = module.HourlyTenDayExtreme_H082_v1

META = {"pair": "BTC/USDT"}


def make_frame(prices):
    prices = list(prices)
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=len(prices), freq="1h", tz="UTC"),
            "open": prices,
            "high": [p * 1.01 for p in prices],
            "low": [p * 0.99 for p in prices],
            "close": prices,
            "volume": [1.0] * len(prices),
        }
    )


def random_walk(n, seed=7):
    rng = np.random.default_rng(seed)
    return 100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))


def run(frame):
    s = Strategy()
    f = s.populate_indicators(frame.copy(), META)
    f = s.populate_entry_trend(f, META)
    f = s.populate_exit_trend(f, META)
    return f


def signal_sum(frame, column):
    if column not in frame:
        return 0
    return int(frame[column].fillna(0).sum())


class HourlyTenDayExtremeTests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.99)
        self.assertGreaterEqual(Strategy.startup_candle_count, 240)

    def test_channel_excludes_current_bar(self):
        prices = list(range(100, 400))
        f = run(make_frame(prices))
        self.assertTrue(pd.isna(f.loc[239, "max240"]))
        self.assertEqual(f.loc[240, "max240"], max(prices[0:240]))
        self.assertEqual(f.loc[240, "min240"], min(prices[0:240]))
        self.assertEqual(f.loc[240, "enter_long"], 1)

    def test_both_extremes_trigger(self):
        prices = [100.0 + (i % 5) for i in range(300)]
        prices[260] = 200.0
        prices[280] = 50.0
        f = run(make_frame(prices))
        self.assertEqual(f.loc[260, "enter_long"], 1)
        self.assertEqual(f.loc[260, "enter_tag"], "at_max240")
        self.assertEqual(f.loc[280, "enter_long"], 1)
        self.assertEqual(f.loc[280, "enter_tag"], "at_min240")
        self.assertEqual(signal_sum(f, "enter_long"), 2)

    def test_signals_binary(self):
        f = run(make_frame(random_walk(1200)))
        self.assertGreater(signal_sum(f, "enter_long"), 0)
        for col in ("enter_long", "exit_long"):
            if col in f:
                self.assertTrue(set(f[col].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_no_signal(self):
        frame = make_frame(random_walk(1200))
        frame["volume"] = 0.0
        f = run(frame)
        self.assertEqual(signal_sum(f, "enter_long"), 0)
        self.assertEqual(signal_sum(f, "exit_long"), 0)

    def test_nan_startup_no_signal(self):
        f = run(make_frame([100.0 + i for i in range(400)]))
        self.assertEqual(signal_sum(f.iloc[:240], "enter_long"), 0)

    def test_no_lookahead(self):
        prices = random_walk(1500)
        n = 1000
        short = run(make_frame(prices[:n]))
        full = run(make_frame(prices))
        cols = ["max240", "min240", "enter_long"]
        pd.testing.assert_frame_equal(
            short.loc[: n - 1, cols].reset_index(drop=True),
            full.loc[: n - 1, cols].reset_index(drop=True),
            check_dtype=False,
        )

    def test_time_exit_after_24h(self):
        s = Strategy()
        opened = datetime(2024, 1, 1, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_date_utc=opened)
        self.assertIsNone(s.custom_exit("BTC/USDT", trade, opened + timedelta(hours=23), 1.0, 0.0))
        self.assertEqual(
            s.custom_exit("BTC/USDT", trade, opened + timedelta(hours=24), 1.0, 0.0), "time_24h"
        )


if __name__ == "__main__":
    unittest.main()
