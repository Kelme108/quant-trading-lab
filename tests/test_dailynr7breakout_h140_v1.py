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
NAME = "DailyNR7Breakout_H140_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


Strategy = getattr(load(), NAME)

START = pd.Timestamp("2024-01-01 00:00", tz="UTC")
DAY = 96
D = 12  # the trading day of the crafted frame
FIRST = D * DAY  # index of the 00:00 bar of day D


def dates(n):
    return pd.date_range(START, periods=n, freq="15min")


def random_frame(n=2000, seed=5):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.003, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.003, n))
    volume = rng.lognormal(3, 0.8, n)
    return pd.DataFrame(
        {"date": dates(n), "open": open_, "high": high, "low": low, "close": close, "volume": volume}
    )


WIDE = (96.0, 108.0)  # (low, high) of a wide day: range 12


def crafted(d1=(98.0, 106.0), d2=WIDE, wide=WIDE, drift=0.00002, days=14, breakout_bar=8):
    """Days 0..D-1 have an intraday spike giving them a fixed (low, high). Day D-1 is d1, D-2 is d2.
    Base price drifts (up by default, so the 4h close stays above its SMA(50)).
    On day D the open is the base price; with d1 = (98, 106), R1 = 8, so T = O + 4 and S = O - 4.
    The breakout bar of day D closes at 107, above T."""
    n = days * DAY
    base = 100.0 * (1.0 + drift * np.arange(n))
    frame = pd.DataFrame(
        {
            "date": dates(n),
            "open": base,
            "high": base * 1.0005,
            "low": base * 0.9995,
            "close": base,
            "volume": 10.0,
        }
    )
    for day in range(D):
        low, high = wide
        if day == D - 1:
            low, high = d1
        elif day == D - 2:
            low, high = d2
        i = day * DAY + 48
        frame.loc[i, "high"] = high
        frame.loc[i, "low"] = low
    if breakout_bar is not None:
        i = FIRST + breakout_bar
        frame.loc[i, ["high", "close"]] = [107.5, 107.0]
    return frame


def run(frame):
    strategy = Strategy()
    out = strategy.populate_indicators(frame.copy(), {})
    return strategy.populate_exit_trend(strategy.populate_entry_trend(out, {}), {})


def entries(out):
    if "enter_long" not in out:
        return []
    return out.index[out["enter_long"].fillna(0) == 1].tolist()


