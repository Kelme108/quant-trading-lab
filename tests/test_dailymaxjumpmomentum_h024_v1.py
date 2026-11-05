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
NAME = "DailyMaxJumpMomentum_H024_v1"


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


def daily_closes_to_hourly(daily):
    return [price for price in daily for _ in range(24)]


def wavy_prices(days):
    rng = np.random.default_rng(11)
    steps = rng.normal(0.003, 0.04, days)
    return list(100 * np.exp(np.cumsum(steps)))


class MaxJumpTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.12)
        self.assertGreaterEqual(Strategy.startup_candle_count, 4320)
        self.assertLessEqual(Strategy.startup_candle_count, 4500)
        prot = Strategy().protections
        self.assertEqual(prot[0]["method"], "CooldownPeriod")
        self.assertEqual(prot[0]["stop_duration_candles"], 72)

    def test_indicator_definitions(self) -> None:
        closes = wavy_prices(300)
        daily = pd.DataFrame({"close": closes})
        out = Strategy().populate_indicators_1d(daily, {})
        r = daily["close"].pct_change()
        d = 250
        self.assertAlmostEqual(out.loc[d, "max30"], r.iloc[d - 29 : d + 1].max())
        prev = [r.iloc[k - 29 : k + 1].max() for k in range(d - 150, d)]
        self.assertAlmostEqual(out.loc[d, "max_median150"], float(np.median(prev)))
        self.assertAlmostEqual(out.loc[d, "high10_prev"], max(closes[d - 10 : d]))
        self.assertAlmostEqual(out.loc[d, "sma50"], np.mean(closes[d - 49 : d + 1]))
        self.assertAlmostEqual(out.loc[d, "sma20"], np.mean(closes[d - 19 : d + 1]))
        self.assertTrue(pd.isna(out.loc[179, "max_median150"]))
        self.assertFalse(pd.isna(out.loc[180, "max_median150"]))

    def test_binary_signals(self) -> None:
        out = run(Strategy(), make_frame(daily_closes_to_hourly(wavy_prices(500))))
        for column in ("enter_long", "exit_long"):
            self.assertIn(column, out)
            self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(out["enter_long"].fillna(0).sum(), 0)
        self.assertGreater(out["exit_long"].fillna(0).sum(), 0)

    def test_zero_volume_no_signal(self) -> None:
        frame = make_frame(daily_closes_to_hourly(wavy_prices(500)))
        frame["volume"] = 0.0
        out = run(Strategy(), frame)
        self.assertEqual(out.get("enter_long", pd.Series(0)).fillna(0).sum(), 0)
        self.assertEqual(out.get("exit_long", pd.Series(0)).fillna(0).sum(), 0)

    def test_startup_nan_no_entry(self) -> None:
        out = run(Strategy(), make_frame(daily_closes_to_hourly(wavy_prices(500))))
        first_valid = out["max_median150_1d"].first_valid_index()
        self.assertGreaterEqual(first_valid, 180 * 24)
        self.assertEqual(out.iloc[:first_valid].get("enter_long", pd.Series(0)).fillna(0).sum(), 0)
        # Exit needs only SMA20: silent before 20 daily values.
        self.assertEqual(out.iloc[: 20 * 24].get("exit_long", pd.Series(0)).fillna(0).sum(), 0)

    def test_no_lookahead(self) -> None:
        full = make_frame(daily_closes_to_hourly(wavy_prices(520)))
        n = 450 * 24 + 5  # cut mid-day
        strategy = Strategy()
        short = run(strategy, full.iloc[:n].copy())
        long = run(strategy, full.copy())
        cols = ["enter_long", "exit_long"]
        a = short[cols].fillna(0).iloc[:n].reset_index(drop=True)
        b = long[cols].fillna(0).iloc[:n].reset_index(drop=True)
        pd.testing.assert_frame_equal(a, b, check_dtype=False)


if __name__ == "__main__":
    unittest.main()
