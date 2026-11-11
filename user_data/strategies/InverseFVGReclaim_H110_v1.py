"""H-110: 15m inverse fair value gap reclaim (research/proposals/H-110.json).

Closed 15m bars only, UTC, long only, spot. A signal at the close of bar t fills at the open of bar t+1.

- GAP at the close of bar k: bearish FVG when high(k) < low(k-2). GT = low(k-2), GB = high(k).
  Valid only if (GT-GB)/GB >= 0.004 and the middle bar k-1 is a down displacement:
  close(k-1) < open(k-1) and open(k-1)/close(k-1) - 1 >= 0.01.
  Only the most recent valid gap is tracked; a new valid gap replaces the old one.
- INVERSION: first bar t in k+1..k+24 with close(t) > GT and close(t) > open(t). The gap is consumed there
  (one entry per gap); a gap with no such bar by k+24 is dropped. At bar t the existing gap is tested first,
  then a gap that forms at t becomes the tracked one.
- RISK FILTER: SL = lowest low of bars k-2..t, R = close(t) - SL, trade only if 0.008 <= R/close(t) <= 0.03.
- ENTRY: open(t+1), only if flat (engine), fewer than 3 entries on the pair this UTC day and open(t+1) > SL
  (confirm_trade_entry). The entry tag records SL and TP = close(t) + 1.5 R.
- STOP: fixed price SL frozen at entry (custom_stoploss); native stoploss -0.035 is the backstop.
- TAKE PROFIT: custom_exit when the rate reaches TP. TIME EXIT: 48 bars (12 h) after the entry bar open.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

MIN_GAP_PCT = 0.004
MIN_DISPLACEMENT_BODY_PCT = 0.01
INVERSION_WINDOW_BARS = 24
MIN_RISK_PCT = 0.008
MAX_RISK_PCT = 0.03
TARGET_R_MULTIPLE = 1.5
TIME_EXIT_BARS = 48
BAR = timedelta(minutes=15)
MAX_ENTRIES_PER_DAY = 3
TAG_PREFIX = "ifvg"


def utc_day(value) -> pd.Timestamp:
    """UTC calendar day of a timestamp (naive timestamps are taken as UTC)."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return ts.floor("D")


def make_tag(stop_price: float, take_profit: float) -> str:
    return f"{TAG_PREFIX}|{float(stop_price)!r}|{float(take_profit)!r}"


def parse_tag(tag):
    """(SL, TP) recorded in an entry tag, or None for a tag this strategy did not write."""
    if not isinstance(tag, str):
        return None
    parts = tag.split("|")
    if len(parts) != 3 or parts[0] != TAG_PREFIX:
        return None
    try:
        stop_price = float(parts[1])
        take_profit = float(parts[2])
    except ValueError:
        return None
    if not (np.isfinite(stop_price) and np.isfinite(take_profit)):
        return None
    if stop_price <= 0 or take_profit <= stop_price:
        return None
    return stop_price, take_profit


def inverse_fvg_signals(dataframe: DataFrame) -> DataFrame:
    """Add ifvg_signal (bool), ifvg_sl and ifvg_tp. Looks backwards only (sequential state machine)."""
    open_ = dataframe["open"].to_numpy(dtype=float)
    high = dataframe["high"].to_numpy(dtype=float)
    low = dataframe["low"].to_numpy(dtype=float)
    close = dataframe["close"].to_numpy(dtype=float)
    volume = dataframe["volume"].to_numpy(dtype=float)
    n = len(dataframe)

    signal = np.zeros(n, dtype=bool)
    sl_out = np.full(n, np.nan)
    tp_out = np.full(n, np.nan)

    gap_k = -1
    gap_top = np.nan
    swing_low = np.nan

    for t in range(n):
        # 1) inversion test of the gap tracked from earlier bars (k < t)
        if gap_k >= 0:
            if t - gap_k > INVERSION_WINDOW_BARS:
                gap_k = -1
            else:
                swing_low = min(swing_low, low[t]) if np.isfinite(low[t]) else swing_low
                if (
                    np.isfinite(close[t])
                    and np.isfinite(open_[t])
                    and close[t] > gap_top
                    and close[t] > open_[t]
                ):
                    # first qualifying bar: the gap is consumed whether or not a trade follows
                    risk = close[t] - swing_low
                    ok = (
                        np.isfinite(risk)
                        and np.isfinite(volume[t])
                        and volume[t] > 0
                        and MIN_RISK_PCT <= risk / close[t] <= MAX_RISK_PCT
                    )
                    if ok:
                        signal[t] = True
                        sl_out[t] = swing_low
                        tp_out[t] = close[t] + TARGET_R_MULTIPLE * risk
                    gap_k = -1

        # 2) a bearish gap closing at bar t replaces any tracked gap
        if t >= 2:
            window_ok = np.isfinite(
                [high[t], low[t - 2], low[t - 1], open_[t - 1], close[t - 1], low[t]]
            ).all()
            if window_ok and high[t] < low[t - 2]:
                gap_top_new = low[t - 2]
                gap_bottom = high[t]
                gap_pct = (gap_top_new - gap_bottom) / gap_bottom if gap_bottom > 0 else np.nan
                body_ok = (
                    close[t - 1] > 0
                    and close[t - 1] < open_[t - 1]
                    and open_[t - 1] / close[t - 1] - 1.0 >= MIN_DISPLACEMENT_BODY_PCT
                )
                if np.isfinite(gap_pct) and gap_pct >= MIN_GAP_PCT and body_ok:
                    gap_k = t
                    gap_top = gap_top_new
                    swing_low = min(low[t - 2], low[t - 1], low[t])

    dataframe["ifvg_signal"] = signal
    dataframe["ifvg_sl"] = sl_out
    dataframe["ifvg_tp"] = tp_out
    return dataframe


class InverseFVGReclaim_H110_v1(IStrategy):
    """Buy the first bullish close back above a bearish displacement gap; SL swing low, TP 1.5R, 12h cap."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.035
    use_custom_stoploss = True
    use_exit_signal = True
    startup_candle_count = 30

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return inverse_fvg_signals(dataframe)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (
            dataframe["ifvg_signal"].astype(bool)
            & dataframe["ifvg_sl"].notna()
            & dataframe["ifvg_tp"].notna()
            & dataframe["close"].notna()
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = [
                make_tag(sl, tp)
                for sl, tp in zip(dataframe.loc[cond, "ifvg_sl"], dataframe.loc[cond, "ifvg_tp"])
            ]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Take profit and time exit depend on the open trade: see custom_exit.
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """Entry only above SL, and fewer than 3 entries on the pair in the current UTC day."""
        from freqtrade.persistence import Trade

        levels = parse_tag(entry_tag)
        if levels is None:
            return False
        if not rate > levels[0]:
            return False
        today = utc_day(current_time)
        opened_today = 0
        for trade in Trade.get_trades_proxy(pair=pair):
            if utc_day(trade.open_date_utc) == today:
                opened_today += 1
        return opened_today < MAX_ENTRIES_PER_DAY

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        """Fixed price stop SL frozen at entry, expressed relative to the current rate."""
        levels = parse_tag(trade.enter_tag)
        if levels is None or not current_rate > 0:
            return None
        distance = levels[0] / current_rate - 1.0
        return min(distance, -0.0001)

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        levels = parse_tag(trade.enter_tag)
        if levels is not None and current_rate >= levels[1]:
            return "take_profit_1_5R"
        if current_time - trade.open_date_utc >= TIME_EXIT_BARS * BAR:
            return "time_exit_12h"
        return None
