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


MOD = load("TripleBottomReversal_H011_v1")
MOD4H = load("TripleBottomReversal_H013_v1")


def path(waypoints, tail=10):
    """Piecewise-linear close from (index, price) waypoints; high/low = close +/- 0.2."""
    xs, ys = zip(*waypoints)
    n = xs[-1] + tail
    close = np.interp(np.arange(n), xs, ys)
    return close, close + 0.2, close - 0.2


def pattern(b1=100.0, b2=100.4, b3=100.2, sep=(20, 40, 60, 80, 100), peak=110.0, end=125.0):
    """Start high, three bottoms with two recoveries, then a rally through the neckline."""
    wp = [(0, 125.0), (sep[0], b1), (sep[1], peak), (sep[2], b2), (sep[3], peak + 0.5),
          (sep[4], b3), (sep[4] + 20, end)]
    return path(wp)


def signals(close, high, low, volume=None, ema_value=50.0, rsi_value=50.0, **kwargs):
    n = len(close)
    volume = np.ones(n) if volume is None else volume
    atr = np.full(n, 0.5)
    rsi = np.full(n, rsi_value) if np.isscalar(rsi_value) else rsi_value
    ema = np.full(n, ema_value)
    return MOD.find_triple_bottom_signals(high, low, close, volume, atr, rsi, ema, **kwargs)


def with_breakout_volume(close, mult=3.0):
    volume = np.ones(len(close))
    volume[105:] = mult
    return volume


class PivotTests(unittest.TestCase):
    def test_pivot_is_known_only_k_candles_later(self):
        low = np.array([5, 5, 5, 5, 5, 1, 5, 5, 5, 5, 5, 5], dtype=float)
        flags = MOD.pivot_low_flags(low, 5)
        self.assertEqual(list(np.flatnonzero(flags)), [10])  # pivot at 5, confirmed at 10
        self.assertFalse(flags[:10].any())

    def test_flat_floor_pivot_is_the_last_equal_low_not_the_first(self):
        # ties are allowed on the left only: the pivot is candle 6, known at candle 11
        low = np.array([5, 5, 5, 5, 5, 1, 1, 5, 5, 5, 5, 5, 5], dtype=float)
        self.assertEqual(list(np.flatnonzero(MOD.pivot_low_flags(low, 5))), [11])


class PatternTests(unittest.TestCase):
    def test_valid_pattern_signals_once_after_neckline_close(self):
        close, high, low = pattern()
        signal, stop, target, neckline, pivot = signals(close, high, low, with_breakout_volume(close))
        idx = np.flatnonzero(signal)
        self.assertEqual(len(idx), 1)
        t = idx[0]
        self.assertGreater(close[t], neckline[t])
        self.assertTrue(np.all(close[105:t] <= neckline[t]))  # first close above the neckline
        self.assertLess(stop[t], low[100])
        self.assertGreater(target[t], neckline[t])
        self.assertEqual(pivot[t], 100)

    def test_no_signal_when_third_bottom_outside_tolerance(self):
        close, high, low = pattern(b3=106.0)
        self.assertFalse(signals(close, high, low, with_breakout_volume(close))[0].any())

    def test_no_signal_when_bottoms_too_close(self):
        close, high, low = pattern(sep=(20, 24, 28, 32, 36))
        self.assertFalse(signals(close, high, low, np.full(len(close), 3.0))[0].any())

    def test_no_signal_when_recovery_too_small(self):
        close, high, low = pattern(peak=101.5)
        self.assertFalse(signals(close, high, low, np.full(len(close), 3.0))[0].any())

    def test_volume_filter_blocks_breakout(self):
        close, high, low = pattern()
        flat = np.ones(len(close))
        self.assertFalse(signals(close, high, low, flat, volume_mult=1.5)[0].any())
        self.assertTrue(signals(close, high, low, with_breakout_volume(close), volume_mult=1.5)[0].any())

    def test_ema200_filter(self):
        close, high, low = pattern()
        volume = with_breakout_volume(close)
        self.assertFalse(signals(close, high, low, volume, ema_value=500.0, use_ema200=True)[0].any())
        self.assertTrue(signals(close, high, low, volume, ema_value=50.0, use_ema200=True)[0].any())

    def test_rsi_divergence_filter(self):
        close, high, low = pattern()
        volume = with_breakout_volume(close)
        rsi_up = np.full(len(close), 40.0)
        rsi_up[100] = 55.0  # RSI higher at the third bottom than at the first
        rsi_down = np.full(len(close), 40.0)
        rsi_down[20] = 55.0
        self.assertTrue(signals(close, high, low, volume, rsi_value=rsi_up, use_rsi_divergence=True)[0].any())
        self.assertFalse(signals(close, high, low, volume, rsi_value=rsi_down, use_rsi_divergence=True)[0].any())

    def test_min_rr_filter(self):
        close, high, low = pattern()
        volume = with_breakout_volume(close)
        self.assertTrue(signals(close, high, low, volume, min_rr=0.0)[0].any())
        self.assertFalse(signals(close, high, low, volume, min_rr=1.5)[0].any())

    def test_breakout_after_support_break_is_invalid(self):
        close, high, low = pattern()
        low = low.copy()
        low[103] = 90.0  # a low well under the support zone after the third bottom
        self.assertFalse(signals(close, high, low, with_breakout_volume(close))[0].any())

    def test_bottoms_are_never_reused_by_a_second_signal(self):
        wp = [(0, 125.0), (20, 100.0), (40, 110.0), (60, 100.4), (80, 110.5), (100, 100.2), (115, 118.0),
              (130, 105.0), (145, 100.1), (165, 118.0)]
        close, high, low = path(wp)
        signal, _, _, _, pivot = signals(close, high, low, np.full(len(close), 3.0))
        used = pivot[signal]
        self.assertEqual(len(used), len(set(used)))
        self.assertLessEqual(int(signal.sum()), 1)


