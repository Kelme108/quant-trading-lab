import importlib.util
import sys
import types
import unittest
from datetime import timedelta
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
for _name in ("merge_informative_pair", "stoploss_from_absolute"):
    if not hasattr(sys.modules["freqtrade.strategy"], _name):
        setattr(sys.modules["freqtrade.strategy"], _name, lambda *a, **k: None)

talib = types.ModuleType("talib")
talib_abstract = types.ModuleType("talib.abstract")
talib_abstract.SMA = lambda dataframe, timeperiod: dataframe["close"].rolling(timeperiod).mean()
talib_abstract.RSI = lambda dataframe, timeperiod: pd.Series(50.0, index=dataframe.index)
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)

ROOT = Path(__file__).parents[1]
NAME = "HourlyKeltnerMTFBreakout_H066_v1"
PATH = ROOT / "user_data" / "strategies" / f"{NAME}.py"
spec = importlib.util.spec_from_file_location(NAME, PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Strategy = module.HourlyKeltnerMTFBreakout_H066_v1

MINUTES = {"15m": 15, "1h": 60, "4h": 240, "1d": 1440}


def merge_informative_pair(dataframe, informative, timeframe, timeframe_inf, ffill=True, **kwargs):
    """Same semantics as freqtrade's helper: an informative candle is visible from the last base candle
    inside its period (i.e. once that period has closed)."""
    informative = informative.copy()
    shift = MINUTES[timeframe_inf] - MINUTES[timeframe]
    informative["date_merge"] = informative["date"] + pd.Timedelta(minutes=shift)
    informative.columns = [f"{column}_{timeframe_inf}" for column in informative.columns]
    merged = pd.merge(
        dataframe, informative, left_on="date",
        right_on=f"date_merge_{timeframe_inf}", how="left",
    )
    merged = merged.drop(columns=[f"date_merge_{timeframe_inf}"])
    if ffill:
        columns = [c for c in merged.columns if c.endswith(f"_{timeframe_inf}")]
        merged[columns] = merged[columns].ffill()
    return merged


# Use the faithful merge regardless of which stub module was registered first.
module.merge_informative_pair = merge_informative_pair

START = pd.Timestamp("2025-01-01 00:00", tz="UTC")


def make_frame(n=4000, seed=5):
    """Uptrending random walk with occasional upward jumps, so fresh band breakouts occur."""
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0003, 0.004, n)
    jumps = rng.random(n) < 0.01
    returns[jumps] += 0.03
    close = 100.0 * np.exp(np.cumsum(returns))
    open_ = np.concatenate([[100.0], close[:-1]])
    high = np.maximum(open_, close) * 1.002
    low = np.minimum(open_, close) * 0.998
    return pd.DataFrame(
        {
            "date": pd.date_range(START, periods=n, freq="1h"),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.ones(n),
        }
    )


def run(frame):
    strategy = Strategy()
    frame = strategy.populate_indicators(frame, {"pair": "BTC/USDT"})
    frame = strategy.populate_entry_trend(frame, {"pair": "BTC/USDT"})
    return strategy.populate_exit_trend(frame, {"pair": "BTC/USDT"})


def entries(frame):
    return frame.get("enter_long", pd.Series(np.nan, index=frame.index)).fillna(0)


