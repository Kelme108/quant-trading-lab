"""H-037: Hourly MACD cross-up gated by daily MACD uptrend.

Hourly MACD = EMA12 - EMA26 of 1h closes, signal = EMA9 of MACD (adjust=False).
Daily candles are built from the 1h data (UTC days); a daily value becomes
visible only on the first 1h bar after that day has closed (same visibility as
merge_informative_pair). DAILY UP = last closed daily MACD > daily signal.

Entry: hourly cross-up AND DAILY UP. Exit: hourly cross-down, or DAILY UP turns
false on the bar where a new daily value first appears. Native 5% stop.
"""

import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy


def _macd(close: pd.Series):
    fast = close.ewm(span=12, adjust=False).mean()
    slow = close.ewm(span=26, adjust=False).mean()
    macd = fast - slow
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal


class MultiTimeframeMACDTrend_H037_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.05
    startup_candle_count = 4200

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        macd, signal = _macd(dataframe["close"])
        dataframe["macd"] = macd
        dataframe["macd_signal"] = signal

        dates = dataframe["date"]
        day = dates.dt.floor("D")
        daily_close = dataframe["close"].groupby(day).last()
        d_macd, d_signal = _macd(daily_close)
        # A bar on day D sees the last daily value of the previous available
        # day (shift(1) on the daily series), i.e. only closed daily candles.
        prev_macd = pd.Series(d_macd.shift(1).to_numpy(), index=daily_close.index)
        prev_sig = pd.Series(d_signal.shift(1).to_numpy(), index=daily_close.index)
        dataframe["daily_macd"] = day.map(prev_macd).to_numpy(dtype=float)
        dataframe["daily_signal"] = day.map(prev_sig).to_numpy(dtype=float)
        valid = dataframe["daily_macd"].notna() & dataframe["daily_signal"].notna()
        up = (dataframe["daily_macd"] > dataframe["daily_signal"]) & valid
        dataframe["daily_up"] = up.astype(float).where(valid)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        macd = dataframe["macd"]
        sig = dataframe["macd_signal"]
        dataframe.loc[
            (
                macd.notna()
                & sig.notna()
                & macd.shift(1).notna()
                & sig.shift(1).notna()
                & dataframe["daily_up"].notna()
                & (macd > sig)
                & (macd.shift(1) <= sig.shift(1))
                & (dataframe["daily_up"] == 1.0)
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "macd_cross_up")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        macd = dataframe["macd"]
        sig = dataframe["macd_signal"]
        up = dataframe["daily_up"]
        base = (
            macd.notna()
            & sig.notna()
            & macd.shift(1).notna()
            & sig.shift(1).notna()
            & (dataframe["volume"] > 0)
        )
        cross_down = (macd < sig) & (macd.shift(1) >= sig.shift(1))
        daily_turn = up.notna() & up.shift(1).notna() & (up == 0.0) & (up.shift(1) == 1.0)
        dataframe.loc[base & cross_down, ["exit_long", "exit_tag"]] = (1, "macd_cross_down")
        dataframe.loc[
            base & daily_turn & ~cross_down, ["exit_long", "exit_tag"]
        ] = (1, "daily_down")
        return dataframe
