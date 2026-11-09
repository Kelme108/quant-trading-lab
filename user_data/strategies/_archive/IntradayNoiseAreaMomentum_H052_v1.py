"""H-052: noise-area intraday momentum on 1h, flat by 00:00 UTC.

Day = UTC calendar day, slot h = hour of the bar's open. O_d = open of the slot-0 bar.
move_d(h) = |close / O_d - 1|. sigma_d(h) = mean of move_k(h) over the 14 previous UTC days
(same slot, timestamps exactly 1..14 days earlier; undefined if any is missing). U = O_d * (1 + sigma).
VWAP resets at slot 0, TP = (high + low + close) / 3.

Entry (signal at the close, fill at next open): slot 1..19, close > U, close > VWAP.
At most one entry fill per pair per UTC day, also after a stop-out (confirm_trade_entry).
Exit signal: close < max(U, VWAP) on any bar while in position.
Time exit: still open at 00:00 UTC of a later day -> exit at that open (custom_exit).
Stop: native 3% stoploss. No take-profit, no cooldown.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy

NOISE_LOOKBACK_DAYS = 14
ENTRY_FIRST_SLOT = 1
ENTRY_LAST_SLOT = 19


def utc_day(value) -> pd.Timestamp:
    """UTC calendar day of a timestamp (naive timestamps are taken as UTC)."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return ts.floor("D")


def noise_area_indicators(dataframe: DataFrame) -> DataFrame:
    """Add day_open, sigma, upper_band, vwap, trail and slot columns. Backward-looking only."""
    dates = pd.to_datetime(dataframe["date"], utc=True)
    day = dates.dt.floor("D")
    slot = dates.dt.hour

    day_open = dataframe["open"].where(slot == 0).groupby(day).transform("first")
    move = (dataframe["close"] / day_open - 1.0).abs()

    move_by_time = pd.Series(move.to_numpy(dtype=float), index=pd.DatetimeIndex(dates))
    move_by_time = move_by_time[~move_by_time.index.duplicated(keep="last")]
    lagged = [
        move_by_time.reindex(pd.DatetimeIndex(dates) - pd.Timedelta(days=k)).to_numpy(dtype=float)
        for k in range(1, NOISE_LOOKBACK_DAYS + 1)
    ]
    # Plain mean: NaN (undefined) unless all 14 previous same-slot values exist.
    sigma = np.vstack(lagged).mean(axis=0)

    tp = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3.0
    pv_cum = (tp * dataframe["volume"]).groupby(day).cumsum()
    vol_cum = dataframe["volume"].groupby(day).cumsum()
    vwap = (pv_cum / vol_cum.where(vol_cum > 0)).to_numpy(dtype=float)

    dataframe["slot"] = slot.to_numpy()
    dataframe["day_open"] = day_open.to_numpy(dtype=float)
    dataframe["sigma"] = sigma
    dataframe["upper_band"] = dataframe["day_open"] * (1.0 + dataframe["sigma"])
    dataframe["vwap"] = vwap
    dataframe["trail"] = dataframe[["upper_band", "vwap"]].max(axis=1, skipna=False)
    return dataframe


class IntradayNoiseAreaMomentum_H052_v1(IStrategy):
    """Upside break of the time-of-day noise band above daily VWAP; trails at max(band, VWAP)."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    startup_candle_count = 360

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return noise_area_indicators(dataframe)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        cond = (
            (dataframe["slot"] >= ENTRY_FIRST_SLOT)
            & (dataframe["slot"] <= ENTRY_LAST_SLOT)
            & (close > dataframe["upper_band"])
            & (close > dataframe["vwap"])
            & dataframe["upper_band"].notna()
            & dataframe["vwap"].notna()
            & (dataframe["volume"] > 0)
        ).fillna(False)
        dataframe.loc[cond, ["enter_long", "enter_tag"]] = (1, "noise_area_break")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (
            (dataframe["close"] < dataframe["trail"])
            & dataframe["trail"].notna()
            & (dataframe["volume"] > 0)
        ).fillna(False)
        dataframe.loc[cond, ["exit_long", "exit_tag"]] = (1, "below_band_or_vwap")
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """At most one entry fill per pair per UTC day, counting trades that were already closed."""
        today = utc_day(current_time)
        for trade in Trade.get_trades_proxy(pair=pair):
            if utc_day(trade.open_date_utc) == today:
                return False
        return True

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        """Time exit: a position still open on a later UTC day closes at the 00:00 UTC open."""
        if utc_day(current_time) > utc_day(trade.open_date_utc):
            return "time_exit_utc_midnight"
        return None
