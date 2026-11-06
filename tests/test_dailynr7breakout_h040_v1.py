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
NAME = "DailyNR7Breakout_H040_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, NAME)


Strategy = load()


def make_frame(n, seed=5):
    rng = np.random.default_rng(seed)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.0004, 0.006, n))))
    spread = rng.uniform(0.001, 0.02, n)
    return pd.DataFrame(
        {
            "date": pd.date_range("2022-01-01", periods=n, freq="1h", tz="UTC"),
            "open": close,
            "high": close * (1 + spread),
            "low": close * (1 - spread),
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


N = 24 * 400


class NR7Tests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.03)
        self.assertGreaterEqual(Strategy.startup_candle_count, 1500)

    def test_nr7_definition(self) -> None:
        rng = np.random.default_rng(1)
        high = 100 + rng.uniform(1, 5, 60)
        daily = pd.DataFrame({"high": high, "low": np.full(60, 100.0), "close": high})
        out = Strategy().populate_indicators_1d(daily, {})
        ranges = high - 100.0
        for i in range(60):
            if i < 6:
                self.assertTrue(pd.isna(out.loc[i, "nr7"]))
            else:
                expected = float(all(ranges[i] < ranges[i - k] for k in range(1, 7)))
                self.assertEqual(out.loc[i, "nr7"], expected)
        self.assertTrue(pd.isna(out.loc[48, "sma50"]))
        self.assertAlmostEqual(out.loc[59, "sma50"], high[10:60].mean())

    def test_binary_signals_and_activity(self) -> None:
        out = run(Strategy(), make_frame(N))
        for column in ("enter_long", "exit_long"):
            self.assertIn(column, out)
            self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(out["enter_long"].fillna(0).sum(), 0)
        entries = out[out["enter_long"] == 1]
        self.assertTrue((entries["date"].dt.hour <= 19).all())
        self.assertEqual(entries["date"].dt.floor("D").duplicated().sum(), 0)
        self.assertTrue((entries["close"] > entries["high_1d"]).all())
        self.assertTrue((entries["close_1d"] > entries["sma50_1d"]).all())

    def test_zero_volume_no_signal(self) -> None:
        frame = make_frame(N)
        frame["volume"] = 0.0
        out = run(Strategy(), frame)
        self.assertEqual(out.get("enter_long", pd.Series(0)).fillna(0).sum(), 0)
        self.assertEqual(out.get("exit_long", pd.Series(0)).fillna(0).sum(), 0)

    def test_startup_nan_no_signal(self) -> None:
        out = run(Strategy(), make_frame(N))
        first_valid = out["sma50_1d"].first_valid_index()
        self.assertGreaterEqual(first_valid, 50 * 24)
        head = out.iloc[:first_valid]
        self.assertEqual(head.get("enter_long", pd.Series(0)).fillna(0).sum(), 0)
        self.assertEqual(head.get("exit_long", pd.Series(0)).fillna(0).sum(), 0)

    def test_no_lookahead(self) -> None:
        full = make_frame(N + 24 * 30)
        n = N + 5
        strategy = Strategy()
        short = run(strategy, full.iloc[:n].copy())
        long = run(strategy, full.copy())
        cols = ["enter_long", "exit_long"]
        a = short[cols].fillna(0).iloc[:n].reset_index(drop=True)
        b = long[cols].fillna(0).iloc[:n].reset_index(drop=True)
        pd.testing.assert_frame_equal(a, b, check_dtype=False)


if __name__ == "__main__":
    unittest.main()
