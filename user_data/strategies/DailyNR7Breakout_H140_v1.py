"""H-140: open-anchored half-range breakout after an NR4 or inside day, 15m, flat by day end or 12h.

Rule (research/proposals/H-140.json), 15m, UTC, closed bars only, spot, long only:
- DAILY BARS are built from the 96 completed 15m bars of each UTC day (a day with missing bars is
  undefined). R1 = range(D-1) = high - low of day D-1.
- CONTRACTION: day D-1 is NR4 (R1 <= range of D-2, D-3 and D-4, ties count) OR an inside day
  (high(D-1) < high(D-2) and low(D-1) > low(D-2)).
- O = open of the 15m bar at 00:00 UTC of day D. Trigger T = O + 0.5 R1. Stop level S = O - 0.5 R1.
- ARMED: contraction and R1 / O >= 0.01.
- FILTER: close of the last completed 4h block (blocks start 00/04/08/12/16/20 UTC, complete after
  their 16th bar closes, evaluated at the signal bar's close) > SMA(50) of the last 50 completed
  4h closes (including that block).
- ENTRY: first bar of an armed day opening 00:00-11:45 UTC whose close > T while the filter holds;
  fills at the next open. At most one entry per UTC day per pair. S travels in enter_tag.
- STOP: fixed absolute price S (custom_stoploss, relative to the open rate), never wider than the
  native -10% backstop.
- EXITS: stop; day-end (close of the 23:45 bar of the entry day -> next open); 12h (48 bars).
  No take-profit.
- Warm-up 900 bars.
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

BAR_MINUTES = 15
BARS_PER_DAY = 96
BARS_PER_BLOCK = 16  # 4h block
NR_WINDOW_DAYS = 4
TRIGGER_MULT = 0.5
STOP_MULT = 0.5
MIN_RANGE_PCT = 0.01
FILTER_SMA_LENGTH = 50
LAST_ENTRY_HOUR_EXCLUSIVE = 12  # bars opening at or after 12:00 UTC cannot signal
TIME_EXIT_HOURS = 12  # 48 bars of 15m
BACKSTOP_PCT = 0.10
TAG_PREFIX = "nr7:"


class DailyNR7Breakout_H140_v1(IStrategy):
    """Open-anchored half-range breakout after an NR4 / inside day, long only, 15m."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.10
    use_custom_stoploss = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 900

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        n = len(dataframe)
        date = pd.to_datetime(dataframe["date"])
        day = date.dt.floor("1D")

        # ---- daily bars from complete UTC days (96 bars) -----------------------------------
        grouped = dataframe.groupby(day)
        complete = grouped["high"].count() == BARS_PER_DAY
        day_high = grouped["high"].max().where(complete)
        day_low = grouped["low"].min().where(complete)
        day_range = day_high - day_low

        def previous(series: pd.Series, k: int) -> np.ndarray:
            index = pd.Index(day - pd.Timedelta(days=k))
            return series.reindex(index).to_numpy(dtype=float)

        r1 = previous(day_range, 1)
        r2 = previous(day_range, 2)
        r3 = previous(day_range, 3)
        r4 = previous(day_range, 4)
        high1 = previous(day_high, 1)
        high2 = previous(day_high, 2)
        low1 = previous(day_low, 1)
        low2 = previous(day_low, 2)

        # open of the 15m bar opening at 00:00 UTC of day D
        midnight = (date == day).to_numpy()
        day_open = pd.Series(
            dataframe["open"].to_numpy(dtype=float)[midnight], index=pd.Index(day[midnight])
        )
        day_open = day_open[~day_open.index.duplicated(keep="first")]
        open_d = day_open.reindex(pd.Index(day)).to_numpy(dtype=float)

        with np.errstate(invalid="ignore", divide="ignore"):
            nr4 = (r1 <= r2) & (r1 <= r3) & (r1 <= r4)
            inside = (high1 < high2) & (low1 > low2)
            big_enough = (r1 / open_d) >= MIN_RANGE_PCT
        defined = np.isfinite(r1) & np.isfinite(open_d) & (open_d > 0)
        armed = defined & (nr4 | inside) & big_enough

        trigger = open_d + TRIGGER_MULT * r1
        stop_level = open_d - STOP_MULT * r1
        dataframe["nr7_trigger"] = np.where(defined, trigger, np.nan)
        dataframe["nr7_stop"] = np.where(defined, stop_level, np.nan)
        dataframe["nr7_armed"] = armed

        # ---- 4h trend filter from complete 4h blocks ----------------------------------------
        block = date.dt.floor("4h")
        block_group = dataframe.groupby(block)["close"]
        block_close = block_group.last().where(block_group.count() == BARS_PER_BLOCK)
        if len(block_close):
            full_index = pd.date_range(block_close.index.min(), block_close.index.max(), freq="4h")
            block_close = block_close.reindex(full_index)
        block_sma = block_close.rolling(FILTER_SMA_LENGTH).mean()
        # last block completed at this bar's close: its start is floor(close time, 4h) - 4h
        key = pd.Index((date + pd.Timedelta(minutes=BAR_MINUTES)).dt.floor("4h") - pd.Timedelta(hours=4))
        close_4h = block_close.reindex(key).to_numpy(dtype=float)
        sma_4h = block_sma.reindex(key).to_numpy(dtype=float)
        dataframe["nr7_close4h"] = close_4h
        dataframe["nr7_sma4h"] = sma_4h
        with np.errstate(invalid="ignore"):
            filter_ok = np.isfinite(close_4h) & np.isfinite(sma_4h) & (close_4h > sma_4h)

        # ---- first qualifying bar per UTC day -----------------------------------------------
        close = dataframe["close"].to_numpy(dtype=float)
        volume = dataframe["volume"].to_numpy(dtype=float)
        in_window = (date.dt.hour < LAST_ENTRY_HOUR_EXCLUSIVE).to_numpy()
        with np.errstate(invalid="ignore"):
            qualifies = (
                armed
                & filter_ok
                & in_window
                & np.isfinite(close)
                & (close > np.where(np.isfinite(trigger), trigger, np.inf))
                & np.isfinite(volume)
                & (volume > 0)
            )
        running = pd.Series(qualifies.astype(int), index=dataframe.index).groupby(day).cumsum()
        dataframe["nr7_signal"] = qualifies & (running.to_numpy() == 1)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ok = (
            dataframe["nr7_signal"].fillna(False).astype(bool)
            & dataframe["nr7_stop"].notna()
            & dataframe["nr7_trigger"].notna()
            & dataframe["nr7_sma4h"].notna()
            & (dataframe["volume"] > 0)
        )
        if ok.any():
            dataframe.loc[ok, "enter_long"] = 1
            dataframe.loc[ok, "enter_tag"] = dataframe.loc[ok, "nr7_stop"].map(
                lambda value: TAG_PREFIX + repr(float(value))
            )
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # No exit signals: exits are the stop, the day-end exit and the 12h time exit.
        return dataframe

    @staticmethod
    def _stop_level(trade):
        tag = trade.enter_tag
        if not isinstance(tag, str) or not tag.startswith(TAG_PREFIX):
            return None
        try:
            value = float(tag[len(TAG_PREFIX):])
        except ValueError:
            return None
        return value if np.isfinite(value) and value > 0 else None

    def custom_stoploss(
        self, pair: str, trade, current_time, current_rate: float,
        current_profit: float, after_fill: bool = False, **kwargs
    ):
        level = self._stop_level(trade)
        entry = trade.open_rate
        if level is None or not entry or not current_rate:
            return None  # fall back to the native backstop
        # stop price S, but never wider than the native 10% backstop
        stop_price = max(level, entry * (1.0 - BACKSTOP_PCT))
        ratio = stop_price / current_rate - 1.0
        if ratio >= 0:
            # price already at or below the frozen stop: stop out as soon as possible
            return -1e-6
        return ratio

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        opened = trade.open_date_utc
        # close of the 23:45 bar of the entry day -> exit at the next open (00:00 of the next day)
        if current_time.date() > opened.date():
            return "day_end_exit"
        if current_time - opened >= timedelta(hours=TIME_EXIT_HOURS):
            return "time_exit_12h"
        return None
