"""P-023 WinMetaorderGrindContinuation - follow a 30-minute move built from many small same-sign minutes with no
jump (WIN only; 1-minute bars, B3 regular session in Sao Paulo time).

Rule, in words (all features from closed bars; r_i = close_i / close_(i-1) - 1 for consecutive bars of the SAME session,
so the overnight gap and the WIN$N roll gap never enter):
- WINDOW at the close of bar t with bar_in_day >= 30 (the last 30 returns are all of today): UP = number of those 30
  returns > 0, DN = number < 0 (zero returns count for neither), D = UP - DN; R30 = close_t / close_(t-30) - 1;
  MAXR = the largest |r_i| among the 30 returns.
- SCALE S, one number per session, fixed at the open: the median of |close_j / close_(j-30) - 1| over every bar j with
  bar_in_day >= 30 (j - 30 inside the same session) of the previous 20 complete sessions, pooled. With fewer than 20 prior
  sessions in the data: no trading.
- LONG setup at t: D >= +10 AND R30 >= 1.0 x S AND MAXR <= 0.5 x R30. SHORT setup: D <= -10 AND R30 <= -1.0 x S AND
  MAXR <= 0.5 x |R30|.
- ENTRY (ENTER_LONG / ENTER_SHORT, fill at the open of bar t+1) only on a FRESH setup (the same side's setup was false at
  bar t-1; at bar_in_day = 30 the previous bar has no setup), only when flat, only if minutes_to_close >= 45 at the close
  of bar t, at most 4 entries per day (both sides together).
- STOP on every entry: long = fill x (1 - S), short = fill x (1 + S), rounded to the tick away from the entry
  (tick_floor for a long, tick_ceil for a short). The fill is the open of bar t+1, which a signal cannot know: the stop is
  computed from the close of bar t (the last known price; the open of t+1 is that close plus the minute's gap). If the
  rounded stop is not strictly on the right side of that close (S so small that it rounds onto the price), no entry.
- EXITS, first that occurs: (a) the stop (the engine checks it from the entry bar on, before the decisions); (b) signal
  exit when the persistence dies: long D <= 0 at a bar close, short D >= 0 -> EXIT at the next bar's open; (c) time exit 30
  bars after the entry decision (the fill is the open of the next bar, so the position is held 30 one-minute bars): decided
  at the close of the bar 30 bars after the signal bar, filled at the next open; (d) flat at the open that follows the
  close of the first bar with minutes_to_close <= 10 (the engine's flatten, `flatten_before_close_min` = 10). After any
  exit a new entry needs a new fresh setup. No events filter.

MAX 4 ENTRIES PER DAY, enforced by the rule itself: `indicators` replays each session bar by bar (entry at the next open,
stop hit when a bar from the entry bar on reaches it, signal / time / flatten exits as above, a new entry possible at the
bar where the stop was hit because the engine is flat then) using only bars up to the current one, and stops signalling
after the 4th entry. BacktestConfig(max_entries_per_day=...) is not needed. (The backtester takes no decision during the
first `warmup` bars; a session that starts inside that stretch can differ from the replay.)

SessionRules note: a fill happens at the close of the signal bar. `entry_start_after_open_min` = 1 is the first possible
fill (the rule itself enforces bar_in_day >= 30); `entry_end_before_close_min` = 44 makes the engine's half-open entry
phase [start, close - 44 min) accept a signal at close - 45 min (minutes_to_close = 45) and refuse a later one.

Lookbacks: 30 bars for the window, 20 previous sessions for the scale. `warmup` = 12000 one-minute bars: the live window
(warmup + 4 bars) then holds today's whole session (at most 565 bars: 09:00-18:25) plus the 20 previous full sessions
(20 x 565 = 11300), with a margin for a partial older session.

Source: Toth, Palit, Lillo & Farmer, Why is equity order flow so persistent? (JEDC 2015, arXiv 1108.1632); Bacry, Iuga,
Lasnier & Lehalle, Market impacts and the life cycle of investors orders (arXiv 1412.0217); Da, Gurun & Warachka, Frog in
the Pan (continuous information and momentum). Proposal: research/b3/proposals/P-023.json.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from b3.calendar import SessionRules
from b3.markets import ProxyStrategy
from b3.strategy import ENTER_LONG, ENTER_SHORT, EXIT, HOLD, tick_ceil, tick_floor
from live.core.models import Signal

RULE_ID = "P-023"
EPS = 1e-12


class WinMetaorderGrindContinuation(ProxyStrategy):
    name = "P-023_win_metaorder_grind_continuation"
    timeframe_min = 1
    warmup = 12000        # today's whole session (at most 565 one-minute bars) + 20 previous full sessions, plus margin
    rules = SessionRules(entry_start_after_open_min=1, entry_end_before_close_min=44, flatten_before_close_min=10)
    params = {
        "window_bars": 30,
        "net_sign_threshold": 10,
        "min_move_over_scale": 1.0,
        "max_single_bar_share": 0.5,
        "scale_lookback_sessions": 20,
        "scale_return_bars": 30,
        "stop_over_scale": 1.0,
        "signal_exit_net_sign": 0,
        "time_exit_bars": 30,
        "min_bar_in_day": 30,
        "last_entry_minutes_to_close": 45,
        "flat_minutes_to_close": 10,
        "max_entries_per_day": 4,
    }

    def indicators(self, df):
        p = self.params
        tick = self.market.tick_size
        n = len(df)
        w, rb = p["window_bars"], p["scale_return_bars"]

        day = df["local_date"].to_numpy()
        close = df["close"].to_numpy(dtype=float)
        high = df["high"].to_numpy(dtype=float)
        low = df["low"].to_numpy(dtype=float)
        mtc = df["minutes_to_close"].to_numpy(dtype=float)

        starts = [0]
        for i in range(1, n):
            if day[i] != day[i - 1]:
                starts.append(i)
        bounds = list(zip(starts, starts[1:] + [n]))

        d_net = np.full(n, np.nan)       # UP - DN over the last `window_bars` returns of the session
        r30 = np.full(n, np.nan)         # close_t / close_(t - scale_return_bars) - 1 (same session)
        maxr = np.full(n, np.nan)        # the largest |return| among those returns
        scale = np.full(n, np.nan)       # S: one number per session, from the previous sessions only
        abs_moves = []                   # per session: |close_j / close_(j-30) - 1| for the bars with bar_in_day >= 30
        for s, e in bounds:
            m = e - s
            moves = np.empty(0)
            if m > w and m > rb:
                c = close[s:e]
                r1 = c[1:] / c[:-1] - 1.0                                   # r1[k] = return of bar k + 1
                up = np.concatenate(([0], np.cumsum(r1 > 0)))
                dn = np.concatenate(([0], np.cumsum(r1 < 0)))
                d_net[s + w:e] = (up[w:] - up[:m - w]) - (dn[w:] - dn[:m - w])
                maxr[s + w:e] = np.lib.stride_tricks.sliding_window_view(np.abs(r1), w).max(axis=1)
                moves_signed = c[rb:] / c[:m - rb] - 1.0
                r30[s + rb:e] = moves_signed
                moves = np.abs(moves_signed)
            abs_moves.append(moves)
        lookback = p["scale_lookback_sessions"]
        for k, (s, e) in enumerate(bounds):
            if k >= lookback:
                pooled = np.concatenate(abs_moves[k - lookback:k])
                pooled = pooled[np.isfinite(pooled)]
                if pooled.size:
                    scale[s:e] = float(np.median(pooled))

        nt, ms, sh = p["net_sign_threshold"], p["min_move_over_scale"], p["max_single_bar_share"]
        with np.errstate(invalid="ignore"):
            long_setup = (d_net >= nt) & (r30 >= ms * scale - EPS) & (maxr <= sh * r30 + EPS)
            short_setup = (d_net <= -nt) & (r30 <= -ms * scale + EPS) & (maxr <= sh * (-r30) + EPS)

        side = np.zeros(n, dtype=int)
        stop = np.full(n, np.nan)
        time_exit = np.zeros(n, dtype=int)

        sx, tx, so = p["signal_exit_net_sign"], p["time_exit_bars"], p["stop_over_scale"]
        min_bar, min_mtc = p["min_bar_in_day"], p["last_entry_minutes_to_close"]
        flat_mtc, max_entries = p["flat_minutes_to_close"], p["max_entries_per_day"]

        for s, e in bounds:
            in_pos, pos_stop, pos_bar, entries = 0, math.nan, -1, 0
            for i in range(s, e):
                if in_pos != 0:
                    if (in_pos > 0 and low[i] <= pos_stop) or (in_pos < 0 and high[i] >= pos_stop):
                        in_pos = 0                         # stopped in this bar: flat, a new entry may be decided now
                    else:
                        d = d_net[i]
                        if mtc[i] <= flat_mtc + EPS:
                            in_pos = 0                     # the engine flattens at the next open
                        elif (in_pos > 0 and d <= sx) or (in_pos < 0 and d >= sx):
                            in_pos = 0                     # persistence died: EXIT at the next open
                        elif i - pos_bar >= tx:
                            time_exit[i] = 1
                            in_pos = 0
                        continue
                if entries >= max_entries or i - s < min_bar or not mtc[i] >= min_mtc - EPS or math.isnan(scale[i]):
                    continue
                c = close[i]
                if long_setup[i] and not (i > s and long_setup[i - 1]):
                    st = tick_floor(c * (1.0 - so * scale[i]), tick)
                    if st < c:
                        side[i], stop[i] = 1, st
                        in_pos, pos_stop, pos_bar, entries = 1, st, i, entries + 1
                elif short_setup[i] and not (i > s and short_setup[i - 1]):
                    st = tick_ceil(c * (1.0 + so * scale[i]), tick)
                    if st > c:
                        side[i], stop[i] = -1, st
                        in_pos, pos_stop, pos_bar, entries = -1, st, i, entries + 1

        df["gp_d"] = d_net
        df["gp_r30"] = r30
        df["gp_maxr"] = maxr
        df["gp_scale"] = scale
        df["gp_long_setup"] = long_setup.astype(int)
        df["gp_short_setup"] = short_setup.astype(int)
        df["gp_side"] = side
        df["gp_stop"] = stop
        df["gp_time_exit"] = time_exit
        return df

    def decide(self, row, position):
        sx = self.params["signal_exit_net_sign"]
        if position is not None:
            d = row.gp_d
            if position.volume > 0 and d <= sx:
                return Signal(EXIT, reason="persistence_died_long")
            if position.volume < 0 and d >= sx:
                return Signal(EXIT, reason="persistence_died_short")
            if row.gp_time_exit == 1:
                return Signal(EXIT, reason="time_exit_30_bars")
            return Signal(HOLD)
        if row.gp_side > 0:
            return Signal(ENTER_LONG, stop_price=float(row.gp_stop), reason="grind_up_long")
        if row.gp_side < 0:
            return Signal(ENTER_SHORT, stop_price=float(row.gp_stop), reason="grind_down_short")
        return Signal(HOLD)
