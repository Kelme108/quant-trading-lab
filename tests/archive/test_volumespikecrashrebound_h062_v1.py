import importlib.util
import math
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
FILENAME = "VolumeSpikeCrashRebound_H062_v1.py"
CLASS_NAME = "VolumeSpikeCrashRebound_H062_v1"


def load_module():
    path = ROOT / "user_data" / "strategies" / "_archive" / FILENAME
    spec = importlib.util.spec_from_file_location(CLASS_NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()
Strategy = MODULE.VolumeSpikeCrashRebound_H062_v1
START = datetime(2024, 1, 1, tzinfo=timezone.utc)
BAR = timedelta(minutes=15)
SHOCK = 750


def make_frame(n: int, shock: int | None = SHOCK) -> pd.DataFrame:
    closes = [100.0 * (1.0 + 0.001 * math.sin(i * 0.7)) for i in range(n)]
    opens = [closes[i - 1] if i > 0 else closes[0] for i in range(n)]
    volumes = [1.0 + 0.1 * (i % 5) for i in range(n)]
    if shock is not None and shock < n:
        opens[shock] = 100.0
        closes[shock] = 98.0
        volumes[shock] = 10.0
        for j in range(shock + 1, n):
            closes[j] = 98.0 + 0.1 * math.sin(j)
            opens[j] = closes[j - 1]
    return pd.DataFrame(
        {
            "date": pd.date_range(START, periods=n, freq="15min", tz="UTC"),
            "open": opens,
            "high": [max(o, c) * 1.001 for o, c in zip(opens, closes)],
            "low": [min(o, c) * 0.999 for o, c in zip(opens, closes)],
            "close": closes,
            "volume": volumes,
        }
    )


def run(frame: pd.DataFrame) -> pd.DataFrame:
    strategy = Strategy()
    frame = strategy.populate_indicators(frame, {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    return frame


class _DP:
    def __init__(self, frame):
        self.frame = frame

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.frame, None


class _Trade:
    def __init__(self, tag, open_date):
        self.enter_tag = tag
        self.open_date_utc = open_date


class VolumeSpikeCrashReboundH062Tests(unittest.TestCase):
    def test_class_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.03)
        self.assertGreaterEqual(Strategy.startup_candle_count, 700)
        self.assertEqual(
            Strategy().protections,
            [{"method": "CooldownPeriod", "stop_duration_candles": 8}],
        )

    def test_indicators_exclude_current_bar(self) -> None:
        frame = run(make_frame(800))
        ret = frame["close"] / frame["close"].shift(1) - 1.0
        t = 700
        self.assertAlmostEqual(frame.loc[t, "sigma"], ret.iloc[t - 672:t].std(ddof=1))
        self.assertAlmostEqual(frame.loc[t, "vmed"], frame["volume"].iloc[t - 96:t].median())
        self.assertTrue(pd.isna(frame.loc[672, "sigma"]))
        self.assertFalse(pd.isna(frame.loc[673, "sigma"]))

    def test_shock_bar_signals_with_tag(self) -> None:
        frame = run(make_frame(800))
        entries = frame.index[frame.get("enter_long", pd.Series(dtype=float)) == 1].tolist()
        self.assertEqual(entries, [SHOCK])
        target, floor = MODULE.parse_tag(frame.loc[SHOCK, "enter_tag"])
        self.assertEqual(target, 100.0)
        self.assertAlmostEqual(floor, 0.99 * frame.loc[SHOCK, "low"])

    def test_small_drop_below_min_threshold_does_not_signal(self) -> None:
        frame = make_frame(800)
        frame.loc[SHOCK, "close"] = 100.0 * (1 - 0.0079)
        frame = run(frame)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_low_volume_shock_does_not_signal(self) -> None:
        frame = make_frame(800)
        frame.loc[SHOCK, "volume"] = 2.0
        frame = run(frame)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_signal_columns_are_binary(self) -> None:
        frame = run(make_frame(800))
        for column in ("enter_long", "exit_long"):
            if column in frame:
                self.assertTrue(set(frame[column].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_produces_no_signal(self) -> None:
        frame = make_frame(800)
        frame.loc[SHOCK, "volume"] = 0.0
        frame = run(frame)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        frame = make_frame(800)
        frame["volume"] = 0.0
        frame = run(frame)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(frame.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_startup_nan_produces_no_signal(self) -> None:
        # A shock inside the warm-up (sigma undefined) must not signal.
        frame = run(make_frame(800, shock=500))
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        startup = Strategy.startup_candle_count
        self.assertEqual(
            int(frame.iloc[:startup].get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0
        )

    def test_signals_do_not_change_when_future_appended(self) -> None:
        n, k = 760, 60
        short = run(make_frame(n))
        full = run(make_frame(n + k))
        cols = ["sigma", "vmed", "bar_ret", "drop_threshold", "enter_long", "enter_tag"]
        pd.testing.assert_frame_equal(
            short[cols].reset_index(drop=True),
            full[cols].iloc[:n].reset_index(drop=True),
            check_dtype=False,
        )

    def _exit_at(self, frame, current_time, tag, open_date):
        strategy = Strategy()
        strategy.dp = _DP(frame)
        return strategy.custom_exit("X/USDT", _Trade(tag, open_date), current_time, 0.0, 0.0)

    def test_custom_exit_rules(self) -> None:
        frame = run(make_frame(800))
        tag = frame.loc[SHOCK, "enter_tag"]
        open_date = frame.loc[SHOCK + 1, "date"].to_pydatetime()
        # After entry bar closes below target and above floor: no exit.
        self.assertIsNone(self._exit_at(frame, open_date + BAR, tag, open_date))
        # Full retrace on the entry bar.
        f = frame.copy()
        f.loc[SHOCK + 1, "close"] = 100.0
        self.assertEqual(self._exit_at(f, open_date + BAR, tag, open_date), "full_retrace")
        # Shock bar itself (before entry) is not checked.
        f = frame.copy()
        f.loc[SHOCK, "close"] = 101.0
        self.assertIsNone(self._exit_at(f, open_date, tag, open_date))
        # Breakdown below floor.
        f = frame.copy()
        f.loc[SHOCK + 2, "close"] = 90.0
        self.assertEqual(
            self._exit_at(f, open_date + 2 * BAR, tag, open_date), "breakdown_below_floor"
        )
        # Time exit at open of bar t+17.
        self.assertIsNone(self._exit_at(frame, open_date + 15 * BAR, tag, open_date))
        self.assertEqual(
            self._exit_at(frame, open_date + 16 * BAR, tag, open_date), "time_exit_16_bars"
        )


if __name__ == "__main__":
    unittest.main()
