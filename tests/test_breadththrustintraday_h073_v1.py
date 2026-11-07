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

ROOT = Path(__file__).parents[1]
NAME = "BreadthThrustIntraday_H073_v1"


def load_module():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()
Strategy = getattr(MODULE, NAME)
PAIRS = MODULE.PAIRS
TRADED = "ETH/USDT"


class FakeDP:
    def __init__(self, frames, analyzed=None):
        self.frames = frames
        self.analyzed = analyzed

    def get_pair_dataframe(self, pair, timeframe):
        return self.frames[pair].copy()

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.analyzed, None


class FakeTrade:
    def __init__(self, open_date):
        self.open_date_utc = open_date
        self.open_rate = 100.0


def make_frame(prices, volume=1.0):
    n = len(prices)
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=n, freq="1h"),
            "open": prices,
            "high": [p * 1.01 for p in prices],
            "low": [p * 0.99 for p in prices],
            "close": prices,
            "volume": [volume] * n,
        }
    )


def make_universe(total):
    """Strongly correlated hourly random walks so that breadth swings widely."""
    rng = np.random.default_rng(7)
    common = rng.normal(0.0, 0.01, total)
    series = {}
    for i, pair in enumerate(PAIRS):
        own = np.random.default_rng(100 + i).normal(0.0, 0.004, total)
        series[pair] = list(100.0 * np.exp(np.cumsum(common + own)))
    return series


def build(n, volume=1.0, total=None):
    total = total or n
    series = make_universe(total)
    frames = {pair: make_frame(values[:n]) for pair, values in series.items()}
    strat = Strategy()
    strat.dp = FakeDP(frames)
    return strat, make_frame(series[TRADED][:n], volume)


def run(strat, frame):
    meta = {"pair": TRADED}
    frame = strat.populate_indicators(frame, meta)
    frame = strat.populate_entry_trend(frame, meta)
    return strat.populate_exit_trend(frame, meta)


class H073Tests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertAlmostEqual(Strategy.stoploss, -0.03)
        self.assertGreaterEqual(Strategy.startup_candle_count, 200)
        self.assertEqual(len(PAIRS), 9)
        self.assertEqual(Strategy().informative_pairs(), [(p, "1h") for p in PAIRS])

    def test_breadth_definition(self):
        dates = pd.date_range("2024-01-01", periods=4, freq="1h")
        up = pd.Series([1.0, 2.0, 3.0, 3.0], index=dates)
        down = pd.Series([3.0, 2.0, 1.0, 1.0], index=dates)
        gap = pd.Series([1.0, 2.0, 3.0], index=dates[[0, 2, 3]])  # no candle at t=1
        ind = MODULE.breadth_indicators([up, down, gap], dates)
        self.assertEqual(ind["breadth"].iloc[0], 0.5)  # no previous candle anywhere
        self.assertEqual(ind["breadth"].iloc[1], 0.5)  # 1 up, 1 down, gap pair missing
        self.assertAlmostEqual(ind["breadth"].iloc[2], 0.5)  # 1 up, 1 down, gap pair missing t-1
        self.assertAlmostEqual(ind["breadth"].iloc[3], 1.0)  # up, down flat; gap pair up
        expected = ind["breadth"].ewm(span=10, adjust=False).mean()
        pd.testing.assert_series_equal(ind["breadth_ema"], expected, check_names=False)

    def test_signals_binary_and_present(self):
        strat, frame = build(3000)
        out = run(strat, frame)
        self.assertIn("enter_long", out)
        self.assertTrue(set(out["enter_long"].dropna().unique().tolist()).issubset({1}))
        self.assertGreater(int(out["enter_long"].fillna(0).sum()), 0)
        entries = out[out["enter_long"] == 1]
        self.assertTrue((entries["breadth_ema"] > 0.615).all())
        self.assertTrue((entries["breadth_ema_prior_min"] < 0.40).all())
        self.assertTrue((entries["close"] > entries["close_lookback"]).all())

    def test_zero_volume_no_signal(self):
        strat, frame = build(3000, volume=0.0)
        out = run(strat, frame)
        self.assertEqual(int(out.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(out.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        strat.dp.analyzed = out
        trade = FakeTrade(out["date"].iloc[100])
        self.assertIsNone(strat.custom_exit(TRADED, trade, None, 100.0, 0.0))

    def test_nan_startup_no_signal(self):
        strat, frame = build(3000)
        out = run(strat, frame)
        undefined = out["thrust_prev"].isna() | out["close_lookback"].isna()
        self.assertTrue(undefined.iloc[:11].all())
        self.assertEqual(int(out.loc[undefined, "enter_long"].fillna(0).sum()), 0)

    def test_no_lookahead(self):
        n, total = 2000, 2400
        strat_a, frame_a = build(n, total=total)
        strat_b, frame_b = build(total, total=total)
        a = run(strat_a, frame_a)
        b = run(strat_b, frame_b)
        cols = ["breadth", "breadth_ema", "breadth_ema_prior_min", "thrust", "thrust_prev",
                "close_lookback", "enter_long"]
        pd.testing.assert_frame_equal(
            a.loc[: n - 1, cols].fillna(-1), b.loc[: n - 1, cols].fillna(-1), check_dtype=False
        )

    def test_custom_exit_time_and_collapse(self):
        strat, frame = build(400)
        out = run(strat, frame)
        out["breadth_ema"] = 0.5
        fill = out["date"].iloc[300]
        trade = FakeTrade(fill)
        # Candle dated fill + 22h (bar t+23): still open.
        strat.dp.analyzed = out.iloc[: 300 + 23]
        self.assertIsNone(strat.custom_exit(TRADED, trade, None, 100.0, 0.0))
        # Candle dated fill + 23h (bar t+24): time exit.
        strat.dp.analyzed = out.iloc[: 300 + 24]
        self.assertEqual(strat.custom_exit(TRADED, trade, None, 100.0, 0.0), "time_24h")
        # Collapse on the fill bar itself is ignored; on a later bar it exits.
        collapsed = out.copy()
        collapsed["breadth_ema"] = 0.3
        strat.dp.analyzed = collapsed.iloc[: 301]
        self.assertIsNone(strat.custom_exit(TRADED, trade, None, 100.0, 0.0))
        strat.dp.analyzed = collapsed.iloc[: 302]
        self.assertEqual(strat.custom_exit(TRADED, trade, None, 100.0, 0.0), "breadth_collapse")
        # NaN breadth never exits on collapse.
        collapsed["breadth_ema"] = np.nan
        strat.dp.analyzed = collapsed.iloc[: 302]
        self.assertIsNone(strat.custom_exit(TRADED, trade, None, 100.0, 0.0))


if __name__ == "__main__":
    unittest.main()
