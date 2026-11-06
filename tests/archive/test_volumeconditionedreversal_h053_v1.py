import importlib.util
import math
import sys
import types
import unittest
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

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
NAME = "VolumeConditionedReversal_H053_v1"
BAR = timedelta(hours=1)


def load_module():
    path = ROOT / "user_data" / "strategies" / "_archive" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


module = load_module()
Strategy = getattr(module, NAME)

START = pd.Timestamp("2024-03-01 00:00", tz="UTC")
SIGNAL_BAR = 900


class FakeDP:
    def __init__(self, analyzed=None):
        self.analyzed = analyzed

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.analyzed, None


class FakeTrade:
    def __init__(self, open_date):
        self.open_date_utc = open_date


def make_1h(n=1000, selloff=True, stay_down=False):
    """Close oscillates 100 / 100.2; flat at 100 on low volume, then a drop to 97 at SIGNAL_BAR."""
    close = np.where(np.arange(n) % 2 == 0, 100.0, 100.2)
    volume = np.ones(n)
    s = SIGNAL_BAR
    if selloff and n > s:
        close[s - 12] = 100.0
        close[s - 11 : s] = 100.0
        close[s] = 97.0
        volume[s - 11 : s + 1] = 0.5
        if stay_down:
            close[s + 1 :] = 97.5
            volume[s + 1 :] = 2.0
    open_ = np.concatenate([[close[0]], close[:-1]])
    return pd.DataFrame(
        {
            "date": pd.date_range(START, periods=n, freq="1h"),
            "open": open_,
            "high": np.maximum(open_, close) * 1.001,
            "low": np.minimum(open_, close) * 0.999,
            "close": close,
            "volume": volume,
        }
    )


def run(frame):
    strategy = Strategy()
    strategy.dp = FakeDP()
    out = strategy.populate_indicators(frame.copy(), {"pair": "BTC/USDT"})
    out = strategy.populate_entry_trend(out, {"pair": "BTC/USDT"})
    out = strategy.populate_exit_trend(out, {"pair": "BTC/USDT"})
    return strategy, out


def entries(out):
    return out.get("enter_long", pd.Series(0.0, index=out.index)).fillna(0)


