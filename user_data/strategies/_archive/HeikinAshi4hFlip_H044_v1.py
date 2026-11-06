"""H-044: 4h Heikin Ashi fresh bullish flip, no lower wick, SMA(100) 4h filter.

Runs on 1h candles. Completed 4h bars are built from UTC blocks 00,04,...,20 and
are used only on the 1h candle that completes them (hour 03,07,11,15,19,23).
Orders fill at the next 1h open. Spot long only, 5% hard stop via stoploss.

Entry (at completion of 4h bar t): HA[t] bullish, HA[t-1] bullish, HA[t-2]
bearish, (haO-haL)/haO <= 0.0005 on bar t, real 4h close > SMA(100) of real 4h
closes. Exit: first completed 4h bar with a bearish HA candle (or the stop).
"""

import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class HeikinAshi4hFlip_H044_v1(IStrategy):
    """4h Heikin Ashi fresh flip with trend filter."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.05
    startup_candle_count = 1200

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        n = len(dataframe)
        cols = [
            "ha_open",
            "ha_close",
            "ha_low",
            "ha_bull",
            "ha_bear",
            "ha_bull_prev1",
            "ha_bull_prev2",
            "ha_bear_prev2",
            "sma_4h",
            "close_4h",
        ]
        for col in cols:
            dataframe[col] = np.nan
        dataframe["bar_complete"] = False
        if n == 0:
            return dataframe

        dates = pd.to_datetime(dataframe["date"], utc=True)
        block = dates.dt.floor("4h")
        grp = block.reset_index(drop=True)
        opens = dataframe["open"].reset_index(drop=True)
        highs = dataframe["high"].reset_index(drop=True)
        lows = dataframe["low"].reset_index(drop=True)
        closes = dataframe["close"].reset_index(drop=True)

        b_open = opens.groupby(grp).transform("first")
        b_high = highs.groupby(grp).cummax()
        b_low = lows.groupby(grp).cummin()
        pos_in_block = grp.groupby(grp).cumcount() + 1
        complete = ((dates.dt.hour % 4) == 3).reset_index(drop=True) & (pos_in_block == 4)
        complete = complete.to_numpy()

        idx = np.flatnonzero(complete)
        if len(idx) > 0:
            o = b_open.to_numpy()[idx]
            h = b_high.to_numpy()[idx]
            lo = b_low.to_numpy()[idx]
            c = closes.to_numpy()[idx]
            m = len(idx)
            ha_c = (o + h + lo + c) / 4.0
            ha_o = np.empty(m)
            ha_o[0] = (o[0] + c[0]) / 2.0
            for i in range(1, m):
                ha_o[i] = (ha_o[i - 1] + ha_c[i - 1]) / 2.0
            ha_l = np.minimum(lo, np.minimum(ha_o, ha_c))
            bull = ha_c > ha_o
            bear = ha_c < ha_o
            sma = pd.Series(c).rolling(100).mean().to_numpy()

            bull_p1 = np.zeros(m, dtype=bool)
            bull_p2 = np.zeros(m, dtype=bool)
            bear_p2 = np.zeros(m, dtype=bool)
            bull_p1[1:] = bull[:-1]
            bull_p2[2:] = bull[:-2]
            bear_p2[2:] = bear[:-2]
            valid_hist = np.arange(m) >= 2

            def put(name, values):
                full = np.full(n, np.nan)
                full[idx] = values
                dataframe[name] = full

            put("ha_open", ha_o)
            put("ha_close", ha_c)
            put("ha_low", ha_l)
            put("ha_bull", bull.astype(float))
            put("ha_bear", bear.astype(float))
            put("ha_bull_prev1", np.where(valid_hist, bull_p1, np.nan))
            put("ha_bull_prev2", np.where(valid_hist, bull_p2, np.nan))
            put("ha_bear_prev2", np.where(valid_hist, bear_p2, np.nan))
            put("sma_4h", sma)
            put("close_4h", c)
        dataframe["bar_complete"] = complete
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        wick = (dataframe["ha_open"] - dataframe["ha_low"]) / dataframe["ha_open"]
        dataframe.loc[
            (
                dataframe["bar_complete"]
                & dataframe["ha_open"].notna()
                & dataframe["ha_bear_prev2"].notna()
                & dataframe["sma_4h"].notna()
                & (dataframe["ha_bull"] == 1.0)
                & (dataframe["ha_bull_prev1"] == 1.0)
                & (dataframe["ha_bear_prev2"] == 1.0)
                & (wick <= 0.0005)
                & (dataframe["close_4h"] > dataframe["sma_4h"])
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "ha4h_fresh_flip")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["bar_complete"]
                & dataframe["ha_open"].notna()
                & (dataframe["ha_bear"] == 1.0)
                & (dataframe["volume"] > 0)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "ha4h_bearish")
        return dataframe
