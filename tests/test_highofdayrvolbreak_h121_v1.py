import importlib.util
import sys
import types
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

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

ROOT = Path(__file__).parents[1]
NAME = "HighOfDayRVolBreak_H121_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load()
Strategy = getattr(MODULE, NAME)

EVENT_DAY = 21  # 0-based day with 21 complete previous days
EVENT_SLOT = 30
EVENT_INDEX = EVENT_DAY * 96 + EVENT_SLOT
INDICATORS = ["hod", "hod_held", "day_open", "day_return", "rvol", "slot"]


def make_frame(days=EVENT_DAY + 1, event_volume=3.0):
    """Flat market at 100; on the event day a 2h-held high of 101 is broken at slot 30 on triple volume."""
    n = days * 96
    dates = pd.date_range("2024-01-01", periods=n, freq="15min", tz="UTC")
    frame = pd.DataFrame(
        {
            "date": dates,
            "open": 100.0,
            "high": 100.1,
            "low": 99.9,
            "close": 100.0,
            "volume": 1.0,
        }
    )
    base = EVENT_DAY * 96
    if n > base:
        end = min(n, base + 96)
        frame.loc[base:end - 1, "volume"] = event_volume
        if base + 10 < n:
            frame.loc[base + 10, ["high", "close"]] = [101.0, 100.5]
        for i in range(base + 11, min(n, base + 30)):
            frame.loc[i, ["open", "high", "close"]] = [100.5, 100.7, 100.6]
        if base + 30 < n:
            frame.loc[base + 30, ["open", "high", "close"]] = [100.6, 101.6, 101.5]
        for i in range(base + 31, end):
            frame.loc[i, ["open", "high", "close"]] = [101.5, 101.55, 101.5]
    return frame


def run(frame):
    strategy = Strategy()
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    return frame


def entries(frame):
    if "enter_long" not in frame:
        return []
    return frame.index[frame["enter_long"].fillna(0) == 1].tolist()


class FakeTrade:
    def __init__(self, open_date_utc):
        self.open_date_utc = open_date_utc


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


class HighOfDayRVolBreakTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.01)
        self.assertGreaterEqual(Strategy.startup_candle_count, 2112)

    def test_event_creates_exactly_one_binary_entry(self):
        frame = run(make_frame())
        self.assertEqual(entries(frame), [EVENT_INDEX])
        values = frame["enter_long"].dropna().unique().tolist()
        self.assertTrue(set(values).issubset({1}))
        self.assertNotIn("exit_long", frame.columns)
        self.assertAlmostEqual(frame.loc[EVENT_INDEX, "rvol"], 3.0)
        self.assertEqual(frame.loc[EVENT_INDEX, "hod"], 101.0)
        self.assertTrue(bool(frame.loc[EVENT_INDEX, "hod_held"]))
        self.assertAlmostEqual(frame.loc[EVENT_INDEX, "day_return"], 0.015)

    def test_level_set_less_than_two_hours_earlier_is_not_held(self):
        frame = run(make_frame())
        base = EVENT_DAY * 96
        # Close above the running high at slot 10 happens when the level (slot 9) is 1 bar old.
        self.assertFalse(bool(frame.loc[base + 10, "hod_held"]))
        self.assertFalse(bool(frame.loc[base + 17, "hod_held"]))  # level at slot 10 is 7 bars old
        self.assertTrue(bool(frame.loc[base + 18, "hod_held"]))  # 8 bars old

    def test_low_relative_volume_gives_no_entry(self):
        frame = run(make_frame(event_volume=1.4))
        self.assertEqual(entries(frame), [])

    def test_small_day_return_gives_no_entry(self):
        raw = make_frame()
        base = EVENT_DAY * 96
        raw.loc[base + 30, ["high", "close"]] = [101.6, 100.9]
        # close 100.9 < HOD 101 is not a break; use a day open above to make the return < 0.5%
        raw.loc[base:base + 29, ["open"]] = 100.0
        raw.loc[base, "open"] = 101.4  # Od = 101.4 -> 101.5/101.4 - 1 < 0.5%
        raw.loc[base + 30, ["high", "close"]] = [101.6, 101.5]
        frame = run(raw)
        self.assertEqual(entries(frame), [])

    def test_outside_entry_window_gives_no_entry(self):
        raw = make_frame()
        base = EVENT_DAY * 96
        # Shift the whole pattern so the break lands at slot 84 (21:00): level at slot 60, flat before.
        raw.loc[base:base + 95, ["open", "high", "low", "close"]] = [100.0, 100.1, 99.9, 100.0]
        raw.loc[base + 60, ["high", "close"]] = [101.0, 100.5]
        raw.loc[base + 61:base + 83, ["open", "high", "close"]] = [100.5, 100.7, 100.6]
        raw.loc[base + 84, ["open", "high", "close"]] = [100.6, 101.6, 101.5]
        self.assertEqual(entries(run(raw)), [])
        # The same pattern at slot 78 (19:30 bar) is allowed.
        raw2 = make_frame().iloc[: base + 96].copy()
        raw2.loc[base:base + 95, ["open", "high", "low", "close"]] = [100.0, 100.1, 99.9, 100.0]
        raw2.loc[base + 60, ["high", "close"]] = [101.0, 100.5]
        raw2.loc[base + 61:base + 77, ["open", "high", "close"]] = [100.5, 100.7, 100.6]
        raw2.loc[base + 78, ["open", "high", "close"]] = [100.6, 101.6, 101.5]
        self.assertEqual(entries(run(raw2)), [base + 78])

    def test_zero_volume_candle_gives_no_signal(self):
        raw = make_frame()
        raw.loc[EVENT_INDEX, "volume"] = 0.0
        self.assertEqual(entries(run(raw)), [])
        allzero = make_frame()
        allzero["volume"] = 0.0
        frame = run(allzero)
        self.assertEqual(entries(frame), [])
        self.assertTrue(frame["rvol"].isna().all())

    def test_undefined_startup_values_give_no_signal(self):
        # Event placed on day 20 has only 20 previous days -> defined; day 19 has only 19 -> undefined.
        raw = make_frame()
        frame = run(raw)
        self.assertTrue(frame["rvol"].iloc[: 20 * 96].isna().all())
        self.assertTrue(frame["rvol"].iloc[20 * 96:].notna().all())
        rng = np.random.default_rng(3)
        n = 2112
        dates = pd.date_range("2024-01-01", periods=n, freq="15min", tz="UTC")
        close = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.002, n)))
        noisy = pd.DataFrame(
            {
                "date": dates,
                "open": close * 0.9995,
                "high": close * 1.001,
                "low": close * 0.998,
                "close": close,
                "volume": rng.uniform(1.0, 5.0, n),
            }
        )
        out = run(noisy)
        startup = Strategy.startup_candle_count
        self.assertEqual([i for i in entries(out) if i < 20 * 96], [])
        self.assertLessEqual(len([i for i in entries(out) if i < startup]), len(entries(out)))

    def test_missing_bar_in_a_previous_day_makes_rvol_undefined(self):
        raw = make_frame()
        raw = raw.drop(index=5 * 96 + 3).reset_index(drop=True)
        frame = run(raw)
        event = frame.index[(frame["date"] == pd.Timestamp("2024-01-22 07:30", tz="UTC"))][0]
        self.assertTrue(pd.isna(frame.loc[event, "rvol"]))
        self.assertEqual(entries(frame), [])

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        rng = np.random.default_rng(11)
        n_total = 30 * 96
        dates = pd.date_range("2024-01-01", periods=n_total, freq="15min", tz="UTC")
        close = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.003, n_total)))
        full = pd.DataFrame(
            {
                "date": dates,
                "open": np.roll(close, 1),
                "high": close * (1 + rng.uniform(0, 0.003, n_total)),
                "low": close * (1 - rng.uniform(0, 0.003, n_total)),
                "close": close,
                "volume": rng.uniform(0.5, 6.0, n_total),
            }
        )
        n = 26 * 96 + 37
        short = run(full.iloc[:n])
        long = run(full)
        columns = INDICATORS + ["enter_long"]
        for column in columns:
            if column not in short.columns:
                short[column] = np.nan
            if column not in long.columns:
                long[column] = np.nan
        pd.testing.assert_frame_equal(
            short.loc[: n - 1, columns].reset_index(drop=True),
            long.loc[: n - 1, columns].reset_index(drop=True),
            check_dtype=False,
        )
        # The same on the deterministic event series with a tail of extreme future candles.
        base = make_frame(days=EVENT_DAY + 2)
        a = run(base.iloc[: EVENT_INDEX + 5])
        changed = base.copy()
        changed.loc[EVENT_INDEX + 5:, ["open", "high", "low", "close"]] = 500.0
        changed.loc[EVENT_INDEX + 5:, "volume"] = 99.0
        b = run(changed)
        self.assertEqual(entries(a), [EVENT_INDEX])
        self.assertEqual(entries(b), [EVENT_INDEX])
        pd.testing.assert_frame_equal(
            a[INDICATORS], b.loc[: EVENT_INDEX + 4, INDICATORS], check_dtype=False
        )

    def test_two_entries_per_day_limit(self):
        strategy = Strategy()
        fake_module = types.ModuleType("freqtrade.persistence")

        def trades(count, day=utc(2024, 3, 5, 3, 0)):
            fake = type("Trade", (), {})
            fake.get_trades_proxy = staticmethod(
                lambda pair=None: [FakeTrade(day)] * count + [FakeTrade(utc(2024, 3, 4, 22, 0))]
            )
            return fake

        now = utc(2024, 3, 5, 12, 0)
        for count, expected in ((0, True), (1, True), (2, False), (3, False)):
            fake_module.Trade = trades(count)
            with mock.patch.dict(sys.modules, {"freqtrade.persistence": fake_module}):
                result = strategy.confirm_trade_entry(
                    "BTC/USDT", "limit", 1.0, 100.0, "GTC", now, None, "long"
                )
            self.assertEqual(result, expected)

    def test_take_profit_exit(self):
        strategy = Strategy()
        trade = FakeTrade(utc(2024, 3, 5, 10, 0))
        now = utc(2024, 3, 5, 10, 15)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, now, 102.0, 0.0199))
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, now, 102.0, 0.02), "take_profit_2pct")
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, now, 103.0, 0.03), "take_profit_2pct")

    def test_time_exit_after_eight_hours(self):
        strategy = Strategy()
        trade = FakeTrade(utc(2024, 3, 5, 2, 0))
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, utc(2024, 3, 5, 9, 45), 100.0, -0.005))
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade, utc(2024, 3, 5, 10, 0), 100.0, -0.005),
            "time_exit_8h",
        )

    def test_time_exit_at_utc_day_end(self):
        strategy = Strategy()
        trade = FakeTrade(utc(2024, 3, 5, 20, 0))
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, utc(2024, 3, 5, 23, 30), 100.0, 0.001))
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade, utc(2024, 3, 5, 23, 45), 100.0, 0.001),
            "time_exit_utc_day_close",
        )
        naive_trade = FakeTrade(datetime(2024, 3, 5, 20, 0))
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", naive_trade, datetime(2024, 3, 5, 23, 45), 100.0, 0.0),
            "time_exit_utc_day_close",
        )


if __name__ == "__main__":
    unittest.main()
