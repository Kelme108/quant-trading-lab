import importlib.util
import sys
import types
import unittest
from datetime import timedelta
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
NAME = "IdiosyncraticResidualReversal_H072_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / "_archive" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, NAME)


Strategy = load_strategy()
PAIR = "SOL/USDT"
START = pd.Timestamp("2024-01-01", tz="UTC")


class FakeDP:
    def __init__(self, frames, analyzed=None):
        self.frames = frames
        self.analyzed = analyzed

    def get_pair_dataframe(self, pair, timeframe):
        return self.frames[pair].copy()

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.analyzed, None


class FakeTrade:
    def __init__(self, open_date, open_rate):
        self.open_date_utc = open_date
        self.open_rate = open_rate


def make_frame(prices, volume=1.0):
    n = len(prices)
    return pd.DataFrame(
        {
            "date": pd.date_range(START, periods=n, freq="1h"),
            "open": prices,
            "high": [p * 1.01 for p in prices],
            "low": [p * 0.99 for p in prices],
            "close": prices,
            "volume": [volume] * n,
        }
    )


def make_series(total):
    """Reference random walk; traded pair = 1.2 * reference returns + noise, with idiosyncratic drops."""
    rng = np.random.default_rng(7)
    rb = rng.normal(0.0, 0.004, total)
    rx = 1.2 * rb + rng.normal(0.0, 0.004, total)
    # Idiosyncratic 6-bar drops while the reference stays flat.
    for start in range(1600, total - 10, 150):
        rb[start : start + 6] = 0.0
        rx[start : start + 6] = -0.008
    ref = 100.0 * np.exp(np.cumsum(rb))
    px = 50.0 * np.exp(np.cumsum(rx))
    return list(px), list(ref)


def build(n, total, volume=1.0):
    px, ref = make_series(total)
    frames = {"BTC/USDT": make_frame(ref[:n]), "ETH/USDT": make_frame(ref[:n])}
    strat = Strategy()
    strat.dp = FakeDP(frames)
    return strat, make_frame(px[:n], volume)


def run(strat, frame):
    meta = {"pair": PAIR}
    frame = strat.populate_indicators(frame, meta)
    frame = strat.populate_entry_trend(frame, meta)
    return strat.populate_exit_trend(frame, meta)


class H072Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertAlmostEqual(Strategy.stoploss, -0.04)
        self.assertGreaterEqual(Strategy.startup_candle_count, 1447)

    def test_reference_pair(self):
        strat = Strategy()
        self.assertIn(("BTC/USDT", "1h"), strat.informative_pairs())
        self.assertIn(("ETH/USDT", "1h"), strat.informative_pairs())

    def test_beta_and_std_exclude_current_bar(self):
        strat, frame = build(2000, 2000)
        out = run(strat, frame)
        self.assertTrue(out["beta"].iloc[:721].isna().all())
        self.assertTrue(out["beta"].iloc[721:].notna().all())
        self.assertTrue(out["e6_std"].iloc[:1441].isna().all())
        self.assertTrue(out["e6_std"].iloc[1441:].notna().all())
        # beta at t equals the ratio computed on bars t-720..t-1 only.
        t = 1800
        x = np.log(out["close"] / out["close"].shift(1)).iloc[t - 720 : t]
        b = np.log(out["ref_close"] / out["ref_close"].shift(1)).iloc[t - 720 : t]
        self.assertAlmostEqual(out["beta"].iloc[t], np.cov(x, b, ddof=1)[0, 1] / b.var(ddof=1))
        self.assertAlmostEqual(out["e6_std"].iloc[t], out["e6"].iloc[t - 720 : t].std(ddof=1))

    def test_signals_binary_and_fire(self):
        strat, frame = build(2600, 2600)
        out = run(strat, frame)
        self.assertIn("enter_long", out)
        self.assertTrue(set(out["enter_long"].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(out["enter_long"].fillna(0).sum(), 0)
        if "exit_long" in out:
            self.assertTrue(set(out["exit_long"].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_no_signal(self):
        strat, frame = build(2600, 2600, volume=0.0)
        out = run(strat, frame)
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)
        trade = FakeTrade(out["date"].iloc[2000], out["open"].iloc[2000])
        strat.dp.analyzed = out.iloc[: 2000 + 20]
        self.assertIsNone(strat.custom_exit(PAIR, trade, None, 0.0, 0.0))

    def test_nan_startup_no_signal(self):
        strat, frame = build(2600, 2600)
        out = run(strat, frame)
        self.assertEqual(int(out.iloc[:1441]["enter_long"].fillna(0).sum()), 0)

    def test_missing_reference_bar_no_signal(self):
        strat, frame = build(2600, 2600)
        ref = strat.dp.frames["BTC/USDT"]
        strat.dp.frames["BTC/USDT"] = ref.drop(index=2000).reset_index(drop=True)
        out = run(strat, frame)
        # Bar 2000 missing in B: beta windows covering it are undefined, so no entries there.
        self.assertEqual(int(out.iloc[2000:2721]["enter_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self):
        n, total = 2200, 2600
        a = run(*build(n, total))
        b = run(*build(total, total))
        cols = ["ref_close", "beta", "rb6", "e6", "e6_std"]
        pd.testing.assert_frame_equal(a.loc[: n - 1, cols], b.loc[: n - 1, cols])
        pd.testing.assert_series_equal(
            a["enter_long"].iloc[:n].fillna(0), b["enter_long"].iloc[:n].fillna(0), check_dtype=False
        )

    def test_custom_exit_target_and_time(self):
        strat, frame = build(2600, 2600)
        out = run(strat, frame)
        sig = int(np.flatnonzero(out["enter_long"].fillna(0).to_numpy() == 1)[0])
        entry = sig + 1
        trade = FakeTrade(out["date"].iloc[entry], out["open"].iloc[entry])
        beta_e, e_abs, b0 = out["beta"].iloc[sig], abs(out["e6"].iloc[sig]), out["ref_close"].iloc[sig]
        for u in range(entry, entry + 12):
            strat.dp.analyzed = out.iloc[: u + 1]
            gap = np.log(out["close"].iloc[u] / trade.open_rate) - beta_e * np.log(
                out["ref_close"].iloc[u] / b0
            )
            reason = strat.custom_exit(PAIR, trade, None, 0.0, 0.0)
            if gap >= 0.6 * e_abs:
                self.assertEqual(reason, "residual_gap_closed")
            elif u == entry + 11:
                self.assertEqual(reason, "time_12h")
            else:
                self.assertIsNone(reason)

    def test_custom_exit_time_only(self):
        strat, frame = build(2600, 2600)
        out = run(strat, frame)
        # Build a trade whose price only falls, so the target never hits.
        entry = 2000
        trade = FakeTrade(out["date"].iloc[entry], out["close"].max() * 10)
        strat.dp.analyzed = out.iloc[: entry + 11]
        self.assertIsNone(strat.custom_exit(PAIR, trade, None, 0.0, 0.0))
        strat.dp.analyzed = out.iloc[: entry + 12]
        self.assertEqual(strat.custom_exit(PAIR, trade, None, 0.0, 0.0), "time_12h")
        self.assertEqual(out["date"].iloc[entry + 11] - trade.open_date_utc, timedelta(hours=11))


if __name__ == "__main__":
    unittest.main()
