import importlib.util
import math
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
for name in ("merge_informative_pair", "stoploss_from_absolute"):
    if not hasattr(sys.modules["freqtrade.strategy"], name):
        setattr(sys.modules["freqtrade.strategy"], name, lambda *a, **k: None)
persistence_module = types.ModuleType("freqtrade.persistence")


class _TradeStub:
    trades: list = []

    @classmethod
    def get_trades_proxy(cls, pair=None, **kwargs):
        return [trade for trade in cls.trades if pair is None or trade.pair == pair]


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
PATH = ROOT / "user_data" / "strategies" / "_archive" / "IntradayJumpContinuation_H059_v1.py"
spec = importlib.util.spec_from_file_location("IntradayJumpContinuation_H059_v1", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Strategy = module.IntradayJumpContinuation_H059_v1

MINUTES = {"15m": 15, "1h": 60, "1d": 1440}


def merge_informative_pair(dataframe, informative, timeframe, timeframe_inf, ffill=True, **kwargs):
    """Same semantics as freqtrade's helper: an informative candle is visible from the last base candle
    inside its period (i.e. once that period has closed)."""
    informative = informative.copy()
    shift = MINUTES[timeframe_inf] - MINUTES[timeframe]
    informative["date_merge"] = informative["date"] + pd.Timedelta(minutes=shift)
    informative.columns = [f"{column}_{timeframe_inf}" for column in informative.columns]
    merged = pd.merge(
        dataframe, informative, left_on="date",
        right_on=f"date_merge_{timeframe_inf}", how="left",
    )
    merged = merged.drop(columns=[f"date_merge_{timeframe_inf}"])
    if ffill:
        columns = [c for c in merged.columns if c.endswith(f"_{timeframe_inf}")]
        merged[columns] = merged[columns].ffill()
    return merged


# Use the faithful merge regardless of which stub module was registered first.
module.merge_informative_pair = merge_informative_pair
module.Trade = _TradeStub

START = pd.Timestamp("2026-01-01 00:00", tz="UTC")
BARS_PER_DAY = 96
DAYS = 40
JUMP_DAYS = range(33, DAYS)  # all after startup_candle_count (32 days)
JUMP_SLOT = 40  # 10:00 UTC
JUMP_SIZE = 0.015


def make_frame(drift=0.0001, jump_days=JUMP_DAYS, jump_slot=JUMP_SLOT, days=DAYS, seed=7):
    rng = np.random.default_rng(seed)
    n = days * BARS_PER_DAY
    returns = drift + rng.normal(0.0, 0.001, n)
    for day in jump_days:
        returns[day * BARS_PER_DAY + jump_slot] = JUMP_SIZE
    close = 100.0 * np.exp(np.cumsum(returns))
    open_ = np.concatenate([[100.0], close[:-1]])
    return pd.DataFrame(
        {
            "date": pd.date_range(START, periods=n, freq="15min"),
            "open": open_,
            "high": np.maximum(open_, close) * 1.001,
            "low": np.minimum(open_, close) * 0.999,
            "close": close,
            "volume": 1.0,
        }
    )


def run(frame):
    strategy = Strategy()
    out = strategy.populate_indicators(frame.copy(), {"pair": "BTC/USDT"})
    out = strategy.populate_entry_trend(out, {"pair": "BTC/USDT"})
    out = strategy.populate_exit_trend(out, {"pair": "BTC/USDT"})
    return out


def entries(out):
    return out.get("enter_long", pd.Series(0.0, index=out.index)).fillna(0)


class FakeDP:
    def __init__(self, frame):
        self.frame = frame

    def get_analyzed_dataframe(self, pair, timeframe):
        return self.frame, None


class FakeTrade:
    def __init__(self, open_date, enter_tag, pair="BTC/USDT"):
        self.open_date_utc = open_date
        self.enter_tag = enter_tag
        self.pair = pair


class ContractTests(unittest.TestCase):
    def test_class_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.03)
        self.assertGreaterEqual(Strategy.startup_candle_count, 3072)
        self.assertLessEqual(Strategy.startup_candle_count, 4500)
        for name in ("custom_stake_amount", "adjust_trade_position", "leverage"):
            self.assertFalse(hasattr(Strategy, name))

    def test_signals_are_binary_and_fire_on_planted_jumps(self):
        out = run(make_frame())
        values = set(out["enter_long"].dropna().unique().tolist())
        self.assertTrue(values.issubset({1}))
        if "exit_long" in out:
            self.assertTrue(set(out["exit_long"].dropna().unique().tolist()).issubset({1}))
        expected = [day * BARS_PER_DAY + JUMP_SLOT for day in JUMP_DAYS]
        self.assertEqual(list(out.index[entries(out) == 1]), expected)
        row = out.loc[expected[0]]
        self.assertEqual(module.parse_tag(row["enter_tag"]), float(row["low"]))

    def test_zero_volume_produces_no_signal(self):
        frame = make_frame()
        frame["volume"] = 0.0
        self.assertEqual(int(entries(run(frame)).sum()), 0)
        frame = make_frame()
        frame.loc[frame.index[33 * BARS_PER_DAY + JUMP_SLOT], "volume"] = 0.0
        out = run(frame)
        self.assertEqual(entries(out).iloc[33 * BARS_PER_DAY + JUMP_SLOT], 0)
        self.assertEqual(int(entries(out).sum()), len(JUMP_DAYS) - 1)

    def test_undefined_startup_values_produce_no_signal(self):
        # Jumps on every day, including the warm-up days where the daily mean is undefined.
        self.assertEqual(int(entries(run(make_frame())).iloc[: Strategy.startup_candle_count].sum()), 0)
        out = run(make_frame(jump_days=range(0, DAYS)))
        # The 30-day mean of completed daily closes first exists on day 30 (after day 29 closed).
        self.assertEqual(int(entries(out).iloc[: 30 * BARS_PER_DAY].sum()), 0)
        undefined = out["jump_stat"].isna() | out["dsma_1d"].isna() | out["close_1d"].isna()
        self.assertTrue(undefined.iloc[:98].all())
        self.assertEqual(int(entries(out)[undefined].sum()), 0)
        # After the 30-day mean is defined the planted jumps do fire.
        self.assertGreater(int(entries(out).sum()), 0)

    def test_signals_do_not_change_when_future_candles_are_appended(self):
        full = make_frame()
        n = 36 * BARS_PER_DAY + 50  # mid-day, after three planted jumps
        short = run(full.iloc[:n].copy())
        longer = run(full.copy())
        columns = ["log_ret", "bipower_sigma", "jump_stat", "close_1d", "dsma_1d", "enter_long", "enter_tag"]
        pd.testing.assert_frame_equal(
            short.loc[: n - 1, columns].reset_index(drop=True),
            longer.loc[: n - 1, columns].reset_index(drop=True),
            check_dtype=False,
        )
        self.assertGreater(int(entries(short).sum()), 0)


