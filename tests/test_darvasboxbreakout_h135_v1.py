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
NAME = "DarvasBoxBreakout_H135_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Pandas stand-in for TA-Lib EMA (the shared stub only has SMA/RSI): NaN for the first 199 rows.
def _ema(dataframe, timeperiod):
    out = dataframe["close"].ewm(span=timeperiod, adjust=False).mean()
    out.iloc[: timeperiod - 1] = np.nan
    return out


MODULE = load()
MODULE.ta = types.SimpleNamespace(EMA=_ema)
Strategy = getattr(MODULE, NAME)

OFF = 250  # the box starts after the EMA200 warm-up of the stub


def crafted(off=OFF, jb=2, n=420):
    """Flat 100 base. Top bar k = off+20 (high 102 = T). Bars k+1..: highs 101.5, lows descending
    100.5-0.01j up to j = jb (the bottom b = k+jb), then 100.9. Bottom confirmed at c = k+jb+3.
    Breakout bar t = k+jb+5: close 102.5, volume 30 (box mean volume 10)."""
    frame = pd.DataFrame(
        {"open": 100.0, "high": 100.2, "low": 99.8, "close": 100.0, "volume": 10.0},
        index=range(n),
    )
    k = off + 20
    frame.loc[k, ["open", "high", "low", "close"]] = [100.0, 102.0, 100.0, 101.0]
    t = k + jb + 5
    frame.loc[k + 1 : t - 1, ["open", "close", "high"]] = [101.0, 101.0, 101.5]
    for j in range(1, t - k):
        frame.loc[k + j, "low"] = 100.5 - 0.01 * j if j <= jb else 100.9
    frame.loc[t, ["open", "high", "low", "close", "volume"]] = [101.0, 102.6, 101.0, 102.5, 30.0]
    frame.loc[t + 1 :, ["open", "high", "low", "close"]] = [102.5, 102.55, 102.4, 102.5]
    return frame, k, t


def run(frame):
    strategy = Strategy()
    out = strategy.populate_indicators(frame.copy(), {})
    return strategy.populate_exit_trend(strategy.populate_entry_trend(out, {}), {})


def entries(out):
    if "enter_long" not in out:
        return []
    return out.index[out["enter_long"].fillna(0) == 1].tolist()


def random_frame(n=1200, seed=4):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.006, n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.004, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.004, n))
    volume = rng.lognormal(3, 0.8, n)
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume})


class DarvasBoxBreakoutTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.10)
        self.assertTrue(Strategy.use_custom_stoploss)
        self.assertGreaterEqual(Strategy.startup_candle_count, 1000)

    def test_signal_columns_are_binary(self):
        for frame in (random_frame(), crafted()[0]):
            out = run(frame)
            for column in ("enter_long", "exit_long"):
                if column in out:
                    self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_crafted_box_gives_one_entry_with_tag(self):
        frame, k, t = crafted()
        out = run(frame)
        self.assertEqual(entries(out), [t])
        bottom = float(frame.loc[k + 2, "low"])
        self.assertEqual(out.loc[t, "dbx_top"], 102.0)
        self.assertEqual(out.loc[t, "dbx_bottom"], bottom)
        self.assertEqual(out.loc[t, "enter_tag"], f"dbx:102.0:{bottom!r}")

    def test_box_is_used_up_at_signal_bar(self):
        frame, k, t = crafted()
        frame.loc[t + 1 : t + 5, ["close", "volume"]] = [102.8, 50.0]
        frame.loc[t + 1 : t + 5, "high"] = 102.9
        self.assertEqual(entries(run(frame)), [t])

    def test_zero_volume_gives_no_signal(self):
        frame, k, t = crafted()
        frame.loc[t, "volume"] = 0.0
        self.assertEqual(entries(run(frame)), [])
        frame, k, t = crafted()
        frame["volume"] = 0.0
        self.assertEqual(entries(run(frame)), [])
        self.assertEqual(entries(run(random_frame().assign(volume=0.0))), [])

    def test_undefined_startup_values_give_no_signal(self):
        # same box in the first bars: EMA200 is still undefined, so no entry
        frame, k, t = crafted(off=0)
        self.assertLess(t, 199)
        out = run(frame)
        self.assertTrue(out["ema200"].iloc[:199].isna().all())
        self.assertEqual(entries(out), [])
        # NaN volume in the box window: no signal
        frame, k, t = crafted()
        frame.loc[k + 3, "volume"] = np.nan
        self.assertEqual(entries(run(frame)), [])
        # no rows before the first full lookback give any signal on random data
        out = run(random_frame())
        self.assertEqual([i for i in entries(out) if i < 199], [])

    def test_breakout_close_and_volume_thresholds(self):
        frame, k, t = crafted()
        frame.loc[t, "close"] = 102.2  # < 1.002 x 102 = 102.204
        self.assertEqual(entries(run(frame)), [])
        frame, k, t = crafted()
        frame.loc[t, "close"] = 102.21
        self.assertEqual(entries(run(frame)), [t])
        frame, k, t = crafted()
        frame.loc[t, "volume"] = 14.9  # < 1.5 x 10
        self.assertEqual(entries(run(frame)), [])
        frame, k, t = crafted()
        frame.loc[t, "volume"] = 15.0  # exactly 1.5x passes
        self.assertEqual(entries(run(frame)), [t])

    def test_volume_mean_covers_bars_k_to_t_minus_1(self):
        frame, k, t = crafted()
        frame.loc[k, "volume"] = 100.0  # mean (100+6*10)/7 = 22.9 -> needs 34.3, 30 is not enough
        out = run(frame)
        self.assertEqual(entries(out), [])
        frame.loc[t, "volume"] = 1000.0
        self.assertEqual(entries(run(frame)), [t])
        frame, k, t = crafted()
        frame.loc[k - 1, "volume"] = 1000.0  # before the box: ignored
        self.assertEqual(entries(run(frame)), [t])

    def test_trend_filter(self):
        frame, k, t = crafted()
        strategy = Strategy()
        saved = MODULE.ta
        try:
            MODULE.ta = types.SimpleNamespace(EMA=lambda df, timeperiod: pd.Series(1000.0, index=df.index))
            out = strategy.populate_entry_trend(strategy.populate_indicators(frame.copy(), {}), {})
        finally:
            MODULE.ta = saved
        self.assertEqual(entries(out), [])

    def test_earlier_qualifying_close_on_weak_volume_does_not_void_box(self):
        frame, k, t = crafted()
        frame.loc[t - 1, ["close", "high"]] = [102.5, 102.6]  # volume 10: fails volume test
        self.assertEqual(entries(run(frame)), [t])

    def test_box_void_after_close_below_bottom(self):
        frame, k, t = crafted()
        c = k + 2 + 3
        frame.loc[c + 1, ["low", "close"]] = [99.5, 100.4]  # below B = 100.48
        self.assertEqual(entries(run(frame)), [])
        frame, k, t = crafted()
        frame.loc[c + 1, ["low", "close"]] = [99.5, 100.5]  # wick below, close above: still valid
        self.assertEqual(entries(run(frame)), [t])

    def test_box_height_limits(self):
        # B = 101.1: height 0.88% < 1%
        frame, k, t = crafted()
        frame.loc[k + 1 : t - 1, "low"] = 101.3
        frame.loc[k + 2, "low"] = 101.1
        self.assertEqual(entries(run(frame)), [])
        # B = 98.0: height 3.9% > 3%
        frame, k, t = crafted()
        frame.loc[k + 2, "low"] = 98.0
        self.assertEqual(entries(run(frame)), [])
        # B = 99.0: height 2.94% valid
        frame, k, t = crafted()
        frame.loc[k + 2, "low"] = 99.0
        frame.loc[k + 1, "low"] = 100.0
        self.assertEqual(entries(run(frame)), [t])

    def test_high_above_top_drops_the_attempt(self):
        frame, k, t = crafted()
        frame.loc[k + 4, "high"] = 102.5  # above T before c = k+5
        self.assertEqual(entries(run(frame)), [])

    def test_formation_limit_is_48_bars(self):
        # bottom at j = 45 -> c = k+48 is allowed; j = 46 -> c = k+49 is too late
        frame, k, t = crafted(jb=45)
        self.assertEqual(entries(run(frame)), [t])
        frame, k, t = crafted(jb=46)
        self.assertEqual(entries(run(frame)), [])

    def test_top_needs_three_lower_highs(self):
        frame, k, t = crafted()
        frame.loc[k + 3, "high"] = 102.0  # not strictly lower than T: no box
        self.assertEqual(entries(run(frame)), [])

    def test_top_must_be_a_17_bar_high(self):
        # a higher high 16 bars earlier is inside the window: bar k is not a top; the earlier bar
        # (T = 102.1) is itself the top of a box (flat lows, bottom = bar k-1), so T changes
        frame, k, t = crafted()
        frame.loc[k - 16, "high"] = 102.1
        out = run(frame)
        self.assertEqual(entries(out), [t])
        self.assertEqual(out.loc[t, "dbx_top"], 102.1)
        # 17 bars earlier is outside the window: bar k is a top and its newer box replaces the older
        frame, k, t = crafted()
        frame.loc[k - 17, "high"] = 102.1
        out = run(frame)
        self.assertEqual(entries(out), [t])
        self.assertEqual(out.loc[t, "dbx_top"], 102.0)

    def test_newer_box_replaces_older(self):
        def two_boxes(close_t2):
            frame, k, t = crafted()
            # bar t of the default frame is flat here; box 1 (T = 102) confirmed at k+5
            frame.loc[t : k + 25, ["open", "close", "high", "low", "volume"]] = [101.0, 101.0, 101.5, 100.9, 10.0]
            frame.loc[k + 8, "high"] = 103.0  # second top T2 = 103
            frame.loc[k + 9, "low"] = 100.7  # second bottom B2, confirmed at k+12
            t2 = k + 20
            frame.loc[t2, ["open", "high", "low", "close", "volume"]] = [101.0, 103.5, 101.0, close_t2, 30.0]
            frame.loc[t2 + 1 :, ["open", "high", "low", "close"]] = [102.5, 102.55, 102.4, 102.5]
            return run(frame), t2

        # 102.5 would break box 1 (T = 102) but box 2 (T = 103) replaced it: no entry
        out, t2 = two_boxes(102.5)
        self.assertEqual(entries(out), [])
        out, t2 = two_boxes(103.3)
        self.assertEqual(entries(out), [t2])
        self.assertEqual(out.loc[t2, "dbx_top"], 103.0)
        self.assertEqual(out.loc[t2, "dbx_bottom"], 100.7)

    def test_stop_is_box_bottom(self):
        strategy = Strategy()
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_rate=101.0, enter_tag="dbx:102.0:100.0")
        self.assertAlmostEqual(strategy.custom_stoploss("BTC/USDT", trade, now, 101.0, 0.0), 100.0 / 101.0 - 1)
        ratio = strategy.custom_stoploss("BTC/USDT", trade, now, 103.0, 0.02)
        self.assertAlmostEqual(103.0 * (1 + ratio), 100.0)
        self.assertLess(strategy.custom_stoploss("BTC/USDT", trade, now, 99.0, -0.02), 0)
        trade = types.SimpleNamespace(open_rate=101.0, enter_tag=None)
        self.assertIsNone(strategy.custom_stoploss("BTC/USDT", trade, now, 101.0, 0.0))

    def test_entry_skipped_when_fill_at_or_below_bottom(self):
        strategy = Strategy()
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        args = ("BTC/USDT", "limit", 1.0)
        self.assertFalse(strategy.confirm_trade_entry(*args, 100.0, "GTC", now, "dbx:102.0:100.0", "long"))
        self.assertFalse(strategy.confirm_trade_entry(*args, 99.0, "GTC", now, "dbx:102.0:100.0", "long"))
        self.assertTrue(strategy.confirm_trade_entry(*args, 100.5, "GTC", now, "dbx:102.0:100.0", "long"))

    def test_target_exit(self):
        strategy = Strategy()
        opened = datetime(2025, 1, 1, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_date_utc=opened, open_rate=101.0, enter_tag="dbx:102.0:100.0")
        soon = opened + timedelta(hours=1)
        # target = 101 + 1.5 * 2 = 104 -> +2.970297%
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, soon, 103.9, 0.0289))
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, soon, 104.0, 0.0298), "target_1_5_box")

    def test_time_exit_after_12_hours(self):
        strategy = Strategy()
        opened = datetime(2025, 1, 1, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_date_utc=opened, open_rate=101.0, enter_tag="dbx:102.0:100.0")
        before = opened + timedelta(hours=11, minutes=45)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, before, 101.0, 0.0))
        at = opened + timedelta(hours=12)
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, at, 101.0, -0.005), "time_exit_12h")

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        columns = ["ema200", "dbx_signal", "dbx_top", "dbx_bottom", "enter_long", "enter_tag"]
        cf, k, t = crafted()
        cases = [(random_frame(1200), n) for n in (500, 777, 1000)]
        cases += [(cf, n) for n in (k + 3, k + 6, t, t + 1, t + 3)]
        for frame, n in cases:
            short = run(frame.iloc[:n])
            long = run(frame)
            for column in columns:
                a = (short[column] if column in short else pd.Series(np.nan, index=short.index)).reset_index(drop=True)
                b = (
                    long[column] if column in long else pd.Series(np.nan, index=long.index)
                ).iloc[:n].reset_index(drop=True)
                pd.testing.assert_series_equal(a, b, check_dtype=False, check_names=False)

    def test_random_data_runs_and_signals_only_on_defined_rows(self):
        out = run(random_frame(3000, seed=9))
        for i in entries(out):
            self.assertTrue(np.isfinite(out.loc[i, "ema200"]))
            self.assertGreater(out.loc[i, "volume"], 0)
            self.assertGreaterEqual(out.loc[i, "close"], 1.002 * out.loc[i, "dbx_top"])


if __name__ == "__main__":
    unittest.main()
