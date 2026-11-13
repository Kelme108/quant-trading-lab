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
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)

ROOT = Path(__file__).parents[2]
NAME = "HourlyRangeExpansionDrift_H035_v1"


def load():
    path = ROOT / "user_data" / "strategies" / "_archive" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, NAME)


Strategy = load()


def make_frame(n=700, seed=1):
    rng = np.random.default_rng(seed)
    close = 100 + np.cumsum(rng.normal(0.05, 0.3, n))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) + rng.uniform(0, 0.2, n)
    low = np.minimum(open_, close) - rng.uniform(0, 0.2, n)
    # Inject shock bars closing at the high.
    for i in range(520, n, 40):
        open_[i] = close[i - 1]
        low[i] = open_[i] - 0.1
        high[i] = open_[i] + 6.0
        close[i] = high[i] - 0.1
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": 1.0}
    )


def run(frame):
    s = Strategy()
    f = s.populate_indicators(frame.copy(), {})
    f = s.populate_entry_trend(f, {})
    return s.populate_exit_trend(f, {})


class H035Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 480)
        self.assertEqual(Strategy().protections[0]["stop_duration_candles"], 6)

    def test_binary_and_signals_exist(self):
        f = run(make_frame())
        self.assertGreater(int(f["enter_long"].fillna(0).sum()), 0)
        for col in ("enter_long", "exit_long"):
            self.assertTrue(set(f[col].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_no_signal(self):
        fr = make_frame()
        fr["volume"] = 0.0
        f = run(fr)
        self.assertEqual(int(f["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(f["exit_long"].fillna(0).sum()), 0)

    def test_startup_no_signal(self):
        f = run(make_frame())
        self.assertEqual(int(f.iloc[:480]["enter_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self):
        fr = make_frame(n=800)
        a = run(fr.iloc[:650])
        b = run(fr)
        cols = [c for c in a.columns]
        pd.testing.assert_frame_equal(
            a[cols].reset_index(drop=True),
            b.iloc[:650][cols].reset_index(drop=True),
            check_dtype=False,
        )

    def test_flat_bar_does_not_qualify(self):
        fr = make_frame()
        fr.loc[600, ["open", "high", "low", "close"]] = 100.0
        f = run(fr)
        self.assertTrue(pd.isna(f.loc[600, "pos"]))
        self.assertFalse(f.loc[600, "enter_long"] == 1)


if __name__ == "__main__":
    unittest.main()
