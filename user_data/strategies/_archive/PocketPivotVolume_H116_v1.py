"""H-116: hourly pocket pivot (up bar out-volumes every recent down bar, at the 10-bar mean), 4h uptrend.

All times UTC, closed 1h bars only; a signal at the close of bar t fills at the open of bar t+1.
Long only, spot, one position per pair (engine), no pyramiding.

Definitions:
- DOWN BAR: close(i) < close(i-1).
- VD(t) = highest volume among the down bars in t-10..t-1 (bar t excluded); no down bar -> no signal.
- SMA10(t) = mean of closes t-9..t.
Pocket pivot at t when all hold:
  (1) close(t) > close(t-1); (2) volume(t) > VD(t); (3) close(t) > SMA10(t); (4) low(t) <= 1.005 * SMA10(t).
Filter: the last COMPLETED 4h candle (UTC blocks 00,04,...,20, built from four closed 1h bars) closes above
the SMA(50) of the last 50 completed 4h closes (that candle included).
Risk: r = (close(t) - low(t)) / close(t); skip if r > 0.025; d = max(r, 0.01), frozen in the entry tag.
Exits (first to occur):
- stop at E * (1 - d) (custom_stoploss, intrabar); native -3% stoploss is only a backstop;
- take-profit at E * (1 + 2d) (custom_exit);
- time exit 12 hours after the fill (custom_exit).
At most 2 entries per pair per UTC day of the fill (confirm_trade_entry).
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy

DOWN_VOLUME_LOOKBACK = 10
SMA_FAST_BARS = 10
NEAR_SMA_TOLERANCE = 1.005
FILTER_SMA_BARS = 50
MAX_SIGNAL_BAR_RISK = 0.025
MIN_STOP_DISTANCE = 0.01
TARGET_R_MULTIPLE = 2.0
TIME_EXIT_HOURS = 12
MAX_ENTRIES_PER_UTC_DAY = 2
TAG_PREFIX = "ppv"


def utc_day(value) -> pd.Timestamp:
    """UTC calendar day of a timestamp (naive timestamps are taken as UTC)."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return ts.floor("D")


def parse_tag(tag) -> float | None:
    """Frozen stop distance d recorded in an entry tag, or None for a tag this strategy did not write."""
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


def pocket_pivot_indicators(dataframe: DataFrame) -> DataFrame:
    """Add the pivot columns. Backward-looking only; the volume reference excludes the current bar."""
    close = dataframe["close"].astype(float)
    volume = dataframe["volume"].astype(float)
    prev_close = close.shift(1)
    down = close < prev_close
    # Volume of down bars, -1 on the other bars (volumes are >= 0, so a result >= 0 means a down bar exists).
    down_volume = volume.where(down, -1.0)
    down_volume = down_volume.where(prev_close.notna())
    vd = down_volume.shift(1).rolling(DOWN_VOLUME_LOOKBACK).max()
    vd = vd.where(vd >= 0)
    sma_fast = close.rolling(SMA_FAST_BARS).mean()
    risk = (close - dataframe["low"].astype(float)) / close
    dataframe["down_vol_max"] = vd
    dataframe["sma_fast"] = sma_fast
    dataframe["signal_risk"] = risk
    dataframe["stop_dist"] = risk.clip(lower=MIN_STOP_DISTANCE)
    return dataframe


def completed_4h_filter(dataframe: DataFrame) -> DataFrame:
    """Close and SMA(50) of the last COMPLETED 4h candle, built from closed 1h bars.

    A 4h block (UTC 00,04,..,20) is complete once its 4th hourly bar (hour % 4 == 3) has closed, i.e. at the
    close of that bar. Before that, the previous block is the last completed one.
    """
    dates = pd.to_datetime(dataframe["date"], utc=True)
    block = dates.dt.floor("4h")
    last_in_block = (dates.dt.hour % 4) == 3
    close = dataframe["close"].astype(float)
    block_close = close.groupby(block).last()
    block_complete = last_in_block.groupby(block).last()
    calendar = pd.date_range(block_close.index.min(), block_close.index.max(), freq="4h")
    block_close = block_close.where(block_complete.reindex(block_close.index).astype(bool)).reindex(calendar)
    block_sma = block_close.rolling(FILTER_SMA_BARS).mean()
    available = block.where(last_in_block, block - pd.Timedelta(hours=4))
    keys = pd.DatetimeIndex(available)
    dataframe["close_4h"] = block_close.reindex(keys).to_numpy(dtype=float)
    dataframe["sma50_4h"] = block_sma.reindex(keys).to_numpy(dtype=float)
    return dataframe


class PocketPivotVolume_H116_v1(IStrategy):
    """Buy an hourly pocket pivot near the 10-bar mean in a 4h uptrend; 2R target, stop, 12h time exit."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03  # engine backstop; the binding stop is custom_stoploss (d <= 0.025)
    use_custom_stoploss = True
    use_exit_signal = True
    startup_candle_count = 250

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = pocket_pivot_indicators(dataframe)
        dataframe = completed_4h_filter(dataframe)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        sma_fast = dataframe["sma_fast"]
        vd = dataframe["down_vol_max"]
        risk = dataframe["signal_risk"]
        cond = (
            close.notna()
            & sma_fast.notna()
            & vd.notna()
            & risk.notna()
            & dataframe["close_4h"].notna()
            & dataframe["sma50_4h"].notna()
            & dataframe["low"].notna()
            & (close > close.shift(1))
            & (dataframe["volume"] > vd)
            & (close > sma_fast)
            & (dataframe["low"] <= NEAR_SMA_TOLERANCE * sma_fast)
            & (risk <= MAX_SIGNAL_BAR_RISK)
            & (dataframe["close_4h"] > dataframe["sma50_4h"])
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = [
                f"{TAG_PREFIX}|{float(value)!r}" for value in dataframe.loc[cond, "stop_dist"]
            ]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Take-profit and time exit depend on the open trade: see custom_exit.
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """At most 2 entries per pair per UTC calendar day of the fill (closed trades included)."""
        if parse_tag(entry_tag) is None:
            return False
        today = utc_day(current_time)
        count = 0
        for trade in Trade.get_trades_proxy(pair=pair):
            if utc_day(trade.open_date_utc) == today:
                count += 1
        return count < MAX_ENTRIES_PER_UTC_DAY

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        """Fixed stop at E * (1 - d), d frozen at the signal bar; expressed relative to the current rate."""
        distance = parse_tag(trade.enter_tag)
        if distance is None or not current_rate or current_rate <= 0:
            return None
        stop_price = trade.open_rate * (1.0 - distance)
        relative = stop_price / current_rate - 1.0
        return min(relative, -1e-6)

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        distance = parse_tag(trade.enter_tag)
        if distance is not None and trade.open_rate and current_rate:
            if current_rate / trade.open_rate - 1.0 >= TARGET_R_MULTIPLE * distance:
                return "take_profit_2r"
        if current_time >= trade.open_date_utc + timedelta(hours=TIME_EXIT_HOURS):
            return "time_exit_12h"
        return None
