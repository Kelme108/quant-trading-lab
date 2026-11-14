import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

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


Strategy = load_strategy("DualThrustIntraday_H139_v1.py", "DualThrustIntraday_H139_v1")

START = pd.Timestamp("2024-01-01 00:00", tz="UTC")
JUMP_BAR = 30 * 24 + 3  # 03:00 bar of day 30


def make_frame(n_bars: int = 33 * 24, jump: bool = True) -> pd.DataFrame:
    """Slow uptrend; on day 30 the price jumps at 03:00 (a Dual Thrust breakout)."""
    closes = []
    for i in range(n_bars):
        price = 100.0 + 0.05 * i
        if jump and i >= JUMP_BAR:
            price *= 1.08
        closes.append(price)
    opens = [closes[0]] + closes[:-1]
    # The day-30 jump bar opens at the pre-jump level.
    frame = pd.DataFrame(
        {
            "date": pd.date_range(START, periods=n_bars, freq="1h"),
            "open": opens,
            "high": [max(o, c) * 1.001 for o, c in zip(opens, closes)],
            "low": [min(o, c) * 0.999 for o, c in zip(opens, closes)],
            "close": closes,
            "volume": [10.0] * n_bars,
        }
    )
    return frame


def run(frame: pd.DataFrame) -> pd.DataFrame:
    strategy = Strategy()
    frame = strategy.populate_indicators(frame, {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    return frame


class FakeTrade:
    def __init__(self, open_date_utc):
        self.open_date_utc = open_date_utc


class DualThrustH139Tests(unittest.TestCase):
    def test_class_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.05)
        self.assertGreaterEqual(Strategy.startup_candle_count, 300)

    def test_breakout_entry_once_per_day(self) -> None:
        frame = run(make_frame())
        entries = frame.index[frame["enter_long"] == 1].tolist()
        self.assertEqual(entries, [JUMP_BAR])
        row = frame.loc[JUMP_BAR]
        self.assertGreater(row["close"], row["upper"])
        self.assertGreaterEqual(row["half_range_ratio"], 0.01)
        self.assertEqual(row["filter_4h"], 1.0)

    def test_level_formula(self) -> None:
        frame = run(make_frame())
        day = 30
        raw = make_frame()
        highs = [raw["high"][d * 24:(d + 1) * 24].max() for d in range(day - 4, day)]
        lows = [raw["low"][d * 24:(d + 1) * 24].min() for d in range(day - 4, day)]
        closes = [raw["close"][d * 24 + 23] for d in range(day - 4, day)]
        rng = max(max(highs) - min(closes), max(closes) - min(lows))
        o = raw["open"][day * 24]
        row = frame.loc[day * 24 + 5]
        self.assertAlmostEqual(row["upper"], o + 0.5 * rng)
        self.assertAlmostEqual(row["lower"], o - 0.5 * rng)

    def test_no_entry_after_17h_open(self) -> None:
        raw = make_frame(jump=False)
        # Jump only from the 18:00 bar of day 30.
        late = 30 * 24 + 18
        for col in ("open", "high", "low", "close"):
            raw.loc[late:, col] = raw.loc[late:, col] * 1.08
        frame = run(raw)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)

    def test_filter_blocks_entry_in_downtrend(self) -> None:
        raw = make_frame(jump=False)
        closes = 300.0 - 0.15 * raw.index.to_series()
        opens = closes.shift(1).fillna(closes.iloc[0])
        raw["close"] = closes
        raw["open"] = opens
        raw["high"] = pd.concat([opens, closes], axis=1).max(axis=1) * 1.001
        raw["low"] = pd.concat([opens, closes], axis=1).min(axis=1) * 0.999
        for col in ("open", "high", "low", "close"):
            raw.loc[JUMP_BAR:, col] = raw.loc[JUMP_BAR:, col] * 1.05
        frame = run(raw)
        self.assertGreater(frame.loc[JUMP_BAR, "close"], frame.loc[JUMP_BAR, "upper"])
        self.assertEqual(frame.loc[JUMP_BAR, "filter_4h"], 0.0)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)

    def test_exit_below_lower_and_day_end(self) -> None:
        frame = run(make_frame())
        day_end_rows = frame[frame["hour_utc"] == 23]
        self.assertTrue((day_end_rows["exit_long"] == 1).all())
        # Close below LOWER signals an exit on any hour.
        raw = make_frame()
        drop = 30 * 24 + 8
        for col in ("open", "high", "low", "close"):
            raw.loc[drop:, col] = raw.loc[drop:, col] * 0.8
        frame = run(raw)
        self.assertEqual(frame.loc[drop, "exit_long"], 1)
        self.assertEqual(frame.loc[drop, "exit_tag"], "close_below_lower")
        self.assertTrue(pd.isna(frame.loc[30 * 24 + 7, "exit_long"]))

    def test_custom_exit_time_limit(self) -> None:
        strategy = Strategy()
        opened = datetime(2024, 2, 1, 5, 0, tzinfo=timezone.utc)
        trade = FakeTrade(opened)
        self.assertIsNone(
            strategy.custom_exit(
                "BTC/USDT", trade, opened + timedelta(hours=11), 100.0, 0.5
            )
        )
        self.assertEqual(
            strategy.custom_exit(
                "BTC/USDT", trade, opened + timedelta(hours=12), 100.0, -0.01
            ),
            "time_exit_12h",
        )

    def test_signal_columns_are_binary(self) -> None:
        frame = run(make_frame())
        for column in ("enter_long", "exit_long"):
            values = frame[column].dropna().unique().tolist()
            self.assertTrue(set(values).issubset({1}))

    def test_zero_volume_no_signal(self) -> None:
        raw = make_frame()
        raw["volume"] = 0.0
        frame = run(raw)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame["exit_long"].fillna(0).sum()), 0)
        # A single zero-volume breakout bar gives no entry.
        raw = make_frame()
        raw.loc[JUMP_BAR, "volume"] = 0.0
        frame = run(raw)
        self.assertTrue(pd.isna(frame.loc[JUMP_BAR, "enter_long"]))

    def test_nan_startup_no_signal(self) -> None:
        frame = run(make_frame())
        startup = Strategy.startup_candle_count
        self.assertEqual(int(frame.iloc[:startup]["enter_long"].fillna(0).sum()), 0)
        # Early rows have undefined levels.
        self.assertTrue(frame.loc[:80, "upper"].isna().all())
        self.assertTrue(frame.loc[:150, "filter_4h"].isna().all())

    def test_missing_bar_disables_day(self) -> None:
        raw = make_frame()
        raw = raw.drop(index=30 * 24 - 10).reset_index(drop=True)  # hole in day 29
        frame = run(raw)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self) -> None:
        full = make_frame(36 * 24)
        n = 31 * 24 + 6
        before = run(full.iloc[:n].copy().reset_index(drop=True))
        after = run(full.copy())
        cols = [c for c in before.columns if c not in {"date", "day_utc"}]
        pd.testing.assert_frame_equal(
            before.loc[: n - 1, cols],
            after.loc[: n - 1, cols],
            check_dtype=False,
        )

    def test_no_lookahead_with_changed_future(self) -> None:
        raw = make_frame()
        changed = raw.copy()
        cut = 31 * 24
        for col in ("open", "high", "low", "close"):
            changed.loc[cut:, col] = 500.0
        a = run(raw)
        b = run(changed)
        cols = [c for c in a.columns if c not in {"date", "day_utc"}]
        pd.testing.assert_frame_equal(
            a.loc[: cut - 1, cols], b.loc[: cut - 1, cols], check_dtype=False
        )


if __name__ == "__main__":
    unittest.main()
