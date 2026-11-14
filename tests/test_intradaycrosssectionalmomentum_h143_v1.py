import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

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
CLASS_NAME = "IntradayCrossSectionalMomentum_H143_v1"


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Strategy = load_strategy(CLASS_NAME + ".py", CLASS_NAME)

START = pd.Timestamp("2024-01-01 00:00", tz="UTC")  # bar i has hour i % 24
BASE_COLS = {"open", "high", "low", "close", "volume", "date"}


class StubDP:
    def __init__(self, frames: dict):
        self.frames = frames

    def current_whitelist(self):
        return list(self.frames)

    def get_pair_dataframe(self, pair, timeframe):
        return self.frames[pair].copy()


def make_frame(closes, volumes) -> pd.DataFrame:
    closes = np.asarray(closes, dtype=float)
    n = len(closes)
    return pd.DataFrame(
        {
            "date": pd.date_range(START, periods=n, freq="1h"),
            "open": closes,
            "high": closes * 1.001,
            "low": closes * 0.999,
            "close": closes,
            "volume": np.asarray(volumes, dtype=float),
        }
    )


def run(frames: dict, pair: str, n: int | None = None) -> pd.DataFrame:
    """Run the three populate steps for ``pair``; frames are truncated to n rows if given."""
    if n is not None:
        frames = {name: frame.iloc[:n].reset_index(drop=True) for name, frame in frames.items()}
    strategy = Strategy()
    strategy.dp = StubDP(frames)
    frame = frames[pair].copy()
    frame = strategy.populate_indicators(frame, {"pair": pair})
    frame = strategy.populate_entry_trend(frame, {"pair": pair})
    frame = strategy.populate_exit_trend(frame, {"pair": pair})
    return frame


def flat_universe(n_pairs=12, bars=400) -> dict:
    return {
        f"P{i:02d}/USDT": make_frame([100.0] * bars, [100.0] * bars) for i in range(n_pairs)
    }


def surge(frame: pd.DataFrame, first: int, closes: list, volume: float) -> pd.DataFrame:
    """Set closes for bars first.. and volume 'volume' on the same bars (everything after keeps last close)."""
    frame = frame.copy()
    last = closes[-1]
    for offset, price in enumerate(closes):
        frame.loc[first + offset, ["open", "close"]] = price
    frame.loc[first + len(closes):, ["open", "close"]] = last
    frame["high"] = frame["close"] * 1.001
    frame["low"] = frame["close"] * 0.999
    frame.loc[first:first + len(closes) - 1, "volume"] = volume
    return frame


def random_universe(seed=7, n_pairs=12, bars=500) -> dict:
    rng = np.random.default_rng(seed)
    frames = {}
    for i in range(n_pairs):
        steps = rng.normal(0, 0.012, bars)
        closes = 100.0 * np.exp(np.cumsum(steps))
        volumes = rng.uniform(50, 150, bars) * (1 + 2 * (rng.random(bars) < 0.1))
        frames[f"R{i:02d}/USDT"] = make_frame(closes, volumes)
    return frames


class ContractTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertAlmostEqual(Strategy.stoploss, -0.012)
        self.assertGreaterEqual(Strategy.startup_candle_count, 124)
        self.assertEqual(Strategy.startup_candle_count, 200)

    def test_no_futures_marker(self) -> None:
        source = (ROOT / "user_data" / "strategies" / (CLASS_NAME + ".py")).read_text()
        self.assertNotIn("LAB_MARKET", source)

    def test_signal_columns_binary(self) -> None:
        frames = random_universe()
        for pair in list(frames)[:3]:
            frame = run(frames, pair)
            for column in ("enter_long", "exit_long"):
                self.assertIn(column, frame)
                self.assertTrue(set(frame[column].dropna().unique().tolist()).issubset({1}))
        total_entries = sum(
            int(run(frames, pair).get("enter_long", pd.Series(dtype=float)).fillna(0).sum())
            for pair in frames
        )
        self.assertGreater(total_entries, 0)


