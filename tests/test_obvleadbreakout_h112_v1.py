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
persistence = types.ModuleType("freqtrade.persistence")
freqtrade.strategy = strategy_module
freqtrade.persistence = persistence
sys.modules.setdefault("freqtrade", freqtrade)
sys.modules.setdefault("freqtrade.strategy", strategy_module)
sys.modules.setdefault("freqtrade.persistence", persistence)
_strategy_module = sys.modules["freqtrade.strategy"]
_persistence_module = sys.modules["freqtrade.persistence"]
if not hasattr(_strategy_module, "merge_informative_pair"):
    _strategy_module.merge_informative_pair = lambda *a, **k: a[0]
if not hasattr(_persistence_module, "Trade"):
    _persistence_module.Trade = type("Trade", (), {"get_trades_proxy": staticmethod(lambda **k: [])})

talib = types.ModuleType("talib")
talib_abstract = types.ModuleType("talib.abstract")
talib_abstract.SMA = lambda dataframe, timeperiod: dataframe["close"].rolling(timeperiod).mean()
talib_abstract.RSI = lambda dataframe, timeperiod: pd.Series(50.0, index=dataframe.index)
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)

ROOT = Path(__file__).parents[1]
NAME = "OBVLeadBreakout_H112_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fake_merge_informative_pair(dataframe, informative, timeframe, timeframe_inf, ffill=True):
    """Same visibility as freqtrade: a 1h bar is attached from the end of its hour."""
    inf = informative.copy()
    inf["date"] = inf["date"] + pd.Timedelta(hours=1)
    inf.columns = [f"{column}_{timeframe_inf}" for column in inf.columns]
    inf["date_1h"] = inf["date_1h"].astype(dataframe["date"].dtype)
    merged = pd.merge_asof(
        dataframe.sort_values("date"), inf.sort_values("date_1h"), left_on="date", right_on="date_1h"
    )
    return merged.drop(columns=["date_1h"])


MODULE = load()
MODULE.merge_informative_pair = fake_merge_informative_pair
Strategy = getattr(MODULE, NAME)

SIGNAL_BAR = 301


def make_frame(closes, volumes):
    closes = np.asarray(closes, dtype=float)
    opens = np.concatenate([[closes[0]], closes[:-1]])
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=len(closes), freq="15min", tz="UTC"),
            "open": opens,
            "high": np.maximum(opens, closes) * 1.001,
            "low": np.minimum(opens, closes) * 0.999,
            "close": closes,
            "volume": np.asarray(volumes, dtype=float),
        }
    )


def fixture(extra_closes=(), extra_volumes=()):
    """Slow rise to 103 (OBV climbs), a drop to 101.5 on small volume, then one up bar on big volume (bar 301)."""
    closes = [100.0 + 3.0 * i / 299.0 for i in range(300)]
    volumes = [1.0] * 300
    closes += [101.5, 102.5]
    volumes += [1.0, 10.0]
    closes += [102.5] * 98
    volumes += [1.0] * 98
    closes += list(extra_closes)
    volumes += list(extra_volumes)
    return make_frame(closes, volumes)


def run(strategy, frame):
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    # Freqtrade creates these columns (all zero) when a strategy sets no signal at all.
    for column in ("enter_long", "exit_long"):
        if column not in frame:
            frame[column] = np.nan
    return frame


class FakeTrade:
    def __init__(self, tag, open_rate=102.5, open_date=None):
        self.enter_tag = tag
        self.open_rate = open_rate
        self.open_date_utc = open_date or datetime(2024, 1, 5, 10, 0, tzinfo=timezone.utc)


