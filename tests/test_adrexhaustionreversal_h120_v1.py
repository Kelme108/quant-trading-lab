import importlib.util
import sys
import types
import unittest
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

freqtrade = types.ModuleType("freqtrade")
strategy_module = types.ModuleType("freqtrade.strategy")
strategy_module.IStrategy = object
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


def _fake_atr(dataframe, timeperiod=14):
    """Wilder ATR stand-in (used only when the stubbed talib has none)."""
    prev_close = dataframe["close"].shift(1)
    true_range = pd.concat(
        [
            dataframe["high"] - dataframe["low"],
            (dataframe["high"] - prev_close).abs(),
            (dataframe["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1, skipna=False)
    atr = true_range.ewm(alpha=1.0 / timeperiod, adjust=False).mean()
    atr.iloc[:timeperiod] = np.nan
    return atr


if not hasattr(sys.modules["talib.abstract"], "ATR"):
    sys.modules["talib.abstract"].ATR = _fake_atr

ROOT = Path(__file__).parents[1]
NAME = "ADRExhaustionReversal_H120_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load()
Strategy = getattr(MODULE, NAME)

BARS = 96
SIGNAL_DAY = 16
SIGNAL_ROW = SIGNAL_DAY * BARS + 61  # 15:15 UTC


def make_frame(days: int = 18) -> pd.DataFrame:
    """Sine days (range about 2.6%), then on day 16 a rise to 101, a fall to 95.5 and a green bar at 15:15."""
    n = days * BARS
    closes = np.empty(n)
    for i in range(n):
        closes[i] = 100.0 + np.sin(2 * np.pi * (i % BARS) / BARS)
    base = SIGNAL_DAY * BARS
    for k in range(BARS):
        if k <= 20:
            value = 100.0 + k / 20.0
        elif k <= 60:
            value = 101.0 - 5.5 * (k - 20) / 40.0
        elif k == 61:
            value = 96.5
        else:
            value = 96.5 + 0.01 * ((k % 5) - 2)
        if base + k < n:
            closes[base + k] = value
    opens = np.concatenate([[100.0], closes[:-1]])
    highs = np.maximum(opens, closes) * 1.003
    lows = np.minimum(opens, closes) * 0.997
    dates = pd.date_range("2024-01-01", periods=n, freq="15min", tz="UTC")
    return pd.DataFrame(
        {"date": dates, "open": opens, "high": highs, "low": lows, "close": closes, "volume": 10.0}
    )


def run(strategy, frame):
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    return frame


def entries(frame) -> pd.Series:
    if "enter_long" not in frame:
        return pd.Series(False, index=frame.index)
    return frame["enter_long"].fillna(0) == 1


def make_trade(tag, open_rate=96.5, minutes_ago=0):
    opened = pd.Timestamp("2024-01-17 15:30", tz="UTC")
    return SimpleNamespace(enter_tag=tag, open_rate=open_rate, open_date_utc=opened), opened


class ADRExhaustionReversalTests(unittest.TestCase):
    def setUp(self):
        self.strategy = Strategy()

    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.15)
        self.assertTrue(Strategy.use_custom_stoploss)
        self.assertGreaterEqual(Strategy.startup_candle_count, 1440)

    def test_numbers_are_the_proposals(self):
        self.assertEqual(MODULE.ADR_DAYS, 14)
        self.assertEqual(MODULE.BARS_PER_DAY, 96)
        self.assertEqual(MODULE.LOW_RECENCY_BARS, 4)
        self.assertEqual(MODULE.ATR_PERIOD, 14)
        self.assertEqual(MODULE.ATR_OVER_CLOSE_MIN, 0.004)
        self.assertEqual(MODULE.WINDOW_START_MINUTE, 240)
        self.assertEqual(MODULE.WINDOW_END_MINUTE, 21 * 60 + 45)
        self.assertEqual(MODULE.MIN_TARGET_DISTANCE, 0.01)
        self.assertEqual(MODULE.STOP_BELOW_DAY_LOW, 0.997)
        self.assertEqual(MODULE.MIN_STOP_DISTANCE, 0.01)
        self.assertEqual(MODULE.TIME_EXIT_BARS, 48)

    def test_signal_fires_on_the_reversal_bar(self):
        frame = run(self.strategy, make_frame())
        fired = entries(frame)
        self.assertTrue(fired.iloc[SIGNAL_ROW])
        day = frame.iloc[SIGNAL_DAY * BARS: SIGNAL_ROW + 1]
        dh, dl = day["high"].max(), day["low"].min()
        parsed = MODULE.parse_tag(frame.loc[SIGNAL_ROW, "enter_tag"])
        self.assertIsNotNone(parsed)
        self.assertAlmostEqual(parsed[0], dh)
        self.assertAlmostEqual(parsed[1], dl)
        self.assertAlmostEqual(parsed[2], (dh + dl) / 2.0)
        self.assertGreaterEqual(parsed[2], 1.01 * frame.loc[SIGNAL_ROW, "close"])
        # No entries before the signal day (earlier days have identical ranges and no deep fall).
        self.assertEqual(int(fired.iloc[: SIGNAL_DAY * BARS].sum()), 0)

    def test_adr_uses_only_the_14_completed_days_before_the_day(self):
        frame = run(self.strategy, make_frame())
        day = pd.to_datetime(frame["date"], utc=True).dt.floor("D")
        ranges = frame.groupby(day).apply(lambda g: g["high"].max() - g["low"].min())
        expected = ranges.iloc[SIGNAL_DAY - 14: SIGNAL_DAY].mean()
        self.assertAlmostEqual(frame.loc[SIGNAL_ROW, "adr"], expected)
        self.assertTrue(frame["adr"].iloc[: 14 * BARS].isna().all())
        self.assertTrue(frame["adr"].iloc[14 * BARS:].notna().all())

    def test_signal_columns_are_binary(self):
        frame = run(self.strategy, make_frame())
        for column in ("enter_long", "exit_long"):
            if column in frame:
                values = frame[column].dropna().unique().tolist()
                self.assertTrue(set(values).issubset({1}))

    def test_zero_volume_candle_has_no_signal(self):
        frame = make_frame()
        frame.loc[SIGNAL_ROW, "volume"] = 0.0
        self.assertFalse(entries(run(self.strategy, frame)).iloc[SIGNAL_ROW])
        frame["volume"] = 0.0
        out = run(self.strategy, frame)
        self.assertEqual(int(entries(out).sum()), 0)
        if "exit_long" in out:
            self.assertEqual(int(out["exit_long"].fillna(0).sum()), 0)

    def test_undefined_startup_values_have_no_signal(self):
        # Only 14 days of data in total: ADR is undefined on every row, so nothing may fire.
        frame = make_frame()
        frame = frame.iloc[: 14 * BARS].reset_index(drop=True)
        out = run(self.strategy, frame)
        self.assertTrue(out["adr"].isna().all())
        self.assertEqual(int(entries(out).sum()), 0)
        # Day 16 is the same shape but 15 days of history are missing the first day's start.
        short = make_frame().iloc[BARS * 3 + 5:].reset_index(drop=True)
        out = run(self.strategy, short)
        rows_without_adr = out["adr"].isna()
        self.assertFalse(bool((entries(out) & rows_without_adr).any()))

    def test_atr_filter_blocks_quiet_markets(self):
        frame = make_frame()
        # Same closes but wicks removed on the signal day makes ATR/close fall below 0.4%.
        quiet = frame.copy()
        quiet["high"] = np.maximum(quiet["open"], quiet["close"]) * 1.0002
        quiet["low"] = np.minimum(quiet["open"], quiet["close"]) * 0.9998
        out = run(self.strategy, quiet)
        self.assertFalse(entries(out).iloc[SIGNAL_ROW])

    def test_time_window_blocks_bars_before_0400(self):
        frame = make_frame()
        out = run(self.strategy, frame)
        minute = out["minute_of_day"]
        self.assertFalse(bool((entries(out) & ((minute < 240) | (minute > 21 * 60 + 45))).any()))

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        full = make_frame(18)
        n = SIGNAL_ROW + 10
        short = run(self.strategy, full.iloc[:n].copy())
        long = run(self.strategy, full.copy())
        columns = ["adr", "day_high", "day_low", "day_open", "low_5bar_min", "atr_over_close"]
        pd.testing.assert_frame_equal(
            short.loc[: n - 1, columns].reset_index(drop=True),
            long.loc[: n - 1, columns].reset_index(drop=True),
            check_dtype=False,
        )
        self.assertTrue((entries(short).iloc[:n].to_numpy() == entries(long).iloc[:n].to_numpy()).all())
        tags_short = short["enter_tag"].iloc[:n].fillna("") if "enter_tag" in short else pd.Series([""] * n)
        tags_long = long["enter_tag"].iloc[:n].fillna("")
        self.assertTrue((tags_short.to_numpy() == tags_long.to_numpy()).all())
        # Changing every candle after n leaves the first n rows untouched too.
        changed = full.copy()
        for column in ("open", "high", "low", "close"):
            changed.loc[n:, column] = 1000.0
        again = run(self.strategy, changed)
        self.assertTrue((entries(again).iloc[:n].to_numpy() == entries(long).iloc[:n].to_numpy()).all())

    def test_stop_is_fixed_and_at_least_one_percent_below_the_fill(self):
        tag = "adr|101.3|95.2|98.25"
        trade, _ = make_trade(tag, open_rate=96.5)
        sp = min(0.997 * 95.2, 0.99 * 96.5)
        self.assertAlmostEqual(MODULE.stop_price(95.2, 96.5), sp)
        self.assertLessEqual(sp, 0.99 * 96.5)
        for rate in (96.5, 98.0, 97.0):
            value = self.strategy.custom_stoploss("BTC/USDT", trade, None, rate, 0.0)
            self.assertAlmostEqual(rate * (1.0 - value), sp)
        # Day low far below the fill: the stop is the day-low level, below the 1% distance.
        trade2, _ = make_trade("adr|101.3|90.0|95.65", open_rate=96.5)
        value = self.strategy.custom_stoploss("BTC/USDT", trade2, None, 96.5, 0.0)
        self.assertAlmostEqual(96.5 * (1.0 - value), 0.997 * 90.0)
        trade3, _ = make_trade("junk", open_rate=96.5)
        self.assertIsNone(self.strategy.custom_stoploss("BTC/USDT", trade3, None, 96.5, 0.0))

    def test_target_exit(self):
        trade, opened = make_trade("adr|101.3|95.2|98.25")
        now = opened + timedelta(minutes=15)
        self.assertIsNone(self.strategy.custom_exit("BTC/USDT", trade, now, 98.24, 0.02))
        self.assertEqual(
            self.strategy.custom_exit("BTC/USDT", trade, now, 98.25, 0.02), "target_mid_range"
        )

    def test_time_exit_after_48_bars(self):
        trade, opened = make_trade("adr|101.3|95.2|98.25")
        self.assertIsNone(
            self.strategy.custom_exit("BTC/USDT", trade, opened + timedelta(hours=11, minutes=45), 96.0, -0.01)
        )
        self.assertEqual(
            self.strategy.custom_exit("BTC/USDT", trade, opened + timedelta(hours=12), 96.0, -0.01),
            "time_exit_48_bars",
        )
        other, _ = make_trade("junk")
        self.assertIsNone(self.strategy.custom_exit("BTC/USDT", other, opened + timedelta(hours=13), 1e9, 1.0))

    def test_one_entry_per_pair_per_utc_day(self):
        tag = "adr|101.3|95.2|98.25"
        now = pd.Timestamp("2024-01-17 22:00", tz="UTC")
        original = MODULE.Trade
        try:
            MODULE.Trade = type(
                "Trade",
                (),
                {
                    "get_trades_proxy": staticmethod(
                        lambda **k: [SimpleNamespace(open_date_utc=pd.Timestamp("2024-01-17 09:00", tz="UTC"))]
                    )
                },
            )
            self.assertFalse(
                self.strategy.confirm_trade_entry("BTC/USDT", "limit", 1, 96.5, "GTC", now, tag, "long")
            )
            MODULE.Trade = type(
                "Trade",
                (),
                {
                    "get_trades_proxy": staticmethod(
                        lambda **k: [SimpleNamespace(open_date_utc=pd.Timestamp("2024-01-16 23:45", tz="UTC"))]
                    )
                },
            )
            self.assertTrue(
                self.strategy.confirm_trade_entry("BTC/USDT", "limit", 1, 96.5, "GTC", now, tag, "long")
            )
            self.assertFalse(
                self.strategy.confirm_trade_entry("BTC/USDT", "limit", 1, 96.5, "GTC", now, "junk", "long")
            )
        finally:
            MODULE.Trade = original


if __name__ == "__main__":
    unittest.main()
