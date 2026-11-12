import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd


# Keep the tests runnable without installing Freqtrade or TA-Lib on the host.
freqtrade = types.ModuleType("freqtrade")
strategy_module = types.ModuleType("freqtrade.strategy")
strategy_module.IStrategy = object
freqtrade.strategy = strategy_module
sys.modules.setdefault("freqtrade", freqtrade)
sys.modules.setdefault("freqtrade.strategy", strategy_module)

persistence_module = types.ModuleType("freqtrade.persistence")


class _TradeStub:
    @staticmethod
    def get_trades_proxy(**kwargs):
        return []


persistence_module.Trade = _TradeStub
sys.modules.setdefault("freqtrade.persistence", persistence_module)

talib = types.ModuleType("talib")
talib_abstract = types.ModuleType("talib.abstract")
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)


ROOT = Path(__file__).parents[1]
STRATEGY_FILE = "FairValueGapRetest_H117_v1.py"
CLASS_NAME = "FairValueGapRetest_H117_v1"


def load_module():
    path = ROOT / "user_data" / "strategies" / STRATEGY_FILE
    spec = importlib.util.spec_from_file_location(CLASS_NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()
Strategy = getattr(MODULE, CLASS_NAME)

GAP_K = 40  # displacement bar; the gap is complete at the close of bar 41.
GAP_BOTTOM = 100.1
GAP_TOP = 100.6
ENTRY_TAG = "fvg|100.1"


def make_frame(retest_at=None, kill_at=None, extra_bars=70) -> pd.DataFrame:
    """Flat market, one bullish gap (GL 100.1, GH 100.6, CE 100.35), optional retest / kill bar."""
    rows = []
    for _ in range(GAP_K):
        rows.append((100.0, 100.1, 99.9, 100.0, 10.0))
    rows.append((100.0, 101.6, 100.0, 101.5, 50.0))  # displacement bar k
    rows.append((101.5, 102.2, 100.6, 102.0, 10.0))  # bar k+1
    for _ in range(extra_bars):
        rows.append((101.8, 102.0, 101.5, 101.8, 10.0))
    frame = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"])
    if retest_at is not None:
        frame.loc[retest_at, ["open", "high", "low", "close"]] = [101.8, 102.0, 100.3, 101.0]
    if kill_at is not None:
        frame.loc[kill_at, ["open", "high", "low", "close"]] = [101.8, 102.0, 99.0, 100.0]
    return frame


def run(frame: pd.DataFrame) -> pd.DataFrame:
    strategy = Strategy()
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    return frame


def signal_rows(frame: pd.DataFrame) -> list[int]:
    if "enter_long" not in frame:
        return []
    return frame.index[frame["enter_long"].fillna(0) == 1].tolist()


class FakeTrade:
    def __init__(self, open_rate, open_date, tag=ENTRY_TAG):
        self.open_rate = open_rate
        self.open_date_utc = open_date
        self.enter_tag = tag


T0 = datetime(2026, 1, 5, 10, 0, tzinfo=timezone.utc)


class ContractTests(unittest.TestCase):
    def test_class_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.10)
        self.assertGreaterEqual(Strategy.startup_candle_count, 55)
        self.assertEqual(Strategy.startup_candle_count, 100)


