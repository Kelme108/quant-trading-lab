import importlib.util
import math
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
NAME = "FeedbackVolRegimeSwitch_H074_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, NAME)


Strategy = load_strategy()


def make_prices(n, seed=7):
    """Random walk with alternating calm/volatile stretches so both entry types can fire."""
    rng = np.random.default_rng(seed)
    scale = np.where((np.arange(n) // 300) % 3 == 2, 0.03, 0.006)
    return list(100.0 * np.exp(np.cumsum(rng.normal(0.0, 1.0, n) * scale)))


def make_frame(prices, volume=1.0):
    n = len(prices)
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC"),
            "open": prices,
            "high": [p * 1.01 for p in prices],
            "low": [p * 0.99 for p in prices],
            "close": prices,
            "volume": [volume] * n,
        }
    )


def run(frame):
    strat = Strategy()
    meta = {"pair": "ETH/USDT"}
    frame = strat.populate_indicators(frame, meta)
    frame = strat.populate_entry_trend(frame, meta)
    return strat.populate_exit_trend(frame, meta)


class FakeDP:
    def __init__(self, frame):
        self.frame = frame

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.frame, None


class FakeTrade:
    def __init__(self, open_date):
        self.open_date_utc = open_date


class H074Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertAlmostEqual(Strategy.stoploss, -0.03)
        self.assertGreaterEqual(Strategy.startup_candle_count, 745)
        self.assertEqual(
            Strategy().protections,
            [{"method": "CooldownPeriod", "stop_duration_candles": 6}],
        )

    def test_indicator_definitions(self):
        out = run(make_frame(make_prices(1200)))
        close = out["close"]
        r = np.log(close / close.shift(1))
        t = 900
        self.assertAlmostEqual(out.loc[t, "sig"], float(np.std(r.iloc[t - 23 : t + 1], ddof=1)))
        self.assertAlmostEqual(
            out.loc[t, "sig_median"], float(np.median(out["sig"].iloc[t - 720 : t]))
        )
        self.assertAlmostEqual(out.loc[t, "r6"], close[t] / close[t - 6] - 1.0)
        self.assertTrue(pd.isna(out.loc[743, "sig_median"]))
        self.assertFalse(pd.isna(out.loc[744, "sig_median"]))

    def test_entries_match_rule(self):
        out = run(make_frame(make_prices(3000)))
        sig, med, r6 = out["sig"], out["sig_median"], out["r6"]
        move = 2.0 * sig * math.sqrt(6)
        a = (sig < med) & (r6 >= move) & (r6 >= 0.012)
        b = (sig >= 1.5 * med) & (r6 <= -move) & (r6 <= -0.025)
        expected = (a | b) & sig.notna() & med.notna() & r6.notna()
        got = out["enter_long"].fillna(0) == 1
        pd.testing.assert_series_equal(got, expected, check_names=False)
        self.assertGreater(int(got.sum()), 0)

    def test_signals_binary(self):
        out = run(make_frame(make_prices(3000)))
        self.assertIn("enter_long", out)
        for col in ("enter_long", "exit_long"):
            if col in out:
                self.assertTrue(set(out[col].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_no_signal(self):
        out = run(make_frame(make_prices(3000), volume=0.0))
        self.assertEqual(int(out.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(out.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self):
        out = run(make_frame(make_prices(3000)))
        self.assertEqual(int(out.iloc[:744]["enter_long"].fillna(0).sum()), 0)
        undefined = out["sig"].isna() | out["sig_median"].isna() | out["r6"].isna()
        self.assertEqual(int(out.loc[undefined, "enter_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self):
        n, k = 2000, 400
        prices = make_prices(n + k)
        a = run(make_frame(prices[:n]))
        b = run(make_frame(prices))
        cols = ["log_ret", "sig", "sig_median", "r6"]
        pd.testing.assert_frame_equal(a.loc[: n - 1, cols], b.loc[: n - 1, cols])
        pd.testing.assert_series_equal(
            a["enter_long"].iloc[:n].fillna(0), b["enter_long"].iloc[:n].fillna(0), check_dtype=False
        )

    def test_time_exit_after_12_bars(self):
        frame = run(make_frame(make_prices(1000)))
        open_date = frame["date"].iloc[900].to_pydatetime()
        trade = FakeTrade(open_date)
        strat = Strategy()
        for offset, expected in ((0, None), (11, None), (12, "time_12_bars")):
            strat.dp = FakeDP(frame.iloc[: 901 + offset])
            now = open_date + timedelta(hours=offset + 1)
            self.assertEqual(strat.custom_exit("ETH/USDT", trade, now, 100.0, 0.0), expected)
        zero = frame.iloc[:913].copy()
        zero.loc[zero.index[-1], "volume"] = 0.0
        strat.dp = FakeDP(zero)
        self.assertIsNone(
            strat.custom_exit("ETH/USDT", trade, open_date + timedelta(hours=13), 100.0, 0.0)
        )


if __name__ == "__main__":
    unittest.main()
