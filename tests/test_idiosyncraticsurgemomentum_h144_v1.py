import importlib.util
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

talib = types.ModuleType("talib")
talib_abstract = types.ModuleType("talib.abstract")
talib_abstract.SMA = lambda dataframe, timeperiod: dataframe["close"].rolling(timeperiod).mean()
talib_abstract.RSI = lambda dataframe, timeperiod: pd.Series(50.0, index=dataframe.index)
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)


ROOT = Path(__file__).parents[1]


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Strategy = load_strategy(
    "IdiosyncraticSurgeMomentum_H144_v1.py", "IdiosyncraticSurgeMomentum_H144_v1"
)

START = pd.Timestamp("2024-01-01", tz="UTC")
SURGE = 250


class FakeDP:
    def __init__(self, btc: pd.DataFrame) -> None:
        self.btc = btc

    def get_pair_dataframe(self, pair: str, timeframe: str) -> pd.DataFrame:
        assert pair == "BTC/USDT"
        assert timeframe == "15m"
        return self.btc.copy()


class FakeTrade:
    def __init__(self, open_date_utc) -> None:
        self.open_date_utc = open_date_utc


def make_frame(closes, volumes=None, spread=0.0) -> pd.DataFrame:
    closes = np.asarray(closes, dtype=float)
    n = len(closes)
    return pd.DataFrame(
        {
            "date": pd.date_range(START, periods=n, freq="15min"),
            "open": closes,
            "high": closes * (1 + spread) + 0.0,
            "low": closes * (1 - spread),
            "close": closes,
            "volume": np.ones(n) if volumes is None else np.asarray(volumes, dtype=float),
        }
    )


def surge_frame(n=300) -> pd.DataFrame:
    closes = np.full(n, 100.0)
    closes[SURGE:] = 103.0
    volumes = np.ones(n)
    volumes[SURGE] = 5.0
    frame = make_frame(closes, volumes)
    frame.loc[SURGE, "low"] = 100.0  # close == high, CL = 1
    frame.loc[SURGE, "high"] = 103.0
    return frame


def flat_btc(n=300) -> pd.DataFrame:
    return make_frame(np.full(n, 20000.0))


def run(frame, btc, pair="ETH/USDT"):
    strategy = Strategy()
    strategy.dp = FakeDP(btc)
    metadata = {"pair": pair}
    out = strategy.populate_indicators(frame.copy(), metadata)
    out = strategy.populate_entry_trend(out, metadata)
    out = strategy.populate_exit_trend(out, metadata)
    return out


