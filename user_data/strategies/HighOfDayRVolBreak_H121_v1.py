"""H-121: high-of-day break on a high-volume day, 15m, all times UTC, closed bars only.

A signal at the close of bar t fills at the open of bar t+1. Long only, spot, one position per pair (engine).

Definitions (day d = the 96 bars opening 00:00-23:45 UTC; k(t) = clock slot of bar t, 0..95):
- Od = open of day d's 00:00 bar.
- CUMVOL(d, k) = sum of volume of day d's bars from slot 0 through slot k.
- RVOL(t) = CUMVOL(d, k(t)) / mean over the 20 previous UTC days (d-1..d-20) of CUMVOL(j, k(t)).
  Undefined (no entry) when any of those 20 days lacks a bar at or before slot k, or the mean is 0.
- HOD(t) = highest high of day d's bars from slot 0 through bar t-1; s(t) = the most recent bar in that window
  whose high equals HOD(t). The level is "held" only if s(t) <= t-8 (at least 2 h earlier).
Entry (all at the close of bar t): bar t opens 02:00-19:45 UTC; close(t) > HOD(t) and held; RVOL(t) >= 1.5;
close(t)/Od - 1 >= 0.005; no open position (engine); fewer than 2 entries already filled that UTC day on the pair
(confirm_trade_entry).
Exits (first that occurs): native stop 1% below the entry price; take-profit +2% and the time exit (32 bars = 8 h
after the entry fill, or the open of the 23:45 UTC bar of the entry day, whichever is first) in custom_exit.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

SLOTS_PER_DAY = 96
RVOL_LOOKBACK_DAYS = 20
RVOL_MIN = 1.5
HOD_HOLD_BARS = 8
ENTRY_FIRST_SLOT = 8  # 02:00 UTC
ENTRY_LAST_SLOT = 79  # 19:45 UTC
MIN_DAY_RETURN = 0.005
MAX_ENTRIES_PER_DAY = 2
TAKE_PROFIT = 0.02
TIME_EXIT = timedelta(hours=8)  # 32 bars of 15m
EOD_EXIT_OFFSET = timedelta(hours=23, minutes=45)


def to_utc(value) -> pd.Timestamp:
    """Timestamp as tz-aware UTC (naive values are taken as UTC)."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")


def utc_day(value) -> pd.Timestamp:
    return to_utc(value).floor("D")


def rvol_series(day_index: np.ndarray, slot: np.ndarray, volume: np.ndarray) -> np.ndarray:
    """Time-of-day matched cumulative relative volume for each bar (NaN where undefined).

    day_index: integer day number of each bar (consecutive calendar days), slot: 0..95, volume: bar volume.
    Only bars of the same day up to the bar's own slot enter CUMVOL(d, k); the 20 previous days enter only
    through their own complete prefix 0..k, so no later bar influences an earlier row.
    """
    n_days = int(day_index.max()) + 1
    vol = np.full((n_days, SLOTS_PER_DAY), np.nan)
    vol[day_index, slot] = volume
    present = ~np.isnan(vol)
    cum = np.cumsum(np.where(present, vol, 0.0), axis=1)
    complete = np.cumsum(present, axis=1) == np.arange(1, SLOTS_PER_DAY + 1)
    # Previous-day prefix sums count only when every bar at or before the slot exists.
    prev_cum = DataFrame(np.where(complete, cum, np.nan))
    prev_sum = prev_cum.rolling(RVOL_LOOKBACK_DAYS).sum().shift(1).to_numpy()
    prev_mean = prev_sum / RVOL_LOOKBACK_DAYS
    mean_bar = prev_mean[day_index, slot]
    cum_bar = cum[day_index, slot]
    with np.errstate(divide="ignore", invalid="ignore"):
        rvol = np.where(mean_bar > 0, cum_bar / mean_bar, np.nan)
    return rvol


class HighOfDayRVolBreak_H121_v1(IStrategy):
    """Buy a close above a 2h-held intraday high on a day with time-matched cumulative RVOL >= 1.5."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.01
    use_exit_signal = True
    startup_candle_count = 2112

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dates = pd.to_datetime(dataframe["date"], utc=True)
        day = dates.dt.floor("D")
        slot = (dates.dt.hour * 4 + dates.dt.minute // 15).to_numpy()
        day_key = day.to_numpy()
        day_index = ((day - day.min()).dt.days).to_numpy()

        high = dataframe["high"].astype(float)
        by_day = high.groupby(day_key)
        running_max = by_day.cummax()
        # Most recent bar (slot) whose high equals the running day high, as of each bar, then shifted by one
        # so the window ends at bar t-1 (the current candle is excluded).
        updated_slot = pd.Series(slot, index=dataframe.index).where(high == running_max)
        last_update_slot = updated_slot.groupby(day_key).ffill()
        dataframe["hod"] = running_max.groupby(day_key).shift(1)
        hod_slot = last_update_slot.groupby(day_key).shift(1)
        dataframe["hod_held"] = (hod_slot <= (slot - HOD_HOLD_BARS)).where(hod_slot.notna(), False)

        day_open = dataframe["open"].astype(float).where(slot == 0)
        dataframe["day_open"] = day_open.groupby(day_key).transform("first")
        dataframe["day_return"] = dataframe["close"] / dataframe["day_open"] - 1.0

        volume = dataframe["volume"].astype(float).to_numpy()
        dataframe["rvol"] = rvol_series(day_index, slot, volume)
        dataframe["slot"] = slot
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (
            dataframe["hod"].notna()
            & dataframe["rvol"].notna()
            & dataframe["day_return"].notna()
            & dataframe["close"].notna()
            & (dataframe["slot"] >= ENTRY_FIRST_SLOT)
            & (dataframe["slot"] <= ENTRY_LAST_SLOT)
            & (dataframe["close"] > dataframe["hod"])
            & dataframe["hod_held"].astype(bool)
            & (dataframe["rvol"] >= RVOL_MIN)
            & (dataframe["day_return"] >= MIN_DAY_RETURN)
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Take-profit and time exits depend on the open trade: see custom_exit.
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """Fewer than 2 entries already filled on this pair with an entry date in the current UTC day."""
        from freqtrade.persistence import Trade

        today = utc_day(current_time)
        filled_today = 0
        for trade in Trade.get_trades_proxy(pair=pair):
            if utc_day(trade.open_date_utc) == today:
                filled_today += 1
        return filled_today < MAX_ENTRIES_PER_DAY

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        if current_profit is not None and current_profit >= TAKE_PROFIT:
            return "take_profit_2pct"
        opened = to_utc(trade.open_date_utc)
        now = to_utc(current_time)
        if now >= opened + TIME_EXIT:
            return "time_exit_8h"
        if now >= utc_day(opened) + EOD_EXIT_OFFSET:
            return "time_exit_utc_day_close"
        return None
