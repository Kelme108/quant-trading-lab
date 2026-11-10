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

talib = types.ModuleType("talib")
talib_abstract = types.ModuleType("talib.abstract")
talib_abstract.SMA = lambda dataframe, timeperiod: dataframe["close"].rolling(timeperiod).mean()
talib_abstract.RSI = lambda dataframe, timeperiod: pd.Series(50.0, index=dataframe.index)
talib.abstract = talib_abstract
sys.modules.setdefault("talib", talib)
sys.modules.setdefault("talib.abstract", talib_abstract)


ROOT = Path(__file__).parents[2]
FILENAME = "SeasonalVolumeSurprise_H068_v1.py"
CLASS_NAME = "SeasonalVolumeSurprise_H068_v1"


def load_strategy():
    path = ROOT / "user_data" / "strategies" / "_archive" / FILENAME
    spec = importlib.util.spec_from_file_location(CLASS_NAME, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, CLASS_NAME)


Strategy = load_strategy()


def make_frame(n: int, seed: int = 7) -> pd.DataFrame:
    """Random-walk 1h candles with occasional strong high-volume up bars."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
    opens = 100.0 + np.cumsum(rng.normal(0, 0.3, n))
    rets = rng.normal(0, 0.004, n)
    volume = 1.0 + rng.uniform(0, 0.2, n)
    spikes = np.arange(n) % 37 == 5
    rets[spikes] = 0.01
    volume[spikes] = 5.0
    closes = opens * (1 + rets)
    highs = np.maximum(opens, closes) * 1.0005
    lows = np.minimum(opens, closes) * 0.9995
    return pd.DataFrame(
        {"date": dates, "open": opens, "high": highs, "low": lows, "close": closes, "volume": volume}
    )


def run(strategy, frame):
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    frame = strategy.populate_exit_trend(frame, {})
    return frame


class SeasonalVolumeSurpriseTests(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.02)
        self.assertGreaterEqual(Strategy.startup_candle_count, 480)
        self.assertEqual(Strategy.startup_candle_count, 500)

    def test_signals_binary_and_present(self) -> None:
        frame = run(Strategy(), make_frame(900))
        self.assertGreater(int(frame["enter_long"].fillna(0).sum()), 0)
        for column in ("enter_long", "exit_long"):
            if column in frame:
                self.assertTrue(set(frame[column].dropna().unique().tolist()).issubset({1}))

    def test_vexp_is_same_hour_mean_of_previous_20_days(self) -> None:
        frame = run(Strategy(), make_frame(700))
        t = 600
        expected = np.mean([frame.loc[t - 24 * k, "volume"] for k in range(1, 21)])
        self.assertAlmostEqual(frame.loc[t, "vexp"], expected)
        self.assertTrue(pd.isna(frame.loc[479, "vexp"]))
        self.assertFalse(pd.isna(frame.loc[480, "vexp"]))

    def test_zero_volume_no_signal(self) -> None:
        frame = make_frame(900)
        frame["volume"] = 0.0
        out = run(Strategy(), frame)
        self.assertEqual(int(out.get("enter_long", pd.Series(dtype=float)).fillna(0).sum()), 0)
        self.assertEqual(int(out.get("exit_long", pd.Series(dtype=float)).fillna(0).sum()), 0)

    def test_zero_volume_spike_bar_no_signal(self) -> None:
        frame = make_frame(900)
        base = run(Strategy(), frame)
        idx = base.index[base["enter_long"].fillna(0) == 1][0]
        frame.loc[idx, "volume"] = 0.0
        out = run(Strategy(), frame)
        self.assertNotEqual(out.loc[idx, "enter_long"], 1)

    def test_nan_startup_no_signal(self) -> None:
        strategy = Strategy()
        out = run(strategy, make_frame(900))
        self.assertEqual(int(out.iloc[:480]["enter_long"].fillna(0).sum()), 0)
        entries = out["enter_long"].fillna(0) == 1
        self.assertTrue(out.loc[entries, "vexp"].notna().all())

    def test_flat_bar_no_signal(self) -> None:
        frame = make_frame(900)
        base = run(Strategy(), frame)
        idx = base.index[base["enter_long"].fillna(0) == 1][0]
        frame.loc[idx, ["open", "high", "low", "close"]] = 100.0
        out = run(Strategy(), frame)
        self.assertNotEqual(out.loc[idx, "enter_long"], 1)

    def test_no_lookahead(self) -> None:
        n, k = 700, 150
        full = make_frame(n + k)
        short = run(Strategy(), full.iloc[:n].copy())
        changed = full.copy()
        changed.loc[n:, ["open", "high", "low", "close"]] *= 3.0
        changed.loc[n:, "volume"] = 999.0
        longer = run(Strategy(), changed)
        cols = ["vexp", "vol_surprise", "bar_ret", "close_loc", "enter_long", "enter_tag"]
        pd.testing.assert_frame_equal(
            short[cols].reset_index(drop=True),
            longer.iloc[:n][cols].reset_index(drop=True),
            check_dtype=False,
        )

    def test_custom_exit(self) -> None:
        strategy = Strategy()
        frame = run(strategy, make_frame(900))
        idx = frame.index[frame["enter_long"].fillna(0) == 1][0]
        low_sig = frame.loc[idx, "low"]
        open_date = frame.loc[idx + 1, "date"]

        class DP:
            def get_analyzed_dataframe(self, pair, timeframe):
                return frame, None

        strategy.dp = DP()
        trade = types.SimpleNamespace(enter_tag=frame.loc[idx, "enter_tag"], open_date_utc=open_date)
        bar = timedelta(hours=1)
        # Before the entry-fill bar closes: no exit.
        self.assertIsNone(strategy.custom_exit("X", trade, open_date, 0, 0))
        # Force entry-fill bar to close below LOWSIG.
        frame.loc[idx + 1, "close"] = low_sig * 0.99
        self.assertEqual(
            strategy.custom_exit("X", trade, open_date + bar, 0, 0), "close_below_signal_low"
        )
        frame.loc[idx + 1:, "close"] = low_sig * 2
        self.assertIsNone(strategy.custom_exit("X", trade, open_date + bar * 11, 0, 0))
        self.assertEqual(
            strategy.custom_exit("X", trade, open_date + bar * 12, 0, 0), "time_exit_12_bars"
        )


if __name__ == "__main__":
    unittest.main()