class HourlyKeltnerMTFBreakoutTests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertTrue(Strategy.use_custom_stoploss)
        self.assertEqual(Strategy.startup_candle_count, 1000)
        self.assertGreaterEqual(Strategy.startup_candle_count, (50 + 6) * 4)
        self.assertEqual(module.BAND_ATR_MULT, 2.5)
        self.assertEqual(module.RSI_PERIOD, 40)
        self.assertEqual(module.STOP_ATR_MULT, 1.6)
        self.assertEqual(module.TARGET_ATR_MULT, 4.5)
        self.assertEqual(module.TIME_EXIT_BARS, 16)

    def test_signals_binary_and_present(self):
        frame = run(make_frame())
        self.assertGreater(entries(frame).sum(), 0)
        for column in ("enter_long", "exit_long"):
            if column in frame:
                self.assertTrue(set(frame[column].dropna().unique().tolist()).issubset({1}))

    def test_entry_conditions_hold_where_signalled(self):
        frame = run(make_frame())
        hit = frame[entries(frame) == 1]
        self.assertTrue((hit["close"] > hit["kc_upper"]).all())
        self.assertTrue((hit["close_prev"] <= hit["kc_upper_prev"]).all())
        self.assertTrue((hit["rsi40_tp"] > 50).all())
        self.assertTrue((hit["close_4h"] > hit["ema_4h"]).all())
        self.assertTrue((hit["ema_4h"] > hit["ema_lag_4h"]).all())
        for tag, a20, a30 in zip(hit["enter_tag"], hit["atr20"], hit["atr30"]):
            self.assertEqual(module.parse_tag(tag), (a20, a30))

    def test_zero_volume_no_signal(self):
        frame = make_frame()
        frame["volume"] = 0.0
        frame = run(frame)
        self.assertEqual(int(entries(frame).sum()), 0)
        self.assertEqual(int(frame.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self):
        frame = run(make_frame())
        # The 4h EMA50 plus its 6-bar lag needs 56 completed 4h bars, i.e. 224 1h bars.
        self.assertTrue(frame.loc[: 4 * 55 - 1, "ema_lag_4h"].isna().all())
        self.assertEqual(int(entries(frame).iloc[: 4 * 56 - 1].sum()), 0)
        undefined = frame[["kc_upper", "kc_upper_prev", "rsi40_tp", "ema_lag_4h"]].isna().any(axis=1)
        self.assertEqual(int(entries(frame)[undefined].sum()), 0)

    def test_four_hour_candle_visible_only_after_close(self):
        frame = run(make_frame(600))
        dates = frame["date"]
        row_03 = frame.index[dates == START + pd.Timedelta(hours=3)][0]
        row_06 = frame.index[dates == START + pd.Timedelta(hours=6)][0]
        self.assertTrue(pd.isna(frame.loc[row_03 - 1, "close_4h"]))
        self.assertEqual(frame.loc[row_03, "close_4h"], frame.loc[row_03, "close"])
        self.assertEqual(frame.loc[row_06, "close_4h"], frame.loc[row_03, "close"])

    def test_no_lookahead(self):
        full = make_frame(4300)
        n = 4000
        short = run(full.iloc[:n].copy())
        long = run(full.copy())
        np.testing.assert_array_equal(entries(short).to_numpy(), entries(long).to_numpy()[:n])
        cols = ["ema50", "atr50", "atr30", "atr20", "kc_upper", "rsi40_tp", "close_4h", "ema_4h", "ema_lag_4h"]
        pd.testing.assert_frame_equal(short[cols], long.loc[: n - 1, cols])
        self.assertTrue(
            short["enter_tag"].fillna("").reset_index(drop=True).equals(
                long["enter_tag"].iloc[:n].fillna("").reset_index(drop=True)
            )
        )

    def test_trade_exits(self):
        strategy = Strategy()
        open_date = START + pd.Timedelta(hours=10)
        trade = SimpleNamespace(
            enter_tag=module.make_tag(2.0, 3.0), open_rate=100.0,
            open_date_utc=open_date, fee_open=0.001, fee_close=0.001,
        )
        # Stop at 100 - 1.6 * 2 = 96.8 regardless of the current rate.
        for rate in (100.0, 104.0):
            stop = strategy.custom_stoploss("X", trade, open_date, rate, 0.0)
            self.assertAlmostEqual(rate * (1.0 - stop), 96.8)
        # Target at 100 + 4.5 * 3 = 113.5 after fees.
        roi = strategy.custom_roi("X", trade, open_date, 0, trade.enter_tag, "long")
        self.assertAlmostEqual((100.0 * (1 + roi) + 100.0 * 0.001) / (1 - 0.001), 113.5)
        self.assertEqual(strategy.custom_exit("X", trade, open_date, 113.6, 0.0), "target_4p5_atr30")
        before = open_date + timedelta(hours=15)
        self.assertIsNone(strategy.custom_exit("X", trade, before, 101.0, 0.0))
        at = open_date + timedelta(hours=16)
        self.assertEqual(strategy.custom_exit("X", trade, at, 101.0, 0.0), "time_exit_16_bars")
        foreign = SimpleNamespace(enter_tag="other", open_rate=100.0, open_date_utc=open_date,
                                  fee_open=0.0, fee_close=0.0)
        self.assertIsNone(strategy.custom_stoploss("X", foreign, open_date, 100.0, 0.0))


if __name__ == "__main__":
    unittest.main()
