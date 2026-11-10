import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

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

ROOT = Path(__file__).parents[2]


def load_strategy(filename, class_name):
    path = ROOT / "user_data" / "strategies" / "_archive" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Strat = load_strategy("SessionRangeJudasSweep_H096_v1.py", "SessionRangeJudasSweep_H096_v1")


class FakeTrade:
    def __init__(self, tag, open_rate, open_time):
        self.enter_tag = tag
        self.open_rate = open_rate
        self.open_date_utc = open_time


def make_frame(n_days=3, sweep=True):
    """Day 0 quiet; day 1 has a wide Asia range, then a sweep and reclaim at 07:00."""
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    rows = []
    for i in range(n_days * 96):
        t = start + timedelta(minutes=15 * i)
        day, minute = divmod(i, 96)
        o, h, l, c = 100.5, 100.6, 100.4, 100.5
        if day == 1:
            if minute == 4:
                h = 102.0
            if minute == 8:
                l = 100.0
            if sweep and minute == 28:  # 07:00 sweep + reclaim
                o, h, l, c = 100.5, 101.0, 98.9, 100.6
        rows.append(
            {"date": t, "open": o, "high": h, "low": l, "close": c, "volume": 10.0}
        )
    return pd.DataFrame(rows)


def run(strategy, frame):
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


class H096Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strat.INTERFACE_VERSION, 3)
        self.assertEqual(Strat.timeframe, "15m")
        self.assertFalse(Strat.can_short)
        self.assertEqual(Strat.minimal_roi, {"0": 100.0})
        self.assertLess(Strat.stoploss, 0)
        self.assertGreaterEqual(Strat.startup_candle_count, 96)

    def test_signal_and_binary(self):
        frame = run(Strat(), make_frame())
        rows = frame.index[frame["enter_long"] == 1].tolist()
        self.assertEqual(rows, [96 + 28])
        self.assertEqual(frame.loc[rows[0], "enter_tag"], "A|102.0000000000|98.9000000000")
        self.assertTrue(set(frame["enter_long"].dropna().unique()).issubset({1}))

    def test_no_sweep_no_signal(self):
        frame = run(Strat(), make_frame(sweep=False))
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)

    def test_zero_volume_no_signal(self):
        data = make_frame()
        data["volume"] = 0.0
        frame = run(Strat(), data)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)

    def test_zero_volume_on_signal_bar(self):
        data = make_frame()
        data.loc[96 + 28, "volume"] = 0.0
        frame = run(Strat(), data)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)

    def test_startup_rows_no_signal(self):
        # Signal in the first 96 rows (day 0 as the wide-range day) must be suppressed.
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        data = make_frame()
        data["date"] = [start + timedelta(minutes=15 * i) for i in range(len(data))]
        shifted = pd.concat([data.iloc[96:192], data.iloc[192:]]).reset_index(drop=True)
        shifted["date"] = [start + timedelta(minutes=15 * i) for i in range(len(shifted))]
        frame = run(Strat(), shifted)
        self.assertEqual(int(frame.iloc[:96]["enter_long"].fillna(0).sum()), 0)

    def test_nan_values_no_signal(self):
        data = make_frame()
        data.loc[96 + 5, "high"] = float("nan")
        frame = run(Strat(), data)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)

    def test_missing_range_bar_turns_setup_off(self):
        data = make_frame().drop(index=96 + 10).reset_index(drop=True)
        frame = run(Strat(), data)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self):
        full = make_frame(n_days=4)
        n = 96 + 40
        short = run(Strat(), full.iloc[:n].copy())
        long_ = run(Strat(), full)
        cols = ["judas_tag", "enter_long", "enter_tag"]
        pd.testing.assert_frame_equal(
            short[cols].reset_index(drop=True),
            long_.iloc[:n][cols].reset_index(drop=True),
            check_dtype=False,
        )

    def test_fill_checks(self):
        s = Strat()
        tag = "A|102.0|98.9"
        ok = s.confirm_trade_entry("X", "limit", 1, 100.6, "GTC", None, tag, "long")
        self.assertTrue(ok)
        # stop more than 3% away
        self.assertFalse(s.confirm_trade_entry("X", "limit", 1, 103.0, "GTC", None, tag, "long"))
        # target less than 1% above fill
        self.assertFalse(
            s.confirm_trade_entry("X", "limit", 1, 101.5, "GTC", None, "A|102.0|99.9", "long")
        )

    def test_stop_is_frozen_below_entry(self):
        s = Strat()
        t0 = datetime(2025, 1, 2, 7, 15, tzinfo=timezone.utc)
        trade = FakeTrade("A|102.0|98.9", 100.6, t0)
        sp = min(0.998 * 98.9, 0.99 * 100.6)
        for rate in (100.6, 101.5):
            val = s.custom_stoploss("X", trade, t0, rate, 0.0)
            self.assertAlmostEqual(rate * (1 - val), sp, places=6)

    def test_take_profit_and_time_exit(self):
        s = Strat()
        t0 = datetime(2025, 1, 2, 7, 15, tzinfo=timezone.utc)
        trade = FakeTrade("A|102.0|98.9", 100.6, t0)
        self.assertEqual(
            s.custom_exit("X", trade, t0 + timedelta(hours=1), 102.0, 0.01), "take_profit_rh"
        )
        self.assertIsNone(
            s.custom_exit("X", trade, datetime(2025, 1, 2, 14, 45, tzinfo=timezone.utc), 101.0, 0.0)
        )
        self.assertEqual(
            s.custom_exit("X", trade, datetime(2025, 1, 2, 15, 0, tzinfo=timezone.utc), 101.0, 0.0),
            "time_exit",
        )
        t1 = datetime(2025, 1, 2, 13, 45, tzinfo=timezone.utc)
        trade_l = FakeTrade("L|102.0|98.9", 100.6, t1)
        self.assertIsNone(
            s.custom_exit("X", trade_l, datetime(2025, 1, 2, 20, 45, tzinfo=timezone.utc), 101.0, 0.0)
        )
        self.assertEqual(
            s.custom_exit("X", trade_l, datetime(2025, 1, 2, 21, 0, tzinfo=timezone.utc), 101.0, 0.0),
            "time_exit",
        )


if __name__ == "__main__":
    unittest.main()
