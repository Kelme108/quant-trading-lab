"""H-123: Momentum Pinball on 4h UTC blocks (LBR/RSI(3) < 30), then a 15m first-hour-high breakout.

All times UTC, closed 15m bars only; a signal at the close of bar t fills at the open of bar t+1.
Long only, spot, one position per pair (engine), no pyramiding, no sizing hooks.

Blocks: 4h UTC blocks starting 00:00, 04:00, ..., 20:00; 16 bars each, numbered 1-16 by open time.
- C(k) = close of bar 16 of block k; x(k) = C(k) - C(k-1).
- LBR(k) = Wilder RSI(3) of the series x (not of price): up(k) = max(x(k) - x(k-1), 0),
  down(k) = max(x(k-1) - x(k), 0), Wilder averages (alpha = 1/3, recursive); LBR = 100 when avgDown = 0.
- LBR(k) is known at the close of bar 16 of block k and is forward-filled onto the bars of block k+1.
- SETUP: block k+1 is armed if LBR(k) < 30.
- OPENING RANGE of an armed block: ORH / ORL = max high / min low of bars 1-4. ORH/ORL are only visible
  from bar 5 on (they are NaN on bars 1-4), and only when all four opening bars exist.
- ENTRY: the first bar among bars 5-12 of the armed block whose close > ORH and whose
  ATR(14)/close >= 0.004 (Wilder ATR on 15m bars) gives the signal; fills at the next bar open E.
  Only that first qualifying bar carries a signal; confirm_trade_entry also refuses a second entry
  in a block that already had one (even after an exit).
  The entry tag records ORL.
- STOP: S = min(ORL, 0.99 * E), never below E * 0.95 (the 5% native backstop), fixed at entry and
  never moved; custom_stoploss returns it relative to the current rate. Native stoploss = -0.05.
- TAKE-PROFIT: exit when the gross price move reaches +1.5% (current rate, or the high of any closed
  bar since entry, touched E * 1.015); in custom_exit, so it fills at the following bar open.
- BLOCK-END LOSER EXIT: once the entry block has closed, if the close of its bar 16 < E, exit at the
  next bar open.
- TIME EXIT: at most 48 bars = 12h: exit at entry + 12h (the open after the bar stamped entry + 11h45m).
Whichever comes first applies.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

BAR = timedelta(minutes=15)
BLOCK = timedelta(hours=4)
BARS_PER_BLOCK = 16
LBR_ALPHA = 1.0 / 3.0
LBR_SETUP_THRESHOLD = 30.0
OPENING_RANGE_BARS = 4
ENTRY_FIRST_BAR = 5
ENTRY_LAST_BAR = 12
ATR_LENGTH = 14
MIN_ATR_OVER_CLOSE = 0.004
STOP_FRACTION_OF_ENTRY = 0.99
STOP_BACKSTOP = 0.05
TAKE_PROFIT = 0.015
MAX_HOLD = timedelta(hours=12)
TAG_PREFIX = "pinball_orl"


def as_utc(value) -> pd.Timestamp:
    """Timestamp in UTC (naive values are taken as UTC)."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")


def parse_tag(tag) -> float | None:
    """Opening-range low recorded in an entry tag, or None for a tag this strategy did not write."""
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


def stop_price(opening_range_low: float, entry_rate: float) -> float:
    """S = min(ORL, 0.99 * E), limited to the 5% backstop distance."""
    stop = min(opening_range_low, STOP_FRACTION_OF_ENTRY * entry_rate)
    return max(stop, entry_rate * (1.0 - STOP_BACKSTOP))


def lbr_series(block_close: pd.Series) -> pd.Series:
    """LBR per block: Wilder RSI(3) of the one-block close change x. Input is a gap-free block calendar."""
    x = block_close.diff()
    up = (x - x.shift(1)).clip(lower=0.0)
    down = (x.shift(1) - x).clip(lower=0.0)
    avg_up = up.ewm(alpha=LBR_ALPHA, adjust=False).mean()
    avg_down = down.ewm(alpha=LBR_ALPHA, adjust=False).mean()
    rs = avg_up / avg_down.where(avg_down > 0)
    lbr = 100.0 - 100.0 / (1.0 + rs)
    lbr = lbr.where(avg_down != 0, 100.0)
    return lbr.where(up.notna() & down.notna())


