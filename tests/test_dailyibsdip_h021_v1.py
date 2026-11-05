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
NAME = "DailyIBSDip_H021_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, NAME)


Strategy = load()


def hourly_from_daily(daily_ohlc):
    """daily_ohlc: list of (open, high, low, close); each day becomes 24 hourly candles
    whose aggregate is exactly that daily candle."""
    rows = []
    for o, h, l, c in daily_ohlc:
        for hour in range(24):
            if hour == 0:
                ho, hh, hl, hc = o, o, o, o
            elif hour == 1:
                ho, hh, hl, hc = o, h, l, l
            elif hour == 2:
                ho, hh, hl, hc = l, h, l, h
            else:
                ho, hh, hl, hc = c, c, c, c
            if hour == 23:
                hc = c
            rows.append((ho, hh, hl, hc))
    n = len(rows)
    frame = pd.DataFrame(rows, columns=["open", "high", "low", "close"])
    frame.insert(0, "date", pd.date_range("2022-01-01", periods=n, freq="1h", tz="UTC"))
    frame["volume"] = 1.0
    return frame


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


def wavy_days(days, seed=7):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0.003, 0.03, days)))
    out = []
    prev = 100.0
    for c in close:
        hi = max(prev, c) * (1 + abs(rng.normal(0, 0.015)))
        lo = min(prev, c) * (1 - abs(rng.normal(0, 0.015)))
        out.append((prev, hi, lo, c))
        prev = c
    return out


def rising_days(n):
    return [(100 + i, 101 + i, 99 + i, 100.5 + i) for i in range(n)]


class DailyIBSDipTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.12)
        self.assertGreaterEqual(Strategy.startup_candle_count, 200)

    def test_entry_and_exit_logic(self) -> None:
        # 230 rising days; day 230 closes near its low (IBS 0.1) above SMA200 -> entry.
        days = rising_days(230)
        days.append((330, 340, 320, 322))  # IBS = 0.1
        days.append((322, 330, 320, 329))  # IBS = 0.9 -> exit
        days.append((329, 330, 328, 329))  # flat filler
        out = run(Strategy(), hourly_from_daily(days))
        day = lambda i: out.iloc[i * 24 : (i + 1) * 24]
        self.assertEqual(day(231)["enter_long"].fillna(0).sum(), 24)
        self.assertEqual(day(231).get("exit_long", pd.Series(0)).fillna(0).sum(), 0)
        self.assertEqual(day(232)["exit_long"].fillna(0).sum(), 24)
        self.assertEqual(day(232)["enter_long"].fillna(0).sum(), 0)
        self.assertEqual(day(230)["enter_long"].fillna(0).sum(), 0)

    def test_safety_exit_below_sma(self) -> None:
        days = rising_days(230) + [(330, 331, 100, 101), (101, 102, 100, 101.5)]
        out = run(Strategy(), hourly_from_daily(days))
        # Day 230 closes at 101 < SMA200, IBS ~0.004: no entry, safety exit visible day 231.
        self.assertEqual(out.iloc[231 * 24 : 232 * 24]["enter_long"].fillna(0).sum(), 0)
        self.assertEqual(out.iloc[231 * 24 : 232 * 24]["exit_long"].fillna(0).sum(), 24)

    def test_zero_range_day_has_no_ibs(self) -> None:
        days = rising_days(230) + [(330, 330, 330, 330), (330, 331, 329, 330)]
        out = run(Strategy(), hourly_from_daily(days))
        self.assertTrue(pd.isna(out.iloc[231 * 24]["ibs_1d"]))
        self.assertEqual(out.iloc[231 * 24 : 232 * 24]["enter_long"].fillna(0).sum(), 0)
        self.assertEqual(out.iloc[231 * 24 : 232 * 24].get("exit_long", pd.Series(0)).fillna(0).sum(), 0)

    def test_binary_signals(self) -> None:
        out = run(Strategy(), hourly_from_daily(wavy_days(500)))
        for column in ("enter_long", "exit_long"):
            self.assertIn(column, out)
            self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(out["enter_long"].fillna(0).sum(), 0)
        self.assertGreater(out["exit_long"].fillna(0).sum(), 0)

    def test_zero_volume_no_signal(self) -> None:
        frame = hourly_from_daily(wavy_days(500))
        frame["volume"] = 0.0
        out = run(Strategy(), frame)
        self.assertEqual(out.get("enter_long", pd.Series(0)).fillna(0).sum(), 0)
        self.assertEqual(out.get("exit_long", pd.Series(0)).fillna(0).sum(), 0)

    def test_startup_nan_no_signal(self) -> None:
        out = run(Strategy(), hourly_from_daily(wavy_days(500)))
        first_valid = out["sma200_1d"].first_valid_index()
        early = out.iloc[:first_valid]
        self.assertEqual(early.get("enter_long", pd.Series(0)).fillna(0).sum(), 0)
        # The safety exit needs SMA200, but the IBS exit does not; it may fire earlier.
        nan_rows = out[out["ibs_1d"].isna()]
        if "exit_long" in nan_rows:
            self.assertEqual(nan_rows["exit_long"].fillna(0).sum(), 0)

    def test_no_lookahead(self) -> None:
        full = hourly_from_daily(wavy_days(520))
        n = 450 * 24 + 5
        strategy = Strategy()
        short = run(strategy, full.iloc[:n].copy())
        long = run(strategy, full.copy())
        cols = ["enter_long", "exit_long"]
        a = short[cols].fillna(0).iloc[:n].reset_index(drop=True)
        b = long[cols].fillna(0).iloc[:n].reset_index(drop=True)
        pd.testing.assert_frame_equal(a, b, check_dtype=False)


if __name__ == "__main__":
    unittest.main()
