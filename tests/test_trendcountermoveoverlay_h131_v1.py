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
strategy_module.merge_informative_pair = lambda *a, **k: a[0]
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
NAME = "TrendCounterMoveOverlay_H131_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load()
Strategy = getattr(MODULE, NAME)

BASE_BARS = 2600


def make_frame(n=3400):
    """Quiet slow uptrend, then an active uptrend with 3-bar 0.4%-per-bar dips every 8 bars."""
    close = np.empty(n)
    price = 100.0
    for i in range(n):
        if i < BASE_BARS:
            price *= 1.00003 * (1 + 0.0002 * (1 if i % 2 else -1))
        else:
            price *= 1.005 if (i - BASE_BARS) % 8 < 5 else 0.996
        close[i] = price
    open_ = np.concatenate([[close[0]], close[:-1]])
    spread = np.where(np.arange(n) < BASE_BARS, 0.0003, 0.002)
    high = np.maximum(open_, close) * (1 + spread)
    low = np.minimum(open_, close) * (1 - spread)
    date = pd.date_range(datetime(2024, 1, 1, tzinfo=timezone.utc), periods=n, freq="15min")
    return pd.DataFrame(
        {"date": date, "open": open_, "high": high, "low": low, "close": close, "volume": np.full(n, 10.0)}
    )


def run(strategy, frame):
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


def signal(frame, column):
    if column not in frame:
        return pd.Series(0, index=frame.index)
    return frame[column].fillna(0)


class Trade:
    def __init__(self, open_date):
        self.open_date_utc = open_date


