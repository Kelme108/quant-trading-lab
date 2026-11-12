import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

freqtrade = types.ModuleType("freqtrade")
strategy_module = types.ModuleType("freqtrade.strategy")
strategy_module.IStrategy = object
strategy_module.merge_informative_pair = lambda *a, **k: a[0]
persistence = types.ModuleType("freqtrade.persistence")
persistence.Trade = type("Trade", (), {"get_trades_proxy": staticmethod(lambda **k: [])})
freqtrade.strategy = strategy_module
freqtrade.persistence = persistence
sys.modules.setdefault("freqtrade", freqtrade)
sys.modules.setdefault("freqtrade.strategy", strategy_module)
sys.modules.setdefault("freqtrade.persistence", persistence)
talib = types.ModuleType("talib")
talib_abstract = types.ModuleType("talib.abstract")
talib_abstract.SMA = lambda dataframe, timeperiod: dataframe["close"].rolling(timeperiod).mean()
talib_abstract.RSI = lambda dataframe, timeperiod: pd.Series(50.0, index=dataframe.index)
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)

ROOT = Path(__file__).parents[1]
NAME = "MomentumPinballSession_H123_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load()
Strategy = getattr(MODULE, NAME)

START = "2024-01-01 00:00"
# Steady +1 per block, a sharp drop at block 30 (LBR(30) = 0), flat afterwards.
LEVELS = [100.0 + k for k in range(30)] + [119.0] * 12
ARMED_BLOCK = 31


def build(levels=None, breakouts=None, wide=True, volume=1.0):
    """15m bars; every bar of block k closes at levels[k] except the listed breakout bars.

    breakouts: {(block, bar_number): multiplier of the block level}.
    """
    levels = LEVELS if levels is None else levels
    count = 16 * len(levels)
    close = np.repeat(np.asarray(levels, dtype=float), 16)
    for (block, bar), multiplier in (breakouts or {}).items():
        close[block * 16 + bar - 1] = levels[block] * multiplier
    open_ = np.concatenate([[close[0]], close[:-1]])
    span = 0.003 if wide else 0.0005
    return pd.DataFrame(
        {
            "date": pd.date_range(START, periods=count, freq="15min", tz="UTC"),
            "open": open_,
            "high": np.maximum(open_, close) * (1 + span),
            "low": np.minimum(open_, close) * (1 - span),
            "close": close,
            "volume": np.full(count, float(volume)),
        }
    )


def run(frame):
    strategy = Strategy()
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    return frame


def signal_rows(frame):
    if "enter_long" not in frame:
        return []
    return frame.index[frame["enter_long"] == 1].tolist()


class FakeDp:
    def __init__(self, frame):
        self.frame = frame

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.frame, None


class FakeTrade:
    def __init__(self, open_date, open_rate, tag):
        self.open_date_utc = open_date
        self.open_rate = open_rate
        self.enter_tag = tag


class MomentumPinballTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.05)
        self.assertTrue(Strategy.use_custom_stoploss)
        self.assertGreaterEqual(Strategy.startup_candle_count, 1600)

    def test_lbr_values(self):
        index = pd.date_range(START, periods=32, freq=timedelta(hours=4), tz="UTC")
        closes = pd.Series([100.0 + k for k in range(30)] + [119.0, 119.0], index=index)
        lbr = MODULE.lbr_series(closes)
        self.assertTrue(lbr.iloc[:2].isna().all())  # x and its change are undefined first
        self.assertEqual(lbr.iloc[2], 100.0)  # avgDown = 0 -> 100
        self.assertEqual(lbr.iloc[29], 100.0)
        self.assertAlmostEqual(lbr.iloc[30], 0.0)  # sharp drop: only down moves
        self.assertAlmostEqual(lbr.iloc[31], 100 - 100 / (1 + (10 / 3) / (11 / 3 * 2 / 3)))

    def test_signal_on_first_breakout_bar_only(self):
        frame = run(build(breakouts={(ARMED_BLOCK, 7): 1.01, (ARMED_BLOCK, 9): 1.01}))
        self.assertEqual(signal_rows(frame), [ARMED_BLOCK * 16 + 6])
        row = frame.loc[ARMED_BLOCK * 16 + 6]
        self.assertTrue(row["enter_tag"].startswith("pinball_orl|"))
        self.assertAlmostEqual(MODULE.parse_tag(row["enter_tag"]), 119.0 * 0.997)
        self.assertAlmostEqual(row["or_high"], 119.0 * 1.003)

    def test_entry_window_is_bars_5_to_12(self):
        for bar, expected in [(4, False), (5, True), (12, True), (13, False), (16, False)]:
            frame = run(build(breakouts={(ARMED_BLOCK, bar): 1.01}))
            self.assertEqual(bool(signal_rows(frame)), expected, bar)

    def test_not_armed_when_lbr_not_below_30(self):
        # Block 32 follows block 31, where LBR(31) is about 57.
        frame = run(build(breakouts={(32, 7): 1.01}))
        self.assertEqual(signal_rows(frame), [])
        # Block 29 follows a steady block (LBR = 100).
        frame = run(build(breakouts={(29, 7): 1.01}))
        self.assertEqual(signal_rows(frame), [])

    def test_atr_filter(self):
        frame = run(build(breakouts={(ARMED_BLOCK, 7): 1.01}, wide=False))
        self.assertLess(frame.loc[ARMED_BLOCK * 16 + 6, "atr_pct"], 0.004)
        self.assertEqual(signal_rows(frame), [])

    def test_lbr_is_the_previous_blocks_value(self):
        frame = run(build())
        first_bar = lambda block: block * 16
        for block in (0, 1, 2):
            self.assertTrue(np.isnan(frame.loc[first_bar(block), "lbr_prev"]))
        self.assertFalse(np.isnan(frame.loc[first_bar(3), "lbr_prev"]))
        # LBR(30) = 0 applies to every bar of block 31 and to none of block 30.
        block_31 = frame.loc[31 * 16 : 31 * 16 + 15, "lbr_prev"]
        self.assertTrue((block_31 == block_31.iloc[0]).all())
        self.assertAlmostEqual(block_31.iloc[0], 0.0)
        self.assertEqual(frame.loc[30 * 16, "lbr_prev"], 100.0)

    def test_opening_range_hidden_before_bar_5(self):
        frame = run(build())
        for bar in range(1, 5):
            self.assertTrue(np.isnan(frame.loc[ARMED_BLOCK * 16 + bar - 1, "or_high"]))
        self.assertFalse(np.isnan(frame.loc[ARMED_BLOCK * 16 + 4, "or_high"]))

    def test_undefined_startup_values_give_no_signal(self):
        # Early drop: block 1 -> x(1) is the first x; LBR is undefined until block 2.
        levels = [100.0, 90.0, 90.0, 90.0, 90.0, 90.0]
        frame = run(build(levels=levels, breakouts={(2, 7): 1.01, (1, 7): 1.01}))
        self.assertEqual(signal_rows(frame), [])
        self.assertTrue(frame["lbr_prev"].iloc[:32].isna().all())
        # Drop at block 2 makes LBR(2) defined (0): block 3 is armed.
        levels = [100.0, 101.0, 90.0, 90.0, 90.0]
        frame = run(build(levels=levels, breakouts={(3, 7): 1.01}))
        self.assertEqual(signal_rows(frame), [3 * 16 + 6])

    def test_incomplete_opening_range_gives_no_signal(self):
        frame = build(breakouts={(ARMED_BLOCK, 7): 1.01})
        frame = frame.drop(index=ARMED_BLOCK * 16 + 1).reset_index(drop=True)
        frame = run(frame)
        self.assertEqual(signal_rows(frame), [])

    def test_zero_volume_gives_no_signal(self):
        frame = run(build(breakouts={(ARMED_BLOCK, 7): 1.01}, volume=0.0))
        self.assertEqual(signal_rows(frame), [])
        self.assertNotIn("exit_long", frame)
        single = build(breakouts={(ARMED_BLOCK, 7): 1.01})
        single.loc[ARMED_BLOCK * 16 + 6, "volume"] = 0.0
        self.assertEqual(signal_rows(run(single)), [])

    def test_signal_columns_are_binary(self):
        frame = run(build(breakouts={(ARMED_BLOCK, 7): 1.01}))
        for column in ("enter_long", "exit_long"):
            if column in frame:
                self.assertTrue(set(frame[column].dropna().unique().tolist()).issubset({1}))

    def test_signals_do_not_change_when_future_candles_are_appended(self):
        rng = np.random.default_rng(7)
        levels = list(LEVELS) + list(119.0 + np.cumsum(rng.normal(0, 3, 30)))
        full = build(levels=levels, breakouts={(ARMED_BLOCK, 7): 1.01, (40, 6): 1.02, (50, 8): 1.03})
        # Cut inside the armed block (bar 10) so that the future would reach the opening range's block.
        n = ARMED_BLOCK * 16 + 9
        before = run(full.iloc[:n])
        after = run(full)
        columns = ["bar_no", "lbr_prev", "or_high", "or_low", "atr", "atr_pct"]
        pd.testing.assert_frame_equal(before[columns], after.loc[: n - 1, columns], check_dtype=False)
        self.assertEqual(signal_rows(before), [r for r in signal_rows(after) if r < n])
        self.assertEqual(
            before["enter_tag"].dropna().tolist(), after.loc[: n - 1, "enter_tag"].dropna().tolist()
        )
        # Cut before the signal bar and then after it: earlier rows are unchanged either way.
        for cut in (ARMED_BLOCK * 16 + 5, ARMED_BLOCK * 16 + 7, 41 * 16 + 3):
            part = run(full.iloc[:cut])
            pd.testing.assert_frame_equal(part[columns], after.loc[: cut - 1, columns], check_dtype=False)

    def test_confirm_trade_entry_one_per_block(self):
        strategy = Strategy()
        tag = "pinball_orl|118.0"
        when = datetime(2024, 1, 2, 10, 15, tzinfo=timezone.utc)  # block 08:00-12:00

        def trades(*opens):
            fake = types.ModuleType("freqtrade.persistence")
            items = [FakeTrade(o, 100.0, tag) for o in opens]
            fake.Trade = type("Trade", (), {"get_trades_proxy": staticmethod(lambda **k: items)})
            return {"freqtrade.persistence": fake}

        args = ("BTC/USDT", "limit", 1.0, 100.0, "GTC", when, tag, "long")
        with mock.patch.dict(sys.modules, trades()):
            self.assertTrue(strategy.confirm_trade_entry(*args))
        with mock.patch.dict(sys.modules, trades(datetime(2024, 1, 2, 8, 30, tzinfo=timezone.utc))):
            self.assertFalse(strategy.confirm_trade_entry(*args))
        with mock.patch.dict(sys.modules, trades(datetime(2024, 1, 2, 7, 45, tzinfo=timezone.utc))):
            self.assertTrue(strategy.confirm_trade_entry(*args))
        with mock.patch.dict(sys.modules, trades()):
            self.assertFalse(
                strategy.confirm_trade_entry("BTC/USDT", "limit", 1.0, 100.0, "GTC", when, "other", "long")
            )

    def test_custom_stoploss(self):
        strategy = Strategy()
        now = datetime(2024, 1, 2, 10, tzinfo=timezone.utc)
        trade = FakeTrade(now, 100.0, "pinball_orl|98.5")  # S = min(98.5, 99) = 98.5
        self.assertAlmostEqual(strategy.custom_stoploss("P", trade, now, 100.0, 0.0), 98.5 / 100 - 1)
        # Same absolute price when the rate has moved.
        self.assertAlmostEqual(100.5 * (1 + strategy.custom_stoploss("P", trade, now, 100.5, 0.0)), 98.5)
        # ORL above 0.99 * E: stop is 0.99 * E.
        trade = FakeTrade(now, 100.0, "pinball_orl|99.7")
        self.assertAlmostEqual(strategy.custom_stoploss("P", trade, now, 100.0, 0.0), -0.01)
        # Very low ORL: capped at the 5% backstop.
        trade = FakeTrade(now, 100.0, "pinball_orl|80.0")
        self.assertAlmostEqual(strategy.custom_stoploss("P", trade, now, 100.0, 0.0), -0.05)
        self.assertIsNone(strategy.custom_stoploss("P", FakeTrade(now, 100.0, "x"), now, 100.0, 0.0))
        # Rate already at/below the stop: triggers at once.
        trade = FakeTrade(now, 100.0, "pinball_orl|98.5")
        self.assertLess(strategy.custom_stoploss("P", trade, now, 98.0, -0.02), 0)

    def exit_setup(self, entry_bar, bars):
        """Strategy with a dp serving flat 15m bars from the block start, entering at entry_bar."""
        block_start = datetime(2024, 1, 2, 8, 0, tzinfo=timezone.utc)
        dates = pd.date_range(block_start, periods=bars, freq="15min", tz="UTC")
        frame = pd.DataFrame(
            {
                "date": dates,
                "open": 100.0,
                "high": 100.2,
                "low": 99.8,
                "close": 100.0,
                "volume": 1.0,
            }
        )
        strategy = Strategy()
        strategy.dp = FakeDp(frame)
        entry = block_start + timedelta(minutes=15 * (entry_bar - 1))
        return strategy, frame, FakeTrade(entry, 100.0, "pinball_orl|98.0"), block_start

    def test_take_profit_exit(self):
        strategy, frame, trade, start = self.exit_setup(7, 30)
        now = start + timedelta(hours=1, minutes=45)  # bar 8 opens; flat bars so far
        self.assertIsNone(strategy.custom_exit("P", trade, now, 100.0, 0.0))
        self.assertIsNone(strategy.custom_exit("P", trade, now, 101.4, 0.013))
        self.assertEqual(strategy.custom_exit("P", trade, now, 101.5, 0.0135), "take_profit")
        self.assertEqual(strategy.custom_exit("P", trade, now, 102.0, 0.02), "take_profit")
        # A closed bar since entry whose high touched E * 1.015 also triggers it.
        frame.loc[6, "high"] = 101.5  # bar 7 (entry bar)
        self.assertEqual(strategy.custom_exit("P", trade, now, 100.0, 0.0), "take_profit")
        # A high on a bar that is still open at `now` is not used.
        strategy2, frame2, trade2, start2 = self.exit_setup(7, 30)
        frame2.loc[7, "high"] = 105.0  # bar 8 opens at `now`: not closed yet
        self.assertIsNone(strategy2.custom_exit("P", trade2, now, 100.0, 0.0))
        # A high before the entry bar is not used.
        strategy3, frame3, trade3, _ = self.exit_setup(7, 30)
        frame3.loc[2, "high"] = 105.0
        self.assertIsNone(strategy3.custom_exit("P", trade3, now, 100.0, 0.0))

    def test_block_end_loser_exit(self):
        strategy, frame, trade, start = self.exit_setup(7, 40)
        before_block_end = start + timedelta(hours=3, minutes=45)
        block_end = start + timedelta(hours=4)
        frame.loc[15, "close"] = 99.9  # bar 16 closes below E = 100
        self.assertIsNone(strategy.custom_exit("P", trade, before_block_end, 99.9, -0.001))
        self.assertEqual(strategy.custom_exit("P", trade, block_end, 99.9, -0.001), "block_end_loser")
        # Winner at the block end is carried.
        frame.loc[15, "close"] = 100.4
        self.assertIsNone(strategy.custom_exit("P", trade, block_end, 100.4, 0.004))
        # Even if the current rate later falls, only bar 16's close decides this exit.
        self.assertIsNone(strategy.custom_exit("P", trade, block_end + timedelta(hours=1), 99.0, -0.01))

    def test_time_exit_after_48_bars(self):
        strategy, frame, trade, start = self.exit_setup(7, 100)
        entry = start + timedelta(minutes=15 * 6)
        frame["close"] = 100.5  # winners are carried past the block end
        self.assertIsNone(strategy.custom_exit("P", trade, entry + timedelta(hours=11, minutes=45), 100.5, 0.005))
        self.assertEqual(
            strategy.custom_exit("P", trade, entry + timedelta(hours=12), 100.5, 0.005), "time_exit_12h"
        )
        self.assertEqual(
            strategy.custom_exit("P", trade, entry + timedelta(hours=13), 100.5, 0.005), "time_exit_12h"
        )


if __name__ == "__main__":
    unittest.main()
