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
NAME = "AsianRangeLondonBreakout_H067_v1"
PATH = ROOT / "user_data" / "strategies" / f"{NAME}.py"
spec = importlib.util.spec_from_file_location(NAME, PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Strategy = module.AsianRangeLondonBreakout_H067_v1

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
DAYS = 70


def make_frame(n=DAYS * 96, seed=3):
    """15m random walk, quiet in the Asian session and active afterwards, so breakouts occur."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(START, periods=n, freq="15min")
    hour = dates.hour.to_numpy()
    sigma = np.where(hour < 7, 0.0012, 0.0045)
    drift = np.where((hour >= 7) & (hour < 10), 0.0004, 0.0)
    returns = rng.normal(drift, sigma)
    close = 100.0 * np.exp(np.cumsum(returns))
    open_ = np.concatenate([[100.0], close[:-1]])
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, sigma / 3)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, sigma / 3)))
    return pd.DataFrame(
        {"date": dates, "open": open_, "high": high, "low": low, "close": close, "volume": np.ones(n)}
    )


def run(frame):
    strategy = Strategy()
    frame = strategy.populate_indicators(frame, {"pair": "BTC/USDT"})
    frame = strategy.populate_entry_trend(frame, {"pair": "BTC/USDT"})
    return strategy.populate_exit_trend(frame, {"pair": "BTC/USDT"})


def column(frame, name):
    return frame.get(name, pd.Series(np.nan, index=frame.index)).fillna(0)


class AsianRangeLondonBreakoutTests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertLess(Strategy.stoploss, 0)
        self.assertAlmostEqual(Strategy.stoploss, -0.08)
        self.assertTrue(Strategy.use_custom_stoploss)
        self.assertEqual(Strategy.startup_candle_count, 4320)
        self.assertGreaterEqual(Strategy.startup_candle_count, (14 + 1) * 96)
        self.assertEqual(module.ASIAN_BARS, 28)
        self.assertEqual(module.ATR_DAYS, 14)
        self.assertEqual(module.MIN_RANGE_ATR, 0.25)
        self.assertEqual(module.MAX_RANGE_ATR, 0.80)
        self.assertEqual(module.TARGET_R, 1.0)

    def test_signals_binary_and_present(self):
        frame = run(make_frame())
        self.assertGreater(column(frame, "enter_long").sum(), 0)
        self.assertGreater(column(frame, "exit_long").sum(), 0)
        for name in ("enter_long", "exit_long"):
            if name in frame:
                self.assertTrue(set(frame[name].dropna().unique().tolist()).issubset({1}))

    def test_entry_conditions_hold_where_signalled(self):
        frame = run(make_frame())
        dates = pd.to_datetime(frame["date"], utc=True)
        hit = frame[column(frame, "enter_long") == 1]
        self.assertTrue((hit["close"] > hit["asian_high"]).all())
        self.assertTrue((hit["range_atr_ratio"] >= 0.25).all())
        self.assertTrue((hit["range_atr_ratio"] <= 0.80).all())
        self.assertTrue(((hit["minute_of_day"] >= 420) & (hit["minute_of_day"] < 600)).all())
        # At most one signal per UTC day.
        self.assertEqual(dates[hit.index].dt.floor("D").value_counts().max(), 1)
        for index, row in hit.iterrows():
            self.assertEqual(module.parse_tag(row["enter_tag"]), row["asian_low"])
            day = dates[index].floor("D")
            asian = frame[(dates >= day) & (dates < day + pd.Timedelta(hours=7))]
            self.assertEqual(len(asian), 28)
            self.assertEqual(row["asian_high"], asian["high"].max())
            self.assertEqual(row["asian_low"], asian["low"].min())
            earlier = frame[(dates >= day + pd.Timedelta(hours=7)) & (dates < dates[index])]
            self.assertTrue((earlier["close"] <= row["asian_high"]).all())
            self.assertTrue((earlier["close"] >= row["asian_low"]).all())

    def test_atr_uses_previous_completed_day(self):
        frame = run(make_frame())
        daily = module.daily_atr_from_intraday(frame)
        dates = pd.to_datetime(frame["date"], utc=True)
        day = START + pd.Timedelta(days=30)
        row = frame.index[dates == day + pd.Timedelta(hours=8)][0]
        expected = daily.loc[daily["date"] == day - pd.Timedelta(days=1), "atr"].iloc[0]
        self.assertAlmostEqual(frame.loc[row, "atr_1d"], expected)

    def test_first_break_down_vetoes_day(self):
        base = make_frame()
        frame = run(base.copy())
        dates = pd.to_datetime(frame["date"], utc=True)
        hits = frame.index[column(frame, "enter_long") == 1]
        candidates = [i for i in hits if frame.loc[i, "minute_of_day"] > 420]
        self.assertTrue(candidates)
        index = candidates[0]
        day = dates[index].floor("D")
        first_window = frame.index[dates == day + pd.Timedelta(hours=7)][0]
        changed = base.copy()
        changed.loc[first_window, "close"] = frame.loc[index, "asian_low"] * 0.999
        changed.loc[first_window, "low"] = min(changed.loc[first_window, "low"], changed.loc[first_window, "close"])
        result = run(changed)
        day_rows = pd.to_datetime(result["date"], utc=True).dt.floor("D") == day
        self.assertEqual(int(column(result, "enter_long")[day_rows].sum()), 0)

    def test_missing_asian_bar_disarms_day(self):
        base = make_frame()
        frame = run(base.copy())
        dates = pd.to_datetime(frame["date"], utc=True)
        index = frame.index[column(frame, "enter_long") == 1][0]
        day = dates[index].floor("D")
        dropped = base[base["date"] != day + pd.Timedelta(hours=3)].reset_index(drop=True)
        result = run(dropped)
        day_rows = pd.to_datetime(result["date"], utc=True).dt.floor("D") == day
        self.assertTrue(result.loc[day_rows, "asian_high"].isna().all())
        self.assertEqual(int(column(result, "enter_long")[day_rows].sum()), 0)

    def test_zero_volume_no_signal(self):
        frame = make_frame()
        frame["volume"] = 0.0
        frame = run(frame)
        self.assertEqual(int(column(frame, "enter_long").sum()), 0)
        self.assertEqual(int(column(frame, "exit_long").sum()), 0)

    def test_zero_volume_candle_no_signal(self):
        base = make_frame()
        frame = run(base.copy())
        index = frame.index[column(frame, "enter_long") == 1][0]
        exit_index = frame.index[column(frame, "exit_long") == 1][0]
        changed = base.copy()
        changed.loc[[index, exit_index], "volume"] = 0.0
        result = run(changed)
        self.assertEqual(column(result, "enter_long")[index], 0)
        self.assertEqual(column(result, "exit_long")[exit_index], 0)

    def test_nan_startup_no_signal(self):
        frame = run(make_frame())
        # Wilder ATR14 needs 14 daily true ranges (15 days); visible after day 15 closes.
        self.assertTrue(frame.loc[: 15 * 96 - 2, "atr_1d"].isna().all())
        self.assertEqual(int(column(frame, "enter_long").iloc[: 15 * 96].sum()), 0)
        undefined = frame[["asian_high", "asian_low", "atr_1d", "range_atr_ratio"]].isna().any(axis=1)
        self.assertEqual(int(column(frame, "enter_long")[undefined].sum()), 0)

    def test_no_lookahead(self):
        full = make_frame()
        for n in (60 * 96 + 33, 62 * 96 + 37, 65 * 96):
            short = run(full.iloc[:n].copy())
            long = run(full.copy())
            for name in ("enter_long", "exit_long"):
                np.testing.assert_array_equal(column(short, name).to_numpy(), column(long, name).to_numpy()[:n])
            cols = ["asian_high", "asian_low", "atr_1d", "range_atr_ratio"]
            pd.testing.assert_frame_equal(short[cols], long.loc[: n - 1, cols])
            self.assertTrue(
                short["enter_tag"].fillna("").reset_index(drop=True).equals(
                    long["enter_tag"].iloc[:n].fillna("").reset_index(drop=True)
                )
            )

    def test_trade_callbacks(self):
        strategy = Strategy()
        open_date = START + pd.Timedelta(hours=8, minutes=15)
        trade = SimpleNamespace(
            enter_tag=module.make_tag(98.0), open_rate=100.0,
            open_date_utc=open_date, fee_open=0.001, fee_close=0.001,
        )
        for rate in (100.0, 101.5):
            stop = strategy.custom_stoploss("X", trade, open_date, rate, 0.0)
            self.assertAlmostEqual(rate * (1.0 - stop), 98.0)
        roi = strategy.custom_roi("X", trade, open_date, 0, trade.enter_tag, "long")
        self.assertAlmostEqual((100.0 * (1 + roi) + 100.0 * 0.001) / (1 - 0.001), 102.0)
        self.assertEqual(strategy.custom_exit("X", trade, open_date, 102.1, 0.0), "target_1r")
        before = START + pd.Timedelta(hours=11, minutes=45)
        self.assertIsNone(strategy.custom_exit("X", trade, before, 101.0, 0.0))
        at = START + pd.Timedelta(hours=12)
        self.assertEqual(strategy.custom_exit("X", trade, at, 101.0, 0.0), "time_exit_1200_utc")
        foreign = SimpleNamespace(enter_tag="other", open_rate=100.0, open_date_utc=open_date,
                                  fee_open=0.0, fee_close=0.0)
        self.assertIsNone(strategy.custom_stoploss("X", foreign, open_date, 100.0, 0.0))
        self.assertIsNone(strategy.custom_roi("X", foreign, open_date, 0, "other", "long"))
        self.assertIsNotNone(timedelta)


if __name__ == "__main__":
    unittest.main()
