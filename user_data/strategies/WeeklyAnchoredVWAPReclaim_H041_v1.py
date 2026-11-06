"""H-041: weekly Monday-anchored VWAP reclaim after a sustained dip, in an SMA(480) uptrend (1h, long only).

Weekly VWAP = cumulative sum(typical*volume)/cumulative sum(volume) from Monday 00:00 UTC through the bar, typical =
(high+low+close)/3. Entry at the close of bar t (order at next open) when: the bar's open time is Monday 11:00 UTC or
later, close(t) > VWAP(t), the below-VWAP run that ended at t-1 lasted >= 8 bars (all inside the week) with a minimum
deviation <= -1.0%, close(t) > SMA(480), bar t is not the Sunday 23:00 bar, and no position is open.
Exit at the close of bar t when close < VWAP*(1-0.007), or bar t is the Sunday 23:00 bar, or 48 bars have elapsed
since the entry bar. Stop-loss 3% (native). No cooldown.

"One position" and the 48-bar cap need state. A causal bar-by-bar tracker (only past rows, entry price proxied by the
signal close) decides which setups become entries and when the 48-bar exit fires; a tracked position also ends when a
later low touches the 3% stop level, so the tracker follows the real position.
"""

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy
import talib.abstract as ta

MIN_WEEK_HOURS = 11  # open time >= Monday 11:00 -> at least 12 bars including the signal bar
MIN_RUN_BARS = 8
MIN_DEPTH = -0.010
TREND_SMA = 480
EXIT_BELOW_VWAP = 0.007
MAX_HOLD_BARS = 48
STOP_LOSS = 0.03


class WeeklyAnchoredVWAPReclaim_H041_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    startup_candle_count = 500

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        date = pd.to_datetime(dataframe["date"], utc=True)
        dow = date.dt.day_of_week
        hour = date.dt.hour
        week = (date.dt.normalize() - pd.to_timedelta(dow, unit="D")).astype("int64")
        week = pd.Series(np.asarray(week), index=dataframe.index)

        typical = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3.0
        pv = (typical * dataframe["volume"]).groupby(week).cumsum()
        vol = dataframe["volume"].groupby(week).cumsum()
        vwap = (pv / vol.where(vol > 0)).astype(float)
        dev = dataframe["close"] / vwap - 1.0

        below = (dataframe["close"] < vwap).fillna(False).astype(bool)
        run_key = (~below).groupby(week).cumsum()
        run_len = below.astype(int).groupby([week, run_key]).cumsum()
        run_min = dev.where(below).groupby([week, run_key]).cummin()

        prev_len = run_len.shift(1).fillna(0)
        prev_min = run_min.shift(1)
        prev_below = below.shift(1, fill_value=False).astype(bool)
        setup = prev_below & (prev_len >= MIN_RUN_BARS) & (prev_min <= MIN_DEPTH)

        sma = ta.SMA(dataframe, timeperiod=TREND_SMA)
        week_hours = dow * 24 + hour
        eligible = week_hours >= MIN_WEEK_HOURS
        sunday_last = (dow == 6) & (hour == 23)
        valid = (dataframe["volume"] > 0) & vwap.notna() & sma.notna()

        raw_entry = (
            valid & eligible & ~sunday_last & setup & (dataframe["close"] > vwap) & (dataframe["close"] > sma)
        ).fillna(False).astype(bool)
        base_exit = (valid & ((dataframe["close"] < vwap * (1.0 - EXIT_BELOW_VWAP)) | sunday_last)).fillna(False)
        base_exit = base_exit.astype(bool)

        # causal position tracker
        n = len(dataframe)
        raw = raw_entry.to_numpy()
        bexit = base_exit.to_numpy()
        close = dataframe["close"].to_numpy(dtype=float)
        low = dataframe["low"].to_numpy(dtype=float)
        vol_ok = (dataframe["volume"] > 0).to_numpy()
        entry = np.zeros(n, dtype=int)
        time_exit = np.zeros(n, dtype=int)
        in_pos = False
        entry_i = 0
        entry_px = 0.0
        for i in range(n):
            if in_pos:
                if low[i] <= entry_px * (1.0 - STOP_LOSS):
                    in_pos = False
                elif bexit[i]:
                    in_pos = False
                elif i - entry_i >= MAX_HOLD_BARS:
                    if vol_ok[i]:
                        time_exit[i] = 1
                    in_pos = False
            if not in_pos and raw[i]:
                in_pos = True
                entry_i = i
                entry_px = close[i]
                entry[i] = 1

        dataframe["vwap_week"] = vwap
        dataframe["sma_trend"] = sma
        dataframe["entry_sig"] = entry
        dataframe["exit_base"] = base_exit.astype(int)
        dataframe["exit_time"] = time_exit
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ok = (dataframe["entry_sig"] == 1) & (dataframe["volume"] > 0) & dataframe["vwap_week"].notna()
        ok = ok & dataframe["sma_trend"].notna()
        dataframe.loc[ok, ["enter_long", "enter_tag"]] = (1, "weekly_vwap_reclaim")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ok = (dataframe["exit_base"] == 1) | (dataframe["exit_time"] == 1)
        ok = ok & (dataframe["volume"] > 0) & dataframe["vwap_week"].notna()
        dataframe.loc[ok, ["exit_long", "exit_tag"]] = (1, "vwap_week_time_exit")
        return dataframe
