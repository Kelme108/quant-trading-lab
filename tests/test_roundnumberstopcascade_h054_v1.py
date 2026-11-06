import importlib.util
import sys
import types
import unittest
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np
import pandas as pd

# Keep the tests runnable without installing Freqtrade or TA-Lib on the host.
freqtrade = types.ModuleType("freqtrade")
strategy_module = types.ModuleType("freqtrade.strategy")
strategy_module.IStrategy = object
freqtrade.strategy = strategy_module
sys.modules.setdefault("freqtrade", freqtrade)
sys.modules.setdefault("freqtrade.strategy", strategy_module)


class _StubTrade:
    @staticmethod
    def get_trades_proxy(**kwargs):
        return []


persistence_module = types.ModuleType("freqtrade.persistence")
persistence_module.Trade = _StubTrade
sys.modules.setdefault("freqtrade.persistence", persistence_module)

talib = types.ModuleType("talib")
talib_abstract = types.ModuleType("talib.abstract")
talib_abstract.SMA = lambda dataframe, timeperiod: dataframe["close"].rolling(timeperiod).mean()
talib_abstract.RSI = lambda dataframe, timeperiod: pd.Series(50.0, index=dataframe.index)
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)

ROOT = Path(__file__).parents[1]
NAME = "RoundNumberStopCascade_H054_v1"


def load_module():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()
Strategy = getattr(MODULE, NAME)
START = pd.Timestamp("2024-01-01 00:00", tz="UTC")
BREAK_BAR = 500


def make_frame(closes, volume=1.0, wick=0.001):
    closes = np.asarray(closes, dtype=float)
    opens = np.concatenate([[closes[0]], closes[:-1]])
    return pd.DataFrame(
        {
            "date": pd.date_range(START, periods=len(closes), freq="15min"),
            "open": opens,
            "high": np.maximum(opens, closes) * (1.0 + wick),
            "low": np.minimum(opens, closes) * (1.0 - wick),
            "close": closes,
            "volume": np.full(len(closes), volume),
        }
    )


def breakout_closes():
    """Flat at 100.5 (grid S = 1), then one close at 101.3 through the fresh level 101."""
    closes = [100.5] * 600
    closes[BREAK_BAR] = 101.3
    for i in range(BREAK_BAR + 1, 600):
        closes[i] = 101.3
    return closes


def random_walk(n, seed=7):
    rng = np.random.default_rng(seed)
    return 100.0 * np.exp(np.cumsum(rng.normal(0.0004, 0.004, n)))


def run(frame):
    strategy = Strategy()
    out = strategy.populate_indicators(frame.copy(), {"pair": "BTC/USDT"})
    out = strategy.populate_entry_trend(out, {"pair": "BTC/USDT"})
    out = strategy.populate_exit_trend(out, {"pair": "BTC/USDT"})
    return out


def entries(frame):
    return frame.get("enter_long", pd.Series(0, index=frame.index)).fillna(0)


