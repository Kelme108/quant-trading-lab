import importlib.util
import sys
import types
import unittest
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

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


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / "_archive" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Strategy = load_strategy(
    "SessionVWAPFirstPullback_H095_v1.py", "SessionVWAPFirstPullback_H095_v1"
)

T_INDEX_IN_DAY = 10  # signal candle t (bar 11 of session A)


def build_frame(history_days: int = 15, tail_bars: int = 60) -> pd.DataFrame:
    """Flat history, then a session-A opening drive, VWAP pullback and trigger."""
    n_hist = history_days * 96
    rows = [(100.0, 100.1, 99.9, 100.0, 10.0)] * n_hist
    for j in range(8):
        close = 100.5 + 0.5 * j
        open_ = 100.0 if j == 0 else 100.5 + 0.5 * (j - 1)
        rows.append((open_, close + 0.5, close - 0.5, close, 20.0))
    rows.append((104.0, 104.0, 102.8, 103.2, 10.0))  # bar 9
    rows.append((103.0, 103.1, 102.3, 102.9, 5.0))  # bar 10 = test bar s
    rows.append((102.9, 103.3, 102.8, 103.2, 10.0))  # bar 11 = trigger t
    rows.extend([(103.2, 103.3, 103.1, 103.2, 10.0)] * tail_bars)
    frame = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"])
    frame.insert(
        0, "date", pd.date_range("2024-01-01", periods=len(frame), freq="15min", tz="UTC")
    )
    return frame


def run(strategy, frame):
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    return frame


class FakeDp:
    def __init__(self, frame):
        self.frame = frame

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.frame, None


class H095Tests(unittest.TestCase):
    def setUp(self):
        self.strategy = Strategy()
        self.frame = build_frame()
        self.out = run(self.strategy, self.frame)
        self.t_row = 15 * 96 + T_INDEX_IN_DAY

    def test_constants(self):
        s = Strategy
        self.assertEqual(s.INTERFACE_VERSION, 3)
        self.assertEqual(s.timeframe, "15m")
        self.assertFalse(s.can_short)
        self.assertEqual(s.minimal_roi, {"0": 100.0})
        self.assertLess(s.stoploss, 0)
        self.assertGreaterEqual(s.startup_candle_count, 1440)

    def test_signal_on_trigger_candle(self):
        entries = self.out.index[self.out["enter_long"] == 1].tolist()
        self.assertEqual(entries, [self.t_row])
        self.assertAlmostEqual(self.out.loc[self.t_row, "sig_h"], 104.5)
        self.assertAlmostEqual(self.out.loc[self.t_row, "sig_low_s"], 102.3)

    def test_binary_columns(self):
        for column in ("enter_long", "exit_long"):
            self.assertTrue(set(self.out[column].dropna().unique()).issubset({1}))
        last_bars = self.out.index[self.out["exit_long"] == 1]
        mods = (self.out.loc[last_bars, "date"].dt.hour * 60 + self.out.loc[last_bars, "date"].dt.minute)
        self.assertTrue(set(mods).issubset({465, 795, 1425}))

    def test_zero_volume_no_signal(self):
        frame = self.frame.copy()
        frame["volume"] = 0.0
        out = run(self.strategy, frame)
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(out["exit_long"].fillna(0).sum()), 0)
        frame = self.frame.copy()
        frame.loc[self.t_row, "volume"] = 0.0
        out = run(self.strategy, frame)
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)

    def test_undefined_startup_no_signal(self):
        out = run(self.strategy, build_frame(history_days=5))
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)
        out = run(self.strategy, self.frame)
        self.assertEqual(int(out["enter_long"].iloc[:1440].fillna(0).sum()), 0)

    def test_no_drive_without_volume_surge(self):
        frame = self.frame.copy()
        frame.loc[15 * 96 : 15 * 96 + 7, "volume"] = 10.0
        out = run(self.strategy, frame)
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)

    def test_future_candles_do_not_change_signals(self):
        n = self.t_row + 2
        short = run(self.strategy, self.frame.iloc[:n])
        long_ = run(self.strategy, self.frame)
        cols = ["sig_h", "sig_low_s", "sig_flag", "session_last_bar", "enter_long"]
        pd.testing.assert_frame_equal(
            short[cols].reset_index(drop=True),
            long_[cols].iloc[:n].reset_index(drop=True),
            check_dtype=False,
        )
        # Cut before the trigger: nothing appears early.
        early = run(self.strategy, self.frame.iloc[: self.t_row])
        self.assertEqual(int(early["enter_long"].fillna(0).sum()), 0)

    def _trade(self):
        open_date = self.out.loc[self.t_row + 1, "date"]
        return SimpleNamespace(open_date_utc=open_date, open_rate=103.2), open_date

    def test_confirm_entry_checks(self):
        self.strategy.dp = FakeDp(self.out)
        _, open_date = self._trade()
        args = ("X/USDT", "limit", 1, None, "GTC", open_date, "t", "buy")
        ok = lambda rate: self.strategy.confirm_trade_entry(
            args[0], args[1], args[2], rate, args[4], args[5], args[6], args[7]
        )
        self.assertTrue(ok(103.2))
        self.assertFalse(ok(104.6))  # P >= H
        self.assertFalse(ok(105.2))  # low(s) < 0.975 P

    def test_custom_stoploss_is_fixed_fraction(self):
        self.strategy.dp = FakeDp(self.out)
        trade, open_date = self._trade()
        stop = self.strategy.custom_stoploss("X/USDT", trade, open_date, 103.2, 0.0)
        self.assertAlmostEqual(stop, -0.01, places=6)  # d = 1% (0.99 P below low(s))
        stop = self.strategy.custom_stoploss("X/USDT", trade, open_date, 104.0, 0.0)
        self.assertAlmostEqual(104.0 * (1 + stop), 103.2 * 0.99, places=6)

    def test_take_profit_and_time_exit(self):
        self.strategy.dp = FakeDp(self.out)
        trade, open_date = self._trade()
        self.assertIsNone(
            self.strategy.custom_exit(
                "X/USDT", trade, open_date + timedelta(minutes=15), 103.3, 0.001
            )
        )
        self.assertEqual(
            self.strategy.custom_exit(
                "X/USDT", trade, open_date + timedelta(minutes=30), 104.6, 0.013
            ),
            "tp_session_high",
        )
        self.assertEqual(
            self.strategy.custom_exit(
                "X/USDT", trade, open_date + timedelta(hours=3), 103.3, 0.001
            ),
            "time_12bars",
        )


if __name__ == "__main__":
    unittest.main()