def pinball_indicators(dataframe: DataFrame) -> DataFrame:
    """Add bar_no, lbr_prev, or_high, or_low, atr, atr_pct. Backward-looking only."""
    dates = pd.to_datetime(dataframe["date"], utc=True)
    block = dates.dt.floor(BLOCK)
    bar_no = ((dates - block) // BAR) + 1
    dataframe["bar_no"] = bar_no.to_numpy()

    # Block closes C(k) on a gap-free block calendar, then LBR(k), then shifted one block forward.
    is_last_bar = bar_no == BARS_PER_BLOCK
    if len(dataframe) > 0:
        calendar = pd.date_range(block.min(), block.max(), freq=BLOCK)
        block_close = pd.Series(
            dataframe["close"].to_numpy(dtype=float)[is_last_bar.to_numpy()],
            index=pd.DatetimeIndex(block[is_last_bar]),
        )
        block_close = block_close[~block_close.index.duplicated(keep="last")].reindex(calendar)
        lbr_prev_by_block = lbr_series(block_close).shift(1)
        dataframe["lbr_prev"] = lbr_prev_by_block.reindex(pd.DatetimeIndex(block)).to_numpy(dtype=float)
    else:
        dataframe["lbr_prev"] = np.nan

    # Opening range: bars 1-4 of the block, visible only from bar 5 on and only if all four exist.
    in_range = bar_no <= OPENING_RANGE_BARS
    range_high = dataframe["high"].where(in_range)
    range_low = dataframe["low"].where(in_range)
    complete = range_high.groupby(block).transform("count") == OPENING_RANGE_BARS
    complete &= range_low.groupby(block).transform("count") == OPENING_RANGE_BARS
    visible = complete & (bar_no > OPENING_RANGE_BARS)
    dataframe["or_high"] = range_high.groupby(block).transform("max").where(visible)
    dataframe["or_low"] = range_low.groupby(block).transform("min").where(visible)

    # Wilder ATR(14) on true range.
    previous_close = dataframe["close"].shift(1)
    true_range = pd.concat(
        [
            dataframe["high"] - dataframe["low"],
            (dataframe["high"] - previous_close).abs(),
            (dataframe["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1, skipna=False)
    dataframe["atr"] = true_range.ewm(alpha=1.0 / ATR_LENGTH, adjust=False).mean()
    dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
    return dataframe


class MomentumPinballSession_H123_v1(IStrategy):
    """Buy the first-hour-high breakout of a 4h block that follows an oversold LBR/RSI(3) reading."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.05
    use_custom_stoploss = True
    use_exit_signal = True
    startup_candle_count = 1600

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return pinball_indicators(dataframe)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        bar_no = dataframe["bar_no"]
        candidate = (
            dataframe["lbr_prev"].notna()
            & dataframe["or_high"].notna()
            & dataframe["or_low"].notna()
            & dataframe["atr_pct"].notna()
            & dataframe["close"].notna()
            & (dataframe["lbr_prev"] < LBR_SETUP_THRESHOLD)
            & (bar_no >= ENTRY_FIRST_BAR)
            & (bar_no <= ENTRY_LAST_BAR)
            & (dataframe["close"] > dataframe["or_high"])
            & (dataframe["atr_pct"] >= MIN_ATR_OVER_CLOSE)
            & (dataframe["volume"] > 0)
        ).fillna(False)
        block = pd.to_datetime(dataframe["date"], utc=True).dt.floor(BLOCK)
        # Only the first qualifying bar of a block carries the signal (backward-looking running count).
        first_in_block = candidate & (candidate.astype(int).groupby(block).cumsum() == 1)
        if first_in_block.any():
            dataframe.loc[first_in_block, "enter_long"] = 1
            dataframe.loc[first_in_block, "enter_tag"] = [
                f"{TAG_PREFIX}|{float(value)!r}" for value in dataframe.loc[first_in_block, "or_low"]
            ]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # All exits depend on the open trade (entry rate, entry time): see custom_exit.
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """At most one entry per pair per 4h block, counting trades that were already closed."""
        if parse_tag(entry_tag) is None:
            return False
        from freqtrade.persistence import Trade

        this_block = as_utc(current_time).floor(BLOCK)
        for trade in Trade.get_trades_proxy(pair=pair):
            if as_utc(trade.open_date_utc).floor(BLOCK) == this_block:
                return False
        return True

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit,
                        after_fill=False, **kwargs):
        orl = parse_tag(trade.enter_tag)
        entry_rate = float(trade.open_rate)
        if orl is None or entry_rate <= 0 or not current_rate or current_rate <= 0:
            return None
        stop = stop_price(orl, entry_rate)
        relative = stop / float(current_rate) - 1.0
        # A stop at or above the current rate triggers on the next check.
        return min(relative, -1e-6)

    def _closed_bars(self, pair, current_time):
        """Fully closed 15m bars (open + 15m <= current_time) with their UTC open dates."""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return None
        dates = pd.to_datetime(dataframe["date"], utc=True)
        closed = dataframe.assign(_open=dates).loc[(dates + BAR) <= as_utc(current_time)]
        return closed

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        entry_time = as_utc(trade.open_date_utc)
        now = as_utc(current_time)
        entry_rate = float(trade.open_rate)

        # Take-profit: +1.5% gross, from the current rate or a closed bar's high since entry.
        if entry_rate > 0:
            if current_rate and float(current_rate) / entry_rate - 1.0 >= TAKE_PROFIT - 1e-9:
                return "take_profit"
            closed = self._closed_bars(pair, current_time)
            if closed is not None and not closed.empty:
                since_entry = closed.loc[closed["_open"] >= entry_time]
                since_entry = since_entry.loc[since_entry["volume"] > 0]
                if not since_entry.empty and bool(
                    (since_entry["high"].to_numpy(dtype=float) >= entry_rate * (1.0 + TAKE_PROFIT - 1e-9)).any()
                ):
                    return "take_profit"

            # Block-end loser: close of bar 16 of the entry block below the entry rate.
            block_start = entry_time.floor(BLOCK)
            if now >= block_start + BLOCK and closed is not None and not closed.empty:
                last_bar = closed.loc[closed["_open"] == block_start + BLOCK - BAR]
                if not last_bar.empty and last_bar["volume"].iloc[-1] > 0:
                    if float(last_bar["close"].iloc[-1]) < entry_rate:
                        return "block_end_loser"

        # Time exit: at most 48 bars (12h) held.
        if now >= entry_time + MAX_HOLD:
            return "time_exit_12h"
        return None
