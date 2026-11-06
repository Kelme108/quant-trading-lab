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


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Strategy = load_strategy(
    "HourlyWilliamsVolBreakout_H043_v1.py", "HourlyWilliamsVolBreakout_H043_v1"
)


def make_frame(n: int, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ret = rng.normal(0.0004, 0.012, n)
    close = 100.0 * np.exp(np.cumsum(ret))
    open_ = np.concatenate([[100.0], close[:-1]])
    spread = np.abs(rng.normal(0.006, 0.004, n))
    return pd.DataFrame(
        {
            "date": pd.date_range("2023-01-01", periods=n, freq="h", tz="UTC"),
            "open": open_,
            "high": np.maximum(open_, close) * (1 + spread),
            "low": np.minimum(open_, close) * (1 - spread),
            "close": close,
            "volume": np.full(n, 10.0),
        }
    )


def run(strategy, frame):
    frame = strategy.populate_indicators(frame, {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


class WilliamsH043Tests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 1224)

    def test_signals_binary_and_present(self) -> None:
        frame = run(Strategy(), make_frame(4000))
        for column in ("enter_long", "exit_long"):
            values = frame[column].dropna().unique().tolist()
            self.assertTrue(set(values).issubset({1}))
        self.assertGreater(int(frame["exit_long"].fillna(0).sum()), 0)
        self.assertGreater(int(frame["enter_long"].fillna(0).sum()), 0)
        entries = frame[frame["enter_long"] == 1]
        self.assertTrue(entries["hour_utc"].between(1, 18).all())
        self.assertEqual(entries["day_utc"].duplicated().sum(), 0)

    def test_zero_volume_no_signal(self) -> None:
        base = make_frame(4000)
        base["volume"] = 0.0
        frame = run(Strategy(), base)
        self.assertEqual(int(frame.get("enter_long", pd.Series()).fillna(0).sum()), 0)
        self.assertEqual(int(frame.get("exit_long", pd.Series()).fillna(0).sum()), 0)

    def test_startup_nan_no_entry(self) -> None:
        strategy = Strategy()
        frame = run(strategy, make_frame(4000))
        early = frame.iloc[: 50 * 24]
        self.assertTrue(early["breakout_level"].notna().sum() >= 0)
        self.assertEqual(int(early["enter_long"].fillna(0).sum()), 0)
        undefined = frame[frame["prev_trend"].isna()]
        self.assertEqual(int(undefined["enter_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self) -> None:
        full = make_frame(4300)
        n = 3500
        strategy = Strategy()
        short = run(strategy, full.iloc[:n].copy())
        long = run(strategy, full.copy())
        cols = [
            "day_open", "prev_range", "prev_trend", "breakout_level", "stop_level",
        ]
        pd.testing.assert_frame_equal(
            short[cols].reset_index(drop=True),
            long.iloc[:n][cols].reset_index(drop=True),
            check_dtype=False,
        )
        for column in ("enter_long", "exit_long"):
            a = short[column].fillna(0).to_numpy()
            b = long.iloc[:n][column].fillna(0).to_numpy()
            self.assertTrue((a == b).all())


if __name__ == "__main__":
    unittest.main()
