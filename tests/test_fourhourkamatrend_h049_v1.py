import importlib.util
import sys
import types
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


def _merge_informative_pair(dataframe, informative, timeframe, timeframe_inf, ffill=True):
    """Test double with Freqtrade's visibility rule: an informative candle is merged onto the base candle
    dated date + (inf minutes - base minutes), i.e. the base candle that completes it."""
    minutes = {"1h": 60, "4h": 240, "1d": 1440}
    inf = informative.copy()
    inf["date_merge"] = inf["date"] + pd.Timedelta(minutes=minutes[timeframe_inf] - minutes[timeframe])
    inf.columns = [f"{c}_{timeframe_inf}" for c in inf.columns]
    merged = pd.merge(
        dataframe, inf, left_on="date", right_on=f"date_merge_{timeframe_inf}", how="left"
    )
    merged = merged.drop(columns=[f"date_merge_{timeframe_inf}"])
    if ffill:
        merged = merged.ffill()
    return merged


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
NAME = "FourHourKAMATrend_H049_v1"


def _load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.merge_informative_pair = _merge_informative_pair
    return module


MODULE = _load()
Strategy = MODULE.FourHourKAMATrend_H049_v1


def make_frame(prices, start="2024-01-01 00:00"):
    prices = np.asarray(prices, dtype=float)
    return pd.DataFrame(
        {
            "date": pd.date_range(start, periods=len(prices), freq="1h", tz="UTC"),
            "open": prices,
            "high": prices * 1.01,
            "low": prices * 0.99,
            "close": prices,
            "volume": np.ones(len(prices)),
        }
    )


def synthetic_prices(n):
    t = np.arange(n)
    rng = np.random.default_rng(49)
    return 100.0 * np.exp(0.02 * np.sin(t / 60.0) * 10 + 0.0005 * t + 0.01 * rng.standard_normal(n).cumsum() / 10)


def run(frame):
    strategy = Strategy()
    out = strategy.populate_indicators(frame.copy(), {"pair": "BTC/USDT"})
    out = strategy.populate_entry_trend(out, {"pair": "BTC/USDT"})
    out = strategy.populate_exit_trend(out, {"pair": "BTC/USDT"})
    for column in ("enter_long", "exit_long"):
        if column not in out:
            out[column] = np.nan
    return out


class FourHourKAMATrendTests(unittest.TestCase):
    def test_class_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.08)
        self.assertGreaterEqual(Strategy.startup_candle_count, 4000)

    def test_kama_seed_and_recursion(self):
        closes = np.array([10, 11, 12, 11, 13, 14, 13, 15, 16, 15, 17, 18], dtype=float)
        kama = MODULE.kama_series(closes)
        self.assertTrue(np.isnan(kama[:9]).all())
        self.assertAlmostEqual(kama[9], closes[:10].mean())
        er = abs(closes[10] - closes[0]) / np.abs(np.diff(closes[:11])).sum()
        sc = (er * (2 / 3 - 2 / 31) + 2 / 31) ** 2
        self.assertAlmostEqual(kama[10], kama[9] + sc * (closes[10] - kama[9]))
        flat = MODULE.kama_series(np.full(15, 5.0))
        self.assertAlmostEqual(flat[14], 5.0)

    def test_signals_are_binary(self):
        out = run(make_frame(synthetic_prices(2400)))
        for column in ("enter_long", "exit_long"):
            values = set(out[column].dropna().unique().tolist())
            self.assertTrue(values.issubset({1}))
        self.assertGreater(out["enter_long"].fillna(0).sum(), 0)
        self.assertGreater(out["exit_long"].fillna(0).sum(), 0)

    def test_signals_only_on_block_completing_candle(self):
        out = run(make_frame(synthetic_prices(2400)))
        fired = out[(out["enter_long"] == 1) | (out["exit_long"] == 1)]
        self.assertTrue(len(fired) > 0)
        self.assertTrue((fired["date"].dt.hour % 4 == 3).all())

    def test_4h_close_is_last_1h_close_of_block(self):
        frame = make_frame(synthetic_prices(400))
        out = run(frame)
        row = out[out["date"] == pd.Timestamp("2024-01-02 07:00", tz="UTC")].iloc[0]
        self.assertAlmostEqual(row["close_4h"], row["close"])
        prev = out[out["date"] == pd.Timestamp("2024-01-02 06:00", tz="UTC")].iloc[0]
        three = out[out["date"] == pd.Timestamp("2024-01-02 03:00", tz="UTC")].iloc[0]
        self.assertAlmostEqual(prev["close_4h"], three["close"])

    def test_zero_volume_gives_no_signal(self):
        frame = make_frame(synthetic_prices(2400))
        frame["volume"] = 0.0
        out = run(frame)
        self.assertEqual(int(out["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(out["exit_long"].fillna(0).sum()), 0)

    def test_undefined_startup_gives_no_signal(self):
        out = run(make_frame(100.0 * 1.01 ** np.arange(400)))
        undefined = out["kama_4h"].isna() | out["kama_lag_4h"].isna()
        self.assertTrue(undefined.iloc[:40].all())
        self.assertEqual(int(out.loc[undefined, "enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(out.loc[out["kama_4h"].isna(), "exit_long"].fillna(0).sum()), 0)
        self.assertGreater(out["enter_long"].fillna(0).sum(), 0)

    def test_no_lookahead_when_candles_appended(self):
        prices = synthetic_prices(2400)
        n = 1801  # ends mid-block, so the partial last 4h block must not leak
        short = run(make_frame(prices[:n]))
        long = run(make_frame(prices))
        cols = ["enter_long", "exit_long", "close_4h", "kama_4h", "kama_lag_4h"]
        pd.testing.assert_frame_equal(
            short[cols].reset_index(drop=True),
            long.iloc[:n][cols].reset_index(drop=True),
            check_dtype=False,
        )


if __name__ == "__main__":
    unittest.main()
