import importlib.util
import math
import sys
import types
import unittest
from pathlib import Path

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
FILENAME = "SessionOpeningRangeBreakout_H069_v1.py"
CLASS_NAME = "SessionOpeningRangeBreakout_H069_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / "_archive" / FILENAME
    spec = importlib.util.spec_from_file_location(CLASS_NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, CLASS_NAME)


Strategy = load_strategy()


def flat_frame(start_utc: str, periods: int) -> pd.DataFrame:
    """Flat 100 closes, bar range 0.4% (armed opening range)."""
    dates = pd.date_range(start_utc, periods=periods, freq="15min", tz="UTC")
    return pd.DataFrame(
        {
            "date": dates,
            "open": 100.0,
            "high": 100.2,
            "low": 99.8,
            "close": 100.0,
            "volume": 1.0,
        }
    )


def wave_frame(start_utc: str, periods: int) -> pd.DataFrame:
    dates = pd.date_range(start_utc, periods=periods, freq="15min", tz="UTC")
    closes = [100.0 + 3.0 * math.sin(i / 7.0) + 1.5 * math.sin(i / 2.3) for i in range(periods)]
    return pd.DataFrame(
        {
            "date": dates,
            "open": closes,
            "high": [c * 1.004 for c in closes],
            "low": [c * 0.996 for c in closes],
            "close": closes,
            "volume": [1.0] * periods,
        }
    )


def set_bar(frame: pd.DataFrame, utc: str, **values) -> None:
    idx = frame.index[frame["date"] == pd.Timestamp(utc, tz="UTC")][0]
    for key, value in values.items():
        frame.loc[idx, key] = value


def run(frame: pd.DataFrame) -> pd.DataFrame:
    strategy = Strategy()
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    return frame


def entry_times(frame: pd.DataFrame) -> list:
    if "enter_long" not in frame:
        return []
    return list(frame.loc[frame["enter_long"] == 1, "date"])


