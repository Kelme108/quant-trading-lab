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
strategy_module.merge_informative_pair = lambda *a, **k: a[0]
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
NAME = "SessionHighBreakRetest_H124_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


Strategy = getattr(load(), NAME)

START = pd.Timestamp("2024-01-01 00:00", tz="UTC")


def dates(n):
    return pd.date_range(START, periods=n, freq="15min")


def random_frame(n=900, seed=3):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.003, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.003, n))
    volume = rng.lognormal(3, 0.8, n)
    return pd.DataFrame(
        {"date": dates(n), "open": open_, "high": high, "low": low, "close": close, "volume": volume}
    )


def crafted(n=120):
    """Session 0 (bars 0-31) high = 101. Session 1: break at bar 40 (close 102, volume 30),
    bullish wick-retest of the level at bar 41 (low 101.1, close 101.5 > open 101.0)."""
    frame = pd.DataFrame(
        {
            "date": dates(n),
            "open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0, "volume": 10.0,
        }
    )
    frame.loc[5, "high"] = 101.0
    frame.loc[40, ["open", "high", "low", "close", "volume"]] = [100.0, 102.5, 100.0, 102.0, 30.0]
    frame.loc[41, ["open", "high", "low", "close"]] = [101.0, 101.8, 101.1, 101.5]
    frame.loc[42:, ["open", "high", "low", "close"]] = [102.0, 102.2, 101.9, 102.0]
    return frame


def run(frame):
    strategy = Strategy()
    out = strategy.populate_indicators(frame.copy(), {})
    return strategy.populate_exit_trend(strategy.populate_entry_trend(out, {}), {})


def entries(out):
    if "enter_long" not in out:
        return []
    return out.index[out["enter_long"].fillna(0) == 1].tolist()


class SessionHighBreakRetestTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.10)
        self.assertTrue(Strategy.use_custom_stoploss)
        self.assertGreaterEqual(Strategy.startup_candle_count, 100)

    def test_signal_columns_are_binary(self):
        for frame in (random_frame(), crafted()):
            out = run(frame)
            for column in ("enter_long", "exit_long"):
                if column in out:
                    self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_crafted_setup_gives_one_entry_with_tag(self):
        out = run(crafted())
        self.assertEqual(out["sbr_break"].sum(), 1)
        self.assertTrue(out.loc[40, "sbr_break"])
        self.assertEqual(out.loc[40, "psh"], 101.0)
        self.assertEqual(entries(out), [41])
        self.assertEqual(out.loc[41, "enter_tag"], "shbr:101.1")

    def test_zero_volume_gives_no_signal(self):
        frame = crafted()
        frame["volume"] = 0.0
        out = run(frame)
        self.assertEqual(entries(out), [])
        frame = crafted()
        frame.loc[41, "volume"] = 0.0  # zero-volume retest bar: no entry
        self.assertEqual(entries(run(frame)), [])
        frame = crafted()
        frame.loc[40, "volume"] = 0.0  # zero-volume break bar: no setup
        self.assertEqual(entries(run(frame)), [])
        self.assertEqual(entries(run(random_frame().assign(volume=0.0))), [])

    def test_undefined_startup_values_give_no_signal(self):
        # first 20 bars have no volume mean, first session has no previous session
        out = run(random_frame())
        self.assertEqual([i for i in entries(out) if i < 32], [])
        self.assertTrue(out["vmean"].iloc[:20].isna().all())
        self.assertTrue(out["psh"].iloc[:32].isna().all())
        # a break candle inside the first session cannot fire (no prior session)
        frame = crafted()
        frame.loc[20, ["close", "volume", "high"]] = [150.0, 100.0, 150.0]
        out = run(frame)
        self.assertFalse(out.loc[20, "sbr_break"])
        # NaN volume mean at the break bar: no setup
        frame = crafted()
        frame.loc[30, "volume"] = np.nan
        self.assertEqual(entries(run(frame)), [])
        # NaN stored low blocks the entry
        strategy = Strategy()
        out = strategy.populate_indicators(crafted(), {})
        out.loc[41, "sbr_low"] = np.nan
        self.assertEqual(entries(strategy.populate_entry_trend(out, {})), [])

    def test_break_needs_close_and_volume_thresholds(self):
        frame = crafted()
        frame.loc[40, "close"] = 101.2  # < 1.002 x 101 = 101.202
        self.assertEqual(entries(run(frame)), [])
        frame = crafted()
        frame.loc[40, "volume"] = 14.9  # < 1.5 x 10
        self.assertEqual(entries(run(frame)), [])
        frame = crafted()
        frame.loc[40, "volume"] = 15.0  # exactly 1.5x passes
        self.assertEqual(entries(run(frame)), [41])

    def test_only_first_break_of_a_session_counts(self):
        frame = crafted()
        frame.loc[41, ["open", "high", "low", "close"]] = [102.0, 103.0, 102.0, 102.5]  # no retest
        frame.loc[45, ["open", "high", "low", "close", "volume"]] = [102.0, 105.0, 102.0, 104.0, 40.0]
        out = run(frame)
        self.assertEqual(out.index[out["sbr_break"]].tolist(), [40])

    def test_invalidation_cancels_setup(self):
        frame = crafted()
        frame.loc[41, ["open", "high", "low", "close"]] = [101.0, 101.0, 100.0, 100.4]  # < 0.995 x 101
        frame.loc[42, ["open", "high", "low", "close"]] = [101.0, 101.8, 101.1, 101.5]  # would retest
        self.assertEqual(entries(run(frame)), [])
        frame.loc[41, "close"] = 100.5  # exactly above the invalidation line: no cancel, not a retest
        frame.loc[41, "high"] = 101.0
        frame.loc[41, "open"] = 100.6
        out = run(frame)
        self.assertEqual(entries(out), [42])

    def test_retest_conditions(self):
        for column, value in (("low", 101.21), ("close", 100.9), ("open", 101.6)):
            frame = crafted()
            frame.loc[41, column] = value
            frame.loc[41, "high"] = 102.0
            out = run(frame)
            self.assertNotIn(41, entries(out), column)

    def test_first_retest_uses_up_the_setup(self):
        frame = crafted()
        frame.loc[43, ["open", "high", "low", "close"]] = [101.0, 101.8, 101.1, 101.5]
        self.assertEqual(entries(run(frame)), [41])

    def test_retest_window_is_16_bars(self):
        for bar, expected in ((56, [56]), (57, [])):
            frame = crafted()
            frame.loc[41, ["open", "high", "low", "close"]] = [102.0, 102.2, 101.9, 102.0]
            frame.loc[bar, ["open", "high", "low", "close"]] = [101.0, 101.8, 101.1, 101.5]
            self.assertEqual(entries(run(frame)), expected, bar)

    def test_incomplete_previous_session_gives_no_setup(self):
        frame = crafted().drop(index=10).reset_index(drop=True)  # session 0 now has 31 bars
        out = run(frame)
        self.assertEqual(entries(out), [])
        self.assertTrue(out["psh"].iloc[:63].isna().all())  # sessions 0 and 1 lack a complete predecessor

    def test_sessions_are_utc_eight_hour_blocks(self):
        frame = crafted(200)
        out = run(frame)
        # bars 64.. (08:00-15:45 is session 1; 16:00 is session 2 = bar 64): PSH is session 1's high
        self.assertEqual(out.loc[64, "psh"], 102.5)
        self.assertEqual(out.loc[63, "psh"], 101.0)

    def test_stop_is_frozen_below_entry(self):
        strategy = Strategy()
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        # tight signal low: distance floors at 1%
        trade = types.SimpleNamespace(open_rate=100.0, enter_tag="shbr:99.9")
        self.assertAlmostEqual(strategy.custom_stoploss("BTC/USDT", trade, now, 100.0, 0.0), -0.01)
        # a later price: the absolute stop price stays at 99.0
        ratio = strategy.custom_stoploss("BTC/USDT", trade, now, 101.0, 0.01)
        self.assertAlmostEqual(101.0 * (1 + ratio), 99.0)
        # deep wick: 0.998 x low is the stop (1 - 0.998 x 97 / 100 = 3.194%)
        trade = types.SimpleNamespace(open_rate=100.0, enter_tag="shbr:97.0")
        stop = 100.0 * (1 + strategy.custom_stoploss("BTC/USDT", trade, now, 100.0, 0.0))
        self.assertAlmostEqual(stop, 0.998 * 97.0)
        # price already below the stop: still a negative value
        self.assertLess(strategy.custom_stoploss("BTC/USDT", trade, now, 90.0, -0.1), 0)
        # missing tag: engine backstop
        trade = types.SimpleNamespace(open_rate=100.0, enter_tag=None)
        self.assertIsNone(strategy.custom_stoploss("BTC/USDT", trade, now, 100.0, 0.0))

    def test_take_profit_exit(self):
        strategy = Strategy()
        opened = datetime(2025, 1, 1, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_date_utc=opened)
        soon = opened + timedelta(hours=1)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, soon, 101.9, 0.0199))
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, soon, 102.0, 0.02), "take_profit_2pct")

    def test_time_exit_after_12_hours(self):
        strategy = Strategy()
        opened = datetime(2025, 1, 1, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_date_utc=opened)
        before = opened + timedelta(hours=11, minutes=45)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, before, 100.0, 0.0))
        at = opened + timedelta(hours=12)
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, at, 100.0, -0.005), "time_exit_12h")

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        columns = ["psh", "vmean", "sbr_break", "sbr_signal", "sbr_low", "enter_long", "enter_tag"]
        frames = [random_frame(1200), crafted(200)]
        cuts = [(700, 1200), (41, 200), (42, 200), (45, 200)]
        for frame, (n, total) in zip((frames[0], frames[1], frames[1], frames[1]), cuts):
            short = run(frame.iloc[:n])
            long = run(frame.iloc[:total])
            for column in columns:
                a = (short[column] if column in short else pd.Series(np.nan, index=short.index)).reset_index(drop=True)
                b = (
                    long[column] if column in long else pd.Series(np.nan, index=long.index)
                ).iloc[:n].reset_index(drop=True)
                pd.testing.assert_series_equal(a, b, check_dtype=False, check_names=False)

    def test_volume_mean_excludes_current_bar(self):
        frame = crafted()
        frame["volume"] = 1.0
        frame.loc[59, "volume"] = 10.0
        out = Strategy().populate_indicators(frame, {})
        self.assertAlmostEqual(float(out.loc[59, "vmean"]), 1.0)


if __name__ == "__main__":
    unittest.main()
