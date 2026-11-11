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
NAME = "DailyNR7Breakout_H114_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


Strategy = getattr(load(), NAME)
START = pd.Timestamp("2025-01-01 00:00", tz="UTC")


def dates(n):
    return pd.date_range(START, periods=n, freq="15min", tz="UTC")


def make_frame(n=1400, seed=3):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0002, 0.003, n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.002, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.002, n))
    volume = rng.lognormal(3, 0.6, n)
    return pd.DataFrame(
        {"date": dates(n), "open": open_, "high": high, "low": low, "close": close, "volume": volume}
    )


def run(strategy, frame):
    frame = strategy.populate_indicators(frame.copy(), {})
    return strategy.populate_entry_trend(frame, {})


def count(frame):
    return int(frame["enter_long"].fillna(0).sum()) if "enter_long" in frame else 0


def flat_frame(days=5, ranges=None):
    """Constant close 100; every hour has range 1.0 unless overridden by {(day, hour): range}."""
    n = days * 96
    d = dates(n)
    rng = np.full(n, 1.0)
    for (day, hour), value in (ranges or {}).items():
        start = day * 96 + hour * 4
        rng[start : start + 4] = value
    return pd.DataFrame(
        {
            "date": d,
            "open": 100.0,
            "high": 100.0 + rng / 2,
            "low": 100.0 - rng / 2,
            "close": 100.0,
            "volume": 10.0,
        }
    )


def crafted(n=40):
    """Indicator frame with a valid breakout on the last row (age 60 min after the NR4 bar)."""
    d = dates(n)
    frame = pd.DataFrame(
        {
            "date": d,
            "open": 100.0,
            "high": 100.5,
            "low": 99.5,
            "close": 100.0,
            "volume": 10.0,
            "nr_high": 100.2,
            "nr_low": 99.5,
            "nr_date": d[n - 5],
            "nr_age_min": 60.0,
            "h4_close": 105.0,
            "h4_sma": 100.0,
        }
    )
    frame.loc[n - 1, "close"] = 100.5
    return frame


def trade(open_rate=100.0, tag="nr4|99.5|2025-01-04T10:45:00+00:00|2025-01-04", opened=None):
    opened = opened or datetime(2025, 1, 4, 12, 0, tzinfo=timezone.utc)
    return types.SimpleNamespace(open_rate=open_rate, enter_tag=tag, open_date_utc=opened)