class RuleTests(unittest.TestCase):
    def test_bipower_sigma_excludes_current_bar(self):
        frame = make_frame()
        out = run(frame)
        t = 33 * BARS_PER_DAY + JUMP_SLOT
        r = np.log(frame["close"] / frame["close"].shift(1)).to_numpy()
        products = [abs(r[i]) * abs(r[i - 1]) for i in range(t - 96, t)]
        expected = math.sqrt(math.pi / 2.0 * float(np.mean(products)))
        self.assertAlmostEqual(out.loc[t, "bipower_sigma"], expected, places=12)
        self.assertAlmostEqual(out.loc[t, "jump_stat"], r[t] / expected, places=9)

    def test_daily_close_visible_only_after_day_closed(self):
        frame = make_frame()
        out = run(frame)
        day = 31
        last_bar = day * BARS_PER_DAY + 95  # 23:45 bar
        self.assertEqual(out.loc[last_bar, "close_1d"], frame.loc[last_bar, "close"])
        self.assertEqual(out.loc[last_bar - 1, "close_1d"], frame.loc[day * BARS_PER_DAY - 1, "close"])
        daily = frame.groupby(frame["date"].dt.floor("D"))["close"].last()
        self.assertAlmostEqual(out.loc[last_bar, "dsma_1d"], daily.iloc[day - 29: day + 1].mean(), places=9)

    def test_no_entry_after_1745(self):
        out = run(make_frame(jump_slot=72))  # 18:00 bar
        self.assertEqual(int(entries(out).sum()), 0)
        out = run(make_frame(jump_slot=71))  # 17:45 bar
        self.assertEqual(int(entries(out).sum()), len(JUMP_DAYS))

    def test_no_entry_when_daily_filter_off(self):
        out = run(make_frame(drift=-0.0002))
        self.assertEqual(int(entries(out).sum()), 0)

    def test_small_jump_below_min_return_does_not_fire(self):
        global JUMP_SIZE
        saved = JUMP_SIZE
        try:
            JUMP_SIZE = 0.0055
            out = run(make_frame())
        finally:
            JUMP_SIZE = saved
        self.assertEqual(int(entries(out).sum()), 0)

    def test_confirm_trade_entry_one_per_utc_day(self):
        strategy = Strategy()
        now = datetime(2026, 2, 5, 12, 0, tzinfo=timezone.utc)
        tag = "jump_low|100.0"
        _TradeStub.trades = []
        try:
            self.assertTrue(strategy.confirm_trade_entry("BTC/USDT", "market", 1, 1, "gtc", now, tag, "long"))
            _TradeStub.trades = [FakeTrade(now - timedelta(hours=3), tag)]
            self.assertFalse(strategy.confirm_trade_entry("BTC/USDT", "market", 1, 1, "gtc", now, tag, "long"))
            _TradeStub.trades = [FakeTrade(now - timedelta(days=1), tag)]
            self.assertTrue(strategy.confirm_trade_entry("BTC/USDT", "market", 1, 1, "gtc", now, tag, "long"))
            self.assertFalse(strategy.confirm_trade_entry("BTC/USDT", "market", 1, 1, "gtc", now, None, "long"))
        finally:
            _TradeStub.trades = []

    def test_custom_exit_close_below_jump_low_and_time_exit(self):
        dates = pd.date_range("2026-02-05 10:15", periods=60, freq="15min", tz="UTC")
        closes = [101.0] * 60
        frame = pd.DataFrame({"date": dates, "close": closes, "volume": 1.0})
        strategy = Strategy()
        strategy.dp = FakeDP(frame)
        trade = FakeTrade(dates[0].to_pydatetime(), "jump_low|100.0")
        # Entry bar not yet closed: no exit.
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, dates[0].to_pydatetime(), 101, 0))
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, dates[5].to_pydatetime(), 101, 0))
        # The entry bar itself closes below L: exit at the next open.
        frame.loc[0, "close"] = 99.0
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade, dates[1].to_pydatetime(), 99, 0), "close_below_jump_low"
        )
        # A zero-volume last bar never triggers the loss exit.
        frame.loc[0, "volume"] = 0.0
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, dates[1].to_pydatetime(), 99, 0))
        frame.loc[0, ["close", "volume"]] = [101.0, 1.0]
        # Time exit at 00:00 UTC of the next day (after the 23:45 bar closed).
        midnight = datetime(2026, 2, 6, 0, 0, tzinfo=timezone.utc)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, midnight - timedelta(minutes=15), 101, 0))
        self.assertEqual(strategy.custom_exit("BTC/USDT", trade, midnight, 101, 0), "time_exit_utc_day_close")


if __name__ == "__main__":
    unittest.main()
