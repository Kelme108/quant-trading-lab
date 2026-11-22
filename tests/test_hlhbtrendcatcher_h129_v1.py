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
NAME = "HLHBTrendCatcher_H129_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Pandas stand-ins for the TA-Lib functions the strategy needs (the shared stub only has SMA/RSI).
def _ema(dataframe, timeperiod):
    out = dataframe["close"].ewm(span=timeperiod, adjust=False).mean()
    out.iloc[: timeperiod - 1] = np.nan
    return out


def _rsi(dataframe, timeperiod):
    delta = dataframe["close"].diff()
    up = delta.clip(lower=0).ewm(alpha=1 / timeperiod, adjust=False).mean()
    down = (-delta.clip(upper=0)).ewm(alpha=1 / timeperiod, adjust=False).mean()
    out = 100 - 100 / (1 + up / down.replace(0, np.nan))
    out.iloc[:timeperiod] = np.nan
    return out


def _adx(dataframe, timeperiod):
    high, low, close = dataframe["high"], dataframe["low"], dataframe["close"]
    up, down = high.diff(), -low.diff()
    plus = ((up > down) & (up > 0)) * up
    minus = ((down > up) & (down > 0)) * down
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    alpha = 1 / timeperiod
    atr = tr.ewm(alpha=alpha, adjust=False).mean()
    pdi = 100 * plus.ewm(alpha=alpha, adjust=False).mean() / atr
    mdi = 100 * minus.ewm(alpha=alpha, adjust=False).mean() / atr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    out = dx.ewm(alpha=alpha, adjust=False).mean()
    out.iloc[: 2 * timeperiod] = np.nan
    return out


MODULE = load()
MODULE.ta = types.SimpleNamespace(EMA=_ema, RSI=_rsi, ADX=_adx)
Strategy = getattr(MODULE, NAME)


def make_frame(n=700, seed=5):
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
    """Indicator frame with a clean double cross up on the last row."""
    frame = pd.DataFrame(
        {
            "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 10.0,
            "ema_fast": 99.0, "ema_slow": 100.0, "ema_fast_prev": 99.0, "ema_slow_prev": 100.0,
            "rsi_mp": 45.0, "rsi_mp_prev": 45.0, "adx": 30.0, "vmean": 10.0,
        },
        index=range(n),
    )
    last = n - 1
    frame.loc[last, ["ema_fast", "rsi_mp", "volume"]] = [101.0, 55.0, 15.0]
    frame.loc[last, "rsi_mp_prev"] = 50.0  # <= 50 counts as the previous side
    return frame


class HLHBTrendCatcherTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.015)
        self.assertGreaterEqual(Strategy.startup_candle_count, 400)
        self.assertTrue(Strategy.trailing_stop)
        self.assertEqual(Strategy.trailing_stop_positive, 0.012)
        self.assertEqual(Strategy.trailing_stop_positive_offset, 0.019)
        self.assertTrue(Strategy.trailing_only_offset_is_reached)

    def test_signal_columns_are_binary(self):
        out = run(Strategy(), make_frame())
        for column in ("enter_long", "exit_long"):
            if column in out:
                self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_gives_no_signal(self):
        strategy = Strategy()
        frame = crafted()
        frame.loc[len(frame) - 1, "volume"] = 0.0
        out = strategy.populate_entry_trend(frame, {})
        self.assertEqual(count(out, "enter_long"), 0)
        frame = make_frame()
        frame["volume"] = 0.0
        out = run(strategy, frame)
        self.assertEqual(int(out.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(out.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_undefined_startup_values_give_no_signal(self):
        strategy = Strategy()
        for column in ("ema_slow", "rsi_mp_prev", "adx", "vmean"):
            frame = crafted()
            frame.loc[len(frame) - 1, column] = np.nan
            out = strategy.populate_entry_trend(frame, {})
            self.assertEqual(count(out, "enter_long"), 0, column)
        out = run(strategy, make_frame())
        head = out.iloc[:21]
        self.assertEqual(int(head.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(head.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_entry_needs_all_conditions(self):
        strategy = Strategy()
        out = strategy.populate_entry_trend(crafted(), {})
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 1)
        self.assertEqual(out.loc[59, "enter_long"], 1)
        for column, value in (("adx", 25.0), ("volume", 14.9), ("rsi_mp_prev", 51.0), ("ema_fast_prev", 101.0)):
            frame = crafted()
            frame.loc[59, column] = value
            out = strategy.populate_entry_trend(frame, {})
            self.assertEqual(count(out, "enter_long"), 0, column)
        frame = crafted()
        frame.loc[59, "volume"] = 15.0  # exactly 1.5x the mean passes
        self.assertEqual(count(strategy.populate_entry_trend(frame, {}), "enter_long"), 1)

    def test_mirror_exit(self):
        strategy = Strategy()
        frame = crafted()
        frame["ema_fast"], frame["ema_slow"] = 101.0, 100.0
        frame["ema_fast_prev"], frame["ema_slow_prev"] = 101.0, 100.0
        frame["rsi_mp"], frame["rsi_mp_prev"] = 55.0, 55.0
        frame.loc[59, ["ema_fast", "rsi_mp"]] = [99.0, 45.0]
        out = strategy.populate_exit_trend(frame, {})
        self.assertEqual(int(out["exit_long"].fillna(0).sum()), 1)
        self.assertEqual(out.loc[59, "exit_long"], 1)
        # only one of the two crosses is not enough
        frame = frame.drop(columns=["exit_long", "exit_tag"])
        frame.loc[59, "rsi_mp"] = 55.0
        self.assertEqual(count(strategy.populate_exit_trend(frame, {}), "exit_long"), 0)

    def test_time_exit_after_12_hours(self):
        strategy = Strategy()
        opened = datetime(2025, 1, 1, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_date_utc=opened)
        before = opened + timedelta(hours=11, minutes=45)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, before, 100.0, 0.0))
        at = opened + timedelta(hours=12)
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, at, 100.0, 0.0), "time_exit_12h")

    def test_no_take_profit(self):
        strategy = Strategy()
        opened = datetime(2025, 1, 1, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_date_utc=opened)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, opened + timedelta(hours=1), 110.0, 0.10))

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        strategy = Strategy()
        frame = make_frame(900)
        n = 600
        short = run(strategy, frame.iloc[:n])
        long = run(strategy, frame)
        for column in ("ema_fast", "ema_slow", "rsi_mp", "adx", "vmean"):
            pd.testing.assert_series_equal(short[column], long[column].iloc[:n], check_names=False)
        for column in ("enter_long", "exit_long"):
            a = short[column].fillna(0) if column in short else pd.Series(0, index=short.index)
            b = long[column].iloc[:n].fillna(0) if column in long else pd.Series(0, index=short.index)
            pd.testing.assert_series_equal(a, b, check_dtype=False)

    def test_volume_mean_excludes_current_bar(self):
        frame = make_frame(60)
        frame["volume"] = 1.0
        frame.loc[59, "volume"] = 10.0
        out = Strategy().populate_indicators(frame, {})
        self.assertAlmostEqual(float(out.loc[59, "vmean"]), 1.0)
        self.assertTrue(out["vmean"].iloc[:20].isna().all())


if __name__ == "__main__":
    unittest.main()
