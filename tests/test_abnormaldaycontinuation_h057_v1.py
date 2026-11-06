import importlib.util
import sys
import types
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

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
NAME = "AbnormalDayContinuation_H057_v1"


def load_module():
    path = ROOT / "user_data" / "strategies" / f"{NAME}.py"
    spec = importlib.util.spec_from_file_location(NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()
Strategy = getattr(MODULE, NAME)
START = pd.Timestamp("2024-01-01 00:00", tz="UTC")


def make_frame(closes, volume=1.0):
    closes = np.asarray(closes, dtype=float)
    opens = np.concatenate([[closes[0]], closes[:-1]])
    n = len(closes)
    return pd.DataFrame(
        {
            "date": pd.date_range(START, periods=n, freq="1h"),
            "open": opens,
            "high": np.maximum(opens, closes) * 1.001,
            "low": np.minimum(opens, closes) * 0.999,
            "close": closes,
            "volume": np.full(n, volume, dtype=float),
        }
    )


def noisy_series(n, seed=11):
    rng = np.random.default_rng(seed)
    return 100.0 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, n)))


QUIET_DAYS = 33


def quiet_then_jump():
    """33 days alternating +0.5% / -0.5% (flat inside the day, move on the 23:00 bar),
    then a day flat until 04:00 that jumps 2% on the 05:00 bar and keeps rising."""
    closes = []
    level = 100.0
    for k in range(QUIET_DAYS):
        target = level * (1.005 if k % 2 == 0 else 0.995)
        closes += [level] * 23 + [target]
        level = target
    day = [level] * 5 + [level * 1.02] + [level * (1.02 + 0.001 * h) for h in range(1, 19)]
    closes += day
    return closes


def run(frame):
    s = Strategy()
    out = s.populate_indicators(frame.copy(), {"pair": "BTC/USDT"})
    out = s.populate_entry_trend(out, {"pair": "BTC/USDT"})
    out = s.populate_exit_trend(out, {"pair": "BTC/USDT"})
    return out


def col(frame, name):
    return frame.get(name, pd.Series(np.nan, index=frame.index)).fillna(0)


