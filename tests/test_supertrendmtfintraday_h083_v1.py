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
NAME = "SupertrendMTFIntraday_H083_v1"
PATH = ROOT / "user_data" / "strategies" / f"{NAME}.py"
spec = importlib.util.spec_from_file_location(NAME, PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Strategy = module.SupertrendMTFIntraday_H083_v1

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


def make_frame(n=4000, seed=7):
    """15m random walk with an upward drift so that up-flips above the 1h EMA200 occur."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(START, periods=n, freq="15min")
    returns = rng.normal(0.0002, 0.004, n)
    close = 100.0 * np.exp(np.cumsum(returns))
    open_ = np.concatenate([[100.0], close[:-1]])
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.0015, n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.0015, n)))
    return pd.DataFrame(
        {"date": dates, "open": open_, "high": high, "low": low, "close": close, "volume": np.ones(n)}
    )


def run(frame):
    strategy = Strategy()
    frame = strategy.populate_indicators(frame, {"pair": "BTC/USDT"})
    frame = strategy.populate_entry_trend(frame, {"pair": "BTC/USDT"})
    return strategy.populate_exit_trend(frame, {"pair": "BTC/USDT"})


def column(frame, name):
    return frame[name] if name in frame else pd.Series(np.nan, index=frame.index)


class SupertrendH083Tests(unittest.TestCase):
    def test_class_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertAlmostEqual(Strategy.stoploss, -0.10)
        self.assertGreaterEqual(Strategy.startup_candle_count, 3200)

    def test_signals_exist_and_are_binary(self):
        frame = run(make_frame())
        self.assertGreater(int(column(frame, "enter_long").fillna(0).sum()), 0)
        self.assertGreater(int(column(frame, "exit_long").fillna(0).sum()), 0)
        for name in ("enter_long", "exit_long"):
            values = column(frame, name).dropna().unique().tolist()
            self.assertTrue(set(values).issubset({1}))

    def test_entry_matches_rule(self):
        frame = run(make_frame())
        entries = frame[column(frame, "enter_long") == 1]
        for idx, row in entries.iterrows():
            self.assertEqual(frame.loc[idx - 1, "st_dir"], -1.0)
            self.assertEqual(row["st_dir"], 1.0)
            self.assertGreater(row["close"], row["ema200_1h"])
            self.assertEqual(module.parse_tag(row["enter_tag"]), row["st_line"])
            self.assertEqual(row["st_line"], row["st_lower"])

    def test_ema_uses_only_completed_hours(self):
        frame = run(make_frame())
        hourly = frame.groupby(frame["date"].dt.floor("h"))["close"].last()
        ema = hourly.ewm(span=200, adjust=False, min_periods=200).mean()
        # The 15m bar opening at hh:45 is the first to see hour hh; bars at hh+1:00..:30 still see hh.
        row = frame[frame["date"] == pd.Timestamp("2025-01-20 10:30", tz="UTC")].iloc[0]
        self.assertAlmostEqual(row["ema200_1h"], ema[pd.Timestamp("2025-01-20 09:00", tz="UTC")])
        row = frame[frame["date"] == pd.Timestamp("2025-01-20 10:45", tz="UTC")].iloc[0]
        self.assertAlmostEqual(row["ema200_1h"], ema[pd.Timestamp("2025-01-20 10:00", tz="UTC")])

    def test_zero_volume_creates_no_signals(self):
        frame = make_frame()
        frame["volume"] = 0.0
        frame = run(frame)
        self.assertEqual(int(column(frame, "enter_long").fillna(0).sum()), 0)
        self.assertEqual(int(column(frame, "exit_long").fillna(0).sum()), 0)

    def test_undefined_startup_values_create_no_signals(self):
        frame = run(make_frame())
        undefined = (
            frame["ema200_1h"].isna() | frame["st_dir"].isna() | frame["st_dir"].shift(1).isna()
            | frame["atr10"].isna()
        )
        # EMA200 of hour 199 first becomes visible on the last 15m bar of that hour (row 199 * 4 + 3).
        self.assertTrue(undefined.iloc[:799].all())
        self.assertTrue(frame["ema200_1h"].notna().iloc[799])
        self.assertEqual(int(column(frame, "enter_long")[undefined].fillna(0).sum()), 0)
        self.assertEqual(int(column(frame, "exit_long")[frame["st_dir"].isna()].fillna(0).sum()), 0)

    def test_signals_do_not_change_when_future_candles_are_appended(self):
        full = make_frame(n=4000)
        n = 3500
        short = run(full.iloc[:n].copy())
        longer = run(full.copy())
        columns = ["atr10", "st_upper", "st_lower", "st_dir", "st_line", "ema200_1h"]
        pd.testing.assert_frame_equal(
            short[columns].reset_index(drop=True),
            longer.iloc[:n][columns].reset_index(drop=True),
            check_dtype=False,
        )
        for name in ("enter_long", "exit_long"):
            pd.testing.assert_series_equal(
                column(short, name).fillna(0).reset_index(drop=True),
                column(longer, name).iloc[:n].fillna(0).reset_index(drop=True),
                check_dtype=False,
                check_names=False,
            )

    def test_trade_hooks(self):
        strategy = Strategy()
        tag = module.make_tag(99.0)
        self.assertTrue(strategy.confirm_trade_entry("X", "market", 1, 100.0, "gtc", None, tag, "long"))
        tight = module.make_tag(99.7)
        self.assertFalse(strategy.confirm_trade_entry("X", "market", 1, 100.0, "gtc", None, tight, "long"))
        opened = START
        trade = SimpleNamespace(enter_tag=tag, open_rate=100.0, fee_open=0.0, fee_close=0.0,
                                open_date_utc=opened)
        self.assertAlmostEqual(strategy.custom_stoploss("X", trade, opened, 110.0, 0.1), 1 - 99.0 / 110.0)
        self.assertAlmostEqual(strategy.custom_roi("X", trade, opened, 0, tag, "long"), 0.02)
        self.assertEqual(strategy.custom_exit("X", trade, opened, 102.0, 0.02), "target_2r")
        self.assertIsNone(strategy.custom_exit("X", trade, opened + timedelta(hours=23, minutes=45), 101.0, 0.01))
        self.assertEqual(strategy.custom_exit("X", trade, opened + timedelta(hours=24), 101.0, 0.01),
                         "time_exit_24h")


if __name__ == "__main__":
    unittest.main()
