import importlib.util
import sys
import types
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


def _merge_informative_pair(dataframe, informative, timeframe, timeframe_inf, ffill=True):
    inf = informative.copy()
    inf.columns = [f"{c}_{timeframe_inf}" for c in inf.columns]
    inf["date_merge"] = inf[f"date_{timeframe_inf}"] + pd.Timedelta(days=1)
    merged = pd.merge_asof(
        dataframe.sort_values("date"),
        inf.sort_values("date_merge"),
        left_on="date",
        right_on="date_merge",
        direction="backward",
    )
    return merged.drop(columns=["date_merge"])


freqtrade = types.ModuleType("freqtrade")
strategy_module = types.ModuleType("freqtrade.strategy")
strategy_module.IStrategy = object
strategy_module.merge_informative_pair = _merge_informative_pair
freqtrade.strategy = strategy_module
sys.modules.setdefault("freqtrade", freqtrade)
sys.modules.setdefault("freqtrade.strategy", strategy_module)
if not hasattr(sys.modules["freqtrade.strategy"], "merge_informative_pair"):
    sys.modules["freqtrade.strategy"].merge_informative_pair = _merge_informative_pair

talib = types.ModuleType("talib")
talib_abstract = types.ModuleType("talib.abstract")
talib_abstract.SMA = lambda dataframe, timeperiod: dataframe["close"].rolling(timeperiod).mean()
talib_abstract.RSI = lambda dataframe, timeperiod: pd.Series(50.0, index=dataframe.index)
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)

ROOT = Path(__file__).parents[1]


def load_strategy():
    path = ROOT / "user_data" / "strategies" / "DonchianEnsemble_H018_v1.py"
    spec = importlib.util.spec_from_file_location("DonchianEnsemble_H018_v1", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.merge_informative_pair = _merge_informative_pair
    return module.DonchianEnsemble_H018_v1


Strategy = load_strategy()


class FakeDP:
    def __init__(self, daily):
        self.daily = daily

    def get_pair_dataframe(self, pair, timeframe):
        return self.daily.copy()


def make_hourly(days, seed=1):
    rng = np.random.default_rng(seed)
    hours = days * 24
    price = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, hours)))
    date = pd.date_range("2020-01-01", periods=hours, freq="h", tz="UTC")
    return pd.DataFrame(
        {
            "date": date,
            "open": price,
            "high": price * 1.005,
            "low": price * 0.995,
            "close": price,
            "volume": 1.0,
        }
    )


def to_daily(hourly):
    d = hourly.set_index("date").resample("1D").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    )
    return d.reset_index()


def run(hourly, daily):
    s = Strategy()
    s.dp = FakeDP(daily)
    f = s.populate_indicators(hourly.copy(), {"pair": "BTC/USDT"})
    f = s.populate_entry_trend(f, {})
    f = s.populate_exit_trend(f, {})
    return f


class DonchianEnsembleTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 400)

    def test_signals_binary(self) -> None:
        h = make_hourly(700)
        f = run(h, to_daily(h))
        for col in ("enter_long", "exit_long"):
            self.assertTrue(set(f[col].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(f["enter_long"].sum(), 0)

    def test_zero_volume_no_signal(self) -> None:
        h = make_hourly(700)
        d = to_daily(h)
        h["volume"] = 0.0
        f = run(h, d)
        self.assertEqual(int(f["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(f["exit_long"].fillna(0).sum()), 0)

    def test_undefined_startup_no_signal(self) -> None:
        h = make_hourly(700)
        d = to_daily(h)
        f = run(h, d)
        # first day has no closed daily candle yet: no signals of any kind
        first = f.iloc[:24]
        self.assertEqual(int(first["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(first["exit_long"].fillna(0).sum()), 0)
        # before the 200-day channel exists, a member is OFF, so at most 3 can vote
        self.assertTrue(f["votes_1d"].iloc[24:].notna().all())

    def test_latch_and_vote(self) -> None:
        days = 300
        price = np.concatenate([np.full(120, 100.0), np.linspace(100, 200, 60), np.full(120, 200.0)])
        date = pd.date_range("2020-01-01", periods=days, freq="D", tz="UTC")
        daily = pd.DataFrame(
            {"date": date, "open": price, "high": price, "low": price, "close": price, "volume": 1.0}
        )
        hourly = pd.DataFrame(
            {
                "date": pd.date_range("2020-01-01", periods=days * 24, freq="h", tz="UTC"),
                "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0,
            }
        )
        f = run(hourly, daily)
        self.assertGreaterEqual(f["votes_1d"].iloc[-1], 2)
        self.assertEqual(f["enter_long"].iloc[-1], 1)

    def test_no_lookahead(self) -> None:
        full = make_hourly(700)
        n = 24 * 600
        first = full.iloc[:n]
        a = run(first, to_daily(first))
        b = run(full, to_daily(full)).iloc[:n]
        for col in ("votes_1d", "enter_long", "exit_long"):
            pd.testing.assert_series_equal(
                a[col].reset_index(drop=True), b[col].reset_index(drop=True), check_dtype=False
            )


if __name__ == "__main__":
    unittest.main()
