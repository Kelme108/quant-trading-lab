import tempfile
import textwrap
import unittest
from pathlib import Path

from lab import strategy_check

GOOD = '''
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class Trend_H004_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 100.0}
    stoploss = -0.10
    startup_candle_count = 400

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["sma"] = dataframe["close"].rolling(400).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["close"] > dataframe["sma"], "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["close"] < dataframe["sma"], "exit_long"] = 1
        return dataframe
'''


class StrategyCheckTests(unittest.TestCase):
    def check(self, source: str, name: str = "Trend_H004_v1.py", **kwargs) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / name
            path.write_text(textwrap.dedent(source), encoding="utf-8")
            return strategy_check.check_strategy_source(path, **kwargs)

    def assertFlags(self, problems: list[str], fragment: str) -> None:
        self.assertTrue(any(fragment in p for p in problems), f"{fragment!r} not in {problems}")

    def test_a_clean_strategy_passes(self) -> None:
        self.assertEqual(self.check(GOOD, expected_hypothesis_id="H-004"), [])

    def test_the_existing_baselines_pass_the_screen_except_for_their_names(self) -> None:
        """The screen is not stricter than the strategies already in use: the
        only thing the baselines fail is the new file-name convention."""
        root = Path(__file__).parents[1] / "user_data" / "strategies"
        for baseline in ("SmaTrendBaseline", "DonchianBreakoutBaseline", "BollingerMeanReversionBaseline"):
            problems = strategy_check.check_strategy_source(root / f"{baseline}.py")
            self.assertEqual(len(problems), 1, problems)
            self.assertIn("must look like", problems[0])

    def test_a_warmup_freqtrade_cannot_load_is_rejected(self) -> None:
        problems = self.check(GOOD.replace("startup_candle_count = 400", "startup_candle_count = 5520"))
        self.assertTrue(any("5520" in p and "4500" in p for p in problems), problems)
        self.assertEqual(self.check(GOOD.replace("startup_candle_count = 400", "startup_candle_count = 4500")), [])

    def test_the_warmup_must_be_a_plain_integer(self) -> None:
        problems = self.check(GOOD.replace("    startup_candle_count = 400\n", ""))
        self.assertTrue(any("startup_candle_count" in p for p in problems), problems)

    def test_dangerous_imports_are_rejected(self) -> None:
        for statement in ("import os", "import subprocess", "import socket",
                          "import requests", "from urllib.request import urlopen",
                          "from pathlib import Path", "import pickle"):
            source = statement + "\n" + GOOD
            self.assertFlags(self.check(source), "not allowed")

    def test_relative_imports_are_rejected(self) -> None:
        self.assertFlags(self.check("from . import helper\n" + GOOD), "not allowed")

    def test_dangerous_calls_are_rejected(self) -> None:
        for call in ("open('x')", "eval('1')", "exec('1')", "__import__('os')",
                     "getattr(self, 'x')", "compile('1', 'f', 'eval')"):
            source = GOOD.replace('dataframe["sma"] =', f"_ = {call}\n        dataframe[\"sma\"] =", 1)
            self.assertTrue(self.check(source), call)

    def test_file_io_through_pandas_and_numpy_is_rejected(self) -> None:
        for attribute in ("read_csv", "to_pickle", "load", "to_csv", "query"):
            source = GOOD.replace(
                'dataframe["sma"] =', f'_ = dataframe.{attribute}\n        dataframe["sma"] =', 1
            )
            self.assertFlags(self.check(source), f".{attribute}")

    def test_dunder_escapes_are_rejected(self) -> None:
        source = GOOD.replace(
            'dataframe["sma"] =', '_ = ().__class__.__bases__\n        dataframe["sma"] =', 1
        )
        self.assertFlags(self.check(source), "dunder")

    def test_shorting_is_rejected(self) -> None:
        source = GOOD.replace('"exit_long"', '"exit_short"')
        self.assertFlags(self.check(source), "shorting")

    def test_can_short_must_be_false(self) -> None:
        self.assertFlags(self.check(GOOD.replace("can_short = False", "can_short = True")), "can_short")
        self.assertFlags(self.check(GOOD.replace("    can_short = False\n", "")), "can_short")

    def test_timeframe_and_interface_version_are_enforced(self) -> None:
        self.assertFlags(self.check(GOOD.replace('"1h"', '"4h"')), "timeframe")
        self.assertFlags(self.check(GOOD.replace("INTERFACE_VERSION = 3", "INTERFACE_VERSION = 2")), "INTERFACE_VERSION")

    def test_position_sizing_hooks_are_rejected(self) -> None:
        source = GOOD + "\n    def leverage(self, *args, **kwargs):\n        return 3.0\n"
        self.assertFlags(self.check(source), "leverage")

    def test_class_must_match_the_file_name(self) -> None:
        self.assertFlags(self.check(GOOD, name="Other_H004_v1.py"), "must be named like the file")

    def test_file_name_must_follow_the_convention_and_hypothesis(self) -> None:
        self.assertFlags(self.check(GOOD, name="strategy.py"), "must look like")
        self.assertFlags(self.check(GOOD, expected_hypothesis_id="H-005"), "H-004")

    def test_exactly_one_strategy_class(self) -> None:
        self.assertFlags(self.check("x = 1\n"), "exactly one IStrategy")
        two = GOOD + "\n\nclass Second_H004_v1(IStrategy):\n    pass\n"
        self.assertFlags(self.check(two), "exactly one IStrategy")

    def test_unparseable_source_is_reported(self) -> None:
        self.assertFlags(self.check("def broken(:\n"), "does not parse")


