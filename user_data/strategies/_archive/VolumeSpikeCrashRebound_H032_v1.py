"""H-032: volume-spike hourly crash closing off its low; rebound to crash-bar open.

Closed 1h candles only. Entry at the close of bar t (filled at open t+1) when
r1 <= -3*S, r1 <= -1.5%, V >= 3, Pos >= 0.5. S is the ddof=1 std of the 720
returns ending at t-1, V is volume(t) / mean volume of the 168 bars ending at
t-1. Exit at the close of the first bar u >= t+1 with close >= open(t), or at
the close of bar t+18. Stop 4% (engine), cooldown 6 candles (protections).
"""

import numpy as np
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class VolumeSpikeCrashRebound_H032_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.04
    startup_candle_count = 800

    vol_window = 720
    volume_window = 168
    sigma_multiple = 3.0
    min_drop = 0.015
    volume_multiple = 3.0
    range_position_min = 0.5
    time_exit_bars = 18

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 6}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        r1 = close / close.shift(1) - 1.0
        # Statistics use bars up to t-1 only (shifted by one candle).
        dataframe["r1"] = r1
        dataframe["sigma"] = r1.shift(1).rolling(self.vol_window).std(ddof=1)
        mean_vol = dataframe["volume"].shift(1).rolling(self.volume_window).mean()
        dataframe["vol_ratio"] = dataframe["volume"] / mean_vol.where(mean_vol > 0)
        rng = dataframe["high"] - dataframe["low"]
        dataframe["range_pos"] = (close - dataframe["low"]) / rng.where(rng > 0)

        signal = (
            dataframe["r1"].notna()
            & dataframe["sigma"].notna()
            & dataframe["vol_ratio"].notna()
            & dataframe["range_pos"].notna()
            & (dataframe["r1"] <= -self.sigma_multiple * dataframe["sigma"])
            & (dataframe["r1"] <= -self.min_drop)
            & (dataframe["vol_ratio"] >= self.volume_multiple)
            & (dataframe["range_pos"] >= self.range_position_min)
            & (dataframe["volume"] > 0)
        )
        dataframe["crash_signal"] = signal.astype(int)

        # Most recent crash bar at or before each row (backward-looking only).
        idx = np.arange(len(dataframe), dtype=float)
        last_idx = DataFrame({"i": np.where(signal.to_numpy(), idx, np.nan)}).ffill()["i"]
        bars_since = idx - last_idx.to_numpy()
        pos = last_idx.fillna(0).astype(int).to_numpy()
        target = dataframe["open"].to_numpy()[pos] if len(dataframe) else np.array([])
        target = np.where(np.isnan(last_idx.to_numpy()), np.nan, target)
        dataframe["crash_target"] = target
        dataframe["bars_since_crash"] = bars_since
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["crash_signal"] == 1) & (dataframe["volume"] > 0),
            ["enter_long", "enter_tag"],
        ] = (1, "crash_rebound")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        k = dataframe["bars_since_crash"]
        valid = (
            k.notna()
            & dataframe["crash_target"].notna()
            & (k >= 1)
            & (k <= self.time_exit_bars)
            & (dataframe["volume"] > 0)
        )
        hit = dataframe["close"] >= dataframe["crash_target"]
        timeout = k == self.time_exit_bars
        dataframe.loc[valid & hit, ["exit_long", "exit_tag"]] = (1, "target")
        dataframe.loc[valid & ~hit & timeout, ["exit_long", "exit_tag"]] = (1, "time")
        return dataframe
