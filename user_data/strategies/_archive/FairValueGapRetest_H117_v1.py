"""H-117: 15m bullish fair-value-gap midpoint retest after a 2x-volume displacement bar.

All times UTC, closed 15m bars only; a signal at the close of bar t fills at the open of bar t+1 (price E).
Spot, long only, one position per pair (engine), no pyramiding.

Gap: for bars k-1, k, k+1 a bullish gap exists when low(k+1) > high(k-1). GL = high(k-1), GH = low(k+1),
CE = (GL + GH) / 2. Valid only when (GH-GL)/close(k+1) >= 0.003, close(k) > open(k) and
volume(k) >= 2.0 x mean(volume over bars k-20..k-1). Known at the close of bar k+1.
Tracking: at the close of bar t the tracked gap is the most recent valid gap with k+1 <= t-1 (no fallback
to an older gap). Active on bars t = k+2..k+33. A bar closing below GL kills the gap from that bar on.
The gap is consumed at the first bar with low(t) <= CE and close(t) > GL (one signal per gap).
Zero-volume bars take no part in the gap lifecycle (neither retest nor invalidation) and never signal.
Entry tag carries GL: "fvg|<GL>". Fill only if fewer than 4 trades were opened on the pair on that UTC day
(confirm_trade_entry).
Stop: d = max(1 - 0.998 x GL / E, 0.01) frozen at the fill, stop price E x (1 - d) (custom_stoploss); native
stoploss -0.10 is only an engine backstop.
Take-profit (custom_exit): price E x (1 + 2d). Time exit (custom_exit): 12 hours (48 bars) after the fill bar.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy

MIN_GAP_FRAC = 0.003
VOLUME_LOOKBACK = 20
VOLUME_MULTIPLE = 2.0
ACTIVE_BARS = 32
STOP_BUFFER = 0.998
MIN_STOP_DISTANCE = 0.01
TARGET_R = 2.0
TIME_EXIT_BARS = 48
MAX_ENTRIES_PER_DAY = 4
BAR = timedelta(minutes=15)
TAG_PREFIX = "fvg"


def utc_day(value) -> pd.Timestamp:
    """UTC calendar day of a timestamp (naive timestamps are taken as UTC)."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return ts.floor("D")


def parse_tag(tag) -> float | None:
    """Gap bottom GL recorded in an entry tag, or None for a tag this strategy did not write."""
    if not isinstance(tag, str):
        return None
    parts = tag.split("|")
    if len(parts) != 2 or parts[0] != TAG_PREFIX:
        return None
    try:
        value = float(parts[1])
    except ValueError:
        return None
    if not np.isfinite(value) or value <= 0:
        return None
    return value


def stop_distance(gap_bottom: float, fill_price: float) -> float:
    """Frozen stop distance d = max(1 - 0.998 x GL / E, 0.01)."""
    return max(1.0 - STOP_BUFFER * gap_bottom / fill_price, MIN_STOP_DISTANCE)


def fvg_indicators(dataframe: DataFrame) -> DataFrame:
    """Add fvg_valid, fvg_signal and fvg_gl. Every value at row t uses rows <= t only."""
    high = dataframe["high"].astype(float)
    low = dataframe["low"].astype(float)
    open_ = dataframe["open"].astype(float)
    close = dataframe["close"].astype(float)
    volume = dataframe["volume"].astype(float)

    # At row j = k+1: high(k-1) is high.shift(2); bar k is row j-1.
    gap_bottom = high.shift(2)
    # Mean of volume over bars k-20..k-1 = rows j-21..j-2 (bar k excluded).
    volume_mean = volume.rolling(VOLUME_LOOKBACK).mean().shift(2)
    valid = (
        (low > gap_bottom)
        & ((low - gap_bottom) / close >= MIN_GAP_FRAC)
        & (close.shift(1) > open_.shift(1))
        & (volume.shift(1) >= VOLUME_MULTIPLE * volume_mean)
    ).fillna(False)

    valid_arr = valid.to_numpy(dtype=bool)
    gl_arr = gap_bottom.to_numpy(dtype=float)
    low_arr = low.to_numpy(dtype=float)
    close_arr = close.to_numpy(dtype=float)
    vol_arr = volume.to_numpy(dtype=float)

    n = len(dataframe)
    signal = np.zeros(n, dtype=np.int64)
    signal_gl = np.full(n, np.nan)

    tracked = -1
    alive = False
    gl = ce = np.nan
    for t in range(n):
        # The tracked gap (known at an earlier close) is evaluated against bar t first.
        if tracked >= 0 and alive:
            if t - tracked > ACTIVE_BARS:
                alive = False
            elif vol_arr[t] > 0:
                if close_arr[t] < gl:
                    alive = False
                elif low_arr[t] <= ce and close_arr[t] > gl:
                    signal[t] = 1
                    signal_gl[t] = gl
                    alive = False
        # A valid gap completed by bar t becomes the tracked gap from bar t+1 on.
        if valid_arr[t]:
            tracked = t
            gl = gl_arr[t]
            ce = (gl + low_arr[t]) / 2.0
            alive = True

    dataframe["fvg_valid"] = valid_arr.astype(np.int64)
    dataframe["fvg_signal"] = signal
    dataframe["fvg_gl"] = signal_gl
    return dataframe


class FairValueGapRetest_H117_v1(IStrategy):
    """Buy the midpoint retest of a bullish fair value gap; 2R take-profit, 12h time exit."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.10
    use_custom_stoploss = True
    use_exit_signal = True
    startup_candle_count = 100

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return fvg_indicators(dataframe)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (
            (dataframe["fvg_signal"] == 1)
            & dataframe["fvg_gl"].notna()
            & (dataframe["fvg_gl"] > 0)
            & dataframe["close"].notna()
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = [
                f"{TAG_PREFIX}|{float(value)!r}" for value in dataframe.loc[cond, "fvg_gl"]
            ]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Take-profit and time exit depend on the open trade: see custom_exit.
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """At most 4 trades opened per pair per UTC day (by fill time), open or closed."""
        if parse_tag(entry_tag) is None:
            return False
        today = utc_day(current_time)
        opened_today = 0
        for trade in Trade.get_trades_proxy(pair=pair):
            if utc_day(trade.open_date_utc) == today:
                opened_today += 1
        return opened_today < MAX_ENTRIES_PER_DAY

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        """Fixed price stop E x (1 - d), expressed as a distance below the current rate."""
        gap_bottom = parse_tag(trade.enter_tag)
        if gap_bottom is None or not trade.open_rate or not current_rate or current_rate <= 0:
            return None
        fill_price = float(trade.open_rate)
        stop_price = fill_price * (1.0 - stop_distance(gap_bottom, fill_price))
        distance = 1.0 - stop_price / float(current_rate)
        return -max(distance, 1e-6)

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        gap_bottom = parse_tag(trade.enter_tag)
        if gap_bottom is None or not trade.open_rate:
            return None
        fill_price = float(trade.open_rate)
        d = stop_distance(gap_bottom, fill_price)
        if current_rate is not None and float(current_rate) >= fill_price * (1.0 + TARGET_R * d):
            return "take_profit_2r"
        # Fill at the open of bar e: sold at the open of bar e+48, i.e. 12 hours after that bar opened.
        fill_bar = pd.Timestamp(trade.open_date_utc).floor("15min")
        if pd.Timestamp(current_time) >= fill_bar + TIME_EXIT_BARS * BAR:
            return "time_exit_12h"
        return None
