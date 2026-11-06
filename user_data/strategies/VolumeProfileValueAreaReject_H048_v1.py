"""H-048: prior-week volume-profile value-area-low sweep and reclaim (long only).

Profile: the 168 completed 1h bars before each UTC day (00:00), 50 price rows,
frozen for that day. Entry on a sweep below VAL that is reclaimed, target POC.
Exits: close >= POC (dataframe signal), 48 bars elapsed, or close below
sweep_low * 0.995 (custom_exit). Stop is the native 4% stoploss; cooldown is
6 candles via protections. At most one entry signal per UTC day (the first
candidate of the day).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy

PROFILE_BARS = 168
PRICE_ROWS = 50
VALUE_AREA = 0.7
SWEEP_WINDOW = 4
MIN_POC_DISTANCE = 0.015
TIME_STOP_BARS = 48
SWEEP_EXIT_BUFFER = 0.005


def compute_profile(high, low, volume):
    """Return (VAL, POC price) for one window of bars, or (nan, nan)."""
    lo = float(np.min(low))
    hi = float(np.max(high))
    total = float(np.sum(volume))
    if not (hi > lo) or not (total > 0):
        return np.nan, np.nan
    width = (hi - lo) / PRICE_ROWS
    rows = np.zeros(PRICE_ROWS)
    first = np.clip(np.floor((low - lo) / width).astype(int), 0, PRICE_ROWS - 1)
    last = np.clip(np.floor((high - lo) / width).astype(int), 0, PRICE_ROWS - 1)
    for f, l, v in zip(first, last, volume):
        rows[f : l + 1] += v / (l - f + 1)
    poc = int(np.argmax(rows))
    bottom = top = poc
    area = rows[poc]
    target = VALUE_AREA * rows.sum()
    while area < target:
        above_rows = rows[top + 1 : top + 3]
        below_rows = rows[max(bottom - 2, 0) : bottom][::-1]
        if len(above_rows) == 0 and len(below_rows) == 0:
            break
        if len(above_rows) == 0:
            go_below = True
        elif len(below_rows) == 0:
            go_below = False
        else:
            go_below = below_rows.sum() >= above_rows.sum()
        if go_below:
            area += below_rows.sum()
            bottom -= len(below_rows)
        else:
            area += above_rows.sum()
            top += len(above_rows)
    return lo + bottom * width, lo + (poc + 0.5) * width


class VolumeProfileValueAreaReject_H048_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.04
    startup_candle_count = 200

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 6}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        n = len(dataframe)
        dates = pd.to_datetime(dataframe["date"], utc=True)
        day = dates.dt.floor("D")
        high = dataframe["high"].to_numpy(dtype=float)
        low = dataframe["low"].to_numpy(dtype=float)
        vol = dataframe["volume"].to_numpy(dtype=float)
        date_ns = dates.dt.tz_localize(None).to_numpy().astype("datetime64[ns]")
        val = np.full(n, np.nan)
        poc = np.full(n, np.nan)
        one_hour = np.timedelta64(1, "h")
        for d in day.unique():
            d64 = np.datetime64(d.tz_convert("UTC").tz_localize(None), "ns")
            start = int(np.searchsorted(date_ns, d64 - PROFILE_BARS * one_hour, "left"))
            stop = int(np.searchsorted(date_ns, d64, "left"))
            if stop - start != PROFILE_BARS:
                continue
            v, p = compute_profile(high[start:stop], low[start:stop], vol[start:stop])
            mask = (day == d).to_numpy()
            val[mask] = v
            poc[mask] = p
        dataframe["va_low"] = val
        dataframe["poc"] = poc
        dataframe["sweep_low"] = dataframe["low"].rolling(SWEEP_WINDOW).min()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        cand = (
            (dataframe["sweep_low"] < dataframe["va_low"])
            & (close > dataframe["va_low"])
            & ((close.shift(1) <= dataframe["va_low"]) | (dataframe["low"] < dataframe["va_low"]))
            & ((dataframe["poc"] / close - 1) >= MIN_POC_DISTANCE)
            & (dataframe["volume"] > 0)
        ).fillna(False)
        day = pd.to_datetime(dataframe["date"], utc=True).dt.floor("D")
        first_of_day = cand & (cand.groupby(day).cumsum() == 1)
        dataframe.loc[first_of_day, ["enter_long", "enter_tag"]] = (1, "va_low_reclaim")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = ((dataframe["close"] >= dataframe["poc"]) & (dataframe["volume"] > 0)).fillna(False)
        dataframe.loc[cond, ["exit_long", "exit_tag"]] = (1, "poc_target")
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        df, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if df is None or len(df) == 0:
            return None
        dates = pd.to_datetime(df["date"], utc=True)
        signal_time = pd.Timestamp(trade.open_date_utc) - pd.Timedelta(hours=1)
        idx = dates.index[dates == signal_time]
        if len(idx) == 0:
            return None
        sweep = df.loc[idx[0], "sweep_low"]
        last = df.iloc[-1]
        if pd.isna(sweep):
            return None
        if (dates.iloc[-1] - signal_time) >= pd.Timedelta(hours=TIME_STOP_BARS):
            return "time_stop"
        if last["close"] < sweep * (1 - SWEEP_EXIT_BUFFER):
            return "sweep_break"
        return None
