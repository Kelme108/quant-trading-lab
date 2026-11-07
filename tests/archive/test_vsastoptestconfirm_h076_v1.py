import importlib.util
import math
import sys
import types
import unittest
from datetime import timedelta
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


class _TradeStub:
    trades: list = []

    @classmethod
    def get_trades_proxy(cls, pair=None, **kwargs):
        return list(cls.trades)


persistence_module = types.ModuleType("freqtrade.persistence")
persistence_module.Trade = _TradeStub
sys.modules.setdefault("freqtrade.persistence", persistence_module)

talib = types.ModuleType("talib")
talib_abstract = types.ModuleType("talib.abstract")
talib_abstract.SMA = lambda dataframe, timeperiod: dataframe["close"].rolling(timeperiod).mean()
talib_abstract.RSI = lambda dataframe, timeperiod: pd.Series(50.0, index=dataframe.index)
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)


ROOT = Path(__file__).parents[2]
NAME = "VSAStopTestConfirm_H076_v1"


def load_module():
    path = ROOT / "user_data" / "strategies" / "_archive" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()
STRATEGY = MODULE.VSAStopTestConfirm_H076_v1
# The module bound Trade at import; point it at this test's stub regardless of import order.
MODULE.Trade = _TradeStub

CYCLE = 60
STOP_K = 46
TEST_K = 48
CONFIRM_K = 49


def cycle_bar(k: int, i: int) -> tuple:
    """(open, high, low, close, volume) for offset k of a 60-bar cycle containing one full VSA sequence."""
    if k < 40:  # quiet range around 100
        close = 100.0 + 0.2 * math.sin(i)
        return (100.0, close + 0.5, 99.5 - 0.1 * (k % 3), close, 100.0)
    if k < STOP_K:  # decline into the low
        close = [99.0, 98.0, 97.0, 96.5, 96.0, 95.8][k - 40]
        return (close + 0.2, close + 0.3, close - 0.3, close, 100.0)
    if k == STOP_K:  # stopping bar: new 48-bar low, 4x volume, closes in the upper half
        return (95.6, 96.0, 94.0, 95.5, 400.0)
    if k == STOP_K + 1:
        return (95.5, 96.2, 95.0, 96.0, 100.0)
    if k == TEST_K:  # test bar: lower low holding low(s), half volume, upper-half close
        return (95.6, 95.8, 94.5, 95.5, 50.0)
    if k == CONFIRM_K:  # confirmation: close above high(t) on more volume than the test
        return (95.6, 96.7, 95.4, 96.5, 150.0)
    close = 96.5 + 0.35 * (k - CONFIRM_K)  # recovery to ~100
    return (close - 0.2, close + 0.3, close - 0.3, close, 100.0)