class OBVLeadBreakoutTests(unittest.TestCase):
    def setUp(self):
        self.strategy = Strategy()

    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.04)
        self.assertGreaterEqual(Strategy.startup_candle_count, 2000)
        self.assertEqual(
            self.strategy.protections,
            [{"method": "CooldownPeriod", "stop_duration_candles": 16}],
        )

    def test_rule_numbers(self):
        self.assertEqual(MODULE.OBV_WINDOW, 192)
        self.assertEqual(MODULE.HIGH_WINDOW, 192)
        self.assertEqual(MODULE.NEAR_HIGH_FRACTION, 0.985)
        self.assertEqual(MODULE.STOP_LOW_WINDOW, 10)
        self.assertEqual(MODULE.MIN_RISK_FRACTION, 0.008)
        self.assertEqual(MODULE.MAX_RISK_FRACTION, 0.03)
        self.assertEqual(MODULE.TARGET_R_MULTIPLE, 1.5)
        self.assertEqual(MODULE.FILTER_EMA_PERIOD, 50)
        self.assertEqual(MODULE.MAX_ENTRIES_PER_UTC_DAY, 3)
        self.assertEqual(MODULE.TIME_EXIT_BARS, 48)

    def test_single_signal_with_stop_and_target_in_tag(self):
        frame = run(self.strategy, fixture())
        entries = frame.index[frame["enter_long"] == 1].tolist()
        self.assertEqual(entries, [SIGNAL_BAR])
        stop, target = MODULE.parse_tag(frame.loc[SIGNAL_BAR, "enter_tag"])
        expected_stop = 101.5 * 0.999
        self.assertAlmostEqual(stop, expected_stop, places=9)
        self.assertAlmostEqual(target, 102.5 + 1.5 * (102.5 - expected_stop), places=9)

    def test_obv_is_raw_cumulative_and_windows_exclude_current_bar(self):
        frame = run(self.strategy, fixture())
        self.assertEqual(frame.loc[299, "obv"], 299.0)
        self.assertEqual(frame.loc[300, "obv"], 298.0)
        self.assertEqual(frame.loc[301, "obv"], 308.0)
        self.assertEqual(frame.loc[301, "obv_max"], 299.0)
        self.assertEqual(frame.loc[300, "hh"], frame.loc[108:299, "high"].max())
        self.assertTrue(pd.isna(frame.loc[191, "obv_max"]))
        self.assertTrue(pd.notna(frame.loc[192, "obv_max"]))

    def test_price_must_stay_below_the_high(self):
        closes = [100.0 + 3.0 * i / 299.0 for i in range(300)] + [101.5, 103.5] + [103.5] * 10
        volumes = [1.0] * 300 + [1.0, 10.0] + [1.0] * 10
        frame = run(self.strategy, make_frame(closes, volumes))
        self.assertTrue(frame.loc[301, "close"] >= frame.loc[301, "hh"])
        self.assertNotEqual(frame.loc[301, "enter_long"], 1)

    def test_risk_band_blocks_small_risk(self):
        # Shallow drop: R/close < 0.8%.
        closes = [100.0 + 3.0 * i / 299.0 for i in range(300)] + [102.7, 102.9] + [102.9] * 10
        volumes = [1.0] * 300 + [1.0, 10.0] + [1.0] * 10
        frame = run(self.strategy, make_frame(closes, volumes))
        risk_fraction = (frame.loc[301, "close"] - frame.loc[301, "l10"]) / frame.loc[301, "close"]
        self.assertLess(risk_fraction, 0.008)
        self.assertNotEqual(frame.loc[301, "enter_long"], 1)

    def test_filter_blocks_entry_in_downtrend(self):
        # Long decline before the pattern: the last completed 1h close is below EMA(50).
        closes = [130.0 - 30.0 * i / 299.0 for i in range(300)]
        volumes = [1.0] * 300
        # price bounces to a local high, dips, then a high-volume up bar; OBV must make a high so
        # make the decline bars light and the last bars heavy.
        volumes = [0.01] * 300
        closes += [99.0, 99.8]
        volumes += [0.01, 10.0]
        closes += [99.8] * 10
        volumes += [1.0] * 10
        frame = run(self.strategy, make_frame(closes, volumes))
        self.assertLess(frame.loc[301, "close_1h"], frame.loc[301, "ema_1h"])
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)

    def test_signal_columns_are_binary(self):
        frame = run(self.strategy, fixture([101.0, 100.0, 99.0], [200.0] * 3))
        for column in ("enter_long", "exit_long"):
            self.assertIn(column, frame)
            self.assertTrue(set(frame[column].dropna().unique().tolist()).issubset({1}))

    def test_early_exit_when_obv_falls_below_48h_low(self):
        frame = run(self.strategy, fixture([101.0, 100.0, 99.0], [200.0] * 3))
        exits = frame.index[frame["exit_long"] == 1].tolist()
        self.assertEqual(exits[0], 400)
        self.assertEqual(frame.loc[400, "obv_min"], 208.0)
        self.assertTrue(all(index >= 400 for index in exits))

    def test_zero_volume_creates_no_signal(self):
        frame = fixture([101.0, 100.0], [200.0, 200.0])
        frame["volume"] = 0.0
        result = run(self.strategy, frame)
        self.assertEqual(int(result.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(result.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

        # A zero-volume candle among otherwise live candles never carries a signal.
        live = fixture([101.0, 100.0], [200.0, 200.0])
        live.loc[SIGNAL_BAR, "volume"] = 0.0
        live.loc[400, "volume"] = 0.0
        result = run(self.strategy, live)
        self.assertNotEqual(result.loc[SIGNAL_BAR, "enter_long"], 1)
        self.assertNotEqual(result.loc[400, "exit_long"], 1)

    def test_undefined_startup_values_create_no_signal(self):
        frame = run(self.strategy, fixture([101.0, 100.0], [200.0, 200.0]))
        # No full 192-bar window yet: indicators are undefined and nothing fires.
        self.assertTrue(frame.loc[:191, "obv_max"].isna().all())
        self.assertTrue(frame.loc[:191, "hh"].isna().all())
        self.assertEqual(int(frame.loc[:191, "enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame.loc[:191, "exit_long"].fillna(0).sum()), 0)
        # 1h EMA(50) is undefined during its first 49 hourly bars.
        self.assertTrue(frame.loc[:150, "ema_1h"].isna().all())
        startup = Strategy.startup_candle_count
        self.assertEqual(int(frame.iloc[:startup]["enter_long"].fillna(0).sum()), 1)  # only the designed bar

    def test_signals_do_not_change_when_future_candles_are_appended(self):
        long_frame = fixture([101.0, 100.0, 99.0, 99.5, 100.5, 101.5], [200.0, 200.0, 200.0, 30.0, 30.0, 30.0])
        n = 330
        short_run = run(self.strategy, long_frame.iloc[:n].reset_index(drop=True))
        long_run = run(self.strategy, long_frame.reset_index(drop=True))
        columns = [c for c in short_run.columns if c not in {"enter_tag", "exit_tag"}]
        pd.testing.assert_frame_equal(
            short_run.loc[: n - 1, columns].fillna(-999.0),
            long_run.loc[: n - 1, columns].fillna(-999.0),
            check_dtype=False,
        )
        self.assertEqual(short_run.loc[SIGNAL_BAR, "enter_long"], 1)
        # Cut in the middle of an hour as well.
        n = 355
        short_run = run(self.strategy, long_frame.iloc[:n].reset_index(drop=True))
        pd.testing.assert_frame_equal(
            short_run.loc[: n - 1, columns].fillna(-999.0),
            long_run.loc[: n - 1, columns].fillna(-999.0),
            check_dtype=False,
        )

    def test_hourly_filter_only_uses_completed_hours(self):
        frame = run(self.strategy, fixture())
        # Bar 301 opens at 75:15 (hour 75); the visible 1h bar is hour 74, whose last 15m close is bar 299.
        self.assertEqual(frame.loc[301, "close_1h"], frame.loc[299, "close"])
        self.assertEqual(frame.loc[300, "close_1h"], frame.loc[299, "close"])

    def test_confirm_trade_entry_limits_three_per_utc_day(self):
        tag = "obvlead|101.0|104.0"
        now = datetime(2024, 1, 5, 12, 15, tzinfo=timezone.utc)

        def trades(*stamps):
            return [FakeTrade(tag, open_date=stamp) for stamp in stamps]

        today = datetime(2024, 1, 5, 1, 0, tzinfo=timezone.utc)
        yesterday = datetime(2024, 1, 4, 23, 45, tzinfo=timezone.utc)
        original = MODULE.Trade
        try:
            MODULE.Trade = type(
                "T", (), {"get_trades_proxy": staticmethod(lambda **k: trades(today, today, yesterday))}
            )
            self.assertTrue(
                self.strategy.confirm_trade_entry("BTC/USDT", "limit", 1, 1, "GTC", now, tag, "long")
            )
            MODULE.Trade = type(
                "T", (), {"get_trades_proxy": staticmethod(lambda **k: trades(today, today, today))}
            )
            self.assertFalse(
                self.strategy.confirm_trade_entry("BTC/USDT", "limit", 1, 1, "GTC", now, tag, "long")
            )
            self.assertFalse(
                self.strategy.confirm_trade_entry("BTC/USDT", "limit", 1, 1, "GTC", now, "other", "long")
            )
        finally:
            MODULE.Trade = original

    def test_stop_is_fixed_price_from_tag(self):
        trade = FakeTrade("obvlead|101.0|104.0")
        value = self.strategy.custom_stoploss("BTC/USDT", trade, trade.open_date_utc, 102.5, 0.0)
        self.assertAlmostEqual(102.5 * (1.0 + value), 101.0, places=9)
        # Later, at a higher price, the absolute stop price is unchanged.
        value = self.strategy.custom_stoploss("BTC/USDT", trade, trade.open_date_utc, 103.5, 0.01)
        self.assertAlmostEqual(103.5 * (1.0 + value), 101.0, places=9)
        # Foreign tag: backstop.
        other = FakeTrade("manual")
        self.assertEqual(
            self.strategy.custom_stoploss("BTC/USDT", other, other.open_date_utc, 102.5, 0.0),
            Strategy.stoploss,
        )

    def test_take_profit_exit(self):
        trade = FakeTrade("obvlead|101.0|104.0", open_rate=102.5)
        ratio = 104.0 / 102.5 - 1.0
        when = trade.open_date_utc + timedelta(minutes=30)
        self.assertIsNone(
            self.strategy.custom_exit("BTC/USDT", trade, when, 103.0, 103.0 / 102.5 - 1.0)
        )
        self.assertEqual(
            self.strategy.custom_exit("BTC/USDT", trade, when, 104.0, ratio),
            "take_profit_1_5r",
        )
        # Target at or below the fill: exit at the first bar.
        low_target = FakeTrade("obvlead|101.0|102.0", open_rate=102.5)
        self.assertEqual(
            self.strategy.custom_exit("BTC/USDT", low_target, when, 102.5, 0.0),
            "take_profit_1_5r",
        )

    def test_time_exit_after_48_bars(self):
        trade = FakeTrade("obvlead|101.0|104.0")
        before = trade.open_date_utc + timedelta(hours=12) - timedelta(minutes=15)
        at = trade.open_date_utc + timedelta(hours=12)
        self.assertIsNone(self.strategy.custom_exit("BTC/USDT", trade, before, 102.5, 0.0))
        self.assertEqual(
            self.strategy.custom_exit("BTC/USDT", trade, at, 102.5, 0.0), "time_exit_12h"
        )


if __name__ == "__main__":
    unittest.main()
