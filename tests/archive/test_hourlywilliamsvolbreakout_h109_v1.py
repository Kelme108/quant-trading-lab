import importlib.util
import sys
import types
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


# Keep the tests runnable without installing Freqtrade or TA-Lib on the host.
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


ROOT = Path(__file__).parents[2]


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / "_archive" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Strategy = load_strategy(
    "HourlyWilliamsVolBreakout_H109_v1.py", "HourlyWilliamsVolBreakout_H109_v1"
)

START = pd.Timestamp("2024-01-01 00:00", tz="UTC")
BARS_PER_DAY = 96


def bar_index(day: int, hhmm: str) -> int:
    hour, minute = hhmm.split(":")
    return day * BARS_PER_DAY + int(hour) * 4 + int(minute) // 15


def make_frame(days: int = 16, spikes: dict | None = None) -> pd.DataFrame:
    """Flat 100 price; every session has noise 0.001 (low 99.9, high 100.5), so S = 0.002.

    spikes: {bar index: close} sets a close (and a matching high) at that bar.
    """
    n = days * BARS_PER_DAY
    frame = pd.DataFrame(
        {
            "date": pd.date_range(START, periods=n, freq="15min"),
            "open": 100.0,
            "high": 100.5,
            "low": 99.9,
            "close": 100.0,
            "volume": 1.0,
        }
    )
    for index, close in (spikes or {}).items():
        frame.loc[index, "close"] = close
        frame.loc[index, "high"] = max(close, 100.5) + 0.5
    return frame


def run(strategy, frame):
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    return frame


class FakeDp:
    def __init__(self, frame):
        self.frame = frame

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.frame, None


class FakeTrade:
    def __init__(self, open_date_utc, open_rate):
        self.open_date_utc = open_date_utc
        self.open_rate = open_rate