class IdiosyncraticSurgeContractTests(unittest.TestCase):
    def test_class_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "15m")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.0125)
        self.assertGreaterEqual(Strategy.startup_candle_count, 120)
        self.assertEqual(
            Strategy().protections,
            [{"method": "CooldownPeriod", "stop_duration_candles": 8}],
        )
        self.assertEqual(Strategy().informative_pairs(), [("BTC/USDT", "15m")])

    def test_surge_produces_a_single_signal(self) -> None:
        out = run(surge_frame(), flat_btc())
        self.assertEqual(out.index[out["enter_long"] == 1].tolist(), [SURGE])

    def test_signal_columns_are_binary(self) -> None:
        out = run(surge_frame(), flat_btc())
        for column in ("enter_long", "exit_long"):
            if column in out:
                self.assertTrue(set(out[column].dropna().unique().tolist()).issubset({1}))

    def test_btc_not_flat_blocks_signal(self) -> None:
        btc = np.full(300, 20000.0)
        btc[SURGE:] = 20000.0 * 1.02  # +2% in 4h: |r16 BTC| > 0.75%
        out = run(surge_frame(), make_frame(btc))
        self.assertNotIn("enter_long", out.columns)

    def test_residual_is_difference_to_btc(self) -> None:
        btc = np.full(300, 20000.0)
        btc[SURGE:] = 20000.0 * 1.005  # flat enough, residual 3% - 0.5% = 2.5%
        out = run(surge_frame(), make_frame(btc))
        self.assertAlmostEqual(out.loc[SURGE, "resid"], 0.03 - 0.005, places=9)
        self.assertEqual(out.index[out["enter_long"] == 1].tolist(), [SURGE])
        btc[SURGE:] = 20000.0 * 1.0099  # 3% - 0.99% = 2.01% but |btc| > 0.75%
        out = run(surge_frame(), make_frame(btc))
        self.assertNotIn("enter_long", out.columns)

    def test_small_residual_blocks_signal(self) -> None:
        frame = surge_frame()
        closes = np.full(300, 100.0)
        closes[SURGE:] = 101.9
        small = make_frame(closes, frame["volume"])
        small.loc[SURGE, "high"] = 101.9
        small.loc[SURGE, "low"] = 100.0
        out = run(small, flat_btc())
        self.assertNotIn("enter_long", out.columns)

    def test_low_volume_blocks_signal(self) -> None:
        frame = surge_frame()
        frame.loc[SURGE, "volume"] = 1.4
        out = run(frame, flat_btc())
        self.assertNotIn("enter_long", out.columns)

    def test_weak_close_location_blocks_signal(self) -> None:
        frame = surge_frame()
        frame.loc[SURGE, "high"] = 110.0  # CL = 3/10 = 0.3
        out = run(frame, flat_btc())
        self.assertNotIn("enter_long", out.columns)

    def test_high_equals_low_gives_no_signal(self) -> None:
        frame = surge_frame()
        frame.loc[SURGE, "high"] = 103.0
        frame.loc[SURGE, "low"] = 103.0
        out = run(frame, flat_btc())
        self.assertNotIn("enter_long", out.columns)

    def test_btc_pair_is_never_traded(self) -> None:
        out = run(surge_frame(), flat_btc(), pair="BTC/USDT")
        self.assertNotIn("enter_long", out.columns)

    def test_missing_btc_data_gives_no_signal(self) -> None:
        btc = flat_btc().drop(index=SURGE - 16).reset_index(drop=True)
        # remove the t-16 BTC candle (and keep the rest of the dates)
        btc = flat_btc()
        btc = btc[btc.index != SURGE - 16]
        out = run(surge_frame(), btc)
        self.assertTrue(np.isnan(out.loc[SURGE, "btc_r16"]))
        self.assertNotIn("enter_long", out.columns)

    def test_missing_volume_bar_gives_no_signal(self) -> None:
        frame = surge_frame()
        frame.loc[SURGE - 10, "volume"] = np.nan
        out = run(frame, flat_btc())
        self.assertNotIn("enter_long", out.columns)

    def test_zero_volume_produces_no_signal(self) -> None:
        frame = surge_frame()
        frame["volume"] = 0.0
        out = run(frame, flat_btc())
        self.assertNotIn("enter_long", out.columns)
        self.assertNotIn("exit_long", out.columns)
        frame = surge_frame()
        frame.loc[SURGE, "volume"] = 0.0
        out = run(frame, flat_btc())
        self.assertNotIn("enter_long", out.columns)

    def test_undefined_startup_values_produce_no_signal(self) -> None:
        # a surge inside the first 96 bars has no defined 24h volume mean
        n = 300
        closes = np.full(n, 100.0)
        closes[40:] = 103.0
        volumes = np.ones(n)
        volumes[40] = 5.0
        frame = make_frame(closes, volumes)
        frame.loc[40, "low"] = 100.0
        frame.loc[40, "high"] = 103.0
        out = run(frame, flat_btc())
        self.assertTrue(out.loc[:95, "vmean"].isna().all())
        if "enter_long" in out:
            self.assertEqual(int(out.iloc[:96]["enter_long"].fillna(0).sum()), 0)

    def test_signal_does_not_change_when_future_candles_are_appended(self) -> None:
        n, extra = 280, 60
        rng = np.random.default_rng(7)
        total = n + extra
        closes = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.004, total)))
        btc_closes = 20000.0 * np.exp(np.cumsum(rng.normal(0, 0.0008, total)))
        volumes = rng.uniform(0.5, 1.5, total)
        # force several surges, one in the appended part
        for pos in (150, 230, 300):
            closes[pos:] = closes[pos - 1] * 1.04 * np.ones(total - pos) * (
                closes[pos:] / closes[pos]
            )
            volumes[pos] = 8.0
        full = make_frame(closes, volumes, spread=0.0)
        for pos in (150, 230, 300):
            full.loc[pos, "high"] = full.loc[pos, "close"]
            full.loc[pos, "low"] = full.loc[pos, "close"] * 0.97
        btc_full = make_frame(btc_closes)

        short = run(full.iloc[:n], btc_full.iloc[:n])
        long = run(full, btc_full)
        compare = ["r16", "btc_r16", "resid", "vmean", "close_loc"]
        pd.testing.assert_frame_equal(
            short[compare].reset_index(drop=True),
            long.loc[: n - 1, compare].reset_index(drop=True),
            check_dtype=False,
        )
        short_sig = short["enter_long"].fillna(0) if "enter_long" in short else pd.Series(0, index=short.index)
        long_sig = long["enter_long"].fillna(0) if "enter_long" in long else pd.Series(0, index=long.index)
        self.assertGreater(int(long_sig.sum()), 0)
        self.assertEqual(short_sig.tolist(), long_sig.iloc[:n].tolist())

    def test_take_profit_and_time_exit(self) -> None:
        strategy = Strategy()
        opened = datetime(2024, 1, 1, tzinfo=timezone.utc)
        trade = FakeTrade(opened)
        soon = opened + timedelta(minutes=30)
        self.assertEqual(strategy.custom_exit("ETH/USDT", trade, soon, 1.0, 0.025), "take_profit_2_5pct")
        self.assertEqual(strategy.custom_exit("ETH/USDT", trade, soon, 1.0, 0.03), "take_profit_2_5pct")
        self.assertIsNone(strategy.custom_exit("ETH/USDT", trade, soon, 1.0, 0.0249))
        self.assertIsNone(strategy.custom_exit("ETH/USDT", trade, soon, 1.0, -0.01))
        almost = opened + timedelta(hours=11, minutes=45)
        self.assertIsNone(strategy.custom_exit("ETH/USDT", trade, almost, 1.0, -0.01))
        due = opened + timedelta(hours=12)
        self.assertEqual(strategy.custom_exit("ETH/USDT", trade, due, 1.0, -0.01), "time_exit_12h")
        self.assertEqual(strategy.custom_exit("ETH/USDT", trade, due, 1.0, 0.005), "time_exit_12h")


if __name__ == "__main__":
    unittest.main()
