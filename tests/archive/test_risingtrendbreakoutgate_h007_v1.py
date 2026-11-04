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
CLASS_NAME = "RisingTrendBreakoutGate_H007_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / "_archive" / f"{CLASS_NAME}.py"
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


class RisingTrendBreakoutGateTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.06)
        self.assertGreaterEqual(Strategy.startup_candle_count, 2880)
        self.assertEqual(
            Strategy().protections,
            [{"method": "CooldownPeriod", "stop_duration_candles": 120}],
        )

    def test_signals_binary_and_present(self) -> None:
        frame = run(Strategy(), make_frame(synthetic_prices(6000)))
        for column in ("enter_long", "exit_long"):
            self.assertIn(column, frame)
            self.assertTrue(set(frame[column].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(frame["enter_long"].fillna(0).sum(), 0)

    def test_zero_volume_no_signal(self) -> None:
        frame = make_frame(synthetic_prices(6000))
        frame["volume"] = 0.0
        frame = run(Strategy(), frame)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(frame.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self) -> None:
        strategy = Strategy()
        frame = run(strategy, make_frame(synthetic_prices(6000)))
        # SMA(2400) is undefined for the first 2399 rows; slope needs 2880 rows.
        head = frame.iloc[: strategy.startup_candle_count - 1]
        self.assertEqual(int(head["enter_long"].fillna(0).sum()), 0)
        # Exit needs only SMA(1200) and the 240-bar channel.
        self.assertEqual(int(frame.iloc[:1199]["exit_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self) -> None:
        prices = synthetic_prices(6000)
        n = 5000
        strategy = Strategy()
        short = run(strategy, make_frame(prices[:n]))
        long = run(strategy, make_frame(prices))
        for column in ("enter_long", "exit_long"):
            a = short[column].fillna(0).to_numpy()
            b = long[column].fillna(0).to_numpy()[:n]
            np.testing.assert_array_equal(a, b)
        cols = ["sma_fast", "sma_slow", "sma_slow_lag", "entry_high", "exit_low"]
        pd.testing.assert_frame_equal(short[cols], long.loc[: n - 1, cols])

    def test_channel_excludes_current_candle(self) -> None:
        frame = run(Strategy(), make_frame(synthetic_prices(1000)))
        self.assertTrue(pd.isna(frame.loc[479, "entry_high"]))
        self.assertEqual(frame.loc[480, "entry_high"], frame.loc[0:479, "high"].max())
        self.assertTrue(pd.isna(frame.loc[239, "exit_low"]))
        self.assertEqual(frame.loc[240, "exit_low"], frame.loc[0:239, "low"].min())


if __name__ == "__main__":
    unittest.main()
