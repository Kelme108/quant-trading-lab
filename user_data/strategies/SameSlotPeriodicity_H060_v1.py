"""H-060: same-time-of-day periodicity on UTC 4-hour blocks, 1h chart.

Each UTC day has six 4-hour blocks b = 0..5 (00, 04, 08, 12, 16, 20 UTC), four 1h bars each.
Block return R(d, b) = close of the bar opening at hh+3 / open of the bar opening at hh, minus 1, defined only if
all four bars of the block exist (otherwise missing).

Daily selection for day d (fixed at the close of the 23:00 bar of day d-1): for each block, M(b) = mean of R over
the 28 completed days d-1 .. d-28 and the count of those returns > 0. A block with any missing return in the window
is not eligible. b* = eligible block with the largest M (ties -> earliest block).
Entry: M(b*) >= 0.0040 and positive count >= 16 of 28 -> enter signal at the close of the bar opening at hh-1 (for
block 0, the 23:00 bar of day d-1), filled at the open of the block's first bar.
Exit: exit signal at the close of the block's 4th bar (opening at hh+3), so the hold is 4 bars.
Stop: fixed 3% native stop-loss. No take-profit, no trailing, no other filters. At most one entry per UTC day
(one selected block per day).

Everything is computed from bars at or before the signal bar: block returns use shift(1..3) only, the 28-day window
ends at day d-1 (daily shift(1)), and "the next bar opens a block" is calendar arithmetic on the bar's own timestamp.
"""

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

BLOCK_HOURS = 4
N_BLOCKS = 6
LOOKBACK_DAYS = 28
MIN_MEAN_BLOCK_RETURN = 0.0040
MIN_POSITIVE_COUNT = 16


def _bar_times(dataframe: DataFrame) -> pd.Series:
    return pd.to_datetime(dataframe["date"], utc=True)


def daily_selection(dataframe: DataFrame) -> DataFrame:
    """Per UTC day d: selected block b* (NaN if no block passes), its trailing mean and positive count.

    The table covers every calendar day from the first bar's day to the day after the last bar's day, so the
    selection for the next day is available at the close of the last 23:00 bar.
    """
    date = _bar_times(dataframe)
    hour = date.dt.hour
    day = date.dt.floor("D")

    complete = (hour % BLOCK_HOURS) == (BLOCK_HOURS - 1)
    for k in range(1, BLOCK_HOURS):
        complete = complete & (date.shift(k) == date - pd.Timedelta(hours=k))
    block_ret = dataframe["close"] / dataframe["open"].shift(BLOCK_HOURS - 1) - 1.0
    complete = complete & block_ret.notna()

    columns = ["slot_block", "slot_mean", "slot_poscount"]
    if len(dataframe) == 0:
        return DataFrame(columns=columns, dtype=float)

    days = pd.date_range(day.min(), day.max() + pd.Timedelta(days=1), freq="D")
    table = DataFrame(
        {"day": day[complete], "block": (hour[complete] // BLOCK_HOURS).astype(int), "ret": block_ret[complete]}
    )
    if len(table) == 0:
        returns = DataFrame(np.nan, index=days, columns=range(N_BLOCKS))
    else:
        returns = table.groupby(["day", "block"])["ret"].last().unstack("block")
        returns = returns.reindex(index=days, columns=range(N_BLOCKS))

    # Window of the 28 completed days d-1 .. d-28; any missing day/block gives NaN (not eligible).
    mean = returns.rolling(LOOKBACK_DAYS).mean().shift(1)
    positive = (returns > 0).astype(float).where(returns.notna())
    poscount = positive.rolling(LOOKBACK_DAYS).sum().shift(1)

    mean_arr = mean.to_numpy(dtype=float)
    pos_arr = poscount.to_numpy(dtype=float)
    eligible_any = ~np.all(np.isnan(mean_arr), axis=1)
    best = np.argmax(np.where(np.isnan(mean_arr), -np.inf, mean_arr), axis=1)  # first max -> earliest block
    rows = np.arange(len(mean_arr))
    best_mean = mean_arr[rows, best]
    best_pos = pos_arr[rows, best]
    passes = (
        eligible_any
        & ~np.isnan(best_mean)
        & ~np.isnan(best_pos)
        & (best_mean >= MIN_MEAN_BLOCK_RETURN)
        & (best_pos >= MIN_POSITIVE_COUNT)
    )
    return DataFrame(
        {
            "slot_block": np.where(passes, best.astype(float), np.nan),
            "slot_mean": np.where(eligible_any, best_mean, np.nan),
            "slot_poscount": np.where(eligible_any, best_pos, np.nan),
        },
        index=days,
    )


class SameSlotPeriodicity_H060_v1(IStrategy):
    """Hold the UTC 4-hour block with the strongest trailing 28-day same-block return."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    trailing_stop = False
    startup_candle_count = 720

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        selection = daily_selection(dataframe)
        date = _bar_times(dataframe)
        next_open = date + pd.Timedelta(hours=1)
        target_day = next_open.dt.floor("D")
        today = date.dt.floor("D")

        # Selection for the day the next bar belongs to (known at this bar's close).
        dataframe["slot_next_block"] = selection["slot_block"].reindex(target_day).to_numpy()
        dataframe["slot_next_mean"] = selection["slot_mean"].reindex(target_day).to_numpy()
        dataframe["slot_next_poscount"] = selection["slot_poscount"].reindex(target_day).to_numpy()
        # Selection for the current bar's own day (used by the time exit).
        dataframe["slot_today_block"] = selection["slot_block"].reindex(today).to_numpy()
        dataframe["slot_next_bar_block"] = (next_open.dt.hour // BLOCK_HOURS).astype(float)
        dataframe["slot_next_bar_starts_block"] = (next_open.dt.hour % BLOCK_HOURS == 0).astype(int)
        dataframe["slot_bar_block"] = (date.dt.hour // BLOCK_HOURS).astype(float)
        dataframe["slot_bar_ends_block"] = (date.dt.hour % BLOCK_HOURS == BLOCK_HOURS - 1).astype(int)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        entry = (
            dataframe["slot_next_block"].notna()
            & (dataframe["slot_next_bar_starts_block"] == 1)
            & (dataframe["slot_next_bar_block"] == dataframe["slot_next_block"])
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[entry, ["enter_long", "enter_tag"]] = (1, "same_slot_block")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        leave = (
            dataframe["slot_today_block"].notna()
            & (dataframe["slot_bar_ends_block"] == 1)
            & (dataframe["slot_bar_block"] == dataframe["slot_today_block"])
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[leave, ["exit_long", "exit_tag"]] = (1, "same_slot_block_end")
        return dataframe