class SignalTests(unittest.TestCase):
    def test_gap_is_detected_once_known(self) -> None:
        frame = run(make_frame())
        self.assertEqual(frame.index[frame["fvg_valid"] == 1].tolist(), [GAP_K + 1])
        self.assertEqual(signal_rows(frame), [])

    def test_retest_signals_once_with_gap_bottom_in_tag(self) -> None:
        base = make_frame(retest_at=45)
        base.loc[50, ["open", "high", "low", "close"]] = [101.8, 102.0, 100.3, 101.0]  # second touch
        frame = run(base)
        self.assertEqual(signal_rows(frame), [45])
        self.assertEqual(frame.loc[45, "enter_tag"], ENTRY_TAG)

    def test_retest_on_first_active_bar_and_expiry(self) -> None:
        # Active on bars k+2..k+33 = 42..73.
        self.assertEqual(signal_rows(run(make_frame(retest_at=42))), [42])
        self.assertEqual(signal_rows(run(make_frame(retest_at=GAP_K + 33))), [GAP_K + 33])
        self.assertEqual(signal_rows(run(make_frame(retest_at=GAP_K + 34))), [])

    def test_close_below_gap_bottom_kills_the_gap(self) -> None:
        self.assertEqual(signal_rows(run(make_frame(kill_at=43, retest_at=47))), [])

    def test_touch_with_close_below_bottom_gives_no_signal(self) -> None:
        self.assertEqual(signal_rows(run(make_frame(kill_at=45))), [])

    def test_newer_gap_replaces_older_without_fallback(self) -> None:
        frame = make_frame(extra_bars=70)
        # A second valid gap (higher) completes at bar 52: bars 50 (displacement) and 51.
        frame.loc[50, ["open", "high", "low", "close", "volume"]] = [101.8, 105.0, 101.8, 104.8, 60.0]
        frame.loc[51, ["open", "high", "low", "close", "volume"]] = [104.8, 106.0, 102.5, 105.5, 10.0]
        frame.loc[52:, ["open", "high", "low", "close"]] = [105.0, 105.5, 104.5, 105.0]
        # A dip to the old gap midpoint that closes above the new gap's bottom (102.0).
        frame.loc[56,["open", "high", "low", "close"]] = [105.0, 105.5, 100.3, 105.0]
        out = run(frame)
        self.assertEqual(out.index[out["fvg_valid"] == 1].tolist(), [GAP_K + 1, 51])
        # The low touches the old CE (100.35) and also the new CE; the signal belongs to the new gap.
        self.assertEqual(signal_rows(out), [56])
        self.assertEqual(out.loc[56, "enter_tag"], f"fvg|{float(frame.loc[49, 'high'])!r}")

    def test_small_gap_and_low_volume_are_invalid(self) -> None:
        small = make_frame()
        small.loc[GAP_K + 1, "low"] = 100.3  # (100.3-100.1)/102 < 0.003
        self.assertEqual(int(run(small)["fvg_valid"].sum()), 0)
        quiet = make_frame()
        quiet.loc[GAP_K, "volume"] = 19.9  # below 2.0 x mean volume of 10
        self.assertEqual(int(run(quiet)["fvg_valid"].sum()), 0)
        bearish = make_frame()
        bearish.loc[GAP_K, "close"] = 99.95  # close(k) <= open(k)
        self.assertEqual(int(run(bearish)["fvg_valid"].sum()), 0)

    def test_signal_columns_are_binary(self) -> None:
        frame = run(make_frame(retest_at=45))
        self.assertTrue(set(frame["enter_long"].dropna().unique().tolist()).issubset({1}))
        self.assertTrue(set(frame["fvg_signal"].unique().tolist()).issubset({0, 1}))
        if "exit_long" in frame:
            self.assertTrue(set(frame["exit_long"].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_candle_produces_no_signal(self) -> None:
        frame = make_frame(retest_at=45)
        frame.loc[45, "volume"] = 0.0
        self.assertEqual(signal_rows(run(frame)), [])
        all_zero = make_frame(retest_at=45)
        all_zero["volume"] = 0.0
        out = run(all_zero)
        self.assertEqual(signal_rows(out), [])
        self.assertEqual(int(out["fvg_signal"].sum()), 0)

    def test_undefined_startup_values_produce_no_signal(self) -> None:
        # A gap pattern too early for the 20-bar volume mean must not signal.
        rows = [(100.0, 100.1, 99.9, 100.0, 10.0)] * 5
        rows += [(100.0, 101.6, 100.0, 101.5, 50.0), (101.5, 102.2, 100.6, 102.0, 10.0)]
        rows += [(101.8, 102.0, 100.3, 101.0, 10.0)] * 10
        frame = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"])
        out = run(frame)
        self.assertEqual(int(out["fvg_valid"].sum()), 0)
        self.assertEqual(signal_rows(out), [])
        nan_frame = make_frame(retest_at=45)
        nan_frame.loc[44, "low"] = np.nan
        nan_frame.loc[45, "close"] = np.nan
        self.assertEqual(signal_rows(run(nan_frame)), [])
        startup = Strategy.startup_candle_count
        warm = run(make_frame(retest_at=45))
        self.assertEqual(int(warm.iloc[:GAP_K]["fvg_signal"].sum()), 0)
        self.assertLess(startup, 200)

    def test_signal_does_not_change_when_future_candles_are_appended(self) -> None:
        rng = np.random.default_rng(7)
        n, extra = 600, 200
        steps = rng.normal(0, 0.004, n + extra)
        close = 100 * np.exp(np.cumsum(steps))
        open_ = np.concatenate([[100.0], close[:-1]])
        spread = np.abs(rng.normal(0, 0.003, n + extra))
        high = np.maximum(open_, close) * (1 + spread)
        low = np.minimum(open_, close) * (1 - spread)
        volume = rng.uniform(5, 15, n + extra) * np.where(rng.random(n + extra) < 0.1, 4.0, 1.0)
        full = pd.DataFrame(
            {"open": open_, "high": high, "low": low, "close": close, "volume": volume}
        )
        short = run(full.iloc[:n].copy())
        long_ = run(full.copy())
        self.assertGreater(int(long_["fvg_valid"].sum()), 0)
        cols = ["fvg_valid", "fvg_signal", "fvg_gl"]
        pd.testing.assert_frame_equal(
            short[cols].reset_index(drop=True),
            long_[cols].iloc[:n].reset_index(drop=True),
            check_dtype=False,
        )
        self.assertEqual(signal_rows(short), [i for i in signal_rows(long_) if i < n])


class TradeMechanicsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.strategy = Strategy()

    def test_stop_distance_floor_and_gap_based(self) -> None:
        # 0.998 x 100.1 / 101.0 -> d ~ 0.0109 (gap-based); close to GL -> floored at 1%.
        d = MODULE.stop_distance(100.1, 101.0)
        self.assertAlmostEqual(d, 1 - 0.998 * 100.1 / 101.0)
        self.assertEqual(MODULE.stop_distance(100.1, 100.2), 0.01)

    def test_custom_stoploss_is_fixed_price_below_entry(self) -> None:
        trade = FakeTrade(101.0, T0)
        d = MODULE.stop_distance(100.1, 101.0)
        stop_price = 101.0 * (1 - d)
        for rate in (101.0, 102.0, 103.5):
            value = self.strategy.custom_stoploss("BTC/USDT", trade, T0, rate, 0.0)
            self.assertAlmostEqual(rate * (1 + value), stop_price)
        self.assertAlmostEqual(stop_price, min(0.998 * 100.1, 0.99 * 101.0))
        self.assertIsNone(self.strategy.custom_stoploss("BTC/USDT", FakeTrade(101.0, T0, "x"), T0, 101.0, 0.0))

    def test_take_profit_at_two_r(self) -> None:
        trade = FakeTrade(101.0, T0)
        d = MODULE.stop_distance(100.1, 101.0)
        target = 101.0 * (1 + 2 * d)
        now = T0 + timedelta(hours=1)
        self.assertIsNone(self.strategy.custom_exit("BTC/USDT", trade, now, target * 0.999, 0.01))
        self.assertEqual(
            self.strategy.custom_exit("BTC/USDT", trade, now, target, 0.02), "take_profit_2r"
        )
        self.assertEqual(
            self.strategy.custom_exit("BTC/USDT", trade, now, target * 1.01, 0.03), "take_profit_2r"
        )

    def test_time_exit_after_twelve_hours(self) -> None:
        trade = FakeTrade(101.0, T0 + timedelta(seconds=3))
        before = T0 + timedelta(hours=11, minutes=45)
        at = T0 + timedelta(hours=12)
        self.assertIsNone(self.strategy.custom_exit("BTC/USDT", trade, before, 101.0, 0.0))
        self.assertEqual(self.strategy.custom_exit("BTC/USDT", trade, at, 101.0, 0.0), "time_exit_12h")

    def test_foreign_tag_never_exits_by_rule(self) -> None:
        trade = FakeTrade(101.0, T0, tag=None)
        self.assertIsNone(self.strategy.custom_exit("BTC/USDT", trade, T0 + timedelta(hours=20), 200.0, 1.0))

    def test_at_most_four_entries_per_utc_day(self) -> None:
        def trades_for(count, day_start):
            return [FakeTrade(100.0, day_start + timedelta(minutes=15 * i)) for i in range(count)]

        day = datetime(2026, 1, 5, 0, 0, tzinfo=timezone.utc)
        now = datetime(2026, 1, 5, 20, 0, tzinfo=timezone.utc)
        previous_day = trades_for(10, day - timedelta(days=1))

        def confirm(trades):
            with mock.patch.object(MODULE.Trade, "get_trades_proxy", return_value=trades, create=True):
                return self.strategy.confirm_trade_entry(
                    "BTC/USDT", "limit", 1.0, 100.0, "GTC", now, ENTRY_TAG, "long"
                )

        self.assertTrue(confirm(previous_day + trades_for(3, day)))
        self.assertFalse(confirm(previous_day + trades_for(4, day)))
        self.assertFalse(
            self.strategy.confirm_trade_entry(
                "BTC/USDT", "limit", 1.0, 100.0, "GTC", now, "other", "long"
            )
        )


if __name__ == "__main__":
    unittest.main()
