"""H-039: Weekend US-daytime session long (Sat/Sun 13:00-21:00 UTC) in a daily uptrend.

Uptrend: last completed daily close > SMA(50) of daily closes (1d informative,
visible only after the day has closed). Entry signal on the closed 12:00 UTC bar
on Saturday/Sunday (fills at the 13:00 open). Exit signal on the closed 20:00 UTC
bar (fills at the 21:00 open); any later hour up to 11:00 also signals exit so no
position is held overnight. Native 3% stop. One entry per day by construction.
"""

from pandas import DataFrame
from freqtrade.strategy import IStrategy, informative


class WeekendDaytimeSession_H039_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    startup_candle_count = 1300

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["sma50"] = dataframe["close"].rolling(50).mean()
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["close_1d"].notna()
                & dataframe["sma50_1d"].notna()
                & (dataframe["close_1d"] > dataframe["sma50_1d"])
                & (dataframe["date"].dt.day_of_week >= 5)
                & (dataframe["date"].dt.hour == 12)
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "weekend_session")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        hour = dataframe["date"].dt.hour
        dataframe.loc[
            (
                ((hour >= 20) | (hour <= 11))
                & (dataframe["volume"] > 0)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "session_end")
        return dataframe
