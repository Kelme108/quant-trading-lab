"""H-057: abnormal-day continuation on 1h, first crossing of the daily volatility band.

All times UTC, closed 1h bars only; a signal at a bar close fills at the next bar open.

Daily statistics (completed days only):
- C(k) = close of the last bar of UTC day k (normally the 23:00 bar).
- R(k) = C(k) / C(k-1) - 1, on a full calendar of days (a missing day leaves R undefined).
- For day d: m = mean, s = sample std (ddof=1) of R(d-30 .. d-1); fixed for all of day d.
Intraday:
- O = open of the first bar of day d (normally 00:00). D(t) = close(t) / O - 1.
- T = m + 0.75 * s.
Entry at the close of bar t: hour(t) in 1..18, D(t) >= T, D(t) >= 0.01, D(t-1) < T with t-1 the
previous bar of the same UTC day. One position (engine), at most one entry fill per pair per UTC
day, counting closed trades (confirm_trade_entry). The entry tag records O.
Exits (custom_exit, per trade):
- Failure: a closed bar of the trade closes below O of the signal day (= fill day).
- Time: 24 bars after the entry fill, exit at that open.
Stop: native 4% stoploss. No take-profit, trailing, cooldown or other filters.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy

BAR = timedelta(hours=1)
VOL_LOOKBACK_DAYS = 30
BAND_MULTIPLIER = 0.75
MIN_INTRADAY_MOVE = 0.01
ENTRY_FIRST_HOUR = 1
ENTRY_LAST_HOUR = 18
TIME_EXIT_BARS = 24
TAG_PREFIX = "abnormal_day"


def utc_day(value) -> pd.Timestamp:
    """UTC calendar day of a timestamp (naive timestamps are taken as UTC)."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return ts.floor("D")


def parse_tag(tag) -> float | None:
    """Day open O recorded in an entry tag, or None for a tag this strategy did not write."""
    if not isinstance(tag, str):
        return None
    parts = tag.split("|")
    if len(parts) != 2 or parts[0] != TAG_PREFIX:
        return None
    try:
        value = float(parts[1])
    except ValueError:
        return None
    if not np.isfinite(value) or value <= 0:
        return None
    return value


def abnormal_day_indicators(dataframe: DataFrame) -> DataFrame:
    """Add hour, day_open, d_move, d_move_prev, band_mean, band_std, threshold. Backward-looking only."""
    dates = pd.to_datetime(dataframe["date"], utc=True)
    day = dates.dt.floor("D")

    # Daily close = close of the last bar of each UTC day, on a gap-free day calendar.
    daily_close = dataframe["close"].groupby(day.to_numpy()).last()
    daily_close.index = pd.DatetimeIndex(daily_close.index)
    if daily_close.index.tz is None:
        daily_close.index = daily_close.index.tz_localize("UTC")
    calendar = pd.date_range(daily_close.index.min(), daily_close.index.max(), freq="D")
    daily_close = daily_close.reindex(calendar)
    daily_ret = daily_close / daily_close.shift(1) - 1.0
    # Stats for day d use only completed days d-30 .. d-1.
    band_mean = daily_ret.rolling(VOL_LOOKBACK_DAYS).mean().shift(1)
    band_std = daily_ret.rolling(VOL_LOOKBACK_DAYS).std(ddof=1).shift(1)

    day_index = pd.DatetimeIndex(day)
    dataframe["hour"] = dates.dt.hour.to_numpy()
    dataframe["band_mean"] = band_mean.reindex(day_index).to_numpy(dtype=float)
    dataframe["band_std"] = band_std.reindex(day_index).to_numpy(dtype=float)
    dataframe["threshold"] = dataframe["band_mean"] + BAND_MULTIPLIER * dataframe["band_std"]

    day_key = day.to_numpy()
    dataframe["day_open"] = dataframe["open"].groupby(day_key).transform("first").to_numpy(dtype=float)
    dataframe["d_move"] = dataframe["close"] / dataframe["day_open"] - 1.0
    dataframe["d_move_prev"] = dataframe["d_move"].groupby(day_key).shift(1).to_numpy(dtype=float)
    return dataframe


class AbnormalDayContinuation_H057_v1(IStrategy):
    """Buy the first intraday crossing of the 30-day mean + 0.75 sigma daily-return band."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.04
    startup_candle_count = 800

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return abnormal_day_indicators(dataframe)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        threshold = dataframe["threshold"]
        d_move = dataframe["d_move"]
        cond = (
            (dataframe["hour"] >= ENTRY_FIRST_HOUR)
            & (dataframe["hour"] <= ENTRY_LAST_HOUR)
            & threshold.notna()
            & d_move.notna()
            & dataframe["d_move_prev"].notna()
            & (d_move >= threshold)
            & (d_move >= MIN_INTRADAY_MOVE)
            & (dataframe["d_move_prev"] < threshold)
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = [
                f"{TAG_PREFIX}|{float(value)!r}" for value in dataframe.loc[cond, "day_open"]
            ]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Both exits depend on the trade (signal-day open, fill time); handled in custom_exit.
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """At most one entry fill per pair per UTC day, counting trades that were already closed."""
        if parse_tag(entry_tag) is None:
            return False
        today = utc_day(current_time)
        for trade in Trade.get_trades_proxy(pair=pair):
            if utc_day(trade.open_date_utc) == today:
                return False
        return True

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        day_open = parse_tag(trade.enter_tag)
        if day_open is not None:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if dataframe is not None and len(dataframe) > 0:
                closed = dataframe[dataframe["date"] + BAR <= current_time]
                if len(closed) > 0:
                    last = closed.iloc[-1]
                    if (
                        last["date"] >= trade.open_date_utc
                        and last["volume"] > 0
                        and last["close"] == last["close"]
                        and last["close"] < day_open
                    ):
                        return "failure_below_day_open"
        if current_time >= trade.open_date_utc + BAR * TIME_EXIT_BARS:
            return "time_exit_24_bars"
        return None
