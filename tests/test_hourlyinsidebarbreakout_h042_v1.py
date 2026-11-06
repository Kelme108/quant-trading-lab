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
NAME = "HourlyInsideBarBreakout_H042_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, NAME)


Strategy = load_strategy()


def run(strategy, frame):
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    for col in ("enter_long", "exit_long"):
        if col not in frame:
            frame[col] = np.nan
    return frame


def bars(rows):
    """rows: list of (open, high, low, close)."""
    return pd.DataFrame(
        {
            "open": [r[0] for r in rows],
            "high": [r[1] for r in rows],
            "low": [r[2] for r in rows],
            "close": [r[3] for r in rows],
            "volume": [1.0] * len(rows),
        }
    )


def pattern_frame():
    # 250 flat-ish rising bars, then mother, inside, breakout, then a fall.
    rows = []
    for k in range(250):
        p = 100.0 + k * 0.01
        rows.append((p, p * 1.001, p * 0.999, p))
    rows.append((102.5, 105.0, 102.0, 104.0))  # 250 mother: range 2.9%
    rows.append((103.5, 104.5, 102.5, 104.0))  # 251 inside bar
    rows.append((104.0, 105.5, 103.8, 105.2))  # 252 close > mother high -> entry
    rows.append((105.2, 105.6, 104.9, 105.0))  # 253 entry bar, above midpoint 103.5
    rows.append((105.0, 105.1, 102.9, 103.0))  # 254 close < 103.5 -> exit
    for _ in range(10):
        rows.append((103.0, 103.1, 102.9, 103.0))
    return bars(rows)


class H042Tests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 300)

    def test_pattern_entry_and_exit(self) -> None:
        out = run(Strategy(), pattern_frame())
        self.assertEqual(out.index[out["enter_long"] == 1].tolist(), [252])
        self.assertEqual(out.index[out["exit_long"] == 1].tolist(), [254])

    def test_binary_columns(self) -> None:
        out = run(Strategy(), pattern_frame())
        for col in ("enter_long", "exit_long"):
            self.assertTrue(set(out[col].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_no_signal(self) -> None:
        frame = pattern_frame()
        frame["volume"] = 0.0
        out = run(Strategy(), frame)
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(out["exit_long"].fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self) -> None:
        # pattern placed before SMA(240) is defined
        rows = [(100.0, 100.1, 99.9, 100.0)] * 20
        rows += [
            (100.0, 103.0, 100.0, 102.0),
            (101.5, 102.5, 101.0, 102.0),
            (102.0, 104.0, 101.8, 103.5),
        ]
        rows += [(103.5, 103.6, 103.4, 103.5)] * 10
        out = run(Strategy(), bars(rows))
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(out["exit_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self) -> None:
        rng = np.random.default_rng(7)
        n, k = 420, 60
        close = 100 + np.cumsum(rng.normal(0.02, 0.8, n + k))
        opn = np.r_[close[0], close[:-1]]
        spread = np.abs(rng.normal(0.6, 0.4, n + k))
        full = pd.DataFrame(
            {
                "open": opn,
                "high": np.maximum(opn, close) + spread,
                "low": np.minimum(opn, close) - spread,
                "close": close,
                "volume": 1.0,
            }
        )
        full = pd.concat([pattern_frame(), full], ignore_index=True)
        n_total = len(full) - k
        short = run(Strategy(), full.iloc[:n_total])
        long = run(Strategy(), full)
        for col in ("enter_long", "exit_long"):
            pd.testing.assert_series_equal(
                short[col].reset_index(drop=True),
                long[col].iloc[:n_total].reset_index(drop=True),
                check_dtype=False,
            )


if __name__ == "__main__":
    unittest.main()
