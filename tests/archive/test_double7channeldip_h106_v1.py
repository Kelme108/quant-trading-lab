import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

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


Strategy = load_strategy("Double7ChannelDip_H106_v1.py", "Double7ChannelDip_H106_v1")

START = pd.Timestamp("2024-01-01 00:00:00", tz="UTC")


def make_frame(prices, volume=1.0) -> pd.DataFrame:
    count = len(prices)
    return pd.DataFrame(
        {
            "date": pd.date_range(START, periods=count, freq="1h"),
            "open": prices,
            "high": [p * 1.001 for p in prices],
            "low": [p * 0.999 for p in prices],
            "close": prices,
            "volume": [volume] * count,
        }
    )


def run(strategy, frame):
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    return frame


def dip_prices(count=700, dip_start=600):
    prices = [100.0 + 0.1 * i for i in range(dip_start)]
    top = prices[-1]
    prices += [top - 0.1 * (i + 1) for i in range(count - dip_start)]
    return prices


class Double7ChannelDipTests(unittest.TestCase):
    def setUp(self) -> None:
        self.strategy = Strategy()

    def test_class_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.02)
        self.assertFalse(Strategy.trailing_stop)
        self.assertGreaterEqual(Strategy.startup_candle_count, 420)

    def test_block_indicators(self) -> None:
        prices = dip_prices()
        frame = self.strategy.populate_indicators(make_frame(prices), {})
        # Block 0 = rows 0-1, closes at row 1; block k closes at row 2k+1.
        closes = [prices[2 * k + 1] for k in range(350)]
        row = 2 * 300 + 1
        self.assertAlmostEqual(frame.loc[row, "block_close"], closes[300])
        self.assertAlmostEqual(frame.loc[row, "block_sma"], sum(closes[101:301]) / 200)
        self.assertAlmostEqual(frame.loc[row, "block_low7"], min(closes[294:301]))
        self.assertAlmostEqual(frame.loc[row, "block_high7"], max(closes[294:301]))
        # Even-hour rows carry no block values.
        self.assertTrue(pd.isna(frame.loc[2 * 300, "block_close"]))
        # SMA200b first defined on the 200th block (row 399).
        self.assertTrue(pd.isna(frame.loc[397, "block_sma"]))
        self.assertFalse(pd.isna(frame.loc[399, "block_sma"]))

    def test_entry_fires_on_dip_in_window_only_on_odd_hours(self) -> None:
        frame = run(self.strategy, make_frame(dip_prices()))
        entries = frame[frame["enter_long"] == 1]
        self.assertGreater(len(entries), 0)
        hours = entries["date"].dt.hour
        self.assertTrue((hours % 2 == 1).all())
        self.assertTrue((hours <= 17).all())
        self.assertTrue((entries["close"] > entries["block_sma"]).all())
        self.assertTrue((entries["close"] <= entries["block_low7"]).all())
        # Late blocks (start 18:00 / 20:00 / 22:00) are in the dip but must not enter.
        late = frame[(frame.index >= 600) & frame["hour_utc"].isin([19, 21, 23])]
        self.assertGreater(len(late), 0)
        self.assertTrue(late["enter_long"].isna().all())

    def test_exit_signals_channel_high_and_clock(self) -> None:
        frame = run(self.strategy, make_frame(dip_prices()))
        exits = frame[frame["exit_long"] == 1]
        channel = exits[exits["exit_tag"] == "block_close_at_high7"]
        self.assertGreater(len(channel), 0)
        self.assertTrue((channel["block_close"] >= channel["block_high7"]).all())
        self.assertTrue((channel["date"].dt.hour % 2 == 1).all())
        clock_rows = frame[frame["hour_utc"] == 22]
        self.assertTrue((clock_rows["exit_long"] == 1).all())

    def test_signal_columns_are_binary(self) -> None:
        frame = run(self.strategy, make_frame(dip_prices()))
        for column in ("enter_long", "exit_long"):
            values = frame[column].dropna().unique().tolist()
            self.assertTrue(set(values).issubset({1}))

    def test_zero_volume_gives_no_signal(self) -> None:
        frame = run(self.strategy, make_frame(dip_prices(), volume=0.0))
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame["exit_long"].fillna(0).sum()), 0)
        # A single zero-volume signal candle is suppressed, neighbours are not.
        base = run(self.strategy, make_frame(dip_prices()))
        row = base.index[base["enter_long"] == 1][0]
        data = make_frame(dip_prices())
        data.loc[row, "volume"] = 0.0
        changed = run(self.strategy, data)
        self.assertNotEqual(changed.loc[row, "enter_long"], 1)

    def test_undefined_startup_values_give_no_entry(self) -> None:
        prices = [100.0 + 0.1 * i for i in range(700)]
        # Early dip (rows 100-139) inside the warm-up: low7 is defined, SMA200b is not.
        for i in range(100, 140):
            prices[i] = prices[99] - 0.1 * (i - 99)
        frame = run(self.strategy, make_frame(prices))
        warm = frame.iloc[:399]
        self.assertTrue(warm["block_sma"].isna().all())
        self.assertTrue(warm["block_low7"].iloc[20:].notna().any())
        self.assertEqual(int(warm["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame.iloc[: self.strategy.startup_candle_count]["enter_long"].fillna(0).sum()), 0)

    def test_missing_hour_makes_block_unusable(self) -> None:
        prices = dip_prices()
        data = make_frame(prices)
        data = data.drop(index=[700 - 5]).reset_index(drop=True)  # drop one hourly candle
        frame = self.strategy.populate_indicators(data, {})
        # Windows containing the missing block stay undefined.
        self.assertTrue(pd.isna(frame["block_sma"].iloc[-3:]).all())

    def test_no_lookahead(self) -> None:
        prices = dip_prices(count=760, dip_start=600)
        n, k = 690, 70
        first = run(self.strategy, make_frame(prices[:n]))
        longer = run(self.strategy, make_frame(prices[: n + k]))
        columns = [
            c for c in first.columns if c not in {"open", "high", "low", "close", "volume", "date"}
        ]
        a = first[columns].copy()
        b = longer.loc[: n - 1, columns].copy()
        for column in ("enter_long", "exit_long"):
            a[column] = a[column].fillna(0)
            b[column] = b[column].fillna(0)
        for column in ("enter_tag", "exit_tag"):
            a[column] = a[column].fillna("")
            b[column] = b[column].fillna("")
        pd.testing.assert_frame_equal(a, b, check_dtype=False)

    def test_custom_exit_time_exit(self) -> None:
        opened = datetime(2024, 3, 1, 2, 0, tzinfo=timezone.utc)
        trade = SimpleNamespace(open_date_utc=opened)
        early = self.strategy.custom_exit("BTC/USDT", trade, opened + timedelta(hours=11), 100.0, 0.001)
        self.assertIsNone(early)
        at = self.strategy.custom_exit("BTC/USDT", trade, opened + timedelta(hours=12), 100.0, 0.001)
        self.assertEqual(at, "time_exit_12h")

    def test_custom_exit_clock_exit(self) -> None:
        opened = datetime(2024, 3, 1, 14, 0, tzinfo=timezone.utc)
        trade = SimpleNamespace(open_date_utc=opened)
        before = self.strategy.custom_exit(
            "BTC/USDT", trade, datetime(2024, 3, 1, 22, 0, tzinfo=timezone.utc), 100.0, 0.0
        )
        self.assertIsNone(before)
        at = self.strategy.custom_exit(
            "BTC/USDT", trade, datetime(2024, 3, 1, 23, 0, tzinfo=timezone.utc), 100.0, 0.0
        )
        self.assertEqual(at, "clock_exit_23utc")


if __name__ == "__main__":
    unittest.main()
