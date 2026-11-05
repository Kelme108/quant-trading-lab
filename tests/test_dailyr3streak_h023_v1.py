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

_strategy_mod = sys.modules["freqtrade.strategy"]
if not hasattr(_strategy_mod, "informative"):
    _strategy_mod.informative = lambda *args, **kwargs: (lambda function: function)

ROOT = Path(__file__).parents[1]
NAME = "DailyR3Streak_H023_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load()
Strategy = getattr(MODULE, NAME)


def make_frame(closes_hourly):
    n = len(closes_hourly)
    close = pd.Series(closes_hourly, dtype=float)
    return pd.DataFrame(
        {
            "date": pd.date_range("2022-01-01", periods=n, freq="1h", tz="UTC"),
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": 1.0,
        }
    )


def run(strategy, frame):
    hourly = frame.copy()
    daily = (
        hourly.set_index("date")
        .resample("1D")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        .dropna(subset=["close"])
        .reset_index()
    )
    daily = strategy.populate_indicators_1d(daily, {})
    daily = daily.rename(columns={c: f"{c}_1d" for c in daily.columns if c != "date"})
    daily["date"] = daily["date"] + pd.Timedelta(days=1)
    merged = pd.merge_asof(hourly, daily, on="date", direction="backward")
    merged = strategy.populate_indicators(merged, {})
    merged = strategy.populate_entry_trend(merged, {})
    merged = strategy.populate_exit_trend(merged, {})
    return merged


def hourly(daily):
    return [price for price in daily for _ in range(24)]


def wavy_prices(days):
    rng = np.random.default_rng(7)
    steps = rng.normal(0.002, 0.03, days)
    return list(100 * np.exp(np.cumsum(steps)))


class R3Tests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 400)

    def test_wilder_rsi_values(self) -> None:
        rsi = MODULE.wilder_rsi(pd.Series([10.0, 11.0, 10.0, 9.0, 12.0]), 2)
        self.assertTrue(rsi.iloc[:2].isna().all())
        # seed: avg gain 0.5, avg loss 0.5 -> 50
        self.assertAlmostEqual(rsi.iloc[2], 50.0)
        # next: gain 0, loss 1 -> avg_gain 0.25, avg_loss 0.75 -> 25
        self.assertAlmostEqual(rsi.iloc[3], 25.0)
        # next: gain 3, loss 0 -> avg_gain 1.625, avg_loss 0.375
        self.assertAlmostEqual(rsi.iloc[4], 100 - 100 / (1 + 1.625 / 0.375))

    def test_entry_and_exit_logic(self) -> None:
        # 230 rising days (RSI 100), then falling days, then a sharp rebound.
        daily = [100 + i for i in range(230)] + [329 - 3 * i for i in range(1, 6)] + [400]
        out = run(Strategy(), make_frame(hourly(daily)))
        self.assertGreater(out["enter_long"].fillna(0).sum(), 0)
        self.assertGreater(out["exit_long"].fillna(0).sum(), 0)
        # Entry never before the first falling day closes (visible from day 231).
        self.assertEqual(out.iloc[: 231 * 24]["enter_long"].fillna(0).sum(), 0)

    def test_binary_signals(self) -> None:
        out = run(Strategy(), make_frame(hourly(wavy_prices(600))))
        for column in ("enter_long", "exit_long"):
            self.assertIn(column, out)
            self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_no_signal(self) -> None:
        daily = [100 + i for i in range(230)] + [329 - 3 * i for i in range(1, 6)] + [400]
        frame = make_frame(hourly(daily))
        frame["volume"] = 0.0
        out = run(Strategy(), frame)
        self.assertEqual(out.get("enter_long", pd.Series(0)).fillna(0).sum(), 0)
        self.assertEqual(out.get("exit_long", pd.Series(0)).fillna(0).sum(), 0)

    def test_startup_nan_no_entry(self) -> None:
        # Falling series: RSI is low early, but SMA200 is undefined before day 200.
        daily = [1000 - 2 * i for i in range(150)]
        out = run(Strategy(), make_frame(hourly(daily)))
        self.assertEqual(out.get("enter_long", pd.Series(0)).fillna(0).sum(), 0)
        # Exit needs RSI, undefined before 3 daily closes.
        frame = make_frame(hourly([100, 101, 102]))
        early = run(Strategy(), frame)
        self.assertEqual(early.get("exit_long", pd.Series(0)).fillna(0).sum(), 0)

    def test_no_lookahead(self) -> None:
        full = make_frame(hourly(wavy_prices(620)))
        n = 500 * 24 + 5
        strategy = Strategy()
        short = run(strategy, full.iloc[:n].copy())
        long = run(strategy, full.copy())
        cols = ["enter_long", "exit_long"]
        a = short[cols].fillna(0).iloc[:n].reset_index(drop=True)
        b = long[cols].fillna(0).iloc[:n].reset_index(drop=True)
        pd.testing.assert_frame_equal(a, b, check_dtype=False)


if __name__ == "__main__":
    unittest.main()
