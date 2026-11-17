"""P-026 WinCompressionBoxBreakout - follow a 5-minute close outside a 60-minute box that is tight for its time of day
(WIN only; 5-minute bars, B3 regular session in Sao Paulo time).

Rule, in words (bar t is the bar that has just closed; "tick" = 5 points; bar_in_day counted from 1 in the proposal, the
column of the engine counts from 0):
- BOX at bar t: the 12 bars t-12..t-1 of TODAY's session (60 minutes). H = max High, L = min Low of those 12 bars. Box
  width R(t-1) = (H - L) / Close(t-1).
- TIME-OF-DAY NORM N(t-1) = the median of R computed at the same minute_of_day (a box of 12 bars of one session ending at
  that minute) over the previous 20 completed sessions of the data, today excluded. A norm needs the value in ALL of those
  20 sessions (a session without a bar at that minute, or without 12 bars before it, makes the norm invalid and gives no
  signal there); with fewer than 20 earlier sessions there is no norm and no trading.
- COMPRESSED: R(t-1) <= 0.80 x N(t-1).
- LONG signal at the close of bar t (fill at the open of bar t+1): compressed and Close(t) >= H + 1 tick. SHORT signal:
  compressed and Close(t) <= L - 1 tick. Only while flat.
- ENTRY WINDOW: bar t is at least the 13th bar of the session (bar_in_day >= 13 counting the first bar as 1, i.e. 12
  earlier bars of today; not before about 10:00) and minutes_to_close at the close of bar t is >= 75.
- STOP on every entry (a stop order, on the grid): the box midpoint M = L + 0.5 (H - L) = (H + L) / 2 rounded to the tick
  (down for a long, up for a short); then the distance between the entry price and M is clamped to at least 0.10% and at
  most 0.30% of the entry price; the clamped stop is rounded away from the price (tick_floor for a long, tick_ceil for a
  short), so after rounding the distance can exceed 0.30% by less than one tick. The entry price is the open of bar t+1,
  which a signal cannot know: the distance and the percentages are taken from Close(t) (the last known price). M is
  always on the right side of Close(t) (a long needs Close(t) >= H + 1 tick >= M).
- EXIT, first that occurs: (a) the stop (the engine checks it from the entry bar, the bar whose open is the fill, on);
  (b) time exit at the open of the 13th bar after the signal bar, i.e. 12 bars held = 60 minutes (decided at the close of
  the bar 12 bars after the signal bar, filled at the next open); (c) the engine's flatten 5 minutes before the close
  (the proposal names no offset: 5 minutes, as in the other B3 rules). No profit target, no reversal while in a position.
- A signal bar must come after the exit bar of the previous trade (the exit bar is the bar whose open is the exit fill
  for a time exit, the bar in which the stop is hit for a stop), at most one position.
- MAX 4 ENTRIES PER DAY, enforced by the rule itself: `indicators` replays each session bar by bar (entry at the next
  open, stop hit when a bar from the entry bar on reaches it, time exit as above) using only bars up to the current one
  and stops signalling after the 4th entry. BacktestConfig(max_entries_per_day=...) is not needed. (The backtester takes
  no decisions during the first `warmup` bars; a session inside that stretch can differ from the replay.)

SessionRules note: a fill happens at the close of the signal bar. `entry_start_after_open_min` = 5 is the first possible
fill (the rule itself enforces the 13th bar); `entry_end_before_close_min` = 74 makes the engine's half-open entry phase
[start, close - 74 min) accept a signal at close - 75 min (minutes_to_close = 75) and refuse a later one.

Lookbacks: 12 bars for the box, 20 previous sessions for the norm. `warmup` = 2600 five-minute bars: the live window
(warmup + 4 bars) then holds today's whole session (at most 113 bars: 09:00-18:25) plus the 20 previous full sessions
(21 x 113 = 2373), with a margin for a partial older session.

Source: Osler, Stop-Loss Orders and Price Cascades in Currency Markets (NY Fed Staff Report 150); Andersen & Bollerslev
(1997), Intraday periodicity and volatility persistence in financial markets (J. Empirical Finance 4); Crabel,
contraction-then-expansion (narrow-range / ORB). Proposal: research/b3/proposals/P-026.json.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from b3.calendar import SessionRules
from b3.markets import ProxyStrategy
from b3.strategy import ENTER_LONG, ENTER_SHORT, EXIT, HOLD, tick_ceil, tick_floor
from live.core.models import Signal

RULE_ID = "P-026"
EPS = 1e-9


class WinCompressionBoxBreakout(ProxyStrategy):
    name = "P-026_win_compression_box_breakout"
    timeframe_min = 5
    warmup = 2600         # today's whole session (at most 113 five-minute bars) + 20 previous full sessions, plus margin
    rules = SessionRules(entry_start_after_open_min=5, entry_end_before_close_min=74, flatten_before_close_min=5)
    params = {
        "box_bars": 12,
        "baseline_sessions": 20,
        "compression_ratio_max": 0.8,
        "breakout_ticks": 1,
        "min_bar_in_day": 13,
        "min_minutes_to_close_at_signal": 75,
        "stop_at_box_fraction": 0.5,
        "min_stop_pct": 0.1,
        "max_stop_pct": 0.3,
        "hold_bars": 12,
        "max_entries_per_day": 4,
    }

    def indicators(self, df):
        p = self.params
        tick = self.market.tick_size
        n = len(df)
        w = p["box_bars"]

        day = df["local_date"].to_numpy()
        mtc = df["minutes_to_close"].to_numpy(dtype=float)
        high = df["high"].to_numpy(dtype=float)
        low = df["low"].to_numpy(dtype=float)
        close = df["close"].to_numpy(dtype=float)

        starts = [0]
        for i in range(1, n):
            if day[i] != day[i - 1]:
                starts.append(i)
        bounds = list(zip(starts, starts[1:] + [n]))

        # box of the `box_bars` bars of ONE session ending at each bar (the bar included): high, low and width R
        box_hi = np.full(n, np.nan)
        box_lo = np.full(n, np.nan)
        for s, e in bounds:
            if e - s >= w:
                box_hi[s + w - 1:e] = np.lib.stride_tricks.sliding_window_view(high[s:e], w).max(axis=1)
                box_lo[s + w - 1:e] = np.lib.stride_tricks.sliding_window_view(low[s:e], w).min(axis=1)
        width = (box_hi - box_lo) / close
        df["cb_width"] = width

        # time-of-day norm: median of the width at the same minute_of_day over the previous `baseline_sessions` sessions
        table = pd.Series(width, index=df.index).groupby([df["local_date"], df["minute_of_day"]]).last().unstack()
        norm_table = table.shift(1).rolling(p["baseline_sessions"], min_periods=p["baseline_sessions"]).median()
        rows_ix = norm_table.index.get_indexer(df["local_date"])
        cols_ix = norm_table.columns.get_indexer(df["minute_of_day"])
        norm = norm_table.to_numpy(dtype=float)[rows_ix, cols_ix]
        df["cb_norm"] = norm
        df["cb_box_hi"] = box_hi
        df["cb_box_lo"] = box_lo

        side = np.zeros(n, dtype=int)
        stop = np.full(n, np.nan)
        time_exit = np.zeros(n, dtype=int)

        ratio_max, k_break = p["compression_ratio_max"], p["breakout_ticks"] * tick
        min_bar, min_mtc = p["min_bar_in_day"], p["min_minutes_to_close_at_signal"]
        frac, min_stop, max_stop = p["stop_at_box_fraction"], p["min_stop_pct"] / 100.0, p["max_stop_pct"] / 100.0
        hold, max_entries = p["hold_bars"], p["max_entries_per_day"]
        flat_mtc = self.rules.flatten_before_close_min

        for s, e in bounds:
            in_pos, pos_stop, pos_bar, entries, block = 0, math.nan, -1, 0, -1
            for i in range(s, e):
                if in_pos != 0:
                    # the stop, checked from the entry bar on (the first bar after the signal bar), before the exits
                    if (in_pos > 0 and low[i] <= pos_stop) or (in_pos < 0 and high[i] >= pos_stop):
                        in_pos, block = 0, i
                    elif mtc[i] <= flat_mtc + EPS:
                        in_pos, block = 0, i + 1       # the engine flattens at the next open
                    elif i - pos_bar >= hold:
                        time_exit[i] = 1               # EXIT decided here, filled at the open of the next bar = exit bar
                        in_pos, block = 0, i + 1
                    continue
                if i <= block or entries >= max_entries:
                    continue
                if i - s + 1 < min_bar or i == s or not mtc[i] >= min_mtc - EPS:
                    continue
                h, lo, r, nn = box_hi[i - 1], box_lo[i - 1], width[i - 1], norm[i - 1]
                if math.isnan(h) or math.isnan(lo) or math.isnan(r) or math.isnan(nn):
                    continue
                if not r <= ratio_max * nn * (1.0 + EPS):
                    continue
                c = close[i]
                mid = lo + frac * (h - lo)
                if c >= h + k_break - EPS:
                    dist = c - tick_floor(mid, tick)
                    dist = min(max(dist, min_stop * c), max_stop * c)
                    st = tick_floor(c - dist, tick)
                    if st < c:
                        side[i], stop[i] = 1, st
                        in_pos, pos_stop, pos_bar, entries = 1, st, i, entries + 1
                elif c <= lo - k_break + EPS:
                    dist = tick_ceil(mid, tick) - c
                    dist = min(max(dist, min_stop * c), max_stop * c)
                    st = tick_ceil(c + dist, tick)
                    if st > c:
                        side[i], stop[i] = -1, st
                        in_pos, pos_stop, pos_bar, entries = -1, st, i, entries + 1

        df["cb_side"] = side
        df["cb_stop"] = stop
        df["cb_time_exit"] = time_exit
        return df

    def decide(self, row, position):
        if position is not None:
            if row.cb_time_exit == 1:
                return Signal(EXIT, reason="time_exit_12_bars")
            return Signal(HOLD)
        if row.cb_side > 0:
            return Signal(ENTER_LONG, stop_price=float(row.cb_stop), reason="compressed_box_break_up")
        if row.cb_side < 0:
            return Signal(ENTER_SHORT, stop_price=float(row.cb_stop), reason="compressed_box_break_down")
        return Signal(HOLD)
