import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

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
    return getattr(module, class_name)


Strategy = load_strategy("TimeSeriesMomentum_H099_v1.py", "TimeSeriesMomentum_H099_v1")


def make_frame(prices, start="2025-01-01 00:00", volume=1.0) -> pd.DataFrame:
    n = len(prices)
    return pd.DataFrame(
        {
            "date": pd.date_range(start, periods=n, freq="1h", tz="UTC"),
            "open": prices,
            "high": [p * 1.01 for p in prices],
            "low": [p * 0.99 for p in prices],
            "close": prices,
            "volume": [volume] * n,
        }
    )


def run(strategy, frame):
    frame = strategy.populate_indicators(frame, {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


def col(frame, name):
    if name in frame:
        return frame[name].fillna(0)
    return pd.Series(0, index=frame.index)


class FakeTrade:
    def __init__(self, open_date):
        self.open_date_utc = open_date


class TimeSeriesMomentumH099Tests(unittest.TestCase):
    def setUp(self):
        self.strategy = Strategy()

    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.02)
        self.assertGreaterEqual(Strategy.startup_candle_count, 61)
        self.assertEqual(
            self.strategy.protections,
            [{"method": "CooldownPeriod", "stop_duration_candles": 2}],
        )

    def test_signals_binary(self):
        prices = [100.0 + (i % 13) + 0.1 * i for i in range(300)]
        frame = run(self.strategy, make_frame(prices))
        for column in ("enter_long", "exit_long"):
            self.assertIn(column, frame)
            self.assertTrue(set(frame[column].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_no_signal(self):
        prices = [100.0 + (i % 13) + 0.1 * i for i in range(300)]
        frame = run(self.strategy, make_frame(prices, volume=0.0))
        self.assertEqual(int(col(frame, "enter_long").sum()), 0)
        self.assertEqual(int(col(frame, "exit_long").sum()), 0)

    def test_nan_startup_no_signal(self):
        prices = [100.0 + i for i in range(260)]
        frame = run(self.strategy, make_frame(prices))
        self.assertEqual(int(col(frame, "enter_long").iloc[:60].sum()), 0)
        self.assertEqual(int(col(frame, "exit_long").iloc[:60].sum()), 0)

    def test_entry_rule_and_session_window(self):
        prices = [100.0 + i for i in range(200)]  # always rising
        frame = run(self.strategy, make_frame(prices))
        entries = col(frame, "enter_long") == 1
        hours = frame["date"].dt.hour
        valid_rows = frame.index >= 60
        expected_hours = (hours == 23) | (hours <= 15)
        self.assertTrue(entries[valid_rows].equals(expected_hours[valid_rows]))
        self.assertFalse(entries.iloc[:60].any())
        # hours 16..22 never signal
        self.assertFalse(entries[(hours >= 16) & (hours <= 22)].any())

    def test_entry_requires_rising_bar_and_positive_momentum(self):
        prices = [100.0 + i for i in range(100)]
        prices[80] = prices[79] - 1.0  # falling bar, still above close[t-60]
        frame = run(self.strategy, make_frame(prices))
        self.assertEqual(col(frame, "enter_long").iloc[80], 0)
        # falling market: momentum negative -> no entry, momentum exit
        down = [300.0 - i for i in range(120)]
        frame = run(self.strategy, make_frame(down))
        self.assertEqual(int(col(frame, "enter_long").sum()), 0)
        self.assertTrue((col(frame, "exit_long").iloc[60:] == 1).all())

    def test_evening_exit_signal_on_2200_bar(self):
        prices = [100.0 + i for i in range(200)]
        frame = run(self.strategy, make_frame(prices))
        hours = frame["date"].dt.hour
        exits = col(frame, "exit_long") == 1
        self.assertTrue(exits[(hours == 22) & (frame.index >= 60)].all())
        self.assertFalse(exits[hours != 22].any())

    def test_momentum_exit(self):
        prices = [100.0 + i for i in range(100)]
        prices[90] = prices[30] - 5.0
        frame = run(self.strategy, make_frame(prices))
        self.assertEqual(col(frame, "exit_long").iloc[90], 1)
        self.assertEqual(col(frame, "enter_long").iloc[90], 0)

    def test_no_lookahead(self):
        rng = np.random.default_rng(7)
        prices = list(100.0 + np.cumsum(rng.normal(0, 1.0, 400)))
        long_frame = make_frame(prices)
        n = 250
        short = run(self.strategy, long_frame.iloc[:n].copy())
        full = run(self.strategy, long_frame.copy())
        for column in ("enter_long", "exit_long"):
            a = col(short, column).iloc[:n].reset_index(drop=True)
            b = col(full, column).iloc[:n].reset_index(drop=True)
            pd.testing.assert_series_equal(a, b, check_dtype=False)

    def test_time_exit_after_12_bars(self):
        opened = datetime(2025, 1, 1, 2, 0, tzinfo=timezone.utc)
        trade = FakeTrade(opened)
        self.assertIsNone(
            self.strategy.custom_exit("X/USDT", trade, opened + timedelta(hours=11), 1.0, 0.01)
        )
        self.assertEqual(
            self.strategy.custom_exit("X/USDT", trade, opened + timedelta(hours=12), 1.0, 0.01),
            "time_exit_12h",
        )

    def test_evening_exit_in_custom_exit(self):
        opened = datetime(2025, 1, 1, 15, 0, tzinfo=timezone.utc)
        trade = FakeTrade(opened)
        self.assertIsNone(
            self.strategy.custom_exit(
                "X/USDT", trade, datetime(2025, 1, 1, 22, 0, tzinfo=timezone.utc), 1.0, 0.0
            )
        )
        self.assertEqual(
            self.strategy.custom_exit(
                "X/USDT", trade, datetime(2025, 1, 1, 23, 0, tzinfo=timezone.utc), 1.0, 0.0
            ),
            "evening_exit_2300",
        )

    def test_no_take_profit(self):
        opened = datetime(2025, 1, 1, 2, 0, tzinfo=timezone.utc)
        trade = FakeTrade(opened)
        self.assertIsNone(
            self.strategy.custom_exit(
                "X/USDT", trade, opened + timedelta(hours=3), 1.5, 0.5
            )
        )

    def test_day_cap_in_confirm_trade_entry(self):
        day = datetime(2025, 1, 2, 0, 0, tzinfo=timezone.utc)
        persistence = types.ModuleType("freqtrade.persistence")

        def check(existing, now):
            persistence.Trade = types.SimpleNamespace(
                get_trades_proxy=lambda **kw: [FakeTrade(t) for t in existing]
            )
            with mock.patch.dict(sys.modules, {"freqtrade.persistence": persistence}):
                return self.strategy.confirm_trade_entry(
                    "X/USDT", "limit", 1.0, 1.0, "GTC", now, None, "long"
                )

        now = day + timedelta(hours=10)
        prior = day - timedelta(hours=1)
        self.assertTrue(check([], now))
        self.assertTrue(check([day + timedelta(hours=2)], now))
        self.assertTrue(check([prior, prior], now))
        self.assertFalse(check([day + timedelta(hours=2), day + timedelta(hours=5)], now))
        self.assertFalse(
            check([day + timedelta(hours=2), day + timedelta(hours=5), prior], now)
        )


if __name__ == "__main__":
    unittest.main()
