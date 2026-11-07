"""H-070: negative realized skewness of the prior UTC day, buy 00:00 UTC, exit at 23:45 UTC.

All times UTC, closed 15m bars only, bars labelled by open time; a signal at a bar close
fills at the next bar open.

Daily statistic, computed at the close of the 23:45 bar of day d:
- r_i = ln(close_i / close_{i-1}) for the 96 bars of day d (00:00 .. 23:45); the first return
  uses the close of the 23:45 bar of day d-1 (97 closes in total).
- RV = sum r_i^2, RSK = sqrt(96) * sum r_i^3 / RV^1.5.
- If any of the 97 bars is missing (the 97 rows are not consecutive 15m bars) or RV = 0,
  there is no signal. Freqtrade fills gaps in the candle data with zero-volume candles, so a
  zero-volume candle inside the window is treated as a missing bar.
Entry: at the close of the 23:45 bar of day d, RSK <= -0.25 -> buy (fills at 00:00 of d+1).
Exit: at the close of the 23:30 bar -> sell (fills at the 23:45 open, 95 bars after entry).
Stop: native stoploss -0.99 (not meant to bind). No ROI, trailing, filter or cooldown.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

BARS_PER_DAY = 96
RSK_ENTRY_THRESHOLD = -0.25
BAR_MINUTES = 15
ENTRY_SIGNAL_HOUR, ENTRY_SIGNAL_MINUTE = 23, 45
EXIT_SIGNAL_HOUR, EXIT_SIGNAL_MINUTE = 23, 30


def realized_skewness(dataframe: DataFrame) -> DataFrame:
    """Add bar_hour, bar_minute, rv, rsk. Backward-looking only (current and prior 96 bars)."""
    dates = pd.to_datetime(dataframe["date"], utc=True)
    close = dataframe["close"].astype(float).to_numpy()
    volume = dataframe["volume"].astype(float).to_numpy()
    n = len(dataframe)

    # A bar is usable if its close is a finite positive number and it is a real (traded) bar.
    valid_bar = np.isfinite(close) & (close > 0) & np.isfinite(volume) & (volume > 0)

    # Return of bar i uses bar i-1; defined only when bar i-1 is exactly one bar earlier.
    step_ok = np.zeros(n, dtype=bool)
    if n > 1:
        delta = (dates - dates.shift(1)).to_numpy()
        step_ok[1:] = delta[1:] == np.timedelta64(BAR_MINUTES, "m")
    prev_valid = np.zeros(n, dtype=bool)
    prev_valid[1:] = valid_bar[:-1]
    ret_ok = step_ok & valid_bar & prev_valid

    returns = np.full(n, np.nan)
    if n > 1:
        with np.errstate(divide="ignore", invalid="ignore"):
            raw = np.log(close[1:] / close[:-1])
        returns[1:] = np.where(ret_ok[1:], raw, np.nan)

    rv = np.full(n, np.nan)
    sum_cubed = np.full(n, np.nan)
    if n >= BARS_PER_DAY:
        windows = np.lib.stride_tricks.sliding_window_view(returns, BARS_PER_DAY)
        # Exact per-window sums; NaN propagates when any of the 97 bars is missing.
        rv[BARS_PER_DAY - 1:] = np.sum(windows ** 2, axis=1)
        sum_cubed[BARS_PER_DAY - 1:] = np.sum(windows ** 3, axis=1)

    rsk = np.full(n, np.nan)
    positive = np.isfinite(rv) & (rv > 0)
    rsk[positive] = math.sqrt(BARS_PER_DAY) * sum_cubed[positive] / rv[positive] ** 1.5

    dataframe["bar_hour"] = dates.dt.hour.to_numpy()
    dataframe["bar_minute"] = dates.dt.minute.to_numpy()
    dataframe["rv"] = rv
    dataframe["rsk"] = rsk
    return dataframe


class RealizedSkewnessDay_H070_v1(IStrategy):
    """Hold for the next UTC day after a day with realized skewness <= -0.25."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.99
    startup_candle_count = 192

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return realized_skewness(dataframe)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (
            (dataframe["bar_hour"] == ENTRY_SIGNAL_HOUR)
            & (dataframe["bar_minute"] == ENTRY_SIGNAL_MINUTE)
            & dataframe["rsk"].notna()
            & (dataframe["rsk"] <= RSK_ENTRY_THRESHOLD)
            & (dataframe["volume"] > 0)
        ).fillna(False)
        dataframe.loc[cond, ["enter_long", "enter_tag"]] = (1, "neg_realized_skew")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (
            (dataframe["bar_hour"] == EXIT_SIGNAL_HOUR)
            & (dataframe["bar_minute"] == EXIT_SIGNAL_MINUTE)
            & (dataframe["volume"] > 0)
        ).fillna(False)
        dataframe.loc[cond, ["exit_long", "exit_tag"]] = (1, "time_exit_2330")
        return dataframe
