import importlib.util
import sys
import types
import unittest
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


ROOT = Path(__file__).parents[1]


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


SmaTrendBaseline = load_strategy("SmaTrendBaseline.py", "SmaTrendBaseline")
DonchianBreakoutBaseline = load_strategy(
    "DonchianBreakoutBaseline.py", "DonchianBreakoutBaseline"
)
BollingerMeanReversionBaseline = load_strategy(
    "BollingerMeanReversionBaseline.py", "BollingerMeanReversionBaseline"
)


class StrategyContractTests(unittest.TestCase):
    def make_frame(self, prices: list[float]) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "open": prices,
                "high": [price * 1.01 for price in prices],
                "low": [price * 0.99 for price in prices],
                "close": prices,
                "volume": [1.0] * len(prices),
            }
        )

    def test_all_candidates_are_spot_only_and_fixed(self) -> None:
        for strategy in (
            SmaTrendBaseline,
            DonchianBreakoutBaseline,
            BollingerMeanReversionBaseline,
        ):
            self.assertEqual(strategy.INTERFACE_VERSION, 3)
            self.assertFalse(strategy.can_short)
            self.assertLess(strategy.stoploss, 0)
            self.assertEqual(strategy.minimal_roi, {"0": 100.0})

    def test_donchian_excludes_current_candle_from_channel(self) -> None:
        prices = list(range(100, 140))
        frame = self.make_frame(prices)
        strategy = DonchianBreakoutBaseline()
        frame = strategy.populate_indicators(frame, {})
        self.assertTrue(pd.isna(frame.loc[19, "donchian_high"]))
        self.assertEqual(frame.loc[20, "donchian_high"], max(prices[0:20]) * 1.01)

    def test_indicators_do_not_use_future_candles(self) -> None:
        prices = [100.0 + (index % 7) for index in range(260)]
        original = self.make_frame(prices)
        changed = original.copy()
        changed.loc[220:, "open"] = 1000.0
        changed.loc[220:, "high"] = 1100.0
        changed.loc[220:, "low"] = 900.0
        changed.loc[220:, "close"] = 1050.0
        changed.loc[220:, "volume"] = 999.0

        for strategy_class in (
            SmaTrendBaseline,
            DonchianBreakoutBaseline,
            BollingerMeanReversionBaseline,
        ):
            strategy = strategy_class()
            before = strategy.populate_indicators(original.copy(), {})
            after = strategy.populate_indicators(changed.copy(), {})
            indicator_columns = [
                column
                for column in before.columns
                if column not in {"open", "high", "low", "close", "volume"}
            ]
            pd.testing.assert_frame_equal(
                before.loc[:219, indicator_columns],
                after.loc[:219, indicator_columns],
                check_dtype=False,
            )

    def test_zero_volume_does_not_create_signals(self) -> None:
        prices = [100.0] * 80 + [120.0] * 80 + [90.0] * 80
        frame = self.make_frame(prices)
        frame["volume"] = 0.0

        for strategy_class in (
            SmaTrendBaseline,
            DonchianBreakoutBaseline,
            BollingerMeanReversionBaseline,
        ):
            strategy = strategy_class()
            frame_with_indicators = strategy.populate_indicators(frame.copy(), {})
            frame_with_indicators = strategy.populate_entry_trend(
                frame_with_indicators, {}
            )
            frame_with_indicators = strategy.populate_exit_trend(
                frame_with_indicators, {}
            )
            self.assertEqual(
                int(frame_with_indicators.get("enter_long", pd.Series()).fillna(0).sum()),
                0,
            )
            self.assertEqual(
                int(frame_with_indicators.get("exit_long", pd.Series()).fillna(0).sum()),
                0,
            )

    def test_nan_startup_values_do_not_create_signals(self) -> None:
        prices = [100.0 + index for index in range(260)]
        frame = self.make_frame(prices)

        for strategy_class in (
            SmaTrendBaseline,
            DonchianBreakoutBaseline,
            BollingerMeanReversionBaseline,
        ):
            strategy = strategy_class()
            frame_with_indicators = strategy.populate_indicators(frame.copy(), {})
            frame_with_indicators = strategy.populate_entry_trend(
                frame_with_indicators, {}
            )
            frame_with_indicators = strategy.populate_exit_trend(
                frame_with_indicators, {}
            )
            startup = strategy.startup_candle_count
            self.assertEqual(
                int(
                    frame_with_indicators.iloc[:startup]
                    .get("enter_long", pd.Series())
                    .fillna(0)
                    .sum()
                ),
                0,
            )

    def test_signal_columns_are_binary_when_present(self) -> None:
        prices = [100.0 + (index % 13) for index in range(300)]
        for strategy_class in (
            SmaTrendBaseline,
            DonchianBreakoutBaseline,
            BollingerMeanReversionBaseline,
        ):
            strategy = strategy_class()
            frame = strategy.populate_indicators(self.make_frame(prices), {})
            frame = strategy.populate_entry_trend(frame, {})
            frame = strategy.populate_exit_trend(frame, {})
            for column in ("enter_long", "exit_long"):
                if column in frame:
                    values = frame[column].dropna().unique().tolist()
                    self.assertTrue(set(values).issubset({1}))


if __name__ == "__main__":
    unittest.main()
