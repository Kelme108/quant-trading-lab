"""H-092: US-open 30-minute opening-range breakout on 15m, midpoint stop, 2R target, flat at 20:00 UTC.

Closed 15m candles only, UTC clock. Signal at a bar close, fill at the next bar open.
Spot long only, one position per pair.

Opening range of a UTC day: 15m bars opening 13:30 and 13:45. RH = max high, RL = min low,
M = (RH + RL) / 2. Missing bar or zero volume in either -> day not armed.
Armed only if (RH - RL) / RL >= 0.02, Monday-Friday only.
Entry: first bar of the day whose open time is 14:00..17:45 and close > RH (armed days only).
Stop at M (fixed at entry, carried in the entry tag), target T = fill + 2 * (fill - M),
time exit at the 20:00 UTC open (signal on the bar opening 19:45 or later). Native stoploss -10%.
"""

from __future__ import annotations

import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

TAG_PREFIX = "orb92"
MIN_RANGE_FRACTION = 0.02
TARGET_R = 2.0
OR_START_MIN = 13 * 60 + 30
OR_END_MIN = 13 * 60 + 45
WINDOW_FIRST_MIN = 14 * 60
WINDOW_LAST_MIN = 17 * 60 + 45
EXIT_SIGNAL_MIN = 19 * 60 + 45


def make_tag(mid: float) -> str:
    return f"{TAG_PREFIX}|{mid!r}"


def parse_tag(tag):
    """Midpoint M recorded in an entry tag, or None for a tag this strategy did not write."""
    if not isinstance(tag, str):
        return None
    parts = tag.split("|")
    if len(parts) != 2 or parts[0] != TAG_PREFIX:
        return None
    try:
        value = float(parts[1])
    except ValueError:
        return None
    return value if value == value else None


class SessionOpeningRangeBreakout_H092_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.10
    trailing_stop = False
    use_custom_stoploss = True
    startup_candle_count = 96

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        date = pd.to_datetime(dataframe["date"], utc=True)
        minute = date.dt.hour * 60 + date.dt.minute
        day = date.dt.normalize()
        high = dataframe["high"].astype(float)
        low = dataframe["low"].astype(float)
        volume = dataframe["volume"].astype(float)

        or_bar = (minute == OR_START_MIN) | (minute == OR_END_MIN)
        ok_bar = or_bar & (volume > 0) & high.notna() & low.notna()
        # Both opening-range bars must be present with volume.
        count = ok_bar.astype(int).groupby(day).transform("sum")
        rh = high.where(ok_bar).groupby(day).transform("max")
        rl = low.where(ok_bar).groupby(day).transform("min")

        # Range values are only visible from the first bar after the range (14:00 onwards).
        visible = minute >= WINDOW_FIRST_MIN
        armed = (count == 2) & visible & (rl > 0) & ((rh - rl) / rl >= MIN_RANGE_FRACTION)
        armed = armed & (date.dt.day_of_week < 5)

        dataframe["or_high"] = rh.where(armed)
        dataframe["or_low"] = rl.where(armed)
        dataframe["or_mid"] = ((rh + rl) / 2.0).where(armed)
        dataframe["or_armed"] = armed.astype(int)
        dataframe["minute_of_day"] = minute
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        date = pd.to_datetime(dataframe["date"], utc=True)
        day = date.dt.normalize()
        minute = dataframe["minute_of_day"]
        raw = (
            (dataframe["or_armed"] == 1)
            & dataframe["or_high"].notna()
            & dataframe["or_mid"].notna()
            & dataframe["close"].notna()
            & (minute >= WINDOW_FIRST_MIN)
            & (minute <= WINDOW_LAST_MIN)
            & (dataframe["close"] > dataframe["or_high"])
        )
        first = raw & (raw.astype(int).groupby(day).cumsum() == 1)
        cond = (first & (dataframe["volume"] > 0)).fillna(False)
        if cond.any():
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = [
                make_tag(float(m)) for m in dataframe.loc[cond, "or_mid"]
            ]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        date = pd.to_datetime(dataframe["date"], utc=True)
        minute = date.dt.hour * 60 + date.dt.minute
        cond = ((minute >= EXIT_SIGNAL_MIN) & (dataframe["volume"] > 0)).fillna(False)
        if cond.any():
            dataframe.loc[cond, "exit_long"] = 1
        return dataframe

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        mid = parse_tag(trade.enter_tag)
        if mid is None or not current_rate or current_rate <= mid:
            return self.stoploss if mid is None else -0.0001
        return mid / current_rate - 1.0

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        mid = parse_tag(trade.enter_tag)
        open_date = trade.open_date_utc
        if mid is not None:
            if trade.open_rate <= mid or current_rate <= mid:
                return "stop_midpoint"
            target = trade.open_rate + TARGET_R * (trade.open_rate - mid)
            if current_rate >= target:
                return "take_profit_2R"
        cutoff = open_date.normalize() + pd.Timedelta(hours=20)
        if current_time >= cutoff:
            return "time_exit_2000"
        return None
