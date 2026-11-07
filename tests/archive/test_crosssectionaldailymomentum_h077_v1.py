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
talib_abstract.SMA = lambda dataframe, timeperiod: dataframe["close"].rolling(timeperiod).mean()
talib_abstract.RSI = lambda dataframe, timeperiod: pd.Series(50.0, index=dataframe.index)
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)

ROOT = Path(__file__).parents[2]
NAME = "CrossSectionalDailyMomentum_H077_v1"


def load_module():
    path = ROOT / "user_data" / "strategies" / "_archive" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()
Strategy = MODULE.CrossSectionalDailyMomentum_H077_v1
PAIRS = MODULE.PAIRS


class FakeDP:
    def __init__(self, frames):
        self.frames = frames

    def get_pair_dataframe(self, pair, timeframe):
        return self.frames[pair].copy()


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


def make_prices(n, seed):
    rng = np.random.default_rng(seed)
    return list(100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.01, n))))


def build_series(total):
    return {pair: make_prices(total, i + 1) for i, pair in enumerate(PAIRS)}


def run(series, traded, n, volume=1.0, frames=None):
    if frames is None:
        frames = {k: make_frame(v[:n]) for k, v in series.items()}
    strat = Strategy()
    strat.dp = FakeDP(frames)
    frame = frames[traded].copy()
    frame["volume"] = volume
    meta = {"pair": traded}
    frame = strat.populate_indicators(frame, meta)
    frame = strat.populate_entry_trend(frame, meta)
    return strat.populate_exit_trend(frame, meta)


class H077Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertAlmostEqual(Strategy.stoploss, -0.05)
        self.assertGreaterEqual(Strategy.startup_candle_count, 50)
        self.assertEqual(len(PAIRS), 9)

    def test_signals_binary_and_hours(self):
        series = build_series(24 * 40)
        out = run(series, "ETH/USDT", 24 * 40)
        for col in ("enter_long", "exit_long"):
            self.assertIn(col, out)
            self.assertTrue(set(out[col].dropna().unique().tolist()).issubset({1}))
        hours = out["date"].dt.hour
        self.assertTrue((hours[out["enter_long"] == 1] == 23).all())
        self.assertTrue((hours[out["exit_long"] == 1] == 22).all())
        self.assertGreater(out["enter_long"].fillna(0).sum(), 0)

    def test_ranks_partition_top4(self):
        n = 24 * 20
        series = build_series(n)
        ranks = {p: run(series, p, n) for p in PAIRS}
        idx = ranks["BTC/USDT"].index[ranks["BTC/USDT"]["date"].dt.hour == 23][1:]
        for i in idx:
            r = sorted(ranks[p].loc[i, "xs_rank"] for p in PAIRS)
            self.assertEqual(r, list(range(1, 10)))
            entries = sum(int(ranks[p].loc[i, "enter_long"] == 1) for p in PAIRS)
            self.assertEqual(entries, 4)

    def test_rank_matches_manual(self):
        n = 24 * 5
        series = build_series(n)
        out = run(series, "SOL/USDT", n)
        i = 24 * 3 + 23
        rets = {p: series[p][i] / series[p][i - 24] - 1 for p in PAIRS}
        order = sorted(PAIRS, key=lambda p: (-rets[p], p))
        self.assertEqual(out.loc[i, "xs_rank"], order.index("SOL/USDT") + 1)

    def test_tie_break_by_name(self):
        n = 24 * 4
        flat = [100.0] * n
        series = {p: flat for p in PAIRS}
        i = 24 * 2 + 23
        order = sorted(PAIRS)
        for p in PAIRS:
            out = run(series, p, n)
            self.assertEqual(out.loc[i, "xs_rank"], order.index(p) + 1)
            self.assertEqual(out.loc[i, "enter_long"] == 1, order.index(p) < 4)

    def test_missing_close_drops_pair(self):
        n = 24 * 4
        series = build_series(n)
        frames = {k: make_frame(v) for k, v in series.items()}
        i = 24 * 2 + 23
        # Remove one bar of ADA inside the 25-close window.
        frames["ADA/USDT"] = frames["ADA/USDT"].drop(index=i - 10).reset_index(drop=True)
        out_btc = run(series, "BTC/USDT", n, frames=frames)
        ranks = [run(series, p, n, frames=frames).loc[i, "xs_rank"] for p in PAIRS if p != "ADA/USDT"]
        self.assertEqual(sorted(ranks), list(range(1, 9)))
        self.assertFalse(np.isnan(out_btc.loc[i, "xs_rank"]))

    def test_zero_volume_no_signal(self):
        series = build_series(24 * 20)
        out = run(series, "ETH/USDT", 24 * 20, volume=0.0)
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(out["exit_long"].fillna(0).sum()), 0)

    def test_nan_startup_no_entry(self):
        series = build_series(24 * 20)
        out = run(series, "ETH/USDT", 24 * 20)
        self.assertTrue(out["day_return"].iloc[:24].isna().all())
        self.assertEqual(int(out.iloc[:24]["enter_long"].fillna(0).sum()), 0)
        nan_rows = out["day_return"].isna() | out["xs_rank"].isna()
        self.assertEqual(int(out.loc[nan_rows, "enter_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self):
        n, total = 24 * 30, 24 * 36
        series = build_series(total)
        a = run(series, "LINK/USDT", n)
        b = run(series, "LINK/USDT", total)
        cols = ["day_return", "xs_rank"]
        pd.testing.assert_frame_equal(a.loc[: n - 1, cols], b.loc[: n - 1, cols])
        for col in ("enter_long", "exit_long"):
            pd.testing.assert_series_equal(
                a[col].iloc[:n].fillna(0), b[col].iloc[:n].fillna(0), check_dtype=False
            )


if __name__ == "__main__":
    unittest.main()
