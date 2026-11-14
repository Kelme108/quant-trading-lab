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
NAME = "MomentumThrustIgnition_H141_v1"
START = pd.Timestamp("2024-01-01 00:00", tz="UTC")


def fake_rsi(dataframe, timeperiod=14):
    """Use the scripted test_rsi column when present, else a causal Wilder-style RSI."""
    if "test_rsi" in dataframe:
        return dataframe["test_rsi"].astype(float)
    delta = dataframe["close"].diff()
    up = delta.clip(lower=0).ewm(alpha=1.0 / timeperiod, adjust=False).mean()
    down = (-delta.clip(upper=0)).ewm(alpha=1.0 / timeperiod, adjust=False).mean()
    return 100.0 - 100.0 / (1.0 + up / down)


def load():
    path = ROOT / "user_data" / "strategies" / "_archive" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ta = types.SimpleNamespace(RSI=fake_rsi)
    return module


Strategy = getattr(load(), NAME)


def synthetic(n: int, thrust_every: int = 60, first: int = 40) -> pd.DataFrame:
    """Flat quiet bars (range 1, volume 10, RSI 45) with a thrust bar every `thrust_every`."""
    idx = np.arange(n)
    frame = pd.DataFrame(
        {
            "date": [START + timedelta(hours=int(i)) for i in idx],
            "open": 100.0,
            "high": 100.5,
            "low": 99.5,
            "close": 100.0,
            "volume": 10.0,
            "test_rsi": 45.0,
        }
    )
    for i in range(first, n, thrust_every):
        frame.loc[i, ["high", "low", "close", "volume", "test_rsi"]] = [103.0, 100.0, 102.9, 30.0, 75.0]
    return frame


def run(frame):
    strategy = Strategy()
    out = strategy.populate_indicators(frame.copy(), {})
    out = strategy.populate_entry_trend(out, {})
    out = strategy.populate_exit_trend(out, {})
    return out


def entries(frame):
    out = run(frame)
    return out.get("enter_long", pd.Series(0, index=out.index)).fillna(0)


class FakeDP:
    def __init__(self, frame):
        self.frame = frame

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.frame, None


class FakeTrade:
    def __init__(self, open_date_utc, open_rate=100.0, enter_tag="mti:97.0:101.0"):
        self.open_date_utc = open_date_utc
        self.open_rate = open_rate
        self.enter_tag = enter_tag


class MomentumThrustIgnitionTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.10)
        self.assertTrue(Strategy.use_custom_stoploss)
        self.assertGreaterEqual(Strategy.startup_candle_count, 400)

    def test_indicators_exclude_current_bar(self):
        frame = synthetic(120)
        frame.loc[25, ["high", "low"]] = [105.0, 99.0]
        frame.loc[26, "volume"] = 50.0
        out = Strategy().populate_indicators(frame.copy(), {})
        self.assertTrue(pd.isna(out.loc[19, "mean_range"]))
        self.assertTrue(pd.isna(out.loc[19, "mean_volume"]))
        rng = frame["high"] - frame["low"]
        self.assertAlmostEqual(out.loc[20, "mean_range"], rng.loc[0:19].mean())
        self.assertAlmostEqual(out.loc[26, "mean_range"], rng.loc[6:25].mean())
        self.assertAlmostEqual(out.loc[26, "mean_volume"], frame.loc[6:25, "volume"].mean())
        self.assertAlmostEqual(out.loc[27, "mean_volume"], frame.loc[7:26, "volume"].mean())
        # rest minimum looks at t-3..t-1 only
        self.assertTrue(pd.isna(out.loc[2, "rsi_rest_min"]))
        self.assertEqual(out.loc[40, "rsi_rest_min"], 45.0)

    def test_entries_only_on_thrust_bars_and_binary(self):
        out = run(synthetic(300))
        expected = [40, 100, 160, 220, 280]
        self.assertEqual(out.index[out["enter_long"] == 1].tolist(), expected)
        self.assertTrue(set(out["enter_long"].dropna().unique()).issubset({1}))
        self.assertEqual(out.loc[40, "enter_tag"], "mti:100.0:103.0")
        self.assertNotIn("exit_long", out.columns)

    def test_each_condition_blocks_the_entry(self):
        self.assertEqual(entries(synthetic(60)).iloc[40], 1)

        def blocked(**changes):
            frame = synthetic(60)
            for column, value in changes.items():
                frame.loc[40, column] = value
            return entries(frame).iloc[40] != 1

        self.assertTrue(blocked(test_rsi=69.9))
        self.assertTrue(blocked(volume=19.9))
        self.assertTrue(blocked(high=101.9, close=101.8))  # range 1.9 < 2.0 x 1.0
        self.assertTrue(blocked(close=102.2))  # close location 0.733 < 0.75
        self.assertTrue(blocked(high=100.0))  # high == low
        # the RSI must have been at or below 50 within the previous three bars
        frame = synthetic(60)
        frame.loc[37:39, "test_rsi"] = 50.1
        self.assertNotEqual(entries(frame).iloc[40], 1)
        frame.loc[37, "test_rsi"] = 50.0  # boundary: <= 50 passes
        self.assertEqual(entries(frame).iloc[40], 1)
        # rest condition uses bars t-3..t-1 only, not t-4
        frame = synthetic(60)
        frame.loc[37:39, "test_rsi"] = 60.0
        frame.loc[36, "test_rsi"] = 40.0
        self.assertNotEqual(entries(frame).iloc[40], 1)

    def test_boundaries_are_inclusive(self):
        frame = synthetic(60)
        frame.loc[40, ["high", "low", "close", "volume", "test_rsi"]] = [102.0, 100.0, 101.5, 20.0, 70.0]
        self.assertEqual(entries(frame).iloc[40], 1)  # range 2.0x, loc 0.75, vol 2.0x, rsi 70

    def test_zero_volume_gives_no_signal(self):
        frame = synthetic(300)
        frame["volume"] = 0.0
        out = run(frame)
        self.assertEqual(int(out.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(out.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        frame = synthetic(60)
        frame.loc[40, "volume"] = 0.0
        self.assertNotEqual(entries(frame).iloc[40], 1)

    def test_undefined_startup_values_give_no_signal(self):
        frame = synthetic(120, first=10, thrust_every=500)
        out = run(frame)
        self.assertTrue(out.iloc[:20]["mean_range"].isna().all())
        self.assertEqual(int(out.get("enter_long", pd.Series(0.0, index=out.index)).iloc[:20].fillna(0).sum()), 0)
        # undefined RSI on the bar or in its rest window blocks the entry
        frame = synthetic(60)
        frame.loc[39, "test_rsi"] = np.nan
        frame.loc[38, "test_rsi"] = 60.0
        frame.loc[37, "test_rsi"] = 60.0
        self.assertNotEqual(entries(frame).iloc[40], 1)
        frame = synthetic(60)
        frame.loc[40, "test_rsi"] = np.nan
        self.assertNotEqual(entries(frame).iloc[40], 1)

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        n, k = 250, 90
        long_frame = synthetic(n + k)
        short = run(long_frame.iloc[:n].copy().reset_index(drop=True))
        full = run(long_frame.copy())
        pd.testing.assert_series_equal(
            short["enter_long"].reset_index(drop=True),
            full["enter_long"].iloc[:n].reset_index(drop=True),
            check_dtype=False,
            check_names=False,
        )
        cols = ["rsi14", "rsi_rest_min", "mean_range", "mean_volume", "close_loc"]
        pd.testing.assert_frame_equal(short[cols], full[cols].iloc[:n], check_dtype=False)

        # same with the computed (non scripted) RSI on a noisy series
        rng = np.random.default_rng(7)
        close = 100.0 + np.cumsum(rng.normal(0, 0.5, n + k))
        noisy = synthetic(n + k).drop(columns=["test_rsi"])
        noisy["close"] = close
        noisy["open"] = np.concatenate([[close[0]], close[:-1]])
        noisy["high"] = np.maximum(noisy["open"], noisy["close"]) + 0.3
        noisy["low"] = np.minimum(noisy["open"], noisy["close"]) - 0.3
        short = run(noisy.iloc[:n].copy().reset_index(drop=True))
        full = run(noisy.copy())
        pd.testing.assert_frame_equal(short[cols], full[cols].iloc[:n], check_dtype=False)
        short_entries = short.get("enter_long", pd.Series(0.0, index=short.index)).fillna(0)
        full_entries = full.get("enter_long", pd.Series(0.0, index=full.index)).fillna(0)
        pd.testing.assert_series_equal(
            short_entries.reset_index(drop=True),
            full_entries.iloc[:n].reset_index(drop=True),
            check_dtype=False,
            check_names=False,
        )

    # ---- custom_stoploss ---------------------------------------------
    def stop_ratio(self, entry, tag, rate):
        trade = FakeTrade(START, open_rate=entry, enter_tag=tag)
        return Strategy().custom_stoploss("BTC/USDT", trade, START, rate, 0.0)

    def test_stop_is_signal_low_when_far_enough(self):
        self.assertAlmostEqual(self.stop_ratio(100.0, "mti:98.0:102.0", 100.0), -0.02)
        # stop is a fixed price: from a higher current rate the ratio is relative to it
        self.assertAlmostEqual(self.stop_ratio(100.0, "mti:98.0:102.0", 105.0), 98.0 / 105.0 - 1.0)

    def test_stop_has_one_percent_minimum(self):
        self.assertAlmostEqual(self.stop_ratio(100.0, "mti:99.5:102.0", 100.0), -0.01)
        self.assertAlmostEqual(self.stop_ratio(100.0, "mti:101.0:103.0", 100.0), -0.01)

    def test_stop_is_capped_at_the_backstop(self):
        self.assertAlmostEqual(self.stop_ratio(100.0, "mti:80.0:102.0", 100.0), -0.10)

    def test_stop_out_when_price_is_through_the_stop(self):
        self.assertLess(self.stop_ratio(100.0, "mti:98.0:102.0", 97.0), 0)
        self.assertGreater(self.stop_ratio(100.0, "mti:98.0:102.0", 97.0), -1e-3)

    def test_stop_falls_back_without_a_valid_tag(self):
        self.assertIsNone(self.stop_ratio(100.0, None, 100.0))
        self.assertIsNone(self.stop_ratio(100.0, "other", 100.0))
        self.assertIsNone(self.stop_ratio(100.0, "mti:abc:1", 100.0))

    # ---- custom_exit -------------------------------------------------
    def manual_frame(self, n=40):
        return pd.DataFrame(
            {
                "date": [START + timedelta(hours=i) for i in range(n)],
                "close": [100.0] * n,
                "volume": [1.0] * n,
            }
        )

    def exit_at(self, frame, entry_idx, now_idx, tag="mti:97.0:101.0", with_dp=True):
        strategy = Strategy()
        strategy.dp = FakeDP(frame) if with_dp else None
        trade = FakeTrade(frame.loc[entry_idx, "date"], 100.0, tag)
        return strategy.custom_exit("BTC/USDT", trade, frame.loc[now_idx, "date"], 100.0, 0.0)

    # tag low 97 high 101: midpoint 99, stop_pct 3%, stop 97, target 106
    def test_no_exit_when_nothing_triggers(self):
        frame = self.manual_frame()
        self.assertIsNone(self.exit_at(frame, 5, 5))  # entry bar not yet closed
        self.assertIsNone(self.exit_at(frame, 5, 6))
        self.assertIsNone(self.exit_at(frame, 5, 12))

    def test_target_at_two_r_on_a_closed_bar(self):
        frame = self.manual_frame()
        frame.loc[6, "close"] = 106.0
        self.assertEqual(self.exit_at(frame, 5, 7), "target_2r")
        frame.loc[6, "close"] = 105.9
        self.assertIsNone(self.exit_at(frame, 5, 7))

    def test_target_uses_one_percent_minimum_stop(self):
        frame = self.manual_frame()
        frame.loc[6, "close"] = 102.0  # tag low 99.9 -> stop_pct 1% -> target 102
        self.assertEqual(self.exit_at(frame, 5, 7, tag="mti:99.9:103.0"), "target_2r")
        frame.loc[6, "close"] = 101.9
        self.assertIsNone(self.exit_at(frame, 5, 7, tag="mti:99.9:103.0"))

    def test_fail_fast_when_a_bar_closes_below_the_midpoint(self):
        frame = self.manual_frame()
        frame.loc[5, "close"] = 98.9  # the entry bar itself counts
        self.assertEqual(self.exit_at(frame, 5, 6), "fail_fast_midpoint")
        frame.loc[5, "close"] = 99.0  # not below
        self.assertIsNone(self.exit_at(frame, 5, 6))

    def test_only_closed_bars_from_the_entry_bar_count(self):
        frame = self.manual_frame()
        frame.loc[4, "close"] = 90.0  # the ignition bar, before the entry bar
        frame.loc[6, "close"] = 90.0  # not yet closed at the open of bar 6
        self.assertIsNone(self.exit_at(frame, 5, 6))
        self.assertEqual(self.exit_at(frame, 5, 7), "fail_fast_midpoint")

    def test_zero_volume_bar_blocks_close_based_exits(self):
        frame = self.manual_frame()
        frame.loc[6, "close"] = 90.0
        frame.loc[6, "volume"] = 0.0
        self.assertIsNone(self.exit_at(frame, 5, 7))

    def test_time_exit_twelve_bars_after_entry(self):
        frame = self.manual_frame()
        # entry bar 5 is bar 1; bar 12 is index 16; sell at the open of index 17
        self.assertIsNone(self.exit_at(frame, 5, 16))
        self.assertEqual(self.exit_at(frame, 5, 17), "time_exit_12h")
        self.assertEqual(self.exit_at(frame, 5, 17, with_dp=False), "time_exit_12h")
        self.assertIsNone(self.exit_at(frame, 5, 16, with_dp=False))

    def test_target_and_fail_fast_beat_time_exit_on_the_same_bar(self):
        frame = self.manual_frame()
        frame.loc[16, "close"] = 110.0
        self.assertEqual(self.exit_at(frame, 5, 17), "target_2r")


if __name__ == "__main__":
    unittest.main()
