import importlib.util
import sys
import types
import unittest
from pathlib import Path

import numpy as np
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
FILENAME = "CrossSectionalLowVolReversal_H078_v1.py"
CLASS_NAME = "CrossSectionalLowVolReversal_H078_v1"


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name), module


Strategy, strategy_module_loaded = load_strategy(FILENAME, CLASS_NAME)
PAIRS = strategy_module_loaded.PAIRS
TRADED = "SOL/USDT"
N_BARS = 520
DROP_END = 479  # signal bar for the engineered drop


def make_universe(n_bars: int = N_BARS, seed: int = 7) -> dict:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")
    frames = {}
    for pair in PAIRS:
        returns = rng.normal(0.0, 0.001, n_bars)
        if pair == TRADED:
            returns[DROP_END - 3 : DROP_END + 1] = -0.012
            returns[DROP_END + 1 : DROP_END + 8] = 0.008
        close = 100.0 * np.exp(np.cumsum(returns))
        volume = 100.0 + rng.uniform(-5.0, 5.0, n_bars)
        if pair == TRADED:
            volume[DROP_END - 3 : DROP_END + 1] = 90.0
        frames[pair] = pd.DataFrame(
            {
                "date": dates,
                "open": close,
                "high": close * 1.002,
                "low": close * 0.998,
                "close": close,
                "volume": volume,
            }
        )
    return frames


class FakeDataProvider:
    def __init__(self, frames: dict, analyzed: pd.DataFrame = None):
        self.frames = frames
        self.analyzed = analyzed

    def get_pair_dataframe(self, pair, timeframe):
        return self.frames[pair].copy()

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.analyzed, None


class FakeTrade:
    def __init__(self, open_date):
        self.open_date_utc = open_date


def run(frames: dict, pair: str = TRADED) -> pd.DataFrame:
    strategy = Strategy()
    strategy.dp = FakeDataProvider(frames)
    metadata = {"pair": pair}
    frame = strategy.populate_indicators(frames[pair].copy(), metadata)
    frame = strategy.populate_entry_trend(frame, metadata)
    frame = strategy.populate_exit_trend(frame, metadata)
    return frame


def truncate(frames: dict, n: int) -> dict:
    return {pair: frame.iloc[:n].copy() for pair, frame in frames.items()}


class CrossSectionalLowVolReversalTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.04)
        self.assertGreaterEqual(Strategy.startup_candle_count, 340)
        self.assertEqual(Strategy.startup_candle_count, 400)
        self.assertEqual(
            Strategy().protections,
            [{"method": "CooldownPeriod", "stop_duration_candles": 4}],
        )
        self.assertEqual(len(PAIRS), 9)

    def test_engineered_drop_creates_entry(self) -> None:
        frame = run(make_universe())
        self.assertEqual(frame.loc[DROP_END, "enter_long"], 1)
        self.assertAlmostEqual(
            frame.loc[DROP_END, "pre_drop_close"], frame.loc[DROP_END - 4, "close"]
        )

    def test_signal_columns_are_binary(self) -> None:
        frame = run(make_universe())
        for column in ("enter_long", "exit_long"):
            if column in frame:
                values = frame[column].dropna().unique().tolist()
                self.assertTrue(set(values).issubset({1}))

    def test_zero_volume_produces_no_signal(self) -> None:
        frames = make_universe()
        frames[TRADED].loc[DROP_END, "volume"] = 0.0
        frame = run(frames)
        self.assertTrue(pd.isna(frame.loc[DROP_END].get("enter_long", np.nan)))

        frames = make_universe()
        frames[TRADED]["volume"] = 0.0
        frame = run(frames)
        self.assertEqual(int(frame.get("enter_long", pd.Series()).fillna(0).sum()), 0)

    def test_startup_values_produce_no_signal(self) -> None:
        frame = run(make_universe())
        self.assertTrue(frame["vn"].iloc[:339].isna().all())
        self.assertEqual(
            int(frame.iloc[:339].get("enter_long", pd.Series()).fillna(0).sum()), 0
        )
        self.assertEqual(
            int(
                frame.iloc[: Strategy.startup_candle_count]
                .get("enter_long", pd.Series())
                .fillna(0)
                .sum()
            ),
            0,
        )

    def test_too_few_pairs_produces_no_signal(self) -> None:
        frames = make_universe()
        for pair in PAIRS[:5]:
            if pair != TRADED:
                frames[pair].loc[:, "close"] = np.nan
        frame = run(frames)
        self.assertEqual(int(frame.get("enter_long", pd.Series()).fillna(0).sum()), 0)

    def test_no_lookahead_when_candles_appended(self) -> None:
        full = make_universe()
        for n in (DROP_END + 1, 450, 500):
            short = run(truncate(full, n))
            long = run(full)
            columns = [
                c
                for c in ("r4", "pre_drop_close", "v4", "vn", "xs_count",
                          "xs_median", "xs_min", "enter_long")
                if c in short.columns or c in long.columns
            ]
            for c in columns:
                if c not in short:
                    short[c] = np.nan
            pd.testing.assert_frame_equal(
                short.loc[: n - 1, columns].reset_index(drop=True),
                long.loc[: n - 1, columns].reset_index(drop=True),
                check_dtype=False,
            )

    def test_custom_exit_target_and_time(self) -> None:
        frame = run(make_universe())
        fill_date = frame.loc[DROP_END + 1, "date"]
        trade = FakeTrade(fill_date.to_pydatetime())
        strategy = Strategy()
        target = frame.loc[DROP_END, "pre_drop_close"]

        reasons = {}
        for u in range(DROP_END + 1, DROP_END + 14):
            strategy.dp = FakeDataProvider({}, frame.iloc[: u + 1].copy())
            reasons[u] = strategy.custom_exit(TRADED, trade, None, 0.0, 0.0)
            hit = frame.loc[u, "close"] >= target
            if hit:
                self.assertEqual(reasons[u], "target_pre_drop")
            elif u - (DROP_END + 1) >= 11:
                self.assertEqual(reasons[u], "time_12h")
            else:
                self.assertIsNone(reasons[u])

        # Time exit fires at the close of e+11 when the target is never reached.
        flat = frame.copy()
        flat.loc[DROP_END + 1 :, "close"] = target * 0.9
        e = DROP_END + 1
        strategy.dp = FakeDataProvider({}, flat.iloc[: e + 11].copy())
        self.assertIsNone(strategy.custom_exit(TRADED, trade, None, 0.0, 0.0))
        strategy.dp = FakeDataProvider({}, flat.iloc[: e + 12].copy())
        self.assertEqual(strategy.custom_exit(TRADED, trade, None, 0.0, 0.0), "time_12h")

        # No exit on a zero-volume candle.
        zero = flat.copy()
        zero.loc[e + 11, "volume"] = 0.0
        strategy.dp = FakeDataProvider({}, zero.iloc[: e + 12].copy())
        self.assertIsNone(strategy.custom_exit(TRADED, trade, None, 0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