class DailyNR7BreakoutTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.10)
        self.assertTrue(Strategy.use_custom_stoploss)
        self.assertGreaterEqual(Strategy.startup_candle_count, 900)
        self.assertFalse(hasattr(load(), "LAB_MARKET"))

    def test_signal_columns_are_binary(self):
        for frame in (random_frame(), crafted()):
            out = run(frame)
            for column in ("enter_long", "exit_long"):
                if column in out:
                    self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_crafted_nr4_setup_gives_one_entry_with_stop_tag(self):
        out = run(crafted())
        o = out.loc[FIRST, "open"]
        self.assertAlmostEqual(out.loc[FIRST + 3, "nr7_trigger"], o + 4.0)
        self.assertAlmostEqual(out.loc[FIRST + 3, "nr7_stop"], o - 4.0)
        self.assertTrue(out.loc[FIRST + 3, "nr7_armed"])
        self.assertEqual(entries(out), [FIRST + 8])
        self.assertEqual(out.loc[FIRST + 8, "enter_tag"], "nr7:" + repr(float(o - 4.0)))

    def test_only_first_qualifying_bar_of_the_day(self):
        frame = crafted()
        frame.loc[FIRST + 12, ["high", "close"]] = [108.0, 107.5]
        frame.loc[FIRST + 30, ["high", "close"]] = [108.0, 107.5]
        self.assertEqual(entries(run(frame)), [FIRST + 8])

    def test_close_must_be_above_trigger(self):
        o = 100.0 * (1.0 + 0.00002 * FIRST)
        frame = crafted()
        frame.loc[FIRST + 8, "close"] = o + 4.0  # equal to T: not strictly above
        self.assertEqual(entries(run(frame)), [])
        frame = crafted()
        frame.loc[FIRST + 8, ["high", "close"]] = [o + 4.2, o + 4.01]
        self.assertEqual(entries(run(frame)), [FIRST + 8])

    def test_entry_window_ends_at_1145_bar_open(self):
        frame = crafted(breakout_bar=47)  # bar opening 11:45
        self.assertEqual(entries(run(frame)), [FIRST + 47])
        frame = crafted(breakout_bar=48)  # bar opening 12:00
        self.assertEqual(entries(run(frame)), [])
        frame = crafted(breakout_bar=0)  # bar opening 00:00 is allowed
        self.assertEqual(entries(run(frame)), [FIRST])

    def test_nr4_ties_count(self):
        # R1 == R2 == R3 == R4
        out = run(crafted(d1=WIDE))
        self.assertTrue(out.loc[FIRST + 3, "nr7_armed"])
        # R1 slightly larger than R2 (and not inside): not NR4
        out = run(crafted(d1=(96.0, 108.5)))
        self.assertFalse(out.loc[FIRST + 3, "nr7_armed"])
        self.assertEqual(entries(out), [])

    def test_nr4_needs_all_three_older_days(self):
        frame = crafted(d2=(96.0, 105.0))  # D-2 range 9, D-1 not inside D-2
        # day D-4 narrower than D-1 (range 4 < 8); D-2 = D-3 wide and not inside: no NR4
        frame.loc[(D - 4) * DAY + 48, ["low", "high"]] = [98.0, 102.0]
        out = run(frame)
        self.assertFalse(out.loc[FIRST + 3, "nr7_armed"])
        # D-4 with range equal to R1 still counts
        frame.loc[(D - 4) * DAY + 48, ["low", "high"]] = [98.0, 106.0]
        self.assertTrue(run(frame).loc[FIRST + 3, "nr7_armed"])

    def test_inside_day_arms_without_nr4(self):
        # D-1 (range 10) is inside D-2 (range 16) but wider than D-3 / D-4 (range 6): not NR4
        frame = crafted(d1=(97.0, 107.0), d2=(94.0, 110.0))
        for day in (D - 3, D - 4):
            frame.loc[day * DAY + 48, ["low", "high"]] = [100.0, 106.0]
        out = run(frame)
        self.assertTrue(out.loc[FIRST + 3, "nr7_armed"])
        o = out.loc[FIRST, "open"]
        self.assertAlmostEqual(out.loc[FIRST + 3, "nr7_trigger"], o + 5.0)
        frame.loc[FIRST + 8, ["high", "close"]] = [108.5, 108.0]  # > T = o + 5 = 107.3
        self.assertEqual(entries(run(frame)), [FIRST + 8])
        # touching the high of D-2 is not inside (strict inequality)
        frame = crafted(d1=(97.0, 110.0), d2=(94.0, 110.0))
        for day in (D - 3, D - 4):
            frame.loc[day * DAY + 48, ["low", "high"]] = [100.0, 106.0]
        self.assertFalse(run(frame).loc[FIRST + 3, "nr7_armed"])

    def test_minimum_range_pct(self):
        # R1 about 0.6% of the open: contraction holds but the day is not armed
        out = run(crafted(d1=(100.0, 100.5), drift=0.0))
        self.assertFalse(out.loc[FIRST + 3, "nr7_armed"])
        self.assertEqual(entries(out), [])
        # R1 = 1.0 on an open of 100.0 is exactly 1%: armed; 0.99 is not
        self.assertTrue(run(crafted(d1=(99.5, 100.5), drift=0.0)).loc[FIRST + 3, "nr7_armed"])
        self.assertFalse(run(crafted(d1=(99.5, 100.49), drift=0.0)).loc[FIRST + 3, "nr7_armed"])
        # R1 = 8% passes
        self.assertTrue(run(crafted()).loc[FIRST + 3, "nr7_armed"])

    def test_filter_blocks_entry_in_a_downtrend(self):
        out = run(crafted(drift=-0.00002))
        self.assertTrue(out.loc[FIRST + 3, "nr7_armed"])
        self.assertLess(out.loc[FIRST + 8, "nr7_close4h"], out.loc[FIRST + 8, "nr7_sma4h"])
        self.assertEqual(entries(out), [])

    def test_filter_uses_last_50_completed_4h_closes_including_latest_block(self):
        frame = crafted()
        out = run(frame)
        close = frame["close"].to_numpy()
        # at bar FIRST + 8 the last completed block ends with bar FIRST - 1 (= 16 * 72 - 1)
        ends = [16 * k + 15 for k in range(72)]
        expected = np.mean([close[i] for i in ends[-50:]])
        self.assertAlmostEqual(out.loc[FIRST + 8, "nr7_sma4h"], expected)
        self.assertAlmostEqual(out.loc[FIRST + 8, "nr7_close4h"], close[FIRST - 1])
        # on the last bar of a block (15th 15m bar closes the block) that block is already included
        i = 16 * 72 + 15
        self.assertAlmostEqual(out.loc[i, "nr7_close4h"], close[i])
        ends2 = [16 * k + 15 for k in range(73)]
        self.assertAlmostEqual(out.loc[i, "nr7_sma4h"], np.mean([close[j] for j in ends2[-50:]]))
        # one bar earlier the block is still open
        self.assertAlmostEqual(out.loc[i - 1, "nr7_close4h"], close[16 * 71 + 15])

    def test_incomplete_days_and_blocks_are_undefined(self):
        frame = crafted().drop(index=FIRST - DAY + 10).reset_index(drop=True)  # D-1 loses one bar
        out = run(frame)
        self.assertFalse(out["nr7_armed"].iloc[FIRST - DAY + 96 :].iloc[:60].any())
        self.assertEqual(entries(out), [])
        frame = crafted().drop(index=16 * 40 + 3).reset_index(drop=True)  # one 4h block incomplete
        out = run(frame)
        # SMA over 50 blocks that include the broken one is undefined for the next 49 blocks
        self.assertTrue(out["nr7_sma4h"].iloc[16 * 41 : 16 * 41 + 16 * 40].isna().all())

    def test_zero_volume_gives_no_signal(self):
        frame = crafted()
        frame["volume"] = 0.0
        self.assertEqual(entries(run(frame)), [])
        frame = crafted()
        frame.loc[FIRST + 8, "volume"] = 0.0  # breakout bar has zero volume: no entry on it
        out = run(frame)
        self.assertNotIn(FIRST + 8, entries(out))
        self.assertEqual(entries(run(random_frame().assign(volume=0.0))), [])

    def test_undefined_startup_values_give_no_signal(self):
        out = run(random_frame())
        # nothing before the first 50 completed 4h closes exist (800 bars), inside the 900 warm-up
        self.assertEqual([i for i in entries(out) if i < 16 * 50], [])
        # the 4h SMA(50) needs 50 completed blocks
        self.assertTrue(out["nr7_sma4h"].iloc[: 16 * 49].isna().all())
        self.assertTrue(out["nr7_trigger"].iloc[: DAY].isna().all())
        # a breakout inside the first days has no daily history
        frame = crafted(breakout_bar=None)
        frame.loc[2 * DAY + 8, ["high", "close"]] = [150.0, 140.0]
        self.assertEqual([i for i in entries(run(frame)) if i < 3 * DAY], [])
        # NaN stored stop / SMA blocks the entry
        strategy = Strategy()
        out = strategy.populate_indicators(crafted(), {})
        out.loc[FIRST + 8, "nr7_stop"] = np.nan
        self.assertEqual(entries(strategy.populate_entry_trend(out, {})), [])
        out = strategy.populate_indicators(crafted(), {})
        out.loc[FIRST + 8, "nr7_sma4h"] = np.nan
        self.assertEqual(entries(strategy.populate_entry_trend(out, {})), [])

    def test_stop_is_fixed_at_level_s(self):
        strategy = Strategy()
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_rate=104.5, enter_tag="nr7:98.3")
        ratio = strategy.custom_stoploss("BTC/USDT", trade, now, 104.5, 0.0)
        self.assertAlmostEqual(104.5 * (1 + ratio), 98.3)
        # the absolute stop price stays at S whatever the current rate
        ratio = strategy.custom_stoploss("BTC/USDT", trade, now, 110.0, 0.05)
        self.assertAlmostEqual(110.0 * (1 + ratio), 98.3)
        # S more than 10% below the fill: the native 10% backstop binds
        trade = types.SimpleNamespace(open_rate=100.0, enter_tag="nr7:80.0")
        ratio = strategy.custom_stoploss("BTC/USDT", trade, now, 100.0, 0.0)
        self.assertAlmostEqual(100.0 * (1 + ratio), 90.0)
        # price already below S: still a negative value (stops out)
        trade = types.SimpleNamespace(open_rate=100.0, enter_tag="nr7:98.0")
        self.assertLess(strategy.custom_stoploss("BTC/USDT", trade, now, 97.0, -0.03), 0)
        # missing tag: engine backstop
        trade = types.SimpleNamespace(open_rate=100.0, enter_tag=None)
        self.assertIsNone(strategy.custom_stoploss("BTC/USDT", trade, now, 100.0, 0.0))

    def test_no_take_profit(self):
        strategy = Strategy()
        opened = datetime(2025, 1, 1, 3, 15, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_date_utc=opened)
        soon = opened + timedelta(hours=1)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, soon, 150.0, 0.5))

    def test_day_end_exit(self):
        strategy = Strategy()
        opened = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_date_utc=opened)
        last = datetime(2025, 1, 1, 23, 45, tzinfo=timezone.utc)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, last, 100.0, 0.0))
        nxt = datetime(2025, 1, 2, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, nxt, 100.0, 0.01), "day_end_exit")

    def test_time_exit_after_48_bars(self):
        strategy = Strategy()
        opened = datetime(2025, 1, 1, 0, 15, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_date_utc=opened)
        before = opened + timedelta(hours=11, minutes=45)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, before, 100.0, 0.0))
        at = opened + timedelta(hours=12)
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, at, 100.0, -0.005), "time_exit_12h")

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        columns = [
            "nr7_trigger", "nr7_stop", "nr7_armed", "nr7_close4h", "nr7_sma4h",
            "nr7_signal", "enter_long", "enter_tag",
        ]
        cases = [
            (random_frame(2400), 1500, 2400),
            (crafted(), FIRST + 8, len(crafted())),
            (crafted(), FIRST + 9, len(crafted())),
            (crafted(), FIRST + 40, len(crafted())),
            (crafted(), FIRST + 3, len(crafted())),
        ]
        for frame, n, total in cases:
            short = run(frame.iloc[:n])
            long = run(frame.iloc[:total])
            for column in columns:
                a = (short[column] if column in short else pd.Series(np.nan, index=short.index)).reset_index(drop=True)
                b = (
                    long[column] if column in long else pd.Series(np.nan, index=long.index)
                ).iloc[:n].reset_index(drop=True)
                pd.testing.assert_series_equal(a, b, check_dtype=False, check_names=False)


if __name__ == "__main__":
    unittest.main()
