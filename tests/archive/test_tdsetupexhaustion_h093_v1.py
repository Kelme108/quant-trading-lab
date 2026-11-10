import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta
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


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / "_archive" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Strategy = load_strategy("TDSetupExhaustion_H093_v1.py", "TDSetupExhaustion_H093_v1")


def make_frame(extra_flat: int = 20) -> pd.DataFrame:
    closes = [100.0] * 109 + [100.1]
    for k in range(8):
        closes.append(99.6 * 0.996 ** k)  # bars 110..117
    closes.append(closes[-1] * 1.001)  # bar 118 = n9, reversal close
    closes += [closes[-1]] * extra_flat
    opens = [closes[0]] + closes[:-1]
    highs = [c * 1.0005 for c in closes]
    lows = [c * 0.999 for c in closes]
    return pd.DataFrame(
        {"open": opens, "high": highs, "low": lows, "close": closes,
         "volume": [1.0] * len(closes)}
    )


def run(strategy, frame):
    frame = strategy.populate_indicators(frame, {})
    return strategy.populate_entry_trend(frame, {})


class FakeDp:
    def __init__(self, frame):
        self.frame = frame

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.frame, None


class Trade:
    def __init__(self, open_date_utc):
        self.open_date_utc = open_date_utc


class TDSetupTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 100)

    def test_signal_fires_and_is_binary(self) -> None:
        frame = run(Strategy(), make_frame())
        self.assertEqual(frame.loc[118, "enter_long"], 1)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 1)
        self.assertTrue(set(frame["enter_long"].dropna().unique()).issubset({1}))
        self.assertTrue(frame.loc[118, "td_tp"] > frame.loc[118, "close"] * 1.01)

    def test_zero_volume_no_signal(self) -> None:
        base = make_frame()
        base["volume"] = 0.0
        frame = run(Strategy(), base)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_nan_values_no_signal(self) -> None:
        base = make_frame()
        base.loc[116, ["high", "low", "close"]] = float("nan")
        frame = run(Strategy(), base)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        startup = Strategy.startup_candle_count
        frame = run(Strategy(), make_frame())
        self.assertEqual(int(frame.iloc[:startup].get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_no_lookahead(self) -> None:
        full = make_frame(extra_flat=30)
        short = full.iloc[:125].copy().reset_index(drop=True)
        a = run(Strategy(), short)
        b = run(Strategy(), full.copy())
        cols = ["td_signal", "td_ll", "td_tp"]
        pd.testing.assert_frame_equal(a.loc[:124, cols], b.loc[:124, cols], check_dtype=False)
        # also: changing the future does not alter the past
        changed = full.copy()
        changed.loc[125:, ["open", "high", "low", "close"]] = 500.0
        c = run(Strategy(), changed)
        pd.testing.assert_frame_equal(a.loc[:124, cols], c.loc[:124, cols], check_dtype=False)

    def test_entry_checks_and_exits(self) -> None:
        frame = run(Strategy(), make_frame())
        strategy = Strategy()
        strategy.dp = FakeDp(frame.iloc[:119])
        now = datetime(2026, 1, 1, 12, 0)
        entry = float(frame.loc[118, "close"])
        ok = strategy.confirm_trade_entry("BTC/USDT", "limit", 1, entry, "GTC", now, None, "long")
        self.assertTrue(ok)
        stop, tp = strategy._levels["BTC/USDT"]
        self.assertLessEqual(stop, entry * 0.99)
        self.assertGreaterEqual(stop, entry * 0.97)
        # entry far above TP is skipped
        self.assertFalse(strategy.confirm_trade_entry("BTC/USDT", "limit", 1, tp * 1.5, "GTC", now, None, "long"))
        # stop more than 3% below entry is skipped
        low_frame = frame.iloc[:119].copy()
        low_frame.loc[118, "td_ll"] = entry * 0.9
        strategy.dp = FakeDp(low_frame)
        self.assertFalse(strategy.confirm_trade_entry("BTC/USDT", "limit", 1, entry, "GTC", now, None, "long"))
        strategy.dp = FakeDp(frame.iloc[:119])
        strategy.confirm_trade_entry("BTC/USDT", "limit", 1, entry, "GTC", now, None, "long")

        trade = Trade(now)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, now + timedelta(hours=1), entry, 0.0))
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade, now + timedelta(hours=1), tp * 1.001, 0.02),
            "td_take_profit",
        )
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade, now + timedelta(hours=8), entry, 0.0),
            "td_time_exit",
        )
        sl = strategy.custom_stoploss("BTC/USDT", trade, now, entry, 0.0)
        self.assertAlmostEqual(entry * (1 + sl), stop, places=6)


if __name__ == "__main__":
    unittest.main()
