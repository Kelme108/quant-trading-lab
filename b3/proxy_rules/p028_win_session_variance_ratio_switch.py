"""P-028 WinSessionVarianceRatioSwitch - follow or fade a 15-minute move according to the variance ratio of the day's own
5-minute returns (WIN only; 5-minute bars, B3 regular session in Sao Paulo time).

Rule, in words (every number comes from TODAY's bars only; nothing spans sessions, so the WIN rolls never enter;
the proposal counts bars from 1, the engine's `bar_in_day` from 0; t is the number of bars today at the signal bar):
- Returns: r_1 = ln(close_1 / open_1) for the first bar of the day, r_j = ln(close_j / close_(j-1)) for j >= 2.
- At the close of signal bar t: A(t) = sum_{j=1..t} r_j^2 / t;  B(t) = sum_{j=3..t} (r_j + r_(j-1) + r_(j-2))^2 / (t - 2);
  VR(t) = B(t) / (3 A(t)) (Lo-MacKinlay overlapping variance ratio with q = 3, no mean adjustment); the 15-minute scale
  S(t) = sqrt(3 A(t)); the 15-minute move M(t) = ln(close_t / close_(t-3)).
- Regime: TREND if VR(t) >= 1.15, REVERT if VR(t) <= 0.87, otherwise no trade on that bar. If A(t) = 0 there is no signal.
- Signal: |M(t)| >= 0.75 x S(t). TREND: LONG if M > 0, SHORT if M < 0. REVERT: SHORT if M > 0, LONG if M < 0.
- ENTRY (ENTER_LONG / ENTER_SHORT, fill at the open of bar t+1), only while flat, only if t >= 24 (the first two hours
  only build the statistic: bar_in_day >= 23 in the engine's 0-based count) and minutes_to_close at the close of bar t
  is >= 45.
- STOP on every entry (a stop order, on the grid): long = entry x (1 - 0.003) rounded down to the 5-point tick
  (tick_floor), short = entry x (1 + 0.003) rounded up (tick_ceil). The entry price is the open of bar t+1, which a
  signal cannot know: the stop is computed from Close(t), the last known price. If the rounded stop is not strictly on
  the right side of Close(t), no entry.
- EXIT, first that occurs: (a) the stop (the engine checks it from the entry bar, the bar whose open is the fill, on);
  (b) time exit at the open of bar t+7: 6 bars held = 30 minutes (decided at the close of bar t+6, filled at the next
  open); (c) the engine's flatten before the close (the proposal names no offset: 5 minutes, as in the other B3
  rules). No target, no reversal or re-check while in a position.
- A new signal bar must be at or after the bar on whose open the previous trade exited: after a time exit the bar
  t+7 itself may signal (the book is flat when it closes); after a stop, the bar in which the stop was hit may signal
  (the engine is flat at its decision); after the flatten there is nothing left of the session.
- MAX 5 ENTRIES PER DAY, enforced by the rule itself: `indicators` replays each session bar by bar (entry at the next
  open, stop hit when a bar from the entry bar on reaches it, time exit as above) using only bars up to the current
  one, and stops signalling after the 5th entry. BacktestConfig(max_entries_per_day=...) is not needed. (The
  backtester takes no decisions during the first `warmup` bars; a session inside that stretch can differ from the
  replay.)

SessionRules note: a fill happens at the close of the signal bar. `entry_start_after_open_min` = 5 is the first
possible fill (the rule itself enforces t >= 24); `entry_end_before_close_min` = 44 makes the engine's half-open entry
phase [start, close - 44 min) accept a signal at close - 45 min (minutes_to_close = 45) and refuse a later one.

Lookbacks: today's bars only (at most 113 five-minute bars, 09:00-18:25). `warmup` = 240 five-minute bars: the live
window (warmup + 4 bars) then holds today's whole session plus part of the previous one.

Source: Lo & MacKinlay (1988), Stock Market Prices Do Not Follow Random Walks (Review of Financial Studies 1);
Bianco & Reno (2006), Dynamics of intraday serial correlation in the Italian futures market (J. Futures Markets 26);
Bacry, Iuga, Lasnier & Lehalle, Market impacts and the life cycle of investors orders (arXiv 1412.0217).
Proposal: research/b3/proposals/P-028.json.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from b3.calendar import SessionRules
from b3.markets import ProxyStrategy
from b3.strategy import ENTER_LONG, ENTER_SHORT, EXIT, HOLD, tick_ceil, tick_floor
from live.core.models import Signal

RULE_ID = "P-028"
EPS = 1e-9


class WinSessionVarianceRatioSwitch(ProxyStrategy):
    name = "P-028_win_session_variance_ratio_switch"
    timeframe_min = 5
    warmup = 240          # today's whole session (at most 113 five-minute bars) plus margin; no cross-session lookback
    rules = SessionRules(entry_start_after_open_min=5, entry_end_before_close_min=44, flatten_before_close_min=5)
    params = {
        "vr_lag_bars": 3,
        "min_bar_in_day_at_signal": 24,
        "vr_trend_min": 1.15,
        "vr_revert_max": 0.87,
        "move_bars": 3,
        "move_min_scale": 0.75,
        "stop_pct": 0.3,
        "hold_bars": 6,
        "min_minutes_to_close_at_signal": 45,
        "max_entries_per_day": 5,
    }

    def indicators(self, df):
        p = self.params
        tick = self.market.tick_size
        n = len(df)
        q = p["vr_lag_bars"]
        mb = p["move_bars"]

        day = df["local_date"].to_numpy()
        opn = df["open"].to_numpy(dtype=float)
        high = df["high"].to_numpy(dtype=float)
        low = df["low"].to_numpy(dtype=float)
        close = df["close"].to_numpy(dtype=float)
        mtc = df["minutes_to_close"].to_numpy(dtype=float)

        starts = [0]
        for i in range(1, n):
            if day[i] != day[i - 1]:
                starts.append(i)
        bounds = list(zip(starts, starts[1:] + [n]))

        a_var = np.full(n, np.nan)      # A(t): mean squared 5-minute log return of today up to the bar
        b_var = np.full(n, np.nan)      # B(t): mean squared overlapping q-bar log return of today up to the bar
        move = np.full(n, np.nan)       # M(t): ln(close_t / close_(t - move_bars))
        with np.errstate(divide="ignore", invalid="ignore"):
            for s, e in bounds:
                m = e - s
                c = close[s:e]
                r = np.empty(m)
                r[0] = math.log(c[0] / opn[s]) if opn[s] > 0 and c[0] > 0 else np.nan
                r[1:] = np.log(c[1:] / c[:-1])
                a_var[s:e] = np.cumsum(r * r) / np.arange(1, m + 1)
                if m >= q:
                    cum = np.convolve(r, np.ones(q), mode="valid")           # cum[k] = r_k + ... + r_(k+q-1) (0-based)
                    b_var[s + q - 1:e] = np.cumsum(cum * cum) / np.arange(1, m - q + 2)
                if m > mb:
                    move[s + mb:e] = np.log(c[mb:] / c[:m - mb])

            ratio = b_var / (q * a_var)
            scale = np.sqrt(q * a_var)
            trend = ratio >= p["vr_trend_min"] * (1.0 - EPS)
            revert = ratio <= p["vr_revert_max"] * (1.0 + EPS)
            strong = np.abs(move) >= p["move_min_scale"] * scale * (1.0 - EPS)
            ok = strong & (a_var > 0) & np.isfinite(ratio) & np.isfinite(move)
            up = move > 0
            dn = move < 0
            raw = np.zeros(n, dtype=int)                  # +1 long setup, -1 short setup (before window / state rules)
            raw[ok & ((trend & up) | (revert & dn))] = 1
            raw[ok & ((trend & dn) | (revert & up))] = -1

        df["vr_ratio"] = ratio
        df["vr_scale"] = scale
        df["vr_move"] = move
        df["vr_raw"] = raw

        side = np.zeros(n, dtype=int)
        stop = np.full(n, np.nan)
        time_exit = np.zeros(n, dtype=int)

        min_bar = p["min_bar_in_day_at_signal"] - 1       # engine's bar_in_day is 0-based
        min_mtc = p["min_minutes_to_close_at_signal"]
        frac = p["stop_pct"] / 100.0
        hold, max_entries = p["hold_bars"], p["max_entries_per_day"]
        flat_mtc = self.rules.flatten_before_close_min

        for s, e in bounds:
            in_pos, pos_stop, pos_bar, entries = 0, math.nan, -1, 0
            for i in range(s, e):
                if in_pos != 0:
                    # the stop, checked from the entry bar on (the first bar after the signal bar), before the exits
                    if (in_pos > 0 and low[i] <= pos_stop) or (in_pos < 0 and high[i] >= pos_stop):
                        in_pos = 0                         # flat at this bar's decision: a new signal may come now
                    else:
                        if mtc[i] <= flat_mtc + EPS:
                            in_pos = 0                     # the engine flattens at the next open
                        elif i - pos_bar >= hold:
                            time_exit[i] = 1               # EXIT decided here, filled at the open of the next bar
                            in_pos = 0
                        continue
                if entries >= max_entries or i - s < min_bar or not mtc[i] >= min_mtc - EPS:
                    continue
                c = close[i]
                if raw[i] > 0:
                    st = tick_floor(c * (1.0 - frac), tick)
                    if st < c:
                        side[i], stop[i] = 1, st
                        in_pos, pos_stop, pos_bar, entries = 1, st, i, entries + 1
                elif raw[i] < 0:
                    st = tick_ceil(c * (1.0 + frac), tick)
                    if st > c:
                        side[i], stop[i] = -1, st
                        in_pos, pos_stop, pos_bar, entries = -1, st, i, entries + 1

        df["vr_side"] = side
        df["vr_stop"] = stop
        df["vr_time_exit"] = time_exit
        return df

    def decide(self, row, position):
        if position is not None:
            if row.vr_time_exit == 1:
                return Signal(EXIT, reason="time_exit_6_bars")
            return Signal(HOLD)
        if row.vr_side > 0:
            return Signal(ENTER_LONG, stop_price=float(row.vr_stop), reason="variance_ratio_long")
        if row.vr_side < 0:
            return Signal(ENTER_SHORT, stop_price=float(row.vr_stop), reason="variance_ratio_short")
        return Signal(HOLD)
