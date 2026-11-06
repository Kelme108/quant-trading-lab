"""H-054: round-number stop cascade on 15m. Buy the first close through a fresh round level.

Closed 15m candles only; signals at bar close, fills at the next open. Spot long only.

Round grid (fixed per UTC day): P = close of the previous UTC day's 23:45 bar.
S = largest of {1, 2.5, 5} x 10^k with S <= 0.02 * P. Levels are integer multiples of S.

Entry at the close of bar t when all hold:
  (1) L = floor(close(t) / S) * S and close(t-1) < L
  (2) close(t) >= 1.002 * L
  (3) max(high) over bars t-32..t-1 < L (fresh level, bar t excluded)
  (4) close(t) > SMA(96) of closes (bar t included)
  (5) no position open (one position per pair, handled by the engine)
  (6) no earlier entry at the same L on the same UTC day (confirm_trade_entry; the signal day,
      L and S are recorded in the entry tag and checked against all trades of the pair).
Exits, whichever comes first:
  (a) take-profit at L + S, intrabar: custom_roi sets the ROI that corresponds to the price
      L + S; custom_exit also exits when the current rate (the open in backtests) is already
      at or above L + S.
  (b) stop at L - 0.5 * S, fixed at entry, intrabar (custom_stoploss), plus a 3% native backstop.
  (c) time exit at the open of the bar 32 bars after the entry bar (custom_exit).
No cooldown other than (6). Warm-up 400 bars.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy

BAR_MINUTES = 15
GRID_STEP_FRACTION = 0.02
GRID_MANTISSAS = (1.0, 2.5, 5.0)
BREAK_CONFIRMATION = 0.002
FRESHNESS_BARS = 32
TREND_SMA_BARS = 96
STOP_FRACTION_OF_STEP = 0.5
TIME_EXIT_BARS = 32
TAG_PREFIX = "rn"


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


def round_level_indicators(dataframe: DataFrame) -> DataFrame:
    """Grid step, level, freshness and trend columns. Backward-looking only."""
    dates = pd.to_datetime(dataframe["date"], utc=True)
    day = dates.dt.floor("D")
    close = dataframe["close"].astype(float)

    close_by_time = pd.Series(close.to_numpy(), index=pd.DatetimeIndex(dates))
    close_by_time = close_by_time[~close_by_time.index.duplicated(keep="last")]
    # The previous UTC day's 23:45 bar opens 15 minutes before today's 00:00.
    previous_bar_time = pd.DatetimeIndex(day) - pd.Timedelta(minutes=BAR_MINUTES)
    reference = close_by_time.reindex(previous_bar_time).to_numpy(dtype=float)

    dataframe["grid_ref"] = reference
    dataframe["grid_step"] = grid_step(dataframe["grid_ref"]).to_numpy()
    dataframe["grid_level"] = np.floor(close / dataframe["grid_step"]) * dataframe["grid_step"]
    dataframe["prev_close"] = close.shift(1)
    dataframe["fresh_high"] = dataframe["high"].rolling(FRESHNESS_BARS).max().shift(1)
    dataframe["sma_trend"] = close.rolling(TREND_SMA_BARS).mean()
    dataframe["signal_day"] = day.dt.strftime("%Y-%m-%d").to_numpy()
    return dataframe


def make_tag(day: str, level: float, step: float) -> str:
    return f"{TAG_PREFIX}|{day}|{level!r}|{step!r}"


def parse_tag(tag) -> tuple[float, float] | None:
    """(L, S) recorded in an entry tag, or None for a tag this strategy did not write."""
    if not isinstance(tag, str):
        return None
    parts = tag.split("|")
    if len(parts) != 4 or parts[0] != TAG_PREFIX:
        return None
    try:
        return float(parts[2]), float(parts[3])
    except ValueError:
        return None


class RoundNumberStopCascade_H054_v1(IStrategy):
    """First 15m close through a fresh round level above the 24h mean; target the next level."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    use_custom_stoploss = True
    use_custom_roi = True
    startup_candle_count = 400

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return round_level_indicators(dataframe)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"]
        level = dataframe["grid_level"]
        cond = (
            dataframe["grid_step"].notna()
            & level.notna()
            & dataframe["prev_close"].notna()
            & dataframe["fresh_high"].notna()
            & dataframe["sma_trend"].notna()
            & (level > 0)
            & (dataframe["prev_close"] < level)
            & (close >= (1.0 + BREAK_CONFIRMATION) * level)
            & (dataframe["fresh_high"] < level)
            & (close > dataframe["sma_trend"])
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            tags = [
                make_tag(d, float(lv), float(st))
                for d, lv, st in zip(
                    dataframe.loc[cond, "signal_day"],
                    dataframe.loc[cond, "grid_level"],
                    dataframe.loc[cond, "grid_step"],
                )
            ]
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = tags
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # All exits are per trade (take-profit, structural stop, time exit); no exit signal column.
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """Condition (6): one entry per level per UTC day. The tag holds the signal day and L."""
        if parse_tag(entry_tag) is None:
            return False
        for trade in Trade.get_trades_proxy(pair=pair):
            if trade.enter_tag == entry_tag:
                return False
        return True

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit,
                        after_fill=False, **kwargs):
        """Stop fixed at L - 0.5 * S, expressed relative to the current rate."""
        recorded = parse_tag(trade.enter_tag)
        if recorded is None or not current_rate:
            return None
        level, step = recorded
        stop_price = level - STOP_FRACTION_OF_STEP * step
        return max(1.0 - stop_price / current_rate, 0.0)

    def custom_roi(self, pair, trade, current_time, trade_duration, entry_tag, side, **kwargs):
        """ROI whose exit price is exactly L + S after the engine's fee adjustment."""
        recorded = parse_tag(trade.enter_tag)
        if recorded is None or not trade.open_rate:
            return None
        level, step = recorded
        target = level + step
        fee_open = trade.fee_open or 0.0
        fee_close = trade.fee_close or 0.0
        return (target * (1.0 - fee_close) - trade.open_rate * (1.0 + fee_open)) / trade.open_rate

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        recorded = parse_tag(trade.enter_tag)
        if recorded is not None:
            level, step = recorded
            if current_rate >= level + step:
                return "take_profit_next_level"
        if current_time >= trade.open_date_utc + timedelta(minutes=BAR_MINUTES * TIME_EXIT_BARS):
            return "time_exit_32_bars"
        return None
