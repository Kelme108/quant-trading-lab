import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

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
NAME = "SMTDivergenceSweep_H115_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load()
Strategy = getattr(MODULE, NAME)

START = pd.Timestamp("2026-01-01 00:00", tz="UTC")


class FakeDP:
    def __init__(self, frame):
        self.frame = frame
        self.requested = []

    def get_pair_dataframe(self, pair, timeframe):
        self.requested.append((pair, timeframe))
        return self.frame.copy()


def make_pair_frames(n=200, break_close=101.0, deep_low_at=None):
    """X is flat; B sweeps its 12h low over bars 118..121; X breaks out at bars 122 and 125."""
    dates = pd.date_range(START, periods=n, freq="15min")

    def flat(price, rel_high, rel_low):
        return pd.DataFrame(
            {
                "date": dates,
                "open": price,
                "high": price * rel_high,
                "low": price * rel_low,
                "close": price,
                "volume": 1.0,
            }
        )

    x = flat(100.0, 1.002, 0.998)
    b = flat(1000.0, 1.001, 0.999)
    b.loc[119:122, "low"] = 990.0
    b.loc[[121, 124], "close"] = 995.0
    x.loc[122, ["close", "high"]] = [break_close, break_close * 1.001]
    x.loc[123, "close"] = 100.5
    x.loc[125, ["close", "high"]] = [break_close + 1.0, (break_close + 1.0) * 1.001]
    x.loc[127, ["close", "high"]] = [break_close + 2.0, (break_close + 2.0) * 1.001]
    if deep_low_at is not None:
        x.loc[deep_low_at, "low"] = 96.0
    return x, b


def run(x, b, pair="ETH/USDT"):
    strategy = Strategy()
    strategy.dp = FakeDP(b)
    frame = strategy.populate_indicators(x.copy(), {"pair": pair})
    frame = strategy.populate_entry_trend(frame, {"pair": pair})
    frame = strategy.populate_exit_trend(frame, {"pair": pair})
    return strategy, frame


def signal_rows(frame):
    if "enter_long" not in frame:
        return []
    return frame.index[frame["enter_long"] == 1].tolist()


class FakeTrade:
    def __init__(self, tag, open_rate=100.0, open_date=None):
        self.enter_tag = tag
        self.open_rate = open_rate
        self.open_date_utc = open_date or datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)


