"""H-033: hourly negative-shock overreaction.

Long when the 4-bar return is <= -4% and close is above SMA(1200). Exit when the
pre-drop price close(t-4) is regained, or 24 bars after the signal bar. Native
5% stop, 12-candle cooldown. Everything looks backwards only; the position state
is simulated causally row by row so the exit level P is known at signal time.
"""

import numpy as np
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class HourlyShockOverreaction_H033_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.05
    startup_candle_count = 1210

    SHOCK_BARS = 4
    SHOCK_THRESHOLD = -0.04
    SMA_BARS = 1200
    MAX_HOLD = 24
    COOLDOWN = 12

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 12}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        dataframe["pre_drop"] = close.shift(self.SHOCK_BARS)
        dataframe["r4"] = close / dataframe["pre_drop"] - 1.0
        dataframe["sma1200"] = close.rolling(self.SMA_BARS).mean()

        valid = (
            dataframe["r4"].notna()
            & dataframe["sma1200"].notna()
            & (dataframe["volume"] > 0)
        )
        raw = (
            valid
            & (dataframe["r4"] <= self.SHOCK_THRESHOLD)
            & (close > dataframe["sma1200"])
        ).to_numpy()
        vol_ok = (dataframe["volume"] > 0).to_numpy()
        close_v = close.to_numpy(dtype=float)
        pre_v = dataframe["pre_drop"].to_numpy(dtype=float)

        n = len(dataframe)
        sim_entry = np.zeros(n, dtype=bool)
        sim_exit = np.zeros(n, dtype=bool)
        in_pos = False
        signal_idx = 0
        level = np.nan
        blocked_until = -1
        for i in range(n):
            if in_pos:
                if vol_ok[i] and (
                    close_v[i] >= level or (i - signal_idx) >= self.MAX_HOLD
                ):
                    sim_exit[i] = True
                    in_pos = False
                    blocked_until = i + self.COOLDOWN
            elif raw[i] and i > blocked_until:
                sim_entry[i] = True
                in_pos = True
                signal_idx = i
                level = pre_v[i]

        dataframe["sim_entry"] = sim_entry.astype(int)
        dataframe["sim_exit"] = sim_exit.astype(int)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["sim_entry"] == 1)
                & dataframe["r4"].notna()
                & dataframe["sma1200"].notna()
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "shock_4h_above_sma1200")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["sim_exit"] == 1) & (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"],
        ] = (1, "regain_or_time")
        return dataframe
