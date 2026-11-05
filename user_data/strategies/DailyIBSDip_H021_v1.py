"""H-021: Daily internal bar strength (IBS) dip buy inside a 200-day uptrend.

Signals use closed daily (UTC) candles from the 1d informative frame, merged by
Freqtrade so a daily value is visible only after that day has closed. Orders
execute on the 1h chart at the next open. Spot long only.

Rules (daily candles):
- IBS = (close - low) / (high - low); days with high == low have no IBS (skipped).
- Entry: IBS < 0.2 AND close > SMA(200).
- Exit: IBS >= 0.8 OR close < SMA(200); plus a fixed 12% stop (stoploss attribute).
- No cooldown. Exposure is set by the lab, not here.
"""

import numpy as np
from pandas import DataFrame
from freqtrade.strategy import IStrategy, informative


class DailyIBSDip_H021_v1(IStrategy):
    """Daily IBS dip buy above SMA200, executed on 1h."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.12
    startup_candle_count = 400

    @informative("1d")
    def populate_indicators_1d(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        day_range = dataframe["high"] - dataframe["low"]
        day_range = day_range.where(day_range > 0)
        dataframe["ibs"] = (dataframe["close"] - dataframe["low"]) / day_range
        dataframe["sma200"] = dataframe["close"].rolling(200).mean()
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["close_1d"].notna()
                & dataframe["sma200_1d"].notna()
                & dataframe["ibs_1d"].notna()
                & (dataframe["ibs_1d"] < 0.2)
                & (dataframe["close_1d"] > dataframe["sma200_1d"])
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "daily_ibs_dip")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ibs_exit = dataframe["ibs_1d"].notna() & (dataframe["ibs_1d"] >= 0.8)
        trend_exit = (
            dataframe["close_1d"].notna()
            & dataframe["sma200_1d"].notna()
            & dataframe["ibs_1d"].notna()  # zero-range days are skipped entirely
            & (dataframe["close_1d"] <dataframe["sma200_1d"])
        )
        dataframe.loc[
            ((ibs_exit | trend_exit) & (dataframe["volume"] > 0)),
            ["exit_long", "exit_tag"],
        ] = (1, "daily_ibs_exit")
        return dataframe
