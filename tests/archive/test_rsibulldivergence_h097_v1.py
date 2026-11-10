import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

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

if not hasattr(sys.modules["freqtrade.strategy"], "merge_informative_pair"):
    sys.modules["freqtrade.strategy"].merge_informative_pair = lambda *a, **k: None

ROOT = Path(__file__).parents[2]
NAME = "RSIBullDivergence_H097_v1"


def wilder_rsi(dataframe, timeperiod=14):
    delta = dataframe["close"].diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / timeperiod, adjust=False, min_periods=timeperiod).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / timeperiod, adjust=False, min_periods=timeperiod).mean()
    return 100 - 100 / (1 + gain / loss.replace(0, np.nan))


def fake_merge(dataframe, informative, tf, tf_inf, ffill=True):
    inf = informative.copy()
    inf["date"] = inf["date"] + pd.Timedelta(hours=1)  # usable after the hour closes
    inf = inf.rename(columns={c: f"{c}_{tf_inf}" for c in inf.columns if c != "date"})
    return pd.merge_asof(dataframe.sort_values("date"), inf, on="date")


def load_module():
    path = ROOT / "user_data" / "strategies" / "_archive" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ta = SimpleNamespace(RSI=wilder_rsi)
    module.merge_informative_pair = fake_merge
    return module


MODULE = load_module()
Strategy = getattr(MODULE, NAME)


class FakeDp:
    def __init__(self, frame):
        self.frame = frame

    def get_pair_dataframe(self, pair, timeframe):
        f = self.frame.set_index("date")
        h = f.resample("1h", label="left", closed="left").agg(
            {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
        ).dropna().reset_index()
        return h


def make_frame(prices, volume=1.0):
    n = len(prices)
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=n, freq="15min", tz="UTC"),
            "open": prices,
            "high": [p * 1.003 for p in prices],
            "low": [p * 0.997 for p in prices],
            "close": prices,
            "volume": [volume] * n,
        }
    )


def run(frame):
    s = Strategy()
    s.dp = FakeDp(frame)
    f = s.populate_indicators(frame.copy(), {"pair": "BTC/USDT"})
    f = s.populate_entry_trend(f, {})
    return s, s.populate_exit_trend(f, {})


def synthetic(n=40, pivot2_low=98.5, h1=30.0, rsi1=30.0, i2=20):
    low = np.full(n, 100.0)
    high = np.full(n, 100.5)
    close = np.full(n, 100.0)
    volume = np.ones(n)
    rsi = np.full(n, 50.0)
    h1_rsi = np.full(n, h1)
    low[10], rsi[10] = 99.0, rsi1
    low[i2], rsi[i2] = pivot2_low, 35.0
    close[24], high[24] = 100.9, 101.2
    return low, high, close, volume, rsi, h1_rsi


