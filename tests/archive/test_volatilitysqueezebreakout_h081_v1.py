import importlib.util
import sys
import types
import unittest
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# Keep the tests runnable without installing Freqtrade or TA-Lib on the host.
freqtrade = types.ModuleType("freqtrade")
strategy_module = types.ModuleType("freqtrade.strategy")
strategy_module.IStrategy = object
freqtrade.strategy = strategy_module
sys.modules.setdefault("freqtrade", freqtrade)
sys.modules.setdefault("freqtrade.strategy", strategy_module)
for _name in ("merge_informative_pair", "stoploss_from_absolute"):
    if not hasattr(sys.modules["freqtrade.strategy"], _name):
        setattr(sys.modules["freqtrade.strategy"], _name, lambda *a, **k: None)

talib = types.ModuleType("talib")
talib_abstract = types.ModuleType("talib.abstract")
talib_abstract.SMA = lambda dataframe, timeperiod: dataframe["close"].rolling(timeperiod).mean()
talib_abstract.RSI = lambda dataframe, timeperiod: pd.Series(50.0, index=dataframe.index)
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)

ROOT = Path(__file__).parents[2]
NAME = "VolatilitySqueezeBreakout_H081_v1"
PATH = ROOT / "user_data" / "strategies" / "_archive" / f"{NAME}.py"
spec = importlib.util.spec_from_file_location(NAME, PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Strategy = module.VolatilitySqueezeBreakout_H081_v1

MINUTES = {"15m": 15, "1h": 60, "4h": 240, "1d": 1440}


def merge_informative_pair(dataframe, informative, timeframe, timeframe_inf, ffill=True, **kwargs):
    """Same semantics as freqtrade's helper: an informative candle is visible from the last base candle
    inside its period (i.e. once that period has closed)."""
    informative = informative.copy()
    shift = MINUTES[timeframe_inf] - MINUTES[timeframe]
    informative["date_merge"] = informative["date"] + pd.Timedelta(minutes=shift)
    informative.columns = [f"{column}_{timeframe_inf}" for column in informative.columns]
    merged = pd.merge(
        dataframe, informative, left_on="date",
        right_on=f"date_merge_{timeframe_inf}", how="left",
    )
    merged = merged.drop(columns=[f"date_merge_{timeframe_inf}"])
    if ffill:
        columns = [c for c in merged.columns if c.endswith(f"_{timeframe_inf}")]
        merged[columns] = merged[columns].ffill()
    return merged


# Use the faithful merge regardless of which stub module was registered first.
module.merge_informative_pair = merge_informative_pair

START = pd.Timestamp("2026-01-01 00:00", tz="UTC")
BAR = timedelta(minutes=15)


def make_frame(n=3600, trend=0.006, seed=5):
    """Repeating 60-bar cycles: 40 flat coil bars with wide wicks (squeeze), then 20 trending bars."""
    rng = np.random.default_rng(seed)
    close = np.empty(n)
    level = 100.0
    for i in range(n):
        if i % 60 < 40:
            close[i] = level * (1.0 + rng.normal(0.0, 0.0003))
        else:
            level *= 1.0 + trend
            close[i] = level
    open_ = np.concatenate([[close[0]], close[:-1]])
    return pd.DataFrame(
        {
            "date": pd.date_range(START, periods=n, freq="15min"),
            "open": open_,
            "high": np.maximum(open_, close) * 1.004,
            "low": np.minimum(open_, close) * 0.996,
            "close": close,
            "volume": 1.0,
        }
    )


def run(frame):
    strategy = Strategy()
    out = strategy.populate_indicators(frame.copy(), {"pair": "BTC/USDT"})
    out = strategy.populate_entry_trend(out, {"pair": "BTC/USDT"})
    out = strategy.populate_exit_trend(out, {"pair": "BTC/USDT"})
    return out


def column(out, name):
    return out.get(name, pd.Series(0.0, index=out.index)).fillna(0)


class FakeTrade:
    def __init__(self, open_date):
        self.open_date_utc = open_date


class ContractTests(unittest.TestCase):
    def test_class_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.015)
        self.assertGreaterEqual(Strategy.startup_candle_count, 2400)
        self.assertFalse(hasattr(Strategy(), "protections"))
        for name in ("custom_stake_amount", "adjust_trade_position", "leverage"):
            self.assertFalse(hasattr(Strategy, name))

    def test_signals_are_binary_and_present(self):
        out = run(make_frame())
        for name in ("enter_long", "exit_long"):
            self.assertIn(name, out)
            self.assertTrue(set(out[name].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(int(column(out, "enter_long").sum()), 0)
        self.assertGreater(int(column(out, "exit_long").sum()), 0)

    def test_zero_volume_produces_no_signal(self):
        frame = make_frame()
        frame["volume"] = 0.0
        out = run(frame)
        self.assertEqual(int(column(out, "enter_long").sum()), 0)
        self.assertEqual(int(column(out, "exit_long").sum()), 0)
        frame = make_frame()
        out = run(frame)
        first = int(out.index[column(out, "enter_long") == 1][0])
        frame.loc[first, "volume"] = 0.0
        self.assertEqual(column(run(frame), "enter_long").iloc[first], 0)

    def test_undefined_startup_values_produce_no_signal(self):
        out = run(make_frame())
        undefined_entry = (
            out["squeeze_prior"].isna() | out["mom"].isna() | out["mom_1"].isna() | out["kcu"].isna()
            | out["close_4h"].isna() | out["ema50_4h"].isna() | out["ema50_prev_4h"].isna()
        )
        self.assertTrue(undefined_entry.iloc[:39].all())
        self.assertEqual(int(column(out, "enter_long")[undefined_entry].sum()), 0)
        undefined_exit = out["mom_2"].isna() & out["sma20"].isna()
        self.assertTrue(undefined_exit.iloc[:19].all())
        self.assertEqual(int(column(out, "exit_long")[undefined_exit].sum()), 0)
        # EMA slope needs two closed 4h bars: nothing before bar 31 (end of the second block).
        self.assertTrue(out["ema50_prev_4h"].iloc[:31].isna().all())
        self.assertEqual(int(column(out, "enter_long").iloc[:31].sum()), 0)

    def test_signals_do_not_change_when_future_candles_are_appended(self):
        full = make_frame()
        n = 3000
        short = run(full.iloc[:n].copy())
        longer = run(full.copy())
        columns = [
            "sma20", "bbu", "kcu", "squeeze_on", "squeeze_prior", "mid", "mom",
            "close_4h", "ema50_4h", "ema50_prev_4h", "enter_long", "exit_long",
        ]
        pd.testing.assert_frame_equal(
            short.loc[: n - 1, columns].reset_index(drop=True),
            longer.loc[: n - 1, columns].reset_index(drop=True),
            check_dtype=False,
        )
        self.assertGreater(int(column(short, "enter_long").sum()), 0)


class RuleTests(unittest.TestCase):
    def test_indicator_definitions(self):
        frame = make_frame()
        out = run(frame)
        t = 1234
        close = frame["close"].to_numpy()
        window = close[t - 19: t + 1]
        sma = window.mean()
        self.assertAlmostEqual(out.loc[t, "sma20"], sma, places=10)
        self.assertAlmostEqual(out.loc[t, "bbu"], sma + 2.0 * np.std(window, ddof=0), delta=1e-6)
        mid = ((frame["high"].iloc[t - 19: t + 1].max() + frame["low"].iloc[t - 19: t + 1].min()) / 2 + sma) / 2
        self.assertAlmostEqual(out.loc[t, "mid"], mid, places=10)
        ys = np.array([close[i] - out.loc[i, "mid"] for i in range(t - 19, t + 1)])
        slope, intercept = np.polyfit(np.arange(20.0), ys, 1)
        self.assertAlmostEqual(out.loc[t, "mom"], intercept + slope * 19, places=8)
        self.assertTrue(pd.isna(out.loc[37, "mom"]))
        self.assertTrue(pd.notna(out.loc[38, "mom"]))

    def test_four_hour_bar_visible_only_after_close(self):
        frame = make_frame()
        out = run(frame)
        block = 60
        last_bar = block * 16 + 15
        self.assertEqual(out.loc[last_bar, "close_4h"], frame.loc[last_bar, "close"])
        self.assertEqual(out.loc[last_bar - 1, "close_4h"], frame.loc[block * 16 - 1, "close"])
        closes = frame.groupby(frame["date"].dt.floor("4h"))["close"].last()
        ema = closes.ewm(span=50, adjust=False).mean()
        self.assertAlmostEqual(out.loc[last_bar, "ema50_4h"], ema.iloc[block], places=10)
        self.assertAlmostEqual(out.loc[last_bar, "ema50_prev_4h"], ema.iloc[block - 1], places=10)

    def test_entry_conditions_hold_on_every_signal(self):
        out = run(make_frame())
        sig = out.loc[column(out, "enter_long") == 1]
        self.assertGreater(len(sig), 0)
        squeeze = out["squeeze_on"]
        for i in sig.index:
            self.assertTrue((squeeze.iloc[i - 6: i] == 1).all())
            self.assertEqual(squeeze.iloc[i], 0)
        self.assertTrue((sig["mom"] > 0).all())
        self.assertTrue((sig["mom"] > sig["mom_1"]).all())
        self.assertTrue((sig["close"] > sig["kcu"]).all())
        self.assertTrue((sig["close_4h"] > sig["ema50_4h"]).all())
        self.assertTrue((sig["ema50_4h"] > sig["ema50_prev_4h"]).all())

    def test_no_entry_in_4h_downtrend(self):
        out = run(make_frame(trend=-0.006))
        self.assertEqual(int(column(out, "enter_long").sum()), 0)

    def test_time_exit_after_32_bars(self):
        strategy = Strategy()
        fill = START.to_pydatetime()
        trade = FakeTrade(fill)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, fill + 31 * BAR, 100, 0))
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, fill + 32 * BAR, 100, 0), "time_exit_32_bars")


if __name__ == "__main__":
    unittest.main()
