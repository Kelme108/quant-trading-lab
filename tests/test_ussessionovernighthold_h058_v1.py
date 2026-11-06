import importlib.util
import sys
import types
import unittest
from datetime import datetime, timezone
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


ROOT = Path(__file__).parents[1]
NAME = "USSessionOvernightHold_H058_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, NAME)


Strategy = load_strategy()


def make_frame(prices, start="2024-01-01 00:00"):
    # 2024-01-01 is a Monday.
    dates = pd.date_range(start, periods=len(prices), freq="h", tz="UTC")
    return pd.DataFrame(
        {
            "date": dates,
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
    frame = s.populate_exit_trend(frame, {})
    return frame


def wavy(n):
    return [100.0 + ((i * 7) % 11) - 0.05 * (i % 29) for i in range(n)]


class ContractTests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.03)
        self.assertGreaterEqual(Strategy.startup_candle_count, 24)

    def test_signals_binary(self):
        frame = run(make_frame(wavy(24 * 21)))
        for column in ("enter_long", "exit_long"):
            self.assertIn(column, frame)
            values = set(frame[column].dropna().unique().tolist())
            self.assertTrue(values.issubset({1}))

    def test_entry_and_exit_hours(self):
        # Flat prices: S = 0 < 0.003, so every weekday 19:00 bar signals.
        frame = run(make_frame([100.0] * (24 * 14)))
        entries = frame[frame["enter_long"] == 1]
        self.assertEqual(set(entries["date"].dt.hour), {19})
        self.assertTrue(set(entries["date"].dt.dayofweek).issubset({0, 1, 2, 3, 4}))
        self.assertEqual(len(entries), 10)
        exits = frame[frame["exit_long"] == 1]
        self.assertEqual(set(exits["date"].dt.hour), {12})

    def test_session_threshold(self):
        prices = [100.0] * 48
        frame = make_frame(prices)
        frame.loc[13, "open"] = 100.0
        frame.loc[19, "close"] = 100.31  # S >= 0.003 -> no signal (strict <)
        frame.loc[24 + 13, "open"] = 100.0
        frame.loc[24 + 19, "close"] = 100.29  # S < 0.003 -> signal
        out = run(frame)
        self.assertNotEqual(out.loc[19, "enter_long"], 1)
        self.assertEqual(out.loc[24 + 19, "enter_long"], 1)
        self.assertAlmostEqual(out.loc[24 + 19, "session_ret"], 0.0029, places=9)

    def test_missing_13_bar_no_signal(self):
        frame = make_frame([100.0] * 48).drop(index=24 + 13).reset_index(drop=True)
        out = run(frame)
        day2_19 = out[(out["date"].dt.day == 2) & (out["date"].dt.hour == 19)].index[0]
        self.assertNotEqual(out.loc[day2_19, "enter_long"], 1)

    def test_zero_volume_no_signal(self):
        frame = make_frame([100.0] * (24 * 7))
        frame["volume"] = 0.0
        out = run(frame)
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(out["exit_long"].fillna(0).sum()), 0)

    def test_undefined_startup_no_signal(self):
        # Data starts at 14:00, so the first 19:00 bar has no 13:00 open (undefined S).
        out = run(make_frame([100.0] * 72, start="2024-01-01 14:00"))
        self.assertTrue(pd.isna(out.loc[5, "session_ret"]))
        self.assertEqual(int(out.iloc[: Strategy.startup_candle_count]["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(out[out["session_ret"].isna()]["enter_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self):
        n, k = 24 * 10 + 7, 24 * 5
        prices = wavy(n + k)
        short = run(make_frame(prices[:n]))
        longer = make_frame(prices)
        longer.loc[n:, ["open", "close"]] = 500.0
        longer = run(longer)
        cols = ["session_open", "session_ret", "enter_long", "exit_long"]
        pd.testing.assert_frame_equal(
            short[cols].reset_index(drop=True),
            longer.iloc[:n][cols].reset_index(drop=True),
            check_dtype=False,
        )

    def test_backstop_exit(self):
        s = Strategy()
        trade = types.SimpleNamespace(open_date_utc=datetime(2024, 1, 1, 20, tzinfo=timezone.utc))
        before = datetime(2024, 1, 2, 12, tzinfo=timezone.utc)
        at = datetime(2024, 1, 2, 13, tzinfo=timezone.utc)
        self.assertIsNone(s.custom_exit("BTC/USDT", trade, before, 1.0, 0.0))
        self.assertIsNotNone(s.custom_exit("BTC/USDT", trade, at, 1.0, 0.0))


if __name__ == "__main__":
    unittest.main()