class H097Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 1200)

    def test_divergence_signal(self):
        sig, stop = MODULE.find_signals(*synthetic())
        self.assertEqual(np.flatnonzero(sig).tolist(), [24])
        self.assertAlmostEqual(stop[24], 1 - 98.5 * 0.998 / 100.9)
        # a very tight R is floored at 1%
        low, high, close, volume, rsi, h1 = synthetic()
        close[24], high[24] = 100.9, 101.2
        low[20] = 100.0 - 1e-9
        low[10] = 100.0 - 1e-9 + 1e-10
        sig, stop = MODULE.find_signals(low, high, close, volume, rsi, h1)
        self.assertTrue(sig[24])
        self.assertTrue(stop[24] >= 0.01)

    def test_no_signal_when_filters_fail(self):
        for kwargs in ({"h1": 45.0}, {"rsi1": 45.0}, {"pivot2_low": 98.0}):
            sig, _ = MODULE.find_signals(*synthetic(**kwargs))
            self.assertEqual(int(sig.sum()), 0, kwargs)
        # gap 5 is too short
        arrays = synthetic(i2=15)
        sig, _ = MODULE.find_signals(*arrays)
        self.assertEqual(int(sig.sum()), 0)
        # higher second low is not a divergence
        sig, _ = MODULE.find_signals(*synthetic(pivot2_low=99.5))
        self.assertEqual(int(sig.sum()), 0)

    def test_stop_distance_above_one_percent(self):
        low, high, close, volume, rsi, h1 = synthetic(pivot2_low=98.0)
        close[24], high[24] = 100.5 + 0.4, 101.2
        low[20] = 98.4
        # R = 1 - 98.4*0.998/100.9 ~ 0.0268 -> D = R
        sig, stop = MODULE.find_signals(low, high, close, volume, rsi, h1)
        self.assertTrue(sig[24])
        self.assertAlmostEqual(stop[24], 1 - 98.4 * 0.998 / 100.9)

    def test_zero_volume_and_nan_no_signal(self):
        low, high, close, volume, rsi, h1 = synthetic()
        volume[24] = 0.0
        sig, _ = MODULE.find_signals(low, high, close, volume, rsi, h1)
        self.assertEqual(int(sig.sum()), 0)
        low, high, close, volume, rsi, h1 = synthetic()
        h1[:] = np.nan
        sig, _ = MODULE.find_signals(low, high, close, volume, rsi, h1)
        self.assertEqual(int(sig.sum()), 0)
        rsi[:] = np.nan
        h1[:] = 30.0
        sig, _ = MODULE.find_signals(low, high, close, volume, rsi, h1)
        self.assertEqual(int(sig.sum()), 0)

    def test_frame_level_zero_volume_and_startup(self):
        rng = np.random.default_rng(1)
        prices = 100 + np.cumsum(rng.normal(0, 0.3, 1500))
        frame = make_frame(list(prices), volume=0.0)
        s, out = run(frame)
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(out["exit_long"].fillna(0).sum()), 0)
        frame = make_frame([100.0 + i for i in range(400)])
        s, out = run(frame)
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(out.iloc[:14]["exit_long"].fillna(0).sum()), 0)

    def test_signals_binary_and_no_lookahead(self):
        rng = np.random.default_rng(7)
        prices = list(100 + np.cumsum(rng.normal(0, 0.4, 1800)))
        frame = make_frame(prices)
        n, k = 1500, 300
        _, short = run(frame.iloc[:n].reset_index(drop=True))
        _, full = run(frame)
        for col in ("enter_long", "exit_long"):
            self.assertTrue(set(full[col].dropna().unique().tolist()).issubset({1}))
        cols = ["rsi", "rsi_1h", "div_signal", "stop_dist", "enter_long", "exit_long"]
        # hourly bar still forming at the cut: compare rows safely before it
        pd.testing.assert_frame_equal(
            short.loc[: n - 5, cols].reset_index(drop=True),
            full.loc[: n - 5, cols].reset_index(drop=True),
            check_dtype=False,
        )

    def test_exit_signal_on_rsi(self):
        s = Strategy()
        f = pd.DataFrame({"rsi": [50.0, 70.0, np.nan], "volume": [1.0, 1.0, 1.0]})
        f = s.populate_exit_trend(f, {})
        self.assertEqual(f["exit_long"].fillna(0).tolist(), [0, 1, 0])

    def test_custom_stoploss_and_exits(self):
        s = Strategy()
        t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        trade = SimpleNamespace(enter_tag="div_0.02000", open_rate=100.0, open_date_utc=t0)
        sl = s.custom_stoploss("X", trade, t0, 100.0, 0.0)
        self.assertAlmostEqual(sl, 98.0 / 100.0 - 1)
        sl = s.custom_stoploss("X", trade, t0, 104.0, 0.04)
        self.assertAlmostEqual(sl, 98.0 / 104.0 - 1)
        self.assertEqual(s.custom_exit("X", trade, t0, 104.0, 0.04), "take_profit_2R")
        self.assertIsNone(s.custom_exit("X", trade, t0, 103.0, 0.03))
        self.assertEqual(
            s.custom_exit("X", trade, t0 + timedelta(hours=12), 100.0, 0.0), "time_12h"
        )
        self.assertIsNone(s.custom_exit("X", trade, t0 + timedelta(hours=11, minutes=45), 100.0, 0.0))


if __name__ == "__main__":
    unittest.main()
