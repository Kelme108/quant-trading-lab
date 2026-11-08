"""H-087: intraday return acceleration on 15m candles.

Rule (closed bars only, signal at close of bar t, fill at open of t+1):
    R1(t) = close(t) / close(t-16) - 1          (last 4 hours)
    R0(t) = close(t-16) / close(t-32) - 1       (previous 4 hours)
    A(t)  = R1(t) - R0(t)
    mu(t), sd(t) = mean and sample std (ddof=1) of A over bars t-2880..t-1 (rolling(2880) shifted by 1)
    Z(t)  = (A(t) - mu(t)) / sd(t); no signal if sd is 0 or NaN.
Entry (long, flat): Z(t) >= 2.0 AND Z(t-1) < 2.0 AND R1(t) >= 0.01 AND close(t) > open(t).
Exit signal: Z < 0 (first such bar after entry).
Time exit: trade age >= 480 minutes (custom_exit).
Stop: fixed 2% native stop (stoploss = -0.02), intrabar. No take-profit, no trailing, no cooldown.
Warm-up: 3000 bars (2880 Z window + 32 return lag + 1 for Z(t-1) = 2913).
"""

from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

RETURN_WINDOW = 16
Z_LOOKBACK = 2880
Z_ENTRY = 2.0
Z_EXIT = 0.0
MIN_R1 = 0.01
TIME_EXIT_MINUTES = 480


def acceleration_z(close: pd.Series) -> pd.DataFrame:
    """Causal R1, A and Z. Uses only the current and earlier rows."""
    r1 = close / close.shift(RETURN_WINDOW) - 1.0
    r0 = close.shift(RETURN_WINDOW) / close.shift(2 * RETURN_WINDOW) - 1.0
    accel = r1 - r0
    mu = accel.rolling(Z_LOOKBACK).mean().shift(1)
    sd = accel.rolling(Z_LOOKBACK).std(ddof=1).shift(1)
    sd_valid = sd.where(sd > 0)
    z = (accel - mu) / sd_valid
    z = z.replace([np.inf, -np.inf], np.nan)
    return pd.DataFrame({"r1": r1, "accel": accel, "accel_z": z}, index=close.index)


class IntradayReturnAcceleration_H087_v1(IStrategy):
    """Buy a fresh 2-sigma jump of the last-4h return over the prior 4h; max 8h hold."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.02
    trailing_stop = False
    use_exit_signal = True
    process_only_new_candles = True
    startup_candle_count = 3000

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ind = acceleration_z(dataframe["close"])
        dataframe["r1"] = ind["r1"]
        dataframe["accel"] = ind["accel"]
        dataframe["accel_z"] = ind["accel_z"]
        dataframe["accel_z_prev"] = ind["accel_z"].shift(1)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        z = dataframe["accel_z"]
        z_prev = dataframe["accel_z_prev"]
        cond = (
            z.notna()
            & z_prev.notna()
            & dataframe["r1"].notna()
            & (z >= Z_ENTRY)
            & (z_prev < Z_ENTRY)
            & (dataframe["r1"] >= MIN_R1)
            & (dataframe["close"] > dataframe["open"])
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[cond, ["enter_long", "enter_tag"]] = (1, "accel_z_cross")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        z = dataframe["accel_z"]
        cond = z.notna() & (z < Z_EXIT) & (dataframe["volume"] > 0)
        dataframe.loc[cond, ["exit_long", "exit_tag"]] = (1, "accel_z_below_0")
        return dataframe

    def custom_exit(
        self,
        pair: str,
        trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> Optional[str]:
        if current_time - trade.open_date_utc >= timedelta(minutes=TIME_EXIT_MINUTES):
            return "time_exit_8h"
        return None
