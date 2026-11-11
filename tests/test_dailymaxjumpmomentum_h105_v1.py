import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
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


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Strategy = load_strategy("DailyMaxJumpMomentum_H105_v1.py", "DailyMaxJumpMomentum_H105_v1")

START = pd.Timestamp("2024-01-01 00:00", tz="UTC")


class FakeTrade:
    def __init__(self, open_date_utc):
        self.open_date_utc = open_date_utc


def make_frame(closes, volume=1.0, start=START) -> pd.DataFrame:
    closes = np.asarray(closes, dtype=float)
    opens = np.concatenate([[closes[0]], closes[:-1]])
    return pd.DataFrame(
        {
            "date": pd.date_range(start, periods=len(closes), freq="1h"),
            "open": opens,
            "high": np.maximum(opens, closes) * 1.002,
            "low": np.minimum(opens, closes) * 0.998,
            "close": closes,
            "volume": np.full(len(closes), volume, dtype=float),
        }
    )


def synthetic_closes(n: int, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    steps = rng.normal(0.0004, 0.004, n)
    jumps = rng.random(n) < 0.03
    steps = steps + jumps * rng.normal(0.02, 0.005, n)
    return 100.0 * np.exp(np.cumsum(steps))


def run(strategy, frame):
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    return frame


class H105Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.strategy = Strategy()

    def test_class_constants(self) -> None:
        s = Strategy
        self.assertEqual(s.INTERFACE_VERSION, 3)
        self.assertEqual(s.timeframe, "1h")
        self.assertFalse(s.can_short)
        self.assertEqual(s.minimal_roi, {"0": 100.0})
        self.assertEqual(s.stoploss, -0.02)
        self.assertGreaterEqual(s.startup_candle_count, 362)
        self.assertEqual(
            self.strategy.protections,
            [{"method": "CooldownPeriod", "stop_duration_candles": 6}],
        )

    def test_block_values_match_manual_computation(self) -> None:
        closes = synthetic_closes(700)
        frame = run(self.strategy, make_frame(closes))
        # Block closes are the odd-hour bar closes (bars 1, 3, 5, ... from a 00:00 start).
        c = closes[1::2]
        last_block = len(c) - 1  # last odd bar index = 2*last_block + 1
        row = 2 * last_block + 1
        self.assertTrue(frame.loc[row, "block_end"])
        self.assertAlmostEqual(frame.loc[row, "block_close"], c[last_block])
        self.assertAlmostEqual(frame.loc[row, "sma50"], c[last_block - 49 : last_block + 1].mean())
        self.assertAlmostEqual(frame.loc[row, "sma20"], c[last_block - 19 : last_block + 1].mean())
        self.assertAlmostEqual(frame.loc[row, "hh10"], c[last_block - 10 : last_block].max())
        r = c[1:] / c[:-1] - 1.0  # r[k] belongs to block k+1
        j_now = r[last_block - 30 : last_block].max()  # blocks b-29..b
        self.assertAlmostEqual(frame.loc[row, "block_J"], j_now)
        prior_j = [r[k - 30 : k].max() for k in range(last_block - 150, last_block)]
        self.assertAlmostEqual(frame.loc[row, "block_J_median"], float(np.median(prior_j)))
        # The even bar after a block holds that block's values (forward fill), and is not a block end.
        self.assertFalse(frame.loc[row - 1, "block_end"])
        self.assertAlmostEqual(frame.loc[row - 1, "block_close"], c[last_block - 1])

    def test_signals_are_binary_and_present(self) -> None:
        frame = run(self.strategy, make_frame(synthetic_closes(1500)))
        self.assertGreater(int(frame["enter_long"].fillna(0).sum()), 0)
        for column in ("enter_long", "exit_long"):
            values = frame[column].dropna().unique().tolist()
            self.assertTrue(set(values).issubset({1}))

    def test_entries_only_at_block_close_with_fill_window(self) -> None:
        frame = run(self.strategy, make_frame(synthetic_closes(1500)))
        entries = frame[frame["enter_long"] == 1]
        self.assertGreater(len(entries), 0)
        for hour in entries["hour_utc"]:
            self.assertEqual(hour % 2, 1)
            self.assertLessEqual((hour + 1) % 24, 16)
        # Entry rule re-derived: regime, trend and breakout all hold on entry rows.
        self.assertTrue((entries["block_J"] >= entries["block_J_median"]).all())
        self.assertTrue((entries["block_close"] > entries["sma50"]).all())
        self.assertTrue((entries["block_close"] > entries["hh10"]).all())

    def test_zero_volume_produces_no_signal(self) -> None:
        frame = run(self.strategy, make_frame(synthetic_closes(1500), volume=0.0))
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(frame.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_single_zero_volume_bar_blocks_entry(self) -> None:
        base = run(self.strategy, make_frame(synthetic_closes(1500)))
        row = int(base.index[base["enter_long"] == 1][0])
        frame = make_frame(synthetic_closes(1500))
        frame.loc[row, "volume"] = 0.0
        changed = run(self.strategy, frame)
        self.assertNotEqual(changed.loc[row, "enter_long"], 1)

    def test_startup_values_produce_no_entry(self) -> None:
        frame = run(self.strategy, make_frame(synthetic_closes(1500)))
        # J needs 31 block closes and the median 150 earlier J values: 181 blocks = 362 bars,
        # so the first possible signal is the odd bar at row 361.
        self.assertEqual(int(frame.iloc[:361]["enter_long"].fillna(0).sum()), 0)
        short = run(self.strategy, make_frame(synthetic_closes(300)))
        self.assertEqual(int(short["enter_long"].fillna(0).sum()), 0)

    def test_session_exit_signal_at_2200_bar(self) -> None:
        frame = run(self.strategy, make_frame(synthetic_closes(500)))
        session = frame[frame["exit_tag"] == "session_flat_2300"]
        self.assertGreater(len(session), 0)
        self.assertTrue((session["hour_utc"] == 22).all())
        self.assertTrue((frame.loc[frame["hour_utc"] == 22, "exit_long"] == 1).all())

    def test_sma20_exit_at_block_close(self) -> None:
        up = np.linspace(100.0, 200.0, 600)
        down = np.linspace(200.0, 150.0, 100)
        frame = run(self.strategy, make_frame(np.concatenate([up, down])))
        sma_exits = frame[frame["exit_tag"] == "close_below_sma20"]
        self.assertGreater(len(sma_exits), 0)
        self.assertTrue((sma_exits["hour_utc"] % 2 == 1).all())
        self.assertTrue((sma_exits["block_close"] < sma_exits["sma20"]).all())

    def test_time_exit_12h(self) -> None:
        opened = datetime(2024, 3, 1, 4, 0, 5, tzinfo=timezone.utc)  # fill a few seconds after the open
        trade = FakeTrade(opened)
        before = datetime(2024, 3, 1, 15, 0, tzinfo=timezone.utc)
        at = datetime(2024, 3, 1, 16, 0, tzinfo=timezone.utc)
        self.assertIsNone(self.strategy.custom_exit("BTC/USDT", trade, before, 100.0, 0.05))
        self.assertEqual(
            self.strategy.custom_exit("BTC/USDT", trade, at, 100.0, 0.05), "time_exit_12h"
        )
        # No take-profit: a large profit alone does not exit.
        self.assertIsNone(self.strategy.custom_exit("BTC/USDT", trade, before, 100.0, 0.50))

    def test_no_lookahead_when_future_candles_are_appended(self) -> None:
        closes = synthetic_closes(1700)
        n, k = 1300, 400
        short = run(self.strategy, make_frame(closes[:n]))
        long = run(self.strategy, make_frame(closes[: n + k]))
        columns = [
            "block_close",
            "block_J",
            "block_J_median",
            "sma50",
            "sma20",
            "hh10",
            "block_end",
            "enter_long",
            "exit_long",
        ]
        pd.testing.assert_frame_equal(
            short.loc[: n - 1, columns].reset_index(drop=True),
            long.loc[: n - 1, columns].reset_index(drop=True),
            check_dtype=False,
        )
        self.assertGreater(int(short["enter_long"].fillna(0).sum()), 0)

    def test_missing_bar_voids_block(self) -> None:
        frame = make_frame(synthetic_closes(700))
        gap = 401  # an odd-hour bar: its block needs the preceding even bar
        frame = frame.drop(index=gap - 1).reset_index(drop=True)
        out = run(self.strategy, frame)
        row = out.index[out["date"] == START + timedelta(hours=gap)][0]
        self.assertFalse(out.loc[row, "block_end"])


if __name__ == "__main__":
    unittest.main()
