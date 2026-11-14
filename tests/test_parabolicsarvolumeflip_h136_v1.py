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
NAME = "ParabolicSARVolumeFlip_H136_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load()
Strategy = getattr(MODULE, NAME)

START = pd.Timestamp("2024-01-01 00:00", tz="UTC")


def dates(n):
    return pd.date_range(START, periods=n, freq="15min")


def random_frame(n=1200, seed=5):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.003, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.003, n))
    volume = rng.lognormal(3, 0.8, n)
    return pd.DataFrame(
        {"date": dates(n), "open": open_, "high": high, "low": low, "close": close, "volume": volume}
    )


def crafted(n=60):
    """Steady decline for 30 bars (SAR down), then bar 30 is a volume-surge up-flip bar."""
    close = 100.0 - 0.5 * np.arange(n)
    open_ = np.concatenate([[100.0], close[:-1]])
    frame = pd.DataFrame(
        {
            "date": dates(n),
            "open": open_,
            "high": open_ + 0.1,
            "low": close - 0.1,
            "close": close,
            "volume": 10.0,
        }
    )
    base = 100.0 - 0.5 * 29  # close of bar 29
    frame.loc[30, ["open", "high", "low", "close", "volume"]] = [base, base + 3.2, base - 0.1, base + 3.0, 30.0]
    frame.loc[31:, ["open", "high", "low", "close"]] = [base + 3.0, base + 3.4, base + 2.8, base + 3.2]
    return frame


def run(frame):
    strategy = Strategy()
    out = strategy.populate_indicators(frame.copy(), {})
    return strategy.populate_exit_trend(strategy.populate_entry_trend(out, {}), {})


def entries(out):
    if "enter_long" not in out:
        return []
    return out.index[out["enter_long"].fillna(0) == 1].tolist()


def exits(out):
    if "exit_long" not in out:
        return []
    return out.index[out["exit_long"].fillna(0) == 1].tolist()


class FakeDP:
    def __init__(self, frame):
        self.frame = frame

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.frame, None


class ParabolicSARVolumeFlipTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.03)
        self.assertTrue(Strategy.use_custom_stoploss)
        self.assertGreaterEqual(Strategy.startup_candle_count, 500)

    def test_wilder_sar_hand_checked(self):
        high = np.array([10.0, 11.0, 12.0, 11.5, 11.0, 12.5])
        low = np.array([9.0, 9.5, 10.0, 9.1, 8.5, 10.0])
        direction, sar, nxt = MODULE.wilder_sar(high, low)
        self.assertEqual(direction.tolist(), [1, 1, 1, -1, -1, 1])
        np.testing.assert_allclose(sar, [9, 9, 9, 12, 12, 8.5])
        np.testing.assert_allclose(nxt, [9.0, 9.0, 9.18, 12.0, 11.86, 8.5])

    def test_af_is_capped_at_0_20(self):
        n = 40
        high = 10.0 + np.arange(n)
        low = 9.5 + np.arange(n)
        direction, sar, nxt = MODULE.wilder_sar(high, low)
        self.assertTrue((direction == 1).all())
        # after AF has saturated at 0.20, nxt = sar + 0.2 * (ep - sar) (cap not binding here)
        t = n - 1
        expected = sar[t] + 0.20 * (high[t] - sar[t])
        self.assertAlmostEqual(nxt[t], min(expected, low[t], low[t - 1]))

    def test_signal_columns_are_binary(self):
        for frame in (random_frame(), crafted()):
            out = run(frame)
            for column in ("enter_long", "exit_long"):
                if column in out:
                    self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_crafted_flip_gives_one_entry_with_tag(self):
        out = run(crafted())
        self.assertEqual(entries(out), [30])
        self.assertEqual(out.loc[29, "psar_dir"], -1)
        self.assertEqual(out.loc[30, "psar_dir"], 1)
        tag = out.loc[30, "enter_tag"]
        self.assertTrue(tag.startswith("psar:"))
        self.assertAlmostEqual(float(tag[5:]), out.loc[30, "psar_nxt"])
        self.assertTrue(all(i < 30 for i in exits(out)))  # no SAR-down exit after the flip

    def test_zero_volume_gives_no_signal(self):
        self.assertEqual(entries(run(crafted().assign(volume=0.0))), [])
        self.assertEqual(exits(run(crafted().assign(volume=0.0))), [])
        frame = crafted()
        frame.loc[30, "volume"] = 0.0
        self.assertEqual(entries(run(frame)), [])
        self.assertEqual(entries(run(random_frame().assign(volume=0.0))), [])
        self.assertEqual(exits(run(random_frame().assign(volume=0.0))), [])

    def test_undefined_startup_values_give_no_signal(self):
        out = run(random_frame())
        self.assertEqual([i for i in entries(out) if i < 21], [])
        self.assertTrue(out["vmean"].iloc[:20].isna().all())
        self.assertTrue(pd.isna(out["psar_dir"].shift(1).iloc[0]))
        # a flip bar inside the first 20 bars has no volume mean: no entry
        frame = crafted()
        frame.loc[10, ["open", "high", "low", "close", "volume"]] = [95.0, 140.0, 94.0, 139.0, 500.0]
        self.assertNotIn(10, entries(run(frame)))
        # NaN volume mean: no entry
        frame = crafted()
        frame.loc[15, "volume"] = np.nan
        self.assertEqual(entries(run(frame)), [])
        # NaN stored NXT blocks the entry
        strategy = Strategy()
        out = strategy.populate_indicators(crafted(), {})
        out.loc[30, "psar_nxt"] = np.nan
        self.assertEqual(entries(strategy.populate_entry_trend(out, {})), [])
        # NaN direction blocks entry and exit
        out = strategy.populate_indicators(crafted(), {})
        out.loc[30, "psar_dir"] = np.nan
        out.loc[20, "psar_dir"] = np.nan
        out = strategy.populate_exit_trend(strategy.populate_entry_trend(out, {}), {})
        self.assertEqual(entries(out), [])
        self.assertNotIn(20, exits(out))

    def test_entry_thresholds(self):
        frame = crafted()
        frame.loc[30, "volume"] = 14.9  # < 1.5 x 10
        self.assertEqual(entries(run(frame)), [])
        frame.loc[30, "volume"] = 15.0  # exactly 1.5x passes
        self.assertEqual(entries(run(frame)), [30])
        frame = crafted()
        frame.loc[30, "close"] = frame.loc[30, "open"]  # not an up close
        self.assertEqual(entries(run(frame)), [])
        frame.loc[30, "close"] = frame.loc[30, "open"] - 0.5
        self.assertEqual(entries(run(frame)), [])

    def test_no_entry_without_down_to_up_transition(self):
        # a rising market from the start never has dir(t-1)=down
        n = 80
        close = 100.0 + 0.5 * np.arange(n)
        frame = pd.DataFrame(
            {
                "date": dates(n),
                "open": np.concatenate([[100.0], close[:-1]]),
                "high": close + 0.1,
                "low": np.concatenate([[99.0], close[:-1]]) - 0.1,
                "close": close,
                "volume": 10.0,
            }
        )
        frame.loc[50, "volume"] = 100.0
        self.assertEqual(entries(run(frame)), [])

    def test_sar_exit_signal_when_direction_down(self):
        frame = crafted()
        # a collapse after the flip: bar 40 breaks the SAR
        frame.loc[40:, ["open", "high", "low", "close"]] = [96.0, 96.2, 85.0, 86.0]
        out = run(frame)
        self.assertIn(40, exits(out))
        self.assertEqual(out.loc[40, "psar_dir"], -1)
        self.assertEqual(out.loc[40, "exit_tag"], "sar_down")
        self.assertNotIn(39, exits(out))

    def test_vmean_excludes_current_bar(self):
        frame = crafted()
        frame["volume"] = 1.0
        frame.loc[40, "volume"] = 10.0
        out = Strategy().populate_indicators(frame, {})
        self.assertAlmostEqual(float(out.loc[40, "vmean"]), 1.0)
        self.assertAlmostEqual(float(out.loc[41, "vmean"]), 1.45)

    def test_confirm_trade_entry_fill_check(self):
        strategy = Strategy()
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)

        def confirm(tag, rate=100.0):
            return strategy.confirm_trade_entry("BTC/USDT", "limit", 1.0, rate, "GTC", now, tag, "long")

        self.assertTrue(confirm("psar:99.0"))
        self.assertTrue(confirm("psar:97.5"))
        self.assertFalse(confirm("psar:96.99"))
        self.assertFalse(confirm(None))
        self.assertFalse(confirm("junk"))
        # NXT above the fill is fine
        self.assertTrue(confirm("psar:101.0"))

    def test_initial_stop_without_data(self):
        strategy = Strategy()
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        # NXT 98.5 is below 0.99 E: S0 = 98.5
        trade = types.SimpleNamespace(open_rate=100.0, enter_tag="psar:98.5")
        stop = 100.0 * (1 + strategy.custom_stoploss("BTC/USDT", trade, now, 100.0, 0.0))
        self.assertAlmostEqual(stop, 98.5)
        # NXT 99.5 is within 1% of E: S0 = 99.0 (1% floor)
        trade = types.SimpleNamespace(open_rate=100.0, enter_tag="psar:99.5")
        stop = 100.0 * (1 + strategy.custom_stoploss("BTC/USDT", trade, now, 100.0, 0.0))
        self.assertAlmostEqual(stop, 99.0)
        # missing tag: native backstop
        trade = types.SimpleNamespace(open_rate=100.0, enter_tag=None)
        self.assertIsNone(strategy.custom_stoploss("BTC/USDT", trade, now, 100.0, 0.0))

    def test_trail_follows_sar_shifted_by_gap_and_never_below_s0(self):
        strategy = Strategy()
        last_closed = START + timedelta(minutes=15 * 9)
        now = last_closed + timedelta(minutes=15)  # open of the next bar
        frame = pd.DataFrame(
            {
                "date": dates(11),
                "psar_nxt": [90.0] * 9 + [100.2, 150.0],  # bar 9 closed, bar 10 is current (ignored)
            }
        )
        strategy.dp = FakeDP(frame)
        # G = 0 (NXT 98.5 <= 0.99 E): L = max(98.5, 100.2) = 100.2
        trade = types.SimpleNamespace(open_rate=100.0, enter_tag="psar:98.5")
        stop = 101.0 * (1 + strategy.custom_stoploss("BTC/USDT", trade, now, 101.0, 0.01))
        self.assertAlmostEqual(stop, 100.2)
        # G = 0.5 (NXT 99.5, S0 = 99.0): L = max(99.0, 100.2 - 0.5) = 99.7
        trade = types.SimpleNamespace(open_rate=100.0, enter_tag="psar:99.5")
        stop = 101.0 * (1 + strategy.custom_stoploss("BTC/USDT", trade, now, 101.0, 0.01))
        self.assertAlmostEqual(stop, 99.7)
        # SAR below S0: the stop stays at S0
        frame.loc[9, "psar_nxt"] = 95.0
        stop = 101.0 * (1 + strategy.custom_stoploss("BTC/USDT", trade, now, 101.0, 0.01))
        self.assertAlmostEqual(stop, 99.0)
        # price already below the level: still negative, stops out immediately
        frame.loc[9, "psar_nxt"] = 100.2
        self.assertLess(strategy.custom_stoploss("BTC/USDT", trade, now, 99.0, -0.01), 0)
        # first bar of the trade (k = t+1): level is S0
        frame.loc[9, "psar_nxt"] = 99.5
        stop = 100.0 * (1 + strategy.custom_stoploss("BTC/USDT", trade, now, 100.0, 0.0))
        self.assertAlmostEqual(stop, 99.0)

    def test_time_exit_after_12_hours_and_no_take_profit(self):
        strategy = Strategy()
        opened = datetime(2025, 1, 1, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_date_utc=opened)
        before = opened + timedelta(hours=11, minutes=45)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, before, 100.0, 0.0))
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, before, 150.0, 0.5))  # no take-profit
        at = opened + timedelta(hours=12)
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, at, 100.0, -0.005), "time_exit_12h")

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        columns = ["psar_dir", "psar", "psar_nxt", "vmean", "enter_long", "enter_tag", "exit_long", "exit_tag"]
        cases = [(random_frame(1500), 900), (random_frame(1500, seed=9), 1000), (crafted(80), 30), (crafted(80), 31)]
        for frame, n in cases:
            short = run(frame.iloc[:n])
            long = run(frame)
            for column in columns:
                a = (short[column] if column in short else pd.Series(np.nan, index=short.index)).reset_index(drop=True)
                b = (long[column] if column in long else pd.Series(np.nan, index=long.index)).iloc[:n].reset_index(drop=True)
                pd.testing.assert_series_equal(a, b, check_dtype=False, check_names=False)

    def test_random_series_produces_entries(self):
        out = run(random_frame(3000))
        self.assertGreater(len(entries(out)), 0)


if __name__ == "__main__":
    unittest.main()