class RoundNumberStopCascadeTests(unittest.TestCase):
    def test_class_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertAlmostEqual(Strategy.stoploss, -0.03)
        self.assertGreaterEqual(Strategy.startup_candle_count, 400)
        self.assertTrue(Strategy.use_custom_stoploss)
        self.assertTrue(Strategy.use_custom_roi)

    def test_grid_step_examples(self):
        prices = pd.Series([60000.0, 3000.0, 600.0, 100.0, 50000.0, 12500.0, 0.5, np.nan])
        steps = MODULE.grid_step(prices).tolist()
        self.assertEqual(steps[:7], [1000.0, 50.0, 10.0, 1.0, 1000.0, 250.0, 0.01])
        self.assertTrue(np.isnan(steps[7]))

    def test_reference_is_previous_day_2345_close(self):
        closes = np.arange(200, dtype=float) + 1000.0
        out = MODULE.round_level_indicators(make_frame(closes))
        self.assertTrue(out.loc[:95, "grid_ref"].isna().all())
        self.assertTrue((out.loc[96:191, "grid_ref"] == closes[95]).all())
        self.assertTrue((out.loc[192:, "grid_ref"] == closes[191]).all())

    def test_breakout_through_fresh_level_enters_once_with_tag(self):
        out = run(make_frame(breakout_closes()))
        sig = entries(out)
        self.assertEqual(int(sig.sum()), 1)
        self.assertEqual(int(sig.iloc[BREAK_BAR]), 1)
        tag = out.loc[BREAK_BAR, "enter_tag"]
        self.assertEqual(MODULE.parse_tag(tag), (101.0, 1.0))

    def test_confirmation_and_freshness_filters(self):
        closes = breakout_closes()
        closes[BREAK_BAR] = 101.1  # below 1.002 * 101
        for i in range(BREAK_BAR + 1, 600):
            closes[i] = 101.1
        self.assertEqual(int(entries(run(make_frame(closes))).sum()), 0)

        closes = breakout_closes()
        closes[BREAK_BAR - 10] = 101.05  # level touched within the 32 previous bars
        out = run(make_frame(closes))
        self.assertEqual(int(entries(out).iloc[BREAK_BAR]), 0)

    def test_signal_columns_are_binary(self):
        for closes in (breakout_closes(), random_walk(1500)):
            out = run(make_frame(closes))
            for column in ("enter_long", "exit_long"):
                if column in out:
                    self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_produces_no_signal(self):
        out = run(make_frame(breakout_closes(), volume=0.0))
        self.assertEqual(int(entries(out).sum()), 0)
        self.assertEqual(int(out.get("exit_long", pd.Series(0, index=out.index)).fillna(0).sum()), 0)

    def test_undefined_startup_values_produce_no_signal(self):
        for closes in (breakout_closes(), random_walk(1500), np.linspace(100, 400, 1500)):
            out = run(make_frame(closes))
            sig = entries(out)
            undefined = (
                out["grid_step"].isna() | out["fresh_high"].isna() | out["sma_trend"].isna()
                | out["prev_close"].isna()
            )
            self.assertEqual(int(sig[undefined].sum()), 0)
            self.assertEqual(int(sig.iloc[:96].sum()), 0)

    def test_signals_do_not_change_when_future_candles_are_appended(self):
        closes = random_walk(2000, seed=11)
        n = 1400
        short = run(make_frame(closes[:n]))
        full = run(make_frame(closes))
        self.assertGreater(int(entries(full).iloc[:n].sum()), 0)
        pd.testing.assert_series_equal(entries(short), entries(full).iloc[:n], check_dtype=False)
        columns = ["grid_ref", "grid_step", "grid_level", "fresh_high", "sma_trend", "prev_close"]
        pd.testing.assert_frame_equal(short[columns], full.iloc[:n][columns], check_dtype=False)
        if "enter_tag" in short:
            pd.testing.assert_series_equal(
                short["enter_tag"], full["enter_tag"].iloc[:n], check_dtype=False
            )

    def _trade(self, open_rate=101.4, tag=None):
        return SimpleNamespace(
            enter_tag=tag or MODULE.make_tag("2024-01-06", 101.0, 1.0),
            open_rate=open_rate,
            fee_open=0.001,
            fee_close=0.001,
            open_date_utc=START.to_pydatetime(),
        )

    def test_stop_is_fixed_at_half_step_below_level(self):
        strategy = Strategy()
        trade = self._trade()
        for rate in (101.4, 102.0, 100.9):
            ratio = strategy.custom_stoploss("BTC/USDT", trade, START, rate, 0.0)
            self.assertAlmostEqual(rate * (1.0 - ratio), 100.5)
        self.assertEqual(strategy.custom_stoploss("BTC/USDT", trade, START, 100.0, 0.0), 0.0)

    def test_roi_exit_price_is_next_level(self):
        strategy = Strategy()
        trade = self._trade()
        roi = strategy.custom_roi("BTC/USDT", trade, START, 0, trade.enter_tag, "long")
        # Freqtrade's ROI exit price: open * (roi + 1 + fee_open) / (1 - fee_close).
        price = trade.open_rate * (roi + 1.0 + trade.fee_open) / (1.0 - trade.fee_close)
        self.assertAlmostEqual(price, 102.0)

    def test_custom_exit_take_profit_and_time_exit(self):
        strategy = Strategy()
        trade = self._trade()
        t0 = START.to_pydatetime()
        self.assertIsNone(strategy.custom_exit("p", trade, t0 + timedelta(minutes=15 * 31), 101.5, 0.0))
        self.assertEqual(
            strategy.custom_exit("p", trade, t0 + timedelta(minutes=15 * 32), 101.5, 0.0),
            "time_exit_32_bars",
        )
        self.assertEqual(
            strategy.custom_exit("p", trade, t0 + timedelta(minutes=15), 102.0, 0.0),
            "take_profit_next_level",
        )

    def test_one_entry_per_level_per_day(self):
        strategy = Strategy()
        tag = MODULE.make_tag("2024-01-06", 101.0, 1.0)
        other = MODULE.make_tag("2024-01-07", 101.0, 1.0)
        previous = [SimpleNamespace(enter_tag=tag)]
        with mock.patch.object(MODULE.Trade, "get_trades_proxy", return_value=previous):
            self.assertFalse(
                strategy.confirm_trade_entry("p", "market", 1.0, 101.4, "GTC", START, tag, "long")
            )
            self.assertTrue(
                strategy.confirm_trade_entry("p", "market", 1.0, 101.4, "GTC", START, other, "long")
            )


if __name__ == "__main__":
    unittest.main()
