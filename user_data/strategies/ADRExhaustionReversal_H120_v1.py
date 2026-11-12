"""H-120: 15m ADR exhaustion reversal, buy the first up-reversal bar after a full ADR drop from the day high.

All times UTC, closed 15m bars only; a signal at the close of bar t fills at the open of bar t+1.
Long only, spot, one position per pair (engine), no pyramiding.

Definitions (day d = the 96 bars whose open time falls in [00:00, 24:00)):
- ADR(d) = mean of (max high - min low) of the 14 completed UTC days before d (a day is completed when all
  96 of its bars are present); constant over day d; undefined (no signal) until 14 such days exist.
- DH(t), DL(t) = highest high / lowest low of day d from 00:00 up to and including t; O = open of the 00:00 bar.
- EXHAUSTION: DH-DL >= ADR(d); min(low[t-4..t]) == DL(t); DL(t) < O.
- TRIGGER: close(t) > high(t-1) and close(t) > open(t).
- ACTIVITY: ATR(14) (talib, Wilder) / close(t) >= 0.004.
- WINDOW: bar t opens 04:00..21:45 UTC.
- TARGET M = (DH+DL)/2 frozen at the signal bar; skipped when M < 1.01 * close(t).
- One entry per pair per UTC day (confirm_trade_entry, counting closed trades too).
The entry tag carries "adr|DH|DL|M".
Exits: stop SP = min(0.997*DL, 0.99*E), fixed, set at the fill (custom_stoploss; native -0.15 is only an outer
backstop); target when current_rate >= M (custom_exit); time exit 48 bars after the entry fill (custom_exit).
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy

BAR = timedelta(minutes=15)
BARS_PER_DAY = 96
ADR_DAYS = 14
LOW_RECENCY_BARS = 4
ATR_PERIOD = 14
ATR_OVER_CLOSE_MIN = 0.004
WINDOW_START_MINUTE = 4 * 60  # 04:00
WINDOW_END_MINUTE = 21 * 60 + 45  # 21:45
MIN_TARGET_DISTANCE = 0.01
STOP_BELOW_DAY_LOW = 0.997
MIN_STOP_DISTANCE = 0.01
TIME_EXIT_BARS = 48
TAG_PREFIX = "adr"


def utc_day(value) -> pd.Timestamp:
    """UTC calendar day of a timestamp (naive timestamps are taken as UTC)."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return ts.floor("D")


def parse_tag(tag):
    """Return (DH, DL, M) from an entry tag written by this strategy, or None."""
    if not isinstance(tag, str):
        return None
    parts = tag.split("|")
    if len(parts) != 4 or parts[0] != TAG_PREFIX:
        return None
    try:
        values = [float(part) for part in parts[1:]]
    except ValueError:
        return None
    if not all(np.isfinite(value) and value > 0 for value in values):
        return None
    return values[0], values[1], values[2]


def stop_price(day_low: float, fill: float) -> float:
    return min(STOP_BELOW_DAY_LOW * day_low, (1.0 - MIN_STOP_DISTANCE) * fill)


def adr_by_row(dates: pd.Series, high: pd.Series, low: pd.Series) -> np.ndarray:
    """ADR of the day of each row from the 14 completed days before it (backward-looking only)."""
    day = dates.dt.floor("D")
    day_high = high.groupby(day).max()
    day_low = low.groupby(day).min()
    bars = day.groupby(day).size()
    day_range = (day_high - day_low).where(bars == BARS_PER_DAY)
    calendar = pd.date_range(day_range.index.min(), day_range.index.max(), freq="D")
    day_range = day_range.reindex(calendar)
    # Mean of days d-14..d-1: the rolling window ends on d-1, so day d itself is excluded.
    adr = day_range.rolling(ADR_DAYS).mean().shift(1)
    return adr.reindex(pd.DatetimeIndex(day)).to_numpy(dtype=float)


class ADRExhaustionReversal_H120_v1(IStrategy):
    """Buy the first green reversal bar after price fell a full ADR from the day high."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.15
    use_custom_stoploss = True
    use_exit_signal = True
    # 14 completed days of 96 bars plus up to 95 bars of the current day (1440 per the proposal).
    startup_candle_count = 1440

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        if len(dataframe) == 0:
            return dataframe
        dates = pd.to_datetime(dataframe["date"], utc=True)
        day = dates.dt.floor("D")
        high = dataframe["high"].astype(float)
        low = dataframe["low"].astype(float)
        close = dataframe["close"].astype(float)

        dataframe["adr"] = adr_by_row(dates, high, low)
        dataframe["day_high"] = high.groupby(day).cummax()
        dataframe["day_low"] = low.groupby(day).cummin()
        day_open = dataframe["open"].astype(float).groupby(day).transform("first")
        # The day's open is only valid when the 00:00 bar is present.
        starts_at_midnight = dates.groupby(day).transform("min") == day
        dataframe["day_open"] = day_open.where(starts_at_midnight)
        dataframe["low_5bar_min"] = low.rolling(LOW_RECENCY_BARS + 1).min()
        atr = pd.Series(ta.ATR(dataframe, timeperiod=ATR_PERIOD), index=dataframe.index).astype(float)
        dataframe["atr_over_close"] = atr / close.where(close > 0)
        dataframe["minute_of_day"] = (dates.dt.hour * 60 + dates.dt.minute).to_numpy()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        if len(dataframe) == 0:
            return dataframe
        day_high = dataframe["day_high"]
        day_low = dataframe["day_low"]
        target = (day_high + day_low) / 2.0
        close = dataframe["close"]
        needed = dataframe[["adr", "day_high", "day_low", "day_open", "low_5bar_min", "atr_over_close"]]
        cond = (
            needed.notna().all(axis=1)
            & dataframe[["open", "high", "low", "close"]].shift(1).notna().all(axis=1)
            & (dataframe["adr"] > 0)
            & ((day_high - day_low) >= dataframe["adr"])
            & (dataframe["low_5bar_min"] == day_low)
            & (day_low < dataframe["day_open"])
            & (close > dataframe["high"].shift(1))
            & (close > dataframe["open"])
            & (dataframe["atr_over_close"] >= ATR_OVER_CLOSE_MIN)
            & (dataframe["minute_of_day"] >= WINDOW_START_MINUTE)
            & (dataframe["minute_of_day"] <= WINDOW_END_MINUTE)
            & (target >= (1.0 + MIN_TARGET_DISTANCE) * close)
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = [
                f"{TAG_PREFIX}|{float(h)!r}|{float(l)!r}|{float(m)!r}"
                for h, l, m in zip(day_high[cond], day_low[cond], target[cond])
            ]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Target and time exit depend on the open trade: see custom_exit.
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """At most one entry per pair per UTC day, counting trades that were already closed."""
        if parse_tag(entry_tag) is None:
            return False
        today = utc_day(current_time)
        for trade in Trade.get_trades_proxy(pair=pair):
            if utc_day(trade.open_date_utc) == today:
                return False
        return True

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        parsed = parse_tag(trade.enter_tag)
        if parsed is None or current_rate is None or current_rate <= 0:
            return None
        _dh, day_low, _m = parsed
        sp = stop_price(day_low, trade.open_rate)
        # Fixed absolute stop at SP, expressed relative to the current rate.
        return max(1.0 - sp / current_rate, 0.0001)

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        parsed = parse_tag(trade.enter_tag)
        if parsed is None:
            return None
        _dh, _dl, target = parsed
        if current_rate >= target:
            return "target_mid_range"
        if current_time >= trade.open_date_utc + TIME_EXIT_BARS * BAR:
            return "time_exit_48_bars"
        return None
