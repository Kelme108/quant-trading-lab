import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
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


ROOT = Path(__file__).parents[1]
FILENAME = "SessionVWAPBandFade_H086_v1.py"
CLASS_NAME = "SessionVWAPBandFade_H086_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / FILENAME
    spec = importlib.util.spec_from_file_location(CLASS_NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, CLASS_NAME)


Strategy = load_strategy()

START = pd.Timestamp("2026-01-01 00:00", tz="UTC")
DAY3 = 192  # first row of the third UTC day (00:00)
TAG_ROW = DAY3 + 20  # 05:00
ENTRY_ROW = DAY3 + 21  # 05:15
TARGET_ROW = DAY3 + 26  # 06:30


def bar(o, h, l, c, v=1.0):
    return {"open": o, "high": h, "low": l, "close": c, "volume": v}


def scenario_frame(total_rows: int = 288 + 96) -> pd.DataFrame:
    """Two flat warm-up days, then a day that trades above VWAP, dips 2 sigma below and reverts."""
    rows = [bar(100.0, 100.0, 100.0, 100.0) for _ in range(total_rows)]
    rows[DAY3 + 1] = bar(100.0, 100.3, 100.0, 100.3)  # closes above its VWAP (trend-day filter)
    rows[TAG_ROW] = bar(100.0, 100.0, 97.0, 97.6, 4.0)  # low below LB: tag
    rows[ENTRY_ROW] = bar(97.6, 98.9, 97.6, 98.8)  # back inside the band, >= 0.8% below VWAP
    for r in range(ENTRY_ROW + 1, TARGET_ROW):
        rows[r] = bar(98.8, 98.8, 98.8, 98.8)
    rows[TARGET_ROW] = bar(98.8, 100.0, 98.8, 100.0)  # close above VWAP: target exit
    frame = pd.DataFrame(rows)
    frame.insert(0, "date", pd.date_range(START, periods=total_rows, freq="15min"))
    return frame


def run(frame: pd.DataFrame) -> pd.DataFrame:
    strategy = Strategy()
    out = strategy.populate_indicators(frame.copy(), {})
    out = strategy.populate_entry_trend(out, {})
    out = strategy.populate_exit_trend(out, {})
    for column in ("enter_long", "exit_long"):
        if column not in out:
            out[column] = np.nan
    return out


class FakeTrade:
    def __init__(self, open_date):
        self.open_date_utc = open_date