class ContractTests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertAlmostEqual(Strategy.stoploss, -0.04)
        self.assertGreaterEqual(Strategy.startup_candle_count, 800)

    def test_signals_binary(self):
        out = run(make_frame(noisy_series(24 * 120)))
        self.assertGreater(int(col(out, "enter_long").sum()), 0)
        for c in ("enter_long", "exit_long"):
            if c in out:
                self.assertTrue(set(out[c].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_no_signal(self):
        out = run(make_frame(noisy_series(24 * 120), volume=0.0))
        self.assertEqual(int(col(out, "enter_long").sum()), 0)
        self.assertEqual(int(col(out, "exit_long").sum()), 0)

        frame = make_frame(quiet_then_jump())
        idx = QUIET_DAYS * 24 + 5
        frame.loc[idx, "volume"] = 0.0
        out = run(frame)
        self.assertEqual(col(out, "enter_long").iloc[idx], 0)

    def test_undefined_startup_no_signal(self):
        out = run(make_frame(noisy_series(24 * 120)))
        # 31 daily closes are needed: days 0..30 have no band.
        self.assertTrue(out["threshold"].iloc[: 31 * 24].isna().all())
        self.assertTrue(out["threshold"].iloc[31 * 24 :].notna().all())
        undefined = out["threshold"].isna() | out["d_move_prev"].isna()
        self.assertEqual(int(col(out, "enter_long")[undefined].sum()), 0)
        self.assertEqual(int(col(out, "enter_long").iloc[: 31 * 24].sum()), 0)

    def test_missing_day_makes_band_undefined(self):
        frame = make_frame(noisy_series(24 * 70))
        frame = frame.drop(index=range(10 * 24, 11 * 24)).reset_index(drop=True)
        out = run(frame)
        dates = pd.to_datetime(out["date"], utc=True)
        # Days whose 30-day window contains the missing day's return are undefined.
        # R(10) and R(11) are undefined; they sit in the windows of days 11..41.
        inside = (dates >= START + pd.Timedelta(days=11)) & (dates < START + pd.Timedelta(days=42))
        self.assertTrue(out.loc[inside, "threshold"].isna().all())
        self.assertTrue(out.loc[dates >= START + pd.Timedelta(days=42), "threshold"].notna().all())

    def test_no_lookahead(self):
        n, k = 24 * 50 + 7, 24 * 3 + 5
        full = make_frame(noisy_series(n + k))
        short = run(full.iloc[:n].copy())
        long = run(full.copy())
        cols = ["day_open", "d_move", "d_move_prev", "band_mean", "band_std", "threshold",
                "enter_long", "exit_long"]
        for c in ("enter_long", "exit_long"):
            short[c] = col(short, c)
            long[c] = col(long, c)
        pd.testing.assert_frame_equal(
            short[cols].reset_index(drop=True),
            long[cols].iloc[:n].reset_index(drop=True),
            check_dtype=False,
        )

    def test_rule_values_and_entry(self):
        closes = quiet_then_jump()
        out = run(make_frame(closes))
        base = QUIET_DAYS * 24
        daily = [closes[24 * k + 23] for k in range(QUIET_DAYS)]
        rets = [daily[k] / daily[k - 1] - 1 for k in range(QUIET_DAYS - 30, QUIET_DAYS)]
        self.assertAlmostEqual(out.loc[base + 5, "band_mean"], float(np.mean(rets)), places=12)
        self.assertAlmostEqual(out.loc[base + 5, "band_std"], float(np.std(rets, ddof=1)), places=12)
        self.assertAlmostEqual(out.loc[base, "day_open"], out.loc[base, "open"])
        self.assertAlmostEqual(out.loc[base + 5, "d_move"], 0.02, places=9)
        enter = col(out, "enter_long")
        self.assertEqual(enter.iloc[base + 5], 1)
        self.assertEqual(int(enter.sum()), 1)  # only the first crossing
        tag = out.loc[base + 5, "enter_tag"]
        self.assertEqual(MODULE.parse_tag(tag), out.loc[base, "day_open"])

    def test_entry_window_hours(self):
        closes = quiet_then_jump()
        base = QUIET_DAYS * 24
        level = closes[base - 1]
        # Jump on the 19:00 bar instead: outside 01..18.
        closes[base:] = [level] * 19 + [level * 1.02] * 5
        out = run(make_frame(closes))
        self.assertEqual(int(col(out, "enter_long").iloc[base:].sum()), 0)

    def test_one_entry_per_utc_day(self):
        s = Strategy()
        now = datetime(2024, 2, 16, 9, tzinfo=timezone.utc)
        tag = "abnormal_day|100.0"
        earlier = types.SimpleNamespace(open_date_utc=datetime(2024, 2, 16, 3, tzinfo=timezone.utc))
        yesterday = types.SimpleNamespace(open_date_utc=datetime(2024, 2, 15, 3, tzinfo=timezone.utc))
        fake = types.SimpleNamespace(get_trades_proxy=lambda **kw: [earlier])
        with mock.patch.object(MODULE, "Trade", fake):
            self.assertFalse(s.confirm_trade_entry("BTC/USDT", "market", 1, 1, "gtc", now, tag, "long"))
        fake = types.SimpleNamespace(get_trades_proxy=lambda **kw: [yesterday])
        with mock.patch.object(MODULE, "Trade", fake):
            self.assertTrue(s.confirm_trade_entry("BTC/USDT", "market", 1, 1, "gtc", now, tag, "long"))

    def _strategy_with_frame(self, frame):
        s = Strategy()
        s.timeframe = "1h"
        s.dp = types.SimpleNamespace(get_analyzed_dataframe=lambda pair, tf: (frame, None))
        return s

    def test_failure_and_time_exit(self):
        open_date = datetime(2024, 2, 16, 6, tzinfo=timezone.utc)
        dates = pd.date_range("2024-02-16 00:00", periods=48, freq="1h", tz="UTC")
        frame = pd.DataFrame({"date": dates, "close": 101.0, "volume": 1.0})
        trade = types.SimpleNamespace(open_date_utc=open_date, enter_tag="abnormal_day|100.0")
        s = self._strategy_with_frame(frame)
        # Above day open, before 24 bars: hold.
        self.assertIsNone(s.custom_exit("X", trade, datetime(2024, 2, 16, 10, tzinfo=timezone.utc), 1, 0))
        # 24 bars after fill: time exit.
        self.assertIsNone(s.custom_exit("X", trade, datetime(2024, 2, 17, 5, tzinfo=timezone.utc), 1, 0))
        self.assertEqual(
            s.custom_exit("X", trade, datetime(2024, 2, 17, 6, tzinfo=timezone.utc), 1, 0),
            "time_exit_24_bars",
        )
        # The 09:00 bar closes below the day open: failure exit at the 10:00 open.
        frame2 = frame.copy()
        frame2.loc[9, "close"] = 99.0
        s = self._strategy_with_frame(frame2)
        self.assertEqual(
            s.custom_exit("X", trade, datetime(2024, 2, 16, 10, tzinfo=timezone.utc), 1, 0),
            "failure_below_day_open",
        )
        # The failure level stays the signal day's open on the next UTC day.
        frame3 = frame.copy()
        frame3.loc[26, "close"] = 99.5
        s = self._strategy_with_frame(frame3)
        self.assertEqual(
            s.custom_exit("X", trade, datetime(2024, 2, 17, 3, tzinfo=timezone.utc), 1, 0),
            "failure_below_day_open",
        )
        # Zero-volume bar never triggers the failure exit.
        frame2.loc[9, "volume"] = 0.0
        s = self._strategy_with_frame(frame2)
        self.assertIsNone(s.custom_exit("X", trade, datetime(2024, 2, 16, 10, tzinfo=timezone.utc), 1, 0))
        # A bar before the entry fill does not count.
        frame4 = frame.copy()
        frame4.loc[3, "close"] = 99.0
        s = self._strategy_with_frame(frame4.iloc[:4])
        self.assertIsNone(s.custom_exit("X", trade, datetime(2024, 2, 16, 10, tzinfo=timezone.utc), 1, 0))


if __name__ == "__main__":
    unittest.main()
