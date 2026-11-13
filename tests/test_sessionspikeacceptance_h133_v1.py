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
NAME = "SessionSpikeAcceptance_H133_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


Strategy = getattr(load(), NAME)

START = pd.Timestamp("2024-01-01 00:00", tz="UTC")
X0 = 960  # first bar of the spike session X (session index 30, a 00:00 session)
N0 = 992  # first bar of the acceptance session N
SIGNAL = N0 + 3  # bar 4 of N


def dates(n):
    return pd.date_range(START, periods=n, freq="15min")


def random_frame(n=1500, seed=5):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.003, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.003, n))
    volume = rng.lognormal(3, 0.8, n)
    return pd.DataFrame(
        {"date": dates(n), "open": open_, "high": high, "low": low, "close": close, "volume": volume}
    )


def crafted(n=1100):
    """Every session has range 1.0 (high 100.5, low 99.5) so AR = 1.0 for the spike session X
    (bars 960-991). X: BASE = 100.5, WH = 102.0 (bar 986), WL = 100.0, C = 101.8.
    N (bars 992-1023): closes 101.6, 101.7, 101.9, 102.2 -> MID = 101.25, close of bar 4 > WH."""
    frame = pd.DataFrame(
        {"date": dates(n), "open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0, "volume": 10.0}
    )
    last_x = X0 + 31
    frame.loc[X0 + 24:last_x, "high"] = 101.5
    frame.loc[X0 + 24:last_x, "low"] = 100.0
    frame.loc[X0 + 26, "high"] = 102.0
    frame.loc[last_x, "close"] = 101.8
    frame.loc[N0, ["open", "high", "low", "close"]] = [101.8, 102.0, 101.5, 101.6]
    frame.loc[N0 + 1, ["open", "high", "low", "close"]] = [101.6, 101.9, 101.5, 101.7]
    frame.loc[N0 + 2, ["open", "high", "low", "close"]] = [101.7, 102.0, 101.6, 101.9]
    frame.loc[N0 + 3, ["open", "high", "low", "close"]] = [101.9, 102.4, 101.8, 102.2]
    frame.loc[N0 + 4:, ["open", "high", "low", "close"]] = [102.2, 102.5, 101.9, 102.2]
    return frame


def run(frame):
    strategy = Strategy()
    out = strategy.populate_indicators(frame.copy(), {})
    return strategy.populate_exit_trend(strategy.populate_entry_trend(out, {}), {})


def entries(out):
    if "enter_long" not in out:
        return []
    return out.index[out["enter_long"].fillna(0) == 1].tolist()


def trade(open_rate=100.0, tag="ssa:99.0", opened=None):
    return types.SimpleNamespace(
        open_rate=open_rate,
        enter_tag=tag,
        open_date_utc=opened or datetime(2025, 1, 1, 1, 0, tzinfo=timezone.utc),
    )


NOW = datetime(2025, 1, 1, 2, 0, tzinfo=timezone.utc)


class SessionSpikeAcceptanceTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.03)
        self.assertGreaterEqual(Strategy.startup_candle_count, 996)

    def test_signal_columns_are_binary(self):
        for frame in (random_frame(), crafted()):
            out = run(frame)
            for column in ("enter_long", "exit_long"):
                if column in out:
                    self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_crafted_setup_gives_one_entry_with_tag(self):
        out = run(crafted())
        self.assertEqual(entries(out), [SIGNAL])
        self.assertEqual(out.loc[SIGNAL, "enter_tag"], "ssa:100.5")
        self.assertEqual(out.loc[SIGNAL, "ssa_wh"], 102.0)
        self.assertAlmostEqual(out.loc[SIGNAL, "ssa_mid"], 101.25)

    def test_zero_volume_gives_no_signal(self):
        self.assertEqual(entries(run(crafted().assign(volume=0.0))), [])
        frame = crafted()
        frame.loc[SIGNAL, "volume"] = 0.0
        self.assertEqual(entries(run(frame)), [])
        self.assertEqual(entries(run(random_frame().assign(volume=0.0))), [])
        out = run(crafted().assign(volume=0.0))
        self.assertNotIn("exit_long", out)

    def test_undefined_startup_values_give_no_signal(self):
        out = run(random_frame())
        self.assertEqual([i for i in entries(out) if i < 992], [])
        # fewer than 10 earlier complete sessions of the type: no spike
        short_history = crafted().iloc[320:].reset_index(drop=True)
        self.assertEqual(entries(run(short_history)), [])
        # only 9 earlier complete sessions of the type (session 0 cut off): no spike
        nine = crafted().iloc[96:].reset_index(drop=True)
        self.assertEqual(entries(run(nine)), [])
        # exactly 10 earlier complete sessions of the type: spike works
        self.assertEqual(entries(run(crafted().iloc[:])), [SIGNAL])
        # NaN price at the signal bar: no entry
        frame = crafted()
        frame.loc[SIGNAL, "close"] = np.nan
        self.assertEqual(entries(run(frame)), [])
        # NaN stored base blocks the entry
        strategy = Strategy()
        out = strategy.populate_indicators(crafted(), {})
        out.loc[SIGNAL, "ssa_base"] = np.nan
        self.assertEqual(entries(strategy.populate_entry_trend(out, {})), [])

    def test_ar_counts_only_complete_sessions(self):
        # session 0 loses a bar -> only 9 complete 00:00 sessions before X -> no spike
        frame = crafted().drop(index=10).reset_index(drop=True)
        self.assertEqual(entries(run(frame)), [])
        # a missing bar in another session type does not matter
        frame = crafted().drop(index=40).reset_index(drop=True)
        self.assertEqual(entries(run(frame)), [SIGNAL - 1])

    def test_spike_conditions(self):
        # incomplete X
        frame = crafted().drop(index=X0 + 5).reset_index(drop=True)
        self.assertEqual(entries(run(frame)), [])
        # no new high in the last 2h: WH <= BASE
        frame = crafted()
        frame.loc[X0 + 24:X0 + 31, "high"] = 100.5
        self.assertEqual(entries(run(frame)), [])
        # close below BASE + 0.25 AR = 100.75 (also fails the close location)
        frame = crafted()
        frame.loc[X0 + 31, "close"] = 100.7
        self.assertEqual(entries(run(frame)), [])
        # close location just below 0.70: (C - WL)/(WH - WL) with WL=100, WH=102 -> C < 101.4
        frame = crafted()
        frame.loc[X0 + 31, "close"] = 101.39
        self.assertEqual(entries(run(frame)), [])
        # exactly 0.70 passes the location test, but the signal bar must still beat WH
        frame = crafted()
        frame.loc[X0 + 31, "close"] = 101.4
        self.assertEqual(entries(run(frame)), [SIGNAL])
        # larger average range raises the bar: AR = 8.5 -> BASE + 2.125 = 102.625 > C
        frame = crafted()
        for session_index in range(0, 30, 3):
            frame.loc[session_index * 32 + 3, "high"] = 108.0
        self.assertEqual(entries(run(frame)), [])

    def test_acceptance_conditions(self):
        # a close in bars 1-3 of N below MID = 101.25
        for offset in (0, 1, 2):
            frame = crafted()
            frame.loc[N0 + offset, "close"] = 101.2
            self.assertEqual(entries(run(frame)), [], offset)
        # exactly MID passes
        frame = crafted()
        frame.loc[N0 + 1, "close"] = 101.25
        self.assertEqual(entries(run(frame)), [SIGNAL])
        # close of bar 4 not above WH
        for value in (102.0, 101.9):
            frame = crafted()
            frame.loc[SIGNAL, "close"] = value
            self.assertEqual(entries(run(frame)), [], value)
        frame = crafted()
        frame.loc[SIGNAL, "close"] = 102.01
        self.assertEqual(entries(run(frame)), [SIGNAL])
        # a missing bar among bars 1-4 of N
        frame = crafted().drop(index=N0 + 1).reset_index(drop=True)
        self.assertEqual(entries(run(frame)), [])
        # a late "acceptance" in a later bar does not count
        frame = crafted()
        frame.loc[SIGNAL, "close"] = 101.9
        frame.loc[SIGNAL + 1, ["close", "high"]] = [102.3, 102.4]
        self.assertEqual(entries(run(frame)), [])

    def test_one_signal_per_spike_and_following_session_only(self):
        out = run(crafted())
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 1)
        # the session after N is not tied to X
        self.assertTrue(out["ssa_prev_spike"].iloc[N0:N0 + 32].all())
        self.assertFalse(out["ssa_prev_spike"].iloc[N0 + 32:].any())
        self.assertFalse(out["ssa_prev_spike"].iloc[:N0].any())

    def test_s3_is_followed_by_next_days_s1(self):
        # shift the crafted pattern by 64 bars so X is an S3 session (16:00) and N the next 00:00
        frame = crafted(1250)
        shifted = pd.DataFrame(
            {"date": dates(1250), "open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0, "volume": 10.0}
        )
        # reuse the pattern: session 32 (index) is type 2 = 16:00. Build X there directly.
        x0 = 32 * 32 + 0
        # make every earlier 16:00 session range 1.0 (default) and build the spike at x0
        # session index 32 -> type 32 % 3 = 2 (16:00)
        shifted.loc[x0 + 24:x0 + 31, "high"] = 101.5
        shifted.loc[x0 + 24:x0 + 31, "low"] = 100.0
        shifted.loc[x0 + 26, "high"] = 102.0
        shifted.loc[x0 + 31, "close"] = 101.8
        n0 = x0 + 32
        shifted.loc[n0 + 0, "close"] = 101.6
        shifted.loc[n0 + 1, "close"] = 101.7
        shifted.loc[n0 + 2, "close"] = 101.9
        shifted.loc[n0 + 3, ["high", "close"]] = [102.4, 102.2]
        out = run(shifted)
        self.assertEqual(shifted.loc[x0, "date"].hour, 16)
        self.assertEqual(shifted.loc[n0, "date"].hour, 0)
        self.assertEqual(entries(out), [n0 + 3])
        del frame

    def test_stop_is_frozen_below_entry(self):
        strategy = Strategy()
        # BASE 99.0, E 100: SP = min(99, 99) = 99 -> d = 1%
        self.assertAlmostEqual(strategy.custom_stoploss("BTC/USDT", trade(100.0, "ssa:99.0"), NOW, 100.0, 0.0), -0.01)
        # later price: the absolute stop stays at 99
        ratio = strategy.custom_stoploss("BTC/USDT", trade(100.0, "ssa:99.0"), NOW, 101.0, 0.01)
        self.assertAlmostEqual(101.0 * (1 + ratio), 99.0)
        # BASE far enough below 0.99 E: stop at BASE (d = 2.5%)
        stop = 100.0 * (1 + Strategy().custom_stoploss("BTC/USDT", trade(100.0, "ssa:97.5"), NOW, 100.0, 0.0))
        self.assertAlmostEqual(stop, 97.5)
        # BASE above 0.99 E: stop at 0.99 E
        stop = 100.0 * (1 + Strategy().custom_stoploss("BTC/USDT", trade(100.0, "ssa:100.4"), NOW, 100.0, 0.0))
        self.assertAlmostEqual(stop, 99.0)
        # price already below the stop: still negative
        self.assertLess(strategy.custom_stoploss("BTC/USDT", trade(100.0, "ssa:97.5"), NOW, 90.0, -0.1), 0)
        # missing tag: native backstop
        self.assertIsNone(strategy.custom_stoploss("BTC/USDT", trade(100.0, None), NOW, 100.0, 0.0))

    def test_fill_check(self):
        strategy = Strategy()

        def confirm(rate, tag):
            return strategy.confirm_trade_entry("BTC/USDT", "market", 1.0, rate, "GTC", NOW, tag, "long")

        self.assertTrue(confirm(100.0, "ssa:97.0"))  # exactly 0.97 E is allowed
        self.assertFalse(confirm(100.0, "ssa:96.99"))
        self.assertTrue(confirm(100.0, "ssa:101.0"))
        self.assertFalse(confirm(100.0, None))

    def test_take_profit_exit(self):
        strategy = Strategy()
        soon = trade().open_date_utc + timedelta(hours=1)
        # E 100, BASE 99 -> SP 99, TP = 100 + 1.5 = 101.5
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade(), soon, 101.49, 0.0149))
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade(), soon, 101.5, 0.015), "take_profit_1p5R")
        # E 100, BASE 97.5 -> d = 2.5%, TP = 103.75
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade(100.0, "ssa:97.5"), soon, 103.7, 0.037))
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade(100.0, "ssa:97.5"), soon, 103.75, 0.0375), "take_profit_1p5R"
        )

    def test_time_exit_after_7_hours(self):
        strategy = Strategy()
        opened = datetime(2025, 1, 1, 1, 0, tzinfo=timezone.utc)
        t = trade(opened=opened)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", t, opened + timedelta(hours=6, minutes=45), 100.0, 0.0))
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", t, opened + timedelta(hours=7), 100.0, -0.005), "time_exit_7h"
        )

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        columns = [
            "ssa_prev_spike", "ssa_base", "ssa_wh", "ssa_mid", "ssa_signal", "enter_long", "enter_tag",
        ]
        cases = [(random_frame(1500), 1200), (random_frame(1500), 1000)]
        frame = crafted(1100)
        cases += [(frame, 991), (frame, 992), (frame, 995), (frame, 996), (frame, 1000), (frame, 1030)]
        for source, n in cases:
            short = run(source.iloc[:n])
            long = run(source)
            for column in columns:
                a = (short[column] if column in short else pd.Series(np.nan, index=short.index)).reset_index(drop=True)
                b = (
                    long[column] if column in long else pd.Series(np.nan, index=long.index)
                ).iloc[:n].reset_index(drop=True)
                pd.testing.assert_series_equal(a, b, check_dtype=False, check_names=False)
        self.assertEqual(entries(run(frame.iloc[:996])), [SIGNAL])
        self.assertEqual(entries(run(frame.iloc[:995])), [])


if __name__ == "__main__":
    unittest.main()
