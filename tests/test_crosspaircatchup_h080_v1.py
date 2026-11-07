import importlib.util
import sys
import types
import unittest
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

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
NAME = "CrossPairCatchUp_H080_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, NAME)


Strategy = load_strategy()
BAR = timedelta(minutes=15)
SURGES = (300, 900, 1100)


class FakeDP:
    def __init__(self, frames, analyzed=None):
        self.frames = frames
        self.analyzed = analyzed

    def get_pair_dataframe(self, pair, timeframe):
        return self.frames[pair].copy()

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.analyzed, None


class FakeTrade:
    def __init__(self, open_date, open_rate):
        self.open_date_utc = open_date
        self.open_rate = open_rate


def frame_from_returns(returns, volumes):
    closes = 100.0 * np.cumprod(1.0 + np.asarray(returns))
    n = len(closes)
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=n, freq="15min", tz="UTC"),
            "open": closes,
            "high": closes * 1.002,
            "low": closes * 0.998,
            "close": closes,
            "volume": volumes,
        }
    )


def make_series(total, seed):
    rng = np.random.default_rng(seed)
    lead_ret = rng.normal(0.0002, 0.001, total)
    lead_vol = rng.uniform(0.8, 1.2, total)
    pair_ret = rng.normal(0.0, 0.001, total)
    for s in SURGES:
        if s < total:
            lead_ret[s] = 0.012
            lead_vol[s] = 5.0
            pair_ret[s] = 0.001
    lead_ret[0] = 0.0
    pair_ret[0] = 0.0
    return lead_ret, lead_vol, pair_ret


def build(n, total=None, volume=None, seed=7):
    total = total or n
    lead_ret, lead_vol, pair_ret = make_series(total, seed)
    leader = frame_from_returns(lead_ret[:n], lead_vol[:n])
    pair_vol = np.ones(n) if volume is None else np.full(n, volume)
    pair = frame_from_returns(pair_ret[:n], pair_vol)
    strat = Strategy()
    strat.dp = FakeDP({"BTC/USDT": leader})
    return strat, pair


def run(strat, frame, pair="ETH/USDT"):
    meta = {"pair": pair}
    frame = strat.populate_indicators(frame, meta)
    frame = strat.populate_entry_trend(frame, meta)
    return strat.populate_exit_trend(frame, meta)


class H080Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertAlmostEqual(Strategy.stoploss, -0.03)
        self.assertGreaterEqual(Strategy.startup_candle_count, 673)

    def test_leader_choice(self):
        strat, frame = build(800)
        strat.dp = FakeDP({"ETH/USDT": strat.dp.frames["BTC/USDT"]})
        out = run(strat, frame, pair="BTC/USDT")
        self.assertTrue(out["lead_close"].notna().all())

    def test_signals_binary_and_surge_entries(self):
        strat, frame = build(1300)
        out = run(strat, frame)
        self.assertIn("enter_long", out)
        self.assertTrue(set(out["enter_long"].dropna().unique().tolist()).issubset({1}))
        entries = out.index[out["enter_long"] == 1].tolist()
        self.assertIn(900, entries)
        self.assertIn(1100, entries)
        if "exit_long" in out:
            self.assertTrue(set(out["exit_long"].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_no_signal(self):
        strat, frame = build(1300, volume=0.0)
        out = run(strat, frame)
        self.assertEqual(int(out.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(out.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self):
        strat, frame = build(1300)
        out = run(strat, frame)
        self.assertTrue(out["lead_sigma"].iloc[:673].isna().all())
        self.assertEqual(int(out.iloc[:673]["enter_long"].fillna(0).sum()), 0)
        self.assertNotEqual(out.loc[300, "enter_long"], 1)

    def test_no_lookahead(self):
        n, total = 1000, 1300
        strat_a, frame_a = build(n, total=total)
        strat_b, frame_b = build(total, total=total)
        a = run(strat_a, frame_a)
        b = run(strat_b, frame_b)
        cols = ["lead_ret", "lead_sigma", "lead_vol_ratio", "lead_sma", "pair_ret", "catchup_target"]
        pd.testing.assert_frame_equal(a.loc[: n - 1, cols], b.loc[: n - 1, cols])
        pd.testing.assert_series_equal(
            a["enter_long"].iloc[:n].fillna(0), b["enter_long"].iloc[:n].fillna(0), check_dtype=False
        )

    def _exit_setup(self):
        strat, frame = build(1300)
        out = run(strat, frame)
        strat.dp.analyzed = out
        open_date = out.loc[901, "date"]
        trade = FakeTrade(open_date, out.loc[901, "open"])
        return strat, out, trade

    def _exit_at(self, strat, trade, out, closed_index):
        current_time = out.loc[closed_index, "date"] + BAR
        return strat.custom_exit("ETH/USDT", trade, current_time, 0.0, 0.0)

    def test_custom_exit_target_and_level(self):
        strat, out, trade = self._exit_setup()
        target = out.loc[900, "catchup_target"]
        out.loc[905, "close"] = target * 1.0001
        self.assertEqual(self._exit_at(strat, trade, out, 905), "catchup_target")
        level = trade.open_rate * (1 - 1.5 * out.loc[900, "lead_ret"])
        out.loc[906, "close"] = level * 0.999
        self.assertEqual(self._exit_at(strat, trade, out, 906), "catchup_fail_level")
        out.loc[907, "volume"] = 0.0
        out.loc[907, "close"] = level * 0.999
        self.assertIsNone(self._exit_at(strat, trade, out, 907))

    def test_custom_exit_time_cap_and_entry_bar(self):
        strat, out, trade = self._exit_setup()
        target = out.loc[900, "catchup_target"]
        level = trade.open_rate * (1 - 1.5 * out.loc[900, "lead_ret"])
        out.loc[901:930, "close"] = (target + level) / 2
        # Signal bar itself is not evaluated.
        out.loc[900, "close"] = level * 0.5
        self.assertIsNone(self._exit_at(strat, trade, out, 900))
        # Bars 1..15 of the trade: no exit; close of the 16th bar (index 916): exit.
        self.assertIsNone(self._exit_at(strat, trade, out, 901))
        self.assertIsNone(self._exit_at(strat, trade, out, 915))
        self.assertEqual(self._exit_at(strat, trade, out, 916), "time_exit_16")
        # Data later than current_time is ignored.
        out.loc[905, "close"] = target * 2
        self.assertIsNone(self._exit_at(strat, trade, out, 904))


if __name__ == "__main__":
    unittest.main()
