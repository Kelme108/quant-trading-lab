import importlib.util
import sys
import types
import unittest
from pathlib import Path

import pandas as pd

freqtrade = types.ModuleType("freqtrade")
strategy_module = types.ModuleType("freqtrade.strategy")
strategy_module.IStrategy = object
freqtrade.strategy = strategy_module
sys.modules.setdefault("freqtrade", freqtrade)
sys.modules.setdefault("freqtrade.strategy", strategy_module)
for name in ("merge_informative_pair", "stoploss_from_absolute"):
    if not hasattr(sys.modules["freqtrade.strategy"], name):
        setattr(sys.modules["freqtrade.strategy"], name, lambda *a, **k: None)
talib = types.ModuleType("talib")
talib_abstract = types.ModuleType("talib.abstract")
talib_abstract.SMA = lambda dataframe, timeperiod: dataframe["close"].rolling(timeperiod).mean()
talib_abstract.RSI = lambda dataframe, timeperiod: pd.Series(50.0, index=dataframe.index)
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)

ROOT = Path(__file__).parents[1]
path = ROOT / "user_data" / "strategies" / "Sma200Baseline.py"
spec = importlib.util.spec_from_file_location("Sma200Baseline", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Strategy = module.Sma200Baseline


def frame(close_1d, sma_1d):
    return pd.DataFrame({"close_1d": close_1d, "sma_1d": sma_1d, "volume": 1.0})


class Sma200BaselineTests(unittest.TestCase):
    def test_enters_only_when_the_closed_daily_close_is_above_its_sma(self):
        out = Strategy().populate_entry_trend(frame([101.0, 99.0, 100.0, 105.0], [100.0, 100.0, 100.0, 100.0]), {})
        self.assertEqual(list(out["enter_long"].fillna(0)), [1, 0, 0, 1])

    def test_exits_when_the_daily_close_is_at_or_below_the_sma(self):
        out = Strategy().populate_exit_trend(frame([101.0, 99.0, 100.0, 105.0], [100.0, 100.0, 100.0, 100.0]), {})
        self.assertEqual(list(out["exit_long"].fillna(0)), [0, 1, 1, 0])

    def test_no_signal_while_the_sma_is_not_available(self):
        # row 0 has no SMA yet (warm-up): it must not signal; row 1 is a normal entry/exit row
        nan = float("nan")
        entry = Strategy().populate_entry_trend(frame([101.0, 101.0], [nan, 100.0]), {})
        exit_ = Strategy().populate_exit_trend(frame([99.0, 99.0], [nan, 100.0]), {})
        self.assertEqual(list(entry["enter_long"].fillna(0)), [0, 1])
        self.assertEqual(list(exit_["exit_long"].fillna(0)), [0, 1])

    def test_contract(self):
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertGreaterEqual(Strategy.startup_candle_count, module.SMA_DAYS)  # freqtrade loads this many 1d candles
        for name in ("custom_stake_amount", "adjust_trade_position", "leverage"):
            self.assertFalse(hasattr(Strategy, name))


if __name__ == "__main__":
    unittest.main()
