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
strategy_module.merge_informative_pair = lambda *a, **k: a[0]
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
NAME = "HourlyWilliamsVolBreakoutRVol_H104_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load()
Strategy = getattr(MODULE, NAME)


class HourlyWilliamsVolBreakoutRVolTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 120)

    def test_relative_volume_excludes_the_current_bar(self):
        volume = pd.Series([1.0] * 130 + [10.0])
        rvol = MODULE.relative_volume(volume)
        self.assertAlmostEqual(float(rvol.iloc[-1]), 10.0)
        self.assertTrue(rvol.iloc[:120].isna().all())

    def test_the_threshold_is_two_times_over_120_bars(self):
        self.assertEqual(MODULE.RVOL_MIN, 2.0)
        self.assertEqual(MODULE.RVOL_WINDOW, 120)
        self.assertGreaterEqual(Strategy.startup_candle_count, 121)

    def test_no_lookahead_in_the_filter(self):
        rng = np.random.default_rng(3)
        volume = pd.Series(rng.lognormal(0.0, 1.0, 600))
        full = MODULE.relative_volume(volume)
        short = MODULE.relative_volume(volume.iloc[:400])
        pd.testing.assert_series_equal(full.iloc[:400].reset_index(drop=True), short.reset_index(drop=True))


if __name__ == "__main__":
    unittest.main()
