import importlib.util
import sys
import types
import unittest
from pathlib import Path

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
NAME = "DailyPivotS1Reclaim_H061_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, NAME)


Strategy = load_strategy()
START = pd.Timestamp("2024-01-01 00:00", tz="UTC")


def frame_from(opens, highs, lows, closes, volume=1.0):
    n = len(closes)
    return pd.DataFrame(
        {
            "date": pd.date_range(START, periods=n, freq="15min"),
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": [volume] * n,
        }
    )


def scenario_frame():
    """Day 1 filler, day 2 sets H=110 L=90 C=100 (P=100, S1=90, S2=80), day 3 sweeps S1 and reclaims."""
    closes, highs, lows = [], [], []
    for _ in range(96):
        closes.append(100.0); highs.append(100.5); lows.append(99.5)
    for i in range(96):
        closes.append(100.0); highs.append(100.5); lows.append(99.5)
    highs[96 + 10] = 110.0
    lows[96 + 20] = 90.0
    for i in range(96):
        closes.append(95.0); highs.append(95.5); lows.append(94.5)
    # Day 3 bar 10: sweep below S1=90 and close back above.
    lows[192 + 10] = 89.0
    closes[192 + 10] = 91.0
    highs[192 + 10] = 91.5
    # Day 3 bar 20: close at the pivot -> target exit.
    closes[192 + 20] = 101.0
    highs[192 + 20] = 101.5
    # Day 4 filler.
    for _ in range(96):
        closes.append(95.0); highs.append(95.5); lows.append(94.5)
    return frame_from(closes, highs, lows, closes)


def random_frame(n=96 * 8, seed=7):
    rng = np.random.default_rng(seed)
    closes = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.006, n)))
    opens = np.concatenate([[closes[0]], closes[:-1]])
    highs = np.maximum(opens, closes) * (1 + np.abs(rng.normal(0, 0.003, n)))
    lows = np.minimum(opens, closes) * (1 - np.abs(rng.normal(0, 0.003, n)))
    return frame_from(opens, highs, lows, closes)


def run(frame):
    s = Strategy()
    out = s.populate_indicators(frame.copy(), {"pair": "BTC/USDT"})
    out = s.populate_entry_trend(out, {"pair": "BTC/USDT"})
    out = s.populate_exit_trend(out, {"pair": "BTC/USDT"})
    return out


def col(frame, name):
    return frame.get(name, pd.Series(0, index=frame.index)).fillna(0)


class DailyPivotS1ReclaimTests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertAlmostEqual(Strategy.stoploss, -0.03)
        self.assertGreaterEqual(Strategy.startup_candle_count, 200)

    def test_levels_and_scenario_signals(self):
        out = run(scenario_frame())
        row = out.iloc[192 + 10]
        self.assertAlmostEqual(row["pivot_p"], 100.0)
        self.assertAlmostEqual(row["pivot_s1"], 90.0)
        self.assertAlmostEqual(row["pivot_s2"], 80.0)
        entries = list(np.flatnonzero(col(out, "enter_long").to_numpy() == 1))
        exits = list(np.flatnonzero(col(out, "exit_long").to_numpy() == 1))
        self.assertEqual(entries, [192 + 10])
        self.assertEqual(exits, [192 + 20])

    def test_time_exit_at_2345(self):
        frame = scenario_frame()
        frame.loc[192 + 20, ["close", "high"]] = (95.0, 95.5)
        out = run(frame)
        exits = list(np.flatnonzero(col(out, "exit_long").to_numpy() == 1))
        self.assertEqual(exits, [192 + 95])

    def test_signals_are_binary(self):
        for frame in (scenario_frame(), random_frame()):
            out = run(frame)
            for column in ("enter_long", "exit_long"):
                if column in out:
                    self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_no_signal(self):
        frame = scenario_frame()
        frame["volume"] = 0.0
        out = run(frame)
        self.assertEqual(int(col(out, "enter_long").sum()), 0)
        self.assertEqual(int(col(out, "exit_long").sum()), 0)

        frame = scenario_frame()
        frame.loc[192 + 10, "volume"] = 0.0
        out = run(frame)
        self.assertEqual(int(col(out, "enter_long").iloc[192 + 10]), 0)

    def test_nan_startup_no_signal(self):
        for frame in (scenario_frame(), random_frame()):
            out = run(frame)
            self.assertEqual(int(col(out, "enter_long").iloc[:96].sum()), 0)
            self.assertEqual(int(col(out, "exit_long").iloc[:96].sum()), 0)
            undefined = out[["pivot_p", "pivot_s1", "pivot_s2", "sweep_low"]].isna().any(axis=1)
            self.assertTrue(undefined.iloc[:96].all())
            self.assertEqual(int(col(out, "enter_long")[undefined].sum()), 0)
        out = run(scenario_frame())
        self.assertEqual(int(col(out, "enter_long").iloc[: Strategy.startup_candle_count].sum()), 0)

    def test_no_lookahead(self):
        for frame, n in ((scenario_frame(), 192 + 15), (random_frame(), 96 * 5 + 37)):
            short = run(frame.iloc[:n].copy())
            full = run(frame.copy())
            for column in ("enter_long", "exit_long", "pivot_p", "pivot_s1", "pivot_s2", "sweep_low"):
                pd.testing.assert_series_equal(
                    col(short, column).iloc[:n].reset_index(drop=True),
                    col(full, column).iloc[:n].reset_index(drop=True),
                    check_dtype=False,
                    check_names=False,
                )


if __name__ == "__main__":
    unittest.main()
