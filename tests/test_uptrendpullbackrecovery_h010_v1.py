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
CLASS_NAME = "UptrendPullbackRecovery_H010_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / f"{CLASS_NAME}.py"
    spec = importlib.util.spec_from_file_location(CLASS_NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, CLASS_NAME)


Strategy = load_strategy()


def make_frame(prices) -> pd.DataFrame:
    prices = list(prices)
    return pd.DataFrame(
        {
            "open": prices,
            "high": [p * 1.005 for p in prices],
            "low": [p * 0.995 for p in prices],
            "close": prices,
            "volume": [1.0] * len(prices),
        }
    )


def run(strategy, frame):
    frame = strategy.populate_indicators(frame, {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


def synthetic_prices(n):
    rng = np.random.default_rng(7)
    steps = rng.normal(0.0004, 0.01, n)
    return 100.0 * np.exp(np.cumsum(steps))


class UptrendPullbackRecoveryTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.05)
        self.assertGreaterEqual(Strategy.startup_candle_count, 2400)
        self.assertLessEqual(Strategy.startup_candle_count, 4500)
        self.assertEqual(Strategy().protections, [{"method": "CooldownPeriod", "stop_duration_candles": 48}])

    def test_signals_binary_and_present(self) -> None:
        frame = run(Strategy(), make_frame(synthetic_prices(9000)))
        for column in ("enter_long", "exit_long"):
            self.assertTrue(set(frame[column].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(frame["enter_long"].fillna(0).sum(), 0)

    def test_zero_volume_no_signal(self) -> None:
        frame = make_frame(synthetic_prices(9000))
        frame["volume"] = 0.0
        frame = run(Strategy(), frame)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(frame.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self) -> None:
        frame = run(Strategy(), make_frame(synthetic_prices(9000)))
        self.assertEqual(int(frame.iloc[:2399]["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame.iloc[:2399]["exit_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self) -> None:
        prices = synthetic_prices(9000)
        n = 7000
        strategy = Strategy()
        short = run(strategy, make_frame(prices[:n]))
        long = run(strategy, make_frame(prices))
        for column in ("enter_long", "exit_long"):
            np.testing.assert_array_equal(short[column].fillna(0).to_numpy(), long[column].fillna(0).to_numpy()[:n])
        cols = ["sma_long", "sma_mid", "sma_fast", "recent_low_close", "prior_high"]
        pd.testing.assert_frame_equal(short[cols], long.loc[: n - 1, cols])

    def test_levels_exclude_current_candle(self) -> None:
        frame = run(Strategy(), make_frame(synthetic_prices(1000)))
        self.assertTrue(pd.isna(frame.loc[335, "prior_high"]))
        self.assertEqual(frame.loc[336, "prior_high"], frame.loc[0:335, "high"].max())
        self.assertTrue(pd.isna(frame.loc[47, "recent_low_close"]))
        self.assertEqual(frame.loc[48, "recent_low_close"], frame.loc[0:47, "close"].min())


if __name__ == "__main__":
    unittest.main()
