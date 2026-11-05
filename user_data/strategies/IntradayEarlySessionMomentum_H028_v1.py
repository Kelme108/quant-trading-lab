"""H-028: early-UTC-day rally continuation (1h, long only).

For each UTC day, r = close of the 03:00 bar / open of the 00:00 bar - 1.
Entry signal on the 03:00 bar if r >= 1%; the order fills at the 04:00 open.
Exit signal on the 15:00 bar; the order fills at the 16:00 open.
Stop-loss is the engine's fixed 2.5% intrabar stop.
"""

import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class IntradayEarlySessionMomentum_H028_v1(IStrategy):
    """Clock-based intraday continuation."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.025
    startup_candle_count = 24

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Return since the 00:00 bar open, valid only on the 03:00 bar."""
        hour = dataframe["date"].dt.hour
        open_0 = dataframe["open"].shift(3)
        date_0 = dataframe["date"].shift(3)
        complete = (
            (hour == 3)
            & (date_0.dt.hour == 0)
            & ((dataframe["date"] - date_0) == pd.Timedelta(hours=3))
        )
        ret = dataframe["close"] / open_0 - 1.0
        dataframe["utc_hour"] = hour
        dataframe["early_return"] = ret.where(complete)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["early_return"] >= 0.01)
                & (dataframe["utc_hour"] == 3)
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "early_rally_1pct")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["utc_hour"] == 15)
                & dataframe["close"].notna()
                & (dataframe["volume"] > 0)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "time_exit_16utc")
        return dataframe
