"""H-122: ICT Silver Bullet on 15m - 4 h low sweep, volume-backed up gap in a New York window, buy the gap retest.

Rule (research/proposals/H-122.json), 15m, closed bars only, spot, long only. A signal at the close of bar t
fills at the open of bar t+1 (price E).

- CLOCK: each bar's UTC open time is converted to America/New_York (DST per date).
- WINDOWS: per NY day, the four bars opening 03:00-03:45 (W1), 10:00-10:45 (W2), 14:00-14:45 (W3).
  w0 = first, w3 = last bar of a window.
- POOL: PL = lowest low of the 16 bars w0-16..w0-1. A missing pool bar or window bar -> no trade for the window.
- SWEEP: j = first bar in w0-8..w3 with low < PL.
- GAP: bars k-1, k, k+1 with k, k+1 in the window and k-1 >= j, and all of
  low(k+1) > high(k-1); (low(k+1) - high(k-1)) / close(k+1) >= 0.0025; close(k) > open(k);
  volume(k) >= 1.5 x mean volume of bars k-20..k-1. Only the first such gap (smallest k+1) is used.
  GT = low(k+1), GB = high(k-1), S = lowest low of bars j..k+1.
- RETEST: for t = k+2..k+9 in order: low(t) < S or close(t) < GB cancels the setup (checked first);
  else low(t) <= GT is the entry signal and the setup is consumed (a zero-volume bar gives no order).
- STOP: min(S, 0.99 x E); d = 1 - stop/E, frozen at the fill; custom_stoploss keeps the stop at that absolute
  price (no trailing). The native stoploss -0.10 is an engine backstop only.
- TARGET: E x (1 + 2d), checked in custom_exit. TIME EXIT: 32 bars (8 hours) after the fill, in custom_exit.
- Warm-up 100 bars. No cooldown, no other filters.

The setup stop reference S is carried in the entry tag ("fvg_retest|<S>").
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

CLOCK_TZ = "America/New_York"
BAR = pd.Timedelta(minutes=15)
WINDOW_START_MINUTES = (3 * 60, 10 * 60, 14 * 60)  # NY open time of w0: 03:00, 10:00, 14:00
WINDOW_BARS = 4
POOL_BARS = 16
SWEEP_LOOKBACK_BARS = 8
GAP_MIN_FRAC = 0.0025
VOLUME_MEAN_BARS = 20
VOLUME_MULT = 1.5
RETEST_BARS = 8
MIN_STOP_FRAC = 0.01
TARGET_R = 2.0
TIME_EXIT_BARS = 32
TAG_PREFIX = "fvg_retest"


def parse_tag(tag) -> float | None:
    """Setup low S recorded in an entry tag, or None for a tag this strategy did not write."""
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


def stop_distance(open_rate: float, setup_low: float) -> float:
    """d = 1 - stop/E with stop = min(S, 0.99 x E)."""
    stop = min(setup_low, (1.0 - MIN_STOP_FRAC) * open_rate)
    return 1.0 - stop / open_rate


def find_setups(
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    volume: np.ndarray,
    vmean: np.ndarray,
    starts: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Scan every window; return (signal bar flags, setup low S at the signal bar) on the gap-free grid.

    A signal at bar t only uses bars up to t. Grid positions past the last observed bar are "not yet seen",
    not "missing"; NaN rows inside the grid are missing bars.
    """
    n = len(low)
    signal = np.zeros(n, dtype=bool)
    setup_low = np.full(n, np.nan)
    present = ~(np.isnan(open_) | np.isnan(high) | np.isnan(low) | np.isnan(close) | np.isnan(volume))

    for p in starts:
        p = int(p)
        if p < POOL_BARS:
            continue
        last_w = min(p + WINDOW_BARS - 1, n - 1)
        if not present[p - POOL_BARS : p].all() or not present[p : last_w + 1].all():
            continue
        pool_low = float(low[p - POOL_BARS : p].min())

        j = -1
        for i in range(p - SWEEP_LOOKBACK_BARS, last_w + 1):
            if low[i] < pool_low:
                j = i
                break
        if j < 0:
            continue

        found = -1
        for k in range(p, p + WINDOW_BARS - 1):
            if k + 1 > last_w:
                break
            if k - 1 < j:
                continue
            gap_bottom = high[k - 1]
            gap_top = low[k + 1]
            if not gap_top > gap_bottom:
                continue
            if not (gap_top - gap_bottom) / close[k + 1] >= GAP_MIN_FRAC:
                continue
            if not close[k] > open_[k]:
                continue
            mean_volume = vmean[k]
            if np.isnan(mean_volume) or not volume[k] >= VOLUME_MULT * mean_volume:
                continue
            found = k
            break
        if found < 0:
            continue

        k = found
        gap_bottom = high[k - 1]
        gap_top = low[k + 1]
        s_low = float(low[j : k + 2].min())
        for t in range(k + 2, k + 2 + RETEST_BARS):
            if t >= n:
                break
            if not present[t]:
                continue
            if low[t] < s_low or close[t] < gap_bottom:
                break
            if low[t] <= gap_top:
                if volume[t] > 0:
                    signal[t] = True
                    setup_low[t] = s_low
                break
    return signal, setup_low


