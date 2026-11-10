import importlib.util
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace

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

ROOT = Path(__file__).parents[1]
NAME = "SessionOpeningRangeBreakout_H092_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_strategy()
Strategy = getattr(MODULE, NAME)


def make_frame(days=3, start="2024-01-01", breakout_close=104.0, wide=True):
    """15m bars from a Monday 00:00 UTC. Each day: flat 100, opening range 100..103 (3%)."""
    dates = pd.date_range(start, periods=96 * days, freq="15min", tz="UTC")
    frame = pd.DataFrame(
        {"date": dates, "open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0, "volume": 10.0}
    )
    minute = dates.hour * 60 + dates.minute
    top = 103.0 if wide else 100.8
    frame.loc[minute == 13 * 60 + 30, "high"] = top
    frame.loc[minute == 13 * 60 + 30, "low"] = 100.0
    frame.loc[minute == 13 * 60 + 45, "high"] = 102.0 if wide else 100.7
    frame.loc[minute == 13 * 60 + 45, "low"] = 100.5
    brk = minute == 14 * 60 + 15
    frame.loc[brk, "close"] = breakout_close
    frame.loc[brk, "high"] = breakout_close + 0.1
    return frame


def run(frame):
    s = Strategy()
    frame = s.populate_indicators(frame.copy(), {})
    frame = s.populate_entry_trend(frame, {})
    frame = s.populate_exit_trend(frame, {})
    return frame


def trade(open_rate, tag, open_date):
    return SimpleNamespace(
        open_rate=open_rate, enter_tag=tag, open_date_utc=pd.Timestamp(open_date, tz="UTC")
    )


class OrbH092Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 96)

    def test_single_entry_per_day_with_midpoint_tag(self):
        out = run(make_frame())
        entries = out[out["enter_long"] == 1]
        # Jan 1-3 are Mon-Wed: one entry each at 14:15.
        self.assertEqual(len(entries), 3)
        self.assertTrue(all(d.hour == 14 and d.minute == 15 for d in entries["date"]))
        self.assertEqual(entries["enter_tag"].iloc[0], MODULE.make_tag(101.5))

    def test_binary_signals(self):
        out = run(make_frame())
        for col in ("enter_long", "exit_long"):
            self.assertTrue(set(out[col].dropna().unique().tolist()).issubset({1}))

    def test_narrow_range_not_armed(self):
        out = run(make_frame(wide=False))
        self.assertNotIn("enter_long", out.columns)

    def test_weekend_no_entry(self):
        out = run(make_frame(days=2, start="2024-01-06"))  # Saturday, Sunday
        self.assertNotIn("enter_long", out.columns)

    def test_only_first_breakout_signals(self):
        frame = make_frame(days=1)
        later = pd.to_datetime(frame["date"]).dt.hour * 60 + pd.to_datetime(frame["date"]).dt.minute == 15 * 60
        frame.loc[later, "close"] = 105.0
        out = run(frame)
        self.assertEqual(int(out["enter_long"].sum()), 1)

    def test_no_entry_after_window(self):
        frame = make_frame(days=1, breakout_close=100.0)
        m = frame["date"].dt.hour * 60 + frame["date"].dt.minute
        frame.loc[m == 18 * 60, "close"] = 105.0
        out = run(frame)
        self.assertNotIn("enter_long", out.columns)

    def test_zero_volume_no_signal(self):
        frame = make_frame()
        frame["volume"] = 0.0
        out = run(frame)
        self.assertEqual(int(out.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(out.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_zero_volume_breakout_bar_or_range_bar(self):
        frame = make_frame(days=1)
        m = frame["date"].dt.hour * 60 + frame["date"].dt.minute
        f1 = frame.copy()
        f1.loc[m == 14 * 60 + 15, "volume"] = 0.0
        self.assertNotIn("enter_long", run(f1).columns)
        f2 = frame.copy()
        f2.loc[m == 13 * 60 + 45, "volume"] = 0.0
        self.assertNotIn("enter_long", run(f2).columns)

    def test_missing_range_bar_not_armed(self):
        frame = make_frame(days=1)
        m = frame["date"].dt.hour * 60 + frame["date"].dt.minute
        out = run(frame[m != 13 * 60 + 30].reset_index(drop=True))
        self.assertNotIn("enter_long", out.columns)

    def test_nan_startup_no_signal(self):
        frame = make_frame()
        out = run(frame)
        # Rows before the first opening range is complete (13:45 of day 1) have undefined values.
        early = out.iloc[:56]
        self.assertTrue(early["or_high"].isna().all())
        self.assertEqual(int(early.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        nan_rows = out[out["or_high"].isna()]
        self.assertEqual(int(nan_rows.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_no_lookahead(self):
        full = make_frame(days=4)
        n = 96 * 2 + 62  # cut after the day-3 breakout region
        for cut in (n, 96 * 2 + 55, 96 + 60):
            short = run(full.iloc[:cut].copy())
            long = run(full.copy())
            cols = [c for c in short.columns if c in long.columns]
            pd.testing.assert_frame_equal(
                short[cols].reset_index(drop=True),
                long.iloc[:cut][cols].reset_index(drop=True),
                check_dtype=False,
            )

    def test_exits(self):
        s = Strategy()
        tag = MODULE.make_tag(101.5)
        t = trade(104.0, tag, "2024-01-01 14:30")
        now = pd.Timestamp("2024-01-01 15:00", tz="UTC")
        self.assertIsNone(s.custom_exit("X", t, now, 105.0, 0.01))
        # target = 104 + 2 * 2.5 = 109
        self.assertEqual(s.custom_exit("X", t, now, 109.0, 0.05), "take_profit_2R")
        self.assertEqual(s.custom_exit("X", t, now, 101.5, -0.02), "stop_midpoint")
        self.assertEqual(
            s.custom_exit("X", t, pd.Timestamp("2024-01-01 20:00", tz="UTC"), 105.0, 0.01),
            "time_exit_2000",
        )
        self.assertIsNone(
            s.custom_exit("X", t, pd.Timestamp("2024-01-01 19:45", tz="UTC"), 105.0, 0.01)
        )
        # fill at or below M exits at once
        t2 = trade(101.0, tag, "2024-01-01 14:30")
        self.assertEqual(s.custom_exit("X", t2, now, 101.0, 0.0), "stop_midpoint")

    def test_custom_stoploss_is_midpoint(self):
        s = Strategy()
        t = trade(104.0, MODULE.make_tag(101.5), "2024-01-01 14:30")
        now = pd.Timestamp("2024-01-01 15:00", tz="UTC")
        value = s.custom_stoploss("X", t, now, 104.0, 0.0)
        self.assertAlmostEqual(104.0 * (1 + value), 101.5)
        self.assertEqual(s.custom_stoploss("X", trade(104.0, None, "2024-01-01 14:30"), now, 104.0, 0.0), -0.10)


if __name__ == "__main__":
    unittest.main()