class CausalityTests(unittest.TestCase):
    def test_prefix_signals_equal_full_series_signals(self):
        for seed in range(6):
            rng = np.random.default_rng(seed)
            n = 1500
            close = 100 * np.exp(np.cumsum(rng.normal(0, 0.012, n)))
            high = close * (1 + np.abs(rng.normal(0, 0.003, n)))
            low = close * (1 - np.abs(rng.normal(0, 0.003, n)))
            volume = rng.uniform(0.5, 2.0, n)
            kwargs = dict(tolerance=0.04, min_rebound=0.02)
            full = signals(close, high, low, volume, **kwargs)
            for cut in (400, 777, 1200):
                part = signals(close[:cut], high[:cut], low[:cut], volume[:cut], **kwargs)
                np.testing.assert_array_equal(part[0], full[0][:cut])
                np.testing.assert_allclose(part[1], full[1][:cut], equal_nan=True)

    def test_random_walks_produce_signals_so_the_causality_test_is_not_vacuous(self):
        total = 0
        for seed in range(20):
            rng = np.random.default_rng(seed)
            close = 100 * np.exp(np.cumsum(rng.normal(0, 0.012, 3000)))
            total += int(signals(close, close * 1.003, close * 0.997, np.ones(3000),
                                 tolerance=0.04, min_rebound=0.02)[0].sum())
        self.assertGreater(total, 0)


class SizingAndContractTests(unittest.TestCase):
    def test_risk_position_fraction(self):
        self.assertAlmostEqual(MOD.risk_position_fraction(0.01, 100.0, 95.0), 0.2)
        self.assertEqual(MOD.risk_position_fraction(0.01, 100.0, 99.9), 1.0)  # capped: spot, no leverage
        self.assertEqual(MOD.risk_position_fraction(0.01, 100.0, 101.0), 0.0)
        self.assertEqual(MOD.risk_position_fraction(0.0, 100.0, 95.0), 0.0)

    def test_contract(self):
        cls = MOD.TripleBottomReversal_H011_v1
        self.assertEqual(cls.timeframe, "1h")
        self.assertFalse(cls.can_short)
        self.assertLessEqual(cls.startup_candle_count, 4500)
        self.assertEqual(MOD4H.TripleBottomReversal_H013_v1.timeframe, "4h")
        self.assertEqual(MOD4H.TIMEFRAME_HOURS, 4)
        for name in ("custom_stake_amount", "adjust_trade_position", "leverage"):
            self.assertFalse(hasattr(cls, name))

    def test_4h_file_has_the_same_rule_constants(self):
        for name in ("PIVOT_K", "TOLERANCE", "MIN_SEPARATION", "MAX_SPAN", "MIN_REBOUND", "MAX_WAIT",
                     "VOLUME_MULT", "ATR_STOP_MULT", "TP_MULT", "MIN_RR", "MAX_HOLD_BARS"):
            self.assertEqual(getattr(MOD, name), getattr(MOD4H, name), name)


if __name__ == "__main__":
    unittest.main()
