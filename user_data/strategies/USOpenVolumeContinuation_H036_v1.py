"""H-036: US-open volume-surge continuation (14:00 UTC 1h bar, 4-hour hold).

Signal bar: the 1h bar opening 14:00 UTC. Entry signal at its close when
volume >= 2.0 * mean volume of the 14:00 bars of the previous 20 calendar days,
close > open, close/open - 1 >= 0.7% and close > SMA(200). The order fills at
the next bar open (15:00). Exit signal on the 18:00 bar (fills at 19:00 open).
Stop-loss is a fixed 1.5% (native intrabar stop). Spot, long only.
"""

import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class USOpenVolumeContinuation_H036_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.015
    startup_candle_count = 500

    signal_hour = 14
    exit_hour = 18
    volume_multiple = 2.0
    reference_days = 20
    min_bar_return = 0.007
    trend_bars = 200

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["sma200"] = dataframe["close"].rolling(self.trend_bars).mean()
        dataframe["vref"] = float("nan")

        date = pd.to_datetime(dataframe["date"])
        mask = date.dt.hour == self.signal_hour
        if bool(mask.any()):
            days = date[mask].dt.normalize()
            daily = pd.Series(dataframe.loc[mask, "volume"].values, index=pd.DatetimeIndex(days))
            daily = daily[~daily.index.duplicated(keep="last")]
            calendar = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
            daily = daily.reindex(calendar)
            # previous 20 calendar days, current day excluded
            ref = daily.rolling(self.reference_days).mean().shift(1)
            dataframe.loc[mask, "vref"] = ref.reindex(pd.DatetimeIndex(days)).values
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        hour = pd.to_datetime(dataframe["date"]).dt.hour
        cond = (
            (hour == self.signal_hour)
            & dataframe["vref"].notna()
            & dataframe["sma200"].notna()
            & (dataframe["vref"] > 0)
            & (dataframe["volume"] >= self.volume_multiple * dataframe["vref"])
            & (dataframe["close"] > dataframe["open"])
            & (dataframe["close"] / dataframe["open"] - 1 >= self.min_bar_return)
            & (dataframe["close"] > dataframe["sma200"])
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[cond, ["enter_long", "enter_tag"]] = (1, "us_open_volume_surge")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        hour = pd.to_datetime(dataframe["date"]).dt.hour
        cond = (hour == self.exit_hour) & (dataframe["volume"] > 0)
        dataframe.loc[cond, ["exit_long", "exit_tag"]] = (1, "hold_4_bars")
        return dataframe
