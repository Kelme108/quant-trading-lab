"""H-067: Asian-session (00:00-06:45 UTC) range breakout at the European open on 15m, 1R target, flat by 12:00.

Closed 15m bars only, UTC clock; a signal at the close of bar t fills at the open of bar t+1.
Long only, spot, one position per pair (engine), no pyramiding, no sizing hooks, no cooldown.

Asian range of UTC day D: AH = max high, AL = min low of the 28 bars opening 00:00 .. 06:45. A bar counts as
present only if it has defined high/low and volume > 0 (Freqtrade fills gaps with zero-volume candles); if fewer
than 28 are present, day D is not armed. AH/AL are attached only to bars opening at or after 07:00, so every
value is built from bars that have already closed.
Daily filter: UTC daily candles built from the 15m bars, ATR14 = Wilder ATR(14) (SMA-seeded RMA, alpha 1/14)
of the daily true range, attached with merge_informative_pair (ffill), so day D sees the value at the close of
day D-1. Armed when 0.25 <= (AH - AL) / ATR14 <= 0.80.
Entry window: bars opening 07:00 .. 09:45. Scanning their closes in time order, the first close outside
[AL, AH] decides the day: if it is above AH, enter at that bar (fill at the next open, latest 10:00); if it is
below AL, no trade that day. Hence at most one entry signal per UTC day, so at most one trade per day.
Per trade (AL written into the entry tag):
- Stop at AL, intrabar (custom_stoploss); native 8% stoploss is only a backstop.
- Target T = fill + (fill - AL), intrabar (custom_roi at that price; custom_exit if the open is already >= T).
- Time exit: exit signal on the close of the 11:45 bar -> sell at the 12:00 open (custom_exit also exits at
  or after 12:00 of the entry day, in case the 11:45 bar has no volume).
Warm-up: 4320 bars (45 days).
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy, merge_informative_pair

ASIAN_BARS = 28
ASIAN_END_MINUTE = 7 * 60  # Asian bars open before 07:00
WINDOW_END_MINUTE = 10 * 60  # entry-window bars open 07:00 .. 09:45
TIME_EXIT_SIGNAL_MINUTE = 11 * 60 + 45  # exit signal on the close of the 11:45 bar
TIME_EXIT_HOUR = 12
ATR_DAYS = 14
MIN_RANGE_ATR = 0.25
MAX_RANGE_ATR = 0.80
TARGET_R = 1.0
BARS_PER_DAY = 96
TAG_PREFIX = "arlb"


def _recursive_smooth(values: np.ndarray, period: int, alpha: float) -> np.ndarray:
    """Seed with the mean of the first `period` defined values, then s = s + alpha * (x - s). Backward-only."""
    out = np.full(len(values), np.nan)
    defined = np.flatnonzero(~np.isnan(values))
    if len(defined) == 0:
        return out
    start = defined[0]
    seed_end = start + period - 1
    if seed_end >= len(values):
        return out
    state = float(np.mean(values[start : seed_end + 1]))
    out[seed_end] = state
    for i in range(seed_end + 1, len(values)):
        state = state + alpha * (values[i] - state)
        out[i] = state
    return out


def wilder(values: pd.Series, period: int) -> pd.Series:
    return pd.Series(
        _recursive_smooth(values.to_numpy(dtype=float), period, 1.0 / period), index=values.index
    )


def utc_day(value) -> pd.Timestamp:
    """UTC calendar day of a timestamp (naive timestamps are taken as UTC), tz-aware."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts.floor("D")


