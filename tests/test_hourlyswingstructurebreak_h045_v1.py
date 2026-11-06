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
NAME = "HourlySwingStructureBreak_H045_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, NAME)


Strategy = load()


def make_frame(n: int, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.012, n)))
    return pd.DataFrame(
        {
            "open": close,
            "high": close * 1.004,
            "low": close * 0.996,
            "close": close,
            "volume": np.ones(n),
        }
    )


def run(frame):
    s = Strategy()
    f = s.populate_indicators(frame.copy(), {})
    f = s.populate_entry_trend(f, {})
    return s.populate_exit_trend(f, {})


class H045Tests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 1500)
        self.assertEqual(Strategy().protections[0]["method"], "CooldownPeriod")

    def test_binary_and_signals_exist(self) -> None:
        f = run(make_frame(6000))
        for col in ("enter_long", "exit_long"):
            self.assertTrue(set(f[col].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(int(f["exit_long"].fillna(0).sum()), 0)

    def test_zero_volume_no_signal(self) -> None:
        frame = make_frame(4000)
        frame["volume"] = 0.0
        f = run(frame)
        self.assertEqual(int(f["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(f["exit_long"].fillna(0).sum()), 0)

    def test_startup_no_signal(self) -> None:
        f = run(make_frame(4000))
        n = Strategy.startup_candle_count
        self.assertEqual(int(f.iloc[:n]["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(f.iloc[:n]["exit_long"].fillna(0).sum()), 0)

    def test_pivot_known_only_after_confirmation(self) -> None:
        frame = make_frame(300)
        f = Strategy().populate_indicators(frame.copy(), {})
        # first swing values can only appear at index >= 6 (pivot i>=3, known at i+3)
        self.assertTrue(f["swing_high"].iloc[:6].isna().all())
        self.assertTrue(f["swing_low"].iloc[:6].isna().all())

    def test_no_lookahead(self) -> None:
        full = make_frame(5000)
        short = full.iloc[:4000]
        a = run(short)
        b = run(full)
        cols = ["swing_high", "swing_low", "swing_low_prev", "sma200", "enter_long", "exit_long"]
        pd.testing.assert_frame_equal(
            a[cols].reset_index(drop=True),
            b.iloc[:4000][cols].reset_index(drop=True),
            check_dtype=False,
        )


if __name__ == "__main__":
    unittest.main()