class SessionVWAPBandFadeTests(unittest.TestCase):
    def test_class_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertAlmostEqual(Strategy.stoploss, -0.01)
        self.assertIsInstance(Strategy.startup_candle_count, int)
        self.assertEqual(Strategy.startup_candle_count, 192)

    def test_scenario_produces_expected_entry_and_target_exit(self) -> None:
        out = run(scenario_frame())
        entries = out.index[out["enter_long"] == 1].tolist()
        self.assertEqual(entries, [ENTRY_ROW])
        self.assertLessEqual(out.loc[TAG_ROW, "low"], out.loc[TAG_ROW, "session_lb"])
        self.assertEqual(out.loc[TARGET_ROW, "exit_long"], 1)
        self.assertEqual(out.loc[TARGET_ROW, "exit_tag"], "vwap_target")
        # Bars held below VWAP after the entry give no exit signal.
        self.assertTrue(out.loc[ENTRY_ROW:TARGET_ROW - 1, "exit_long"].isna().all())

    def test_session_end_exit_signal_on_2345_bar(self) -> None:
        frame = scenario_frame()
        frame.loc[DAY3 + 95, ["open", "high", "low", "close"]] = 90.0  # below VWAP at 23:45
        out = run(frame)
        self.assertEqual(out.loc[DAY3 + 95, "exit_long"], 1)
        self.assertEqual(out.loc[DAY3 + 95, "exit_tag"], "session_end_2345")

    def test_custom_exit_time_exits(self) -> None:
        strategy = Strategy()
        opened = datetime(2026, 1, 3, 5, 30, tzinfo=timezone.utc)
        trade = FakeTrade(opened)
        self.assertIsNone(strategy.custom_exit("X/USDT", trade, opened + timedelta(hours=11, minutes=45), 1.0, 0.0))
        self.assertEqual(
            strategy.custom_exit("X/USDT", trade, opened + timedelta(hours=12), 1.0, 0.0),
            "time_exit_48_bars",
        )
        late = FakeTrade(datetime(2026, 1, 3, 20, 0, tzinfo=timezone.utc))
        self.assertIsNone(strategy.custom_exit("X/USDT", late, datetime(2026, 1, 3, 23, 45, tzinfo=timezone.utc), 1.0, 0.0))
        self.assertEqual(
            strategy.custom_exit("X/USDT", late, datetime(2026, 1, 4, 0, 0, tzinfo=timezone.utc), 1.0, 0.0),
            "session_end_0000",
        )

    def test_signal_columns_are_binary(self) -> None:
        n = 96 * 6
        idx = np.arange(n)
        close = 100.0 + 2.0 * np.sin(idx / 7.0) + np.where(idx % 37 == 0, -3.0, 0.0)
        frame = pd.DataFrame(
            {
                "date": pd.date_range(START, periods=n, freq="15min"),
                "open": close,
                "high": close + 0.3,
                "low": close - 0.3 + np.where(idx % 37 == 0, -2.0, 0.0),
                "close": close,
                "volume": 1.0 + (idx % 5),
            }
        )
        out = run(frame)
        for column in ("enter_long", "exit_long"):
            self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_produces_no_signal(self) -> None:
        frame = scenario_frame()
        frame["volume"] = 0.0
        out = run(frame)
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(out["exit_long"].fillna(0).sum()), 0)

        frame = scenario_frame()
        frame.loc[ENTRY_ROW, "volume"] = 0.0
        frame.loc[TARGET_ROW, "volume"] = 0.0
        out = run(frame)
        zero = out["volume"] == 0
        self.assertEqual(int(out.loc[zero, "enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(out.loc[zero, "exit_long"].fillna(0).sum()), 0)

    def test_undefined_startup_values_produce_no_signal(self) -> None:
        out = run(scenario_frame())
        startup = Strategy.startup_candle_count
        self.assertEqual(int(out.iloc[:startup]["enter_long"].fillna(0).sum()), 0)

        # Data starting mid-session: that session has no VWAP and no signals.
        frame = scenario_frame().iloc[48:].reset_index(drop=True)
        out = run(frame)
        first_day = out.index[: 48]
        self.assertTrue(out.loc[first_day, "session_vwap"].isna().all())
        self.assertEqual(int(out.loc[first_day, "enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(out.loc[first_day, "exit_long"].fillna(0).sum()), 0)

        # An undefined close on the entry bar gives no signal there.
        frame = scenario_frame()
        frame.loc[ENTRY_ROW, "close"] = np.nan
        out = run(frame)
        self.assertNotEqual(out.loc[ENTRY_ROW, "enter_long"], 1)
        self.assertNotEqual(out.loc[ENTRY_ROW, "exit_long"], 1)

    def test_signals_unchanged_when_future_candles_appended(self) -> None:
        full = scenario_frame()
        extra = full.copy()
        rng = np.random.default_rng(7)
        tail = slice(ENTRY_ROW + 3, None)
        extra.loc[ENTRY_ROW + 3:, "close"] = 95.0 + rng.normal(0, 2.0, len(extra.loc[tail]))
        extra.loc[ENTRY_ROW + 3:, "open"] = extra.loc[ENTRY_ROW + 3:, "close"]
        extra.loc[ENTRY_ROW + 3:, "high"] = extra.loc[ENTRY_ROW + 3:, "close"] + 1.0
        extra.loc[ENTRY_ROW + 3:, "low"] = extra.loc[ENTRY_ROW + 3:, "close"] - 1.0
        extra.loc[ENTRY_ROW + 3:, "volume"] = 50.0

        n = ENTRY_ROW + 3
        short = run(full.iloc[:n].copy())
        self.assertEqual(short.loc[ENTRY_ROW, "enter_long"], 1)
        for longer_source in (full, extra):
            longer = run(longer_source.copy())
            columns = ["session_vwap", "session_lb", "trend_day_ok", "enter_long", "exit_long"]
            pd.testing.assert_frame_equal(
                short.loc[: n - 1, columns],
                longer.loc[: n - 1, columns],
                check_dtype=False,
            )

    def test_one_entry_per_tag_and_position_blocks_entry(self) -> None:
        frame = scenario_frame()
        # Bars after the entry also satisfy the band conditions but the position is open.
        out = run(frame)
        self.assertEqual(int(out.loc[ENTRY_ROW + 1:TARGET_ROW, "enter_long"].fillna(0).sum()), 0)


if __name__ == "__main__":
    unittest.main()
