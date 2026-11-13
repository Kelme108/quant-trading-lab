import importlib.util
import math
import sys
import types
import unittest
from datetime import timedelta
from pathlib import Path

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


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Strategy = load_strategy("AwesomeOscillatorSaucer_H134_v1.py", "AwesomeOscillatorSaucer_H134_v1")

START = pd.Timestamp("2026-01-01", tz="UTC")


def make_frame(n: int) -> pd.DataFrame:
    mp = [100.0 + 0.1 * i + 0.8 * math.sin(2 * math.pi * i / 20) for i in range(n)]
    close = pd.Series(mp)
    open_ = close.shift(1).fillna(close.iloc[0])
    return pd.DataFrame(
        {
            "date": [START + timedelta(minutes=15 * i) for i in range(n)],
            "open": open_,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": [10.0] * n,
        }
    )


def run(strategy, frame: pd.DataFrame) -> pd.DataFrame:
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


class FakeDp:
    def __init__(self, frame):
        self.frame = frame

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.frame, None


class FakeTrade:
    def __init__(self, open_date_utc, open_rate):
        self.open_date_utc = open_date_utc
        self.open_rate = open_rate


class SaucerTests(unittest.TestCase):
    def test_class_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 400)

    def test_signals_exist_and_are_binary(self) -> None:
        out = run(Strategy(), make_frame(600))
        self.assertGreater(int(out["enter_long"].fillna(0).sum()), 0)
        for column in ("enter_long", "exit_long"):
            if column in out:
                self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_entry_conditions_hold_on_signal_rows(self) -> None:
        out = run(Strategy(), make_frame(600))
        rows = out[out["enter_long"] == 1]
        self.assertTrue((rows["ao"] > rows["ao_1"]).all())
        self.assertTrue((rows["ao_1"] < rows["ao_2"]).all())
        self.assertTrue((rows["ao_2"] < rows["ao_3"]).all())
        self.assertTrue((rows["ao_3"] > 0).all())
        self.assertTrue((rows["atr_pct"] >= 0.004).all())
        self.assertTrue((rows["close"] > rows["open"]).all())
        self.assertTrue(rows["stop_dist"].between(0.01, 0.025).all())

    def test_zero_volume_no_signal(self) -> None:
        strategy = Strategy()
        frame = make_frame(600)
        base = run(strategy, frame)
        signal_rows = base.index[base["enter_long"] == 1]
        self.assertGreater(len(signal_rows), 0)
        zeroed = frame.copy()
        zeroed.loc[signal_rows, "volume"] = 0.0
        out = run(strategy, zeroed)
        self.assertEqual(int(out.loc[signal_rows, "enter_long"].fillna(0).sum()), 0)
        zeroed["volume"] = 0.0
        out = run(strategy, zeroed)
        self.assertEqual(int(out.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(out.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_undefined_startup_values_no_signal(self) -> None:
        # AO(t-3) needs 34 + 3 bars of history; rows 0..35 are undefined.
        frame = make_frame(600)
        frame["close"] = 100.0 - 0.1 * pd.Series(range(600))  # AO < 0: exits possible later
        out = run(Strategy(), frame)
        first = out.iloc[:36]
        self.assertEqual(int(first.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(first.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        out = run(Strategy(), make_frame(600))
        self.assertEqual(int(out.iloc[:36].get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_exit_signal_when_ao_below_zero(self) -> None:
        frame = make_frame(200)
        frame["close"] = 200.0 - 0.3 * pd.Series(range(200))
        frame["open"] = frame["close"]
        frame["high"] = frame["close"] + 0.5
        frame["low"] = frame["close"] - 0.5
        out = run(Strategy(), frame)
        self.assertGreater(int(out["exit_long"].fillna(0).sum()), 0)
        flagged = out[out["exit_long"] == 1]
        self.assertTrue((flagged["ao"] < 0).all())

    def test_no_lookahead(self) -> None:
        strategy = Strategy()
        full = make_frame(700)
        n = 450
        short = run(strategy, full.iloc[:n])
        long_ = run(strategy, full)
        cols = [c for c in short.columns if c not in {"enter_tag", "exit_tag"}]
        pd.testing.assert_frame_equal(
            short[cols].reset_index(drop=True),
            long_.loc[: n - 1, cols].reset_index(drop=True),
            check_dtype=False,
        )

    def test_stop_distance_floor_and_skip(self) -> None:
        frame = make_frame(200)
        out = Strategy().populate_indicators(frame, {})
        valid = out["stop_dist"].dropna()
        self.assertTrue(valid.between(0.01, 0.025).all())
        frame = make_frame(200)
        frame.loc[100, "low"] = frame.loc[100, "close"] * 0.9  # raw > 2.5% for bars 100..105
        out = Strategy().populate_indicators(frame, {})
        self.assertTrue(out.loc[100:105, "stop_dist"].isna().all())

    def _setup_trade(self):
        strategy = Strategy()
        frame = make_frame(100)
        frame["stop_dist"] = 0.02
        frame.loc[50, "stop_dist"] = 0.012
        strategy.dp = FakeDp(frame)
        fill_time = frame.loc[51, "date"]
        return strategy, FakeTrade(fill_time, 100.0), fill_time

    def test_custom_stoploss_uses_fixed_distance(self) -> None:
        strategy, trade, fill_time = self._setup_trade()
        value = strategy.custom_stoploss("X/USDT", trade, fill_time, 100.0, 0.0)
        self.assertAlmostEqual(value, -0.012)
        value = strategy.custom_stoploss("X/USDT", trade, fill_time, 101.0, 0.01)
        self.assertAlmostEqual(100.0 * (1 - 0.012) / 101.0 - 1.0, value)

    def test_take_profit_exit(self) -> None:
        strategy, trade, fill_time = self._setup_trade()
        t = fill_time + timedelta(minutes=30)
        self.assertIsNone(strategy.custom_exit("X/USDT", trade, t, 101.7, 0.017))
        self.assertEqual(
            strategy.custom_exit("X/USDT", trade, t, 101.81, 0.0181), "take_profit_1_5R"
        )

    def test_time_exit(self) -> None:
        strategy, trade, fill_time = self._setup_trade()
        self.assertIsNone(
            strategy.custom_exit("X/USDT", trade, fill_time + timedelta(hours=11, minutes=45), 100.0, 0.0)
        )
        self.assertEqual(
            strategy.custom_exit("X/USDT", trade, fill_time + timedelta(hours=12), 100.0, 0.0),
            "time_exit_12h",
        )


if __name__ == "__main__":
    unittest.main()
