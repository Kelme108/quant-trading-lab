"""H-053: 1h low-volume 12-hour selloff reversal, exit on full retrace or after 12 bars.

Closed candles only; a signal at the close of bar t is filled at the open of bar t+1. Spot, long only,
one position per pair, whole allowed balance, no sizing hooks, no other filters.

Definitions (completed 1h bars):
- r12(t)  = close(t) / close(t-12) - 1
- s12(t)  = sample std (ddof=1) of the 720 log returns ln(close(i)/close(i-1)), i = t-720..t-1
            (current bar's return excluded), times sqrt(12)
- V12(t)  = sum of volume over bars t-11..t
- Vmed(t) = median of V12(t - 12*k), k = 1..60 (bars t-731..t-12; current window excluded)

Entry at the close of bar t when all hold: r12 <= -1.0 * s12; r12 <= -0.015; V12 < Vmed; all inputs defined;
volume > 0. One position per pair is enforced by the engine.

Exit (custom_exit, evaluated on closed bars, filled at the next open), first of:
- (a) close(u) >= P for some bar u >= t+1, where P = close(t-12) of the signal bar (fixed for the trade);
- (b) time exit at the close of bar t+12 (filled at the open of bar t+13).
Stop: fixed 5% below entry (native intrabar stoploss). No cooldown.
"""

import math
from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

RETURN_BARS = 12
VOL_LOOKBACK = 720
VOL_SCALE_BARS = 12
SIGMA_MULTIPLE = 1.0
MIN_DROP = -0.015
VOLUME_WINDOW = 12
VOLUME_REF_WINDOWS = 60
TIME_EXIT_BARS = 12
BAR_MINUTES = 60


def scaled_volatility(close: pd.Series, lookback: int = VOL_LOOKBACK, scale_bars: int = VOL_SCALE_BARS) -> pd.Series:
    """s12(t): ddof=1 std of the log returns of bars t-lookback..t-1, times sqrt(scale_bars)."""
    log_ret = np.log(close / close.shift(1))
    return log_ret.shift(1).rolling(lookback).std(ddof=1) * math.sqrt(scale_bars)


def volume_reference(volume: pd.Series, window: int = VOLUME_WINDOW, samples: int = VOLUME_REF_WINDOWS):
    """(V12, Vmed): rolling window sum and the median of the `samples` previous non-overlapping window sums."""
    v12 = volume.rolling(window).sum()
    lagged = pd.concat([v12.shift(window * k) for k in range(1, samples + 1)], axis=1)
    vmed = lagged.median(axis=1, skipna=False)
    return v12, vmed


class VolumeConditionedReversal_H053_v1(IStrategy):
    """Buy a 1-sigma, >=1.5% 12-hour drop that happened on below-median volume."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.05
    use_exit_signal = True
    startup_candle_count = 800

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["pre_drop_close"] = dataframe["close"].shift(RETURN_BARS)
        dataframe["r12"] = dataframe["close"] / dataframe["pre_drop_close"] - 1.0
        dataframe["s12"] = scaled_volatility(dataframe["close"])
        v12, vmed = volume_reference(dataframe["volume"])
        dataframe["v12"] = v12
        dataframe["vmed"] = vmed
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        defined = (
            dataframe["r12"].notna()
            & dataframe["s12"].notna()
            & dataframe["v12"].notna()
            & dataframe["vmed"].notna()
            & dataframe["pre_drop_close"].notna()
        )
        dataframe.loc[
            (
                defined
                & (dataframe["r12"] <= -SIGMA_MULTIPLE * dataframe["s12"])
                & (dataframe["r12"] <= MIN_DROP)
                & (dataframe["v12"] < dataframe["vmed"])
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "low_volume_selloff_reversal")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Both exits depend on the open trade (fixed P, bars since the signal): see custom_exit.
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return None
        bar = timedelta(minutes=BAR_MINUTES)
        open_date = trade.open_date_utc

        # Signal bar t: the last bar that opened before the entry fill (entry fills at the open of t+1).
        before = dataframe.loc[dataframe["date"] < open_date]
        if before.empty:
            return None
        signal = before.iloc[-1]

        # Closed bars u >= t+1: opened at or after the entry and fully closed by current_time.
        after = dataframe.loc[(dataframe["date"] >= open_date) & (dataframe["date"] + bar <= current_time)]
        # Never exit on a candle with zero volume.
        if after.empty or not after["volume"].iloc[-1] > 0:
            return None
        after = after.loc[after["volume"] > 0]

        target = signal["pre_drop_close"]
        if target == target and bool(np.any(after["close"].to_numpy() >= float(target))):
            return "retrace_to_pre_drop_close"

        # Bar t+12 opens at open_date + 11 bars; its close is open_date + 12 bars.
        if open_date + TIME_EXIT_BARS * bar <= current_time:
            return "time_exit_12_bars"
        return None
