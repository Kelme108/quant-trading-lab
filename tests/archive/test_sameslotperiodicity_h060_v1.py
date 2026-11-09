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


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / "_archive" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Strategy = load_strategy("SameSlotPeriodicity_H060_v1.py", "SameSlotPeriodicity_H060_v1")


def make_frame(n_bars: int, drift_block: int = 2, drift: float = 0.01, seed: int = 7) -> pd.DataFrame:
    """1h bars from 2024-01-01 00:00 UTC; bars in drift_block rise by `drift` per block, others are noise."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")
    opens, closes = [], []
    price = 100.0
    for ts in dates:
        step = rng.normal(0.0, 0.002)
        if ts.hour // 4 == drift_block:
            step += drift / 4.0
        opens.append(price)
        price = price * (1.0 + step)
        closes.append(price)
    return pd.DataFrame(
        {
            "date": dates,
            "open": opens,
            "high": [max(o, c) * 1.002 for o, c in zip(opens, closes)],
            "low": [min(o, c) * 0.998 for o, c in zip(opens, closes)],
            "close": closes,
            "volume": [1.0] * n_bars,
        }
    )


def run(frame: pd.DataFrame) -> pd.DataFrame:
    strategy = Strategy()
    frame = strategy.populate_indicators(frame, {"pair": "BTC/USDT"})
    frame = strategy.populate_entry_trend(frame, {"pair": "BTC/USDT"})
    return strategy.populate_exit_trend(frame, {"pair": "BTC/USDT"})


class SameSlotPeriodicityTests(unittest.TestCase):
    def test_class_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertAlmostEqual(Strategy.stoploss, -0.03)
        self.assertGreaterEqual(Strategy.startup_candle_count, 720)

    def test_signals_binary_and_on_expected_bars(self) -> None:
        frame = run(make_frame(24 * 40))
        for column in ("enter_long", "exit_long"):
            self.assertIn(column, frame)
            values = frame[column].dropna().unique().tolist()
            self.assertTrue(set(values).issubset({1}))
        entries = frame[frame["enter_long"] == 1]
        exits = frame[frame["exit_long"] == 1]
        self.assertGreater(len(entries), 0)
        # Block 2 (08:00-11:59) is the drifting block: enter at close of 07:00 bar, exit at close of 11:00 bar.
        self.assertTrue((entries["date"].dt.hour == 7).all())
        self.assertTrue((exits["date"].dt.hour == 11).all())
        # At most one entry per UTC day.
        self.assertEqual(entries["date"].dt.floor("D").value_counts().max(), 1)
        # No entries before 28 full days of history (selection for day 29 is the first possible).
        self.assertGreaterEqual(entries["date"].min(), pd.Timestamp("2024-01-29 07:00", tz="UTC"))

    def test_block_zero_entry_on_previous_day_2300_bar(self) -> None:
        frame = run(make_frame(24 * 40, drift_block=0))
        entries = frame[frame["enter_long"] == 1]
        exits = frame[frame["exit_long"] == 1]
        self.assertGreater(len(entries), 0)
        self.assertTrue((entries["date"].dt.hour == 23).all())
        self.assertTrue((exits["date"].dt.hour == 3).all())

    def test_no_trade_without_drift(self) -> None:
        frame = run(make_frame(24 * 40, drift=0.0))
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_missing_bar_makes_block_ineligible(self) -> None:
        frame = make_frame(24 * 40)
        # Drop a block-2 bar on day 10: block 2 is ineligible for days 11 .. 38.
        drop = frame.index[frame["date"] == pd.Timestamp("2024-01-10 09:00", tz="UTC")]
        frame = run(frame.drop(drop).reset_index(drop=True))
        entries = frame[frame["enter_long"] == 1]
        bad = entries[
            (entries["date"] >= pd.Timestamp("2024-01-11", tz="UTC"))
            & (entries["date"] < pd.Timestamp("2024-02-08", tz="UTC"))
            & (entries["date"].dt.hour == 7)
        ]
        self.assertEqual(len(bad), 0)

    def test_zero_volume_does_not_create_signals(self) -> None:
        frame = make_frame(24 * 40)
        frame["volume"] = 0.0
        frame = run(frame)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(frame.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_nan_startup_values_do_not_create_signals(self) -> None:
        frame = run(make_frame(24 * 40))
        # The 28-day window (672 bars) is undefined until 28 full days have closed; the frame starts at 00:00,
        # so the first possible signal is the 07:00 bar of day 29 (row 679).
        warmup = 24 * 28 + 7
        self.assertEqual(int(frame.iloc[:warmup]["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame.iloc[:warmup]["exit_long"].fillna(0).sum()), 0)
        # Frame starting mid-day: still nothing until the window is complete.
        shifted = run(make_frame(24 * 40).iloc[5:].reset_index(drop=True))
        self.assertEqual(int(shifted.iloc[: 24 * 28]["enter_long"].fillna(0).sum()), 0)
        undefined = frame["slot_next_block"].isna()
        self.assertEqual(int(frame.loc[undefined, "enter_long"].fillna(0).sum()), 0)

    def test_signals_do_not_change_when_future_candles_appended(self) -> None:
        full = make_frame(24 * 45)
        for n in (24 * 35 + 7, 24 * 36 + 11, 24 * 37 + 23, 24 * 38):
            before = run(full.iloc[:n].copy())
            after = run(full.copy()).iloc[:n]
            for column in ("enter_long", "exit_long", "slot_next_block", "slot_today_block"):
                pd.testing.assert_series_equal(
                    before[column].reset_index(drop=True),
                    after[column].reset_index(drop=True),
                    check_dtype=False,
                    check_names=False,
                )


if __name__ == "__main__":
    unittest.main()
