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
CLASS_NAME = "WeeklyAnchoredVWAPReclaim_H041_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / f"{CLASS_NAME}.py"
    spec = importlib.util.spec_from_file_location(CLASS_NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, CLASS_NAME)


Strategy = load_strategy()


def make_frame(prices, start="2024-01-01 00:00"):  # 2024-01-01 is a Monday
    n = len(prices)
    prices = np.asarray(prices, dtype=float)
    return pd.DataFrame(
        {
            "date": pd.date_range(start, periods=n, freq="1h", tz="UTC"),
            "open": prices,
            "high": prices * 1.001,
            "low": prices * 0.999,
            "close": prices,
            "volume": np.ones(n),
        }
    )


def scenario_prices():
    # 4 weeks of slow uptrend (672 bars), then a week: 12 flat bars, 10 dip bars, reclaim.
    base = list(100.0 + 0.01 * np.arange(672))
    top = base[-1]
    week = [top] * 12 + [top * 0.98] * 10 + [top] * 5 + [top] * 141
    return base + week


def run(strategy, frame):
    frame = strategy.populate_indicators(frame, {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    return frame


class WeeklyVwapTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 500)

    def test_entry_fires_on_reclaim(self) -> None:
        frame = run(Strategy(), make_frame(scenario_prices()))
        idx = frame.index[frame["enter_long"] == 1].tolist()
        self.assertEqual(idx, [672 + 22])

    def test_signals_binary(self) -> None:
        frame = run(Strategy(), make_frame(scenario_prices()))
        for column in ("enter_long", "exit_long"):
            self.assertIn(column, frame)
            self.assertTrue(set(frame[column].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_no_signal(self) -> None:
        frame = make_frame(scenario_prices())
        frame["volume"] = 0.0
        frame = run(Strategy(), frame)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(frame.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_zero_volume_candle_no_signal(self) -> None:
        frame = make_frame(scenario_prices())
        frame.loc[672 + 22, "volume"] = 0.0
        frame = run(Strategy(), frame)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self) -> None:
        frame = run(Strategy(), make_frame(scenario_prices()))
        startup = Strategy.startup_candle_count
        self.assertEqual(int(frame.iloc[:startup]["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame.iloc[:479]["exit_long"].fillna(0).sum()), 0)

    def test_future_candles_do_not_change_signals(self) -> None:
        rng = np.random.default_rng(1)
        prices = scenario_prices()
        prices = prices + list(prices[-1] * (1 + 0.01 * np.sin(np.arange(300) / 3.0)))
        n, k = 900, 150
        a = run(Strategy(), make_frame(prices[:n]))
        b = run(Strategy(), make_frame(prices[: n + k]))
        for column in ("enter_long", "exit_long", "vwap_week", "entry_sig", "exit_time"):
            pd.testing.assert_series_equal(
                a[column].reset_index(drop=True),
                b[column].iloc[:n].reset_index(drop=True),
                check_dtype=False,
                check_names=False,
            )
        self.assertGreaterEqual(int(a["enter_long"].fillna(0).sum()), 1)
        del rng

    def test_time_exit_after_48_bars(self) -> None:
        prices = scenario_prices()
        # hold flat above VWAP: no VWAP/week-end exit before 48 bars -> time exit at entry+48 (if still inside week)
        frame = run(Strategy(), make_frame(prices))
        entry = 672 + 22
        exits = frame.index[frame["exit_long"] == 1].tolist()
        self.assertIn(entry + 48, exits)


if __name__ == "__main__":
    unittest.main()
