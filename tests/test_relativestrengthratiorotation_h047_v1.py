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

ROOT = Path(__file__).parents[1]
NAME = "RelativeStrengthRatioRotation_H047_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, NAME)


Strategy = load_strategy()


class FakeDP:
    def __init__(self, frames):
        self.frames = frames

    def get_pair_dataframe(self, pair, timeframe):
        return self.frames[pair].copy()


def make_frame(prices, volume=1.0):
    n = len(prices)
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=n, freq="1h"),
            "open": prices,
            "high": [p * 1.01 for p in prices],
            "low": [p * 0.99 for p in prices],
            "close": prices,
            "volume": [volume] * n,
        }
    )


def make_prices(n, seed):
    rng = np.random.default_rng(seed)
    return list(100.0 * np.exp(np.cumsum(rng.normal(0.0005, 0.01, n))))


def build(n, volume=1.0, total=None):
    """Return (strategy, frame) for ETH using BTC/BNB as basket."""
    total = total or n
    series = {
        "ETH/USDT": make_prices(total, 1)[:n],
        "BTC/USDT": make_prices(total, 2)[:n],
        "BNB/USDT": make_prices(total, 3)[:n],
    }
    frames = {k: make_frame(v) for k, v in series.items()}
    strat = Strategy()
    strat.dp = FakeDP(frames)
    frame = make_frame(series["ETH/USDT"], volume)
    return strat, frame


def run(strat, frame):
    meta = {"pair": "ETH/USDT"}
    frame = strat.populate_indicators(frame, meta)
    frame = strat.populate_entry_trend(frame, meta)
    return strat.populate_exit_trend(frame, meta)


class H047Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 480)
        self.assertEqual(
            Strategy().protections,
            [{"method": "CooldownPeriod", "stop_duration_candles": 12}],
        )

    def test_signals_binary(self):
        strat, frame = build(1500)
        out = run(strat, frame)
        for col in ("enter_long", "exit_long"):
            self.assertIn(col, out)
            self.assertTrue(set(out[col].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(out["exit_long"].fillna(0).sum(), 0)

    def test_zero_volume_no_signal(self):
        strat, frame = build(1500, volume=0.0)
        out = run(strat, frame)
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(out["exit_long"].fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self):
        strat, frame = build(1500)
        out = run(strat, frame)
        self.assertEqual(int(out.iloc[:479]["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(out.iloc[:479]["exit_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self):
        n, total = 1200, 1400
        strat_a, frame_a = build(n, total=total)
        strat_b, frame_b = build(total, total=total)
        a = run(strat_a, frame_a)
        b = run(strat_b, frame_b)
        cols = ["ratio", "ratio_sma_entry", "ratio_high", "ratio_sma_exit", "close_sma_regime"]
        pd.testing.assert_frame_equal(a.loc[: n - 1, cols], b.loc[: n - 1, cols])
        for col in ("enter_long", "exit_long"):
            pd.testing.assert_series_equal(
                a[col].iloc[:n].fillna(0), b[col].iloc[:n].fillna(0), check_dtype=False
            )


if __name__ == "__main__":
    unittest.main()
