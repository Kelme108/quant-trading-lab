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

# The `informative` decorator is only stubbed (identity); the merge is emulated below.
_strategy_mod = sys.modules["freqtrade.strategy"]
if not hasattr(_strategy_mod, "informative"):
    _strategy_mod.informative = lambda *args, **kwargs: (lambda function: function)

ROOT = Path(__file__).parents[2]
NAME = "Double7ChannelDip_H020_v1"


def load():
    path = ROOT / "user_data" / "strategies" / "_archive" / f"{NAME}.py"
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
    rng = np.random.default_rng(7)
    steps = rng.normal(0.002, 0.03, days)
    return list(100 * np.exp(np.cumsum(steps)))


class Double7Tests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 200)

    def test_entry_and_exit_logic(self) -> None:
        # 230 rising days, then 7 falling days (new 7-day closing low above SMA200), then a jump.
        daily = [100 + i for i in range(230)] + [329 - 3 * i for i in range(1, 8)] + [400]
        out = run(Strategy(), make_frame(daily_closes_to_hourly(daily)))
        day = lambda i: out.iloc[i * 24 : (i + 1) * 24]
        # Daily value of day i is visible from day i+1.
        # Day 236 closes at a 7-day low above SMA200 -> entry visible during day 237.
        self.assertEqual(day(237)["enter_long"].fillna(0).sum(), 24)
        # Day 230 (326) is not yet below the prior 7-day minimum, so nothing is visible on day 231.
        self.assertEqual(day(231)["enter_long"].fillna(0).sum(), 0)
        self.assertEqual(day(232)["enter_long"].fillna(0).sum(), 24)
        self.assertEqual(day(237).get("exit_long", pd.Series(0)).fillna(0).sum(), 0)
        # Day 237 closes at a 7-day high -> exit visible during day 238.
        longer = run(Strategy(), make_frame(daily_closes_to_hourly(daily + [401])))
        self.assertEqual(longer.iloc[238 * 24 : 239 * 24]["exit_long"].fillna(0).sum(), 24)

    def test_binary_signals(self) -> None:
        out = run(Strategy(), make_frame(daily_closes_to_hourly(wavy_prices(400))))
        for column in ("enter_long", "exit_long"):
            self.assertIn(column, out)
            self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(out["enter_long"].fillna(0).sum(), 0)
        self.assertGreater(out["exit_long"].fillna(0).sum(), 0)

    def test_zero_volume_no_signal(self) -> None:
        frame = make_frame(daily_closes_to_hourly(wavy_prices(400)))
        frame["volume"] = 0.0
        out = run(Strategy(), frame)
        self.assertEqual(out.get("enter_long", pd.Series(0)).fillna(0).sum(), 0)
        self.assertEqual(out.get("exit_long", pd.Series(0)).fillna(0).sum(), 0)

    def test_startup_nan_no_entry(self) -> None:
        frame = make_frame(daily_closes_to_hourly(wavy_prices(400)))
        out = run(Strategy(), frame)
        first_valid = out["sma200_1d"].first_valid_index()
        early = out.iloc[:first_valid]
        self.assertEqual(early.get("enter_long", pd.Series(0)).fillna(0).sum(), 0)
        # Exit needs only the 7-day channel, so it must stay silent before 7 daily values.
        self.assertEqual(out.iloc[: 7 * 24].get("exit_long", pd.Series(0)).fillna(0).sum(), 0)

    def test_no_lookahead(self) -> None:
        full = make_frame(daily_closes_to_hourly(wavy_prices(420)))
        n = 330 * 24 + 5  # cut mid-day
        strategy = Strategy()
        short = run(strategy, full.iloc[:n].copy())
        long = run(strategy, full.copy())
        cols = ["enter_long", "exit_long"]
        a = short[cols].fillna(0).iloc[:n].reset_index(drop=True)
        b = long[cols].fillna(0).iloc[:n].reset_index(drop=True)
        pd.testing.assert_frame_equal(a, b, check_dtype=False)


if __name__ == "__main__":
    unittest.main()