class NR4Tests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.02)
        self.assertTrue(Strategy.use_custom_stoploss)
        self.assertGreaterEqual(Strategy.startup_candle_count, 900)

    def test_signal_columns_are_binary(self):
        out = run(Strategy(), make_frame())
        for column in ("enter_long", "exit_long"):
            if column in out:
                self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_hourly_nr4_detected_against_same_hour_of_three_prior_days(self):
        # day 3 (4th day), hour 10: range 0.5 vs 1.0 on days 0..2
        frame = flat_frame(ranges={(3, 10): 0.5})
        out = Strategy().populate_indicators(frame, {})
        row = 3 * 96 + 10 * 4 + 3
        self.assertAlmostEqual(out.loc[row, "nr_high"], 100.25)
        self.assertAlmostEqual(out.loc[row, "nr_low"], 99.75)
        self.assertEqual(out.loc[row, "nr_age_min"], 0.0)
        self.assertEqual(out.loc[row + 2, "nr_age_min"], 30.0)
        self.assertAlmostEqual(out.loc[row + 2, "nr_high"], 100.25)
        # no NR4 before it, not even on day 2 (only two prior days exist)
        self.assertTrue(out.loc[: row - 1, "nr_high"].isna().all())

    def test_nr4_needs_three_prior_days_strict_and_range_floor(self):
        s = Strategy()
        # only two prior days: the same narrow bar on day 2 is not an NR4
        out = s.populate_indicators(flat_frame(ranges={(2, 10): 0.5}), {})
        self.assertTrue(out["nr_high"].isna().all())
        # equal to one prior day: not strictly smaller
        out = s.populate_indicators(flat_frame(ranges={(3, 10): 1.0}), {})
        self.assertTrue(out["nr_high"].isna().all())
        # one earlier day is narrower than the signal bar
        out = s.populate_indicators(flat_frame(ranges={(3, 10): 0.5, (1, 10): 0.4}), {})
        self.assertTrue(out["nr_high"].isna().all())
        # range/close below 0.0025 (0.2 / 100 = 0.002) is rejected
        frame = flat_frame(days=5, ranges={(3, 10): 0.2})
        out = s.populate_indicators(frame, {})
        self.assertTrue(out["nr_high"].isna().all())
        # exactly 0.0025 passes (0.25 / 100)
        out = s.populate_indicators(flat_frame(ranges={(3, 10): 0.25}), {})
        self.assertFalse(out["nr_high"].isna().all())

    def test_most_recent_nr4_is_used(self):
        frame = flat_frame(ranges={(3, 10): 0.5, (3, 11): 0.4})
        out = Strategy().populate_indicators(frame, {})
        row10 = 3 * 96 + 10 * 4 + 3
        row11 = row10 + 4
        self.assertAlmostEqual(out.loc[row11 - 1, "nr_high"], 100.25)
        self.assertEqual(out.loc[row11 - 1, "nr_age_min"], 45.0)
        self.assertAlmostEqual(out.loc[row11, "nr_high"], 100.2)
        self.assertEqual(out.loc[row11, "nr_age_min"], 0.0)

    def test_4h_block_close_and_sma50(self):
        n = 60 * 16
        d = dates(n)
        block = np.arange(n) // 16
        close = 100.0 + block
        frame = pd.DataFrame(
            {"date": d, "open": close, "high": close + 1, "low": close - 1, "close": close, "volume": 1.0}
        )
        out = Strategy().populate_indicators(frame, {})
        # the 50th completed block ends on row 799
        self.assertTrue(out.loc[:798, "h4_sma"].isna().all())
        self.assertAlmostEqual(out.loc[799, "h4_sma"], np.mean(np.arange(100, 150)))
        self.assertEqual(out.loc[799, "h4_close"], 149.0)
        # inside the next block the previous completed block is still the reference
        self.assertEqual(out.loc[800, "h4_close"], 149.0)
        self.assertEqual(out.loc[814, "h4_close"], 149.0)
        self.assertEqual(out.loc[815, "h4_close"], 150.0)
        self.assertAlmostEqual(out.loc[815, "h4_sma"], np.mean(np.arange(101, 151)))
        self.assertTrue(out.loc[:14, "h4_close"].isna().all())

    def test_entry_needs_all_conditions(self):
        s = Strategy()
        out = s.populate_entry_trend(crafted(), {})
        self.assertEqual(count(out), 1)
        self.assertEqual(out.loc[39, "enter_long"], 1)
        self.assertEqual(out.loc[39, "enter_tag"], "nr4|99.5|2025-01-01T08:45:00+00:00|2025-01-01")
        for column, value in (
            ("close", 100.2),  # not above high(H)
            ("nr_age_min", 0.0),
            ("nr_age_min", 135.0),
            ("h4_close", 99.0),  # filter fails
            ("nr_low", 98.0),  # low(H) more than 2% below close
        ):
            frame = crafted()
            frame.loc[39, column] = value
            self.assertEqual(count(s.populate_entry_trend(frame, {})), 0, (column, value))
        for age in (15.0, 120.0):
            frame = crafted()
            frame.loc[39, "nr_age_min"] = age
            self.assertEqual(count(s.populate_entry_trend(frame, {})), 1, age)

    def test_zero_volume_gives_no_signal(self):
        s = Strategy()
        frame = crafted()
        frame.loc[39, "volume"] = 0.0
        self.assertEqual(count(s.populate_entry_trend(frame, {})), 0)
        frame = make_frame()
        frame["volume"] = 0.0
        self.assertEqual(count(run(s, frame)), 0)

    def test_undefined_values_give_no_signal(self):
        s = Strategy()
        for column in ("nr_high", "nr_low", "nr_age_min", "h4_close", "h4_sma"):
            frame = crafted()
            frame.loc[39, column] = np.nan
            self.assertEqual(count(s.populate_entry_trend(frame, {})), 0, column)
        out = run(s, make_frame())
        self.assertEqual(count(out.iloc[:790]), 0)

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        s = Strategy()
        frame = make_frame(1500)
        for n in (1000, 1003, 1101):
            short = run(s, frame.iloc[:n])
            long = run(s, frame)
            columns = ["nr_high", "nr_low", "nr_date", "nr_age_min", "h4_close", "h4_sma"]
            pd.testing.assert_frame_equal(short[columns], long[columns].iloc[:n])
            a = short["enter_long"].fillna(0) if "enter_long" in short else pd.Series(0, index=short.index)
            b = long["enter_long"].iloc[:n].fillna(0) if "enter_long" in long else pd.Series(0, index=short.index)
            pd.testing.assert_series_equal(a, b, check_dtype=False)

    def test_confirm_limits_one_entry_per_nr4_bar_and_two_per_day(self):
        s = Strategy()
        s.bot_start()
        now = datetime(2025, 1, 4, 12, 0, tzinfo=timezone.utc)

        def confirm(pair, nr, day):
            return s.confirm_trade_entry(
                pair, "limit", 1.0, 100.0, "GTC", now, f"nr4|99.5|{nr}|{day}", "long"
            )

        self.assertTrue(confirm("BTC/USDT", "a", "2025-01-04"))
        self.assertFalse(confirm("BTC/USDT", "a", "2025-01-04"))  # same NR4 bar
        self.assertTrue(confirm("BTC/USDT", "b", "2025-01-04"))
        self.assertFalse(confirm("BTC/USDT", "c", "2025-01-04"))  # third on the date
        self.assertTrue(confirm("ETH/USDT", "c", "2025-01-04"))  # other pair
        self.assertTrue(confirm("BTC/USDT", "d", "2025-01-05"))  # next date

    def test_custom_stop_is_constant_price_with_floor_and_cap(self):
        s = Strategy()
        now = datetime(2025, 1, 4, 12, 0, tzinfo=timezone.utc)
        # low 99.5 -> 0.5% distance, floored to 1%
        self.assertAlmostEqual(s.custom_stoploss("X", trade(), now, 100.0, 0.0), 99.0 / 100.0 - 1)
        self.assertAlmostEqual(s.custom_stoploss("X", trade(), now, 103.0, 0.03), 99.0 / 103.0 - 1)
        # low 98.5 -> 1.5% distance
        t = trade(tag="nr4|98.5|x|2025-01-04")
        self.assertAlmostEqual(s.custom_stoploss("X", t, now, 100.0, 0.0), 98.5 / 100.0 - 1)
        # low 90 -> 10% distance, capped at 2%
        t = trade(tag="nr4|90.0|x|2025-01-04")
        self.assertAlmostEqual(s.custom_stoploss("X", t, now, 100.0, 0.0), 98.0 / 100.0 - 1)
        # no tag: leave the native stop alone
        self.assertIsNone(s.custom_stoploss("X", trade(tag=None), now, 100.0, 0.0))
        self.assertEqual(Strategy.stoploss, -0.02)

    def test_target_2r_from_current_profit(self):
        s = Strategy()
        s.dp = None
        opened = datetime(2025, 1, 4, 12, 0, tzinfo=timezone.utc)
        now = opened + timedelta(hours=1)
        # stop_pct 1% -> target +2%
        self.assertIsNone(s.custom_exit("X", trade(), now, 101.9, 0.019))
        self.assertEqual(s.custom_exit("X", trade(), now, 102.1, 0.021), "take_profit_2R")
        # stop_pct 1.5% -> target +3%
        t = trade(tag="nr4|98.5|x|2025-01-04")
        self.assertIsNone(s.custom_exit("X", t, now, 102.5, 0.025))
        self.assertEqual(s.custom_exit("X", t, now, 103.5, 0.035), "take_profit_2R")

    def test_target_uses_last_closed_candle_close(self):
        s = Strategy()
        opened = datetime(2025, 1, 4, 12, 0, tzinfo=timezone.utc)
        now = opened + timedelta(hours=1)

        def provide(candle_time, close):
            frame = pd.DataFrame({"date": [pd.Timestamp(candle_time)], "close": [close]})
            s.dp = types.SimpleNamespace(get_analyzed_dataframe=lambda pair, tf: (frame, None))

        provide(opened + timedelta(minutes=45), 102.5)
        self.assertEqual(s.custom_exit("X", trade(), now, 100.0, 0.0), "take_profit_2R")
        # the current price is high but the last closed candle did not close at the target
        provide(opened + timedelta(minutes=45), 101.5)
        self.assertIsNone(s.custom_exit("X", trade(), now, 103.0, 0.03))
        # a closed candle before the entry bar does not count
        provide(opened - timedelta(minutes=15), 105.0)
        self.assertIsNone(s.custom_exit("X", trade(), now, 100.0, 0.0))
        # the entry bar itself counts
        provide(opened, 102.5)
        self.assertEqual(s.custom_exit("X", trade(), now, 100.0, 0.0), "take_profit_2R")

    def test_time_exit_after_32_bars(self):
        s = Strategy()
        s.dp = None
        opened = datetime(2025, 1, 4, 12, 0, tzinfo=timezone.utc)
        t = trade(opened=opened)
        self.assertIsNone(s.custom_exit("X", t, opened + timedelta(hours=7, minutes=45), 100.0, 0.0))
        self.assertEqual(s.custom_exit("X", t, opened + timedelta(hours=8), 100.0, 0.0), "time_exit_8h")
        # time exit also applies when the tag is missing
        t = trade(tag=None, opened=opened)
        self.assertEqual(s.custom_exit("X", t, opened + timedelta(hours=9), 100.0, 0.0), "time_exit_8h")


if __name__ == "__main__":
    unittest.main()
