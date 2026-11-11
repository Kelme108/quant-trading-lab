import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

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


def load_strategy(filename: str, class_name: str):
    path = ROOT / "user_data" / "strategies" / "_archive" / filename
    spec = importlib.util.spec_from_file_location(class_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


Strategy = load_strategy("DailyKeltnerBreakout_H107_v1.py", "DailyKeltnerBreakout_H107_v1")

JUMP_ROW = 24 * 20 + 10  # 10:00 UTC, first bar of the block 10:00-12:00
DROP_ROW = 24 * 21 + 3  # 03:00 UTC


def make_frame(rows: int = 700, jump: bool = True, drop: bool = False, noise: float = 0.2) -> pd.DataFrame:
    index = np.arange(rows)
    prices = 100.0 + 0.01 * index + noise * np.sin(index / 3.0)
    if jump:
        prices = prices + np.where(index >= JUMP_ROW, 5.0, 0.0)
    if drop:
        prices = prices - np.where(index >= DROP_ROW, 5.0, 0.0)
    opens = np.concatenate([[prices[0]], prices[:-1]])
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01 00:00", periods=rows, freq="h", tz="UTC"),
            "open": opens,
            "high": np.maximum(opens, prices) * 1.001,
            "low": np.minimum(opens, prices) * 0.999,
            "close": prices,
            "volume": 1.0,
        }
    )


def run_all(frame: pd.DataFrame) -> pd.DataFrame:
    strategy = Strategy()
    frame = strategy.populate_indicators(frame.copy(), {})
    frame = strategy.populate_entry_trend(frame, {})
    return strategy.populate_exit_trend(frame, {})


