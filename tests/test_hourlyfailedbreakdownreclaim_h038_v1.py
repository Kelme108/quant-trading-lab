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

talib = types.ModuleType("talib")
talib_abstract = types.ModuleType("talib.abstract")
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)

ROOT = Path(__file__).parents[1]
CLASS_NAME = "HourlyFailedBreakdownReclaim_H038_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / f"{CLASS_NAME}.py"
    spec = importlib.util.spec_from_file_location(CLASS_NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, CLASS_NAME)


Strategy = load_strategy()
SETUP_BAR = 650


def make_frame(n: int = 700) -> pd.DataFrame:
    close = [100.0] * n
    low = [99.0] * n
    high = [101.0] * n
    low[300] = 90.0  # old 20-day low, well over 96 bars before the setup
    close[SETUP_BAR - 1] = 95.0
    low[SETUP_BAR - 1] = 94.0
    low[SETUP_BAR] = 89.0  # sweep below PL = 90
    close[SETUP_BAR] = 91.0  # reclaim
    return pd.DataFrame(
        {
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "volume": [1.0] * n,
        }
    )


def run(frame: pd.DataFrame) -> pd.DataFrame:
    s = Strategy()
    frame = s.populate_indicators(frame, {})
    frame = s.populate_entry_trend(frame, {})
    return s.populate_exit_trend(frame, {})


class H038Tests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.03)
        self.assertGreaterEqual(Strategy.startup_candle_count, 483)
        prot = Strategy().protections
        self.assertEqual(prot[0]["method"], "CooldownPeriod")
        self.assertEqual(prot[0]["stop_duration_candles"], 24)

    def test_setup_fires_once_and_is_binary(self) -> None:
        frame = run(make_frame())
        values = frame["enter_long"].dropna().unique().tolist()
        self.assertEqual(values, [1])
        self.assertEqual(frame.index[frame["enter_long"] == 1].tolist(), [SETUP_BAR])

    def test_young_low_is_rejected(self) -> None:
        frame = make_frame()
        frame.loc[300, "low"] = 99.0
        frame.loc[SETUP_BAR - 50, "low"] = 90.0
        frame = run(frame)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)

    def test_zero_volume_no_signal(self) -> None:
        frame = make_frame()
        frame["volume"] = 0.0
        frame = run(frame)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self) -> None:
        frame = run(make_frame())
        startup = Strategy.startup_candle_count
        # Window needs 484 bars; nothing before it may fire.
        self.assertEqual(int(frame.iloc[:483]["enter_long"].fillna(0).sum()), 0)
        short = run(make_frame().iloc[:400].copy().reset_index(drop=True))
        self.assertEqual(int(short.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertGreaterEqual(startup, 483)

    def test_no_lookahead(self) -> None:
        full = make_frame(760)
        full.loc[SETUP_BAR + 5 :, ["open", "high", "low", "close"]] = 50.0
        n = 700
        a = run(full.iloc[:n].copy().reset_index(drop=True))
        b = run(full.copy())
        cols = [c for c in a.columns if c not in {"enter_tag"}]
        pd.testing.assert_frame_equal(
            a[cols].reset_index(drop=True),
            b.iloc[:n][cols].reset_index(drop=True),
            check_dtype=False,
        )


if __name__ == "__main__":
    unittest.main()
