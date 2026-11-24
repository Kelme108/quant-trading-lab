"""Conveyor batch B-079 (agent, 2026-11-23). Mixed: narrow-bar breaks, stochastic fade, gap-bar fade, volume stairs,
DI cross, counter-trend shock, end-of-day midpoint pull, two-bar midpoint reclaim, dry-up expansion, regression slope."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _nr_break(ctx, p):
    n = int(p["n"])
    rng = ctx.h - ctx.l
    minr = ctx.roll(rng, n, "min")
    r1 = ctx.prev(rng, 1)
    nr = (r1 <= ctx.prev(minr, 1)) & (r1 > 0)
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    return (nr & (ctx.c > h1)).astype(int) - (nr & (ctx.c < l1)).astype(int)


def _stoch_fade(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    hh, ll = ctx.roll(ctx.h, nb, "max"), ctx.roll(ctx.l, nb, "min")
    with np.errstate(all="ignore"):
        k = (ctx.c - ll) / (hh - ll)
    k1 = ctx.prev(k, 1)
    short = (k1 >= th) & (k < th)
    long = (k1 <= 1 - th) & (k > 1 - th)
    return long.astype(int) - short.astype(int)


def _gap_bar_fade(ctx, p):
    k = p["k"]
    avg = ctx.prev(ctx.roll(ctx.h - ctx.l, 20, "mean"), 1)
    gap = ctx.o - ctx.prev(ctx.c, 1)
    short = (gap > k * avg) & (ctx.c < ctx.o)
    long = (gap < -k * avg) & (ctx.c > ctx.o)
    return long.astype(int) - short.astype(int)


def _volume_stairs(ctx, p):
    n = int(p["n"])
    up = ((ctx.c > ctx.prev(ctx.c, 1)) & (ctx.v > ctx.prev(ctx.v, 1))).astype(float)
    dn = ((ctx.c < ctx.prev(ctx.c, 1)) & (ctx.v > ctx.prev(ctx.v, 1))).astype(float)
    u = ctx.roll(up, n, "min") == 1
    d = ctx.roll(dn, n, "min") == 1
    return ctx.cross(u).astype(int) - ctx.cross(d).astype(int)


def _di_cross(ctx, p):
    nb, m = ctx.bars(p["win_min"]), p["margin"]
    uh = ctx.h - ctx.prev(ctx.h, 1)
    dl = ctx.prev(ctx.l, 1) - ctx.l
    pdm = np.where((uh > dl) & (uh > 0), uh, 0.0)
    mdm = np.where((dl > uh) & (dl > 0), dl, 0.0)
    sp, sm = ctx.roll(pdm, nb, "sum"), ctx.roll(mdm, nb, "sum")
    with np.errstate(all="ignore"):
        d = (sp - sm) / (sp + sm)
    return ctx.cross(d > m).astype(int) - ctx.cross(d < -m).astype(int)


def _counter_shock(ctx, p):
    k, nb = p["k"], ctx.bars(p["trend_min"])
    avg = ctx.prev(ctx.roll(ctx.h - ctx.l, 20, "mean"), 1)
    ema = ctx.cached(("ema_cs", nb), lambda: ctx.ema(ctx.c, nb))
    up = (ctx.prev(ctx.c, 1) > ctx.prev(ema, 1)) & (ema > ctx.prev(ema, 3))
    dn = (ctx.prev(ctx.c, 1) < ctx.prev(ema, 1)) & (ema < ctx.prev(ema, 3))
    big = (ctx.h - ctx.l) > k * avg
    long = up & big & (ctx.c < ctx.o)
    short = dn & big & (ctx.c > ctx.o)
    return long.astype(int) - short.astype(int)


def _eod_mid_pull(ctx, p):
    f, w = p["f"], p["win_min"]
    sh, sl = ctx.session_high(include_current=True), ctx.session_low(include_current=True)
    mid, rng = (sh + sl) / 2, sh - sl
    with np.errstate(all="ignore"):
        dev = (ctx.c - mid) / rng
    win = (ctx.minutes_to_close <= w) & (ctx.minutes_to_close >= 15)
    short = win & (dev > f)
    long = win & (dev < -f)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _midpoint_reclaim(ctx, p):
    k = p["k"]
    avg = ctx.prev(ctx.roll(ctx.h - ctx.l, 20, "mean"), 2)
    o1, c1 = ctx.prev(ctx.o, 1), ctx.prev(ctx.c, 1)
    mid1 = (o1 + c1) / 2
    big_dn = (o1 - c1) >= k * avg
    big_up = (c1 - o1) >= k * avg
    long = big_dn & (ctx.c > ctx.o) & (ctx.c > mid1) & (ctx.c < o1)
    short = big_up & (ctx.c < ctx.o) & (ctx.c < mid1) & (ctx.c > o1)
    return long.astype(int) - short.astype(int)


def _dryup_expand(ctx, p):
    q, k = p["quiet"], p["expand"]
    med = ctx.cached("vol_med_b079", lambda: ctx.same_minute(ctx.v, "median"))
    quiet = (ctx.prev(ctx.v, 1) < q * ctx.prev(med, 1)) & (ctx.prev(ctx.v, 2) < q * ctx.prev(med, 2)) & \
            (ctx.prev(ctx.v, 3) < q * ctx.prev(med, 3))
    big = ctx.v > k * med
    return (quiet & big & (ctx.c > ctx.o)).astype(int) - (quiet & big & (ctx.c < ctx.o)).astype(int)


def _slope_cross(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th_bp"] * 1e-4
    b = ctx.bar_in_day.astype(float)
    sxy = ctx.roll(b * ctx.c, nb, "sum")
    sy = ctx.roll(ctx.c, nb, "sum")
    bbar = ctx.roll(b, nb, "mean")
    denom = nb * (nb * nb - 1) / 12.0
    if denom <= 0:
        return np.zeros(ctx.n, dtype=int)
    slope = (sxy - bbar * sy) / denom
    t = slope * nb / ctx.c
    return ctx.cross(t > th).astype(int) - ctx.cross(t < -th).astype(int)


FAMILIES = [
    Family("E-788", "Narrowest-bar break",
           "The narrowest bar of the last n bars marks stalled quoting; the next bar closing beyond its extreme "
           "shows which side's resting orders were absorbed; follow.",
           {"n": [5, 8, 12]}, _nr_break, source="assistant reasoning", author="agent"),
    Family("E-789", "Stochastic re-entry fade",
           "A close that leaves the top (bottom) of the recent range marks the end of the push by aggressive "
           "buyers (sellers); fade the exit from the extreme zone.",
           {"win_min": [30, 60, 120], "th": [0.8, 0.9]}, _stoch_fade, source="assistant reasoning", author="agent"),
    Family("E-790", "Bar-open gap fade",
           "A bar opening far from the previous close is a burst of market orders; if the bar then closes back "
           "against the burst, the aggressors are underwater; fade the gap.",
           {"k": [0.5, 1.0, 1.5]}, _gap_bar_fade, source="assistant reasoning", author="agent", markets=("WIN",)),
    Family("E-791", "Rising-volume close stairs",
           "Consecutive higher closes each on larger volume show participation growing with the move; follow once.",
           {"n": [2, 3, 4]}, _volume_stairs, source="assistant reasoning", author="agent"),
    Family("E-792", "Directional-movement balance cross",
           "When upward bar extensions dominate downward ones over a window (Wilder directional movement), "
           "buyers are repeatedly pushing past prior highs; follow the crossing.",
           {"win_min": [15, 30, 60], "margin": [0.2, 0.3, 0.4]}, _di_cross, source="assistant reasoning",
           author="agent", markets=("WIN",)),
    Family("E-793", "Counter-trend shock bar fade",
           "In a trending tape a large bar against the trend is often a liquidity sweep by a single large order; "
           "trade back with the trend.",
           {"k": [1.5, 2.0, 3.0], "trend_min": [30, 60, 120]}, _counter_shock, source="assistant reasoning",
           author="agent", markets=("WIN",)),
    Family("E-794", "End-of-day midpoint pull",
           "Late in the session, positions are squared toward the day's midpoint; price far from it in the last "
           "hour drifts back as day traders close.",
           {"f": [0.3, 0.35, 0.4], "win_min": [45, 75]}, _eod_mid_pull, source="assistant reasoning",
           author="agent", markets=("WIN",)),
    Family("E-795", "Two-bar midpoint reclaim",
           "After a large bar, an opposite bar that retakes more than half of its body without exceeding its "
           "open shows the first move was rejected; trade the rejection.",
           {"k": [1.0, 1.5, 2.0]}, _midpoint_reclaim, source="candlestick piercing/dark-cloud pattern",
           author="agent", markets=("WIN",)),
    Family("E-796", "Volume dry-up then expansion",
           "Three bars of very thin volume mean the book was left alone; the first bar with heavy volume shows "
           "the side that finally acts; follow its colour.",
           {"quiet": [0.5, 0.7], "expand": [1.5, 2.0, 3.0]}, _dryup_expand, source="volume-price analysis",
           author="agent", markets=("WIN",)),
    Family("E-797", "Regression slope threshold cross",
           "A least-squares line through recent closes that becomes steep enough shows persistent one-sided "
           "pressure rather than one noisy spike; follow the crossing.",
           {"win_min": [30, 60], "th_bp": [5, 10, 15]}, _slope_cross, source="assistant reasoning",
           author="agent", markets=("WIN",)),
]
