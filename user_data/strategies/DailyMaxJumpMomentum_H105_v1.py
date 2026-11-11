"""H-105: two-hour MAX-jump regime breakout on 1h candles (long only), flat within 12h / by 23:00 UTC.

Chart 1h, closed bars only, all times UTC; a signal at a bar close is filled at the next 1h open.
Blocks: two-hour blocks aligned to even UTC hours; block b = the bar opening at even hour H plus the
bar opening at H+1. C(b) = close of the H+1 bar; a block exists only when both bars exist. Block values
are computed at the close of the odd-hour bar and forward-filled on the next bar.

On block closes: r(b) = C(b)/C(b-1) - 1; J(b) = max r over blocks b-29..b;
regime ON when J(b) >= median of J(b-150)..J(b-1); SMA50 / SMA20 of C; HH10(b) = max C(b-10..b-1).
Entry (at a block close): regime ON, C > SMA50, C > HH10, the next block opens 00:00..16:00 UTC.
Exit, first of: (a) block close with C < SMA20; (b) session: the 22:00 bar's close raises the exit,
sell at the 23:00 open; (c) 12 hours after the entry fill (custom_exit); (d) native 2% stop.
Cooldown 6 candles after any exit (CooldownPeriod). No take-profit.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

MAX_WINDOW_BLOCKS = 30
MEDIAN_WINDOW_BLOCKS = 150
TREND_SMA_BLOCKS = 50
BREAKOUT_BLOCKS = 10
EXIT_SMA_BLOCKS = 20
SESSION_EXIT_SIGNAL_HOUR = 22  # the 22:00 bar's close raises the exit; sold at the 23:00 open
MAX_HOLD = timedelta(hours=12)
ENTRY_FILL_LAST_HOUR = 16  # next block opens between 00:00 and 16:00 inclusive


def block_indicators(dataframe: DataFrame) -> DataFrame:
    """Add block columns. Everything looks backwards only."""
    date = pd.to_datetime(dataframe["date"], utc=True)
    index = pd.DatetimeIndex(date)
    hour = index.hour
    is_odd = np.asarray(hour % 2 == 1)
    has_even_partner = np.asarray((index - pd.Timedelta(hours=1)).isin(index))
    block_start = index.floor("2h")

    dataframe["hour_utc"] = np.asarray(hour)
    complete = is_odd & has_even_partner  # odd-hour bar whose block has both bars

    close = pd.Series(dataframe["close"].to_numpy(dtype=float), index=index)
    block_close_known = close[complete]
    block_close_known.index = block_start[complete]
    block_close_known = block_close_known[~block_close_known.index.duplicated(keep="last")]
    if len(block_close_known) == 0:
        for name in ("block_close", "block_J", "block_J_median", "sma50", "sma20", "hh10"):
            dataframe[name] = np.nan
        dataframe["block_end"] = False
        return dataframe

    calendar = pd.date_range(block_close_known.index.min(), block_close_known.index.max(), freq="2h")
    c = block_close_known.reindex(calendar)  # missing blocks stay NaN, so windows touching them are NaN
    r = c / c.shift(1) - 1.0
    j = r.rolling(MAX_WINDOW_BLOCKS).max()
    j_median = j.shift(1).rolling(MEDIAN_WINDOW_BLOCKS).median()
    sma50 = c.rolling(TREND_SMA_BLOCKS).mean()
    sma20 = c.rolling(EXIT_SMA_BLOCKS).mean()
    hh10 = c.shift(1).rolling(BREAKOUT_BLOCKS).max()

    # Latest completed block for every row: the row's own block on an odd bar (complete),
    # the previous block (held) on an even bar.
    key = block_start.where(is_odd, block_start - pd.Timedelta(hours=2))
    for name, series in (
        ("block_close", c),
        ("block_J", j),
        ("block_J_median", j_median),
        ("sma50", sma50),
        ("sma20", sma20),
        ("hh10", hh10),
    ):
        dataframe[name] = series.reindex(key).to_numpy(dtype=float)
    dataframe["block_end"] = complete & np.isfinite(dataframe["block_close"].to_numpy(dtype=float))
    return dataframe


class DailyMaxJumpMomentum_H105_v1(IStrategy):
    """Buy a fresh 10-block closing high after a large recent 2h jump; flat by 23:00 UTC or 12h."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.02
    use_exit_signal = True
    startup_candle_count = 400

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 6}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return block_indicators(dataframe)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        hour = dataframe["hour_utc"]
        fill_hour = (hour + 1) % 24  # open of the next block
        cond = (
            dataframe["block_end"]
            & dataframe["block_close"].notna()
            & dataframe["block_J"].notna()
            & dataframe["block_J_median"].notna()
            & dataframe["sma50"].notna()
            & dataframe["hh10"].notna()
            & (dataframe["block_J"] >= dataframe["block_J_median"])
            & (dataframe["block_close"] > dataframe["sma50"])
            & (dataframe["block_close"] > dataframe["hh10"])
            & (fill_hour <= ENTRY_FILL_LAST_HOUR)
            & (dataframe["volume"] > 0)
        ).fillna(False)
        dataframe.loc[cond, ["enter_long", "enter_tag"]] = (1, "max_jump_breakout")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        volume_ok = dataframe["volume"] > 0
        below_sma20 = (
            dataframe["block_end"]
            & dataframe["block_close"].notna()
            & dataframe["sma20"].notna()
            & (dataframe["block_close"] < dataframe["sma20"])
        ).fillna(False)
        session = dataframe["hour_utc"] == SESSION_EXIT_SIGNAL_HOUR
        dataframe.loc[below_sma20 & volume_ok, ["exit_long", "exit_tag"]] = (1, "close_below_sma20")
        dataframe.loc[session & volume_ok & ~below_sma20, ["exit_long", "exit_tag"]] = (
            1,
            "session_flat_2300",
        )
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        """12-hour time exit: sold at the open 12 hours after the entry fill (fill time floored to the hour)."""
        opened = pd.Timestamp(trade.open_date_utc)
        now = pd.Timestamp(current_time)
        if opened.tzinfo is None:
            opened = opened.tz_localize("UTC")
        if now.tzinfo is None:
            now = now.tz_localize("UTC")
        if now >= opened.floor("h") + MAX_HOLD:
            return "time_exit_12h"
        return None
