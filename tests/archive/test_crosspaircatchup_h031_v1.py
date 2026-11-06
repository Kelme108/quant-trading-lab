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


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / "_archive" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Strategy = load_strategy("CrossPairCatchUp_H031_v1.py", "CrossPairCatchUp_H031_v1")


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


def make_prices(n):
    """Leaders jump at some bars while BNB stays flat -> some entries."""
    rng = np.random.default_rng(1)
    base = 100 + np.cumsum(rng.normal(0, 0.3, n))
    btc = base.copy()
    eth = base * 1.1
    bnb = np.full(n, 50.0) + np.cumsum(rng.normal(0, 0.05, n))
    for k in range(80, n - 10, 40):
        btc[k:] *= 1.03
        eth[k:] *= 1.03
    return {"BTC/USDT": btc, "ETH/USDT": eth, "BNB/USDT": bnb}


def run(prices, n, pair="BNB/USDT", volume=1.0):
    frames = {p: make_frame(list(v[:n]), volume) for p, v in prices.items()}
    s = Strategy()
    s.dp = FakeDP(frames)
    df = frames[pair].copy()
    md = {"pair": pair}
    df = s.populate_indicators(df, md)
    df = s.populate_entry_trend(df, md)
    df = s.populate_exit_trend(df, md)
    return s, df


class H031Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 50)
        self.assertEqual(
            Strategy().protections,
            [{"method": "CooldownPeriod", "stop_duration_candles": 4}],
        )

    def test_signals_binary_and_present(self):
        _, df = run(make_prices(400), 400)
        self.assertGreater(int(df["enter_long"].fillna(0).sum()), 0)
        for col in ("enter_long", "exit_long"):
            self.assertTrue(set(df[col].dropna().unique().tolist()).issubset({1}))

    def test_exit_four_bars_after_entry(self):
        _, df = run(make_prices(400), 400)
        first = int(df.index[df["enter_long"] == 1][0])
        self.assertEqual(df.loc[first + 4, "exit_long"], 1)

    def test_zero_volume_no_signal(self):
        _, df = run(make_prices(400), 400, volume=0.0)
        self.assertEqual(int(df["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(df["exit_long"].fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self):
        s, df = run(make_prices(400), 400)
        self.assertEqual(int(df.iloc[:2]["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(df.iloc[: s.startup_candle_count - 48]["enter_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self):
        prices = make_prices(400)
        _, short = run(prices, 300)
        _, long = run(prices, 340)
        cols = ["ret2", "leader_ret2", "raw_entry", "enter_long"]
        pd.testing.assert_frame_equal(
            short[cols].iloc[:290].reset_index(drop=True),
            long[cols].iloc[:290].reset_index(drop=True),
            check_dtype=False,
        )
        a = short["exit_long"].iloc[:290].fillna(0).to_numpy()
        b = long["exit_long"].iloc[:290].fillna(0).to_numpy()
        self.assertTrue((a == b).all())


if __name__ == "__main__":
    unittest.main()
