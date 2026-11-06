"""H-040: Daily NR7 compression day, next-day upside breakout on 1h in a 50-day uptrend.

Daily (UTC) values come from the 1d informative frame, merged by Freqtrade so a
day is visible only after it has closed. On the day after an NR7 day D, the first
1h bar (open hour <= 19) whose close > high(D) is the entry signal, provided
close(D) > SMA50 of daily closes at D. Orders execute at the next 1h open.
Exit signals: 1h close < low(D) of the triggering NR7 day, or 48 bars after the
entry bar. Native stop is 3% below entry.
"""

import numpy as np
from pandas import DataFrame
from freqtrade.strategy import IStrategy, informative


class DailyNR7Breakout_H040_v1(IStrategy):
    """NR7 daily contraction followed by an upside breakout of that day's high."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    startup_candle_count = 1500

    NR_WINDOW = 7
    SMA_DAYS = 50
    LAST_ENTRY_OPEN_HOUR = 19
    TIME_EXIT_BARS = 48

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        day_range = dataframe["high"] - dataframe["low"]
        prior_min = day_range.shift(1)
        for lag in range(2, self.NR_WINDOW):
            prior_min = prior_min.combine(day_range.shift(lag), np.fmin)
        has_history = day_range.shift(self.NR_WINDOW - 1).notna()
        nr7 = (day_range < prior_min).astype(float)
        dataframe["nr7"] = nr7.where(has_history & day_range.notna() & prior_min.notna())
        dataframe["sma50"] = dataframe["close"].rolling(self.SMA_DAYS).mean()
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        required = ["nr7_1d", "sma50_1d", "close_1d", "high_1d", "low_1d"]
        defined = dataframe[required].notna().all(axis=1)
        hour = dataframe["date"].dt.hour
        raw = (
            defined
            & (dataframe["nr7_1d"] == 1.0)
            & (dataframe["close_1d"] > dataframe["sma50_1d"])
            & (dataframe["close"] > dataframe["high_1d"])
            & (hour <= self.LAST_ENTRY_OPEN_HOUR)
            & (dataframe["volume"] > 0)
        )
        day = dataframe["date"].dt.floor("D")
        first_of_day = raw & (raw.astype(int).groupby(day).cumsum() == 1)
        dataframe["nr7_entry_signal"] = first_of_day.astype(float)

        position = np.arange(len(dataframe), dtype=float)
        marks = DataFrame({"v": np.where(first_of_day.to_numpy(), position, np.nan)})
        dataframe["bars_since_signal"] = position - marks["v"].ffill().to_numpy()
        dataframe["entry_nr7_low"] = dataframe["low_1d"].where(first_of_day).ffill()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["nr7_entry_signal"] == 1.0) & (dataframe["volume"] > 0),
            ["enter_long", "enter_tag"],
        ] = (1, "nr7_breakout")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        valid = (
            dataframe["entry_nr7_low"].notna()
            & dataframe["bars_since_signal"].notna()
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[
            valid & (dataframe["close"] < dataframe["entry_nr7_low"]),
            ["exit_long", "exit_tag"],
        ] = (1, "close_below_nr7_low")
        dataframe.loc[
            valid & (dataframe["bars_since_signal"] == self.TIME_EXIT_BARS),
            ["exit_long", "exit_tag"],
        ] = (1, "time_exit_48")
        return dataframe
