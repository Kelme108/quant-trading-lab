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
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)

ROOT = Path(__file__).parents[1]


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


S = load_strategy("OvernightDropReversal_H030_v1.py", "OvernightDropReversal_H030_v1")


def make_frame(n: int, seed: int = 1, drops: bool = True) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.004, n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    date = pd.date_range("2022-01-01", periods=n, freq="1h", tz="UTC")
    df = pd.DataFrame(
        {"date": date, "open": open_, "high": np.maximum(open_, close) * 1.002,
         "low": np.minimum(open_, close) * 0.998, "close": close, "volume": 1.0}
    )
    if drops:
        # Force a 2% overnight fall on every 10th day: 07:00 close below 00:00 open.
        for i in range(n):
            if date[i].hour == 7 and date[i].dayofyear % 10 == 0:
                df.loc[i, "close"] = df.loc[i - 7, "open"] * 0.98
    return df


def run(df: pd.DataFrame) -> pd.DataFrame:
    s = S()
    df = s.populate_indicators(df.copy(), {})
    df = s.populate_entry_trend(df, {})
    return s.populate_exit_trend(df, {})


class OvernightDropTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(S.INTERFACE_VERSION, 3)
        self.assertEqual(S.timeframe, "1h")
        self.assertFalse(S.can_short)
        self.assertEqual(S.minimal_roi, {"0": 100.0})
        self.assertLess(S.stoploss, 0)
        self.assertGreaterEqual(S.startup_candle_count, 2400)

    def test_binary_and_hours(self) -> None:
        df = run(make_frame(24 * 300))
        for col in ("enter_long", "exit_long"):
            self.assertTrue(set(df[col].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(int(df["enter_long"].fillna(0).sum()), 0)
        self.assertTrue((df.loc[df["enter_long"] == 1, "hour_utc"] == 7).all())
        self.assertTrue((df.loc[df["exit_long"] == 1, "hour_utc"] == 15).all())

    def test_zero_volume_no_signal(self) -> None:
        f = make_frame(24 * 300)
        f["volume"] = 0.0
        df = run(f)
        self.assertEqual(int(df["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(df["exit_long"].fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self) -> None:
        df = run(make_frame(24 * 300))
        self.assertEqual(int(df.iloc[: 24 * 100]["enter_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self) -> None:
        full = make_frame(24 * 300)
        a = run(full.iloc[: 24 * 200 + 5])
        b = run(full)
        cols = ["overnight_ret", "prev_daily_close", "prev_daily_sma", "enter_long", "exit_long"]
        pd.testing.assert_frame_equal(
            a[cols].reset_index(drop=True),
            b.iloc[: len(a)][cols].reset_index(drop=True),
            check_dtype=False,
        )


if __name__ == "__main__":
    unittest.main()