class VolumeConditionedReversalH053Tests(unittest.TestCase):
    def test_contract_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.05)
        self.assertGreaterEqual(Strategy.startup_candle_count, 732)
        self.assertEqual(Strategy.startup_candle_count, 800)
        for name in ("custom_stake_amount", "adjust_trade_position", "leverage", "protections"):
            self.assertFalse(hasattr(Strategy, name))

    def test_volume_reference_excludes_current_window(self):
        rng = np.random.default_rng(1)
        volume = pd.Series(rng.uniform(1.0, 10.0, 900))
        v12, vmed = module.volume_reference(volume)
        t = 850
        self.assertAlmostEqual(v12.iloc[t], volume.iloc[t - 11 : t + 1].sum())
        expected = np.median(
            [volume.iloc[t - 12 * k - 11 : t - 12 * k + 1].sum() for k in range(1, 61)]
        )
        self.assertAlmostEqual(vmed.iloc[t], expected)
        self.assertTrue(pd.isna(vmed.iloc[730]))
        self.assertFalse(pd.isna(vmed.iloc[731]))

    def test_volatility_excludes_current_return(self):
        rng = np.random.default_rng(2)
        close = pd.Series(100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, 900))))
        s12 = module.scaled_volatility(close)
        t = 800
        rets = np.log(close.iloc[t - 720 : t].to_numpy() / close.iloc[t - 721 : t - 1].to_numpy())
        self.assertAlmostEqual(s12.iloc[t], np.std(rets, ddof=1) * math.sqrt(12))
        self.assertTrue(pd.isna(s12.iloc[720]))
        self.assertFalse(pd.isna(s12.iloc[721]))

    def test_entry_fires_only_on_low_volume_selloff_bar(self):
        _, out = run(make_1h())
        self.assertEqual(entries(out)[entries(out) == 1].index.tolist(), [SIGNAL_BAR])
        self.assertAlmostEqual(out.loc[SIGNAL_BAR, "pre_drop_close"], 100.0)

    def test_no_entry_when_drop_volume_is_not_below_median(self):
        frame = make_1h()
        frame.loc[SIGNAL_BAR - 11 : SIGNAL_BAR, "volume"] = 1.0  # V12 == Vmed, not strictly below
        _, out = run(frame)
        self.assertEqual(int(entries(out).sum()), 0)

    def test_signal_columns_are_binary(self):
        _, out = run(make_1h(stay_down=True))
        for column in ("enter_long", "exit_long"):
            if column in out:
                self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_produces_no_signal(self):
        frame = make_1h()
        frame["volume"] = 0.0
        _, out = run(frame)
        self.assertEqual(int(entries(out).sum()), 0)
        self.assertEqual(int(out.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

        frame = make_1h()
        frame.loc[SIGNAL_BAR, "volume"] = 0.0
        _, out = run(frame)
        self.assertEqual(entries(out).iloc[SIGNAL_BAR], 0)

    def test_undefined_startup_values_produce_no_signal(self):
        # Same selloff placed inside the warm-up: inputs undefined, no entry.
        frame = make_1h(n=1000)
        frame["close"] = np.where(np.arange(1000) % 2 == 0, 100.0, 100.2)
        frame.loc[300, "close"] = 100.0
        frame.loc[301:311, "close"] = 100.0
        frame.loc[312, "close"] = 97.0
        frame.loc[301:312, "volume"] = 0.5
        _, out = run(frame)
        self.assertEqual(int(entries(out).iloc[: Strategy.startup_candle_count].sum()), 0)
        undefined = out[["r12", "s12", "v12", "vmed"]].isna().any(axis=1)
        self.assertTrue(undefined.iloc[312])
        self.assertEqual(int(entries(out)[undefined].sum()), 0)

    def test_signal_unchanged_when_future_candles_are_appended(self):
        full = make_1h(1000)
        n = 905
        _, short = run(full.iloc[:n].copy())
        _, long = run(full.copy())
        columns = ["r12", "pre_drop_close", "s12", "v12", "vmed"]
        pd.testing.assert_frame_equal(
            short.loc[: n - 1, columns], long.loc[: n - 1, columns], check_dtype=False
        )
        pd.testing.assert_series_equal(
            entries(short).iloc[:n], entries(long).iloc[:n], check_dtype=False, check_names=False
        )
        self.assertEqual(int(entries(short).sum()), 1)

    def _exit_setup(self, frame):
        strategy, out = run(frame)
        strategy.dp.analyzed = out
        trade = FakeTrade(out.loc[SIGNAL_BAR + 1, "date"].to_pydatetime())
        return strategy, out, trade

    def _exit(self, strategy, trade, current_time):
        return strategy.custom_exit("BTC/USDT", trade, current_time, 97.5, 0.0)

    def test_time_exit_after_12_bars(self):
        strategy, out, trade = self._exit_setup(make_1h(stay_down=True))
        open_date = trade.open_date_utc
        self.assertIsNone(self._exit(strategy, trade, open_date + 11 * BAR))
        self.assertEqual(self._exit(strategy, trade, open_date + 12 * BAR), "time_exit_12_bars")

    def test_retrace_exit_on_closed_bar_reaching_pre_drop_close(self):
        frame = make_1h(stay_down=True)
        u = SIGNAL_BAR + 5
        frame.loc[u, "close"] = 100.0
        strategy, out, trade = self._exit_setup(frame)
        u_date = out.loc[u, "date"].to_pydatetime()
        self.assertIsNone(self._exit(strategy, trade, u_date))
        self.assertEqual(self._exit(strategy, trade, u_date + BAR), "retrace_to_pre_drop_close")

    def test_no_exit_on_zero_volume_candle(self):
        frame = make_1h(stay_down=True)
        frame.loc[SIGNAL_BAR + 12, "volume"] = 0.0
        strategy, out, trade = self._exit_setup(frame)
        self.assertIsNone(self._exit(strategy, trade, trade.open_date_utc + 12 * BAR))
        self.assertEqual(
            self._exit(strategy, trade, trade.open_date_utc + 13 * BAR), "time_exit_12_bars"
        )


if __name__ == "__main__":
    unittest.main()
