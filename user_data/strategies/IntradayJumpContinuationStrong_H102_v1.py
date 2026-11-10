"""H-102 (v2 of H-059): Intraday positive-jump continuation on 15m with a stronger jump (statistic at least 6.0 instead of 4.0).

One change from H-059, fixed ex ante: the bipower jump statistic threshold is 6.0 instead of 4.0.
Everything else (entries, exits, stop, warm-up) is the parent's code.

--- parent description ---
H-059: intraday positive-jump continuation on 15m, held to the UTC day close.

All times UTC, closed 15m bars only; a signal at the close of bar t fills at the open of bar t+1.
Long only, spot, one position per pair (engine), no pyramiding, no take-profit, no sizing hooks.

Definitions:
- r(i) = ln(close(i) / close(i-1)).
- s(t) = sqrt((pi/2) * mean over i = t-96..t-1 of |r(i)| * |r(i-1)|)   (bipower, bar t excluded).
- J(t) = r(t) / s(t); no signal when s(t) is 0 or undefined.
Daily filter: UTC daily closes built from the 15m data, attached with merge_informative_pair (ffill), so a
daily close is visible only once its day has closed. Holds when the last completed daily close is strictly
above the simple mean of the last 30 completed daily closes (that day included).
Entry at the close of bar t when all hold: J(t) >= 4.0; r(t) >= 0.006; bar t opens 00:00..17:45 UTC;
daily filter; no position open (engine); no trade already entered on this UTC day (confirm_trade_entry).
The entry tag records L = low of the jump bar t.
Exits (custom_exit), first of:
- (a) a closed bar u >= t+1 (entry bar included) closes below L -> sell at the open of u+1;
- (b) time exit: after the 23:45 UTC bar of the signal day closes -> sell at the 00:00 UTC open.
Stop: native 3% stoploss (backstop). No cooldown beyond one trade per UTC day.
"""

from __future__ import annotations

import math
from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, merge_informative_pair

BAR = timedelta(minutes=15)
BIPOWER_WINDOW = 96
JUMP_THRESHOLD = 6.0
MIN_BAR_LOG_RETURN = 0.006
ENTRY_LAST_HOUR = 17  # last entry bar opens at 17:45 UTC
DAILY_SMA_DAYS = 30
TAG_PREFIX = "jump_low"


def utc_day(value) -> pd.Timestamp:
    """UTC calendar day of a timestamp (naive timestamps are taken as UTC)."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return ts.floor("D")


def parse_tag(tag) -> float | None:
    """Jump-bar low L recorded in an entry tag, or None for a tag this strategy did not write."""
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


def jump_indicators(dataframe: DataFrame) -> DataFrame:
    """Add log_ret, bipower_sigma, jump_stat and hour. Backward-looking only."""
    close = dataframe["close"]
    log_ret = np.log(close / close.shift(1))
    product = log_ret.abs() * log_ret.shift(1).abs()
    # Mean over i = t-96..t-1: the window ends at t-1, so the current bar is excluded.
    mean_product = product.rolling(BIPOWER_WINDOW).mean().shift(1)
    sigma = np.sqrt((math.pi / 2.0) * mean_product)
    dataframe["log_ret"] = log_ret
    dataframe["bipower_sigma"] = sigma
    dataframe["jump_stat"] = (log_ret / sigma.where(sigma > 0)).replace([np.inf, -np.inf], np.nan)
    dataframe["hour"] = pd.to_datetime(dataframe["date"], utc=True).dt.hour.to_numpy()
    return dataframe


def daily_from_intraday(dataframe: DataFrame) -> DataFrame:
    """UTC daily closes from the 15m bars, on a gap-free calendar, with the 30-day simple mean."""
    dates = pd.to_datetime(dataframe["date"], utc=True)
    day = dates.dt.floor("D")
    daily_close = dataframe["close"].groupby(day.to_numpy()).last()
    daily_close.index = pd.DatetimeIndex(daily_close.index)
    if daily_close.index.tz is None:
        daily_close.index = daily_close.index.tz_localize("UTC")
    calendar = pd.date_range(daily_close.index.min(), daily_close.index.max(), freq="D")
    daily_close = daily_close.reindex(calendar)
    return DataFrame(
        {
            "date": calendar,
            "close": daily_close.to_numpy(dtype=float),
            "dsma": daily_close.rolling(DAILY_SMA_DAYS).mean().to_numpy(dtype=float),
        }
    )


class IntradayJumpContinuationStrong_H102_v1(IStrategy):
    """Buy a 4-sigma bipower-scaled 15m up-jump in a daily uptrend; flat by the UTC day close."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    use_exit_signal = True
    startup_candle_count = 3072

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = jump_indicators(dataframe)
        daily = daily_from_intraday(dataframe)
        dataframe = merge_informative_pair(dataframe, daily, self.timeframe, "1d", ffill=True)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        jump = dataframe["jump_stat"]
        log_ret = dataframe["log_ret"]
        close_1d = dataframe["close_1d"]
        dsma_1d = dataframe["dsma_1d"]
        cond = (
            jump.notna()
            & log_ret.notna()
            & close_1d.notna()
            & dsma_1d.notna()
            & dataframe["low"].notna()
            & (dataframe["bipower_sigma"] > 0)
            & (jump >= JUMP_THRESHOLD)
            & (log_ret >= MIN_BAR_LOG_RETURN)
            & (dataframe["hour"] >= 0)
            & (dataframe["hour"] <= ENTRY_LAST_HOUR)
            & (close_1d > dsma_1d)
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = [
                f"{TAG_PREFIX}|{float(value)!r}" for value in dataframe.loc[cond, "low"]
            ]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Both exits depend on the open trade (jump-bar low L, signal day): see custom_exit.
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """At most one entry per pair per UTC day, counting trades that were already closed."""
        if parse_tag(entry_tag) is None:
            return False
        today = utc_day(current_time)
        for trade in Trade.get_trades_proxy(pair=pair):
            if utc_day(trade.open_date_utc) == today:
                return False
        return True

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        jump_low = parse_tag(trade.enter_tag)
        if jump_low is not None:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if dataframe is not None and len(dataframe) > 0:
                # Closed bars u >= t+1: opened at or after the entry fill, fully closed by current_time.
                after = dataframe.loc[
                    (dataframe["date"] >= trade.open_date_utc) & (dataframe["date"] + BAR <= current_time)
                ]
                if not after.empty and after["volume"].iloc[-1] > 0:
                    after = after.loc[after["volume"] > 0]
                    if bool(np.any(after["close"].to_numpy(dtype=float) < jump_low)):
                        return "close_below_jump_low"
        # The 23:45 bar of the signal day has closed once a later UTC day has begun.
        if utc_day(current_time) > utc_day(trade.open_date_utc):
            return "time_exit_utc_day_close"
        return None
