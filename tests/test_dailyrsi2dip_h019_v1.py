import importlib.util
import sys
import types
import unittest
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


def merge_informative_pair(dataframe, informative, timeframe, timeframe_inf, ffill=True):
    """Minimal stand-in: a daily candle becomes visible once its day has closed (date + 1 day)."""
    inf = informative.copy()
    inf["date"] = inf["date"] + pd.Timedelta(days=1)
    inf = inf.rename(columns={c: f"{c}_{timeframe_inf}" for c in inf.columns})
    inf = inf.rename(columns={f"date_{timeframe_inf}": f"date_{timeframe_inf}"})
    merged = pd.merge_asof(
        dataframe.sort_values("date"), inf, left_on="date", right_on=f"date_{timeframe_inf}"
    )
    return merged


_host = sys.modules["freqtrade.strategy"]
if not hasattr(_host, "merge_informative_pair"):
    _host.merge_informative_pair = merge_informative_pair
MERGE = _host.merge_informative_pair

ROOT = Path(__file__).parents[1]
path = ROOT / "user_data" / "strategies" / "DailyRSI2Dip_H019_v1.py"
spec = importlib.util.spec_from_file_location("DailyRSI2Dip_H019_v1", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Strategy = module.DailyRSI2Dip_H019_v1


class FakeDP:
    def __init__(self, daily):
        self.daily = daily

    def get_pair_dataframe(self, pair, timeframe):
        return self.daily.copy()


def make_hourly(days_prices, volume=1.0):
    daily_dates = pd.date_range("2022-01-01", periods=len(days_prices), freq="1D", tz="UTC")
    daily = pd.DataFrame(
        {
            "date": daily_dates,
            "open": days_prices,
            "high": days_prices,
            "low": days_prices,
            "close": days_prices,
            "volume": volume,
        }
    )
    hourly_dates = pd.date_range(daily_dates[0], periods=len(days_prices) * 24, freq="1h", tz="UTC")
    hourly = pd.DataFrame({"date": hourly_dates})
    for col in ("open", "high", "low", "close"):
        hourly[col] = np.repeat(days_prices, 24)
    hourly["volume"] = volume
    return hourly, daily


def run(strategy_daily, hourly, daily):
    # Make the merge helper visible to the strategy module regardless of stub order.
    module.merge_informative_pair = MERGE
    strat = Strategy()
    strat.dp = FakeDP(daily)
    frame = strat.populate_indicators(hourly.copy(), {"pair": "BTC/USDT"})
    frame = strat.populate_entry_trend(frame, {})
    frame = strat.populate_exit_trend(frame, {})
    return frame


def prices(n):
    rng = np.random.default_rng(3)
    return list(100 * np.exp(np.cumsum(rng.normal(0.002, 0.03, n))))


class DailyRSI2DipTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertGreaterEqual(Strategy.startup_candle_count, 400)

    def test_wilder_rsi_seed(self) -> None:
        rsi = module.wilder_rsi(pd.Series([10.0, 11.0, 10.0, 9.0]), 2)
        self.assertTrue(rsi.iloc[:2].isna().all())
        # seed: avg gain 0.5, avg loss 0.5 -> RSI 50 at index 2
        self.assertAlmostEqual(rsi.iloc[2], 50.0)
        # index 3: gain (0.5+0)/2=0.25, loss (0.5+1)/2=0.75 -> 25
        self.assertAlmostEqual(rsi.iloc[3], 25.0)

    def test_signals_binary_and_present(self) -> None:
        # long uptrend then a sharp 3-day dip, then recovery
        p = [100.0 + i * 0.5 for i in range(260)]
        p += [p[-1] * 0.97, p[-1] * 0.93, p[-1] * 0.90, p[-1] * 0.98, p[-1] * 1.05]
        hourly, daily = make_hourly(p)
        frame = run(None, hourly, daily)
        for col in ("enter_long", "exit_long"):
            self.assertTrue(set(frame[col].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(frame["enter_long"].fillna(0).sum(), 0)

    def test_zero_volume_no_signal(self) -> None:
        p = [100.0 + i * 0.5 for i in range(260)] + [200.0, 150.0, 120.0]
        hourly, daily = make_hourly(p, volume=0.0)
        frame = run(None, hourly, daily)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame["exit_long"].fillna(0).sum()), 0)

    def test_undefined_startup_no_signal(self) -> None:
        p = prices(260)
        hourly, daily = make_hourly(p)
        frame = run(None, hourly, daily)
        first_valid = 199 * 24 + 24  # SMA(200) visible only after day 200 closes
        self.assertEqual(int(frame.iloc[:first_valid]["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame.iloc[:first_valid]["exit_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self) -> None:
        p = prices(320)
        n_days = 280
        h1, d1 = make_hourly(p[:n_days])
        h2, d2 = make_hourly(p)
        a = run(None, h1, d1)
        b = run(None, h2, d2).iloc[: len(a)]
        cols = ["enter_long", "exit_long"]
        pd.testing.assert_frame_equal(
            a[cols].reset_index(drop=True).fillna(0),
            b[cols].reset_index(drop=True).fillna(0),
            check_dtype=False,
        )
        ind = ["dclose_1d", "rsi2_1d", "sma200_1d", "sma5_1d"]
        pd.testing.assert_frame_equal(
            a[ind].reset_index(drop=True), b[ind].reset_index(drop=True), check_dtype=False
        )


if __name__ == "__main__":
    unittest.main()
