"""H-045: hourly confirmed-swing structure break (long only, 1h).

Pivots use a 3-bar half window and are known only at the close of bar i+3.
A pivot is accepted only if it is at least 2% away from the latest accepted
opposite pivot. Entry: higher swing low, close crosses above the latest swing
high, close above SMA(200). Exit: close below the latest swing low.
Stop-loss 4%; 6-candle cooldown after any exit.
"""

import numpy as np
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class HourlySwingStructureBreak_H045_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.04
    startup_candle_count = 1500

    HALF_WINDOW = 3
    MIN_SWING = 0.02
    SMA_LENGTH = 200
    WARMUP_BARS = 1500

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 6}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        n = len(dataframe)
        w = self.HALF_WINDOW
        highs = dataframe["high"].to_numpy(dtype=float)
        lows = dataframe["low"].to_numpy(dtype=float)

        sh = np.full(n, np.nan)
        sl = np.full(n, np.nan)
        sl_prev = np.full(n, np.nan)

        cur_sh = np.nan
        cur_sl = np.nan
        cur_sl_prev = np.nan

        for t in range(n):
            i = t - w
            if i >= w:
                hw = highs[i - w : t + 1]
                lw = lows[i - w : t + 1]
                # Pivot high: earliest of equal highs counts.
                if not np.isnan(hw).any():
                    h = highs[i]
                    if h > hw[:w].max() and h >= hw[w + 1 :].max():
                        if np.isnan(cur_sl) or (h - cur_sl) / cur_sl >= self.MIN_SWING:
                            cur_sh = h
                if not np.isnan(lw).any():
                    low = lows[i]
                    if low < lw[:w].min() and low <= lw[w + 1 :].min():
                        if np.isnan(cur_sh) or (cur_sh - low) / cur_sh >= self.MIN_SWING:
                            cur_sl_prev = cur_sl
                            cur_sl = low
            sh[t] = cur_sh
            sl[t] = cur_sl
            sl_prev[t] = cur_sl_prev

        dataframe["swing_high"] = sh
        dataframe["swing_low"] = sl
        dataframe["swing_low_prev"] = sl_prev
        dataframe["sma200"] = dataframe["close"].rolling(self.SMA_LENGTH).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        past = dataframe["close"].shift(1)
        index_ok = np.arange(len(dataframe)) >= self.WARMUP_BARS
        dataframe.loc[
            (
                (dataframe["swing_low"] > dataframe["swing_low_prev"])
                & (dataframe["close"] > dataframe["swing_high"])
                & (past <= dataframe["swing_high"])
                & (dataframe["close"] > dataframe["sma200"])
                & (dataframe["volume"] > 0)
                & index_ok
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "swing_structure_break")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        index_ok = np.arange(len(dataframe)) >= self.WARMUP_BARS
        dataframe.loc[
            (
                (dataframe["close"] < dataframe["swing_low"])
                & (dataframe["volume"] > 0)
                & index_ok
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "swing_low_break")
        return dataframe
