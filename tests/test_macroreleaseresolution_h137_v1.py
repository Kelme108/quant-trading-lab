import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# Keep the tests runnable without installing Freqtrade or TA-Lib on the host.
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


Strategy = load_strategy("MacroReleaseResolution_H137_v1.py", "MacroReleaseResolution_H137_v1")


class FakeTrade:
    def __init__(self, open_rate, enter_tag, open_date_utc):
        self.open_rate = open_rate
        self.enter_tag = enter_tag
        self.open_date_utc = open_date_utc


def make_frame(start, days, spike_day, spike_hour_utc, spike_minute=30, closes=(100.5, 100.6, 101.5, 102.0)):
    """Flat 100 market with range 0.4 per bar; release bar on spike_day (UTC date string)."""
    index = pd.date_range(start, periods=days * 96, freq="15min", tz="UTC")
    n = len(index)
    frame = pd.DataFrame(
        {
            "date": index,
            "open": 100.0,
            "high": 100.2,
            "low": 99.8,
            "close": 100.0,
            "volume": 1.0,
        }
    )
    spike = pd.Timestamp(f"{spike_day} {spike_hour_utc:02d}:{spike_minute:02d}", tz="UTC")
    i = int(frame.index[frame["date"] == spike][0])
    frame.loc[i, ["high", "low", "close"]] = [101.0, 99.0, 100.0]  # range 2.0 = 5x baseline, 2% of open
    for offset, close in enumerate(closes, start=1):
        frame.loc[i + offset, ["open", "high", "low", "close"]] = [100.0, max(close, 100.0) + 0.1, 99.9, close]
    return frame, i


def run(frame):
    strategy = Strategy()
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    if "enter_long" not in frame:  # strategy sets the column only when a signal exists
        frame["enter_long"] = np.nan
    return frame


