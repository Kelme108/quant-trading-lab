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
CLASS_NAME = "ADXRegimeSwitch_H065_v1"


def load_module():
    path = ROOT / "user_data" / "strategies" / "_archive" / f"{CLASS_NAME}.py"
    spec = importlib.util.spec_from_file_location(CLASS_NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()
Strategy = getattr(MODULE, CLASS_NAME)


def synthetic_frame(n: int, seed: int = 11) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    # Alternate calm and volatile, drifting and flat stretches so both regimes occur.
    vol = np.where((np.arange(n) // 300) % 2 == 0, 0.004, 0.012)
    drift = np.where((np.arange(n) // 450) % 3 == 0, 0.0015, 0.0)
    close = 100.0 * np.exp(np.cumsum(rng.normal(drift, vol)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    spread = np.abs(rng.normal(0.0, vol)) * close
    high = np.maximum(open_, close) + spread
    low = np.minimum(open_, close) - spread
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": np.ones(n)})


def run(strategy, frame):
    frame = strategy.populate_indicators(frame, {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


SIGNAL_COLUMNS = ("enter_long", "exit_trend_cond", "exit_range_cond")


class FakeDp:
    def __init__(self, frame):
        self.frame = frame

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.frame, None


class FakeTrade:
    def __init__(self, tag, open_date):
        self.enter_tag = tag
        self.open_date_utc = open_date


class ADXRegimeSwitchTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.03)
        self.assertGreaterEqual(Strategy.startup_candle_count, 1000)
        self.assertEqual(Strategy().protections, [{"method": "CooldownPeriod", "stop_duration_candles": 4}])

    def test_signals_binary_and_both_tags_present(self) -> None:
        frame = run(Strategy(), synthetic_frame(4000))
        values = frame["enter_long"].dropna().unique().tolist()
        self.assertTrue(set(values).issubset({1}))
        self.assertGreater(frame["enter_long"].fillna(0).sum(), 0)
        tags = set(frame.loc[frame["enter_long"] == 1, "enter_tag"].unique().tolist())
        self.assertTrue(tags.issubset({"trend", "range"}))
        self.assertNotIn("exit_long", frame.columns)
        for column in ("exit_trend_cond", "exit_range_cond"):
            self.assertTrue(set(frame[column].unique().tolist()).issubset({0, 1}))

    def test_entry_rules_hold_where_signalled(self) -> None:
        frame = run(Strategy(), synthetic_frame(4000))
        trend = frame[frame["enter_tag"] == "trend"]
        self.assertTrue((trend["adx"] >= 25).all())
        self.assertTrue((trend["plus_di"] > trend["minus_di"]).all())
        self.assertTrue((trend["atrp"] >= trend["atrp_med"]).all())
        self.assertTrue((trend["ema_fast"] > 1.002 * trend["ema_slow"]).all())
        rng = frame[frame["enter_tag"] == "range"]
        self.assertTrue((rng["adx"] < 20).all())
        self.assertTrue((rng["rsi"] < 30).all())

    def test_median_excludes_current_bar(self) -> None:
        frame = run(Strategy(), synthetic_frame(2000))
        first = frame["atrp"].first_valid_index()
        self.assertTrue(pd.isna(frame.loc[first + 719, "atrp_med"]))
        t = first + 720
        self.assertAlmostEqual(frame.loc[t, "atrp_med"], frame.loc[t - 720 : t - 1, "atrp"].median())

    def test_zero_volume_no_signal(self) -> None:
        frame = synthetic_frame(3000)
        frame["volume"] = 0.0
        frame = run(Strategy(), frame)
        for column in SIGNAL_COLUMNS:
            self.assertEqual(int(frame.get(column, pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self) -> None:
        frame = run(Strategy(), synthetic_frame(3000))
        undefined = frame[["adx", "atrp_med", "ema_slow", "rsi"]].isna().any(axis=1)
        self.assertTrue(undefined.iloc[:700].all())
        trend_rows = frame["enter_tag"] == "trend"
        self.assertEqual(int((trend_rows & undefined).sum()), 0)
        rsi_or_adx_nan = frame["rsi"].isna() | frame["adx"].isna()
        self.assertEqual(int((frame["enter_long"].fillna(0) == 1)[rsi_or_adx_nan].sum()), 0)
        self.assertEqual(int(frame.loc[frame["ema_slow"].isna(), "exit_trend_cond"].sum()), 0)
        self.assertEqual(int(frame.loc[frame["rsi"].isna(), "exit_range_cond"].sum()), 0)

    def test_no_lookahead(self) -> None:
        full = synthetic_frame(3500)
        n = 2500
        strategy = Strategy()
        short = run(strategy, full.iloc[:n].copy())
        long = run(strategy, full.copy())
        for column in SIGNAL_COLUMNS:
            np.testing.assert_array_equal(
                short[column].fillna(0).to_numpy(), long[column].fillna(0).to_numpy()[:n]
            )
        pd.testing.assert_series_equal(short["enter_tag"], long["enter_tag"].iloc[:n])
        cols = ["adx", "plus_di", "minus_di", "atr", "atrp", "atrp_med", "ema_fast", "ema_slow", "rsi"]
        pd.testing.assert_frame_equal(short[cols], long.loc[: n - 1, cols])

    def test_custom_exit_by_tag_and_time(self) -> None:
        strategy = Strategy()
        frame = pd.DataFrame({"exit_trend_cond": [0, 1], "exit_range_cond": [0, 0]})
        strategy.dp = FakeDp(frame)
        opened = datetime(2025, 1, 1, tzinfo=timezone.utc)
        now = opened + timedelta(hours=5)
        self.assertEqual(strategy.custom_exit("X/USDT", FakeTrade("trend", opened), now, 1.0, 0.0), "trend_ema_exit")
        self.assertIsNone(strategy.custom_exit("X/USDT", FakeTrade("range", opened), now, 1.0, 0.0))
        frame.loc[1, "exit_range_cond"] = 1
        frame.loc[1, "exit_trend_cond"] = 0
        self.assertEqual(strategy.custom_exit("X/USDT", FakeTrade("range", opened), now, 1.0, 0.0), "range_rsi_exit")
        self.assertIsNone(strategy.custom_exit("X/USDT", FakeTrade("trend", opened), now, 1.0, 0.0))
        frame.loc[1, "exit_range_cond"] = 0
        before = opened + timedelta(hours=23)
        at_cap = opened + timedelta(hours=24)
        self.assertIsNone(strategy.custom_exit("X/USDT", FakeTrade("trend", opened), before, 1.0, 0.0))
        self.assertEqual(strategy.custom_exit("X/USDT", FakeTrade("range", opened), at_cap, 1.0, 0.0), "time_exit")


if __name__ == "__main__":
    unittest.main()
