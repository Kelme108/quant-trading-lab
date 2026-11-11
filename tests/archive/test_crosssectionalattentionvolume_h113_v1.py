import importlib.util
import sys
import types
import unittest
from unittest import mock
from pathlib import Path

import numpy as np
import pandas as pd


# Keep the tests runnable without installing Freqtrade or TA-Lib on the host.
freqtrade = types.ModuleType("freqtrade")
strategy_module = types.ModuleType("freqtrade.strategy")
strategy_module.IStrategy = object
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


ROOT = Path(__file__).parents[2]
NAME = "CrossSectionalAttentionVolume_H113_v1"


def load():
    path = ROOT / "user_data" / "strategies" / "_archive" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load()
Strategy = getattr(MODULE, NAME)
PAIRS = MODULE.PAIRS
TRADED = "SOL/USDT"
N_BARS = 520
S = 479  # signal bar
BURST = range(S - 3, S + 1)  # bars 476..479


def make_universe(
    n_bars: int = N_BARS,
    burst_pairs=(TRADED,),
    burst_volume: float = 300.0,
    burst_ret: float = 0.004,
    burst_ret_by_pair: dict = None,
    burst_bars=BURST,
    all_ret: float = None,
    seed=None,
) -> dict:
    """Deterministic universe: flat prices, volume 100, a burst on the chosen pairs."""
    rng = np.random.default_rng(seed) if seed is not None else None
    dates = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")
    frames = {}
    for pair in PAIRS:
        returns = np.zeros(n_bars)
        volume = np.full(n_bars, 100.0)
        if rng is not None:
            returns = rng.normal(0.0, 0.001, n_bars)
            volume = 100.0 + rng.uniform(-5.0, 5.0, n_bars)
        if all_ret is not None:
            for b in burst_bars:
                returns[b] = all_ret
        if pair in burst_pairs:
            for b in burst_bars:
                returns[b] = (burst_ret_by_pair or {}).get(pair, burst_ret)
                volume[b] = burst_volume
        close = 100.0 * np.exp(np.cumsum(returns))
        open_ = np.concatenate([[close[0]], close[:-1]])
        frames[pair] = pd.DataFrame(
            {
                "date": dates,
                "open": open_,
                "high": np.maximum(open_, close) * 1.001,
                "low": np.minimum(open_, close) * 0.999,
                "close": close,
                "volume": volume,
            }
        )
    return frames


class FakeDataProvider:
    def __init__(self, frames: dict):
        self.frames = frames

    def get_pair_dataframe(self, pair, timeframe):
        return self.frames[pair].copy()


def run(frames: dict, pair: str = TRADED) -> pd.DataFrame:
    strategy = Strategy()
    strategy.dp = FakeDataProvider(frames)
    metadata = {"pair": pair}
    frame = strategy.populate_indicators(frames[pair].copy(), metadata)
    frame = strategy.populate_entry_trend(frame, metadata)
    frame = strategy.populate_exit_trend(frame, metadata)
    return frame


def entries(frame: pd.DataFrame) -> list:
    if "enter_long" not in frame:
        return []
    return frame.index[frame["enter_long"].fillna(0) == 1].tolist()


def truncate(frames: dict, n: int) -> dict:
    return {pair: frame.iloc[:n].copy() for pair, frame in frames.items()}


class FakeTrade:
    def __init__(self, open_date):
        self.open_date_utc = open_date


class CrossSectionalAttentionVolumeTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.01)
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 172)
        self.assertEqual(Strategy.startup_candle_count, 400)
        self.assertEqual(
            Strategy().protections,
            [{"method": "CooldownPeriod", "stop_duration_candles": 2}],
        )
        self.assertEqual(len(PAIRS), 9)
        self.assertEqual(Strategy().informative_pairs(), [(p, "1h") for p in PAIRS])

    def test_engineered_burst_creates_entries(self) -> None:
        frame = run(make_universe())
        self.assertEqual(frame.loc[S, "enter_long"], 1)
        self.assertEqual(frame.loc[S, "enter_tag"], "attention_leader")
        self.assertAlmostEqual(frame.loc[S, "av"], 3.0)
        self.assertEqual(frame.loc[S, "xs_rank"], 1)
        self.assertEqual(frame.loc[S, "xs_count"], 9)
        # Bar 476 has AV 1.5 but R4 only 0.4%; bar 480 is not a green bar.
        self.assertEqual(entries(frame), [S - 2, S - 1, S])

    def test_signal_columns_are_binary(self) -> None:
        for frames in (make_universe(), make_universe(seed=3)):
            frame = run(frames)
            for column in ("enter_long", "exit_long"):
                if column in frame:
                    values = frame[column].dropna().unique().tolist()
                    self.assertTrue(set(values).issubset({1}))

    def test_rank_two_allowed_rank_three_not(self) -> None:
        # Two other pairs with larger abnormal volume: X is rank 3 -> no signal.
        frames = make_universe(burst_pairs=(TRADED,))
        for other, vol in (("BTC/USDT", 500.0), ("ETH/USDT", 400.0)):
            frames[other].loc[list(BURST), "volume"] = vol
        frame = run(frames)
        self.assertEqual(frame.loc[S, "xs_rank"], 3)
        self.assertTrue(pd.isna(frame.loc[S].get("enter_long", np.nan)))

        # Only one pair above X: rank 2 -> signal.
        frames = make_universe(burst_pairs=(TRADED,))
        frames["BTC/USDT"].loc[list(BURST), "volume"] = 500.0
        frame = run(frames)
        self.assertEqual(frame.loc[S, "xs_rank"], 2)
        self.assertEqual(frame.loc[S, "enter_long"], 1)

    def test_ties_break_by_r4_then_name(self) -> None:
        # Exact AV ties (3.0). Larger R4 ranks first.
        frames = make_universe(
            burst_pairs=(TRADED, "BTC/USDT", "ETH/USDT"),
            burst_ret_by_pair={"BTC/USDT": 0.006, "ETH/USDT": 0.005, TRADED: 0.004},
        )
        frame = run(frames)
        self.assertEqual(frame.loc[S, "xs_rank"], 3)
        self.assertTrue(pd.isna(frame.loc[S].get("enter_long", np.nan)))

        # Same AV and same R4: pair name ascending. SOL is last among three.
        frames = make_universe(burst_pairs=(TRADED, "ADA/USDT", "BNB/USDT"))
        frame = run(frames)
        self.assertEqual(frame.loc[S, "xs_rank"], 3)
        self.assertTrue(pd.isna(frame.loc[S].get("enter_long", np.nan)))

        # Name tie-break with only two tied pairs: SOL is rank 2 -> signal.
        frames = make_universe(burst_pairs=(TRADED, "ADA/USDT"))
        frame = run(frames)
        self.assertEqual(frame.loc[S, "xs_rank"], 2)
        self.assertEqual(frame.loc[S, "enter_long"], 1)

        # Trading ADA with the same data: ADA is rank 1 by name.
        frame = run(frames, pair="ADA/USDT")
        self.assertEqual(frame.loc[S, "xs_rank"], 1)

    def test_abnormal_volume_below_threshold_gives_no_signal(self) -> None:
        # AV = 4 * 140 / 400 = 1.4 < 1.5.
        frame = run(make_universe(burst_volume=140.0))
        self.assertAlmostEqual(frame.loc[S, "av"], 1.4)
        self.assertEqual(entries(frame), [])

    def test_weak_return_gives_no_signal(self) -> None:
        frame = run(make_universe(burst_ret=0.0014))  # R4 about 0.56% < 0.6%
        self.assertEqual(entries(frame), [])

    def test_return_must_exceed_median_strictly(self) -> None:
        # Every pair moves the same, so R4_X equals the cross-sectional median.
        frame = run(make_universe(all_ret=0.004))
        self.assertAlmostEqual(frame.loc[S, "r4"], frame.loc[S, "xs_median"])
        self.assertEqual(entries(frame), [])

    def test_signal_bar_must_be_green(self) -> None:
        frames = make_universe()
        frames[TRADED].loc[list(BURST), "open"] = frames[TRADED].loc[list(BURST), "close"] * 1.01
        frame = run(frames)
        self.assertEqual(entries(frame), [])

    def test_fewer_than_five_counting_pairs_gives_no_signal(self) -> None:
        others = [p for p in PAIRS if p != TRADED]
        frames = make_universe()
        for pair in others[:4]:
            frames[pair].loc[:, "close"] = np.nan
        frame = run(frames)
        self.assertEqual(frame.loc[S, "xs_count"], 5)
        self.assertEqual(frame.loc[S, "enter_long"], 1)

        frames = make_universe()
        for pair in others[:5]:
            frames[pair].loc[:, "close"] = np.nan
        frame = run(frames)
        self.assertEqual(frame.loc[S, "xs_count"], 4)
        self.assertEqual(entries(frame), [])

    def test_pair_outside_universe_gives_no_signal(self) -> None:
        frames = make_universe()
        frames["FOO/USDT"] = frames[TRADED].copy()
        frame = run(frames, pair="FOO/USDT")
        self.assertEqual(entries(frame), [])

    def test_zero_volume_produces_no_signal(self) -> None:
        frames = make_universe()
        frames[TRADED].loc[S, "volume"] = 0.0
        frame = run(frames)
        self.assertTrue(pd.isna(frame.loc[S].get("enter_long", np.nan)))

        frames = make_universe()
        frames[TRADED]["volume"] = 0.0
        frame = run(frames)
        self.assertEqual(int(frame.get("enter_long", pd.Series()).fillna(0).sum()), 0)

        frames = make_universe(seed=5)
        for pair in PAIRS:
            frames[pair]["volume"] = 0.0
        frame = run(frames)
        self.assertEqual(int(frame.get("enter_long", pd.Series()).fillna(0).sum()), 0)

    def test_startup_values_produce_no_signal(self) -> None:
        frame = run(make_universe(seed=7))
        # V4 needs 4 bars and Base reaches back to V4(t-168): first defined bar is 171.
        self.assertTrue(frame["av"].iloc[:171].isna().all())
        self.assertTrue(pd.notna(frame.loc[171, "av"]))
        self.assertEqual(
            int(frame.iloc[: Strategy.startup_candle_count].get("enter_long", pd.Series()).fillna(0).sum()),
            0,
        )

        # A burst inside the undefined start-up region gives no signal.
        early = (97, 98, 99, 100)
        frames = make_universe(burst_bars=early)
        frame = run(frames)
        self.assertEqual(int(frame.get("enter_long", pd.Series()).fillna(0).sum()), 0)
        self.assertTrue(frame["av"].iloc[:171].isna().all())

        # Right after the first defined bar the same burst does signal.
        late = (174, 175, 176, 177)
        frame = run(make_universe(burst_bars=late))
        self.assertIn(177, entries(frame))

    def test_no_lookahead_when_candles_appended(self) -> None:
        for builder in (lambda: make_universe(), lambda: make_universe(seed=11)):
            full = builder()
            long = run(full)
            for n in (S + 1, 495, 510):
                short = run(truncate(full, n))
                columns = [
                    c
                    for c in ("av", "r4", "xs_count", "xs_median", "xs_rank", "enter_long")
                    if c in short.columns or c in long.columns
                ]
                for c in columns:
                    if c not in short:
                        short[c] = np.nan
                    if c not in long:
                        long[c] = np.nan
                pd.testing.assert_frame_equal(
                    short.loc[: n - 1, columns].reset_index(drop=True),
                    long.loc[: n - 1, columns].reset_index(drop=True),
                    check_dtype=False,
                )

    def test_custom_exit_take_profit(self) -> None:
        strategy = Strategy()
        fill = pd.Timestamp("2024-02-01 10:00", tz="UTC")
        trade = FakeTrade(fill.to_pydatetime())
        now = fill + pd.Timedelta(hours=1)
        self.assertIsNone(strategy.custom_exit(TRADED, trade, now, 100.0, 0.0179))
        self.assertEqual(strategy.custom_exit(TRADED, trade, now, 100.0, 0.018), "take_profit_1p8")
        self.assertEqual(strategy.custom_exit(TRADED, trade, now, 100.0, 0.05), "take_profit_1p8")
        self.assertIsNone(strategy.custom_exit(TRADED, trade, now, 100.0, -0.009))

    def test_custom_exit_time_exit_after_six_hours(self) -> None:
        strategy = Strategy()
        fill = pd.Timestamp("2024-02-01 10:00", tz="UTC")
        trade = FakeTrade((fill + pd.Timedelta(seconds=7)).to_pydatetime())
        # Exit signal at the close of bar e+5, i.e. fill at the open of e+6.
        for hours in range(0, 6):
            now = fill + pd.Timedelta(hours=hours)
            self.assertIsNone(strategy.custom_exit(TRADED, trade, now, 100.0, 0.0), hours)
        now = fill + pd.Timedelta(hours=5, minutes=59)
        self.assertIsNone(strategy.custom_exit(TRADED, trade, now, 100.0, 0.0))
        now = fill + pd.Timedelta(hours=6)
        self.assertEqual(strategy.custom_exit(TRADED, trade, now, 100.0, -0.005), "time_exit_6h")
        now = fill + pd.Timedelta(hours=9)
        self.assertEqual(strategy.custom_exit(TRADED, trade, now, 100.0, 0.0), "time_exit_6h")

    def test_at_most_two_entries_per_utc_day(self) -> None:
        def fake_trades(opens):
            class FakeTradeClass:
                @staticmethod
                def get_trades_proxy(**kwargs):
                    return [FakeTrade(pd.Timestamp(o, tz="UTC").to_pydatetime()) for o in opens]

            return FakeTradeClass

        strategy = Strategy()
        now = pd.Timestamp("2024-02-01 20:00", tz="UTC").to_pydatetime()

        def confirm(opens):
            with mock.patch.object(MODULE, "Trade", fake_trades(opens)):
                return strategy.confirm_trade_entry(
                    TRADED, "limit", 1.0, 100.0, "GTC", now, "attention_leader", "long"
                )

        self.assertTrue(confirm([]))
        self.assertTrue(confirm(["2024-02-01 03:00"]))
        self.assertFalse(confirm(["2024-02-01 03:00", "2024-02-01 09:00"]))
        self.assertTrue(confirm(["2024-01-31 03:00", "2024-01-31 09:00", "2024-02-01 09:00"]))


if __name__ == "__main__":
    unittest.main()
