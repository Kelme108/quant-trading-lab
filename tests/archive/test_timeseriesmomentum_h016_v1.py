import importlib.util
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parents[2]
STRATEGIES = ROOT / "user_data" / "strategies"
ARCHIVE = STRATEGIES / "_archive"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(STRATEGIES))
sys.path.insert(0, str(Path(__file__).parent))

import test_timeseriesmomentum_h015_v1 as h15  # noqa: E402  (installs the freqtrade test doubles)
from lab import strategy_check  # noqa: E402

NAME = "TimeSeriesMomentum_H016_v1"
spec = importlib.util.spec_from_file_location(NAME, ARCHIVE / f"{NAME}.py")
h16 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h16)


class H016Tests(unittest.TestCase):
    def test_chosen_constants(self):
        self.assertEqual((h16.N_DAYS, h16.USE_REGIME), (30, False))

    def test_passes_screen_without_warnings(self):
        path = ARCHIVE / f"{NAME}.py"
        self.assertEqual(strategy_check.check_strategy_source(path, expected_hypothesis_id="H-016"), [])
        self.assertEqual(strategy_check.warmup_warnings(path), [])

    def test_signals_equal_the_h015_rule_at_n30_without_regime(self):
        daily = h15.daily_frame(420)
        expected = h15.build(daily, 30, False)[["date", "enter_long", "exit_long"]].set_index("date")
        strategy = h16.TimeSeriesMomentum_H016_v1.__new__(h16.TimeSeriesMomentum_H016_v1)
        strategy.dp = h15.FakeDP(daily)
        out = strategy.populate_indicators(h15.hourly_from_daily(daily), {"pair": "BTC/USDT"})
        out["enter_long"], out["exit_long"] = 0, 0
        out = strategy.populate_exit_trend(strategy.populate_entry_trend(out, {}), {})
        pd.testing.assert_frame_equal(out[["date", "enter_long", "exit_long"]].set_index("date"), expected, check_dtype=False)


if __name__ == "__main__":
    unittest.main()
