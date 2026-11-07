import importlib.util
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


ROOT = Path(__file__).parents[1]
NAME = "HourlyBullFlagBreak_H075_v1"


def load_module():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()
STRATEGY = MODULE.HourlyBullFlagBreak_H075_v1
# The module bound Trade at import; point it at this test's stub regardless of import order.
MODULE.Trade = _TradeStub


def make_flag_frame(n: int = 600) -> pd.DataFrame:
    """Slow uptrend with a bull flag (6-bar pole, 4-bar quiet flag, breakout) every 30 bars."""
    rows = []
    price = 100.0
    i = 0
    while len(rows) < n:
        phase = i % 30
        if 10 <= phase < 16:  # pole: +1% per bar, high volume
            open_ = price
            price *= 1.01
            rows.append((open_, price * 1.001, open_ * 0.999, price, 300.0))
        elif 16 <= phase < 20:  # flag: small pullback, tight, quiet
            open_ = price
            price *= 0.998
            rows.append((open_, open_ * 1.0005, price * 0.999, price, 50.0))
        elif phase == 20:  # breakout bar
            open_ = price
            price *= 1.02
            rows.append((open_, price * 1.001, open_ * 0.999, price, 200.0))
        else:  # slow drift up with small noise
            open_ = price
            price *= 1.0005 + 0.002 * np.sin(i)
            rows.append((open_, max(open_, price) * 1.002, min(open_, price) * 0.998, price, 100.0))
        i += 1
    frame = pd.DataFrame(rows[:n], columns=["open", "high", "low", "close", "volume"])
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


class HourlyBullFlagBreakTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(STRATEGY.INTERFACE_VERSION, 3)
        self.assertEqual(STRATEGY.timeframe, "1h")
        self.assertFalse(STRATEGY.can_short)
        self.assertEqual(STRATEGY.minimal_roi, {"0": 100.0})
        self.assertEqual(STRATEGY.stoploss, -0.04)
        self.assertGreaterEqual(STRATEGY.startup_candle_count, 200)

    def test_synthetic_flags_produce_entries(self) -> None:
        out = run(make_flag_frame())
        self.assertGreater(int(column(out, "enter_long").fillna(0).sum()), 0)

    def test_signal_columns_are_binary(self) -> None:
        out = run(make_flag_frame())
        for name in ("enter_long", "exit_long"):
            if name in out:
                values = out[name].dropna().unique().tolist()
                self.assertTrue(set(values).issubset({1}))

    def test_zero_volume_produces_no_signal(self) -> None:
        frame = make_flag_frame()
        base = run(frame)
        entries = base.index[column(base, "enter_long").fillna(0) == 1]
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
        out = run(make_flag_frame())
        enter = column(out, "enter_long").fillna(0)
        self.assertEqual(int(enter[out["sma168"].isna()].sum()), 0)
        self.assertEqual(int(enter.iloc[: STRATEGY.startup_candle_count - 32].sum()), 0)

    def test_no_lookahead_when_future_candles_appended(self) -> None:
        full = make_flag_frame(600)
        n = 450
        short = run(full.iloc[:n].copy())
        long = run(full.copy())
        for name in ("sma168", "pole_high", "pole_height", "flag_low", "pole_ts", "flag_target"):
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

    def test_tag_and_one_trade_per_pole(self) -> None:
        out = run(make_flag_frame())
        row = out[column(out, "enter_long").fillna(0) == 1].iloc[0]
        parsed = MODULE.parse_tag(row["enter_tag"])
        self.assertIsNotNone(parsed)
        pole_ts, flag_low, target = parsed
        self.assertAlmostEqual(flag_low, row["flag_low"])
        self.assertAlmostEqual(target, row["flag_low"] + row["pole_height"])
        strategy = STRATEGY()
        _TradeStub.trades = []
        self.assertTrue(strategy.confirm_trade_entry(
            "BTC/USDT", "market", 1.0, 1.0, "gtc", row["date"], row["enter_tag"], "long"))
        _TradeStub.trades = [types.SimpleNamespace(enter_tag=row["enter_tag"])]
        self.assertFalse(strategy.confirm_trade_entry(
            "BTC/USDT", "market", 1.0, 1.0, "gtc", row["date"], row["enter_tag"], "long"))
        _TradeStub.trades = []

    def test_custom_exit_rules(self) -> None:
        tag = MODULE.make_tag(1_700_000_000, 100.0, 106.0)
        open_date = pd.Timestamp("2024-01-10 00:00", tz="UTC")
        trade = types.SimpleNamespace(
            enter_tag=tag, open_rate=104.0, fee_open=0.0, fee_close=0.0, open_date_utc=open_date
        )
        bars = pd.DataFrame(
            {
                "date": pd.date_range(open_date, periods=3, freq="1h"),
                "close": [104.0, 99.0, 104.0],
                "volume": [10.0, 10.0, 10.0],
            }
        )
        strategy = STRATEGY()
        strategy.dp = types.SimpleNamespace(get_analyzed_dataframe=lambda pair, tf: (bars, None))
        self.assertAlmostEqual(strategy.custom_roi("X", trade, open_date, 0, tag, "long"), 2.0 / 104.0)
        self.assertEqual(
            strategy.custom_exit("X", trade, open_date + timedelta(hours=1), 104.0, 0.0), None
        )
        self.assertEqual(
            strategy.custom_exit("X", trade, open_date + timedelta(hours=2), 101.0, 0.0),
            "close_below_flag_low",
        )
        self.assertEqual(
            strategy.custom_exit("X", trade, open_date + timedelta(hours=1), 106.5, 0.0),
            "target_flag_low_plus_pole",
        )
        bars.loc[1, "close"] = 103.0
        self.assertEqual(
            strategy.custom_exit("X", trade, open_date + timedelta(hours=24), 104.0, 0.0),
            "time_exit_24_bars",
        )


if __name__ == "__main__":
    unittest.main()
