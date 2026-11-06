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

ROOT = Path(__file__).parents[1]


def load_strategy(filename, class_name):
    path = ROOT / "user_data" / "strategies" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


S = load_strategy("VolumeSpikeCrashRebound_H032_v1.py", "VolumeSpikeCrashRebound_H032_v1")


def make_frame(n=1000, crashes=(850,), seed=1):
    rng = np.random.default_rng(seed)
    close = 100 * np.cumprod(1 + rng.normal(0, 0.003, n))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) * 1.001
    low = np.minimum(open_, close) * 0.999
    volume = rng.uniform(0.9, 1.1, n)
    for c in crashes:
        # crash bar: -5% drop, closing in upper half of its range, volume spike
        close[c:] *= 0.95 * close[c - 1] / close[c]
        open_[c] = close[c - 1]
        low[c] = close[c] * 0.9
        high[c] = open_[c]
        volume[c] = 10.0
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume}
    )


def run(strategy, frame):
    frame = strategy.populate_indicators(frame, {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


class H032Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(S.INTERFACE_VERSION, 3)
        self.assertEqual(S.timeframe, "1h")
        self.assertFalse(S.can_short)
        self.assertEqual(S.minimal_roi, {"0": 100.0})
        self.assertLess(S.stoploss, 0)
        self.assertGreaterEqual(S.startup_candle_count, 721)

    def test_signal_fires_and_is_binary(self):
        out = run(S(), make_frame())
        self.assertEqual(out.loc[850, "enter_long"], 1)
        for col in ("enter_long", "exit_long"):
            self.assertTrue(set(out[col].dropna().unique().tolist()).issubset({1}))
        # time exit at bar t+18 at the latest
        exits = out.index[out["exit_long"] == 1]
        self.assertTrue(any(851 <= i <= 868 for i in exits))
        self.assertEqual(out.loc[868, "exit_long"], 1)

    def test_zero_volume_no_signal(self):
        frame = make_frame()
        frame["volume"] = 0.0
        out = run(S(), frame)
        self.assertEqual(int(out.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(out.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_zero_volume_on_crash_bar(self):
        frame = make_frame()
        frame.loc[850, "volume"] = 0.0
        out = run(S(), frame)
        self.assertTrue(pd.isna(out.loc[850, "enter_long"]))

    def test_nan_startup_no_signal(self):
        out = run(S(), make_frame(crashes=(300, 850)))
        self.assertTrue(out.iloc[:720]["enter_long"].isna().all())
        self.assertEqual(out.loc[850, "enter_long"], 1)

    def test_no_lookahead(self):
        full = make_frame(n=1100, crashes=(850, 1000))
        a = run(S(), full.iloc[:900].copy().reset_index(drop=True))
        b = run(S(), full.copy())
        cols = ["enter_long", "exit_long"]
        pd.testing.assert_frame_equal(
            a[cols].reset_index(drop=True),
            b.iloc[:900][cols].reset_index(drop=True),
            check_dtype=False,
        )


if __name__ == "__main__":
    unittest.main()