class SessionOpeningRangeBreakoutH069Tests(unittest.TestCase):
    def test_class_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertAlmostEqual(Strategy.stoploss, -0.03)
        self.assertGreaterEqual(Strategy.startup_candle_count, 96)

    def test_entry_in_standard_time(self) -> None:
        # Tuesday 2024-01-09, EST: 09:30 ET = 14:30 UTC; first breakout bar at 10:00 ET = 15:00 UTC.
        frame = flat_frame("2024-01-08 00:00", 96 * 3)
        set_bar(frame, "2024-01-09 15:00", high=100.6, close=100.5)
        set_bar(frame, "2024-01-09 16:00", high=100.7, close=100.6)  # later breakout: ignored
        result = run(frame)
        self.assertEqual(entry_times(result), [pd.Timestamp("2024-01-09 15:00", tz="UTC")])

    def test_entry_in_daylight_time(self) -> None:
        # Wednesday 2024-07-10, EDT: 09:30 ET = 13:30 UTC; 09:45 ET = 13:45 UTC.
        frame = flat_frame("2024-07-09 00:00", 96 * 3)
        set_bar(frame, "2024-07-10 13:45", high=100.6, close=100.5)
        # 13:15 UTC (09:15 ET) breakout before the window: ignored.
        set_bar(frame, "2024-07-11 13:15", high=100.6, close=100.5)
        result = run(frame)
        self.assertEqual(entry_times(result), [pd.Timestamp("2024-07-10 13:45", tz="UTC")])
        or_row = result[result["date"] == pd.Timestamp("2024-07-10 13:30", tz="UTC")].iloc[0]
        self.assertAlmostEqual(or_row["or_high"], 100.2)

    def test_entry_window_bounds(self) -> None:
        # EDT 14:30 ET = 18:30 UTC is the last allowed bar; 14:45 ET = 18:45 UTC is not.
        frame = flat_frame("2024-07-09 00:00", 96 * 3)
        set_bar(frame, "2024-07-10 18:30", high=100.6, close=100.5)
        set_bar(frame, "2024-07-11 18:45", high=100.6, close=100.5)
        result = run(frame)
        self.assertEqual(entry_times(result), [pd.Timestamp("2024-07-10 18:30", tz="UTC")])

    def test_unarmed_days_and_weekends_do_not_trade(self) -> None:
        frame = flat_frame("2024-07-09 00:00", 96 * 7)
        # Range too wide on 2024-07-10 (3%), too narrow on 2024-07-11 (0.1%).
        set_bar(frame, "2024-07-10 13:30", high=102.0, low=99.0)
        set_bar(frame, "2024-07-10 14:00", high=102.6, close=102.5)
        set_bar(frame, "2024-07-11 13:30", high=100.05, low=99.95)
        set_bar(frame, "2024-07-11 14:00", high=100.6, close=100.5)
        # Saturday 2024-07-13.
        set_bar(frame, "2024-07-13 14:00", high=100.6, close=100.5)
        result = run(frame)
        self.assertEqual(entry_times(result), [])

    def test_missing_opening_bar_means_no_trade(self) -> None:
        frame = flat_frame("2024-07-09 00:00", 96 * 3)
        set_bar(frame, "2024-07-10 14:00", high=100.6, close=100.5)
        frame = frame[frame["date"] != pd.Timestamp("2024-07-10 13:30", tz="UTC")].reset_index(drop=True)
        result = run(frame)
        self.assertEqual(entry_times(result), [])

    def test_exits(self) -> None:
        frame = flat_frame("2024-07-09 00:00", 96 * 3)
        set_bar(frame, "2024-07-10 14:00", high=100.6, close=100.5)
        set_bar(frame, "2024-07-10 15:00", low=99.5, close=99.6)  # close below ORL 99.8
        result = run(frame)
        exits = set(result.loc[result["exit_long"] == 1, "date"])
        self.assertIn(pd.Timestamp("2024-07-10 15:00", tz="UTC"), exits)
        self.assertIn(pd.Timestamp("2024-07-10 19:45", tz="UTC"), exits)  # 15:45 ET bar
        self.assertNotIn(pd.Timestamp("2024-07-10 19:30", tz="UTC"), exits)
        self.assertNotIn(pd.Timestamp("2024-07-10 14:00", tz="UTC"), exits)

    def test_signal_columns_are_binary(self) -> None:
        result = run(wave_frame("2024-03-04 00:00", 96 * 20))
        self.assertGreater(len(entry_times(result)), 0)
        for column in ("enter_long", "exit_long"):
            if column in result:
                values = result[column].dropna().unique().tolist()
                self.assertTrue(set(values).issubset({1}))

    def test_zero_volume_produces_no_signal(self) -> None:
        frame = wave_frame("2024-03-04 00:00", 96 * 20)
        frame["volume"] = 0.0
        result = run(frame)
        self.assertEqual(int(result.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(result.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_zero_volume_on_breakout_bar(self) -> None:
        frame = flat_frame("2024-07-09 00:00", 96 * 3)
        set_bar(frame, "2024-07-10 14:00", high=100.6, close=100.5, volume=0.0)
        set_bar(frame, "2024-07-10 15:00", high=100.6, close=100.5)  # not the first breakout
        result = run(frame)
        self.assertEqual(entry_times(result), [])

    def test_undefined_startup_values_produce_no_signal(self) -> None:
        # Starts at 10:00 ET (14:00 UTC, EDT): the day's opening range bar is absent, so ORH/ORL are undefined.
        frame = flat_frame("2024-07-10 14:00", 96 * 2)
        set_bar(frame, "2024-07-10 14:15", high=100.6, close=100.5)
        result = run(frame)
        undefined = result["or_high"].isna() | result["or_low"].isna()
        self.assertTrue(undefined.iloc[0])
        self.assertEqual(int(result.loc[undefined, "enter_long"].fillna(0).sum()) if "enter_long" in result else 0, 0)
        if "exit_long" in result:
            below_orl_rows = result.loc[undefined & (result.get("exit_tag") == "close_below_orl")]
            self.assertEqual(len(below_orl_rows), 0)
        # Wave frame: nothing inside the startup window without a defined range.
        wave = run(wave_frame("2024-03-04 00:00", 96 * 5))
        startup = Strategy.startup_candle_count
        head = wave.iloc[:startup]
        nan_rows = head["or_high"].isna()
        self.assertEqual(int(head.loc[nan_rows].get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_signals_do_not_change_when_future_candles_appended(self) -> None:
        full = wave_frame("2024-03-04 00:00", 96 * 30)  # spans the 2024-03-10 DST switch
        n = 96 * 18 + 37
        short = run(full.iloc[:n].copy())
        long = run(full.copy())
        columns = ["or_high", "or_low", "first_breakout", "enter_long", "exit_long", "enter_tag", "exit_tag"]
        for column in columns:
            if column not in short:
                short[column] = float("nan")
            if column not in long:
                long[column] = float("nan")
        pd.testing.assert_frame_equal(
            short.loc[: n - 1, columns].reset_index(drop=True),
            long.loc[: n - 1, columns].reset_index(drop=True),
            check_dtype=False,
        )


if __name__ == "__main__":
    unittest.main()
