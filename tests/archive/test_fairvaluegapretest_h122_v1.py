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

ROOT = Path(__file__).parents[2]


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / "_archive" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Strategy = load_strategy("FairValueGapRetest_H122_v1.py", "FairValueGapRetest_H122_v1")

WINTER = "2024-01-15 00:00"  # NY = UTC-5: 10:00 NY = 15:00 UTC
SUMMER = "2024-07-15 00:00"  # NY = UTC-4: 10:00 NY = 14:00 UTC


class Trade:
    def __init__(self, open_rate, tag, open_date):
        self.open_rate = open_rate
        self.enter_tag = tag
        self.open_date_utc = open_date


def make_frame(start: str, n: int, p: int | None) -> pd.DataFrame:
    """Flat 15m series; if p is given, a sweep/gap/retest pattern on window bars p..p+3.

    Bar p: sweep (low 99.0), bar p+1: up bar on 4x volume, bar p+2: gap above high(p),
    bar p+3: retest into the gap. S = 99.0, GB = 100.2, GT = 100.6.
    """
    dates = pd.date_range(start, periods=n, freq="15min", tz="UTC")
    frame = pd.DataFrame(
        {
            "date": dates,
            "open": 100.0,
            "high": 100.2,
            "low": 99.8,
            "close": 100.0,
            "volume": 10.0,
        }
    )
    if p is not None:
        frame.loc[p, ["open", "high", "low", "close"]] = [100.0, 100.2, 99.0, 100.0]
        frame.loc[p + 1, ["open", "high", "low", "close", "volume"]] = [100.0, 101.5, 100.0, 101.0, 40.0]
        frame.loc[p + 2, ["open", "high", "low", "close"]] = [101.0, 102.0, 100.6, 101.5]
        frame.loc[p + 3, ["open", "high", "low", "close"]] = [101.5, 101.6, 100.5, 101.0]
    return frame


def run(frame: pd.DataFrame) -> pd.DataFrame:
    strategy = Strategy()
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


def entries(frame: pd.DataFrame) -> list[int]:
    if "enter_long" not in frame:
        return []
    return frame.index[frame["enter_long"].fillna(0) == 1].tolist()