class MacroReleaseResolutionTests(unittest.TestCase):
    def winter(self, **kwargs):
        return make_frame("2024-01-01", 50, "2024-02-14", 13, **kwargs)

    def summer(self, **kwargs):
        return make_frame("2024-05-20", 60, "2024-07-10", 12, **kwargs)

    def test_class_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.20)
        self.assertGreaterEqual(Strategy.startup_candle_count, 3000)

    def test_winter_signal_on_first_close_above_release_high(self) -> None:
        frame, i = self.winter()
        out = run(frame)
        # bars: i+1 close 100.5 (<101), i+2 100.6, i+3 101.5 (first above 101.0)
        self.assertEqual(out["enter_long"].fillna(0).sum(), 1)
        self.assertEqual(out.loc[i + 3, "enter_long"], 1)
        self.assertEqual(out.loc[i + 3, "enter_tag"], "mrr:99.0")

    def test_summer_dst_clock(self) -> None:
        frame, i = self.summer()
        out = run(frame)
        self.assertEqual(out.loc[i + 3, "enter_long"], 1)
        # the winter UTC slot (13:30) in summer is NY 09:30 and must not act as a release bar
        frame2, _ = make_frame("2024-05-20", 60, "2024-07-10", 13)
        self.assertEqual(run(frame2)["enter_long"].fillna(0).sum(), 0)

    def test_only_first_close_above_counts(self) -> None:
        frame, i = self.winter(closes=(101.5, 102.0, 103.0, 104.0))
        out = run(frame)
        self.assertEqual(out["enter_long"].fillna(0).sum(), 1)
        self.assertEqual(out.loc[i + 1, "enter_long"], 1)

    def test_no_signal_after_window(self) -> None:
        # first close above high(E) at bar 9 (outside the 8-bar window)
        frame, i = self.winter(closes=(100.5,) * 8 + (101.5,))
        self.assertEqual(run(frame)["enter_long"].fillna(0).sum(), 0)
        frame, i = self.winter(closes=(100.5,) * 7 + (101.5,))
        self.assertEqual(run(frame).loc[i + 8, "enter_long"], 1)

    def test_no_event_when_range_too_small(self) -> None:
        frame, i = self.winter()
        frame.loc[i, ["high", "low"]] = [100.6, 99.8]  # range 0.8 = 2x baseline
        frame.loc[i + 3, "close"] = 101.5
        self.assertEqual(run(frame)["enter_long"].fillna(0).sum(), 0)

    def test_no_event_when_range_below_0_8_percent_of_open(self) -> None:
        index = pd.date_range("2024-01-01", periods=50 * 96, freq="15min", tz="UTC")
        frame = pd.DataFrame(
            {"date": index, "open": 100.0, "high": 100.02, "low": 99.98, "close": 100.0, "volume": 1.0}
        )
        i = int(frame.index[frame["date"] == pd.Timestamp("2024-02-14 13:30", tz="UTC")][0])
        frame.loc[i, ["high", "low"]] = [100.4, 99.8]  # 15x baseline but 0.6% of open
        frame.loc[i + 1, "close"] = 101.5
        self.assertEqual(run(frame)["enter_long"].fillna(0).sum(), 0)

    def test_weekend_release_slot_is_ignored(self) -> None:
        # 2024-02-17 is a Saturday
        frame, _ = make_frame("2024-01-01", 50, "2024-02-17", 13)
        self.assertEqual(run(frame)["enter_long"].fillna(0).sum(), 0)

    def test_zero_volume_has_no_signal(self) -> None:
        frame, i = self.winter()
        frame["volume"] = 0.0
        out = run(frame)
        self.assertEqual(int(out.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(out.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        frame, i = self.winter()
        frame.loc[i + 3, "volume"] = 0.0
        self.assertEqual(int(run(frame).get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_undefined_startup_values_give_no_signal(self) -> None:
        # event fires with fewer than 20 earlier release bars available: no signal
        frame, i = make_frame("2024-01-01", 20, "2024-01-19", 13)
        out = run(frame)
        self.assertEqual(int(out.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        # NaN prices in the baseline history do not create signals
        frame, i = self.winter()
        frame.loc[: i - 1, ["high", "low"]] = np.nan
        out = run(frame)
        self.assertEqual(int(out.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_signal_columns_binary(self) -> None:
        frame, _ = self.winter()
        out = run(frame)
        for column in ("enter_long", "exit_long"):
            if column in out:
                self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_signal_does_not_change_when_future_candles_appended(self) -> None:
        frame, i = make_frame("2024-01-01", 90, "2024-02-14", 13)
        # extra spike later in the series
        later = int(frame.index[frame["date"] == pd.Timestamp("2024-03-20 12:30", tz="UTC")][0])
        frame.loc[later, ["high", "low"]] = [102.0, 98.0]
        frame.loc[later + 1, "close"] = 103.0
        n = i + 6
        short = run(frame.iloc[:n].copy())
        long_ = run(frame.copy())
        cols = ["mrr_signal", "mrr_low"]
        pd.testing.assert_frame_equal(short.loc[: n - 1, cols], long_.loc[: n - 1, cols])
        for column in ("enter_long", "enter_tag"):
            a = short[column] if column in short else pd.Series(np.nan, index=short.index)
            b = long_[column].iloc[:n] if column in long_ else pd.Series(np.nan, index=short.index)
            pd.testing.assert_series_equal(a.reset_index(drop=True), b.reset_index(drop=True), check_names=False)
        self.assertEqual(long_.loc[later + 1, "enter_long"], 1)

    def test_stop_distance_and_floor(self) -> None:
        strategy = Strategy()
        opened = datetime(2024, 2, 14, 14, 0, tzinfo=timezone.utc)
        # low(E) 3% below fill -> d = 0.03; stop at 97
        trade = FakeTrade(100.0, "mrr:97.0", opened)
        ratio = strategy.custom_stoploss("X/USDT", trade, opened, 100.0, 0.0)
        self.assertAlmostEqual(ratio, -0.03)
        # price moved up: stop stays at 97 (absolute)
        ratio = strategy.custom_stoploss("X/USDT", trade, opened, 102.0, 0.02)
        self.assertAlmostEqual(102.0 * (1 + ratio), 97.0)
        # low(E) only 0.4% below fill -> floor d = 0.01
        trade = FakeTrade(100.0, "mrr:99.6", opened)
        self.assertAlmostEqual(strategy.custom_stoploss("X/USDT", trade, opened, 100.0, 0.0), -0.01)
        # missing tag -> backstop
        trade = FakeTrade(100.0, "other", opened)
        self.assertIsNone(strategy.custom_stoploss("X/USDT", trade, opened, 100.0, 0.0))

    def test_target_exit(self) -> None:
        strategy = Strategy()
        opened = datetime(2024, 2, 14, 14, 0, tzinfo=timezone.utc)
        trade = FakeTrade(100.0, "mrr:98.0", opened)  # d = 0.02, T = 103
        now = opened + timedelta(hours=1)
        self.assertIsNone(strategy.custom_exit("X/USDT", trade, now, 102.9, 0.029))
        self.assertEqual(strategy.custom_exit("X/USDT", trade, now, 103.0, 0.03), "target_1_5R")
        # floored stop: d = 0.01, T = 101.5
        trade = FakeTrade(100.0, "mrr:99.8", opened)
        self.assertEqual(strategy.custom_exit("X/USDT", trade, now, 101.5, 0.015), "target_1_5R")
        self.assertIsNone(strategy.custom_exit("X/USDT", trade, now, 101.4, 0.014))

    def test_time_exit(self) -> None:
        strategy = Strategy()
        opened = datetime(2024, 2, 14, 14, 0, tzinfo=timezone.utc)
        trade = FakeTrade(100.0, "mrr:98.0", opened)
        before = opened + timedelta(hours=7, minutes=45)
        self.assertIsNone(strategy.custom_exit("X/USDT", trade, before, 100.5, 0.005))
        at = opened + timedelta(hours=8)
        self.assertEqual(strategy.custom_exit("X/USDT", trade, at, 100.5, 0.005), "time_exit_8h")
        self.assertEqual(strategy.custom_exit("X/USDT", trade, at, 90.0, -0.10), "time_exit_8h")


if __name__ == "__main__":
    unittest.main()
