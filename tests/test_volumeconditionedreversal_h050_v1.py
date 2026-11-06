import importlib.util
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
NAME = "VolumeConditionedReversal_H050_v1"
BAR = timedelta(minutes=15)


def fake_merge_informative_pair(dataframe, informative, timeframe, timeframe_inf, ffill=True):
    """Mimics freqtrade: a daily candle becomes visible on the 15m candle that closes with it."""
    inf = informative.copy()
    inf["date_merge"] = inf["date"] + timedelta(days=1) - BAR
    inf.columns = [f"{c}_{timeframe_inf}" if c != "date_merge" else c for c in inf.columns]
    merged = dataframe.merge(inf, left_on="date", right_on="date_merge", how="left")
    merged = merged.drop(columns=["date_merge"])
    if ffill:
        cols = [c for c in merged.columns if c.endswith(f"_{timeframe_inf}")]
        merged[cols] = merged[cols].ffill()
    return merged


def load_module():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.merge_informative_pair = fake_merge_informative_pair
    return module


module = load_module()
Strategy = getattr(module, NAME)

START = pd.Timestamp("2024-03-01 00:00", tz="UTC")
SIGNAL_BAR = 1600


class FakeDP:
    def __init__(self, daily, analyzed=None):
        self.daily = daily
        self.analyzed = analyzed

    def get_pair_dataframe(self, pair, timeframe):
        return self.daily.copy()

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.analyzed, None


class FakeTrade:
    def __init__(self, open_date):
        self.open_date_utc = open_date


def make_15m(n=2000, selloff=True):
    close = np.full(n, 100.0) + 0.1 * np.sin(np.arange(n) / 5.0)
    volume = np.ones(n)
    s = SIGNAL_BAR
    if selloff and n > s:
        close[: s - 23] = 100.0
        close[s - 23 : s] = np.linspace(99.8, 95.0, 23)
        close[s:] = 95.5
        volume[s - 23 : s + 1] = 5.0
    open_ = np.concatenate([[close[0]], close[:-1]])
    if selloff and n > s:
        open_[s + 1 :] = close[s + 1 :]
    return pd.DataFrame(
        {
            "date": pd.date_range(START, periods=n, freq="15min"),
            "open": open_,
            "high": np.maximum(open_, close) * 1.001,
            "low": np.minimum(open_, close) * 0.999,
            "close": close,
            "volume": volume,
        }
    )


def make_daily(frame, days=160, rising=True):
    dates = pd.date_range(START - timedelta(days=days), START + timedelta(days=60), freq="1D")
    step = 1.0 if rising else -1.0
    closes = 200.0 + step * np.arange(len(dates))
    daily = pd.DataFrame({"date": dates, "open": closes, "high": closes, "low": closes,
                          "close": closes, "volume": 1.0})
    last_close_time = frame["date"].iloc[-1] + BAR
    return daily.loc[daily["date"] + timedelta(days=1) <= last_close_time].reset_index(drop=True)


def run(frame, daily=None):
    strategy = Strategy()
    strategy.dp = FakeDP(make_daily(frame) if daily is None else daily)
    out = strategy.populate_indicators(frame.copy(), {"pair": "BTC/USDT"})
    out = strategy.populate_entry_trend(out, {"pair": "BTC/USDT"})
    out = strategy.populate_exit_trend(out, {"pair": "BTC/USDT"})
    return strategy, out


def entries(out):
    return out.get("enter_long", pd.Series(dtype=float)).fillna(0)


