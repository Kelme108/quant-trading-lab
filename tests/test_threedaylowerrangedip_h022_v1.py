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
_strategy_mod = sys.modules["freqtrade.strategy"]
if not hasattr(_strategy_mod, "informative"):
    _strategy_mod.informative = lambda *args, **kwargs: (lambda func: func)
if not hasattr(_strategy_mod, "IStrategy"):
    _strategy_mod.IStrategy = object

talib = types.ModuleType("talib")
talib_abstract = types.ModuleType("talib.abstract")
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)

ROOT = Path(__file__).parents[1]
CLASS = "ThreeDayLowerRangeDip_H022_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / f"{CLASS}.py"
    spec = importlib.util.spec_from_file_location(CLASS, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, CLASS)


Strategy = load_strategy()


def daily_frame(n: int, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100 + np.cumsum(rng.normal(0.3, 2.0, n))
    close = np.abs(close) + 50
    return pd.DataFrame(
        {
            "open": close,
            "high": close + rng.uniform(0.1, 2, n),
            "low": close - rng.uniform(0.1, 2, n),
            "close": close,
            "volume": np.ones(n),
        }
    )


def merged_frame(daily: pd.DataFrame, strategy) -> pd.DataFrame:
    """Emulate the informative merge: each daily row repeated over 24 hours."""
    ind = strategy.populate_indicators_1d(daily.copy(), {})
    hourly = ind.loc[ind.index.repeat(24)].reset_index(drop=True)
    out = pd.DataFrame({"volume": hourly["volume"]})
    for col in ("close", "sma200", "sma5", "falling3"):
        out[f"{col}_1d"] = hourly[col]
    return out


def run(frame, strategy):
    frame = strategy.populate_indicators(frame, {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


class ThreeDayLowerRangeDipTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.12)
        self.assertGreaterEqual(Strategy.startup_candle_count, 400)

    def test_falling_range_is_strict_and_correct(self) -> None:
        high = [10, 9, 8, 7, 7, 6]
        low = [5, 4, 3, 2, 1, 0]
        daily = pd.DataFrame(
            {"open": high, "high": high, "low": low, "close": high, "volume": 1.0}
        )
        out = Strategy().populate_indicators_1d(daily, {})
        self.assertEqual(out["falling3"].tolist(), [0, 0, 0, 1, 0, 0])

    def test_signals_binary_and_present(self) -> None:
        s = Strategy()
        frame = run(merged_frame(daily_frame(900), s), s)
        for column in ("enter_long", "exit_long"):
            self.assertIn(column, frame)
            self.assertTrue(set(frame[column].dropna().unique()).issubset({1}))
        self.assertGreater(int(frame["exit_long"].fillna(0).sum()), 0)

    def test_entry_requires_conditions(self) -> None:
        s = Strategy()
        frame = pd.DataFrame(
            {
                "volume": [1.0, 1.0, 1.0, 1.0],
                "close_1d": [100.0, 100.0, 100.0, 100.0],
                "sma200_1d": [90.0, 90.0, 110.0, 90.0],
                "sma5_1d": [105.0, 105.0, 105.0, 95.0],
                "falling3_1d": [1, 0, 1, 1],
            }
        )
        frame = run(frame, s)
        self.assertEqual(frame["enter_long"].fillna(0).tolist(), [1, 0, 0, 0])
        self.assertEqual(frame["exit_long"].fillna(0).tolist(), [0, 0, 1, 1])

    def test_zero_volume_no_signal(self) -> None:
        s = Strategy()
        merged = merged_frame(daily_frame(900), s)
        merged["volume"] = 0.0
        frame = run(merged, s)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame["exit_long"].fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self) -> None:
        s = Strategy()
        frame = run(merged_frame(daily_frame(900), s), s)
        warm = 199 * 24
        self.assertEqual(int(frame.iloc[:warm]["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame.iloc[:warm]["exit_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self) -> None:
        s = Strategy()
        full = daily_frame(700)
        short = full.iloc[:500].copy()
        a = s.populate_indicators_1d(short.copy(), {})
        b = s.populate_indicators_1d(full.copy(), {})
        pd.testing.assert_frame_equal(a, b.iloc[:500], check_dtype=False)
        fa = run(merged_frame(short, s), s)
        fb = run(merged_frame(full, s), s).iloc[: len(fa)]
        for column in ("enter_long", "exit_long"):
            pd.testing.assert_series_equal(
                fa[column].fillna(0), fb[column].fillna(0), check_dtype=False
            )


if __name__ == "__main__":
    unittest.main()