def make_frame(n: int = 300) -> pd.DataFrame:
    rows = [cycle_bar(i % CYCLE, i) for i in range(n)]
    frame = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"])
    frame.insert(0, "date", pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC"))
    return frame


def run(frame: pd.DataFrame) -> pd.DataFrame:
    strategy = STRATEGY()
    out = strategy.populate_indicators(frame.copy(), {"pair": "BTC/USDT"})
    out = strategy.populate_entry_trend(out, {"pair": "BTC/USDT"})
    out = strategy.populate_exit_trend(out, {"pair": "BTC/USDT"})
    return out


def column(frame: pd.DataFrame, name: str) -> pd.Series:
    if name in frame:
        return frame[name]
    return pd.Series(np.nan, index=frame.index)


def entry_index(frame: pd.DataFrame) -> list:
    return frame.index[column(frame, "enter_long").fillna(0) == 1].tolist()


class VSAStopTestConfirmTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(STRATEGY.INTERFACE_VERSION, 3)
        self.assertEqual(STRATEGY.timeframe, "1h")
        self.assertFalse(STRATEGY.can_short)
        self.assertEqual(STRATEGY.minimal_roi, {"0": 100.0})
        self.assertEqual(STRATEGY.stoploss, -0.10)
        self.assertGreaterEqual(STRATEGY.startup_candle_count, 64)

    def test_sequence_produces_entry_on_confirmation_bar(self) -> None:
        out = run(make_frame())
        # The first cycle's stopping bar has no 48-bar volume median, so entries start in cycle 2.
        # Every bar in t+1..t+3 closing above high(t) on more volume than t confirms; confirm_trade_entry
        # lets only the first entry per stopping bar through.
        expected = [c * CYCLE + CONFIRM_K + j for c in range(1, 5) for j in range(3)]
        self.assertEqual(entry_index(out), expected)
        self.assertEqual(len(set(out.loc[expected[:3], "enter_tag"])), 1)
        row = out.loc[expected[0]]
        stop_ts, test_low = MODULE.parse_tag(row["enter_tag"])
        self.assertAlmostEqual(test_low, 94.5)
        self.assertEqual(stop_ts, int(out.loc[CYCLE + STOP_K, "date"].timestamp()))

    def test_void_and_volume_conditions(self) -> None:
        frame = make_frame()
        # A close below low(s) between the stopping and the test bar cancels the cycle-2 setup.
        frame.loc[CYCLE + STOP_K + 1, ["low", "close"]] = [93.5, 93.9]
        out = run(frame)
        self.assertNotIn(CYCLE + CONFIRM_K, entry_index(out))
        frame = make_frame()
        # A test bar on too much volume (> 0.6 * Vmed(s)) is not a test.
        frame.loc[CYCLE + TEST_K, "volume"] = 61.0
        out = run(frame)
        self.assertNotIn(CYCLE + CONFIRM_K, entry_index(out))

    def test_signal_columns_are_binary(self) -> None:
        out = run(make_frame())
        for name in ("enter_long", "exit_long"):
            if name in out:
                values = out[name].dropna().unique().tolist()
                self.assertTrue(set(values).issubset({1}))

    def test_zero_volume_produces_no_signal(self) -> None:
        frame = make_frame()
        entries = entry_index(run(frame))
        self.assertGreater(len(entries), 0)
        frame.loc[entries, "volume"] = 0.0
        out = run(frame)
        self.assertEqual(int(column(out, "enter_long").fillna(0).loc[entries].sum()), 0)
        self.assertEqual(int(column(out, "exit_long").fillna(0).loc[entries].sum()), 0)

        frame["volume"] = 0.0
        out = run(frame)
        self.assertEqual(int(column(out, "enter_long").fillna(0).sum()), 0)
        self.assertEqual(int(column(out, "exit_long").fillna(0).sum()), 0)

    def test_undefined_startup_values_produce_no_signal(self) -> None:
        out = run(make_frame())
        enter = column(out, "enter_long").fillna(0)
        self.assertEqual(int(enter.iloc[: STRATEGY.startup_candle_count].sum()), 0)
        self.assertEqual(int(enter[out["test_low"].isna() | out["setup_ts"].isna()].sum()), 0)
        # Undefined prices at the start produce no signal either.
        frame = make_frame()
        frame.loc[:70, ["open", "high", "low", "close"]] = np.nan
        out = run(frame)
        self.assertEqual(int(column(out, "enter_long").fillna(0).iloc[:71].sum()), 0)

    def test_no_lookahead_when_future_candles_appended(self) -> None:
        full = make_frame(300)
        for n in (170, 229, 230):
            short = run(full.iloc[:n].copy())
            long = run(full.copy())
            for name in ("vmed48", "close_pos", "stopping_bar", "setup_ts", "setup_low",
                         "test_low", "test_high", "confirm_bar"):
                pd.testing.assert_series_equal(
                    short[name], long[name].iloc[:n], check_dtype=False, check_names=False
                )
            pd.testing.assert_series_equal(
                column(short, "enter_long").fillna(0),
                column(long, "enter_long").iloc[:n].fillna(0),
                check_dtype=False,
                check_names=False,
            )
            pd.testing.assert_series_equal(
                column(short, "enter_tag").fillna(""),
                column(long, "enter_tag").iloc[:n].fillna(""),
                check_dtype=False,
                check_names=False,
            )

    def test_stopping_bar_used_once(self) -> None:
        out = run(make_frame())
        tag = out.loc[entry_index(out)[0], "enter_tag"]
        strategy = STRATEGY()
        _TradeStub.trades = []
        self.assertTrue(strategy.confirm_trade_entry("X", "market", 1.0, 1.0, "gtc", None, tag, "long"))
        _TradeStub.trades = [types.SimpleNamespace(enter_tag=tag)]
        self.assertFalse(strategy.confirm_trade_entry("X", "market", 1.0, 1.0, "gtc", None, tag, "long"))
        _TradeStub.trades = []

    def test_exit_rules(self) -> None:
        tag = MODULE.make_tag(1_700_000_000, 95.0)
        open_date = pd.Timestamp("2024-01-10 00:00", tz="UTC")
        trade = types.SimpleNamespace(
            enter_tag=tag, open_rate=97.0, fee_open=0.0, fee_close=0.0, open_date_utc=open_date
        )
        strategy = STRATEGY()
        # Stop price 95 expressed relative to the current rate.
        self.assertAlmostEqual(strategy.custom_stoploss("X", trade, open_date, 100.0, 0.0), 0.05)
        # Target 97 + 2 * 2 = 101.
        self.assertAlmostEqual(strategy.custom_roi("X", trade, open_date, 0, tag, "long"), 4.0 / 97.0)
        self.assertIsNone(strategy.custom_exit("X", trade, open_date + timedelta(hours=23), 98.0, 0.0))
        self.assertEqual(strategy.custom_exit("X", trade, open_date + timedelta(hours=1), 101.5, 0.0), "target_2r")
        self.assertEqual(
            strategy.custom_exit("X", trade, open_date + timedelta(hours=24), 98.0, 0.0), "time_exit_24_bars"
        )
        low_fill = types.SimpleNamespace(
            enter_tag=tag, open_rate=94.8, fee_open=0.0, fee_close=0.0, open_date_utc=open_date
        )
        self.assertEqual(strategy.custom_stoploss("X", low_fill, open_date, 94.8, 0.0), 0.0)
        self.assertIsNone(strategy.custom_roi("X", low_fill, open_date, 0, tag, "long"))
        self.assertEqual(
            strategy.custom_exit("X", low_fill, open_date, 94.8, 0.0), "stop_entry_at_or_below_test_low"
        )


if __name__ == "__main__":
    unittest.main()
