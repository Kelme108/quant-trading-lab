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


def load():
    path = ROOT / "user_data" / "strategies" / "_archive" / "ElderTripleScreen_H088_v1.py"
    spec = importlib.util.spec_from_file_location("ElderTripleScreen_H088_v1", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ElderTripleScreen_H088_v1


Strat = load()


def make_frame(n, seed=1):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, n)))
    open_ = np.concatenate([[100.0], close[:-1]])
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.004, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.004, n))
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC"),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": rng.uniform(1, 100, n),
        }
    )


def run(frame):
    s = Strat()
    f = s.populate_indicators(frame.copy(), {})
    f = s.populate_entry_trend(f, {})
    return s.populate_exit_trend(f, {})


class Trade:
    def __init__(self, open_date, open_rate):
        self.open_date_utc = open_date
        self.open_rate = open_rate


class Dp:
    def __init__(self, frame):
        self.frame = frame

    def get_analyzed_dataframe(self, pair, tf):
        return self.frame, None


class H088Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strat.INTERFACE_VERSION, 3)
        self.assertEqual(Strat.timeframe, "1h")
        self.assertFalse(Strat.can_short)
        self.assertEqual(Strat.minimal_roi, {"0": 100.0})
        self.assertLess(Strat.stoploss, 0)
        self.assertGreaterEqual(Strat.startup_candle_count, 140)

    def test_signals_binary_and_present(self):
        f = run(make_frame(3000))
        total = 0
        for col in ("enter_long", "exit_long"):
            vals = f[col].dropna().unique().tolist()
            self.assertTrue(set(vals).issubset({1}))
            total += int(f[col].fillna(0).sum())
        self.assertGreater(int(f["enter_long"].fillna(0).sum()), 0)

    def test_zero_volume_no_signal(self):
        fr = make_frame(3000)
        fr["volume"] = 0.0
        f = run(fr)
        self.assertEqual(int(f["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(f["exit_long"].fillna(0).sum()), 0)

    def test_single_zero_volume_candle(self):
        base = run(make_frame(3000))
        idx = base.index[base["enter_long"] == 1][0]
        fr = make_frame(3000)
        fr.loc[idx, "volume"] = 0.0
        self.assertNotEqual(run(fr).loc[idx, "enter_long"], 1)

    def test_nan_startup_no_signal(self):
        f = run(make_frame(3000))
        self.assertTrue(f["tide_up"].iloc[:7].isna().all())
        self.assertEqual(int(f["enter_long"].iloc[:7].fillna(0).sum()), 0)
        self.assertEqual(int(f["exit_long"].iloc[:7].fillna(0).sum()), 0)

    def test_no_lookahead(self):
        fr = make_frame(3000)
        a = run(fr.iloc[:2500])
        b = run(fr)
        cols = [c for c in a.columns if c not in ("enter_tag", "exit_tag")]
        pd.testing.assert_frame_equal(
            a[cols].fillna(-999), b.iloc[:2500][cols].fillna(-999), check_dtype=False
        )

    def test_tide_visible_only_after_block_complete(self):
        fr = make_frame(400)
        f = run(fr)
        # changing a bar inside the current 4h block must not change earlier rows
        fr2 = fr.copy()
        fr2.loc[200, "close"] *= 1.5
        g = run(fr2)
        before = (200 // 4) * 4 + 3
        pd.testing.assert_series_equal(
            f["tide_up"].iloc[: min(before, 200)],
            g["tide_up"].iloc[: min(before, 200)],
        )

    def _setup(self):
        fr = make_frame(50)
        fr["stop_level"] = 98.0
        s = Strat()
        s.dp = Dp(fr)
        t0 = fr["date"].iloc[11] + timedelta(hours=1)
        return s, fr, Trade(t0, 100.0)

    def test_custom_exit_take_profit_and_time(self):
        s, fr, trade = self._setup()
        now = trade.open_date_utc + timedelta(hours=1)
        # R = 2% -> target 4%
        self.assertEqual(s.custom_exit("X", trade, now, 104, 0.04), "take_profit_2R")
        self.assertIsNone(s.custom_exit("X", trade, now, 102, 0.02))
        late = trade.open_date_utc + timedelta(hours=12)
        self.assertEqual(s.custom_exit("X", trade, late, 101, 0.01), "time_12h")

    def test_custom_stoploss_fixed_level(self):
        s, fr, trade = self._setup()
        now = trade.open_date_utc
        r = s.custom_stoploss("X", trade, now, 101.0, 0.01)
        self.assertAlmostEqual(101.0 * (1 + r), 98.0)
        self.assertLess(r, 0)

    def test_min_risk_filter(self):
        s, fr, trade = self._setup()
        now = trade.open_date_utc
        args = ("X", "limit", 1, 0, "GTC", now, None, "long")
        self.assertTrue(s.confirm_trade_entry(*args[:3], 100.0, *args[4:]))
        self.assertFalse(s.confirm_trade_entry(*args[:3], 98.2, *args[4:]))


if __name__ == "__main__":
    unittest.main()