class FairValueGapRetest_H122_v1(IStrategy):
    """Silver Bullet: NY-window low sweep, volume-backed up fair value gap, buy its retest; 2R target, 8 h exit."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.10  # engine backstop only; the real stop is custom_stoploss
    use_custom_stoploss = True
    use_exit_signal = True
    startup_candle_count = 100

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        n_rows = len(dataframe)
        dataframe["fvg_signal"] = 0
        dataframe["fvg_setup_low"] = np.nan
        if n_rows == 0:
            return dataframe

        dates = pd.DatetimeIndex(pd.to_datetime(dataframe["date"], utc=True))
        grid_index = pd.date_range(dates.min(), dates.max(), freq=BAR)
        values = DataFrame(
            {
                "open": dataframe["open"].to_numpy(dtype=float),
                "high": dataframe["high"].to_numpy(dtype=float),
                "low": dataframe["low"].to_numpy(dtype=float),
                "close": dataframe["close"].to_numpy(dtype=float),
                "volume": dataframe["volume"].to_numpy(dtype=float),
            },
            index=dates,
        )
        grid = values.reindex(grid_index)
        positions = grid_index.get_indexer(dates)

        volume = grid["volume"]
        # Mean volume of bars k-20..k-1: the current bar is excluded; a missing bar makes it undefined.
        vmean = volume.shift(1).rolling(VOLUME_MEAN_BARS).mean().to_numpy(dtype=float)

        local = grid_index.tz_convert(CLOCK_TZ)
        minute_of_day = (local.hour * 60 + local.minute).to_numpy()
        starts = np.flatnonzero(np.isin(minute_of_day, WINDOW_START_MINUTES))

        signal, setup_low = find_setups(
            grid["open"].to_numpy(dtype=float),
            grid["high"].to_numpy(dtype=float),
            grid["low"].to_numpy(dtype=float),
            grid["close"].to_numpy(dtype=float),
            volume.to_numpy(dtype=float),
            vmean,
            starts,
        )
        valid_pos = positions >= 0
        sig_rows = np.zeros(n_rows, dtype=int)
        low_rows = np.full(n_rows, np.nan)
        sig_rows[valid_pos] = signal[positions[valid_pos]].astype(int)
        low_rows[valid_pos] = setup_low[positions[valid_pos]]
        dataframe["fvg_signal"] = sig_rows
        dataframe["fvg_setup_low"] = low_rows
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (
            (dataframe["fvg_signal"] == 1)
            & dataframe["fvg_setup_low"].notna()
            & dataframe["open"].notna()
            & dataframe["close"].notna()
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = [
                f"{TAG_PREFIX}|{float(value)!r}" for value in dataframe.loc[cond, "fvg_setup_low"]
            ]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Target and time exit depend on the open trade (fill price, S): see custom_exit.
        return dataframe

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit, after_fill=False, **kwargs):
        """Hold the stop at the absolute price min(S, 0.99 x E) (distance d frozen at the fill); no trailing."""
        setup_low = parse_tag(trade.enter_tag)
        open_rate = float(trade.open_rate)
        if setup_low is None or not open_rate > 0 or not current_rate > 0:
            return None
        stop_price = open_rate * (1.0 - stop_distance(open_rate, setup_low))
        return min(stop_price / current_rate - 1.0, -0.0001)

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        setup_low = parse_tag(trade.enter_tag)
        open_rate = float(trade.open_rate)
        if setup_low is not None and open_rate > 0:
            target = open_rate * (1.0 + TARGET_R * stop_distance(open_rate, setup_low))
            if current_rate >= target:
                return "take_profit_2R"
        if current_time - trade.open_date_utc >= timedelta(minutes=15 * TIME_EXIT_BARS):
            return "time_exit_8h"
        return None
