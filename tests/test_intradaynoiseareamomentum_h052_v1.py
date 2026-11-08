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
NAME = "IntradayNoiseAreaMomentum_H052_v1"


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


def quiet_then_breakout(quiet_days=15):
    """Quiet days oscillating around 100, then a trending-up day, then a falling day."""
    closes = []
    for _ in range(quiet_days):
        closes += [100.0 * (1 + 0.002 * (-1) ** h) for h in range(24)]
    closes += [100.0 * (1 + 0.01 * h) for h in range(24)]
    closes += [124.0 * (1 - 0.01 * h) for h in range(24)]
    return closes


def noisy_series(n, seed=7):
    rng = np.random.default_rng(seed)
    return 100.0 * np.exp(np.cumsum(rng.normal(0.0005, 0.01, n)))


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
        self.assertAlmostEqual(Strategy.stoploss, -0.03)
        self.assertGreaterEqual(Strategy.startup_candle_count, 360)

    def test_signals_binary(self):
        out = run(make_frame(noisy_series(24 * 40)))
        self.assertGreater(int(col(out, "enter_long").sum()), 0)
        self.assertGreater(int(col(out, "exit_long").sum()), 0)
        for c in ("enter_long", "exit_long"):
            self.assertTrue(set(out[c].dropna().unique().tolist()).issubset({1}))

    def test_zero_volume_no_signal(self):
        out = run(make_frame(noisy_series(24 * 40), volume=0.0))
        self.assertEqual(int(col(out, "enter_long").sum()), 0)
        self.assertEqual(int(col(out, "exit_long").sum()), 0)

        frame = make_frame(quiet_then_breakout())
        idx = 15 * 24 + 1
        frame.loc[idx, "volume"] = 0.0
        out = run(frame)
        self.assertEqual(col(out, "enter_long").iloc[idx], 0)

    def test_undefined_startup_no_signal(self):
        out = run(make_frame(noisy_series(24 * 40)))
        self.assertTrue(out["sigma"].iloc[: 14 * 24].isna().all())
        undefined = out["sigma"].isna() | out["vwap"].isna()
        self.assertEqual(int(col(out, "enter_long")[undefined].sum()), 0)
        self.assertEqual(int(col(out, "exit_long")[undefined].sum()), 0)
        self.assertEqual(int(col(out, "enter_long").iloc[: 14 * 24].sum()), 0)

    def test_missing_same_slot_day_makes_sigma_undefined(self):
        frame = make_frame(noisy_series(24 * 20))
        frame = frame.drop(index=5 * 24 + 10).reset_index(drop=True)
        out = run(frame)
        dates = pd.to_datetime(out["date"], utc=True)
        target = START + pd.Timedelta(days=15, hours=10)
        self.assertTrue(pd.isna(out.loc[dates == target, "sigma"]).all())

    def test_no_lookahead(self):
        n, k = 24 * 20 + 7, 24 * 3 + 5
        full = make_frame(noisy_series(n + k))
        short = run(full.iloc[:n].copy())
        long = run(full.copy())
        cols = ["day_open", "sigma", "upper_band", "vwap", "trail", "enter_long", "exit_long"]
        for c in ("enter_long", "exit_long"):
            short[c] = col(short, c)
            long[c] = col(long, c)
        pd.testing.assert_frame_equal(
            short[cols].reset_index(drop=True),
            long[cols].iloc[:n].reset_index(drop=True),
            check_dtype=False,
        )

    def test_rule_values_and_entry_window(self):
        out = run(make_frame(quiet_then_breakout()))
        base = 15 * 24
        self.assertAlmostEqual(out.loc[base, "day_open"], out.loc[base, "open"])
        moves = [
            abs(out.loc[base + 3 - 24 * k, "close"] / out.loc[base - 24 * k, "open"] - 1)
            for k in range(1, 15)
        ]
        self.assertAlmostEqual(out.loc[base + 3, "sigma"], float(np.mean(moves)), places=12)
        self.assertAlmostEqual(
            out.loc[base + 3, "upper_band"],
            out.loc[base, "open"] * (1 + float(np.mean(moves))),
            places=9,
        )
        tp = (out["high"] + out["low"] + out["close"]) / 3
        expected_vwap = tp.iloc[base : base + 4].mean()
        self.assertAlmostEqual(out.loc[base + 3, "vwap"], expected_vwap, places=9)
        enter = col(out, "enter_long")
        self.assertEqual(enter.iloc[base], 0)  # slot 0 never enters
        self.assertEqual(enter.iloc[base + 1], 1)
        self.assertEqual(int(enter.iloc[base + 20 : base + 24].sum()), 0)  # slots 20..23
        exit_ = col(out, "exit_long")
        self.assertGreater(int(exit_.iloc[base + 24 + 2 : base + 48].sum()), 0)

    def test_one_entry_per_utc_day(self):
        s = Strategy()
        now = datetime(2024, 1, 16, 9, tzinfo=timezone.utc)
        earlier = types.SimpleNamespace(open_date_utc=datetime(2024, 1, 16, 3, tzinfo=timezone.utc))
        yesterday = types.SimpleNamespace(open_date_utc=datetime(2024, 1, 15, 3, tzinfo=timezone.utc))
        fake = types.SimpleNamespace(get_trades_proxy=lambda **kw: [earlier])
        with mock.patch.object(MODULE, "Trade", fake):
            self.assertFalse(s.confirm_trade_entry("BTC/USDT", "market", 1, 1, "gtc", now, None, "long"))
        fake = types.SimpleNamespace(get_trades_proxy=lambda **kw: [yesterday])
        with mock.patch.object(MODULE, "Trade", fake):
            self.assertTrue(s.confirm_trade_entry("BTC/USDT", "market", 1, 1, "gtc", now, None, "long"))

    def test_time_exit_at_utc_midnight(self):
        s = Strategy()
        trade = types.SimpleNamespace(open_date_utc=datetime(2024, 1, 16, 5, tzinfo=timezone.utc))
        self.assertIsNone(
            s.custom_exit("X", trade, datetime(2024, 1, 16, 23, tzinfo=timezone.utc), 1, 0)
        )
        self.assertEqual(
            s.custom_exit("X", trade, datetime(2024, 1, 17, 0, tzinfo=timezone.utc), 1, 0),
            "time_exit_utc_midnight",
        )


if __name__ == "__main__":
    unittest.main()
