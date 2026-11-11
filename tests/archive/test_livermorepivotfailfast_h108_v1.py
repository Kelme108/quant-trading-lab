import importlib.util
import sys
import types
import unittest
from datetime import timedelta
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
NAME = "LivermorePivotFailFast_H108_v1"


def load():
    path = ROOT / "user_data" / "strategies" / "_archive" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


Strategy = getattr(load(), NAME)
START = pd.Timestamp("2024-01-01 00:00", tz="UTC")


def synthetic(n: int) -> pd.DataFrame:
    """Gentle up-drift with periodic jumps and volume bursts so entries occur."""
    idx = np.arange(n)
    close = 100.0 + 0.05 * idx + 0.3 * np.sin(idx / 5.0)
    close = close + 3.0 * (idx // 37)  # step up every 37 bars
    volume = np.full(n, 10.0)
    volume[idx % 37 == 0] = 60.0
    return pd.DataFrame(
        {
            "date": [START + timedelta(hours=int(i)) for i in idx],
            "open": np.concatenate([[close[0]], close[:-1]]),
            "high": close + 0.2,
            "low": close - 0.2,
            "close": close,
            "volume": volume,
        }
    )


def run(strategy, frame):
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    return frame


class FakeDP:
    def __init__(self, frame):
        self.frame = frame

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.frame, None


class FakeTrade:
    def __init__(self, open_date_utc):
        self.open_date_utc = open_date_utc


class LivermoreH108Tests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.02)
        self.assertGreaterEqual(Strategy.startup_candle_count, 100)
        self.assertEqual(
            Strategy().protections,
            [{"method": "CooldownPeriod", "stop_duration_candles": 1}],
        )

    def test_indicators_exclude_current_bar(self):
        frame = synthetic(120)
        out = Strategy().populate_indicators(frame.copy(), {})
        self.assertTrue(pd.isna(out.loc[19, "pivot"]))
        self.assertEqual(out.loc[20, "pivot"], frame.loc[0:19, "high"].max())
        self.assertEqual(out.loc[4, "vol_avg"], frame.loc[0:3, "volume"].mean())
        self.assertTrue(pd.isna(out.loc[3, "vol_avg"]))
        self.assertTrue(pd.isna(out.loc[38, "sma40"]))
        self.assertAlmostEqual(out.loc[39, "sma40"], frame.loc[0:39, "close"].mean())
        self.assertEqual(out.loc[10, "trail_low"], frame.loc[6:9, "low"].min())

    def test_entries_exist_binary_and_in_hour_window(self):
        out = run(Strategy(), synthetic(400))
        entries = out[out["enter_long"] == 1]
        self.assertGreater(len(entries), 0)
        self.assertTrue(set(out["enter_long"].dropna().unique()).issubset({1}))
        self.assertTrue(entries["date"].dt.hour.between(0, 16).all())
        self.assertTrue((entries["volume"] > 0).all())
        if "exit_long" in out:
            self.assertTrue(set(out["exit_long"].dropna().unique()).issubset({1}))

    def test_hour_window_excludes_late_bars(self):
        strategy = Strategy()
        out = run(strategy, synthetic(400))
        late = out["date"].dt.hour > 16
        self.assertEqual(int(out.loc[late, "enter_long"].fillna(0).sum()), 0)

    def test_zero_volume_has_no_signal(self):
        frame = synthetic(300)
        frame["volume"] = 0.0
        out = run(Strategy(), frame)
        self.assertEqual(int(out.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(out.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_zero_volume_on_signal_bar_blocks_entry(self):
        frame = synthetic(400)
        base = run(Strategy(), frame)
        first = int(base.index[base["enter_long"] == 1][0])
        frame.loc[first, "volume"] = 0.0
        out = run(Strategy(), frame)
        self.assertNotEqual(out.loc[first, "enter_long"], 1)

    def test_startup_values_undefined_give_no_signal(self):
        out = run(Strategy(), synthetic(400))
        startup = Strategy.startup_candle_count
        self.assertEqual(int(out.iloc[:40]["enter_long"].fillna(0).sum()), 0)
        self.assertTrue(out.iloc[:39]["sma40"].isna().all())
        self.assertLessEqual(40, startup)

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        n, k = 250, 80
        long_frame = synthetic(n + k)
        short = run(Strategy(), long_frame.iloc[:n].copy().reset_index(drop=True))
        full = run(Strategy(), long_frame.copy())
        pd.testing.assert_series_equal(
            short["enter_long"].reset_index(drop=True),
            full["enter_long"].iloc[:n].reset_index(drop=True),
            check_dtype=False,
            check_names=False,
        )
        cols = ["pivot", "vol_avg", "sma40", "trail_low"]
        pd.testing.assert_frame_equal(
            short[cols], full[cols].iloc[:n], check_dtype=False
        )

    # ---- custom_exit -------------------------------------------------
    def manual_frame(self, n=40):
        return pd.DataFrame(
            {
                "date": [START + timedelta(hours=i) for i in range(n)],
                "close": [100.0] * n,
                "volume": [1.0] * n,
                "pivot": [100.0] * n,
                "trail_low": [95.0] * n,
            }
        )

    def exit_at(self, frame, signal_idx, now_idx):
        strategy = Strategy()
        strategy.dp = FakeDP(frame)
        trade = FakeTrade(frame.loc[signal_idx + 1, "date"])
        return strategy.custom_exit(
            "BTC/USDT", trade, frame.loc[now_idx, "date"], 100.0, 0.0
        )

    def test_no_exit_on_fill_bar_or_when_price_holds(self):
        frame = self.manual_frame()
        self.assertIsNone(self.exit_at(frame, 2, 3))
        self.assertIsNone(self.exit_at(frame, 2, 4))
        self.assertIsNone(self.exit_at(frame, 2, 8))

    def test_fail_fast_in_first_two_bars_only(self):
        frame = self.manual_frame()
        frame.loc[3, "close"] = 99.0  # bar t+1 closes under the pivot
        self.assertEqual(self.exit_at(frame, 2, 4), "fail_fast_pivot")
        frame = self.manual_frame()
        frame.loc[4, "close"] = 99.0  # bar t+2
        self.assertIsNone(self.exit_at(frame, 2, 4))
        self.assertEqual(self.exit_at(frame, 2, 5), "fail_fast_pivot")
        # bar t+3 closing under the pivot but above the 4-bar low: no exit
        frame = self.manual_frame()
        frame.loc[5, "close"] = 99.0
        self.assertIsNone(self.exit_at(frame, 2, 6))

    def test_fail_fast_uses_the_pivot_of_the_signal_bar(self):
        frame = self.manual_frame()
        frame.loc[2, "pivot"] = 98.0
        frame.loc[3, "pivot"] = 100.0  # later pivot must not matter
        frame.loc[3, "close"] = 99.0
        self.assertIsNone(self.exit_at(frame, 2, 4))

    def test_trailing_exit_from_bar_t_plus_3(self):
        frame = self.manual_frame()
        frame.loc[5, "close"] = 94.0  # t+3 under the 4-bar low
        self.assertEqual(self.exit_at(frame, 2, 6), "trail_4_low")
        frame = self.manual_frame()
        frame.loc[4, "close"] = 94.0  # t+2: trailing not yet active, fail-fast fires
        self.assertEqual(self.exit_at(frame, 2, 5), "fail_fast_pivot")

    def test_zero_volume_candle_blocks_indicator_exit(self):
        frame = self.manual_frame()
        frame.loc[5, "close"] = 94.0
        frame.loc[5, "volume"] = 0.0
        self.assertIsNone(self.exit_at(frame, 2, 6))

    def test_max_hold_twelve_hours_after_fill(self):
        frame = self.manual_frame()
        # signal 02:00, fill 03:00 -> sold at 15:00 open
        self.assertIsNone(self.exit_at(frame, 2, 14))
        self.assertEqual(self.exit_at(frame, 2, 15), "max_hold_12h")

    def test_session_flat_at_2300_open(self):
        frame = self.manual_frame()
        # signal 14:00, fill 15:00 -> still open at 22:00 open, sold at 23:00 open
        self.assertIsNone(self.exit_at(frame, 14, 22))
        self.assertEqual(self.exit_at(frame, 14, 23), "session_flat_2300")


if __name__ == "__main__":
    unittest.main()