class DailyKeltnerBreakoutH107Tests(unittest.TestCase):
    def test_class_constants(self) -> None:
        self.assertEqual(Strategy.INTERFACE_VERSION, 3)
        self.assertEqual(Strategy.timeframe, "1h")
        self.assertFalse(Strategy.can_short)
        self.assertEqual(Strategy.minimal_roi, {"0": 100.0})
        self.assertEqual(Strategy.stoploss, -0.02)
        self.assertGreaterEqual(Strategy.startup_candle_count, 1000)

    def test_signal_columns_are_binary(self) -> None:
        frame = run_all(make_frame(drop=True))
        for column in ("enter_long", "exit_long"):
            self.assertIn(column, frame)
            self.assertTrue(set(frame[column].dropna().unique().tolist()).issubset({1}))

    def test_block_construction(self) -> None:
        frame = run_all(make_frame(rows=48))
        rows = np.flatnonzero(frame["kc_block"].to_numpy())
        self.assertEqual(rows.tolist(), list(range(1, 48, 2)))
        raw = make_frame(rows=48)
        row = 5
        self.assertEqual(frame.loc[row, "kc_block_close"], raw.loc[row, "close"])
        # The even-hour row has no block yet.
        self.assertTrue(pd.isna(frame.loc[4, "kc_ema20"]) or frame.loc[4, "kc_ema20"] == frame.loc[3, "kc_ema20"])
        # Forward-filled to the following even row.
        self.assertEqual(frame.loc[6, "kc_ema20"], frame.loc[5, "kc_ema20"])

    def test_missing_bar_skips_block(self) -> None:
        raw = make_frame(rows=48).drop(index=[4]).reset_index(drop=True)
        frame = run_all(raw)
        closing_dates = frame.loc[frame["kc_block"], "date"].dt.hour.tolist()
        self.assertEqual(len(closing_dates), 23)
        self.assertNotIn(pd.Timestamp("2024-01-01 05:00", tz="UTC"), frame.loc[frame["kc_block"], "date"].tolist())

    def test_ema_atr_values(self) -> None:
        raw = make_frame(rows=200)
        frame = run_all(raw)
        # Recompute by hand on the first blocks.
        blocks = []
        for i in range(1, 200, 2):
            blocks.append(
                (
                    raw.loc[i - 1, "open"],
                    max(raw.loc[i, "high"], raw.loc[i - 1, "high"]),
                    min(raw.loc[i, "low"], raw.loc[i - 1, "low"]),
                    raw.loc[i, "close"],
                )
            )
        closes = [b[3] for b in blocks]
        ema = closes[0]
        for c in closes[1:25]:
            ema = (2 / 21) * c + (1 - 2 / 21) * ema
        trs = [
            max(blocks[i][1] - blocks[i][2], abs(blocks[i][1] - closes[i - 1]), abs(blocks[i][2] - closes[i - 1]))
            for i in range(1, 25)
        ]
        atr = float(np.mean(trs[:20]))
        for tr in trs[20:24]:
            atr = (atr * 19 + tr) / 20
        row = 2 * 24 + 1  # block index 24
        self.assertAlmostEqual(frame.loc[row, "kc_ema20"], ema)
        self.assertAlmostEqual(frame.loc[row, "kc_atr20"], atr)
        self.assertAlmostEqual(frame.loc[row, "kc_upper"], ema + 1.5 * atr)
        self.assertTrue(pd.isna(frame.loc[2 * 19 + 1, "kc_atr20"]))

    def test_entry_on_fresh_cross_in_window(self) -> None:
        frame = run_all(make_frame())
        entries = frame.index[frame["enter_long"] == 1].tolist()
        self.assertIn(JUMP_ROW + 1, entries)
        for row in entries:
            self.assertTrue(frame.loc[row, "kc_block"])
            self.assertLessEqual(frame.loc[row, "date"].hour - 1, 16)
            self.assertGreater(frame.loc[row, "kc_block_close"], frame.loc[row, "kc_upper"])
            self.assertGreater(frame.loc[row, "kc_block_close"], frame.loc[row, "kc_sma100"])
            self.assertLessEqual(frame.loc[row, "kc_prev_block_close"], frame.loc[row, "kc_prev_upper"])
        # No entry on the even-hour row of the jump block.
        self.assertTrue(pd.isna(frame.loc[JUMP_ROW, "enter_long"]))

    def test_no_entry_for_block_opening_after_16(self) -> None:
        late_row = 24 * 20 + 18  # block 18:00-20:00 opens after the entry window
        raw = make_frame(jump=False)
        raw.loc[late_row:, ["open", "high", "low", "close"]] += 5.0
        frame = run_all(raw)
        self.assertTrue(pd.isna(frame.loc[late_row + 1, "enter_long"]))
        self.assertGreater(frame.loc[late_row + 1, "kc_block_close"], frame.loc[late_row + 1, "kc_upper"])

    def test_exit_below_ema20_and_session_exit(self) -> None:
        frame = run_all(make_frame(drop=True))
        drop_block_row = DROP_ROW + 1 if (DROP_ROW % 2 == 0) else DROP_ROW
        self.assertEqual(frame.loc[drop_block_row, "exit_long"], 1)
        self.assertEqual(frame.loc[drop_block_row, "exit_tag"], "below_ema20")
        # The close of the 22:00 bar always signals the session exit; no other bar of a calm uptrend does.
        calm = run_all(make_frame(jump=False, noise=0.0))
        exits = calm.index[calm["exit_long"] == 1]
        self.assertTrue(len(exits) > 0)
        self.assertTrue(all(calm.loc[i, "date"].hour == 22 for i in exits))
        self.assertTrue((calm.loc[calm["date"].dt.hour == 22, "exit_long"] == 1).all())

    def test_custom_exit_time_limit(self) -> None:
        strategy = Strategy()
        opened = datetime(2024, 1, 5, 10, tzinfo=timezone.utc)
        trade = SimpleNamespace(open_date_utc=opened)
        self.assertIsNone(strategy.custom_exit("BTC/USDT", trade, opened + timedelta(hours=11), 1.0, 0.01))
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade, opened + timedelta(hours=12), 1.0, 0.01), "time_exit_12h"
        )
        self.assertEqual(
            strategy.custom_exit("BTC/USDT", trade, opened + timedelta(hours=20), 1.0, -0.01), "time_exit_12h"
        )

    def test_zero_volume_creates_no_signal(self) -> None:
        raw = make_frame(drop=True)
        baseline = run_all(raw)
        self.assertGreater(int(baseline["enter_long"].fillna(0).sum()), 0)
        raw["volume"] = 0.0
        frame = run_all(raw)
        self.assertEqual(int(frame["enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame["exit_long"].fillna(0).sum()), 0)

    def test_zero_volume_on_single_signal_bar(self) -> None:
        raw = make_frame()
        raw.loc[JUMP_ROW + 1, "volume"] = 0.0
        frame = run_all(raw)
        self.assertTrue(pd.isna(frame.loc[JUMP_ROW + 1, "enter_long"]))

    def test_undefined_startup_values_create_no_signal(self) -> None:
        # Jump early, while ATR20/SMA100 are still undefined.
        raw = make_frame(rows=400, jump=False)
        raw.loc[2 * 30 :, ["open", "high", "low", "close"]] += 5.0
        frame = run_all(raw)
        sma_ready = frame["kc_sma100"].first_valid_index()
        self.assertEqual(sma_ready, 199)
        self.assertEqual(int(frame.loc[: sma_ready - 1, "enter_long"].fillna(0).sum()), 0)
        self.assertEqual(int(frame.iloc[: Strategy.startup_candle_count]["enter_long"].fillna(0).sum()), 0)

    def test_nan_prices_create_no_signal(self) -> None:
        raw = make_frame()
        raw.loc[JUMP_ROW + 1, "close"] = np.nan
        frame = run_all(raw)
        self.assertTrue(pd.isna(frame.loc[JUMP_ROW + 1, "enter_long"]))

    def test_future_candles_do_not_change_past_rows(self) -> None:
        full = make_frame(rows=900, drop=True)
        for n in (519, 520, 600):
            short = run_all(full.iloc[:n].copy())
            longer = run_all(full.copy())
            pd.testing.assert_frame_equal(
                short.reset_index(drop=True),
                longer.iloc[:n].reset_index(drop=True),
                check_dtype=False,
            )


if __name__ == "__main__":
    unittest.main()
