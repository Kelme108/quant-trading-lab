import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

freqtrade = types.ModuleType("freqtrade")
strategy_module = types.ModuleType("freqtrade.strategy")
strategy_module.IStrategy = object
strategy_module.merge_informative_pair = lambda *a, **k: a[0]
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
NAME = "EfficiencyRatioThrust_H119_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Pandas stand-in for TA-Lib ATR (Wilder smoothing, first value after 14 true ranges).
def _atr(dataframe, timeperiod):
    high, low, close = dataframe["high"], dataframe["low"], dataframe["close"]
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    tr.iloc[0] = np.nan
    out = tr.ewm(alpha=1 / timeperiod, adjust=False).mean()
    out.iloc[:timeperiod] = np.nan
    return out


MODULE = load()
MODULE.ta = types.SimpleNamespace(ATR=_atr)
Strategy = getattr(MODULE, NAME)


def make_frame(n=700, seed=7):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.003, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.003, n))
    volume = rng.lognormal(3, 0.6, n)
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume})


def run(strategy, frame):
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


def count(frame, column):
    return int(frame[column].fillna(0).sum()) if column in frame else 0


def crafted(n=60):
    """Indicator frame with a clean ER cross above 0.6 on the last row."""
    frame = pd.DataFrame(
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 10.0,
         "er": 0.2, "er_prev": 0.2, "atr_ratio": 0.005},
        index=range(n),
    )
    frame.loc[n - 1, "er"] = 0.65
    frame.loc[n - 1, "er_prev"] = 0.6  # exactly 0.6 counts as the lower side
    return frame


class DataProviderStub:
    def __init__(self, frame):
        self.frame = frame

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.frame, None


class EfficiencyRatioThrustTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.10)
        self.assertTrue(Strategy.use_custom_stoploss)
        self.assertGreaterEqual(Strategy.startup_candle_count, 400)

    def test_signal_columns_are_binary(self):
        out = run(Strategy(), make_frame())
        self.assertGreater(count(out, "enter_long"), 0)
        for column in ("enter_long", "exit_long"):
            if column in out:
                self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_gives_no_signal(self):
        strategy = Strategy()
        frame = crafted()
        frame.loc[len(frame) - 1, "volume"] = 0.0
        self.assertEqual(count(strategy.populate_entry_trend(frame, {}), "enter_long"), 0)
        frame = make_frame()
        frame["volume"] = 0.0
        out = run(strategy, frame)
        self.assertEqual(count(out, "enter_long"), 0)
        self.assertEqual(count(out, "exit_long"), 0)

    def test_undefined_values_give_no_signal(self):
        strategy = Strategy()
        for column in ("er", "er_prev", "atr_ratio"):
            frame = crafted()
            frame.loc[len(frame) - 1, column] = np.nan
            self.assertEqual(count(strategy.populate_entry_trend(frame, {}), "enter_long"), 0, column)
        out = run(strategy, make_frame())
        self.assertEqual(count(out.iloc[:15], "enter_long"), 0)
        self.assertTrue(out["er"].iloc[:10].isna().all())
        self.assertTrue(out["atr_ratio"].iloc[:14].isna().all())

    def test_entry_needs_all_conditions(self):
        strategy = Strategy()
        out = strategy.populate_entry_trend(crafted(), {})
        self.assertEqual(count(out, "enter_long"), 1)
        self.assertEqual(out.loc[59, "enter_long"], 1)
        for column, value in (("er", 0.6), ("er_prev", 0.61), ("atr_ratio", 0.0039)):
            frame = crafted()
            frame.loc[59, column] = value
            self.assertEqual(count(strategy.populate_entry_trend(frame, {}), "enter_long"), 0, column)
        frame = crafted()
        frame.loc[59, "atr_ratio"] = 0.004  # exactly the minimum passes
        self.assertEqual(count(strategy.populate_entry_trend(frame, {}), "enter_long"), 1)

    def test_efficiency_ratio_values(self):
        n = 30
        frame = make_frame(n)
        frame["close"] = 100.0 + np.arange(n)  # straight climb: ER = 1
        out = Strategy().populate_indicators(frame, {})
        self.assertTrue(out["er"].iloc[:10].isna().all())
        self.assertAlmostEqual(float(out.loc[10, "er"]), 1.0)
        # zigzag: +1, -1 repeated -> net 0 over 10 bars
        frame = make_frame(n)
        frame["close"] = [100.0 + (i % 2) for i in range(n)]
        out = Strategy().populate_indicators(frame, {})
        self.assertAlmostEqual(float(out.loc[20, "er"]), 0.0)
        # flat: denominator 0 -> ER = 0
        frame = make_frame(n)
        frame["close"] = 100.0
        out = Strategy().populate_indicators(frame, {})
        self.assertEqual(float(out.loc[20, "er"]), 0.0)
        # mixed: closes 0,2,1,3,4,5,6,5,7,8,9 -> net 9 over path 1*? computed directly
        closes = [100, 102, 101, 103, 104, 105, 106, 105, 107, 108, 109.0]
        frame = make_frame(len(closes))
        frame["close"] = closes
        out = Strategy().populate_indicators(frame, {})
        path = sum(abs(closes[i] - closes[i - 1]) for i in range(1, 11))
        self.assertAlmostEqual(float(out.loc[10, "er"]), (closes[10] - closes[0]) / path)

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        strategy = Strategy()
        frame = make_frame(900)
        n = 600
        short = run(strategy, frame.iloc[:n])
        long = run(strategy, frame)
        for column in ("er", "er_prev", "atr_ratio", "low10"):
            pd.testing.assert_series_equal(short[column], long[column].iloc[:n], check_names=False)
        a = short["enter_long"].fillna(0) if "enter_long" in short else pd.Series(0, index=short.index)
        b = long["enter_long"].iloc[:n].fillna(0) if "enter_long" in long else pd.Series(0, index=short.index)
        pd.testing.assert_series_equal(a, b, check_dtype=False)

    def _stop_setup(self, low10_values):
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        n = len(low10_values)
        frame = pd.DataFrame(
            {"date": [start + timedelta(minutes=15 * i) for i in range(n)], "low10": low10_values}
        )
        strategy = Strategy()
        strategy.dp = DataProviderStub(frame)
        return strategy, start

    def test_custom_stoploss_initial_trailing_and_never_lowered(self):
        low10 = [90.0] * 20 + [98.0, 98.5, 99.5, 97.0, 96.0]  # indexes 20..24
        strategy, start = self._stop_setup(low10)
        trade = types.SimpleNamespace(open_date_utc=start + timedelta(minutes=15 * 21), open_rate=100.0)
        rate = 101.0
        # at bar 21's open only bar 20 (the signal bar) is closed: S0 = min(98, 99) = 98
        now = start + timedelta(minutes=15 * 21)
        self.assertAlmostEqual(strategy.custom_stoploss("BTC/USDT", trade, now, rate, 0.01), 1 - 98.0 / rate)
        # at bar 23's open bars 20..22 are closed: S = max(98, 98.5, 99.5) = 99.5
        now = start + timedelta(minutes=15 * 23)
        self.assertAlmostEqual(strategy.custom_stoploss("BTC/USDT", trade, now, rate, 0.01), 1 - 99.5 / rate)
        # at bar 25 bars 23, 24 have lower 10-bar lows: the level is not lowered
        now = start + timedelta(minutes=15 * 25)
        self.assertAlmostEqual(strategy.custom_stoploss("BTC/USDT", trade, now, rate, 0.01), 1 - 99.5 / rate)
        # the bar that is still open at `now` is not used
        now = start + timedelta(minutes=15 * 22)
        self.assertAlmostEqual(strategy.custom_stoploss("BTC/USDT", trade, now, rate, 0.01), 1 - 98.5 / rate)

    def test_initial_stop_is_at_least_one_percent_below_entry(self):
        low10 = [90.0] * 20 + [99.6, 99.7]
        strategy, start = self._stop_setup(low10)
        trade = types.SimpleNamespace(open_date_utc=start + timedelta(minutes=15 * 21), open_rate=100.0)
        now = start + timedelta(minutes=15 * 21)
        self.assertAlmostEqual(strategy.custom_stoploss("BTC/USDT", trade, now, 100.5, 0.0), 1 - 99.0 / 100.5)

    def test_custom_stoploss_without_data_keeps_backstop(self):
        strategy, start = self._stop_setup([90.0] * 5)
        trade = types.SimpleNamespace(open_date_utc=start + timedelta(minutes=15 * 50), open_rate=100.0)
        self.assertIsNone(strategy.custom_stoploss("BTC/USDT", trade, start + timedelta(minutes=15 * 50), 100.0, 0.0))

    def test_time_exit_after_32_bars(self):
        strategy = Strategy()
        opened = datetime(2025, 1, 1, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_date_utc=opened)
        before = opened + timedelta(hours=7, minutes=45)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, before, 100.0, 0.0))
        at = opened + timedelta(hours=8)
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, at, 100.0, 0.0), "time_exit_8h")

    def test_take_profit_at_two_percent(self):
        strategy = Strategy()
        opened = datetime(2025, 1, 1, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_date_utc=opened)
        now = opened + timedelta(hours=1)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, now, 101.9, 0.019))
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, now, 102.0, 0.02), "take_profit_2pct")


if __name__ == "__main__":
    unittest.main()
