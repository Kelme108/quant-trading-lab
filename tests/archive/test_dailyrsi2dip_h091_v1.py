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


Strategy = load_strategy("DailyRSI2Dip_H091_v1.py", "DailyRSI2Dip_H091_v1")


def make_frame(prices):
    dates = pd.date_range("2024-01-01 00:00", periods=len(prices), freq="1h", tz="UTC")
    return pd.DataFrame(
        {
            "date": dates,
            "open": prices,
            "high": [p * 1.001 for p in prices],
            "low": [p * 0.999 for p in prices],
            "close": prices,
            "volume": [1.0] * len(prices),
        }
    )


def run(frame):
    s = Strategy()
    frame = s.populate_indicators(frame, {})
    frame = s.populate_entry_trend(frame, {})
    return s.populate_exit_trend(frame, {})


def dip_prices(length=902, dip_at=901):
    prices = [100.0 + 0.1 * i for i in range(length)]
    for i in range(dip_at, length):
        prices[i] = prices[dip_at - 1] * 0.95
    return prices


class Trade:
    def __init__(self, open_date):
        self.open_date_utc = open_date


class DailyRSI2DipTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.02)
        self.assertGreaterEqual(Strategy.startup_candle_count, 800)

    def test_dip_signals_entry_and_binary(self) -> None:
        frame = run(make_frame(dip_prices()))
        self.assertEqual(frame["enter_long"].iloc[-1], 1)
        for col in ("enter_long", "exit_long"):
            self.assertTrue(set(frame[col].dropna().unique().tolist()).issubset({1}))
        # Signals only on odd-hour (block-completing) bars.
        flagged = frame.loc[frame["enter_long"] == 1, "date"].dt.hour
        self.assertTrue((flagged % 2 == 1).all())

    def test_entry_window(self) -> None:
        # Dip completing at hour 17 (fills 18:00) is outside the window.
        frame = run(make_frame(dip_prices(length=905, dip_at=905 - 1)))
        self.assertEqual(frame["date"].iloc[-1].hour, 16)
        # Last bar index 904 is hour 16 (even): no block completes there.
        self.assertTrue(frame["enter_long"].isna().iloc[-1])
        late = run(make_frame(dip_prices(length=907, dip_at=906)))
        self.assertEqual(late["date"].iloc[-1].hour, 18)
        late = run(make_frame(dip_prices(length=906, dip_at=905)))
        self.assertEqual(late["date"].iloc[-1].hour, 17)
        self.assertTrue(late["enter_long"].isna().iloc[-1])

    def test_zero_volume_no_signal(self) -> None:
        frame = make_frame(dip_prices())
        frame["volume"] = 0.0
        frame = run(frame)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(frame.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self) -> None:
        prices = [100.0 + 0.1 * i for i in range(902)]
        for i in range(101, 902):
            prices[i] = prices[100] * 0.95 if i < 110 else prices[i]
        frame = run(make_frame(prices))
        head = frame.iloc[:399]
        self.assertEqual(int(head.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(head.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_no_lookahead(self) -> None:
        prices = dip_prices(length=1000, dip_at=901)
        n = 902
        short = run(make_frame(prices[:n]))
        long = run(make_frame(prices))
        cols = ["close_2h", "rsi2_2h", "sma200_2h", "sma5_2h", "enter_long", "exit_long"]
        pd.testing.assert_frame_equal(
            short.loc[: n - 1, cols].reset_index(drop=True),
            long.loc[: n - 1, cols].reset_index(drop=True),
            check_dtype=False,
        )

    def test_time_and_profit_exits(self) -> None:
        s = Strategy()
        t0 = datetime(2024, 1, 5, 10, 0, tzinfo=timezone.utc)
        trade = Trade(t0)
        self.assertIsNone(s.custom_exit("X", trade, t0 + timedelta(hours=5), 1.0, 0.0))
        self.assertEqual(
            s.custom_exit("X", trade, t0 + timedelta(hours=12), 1.0, 0.0), "time_12h"
        )
        self.assertEqual(
            s.custom_exit(
                "X", trade, datetime(2024, 1, 5, 23, 0, tzinfo=timezone.utc), 1.0, 0.0
            ),
            "time_2300",
        )


if __name__ == "__main__":
    unittest.main()
