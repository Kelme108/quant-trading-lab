import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

freqtrade = types.ModuleType("freqtrade")
strategy_module = types.ModuleType("freqtrade.strategy")
strategy_module.IStrategy = object
strategy_module.merge_informative_pair = lambda *a, **k: a[0]
persistence = types.ModuleType("freqtrade.persistence")
persistence.Trade = type("Trade", (), {"get_trades_proxy": staticmethod(lambda **k: [])})
freqtrade.strategy = strategy_module
freqtrade.persistence = persistence
sys.modules.setdefault("freqtrade", freqtrade)
sys.modules.setdefault("freqtrade.strategy", strategy_module)
sys.modules.setdefault("freqtrade.persistence", persistence)
talib = types.ModuleType("talib")
talib_abstract = types.ModuleType("talib.abstract")
talib_abstract.SMA = lambda dataframe, timeperiod: dataframe["close"].rolling(timeperiod).mean()
talib_abstract.RSI = lambda dataframe, timeperiod: pd.Series(50.0, index=dataframe.index)
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)

ROOT = Path(__file__).parents[1]
NAME = "PocketPivotVolume_H116_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load()
Strategy = getattr(MODULE, NAME)

SIGNAL_ROW = 295


def make_frame(rows: int = 320, low_factor: float = 0.98) -> pd.DataFrame:
    """Steady uptrend with one down bar at row 290 and a high-volume pocket pivot at row 295."""
    close = np.array([100.0 + 0.2 * i for i in range(rows)])
    close[290:] -= 0.5  # row 290 is a down bar; later rows keep the same slope
    volume = np.full(rows, 10.0)
    volume[290] = 50.0
    volume[SIGNAL_ROW] = 100.0
    frame = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=rows, freq="1h", tz="UTC"),
            "open": close,
            "high": close * 1.002,
            "low": close * 0.998,
            "close": close,
            "volume": volume,
        }
    )
    frame.loc[SIGNAL_ROW, "low"] = frame.loc[SIGNAL_ROW, "close"] * low_factor
    return frame


def run(frame: pd.DataFrame) -> pd.DataFrame:
    strategy = Strategy()
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


def entry_rows(frame: pd.DataFrame) -> list:
    if "enter_long" not in frame:
        return []
    return frame.index[frame["enter_long"].fillna(0) == 1].tolist()


class PocketPivotVolumeTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertGreaterEqual(Strategy.startup_candle_count, 250)

    def test_pivot_signal_fires_with_frozen_stop_distance(self):
        frame = run(make_frame(low_factor=0.98))
        self.assertEqual(entry_rows(frame), [SIGNAL_ROW])
        self.assertAlmostEqual(MODULE.parse_tag(frame.loc[SIGNAL_ROW, "enter_tag"]), 0.02, places=9)

    def test_stop_distance_is_floored_at_one_percent(self):
        frame = run(make_frame(low_factor=0.995))
        self.assertEqual(entry_rows(frame), [SIGNAL_ROW])
        self.assertAlmostEqual(MODULE.parse_tag(frame.loc[SIGNAL_ROW, "enter_tag"]), 0.01, places=12)

    def test_extended_signal_bar_is_skipped(self):
        self.assertEqual(entry_rows(run(make_frame(low_factor=0.97))), [])

    def test_volume_must_strictly_exceed_largest_down_bar_volume(self):
        frame = make_frame()
        frame.loc[SIGNAL_ROW, "volume"] = 50.0
        self.assertEqual(entry_rows(run(frame)), [])
        frame.loc[SIGNAL_ROW, "volume"] = 50.5
        self.assertEqual(entry_rows(run(frame)), [SIGNAL_ROW])

    def test_no_down_bar_in_window_means_no_signal(self):
        frame = make_frame()
        frame.loc[290:, "close"] += 0.5
        frame.loc[290:, "open"] = frame.loc[290:, "close"]
        frame.loc[SIGNAL_ROW, "low"] = frame.loc[SIGNAL_ROW, "close"] * 0.98
        self.assertEqual(entry_rows(run(frame)), [])

    def test_bar_must_close_above_sma_and_low_must_reach_it(self):
        frame = make_frame()
        # Extended bar: close well above SMA10, low above 1.005 x SMA10, so rule (4) fails.
        frame.loc[SIGNAL_ROW, "close"] += 3.0
        frame.loc[SIGNAL_ROW, "low"] = frame.loc[SIGNAL_ROW, "close"] * 0.9999
        self.assertEqual(entry_rows(run(frame)), [])

    def test_four_hour_filter_blocks_downtrend(self):
        frame = make_frame()
        trend = np.array([200.0 - 0.2 * i for i in range(len(frame))])
        frame["close"] = trend
        frame["open"] = trend
        frame["high"] = trend * 1.002
        frame["low"] = trend * 0.998
        out = run(frame)
        self.assertEqual(entry_rows(out), [])
        valid = out["sma50_4h"].notna()
        self.assertTrue(valid.any())
        self.assertTrue((out.loc[valid, "close_4h"] < out.loc[valid, "sma50_4h"]).all())

    def test_zero_volume_candle_produces_no_signal(self):
        frame = make_frame()
        frame.loc[SIGNAL_ROW, "volume"] = 0.0
        self.assertEqual(entry_rows(run(frame)), [])
        frame["volume"] = 0.0
        out = run(frame)
        self.assertEqual(entry_rows(out), [])
        self.assertNotIn("exit_long", out)

    def test_undefined_startup_values_produce_no_signal(self):
        out = run(make_frame())
        # 50 completed 4h closes need 200 hourly bars; before that the 4h SMA is undefined.
        self.assertTrue(out["sma50_4h"].iloc[:199].isna().all())
        self.assertTrue(out["sma_fast"].iloc[:9].isna().all())
        self.assertTrue(out["down_vol_max"].iloc[:11].isna().all())
        # A pivot pattern placed inside the undefined start-up stretch must not fire.
        early = make_frame()
        shift = 140
        for column in ("open", "high", "low", "close", "volume"):
            values = early[column].to_numpy().copy()
            early[column] = np.roll(values, -shift)
        out = run(early)
        self.assertEqual([row for row in entry_rows(out) if row < 199], [])

    def test_signal_columns_are_binary(self):
        out = run(make_frame())
        self.assertTrue(set(out["enter_long"].dropna().unique().tolist()).issubset({1}))
        if "exit_long" in out:
            self.assertTrue(set(out["exit_long"].dropna().unique().tolist()).issubset({1}))

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        full = make_frame(rows=340)
        for rows in (294, 296, 297):
            first = run(full.iloc[:rows])
            longer = run(full)
            columns = [
                c
                for c in first.columns
                if c not in {"date", "open", "high", "low", "close", "volume"}
            ]
            pd.testing.assert_frame_equal(
                first.loc[: rows - 1, columns].reset_index(drop=True),
                longer.loc[: rows - 1, columns].reset_index(drop=True),
                check_dtype=False,
            )

    def test_stoploss_is_fixed_distance_below_entry(self):
        strategy = Strategy()
        trade = SimpleNamespace(enter_tag="ppv|0.02", open_rate=100.0)
        now = datetime(2024, 1, 1, tzinfo=timezone.utc)
        self.assertAlmostEqual(strategy.custom_stoploss("X", trade, now, 100.0, 0.0), -0.02)
        self.assertAlmostEqual(strategy.custom_stoploss("X", trade, now, 105.0, 0.05), 98.0 / 105.0 - 1.0)
        self.assertLess(strategy.custom_stoploss("X", trade, now, 97.0, -0.03), 0)
        self.assertIsNone(
            strategy.custom_stoploss("X", SimpleNamespace(enter_tag=None, open_rate=100.0), now, 100.0, 0.0)
        )

    def test_take_profit_at_two_r(self):
        strategy = Strategy()
        opened = datetime(2024, 1, 1, 10, tzinfo=timezone.utc)
        trade = SimpleNamespace(enter_tag="ppv|0.01", open_rate=100.0, open_date_utc=opened)
        now = opened + timedelta(hours=3)
        self.assertIsNone(strategy.custom_exit("X", trade, now, 101.9, 0.019))
        self.assertEqual(strategy.custom_exit("X", trade, now, 102.0, 0.02), "take_profit_2r")
        wide = SimpleNamespace(enter_tag="ppv|0.025", open_rate=100.0, open_date_utc=opened)
        self.assertIsNone(strategy.custom_exit("X", wide, now, 104.9, 0.049))
        self.assertEqual(strategy.custom_exit("X", wide, now, 105.0, 0.05), "take_profit_2r")

    def test_time_exit_after_twelve_hours(self):
        strategy = Strategy()
        opened = datetime(2024, 1, 1, 10, tzinfo=timezone.utc)
        trade = SimpleNamespace(enter_tag="ppv|0.01", open_rate=100.0, open_date_utc=opened)
        self.assertIsNone(strategy.custom_exit("X", trade, opened + timedelta(hours=11), 100.0, 0.0))
        self.assertEqual(
            strategy.custom_exit("X", trade, opened + timedelta(hours=12), 100.0, 0.0), "time_exit_12h"
        )

    def test_two_entries_per_utc_day_cap(self):
        strategy = Strategy()
        day = datetime(2024, 1, 5, 9, tzinfo=timezone.utc)
        earlier = [
            SimpleNamespace(open_date_utc=datetime(2024, 1, 4, 22, tzinfo=timezone.utc)),
            SimpleNamespace(open_date_utc=datetime(2024, 1, 5, 1, tzinfo=timezone.utc)),
        ]
        original = MODULE.Trade
        try:
            for trades, expected in (
                (earlier, True),
                (earlier + [SimpleNamespace(open_date_utc=datetime(2024, 1, 5, 5, tzinfo=timezone.utc))], False),
            ):
                MODULE.Trade = type(
                    "FakeTrade", (), {"get_trades_proxy": staticmethod(lambda pair=None, _t=trades: _t)}
                )
                result = strategy.confirm_trade_entry(
                    "BTC/USDT", "limit", 1.0, 100.0, "GTC", day, "ppv|0.01", "long"
                )
                self.assertEqual(result, expected)
            self.assertFalse(
                strategy.confirm_trade_entry("BTC/USDT", "limit", 1.0, 100.0, "GTC", day, None, "long")
            )
        finally:
            MODULE.Trade = original


if __name__ == "__main__":
    unittest.main()
