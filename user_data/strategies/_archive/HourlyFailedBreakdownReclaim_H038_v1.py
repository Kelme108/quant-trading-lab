"""H-038: Turtle Soup on 1h - failed 20-day-low sweep reclaimed within 3 bars.

Closed 1h candles only; signal at close of bar t, order at next open. Long only.
- PL = lowest low of the 480 bars t-483..t-4. The bar that set PL (most recent
  if tied) must be at index <= t-96.
- SWEEP: min(low over t-3..t) < PL.
- RECLAIM: close(t) > PL and (close(t-1) <= PL or low(t) < PL).
- Entry on SWEEP and RECLAIM. Cooldown 24 candles after any exit.
- TARGET = highest high of the 24 bars ending at the signal bar, fixed at
  signal time. Exit at the first bar close >= TARGET, or at the close of the
  48th bar after the signal bar (time stop). Both are evaluated in custom_exit
  because the target is per-trade state. Stop: fixed 3% (native stoploss).
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
from pandas import DataFrame
from freqtrade.strategy import IStrategy


LOW_LOOKBACK = 480
LOW_WINDOW_LAG = 4
MIN_AGE = 96
SWEEP_BARS = 4
TARGET_LOOKBACK = 24
TIME_STOP_BARS = 48
COOLDOWN_BARS = 24


def _last_min_offset(window: np.ndarray) -> float:
    """Offset inside the window of the most recent lowest value."""
    n = len(window)
    return float(n - 1 - np.argmin(window[::-1]))


class HourlyFailedBreakdownReclaim_H038_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    startup_candle_count = 500
    process_only_new_candles = True
    use_custom_stoploss = False

    @property
    def protections(self):
        return [
            {
                "method": "CooldownPeriod",
                "stop_duration_candles": COOLDOWN_BARS,
            }
        ]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        low_shifted = dataframe["low"].shift(LOW_WINDOW_LAG)
        dataframe["pl"] = low_shifted.rolling(LOW_LOOKBACK).min()
        dataframe["pl_offset"] = low_shifted.rolling(LOW_LOOKBACK).apply(
            _last_min_offset, raw=True
        )
        # Window starts at bar t-483 (offset 0); age of the low bar = 483 - offset.
        dataframe["pl_age"] = (LOW_LOOKBACK + LOW_WINDOW_LAG - 1) - dataframe["pl_offset"]
        dataframe["sweep_low"] = dataframe["low"].rolling(SWEEP_BARS).min()
        dataframe["target"] = dataframe["high"].rolling(TARGET_LOOKBACK).max()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pl = dataframe["pl"]
        sweep = dataframe["sweep_low"] < pl
        reclaim = (dataframe["close"] > pl) & (
            (dataframe["close"].shift(1) <= pl) | (dataframe["low"] < pl)
        )
        dataframe.loc[
            (
                pl.notna()
                & dataframe["pl_age"].notna()
                & dataframe["sweep_low"].notna()
                & dataframe["target"].notna()
                & (dataframe["pl_age"] >= MIN_AGE)
                & sweep
                & reclaim
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "failed_breakdown_reclaim")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Exits depend on per-trade state (target fixed at the signal bar);
        # they are handled in custom_exit.
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        frame, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if frame is None or len(frame) == 0:
            return None
        frame = frame.reset_index(drop=True)
        step = timedelta(hours=1)
        signal_date = trade.open_date_utc - step
        match = frame.index[frame["date"] == signal_date]
        if len(match) == 0:
            return None
        signal_idx = int(match[0])
        target = frame.loc[signal_idx, "target"]
        last = frame.iloc[-1]
        if last["volume"] <= 0:
            return None
        if target == target and last["close"] >= target:
            return "target_24h_high"
        if len(frame) - 1 - signal_idx >= TIME_STOP_BARS:
            return "time_stop_48"
        return None
