"""H-030: overnight (00-08 UTC) drop reversal in a daily uptrend, time exit at 16:00 UTC.

Signal on the 07:00 UTC bar close: d = close(07:00 bar) / open(00:00 bar of the same day) - 1 <= -1.5% and the
previous (closed) UTC day's close > SMA(100) of daily closes including that day. Freqtrade fills at the next open
(08:00 bar). The exit signal fires on the 15:00 bar and fills at the 16:00 open. Stop: fixed 3% intrabar.
"""

import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

TREND_SMA_DAYS = 100
DROP_THRESHOLD = -0.015
WINDOW_BARS = 7  # 00:00 open is 7 hours before the 07:00 bar's open


class OvernightDropReversal_H030_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    startup_candle_count = 2500

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        date = pd.to_datetime(dataframe["date"], utc=True)
        index = pd.DatetimeIndex(date)
        close = pd.Series(dataframe["close"].to_numpy(), index=index)
        open_ = pd.Series(dataframe["open"].to_numpy(), index=index)

        # Open of the 00:00 bar of the same day, looked up by timestamp (backwards only).
        day = date.dt.floor("D")
        day_open = open_.reindex(pd.DatetimeIndex(day)).to_numpy()
        dataframe["overnight_ret"] = dataframe["close"].to_numpy() / day_open - 1.0

        # Previous day's closed daily close and its SMA(100); the current day's value is never used.
        daily_close = close.resample("1D").last()
        daily_sma = daily_close.rolling(TREND_SMA_DAYS).mean()
        prev_day = pd.DatetimeIndex(day) - pd.Timedelta(days=1)
        dataframe["prev_daily_close"] = daily_close.reindex(prev_day).to_numpy()
        dataframe["prev_daily_sma"] = daily_sma.reindex(prev_day).to_numpy()
        dataframe["hour_utc"] = date.dt.hour.to_numpy()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (
            (dataframe["hour_utc"] == 7)
            & dataframe["overnight_ret"].notna()
            & dataframe["prev_daily_close"].notna()
            & dataframe["prev_daily_sma"].notna()
            & (dataframe["overnight_ret"] <= DROP_THRESHOLD)
            & (dataframe["prev_daily_close"] > dataframe["prev_daily_sma"])
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[cond, ["enter_long", "enter_tag"]] = (1, "overnight_drop")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (dataframe["hour_utc"] == 15) & (dataframe["volume"] > 0)
        dataframe.loc[cond, ["exit_long", "exit_tag"]] = (1, "time_exit_16")
        return dataframe
