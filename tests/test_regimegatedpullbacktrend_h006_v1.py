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
NAME = "RegimeGatedPullbackTrend_H006_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, NAME)


Strategy = load_strategy()


def make_frame(prices):
    prices = list(prices)
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
    s = Strategy()
    frame = s.populate_indicators(frame, {})
    frame = s.populate_entry_trend(frame, {})
    return s.populate_exit_trend(frame, {})


def synthetic_prices(n):
    # Rising trend with periodic sharp dips and recoveries.
    idx = np.arange(n)
    trend = 100.0 * np.exp(idx * 0.0003)
    wave = 1.0 - 0.09 * (np.sin(idx / 40.0) > 0.95)
    wiggle = 1.0 + 0.03 * np.sin(idx / 9.0)
    return trend * wave * wiggle


class RegimeGatedPullbackTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 5520)
        self.assertEqual(
            Strategy().protections,
            [{"method": "CooldownPeriod", "stop_duration_candles": 48}],
        )

    def test_signals_binary(self) -> None:
        frame = run(make_frame(synthetic_prices(7000)))
        for column in ("enter_long", "exit_long"):
            if column in frame:
                self.assertTrue(set(frame[column].dropna().unique()).issubset({1}))

    def test_signals_occur_on_synthetic_series(self) -> None:
        frame = run(make_frame(synthetic_prices(7000)))
        self.assertGreater(int(frame["enter_long"].fillna(0).sum()), 0)

    def test_zero_volume_no_signal(self) -> None:
        frame = make_frame(synthetic_prices(7000))
        frame["volume"] = 0.0
        frame = run(frame)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(frame.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self) -> None:
        frame = run(make_frame(synthetic_prices(7000)))
        head = frame.iloc[: Strategy.startup_candle_count - 1]
        self.assertEqual(int(head["enter_long"].fillna(0).sum()), 0)
        # Short series: everything undefined, nothing fires.
        short = run(make_frame(synthetic_prices(300)))
        self.assertEqual(int(short.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_no_lookahead(self) -> None:
        n, k = 6500, 400
        full = synthetic_prices(n + k)
        a = run(make_frame(full[:n]))
        b = run(make_frame(full))
        cols = [c for c in a.columns if c not in {"open", "high", "low", "close", "volume"}]
        pd.testing.assert_frame_equal(
            a[cols].reset_index(drop=True),
            b.loc[: n - 1, cols].reset_index(drop=True),
            check_dtype=False,
        )


if __name__ == "__main__":
    unittest.main()
