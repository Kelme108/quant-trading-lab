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

ROOT = Path(__file__).parents[1]
NAME = "RSIOverboughtMomentum_H085_v1"


def wilder_rsi(dataframe, timeperiod):
    """Causal Wilder RSI used in place of TA-Lib on the host (NaN for the first `timeperiod` rows)."""
    delta = dataframe["close"].diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    alpha = 1.0 / timeperiod
    avg_gain = gain.ewm(alpha=alpha, adjust=False, min_periods=timeperiod).mean()
    avg_loss = loss.ewm(alpha=alpha, adjust=False, min_periods=timeperiod).mean()
    rs = avg_gain / avg_loss
    rsi = 100.0 - 100.0 / (1.0 + rs)
    rsi[delta.isna()] = np.nan
    return rsi


def load_module():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ta = types.SimpleNamespace(RSI=wilder_rsi)
    return module


MODULE = load_module()
Strategy = getattr(MODULE, NAME)


def make_prices(n, seed=7):
    rng = np.random.default_rng(seed)
    return list(100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.01, n))))


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


def run(frame):
    strat = Strategy()
    frame = strat.populate_indicators(frame.copy(), {"pair": "ETH/USDT"})
    frame = strat.populate_entry_trend(frame, {"pair": "ETH/USDT"})
    frame = strat.populate_exit_trend(frame, {"pair": "ETH/USDT"})
    return frame


class FakeTrade:
    def __init__(self, open_date):
        self.open_date_utc = open_date


class RSIOverboughtMomentumH085Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.99)
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 400)
        self.assertEqual(MODULE.RSI_LENGTH, 14)
        self.assertEqual(MODULE.RSI_ENTRY_LEVEL, 70.0)
        self.assertEqual(MODULE.RSI_EXIT_LEVEL, 55.0)
        self.assertEqual(MODULE.TAKE_PROFIT, 0.03)
        self.assertEqual(MODULE.TIME_EXIT_HOURS, 24)

    def test_signals_binary_and_present(self):
        frame = run(make_frame(make_prices(2000)))
        for column in ("enter_long", "exit_long"):
            self.assertIn(column, frame)
            self.assertTrue(set(frame[column].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(int(frame["enter_long"].fillna(0).sum()), 0)
        self.assertGreater(int(frame["exit_long"].fillna(0).sum()), 0)

    def test_entry_is_fresh_cross_only(self):
        frame = run(make_frame(make_prices(2000)))
        entries = frame["enter_long"].fillna(0) == 1
        self.assertTrue((frame.loc[entries, "rsi"] > 70).all())
        self.assertTrue((frame.loc[entries, "rsi"].shift(0).index.isin(frame.index)).all())
        self.assertTrue((frame["rsi"].shift(1)[entries] <= 70).all())
        exits = frame["exit_long"].fillna(0) == 1
        self.assertTrue((frame.loc[exits, "rsi"] < 55).all())

    def test_zero_volume_no_signal(self):
        frame = run(make_frame(make_prices(2000), volume=0.0))
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(frame.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self):
        frame = run(make_frame(make_prices(400)))
        undefined = frame["rsi"].isna() | frame["rsi"].shift(1).isna()
        self.assertTrue(undefined.iloc[:15].all())
        self.assertEqual(int(frame.loc[undefined, "enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame.loc[frame["rsi"].isna(), "exit_long"].fillna(0).sum()), 0)

    def test_no_lookahead_when_appending(self):
        prices = make_prices(1500)
        n = 1200
        short = run(make_frame(prices[:n]))
        full = run(make_frame(prices))
        for column in ("rsi", "rsi_prev", "enter_long", "exit_long"):
            pd.testing.assert_series_equal(
                short[column].fillna(-1).reset_index(drop=True),
                full[column].iloc[:n].fillna(-1).reset_index(drop=True),
                check_dtype=False,
                check_names=False,
            )

    def test_custom_exit_take_profit(self):
        strat = Strategy()
        opened = datetime(2024, 1, 1, tzinfo=timezone.utc)
        trade = FakeTrade(opened)
        now = opened + timedelta(hours=3)
        self.assertEqual(strat.custom_exit("ETH/USDT", trade, now, 103.0, 0.03), "take_profit_3pct")
        self.assertEqual(strat.custom_exit("ETH/USDT", trade, now, 105.0, 0.05), "take_profit_3pct")
        self.assertIsNone(strat.custom_exit("ETH/USDT", trade, now, 102.9, 0.0299))

    def test_custom_exit_time(self):
        strat = Strategy()
        opened = datetime(2024, 1, 1, tzinfo=timezone.utc)
        trade = FakeTrade(opened)
        self.assertIsNone(strat.custom_exit("ETH/USDT", trade, opened + timedelta(hours=23), 100.0, 0.0))
        self.assertEqual(
            strat.custom_exit("ETH/USDT", trade, opened + timedelta(hours=24), 100.0, 0.0), "time_exit_24h"
        )
        self.assertEqual(
            strat.custom_exit("ETH/USDT", trade, opened + timedelta(hours=30), 95.0, -0.05), "time_exit_24h"
        )


if __name__ == "__main__":
    unittest.main()