class SMTDivergenceSweepTests(unittest.TestCase):
    def test_contract_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.03)
        self.assertTrue(Strategy.use_custom_stoploss)
        self.assertGreaterEqual(Strategy.startup_candle_count, 60)
        self.assertEqual(Strategy.startup_candle_count, 100)

    def test_reference_pair_selection(self):
        self.assertEqual(MODULE.reference_pair_for("ETH/USDT"), "BTC/USDT")
        self.assertEqual(MODULE.reference_pair_for("SOL/USDT"), "BTC/USDT")
        self.assertEqual(MODULE.reference_pair_for("BTC/USDT"), "ETH/USDT")
        x, b = make_pair_frames()
        strategy, _ = run(x, b, pair="BTC/USDT")
        self.assertEqual(strategy.dp.requested, [("ETH/USDT", "15m")])
        strategy, _ = run(x, b, pair="SOL/USDT")
        self.assertEqual(strategy.dp.requested, [("BTC/USDT", "15m")])

    def test_signals_and_setup_consumption(self):
        x, b = make_pair_frames()
        _, frame = run(x, b)
        # Setups at 119..123; bar 122 consumes 119..122; bar 125 consumes 123; bar 127 has none left.
        self.assertEqual(signal_rows(frame), [122, 125])
        self.assertTrue(frame.loc[119:123, "smt_setup"].all())
        self.assertFalse(frame.loc[[118, 124, 125, 126], "smt_setup"].any())
        for column in ("enter_long",):
            self.assertTrue(set(frame[column].dropna().unique().tolist()).issubset({1}))
        d = (101.0 - 100.0 * 0.998) / 101.0
        self.assertAlmostEqual(MODULE.parse_tag(frame.loc[122, "enter_tag"]), d)
        self.assertNotIn("exit_long", frame.columns)

    def test_setup_expires_after_eight_armed_bars(self):
        x, b = make_pair_frames()
        # Last setup is bar 123, armed through bar 131 (s..s+8).
        x.loc[[122, 125, 127], ["close", "high"]] = [100.0, 100.2]
        x.loc[131, ["close", "high"]] = [101.0, 101.1]
        b.loc[130, "close"] = 995.0
        _, frame = run(x, b)
        self.assertEqual(signal_rows(frame), [131])
        x.loc[131, ["close", "high"]] = [100.0, 100.2]
        x.loc[132, ["close", "high"]] = [101.0, 101.1]
        b.loc[131, "close"] = 995.0
        _, frame = run(x, b)
        self.assertEqual(signal_rows(frame), [])

    def test_stop_distance_floor_and_cap(self):
        x, b = make_pair_frames(break_close=100.25)
        _, frame = run(x, b)
        self.assertEqual(frame.loc[122, "smt_stop_d"], MODULE.MIN_STOP_PCT)
        self.assertEqual(signal_rows(frame), [122, 125])
        self.assertEqual(MODULE.parse_tag(frame.loc[122, "enter_tag"]), 0.008)
        # LL far below the close gives d > 0.03: no signal and the setup is not consumed.
        x, b = make_pair_frames(deep_low_at=115)
        _, frame = run(x, b)
        self.assertEqual(signal_rows(frame), [])

    def test_b_must_close_up(self):
        x, b = make_pair_frames()
        b.loc[122, "close"] = 995.0
        _, frame = run(x, b)
        self.assertNotIn(122, signal_rows(frame))

    def test_x_must_not_make_new_low(self):
        x, b = make_pair_frames()
        x.loc[119:123, "low"] = 90.0
        _, frame = run(x, b)
        self.assertFalse(frame.loc[120:123, "smt_setup"].any())
        self.assertEqual(signal_rows(frame), [])

    def test_zero_volume_gives_no_signal(self):
        x, b = make_pair_frames()
        x["volume"] = 0.0
        _, frame = run(x, b)
        self.assertEqual(signal_rows(frame), [])
        x, b = make_pair_frames()
        x.loc[122, "volume"] = 0.0
        _, frame = run(x, b)
        self.assertNotIn(122, signal_rows(frame))
        self.assertEqual(signal_rows(frame), [125])

    def test_undefined_values_give_no_signal(self):
        x, b = make_pair_frames()
        # No reference data at all.
        _, frame = run(x, b.iloc[0:0])
        self.assertEqual(signal_rows(frame), [])
        # Reference NaN where it is needed at the entry bar.
        b2 = b.copy()
        b2.loc[122, "close"] = np.nan
        _, frame = run(x, b2)
        self.assertNotIn(122, signal_rows(frame))
        # NaN in B's low inside the prior-low window kills the setup.
        b3 = b.copy()
        b3.loc[100, "low"] = np.nan
        _, frame = run(x, b3)
        self.assertEqual(signal_rows(frame), [])
        # Start-up rows (before the 52-bar prior low exists) never signal.
        x4, b4 = make_pair_frames()
        _, frame = run(x4, b4)
        self.assertTrue(frame.loc[:51, "smt_pl_x"].isna().all())
        self.assertFalse(frame.loc[:51, "smt_setup"].any())
        self.assertEqual([r for r in signal_rows(frame) if r < 52], [])

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        x, b = make_pair_frames(n=220)
        n = 126
        _, short = run(x.iloc[:n].reset_index(drop=True), b.iloc[:n].reset_index(drop=True))
        _, full = run(x, b)
        self.assertEqual(signal_rows(short), [r for r in signal_rows(full) if r < n])
        columns = [c for c in short.columns if c not in {"enter_long", "enter_tag"}]
        pd.testing.assert_frame_equal(short[columns], full.loc[: n - 1, columns], check_dtype=False)
        pd.testing.assert_series_equal(
            short["enter_long"].fillna(0), full.loc[: n - 1, "enter_long"].fillna(0), check_dtype=False
        )

    def test_random_walk_has_no_lookahead_and_binary_signals(self):
        rng = np.random.default_rng(7)
        n, k = 900, 300
        dates = pd.date_range(START, periods=n + k, freq="15min")

        def walk(scale):
            close = 100.0 * np.exp(np.cumsum(rng.normal(0, scale, n + k)))
            open_ = np.concatenate([[close[0]], close[:-1]])
            spread = np.abs(rng.normal(0, scale, n + k)) * close
            return pd.DataFrame(
                {
                    "date": dates,
                    "open": open_,
                    "high": np.maximum(open_, close) + spread,
                    "low": np.minimum(open_, close) - spread,
                    "close": close,
                    "volume": 1.0,
                }
            )

        x, b = walk(0.004), walk(0.004)
        _, full = run(x, b)
        _, short = run(x.iloc[:n].reset_index(drop=True), b.iloc[:n].reset_index(drop=True))
        self.assertEqual(signal_rows(short), [r for r in signal_rows(full) if r < n])
        self.assertGreater(len(signal_rows(full)), 0)
        self.assertTrue(set(full["enter_long"].dropna().unique().tolist()).issubset({1}))
        columns = [c for c in short.columns if c not in {"enter_long", "enter_tag"}]
        pd.testing.assert_frame_equal(short[columns], full.loc[: n - 1, columns], check_dtype=False)

    def test_confirm_trade_entry_limits_two_per_utc_day(self):
        strategy = Strategy()
        day = datetime(2026, 1, 5, 3, 0, tzinfo=timezone.utc)
        prior = [
            FakeTrade("smt|0.01", open_date=day),
            FakeTrade("smt|0.01", open_date=day + timedelta(hours=2)),
            FakeTrade("smt|0.01", open_date=day - timedelta(days=1)),
        ]
        persistence = types.ModuleType("freqtrade.persistence")
        persistence.Trade = type("Trade", (), {"get_trades_proxy": staticmethod(lambda **k: prior)})
        with mock.patch.dict(sys.modules, {"freqtrade.persistence": persistence}):
            args = ("ETH/USDT", "limit", 1.0, 100.0, "GTC")
            self.assertFalse(
                strategy.confirm_trade_entry(*args, day + timedelta(hours=5), "smt|0.01", "long")
            )
            # Next UTC day: only the one trade of the previous day, none on this day.
            self.assertTrue(
                strategy.confirm_trade_entry(*args, day + timedelta(days=1), "smt|0.01", "long")
            )
            # One trade only on the fill day -> second allowed.
            prior.pop(1)
            self.assertTrue(
                strategy.confirm_trade_entry(*args, day + timedelta(hours=5), "smt|0.01", "long")
            )
            self.assertFalse(strategy.confirm_trade_entry(*args, day, "other", "long"))

    def test_take_profit_and_time_exit(self):
        strategy = Strategy()
        trade = FakeTrade("smt|0.01")
        opened = trade.open_date_utc
        self.assertEqual(
            strategy.custom_exit("ETH/USDT", trade, opened + timedelta(minutes=15), 101.5, 0.015),
            "take_profit_1_5R",
        )
        self.assertIsNone(
            strategy.custom_exit("ETH/USDT", trade, opened + timedelta(minutes=15), 101.4, 0.0149)
        )
        self.assertIsNone(
            strategy.custom_exit("ETH/USDT", trade, opened + 47 * timedelta(minutes=15), 100.0, 0.0)
        )
        self.assertEqual(
            strategy.custom_exit("ETH/USDT", trade, opened + 48 * timedelta(minutes=15), 100.0, 0.0),
            "time_exit_12h",
        )
        self.assertEqual(
            strategy.custom_exit("ETH/USDT", trade, opened + 48 * timedelta(minutes=15), 99.0, -0.01),
            "time_exit_12h",
        )

    def test_custom_stoploss_is_fixed_below_entry(self):
        strategy = Strategy()
        trade = FakeTrade("smt|0.01", open_rate=100.0)
        when = trade.open_date_utc
        for current_rate in (100.0, 100.8, 99.5):
            value = strategy.custom_stoploss("ETH/USDT", trade, when, current_rate, 0.0)
            self.assertLess(value, 0)
            self.assertAlmostEqual(current_rate * (1 + value), 99.0)
        self.assertLess(strategy.custom_stoploss("ETH/USDT", trade, when, 98.0, -0.02), 0)
        self.assertIsNone(strategy.custom_stoploss("ETH/USDT", FakeTrade("other"), when, 100.0, 0.0))


if __name__ == "__main__":
    unittest.main()
