"""H-034: UTC-day opening-range breakout on 1h candles (long only).

Opening range = the 1h candle opening at 00:00 UTC. The day is armed when
(RH - RL) / RL >= 0.008. Entry on the first close above RH among candles
opening 01:00-11:00 UTC; at most one entry per UTC day. Exits at bar close:
close < midpoint, close >= RH + 1.5 * H, or the candle opening at 19:00 UTC.
The range values are carried forward causally within each UTC day.
"""

import numpy as np
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class SessionOpeningRangeBreakout_H034_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.04
    startup_candle_count = 48

    min_range_pct = 0.008
    target_multiple = 1.5

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dates = dataframe["date"]
        hour = dates.dt.hour
        day = dates.dt.normalize()
        is_open_range = hour == 0

        range_high = dataframe["high"].where(is_open_range)
        range_low = dataframe["low"].where(is_open_range)
        dataframe["or_high"] = range_high.groupby(day).ffill()
        dataframe["or_low"] = range_low.groupby(day).ffill()
        dataframe["or_height"] = dataframe["or_high"] - dataframe["or_low"]
        dataframe["or_mid"] = (dataframe["or_high"] + dataframe["or_low"]) / 2.0
        dataframe["or_armed"] = (
            (dataframe["or_low"] > 0)
            & (dataframe["or_height"] / dataframe["or_low"] >= self.min_range_pct)
        )
        dataframe["or_hour"] = hour
        dataframe["or_day"] = day
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        hour = dataframe["or_hour"]
        candidate = (
            dataframe["or_armed"]
            & (hour >= 1)
            & (hour <= 11)
            & (dataframe["close"] > dataframe["or_high"])
            & (dataframe["volume"] > 0)
        )
        # Only the first qualifying candle of each UTC day may enter.
        order = candidate.astype(int).groupby(dataframe["or_day"]).cumsum()
        first = candidate & (order == 1)
        dataframe.loc[first, ["enter_long", "enter_tag"]] = (1, "orb_break")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        hour = dataframe["or_hour"]
        valid = dataframe["or_mid"].notna() & (dataframe["volume"] > 0)
        below_mid = dataframe["close"] < dataframe["or_mid"]
        target = dataframe["close"] >= (
            dataframe["or_high"] + self.target_multiple * dataframe["or_height"]
        )
        time_exit = hour >= 19
        cond = valid & (hour >= 1) & (below_mid | target | time_exit)
        dataframe.loc[cond, ["exit_long", "exit_tag"]] = (1, "orb_exit")
        return dataframe