class SignalTests(unittest.TestCase):
    def scenario(self):
        frames = flat_universe()
        # bar 303 opens at 15:00 UTC (check bar); X surges 3% over bars 300..303 on 3x volume
        frames["P00/USDT"] = surge(
            frames["P00/USDT"], 300, [101.0, 102.0, 102.5, 103.0], 300.0
        )
        return frames

    def test_entry_on_leader_at_check_bar_only(self) -> None:
        frames = self.scenario()
        frame = run(frames, "P00/USDT")
        self.assertEqual(frame.loc[303, "date"].hour, 15)
        entries = frame.index[frame["enter_long"] == 1].tolist()
        self.assertEqual(entries, [303])
        self.assertEqual(frame.loc[303, "xs_rank"], 1)
        self.assertGreaterEqual(frame.loc[303, "vr"], 1.5)

    def test_non_leaders_do_not_enter(self) -> None:
        frames = self.scenario()
        frame = run(frames, "P01/USDT")
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_volume_filter(self) -> None:
        frames = self.scenario()
        # same price move, ordinary volume: VR = 1 < 1.5
        frames["P00/USDT"]["volume"] = 100.0
        frame = run(frames, "P00/USDT")
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_min_return_filter(self) -> None:
        frames = flat_universe()
        frames["P00/USDT"] = surge(frames["P00/USDT"], 300, [100.5, 101.0, 101.2, 101.4], 300.0)
        frame = run(frames, "P00/USDT")
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_not_a_check_bar(self) -> None:
        frames = flat_universe()
        # the surge completes at bar 302 (14:00 UTC), no check there; at 303 r4 is still >= 1.5%
        frames["P00/USDT"] = surge(frames["P00/USDT"], 299, [101.0, 102.0, 103.0, 103.0], 300.0)
        frame = run(frames, "P00/USDT")
        self.assertNotIn(302, frame.index[frame["enter_long"] == 1].tolist())

    def test_rank_must_be_within_top_five(self) -> None:
        frames = self.scenario()
        # five other pairs rise more than X over the same bars
        for i in range(1, 6):
            frames[f"P{i:02d}/USDT"] = surge(
                frames[f"P{i:02d}/USDT"], 300, [102.0, 103.0, 104.0, 104.0 + i], 100.0
            )
        frame = run(frames, "P00/USDT")
        self.assertEqual(frame.loc[303, "xs_rank"], 6)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        # with only four pairs ahead X is rank 5 and enters
        frames["P05/USDT"] = make_frame([100.0] * 400, [100.0] * 400)
        frame = run(frames, "P00/USDT")
        self.assertEqual(frame.loc[303, "xs_rank"], 5)
        self.assertEqual(frame.index[frame["enter_long"] == 1].tolist(), [303])

    def test_ties_broken_by_pair_name(self) -> None:
        frames = self.scenario()
        # P01 has exactly the same r4 as P00 (same closes); with 5 identical-or-better pairs
        for i in range(1, 6):
            frames[f"P{i:02d}/USDT"] = frames["P00/USDT"].copy()
        frame_p00 = run(frames, "P00/USDT")
        frame_p05 = run(frames, "P05/USDT")
        self.assertEqual(frame_p00.loc[303, "xs_rank"], 1)
        self.assertEqual(frame_p05.loc[303, "xs_rank"], 6)
        self.assertEqual(int(frame_p05.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_fewer_than_ten_counting_pairs(self) -> None:
        frames = flat_universe(n_pairs=9)
        frames["P00/USDT"] = surge(frames["P00/USDT"], 300, [101.0, 102.0, 102.5, 103.0], 300.0)
        frame = run(frames, "P00/USDT")
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        # a tenth pair makes the ranking valid
        frames["P09/USDT"] = make_frame([100.0] * 400, [100.0] * 400)
        frame = run(frames, "P00/USDT")
        self.assertEqual(frame.index[frame["enter_long"] == 1].tolist(), [303])

    def test_pair_without_candle_does_not_count(self) -> None:
        frames = self.scenario()
        # drop the candle of one pair at the check bar: 11 counting pairs remain
        frames["P11/USDT"] = frames["P11/USDT"].drop(index=303).reset_index(drop=True)
        frame = run(frames, "P00/USDT")
        self.assertEqual(frame.loc[303, "n_counting"], 11)
        # zero-volume (gap filled) candles do not count either
        frames = self.scenario()
        for i in range(8, 12):
            frames[f"P{i:02d}/USDT"].loc[303, "volume"] = 0.0
        frame = run(frames, "P00/USDT")
        self.assertEqual(frame.loc[303, "n_counting"], 8)
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_check_exit_when_leadership_lost(self) -> None:
        frames = self.scenario()
        frame = run(frames, "P00/USDT")
        # next check is bar 307 (19:00); X price flat since 303 so r4 = 0 < 1.5%
        self.assertEqual(frame.loc[307, "date"].hour, 19)
        self.assertEqual(frame.loc[307, "exit_long"], 1)
        # exit signals only occur on check bars
        exits = frame.index[frame["exit_long"] == 1]
        self.assertTrue(all(frame.loc[i, "date"].hour in (3, 7, 11, 15, 19, 23) for i in exits))
        # no exit signal on the entry bar itself
        self.assertTrue(pd.isna(frame.loc[303, "exit_long"]))

    def test_no_check_exit_while_still_leading(self) -> None:
        frames = flat_universe()
        frames["P00/USDT"] = surge(
            frames["P00/USDT"], 300, [101.0, 102.0, 102.5, 103.0, 104.0, 105.0, 106.0, 107.0], 300.0
        )
        frame = run(frames, "P00/USDT")
        # at 307: r4 = 107 / 103 - 1 = 3.9%, rank 1, hold even though VR may be high or low
        self.assertEqual(frame.loc[307, "xs_rank"], 1)
        self.assertTrue(pd.isna(frame.loc[307, "exit_long"]))

    def test_zero_volume_candle_gives_no_signal(self) -> None:
        frames = self.scenario()
        frames["P00/USDT"].loc[303, "volume"] = 0.0
        frame = run(frames, "P00/USDT")
        self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertTrue(pd.isna(frame.loc[303, "exit_long"]))
        frames = self.scenario()
        frames["P00/USDT"].loc[307, "volume"] = 0.0
        frame = run(frames, "P00/USDT")
        self.assertTrue(pd.isna(frame.loc[307, "exit_long"]))

    def test_all_zero_volume_gives_no_signals(self) -> None:
        frames = {name: frame.assign(volume=0.0) for name, frame in random_universe().items()}
        for pair in frames:
            frame = run(frames, pair)
            self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
            self.assertEqual(int(frame.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_undefined_startup_values_give_no_signal(self) -> None:
        frames = random_universe(seed=3)
        # first defined VR is at bar 123 (needs bars 0..123)
        for pair in frames:
            frame = run(frames, pair)
            self.assertTrue(frame["vr"].iloc[:123].isna().all())
            self.assertTrue(pd.notna(frame["vr"].iloc[123]))
            for column in ("enter_long", "exit_long"):
                if column in frame:
                    self.assertEqual(int(frame[column].iloc[:123].fillna(0).sum()), 0)

    def test_no_dataprovider_gives_no_entry(self) -> None:
        strategy = Strategy()
        self.assertEqual(strategy.informative_pairs(), [])
        frame = self.scenario()["P00/USDT"]
        frame = strategy.populate_indicators(frame, {"pair": "P00/USDT"})
        frame = strategy.populate_entry_trend(frame, {"pair": "P00/USDT"})
        self.assertNotIn("enter_long", frame)

    def test_informative_pairs_from_whitelist(self) -> None:
        strategy = Strategy()
        strategy.dp = StubDP(flat_universe(n_pairs=3))
        self.assertEqual(
            strategy.informative_pairs(),
            [("P00/USDT", "1h"), ("P01/USDT", "1h"), ("P02/USDT", "1h")],
        )


class NoLookaheadTests(unittest.TestCase):
    def test_signals_do_not_change_when_future_candles_are_appended(self) -> None:
        frames = random_universe(seed=11, bars=520)
        n, k = 400, 120
        for pair in list(frames)[:4]:
            short = run(frames, pair, n=n)
            long = run(frames, pair, n=n + k)
            # also: the full informative history is available while own rows are cut
            cols = [c for c in short.columns if c not in BASE_COLS]
            pd.testing.assert_frame_equal(
                short.loc[: n - 1, cols].reset_index(drop=True),
                long.loc[: n - 1, cols].reset_index(drop=True),
                check_dtype=False,
            )

    def test_signals_ignore_informative_future(self) -> None:
        frames = random_universe(seed=13, bars=520)
        pair = "R00/USDT"
        n = 400
        own = frames[pair].iloc[:n].reset_index(drop=True)
        strategy = Strategy()
        strategy.dp = StubDP(frames)  # informative frames extend beyond n
        a = strategy.populate_exit_trend(
            strategy.populate_entry_trend(
                strategy.populate_indicators(own.copy(), {"pair": pair}), {"pair": pair}
            ),
            {"pair": pair},
        )
        b = run(frames, pair, n=n)
        cols = [c for c in b.columns if c not in BASE_COLS]
        pd.testing.assert_frame_equal(a[cols], b[cols], check_dtype=False)


class CustomExitTests(unittest.TestCase):
    OPEN = datetime(2024, 3, 1, 3, 0, tzinfo=timezone.utc)

    def trade(self):
        return SimpleNamespace(open_date_utc=self.OPEN)

    def call(self, hours, profit):
        return Strategy().custom_exit(
            "P00/USDT", self.trade(), self.OPEN + timedelta(hours=hours), 100.0, profit
        )

    def test_take_profit(self) -> None:
        self.assertEqual(self.call(2, 0.02), "take_profit_2pct")
        self.assertEqual(self.call(2, 0.05), "take_profit_2pct")
        self.assertIsNone(self.call(2, 0.0199))

    def test_time_exit_after_12_hours(self) -> None:
        self.assertIsNone(self.call(11, 0.005))
        self.assertEqual(self.call(12, 0.005), "time_exit_12h")
        self.assertEqual(self.call(12, -0.01), "time_exit_12h")
        self.assertEqual(self.call(30, -0.01), "time_exit_12h")

    def test_no_exit_when_neither_applies(self) -> None:
        self.assertIsNone(self.call(5, -0.005))


if __name__ == "__main__":
    unittest.main()
