import importlib.util
import sys
import types
import unittest
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
CLASS_NAME = "SameSlotPeriodicity_H064_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / "_archive" / f"{CLASS_NAME}.py"
    spec = importlib.util.spec_from_file_location(CLASS_NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, CLASS_NAME)


Strategy = load_strategy()

START = pd.Timestamp("2024-01-01 00:00", tz="UTC")  # a Monday
HISTORY_ROWS = 26 * 7 * 24  # first day with 26 weeks of same-slot history starts at this row


def make_frame(n, drift_slots=((0, 12),), seed=11, start=START):
    """1h frame; each (weekday, start hour) slot in drift_slots gets +0.3% per bar for its 4 bars."""
    dates = pd.date_range(start, periods=n, freq="1h")
    rng = np.random.default_rng(seed)
    steps = rng.normal(0.0, 0.003, n)
    for weekday, hour in drift_slots:
        mask = (dates.day_of_week == weekday) & (dates.hour >= hour) & (dates.hour < hour + 4)
        steps = steps + np.where(mask, 0.003, 0.0)
    closes = 100.0 * np.exp(np.cumsum(steps))
    opens = np.concatenate([[100.0], closes[:-1]])
    return pd.DataFrame(
        {
            "date": dates,
            "open": opens,
            "high": np.maximum(opens, closes) * 1.002,
            "low": np.minimum(opens, closes) * 0.998,
            "close": closes,
            "volume": np.ones(n),
        }
    )


