"""H-056: round-number support bounce on 15m. Buy a rejection of a round level after a decline into it.

Closed 15m candles only; signals at the close of bar t, fills at the open of bar t+1. Spot long only.

Round grid (fixed per UTC day): P = close of the previous UTC day's 23:45 bar.
S = largest of {1, 2.5, 5} x 10^k with S <= 0.02 * P. Levels are integer multiples of S.
Level at bar t: L = the multiple of S with 0.996 * L <= low(t) <= 1.001 * L (none -> no signal).

Entry at the close of bar t when all hold:
  (1) DECLINE INTO LEVEL: max(high of bars t-32..t-1) >= 1.012 * L
  (2) TOUCH WITHOUT BREAK: 0.996 * L <= low(t) <= 1.001 * L and min(close of bars t-32..t-1) >= L
  (3) REJECTION: close(t) >= 1.002 * L
  (4) no position open (one position per pair, handled by the engine)
  (5) one trade per level per UTC day (confirm_trade_entry; the signal day and L are recorded in
      the entry tag and checked against all trades of the pair).
L is recorded in the entry tag and fixed for the trade.
Exits, whichever comes first:
  (a) take-profit at entry_fill * 1.010, intrabar via custom_roi; custom_exit also exits at the
      open when the bar opens at or above that price.
  (b) a closed bar u after the entry fill with close < 0.993 * L -> exit at the open of bar u+1.
  (c) native intrabar stop 1.5% below the entry fill (stoploss = -0.015).
  (d) time exit at the open of bar e+24 (entry filled at the open of bar e).
No cooldown other than (5), no other filters. Warm-up 200 bars.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy

BAR_MINUTES = 15
BAR = timedelta(minutes=BAR_MINUTES)
GRID_STEP_FRACTION = 0.02
GRID_MANTISSAS = (1.0, 2.5, 5.0)
DECLINE_LOOKBACK_BARS = 32
DECLINE_MIN_ABOVE_LEVEL = 1.012
TOUCH_LOW_LOWER = 0.996
TOUCH_LOW_UPPER = 1.001
REJECTION_CLOSE_MIN = 1.002
TAKE_PROFIT = 0.010
LEVEL_BREAK_CLOSE_RATIO = 0.993
TIME_EXIT_BARS = 24
TAG_PREFIX = "rnsb"


def grid_step(reference: pd.Series) -> pd.Series:
    """Largest 1/2.5/5 x 10^k that is <= 0.02 * reference (NaN where the reference is undefined)."""
    target = (GRID_STEP_FRACTION * reference.astype(float)).to_numpy()
    valid = np.isfinite(target) & (target > 0)
    exponent = np.full(target.shape, np.nan)
    exponent[valid] = np.floor(np.log10(target[valid]))
    best = np.full(target.shape, np.nan)
    # Check the neighbouring exponents too, so a rounding error in log10 cannot pick the wrong decade.
    for shift in (-1.0, 0.0, 1.0):
        power = np.power(10.0, exponent + shift)
        for mantissa in GRID_MANTISSAS:
            candidate = mantissa * power
            better = valid & (candidate <= target) & ~(candidate <= best)
            best = np.where(better, candidate, best)
    return pd.Series(best, index=reference.index)


def touched_level(low: pd.Series, step: pd.Series) -> pd.Series:
    """The multiple L of the step with 0.996 * L <= low <= 1.001 * L, NaN if there is none."""
    low_values = low.astype(float).to_numpy()
    step_values = step.astype(float).to_numpy()
    valid = np.isfinite(low_values) & np.isfinite(step_values) & (step_values > 0)
    base = np.full(low_values.shape, np.nan)
    base[valid] = np.floor(low_values[valid] / (TOUCH_LOW_LOWER * step_values[valid]))
    level = np.full(low_values.shape, np.nan)
    # Test the neighbouring multiples too, so a floating-point error in the division cannot miss L.
    for offset in (-1.0, 0.0, 1.0):
        candidate = (base + offset) * step_values
        hit = (
            valid
            & np.isnan(level)
            & (candidate > 0)
            & (TOUCH_LOW_LOWER * candidate <= low_values)
            & (low_values <= TOUCH_LOW_UPPER * candidate)
        )
        level = np.where(hit, candidate, level)
    return pd.Series(level, index=low.index)


def make_tag(day: str, level: float) -> str:
    return f"{TAG_PREFIX}|{day}|{level!r}"


def parse_tag(tag) -> float | None:
    """L recorded in an entry tag, or None for a tag this strategy did not write."""
    if not isinstance(tag, str):
        return None
    parts = tag.split("|")
    if len(parts) != 3 or parts[0] != TAG_PREFIX:
        return None
    try:
        return float(parts[2])
    except ValueError:
        return None


class RoundNumberSupportBounce_H056_v1(IStrategy):
    """Buy a 15m bar that dips into a round level after an 8-hour decline and closes back above it."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.015
    trailing_stop = False
    use_custom_roi = True
    startup_candle_count = 200

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dates = pd.to_datetime(dataframe["date"], utc=True)
        day = dates.dt.floor("D")
        close = dataframe["close"].astype(float)
        high = dataframe["high"].astype(float)

        close_by_time = pd.Series(close.to_numpy(), index=pd.DatetimeIndex(dates))
        close_by_time = close_by_time[~close_by_time.index.duplicated(keep="last")]
        # The previous UTC day's 23:45 bar opens 15 minutes before today's 00:00.
        previous_bar_time = pd.DatetimeIndex(day) - pd.Timedelta(minutes=BAR_MINUTES)
        reference = close_by_time.reindex(previous_bar_time).to_numpy(dtype=float)

        dataframe["grid_ref"] = reference
        dataframe["grid_step"] = grid_step(dataframe["grid_ref"]).to_numpy()
        dataframe["touch_level"] = touched_level(dataframe["low"], dataframe["grid_step"]).to_numpy()
        # Bars t-32..t-1 (bar t excluded).
        dataframe["prior_high"] = high.rolling(DECLINE_LOOKBACK_BARS).max().shift(1)
        dataframe["prior_min_close"] = close.rolling(DECLINE_LOOKBACK_BARS).min().shift(1)
        dataframe["signal_day"] = day.dt.strftime("%Y-%m-%d").to_numpy()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        low = dataframe["low"]
        level = dataframe["touch_level"]
        cond = (
            dataframe["grid_step"].notna()
            & level.notna()
            & dataframe["prior_high"].notna()
            & dataframe["prior_min_close"].notna()
            & close.notna()
            & (level > 0)
            & (dataframe["prior_high"] >= DECLINE_MIN_ABOVE_LEVEL * level)
            & (TOUCH_LOW_LOWER * level <= low)
            & (low <= TOUCH_LOW_UPPER * level)
            & (dataframe["prior_min_close"] >= level)
            & (close >= REJECTION_CLOSE_MIN * level)
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            tags = [
                make_tag(d, float(lv))
                for d, lv in zip(dataframe.loc[cond, "signal_day"], dataframe.loc[cond, "touch_level"])
            ]
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = tags
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # All exits depend on per-trade state (entry fill, L, entry bar); handled per trade.
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """Condition (5): one entry per level per UTC day. The tag holds the signal day and L."""
        if parse_tag(entry_tag) is None:
            return False
        for trade in Trade.get_trades_proxy(pair=pair):
            if trade.enter_tag == entry_tag:
                return False
        return True

    def custom_roi(self, pair, trade, current_time, trade_duration, entry_tag, side, **kwargs):
        """ROI whose exit price is exactly entry_fill * 1.010 after the engine's fee adjustment."""
        if not trade.open_rate:
            return None
        target = trade.open_rate * (1.0 + TAKE_PROFIT)
        fee_open = trade.fee_open or 0.0
        fee_close = trade.fee_close or 0.0
        return (target * (1.0 - fee_close) - trade.open_rate * (1.0 + fee_open)) / trade.open_rate

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        if trade.open_rate and current_rate >= trade.open_rate * (1.0 + TAKE_PROFIT):
            return "take_profit_1pct"
        level = parse_tag(trade.enter_tag)
        if level is not None:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if dataframe is not None and len(dataframe) > 0:
                closed = dataframe[dataframe["date"] + BAR <= current_time]
                if len(closed) > 0:
                    last = closed.iloc[-1]
                    if (
                        last["date"] >= trade.open_date_utc
                        and last["volume"] > 0
                        and last["close"] == last["close"]
                        and last["close"] < LEVEL_BREAK_CLOSE_RATIO * level
                    ):
                        return "level_break_exit"
        if current_time >= trade.open_date_utc + BAR * TIME_EXIT_BARS:
            return "time_exit_24_bars"
        return None