class ContractTests(unittest.TestCase):
    def test_class_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.012)
        self.assertGreaterEqual(Strategy.startup_candle_count, 2400)
        self.assertEqual(
            Strategy().protections, [{"method": "CooldownPeriod", "stop_duration_candles": 4}]
        )

    def test_signals_binary_and_present(self):
        frame = run(Strategy(), make_frame())
        for column in ("enter_long", "exit_long"):
            if column in frame:
                self.assertTrue(set(frame[column].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(int(signal(frame, "enter_long").sum()), 0)

    def test_entry_requires_trend_activity_streak_and_move(self):
        frame = run(Strategy(), make_frame())
        entries = frame[signal(frame, "enter_long") == 1]
        self.assertTrue((entries["h_trend"] == 1.0).all())
        self.assertTrue((entries["h_activity"] == 1.0).all())
        self.assertTrue((entries["close"] <= 0.994 * entries["close_lag3"]).all())
        idx = entries.index[0]
        c = frame["close"]
        self.assertTrue(c[idx] < c[idx - 1] < c[idx - 2] < c[idx - 3])

    def test_no_entry_if_counter_move_too_small_or_not_a_streak(self):
        strategy = Strategy()
        frame = strategy.populate_indicators(make_frame(), {})
        frame["h_trend"] = 1.0
        frame["h_activity"] = 1.0
        base = strategy.populate_entry_trend(frame.copy(), {})
        self.assertGreater(int(signal(base, "enter_long").sum()), 0)
        small = frame.copy()
        small["counter_move"] = False
        self.assertEqual(int(signal(strategy.populate_entry_trend(small, {}), "enter_long").sum()), 0)
        nostreak = frame.copy()
        nostreak["streak_down"] = False
        self.assertEqual(int(signal(strategy.populate_entry_trend(nostreak, {}), "enter_long").sum()), 0)
        for column in ("h_trend", "h_activity"):
            off = frame.copy()
            off[column] = 0.0
            self.assertEqual(int(signal(strategy.populate_entry_trend(off, {}), "enter_long").sum()), 0)

    def test_trend_exit_signal_when_trend_false(self):
        strategy = Strategy()
        frame = strategy.populate_indicators(make_frame(), {})
        frame["h_trend"] = 0.0
        out = strategy.populate_exit_trend(frame.copy(), {})
        self.assertEqual(int(signal(out, "exit_long").sum()), len(frame))
        frame["h_trend"] = 1.0
        out = strategy.populate_exit_trend(frame.copy(), {})
        self.assertEqual(int(signal(out, "exit_long").sum()), 0)
        frame["h_trend"] = np.nan
        out = strategy.populate_exit_trend(frame.copy(), {})
        self.assertEqual(int(signal(out, "exit_long").sum()), 0)

    def test_zero_volume_no_signal(self):
        frame = make_frame()
        frame["volume"] = 0.0
        out = run(Strategy(), frame)
        self.assertEqual(int(signal(out, "enter_long").sum()), 0)
        self.assertEqual(int(signal(out, "exit_long").sum()), 0)

    def test_zero_volume_candle_blocks_that_candle_only(self):
        frame = make_frame()
        ref = run(Strategy(), frame)
        idx = ref.index[signal(ref, "enter_long") == 1][0]
        frame.loc[idx, "volume"] = 0.0
        out = run(Strategy(), frame)
        self.assertEqual(signal(out, "enter_long")[idx], 0)

    def test_undefined_startup_values_no_signal(self):
        strategy = Strategy()
        out = run(strategy, make_frame())
        needed = 600 * 4  # 480 median + 1 shift + 14 ATR + margin, in 15m bars, is below this
        self.assertEqual(int(signal(out, "enter_long").iloc[: 520 * 4].sum()), 0)
        self.assertEqual(int(signal(out, "exit_long").iloc[: 48 * 4].sum()), 0)
        self.assertTrue(out["h_activity"].iloc[: 495 * 4].isna().all())
        short = run(strategy, make_frame().iloc[:1000])
        self.assertEqual(int(signal(short, "enter_long").sum()), 0)
        self.assertEqual(int(signal(short, "exit_long").sum()), 0)
        self.assertGreater(needed, 0)

    def test_future_candles_do_not_change_signals(self):
        strategy = Strategy()
        full = make_frame()
        ref = run(strategy, full)
        first = int(signal(ref, "enter_long").pipe(lambda s: s[s == 1].index[2]))
        n = first + 1
        short = run(strategy, full.iloc[:n])
        long_ = run(strategy, full.iloc[: n + 300])
        cols = ["h_trend", "h_activity", "streak_down", "counter_move"]
        pd.testing.assert_frame_equal(short[cols], long_[cols].iloc[:n], check_dtype=False)
        pd.testing.assert_series_equal(
            signal(short, "enter_long"), signal(long_, "enter_long").iloc[:n], check_dtype=False
        )
        pd.testing.assert_series_equal(
            signal(short, "exit_long"), signal(long_, "exit_long").iloc[:n], check_dtype=False
        )

    def test_hourly_values_use_last_completed_hour(self):
        strategy = Strategy()
        frame = make_frame()
        changed = frame.copy()
        # change the whole hour starting at bar index h4 (4 bars); bars of that hour must not see it
        h4 = 3000 - 3000 % 4
        changed.loc[h4 : h4 + 3, ["open", "high", "low", "close"]] *= 3.0
        a = strategy.populate_indicators(frame.copy(), {})
        b = strategy.populate_indicators(changed, {})
        cols = ["h_trend", "h_activity"]
        pd.testing.assert_frame_equal(a.loc[: h4 + 3, cols], b.loc[: h4 + 3, cols])

    def test_wilder_atr_constant_range(self):
        n = 60
        high = np.full(n, 101.0)
        low = np.full(n, 99.0)
        close = np.full(n, 100.0)
        atr = MODULE._wilder_atr(high, low, close, 14)
        self.assertTrue(np.isnan(atr[:14]).all())
        self.assertAlmostEqual(atr[14], 2.0)
        self.assertAlmostEqual(atr[-1], 2.0)

    def test_take_profit_exit(self):
        strategy = Strategy()
        now = datetime(2024, 3, 1, 12, 0, tzinfo=timezone.utc)
        trade = Trade(now - timedelta(minutes=30))
        self.assertIsNone(strategy.custom_exit("X/USDT", trade, now, 100.0, 0.0149))
        self.assertEqual(strategy.custom_exit("X/USDT", trade, now, 101.5, 0.015), "take_profit_1_5pct")

    def test_time_exit(self):
        strategy = Strategy()
        now = datetime(2024, 3, 1, 12, 0, tzinfo=timezone.utc)
        early = Trade(now - timedelta(minutes=705))
        self.assertIsNone(strategy.custom_exit("X/USDT", early, now, 100.0, -0.005))
        late = Trade(now - timedelta(minutes=720))
        self.assertEqual(strategy.custom_exit("X/USDT", late, now, 100.0, -0.005), "time_exit_12h")


if __name__ == "__main__":
    unittest.main()
