"""H-043: Williams-style volatility breakout on 1h candles (long only).

For UTC day D: O = open of the 00:00 bar, R = range of the 24 bars of day D-1,
level = O + 0.6 * R. Entry at the close of a 01:00-18:00 bar when close > level,
R / O >= 0.02 and the prior day's close is above the SMA(50) of daily closes
(23:00-bar closes). One entry per day. Exit when a bar closes below O - 0.5 * R
or on the 23:00 bar (flat at midnight). Native stop-loss 5%.
"""

import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class HourlyWilliamsVolBreakout_H043_v1(IStrategy):
    """Day-anchored volatility breakout, flat at UTC midnight."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.05
    startup_candle_count = 1300

    trigger_multiple = 0.6
    exit_multiple = 0.5
    min_range_over_open = 0.02
    daily_sma_days = 50
    first_hour = 1
    last_hour = 18
    time_exit_hour = 23

    @property
    def protections(self):
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        date = pd.to_datetime(dataframe["date"])
        day = date.dt.floor("D")
        hour = date.dt.hour

        helper = pd.DataFrame(
            {
                "day": day,
                "high": dataframe["high"],
                "low": dataframe["low"],
                "open0": dataframe["open"].where(hour == 0),
                "close23": dataframe["close"].where(hour == 23),
            }
        )
        grouped = helper.groupby("day")
        daily = pd.DataFrame(
            {
                "high": grouped["high"].max(),
                "low": grouped["low"].min(),
                "n": grouped["high"].count(),
                "open0": grouped["open0"].max(),
                "close23": grouped["close23"].max(),
            }
        )
        full_index = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
        daily = daily.reindex(full_index)
        complete = daily["n"] == 24
        daily_range = (daily["high"] - daily["low"]).where(complete)
        close23 = daily["close23"].where(complete)
        sma = close23.rolling(self.daily_sma_days).mean()
        trend = (close23 > sma).astype(float).where(sma.notna() & close23.notna())

        # Prior-day values (completed days only), looked up by current day.
        prev_range = daily_range.shift(1)
        prev_trend = trend.shift(1)

        dataframe["day_open"] = day.map(daily["open0"]).astype(float).values
        dataframe["prev_range"] = day.map(prev_range).astype(float).values
        dataframe["prev_trend"] = day.map(prev_trend).astype(float).values
        dataframe["hour_utc"] = hour.values
        dataframe["day_utc"] = day
        dataframe["breakout_level"] = (
            dataframe["day_open"] + self.trigger_multiple * dataframe["prev_range"]
        )
        dataframe["stop_level"] = (
            dataframe["day_open"] - self.exit_multiple * dataframe["prev_range"]
        )
        dataframe["range_ratio"] = dataframe["prev_range"] / dataframe["day_open"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        defined = (
            dataframe["breakout_level"].notna()
            & dataframe["range_ratio"].notna()
            & dataframe["prev_trend"].notna()
        )
        cond = (
            defined
            & (dataframe["hour_utc"] >= self.first_hour)
            & (dataframe["hour_utc"] <= self.last_hour)
            & (dataframe["close"] > dataframe["breakout_level"])
            & (dataframe["range_ratio"] >= self.min_range_over_open)
            & (dataframe["prev_trend"] == 1.0)
            & (dataframe["volume"] > 0)
        )
        # Only the first qualifying bar of each UTC day may signal an entry.
        order = cond.astype(int).groupby(dataframe["day_utc"]).cumsum()
        first = cond & (order == 1)
        dataframe.loc[first, ["enter_long", "enter_tag"]] = (1, "williams_vol_breakout")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        stop_hit = dataframe["stop_level"].notna() & (
            dataframe["close"] < dataframe["stop_level"]
        )
        time_exit = dataframe["hour_utc"] == self.time_exit_hour
        dataframe.loc[
            (stop_hit & (dataframe["volume"] > 0)),
            ["exit_long", "exit_tag"],
        ] = (1, "below_open_minus_half_range")
        dataframe.loc[
            (time_exit & (dataframe["volume"] > 0) & ~stop_hit),
            ["exit_long", "exit_tag"],
        ] = (1, "midnight_flat")
        return dataframe
