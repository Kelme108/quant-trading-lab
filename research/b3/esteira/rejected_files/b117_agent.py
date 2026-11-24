"""Conveyor batch B-117 (agent, 2026-11-24). Mixed simple themes: volume thrust, compression, exhaustion streaks, efficiency, RSI turns, channel midline, engulfing, day-open cross."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _d(long, short):
    return long.astype(int) - short.astype(int)


def _thrust_close(ctx, p):
    k, loc = p["vol_k"], p["loc"]
    med = ctx.cached("vol_med_b117", lambda: ctx.same_minute(ctx.v, "median"))
    rng = ctx.h - ctx.l
    pos = np.where(rng > 0, (ctx.c - ctx.l) / np.where(rng > 0, rng, 1.0), 0.5)
    big = ctx.v > k * med
    long = big & (pos >= 1 - loc) & (ctx.c > ctx.o)
    short = big & (pos <= loc) & (ctx.c < ctx.o)
    return _d(ctx.cross(long), ctx.cross(short))


def _narrowest_break(ctx, p):
    n = int(p["n"])
    rng = ctx.h - ctx.l
    mn = ctx.roll(rng, n, "min", include_current=True)
    narrow = (rng <= mn) & (rng > 0)
    nar1 = ctx.prev(narrow.astype(float), 1) == 1
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    long = nar1 & (ctx.c > h1)
    short = nar1 & (ctx.c < l1)
    return _d(long, short)


def _streak_reversal(ctx, p):
    k = int(p["streak"])
    dn = (ctx.c < ctx.o).astype(float)
    up = (ctx.c > ctx.o).astype(float)
    sdn = ctx.prev(ctx.roll(dn, k, "sum", True), 1) == k
    sup = ctx.prev(ctx.roll(up, k, "sum", True), 1) == k
    long = sdn & (ctx.c > ctx.o)
    short = sup & (ctx.c < ctx.o)
    return _d(long, short)


def _efficiency_follow(ctx, p):
    nb, thr = ctx.bars(p["win_min"]), p["er"]
    net = ctx.c - ctx.prev(ctx.c, nb)
    path = ctx.roll(np.abs(ctx.c - ctx.prev(ctx.c, 1)), nb, "sum", True)
    er = np.where(path > 0, np.abs(net) / np.where(path > 0, path, 1.0), 0.0)
    ok = er >= thr
    return _d(ctx.cross(ok & (net > 0)), ctx.cross(ok & (net < 0)))


def _rsi_turn(ctx, p):
    n, lvl = int(p["n"]), p["level"]
    r = ctx.rsi(n)
    long = r > lvl
    short = r < 100 - lvl
    # follow the exit from the extreme zone back toward the middle
    pr = ctx.prev(r, 1)
    return _d((pr <= lvl) & long & False | ((pr < lvl) & (r >= lvl)), (pr > 100 - lvl) & (r <= 100 - lvl))


def _channel_mid_cross(ctx, p):
    nb = ctx.bars(p["win_min"])
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    mid = (hi + lo) / 2.0
    wide = (hi - lo) >= p["min_width"] * ctx.c
    return _d(ctx.cross(wide & (ctx.c > mid)), ctx.cross(wide & (ctx.c < mid)))


def _engulf(ctx, p):
    k = p["size_k"]
    rng = ctx.h - ctx.l
    typ = ctx.cached("rng_typ_b117", lambda: ctx.same_minute(rng, "mean"))
    po, pc = ctx.prev(ctx.o, 1), ctx.prev(ctx.c, 1)
    body = np.abs(ctx.c - ctx.o)
    big = body >= k * typ
    long = big & (pc < po) & (ctx.c > po) & (ctx.o <= pc) & (ctx.c > ctx.o)
    short = big & (pc > po) & (ctx.c < po) & (ctx.o >= pc) & (ctx.c < ctx.o)
    return _d(long, short)


def _day_open_cross(ctx, p):
    k = p["away_k"]
    r = ctx.c / ctx.day_open - 1.0
    typ = ctx.cached("abs_ret_sm_b117", lambda: ctx.same_minute(np.abs(r), "mean"))
    nb = ctx.bars(30)
    was_up = ctx.roll((r >= k * typ).astype(float), nb, "max", include_current=False) == 1
    was_dn = ctx.roll((r <= -k * typ).astype(float), nb, "max", include_current=False) == 1
    # price was stretched on one side within the last 30 min and now crosses the day open: follow the cross
    return _d(was_dn & (r > 0) & (ctx.prev(r, 1) <= 0), was_up & (r < 0) & (ctx.prev(r, 1) >= 0))


def _gap_bar_hold(ctx, p):
    k = p["gap_k"]
    rng = ctx.h - ctx.l
    typ = ctx.cached("rng_typ_b117", lambda: ctx.same_minute(rng, "mean"))
    pc = ctx.prev(ctx.c, 1)
    gap_up = (ctx.o - pc) >= k * typ
    gap_dn = (pc - ctx.o) >= k * typ
    # bar-to-bar gap that is not filled within the bar: continuation
    long = gap_up & (ctx.l > pc) & (ctx.c > ctx.o)
    short = gap_dn & (ctx.h < pc) & (ctx.c < ctx.o)
    return _d(long, short)


def _vol_dryup_resume(ctx, p):
    nb = ctx.bars(p["trend_min"])
    mom = ctx.c - ctx.prev(ctx.c, nb)
    vm = ctx.roll(ctx.v, 3, "mean", True)
    vlong = ctx.roll(ctx.v, nb, "mean", True)
    dry = ctx.prev(vm, 1) < p["dry"] * ctx.prev(vlong, 1)
    long = dry & (mom > 0) & (ctx.c > ctx.prev(ctx.h, 1))
    short = dry & (mom < 0) & (ctx.c < ctx.prev(ctx.l, 1))
    return _d(ctx.cross(long), ctx.cross(short))


def _late_session_drift(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    mom = ctx.c - ctx.prev(ctx.c, nb)
    typ = ctx.cached(("absmom_b117", nb), lambda: ctx.prev_sessions(np.abs(mom), "mean"))
    win = (ctx.minutes_to_close <= p["window_min"]) & (ctx.minutes_to_close > 5)
    return _d(ctx.cross(win & (mom >= typ) & (mom > 0)), ctx.cross(win & (mom <= -typ) & (mom < 0)))


FAMILIES = [
    Family("E-1168", "High-volume thrust bar closing at its extreme follow",
           "A bar with volume well above the usual for that minute that closes at its high/low shows aggressive "
           "market orders hitting a thin book; the other side is late and chasing orders should extend it.",
           {"vol_k": [1.5, 2.0, 3.0], "loc": [0.1, 0.2]}, _thrust_close, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1169", "Narrowest-range-of-N bar break follow",
           "The narrowest bar of the last N bars marks a pause in quoting; a close beyond its high/low next bar "
           "releases the compressed range (NR4/NR7 idea at intraday scale).",
           {"n": [4, 7, 10]}, _narrowest_break, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1170", "Streak exhaustion first counter-colour bar",
           "After k bars of the same colour, late trend traders are positioned one way; the first opposite-colour "
           "bar shows the buying/selling dried up and a snap-back should follow.",
           {"streak": [3, 4, 5]}, _streak_reversal, source="assistant reasoning", author="agent"),
    Family("E-1171", "Kaufman efficiency-ratio clean-move follow",
           "When price covers a window in a nearly straight line (efficiency ratio high), one side is absorbing "
           "all the flow; the first bar the ratio crosses the threshold marks the start of a clean trend.",
           {"win_min": [10, 20, 30], "er": [0.5, 0.6, 0.7]}, _efficiency_follow, source="Kaufman adaptive moving average (efficiency ratio)", author="agent"),
    Family("E-1172", "RSI exit from extreme zone follow-through",
           "RSI re-crossing back above 30 (below 70) after an oversold (overbought) spell marks the end of a "
           "forced-flow leg; take the rebound.",
           {"n": [7, 14], "level": [25, 30, 35]}, _rsi_turn, source="assistant reasoning", author="agent"),
    Family("E-1173", "Donchian midline cross follow",
           "The midpoint of the N-minute high/low channel is the equilibrium of recent trade; a close crossing "
           "it in a channel wide enough to matter shifts control to the new side.",
           {"win_min": [20, 40, 60], "min_width": [0.001, 0.002]}, _channel_mid_cross, markets=("WIN",),
           source="Donchian channel midline", author="agent"),
    Family("E-1174", "Large engulfing bar follow",
           "A body that engulfs the previous opposite body and is larger than the typical range for that time "
           "means the prior side was overrun; the engulfed side's stops fuel continuation.",
           {"size_k": [0.75, 1.0, 1.5]}, _engulf, markets=("WIN",), source="candlestick engulfing pattern", author="agent"),
    Family("E-1175", "Day-open recross after stretch follow",
           "The day's opening price is the reference many intraday participants anchor on; crossing it after "
           "having been stretched the other side recently marks a regime flip of the day's bias.",
           {"away_k": [0.5, 1.0, 1.5]}, _day_open_cross, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1176", "Unfilled bar-to-bar gap continuation",
           "A bar that opens beyond the prior close by a sizeable amount and never retraces into it shows "
           "one-sided urgency (market orders through the book); follow.",
           {"gap_k": [0.15, 0.3, 0.5]}, _gap_bar_hold, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1177", "Volume dry-up trend resumption",
           "In a trend, a spell of volume well below the window average is a pause by profit takers without "
           "counter-flow; the first close through the pause bar's extreme resumes the trend.",
           {"trend_min": [20, 30, 60], "dry": [0.6, 0.8]}, _vol_dryup_resume, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
