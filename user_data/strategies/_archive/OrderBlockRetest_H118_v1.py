"""H-118: 15m bullish order-block retest after a structure-breaking displacement.

Rule (research/proposals/H-118.json), 15m, UTC, closed bars only, spot, long only.
A signal at the close of bar t fills at the open of bar t+1 (price E).

- ATR = Wilder ATR(14) of true range (alpha 1/14, seeded with the mean of the first 14 TRs).
- DISPLACEMENT at bar D: close(D) > max high of bars D-16..D-1; high-low >= 1.5 x ATR(D-1);
  (close-low)/(high-low) >= 0.7.
- ORDER BLOCK: most recent bar j in D-5..D-1 with close < open (none: D creates no setup and
  leaves any existing setup untouched). OL = low(j), OH = high(j), MT = (OH+OL)/2.
- SETUP: known at the close of D, replaces any older setup, bar D gives no entry signal. Active on
  bars t = D+1..D+32. Killed by the first bar t > D with close(t) < OL. Consumed by the first bar
  meeting entry conditions (a)-(c), whether or not an order fills.
- ENTRY at the close of bar t: (a) low(t) <= MT, (b) close(t) > OL, (c) ATR(t)/close(t) >= 0.004.
  The tag carries OL and HH = max high of bars D..t.
- Fill only if flat (engine) and fewer than 4 trades opened on the pair in the UTC day of the fill
  (confirm_trade_entry).
- STOP: sd = max(1 - 0.998 x OL / E, 0.01) frozen at the fill; stop price E x (1 - sd), custom_stoploss.
  Native stoploss -0.10 is an engine backstop only.
- TAKE-PROFIT (custom_exit): td = max(HH / E - 1, 0.015); sell when the rate reaches E x (1 + td).
- TIME EXIT (custom_exit): 12 hours (48 bars) after the fill.
- No trailing, no break-even, no cooldown. Warm-up 400 bars.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

ATR_PERIOD = 14
STRUCTURE_LOOKBACK = 16
DISPLACEMENT_RANGE_ATR_MULT = 1.5
DISPLACEMENT_CLOSE_LOCATION_MIN = 0.7
ORDER_BLOCK_SEARCH_BARS = 5
SETUP_ACTIVE_BARS = 32
ACTIVITY_ATR_PCT_MIN = 0.004
STOP_ZONE_BUFFER = 0.998
STOP_MIN_PCT = 0.01
TARGET_MIN_PCT = 0.015
TIME_EXIT_BARS = 48
BAR = timedelta(minutes=15)
MAX_ENTRIES_PER_PAIR_PER_UTC_DAY = 4
TAG_PREFIX = "ob"


def parse_tag(tag) -> tuple[float, float] | None:
    """(OL, HH) recorded in an entry tag, or None for a tag this strategy did not write."""
    if not isinstance(tag, str):
        return None
    parts = tag.split("|")
    if len(parts) != 3 or parts[0] != TAG_PREFIX:
        return None
    try:
        ol = float(parts[1])
        hh = float(parts[2])
    except ValueError:
        return None
    if not (np.isfinite(ol) and np.isfinite(hh)) or ol <= 0 or hh <= 0:
        return None
    return ol, hh


def stop_distance(ol: float, entry: float) -> float:
    """Frozen stop distance sd = max(1 - 0.998 x OL / E, 0.01)."""
    return max(1.0 - STOP_ZONE_BUFFER * ol / entry, STOP_MIN_PCT)


def target_distance(hh: float, entry: float) -> float:
    """Frozen take-profit distance td = max(HH / E - 1, 0.015)."""
    return max(hh / entry - 1.0, TARGET_MIN_PCT)


def wilder_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = ATR_PERIOD) -> np.ndarray:
    """Wilder ATR seeded with the mean of the first `period` true ranges; NaN before that."""
    n = len(close)
    atr = np.full(n, np.nan)
    if n < period:
        return atr
    prev_close = np.concatenate(([np.nan], close[:-1]))
    tr = np.maximum.reduce(
        [
            high - low,
            np.abs(high - prev_close),
            np.abs(low - prev_close),
        ]
    )
    # The first bar has no previous close: its true range is high - low.
    tr[0] = high[0] - low[0]
    if np.isnan(tr[:period]).any():
        return atr
    atr[period - 1] = tr[:period].mean()
    for i in range(period, n):
        if np.isnan(tr[i]) or np.isnan(atr[i - 1]):
            continue
        atr[i] = atr[i - 1] + (tr[i] - atr[i - 1]) / period
    return atr


def order_block_signals(dataframe: DataFrame, atr: np.ndarray):
    """Walk the bars forward and return (signal, ol, hh) arrays. Backward-looking only."""
    open_ = dataframe["open"].to_numpy(dtype=float)
    high = dataframe["high"].to_numpy(dtype=float)
    low = dataframe["low"].to_numpy(dtype=float)
    close = dataframe["close"].to_numpy(dtype=float)
    volume = dataframe["volume"].to_numpy(dtype=float)
    n = len(close)
    signal = np.zeros(n, dtype=bool)
    out_ol = np.full(n, np.nan)
    out_hh = np.full(n, np.nan)

    active = False
    setup_bar = 0
    ol = mt = hh = 0.0

    for t in range(n):
        # --- displacement that creates a new setup (replaces any older one, no signal on D)
        if t >= STRUCTURE_LOOKBACK and not np.isnan(atr[t - 1]):
            window_high = high[t - STRUCTURE_LOOKBACK:t]
            rng = high[t] - low[t]
            if (
                not np.isnan(window_high).any()
                and not np.isnan(close[t])
                and not np.isnan(rng)
                and close[t] > window_high.max()
                and rng >= DISPLACEMENT_RANGE_ATR_MULT * atr[t - 1]
                and rng > 0
                and (close[t] - low[t]) / rng >= DISPLACEMENT_CLOSE_LOCATION_MIN
            ):
                block = None
                for j in range(t - 1, t - ORDER_BLOCK_SEARCH_BARS - 1, -1):
                    if close[j] < open_[j]:
                        block = j
                        break
                if block is not None and not np.isnan(low[block]) and not np.isnan(high[block]):
                    active = True
                    setup_bar = t
                    ol = low[block]
                    mt = (high[block] + low[block]) / 2.0
                    hh = high[t]
                    continue

        if not active:
            continue

        if t > setup_bar + SETUP_ACTIVE_BARS:
            active = False
            continue
        if not np.isnan(high[t]):
            hh = max(hh, high[t])
        if np.isnan(close[t]) or np.isnan(low[t]):
            continue
        if close[t] < ol:
            active = False
            continue
        if (
            low[t] <= mt
            and close[t] > ol
            and not np.isnan(atr[t])
            and close[t] > 0
            and atr[t] / close[t] >= ACTIVITY_ATR_PCT_MIN
            and volume[t] > 0
        ):
            signal[t] = True
            out_ol[t] = ol
            out_hh[t] = hh
            active = False

    return signal, out_ol, out_hh


class OrderBlockRetest_H118_v1(IStrategy):
    """Buy the retest of the last down candle before a structure-breaking displacement, 15m."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.10  # engine backstop; the rule's stop is custom_stoploss
    use_custom_stoploss = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 400

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        high = dataframe["high"].to_numpy(dtype=float)
        low = dataframe["low"].to_numpy(dtype=float)
        close = dataframe["close"].to_numpy(dtype=float)
        atr = wilder_atr(high, low, close)
        signal, ol, hh = order_block_signals(dataframe, atr)
        dataframe["atr"] = atr
        dataframe["ob_signal"] = signal.astype(int)
        dataframe["ob_low"] = ol
        dataframe["ob_high_since_d"] = hh
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (
            (dataframe["ob_signal"] == 1)
            & dataframe["ob_low"].notna()
            & dataframe["ob_high_since_d"].notna()
            & dataframe["atr"].notna()
            & dataframe[["open", "high", "low", "close"]].notna().all(axis=1)
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = [
                f"{TAG_PREFIX}|{float(a)!r}|{float(b)!r}"
                for a, b in zip(
                    dataframe.loc[cond, "ob_low"], dataframe.loc[cond, "ob_high_since_d"]
                )
            ]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Take-profit and time exit depend on the open trade: see custom_exit.
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """Fewer than 4 trades opened on this pair in the UTC calendar day of the fill."""
        if parse_tag(entry_tag) is None:
            return False
        from freqtrade.persistence import Trade

        day = pd.Timestamp(current_time)
        if day.tzinfo is not None:
            day = day.tz_convert("UTC").tz_localize(None)
        day = day.floor("D")
        count = 0
        for trade in Trade.get_trades_proxy(pair=pair):
            opened = pd.Timestamp(trade.open_date_utc)
            if opened.tzinfo is not None:
                opened = opened.tz_convert("UTC").tz_localize(None)
            if opened.floor("D") == day:
                count += 1
        return count < MAX_ENTRIES_PER_PAIR_PER_UTC_DAY

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit,
                        after_fill=False, **kwargs):
        parsed = parse_tag(trade.enter_tag)
        if parsed is None or not trade.open_rate or not current_rate:
            return None
        ol, _ = parsed
        entry = float(trade.open_rate)
        stop_price = entry * (1.0 - stop_distance(ol, entry))
        distance = 1.0 - stop_price / float(current_rate)
        if distance <= 0:
            return -0.0001  # price already at or below the stop: trigger at once
        return -distance

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        parsed = parse_tag(trade.enter_tag)
        if parsed is not None and trade.open_rate:
            _, hh = parsed
            entry = float(trade.open_rate)
            target = entry * (1.0 + target_distance(hh, entry))
            if current_rate is not None and float(current_rate) >= target * (1.0 - 1e-12):
                return "take_profit_displacement_high"
        if current_time - trade.open_date_utc >= TIME_EXIT_BARS * BAR:
            return "time_exit_12h"
        return None