def daily_atr_from_intraday(dataframe: DataFrame) -> DataFrame:
    """UTC daily candles from the 15m bars and their Wilder ATR(14). A partial leading day is dropped."""
    dates = pd.to_datetime(dataframe["date"], utc=True)
    day = dates.dt.floor("D")
    grouped = dataframe[["high", "low", "close"]].astype(float).groupby(day)
    daily = DataFrame(
        {
            "high": grouped["high"].max(),
            "low": grouped["low"].min(),
            "close": grouped["close"].last(),
            "bars": grouped["close"].size(),
        }
    )
    if len(daily) > 0 and daily["bars"].iloc[0] < BARS_PER_DAY:
        daily = daily.iloc[1:]
    index = pd.DatetimeIndex(daily.index)
    if index.tz is None:
        index = index.tz_localize("UTC")
    daily = daily.reset_index(drop=True)
    prev_close = daily["close"].shift(1)
    tr = pd.concat(
        [
            daily["high"] - daily["low"],
            (daily["high"] - prev_close).abs(),
            (daily["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    tr[prev_close.isna()] = np.nan
    atr = wilder(tr, ATR_DAYS)
    return DataFrame({"date": index, "atr": atr.to_numpy(dtype=float)})


def asian_range(dataframe: DataFrame) -> DataFrame:
    """AH/AL of the day's 28 Asian bars, attached only to bars opening at or after 07:00 of that day."""
    dates = pd.to_datetime(dataframe["date"], utc=True)
    day = dates.dt.floor("D")
    minute = (dates.dt.hour * 60 + dates.dt.minute).to_numpy()
    asian = pd.Series(minute < ASIAN_END_MINUTE, index=dataframe.index)
    present = asian & dataframe["high"].notna() & dataframe["low"].notna() & (dataframe["volume"] > 0)
    high = dataframe["high"].astype(float).where(present)
    low = dataframe["low"].astype(float).where(present)
    count = present.astype(int).groupby(day).transform("sum")
    day_high = high.groupby(day).transform("max")
    day_low = low.groupby(day).transform("min")
    usable = pd.Series(minute >= ASIAN_END_MINUTE, index=dataframe.index) & (count == ASIAN_BARS)
    dataframe["asian_high"] = day_high.where(usable)
    dataframe["asian_low"] = day_low.where(usable)
    dataframe["minute_of_day"] = minute
    return dataframe


def make_tag(asian_low: float) -> str:
    return f"{TAG_PREFIX}|{float(asian_low)!r}"


def parse_tag(tag) -> float | None:
    """AL recorded in an entry tag, or None for a tag this strategy did not write."""
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


class AsianRangeLondonBreakout_H067_v1(IStrategy):
    """First 07:00-09:45 close above the Asian high (width-filtered by daily ATR); stop AL, 1R target, out 12:00."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.08
    use_custom_stoploss = True
    use_custom_roi = True
    use_exit_signal = True
    trailing_stop = False
    startup_candle_count = 4320

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = asian_range(dataframe)
        daily = daily_atr_from_intraday(dataframe)
        dataframe = merge_informative_pair(dataframe, daily, self.timeframe, "1d", ffill=True)
        width = dataframe["asian_high"] - dataframe["asian_low"]
        atr = dataframe["atr_1d"]
        dataframe["range_atr_ratio"] = (width / atr.where(atr > 0)).replace([np.inf, -np.inf], np.nan)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dates = pd.to_datetime(dataframe["date"], utc=True)
        day = dates.dt.floor("D")
        minute = dataframe["minute_of_day"]
        window = (minute >= ASIAN_END_MINUTE) & (minute < WINDOW_END_MINUTE)
        close = dataframe["close"]
        ah = dataframe["asian_high"]
        al = dataframe["asian_low"]
        above = (window & ah.notna() & close.notna() & (close > ah)).fillna(False)
        below = (window & al.notna() & close.notna() & (close < al)).fillna(False)
        breaks = (above | below).astype(int)
        # Breaks on earlier window bars of the same day (cumulative sum looks backwards only).
        prior_breaks = breaks.groupby(day).cumsum() - breaks
        ratio = dataframe["range_atr_ratio"]
        cond = (
            above
            & (prior_breaks == 0)
            & ah.notna()
            & al.notna()
            & (al > 0)
            & dataframe["atr_1d"].notna()
            & ratio.notna()
            & (ratio >= MIN_RANGE_ATR)
            & (ratio <= MAX_RANGE_ATR)
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = [make_tag(value) for value in dataframe.loc[cond, "asian_low"]]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Close of the 11:45 bar -> sell at the 12:00 open. Stop and target are per trade (custom_*).
        cond = (
            (dataframe["minute_of_day"] == TIME_EXIT_SIGNAL_MINUTE)
            & dataframe["close"].notna()
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "exit_long"] = 1
        return dataframe

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit,
                        after_fill=False, **kwargs):
        """Stop price AL, fixed for the trade, expressed relative to the current rate."""
        asian_low = parse_tag(trade.enter_tag)
        if asian_low is None or not current_rate:
            return None
        return max(1.0 - asian_low / current_rate, 0.0)

    def _target(self, trade) -> float | None:
        asian_low = parse_tag(trade.enter_tag)
        if asian_low is None or not trade.open_rate:
            return None
        risk = trade.open_rate - asian_low
        if risk <= 0:
            return None
        return trade.open_rate + TARGET_R * risk

    def custom_roi(self, pair, trade, current_time, trade_duration, entry_tag, side, **kwargs):
        """ROI whose exit price is exactly T = fill + (fill - AL) after the engine's fee adjustment."""
        target = self._target(trade)
        if target is None:
            return None
        fee_open = trade.fee_open or 0.0
        fee_close = trade.fee_close or 0.0
        return (target * (1.0 - fee_close) - trade.open_rate * (1.0 + fee_open)) / trade.open_rate

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        target = self._target(trade)
        if target is not None and current_rate >= target:
            return "target_1r"
        if pd.Timestamp(current_time) >= utc_day(trade.open_date_utc) + timedelta(hours=TIME_EXIT_HOUR):
            return "time_exit_1200_utc"
        return None
