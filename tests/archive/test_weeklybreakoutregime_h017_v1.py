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

ROOT = Path(__file__).parents[2]
CLASS_NAME = "WeeklyBreakoutRegime_H017_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / "_archive" / f"{CLASS_NAME}.py"
    spec = importlib.util.spec_from_file_location(CLASS_NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, CLASS_NAME)


Strategy = load_strategy()


def make_frame(n: int) -> pd.DataFrame:
    idx = np.arange(n)
    # Staircase uptrend: a 4% jump every 100 candles clears the 1% high wick.
    prices = 100.0 * 1.04 ** (idx // 100) * (1.0 + 0.001 * np.sin(idx / 7.0))
    return pd.DataFrame(
        {
            "open": prices,
            "high": prices * 1.01,
            "low": prices * 0.99,
            "close": prices,
            "volume": np.ones(n),
        }
    )


def run(frame: pd.DataFrame) -> pd.DataFrame:
    s = Strategy()
    frame = s.populate_indicators(frame, {})
    frame = s.populate_entry_trend(frame, {})
    return s.populate_exit_trend(frame, {})


class H017Tests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.06)
        self.assertGreaterEqual(Strategy.startup_candle_count, 2880)
        self.assertEqual(
            Strategy().protections,
            [{"method": "CooldownPeriod", "stop_duration_candles": 24}],
        )

    def test_signals_binary_and_present(self) -> None:
        out = run(make_frame(4500))
        for column in ("enter_long", "exit_long"):
            self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(int(out["enter_long"].fillna(0).sum()), 0)

    def test_zero_volume_no_signal(self) -> None:
        frame = make_frame(4500)
        frame["volume"] = 0.0
        out = run(frame)
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(out["exit_long"].fillna(0).sum()), 0)

    def test_nan_startup_no_entry(self) -> None:
        out = run(make_frame(4500))
        # slope needs 2160 + 720 candles of history
        self.assertEqual(int(out.iloc[:2879]["enter_long"].fillna(0).sum()), 0)

    def test_slope_condition_blocks_entry(self) -> None:
        # Strong rise then flat/falling slow mean: no entries once slope <= 0.
        n = 4500
        idx = np.arange(n)
        prices = np.where(idx < 3000, 100.0 + idx * 0.05, 250.0 - (idx - 3000) * 0.05)
        prices = prices + 2.0 * np.sin(idx / 5.0)
        frame = pd.DataFrame(
            {"open": prices, "high": prices * 1.01, "low": prices * 0.99,
             "close": prices, "volume": np.ones(n)}
        )
        out = run(frame)
        bad = out["enter_long"].fillna(0).astype(bool) & ~(
            out["sma_slow"] > out["sma_slow_lag"]
        )
        self.assertFalse(bad.any())

    def test_no_lookahead(self) -> None:
        full = make_frame(4800)
        first = run(full.iloc[:4200].copy().reset_index(drop=True))
        longer = run(full.copy())
        cols = ["sma_fast", "sma_slow", "sma_slow_lag", "entry_high", "exit_low",
                "enter_long", "exit_long"]
        pd.testing.assert_frame_equal(
            first[cols], longer.loc[:4199, cols], check_dtype=False
        )


if __name__ == "__main__":
    unittest.main()
