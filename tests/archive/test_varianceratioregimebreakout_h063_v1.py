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
for name in ("merge_informative_pair", "stoploss_from_absolute"):
    if not hasattr(sys.modules["freqtrade.strategy"], name):
        setattr(sys.modules["freqtrade.strategy"], name, lambda *a, **k: None)

talib = types.ModuleType("talib")
talib_abstract = types.ModuleType("talib.abstract")
talib_abstract.SMA = lambda dataframe, timeperiod: dataframe["close"].rolling(timeperiod).mean()
talib_abstract.RSI = lambda dataframe, timeperiod: pd.Series(50.0, index=dataframe.index)
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)

ROOT = Path(__file__).parents[2]
NAME = "VarianceRatioRegimeBreakout_H063_v1"
PATH = ROOT / "user_data" / "strategies" / "_archive" / f"{NAME}.py"
spec = importlib.util.spec_from_file_location(NAME, PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Strategy = module.VarianceRatioRegimeBreakout_H063_v1

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


def make_frame(n=3500, phi=0.3, drift=0.0002, sigma=0.002, seed=11):
    """AR(1) returns: positively autocorrelated, so VR > 1, with drift for the 4h filter."""
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, sigma, n)
    returns = np.empty(n)
    prev = 0.0
    for i in range(n):
        prev = drift + phi * (prev - drift) + noise[i]
        returns[i] = prev
    close = 100.0 * np.exp(np.cumsum(returns))
    open_ = np.concatenate([[100.0], close[:-1]])
    return pd.DataFrame(
        {
            "date": pd.date_range(START, periods=n, freq="15min"),
            "open": open_,
            "high": np.maximum(open_, close) * 1.0005,
            "low": np.minimum(open_, close) * 0.9995,
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


def entries(out):
    return out.get("enter_long", pd.Series(0.0, index=out.index)).fillna(0)


class FakeDP:
    def __init__(self, frame):
        self.frame = frame

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.frame, None


class FakeTrade:
    def __init__(self, open_date):
        self.open_date_utc = open_date
        self.enter_tag = "vr_breakout96"


class ContractTests(unittest.TestCase):
    def test_class_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.05)
        self.assertGreaterEqual(Strategy.startup_candle_count, 900)
        self.assertFalse(hasattr(Strategy(), "protections"))
        for name in ("custom_stake_amount", "adjust_trade_position", "leverage"):
            self.assertFalse(hasattr(Strategy, name))

    def test_signals_are_binary_and_present(self):
        out = run(make_frame())
        for column in ("enter_long", "exit_long"):
            if column in out:
                self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(int(entries(out).sum()), 0)

    def test_zero_volume_produces_no_signal(self):
        frame = make_frame()
        frame["volume"] = 0.0
        self.assertEqual(int(entries(run(frame)).sum()), 0)
        frame = make_frame()
        out = run(frame)
        first = int(out.index[entries(out) == 1][0])
        frame.loc[first, "volume"] = 0.0
        self.assertEqual(entries(run(frame)).iloc[first], 0)

    def test_undefined_startup_values_produce_no_signal(self):
        out = run(make_frame())
        undefined = (
            out["vr"].isna() | out["breakout_high"].isna() | out["close_4h"].isna() | out["hsma_4h"].isna()
        )
        self.assertTrue(undefined.iloc[:VR_START].all())
        self.assertEqual(int(entries(out)[undefined].sum()), 0)
        # The 4h SMA50 first exists once 50 blocks (800 bars) have closed.
        self.assertTrue(out["hsma_4h"].iloc[:799].isna().all())
        self.assertTrue(pd.notna(out["hsma_4h"].iloc[799]))
        self.assertEqual(int(entries(out).iloc[:799].sum()), 0)

    def test_signals_do_not_change_when_future_candles_are_appended(self):
        full = make_frame()
        n = 2900
        short = run(full.iloc[:n].copy())
        longer = run(full.copy())
        columns = ["log_ret", "vr", "breakout_high", "exit_low", "close_4h", "hsma_4h", "enter_long"]
        pd.testing.assert_frame_equal(
            short.loc[: n - 1, columns].reset_index(drop=True),
            longer.loc[: n - 1, columns].reset_index(drop=True),
            check_dtype=False,
        )
        self.assertGreater(int(entries(short).sum()), 0)


VR_START = 384


class RuleTests(unittest.TestCase):
    def test_variance_ratio_matches_definition(self):
        frame = make_frame()
        out = run(frame)
        r = np.log(frame["close"] / frame["close"].shift(1)).to_numpy()
        self.assertTrue(np.isnan(out["vr"].iloc[VR_START - 1]))
        for t in (VR_START, 1500, 3000):
            window = r[t - 383: t + 1]
            q = np.array([r[i - 3] + r[i - 2] + r[i - 1] + r[i] for i in range(t - 380, t + 1)])
            self.assertEqual(len(q), 381)
            expected = np.var(q, ddof=1) / (4.0 * np.var(window, ddof=1))
            self.assertAlmostEqual(out.loc[t, "vr"], expected, places=10)

    def test_levels_exclude_current_candle(self):
        frame = make_frame()
        out = run(frame)
        self.assertTrue(pd.isna(out.loc[95, "breakout_high"]))
        self.assertEqual(out.loc[96, "breakout_high"], frame.loc[0:95, "high"].max())
        self.assertEqual(out.loc[1000, "breakout_high"], frame.loc[904:999, "high"].max())
        self.assertTrue(pd.isna(out.loc[15, "exit_low"]))
        self.assertEqual(out.loc[1000, "exit_low"], frame.loc[984:999, "low"].min())

    def test_four_hour_close_visible_only_after_block_closed(self):
        frame = make_frame()
        out = run(frame)
        block = 60  # block starting at bar 960
        last_bar = block * 16 + 15
        self.assertEqual(out.loc[last_bar, "close_4h"], frame.loc[last_bar, "close"])
        self.assertEqual(out.loc[last_bar - 1, "close_4h"], frame.loc[block * 16 - 1, "close"])
        closes = frame.groupby(frame["date"].dt.floor("4h"))["close"].last()
        self.assertAlmostEqual(out.loc[last_bar, "hsma_4h"], closes.iloc[block - 49: block + 1].mean(), places=10)

    def test_entry_conditions_hold_on_every_signal(self):
        out = run(make_frame())
        sig = out.loc[entries(out) == 1]
        self.assertTrue((sig["close"] > sig["breakout_high"]).all())
        self.assertTrue((sig["vr"] >= 1.10).all())
        self.assertTrue((sig["close_4h"] > sig["hsma_4h"]).all())

    def test_no_entry_when_returns_do_not_trend(self):
        # Negatively autocorrelated returns give VR < 1.1 everywhere.
        out = run(make_frame(phi=-0.3))
        self.assertTrue((out["vr"].dropna() < 1.10).all())
        self.assertEqual(int(entries(out).sum()), 0)

    def test_no_entry_when_4h_filter_off(self):
        out = run(make_frame(drift=-0.0004))
        self.assertEqual(int(entries(out).sum()), 0)

    def test_custom_exit_low16_and_time_exit(self):
        dates = pd.date_range("2026-02-05 10:00", periods=120, freq="15min", tz="UTC")
        frame = pd.DataFrame({"date": dates, "close": 101.0, "exit_low": 100.0, "volume": 1.0})
        strategy = Strategy()
        strategy.dp = FakeDP(frame)
        fill = dates[0].to_pydatetime()
        trade = FakeTrade(fill)
        # Nothing triggers while price holds above the 16-bar low.
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, fill, 101, 0))
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, fill + 5 * BAR, 101, 0))
        # The entry bar itself closing below the low does not count.
        frame.loc[0, "close"] = 99.0
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, fill + BAR, 99, 0))
        # The bar after the entry bar closing below the low exits at the next open.
        frame.loc[1, "close"] = 99.0
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, fill + 2 * BAR, 99, 0), "close_below_low16")
        # A zero-volume bar never triggers the exit.
        frame.loc[1, "volume"] = 0.0
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, fill + 2 * BAR, 99, 0))
        frame.loc[[0, 1], ["close", "volume"]] = [101.0, 1.0]
        # Time exit at the open after the 96th bar (entry bar counted as the first) has closed.
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, fill + 95 * BAR, 101, 0))
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, fill + 96 * BAR, 101, 0), "time_exit_96_bars")


if __name__ == "__main__":
    unittest.main()