class VolumeConditionedReversalH050Tests(unittest.TestCase):
    def test_contract_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.03)
        self.assertGreaterEqual(Strategy.startup_candle_count, 1368)
        self.assertGreaterEqual(Strategy.startup_candle_count, 101)
        self.assertEqual(
            Strategy().protections, [{"method": "CooldownPeriod", "stop_duration_candles": 24}]
        )
        for name in ("custom_stake_amount", "adjust_trade_position", "leverage"):
            self.assertFalse(hasattr(Strategy, name))

    def test_volume_reference_excludes_current_window(self):
        volume = pd.Series(np.arange(1, 1500, dtype=float))
        v6, vref = module.volume_reference(volume)
        t = 1450
        expected = np.mean([volume.iloc[t - 24 * k - 23 : t - 24 * k + 1].sum() for k in range(1, 57)])
        self.assertAlmostEqual(vref.iloc[t], expected)
        self.assertTrue(pd.isna(vref.iloc[1366]))
        self.assertFalse(pd.isna(vref.iloc[1367]))

    def test_entry_fires_only_on_the_green_high_volume_selloff_bar(self):
        _, out = run(make_15m())
        self.assertEqual(entries(out)[entries(out) == 1].index.tolist(), [SIGNAL_BAR])
        self.assertAlmostEqual(out.loc[SIGNAL_BAR, "pre_drop_close"], 100.0)

    def test_no_entry_without_daily_uptrend(self):
        frame = make_15m()
        daily = make_daily(frame, rising=False)
        _, out = run(frame, daily)
        self.assertEqual(int(entries(out).sum()), 0)

    def test_signal_columns_are_binary(self):
        _, out = run(make_15m())
        for column in ("enter_long", "exit_long"):
            if column in out:
                self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_produces_no_signal(self):
        frame = make_15m()
        frame["volume"] = 0.0
        _, out = run(frame)
        self.assertEqual(int(entries(out).sum()), 0)
        self.assertEqual(int(out.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

        frame = make_15m()
        frame.loc[SIGNAL_BAR, "volume"] = 0.0
        _, out = run(frame)
        self.assertEqual(entries(out).iloc[SIGNAL_BAR], 0)

    def test_undefined_startup_values_produce_no_signal(self):
        frame = make_15m()
        _, out = run(frame)
        self.assertEqual(int(entries(out).iloc[: Strategy.startup_candle_count].sum()), 0)
        undefined = out[["r24", "v6", "vref", "close_1d", "dsma_1d"]].isna().any(axis=1)
        self.assertEqual(int(entries(out)[undefined].sum()), 0)

        # Too few daily candles for the SMA(100): no entry anywhere.
        short_daily = make_daily(frame, days=60)
        _, out = run(frame, short_daily)
        self.assertTrue(out["dsma_1d"].isna().all())
        self.assertEqual(int(entries(out).sum()), 0)

    def test_signal_unchanged_when_future_candles_are_appended(self):
        full = make_15m(2000)
        n = 1700
        _, short = run(full.iloc[:n].copy())
        _, long = run(full.copy())
        columns = ["r24", "pre_drop_close", "v6", "vref", "close_1d", "dsma_1d"]
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
        return strategy.custom_exit("BTC/USDT", trade, current_time, 95.5, 0.0)

    def test_time_exit_after_48_bars(self):
        strategy, out, trade = self._exit_setup(make_15m())
        open_date = trade.open_date_utc
        self.assertIsNone(self._exit(strategy, trade, open_date + 47 * BAR))
        self.assertEqual(self._exit(strategy, trade, open_date + 48 * BAR), "time_exit_48_bars")

    def test_retrace_exit_on_closed_bar_reaching_pre_drop_close(self):
        frame = make_15m()
        u = SIGNAL_BAR + 5
        frame.loc[u, "close"] = 100.2
        strategy, out, trade = self._exit_setup(frame)
        u_date = out.loc[u, "date"].to_pydatetime()
        self.assertIsNone(self._exit(strategy, trade, u_date))
        self.assertEqual(self._exit(strategy, trade, u_date + BAR), "retrace_to_pre_drop_close")

    def test_no_exit_on_zero_volume_candle(self):
        frame = make_15m()
        frame.loc[SIGNAL_BAR + 48, "volume"] = 0.0
        strategy, out, trade = self._exit_setup(frame)
        self.assertIsNone(self._exit(strategy, trade, trade.open_date_utc + 48 * BAR))
        self.assertEqual(
            self._exit(strategy, trade, trade.open_date_utc + 49 * BAR), "time_exit_48_bars"
        )


if __name__ == "__main__":
    unittest.main()
