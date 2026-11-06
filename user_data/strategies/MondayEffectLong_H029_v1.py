"""H-029: Monday-session long in a daily uptrend, flat at Tuesday 00:00 UTC.

Closed daily candles are built from the 1h data (UTC days). The signal is evaluated on the Sunday 23:00 bar, whose
close is Sunday's daily close: filter = Sunday close > SMA(50) of the last 50 daily closes including Sunday. Freqtrade
fills at the next open, the Monday 00:00 bar. The exit signal fires on the Monday 23:00 bar and fills at the Tuesday
00:00 open (24 hourly bars). Stop: fixed 3% intrabar. Long only, one position, no other filters.
"""

import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

TREND_SMA_DAYS = 50


class MondayEffectLong_H029_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    startup_candle_count = 1200

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        date = pd.to_datetime(dataframe["date"], utc=True)
        close = pd.Series(dataframe["close"].to_numpy(), index=pd.DatetimeIndex(date))
        daily_close = close.resample("1D").last()
        daily_sma = daily_close.rolling(TREND_SMA_DAYS).mean()
        day = date.dt.floor("D")
        dataframe["daily_close"] = daily_close.reindex(day).to_numpy()
        dataframe["daily_sma"] = daily_sma.reindex(day).to_numpy()
        dataframe["hour_utc"] = date.dt.hour.to_numpy()
        dataframe["weekday_utc"] = date.dt.day_of_week.to_numpy()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (
            (dataframe["weekday_utc"] == 6)
            & (dataframe["hour_utc"] == 23)
            & dataframe["daily_sma"].notna()
            & dataframe["daily_close"].notna()
            & (dataframe["daily_close"] > dataframe["daily_sma"])
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[cond, ["enter_long", "enter_tag"]] = (1, "monday_open")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (dataframe["weekday_utc"] == 0) & (dataframe["hour_utc"] == 23) & (dataframe["volume"] > 0)
        dataframe.loc[cond, ["exit_long", "exit_tag"]] = (1, "tuesday_flat")
        return dataframe
