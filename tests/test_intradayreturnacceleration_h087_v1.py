import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
FILENAME = "IntradayReturnAcceleration_H087_v1.py"
CLASS_NAME = "IntradayReturnAcceleration_H087_v1"


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Strategy = load_strategy(FILENAME, CLASS_NAME)

N_BARS = 3600
JUMP_START = 3300


def make_frame(n: int = N_BARS, seed: int = 7, jump: bool = True) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rets = rng.normal(0.0, 0.001, n)
    if jump:
        # flat-to-slightly-down 4h window, then a strong rising 4h window
        rets[JUMP_START - 16:JUMP_START] = -0.0005
        rets[JUMP_START:JUMP_START + 16] = 0.0015
        # then a reversal so Z falls below 0
        rets[JUMP_START + 16:JUMP_START + 48] = -0.002
    close = 100.0 * np.cumprod(1.0 + rets)
    open_ = np.concatenate([[100.0], close[:-1]])
    return pd.DataFrame(
        {
            "date": pd.date_range("2025-01-01", periods=n, freq="15min", tz="UTC"),
            "open": open_,
            "high": np.maximum(open_, close) * 1.001,
            "low": np.minimum(open_, close) * 0.999,
            "close": close,
            "volume": np.full(n, 10.0),
        }
    )


def run(frame: pd.DataFrame) -> pd.DataFrame:
    strategy = Strategy()
    out = strategy.populate_indicators(frame.copy(), {"pair": "BTC/USDT"})
    out = strategy.populate_entry_trend(out, {"pair": "BTC/USDT"})
    out = strategy.populate_exit_trend(out, {"pair": "BTC/USDT"})
    return out


class FakeTrade:
    def __init__(self, open_date_utc: datetime) -> None:
        self.open_date_utc = open_date_utc


class IntradayReturnAccelerationH087Tests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.02)
        self.assertGreaterEqual(Strategy.startup_candle_count, 2880 + 32 + 1)
        self.assertEqual(Strategy.startup_candle_count, 3000)

    def test_signals_binary_and_entry_fires(self) -> None:
        out = run(make_frame())
        for column in ("enter_long", "exit_long"):
            self.assertIn(column, out)
            values = out[column].dropna().unique().tolist()
            self.assertTrue(set(values).issubset({1}))
        self.assertGreaterEqual(int(out["enter_long"].fillna(0).sum()), 1)
        self.assertGreaterEqual(int(out["exit_long"].fillna(0).sum()), 1)

    def test_entry_conditions_hold_where_signalled(self) -> None:
        out = run(make_frame())
        rows = out[out["enter_long"] == 1]
        self.assertTrue((rows["accel_z"] >= 2.0).all())
        self.assertTrue((rows["accel_z_prev"] < 2.0).all())
        self.assertTrue((rows["r1"] >= 0.01).all())
        self.assertTrue((rows["close"] > rows["open"]).all())
        exits = out[out["exit_long"] == 1]
        self.assertTrue((exits["accel_z"] < 0.0).all())

    def test_zscore_definition(self) -> None:
        frame = make_frame()
        out = run(frame)
        close = frame["close"]
        t = 3400
        a = (close / close.shift(16) - 1.0) - (close.shift(16) / close.shift(32) - 1.0)
        window = a.iloc[t - 2880:t]
        expected = (a.iloc[t] - window.mean()) / window.std(ddof=1)
        self.assertAlmostEqual(out["accel_z"].iloc[t], expected, places=8)

    def test_zero_volume_no_signal(self) -> None:
        frame = make_frame()
        frame["volume"] = 0.0
        out = run(frame)
        self.assertEqual(int(out.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(out.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_nan_startup_no_signal(self) -> None:
        out = run(make_frame())
        first_valid = 2880 + 32  # first row with a defined Z
        self.assertTrue(out["accel_z"].iloc[:first_valid].isna().all())
        self.assertFalse(pd.isna(out["accel_z"].iloc[first_valid]))
        self.assertEqual(int(out["enter_long"].iloc[: first_valid + 1].fillna(0).sum()), 0)
        self.assertEqual(int(out["exit_long"].iloc[:first_valid].fillna(0).sum()), 0)

    def test_constant_price_no_signal(self) -> None:
        frame = make_frame(jump=False)
        frame["close"] = 100.0
        frame["open"] = 100.0
        out = run(frame)
        self.assertEqual(int(out["enter_long"].fillna(0).sum()) if "enter_long" in out else 0, 0)
        self.assertEqual(int(out["exit_long"].fillna(0).sum()) if "exit_long" in out else 0, 0)

    def test_no_lookahead_when_appending_candles(self) -> None:
        full = make_frame()
        n = 3310
        short = run(full.iloc[:n].copy())
        long = run(full.copy())
        cols = ["r1", "accel", "accel_z", "accel_z_prev", "enter_long", "exit_long"]
        for col in ("enter_long", "exit_long"):
            short[col] = short.get(col, pd.Series(np.nan, index=short.index))
            long[col] = long.get(col, pd.Series(np.nan, index=long.index))
        pd.testing.assert_frame_equal(
            short.loc[: n - 1, cols].fillna(0),
            long.loc[: n - 1, cols].fillna(0),
            check_dtype=False,
        )

    def test_time_exit(self) -> None:
        strategy = Strategy()
        opened = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
        trade = FakeTrade(opened)
        self.assertIsNone(
            strategy.custom_exit("BTC/USDT", trade, opened + timedelta(minutes=465), 100.0, 0.05)
        )
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade, opened + timedelta(minutes=480), 100.0, 0.0),
            "time_exit_8h",
        )
        # no take-profit in this rule: a large profit before 8h does not exit
        self.assertIsNone(
            strategy.custom_exit("BTC/USDT", trade, opened + timedelta(minutes=60), 100.0, 0.5)
        )

    def test_signal_exit_on_negative_z(self) -> None:
        out = run(make_frame())
        neg = out["accel_z"] < 0.0
        self.assertTrue((out.loc[neg & (out["volume"] > 0), "exit_long"] == 1).all())


if __name__ == "__main__":
    unittest.main()