class HourlyWilliamsVolBreakoutH109Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.strategy = Strategy()

    def test_class_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertEqual(Strategy.stoploss, -0.15)
        self.assertTrue(Strategy.use_custom_stoploss)
        self.assertGreaterEqual(Strategy.startup_candle_count, 1100)

    def test_entry_on_first_close_beyond_stretch_in_first_half(self) -> None:
        spike = bar_index(11, "09:00")  # Europe session, first half
        frame = run(self.strategy, make_frame(spikes={spike: 100.5}))
        entries = frame.index[frame["enter_long"] == 1].tolist()
        self.assertEqual(entries, [spike])
        self.assertAlmostEqual(frame.loc[spike, "stretch"], 0.002)
        self.assertEqual(frame.loc[spike, "sess_open"], 100.0)

    def test_only_first_qualifying_bar_signals(self) -> None:
        first = bar_index(11, "09:00")
        second = bar_index(11, "09:15")
        frame = run(self.strategy, make_frame(spikes={first: 100.5, second: 100.6}))
        self.assertEqual(frame.index[frame["enter_long"] == 1].tolist(), [first])

    def test_no_entry_if_first_qualifying_bar_in_second_half(self) -> None:
        late = bar_index(11, "11:00")  # Europe second half (first half ends 10:30)
        later_first_half = bar_index(11, "11:15")
        frame = run(self.strategy, make_frame(spikes={late: 100.5, later_first_half: 100.5}))
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_last_first_half_bars_of_each_session(self) -> None:
        for hhmm in ("03:45", "10:30", "18:30"):
            index = bar_index(11, hhmm)
            frame = run(self.strategy, make_frame(spikes={index: 100.5}))
            self.assertEqual(frame.index[frame["enter_long"] == 1].tolist(), [index], hhmm)
        for hhmm in ("04:00", "10:45", "18:45"):
            index = bar_index(11, hhmm)
            frame = run(self.strategy, make_frame(spikes={index: 100.5}))
            self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0, hhmm)

    def test_one_signal_per_session_three_sessions_a_day(self) -> None:
        spikes = {
            bar_index(11, "01:00"): 100.5,
            bar_index(11, "08:30"): 100.5,
            bar_index(11, "14:00"): 100.5,
            bar_index(11, "14:15"): 100.5,
        }
        frame = run(self.strategy, make_frame(spikes=spikes))
        self.assertEqual(
            frame.index[frame["enter_long"] == 1].tolist(),
            [bar_index(11, "01:00"), bar_index(11, "08:30"), bar_index(11, "14:00")],
        )

    def test_no_trade_if_a_prior_session_is_missing_a_bar(self) -> None:
        spike = bar_index(11, "09:00")
        full = make_frame(spikes={spike: 100.5})
        # Remove one Europe bar on day 5 (one of the 10 prior Europe sessions).
        reduced = full.drop(index=bar_index(5, "09:00")).reset_index(drop=True)
        frame = run(self.strategy, reduced)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        # A missing bar in an Asia session does not affect Europe.
        other = full.drop(index=bar_index(5, "01:00")).reset_index(drop=True)
        frame = run(self.strategy, other)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 1)

    def test_no_trade_if_first_bar_of_current_session_missing(self) -> None:
        spike = bar_index(11, "09:00")
        full = make_frame(spikes={spike: 100.5})
        reduced = full.drop(index=bar_index(11, "08:00")).reset_index(drop=True)
        frame = run(self.strategy, reduced)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_no_trade_if_stretch_not_positive(self) -> None:
        frame = make_frame()
        frame["high"] = 100.0  # open-to-high is zero, so noise is zero
        frame.loc[bar_index(11, "09:00"), ["high", "close"]] = 101.0
        frame = run(self.strategy, frame)
        self.assertTrue(pd.isna(frame.loc[bar_index(11, "09:00"), "stretch"]))
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_signal_columns_are_binary(self) -> None:
        spike = bar_index(11, "09:00")
        frame = run(self.strategy, make_frame(spikes={spike: 100.5}))
        for column in ("enter_long", "exit_long"):
            values = frame[column].dropna().unique().tolist()
            self.assertTrue(len(values) > 0)
            self.assertTrue(set(values).issubset({1}))

    def test_exit_signal_on_last_bar_of_each_session(self) -> None:
        frame = run(self.strategy, make_frame())
        exits = frame.index[frame["exit_long"] == 1].tolist()
        for day in range(16):
            for hhmm in ("07:45", "13:15", "23:45"):
                self.assertIn(bar_index(day, hhmm), exits)
        self.assertEqual(len(exits), 16 * 3)

    def test_zero_volume_gives_no_signal(self) -> None:
        spike = bar_index(11, "09:00")
        frame = make_frame(spikes={spike: 100.5})
        frame["volume"] = 0.0
        frame = run(self.strategy, frame)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame["exit_long"].fillna(0).sum()), 0)

        frame = make_frame(spikes={spike: 100.5})
        frame.loc[spike, "volume"] = 0.0
        frame.loc[bar_index(11, "13:15"), "volume"] = 0.0
        frame = run(self.strategy, frame)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)
        self.assertNotIn(bar_index(11, "13:15"), frame.index[frame["exit_long"] == 1].tolist())

    def test_undefined_startup_values_give_no_signal(self) -> None:
        # A rising series with big moves: nothing can trade before 10 prior same-type sessions exist.
        n = 10 * BARS_PER_DAY
        prices = 100.0 + np.arange(n) * 0.5
        frame = pd.DataFrame(
            {
                "date": pd.date_range(START, periods=n, freq="15min"),
                "open": prices,
                "high": prices * 1.01,
                "low": prices * 0.99,
                "close": prices,
                "volume": 1.0,
            }
        )
        frame = run(self.strategy, frame)
        self.assertTrue(frame["stretch"].isna().all())
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_signals_do_not_change_when_future_candles_are_appended(self) -> None:
        spike = bar_index(10, "09:00")
        full = make_frame(days=16, spikes={spike: 100.5})
        # Make the future different from the flat past.
        full.loc[1250:, ["open", "high", "low", "close"]] = 500.0
        first_n, total = 1100, 1400
        short = run(self.strategy, full.iloc[:first_n].copy().reset_index(drop=True))
        long = run(self.strategy, full.iloc[:total].copy().reset_index(drop=True))
        columns = ["sess_open", "stretch", "breakout_level", "enter_long", "exit_long"]
        self.assertEqual(int(short["enter_long"].fillna(0).sum()), 1)
        pd.testing.assert_frame_equal(
            short.loc[: first_n - 1, columns].reset_index(drop=True),
            long.loc[: first_n - 1, columns].reset_index(drop=True),
            check_dtype=False,
        )

    def test_custom_exit_time_exit_at_session_end(self) -> None:
        cases = [
            ("2024-03-01 04:00", "2024-03-01 07:45", "2024-03-01 08:00"),
            ("2024-03-01 08:30", "2024-03-01 13:15", "2024-03-01 13:30"),
            ("2024-03-01 14:00", "2024-03-01 23:45", "2024-03-02 00:00"),
        ]
        for opened, before, at_end in cases:
            trade = FakeTrade(pd.Timestamp(opened, tz="UTC"), 100.0)
            self.assertIsNone(
                self.strategy.custom_exit("X/USDT", trade, pd.Timestamp(before, tz="UTC"), 101.0, 0.01)
            )
            self.assertEqual(
                self.strategy.custom_exit("X/USDT", trade, pd.Timestamp(at_end, tz="UTC"), 101.0, 0.01),
                "session_end",
            )

    def test_no_take_profit(self) -> None:
        trade = FakeTrade(pd.Timestamp("2024-03-01 08:30", tz="UTC"), 100.0)
        self.assertIsNone(
            self.strategy.custom_exit("X/USDT", trade, pd.Timestamp("2024-03-01 09:00", tz="UTC"), 150.0, 0.5)
        )

    def _stop_setup(self, close: float, session_open: float = 100.0):
        spike = bar_index(11, "09:00")
        frame = make_frame(spikes={spike: close})
        frame = run(self.strategy, frame)
        self.strategy.dp = FakeDp(frame)
        opened = frame.loc[spike, "date"] + pd.Timedelta(minutes=15)
        return opened

    def test_custom_stoploss_is_fixed_level_at_least_one_percent(self) -> None:
        opened = self._stop_setup(100.5)
        entry = 100.5
        trade = FakeTrade(opened, entry)
        level = min(100.0 * (1 - 0.002), 0.99 * entry)
        for current in (100.5, 102.0, 99.8):
            result = self.strategy.custom_stoploss(
                "X/USDT", trade, opened, current, current / entry - 1
            )
            self.assertAlmostEqual(current * (1 + result), level, places=9)
        self.assertAlmostEqual(level, 0.99 * entry)

    def test_custom_stoploss_uses_opposite_stretch_when_wider(self) -> None:
        opened = self._stop_setup(100.5)
        self.strategy.dp.frame.loc[:, "stretch"] = 0.05
        trade = FakeTrade(opened, 100.5)
        result = self.strategy.custom_stoploss("X/USDT", trade, opened, 100.5, 0.0)
        self.assertAlmostEqual(100.5 * (1 + result), 95.0, places=9)

    def test_custom_stoploss_capped_by_backstop(self) -> None:
        opened = self._stop_setup(100.5)
        self.strategy.dp.frame.loc[:, "stretch"] = 0.5
        trade = FakeTrade(opened, 100.5)
        result = self.strategy.custom_stoploss("X/USDT", trade, opened, 100.5, 0.0)
        self.assertAlmostEqual(100.5 * (1 + result), 100.5 * 0.85, places=9)

    def test_custom_stoploss_falls_back_to_backstop_without_data(self) -> None:
        opened = self._stop_setup(100.5)
        self.strategy.dp.frame = self.strategy.dp.frame.iloc[0:0]
        trade = FakeTrade(opened, 100.5)
        self.assertEqual(
            self.strategy.custom_stoploss("X/USDT", trade, opened, 100.5, 0.0), Strategy.stoploss
        )


if __name__ == "__main__":
    unittest.main()
