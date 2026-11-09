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


class _TradeStub:
    trades: list = []

    @classmethod
    def get_trades_proxy(cls, pair=None, **kwargs):
        return list(cls.trades)


persistence_module = types.ModuleType("freqtrade.persistence")
persistence_module.Trade = _TradeStub
sys.modules.setdefault("freqtrade.persistence", persistence_module)

ROOT = Path(__file__).parents[1]
FILENAME = "RoundNumberSupportBounce_H056_v1.py"
CLASS_NAME = "RoundNumberSupportBounce_H056_v1"


def load_module():
    path = ROOT / "user_data" / "strategies" / FILENAME
    spec = importlib.util.spec_from_file_location(CLASS_NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()
Strategy = MODULE.RoundNumberSupportBounce_H056_v1
START = datetime(2024, 1, 1, tzinfo=timezone.utc)
BAR = timedelta(minutes=15)
SIGNAL_INDEX = 207


def make_frame(closes, lows=None, highs=None) -> pd.DataFrame:
    n = len(closes)
    return pd.DataFrame(
        {
            "date": pd.date_range(START, periods=n, freq="15min", tz="UTC"),
            "open": list(closes),
            "high": list(highs) if highs is not None else [c * 1.001 for c in closes],
            "low": list(lows) if lows is not None else [c * 0.999 for c in closes],
            "close": list(closes),
            "volume": [1.0] * n,
        }
    )


DECLINE = [102.3, 102.1, 101.9, 101.7, 101.5, 101.4, 101.3]


def bounce_frame(extra: int = 20) -> pd.DataFrame:
    """Day 1 and early day 2 flat at 102.5 (P = 102.5, S = 1), a decline, then a bounce off L = 101.

    The rejection bar is index 207: low 100.9 (touches 101), close 101.3 (>= 1.002 * 101).
    """
    closes = [102.5] * 200 + DECLINE + [101.3] + [101.3] * extra
    lows = [c * 0.999 for c in closes]
    highs = [c * 1.001 for c in closes]
    lows[SIGNAL_INDEX] = 100.9
    highs[SIGNAL_INDEX] = 101.4
    return make_frame(closes, lows, highs)


def run(frame: pd.DataFrame) -> pd.DataFrame:
    strategy = Strategy()
    frame = strategy.populate_indicators(frame, {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    return frame


def column(frame: pd.DataFrame, name: str) -> pd.Series:
    if name in frame:
        return frame[name].fillna(0)
    return pd.Series(0, index=frame.index)


class _Trade:
    def __init__(self, open_date, open_rate=100.0, enter_tag=None):
        self.open_date_utc = open_date
        self.open_rate = open_rate
        self.enter_tag = enter_tag
        self.fee_open = 0.001
        self.fee_close = 0.001


class H056ContractTests(unittest.TestCase):
    def test_class_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.015)
        self.assertGreaterEqual(Strategy.startup_candle_count, 200)

    def test_grid_step_examples(self) -> None:
        steps = MODULE.grid_step(pd.Series([60000.0, 3000.0, 600.0, 102.5, float("nan")]))
        self.assertEqual(steps.iloc[0], 1000.0)
        self.assertEqual(steps.iloc[1], 50.0)
        self.assertEqual(steps.iloc[2], 10.0)
        self.assertEqual(steps.iloc[3], 1.0)
        self.assertTrue(pd.isna(steps.iloc[4]))

    def test_touched_level(self) -> None:
        lows = pd.Series([59800.0, 60050.0, 60100.0, 59700.0, 100.9])
        steps = pd.Series([1000.0, 1000.0, 1000.0, 1000.0, 1.0])
        levels = MODULE.touched_level(lows, steps)
        self.assertEqual(levels.iloc[0], 60000.0)  # 0.4% band below
        self.assertEqual(levels.iloc[1], 60000.0)  # 0.1% band above
        self.assertTrue(pd.isna(levels.iloc[2]))  # too far above
        self.assertTrue(pd.isna(levels.iloc[3]))  # too far below
        self.assertEqual(levels.iloc[4], 101.0)

    def test_previous_day_reference(self) -> None:
        frame = Strategy().populate_indicators(bounce_frame(), {})
        self.assertTrue(frame.loc[:95, "grid_ref"].isna().all())
        self.assertEqual(frame.loc[96, "grid_ref"], 102.5)
        self.assertEqual(frame.loc[96, "grid_step"], 1.0)
        # Lookbacks exclude bar t.
        self.assertEqual(frame.loc[SIGNAL_INDEX, "prior_min_close"], 101.3)
        self.assertAlmostEqual(frame.loc[SIGNAL_INDEX, "prior_high"], 102.5 * 1.001)

    def test_bounce_fires_one_entry(self) -> None:
        frame = run(bounce_frame())
        entries = column(frame, "enter_long")
        self.assertEqual(entries.sum(), 1)
        self.assertEqual(entries[SIGNAL_INDEX], 1)
        self.assertEqual(MODULE.parse_tag(frame.loc[SIGNAL_INDEX, "enter_tag"]), 101.0)
        self.assertIn("2024-01-03", frame.loc[SIGNAL_INDEX, "enter_tag"])

    def test_weak_rejection_blocks_entry(self) -> None:
        frame = bounce_frame()
        frame.loc[SIGNAL_INDEX, "close"] = 101.15  # below 1.002 * 101
        self.assertEqual(column(run(frame), "enter_long").sum(), 0)

    def test_prior_close_below_level_blocks_entry(self) -> None:
        frame = bounce_frame()
        frame.loc[205, "close"] = 100.9
        frame.loc[205, "low"] = 100.8
        self.assertEqual(column(run(frame), "enter_long").sum(), 0)

    def test_small_decline_blocks_entry(self) -> None:
        frame = bounce_frame()
        frame.loc[: SIGNAL_INDEX - 1, "high"] = 102.2  # < 1.012 * 101 = 102.212
        self.assertEqual(column(run(frame), "enter_long").sum(), 0)

    def test_signal_columns_are_binary(self) -> None:
        closes = [100.0 + (i % 13) * 0.3 - (i % 29) * 0.2 for i in range(900)]
        frame = run(make_frame(closes))
        frame = pd.concat([frame, run(bounce_frame())], ignore_index=True)
        for name in ("enter_long", "exit_long"):
            if name in frame:
                self.assertTrue(set(frame[name].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_produces_no_signal(self) -> None:
        frame = bounce_frame()
        frame["volume"] = 0.0
        frame = run(frame)
        self.assertEqual(column(frame, "enter_long").sum(), 0)
        self.assertEqual(column(frame, "exit_long").sum(), 0)
        frame = bounce_frame()
        frame.loc[SIGNAL_INDEX, "volume"] = 0.0
        self.assertEqual(column(run(frame), "enter_long").sum(), 0)

    def test_undefined_startup_values_produce_no_signal(self) -> None:
        # The same bounce on the first UTC day, where the grid reference is undefined.
        closes = [102.5] * 50 + DECLINE + [101.3] * 30
        lows = [c * 0.999 for c in closes]
        lows[57] = 100.9
        frame = run(make_frame(closes, lows))
        self.assertTrue(frame["grid_step"].isna().all())
        self.assertEqual(column(frame, "enter_long").sum(), 0)
        frame = run(bounce_frame())
        self.assertEqual(column(frame, "enter_long").iloc[: Strategy.startup_candle_count].sum(), 0)

    def test_signal_unchanged_when_future_candles_appended(self) -> None:
        n, k = 215, 120
        full = bounce_frame(extra=k)
        full.loc[n:, "close"] = 50.0
        full.loc[n:, "open"] = 50.0
        full.loc[n:, "low"] = 40.0
        full.loc[n:, "high"] = 60.0
        before = run(full.iloc[:n].copy())
        after = run(full.copy())
        for name in ("enter_long", "exit_long", "grid_step", "touch_level", "prior_high", "prior_min_close"):
            pd.testing.assert_series_equal(
                column(before, name).reset_index(drop=True),
                column(after, name).iloc[:n].reset_index(drop=True),
                check_dtype=False,
                check_names=False,
            )
        self.assertEqual(column(before, "enter_long").sum(), 1)

    def test_one_trade_per_level_per_day(self) -> None:
        strategy = Strategy()
        tag = MODULE.make_tag("2024-01-03", 101.0)
        fill_time = START + BAR * (SIGNAL_INDEX + 1)
        original = MODULE.Trade
        try:
            MODULE.Trade = _TradeStub
            _TradeStub.trades = [_Trade(START, enter_tag=tag)]
            self.assertFalse(strategy.confirm_trade_entry("BTC/USDT", "market", 1, 1, "GTC", fill_time, tag, "long"))
            _TradeStub.trades = [
                _Trade(START, enter_tag=MODULE.make_tag("2024-01-02", 101.0)),
                _Trade(START, enter_tag=MODULE.make_tag("2024-01-03", 102.0)),
            ]
            self.assertTrue(strategy.confirm_trade_entry("BTC/USDT", "market", 1, 1, "GTC", fill_time, tag, "long"))
            self.assertFalse(strategy.confirm_trade_entry("BTC/USDT", "market", 1, 1, "GTC", fill_time, "x", "long"))
        finally:
            _TradeStub.trades = []
            MODULE.Trade = original

    def test_take_profit_level_break_and_time_exit(self) -> None:
        strategy = Strategy()
        trade = _Trade(START, open_rate=101.5, enter_tag=MODULE.make_tag("2024-01-01", 101.0))
        roi = strategy.custom_roi("BTC/USDT", trade, START, 0, trade.enter_tag, "long")
        exit_price = 101.5 * (1 + roi + 0.001) / (1 - 0.001)
        self.assertAlmostEqual(exit_price, 101.5 * 1.01)

        class _DP:
            def __init__(self, frame):
                self.frame = frame

            def get_analyzed_dataframe(self, pair, timeframe):
                return self.frame, None

        frame = make_frame([101.5] * 60)
        frame["date"] = pd.date_range(START - BAR * 5, periods=60, freq="15min", tz="UTC")
        strategy.dp = _DP(frame)
        self.assertEqual(strategy.custom_exit("p", trade, START + BAR * 2, 102.6, 0.0), "take_profit_1pct")
        self.assertIsNone(strategy.custom_exit("p", trade, START + BAR * 23, 101.5, 0.0))
        self.assertEqual(strategy.custom_exit("p", trade, START + BAR * 24, 101.5, 0.0), "time_exit_24_bars")
        # Bar 3 after the fill closes under 0.993 * 101 = 100.293 -> exit at the open of bar 4.
        frame.loc[frame["date"] == START + BAR * 3, "close"] = 100.2
        self.assertIsNone(strategy.custom_exit("p", trade, START + BAR * 3, 101.0, 0.0))
        self.assertEqual(strategy.custom_exit("p", trade, START + BAR * 4, 101.0, 0.0), "level_break_exit")
        # A close at 100.3 is not under 100.293.
        frame.loc[frame["date"] == START + BAR * 3, "close"] = 100.3
        self.assertIsNone(strategy.custom_exit("p", trade, START + BAR * 4, 101.0, 0.0))


if __name__ == "__main__":
    unittest.main()
