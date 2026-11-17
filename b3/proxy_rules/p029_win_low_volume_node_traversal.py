"""P-029 WinLowVolumeNodeTraversal - follow a 1-minute exit from a high-volume price zone of today's profile into a
thin zone (WIN only; 1-minute bars, B3 regular session in Sao Paulo time).

Rule, in words (bar t is the bar that has just closed; B = 50 points; points are index points, tick = 5):
- PROFILE (session only, reset every local_date): price bucket k = [k*B, (k+1)*B), k = floor(price / B). Each bar's real
  volume (column `volume`) is split equally over all buckets from floor(low/B) to floor(high/B). At the close of bar t the
  profile P holds only TODAY's bars before t (bar t excluded). Vmax = max_k P[k]. HVN bucket: P[k] >= 0.5 Vmax. LVN bucket:
  P[k] <= 0.2 Vmax (an empty bucket is an LVN). Vmax = 0 gives no signal.
- WINDOW: a signal only when the minutes since the session open, counted at the close of bar t, are >= 60 and the
  minutes_to_close at that close are > 60; no open position; at most 4 entries per day.
- LONG at the close of bar t: b_now = floor(close[t]/B) > b_prev = floor(close[t-1]/B); bucket b_now-1 is an HVN; bucket
  b_now is an LVN; h = the nearest HVN bucket above b_now exists; target T = h*B (its lower edge) and T - close[t] >= 200.
- SHORT (mirror): b_now < b_prev; bucket b_now+1 is an HVN; b_now is an LVN; h = the nearest HVN bucket below b_now exists;
  T = (h+1)*B (its upper edge) and close[t] - T >= 200. Long and short cannot fire on the same bar (b_now > b_prev vs <).
- ENTRY: market at the open of bar t+1 (the engine's fill of a signal at the close of bar t).
- STOP on every entry (a stop order resting from the entry): 100 points from the ENTRY FILL price. The fill (open of bar
  t+1) is unknown at the close of bar t, so the stop is built from close[t] (the last known price): long
  tick_floor(close[t] - 100), short tick_ceil(close[t] + 100); the engine checks it from the entry bar on.
- EXITS, first that occurs: (a) target: a bar (from the entry bar on) closes at or beyond T (long close >= T, short
  close <= T) -> EXIT decided at that close, filled at the next open; (b) time: the bar 60 bars after the entry bar (entry
  bar = bar t+1, so bar t+61) is closed while still in the position -> EXIT, filled at the next open; (c) flat: the engine's
  flatten at the close of the last bar with minutes_to_close <= 5 (flatten_before_close_min = 5). T and the stop are fixed
  at entry; the profile is not used for exits.
- After any exit a new entry needs a fresh signal on a later bar than the exit bar (the exit bar: the bar whose open is the
  fill of a market exit, or the bar that hits the stop; a stop is checked before the exits, the same order as the engine).
- MAX 4 ENTRIES PER DAY, enforced by the rule itself: `indicators` replays each session bar by bar (entry at the next open,
  stop hit when a bar from the entry bar on reaches it, exits as above) using only bars up to the current one, and stops
  signalling after the 4th entry. BacktestConfig(max_entries_per_day=...) is not needed. (The backtester takes no decisions
  during the first `warmup` bars; a session inside that stretch can differ from the replay.)

SessionRules note: a fill happens at the close of the signal bar. `entry_start_after_open_min` = 60 and
`entry_end_before_close_min` = 60 make the engine's half-open entry phase [open + 60, close - 60) accept a signal whose close
is at least 60 minutes after the open and more than 60 minutes before the close.

Lookbacks: today's whole session (WIN 09:00-18:25 = 565 one-minute bars). `warmup` = 1200 one-minute bars: the live window
(warmup + 4 bars) holds today's whole session plus part of the previous one.

Source: Kavajecz & Odders-White (2004), Technical Analysis and Liquidity Provision, RFS 17(4); volume-profile practice
(high/low volume nodes). Proposal: research/b3/proposals/P-029.json.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from b3.calendar import SessionRules
from b3.markets import ProxyStrategy
from b3.strategy import ENTER_LONG, ENTER_SHORT, EXIT, HOLD, tick_ceil, tick_floor
from live.core.models import Signal

RULE_ID = "P-029"
EPS = 1e-9


class WinLowVolumeNodeTraversal(ProxyStrategy):
    name = "P-029_win_low_volume_node_traversal"
    timeframe_min = 1
    warmup = 1200         # today's whole session (at most 565 one-minute bars) plus a full earlier session, plus margin
    rules = SessionRules(entry_start_after_open_min=60, entry_end_before_close_min=60, flatten_before_close_min=5)
    params = {
        "bucket_points": 50,
        "hvn_frac_of_poc": 0.5,
        "lvn_frac_of_poc": 0.2,
        "warmup_min_after_open": 60,
        "last_entry_min_before_close": 60,
        "min_target_distance_points": 200,
        "stop_points": 100,
        "max_hold_bars": 60,
        "flat_min_before_close": 5,
        "max_entries_per_day": 4,
    }

    def indicators(self, df):
        p = self.params
        tick = self.market.tick_size
        n = len(df)
        bsz = float(p["bucket_points"])
        hvn_f, lvn_f = p["hvn_frac_of_poc"], p["lvn_frac_of_poc"]
        min_dist, stop_pts = float(p["min_target_distance_points"]), float(p["stop_points"])
        hold, max_entries = p["max_hold_bars"], p["max_entries_per_day"]
        open_min = self.market.open.hour * 60 + self.market.open.minute
        tf = self.timeframe_min

        day = df["local_date"].to_numpy()
        mod = df["minute_of_day"].to_numpy(dtype=float)
        mtc = df["minutes_to_close"].to_numpy(dtype=float)
        high = df["high"].to_numpy(dtype=float)
        low = df["low"].to_numpy(dtype=float)
        close = df["close"].to_numpy(dtype=float)
        vol = np.nan_to_num(df["volume"].to_numpy(dtype=float), nan=0.0)

        k_lo = np.floor(low / bsz + EPS).astype(np.int64)
        k_hi = np.floor(high / bsz + EPS).astype(np.int64)
        k_cl = np.floor(close / bsz + EPS).astype(np.int64)

        starts = [0]
        for i in range(1, n):
            if day[i] != day[i - 1]:
                starts.append(i)
        bounds = list(zip(starts, starts[1:] + [n]))

        side = np.zeros(n, dtype=int)
        stop = np.full(n, np.nan)
        target = np.full(n, np.nan)
        exit_code = np.zeros(n, dtype=int)         # 1 target, 2 time
        flat_mtc = self.rules.flatten_before_close_min
        win_start = p["warmup_min_after_open"]
        win_end = p["last_entry_min_before_close"]

        for s, e in bounds:
            base = int(k_lo[s:e].min()) - 3
            prof = np.zeros(int(k_hi[s:e].max()) - base + 4)
            in_pos, pos_stop, pos_target, entry_bar, entries, block = 0, math.nan, math.nan, -1, 0, -1
            for i in range(s, e):
                if in_pos != 0:
                    if (in_pos > 0 and low[i] <= pos_stop) or (in_pos < 0 and high[i] >= pos_stop):
                        in_pos, block = 0, i
                    elif mtc[i] <= flat_mtc + EPS:
                        in_pos, block = 0, i + 1               # the engine flattens at this close
                    elif (in_pos > 0 and close[i] >= pos_target) or (in_pos < 0 and close[i] <= pos_target):
                        exit_code[i] = 1
                        in_pos, block = 0, i + 1
                    elif i - entry_bar >= hold:
                        exit_code[i] = 2
                        in_pos, block = 0, i + 1
                elif (i > block and i > s and entries < max_entries
                      and (mod[i] + tf - open_min) >= win_start - EPS and mtc[i] > win_end + EPS
                      and k_cl[i] != k_cl[i - 1]):
                    vmax = float(prof.max())
                    if vmax > 0.0:
                        hvn_thr, lvn_thr = hvn_f * vmax * (1.0 - EPS), lvn_f * vmax * (1.0 + EPS)
                        idx = int(k_cl[i]) - base
                        c = close[i]
                        if k_cl[i] > k_cl[i - 1]:
                            if prof[idx - 1] >= hvn_thr and prof[idx] <= lvn_thr:
                                above = np.flatnonzero(prof[idx + 1:] >= hvn_thr)
                                if len(above):
                                    t_px = (int(k_cl[i]) + 1 + int(above[0])) * bsz
                                    st = tick_floor(c - stop_pts, tick)
                                    if t_px - c >= min_dist - EPS and st < c:
                                        side[i], stop[i], target[i] = 1, st, t_px
                                        in_pos, pos_stop, pos_target = 1, st, t_px
                                        entry_bar, entries = i + 1, entries + 1
                        else:
                            if prof[idx + 1] >= hvn_thr and prof[idx] <= lvn_thr:
                                below = np.flatnonzero(prof[:idx] >= hvn_thr)
                                if len(below):
                                    t_px = (base + int(below[-1]) + 1) * bsz
                                    st = tick_ceil(c + stop_pts, tick)
                                    if c - t_px >= min_dist - EPS and st > c:
                                        side[i], stop[i], target[i] = -1, st, t_px
                                        in_pos, pos_stop, pos_target = -1, st, t_px
                                        entry_bar, entries = i + 1, entries + 1
                # the profile for the NEXT bar's decision: bar i is added only after its own decision
                nb = int(k_hi[i] - k_lo[i]) + 1
                prof[int(k_lo[i]) - base:int(k_hi[i]) - base + 1] += vol[i] / nb

        df["lv_side"] = side
        df["lv_stop"] = stop
        df["lv_target"] = target
        df["lv_exit"] = exit_code
        return df

    def decide(self, row, position):
        if position is not None:
            if row.lv_exit == 1:
                return Signal(EXIT, reason="target_reached")
            if row.lv_exit == 2:
                return Signal(EXIT, reason="time_exit_60_bars")
            return Signal(HOLD)
        if row.lv_side > 0:
            return Signal(ENTER_LONG, stop_price=float(row.lv_stop), reason="lvn_traversal_up")
        if row.lv_side < 0:
            return Signal(ENTER_SHORT, stop_price=float(row.lv_stop), reason="lvn_traversal_down")
        return Signal(HOLD)
