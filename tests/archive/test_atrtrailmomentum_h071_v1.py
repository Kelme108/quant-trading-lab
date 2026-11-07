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
PATH = ROOT / "user_data" / "strategies" / "_archive" / "ATRTrailMomentum_H071_v1.py"
SPEC = importlib.util.spec_from_file_location("ATRTrailMomentum_H071_v1", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
Strategy = MODULE.ATRTrailMomentum_H071_v1
trail_exit_reason = MODULE.trail_exit_reason

HOUR = timedelta(hours=1)


def make_frame(n: int, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0, 0.006, n)
    # Bursts of strong drift so the momentum condition is met at times.
    for start in range(800, n, 150):
        returns[start:start + 20] += 0.004
    close = 100.0 * np.exp(np.cumsum(returns))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) * 1.003
    low = np.minimum(open_, close) * 0.997
    dates = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
    return pd.DataFrame(
        {"date": dates, "open": open_, "high": high, "low": low, "close": close, "volume": 1.0}
    )


def run(frame: pd.DataFrame) -> pd.DataFrame:
    strategy = Strategy()
    frame = strategy.populate_indicators(frame, {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


class ATRTrailMomentumH071Tests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertAlmostEqual(Strategy.stoploss, -0.08)
        self.assertGreaterEqual(Strategy.startup_candle_count, 744)
        self.assertEqual(
            Strategy().protections,
            [{"method": "CooldownPeriod", "stop_duration_candles": 6}],
        )

    def test_entries_occur_and_are_binary(self) -> None:
        frame = run(make_frame(1600))
        self.assertGreater(int(frame["enter_long"].fillna(0).sum()), 0)
        for column in ("enter_long", "exit_long"):
            if column in frame:
                self.assertTrue(set(frame[column].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_gives_no_signal(self) -> None:
        frame = make_frame(1600)
        frame["volume"] = 0.0
        frame = run(frame)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(frame.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        # The trail would be breached, but no exit fires on zero-volume candles.
        open_date = frame.loc[900, "date"]
        now = frame.loc[960, "date"]
        self.assertIsNone(trail_exit_reason(frame, open_date, 1e9, now))

    def test_undefined_startup_gives_no_signal(self) -> None:
        frame = run(make_frame(1600))
        self.assertTrue(frame.loc[: 24 + 720 - 1, "mom_std"].isna().all())
        self.assertEqual(int(frame.loc[: 24 + 720 - 1, "enter_long"].fillna(0).sum()), 0)
        undefined = frame["mom_std"].isna() | frame["mom"].isna() | frame["atr"].isna()
        self.assertEqual(int(frame.loc[undefined, "enter_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self) -> None:
        full = make_frame(1600)
        n = 1300
        before = run(full.iloc[:n].copy())
        after = run(full.copy())
        columns = ["mom", "mom_std", "atr", "enter_long"]
        pd.testing.assert_frame_equal(
            before[columns].fillna(-1.0), after.iloc[:n][columns].fillna(-1.0), check_dtype=False
        )
        # Exit decision at a given time does not depend on later candles.
        for i in range(900, n - 30, 7):
            open_date = full.loc[i, "date"]
            rate = full.loc[i, "open"]
            for k in (1, 5, 24, 25):
                now = open_date + k * HOUR
                self.assertEqual(
                    trail_exit_reason(before, open_date, rate, now),
                    trail_exit_reason(after, open_date, rate, now),
                )

    def test_trail_and_time_exit(self) -> None:
        n = 60
        dates = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
        frame = pd.DataFrame(
            {"date": dates, "close": 100.0, "atr": 1.0, "volume": 1.0}
        )
        open_date = dates[10]
        # Flat price: trail = 100 - 2.5 = 97.5, never breached -> time exit after 24 closed trade bars.
        self.assertIsNone(trail_exit_reason(frame, open_date, 100.0, open_date + 23 * HOUR))
        self.assertEqual(trail_exit_reason(frame, open_date, 100.0, open_date + 24 * HOUR), "time_exit_24h")
        # Ratchet: rise to 110 on bar e+2 lifts T to 107.5; close 107 on e+3 breaches it.
        rising = frame.copy()
        rising.loc[12, "close"] = 110.0
        rising.loc[13:, "close"] = 107.0
        self.assertIsNone(trail_exit_reason(rising, open_date, 100.0, open_date + 3 * HOUR))
        self.assertEqual(trail_exit_reason(rising, open_date, 100.0, open_date + 4 * HOUR), "atr_trail")
        # Initial trail uses ATR of the signal bar (e-1): close 97 on bar e breaches 97.5.
        drop = frame.copy()
        drop.loc[10:, "close"] = 97.0
        self.assertEqual(trail_exit_reason(drop, open_date, 100.0, open_date + HOUR), "atr_trail")
        self.assertIsNone(trail_exit_reason(drop, open_date, 100.0, open_date))


if __name__ == "__main__":
    unittest.main()
