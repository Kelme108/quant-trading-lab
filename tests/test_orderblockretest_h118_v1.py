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
NAME = "OrderBlockRetest_H118_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load()
Strategy = getattr(MODULE, NAME)

D = 60  # displacement bar in the standard scenario


def set_bar(frame, i, o, h, l, c, v=1.0):
    frame.loc[i, ["open", "high", "low", "close", "volume"]] = [o, h, l, c, v]


def make_frame(n=120, d=D, retest=D + 1):
    """Quiet 100-centred market, an order block at d-2, a displacement at d, a retest bar."""
    frame = pd.DataFrame(
        {
            "date": pd.date_range("2025-01-01", periods=n, freq="15min", tz="UTC"),
            "open": 100.0,
            "high": 100.5,
            "low": 99.5,
            "close": 100.0,
            "volume": 1.0,
        }
    )
    set_bar(frame, d - 2, 100.2, 100.5, 99.5, 99.8)  # order block: OL 99.5, OH 100.5, MT 100
    set_bar(frame, d, 100.0, 103.0, 99.8, 102.8)  # displacement
    for i in range(d + 1, n):  # quiet above the mean threshold
        set_bar(frame, i, 102.0, 102.5, 101.5, 102.0)
    if retest is not None:
        set_bar(frame, retest, 102.0, 102.5, 99.9, 101.0)
    return frame


def run(frame):
    strategy = Strategy()
    frame = strategy.populate_indicators(frame.copy(), {})
    return strategy.populate_entry_trend(frame, {})


def signals(frame):
    out = run(frame)
    if "enter_long" not in out:
        return []
    return out.index[out["enter_long"] == 1].tolist()


class FakeTrade:
    def __init__(self, open_rate=102.0, tag="ob|99.5|103.0", opened=None):
        self.open_rate = open_rate
        self.enter_tag = tag
        self.open_date_utc = opened or datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)


class OrderBlockRetestTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertGreaterEqual(Strategy.startup_candle_count, 400)

    def test_atr_is_wilder_seeded_with_mean_of_first_tr(self):
        frame = make_frame()
        atr = MODULE.wilder_atr(
            frame["high"].to_numpy(float), frame["low"].to_numpy(float), frame["close"].to_numpy(float)
        )
        self.assertTrue(np.isnan(atr[:13]).all())
        tr0_13 = [1.0] * 14
        self.assertAlmostEqual(atr[13], np.mean(tr0_13))
        # bar 58 TR = 1.0; bar 60 TR = max(3.2, |103-100|, |99.8-100|) = 3.2
        self.assertAlmostEqual(atr[60], atr[59] + (3.2 - atr[59]) / 14)

    def test_standard_scenario_gives_one_signal_with_tag(self):
        out = run(make_frame())
        self.assertEqual(out.index[out["enter_long"] == 1].tolist(), [D + 1])
        self.assertEqual(out.loc[D + 1, "enter_tag"], "ob|99.5|103.0")
        self.assertEqual(out.loc[D, "ob_signal"], 0)  # the displacement bar gives no entry

    def test_signal_columns_are_binary(self):
        out = run(make_frame())
        self.assertTrue(set(out["enter_long"].dropna().unique().tolist()).issubset({1}))
        self.assertTrue(set(out["ob_signal"].unique().tolist()).issubset({0, 1}))
        self.assertNotIn("exit_long", out)

    def test_zero_volume_gives_no_signal(self):
        frame = make_frame()
        frame["volume"] = 0.0
        self.assertEqual(signals(frame), [])
        frame = make_frame()
        frame.loc[D + 1, "volume"] = 0.0
        self.assertNotIn(D + 1, signals(frame))

    def test_undefined_startup_values_give_no_signal(self):
        frame = make_frame(n=40, d=12, retest=13)
        out = run(frame)
        self.assertTrue(out["atr"].iloc[:13].isna().all())
        self.assertEqual(signals(frame), [])

    def test_all_nan_prices_give_no_signal(self):
        frame = make_frame()
        frame.loc[D + 1, ["open", "high", "low", "close"]] = np.nan
        self.assertEqual(signals(frame), [])

    def test_no_order_block_means_no_setup(self):
        frame = make_frame()
        set_bar(frame, D - 2, 99.8, 100.5, 99.5, 100.2)  # up candle
        self.assertEqual(signals(frame), [])

    def test_order_block_search_is_limited_to_five_bars(self):
        frame = make_frame()
        set_bar(frame, D - 2, 100.0, 100.5, 99.5, 100.0)
        set_bar(frame, D - 6, 100.2, 100.5, 99.5, 99.8)  # down candle, 6 bars before D
        self.assertEqual(signals(frame), [])
        set_bar(frame, D - 5, 100.2, 100.5, 99.5, 99.8)  # now 5 bars before D
        self.assertEqual(signals(frame), [D + 1])

    def test_displacement_conditions_are_all_required(self):
        # (1) no structure break
        frame = make_frame()
        set_bar(frame, D - 10, 100.0, 103.5, 99.5, 100.0)
        self.assertEqual(signals(frame), [])
        # (2) range below 1.5 ATR
        frame = make_frame()
        set_bar(frame, D, 100.0, 101.2, 99.9, 101.1)
        self.assertEqual(signals(frame), [])
        # (3) close in the lower part of the bar
        frame = make_frame()
        set_bar(frame, D, 100.0, 103.0, 99.8, 101.5)
        self.assertEqual(signals(frame), [])

    def test_retest_must_reach_mean_threshold(self):
        frame = make_frame()
        set_bar(frame, D + 1, 102.0, 102.5, 100.1, 101.0)  # low above MT = 100
        self.assertEqual(signals(frame), [])

    def test_close_below_zone_low_invalidates(self):
        frame = make_frame(retest=None)
        set_bar(frame, D + 1, 102.0, 102.0, 99.0, 99.3)  # close < OL = 99.5
        set_bar(frame, D + 2, 100.0, 102.0, 99.9, 101.0)  # would be a valid retest
        self.assertEqual(signals(frame), [])

    def test_close_not_above_zone_low_gives_no_signal(self):
        frame = make_frame()
        set_bar(frame, D + 1, 102.0, 102.5, 99.0, 99.5)  # close == OL: not > OL, not < OL
        self.assertEqual(signals(frame), [])

    def test_setup_is_consumed_by_first_qualifying_bar(self):
        frame = make_frame()
        set_bar(frame, D + 2, 102.0, 102.5, 99.9, 101.0)  # second qualifying bar
        self.assertEqual(signals(frame), [D + 1])

    def test_retest_later_in_window_signals(self):
        frame = make_frame(retest=None)
        set_bar(frame, D + 3, 102.0, 102.5, 99.9, 101.0)
        self.assertEqual(signals(frame), [D + 3])

    def test_setup_expires_after_32_bars(self):
        frame = make_frame(retest=D + 32)
        self.assertEqual(signals(frame), [D + 32])
        frame = make_frame(retest=D + 33)
        self.assertEqual(signals(frame), [])

    def test_activity_filter(self):
        frame = make_frame(n=120)
        frame[["open", "high", "low", "close"]] = frame[["open", "high", "low", "close"]] * 1000.0
        # same relative shape: ATR/close is unchanged, so still a signal
        self.assertEqual(signals(frame), [D + 1])
        # flatten the whole market: ATR/close drops under 0.4% while the displacement stays valid
        frame = make_frame()
        for i in range(0, 120):
            if i in (D - 2, D, D + 1):
                continue
            o = frame.loc[i, "open"]
            frame.loc[i, ["high", "low"]] = [o + 0.05, o - 0.05]
        set_bar(frame, D - 2, 100.1, 100.15, 99.95, 99.98)
        set_bar(frame, D, 100.0, 100.4, 99.99, 100.39)
        set_bar(frame, D + 1, 100.3, 100.35, 100.0, 100.2)
        out = run(frame)
        self.assertGreater(out.loc[D, "high"] - out.loc[D, "low"], 1.5 * out.loc[D - 1, "atr"])
        self.assertLess(out.loc[D + 1, "atr"] / out.loc[D + 1, "close"], 0.004)
        self.assertEqual(signals(frame), [])

    def test_new_displacement_replaces_older_setup(self):
        def build(retest_bar):
            frame = make_frame(retest=None)
            # second displacement at D+10 with its own order block at D+8 (OL 101.4, MT 101.9)
            set_bar(frame, D + 8, 102.2, 102.4, 101.4, 101.6)
            set_bar(frame, D + 10, 102.0, 106.0, 101.8, 105.8)
            for i in range(D + 11, len(frame)):
                set_bar(frame, i, 105.0, 105.5, 104.5, 105.0)
            set_bar(frame, D + 12, *retest_bar)
            return frame

        # fits the old zone (low <= 100, close > 99.5) but closes below the new zone low: no signal
        self.assertEqual(signals(build((105.0, 105.2, 99.9, 100.5))), [])
        # retest of the new block's mean threshold with a close above its low signals
        out = run(build((105.0, 105.2, 101.8, 104.0)))
        self.assertEqual(out.index[out["enter_long"] == 1].tolist(), [D + 12])
        self.assertEqual(out.loc[D + 12, "enter_tag"], "ob|101.4|106.0")

    def test_displacement_without_order_block_leaves_setup_untouched(self):
        frame = make_frame(retest=None)
        # a displacement at D+10 with no down candle in D+5..D+9 (all quiet bars close == open)
        set_bar(frame, D + 10, 102.0, 106.0, 101.8, 105.8)
        set_bar(frame, D + 12, 105.0, 105.2, 99.9, 104.0)
        out = run(frame)
        self.assertEqual(out.index[out["enter_long"] == 1].tolist(), [D + 12])
        self.assertEqual(out.loc[D + 12, "enter_tag"], "ob|99.5|106.0")

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        rng = np.random.default_rng(7)
        frame = make_frame(n=160)
        noise = rng.normal(0, 0.05, size=160)
        for column in ("open", "close"):
            frame[column] = frame[column] + noise * (np.arange(160) > 90)
        frame["high"] = frame[["open", "close", "high"]].max(axis=1)
        frame["low"] = frame[["open", "close", "low"]].min(axis=1)
        short = run(frame.iloc[:75].copy())
        long = run(frame.copy())
        columns = ["atr", "ob_signal", "ob_low", "ob_high_since_d"]
        pd.testing.assert_frame_equal(
            short[columns].reset_index(drop=True),
            long[columns].iloc[:75].reset_index(drop=True),
            check_dtype=False,
        )
        self.assertEqual(short["enter_tag"].dropna().tolist(), long["enter_tag"].iloc[:75].dropna().tolist())
        self.assertEqual(int(short["ob_signal"].sum()), 1)

    # ---- trade hooks -------------------------------------------------

    def test_stop_distance_and_target_distance(self):
        self.assertAlmostEqual(MODULE.stop_distance(99.5, 102.0), 1 - 0.998 * 99.5 / 102.0)
        self.assertAlmostEqual(MODULE.stop_distance(101.9, 102.0), 0.01)  # floor 1%
        self.assertAlmostEqual(MODULE.target_distance(105.0, 102.0), 105.0 / 102.0 - 1)
        self.assertAlmostEqual(MODULE.target_distance(102.5, 102.0), 0.015)  # floor 1.5%

    def test_custom_stoploss_is_a_fixed_price_below_entry(self):
        strategy = Strategy()
        trade = FakeTrade(open_rate=102.0, tag="ob|99.5|103.0")
        stop_price = 102.0 * (1 - max(1 - 0.998 * 99.5 / 102.0, 0.01))
        self.assertAlmostEqual(stop_price, min(0.998 * 99.5, 0.99 * 102.0))
        for rate in (102.0, 103.0, 101.0):
            value = strategy.custom_stoploss("BTC/USDT", trade, trade.open_date_utc, rate, 0.0)
            self.assertLess(value, 0)
            self.assertAlmostEqual(rate * (1 + value), stop_price)
        self.assertLess(strategy.custom_stoploss("BTC/USDT", trade, trade.open_date_utc, 90.0, -0.1), 0)

    def test_custom_stoploss_floor_one_percent(self):
        strategy = Strategy()
        trade = FakeTrade(open_rate=100.0, tag="ob|100.0|101.0")  # 0.998 x OL / E = 0.998 -> 0.2%
        value = strategy.custom_stoploss("BTC/USDT", trade, trade.open_date_utc, 100.0, 0.0)
        self.assertAlmostEqual(value, -0.01)

    def test_custom_stoploss_ignores_foreign_tags(self):
        trade = FakeTrade(tag="something")
        self.assertIsNone(Strategy().custom_stoploss("BTC/USDT", trade, trade.open_date_utc, 102.0, 0.0))

    def test_take_profit_at_displacement_high(self):
        strategy = Strategy()
        trade = FakeTrade(open_rate=100.0, tag="ob|99.0|103.0")  # target 103
        now = trade.open_date_utc + timedelta(hours=1)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, now, 102.9, 0.029))
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade, now, 103.0, 0.03), "take_profit_displacement_high"
        )
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade, now, 104.0, 0.04), "take_profit_displacement_high"
        )

    def test_take_profit_floor_when_displacement_high_is_close(self):
        strategy = Strategy()
        trade = FakeTrade(open_rate=100.0, tag="ob|99.0|100.5")  # target max(100.5, 101.5) = 101.5
        now = trade.open_date_utc + timedelta(hours=1)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, now, 101.4, 0.014))
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade, now, 101.5, 0.015), "take_profit_displacement_high"
        )

    def test_time_exit_after_48_bars(self):
        strategy = Strategy()
        trade = FakeTrade(open_rate=100.0, tag="ob|99.0|103.0")
        before = trade.open_date_utc + timedelta(hours=11, minutes=45)
        after = trade.open_date_utc + timedelta(hours=12)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, before, 100.5, 0.005))
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, after, 100.5, 0.005), "time_exit_12h")

    def test_daily_entry_limit_counts_fills_per_utc_day(self):
        strategy = Strategy()
        day = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)

        def trades(count_today, count_other):
            items = [FakeTrade(opened=day.replace(hour=1 + i)) for i in range(count_today)]
            items += [FakeTrade(opened=day - timedelta(days=1, hours=i)) for i in range(count_other)]
            return items

        persistence = types.ModuleType("freqtrade.persistence")
        for count_today, expected in ((3, True), (4, False)):
            persistence.Trade = type(
                "Trade", (), {"get_trades_proxy": staticmethod(lambda pair=None, c=count_today: trades(c, 5))}
            )
            with mock.patch.dict(sys.modules, {"freqtrade.persistence": persistence}):
                result = strategy.confirm_trade_entry(
                    "BTC/USDT", "limit", 1.0, 100.0, "GTC", day, "ob|99.5|103.0", "long"
                )
            self.assertEqual(result, expected)
        self.assertFalse(
            strategy.confirm_trade_entry("BTC/USDT", "limit", 1.0, 100.0, "GTC", day, "other", "long")
        )


if __name__ == "__main__":
    unittest.main()
