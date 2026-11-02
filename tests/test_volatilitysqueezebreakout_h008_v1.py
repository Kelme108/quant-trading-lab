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
NAME = "VolatilitySqueezeBreakout_H008_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, NAME)


Strategy = load_strategy()


def make_frame(n: int, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    # Alternating volatility regimes with an upward drift to produce squeezes/breakouts.
    vol = np.where((np.arange(n) // 500) % 2 == 0, 0.002, 0.012)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0004, vol)))
    return pd.DataFrame(
        {
            "open": close,
            "high": close * 1.002,
            "low": close * 0.998,
            "close": close,
            "volume": np.ones(n),
        }
    )


def run(strategy, frame):
    frame = strategy.populate_indicators(frame, {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


class VolatilitySqueezeH008Tests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 2400)
        self.assertEqual(
            Strategy().protections,
            [{"method": "CooldownPeriod", "stop_duration_candles": 72}],
        )

    def test_signals_binary_and_present(self) -> None:
        frame = run(Strategy(), make_frame(6000))
        for column in ("enter_long", "exit_long"):
            self.assertIn(column, frame)
            self.assertTrue(set(frame[column].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(int(frame["enter_long"].fillna(0).sum()), 0)

    def test_zero_volume_no_signal(self) -> None:
        frame = make_frame(6000)
        frame["volume"] = 0.0
        frame = run(Strategy(), frame)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame["exit_long"].fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self) -> None:
        frame = run(Strategy(), make_frame(6000))
        startup = Strategy.startup_candle_count
        self.assertEqual(int(frame.iloc[:startup]["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame.iloc[:336]["exit_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self) -> None:
        full = make_frame(6000)
        n = 5000
        short = run(Strategy(), full.iloc[:n].copy())
        long = run(Strategy(), full.copy())
        pd.testing.assert_frame_equal(
            short.iloc[:n].reset_index(drop=True),
            long.iloc[:n].reset_index(drop=True),
            check_dtype=False,
        )


class SameRuleAsH005Tests(unittest.TestCase):
    def test_signals_are_identical_to_h005(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "h005", ROOT / "user_data" / "strategies" / "VolatilitySqueezeBreakout_H005_v1.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        old = module.VolatilitySqueezeBreakout_H005_v1()
        new = Strategy()
        frame = make_frame(6000)
        out = []
        for strat in (old, new):
            df = strat.populate_indicators(frame.copy(), {"pair": "BTC/USDT"})
            df = strat.populate_entry_trend(df, {"pair": "BTC/USDT"})
            df = strat.populate_exit_trend(df, {"pair": "BTC/USDT"})
            out.append(df[["enter_long", "exit_long"]].fillna(0))
        pd.testing.assert_frame_equal(out[0], out[1])
        self.assertEqual((old.stoploss, old.startup_candle_count), (new.stoploss, new.startup_candle_count))
        self.assertEqual(old.protections, new.protections)


if __name__ == "__main__":
    unittest.main()
