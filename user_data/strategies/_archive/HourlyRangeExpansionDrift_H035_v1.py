"""H-035: hourly range-expansion bar closing near its high, 24h hold, in uptrend.

Entry (closed 1h bar t, filled at open of t+1), all of:
- Range(t) >= 3.0 * ATR(t), ATR = simple mean of TR over bars t-24..t-1
- Pos(t) = (close-low)/(high-low) >= 0.8 (high == low does not qualify)
- close > open and close > SMA(480)
Exit: close below the low of the most recent earlier signal bar (executed at the
next open), or 24 hours after entry (custom_exit). Fixed 5% stop, 6-candle
cooldown. Note: the signal-bar low is the most recent prior signal bar's low,
since the vectorised exit cannot see which signal became the actual entry.
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class HourlyRangeExpansionDrift_H035_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.05
    startup_candle_count = 500

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 6}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        prev_close = dataframe["close"].shift(1)
        tr = pd.concat(
            [
                dataframe["high"] - dataframe["low"],
                (dataframe["high"] - prev_close).abs(),
                (dataframe["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1, skipna=False)
        dataframe["atr24"] = tr.rolling(24).mean().shift(1)
        dataframe["range"] = dataframe["high"] - dataframe["low"]
        rng = dataframe["range"].replace(0.0, np.nan)
        dataframe["pos"] = (dataframe["close"] - dataframe["low"]) / rng
        dataframe["sma480"] = dataframe["close"].rolling(480).mean()
        signal = (
            dataframe["atr24"].notna()
            & dataframe["pos"].notna()
            & dataframe["sma480"].notna()
            & (dataframe["range"] >= 3.0 * dataframe["atr24"])
            & (dataframe["pos"] >= 0.8)
            & (dataframe["close"] > dataframe["open"])
            & (dataframe["close"] > dataframe["sma480"])
        )
        dataframe["signal_bar"] = signal.astype(int)
        sig_low = dataframe["low"].where(signal)
        # Low of the latest signal bar strictly before the current bar.
        dataframe["signal_low"] = sig_low.shift(1).ffill()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["signal_bar"] == 1) & (dataframe["volume"] > 0),
            ["enter_long", "enter_tag"],
        ] = (1, "range_expansion")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            dataframe["signal_low"].notna()
            & (dataframe["close"] < dataframe["signal_low"])
            & (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"],
        ] = (1, "below_signal_low")
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        if current_time - trade.open_date_utc >= timedelta(hours=24):
            return "time_exit_24h"
        return None
