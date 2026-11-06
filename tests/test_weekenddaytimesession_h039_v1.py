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
NAME = "WeekendDaytimeSession_H039_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, NAME)


Strategy = load()


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
    """Emulate Freqtrade's informative 1d merge (value visible after the day closed)."""
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


def hourly_from_daily(daily):
    return [price for price in daily for _ in range(24)]


def uptrend_prices(days):
    rng = np.random.default_rng(5)
    steps = rng.normal(0.004, 0.02, days)
    return list(100 * np.exp(np.cumsum(steps)))


class WeekendSessionTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.03)
        self.assertGreaterEqual(Strategy.startup_candle_count, 1250)

    def test_binary_and_weekend_hours(self) -> None:
        out = run(Strategy(), make_frame(hourly_from_daily(uptrend_prices(300))))
        for column in ("enter_long", "exit_long"):
            self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))
        entries = out[out["enter_long"] == 1]
        self.assertGreater(len(entries), 0)
        self.assertTrue((entries["date"].dt.hour == 12).all())
        self.assertTrue((entries["date"].dt.dayofweek >= 5).all())
        self.assertTrue((entries.groupby(entries["date"].dt.date).size() == 1).all())
        self.assertTrue((entries["close_1d"] > entries["sma50_1d"]).all())
        exits = out[out["exit_long"] == 1]
        self.assertTrue((exits["date"].dt.hour != 12).all())
        self.assertTrue((exits["date"].dt.hour != 19).all())
        self.assertTrue((out.loc[out["date"].dt.hour == 20, "exit_long"] == 1).all())

    def test_downtrend_no_entry(self) -> None:
        prices = list(np.linspace(300, 100, 300))
        out = run(Strategy(), make_frame(hourly_from_daily(prices)))
        self.assertEqual(out["enter_long"].fillna(0).sum(), 0)

    def test_zero_volume_no_signal(self) -> None:
        frame = make_frame(hourly_from_daily(uptrend_prices(300)))
        frame["volume"] = 0.0
        out = run(Strategy(), frame)
        self.assertEqual(out["enter_long"].fillna(0).sum(), 0)
        self.assertEqual(out["exit_long"].fillna(0).sum(), 0)

    def test_startup_nan_no_entry(self) -> None:
        out = run(Strategy(), make_frame(hourly_from_daily(uptrend_prices(300))))
        first_valid = out["sma50_1d"].first_valid_index()
        self.assertGreaterEqual(first_valid, 50 * 24)
        self.assertEqual(out.iloc[:first_valid]["enter_long"].fillna(0).sum(), 0)

    def test_no_lookahead(self) -> None:
        full = make_frame(hourly_from_daily(uptrend_prices(320)))
        n = 280 * 24 + 5
        strategy = Strategy()
        short = run(strategy, full.iloc[:n].copy())
        long = run(strategy, full.copy())
        cols = ["enter_long", "exit_long"]
        a = short[cols].fillna(0).iloc[:n].reset_index(drop=True)
        b = long[cols].fillna(0).iloc[:n].reset_index(drop=True)
        pd.testing.assert_frame_equal(a, b, check_dtype=False)


if __name__ == "__main__":
    unittest.main()
