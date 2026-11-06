import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

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


class _TradeStub:
    trades: list = []

    @classmethod
    def get_trades_proxy(cls, pair=None, **kwargs):
        return list(cls.trades)


persistence_module = types.ModuleType("freqtrade.persistence")
persistence_module.Trade = _TradeStub
sys.modules.setdefault("freqtrade.persistence", persistence_module)

ROOT = Path(__file__).parents[2]
FILENAME = "HourlyFailedBreakdownReclaim_H055_v1.py"
CLASS_NAME = "HourlyFailedBreakdownReclaim_H055_v1"


def load_module():
    path = ROOT / "user_data" / "strategies" / "_archive" / FILENAME
    spec = importlib.util.spec_from_file_location(CLASS_NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()
Strategy = MODULE.HourlyFailedBreakdownReclaim_H055_v1
START = datetime(2024, 1, 1, tzinfo=timezone.utc)
BAR = timedelta(minutes=15)


def make_frame(closes, lows=None) -> pd.DataFrame:
    n = len(closes)
    return pd.DataFrame(
        {
            "date": pd.date_range(START, periods=n, freq="15min", tz="UTC"),
            "open": closes,
            "high": [c * 1.001 for c in closes],
            "low": lows if lows is not None else [c * 0.999 for c in closes],
            "close": closes,
            "volume": [1.0] * n,
        }
    )


def sweep_frame(extra: int = 0) -> pd.DataFrame:
    """Flat at 100, then a sweep bar (index 450) and a reclaim bar (index 451)."""
    closes = [100.0] * 450 + [99.5, 100.5] + [100.5 + 0.01 * i for i in range(extra)]
    lows = [c * 0.999 for c in closes]
    lows[450] = 99.4
    lows[451] = 100.4
    return make_frame(closes, lows)


def run(frame: pd.DataFrame) -> pd.DataFrame:
    strategy = Strategy()
    frame = strategy.populate_indicators(frame, {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    return frame


def column(frame: pd.DataFrame, name: str) -> pd.Series:
    if name in frame:
        return frame[name].fillna(0)
    return pd.Series(0, index=frame.index)


class _Trade:
    def __init__(self, open_date, open_rate=100.0, enter_tag=None):
        self.open_date_utc = open_date
        self.open_rate = open_rate
        self.enter_tag = enter_tag
        self.fee_open = 0.001
        self.fee_close = 0.001


class H055ContractTests(unittest.TestCase):
    def test_class_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.02)
        self.assertGreaterEqual(Strategy.startup_candle_count, 400)

    def test_indicator_windows(self) -> None:
        lows = [float(200 - i) for i in range(500)]
        frame = make_frame([100.0] * 500, lows)
        frame = Strategy().populate_indicators(frame, {})
        self.assertTrue(pd.isna(frame.loc[99, "pl"]))
        # PL(t) = min low of bars t-100..t-5.
        self.assertEqual(frame.loc[100, "pl"], min(lows[0:96]))
        self.assertEqual(frame.loc[300, "pl"], min(lows[200:296]))
        self.assertEqual(frame.loc[300, "sl4"], min(lows[297:301]))
        self.assertTrue(pd.isna(frame.loc[382, "sma_trend"]))
        self.assertFalse(pd.isna(frame.loc[383, "sma_trend"]))

    def test_sweep_and_reclaim_fires_entry(self) -> None:
        frame = run(sweep_frame(extra=10))
        entries = column(frame, "enter_long")
        self.assertEqual(entries.sum(), 1)
        self.assertEqual(entries[451], 1)
        self.assertEqual(MODULE.parse_tag(frame.loc[451, "enter_tag"]), 99.4)

    def test_depth_cap_blocks_deep_breaks(self) -> None:
        frame = sweep_frame(extra=10)
        frame.loc[450, "low"] = 97.0  # more than 2% under PL (99.9)
        self.assertEqual(column(run(frame), "enter_long").sum(), 0)

    def test_signal_columns_are_binary(self) -> None:
        closes = [100.0 + (i % 13) * 0.3 - (i % 29) * 0.2 for i in range(900)]
        frame = run(make_frame(closes))
        frame = pd.concat([frame, run(sweep_frame(extra=20))], ignore_index=True)
        for name in ("enter_long", "exit_long"):
            if name in frame:
                self.assertTrue(set(frame[name].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_produces_no_signal(self) -> None:
        frame = sweep_frame(extra=10)
        frame["volume"] = 0.0
        frame = run(frame)
        self.assertEqual(column(frame, "enter_long").sum(), 0)
        self.assertEqual(column(frame, "exit_long").sum(), 0)

    def test_undefined_startup_values_produce_no_signal(self) -> None:
        # A sweep-and-reclaim pattern inside the warm-up, where SMA384 is undefined.
        closes = [100.0] * 200 + [99.5, 100.5] + [100.5] * 50
        lows = [c * 0.999 for c in closes]
        lows[200] = 99.4
        frame = run(make_frame(closes, lows))
        self.assertEqual(column(frame, "enter_long").iloc[: Strategy.startup_candle_count].sum(), 0)
        self.assertEqual(column(frame, "enter_long").sum(), 0)

    def test_signal_unchanged_when_future_candles_appended(self) -> None:
        n, k = 460, 200
        full = sweep_frame(extra=k)
        full.loc[n:, "close"] = 50.0
        full.loc[n:, "low"] = 40.0
        full.loc[n:, "high"] = 60.0
        before = run(full.iloc[:n].copy())
        after = run(full.copy())
        for name in ("enter_long", "exit_long", "pl", "sl4", "sma_trend"):
            pd.testing.assert_series_equal(
                column(before, name).reset_index(drop=True),
                column(after, name).iloc[:n].reset_index(drop=True),
                check_dtype=False,
                check_names=False,
            )
        self.assertEqual(column(before, "enter_long").sum(), 1)

    def test_entry_spacing(self) -> None:
        strategy = Strategy()
        tag = MODULE.make_tag(99.4)
        fill_time = START + BAR * 100  # fill at open of bar t+1, signal bar t = 99
        try:
            # Previous fill at bar t-15 = 84: blocked.
            _TradeStub.trades = [_Trade(START + BAR * 84)]
            self.assertFalse(strategy.confirm_trade_entry("BTC/USDT", "market", 1, 1, "GTC", fill_time, tag, "long"))
            # Previous fill at bar t-16 = 83: allowed.
            _TradeStub.trades = [_Trade(START + BAR * 83)]
            self.assertTrue(strategy.confirm_trade_entry("BTC/USDT", "market", 1, 1, "GTC", fill_time, tag, "long"))
        finally:
            _TradeStub.trades = []

    def test_take_profit_and_time_exit(self) -> None:
        strategy = Strategy()
        trade = _Trade(START, open_rate=100.0, enter_tag=MODULE.make_tag(99.4))
        roi = strategy.custom_roi("BTC/USDT", trade, START, 0, trade.enter_tag, "long")
        exit_price = 100.0 * (1 + roi + 0.001) / (1 - 0.001)
        self.assertAlmostEqual(exit_price, 101.2)

        class _DP:
            def __init__(self, frame):
                self.frame = frame

            def get_analyzed_dataframe(self, pair, timeframe):
                return self.frame, None

        frame = make_frame([100.0] * 60)
        frame["date"] = pd.date_range(START - BAR * 5, periods=60, freq="15min", tz="UTC")
        strategy.dp = _DP(frame)
        self.assertEqual(strategy.custom_exit("p", trade, START + BAR * 2, 101.3, 0.0), "take_profit_1_2pct")
        self.assertIsNone(strategy.custom_exit("p", trade, START + BAR * 47, 100.0, 0.0))
        self.assertEqual(strategy.custom_exit("p", trade, START + BAR * 48, 100.0, 0.0), "time_exit_48_bars")
        # Bar 3 after the fill closes under SWEEP_LOW * 0.998 -> exit at the open of bar 4.
        frame.loc[frame["date"] == START + BAR * 3, "close"] = 99.0
        self.assertIsNone(strategy.custom_exit("p", trade, START + BAR * 3, 100.0, 0.0))
        self.assertEqual(strategy.custom_exit("p", trade, START + BAR * 4, 100.0, 0.0), "sweep_low_exit")


if __name__ == "__main__":
    unittest.main()
