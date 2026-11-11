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

ROOT = Path(__file__).parents[1]
NAME = "MACDBollingerTurn_H111_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load()
Strategy = getattr(MODULE, NAME)

T0 = datetime(2026, 1, 5, 10, 0, tzinfo=timezone.utc)


def make_frame(n: int = 3000, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0, 0.006, n)
    close = 100.0 * np.exp(np.cumsum(returns))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.002, n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.002, n)))
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": np.ones(n)}
    )


def run(strategy, frame):
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


class FakeTrade:
    def __init__(self, open_rate=100.0, d_tp=0.012, d_sl=0.008, opened=T0, tag=None):
        self.open_rate = open_rate
        self.open_date_utc = opened
        self.enter_tag = tag if tag is not None else MODULE.make_tag(d_tp, d_sl)


class MACDBollingerTurnTests(unittest.TestCase):
    def setUp(self):
        self.strategy = Strategy()

    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 500)
        self.assertEqual(
            self.strategy.protections,
            [{"method": "CooldownPeriod", "stop_duration_candles": 1}],
        )

    def test_signals_exist_and_are_binary(self):
        frame = run(self.strategy, make_frame())
        self.assertGreater(int(frame["enter_long"].fillna(0).sum()), 0)
        self.assertTrue(set(frame["enter_long"].dropna().unique().tolist()).issubset({1}))
        if "exit_long" in frame:
            self.assertTrue(set(frame["exit_long"].dropna().unique().tolist()).issubset({1}))

    def test_entry_conditions_hold_on_signal_rows(self):
        frame = run(self.strategy, make_frame())
        rows = frame[frame["enter_long"] == 1]
        self.assertFalse(rows.empty)
        self.assertTrue((rows["bb_pctb"] < 0.2).all())
        self.assertTrue((rows["macd_hist"] > 0).all())
        self.assertTrue((rows["macd_hist_prev"] <= 0).all())
        self.assertTrue((rows["macd"] < 0).all())
        self.assertTrue((rows["atrp"] >= 0.004).all())
        for _, row in rows.iterrows():
            self.assertEqual(
                row["enter_tag"], MODULE.make_tag(row["d_tp"], row["d_sl"])
            )

    def test_barrier_distances_have_floors(self):
        frame = run(self.strategy, make_frame()).dropna(subset=["std_pct"])
        self.assertTrue((frame["d_tp"] >= 0.012).all())
        self.assertTrue((frame["d_sl"] >= 0.008).all())
        np.testing.assert_allclose(
            frame["d_tp"], np.maximum(1.5 * frame["std_pct"], 0.012)
        )
        np.testing.assert_allclose(
            frame["d_sl"], np.maximum(0.75 * frame["std_pct"], 0.008)
        )

    def test_zero_volume_gives_no_signal(self):
        base = make_frame()
        signalled = run(self.strategy, base)
        index = int(signalled.index[signalled["enter_long"] == 1][0])
        frame = base.copy()
        frame.loc[index, "volume"] = 0.0
        result = run(self.strategy, frame)
        self.assertNotEqual(result.get("enter_long", pd.Series(0, index=result.index)).loc[index], 1)
        frame["volume"] = 0.0
        result = run(self.strategy, frame)
        self.assertEqual(
            int(result.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0
        )

    def test_startup_values_are_undefined_and_give_no_signal(self):
        frame = run(self.strategy, make_frame())
        self.assertTrue(frame["bb_pctb"].iloc[:99].isna().all())
        self.assertEqual(
            int(frame["enter_long"].iloc[: Strategy.startup_candle_count].fillna(0).sum()), 0
        )
        short = run(self.strategy, make_frame(n=450))
        self.assertEqual(
            int(short.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0
        )

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        full = make_frame(n=3400)
        first = run(self.strategy, full.iloc[:3000])
        later = run(self.strategy, full)
        columns = [c for c in first.columns if c != "bar_index"]
        pd.testing.assert_frame_equal(
            first[columns], later.loc[:2999, columns], check_dtype=False
        )
        self.assertGreater(int(first["enter_long"].fillna(0).sum()), 0)

    def test_take_profit_exit(self):
        trade = FakeTrade()
        now = T0 + timedelta(minutes=30)
        self.assertIsNone(self.strategy.custom_exit("X", trade, now, 101.1, 0.01))
        self.assertEqual(
            self.strategy.custom_exit("X", trade, now, 101.2, 0.011), "take_profit"
        )

    def test_take_profit_uses_frozen_distance(self):
        trade = FakeTrade(d_tp=0.03)
        now = T0 + timedelta(minutes=30)
        self.assertIsNone(self.strategy.custom_exit("X", trade, now, 102.0, 0.019))
        self.assertEqual(
            self.strategy.custom_exit("X", trade, now, 103.0, 0.029), "take_profit"
        )

    def test_time_exit_after_24_bars(self):
        trade = FakeTrade()
        before = T0 + timedelta(hours=6) - timedelta(minutes=1)
        self.assertIsNone(self.strategy.custom_exit("X", trade, before, 100.0, 0.0))
        at = T0 + timedelta(hours=6)
        self.assertEqual(self.strategy.custom_exit("X", trade, at, 100.0, 0.0), "time_exit_6h")

    def test_custom_stoploss_is_frozen_at_entry_price(self):
        trade = FakeTrade(d_sl=0.01)
        now = T0 + timedelta(minutes=15)
        for profit in (-0.001, 0.0, 0.005):
            relative = self.strategy.custom_stoploss("X", trade, now, 100.0, profit)
            stop_price = 100.0 * (1 + profit) / (1 + profit)  # current price scale cancels
            self.assertGreater(relative, 0)
            # stop price relative to the open price must be 1 - dSL for any current profit
            current_price_ratio = 1 + profit
            self.assertAlmostEqual(current_price_ratio * (1 - relative), 0.99, places=9)
            del stop_price
        self.assertIsNone(
            self.strategy.custom_stoploss("X", FakeTrade(tag="other"), now, 100.0, 0.0)
        )

    def test_max_four_entries_per_utc_day(self):
        day = datetime(2026, 1, 6, 12, 0, tzinfo=timezone.utc)
        tag = MODULE.make_tag(0.012, 0.008)

        def trades(count, other_day=False):
            opened = day - timedelta(days=1) if other_day else day - timedelta(hours=2)
            return [FakeTrade(opened=opened) for _ in range(count)]

        class Fake:
            items = []

            @staticmethod
            def get_trades_proxy(**kwargs):
                return Fake.items

        with mock.patch.object(MODULE, "Trade", Fake):
            Fake.items = trades(3)
            self.assertTrue(
                self.strategy.confirm_trade_entry("X", "limit", 1, 1, "GTC", day, tag, "long")
            )
            Fake.items = trades(4)
            self.assertFalse(
                self.strategy.confirm_trade_entry("X", "limit", 1, 1, "GTC", day, tag, "long")
            )
            Fake.items = trades(4, other_day=True)
            self.assertTrue(
                self.strategy.confirm_trade_entry("X", "limit", 1, 1, "GTC", day, tag, "long")
            )
            self.assertFalse(
                self.strategy.confirm_trade_entry("X", "limit", 1, 1, "GTC", day, "foreign", "long")
            )


if __name__ == "__main__":
    unittest.main()
