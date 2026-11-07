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


ROOT = Path(__file__).parents[2]


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / "_archive" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Strategy = load_strategy("MoneyFlowBreakout_H079_v1.py", "MoneyFlowBreakout_H079_v1")


def synthetic_frame(n: int, seed: int = 7) -> pd.DataFrame:
    """Random walk with alternating trend legs; closes skew toward highs in up legs."""
    rng = np.random.default_rng(seed)
    drift = np.where((np.arange(n) // 60) % 2 == 0, 0.004, -0.003)
    close = 100.0 * np.exp(np.cumsum(drift + rng.normal(0, 0.008, n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    spread = np.abs(rng.normal(0, 0.006, n)) + 0.002
    high = np.maximum(open_, close) * (1 + spread)
    low = np.minimum(open_, close) * (1 - spread)
    volume = rng.uniform(50, 150, n)
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC"),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


def run(frame: pd.DataFrame) -> pd.DataFrame:
    strategy = Strategy()
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    return frame


class MoneyFlowBreakoutH079Tests(unittest.TestCase):
    def test_class_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertAlmostEqual(Strategy.stoploss, -0.025)
        self.assertGreaterEqual(Strategy.startup_candle_count, 30)
        protections = Strategy().protections
        self.assertEqual(protections, [{"method": "CooldownPeriod", "stop_duration_candles": 6}])

    def test_cmf_and_levels_match_definition(self) -> None:
        frame = run(synthetic_frame(120))
        t = 80
        window = frame.iloc[t - 19 : t + 1]
        mfm = ((window["close"] - window["low"]) - (window["high"] - window["close"])) / (
            window["high"] - window["low"]
        )
        expected_cmf = (mfm * window["volume"]).sum() / window["volume"].sum()
        self.assertAlmostEqual(frame.loc[t, "cmf20"], expected_cmf)
        self.assertAlmostEqual(frame.loc[t, "cmf20_lag"], frame.loc[t - 6, "cmf20"])
        self.assertAlmostEqual(frame.loc[t, "h24"], frame["high"].iloc[t - 24 : t].max())
        self.assertAlmostEqual(frame.loc[t, "l24"], frame["low"].iloc[t - 24 : t].min())
        self.assertAlmostEqual(frame.loc[t, "l6"], frame["low"].iloc[t - 6 : t].min())

    def test_flat_bars_give_zero_mfm(self) -> None:
        n = 60
        frame = pd.DataFrame(
            {"open": [100.0] * n, "high": [100.0] * n, "low": [100.0] * n,
             "close": [100.0] * n, "volume": [10.0] * n}
        )
        out = run(frame)
        self.assertTrue((out["cmf20"].iloc[19:] == 0.0).all())

    def test_signal_columns_are_binary(self) -> None:
        frame = run(synthetic_frame(1500))
        self.assertGreater(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        for column in ("enter_long", "exit_long"):
            if column in frame:
                values = frame[column].dropna().unique().tolist()
                self.assertTrue(set(values).issubset({1}))

    def test_zero_volume_does_not_create_signals(self) -> None:
        frame = synthetic_frame(1500)
        baseline = run(frame)
        signal_rows = baseline.index[
            (baseline.get("enter_long", pd.Series(dtype=float)).fillna(0) == 1)
            | (baseline.get("exit_long", pd.Series(dtype=float)).fillna(0) == 1)
        ]
        self.assertGreater(len(signal_rows), 0)
        zeroed = frame.copy()
        zeroed.loc[signal_rows, "volume"] = 0.0
        out = run(zeroed)
        for column in ("enter_long", "exit_long"):
            if column in out:
                self.assertEqual(int(out.loc[signal_rows, column].fillna(0).sum()), 0)

        all_zero = frame.copy()
        all_zero["volume"] = 0.0
        out = run(all_zero)
        for column in ("enter_long", "exit_long"):
            self.assertEqual(int(out.get(column, pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_nan_startup_values_do_not_create_signals(self) -> None:
        frame = run(synthetic_frame(400))
        startup = Strategy.startup_candle_count
        undefined = frame[["cmf20", "cmf20_lag", "h24", "l24"]].isna().any(axis=1)
        self.assertTrue(undefined.iloc[:25].all())
        enter = frame.get("enter_long", pd.Series(0, index=frame.index)).fillna(0)
        exit_ = frame.get("exit_long", pd.Series(0, index=frame.index)).fillna(0)
        self.assertEqual(int(enter[undefined].sum()), 0)
        self.assertEqual(int(enter.iloc[:startup].sum()), 0)
        exit_undefined = frame["cmf20"].isna() & frame["l6"].isna()
        self.assertEqual(int(exit_[exit_undefined].sum()), 0)

    def test_signals_do_not_change_when_future_candles_are_appended(self) -> None:
        full = synthetic_frame(1500)
        n = 1000
        short = run(full.iloc[:n].copy())
        long = run(full.copy())
        columns = ["cmf20", "cmf20_lag", "h24", "l24", "l6"]
        pd.testing.assert_frame_equal(short[columns], long.iloc[:n][columns], check_dtype=False)
        for column in ("enter_long", "exit_long"):
            a = short.get(column, pd.Series(np.nan, index=short.index)).fillna(0)
            b = long.get(column, pd.Series(np.nan, index=long.index)).iloc[:n].fillna(0)
            pd.testing.assert_series_equal(a, b, check_dtype=False, check_names=False)

    def test_time_exit_after_24_bars(self) -> None:
        strategy = Strategy()
        opened = datetime(2024, 1, 1, 0, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_date_utc=opened)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, opened + timedelta(hours=23), 1.0, 0.0))
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade, opened + timedelta(hours=24), 1.0, 0.0),
            "time_exit_24h",
        )


if __name__ == "__main__":
    unittest.main()
