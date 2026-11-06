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

ROOT = Path(__file__).parents[2]
NAME = "LivermorePivotFailFast_H046_v1"


def load():
    path = ROOT / "user_data" / "strategies" / "_archive" / (NAME + ".py")
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, NAME)


Strat = load()


def make_frame(n, with_break=True):
    rng = np.random.default_rng(1)
    close = 100 + np.cumsum(rng.normal(0.05, 0.3, n))
    close = close.copy()
    volume = np.full(n, 10.0)
    if with_break:
        for i in range(700, n, 97):
            close[i:] += 8.0
            volume[i] = 50.0
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC"),
            "open": close,
            "high": close * 1.002,
            "low": close * 0.998,
            "close": close,
            "volume": volume,
        }
    )
    return df


def run(s, df):
    df = s.populate_indicators(df, {})
    df = s.populate_entry_trend(df, {})
    return s.populate_exit_trend(df, {})


class Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strat.INTERFACE_VERSION, 3)
        self.assertEqual(Strat.timeframe, "1h")
        self.assertFalse(Strat.can_short)
        self.assertEqual(Strat.minimal_roi, {"0": 100.0})
        self.assertEqual(Strat.stoploss, -0.04)
        self.assertGreaterEqual(Strat.startup_candle_count, 480)
        self.assertEqual(Strat().protections[0]["stop_duration_candles"], 12)

    def test_binary_and_has_signals(self):
        df = run(Strat(), make_frame(1200))
        self.assertTrue(set(df["enter_long"].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(int(df["enter_long"].fillna(0).sum()), 0)

    def test_zero_volume_no_signal(self):
        df = make_frame(1200)
        df["volume"] = 0.0
        df = run(Strat(), df)
        self.assertEqual(int(df["enter_long"].fillna(0).sum()) if "enter_long" in df else 0, 0)

    def test_startup_nan_no_signal(self):
        df = run(Strat(), make_frame(1200))
        self.assertEqual(int(df.iloc[:480]["enter_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self):
        full = make_frame(1500)
        a = run(Strat(), full.iloc[:1200].copy())
        b = run(Strat(), full.copy()).iloc[:1200]
        cols = ["pivot", "vol_avg", "sma480", "trail_low"]
        pd.testing.assert_frame_equal(a[cols], b[cols])
        self.assertTrue(
            a["enter_long"].fillna(0).equals(b["enter_long"].fillna(0)),
        )

    def test_custom_exit(self):
        s = Strat()
        df = make_frame(300, with_break=False)
        df = s.populate_indicators(df, {})
        t = 250
        sig_date = df.loc[t, "date"]
        pivot = df.loc[t, "pivot"]

        class DP:
            def get_analyzed_dataframe(self, pair, tf):
                return df, None

        s.dp = DP()
        trade = types.SimpleNamespace(open_date_utc=(sig_date + timedelta(hours=1)).to_pydatetime())
        # fail-fast: bar t+2 closes below pivot
        df.loc[t + 2, "close"] = pivot - 1
        now = (df.loc[t + 2, "date"] + timedelta(hours=1)).to_pydatetime()
        self.assertEqual(s.custom_exit("X", trade, now, 1, 0), "fail_fast_pivot")
        # not below pivot
        df.loc[t + 2, "close"] = pivot + 1
        self.assertIsNone(s.custom_exit("X", trade, now, 1, 0))
        # trail only from t+9
        df.loc[t + 5, "close"] = df.loc[t + 5, "trail_low"] - 1
        df.loc[t + 5, "close"] = min(df.loc[t + 5, "close"], pivot + 1)
        df.loc[t + 5, "close"] = pivot + 1
        df.loc[t + 9, "close"] = df.loc[t + 9, "trail_low"] - 1
        now9 = (df.loc[t + 9, "date"] + timedelta(hours=1)).to_pydatetime()
        self.assertEqual(s.custom_exit("X", trade, now9, 1, 0), "trail_48_low")


if __name__ == "__main__":
    unittest.main()
