import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

freqtrade = types.ModuleType("freqtrade")
strategy_module = types.ModuleType("freqtrade.strategy")
strategy_module.IStrategy = object
persistence = types.ModuleType("freqtrade.persistence")
persistence.Trade = type("Trade", (), {"get_trades_proxy": staticmethod(lambda **k: [])})
freqtrade.strategy = strategy_module
freqtrade.persistence = persistence
sys.modules.setdefault("freqtrade", freqtrade)
sys.modules.setdefault("freqtrade.strategy", strategy_module)
sys.modules.setdefault("freqtrade.persistence", persistence)
if not hasattr(sys.modules["freqtrade.persistence"], "Trade"):
    sys.modules["freqtrade.persistence"].Trade = persistence.Trade

talib = types.ModuleType("talib")
talib_abstract = types.ModuleType("talib.abstract")
talib_abstract.SMA = lambda dataframe, timeperiod: dataframe["close"].rolling(timeperiod).mean()
talib_abstract.RSI = lambda dataframe, timeperiod: pd.Series(50.0, index=dataframe.index)
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)


def _fake_atr(dataframe, timeperiod=14):
    """Wilder ATR stand-in (used only when the stubbed talib has none)."""
    prev_close = dataframe["close"].shift(1)
    true_range = pd.concat(
        [
            dataframe["high"] - dataframe["low"],
            (dataframe["high"] - prev_close).abs(),
            (dataframe["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1, skipna=False)
    atr = true_range.ewm(alpha=1.0 / timeperiod, adjust=False).mean()
    atr.iloc[:timeperiod] = np.nan
    return atr


if not hasattr(sys.modules["talib.abstract"], "ATR"):
    sys.modules["talib.abstract"].ATR = _fake_atr

ROOT = Path(__file__).parents[1]
NAME = "MondayAsiaOpenTrend_H142_v1"


def load():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load()
Strategy = getattr(MODULE, NAME)

SUNDAY = pd.Timestamp("2023-12-31 00:00", tz="UTC")  # Sunday; Monday 00:00 is bar 96
MONDAY0 = 96
MONDAY_2300 = 96 + 92
MONDAY_2330 = 96 + 94
MONDAY_2345 = 96 + 95
TUESDAY_0000 = 96 + 96


def dates(n, start=SUNDAY):
    return pd.date_range(start, periods=n, freq="15min")


def random_frame(n=1200, seed=5):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.004, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.004, n))
    volume = rng.lognormal(3, 0.8, n)
    return pd.DataFrame(
        {"date": dates(n), "open": open_, "high": high, "low": low, "close": close, "volume": volume}
    )


def crafted(n=300):
    """Flat 100 (high 100.5, low 99.5: ATR about 1.0, NATR about 1%). No breakouts."""
    return pd.DataFrame(
        {"date": dates(n), "open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0, "volume": 10.0}
    )


def breakout(frame, bar):
    frame.loc[bar, ["open", "high", "low", "close"]] = [100.0, 101.2, 100.0, 101.0]
    return frame


def uptrend(n=80):
    close = 100.0 * 1.006 ** np.arange(n)
    open_ = np.concatenate([[close[0]], close[:-1]])
    return pd.DataFrame(
        {
            "date": dates(n, pd.Timestamp("2024-01-01 00:00", tz="UTC")),
            "open": open_,
            "high": close * 1.002,
            "low": close * 0.998,
            "close": close,
            "volume": 10.0,
        }
    )


def run(frame):
    strategy = Strategy()
    out = strategy.populate_indicators(frame.copy(), {})
    return strategy.populate_exit_trend(strategy.populate_entry_trend(out, {}), {})


def entries(out):
    if "enter_long" not in out:
        return []
    return out.index[out["enter_long"].fillna(0) == 1].tolist()


def exits(out):
    if "exit_long" not in out:
        return []
    return out.index[out["exit_long"].fillna(0) == 1].tolist()


class FakeTrade:
    trades = []

    @staticmethod
    def get_trades_proxy(**kwargs):
        return list(FakeTrade.trades)


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


class MondayAsiaOpenTrendTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.01)
        self.assertGreaterEqual(Strategy.startup_candle_count, 400)
        self.assertFalse(hasattr(MODULE, "LAB_MARKET"))

    def test_signal_columns_are_binary(self):
        for frame in (random_frame(), uptrend(), breakout(crafted(), 108)):
            out = run(frame)
            for column in ("enter_long", "exit_long"):
                if column in out:
                    self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_breakout_on_monday_gives_entry(self):
        out = run(breakout(crafted(), 108))  # Monday 03:00
        self.assertEqual(entries(out), [108])
        self.assertEqual(out.loc[108, "hh32"], 100.5)
        self.assertGreaterEqual(out.loc[108, "natr"], 0.004)

    def test_first_monday_bar_uses_sunday_evening_range(self):
        frame = crafted()
        frame.loc[MONDAY0 - 5, "high"] = 100.9  # Sunday 22:45 inside the 8h lookback
        frame = breakout(frame, MONDAY0)
        frame.loc[MONDAY0, "close"] = 100.8  # not above 100.9
        self.assertEqual(entries(run(frame)), [])
        frame.loc[MONDAY0, "close"] = 101.0
        self.assertEqual(entries(run(frame)), [MONDAY0])

    def test_breakout_must_be_strictly_above_and_current_bar_excluded(self):
        frame = crafted()
        frame.loc[108, ["high", "close"]] = [100.5, 100.5]  # equal to HH32: no
        self.assertEqual(entries(run(frame)), [])
        frame.loc[108, "high"] = 100.6
        frame.loc[108, "close"] = 100.6
        self.assertEqual(entries(run(frame)), [108])
        out = Strategy().populate_indicators(breakout(crafted(), 108), {})
        self.assertEqual(out.loc[108, "hh32"], 100.5)  # own high 101.2 not included
        self.assertEqual(out.loc[109, "hh32"], 101.2)

    def test_hh32_window_is_32_bars(self):
        frame = crafted()
        frame.loc[100, "high"] = 105.0
        out = Strategy().populate_indicators(frame, {})
        self.assertEqual(out.loc[101, "hh32"], 105.0)
        self.assertEqual(out.loc[132, "hh32"], 105.0)  # bars 100..131
        self.assertEqual(out.loc[133, "hh32"], 100.5)  # bar 100 dropped

    def test_only_monday_window(self):
        # Sunday, Tuesday: no entries
        sunday = breakout(crafted(), 70)
        self.assertEqual(entries(run(sunday)), [])
        tuesday = breakout(crafted(), TUESDAY_0000 + 8)
        self.assertEqual(entries(run(tuesday)), [])
        # Monday 23:30 is the last signal bar; 23:45 and Tuesday 00:00 are not
        self.assertEqual(entries(run(breakout(crafted(), MONDAY_2330))), [MONDAY_2330])
        self.assertEqual(entries(run(breakout(crafted(), MONDAY_2345))), [])
        self.assertEqual(entries(run(breakout(crafted(), TUESDAY_0000))), [])
        # the bar open time (not the close time) decides the weekday: Monday 00:00 counts
        self.assertEqual(entries(run(breakout(crafted(), MONDAY0))), [MONDAY0])
        # Sunday 23:45 bar (open) is Sunday
        self.assertEqual(entries(run(breakout(crafted(), MONDAY0 - 1))), [])

    def test_natr_filter(self):
        # tight ranges: NATR about 0.2% < 0.4%
        frame = crafted()
        frame["high"] = 100.05
        frame["low"] = 99.95
        frame.loc[108, ["high", "close"]] = [100.3, 100.2]
        out = run(frame)
        self.assertLess(out.loc[108, "natr"], 0.004)
        self.assertEqual(entries(out), [])
        # inclusive boundary on the NATR column itself
        strategy = Strategy()
        out = strategy.populate_indicators(breakout(crafted(), 108), {})
        out.loc[108, "natr"] = 0.004
        self.assertEqual(entries(strategy.populate_entry_trend(out.copy(), {})), [108])
        out.loc[108, "natr"] = 0.00399
        self.assertEqual(entries(strategy.populate_entry_trend(out.copy(), {})), [])

    def test_natr_is_atr_over_close(self):
        out = Strategy().populate_indicators(breakout(crafted(), 108), {})
        self.assertAlmostEqual(out.loc[108, "natr"], out.loc[108, "atr14"] / 101.0)

    def test_zero_volume_gives_no_signal(self):
        frame = breakout(crafted(), 108)
        frame["volume"] = 0.0
        out = run(frame)
        self.assertEqual(entries(out), [])
        self.assertEqual(exits(out), [])
        frame = breakout(crafted(), 108)
        frame.loc[108, "volume"] = 0.0
        self.assertEqual(entries(run(frame)), [])
        frame = crafted()
        frame.loc[MONDAY_2345, "volume"] = 0.0
        self.assertEqual(exits(run(frame)), [])
        self.assertEqual(entries(run(random_frame().assign(volume=0.0))), [])
        self.assertEqual(exits(run(random_frame().assign(volume=0.0))), [])

    def test_undefined_startup_values_give_no_signal(self):
        out = run(uptrend())
        self.assertTrue(out["hh32"].iloc[:32].isna().all())
        self.assertEqual([i for i in entries(out) if i < 32], [])
        self.assertIn(32, entries(out))  # first row with a defined HH32 and ATR
        # NaN ATR/NATR at the breakout bar: no entry
        strategy = Strategy()
        out = strategy.populate_indicators(breakout(crafted(), 108), {})
        out.loc[108, "natr"] = np.nan
        self.assertEqual(entries(strategy.populate_entry_trend(out, {})), [])
        out = strategy.populate_indicators(breakout(crafted(), 108), {})
        out.loc[108, "hh32"] = np.nan
        self.assertEqual(entries(strategy.populate_entry_trend(out, {})), [])
        # first rows of any frame are undefined
        out = run(random_frame())
        self.assertEqual([i for i in entries(out) if i < 32], [])

    def test_missing_bar_in_lookback_gives_no_signal(self):
        frame = breakout(crafted(), 108).drop(index=100).reset_index(drop=True)
        out = run(frame)
        self.assertEqual(entries(out), [])
        self.assertTrue(out["hh32"].iloc[100:132].isna().all())
        # the gap leaves the lookback 32 bars later
        frame = breakout(crafted(), 140).drop(index=100).reset_index(drop=True)
        self.assertEqual(entries(run(frame)), [139])

    def test_exit_signal_on_monday_2345_bar(self):
        out = run(crafted())
        self.assertEqual(exits(out), [MONDAY_2345])
        self.assertEqual(exits(run(crafted(400))), [MONDAY_2345])  # only the Monday bar, not a later Monday yet

    def test_exit_signal_on_later_monday_only(self):
        out = run(crafted(900))
        self.assertEqual(exits(out), [MONDAY_2345, MONDAY_2345 + 672])

    def test_take_profit_exit(self):
        strategy = Strategy()
        opened = utc(2024, 1, 1, 2, 0)
        trade = SimpleNamespace(open_date_utc=opened)
        soon = opened + timedelta(hours=1)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, soon, 101.7, 0.0179))
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade, soon, 101.8, 0.018), "take_profit_1p8pct"
        )

    def test_time_exit_after_12_hours(self):
        strategy = Strategy()
        opened = utc(2024, 1, 1, 2, 0)
        trade = SimpleNamespace(open_date_utc=opened)
        self.assertIsNone(
            strategy.custom_exit("BTC/USDT", trade, opened + timedelta(hours=11, minutes=45), 100.0, 0.0)
        )
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade, opened + timedelta(hours=12), 100.0, -0.004),
            "time_exit_12h",
        )

    def test_never_held_past_tuesday_midnight(self):
        strategy = Strategy()
        opened = utc(2024, 1, 1, 20, 0)
        trade = SimpleNamespace(open_date_utc=opened)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, utc(2024, 1, 1, 23, 45), 100.0, 0.0))
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade, utc(2024, 1, 2, 0, 0), 100.0, 0.0), "monday_end"
        )

    def test_confirm_trade_entry_limits(self):
        original = MODULE.Trade
        MODULE.Trade = FakeTrade
        try:
            strategy = Strategy()
            now = utc(2024, 1, 1, 10, 0)  # fill at 10:00, signal bar opened 09:45

            def confirm():
                return strategy.confirm_trade_entry(
                    "BTC/USDT", "limit", 1.0, 100.0, "GTC", now, None, "long"
                )

            def trade(open_at, close_at):
                return SimpleNamespace(open_date_utc=open_at, close_date_utc=close_at)

            FakeTrade.trades = []
            self.assertTrue(confirm())
            # two earlier entries today: third allowed
            FakeTrade.trades = [
                trade(utc(2024, 1, 1, 1, 0), utc(2024, 1, 1, 2, 0)),
                trade(utc(2024, 1, 1, 3, 0), utc(2024, 1, 1, 4, 0)),
            ]
            self.assertTrue(confirm())
            # three earlier entries today: fourth refused
            FakeTrade.trades.append(trade(utc(2024, 1, 1, 5, 0), utc(2024, 1, 1, 6, 0)))
            self.assertFalse(confirm())
            # entries on another Monday do not count
            FakeTrade.trades = [trade(utc(2023, 12, 25, h, 0), utc(2023, 12, 25, h, 30)) for h in (1, 2, 3)]
            self.assertTrue(confirm())
            # previous trade exited on the signal bar or later: refused
            FakeTrade.trades = [trade(utc(2024, 1, 1, 8, 0), utc(2024, 1, 1, 9, 45))]
            self.assertFalse(confirm())
            FakeTrade.trades = [trade(utc(2024, 1, 1, 8, 0), utc(2024, 1, 1, 10, 0))]
            self.assertFalse(confirm())
            # exited on the bar before the signal bar: allowed
            FakeTrade.trades = [trade(utc(2024, 1, 1, 8, 0), utc(2024, 1, 1, 9, 30))]
            self.assertTrue(confirm())
        finally:
            MODULE.Trade = original
            FakeTrade.trades = []

    def test_signal_does_not_change_when_future_candles_are_appended(self):
        columns = ["hh32", "atr14", "natr", "in_window", "forced_exit_bar", "enter_long", "exit_long"]
        random = random_frame(1200)
        full = run(random)
        self.assertGreater(len(entries(full)), 0)
        self.assertGreater(len(exits(full)), 0)
        cases = [(random, 700), (random, 150), (random, 110), (crafted(300), 109), (crafted(300), 190)]
        for frame, n in cases:
            if frame is not random:
                frame = breakout(frame, 108)
            short = run(frame.iloc[:n])
            long = run(frame)
            for column in columns:
                a = (short[column] if column in short else pd.Series(np.nan, index=short.index)).reset_index(drop=True)
                b = (
                    long[column] if column in long else pd.Series(np.nan, index=long.index)
                ).iloc[:n].reset_index(drop=True)
                pd.testing.assert_series_equal(a, b, check_dtype=False, check_names=False)


if __name__ == "__main__":
    unittest.main()
