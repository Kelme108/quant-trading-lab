"""Conveyor batch B-105 (agent, 2026-11-24). Mixed themes: cross-market lead/lag, bands, compression, time windows, levels."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _moves(ctx, nb):
    own = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    oc = ctx.other_close()
    oth = oc / ctx.prev(oc, nb) - 1.0
    t_own = ctx.cached(("tm", nb), lambda: ctx.prev_sessions(np.abs(own), "mean"))
    t_oth = ctx.cached(("tmo", nb), lambda: ctx.prev_sessions(np.abs(oth), "mean"))
    return own, oth, t_own, t_oth


def _dollar_lead(ctx, p):
    nb, k = ctx.bars(p["move_min"]), p["k"]
    own, oth, t_own, t_oth = _moves(ctx, nb)
    short = (oth >= k * t_oth) & (own > 0)
    long = (oth <= -k * t_oth) & (own < 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _index_lead_wdo(ctx, p):
    nb, k = ctx.bars(p["move_min"]), p["k"]
    own, oth, t_own, t_oth = _moves(ctx, nb)   # own = WDO, oth = WIN
    short = (oth >= k * t_oth) & (own >= 0)    # index up, dollar not falling: dollar should drop
    long = (oth <= -k * t_oth) & (own <= 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _boll_reentry(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    m = ctx.roll(ctx.c, n, "mean")
    s = ctx.roll(ctx.c, n, "std")
    pm, ps_ = ctx.prev(m, 1), ctx.prev(s, 1)
    pc = ctx.prev(ctx.c, 1)
    short = (pc > pm + k * ps_) & (ctx.c <= pm + k * ps_) & (ps_ > 0)
    long = (pc < pm - k * ps_) & (ctx.c >= pm - k * ps_) & (ps_ > 0)
    return long.astype(int) - short.astype(int)


def _nr_break(ctx, p):
    n = int(p["n"])
    rng = ctx.h - ctx.l
    lo_rng = ctx.roll(rng, n, "min", include_current=True)
    narrow = (rng <= lo_rng) & (rng > 0)
    nh, nl = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    pn = ctx.prev(narrow.astype(float), 1) == 1
    up = pn & (ctx.c > nh)
    dn = pn & (ctx.c < nl)
    return up.astype(int) - dn.astype(int)


def _vwap_z_fade(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    dev = ctx.c - ctx.vwap()
    sd = ctx.roll(dev, n, "std")
    z = np.where(sd > 0, dev / np.where(sd > 0, sd, 1.0), 0.0)
    return ctx.cross(z <= -k).astype(int) - ctx.cross(z >= k).astype(int)


def _staircase(ctx, p):
    n = int(p["steps"])
    up = np.ones(ctx.n, bool)
    dn = np.ones(ctx.n, bool)
    for i in range(n):
        up &= (ctx.prev(ctx.h, i) > ctx.prev(ctx.h, i + 1)) & (ctx.prev(ctx.l, i) > ctx.prev(ctx.l, i + 1))
        dn &= (ctx.prev(ctx.h, i) < ctx.prev(ctx.h, i + 1)) & (ctx.prev(ctx.l, i) < ctx.prev(ctx.l, i + 1))
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _us_open_break(ctx, p):
    start, nb = int(p["start_min"]), ctx.bars(p["range_min"])
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    win = (ctx.minute >= start) & (ctx.minute < start + 45)
    up = win & (ctx.c > hi)
    dn = win & (ctx.c < lo)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _round_reject(ctx, p):
    step = float(p["step"])
    lvl_h = np.floor(ctx.h / step) * step           # highest round level at or below the high
    lvl_l = np.ceil(ctx.l / step) * step            # lowest round level at or above the low
    short = (ctx.h > ctx.o) & (lvl_h > np.maximum(ctx.o, ctx.prev(ctx.c, 1))) & (ctx.c < lvl_h)
    long = (ctx.l < ctx.o) & (lvl_l < np.minimum(ctx.o, ctx.prev(ctx.c, 1))) & (ctx.c > lvl_l)
    return long.astype(int) - short.astype(int)


def _climax_fade(ctx, p):
    k = p["vol_k"]
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    spike = ctx.v >= k * med
    mid = (ctx.h + ctx.l) / 2.0
    newhi = ctx.h > ctx.session_high(False)
    newlo = ctx.l < ctx.session_low(False)
    short = spike & newhi & (ctx.c < mid)
    long = spike & newlo & (ctx.c > mid)
    return long.astype(int) - short.astype(int)


def _prev_close_cross(ctx, p):
    hold = ctx.bars(p["hold_min"])
    pcl = ctx.prev_session_value("close")
    above = (ctx.c > pcl).astype(float)
    below = (ctx.c < pcl).astype(float)
    was_below = ctx.roll(below, hold + 1, "min", include_current=False) == 1
    was_above = ctx.roll(above, hold + 1, "min", include_current=False) == 1
    up = was_below & (ctx.c > pcl)
    dn = was_above & (ctx.c < pcl)
    return up.astype(int) - dn.astype(int)


def _late_drift(ctx, p):
    # first bar after the day move (vs open) crosses k typical sizes, measured against the previous-session mean abs move
    k = p["k"]
    r = ctx.c / ctx.day_open - 1.0
    typ = ctx.cached("abs_r_same_min", lambda: ctx.same_minute(np.abs(r), "mean"))
    m = ctx.roll(ctx.c, ctx.bars(p["win_min"]), "mean")
    ext = np.abs(r) >= k * typ
    short = ext & (r > 0) & (ctx.c < m)
    long = ext & (r < 0) & (ctx.c > m)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


FAMILIES = [
    Family("E-1048", "Dollar leads the index",
           "WDO moves first when macro news hits; if the dollar jumps while WIN has not yet fallen, the index "
           "catches down (and vice versa), so trade WIN against the unreacted leg.",
           {"move_min": [5, 10, 15], "k": [1.0, 1.5, 2.0]}, _dollar_lead, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1049", "Bollinger band re-entry fade",
           "A close outside a k-sigma band of the recent closes followed by a close back inside signals an "
           "exhausted push; trade back toward the mean.",
           {"win_min": [20, 40, 60], "k": [2.0, 2.5]}, _boll_reentry, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1050", "Narrowest-range bar break",
           "A bar with the smallest range of the last n bars shows compression; a close beyond its extremes on "
           "the next bar releases the stored energy.",
           {"n": [5, 8, 12]}, _nr_break, markets=("WIN",), source="assistant reasoning (NR7 idea)", author="agent"),
    Family("E-1051", "VWAP z-score fade",
           "When the price stretches k standard deviations of its own recent VWAP deviation, late chasers are "
           "exposed and the price drifts back toward VWAP.",
           {"win_min": [30, 60, 90], "k": [2.0, 2.5, 3.0]}, _vwap_z_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1052", "Higher-high higher-low staircase",
           "Consecutive bars each with higher high and higher low (or lower/lower) are orderly one-sided "
           "trading; join the staircase when it forms.",
           {"steps": [3, 4, 5]}, _staircase, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1053", "US-session window range break",
           "Around the US cash open (10:30-11:30 BRT) foreign flow arrives; a close beyond the preceding range "
           "within 45 minutes of the start follows that flow.",
           {"start_min": [630, 660, 690], "range_min": [15, 30, 45]}, _us_open_break,
           source="assistant reasoning", author="agent"),
    Family("E-1054", "Round-number level rejection",
           "Limit orders cluster at round index levels; a bar that pokes through a round level and closes back "
           "under (over) it is absorbed there, so fade it.",
           {"step": [500, 1000, 2000]}, _round_reject, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1055", "Volume climax at a new extreme",
           "A heavy-volume bar that makes a new session extreme but closes in its far half shows absorbed "
           "aggressive flow; fade it.",
           {"vol_k": [1.5, 2.0, 3.0]}, _climax_fade, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1056", "Previous close reclaim",
           "The prior session close is where overnight holders are flat; the first close across it after the "
           "price sat on the other side for a while shifts the day's bias; follow.",
           {"hold_min": [10, 20, 40]}, _prev_close_cross, source="assistant reasoning", author="agent"),
    Family("E-1057", "Index leads the dollar",
           "Sharp WIN moves reflect risk-on/off flows that usually push the dollar the opposite way; if WDO "
           "has not yet moved against a sharp WIN move, trade WDO toward it.",
           {"move_min": [5, 10, 15], "k": [1.0, 1.5, 2.0]}, _index_lead_wdo, markets=("WDO",),
           source="assistant reasoning", author="agent"),
]
