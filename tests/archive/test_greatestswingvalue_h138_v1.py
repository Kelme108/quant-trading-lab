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


def merge_informative_pair(dataframe, informative, timeframe, timeframe_inf, ffill=True, **kwargs):
    """Stand-in with freqtrade's semantics: a 4h candle is visible from its last 15m bar on."""
    inf = informative.copy()
    minutes_inf = 240
    minutes = 15
    inf["date_merge"] = inf["date"] + timedelta(minutes=minutes_inf) - timedelta(minutes=minutes)
    inf.columns = [f"{c}_{timeframe_inf}" for c in inf.columns]
    merged = pd.merge_asof(
        dataframe.sort_values("date"),
        inf.sort_values(f"date_merge_{timeframe_inf}"),
        left_on="date",
        right_on=f"date_merge_{timeframe_inf}",
        direction="backward",
    )
    return merged.drop(columns=[f"date_merge_{timeframe_inf}"])


# The shared stubs are created with setdefault, so another test module may own the module object.
sys.modules["freqtrade.strategy"].merge_informative_pair = merge_informative_pair

ROOT = Path(__file__).parents[2]
NAME = "GreatestSwingValue_H138_v1"


def load():
    path = ROOT / "user_data" / "strategies" / "_archive" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load()
Strategy = getattr(MODULE, NAME)
START = pd.Timestamp("2025-01-01", tz="UTC")


def dates(n, start=START):
    return pd.date_range(start, periods=n, freq="15min")


def make_frame(n=1800, seed=11, drift=0.0004, sigma=0.004):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(drift, sigma, n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.003, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.003, n))
    volume = rng.lognormal(3, 0.6, n)
    return pd.DataFrame(
        {"date": dates(n), "open": open_, "high": high, "low": low, "close": close, "volume": volume}
    )


def run(strategy, frame):
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


def count(frame, column):
    return int(frame[column].fillna(0).sum()) if column in frame else 0


def session_bars(o, h, l, c, start):
    """One 32-bar session whose candle is open o, high h, low l, close c."""
    rows = {"open": [o] * 32, "high": [o] * 32, "low": [o] * 32, "close": [o] * 32}
    rows["high"][5] = h
    rows["low"][5] = l
    rows["close"][31] = c
    rows["high"][31] = max(o, c)
    rows["low"][31] = min(o, c)
    frame = pd.DataFrame(rows)
    frame["date"] = dates(32, start)
    frame["volume"] = 1.0
    return frame


def crafted(n=10):
    """Indicator frame with one clean entry signal on the last row (offset 10)."""
    session = pd.Timestamp("2025-03-01", tz="UTC")
    frame = pd.DataFrame(
        {
            "date": dates(n, session),
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "volume": 10.0,
            "level_up": 102.0,
            "level_dn": 98.0,
            "gsv_ratio": 0.02,
            "session_offset": np.arange(n, dtype=float),
            "session_start": session,
            "close_4h": 101.0,
            "hsma_4h": 100.0,
        }
    )
    frame.loc[n - 1, "close"] = 102.5
    return frame


class GreatestSwingValueTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.03)
        self.assertGreaterEqual(Strategy.startup_candle_count, 900)
        self.assertFalse(hasattr(MODULE, "LAB_MARKET"))

    def test_signal_columns_are_binary(self):
        out = run(Strategy(), make_frame())
        for column in ("enter_long", "exit_long"):
            if column in out:
                self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_random_series_produces_entries_at_most_once_per_session(self):
        out = run(Strategy(), make_frame())
        self.assertGreater(count(out, "enter_long"), 0)
        per_session = out.loc[out["enter_long"] == 1].groupby("session_start").size()
        self.assertTrue((per_session == 1).all())
        entries = out.loc[out["enter_long"] == 1]
        self.assertTrue((entries["session_offset"] <= 27).all())
        self.assertTrue((entries["close"] > entries["level_up"]).all())
        self.assertTrue((entries["gsv_ratio"] >= 0.008).all())
        self.assertTrue((entries["close_4h"] > entries["hsma_4h"]).all())

    def test_zero_volume_gives_no_signal(self):
        strategy = Strategy()
        frame = crafted()
        frame.loc[len(frame) - 1, "volume"] = 0.0
        self.assertEqual(count(strategy.populate_entry_trend(frame, {}), "enter_long"), 0)
        frame = crafted()
        frame["close"] = 90.0
        frame["volume"] = 0.0
        self.assertEqual(count(strategy.populate_exit_trend(frame, {}), "exit_long"), 0)
        frame = make_frame()
        frame["volume"] = 0.0
        out = run(strategy, frame)
        self.assertEqual(count(out, "enter_long"), 0)
        self.assertEqual(count(out, "exit_long"), 0)

    def test_undefined_values_give_no_signal(self):
        strategy = Strategy()
        for column in ("level_up", "gsv_ratio", "close_4h", "hsma_4h"):
            frame = crafted()
            frame.loc[len(frame) - 1, column] = np.nan
            self.assertEqual(count(strategy.populate_entry_trend(frame, {}), "enter_long"), 0, column)
        frame = crafted()
        frame["close"] = 90.0
        frame["level_dn"] = np.nan
        self.assertEqual(count(strategy.populate_exit_trend(frame, {}), "exit_long"), 0)
        out = run(strategy, make_frame())
        head = out.iloc[: Strategy.startup_candle_count - 100]  # 4h SMA(50) needs 800 bars
        self.assertEqual(count(head, "enter_long"), 0)
        # the 10-session noise average needs 10 completed sessions (320 bars) before it is defined
        self.assertEqual(count(out.iloc[:320], "exit_long"), 0)
        self.assertTrue(out["avg_noise"].iloc[:320].isna().all())

    def test_entry_needs_all_conditions(self):
        strategy = Strategy()
        out = strategy.populate_entry_trend(crafted(), {})
        self.assertEqual(count(out, "enter_long"), 1)
        self.assertEqual(out.loc[9, "enter_long"], 1)
        for column, value in (
            ("close", 102.0),  # not strictly above the level
            ("gsv_ratio", 0.0079),
            ("session_offset", 28.0),
            ("close_4h", 100.0),  # not strictly above the SMA
        ):
            frame = crafted()
            frame.loc[9, column] = value
            self.assertEqual(count(strategy.populate_entry_trend(frame, {}), "enter_long"), 0, column)
        frame = crafted()
        frame.loc[9, "gsv_ratio"] = 0.008  # exactly the minimum passes
        frame.loc[9, "session_offset"] = 27.0  # last allowed offset passes
        self.assertEqual(count(strategy.populate_entry_trend(frame, {}), "enter_long"), 1)

    def test_only_first_signal_of_a_session(self):
        strategy = Strategy()
        frame = crafted()
        frame.loc[7, "close"] = 103.0
        out = strategy.populate_entry_trend(frame, {})
        self.assertEqual(count(out, "enter_long"), 1)
        self.assertEqual(out.loc[7, "enter_long"], 1)
        # a new session may signal again
        frame = crafted()
        frame.loc[7, "close"] = 103.0
        frame.loc[9, "session_start"] = frame.loc[9, "session_start"] + pd.Timedelta(hours=8)
        out = strategy.populate_entry_trend(frame, {})
        self.assertEqual(count(out, "enter_long"), 2)

    def test_gsv_exit_signal(self):
        strategy = Strategy()
        frame = crafted()
        frame.loc[6, "close"] = 97.9
        out = strategy.populate_exit_trend(frame, {})
        self.assertEqual(count(out, "exit_long"), 1)
        self.assertEqual(out.loc[6, "exit_long"], 1)
        frame = crafted()
        frame.loc[6, "close"] = 98.0  # equal to the level is not below it
        self.assertEqual(count(strategy.populate_exit_trend(frame, {}), "exit_long"), 0)

    def test_time_exit_at_session_end(self):
        strategy = Strategy()
        opened = datetime(2025, 1, 1, 10, 15, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_date_utc=opened)
        before = datetime(2025, 1, 1, 15, 45, tzinfo=timezone.utc)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, before, 100.0, 0.0))
        at = datetime(2025, 1, 1, 16, 0, tzinfo=timezone.utc)
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, at, 100.0, 0.0), "time_exit_session_end")
        # a fill at offset 28 (23:00 session 16:00) is flat at midnight
        late = types.SimpleNamespace(open_date_utc=datetime(2025, 1, 1, 23, 0, tzinfo=timezone.utc))
        self.assertIsNone(
            strategy.custom_exit("BTC/USDT", late, datetime(2025, 1, 1, 23, 45, tzinfo=timezone.utc), 100.0, 0.0)
        )
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", late, datetime(2025, 1, 2, 0, 0, tzinfo=timezone.utc), 100.0, 0.0),
            "time_exit_session_end",
        )

    def test_no_take_profit(self):
        strategy = Strategy()
        opened = datetime(2025, 1, 1, 1, 0, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_date_utc=opened)
        now = opened + timedelta(hours=1)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, now, 110.0, 0.10))

    def test_noise_and_levels_on_hand_built_sessions(self):
        # 10 completed sessions: 4 up (noise 1), 4 down (noise 1.5), 2 flat (noise min(1, 3) = 1)
        specs = (
            [(100, 102, 99, 101)] * 4  # up: open - low = 1
            + [(100, 101.5, 98, 99)] * 4  # down: high - open = 1.5
            + [(100, 103, 99, 100)] * 2  # flat: min(1, 3) = 1
        )
        parts = []
        start = START
        for spec in specs + [(100, 100, 100, 100)]:
            parts.append(session_bars(*spec, start))
            start = start + pd.Timedelta(hours=8)
        # session 11 (index 10) has bars with a different open to check O and levels
        frame = pd.concat(parts, ignore_index=True)
        expected = (4 * 1.0 + 4 * 1.5 + 2 * 1.0) / 10
        out = Strategy().populate_indicators(frame, {})
        last = out.iloc[-1]
        self.assertAlmostEqual(float(last["avg_noise"]), expected)
        self.assertAlmostEqual(float(last["gsv"]), 2 * expected)
        self.assertAlmostEqual(float(last["session_open"]), 100.0)
        self.assertAlmostEqual(float(last["level_up"]), 100.0 + 2 * expected)
        self.assertAlmostEqual(float(last["level_dn"]), 100.0 - 2 * expected)
        # the 10th session only has 9 completed sessions before it: undefined
        self.assertTrue(pd.isna(out.loc[9 * 32, "avg_noise"]))
        self.assertTrue(out.loc[10 * 32 :, "avg_noise"].notna().all())

    def test_current_session_is_excluded_from_noise(self):
        parts = []
        start = START
        for _ in range(11):
            parts.append(session_bars(100, 102, 99, 101, start))
            start = start + pd.Timedelta(hours=8)
        frame = pd.concat(parts, ignore_index=True)
        base = Strategy().populate_indicators(frame.copy(), {})
        changed = frame.copy()
        changed.loc[10 * 32 : 10 * 32 + 20, "low"] = 50.0  # wild move inside the current session
        again = Strategy().populate_indicators(changed, {})
        self.assertAlmostEqual(float(base.loc[10 * 32 + 20, "avg_noise"]), float(again.loc[10 * 32 + 20, "avg_noise"]))
        self.assertAlmostEqual(float(base.loc[10 * 32 + 20, "avg_noise"]), 1.0)

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        strategy = Strategy()
        frame = make_frame(2000)
        n = 1488  # last row is the last 15m bar of a 4h block, in the middle of an 8h session (1488 % 32 == 16)
        short = run(strategy, frame.iloc[:n])
        long = run(strategy, frame)
        columns = (
            "avg_noise", "session_open", "gsv", "level_up", "level_dn", "gsv_ratio",
            "session_offset", "close_4h", "hsma_4h",
        )
        for column in columns:
            pd.testing.assert_series_equal(
                short[column].reset_index(drop=True),
                long[column].iloc[:n].reset_index(drop=True),
                check_names=False,
            )
        for column in ("enter_long", "exit_long"):
            a = short[column].fillna(0) if column in short else pd.Series(0, index=short.index)
            b = long[column].iloc[:n].fillna(0) if column in long else pd.Series(0, index=short.index)
            pd.testing.assert_series_equal(
                a.reset_index(drop=True), b.reset_index(drop=True), check_dtype=False
            )

    def test_htf_filter_uses_only_completed_4h_candles(self):
        frame = make_frame(1000)
        out = Strategy().populate_indicators(frame.copy(), {})
        # at the last 15m bar of a 4h block the block's own close is visible, one bar earlier it is not
        block_start = START + pd.Timedelta(hours=4 * 60)
        last_bar = int((block_start + pd.Timedelta(minutes=225) - START) / pd.Timedelta(minutes=15))
        self.assertEqual(out.loc[last_bar, "close_4h"], frame.loc[last_bar, "close"])
        self.assertEqual(out.loc[last_bar - 1, "close_4h"], frame.loc[last_bar - 16, "close"])


if __name__ == "__main__":
    unittest.main()
