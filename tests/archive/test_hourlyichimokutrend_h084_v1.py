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
FILENAME = "HourlyIchimokuTrend_H084_v1.py"
CLASS_NAME = "HourlyIchimokuTrend_H084_v1"


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / "_archive" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Strategy = load_strategy(FILENAME, CLASS_NAME)


def make_frame(prices) -> pd.DataFrame:
    prices = list(prices)
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=len(prices), freq="1h", tz="UTC"),
            "open": prices,
            "high": [p * 1.01 for p in prices],
            "low": [p * 0.99 for p in prices],
            "close": prices,
            "volume": [1.0] * len(prices),
        }
    )


def run(frame: pd.DataFrame) -> pd.DataFrame:
    strategy = Strategy()
    frame = strategy.populate_indicators(frame.copy(), {"pair": "BTC/USDT"})
    frame = strategy.populate_entry_trend(frame, {"pair": "BTC/USDT"})
    frame = strategy.populate_exit_trend(frame, {"pair": "BTC/USDT"})
    return frame


def random_walk(n: int, seed: int = 7) -> list:
    rng = np.random.default_rng(seed)
    return list(100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.01, n))))


def trend_series() -> list:
    # Flat, then a steady rise (TK cross above the cloud), then a sharp drop (Kijun exit).
    flat = [100.0] * 200
    rise = [100.0 * (1.003 ** (i + 1)) for i in range(80)]
    drop = [rise[-1] * (0.98 ** (i + 1)) for i in range(20)]
    return flat + rise + drop


class HourlyIchimokuTrendTests(unittest.TestCase):
    def test_class_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.03)
        self.assertIsInstance(Strategy.startup_candle_count, int)
        self.assertEqual(Strategy.startup_candle_count, 150)

    def test_signal_columns_are_binary(self) -> None:
        for prices in (random_walk(600), trend_series()):
            frame = run(make_frame(prices))
            for column in ("enter_long", "exit_long"):
                if column in frame:
                    values = frame[column].dropna().unique().tolist()
                    self.assertTrue(set(values).issubset({1}))

    def test_rule_fires_entry_and_kijun_exit(self) -> None:
        frame = run(make_frame(trend_series()))
        entries = frame.index[frame.get("enter_long", pd.Series(dtype=float)).fillna(0) == 1]
        self.assertGreater(len(entries), 0)
        first = entries[0]
        row = frame.loc[first]
        self.assertGreater(row["close"], row["cloud_top"])
        self.assertGreater(row["close"], frame.loc[first - 30, "close"])
        self.assertGreater(row["tenkan"], row["kijun"])
        exits = frame.index[frame.get("exit_long", pd.Series(dtype=float)).fillna(0) == 1]
        self.assertTrue(any(i >= 280 for i in exits))
        for i in exits:
            self.assertLess(frame.loc[i, "close"], frame.loc[i, "kijun"])

    def test_indicator_windows(self) -> None:
        prices = random_walk(400)
        frame = run(make_frame(prices))
        t = 300
        highs = [p * 1.01 for p in prices]
        lows = [p * 0.99 for p in prices]
        tenkan = (max(highs[t - 19 : t + 1]) + min(lows[t - 19 : t + 1])) / 2
        kijun = (max(highs[t - 59 : t + 1]) + min(lows[t - 59 : t + 1])) / 2
        self.assertAlmostEqual(frame.loc[t, "tenkan"], tenkan)
        self.assertAlmostEqual(frame.loc[t, "kijun"], kijun)
        s = t - 30
        span_a = (
            (max(highs[s - 19 : s + 1]) + min(lows[s - 19 : s + 1])) / 2
            + (max(highs[s - 59 : s + 1]) + min(lows[s - 59 : s + 1])) / 2
        ) / 2
        span_b = (max(highs[s - 119 : s + 1]) + min(lows[s - 119 : s + 1])) / 2
        self.assertAlmostEqual(frame.loc[t, "cloud_top"], max(span_a, span_b))
        self.assertTrue(pd.isna(frame.loc[148, "cloud_top"]))
        self.assertFalse(pd.isna(frame.loc[149, "cloud_top"]))

    def test_zero_volume_produces_no_signal(self) -> None:
        for prices in (random_walk(600), trend_series()):
            frame = make_frame(prices)
            frame["volume"] = 0.0
            frame = run(frame)
            self.assertEqual(int(frame.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
            self.assertEqual(int(frame.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_zero_volume_single_candle(self) -> None:
        base = run(make_frame(trend_series()))
        entries = base.index[base["enter_long"].fillna(0) == 1]
        exits = base.index[base["exit_long"].fillna(0) == 1]
        frame = make_frame(trend_series())
        frame.loc[[entries[0], exits[0]], "volume"] = 0.0
        frame = run(frame)
        self.assertNotEqual(frame.loc[entries[0], "enter_long"], 1)
        self.assertNotEqual(frame.loc[exits[0], "exit_long"], 1)

    def test_nan_startup_values_produce_no_signal(self) -> None:
        for prices in (random_walk(600), [100.0 + i for i in range(300)], trend_series()):
            frame = run(make_frame(prices))
            startup = Strategy.startup_candle_count
            head = frame.iloc[:startup]
            self.assertEqual(int(head.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
            # Exit signals require a defined Kijun.
            undefined = frame["kijun"].isna()
            self.assertEqual(
                int(frame.loc[undefined].get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0
            )

    def test_signals_do_not_change_when_future_candles_are_appended(self) -> None:
        n, k = 400, 150
        for prices in (random_walk(n + k, seed=3), trend_series() + random_walk(k + 100, seed=5)):
            prices = prices[: n + k]
            short = run(make_frame(prices[:n]))
            full = run(make_frame(prices))
            columns = [
                "tenkan", "kijun", "span_a", "span_b", "cloud_top", "close_lag", "enter_long", "exit_long",
            ]
            for column in ("enter_long", "exit_long"):
                for frame in (short, full):
                    if column not in frame:
                        frame[column] = np.nan
            pd.testing.assert_frame_equal(
                short.loc[: n - 1, columns].reset_index(drop=True),
                full.loc[: n - 1, columns].reset_index(drop=True),
                check_dtype=False,
            )

    def test_time_exit_after_24_hours(self) -> None:
        strategy = Strategy()
        opened = datetime(2024, 1, 1, 5, tzinfo=timezone.utc)
        trade = types.SimpleNamespace(open_date_utc=opened, enter_tag="tk_cross")
        self.assertIsNone(
            strategy.custom_exit("BTC/USDT", trade, opened + timedelta(hours=23), 100.0, 0.0)
        )
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade, opened + timedelta(hours=24), 100.0, 0.0),
            "time_exit_24h",
        )


if __name__ == "__main__":
    unittest.main()
