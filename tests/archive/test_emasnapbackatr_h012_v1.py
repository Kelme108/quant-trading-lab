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
if not hasattr(sys.modules["freqtrade.strategy"], "stoploss_from_absolute"):
    sys.modules["freqtrade.strategy"].stoploss_from_absolute = lambda stop, rate, is_short=False: 1 - stop / rate

# Stub of TA-Lib, shared with the other strategy tests: keep the functions they rely on.
talib = types.ModuleType("talib")
talib_abstract = types.ModuleType("talib.abstract")
talib_abstract.SMA = lambda dataframe, timeperiod: dataframe["close"].rolling(timeperiod).mean()
talib_abstract.RSI = lambda dataframe, timeperiod: pd.Series(50.0, index=dataframe.index)
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)

ROOT = Path(__file__).parents[2]


def load(name):
    path = ROOT / "user_data" / "strategies" / "_archive" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MOD = load("EMASnapbackATR_H012_v1")
MOD4H = load("EMASnapbackATR_H014_v1")


def frame(close, volume=None):
    close = pd.Series(close, dtype=float)
    return pd.DataFrame({
        "close": close,
        "high": close + 0.1,
        "volume": pd.Series(1.0 if volume is None else volume, index=close.index, dtype=float),
    })


def scenario():
    """Flat 100, a drop to 94 (stretch), then a candle that closes above the prior high, below EMA20."""
    close = [100.0] * 30 + [99.0, 97.0, 95.0, 94.0, 94.0, 94.8]
    df = frame(close)
    df["ema"] = 100.0
    df["trend"] = 80.0
    df["atr"] = 1.0
    df["rsi"] = 50.0
    return df


def run(df, **kwargs):
    return MOD.snapback_signal(df["high"], df["close"], df["volume"], df["ema"], df["trend"], df["atr"],
                               df["rsi"], **kwargs)


class SignalTests(unittest.TestCase):
    def test_signals_on_confirmation_candle_only(self):
        df = scenario()
        signal = run(df)
        self.assertEqual(list(np.flatnonzero(signal)), [35])  # 94.8 > prior high 94.1, still below EMA

    def test_no_signal_while_still_falling(self):
        df = scenario().iloc[:34]  # last close 94.0, not above the prior high
        self.assertFalse(run(df).any())

    def test_trend_filter_blocks(self):
        df = scenario()
        df["trend"] = 120.0
        self.assertFalse(run(df).any())

    def test_stretch_must_be_deep_enough(self):
        df = scenario()
        self.assertFalse(run(df, z_entry=7.0).any())
        self.assertTrue(run(df, z_entry=5.0).any())

    def test_stretch_expires_after_lookback(self):
        df = frame([100.0] * 30 + [94.0, 94.5, 96.0, 98.0, 99.0, 99.5, 99.0, 98.6, 99.2])
        df["ema"], df["trend"], df["atr"], df["rsi"] = 100.0, 80.0, 1.0, 50.0
        self.assertFalse(run(df, lookback=4).iloc[38])  # the 94.0 stretch is 8 candles old
        self.assertTrue(run(df, lookback=9).iloc[38])

    def test_rsi_and_volume_filters_are_optional_and_work(self):
        df = scenario()
        self.assertFalse(run(df, use_rsi=True, rsi_max=35.0).any())
        df["rsi"] = 25.0
        self.assertTrue(run(df, use_rsi=True, rsi_max=35.0).any())
        self.assertFalse(run(df, use_volume=True, volume_mult=2.0).any())
        df.loc[35, "volume"] = 5.0
        self.assertTrue(run(df, use_volume=True, volume_mult=2.0).any())

    def test_prefix_signals_equal_full_series_signals(self):
        rng = np.random.default_rng(11)
        n = 3000
        close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, n))))
        df = pd.DataFrame({"close": close, "high": close * 1.002, "volume": rng.uniform(0.5, 2, n)})
        df["ema"] = df["close"].ewm(span=20, adjust=False).mean()
        df["trend"] = df["close"].ewm(span=200, adjust=False).mean()
        df["atr"] = (df["high"] - df["close"]).abs().rolling(14).mean() + 0.5
        df["rsi"] = 50.0
        full = run(df, z_entry=1.5)
        self.assertGreater(int(full.sum()), 0)
        for cut in (500, 1234, 2500):
            part = run(df.iloc[:cut], z_entry=1.5)
            pd.testing.assert_series_equal(part, full.iloc[:cut])


class ContractTests(unittest.TestCase):
    def test_contract(self):
        cls = MOD.EMASnapbackATR_H012_v1
        self.assertEqual(cls.timeframe, "1h")
        self.assertFalse(cls.can_short)
        self.assertLessEqual(cls.startup_candle_count, 4500)
        for name in ("custom_stake_amount", "adjust_trade_position", "leverage"):
            self.assertFalse(hasattr(cls, name))
        self.assertEqual(MOD4H.EMASnapbackATR_H014_v1.timeframe, "4h")
        self.assertEqual(MOD4H.TIMEFRAME_HOURS, 4)

    def test_4h_file_has_the_same_rule_constants(self):
        for name in ("EMA_PERIOD", "TREND_PERIOD", "ATR_PERIOD", "Z_ENTRY", "LOOKBACK", "ATR_STOP_MULT",
                     "MAX_HOLD_BARS", "COOLDOWN_BARS", "USE_RSI", "USE_VOLUME", "EXIT_MODE", "RR_TARGET"):
            self.assertEqual(getattr(MOD, name), getattr(MOD4H, name), name)


if __name__ == "__main__":
    unittest.main()
