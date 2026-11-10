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


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / "_archive" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Strategy = load_strategy("HolyGrailADXPullback_H094_v1.py", "HolyGrailADXPullback_H094_v1")


def make_frame(length: int = 700) -> pd.DataFrame:
    index = np.arange(length)
    close = 100 * np.cumprod(np.full(length, 1.002))
    close = close * (1 + 0.0007 * np.sin(index * 1.3))
    open_ = np.r_[close[0], close[:-1]]
    high = np.maximum(open_, close) * 1.001
    low = np.minimum(open_, close) * 0.999
    wick = index % 15 == 14
    low[wick] = np.minimum(open_, close)[wick] * 0.98
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": 1.0}
    )


def run(strategy, frame):
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


def entries(frame):
    if "enter_long" not in frame:
        return pd.Series(0, index=frame.index)
    return frame["enter_long"].fillna(0)


class FakeTrade:
    def __init__(self, open_date, open_rate):
        self.open_date_utc = open_date
        self.open_rate = open_rate


class FakeDp:
    def __init__(self, frame):
        self.frame = frame

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.frame, None


class HolyGrailTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 500)

    def test_signals_binary_and_present(self) -> None:
        frame = run(Strategy(), make_frame())
        self.assertGreater(int(frame["hg_touch"].sum()), 0)
        self.assertGreater(int(entries(frame).sum()), 0)
        self.assertTrue(set(entries(frame).unique().tolist()).issubset({0, 1}))
        self.assertNotIn("exit_long", frame)

    def test_zero_volume_no_signal(self) -> None:
        base = make_frame()
        self.assertGreater(int(entries(run(Strategy(), base)).sum()), 0)
        base["volume"] = 0.0
        self.assertEqual(int(entries(run(Strategy(), base)).sum()), 0)

    def test_nan_startup_no_signal(self) -> None:
        frame = run(Strategy(), make_frame(300))
        self.assertEqual(int(entries(frame).iloc[:5].sum()), 0)
        self.assertTrue(pd.isna(frame.loc[0, "adx"]))

    def test_no_lookahead(self) -> None:
        full = make_frame(800)
        strategy = Strategy()
        first = run(strategy, full.iloc[:500])
        second = run(strategy, full)
        cols = ["adx", "plus_di", "minus_di", "ema20", "hg_touch"]
        pd.testing.assert_frame_equal(first[cols], second.loc[:499, cols], check_dtype=False)
        pd.testing.assert_series_equal(
            entries(first).reset_index(drop=True),
            entries(second).iloc[:500].reset_index(drop=True),
            check_dtype=False,
            check_names=False,
        )

    def test_daily_cap(self) -> None:
        frame = run(Strategy(), make_frame())
        per_day = entries(frame).groupby(np.arange(len(frame)) // 96).sum()
        self.assertLessEqual(int(per_day.max()), 3)

    def _setup(self):
        strategy = Strategy()
        t0 = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
        frame = pd.DataFrame(
            {
                "date": [t0 - timedelta(minutes=15), t0],
                "setup_ll": [98.0, np.nan],
            }
        )
        strategy.dp = FakeDp(frame)
        return strategy, FakeTrade(t0, 100.0), t0

    def test_stop_is_fixed_price(self) -> None:
        strategy, trade, t0 = self._setup()
        # LL 98 < 0.99*100 = 99 so stop price 98
        self.assertAlmostEqual(strategy.custom_stoploss("X", trade, t0, 100.0, 0.0), -0.02)
        self.assertAlmostEqual(
            strategy.custom_stoploss("X", trade, t0, 101.0, 0.01), 98.0 / 101.0 - 1.0
        )

    def test_take_profit_and_time_exit(self) -> None:
        strategy, trade, t0 = self._setup()
        # d = 2% so TP at +3%
        self.assertIsNone(strategy.custom_exit("X", trade, t0 + timedelta(hours=1), 102.0, 0.02))
        self.assertEqual(
            strategy.custom_exit("X", trade, t0 + timedelta(hours=1), 103.0, 0.03),
            "take_profit_1_5R",
        )
        self.assertIsNone(
            strategy.custom_exit("X", trade, t0 + timedelta(minutes=15 * 31), 100.0, 0.0)
        )
        self.assertEqual(
            strategy.custom_exit("X", trade, t0 + timedelta(minutes=15 * 32), 100.0, 0.0),
            "time_exit_8h",
        )


if __name__ == "__main__":
    unittest.main()
