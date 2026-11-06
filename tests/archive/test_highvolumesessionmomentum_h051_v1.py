import importlib.util
import sys
import types
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


# Keep the tests runnable without installing Freqtrade or TA-Lib on the host.
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
NAME = "HighVolumeSessionMomentum_H051_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / "_archive" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, NAME)


Strategy = load_strategy()

SURGE_DAY = 30


def make_frame(days: int = 40, surge_days=(SURGE_DAY,)) -> pd.DataFrame:
    """Hourly candles from 00:00 UTC, slow uptrend, an 8-bar 08-15 UTC surge on high volume on surge days."""
    n = days * 24
    dates = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    returns = np.full(n, 0.0001)
    volume = np.ones(n)
    for d in surge_days:
        for h in range(8, 16):
            returns[d * 24 + h] = 0.004
            volume[d * 24 + h] = 3.0
    close = 100.0 * np.cumprod(1.0 + returns)
    open_ = np.concatenate([[100.0], close[:-1]])
    high = np.maximum(open_, close) * 1.001
    low = np.minimum(open_, close) * 0.999
    return pd.DataFrame(
        {"date": dates, "open": open_, "high": high, "low": low, "close": close, "volume": volume}
    )


def run(frame: pd.DataFrame) -> pd.DataFrame:
    strategy = Strategy()
    frame = strategy.populate_indicators(frame.copy(), {"pair": "BTC/USDT"})
    frame = strategy.populate_entry_trend(frame, {"pair": "BTC/USDT"})
    return strategy.populate_exit_trend(frame, {"pair": "BTC/USDT"})


def entries(frame: pd.DataFrame) -> pd.Series:
    return frame.get("enter_long", pd.Series(0, index=frame.index)).fillna(0)


def exits(frame: pd.DataFrame) -> pd.Series:
    return frame.get("exit_long", pd.Series(0, index=frame.index)).fillna(0)


class HighVolumeSessionMomentumTests(unittest.TestCase):
    def test_class_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertAlmostEqual(Strategy.stoploss, -0.015)
        self.assertGreaterEqual(Strategy.startup_candle_count, 487)

    def test_surge_day_enters_at_15utc_and_exits_at_22utc(self) -> None:
        frame = run(make_frame())
        entry_rows = frame.index[entries(frame) == 1].tolist()
        self.assertEqual(entry_rows, [SURGE_DAY * 24 + 15])
        exit_hours = set(frame.loc[exits(frame) == 1, "date"].dt.hour)
        self.assertEqual(exit_hours, {22})

    def test_signal_columns_are_binary(self) -> None:
        frame = run(make_frame())
        for column in ("enter_long", "exit_long"):
            self.assertIn(column, frame)
            self.assertTrue(set(frame[column].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_produces_no_signal(self) -> None:
        frame = make_frame()
        frame["volume"] = 0.0
        frame = run(frame)
        self.assertEqual(int(entries(frame).sum()), 0)
        self.assertEqual(int(exits(frame).sum()), 0)

        # Zero volume only on the 15:00 surge bar also blocks the entry.
        frame = make_frame()
        frame.loc[SURGE_DAY * 24 + 15, "volume"] = 0.0
        self.assertEqual(int(entries(run(frame)).sum()), 0)

    def test_undefined_startup_values_produce_no_signal(self) -> None:
        # Surges on days 5 and 15: SMA200 or the 20-day volume reference is still undefined.
        frame = run(make_frame(days=25, surge_days=(5, 15)))
        self.assertEqual(int(entries(frame).sum()), 0)
        frame = run(make_frame())
        self.assertEqual(int(entries(frame).iloc[: Strategy.startup_candle_count].sum()), 0)

    def test_missing_session_bar_produces_no_signal(self) -> None:
        frame = make_frame().drop(index=SURGE_DAY * 24 + 10).reset_index(drop=True)
        self.assertEqual(int(entries(run(frame)).sum()), 0)

    def test_signals_do_not_change_when_future_candles_are_appended(self) -> None:
        full = make_frame(days=45, surge_days=(SURGE_DAY, 40))
        for n in (SURGE_DAY * 24 + 16, SURGE_DAY * 24 + 20, 38 * 24 + 5):
            short = run(full.iloc[:n].copy())
            longer = run(full.iloc[: n + 100].copy())
            columns = ["session_ret", "session_vol", "close_loc", "sma200", "vol_ref"]
            pd.testing.assert_frame_equal(
                short[columns], longer.iloc[:n][columns], check_dtype=False
            )
            pd.testing.assert_series_equal(
                entries(short), entries(longer).iloc[:n], check_dtype=False, check_names=False
            )
            pd.testing.assert_series_equal(
                exits(short), exits(longer).iloc[:n], check_dtype=False, check_names=False
            )


if __name__ == "__main__":
    unittest.main()
