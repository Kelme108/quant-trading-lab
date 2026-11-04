import importlib.util
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from lab import causality, strategy_check  # noqa: E402

_spec = importlib.util.spec_from_file_location("regime_filter", ROOT / "user_data" / "strategies" / "regime_filter.py")
regime_filter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(regime_filter)

STRATEGY = '''
from pandas import DataFrame
from freqtrade.strategy import IStrategy
{imports}


class Probe_H099_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False
    minimal_roi = {{"0": 100.0}}
    stoploss = -0.10
    startup_candle_count = 400

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe
'''


def daily_close(n=900, seed=3):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.02, n)))
    return pd.Series(close, index=pd.date_range("2020-01-01", periods=n, freq="D", tz="UTC"))


class ImportScreenTests(unittest.TestCase):
    def check(self, imports):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Probe_H099_v1.py"
            path.write_text(STRATEGY.format(imports=imports), encoding="utf-8")
            return strategy_check.check_strategy_source(path)

    def test_accepts_the_allowed_sibling_module(self):
        self.assertEqual(self.check("from regime_filter import regime_on, vol_regime"), [])
        self.assertEqual(self.check("import regime_filter"), [])

    def test_rejects_everything_else(self):
        for bad in ("import os", "from lab import stats", "import other_module", "from other_module import x",
                    "from . import regime_filter", "from .regime_filter import regime_on",
                    "import regime_filter_extra", "from regime_filter.sub import x", "import subprocess"):
            self.assertTrue(self.check(bad), bad)

    def test_the_module_itself_passes_the_same_ast_screen(self):
        self.assertEqual(strategy_check.check_helper_module_source(ROOT / "user_data" / "strategies" / "regime_filter.py"), [])

    def test_helper_screen_rejects_bad_code_and_unlisted_modules(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "regime_filter.py"
            bad.write_text("import os\nx = open('f')\n", encoding="utf-8")
            self.assertEqual(len(strategy_check.check_helper_module_source(bad)), 2)
            other = Path(tmp) / "helper.py"
            other.write_text("x = 1\n", encoding="utf-8")
            self.assertTrue(strategy_check.check_helper_module_source(other))


class RegimeBehaviourTests(unittest.TestCase):
    def test_trend_regime_matches_definition(self):
        close = daily_close()
        expected = (close > close.rolling(200).mean()).fillna(False)
        self.assertTrue(regime_filter.trend_regime(close, 200).equals(expected))
        self.assertFalse(regime_filter.trend_regime(close, 200).iloc[:199].any())

    def test_vol_regime_is_false_until_defined_and_flags_a_spike(self):
        close = daily_close(900)
        flag = regime_filter.vol_regime(close, 30, 1.5)
        self.assertFalse(flag.iloc[:394].any())   # 30 returns + 365-day median need 395 days
        spiky = close.copy()
        spiky.iloc[700:730] = spiky.iloc[700:730] * np.where(np.arange(30) % 2, 1.25, 0.8)
        self.assertFalse(regime_filter.vol_regime(spiky, 30, 1.5).iloc[720:730].any())
        self.assertTrue(regime_filter.vol_regime(close, 30, 1.5).iloc[400:].mean() > 0.5)

    def test_vol_threshold_is_inclusive(self):
        close = daily_close(900)
        vol = np.log(close).diff().rolling(30).std()
        median = vol.rolling(365).median()
        ratio = float((vol / median).iloc[600])
        self.assertTrue(bool(regime_filter.vol_regime(close, 30, ratio).iloc[600]))

    def test_regime_on_combines_flags(self):
        close = daily_close()
        self.assertFalse(regime_filter.VOL_REGIME_ON_BY_DEFAULT)
        self.assertTrue(regime_filter.regime_on(close).equals(regime_filter.trend_regime(close)))
        both = regime_filter.regime_on(close, use_vol=True)
        self.assertTrue(both.equals(regime_filter.vol_regime(close) & regime_filter.trend_regime(close)))
        self.assertTrue(regime_filter.regime_on(close, use_vol=False).equals(regime_filter.trend_regime(close)))
        self.assertTrue(regime_filter.regime_on(close, use_vol=True, use_trend=False).equals(regime_filter.vol_regime(close)))
        self.assertTrue(regime_filter.regime_on(close, use_vol=False, use_trend=False).all())

    def test_at_most_three_numeric_parameters(self):
        import inspect
        numeric = [p for p in inspect.signature(regime_filter.regime_on).parameters.values()
                   if p.name != "close_1d" and not isinstance(p.default, bool)]
        self.assertLessEqual(len(numeric), 3)


class CausalityTests(unittest.TestCase):
    def frame(self):
        close = daily_close(700)
        return pd.DataFrame({"close": close.to_numpy()}, index=close.index)

    def functions(self):
        return {
            "vol": lambda f: pd.DataFrame({"x": regime_filter.vol_regime(f["close"]).astype(float)}),
            "trend": lambda f: pd.DataFrame({"x": regime_filter.trend_regime(f["close"]).astype(float)}),
            "on": lambda f: pd.DataFrame({"x": regime_filter.regime_on(f["close"], use_vol=True).astype(float)}),
        }

    def test_prefix_invariance_and_future_corruption_for_each_function(self):
        frame = self.frame()
        for name, fn in self.functions().items():
            self.assertEqual(causality.prefix_invariance(fn, frame, [420, 500, 560, 650]), [], name)
            self.assertEqual(causality.future_corruption(fn, frame, 500), [], name)

    def test_the_detector_would_catch_a_leaky_variant(self):
        leaky = lambda f: pd.DataFrame({"x": (f["close"] > f["close"].mean()).astype(float)})  # noqa: E731
        self.assertTrue(causality.prefix_invariance(leaky, self.frame(), [500]))


if __name__ == "__main__":
    unittest.main()