class FairValueGapRetestH122Tests(unittest.TestCase):
    def test_class_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 100)

    def test_signal_on_retest_bar_winter(self) -> None:
        frame = run(make_frame(WINTER, 200, 60))
        self.assertEqual(entries(frame), [63])
        self.assertEqual(frame.loc[63, "enter_tag"], "fvg_retest|99.0")

    def test_signal_follows_new_york_dst(self) -> None:
        # July: the 10:00 NY window opens at 14:00 UTC = bar 56.
        self.assertEqual(entries(run(make_frame(SUMMER, 200, 56))), [59])
        # The winter offset on a summer date is 11:00 NY: not a window.
        self.assertEqual(entries(run(make_frame(SUMMER, 200, 60))), [])

    def test_signal_columns_are_binary(self) -> None:
        frame = run(make_frame(WINTER, 200, 60))
        for column in ("enter_long", "exit_long"):
            if column in frame:
                self.assertTrue(set(frame[column].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_candle_gives_no_signal(self) -> None:
        source = make_frame(WINTER, 200, 60)
        source.loc[63, "volume"] = 0.0
        self.assertEqual(entries(run(source)), [])
        all_zero = make_frame(WINTER, 200, 60)
        all_zero["volume"] = 0.0
        frame = run(all_zero)
        self.assertEqual(entries(frame), [])
        self.assertEqual(int(frame.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_undefined_startup_values_give_no_signal(self) -> None:
        # Start 03:45 UTC: window W1 (08:00 UTC) opens at bar 17, so the gap bar k=18 has no 20-bar volume mean.
        frame = run(make_frame("2024-01-15 03:45", 200, 17))
        self.assertEqual(entries(frame), [])
        # Start 06:00 UTC: window opens at bar 8, the 16-bar pool is not available.
        frame = run(make_frame("2024-01-15 06:00", 200, 8))
        self.assertEqual(entries(frame), [])
        startup = Strategy.startup_candle_count
        self.assertEqual(int(frame.iloc[:startup].get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_pattern_rules_are_enforced(self) -> None:
        # Gap too small (< 0.25%): low(k+1) = 100.3 -> (100.3-100.2)/101.5 = 0.1%
        source = make_frame(WINTER, 200, 60)
        source.loc[62, "low"] = 100.3
        self.assertEqual(entries(run(source)), [])
        # Volume on bar k below 1.5x the 20-bar mean.
        source = make_frame(WINTER, 200, 60)
        source.loc[61, "volume"] = 14.0
        self.assertEqual(entries(run(source)), [])
        # Retest bar breaks S: cancelled.
        source = make_frame(WINTER, 200, 60)
        source.loc[63, "low"] = 98.9
        self.assertEqual(entries(run(source)), [])
        # Retest bar closes below GB: cancelled.
        source = make_frame(WINTER, 200, 60)
        source.loc[63, "close"] = 100.1
        self.assertEqual(entries(run(source)), [])
        # No sweep: the pool low is not undercut.
        source = make_frame(WINTER, 200, 60)
        source.loc[60, "low"] = 99.8
        self.assertEqual(entries(run(source)), [])

    def test_retest_may_come_after_the_window(self) -> None:
        source = make_frame(WINTER, 200, 60)
        source.loc[63, ["open", "high", "low", "close"]] = [101.5, 102.5, 101.4, 102.0]  # no touch of GT
        source.loc[64, ["open", "high", "low", "close"]] = [102.0, 102.1, 100.5, 101.0]
        self.assertEqual(entries(run(source)), [64])
        # No retest within 8 bars after k+1 (bars 64..71 stay above GT): expired.
        for index in range(64, 72):
            source.loc[index, ["open", "high", "low", "close"]] = [102.0, 102.5, 101.4, 102.0]
        source.loc[72, ["open", "high", "low", "close"]] = [102.0, 102.1, 100.5, 101.0]
        self.assertEqual(entries(run(source)), [])

    def test_missing_window_bar_gives_no_trade(self) -> None:
        source = make_frame(WINTER, 200, 60).drop(index=[62]).reset_index(drop=True)
        self.assertEqual(entries(run(source)), [])

    def test_signal_does_not_change_when_future_candles_are_appended(self) -> None:
        source = make_frame(WINTER, 400, 60)
        # a second pattern a day later (same NY window, +96 bars)
        later = make_frame(WINTER, 400, 156)
        source.loc[156:159, ["open", "high", "low", "close", "volume"]] = later.loc[
            156:159, ["open", "high", "low", "close", "volume"]
        ].to_numpy()
        full = run(source)
        self.assertEqual(entries(full), [63, 159])
        compared = ["fvg_signal", "fvg_setup_low", "enter_long", "enter_tag"]
        for n in (58, 61, 62, 63, 64, 80, 120, 157, 159, 160, 250):
            head = run(source.iloc[:n].copy())
            for column in compared:
                left = head.reindex(columns=[column])[column].iloc[:n].reset_index(drop=True)
                right = full.reindex(columns=[column])[column].iloc[:n].reset_index(drop=True)
                pd.testing.assert_series_equal(left, right, check_dtype=False, check_names=False)

    def test_changing_future_candles_does_not_change_past_rows(self) -> None:
        source = make_frame(WINTER, 300, 60)
        changed = source.copy()
        changed.loc[200:, ["open", "high", "low", "close"]] = [500.0, 600.0, 400.0, 550.0]
        a = run(source)
        b = run(changed)
        for column in ("fvg_signal", "fvg_setup_low", "enter_long", "enter_tag"):
            pd.testing.assert_series_equal(
                a.reindex(columns=[column])[column].iloc[:200].reset_index(drop=True),
                b.reindex(columns=[column])[column].iloc[:200].reset_index(drop=True),
                check_dtype=False,
            )

    def test_stop_is_absolute_price_min_of_s_and_one_percent(self) -> None:
        strategy = Strategy()
        opened = datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc)
        # E = 101.5, S = 99.0 -> stop 99.0 (2.46% below E)
        trade = Trade(101.5, "fvg_retest|99.0", opened)
        now = opened + timedelta(hours=1)
        self.assertAlmostEqual(strategy.custom_stoploss("X", trade, now, 101.5, 0.0), 99.0 / 101.5 - 1.0)
        # The stop does not move with the price (no trailing).
        self.assertAlmostEqual(strategy.custom_stoploss("X", trade, now, 103.0, 0.015), 99.0 / 103.0 - 1.0)
        # S above 0.99 x E -> stop 0.99 x E (distance exactly 1%).
        trade = Trade(100.0, "fvg_retest|99.7", opened)
        self.assertAlmostEqual(strategy.custom_stoploss("X", trade, now, 100.0, 0.0), -0.01)
        # Foreign tag: leave the native stop alone.
        self.assertIsNone(strategy.custom_stoploss("X", Trade(100.0, "other", opened), now, 100.0, 0.0))

    def test_take_profit_at_two_r(self) -> None:
        strategy = Strategy()
        opened = datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc)
        now = opened + timedelta(hours=1)
        trade = Trade(100.0, "fvg_retest|98.0", opened)  # d = 2%, target 104
        self.assertIsNone(strategy.custom_exit("X", trade, now, 103.9, 0.039))
        self.assertEqual(strategy.custom_exit("X", trade, now, 104.0, 0.04), "take_profit_2R")
        # Minimum stop distance 1% -> target 102.
        trade = Trade(100.0, "fvg_retest|99.9", opened)
        self.assertIsNone(strategy.custom_exit("X", trade, now, 101.9, 0.019))
        self.assertEqual(strategy.custom_exit("X", trade, now, 102.0, 0.02), "take_profit_2R")

    def test_time_exit_after_eight_hours(self) -> None:
        strategy = Strategy()
        opened = datetime(2024, 1, 15, 15, 0, tzinfo=timezone.utc)
        trade = Trade(100.0, "fvg_retest|98.0", opened)
        before = opened + timedelta(hours=7, minutes=45)
        self.assertIsNone(strategy.custom_exit("X", trade, before, 100.5, 0.005))
        self.assertEqual(
            strategy.custom_exit("X", trade, opened + timedelta(hours=8), 100.5, 0.005), "time_exit_8h"
        )


if __name__ == "__main__":
    unittest.main()
