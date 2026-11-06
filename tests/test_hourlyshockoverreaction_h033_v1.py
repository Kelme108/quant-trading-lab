import importlib.util
import sys
import types
import unittest
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
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)

ROOT = Path(__file__).parents[1]


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


S = load_strategy(
    "HourlyShockOverreaction_H033_v1.py", "HourlyShockOverreaction_H033_v1"
)


def make_frame(prices):
    return pd.DataFrame(
        {
            "open": prices,
            "high": [p * 1.01 for p in prices],
            "low": [p * 0.99 for p in prices],
            "close": prices,
            "volume": [1.0] * len(prices),
        }
    )


def run(frame):
    s = S()
    frame = s.populate_indicators(frame, {})
    frame = s.populate_entry_trend(frame, {})
    return s.populate_exit_trend(frame, {})


def shock_prices(n=1500):
    prices = [100.0 + 0.01 * i for i in range(n)]
    for k in (1300, 1400):
        base = prices[k - 1]
        for j in range(4):
            prices[k + j] = base * (1 - 0.012 * (j + 1))  # -4.8% over 4 bars
        for j in range(k + 4, k + 60):
            prices[j] = prices[k + 3]
    return prices


class H033Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(S.INTERFACE_VERSION, 3)
        self.assertEqual(S.timeframe, "1h")
        self.assertFalse(S.can_short)
        self.assertEqual(S.minimal_roi, {"0": 100.0})
        self.assertLess(S.stoploss, 0)
        self.assertGreaterEqual(S.startup_candle_count, 1200)

    def test_signals_binary_and_present(self):
        f = run(make_frame(shock_prices()))
        for c in ("enter_long", "exit_long"):
            self.assertTrue(set(f[c].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(f["enter_long"].fillna(0).sum(), 0)
        self.assertGreater(f["exit_long"].fillna(0).sum(), 0)

    def test_time_exit_after_24_bars(self):
        f = run(make_frame(shock_prices()))
        e = f.index[f["enter_long"] == 1][0]
        x = f.index[f["exit_long"] == 1][0]
        self.assertEqual(x - e, 24)

    def test_zero_volume_no_signal(self):
        fr = make_frame(shock_prices())
        fr["volume"] = 0.0
        f = run(fr)
        self.assertEqual(int(f["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(f["exit_long"].fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self):
        prices = [100.0] * 1500
        for j in range(4):
            prices[500 + j] = 100.0 * (1 - 0.012 * (j + 1))
        f = run(make_frame(prices))
        self.assertEqual(int(f.iloc[:1200]["enter_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self):
        prices = shock_prices(1700)
        a = run(make_frame(prices[:1500]))
        b = run(make_frame(prices))
        cols = ["enter_long", "exit_long", "sim_entry", "sim_exit", "r4", "sma1200"]
        pd.testing.assert_frame_equal(
            a[cols].iloc[:1500].reset_index(drop=True),
            b[cols].iloc[:1500].reset_index(drop=True),
            check_dtype=False,
        )


if __name__ == "__main__":
    unittest.main()