def run(frame):
    strategy = Strategy()
    frame = strategy.populate_indicators(frame, {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


def flags(frame, column):
    return frame.get(column, pd.Series(0, index=frame.index)).fillna(0).astype(int)


class SameSlotPeriodicityTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.03)
        self.assertGreaterEqual(Strategy.startup_candle_count, 4368)
        self.assertEqual(Strategy.startup_candle_count, 4400)

    def test_signals_binary_and_at_selected_slot(self) -> None:
        frame = run(make_frame(6000))
        for column in ("enter_long", "exit_long"):
            self.assertTrue(set(frame[column].dropna().unique().tolist()).issubset({1}))
        entries = frame[flags(frame, "enter_long") == 1]
        exits = frame[flags(frame, "exit_long") == 1]
        self.assertGreater(len(entries), 0)
        # Monday block 3 (12:00-16:00): entry at the close of the 11:00 bar, exit at the close of the 15:00 bar.
        self.assertTrue((entries["date"].dt.day_of_week == 0).all())
        self.assertTrue((entries["date"].dt.hour == 11).all())
        self.assertTrue((exits["date"].dt.day_of_week == 0).all())
        self.assertTrue((exits["date"].dt.hour == 15).all())
        self.assertEqual(len(entries), len(exits))
        self.assertTrue((entries["slot_mean"] >= 0.004).all())
        self.assertTrue((entries["slot_t"] >= 1.5).all())
        # At most one entry per UTC day of trading.
        trade_day = (entries["date"] + pd.Timedelta(hours=1)).dt.floor("D")
        self.assertFalse(trade_day.duplicated().any())

    def test_block_zero_entry_on_previous_day_23h(self) -> None:
        frame = run(make_frame(6000, drift_slots=((2, 0),)))
        entries = frame[flags(frame, "enter_long") == 1]
        exits = frame[flags(frame, "exit_long") == 1]
        self.assertGreater(len(entries), 0)
        self.assertTrue((entries["date"].dt.day_of_week == 1).all())
        self.assertTrue((entries["date"].dt.hour == 23).all())
        self.assertTrue((exits["date"].dt.day_of_week == 2).all())
        self.assertTrue((exits["date"].dt.hour == 3).all())

    def test_collision_of_block5_exit_and_block0_entry(self) -> None:
        # Sunday block 5 and Monday block 0 both drift: Sunday 23:00 carries both the exit and the next entry.
        base = make_frame(6000, drift_slots=((6, 20), (0, 0)))
        frame = run(base.copy())
        sunday_23 = (frame["date"].dt.day_of_week == 6) & (frame["date"].dt.hour == 23)
        sunday_19 = (frame["date"].dt.day_of_week == 6) & (frame["date"].dt.hour == 19)
        active = frame.index[sunday_23 & (frame["slot_exit"] == 1)]
        self.assertGreater(len(active), 0)
        self.assertGreater(int(flags(frame, "enter_long")[sunday_19].sum()), 0)
        # Position still open: exit only, the new entry is skipped.
        self.assertTrue((flags(frame, "exit_long")[active] == 1).all())
        self.assertTrue((flags(frame, "enter_long")[active] == 0).all())

        # Stop hit during Sunday block 5: no position at 23:00, so the Monday entry is kept.
        row = int(active[-1])
        changed = base.copy()
        fill = changed.loc[row - 3, "open"]
        changed.loc[row - 2, "low"] = fill * 0.96
        frame2 = run(changed)
        self.assertEqual(int(flags(frame2, "enter_long")[row]), 1)
        self.assertEqual(int(flags(frame2, "exit_long")[row]), 0)

    def test_zero_volume_no_signal(self) -> None:
        frame = make_frame(6000)
        frame["volume"] = 0.0
        frame = run(frame)
        self.assertEqual(int(flags(frame, "enter_long").sum()), 0)
        self.assertEqual(int(flags(frame, "exit_long").sum()), 0)

        frame = run(make_frame(6000))
        entry_rows = frame.index[flags(frame, "enter_long") == 1]
        exit_rows = frame.index[flags(frame, "exit_long") == 1]
        changed = make_frame(6000)
        changed.loc[entry_rows[-1], "volume"] = 0.0
        changed.loc[exit_rows[0], "volume"] = 0.0
        changed = run(changed)
        self.assertEqual(int(flags(changed, "enter_long")[entry_rows[-1]]), 0)
        self.assertEqual(int(flags(changed, "exit_long")[exit_rows[0]]), 0)

    def test_nan_startup_no_signal(self) -> None:
        for start in (START, START + pd.Timedelta(hours=13)):
            frame = run(make_frame(6000, start=start))
            first_full_day = (start.floor("D") + pd.Timedelta(days=26 * 7))
            before = frame["date"] < first_full_day - pd.Timedelta(hours=1)
            self.assertTrue(frame.loc[frame["date"] < first_full_day, "slot_t"].isna().all())
            self.assertEqual(int(flags(frame, "enter_long")[before].sum()), 0)
            self.assertEqual(int(flags(frame, "exit_long")[frame["date"] < first_full_day].sum()), 0)
            self.assertEqual(int(flags(frame, "enter_long").iloc[: HISTORY_ROWS - 1].sum()), 0)

    def test_missing_bar_makes_slot_ineligible(self) -> None:
        # Drop the Monday 13:00 bar 10 weeks before the first trade day: that day's selection can not use block 3.
        frame = make_frame(6000)
        first_full_day = START + pd.Timedelta(days=26 * 7)
        gap = first_full_day - pd.Timedelta(days=7 * 10) + pd.Timedelta(hours=13)
        dropped = frame[frame["date"] != gap].reset_index(drop=True)
        result = run(dropped)
        day_rows = (result["date"] >= first_full_day) & (result["date"] < first_full_day + pd.Timedelta(days=1))
        self.assertTrue((result.loc[day_rows, "slot_block"] != 3).all())
        entry_11 = day_rows & (result["date"].dt.hour == 11)
        self.assertEqual(int(flags(result, "enter_long")[entry_11].sum()), 0)

    def test_no_lookahead(self) -> None:
        full = make_frame(6000)
        n = 5000
        short = run(full.iloc[:n].copy())
        long = run(full.copy())
        for column in ("enter_long", "exit_long"):
            np.testing.assert_array_equal(flags(short, column).to_numpy(), flags(long, column).to_numpy()[:n])
        cols = ["slot_entry", "slot_exit", "slot_block", "slot_mean", "slot_t"]
        pd.testing.assert_frame_equal(short[cols], long.loc[: n - 1, cols])


if __name__ == "__main__":
    unittest.main()
