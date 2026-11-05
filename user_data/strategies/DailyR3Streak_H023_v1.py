"""H-023: Daily R3 - three falling RSI(2) days ending below 10 in a 200-day uptrend.

Signals use closed daily (UTC) candles from the 1d informative frame, merged by
Freqtrade so a daily value is visible only after that day has closed. Orders
execute on the 1h chart at the next open. Spot long only.

Rules (daily closes, values include the just-closed day):
- RSI(2), Wilder smoothing (alpha 1/2, seeded with the simple average of the
  first 2 changes).
- Entry: close > SMA(200) AND RSI0 < RSI1 < RSI2 < RSI3 AND RSI3 < 60 AND RSI0 < 10.
- Exit: RSI0 > 70.
- No binding stop (stoploss -0.99 only satisfies the engine contract), no
  cooldown. Exposure is set by the lab, not here.
"""

import numpy as np
from pandas import DataFrame, Series
from freqtrade.strategy import IStrategy, informative


def wilder_rsi(close: Series, length: int) -> Series:
    values = close.to_numpy(dtype=float)
    out = np.full(len(values), np.nan)
    if len(values) <= length:
        return Series(out, index=close.index)
    change = np.diff(values)
    gain = np.where(change > 0, change, 0.0)
    loss = np.where(change < 0, -change, 0.0)
    avg_gain = gain[:length].mean()
    avg_loss = loss[:length].mean()
    for position in range(length, len(values)):
        if position > length:
            avg_gain = (avg_gain * (length - 1) + gain[position - 1]) / length
            avg_loss = (avg_loss * (length - 1) + loss[position - 1]) / length
        if avg_loss == 0:
            out[position] = 100.0 if avg_gain > 0 else 50.0
        else:
            out[position] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    return Series(out, index=close.index)


class DailyR3Streak_H023_v1(IStrategy):
    """Connors/Alvarez R3 on daily closes, executed on 1h."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.99
    startup_candle_count = 400

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["sma200"] = dataframe["close"].rolling(200).mean()
        dataframe["rsi2"] = wilder_rsi(dataframe["close"], 2)
        dataframe["rsi2_p1"] = dataframe["rsi2"].shift(1)
        dataframe["rsi2_p2"] = dataframe["rsi2"].shift(2)
        dataframe["rsi2_p3"] = dataframe["rsi2"].shift(3)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["close_1d"].notna()
                & dataframe["sma200_1d"].notna()
                & dataframe["rsi2_1d"].notna()
                & dataframe["rsi2_p1_1d"].notna()
                & dataframe["rsi2_p2_1d"].notna()
                & dataframe["rsi2_p3_1d"].notna()
                & (dataframe["close_1d"] > dataframe["sma200_1d"])
                & (dataframe["rsi2_1d"] < dataframe["rsi2_p1_1d"])
                & (dataframe["rsi2_p1_1d"] < dataframe["rsi2_p2_1d"])
                & (dataframe["rsi2_p2_1d"] < dataframe["rsi2_p3_1d"])
                & (dataframe["rsi2_p3_1d"] < 60)
                & (dataframe["rsi2_1d"] < 10)
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "daily_r3_streak")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["rsi2_1d"].notna()
                & (dataframe["rsi2_1d"] > 70)
                & (dataframe["volume"] > 0)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "daily_rsi2_above_70")
        return dataframe
