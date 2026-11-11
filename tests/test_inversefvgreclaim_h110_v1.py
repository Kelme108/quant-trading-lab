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
NAME = "InverseFVGReclaim_H110_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load()
Strategy = getattr(MODULE, NAME)

# bar = (open, high, low, close)
FLAT = (100.0, 100.2, 99.8, 100.0)
PATTERN = [
    FLAT,                          # k-2: gap top GT = 99.8
    (100.0, 100.0, 98.4, 98.5),    # k-1: down displacement, body 1.52%
    (98.5, 99.0, 98.2, 98.4),      # k: high 99.0 < 99.8, gap 0.81%
    (98.4, 98.7, 98.3, 98.6),      # no close above GT
    (98.6, 100.3, 98.5, 100.2),    # t: bullish close above GT; SL = 98.2, R = 2.0
]
TAIL = (100.2, 100.4, 100.0, 100.2)
PATTERN_START = 40
SIGNAL_INDEX = PATTERN_START + 4


def make_frame(bars, volume=1.0):
    frame = pd.DataFrame(bars, columns=["open", "high", "low", "close"], dtype=float)
    frame["volume"] = volume
    return frame


def base_bars(pattern=PATTERN, tail=20):
    return [FLAT] * PATTERN_START + list(pattern) + [TAIL] * tail


def entries(frame):
    return frame["enter_long"] if "enter_long" in frame else pd.Series(0, index=frame.index)


