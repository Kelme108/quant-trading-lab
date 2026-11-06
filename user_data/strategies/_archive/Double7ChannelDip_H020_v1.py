"""H-020: Daily Double 7 - buy a 7-day closing low above the 200-day mean, sell a 7-day closing high.

Signals use closed daily (UTC) candles from the 1d informative frame, merged by
Freqtrade so a daily value is visible only after that day has closed. Orders
execute on the 1h chart at the next open. Spot long only.

Rules (daily closes, channels include the just-closed day):
- Entry: close > SMA(200) AND close <= lowest close of the last 7 days.
- Exit: close >= highest close of the last 7 days.
- No binding stop (stoploss -0.99 only satisfies the engine contract), no
  cooldown. Exposure is set by the lab, not here.
"""

from pandas import DataFrame
from freqtrade.strategy import IStrategy, informative


class Double7ChannelDip_H020_v1(IStrategy):
    """Connors-style Double 7 on daily closes, executed on 1h."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.99
    startup_candle_count = 400

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["sma200"] = dataframe["close"].rolling(200).mean()
        dataframe["low7"] = dataframe["close"].rolling(7).min()
        dataframe["high7"] = dataframe["close"].rolling(7).max()
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["close_1d"].notna()
                & dataframe["sma200_1d"].notna()
                & dataframe["low7_1d"].notna()
                & (dataframe["close_1d"] > dataframe["sma200_1d"])
                & (dataframe["close_1d"] <= dataframe["low7_1d"])
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "daily_low7_above_sma200")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["close_1d"].notna()
                & dataframe["high7_1d"].notna()
                & (dataframe["close_1d"] >= dataframe["high7_1d"])
                & (dataframe["volume"] > 0)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "daily_high7")
        return dataframe
