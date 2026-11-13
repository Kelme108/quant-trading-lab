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
NAME = "ChurnAbsorptionBreakout_H130_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


Strategy = getattr(load(), NAME)

START = pd.Timestamp("2024-01-01 00:00", tz="UTC")
COLS = ["open", "high", "low", "close", "volume"]


def dates(n):
    return pd.date_range(START, periods=n, freq="15min")


def random_frame(n=900, seed=3):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.003, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.003, n))
    volume = rng.lognormal(3, 1.0, n)
    return pd.DataFrame(
        {"date": dates(n), "open": open_, "high": high, "low": low, "close": close, "volume": volume}
    )


def crafted(n=260):
    """Flat 100 (range 1.0, volume 10): MV = 10, MR = 1.0.
    Bar 118 closes at 104 so the churn bar 150 (close 100) has a 4.0 decline over 32 bars.
    Bar 150: churn (volume 25, high 100.4, low 99.9) -> zone ZH 100.4, ZL 99.9, z = 150.
    Bar 152: breakout (close 101, range 1.7 >= 1.5 MR) -> entry signal at 152."""
    frame = pd.DataFrame(
        {"date": dates(n), "open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0, "volume": 10.0}
    )
    frame.loc[118, COLS] = [100.0, 104.5, 103.5, 104.0, 10.0]
    frame.loc[150, COLS] = [100.0, 100.4, 99.9, 100.0, 25.0]
    frame.loc[152, COLS] = [100.0, 101.5, 99.8, 101.0, 10.0]
    return frame


def run(frame):
    strategy = Strategy()
    out = strategy.populate_indicators(frame.copy(), {})
    return strategy.populate_exit_trend(strategy.populate_entry_trend(out, {}), {})


def entries(out):
    if "enter_long" not in out:
        return []
    return out.index[out["enter_long"].fillna(0) == 1].tolist()


def entries_of(frame):
    return entries(run(frame))


class ChurnAbsorptionBreakoutTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.05)
        self.assertTrue(Strategy.use_custom_stoploss)
        self.assertGreaterEqual(Strategy.startup_candle_count, 200)

    def test_signal_columns_are_binary(self):
        for frame in (random_frame(), crafted()):
            out = run(frame)
            for column in ("enter_long", "exit_long"):
                if column in out:
                    self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_crafted_setup_gives_one_entry_with_tag(self):
        out = run(crafted())
        self.assertTrue(out.loc[150, "cab_churn"])
        self.assertTrue(out.loc[150, "cab_context"])
        self.assertAlmostEqual(out.loc[150, "cab_mr"], 1.0)
        self.assertAlmostEqual(out.loc[150, "cab_mv"], 10.0)
        self.assertEqual(entries(out), [152])
        self.assertEqual(out.loc[152, "enter_tag"], "cab:99.9")

    def test_zero_volume_gives_no_signal(self):
        self.assertEqual(entries_of(crafted().assign(volume=0.0)), [])
        frame = crafted()
        frame.loc[152, "volume"] = 0.0  # zero-volume breakout bar: no entry
        self.assertEqual(entries_of(frame), [])
        self.assertEqual(entries_of(random_frame().assign(volume=0.0)), [])
        out = run(crafted().assign(volume=0.0))
        self.assertNotIn("exit_long", out)

    def test_undefined_startup_values_give_no_signal(self):
        out = run(random_frame())
        self.assertTrue(out["cab_mv"].iloc[:96].isna().all())
        self.assertTrue(out["cab_mr"].iloc[:96].isna().all())
        self.assertEqual([i for i in entries(out) if i < 96], [])
        # a full setup squeezed into the first 96 bars has no baseline: no signal
        frame = crafted()
        frame.loc[118, COLS] = [100.0, 100.5, 99.5, 100.0, 10.0]
        frame.loc[50, COLS] = [100.0, 104.5, 103.5, 104.0, 10.0]
        frame.loc[82, COLS] = [100.0, 100.4, 99.9, 100.0, 25.0]
        frame.loc[84, COLS] = [100.0, 101.5, 99.8, 101.0, 10.0]
        frame.loc[150, COLS] = [100.0, 100.5, 99.5, 100.0, 10.0]
        frame.loc[152, COLS] = [100.0, 100.5, 99.5, 100.0, 10.0]
        self.assertEqual(entries_of(frame), [])
        # NaN baseline at the churn bar: no zone
        frame = crafted()
        frame.loc[100, "volume"] = np.nan
        self.assertEqual(entries_of(frame), [])
        # NaN stored zone low blocks the entry
        strategy = Strategy()
        out = strategy.populate_indicators(crafted(), {})
        out.loc[152, "cab_zl"] = np.nan
        self.assertEqual(entries(strategy.populate_entry_trend(out, {})), [])

    def test_churn_thresholds(self):
        frame = crafted()
        frame.loc[150, "volume"] = 19.9  # < 2.0 x 10
        self.assertEqual(entries_of(frame), [])
        frame = crafted()
        frame.loc[150, "volume"] = 20.0  # exactly 2x passes
        self.assertEqual(entries_of(frame), [152])
        frame = crafted()
        frame.loc[150, ["high", "low"]] = [100.6, 99.9]  # range 0.7 > 0.6
        self.assertEqual(entries_of(frame), [])

    def test_context_threshold(self):
        frame = crafted()
        frame.loc[118, "close"] = 100.0  # no decline
        self.assertEqual(entries_of(frame), [])
        frame = crafted()
        frame.loc[118, "close"] = 102.9  # decline 2.9 < 3.0 x MR
        self.assertEqual(entries_of(frame), [])
        frame = crafted()
        frame.loc[118, "close"] = 103.0  # decline 3.0 passes
        self.assertEqual(entries_of(frame), [152])

    def test_breakout_conditions(self):
        frame = crafted()
        frame.loc[152, ["high", "low"]] = [101.0, 99.9]  # range 1.1 < 1.5 x MR
        self.assertEqual(entries_of(frame), [])
        frame = crafted()
        frame.loc[152, "close"] = 100.4  # close not above ZH
        frame.loc[152, "high"] = 101.5
        self.assertEqual(entries_of(frame), [])

    def test_void_when_a_bar_closes_below_zone_low(self):
        frame = crafted()
        frame.loc[151, ["open", "high", "low", "close"]] = [100.0, 100.3, 99.3, 99.8]
        self.assertEqual(entries_of(frame), [])
        frame = crafted()
        frame.loc[151, ["open", "high", "low", "close"]] = [100.0, 100.3, 99.3, 99.9]  # at ZL: alive
        self.assertEqual(entries_of(frame), [152])

    def test_entry_window_is_16_bars_after_zone_end(self):
        for bar, expected in ((166, [166]), (167, [])):
            frame = crafted()
            frame.loc[152, COLS] = [100.0, 100.5, 99.5, 100.0, 10.0]
            frame.loc[bar, COLS] = [100.0, 101.5, 99.8, 101.0, 10.0]
            self.assertEqual(entries_of(frame), expected, bar)

    def test_zone_depth_filter(self):
        frame = crafted()
        frame.loc[152, ["high", "close"]] = [104.5, 104.0]  # ZL 99.9 < 0.97 x 104 -> discard
        self.assertEqual(entries_of(frame), [])
        # the discarded zone is used up: a later valid-looking breakout does not trade
        frame.loc[154, COLS] = [100.0, 101.5, 99.8, 101.0, 10.0]
        self.assertEqual(entries_of(frame), [])
        frame = crafted()
        frame.loc[152, ["high", "close"]] = [103.2, 102.9]  # 0.97 x 102.9 = 99.81 <= ZL: trade
        self.assertEqual(entries_of(frame), [152])

    def test_zone_is_used_once(self):
        frame = crafted()
        frame.loc[154, COLS] = [100.0, 101.5, 99.8, 101.0, 10.0]
        self.assertEqual(entries_of(frame), [152])

    def test_extension_widens_zone_and_moves_window(self):
        frame = crafted()
        # churn bar 153 (d=3, no context needed) raises ZH to 100.5
        frame.loc[152, COLS] = [100.0, 100.5, 99.5, 100.0, 10.0]
        frame.loc[153, COLS] = [100.0, 100.5, 100.0, 100.0, 40.0]
        frame.loc[155, COLS] = [100.0, 101.5, 99.8, 100.45, 10.0]  # above old ZH, not new ZH
        self.assertEqual(entries_of(frame), [])
        frame.loc[155, "close"] = 100.6
        self.assertEqual(entries_of(frame), [155])
        # the window now runs to 153 + 16 = 169
        for bar, expected in ((169, [169]), (170, [])):
            f = crafted()
            f.loc[152, COLS] = [100.0, 100.5, 99.5, 100.0, 10.0]
            f.loc[153, COLS] = [100.0, 100.5, 100.0, 100.0, 40.0]
            f.loc[bar, COLS] = [100.0, 101.5, 99.8, 101.0, 10.0]
            self.assertEqual(entries_of(f), expected, bar)
        # extension also lowers ZL (tag carries the lowest low)
        f = crafted()
        f.loc[152, COLS] = [100.0, 100.5, 99.5, 100.0, 10.0]
        f.loc[153, COLS] = [100.0, 100.2, 99.7, 100.0, 40.0]
        f.loc[154, COLS] = [100.0, 101.5, 99.8, 101.0, 10.0]
        self.assertEqual(run(f).loc[154, "enter_tag"], "cab:99.7")

    def test_churn_bar_five_bars_after_zone_end_does_not_extend(self):
        frame = crafted()
        frame.loc[152, COLS] = [100.0, 100.5, 99.5, 100.0, 10.0]
        frame.loc[155, COLS] = [100.0, 100.9, 100.4, 100.0, 40.0]  # d=5, no context: no extension
        frame.loc[156, COLS] = [100.0, 101.5, 99.8, 100.5, 10.0]
        self.assertEqual(entries_of(frame), [156])  # ZH stayed 100.4
        frame = crafted()
        frame.loc[152, COLS] = [100.0, 100.5, 99.5, 100.0, 10.0]
        frame.loc[154, COLS] = [100.0, 100.9, 100.4, 100.0, 40.0]  # d=4: extends ZH to 100.9
        frame.loc[156, COLS] = [100.0, 101.5, 99.8, 100.5, 10.0]
        self.assertEqual(entries_of(frame), [])

    def test_new_context_zone_replaces_older_zone(self):
        frame = crafted()
        frame.loc[152, COLS] = [100.0, 100.5, 99.5, 100.0, 10.0]
        frame.loc[128, "close"] = 104.0
        frame.loc[160, COLS] = [100.0, 100.2, 99.95, 100.0, 40.0]  # new zone ZH 100.2, ZL 99.95
        frame.loc[162, COLS] = [100.0, 101.5, 99.8, 100.3, 10.0]  # above the new ZH, below the old
        out = run(frame)
        self.assertEqual(entries(out), [162])
        self.assertEqual(out.loc[162, "enter_tag"], "cab:99.95")

    def test_stop_is_frozen_below_entry(self):
        strategy = Strategy()
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        # zone low very close to entry: distance floors at 1% (S = 0.99 E)
        trade = types.SimpleNamespace(open_rate=100.0, enter_tag="cab:99.8")
        self.assertAlmostEqual(strategy.custom_stoploss("BTC/USDT", trade, now, 100.0, 0.0), -0.01)
        ratio = strategy.custom_stoploss("BTC/USDT", trade, now, 101.0, 0.01)
        self.assertAlmostEqual(101.0 * (1 + ratio), 99.0)
        # deeper zone: S = ZL
        trade = types.SimpleNamespace(open_rate=100.0, enter_tag="cab:97.5")
        stop = 100.0 * (1 + strategy.custom_stoploss("BTC/USDT", trade, now, 100.0, 0.0))
        self.assertAlmostEqual(stop, 97.5)
        self.assertLess(strategy.custom_stoploss("BTC/USDT", trade, now, 90.0, -0.1), 0)
        trade = types.SimpleNamespace(open_rate=100.0, enter_tag=None)
        self.assertIsNone(strategy.custom_stoploss("BTC/USDT", trade, now, 100.0, 0.0))

    def test_target_exit_is_1_5_r(self):
        strategy = Strategy()
        opened = datetime(2025, 1, 1, tzinfo=timezone.utc)
        soon = opened + timedelta(hours=1)
        trade = types.SimpleNamespace(open_date_utc=opened, open_rate=100.0, enter_tag="cab:99.8")
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, soon, 101.4, 0.0149))
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, soon, 101.6, 0.0151), "target_1_5r")
        trade = types.SimpleNamespace(open_date_utc=opened, open_rate=100.0, enter_tag="cab:97.5")
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, soon, 103.0, 0.03))
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, soon, 103.8, 0.0376), "target_1_5r")

    def test_time_exit_after_12_hours(self):
        strategy = Strategy()
        opened = datetime(2025, 1, 1, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_date_utc=opened, open_rate=100.0, enter_tag="cab:99.8")
        before = opened + timedelta(hours=11, minutes=45)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, before, 100.0, 0.0))
        at = opened + timedelta(hours=12)
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, at, 100.0, -0.005), "time_exit_12h")

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        columns = [
            "cab_mv", "cab_mr", "cab_churn", "cab_context", "cab_signal", "cab_zl",
            "enter_long", "enter_tag",
        ]
        cases = [
            (random_frame(1200), 700),
            (crafted(), 150),
            (crafted(), 151),
            (crafted(), 152),
            (crafted(), 153),
        ]
        for frame, n in cases:
            short = run(frame.iloc[:n])
            long = run(frame)
            for column in columns:
                a = (short[column] if column in short else pd.Series(np.nan, index=short.index)).reset_index(drop=True)
                b = (long[column] if column in long else pd.Series(np.nan, index=long.index)).iloc[:n].reset_index(drop=True)
                pd.testing.assert_series_equal(a, b, check_dtype=False, check_names=False)

    def test_baselines_exclude_current_bar(self):
        frame = crafted()
        frame["volume"] = 1.0
        frame.loc[120, "volume"] = 50.0
        out = Strategy().populate_indicators(frame, {})
        self.assertAlmostEqual(float(out.loc[120, "cab_mv"]), 1.0)
        self.assertAlmostEqual(float(out.loc[121, "cab_mv"]), (95 + 50) / 96)


if __name__ == "__main__":
    unittest.main()
