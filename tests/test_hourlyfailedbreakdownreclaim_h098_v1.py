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
talib_abstract.SMA = lambda dataframe, timeperiod: dataframe["close"].rolling(timeperiod).mean()
talib_abstract.RSI = lambda dataframe, timeperiod: pd.Series(50.0, index=dataframe.index)
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)

ROOT = Path(__file__).parents[1]
CLASS_NAME = "HourlyFailedBreakdownReclaim_H098_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / (CLASS_NAME + ".py")
    spec = importlib.util.spec_from_file_location(CLASS_NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, CLASS_NAME)


Strategy = load_strategy()
START = datetime(2024, 1, 1, tzinfo=timezone.utc)


def make_frame(blocks):
    """blocks: list of (open, high, low, close) per 4h block, 16 bars each."""
    rows = []
    for b, (o, h, l, c) in enumerate(blocks):
        for i in range(16):
            t = START + timedelta(hours=4 * b, minutes=15 * i)
            if i == 0:
                bo, bc = o, o
            else:
                bo, bc = o, o
            bh, bl = o, o
            if i == 5:
                bh = h
            if i == 6:
                bl = l
            if i == 15:
                bc = c
                bh = max(bh, c)
                bl = min(bl, c)
            rows.append(
                {"date": t, "open": bo, "high": max(bh, bo, bc), "low": min(bl, bo, bc),
                 "close": bc, "volume": 1.0}
            )
    return pd.DataFrame(rows)


def setup_blocks():
    flat = [(100.0, 100.5, 99.5, 100.0)] * 10
    c1 = (101.0, 102.0, 100.0, 101.0)  # range 2%, mid 101
    c2 = (100.5, 101.0, 99.0, 100.5)  # sweeps low, closes inside below mid
    return flat + [c1, c2, (100.5, 100.8, 100.2, 100.5)]


def run(frame):
    s = Strategy()
    frame = s.populate_indicators(frame.copy(), {})
    frame = s.populate_entry_trend(frame, {})
    return s.populate_exit_trend(frame, {})


class FakeDP:
    def __init__(self, frame):
        self.frame = frame

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.frame, None


class Trade:
    def __init__(self, open_date, open_rate):
        self.open_date_utc = open_date
        self.open_rate = open_rate


class H098Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 64)

    def test_signal_on_setup_at_16th_bar_only(self):
        out = run(make_frame(setup_blocks()))
        idx = out.index[out["enter_long"] == 1].tolist()
        self.assertEqual(idx, [12 * 16 - 1])
        self.assertTrue(set(out["enter_long"].dropna().unique()).issubset({1}))
        self.assertAlmostEqual(out.loc[idx[0], "crt_sp"], min(99.0, 0.992 * 100.5))

    def test_failed_conditions_give_no_signal(self):
        blocks = setup_blocks()
        blocks[11] = (100.5, 102.5, 99.0, 100.5)  # takes H1
        self.assertEqual(run(make_frame(blocks))["enter_long"].fillna(0).sum(), 0)
        blocks = setup_blocks()
        blocks[11] = (100.5, 101.0, 99.0, 101.5)  # close above mid
        self.assertEqual(run(make_frame(blocks))["enter_long"].fillna(0).sum(), 0)
        blocks = setup_blocks()
        blocks[10] = (100.5, 101.2, 100.0, 101.0)  # range 1.2% < 1.5%
        self.assertEqual(run(make_frame(blocks))["enter_long"].fillna(0).sum(), 0)

    def test_missing_bar_makes_block_unusable(self):
        frame = make_frame(setup_blocks())
        frame = frame.drop(index=[10 * 16 + 3]).reset_index(drop=True)
        self.assertEqual(run(frame)["enter_long"].fillna(0).sum(), 0)

    def test_zero_volume_no_signal(self):
        frame = make_frame(setup_blocks())
        frame["volume"] = 0.0
        out = run(frame)
        self.assertEqual(out["enter_long"].fillna(0).sum(), 0)
        self.assertNotIn("exit_long", out.columns)

    def test_startup_nan_no_signal(self):
        out = run(make_frame(setup_blocks()))
        self.assertEqual(out.iloc[:64]["enter_long"].fillna(0).sum(), 0)
        short = run(make_frame(setup_blocks()[:1]))
        self.assertEqual(short.get("enter_long", pd.Series(dtype=float)).fillna(0).sum(), 0)

    def test_no_lookahead(self):
        full = make_frame(setup_blocks() + setup_blocks())
        n = 12 * 16 + 5  # cut mid-block
        a = run(full.iloc[:n])
        b = run(full)
        cols = [c for c in a.columns if c not in {"date", "open", "high", "low", "close", "volume"}]
        pd.testing.assert_frame_equal(a[cols], b.iloc[:n][cols], check_dtype=False)

    def test_exits_and_stop(self):
        out = run(make_frame(setup_blocks()))
        s = Strategy()
        s.dp = FakeDP(out)
        open_time = out.loc[12 * 16, "date"]
        trade = Trade(open_time, 100.5)
        # target H1 = 102
        self.assertEqual(
            s.custom_exit("X", trade, open_time + timedelta(hours=1), 102.0, 0.015),
            "crt_target_h1",
        )
        self.assertIsNone(
            s.custom_exit("X", trade, open_time + timedelta(hours=1), 101.0, 0.005)
        )
        self.assertEqual(
            s.custom_exit("X", trade, open_time + timedelta(hours=12), 100.0, 0.0),
            "crt_time_exit_12h",
        )
        self.assertIsNone(
            s.custom_exit("X", trade, open_time + timedelta(hours=11, minutes=45), 100.0, 0.0)
        )
        # stop at SP = min(99, 99.696) = 99
        v = s.custom_stoploss("X", trade, open_time, 100.5, 0.0)
        self.assertAlmostEqual(100.5 * (1 + v), 99.0)
        # fill checks
        self.assertTrue(s.confirm_trade_entry("X", "limit", 1, 100.5, "GTC", open_time, None, "long"))
        self.assertFalse(s.confirm_trade_entry("X", "limit", 1, 102.5, "GTC", open_time, None, "long"))
        self.assertFalse(s.confirm_trade_entry("X", "limit", 1, 98.5, "GTC", open_time, None, "long"))


if __name__ == "__main__":
    unittest.main()