def run(frame):
    strategy = Strategy()
    frame = strategy.populate_indicators(frame, {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


class FakeTrade:
    def __init__(self, tag, opened, pair="BTC/USDT"):
        self.enter_tag = tag
        self.open_date_utc = opened
        self.pair = pair


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


class InverseFVGReclaimTests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.035)
        self.assertGreaterEqual(Strategy.startup_candle_count, 30)

    def test_signal_on_first_close_above_gap(self):
        frame = run(make_frame(base_bars()))
        self.assertEqual(frame.index[entries(frame) == 1].tolist(), [SIGNAL_INDEX])
        row = frame.loc[SIGNAL_INDEX]
        self.assertAlmostEqual(row["ifvg_sl"], 98.2)
        self.assertAlmostEqual(row["ifvg_tp"], 100.2 + 1.5 * 2.0)
        sl, tp = MODULE.parse_tag(row["enter_tag"])
        self.assertAlmostEqual(sl, 98.2)
        self.assertAlmostEqual(tp, 103.2)

    def test_signal_columns_are_binary(self):
        rng = np.random.default_rng(1)
        close = 100 + np.cumsum(rng.normal(0, 0.5, 400))
        frame = pd.DataFrame(
            {"open": close, "high": close * 1.004, "low": close * 0.996, "close": close, "volume": 1.0}
        )
        frame = run(frame)
        if "enter_long" in frame:
            self.assertTrue(set(frame["enter_long"].dropna().unique().tolist()).issubset({1}))
        frame = run(make_frame(base_bars()))
        self.assertEqual(set(frame["enter_long"].dropna().unique().tolist()), {1})
        if "exit_long" in frame:
            self.assertTrue(set(frame["exit_long"].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_candle_gives_no_signal(self):
        frame = make_frame(base_bars())
        frame.loc[SIGNAL_INDEX, "volume"] = 0.0
        frame = run(frame)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        frame = make_frame(base_bars(), volume=0.0)
        frame = run(frame)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_undefined_values_give_no_signal(self):
        frame = make_frame(base_bars())
        frame.loc[SIGNAL_INDEX, "close"] = np.nan
        frame = run(frame)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        frame = make_frame(base_bars())
        frame.loc[PATTERN_START, "low"] = np.nan  # k-2 undefined, no gap
        frame = run(frame)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_startup_rows_give_no_signal(self):
        frame = run(make_frame(base_bars()))
        startup = Strategy.startup_candle_count
        self.assertEqual(int(entries(frame).iloc[:startup].fillna(0).sum()), 0)
        nan_frame = pd.DataFrame(
            {c: [np.nan] * 60 for c in ["open", "high", "low", "close"]}
        )
        nan_frame["volume"] = 1.0
        nan_frame = run(nan_frame)
        self.assertEqual(int(nan_frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_no_lookahead(self):
        rng = np.random.default_rng(7)
        bars = base_bars(tail=5)
        n = len(bars)
        extra = []
        price = 100.2
        for _ in range(80):
            price *= 1 + rng.normal(0, 0.01)
            extra.append((price, price * 1.006, price * 0.994, price * (1 + rng.normal(0, 0.004))))
        short = run(make_frame(bars))
        long_ = run(make_frame(bars + extra))
        cols = ["ifvg_signal", "ifvg_sl", "ifvg_tp", "enter_long", "enter_tag"]
        pd.testing.assert_frame_equal(
            short.loc[: n - 1, cols].reset_index(drop=True),
            long_.loc[: n - 1, cols].reset_index(drop=True),
            check_dtype=False,
        )

    def test_gap_expires_after_24_bars(self):
        # k is the 3rd pattern bar; bars k+1..k+24 stay below GT, bar k+25 closes above it
        k = PATTERN_START + 2
        quiet = (98.5, 98.7, 98.3, 98.5)
        bars = [FLAT] * PATTERN_START + PATTERN[:3] + [quiet] * 24 + [PATTERN[4]] + [TAIL] * 5
        frame = run(make_frame(bars))
        self.assertEqual(int(entries(frame).fillna(0).sum()), 0)
        # the same bar at k+24 still qualifies
        bars = [FLAT] * PATTERN_START + PATTERN[:3] + [quiet] * 23 + [PATTERN[4]] + [TAIL] * 5
        frame = run(make_frame(bars))
        self.assertEqual(frame.index[entries(frame) == 1].tolist(), [k + 24])

    def test_wick_above_gap_does_not_count_and_gap_is_consumed_once(self):
        wick = (98.4, 100.0, 98.3, 98.6)  # high above GT, close below
        bearish_close = (100.3, 100.4, 99.9, 99.95)  # close above GT but bearish bar
        pattern = PATTERN[:3] + [wick, bearish_close, PATTERN[4], (100.2, 100.5, 100.0, 100.4)]
        frame = run(make_frame(base_bars(pattern)))
        self.assertEqual(frame.index[entries(frame) == 1].tolist(), [PATTERN_START + 5])

    def test_risk_filter_skips_and_drops_gap(self):
        # swing low far below: R/close > 3% -> skip, and the gap is dropped (no later entry)
        deep = (98.5, 99.0, 96.0, 98.4)
        pattern = [PATTERN[0], PATTERN[1], deep, PATTERN[3], PATTERN[4], (100.2, 100.5, 100.0, 100.4)]
        frame = run(make_frame(base_bars(pattern)))
        self.assertEqual(int(entries(frame).fillna(0).sum()), 0)
        # tiny risk (< 0.8%): swing low too close to the close
        head = [
            FLAT,                            # k-2: GT = 99.8
            (102.0, 102.0, 100.9, 100.9),    # k-1: body 1.09%
            (99.35, 99.4, 99.3, 99.35),      # k: gap (99.8-99.4)/99.4 = 0.40%; swing low 99.3
        ]
        small_risk = head + [(99.35, 99.95, 99.3, 99.9)]  # R = 0.6 -> 0.60% < 0.8%
        frame = run(make_frame(base_bars(small_risk)))
        self.assertEqual(int(entries(frame).fillna(0).sum()), 0)
        ok_risk = head + [(99.35, 100.3, 99.3, 100.2)]    # R = 0.9 -> 0.90%
        frame = run(make_frame(base_bars(ok_risk)))
        self.assertEqual(frame.index[entries(frame) == 1].tolist(), [PATTERN_START + 3])
        self.assertAlmostEqual(frame.loc[PATTERN_START + 3, "ifvg_sl"], 99.3)

    def test_small_gap_and_small_body_are_rejected(self):
        small_gap = [FLAT, (100.0, 100.0, 98.4, 98.5), (98.5, 99.75, 98.2, 98.4), PATTERN[4]]
        # gap (99.8-99.75)/99.75 = 0.05% < 0.4%
        frame = run(make_frame(base_bars(small_gap)))
        self.assertEqual(int(entries(frame).fillna(0).sum()), 0)
        small_body = [FLAT, (100.0, 100.0, 98.4, 99.5), PATTERN[2], PATTERN[4]]  # body 0.5%
        frame = run(make_frame(base_bars(small_body)))
        self.assertEqual(int(entries(frame).fillna(0).sum()), 0)

    def test_new_valid_gap_replaces_the_old_one(self):
        # Second gap forms while the first is open; the signal uses the second gap's top (lower GT)
        pattern = [
            FLAT,
            (100.0, 100.0, 98.4, 98.5),
            (98.5, 99.0, 98.2, 98.4),       # gap 1: GT = 99.8
            (98.4, 98.5, 97.0, 97.1),       # k-1 of gap 2: down body 1.3%
            (97.1, 97.4, 96.9, 97.2),       # high 97.4 < low(k-2)=98.2: gap 2, GT = 98.2
            (97.2, 99.0, 97.1, 98.9),       # closes above 98.2 (gap 2) but below 99.8 (gap 1)
        ]
        frame = run(make_frame(base_bars(pattern)))
        self.assertEqual(frame.index[entries(frame) == 1].tolist(), [PATTERN_START + 5])
        self.assertAlmostEqual(frame.loc[PATTERN_START + 5, "ifvg_sl"], 96.9)

    def test_confirm_trade_entry(self):
        strategy = Strategy()
        tag = MODULE.make_tag(98.2, 103.2)
        now = utc(2026, 1, 5, 10, 0)
        trades = [FakeTrade(tag, utc(2026, 1, 5, h)) for h in (0, 3)]
        persistence = types.ModuleType("freqtrade.persistence")
        persistence.Trade = type(
            "Trade", (), {"get_trades_proxy": staticmethod(lambda **k: list(trades))}
        )
        with mock.patch.dict(sys.modules, {"freqtrade.persistence": persistence}):
            args = ("BTC/USDT", "limit", 1.0)
            kw = dict(time_in_force="GTC", current_time=now, side="long")
            self.assertTrue(strategy.confirm_trade_entry(*args, rate=100.0, entry_tag=tag, **kw))
            self.assertFalse(strategy.confirm_trade_entry(*args, rate=98.2, entry_tag=tag, **kw))
            self.assertFalse(strategy.confirm_trade_entry(*args, rate=97.0, entry_tag=tag, **kw))
            self.assertFalse(strategy.confirm_trade_entry(*args, rate=100.0, entry_tag="other", **kw))
            trades.append(FakeTrade(tag, utc(2026, 1, 5, 6)))
            self.assertFalse(strategy.confirm_trade_entry(*args, rate=100.0, entry_tag=tag, **kw))
            trades[:] = [FakeTrade(tag, utc(2026, 1, 4, h)) for h in (1, 2, 3)]
            self.assertTrue(strategy.confirm_trade_entry(*args, rate=100.0, entry_tag=tag, **kw))

    def test_stop_is_fixed_price_sl(self):
        strategy = Strategy()
        trade = FakeTrade(MODULE.make_tag(98.2, 103.2), utc(2026, 1, 5, 10, 0))
        for rate in (100.0, 101.5, 99.0):
            value = strategy.custom_stoploss("BTC/USDT", trade, utc(2026, 1, 5, 11), rate, 0.0)
            self.assertLess(value, 0)
            self.assertAlmostEqual(rate * (1 + value), 98.2)
        self.assertIsNone(
            strategy.custom_stoploss("BTC/USDT", FakeTrade("x", utc(2026, 1, 5)), utc(2026, 1, 5), 100.0, 0.0)
        )

    def test_take_profit_and_time_exit(self):
        strategy = Strategy()
        opened = utc(2026, 1, 5, 10, 0)
        trade = FakeTrade(MODULE.make_tag(98.2, 103.2), opened)
        now = opened + timedelta(minutes=30)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, now, 103.19, 0.03))
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade, now, 103.2, 0.03), "take_profit_1_5R"
        )
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade, now, 104.0, 0.04), "take_profit_1_5R"
        )
        self.assertIsNone(
            strategy.custom_exit("BTC/USDT", trade, opened + timedelta(minutes=47 * 15), 100.0, 0.0)
        )
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade, opened + timedelta(hours=12), 100.0, 0.0),
            "time_exit_12h",
        )


if __name__ == "__main__":
    unittest.main()
