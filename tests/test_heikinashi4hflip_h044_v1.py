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


Strat = load_strategy("HeikinAshi4hFlip_H044_v1.py", "HeikinAshi4hFlip_H044_v1")


def make_frame(n, seed=1):
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    close = 100 + 0.05 * t + 8 * np.sin(t / 17.0) + rng.normal(0, 0.5, n)
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) + 0.3
    low = np.minimum(open_, close) - 0.3
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC"),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.ones(n),
        }
    )


def run(strategy, frame):
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


class HeikinAshiH044Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strat.INTERFACE_VERSION, 3)
        self.assertEqual(Strat.timeframe, "1h")
        self.assertFalse(Strat.can_short)
        self.assertEqual(Strat.minimal_roi, {"0": 100.0})
        self.assertLess(Strat.stoploss, 0)
        self.assertGreaterEqual(Strat.startup_candle_count, 1200)

    def test_binary_and_signals_exist(self):
        out = run(Strat(), make_frame(3000))
        for col in ("enter_long", "exit_long"):
            self.assertIn(col, out)
            self.assertTrue(set(out[col].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(out["exit_long"].fillna(0).sum(), 0)
        hours = out.loc[out["enter_long"] == 1, "date"].dt.hour
        self.assertTrue(set(hours).issubset({3, 7, 11, 15, 19, 23}))

    def test_zero_volume_no_signal(self):
        frame = make_frame(3000)
        frame["volume"] = 0.0
        out = run(Strat(), frame)
        self.assertEqual(int(out.get("enter_long", pd.Series()).fillna(0).sum()), 0)
        self.assertEqual(int(out.get("exit_long", pd.Series()).fillna(0).sum()), 0)

    def test_startup_nan_no_entry(self):
        out = run(Strat(), make_frame(3000))
        # SMA(100) of 4h closes needs 400 1h candles
        self.assertEqual(int(out.iloc[:399]["enter_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self):
        strat = Strat()
        full = make_frame(2000)
        first = run(strat, full.iloc[:1500])
        longer = run(strat, full)
        cols = [c for c in first.columns if c not in {"enter_tag", "exit_tag"}]
        pd.testing.assert_frame_equal(
            first[cols].reset_index(drop=True),
            longer.iloc[:1500][cols].reset_index(drop=True),
            check_dtype=False,
        )
        for col in ("enter_long", "exit_long"):
            a = first[col].fillna(0).to_numpy()
            b = longer[col].iloc[:1500].fillna(0).to_numpy()
            np.testing.assert_array_equal(a, b)


if __name__ == "__main__":
    unittest.main()