if __name__ == "__main__":
    unittest.main()


class WarmupWarningTests(unittest.TestCase):
    ROOT = Path(__file__).parents[1]

    def warnings(self, source: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "S_H001_v1.py"
            path.write_text(textwrap.dedent(source), encoding="utf-8")
            return strategy_check.warmup_warnings(path)

    def body(self, startup: int, indicators: str, header: str = "") -> str:
        return (
            "import talib.abstract as ta\n" + header +
            "class S_H001_v1(IStrategy):\n"
            f"    startup_candle_count = {startup}\n"
            "    def populate_indicators(self, dataframe, metadata):\n"
            f"        {indicators}\n"
            "        return dataframe\n"
        )

    def test_rsi_with_short_warmup_warns_and_the_minimum_is_400(self):
        out = self.warnings(self.body(200, 'dataframe["r"] = ta.RSI(dataframe, timeperiod=14)'))
        self.assertEqual(len(out), 1)
        self.assertIn("< 400", out[0])
        self.assertEqual(self.warnings(self.body(400, 'dataframe["r"] = ta.RSI(dataframe, timeperiod=14)')), [])

    def test_three_times_the_period_is_required_for_long_periods(self):
        code = 'dataframe["e"] = ta.EMA(dataframe, timeperiod=200)'
        self.assertEqual(len(self.warnings(self.body(599, code))), 1)
        self.assertEqual(self.warnings(self.body(600, code)), [])

    def test_period_from_module_constant_and_positional_argument(self):
        out = self.warnings(self.body(500, 'dataframe["e"] = ta.EMA(dataframe, TREND)', header="TREND = 200\n"))
        self.assertIn("< 600", out[0])

    def test_talib_default_period_is_used_when_omitted(self):
        self.assertEqual(self.warnings(self.body(400, 'dataframe["a"] = ta.ATR(dataframe)')), [])

    def test_pandas_ewm_span_is_checked(self):
        out = self.warnings(self.body(300, 'dataframe["e"] = dataframe["close"].ewm(span=200).mean()'))
        self.assertEqual(len(out), 1)

    def test_non_constant_period_is_reported_not_guessed(self):
        out = self.warnings(self.body(800, 'dataframe["e"] = ta.EMA(dataframe, timeperiod=self.n)'))
        self.assertIn("not a constant", out[0])

    def test_sma_only_strategy_has_no_warning(self):
        self.assertEqual(self.warnings(self.body(210, 'dataframe["s"] = ta.SMA(dataframe, timeperiod=200)')), [])

    def test_existing_strategies(self):
        strategies = self.ROOT / "user_data" / "strategies"
        expected_warning = {"BollingerMeanReversionBaseline.py"}  # RSI(14) with startup 200
        for path in sorted(strategies.glob("*.py")) + sorted((strategies / "_archive").glob("*.py")):
            found = strategy_check.warmup_warnings(path)
            if path.name in expected_warning:
                self.assertEqual(len(found), 1, (path.name, found))
            else:
                self.assertEqual(found, [], (path.name, found))
