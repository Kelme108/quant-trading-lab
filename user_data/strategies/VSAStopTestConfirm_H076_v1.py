"""H-076: VSA stopping volume, then a low-volume test, then a confirmed up bar; buy the retest of an absorbed 1h low.

Closed 1h bars only; a signal at the close of bar c fills at the open of bar c+1 (entry price E).
Long only, spot, one position (engine), whole balance, no pyramiding, no trend filter, no cooldown.

Definitions (bar index i):
- Vmed(i) = median volume of bars i-48..i-1 (48 bars, excluding i).
- Pos(i) = (close - low) / (high - low); a bar with high == low cannot be a stopping, test or confirmation bar.
STOPPING BAR s: low(s) = lowest low of bars s-47..s; volume(s) >= 2.5 * Vmed(s); Pos(s) >= 0.5;
  close(s) < close(s-6). The most recent stopping bar is the only active setup (a new one replaces any older).
VOID: a bar after s (before entry) closing below low(s) cancels the setup.
TEST BAR t in s+1..s+12: low(t) < low(t-1), low(t) >= low(s), volume(t) <= 0.6 * Vmed(s), Pos(t) >= 0.5.
CONFIRMATION bar c in t+1..t+3 with c <= s+15: close(c) > high(t) and volume(c) > volume(t); the most recent
  test bar whose confirmation window is open at c is the one used.
ENTRY: signal on every confirming bar of the active setup; the stopping bar's timestamp and low(t) are written
  into the entry tag. A stopping bar that has produced an entry is used up: confirm_trade_entry rejects a
  signal whose stopping bar was already traded on the pair (signals while a position is open are ignored by
  the engine and do not use the setup up).
Exits:
- Stop at low(t), fixed at entry, intrabar (custom_stoploss); native safety stop -10% below E, so the
  effective stop is max(low(t), 0.90 * E). If E <= low(t) the stop is at the current rate (immediate exit).
- Target E + 2 * (E - low(t)), intrabar (custom_roi at that price; custom_exit if a bar opens at or above it).
  The engine checks the stop before ROI, so a bar touching both is a stop.
- Time exit at the open of bar c+25, i.e. 24 bars after the fill (custom_exit).
Warm-up: 64 bars.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy

BAR = timedelta(hours=1)
VOLUME_MEDIAN_LOOKBACK = 48
LOW_LOOKBACK = 48
STOP_VOLUME_MULTIPLE = 2.5
CLOSE_POSITION_MIN = 0.5
DECLINE_LAG_BARS = 6
TEST_WINDOW_BARS = 12
TEST_VOLUME_MULTIPLE_MAX = 0.6
CONFIRM_WINDOW_BARS = 3
CONFIRM_LAST_OFFSET = TEST_WINDOW_BARS + CONFIRM_WINDOW_BARS  # c <= s + 15
TARGET_RISK_MULTIPLE = 2.0
TIME_EXIT_BARS = 24
TAG_PREFIX = "vsastc"


def make_tag(stop_ts: int, test_low: float) -> str:
    return f"{TAG_PREFIX}|{int(stop_ts)}|{float(test_low)!r}"


def parse_tag(tag) -> tuple[int, float] | None:
    """(stopping-bar timestamp in seconds, low(t)) from an entry tag, or None for a foreign tag."""
    if not isinstance(tag, str):
        return None
    parts = tag.split("|")
    if len(parts) != 3 or parts[0] != TAG_PREFIX:
        return None
    try:
        stop_ts = int(parts[1])
        test_low = float(parts[2])
    except ValueError:
        return None
    if not np.isfinite(test_low) or test_low <= 0:
        return None
    return stop_ts, test_low


def vsa_indicators(dataframe: DataFrame) -> DataFrame:
    """Stopping-bar flags and the sequential setup state machine. Every value uses bars up to i only."""
    high = dataframe["high"].astype(float)
    low = dataframe["low"].astype(float)
    close = dataframe["close"].astype(float)
    volume = dataframe["volume"].astype(float)
    dates = pd.to_datetime(dataframe["date"], utc=True)
    # Seconds since the epoch, independent of the datetime resolution pandas uses.
    epoch = ((dates - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(seconds=1)).to_numpy(dtype=float)

    vmed = volume.shift(1).rolling(VOLUME_MEDIAN_LOOKBACK).median()
    low_min = low.rolling(LOW_LOOKBACK).min()
    spread = high - low
    has_range = spread > 0
    pos = ((close - low) / spread.where(has_range)).where(has_range)
    close_lag = close.shift(DECLINE_LAG_BARS)
    prev_low = low.shift(1)

    stopping = (
        has_range
        & vmed.notna()
        & low_min.notna()
        & close_lag.notna()
        & pos.notna()
        & (low == low_min)
        & (volume >= STOP_VOLUME_MULTIPLE * vmed)
        & (pos >= CLOSE_POSITION_MIN)
        & (close < close_lag)
    ).fillna(False)
    dataframe["vmed48"] = vmed
    dataframe["close_pos"] = pos
    dataframe["stopping_bar"] = stopping.astype(int)

    n = len(dataframe)
    h = high.to_numpy(dtype=float)
    lo = low.to_numpy(dtype=float)
    c = close.to_numpy(dtype=float)
    v = volume.to_numpy(dtype=float)
    vm = vmed.to_numpy(dtype=float)
    ps = pos.to_numpy(dtype=float)
    pl = prev_low.to_numpy(dtype=float)
    rng = has_range.to_numpy(dtype=bool)
    stop_flags = stopping.to_numpy(dtype=bool)

    confirm = np.zeros(n, dtype=bool)
    setup_ts = np.full(n, np.nan)
    setup_low = np.full(n, np.nan)
    test_low_out = np.full(n, np.nan)
    test_high_out = np.full(n, np.nan)

    s = -1  # index of the active stopping bar, -1 if none
    tests: list[int] = []
    for i in range(n):
        if stop_flags[i]:
            s = i
            tests = []
            continue
        if s < 0:
            continue
        low_s = lo[s]
        if c[i] < low_s:
            # Void: a close below low(s) before entry cancels the setup.
            s = -1
            tests = []
            continue
        setup_ts[i] = epoch[s]
        setup_low[i] = low_s
        # Confirmation against the most recent test bar whose window t+1..t+3 is open at i, with i <= s+15.
        if i <= s + CONFIRM_LAST_OFFSET and rng[i]:
            open_tests = [t for t in tests if t + 1 <= i <= t + CONFIRM_WINDOW_BARS]
            if open_tests:
                t = open_tests[-1]
                test_low_out[i] = lo[t]
                test_high_out[i] = h[t]
                if c[i] > h[t] and v[i] > v[t]:
                    confirm[i] = True
        # Test bar (its own confirmation window starts at i+1).
        if (
            i <= s + TEST_WINDOW_BARS
            and rng[i]
            and pl[i] == pl[i]
            and lo[i] < pl[i]
            and lo[i] >= low_s
            and vm[s] == vm[s]
            and v[i] <= TEST_VOLUME_MULTIPLE_MAX * vm[s]
            and ps[i] == ps[i]
            and ps[i] >= CLOSE_POSITION_MIN
        ):
            tests.append(i)

    dataframe["setup_ts"] = setup_ts
    dataframe["setup_low"] = setup_low
    dataframe["test_low"] = test_low_out
    dataframe["test_high"] = test_high_out
    dataframe["confirm_bar"] = confirm.astype(int)
    return dataframe


class VSAStopTestConfirm_H076_v1(IStrategy):
    """Stopping volume at a 48-bar low, low-volume test holding it, rising-volume confirmation; stop low(t), 2R."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.10
    use_custom_stoploss = True
    use_custom_roi = True
    use_exit_signal = True
    trailing_stop = False
    startup_candle_count = 64

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return vsa_indicators(dataframe)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (
            (dataframe["confirm_bar"] == 1)
            & dataframe["close"].notna()
            & dataframe["setup_ts"].notna()
            & dataframe["setup_low"].notna()
            & dataframe["test_low"].notna()
            & dataframe["test_high"].notna()
            & (dataframe["test_low"] > 0)
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = [
                make_tag(ts, tl)
                for ts, tl in zip(dataframe.loc[cond, "setup_ts"], dataframe.loc[cond, "test_low"])
            ]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # All exits depend on the trade (low(t), E, fill time); handled in custom_stoploss / custom_roi / custom_exit.
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """Reject an entry whose stopping bar was already used by an earlier trade on this pair."""
        parsed = parse_tag(entry_tag)
        if parsed is None:
            return False
        stop_ts = parsed[0]
        for trade in Trade.get_trades_proxy(pair=pair):
            previous = parse_tag(trade.enter_tag)
            if previous is not None and previous[0] == stop_ts:
                return False
        return True

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit,
                        after_fill=False, **kwargs):
        """Stop price low(t), fixed for the trade, relative to the current rate (0 if already at/below it)."""
        parsed = parse_tag(trade.enter_tag)
        if parsed is None or not current_rate:
            return None
        return max(1.0 - parsed[1] / current_rate, 0.0)

    def _target(self, trade) -> float | None:
        parsed = parse_tag(trade.enter_tag)
        if parsed is None or not trade.open_rate:
            return None
        risk = trade.open_rate - parsed[1]
        if risk <= 0:
            return None
        return trade.open_rate + TARGET_RISK_MULTIPLE * risk

    def custom_roi(self, pair, trade, current_time, trade_duration, entry_tag, side, **kwargs):
        """ROI whose exit price is exactly E + 2 * (E - low(t)) after the engine's fee adjustment."""
        target = self._target(trade)
        if target is None:
            return None
        fee_open = trade.fee_open or 0.0
        fee_close = trade.fee_close or 0.0
        return (target * (1.0 - fee_close) - trade.open_rate * (1.0 + fee_open)) / trade.open_rate

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        parsed = parse_tag(trade.enter_tag)
        if parsed is not None and trade.open_rate and trade.open_rate <= parsed[1]:
            return "stop_entry_at_or_below_test_low"
        target = self._target(trade)
        if target is not None and current_rate is not None and current_rate >= target:
            return "target_2r"
        if current_time >= trade.open_date_utc + BAR * TIME_EXIT_BARS:
            return "time_exit_24_bars"
        return None
