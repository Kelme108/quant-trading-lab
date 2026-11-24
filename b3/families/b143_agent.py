"""Conveyor batch B-143 (agent, 2026-11-24). Anchors frozen after a window, candle sequences that erase or confirm,
swing-count regimes, cross-market VWAP agreement, nested clock opens and an absolute-point thrust."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _blk_open(ctx, blk):
    """Open of the first bar of the clock block (blk minutes) the bar belongs to. Uses only bars <= t."""
    key = ctx.cached(("blk_key", blk), lambda: ctx.day.astype(np.int64) * 100000
                     + (np.asarray(ctx.minute).astype(np.int64) // blk))
    return ctx.cached(("blk_open", blk), lambda: pd.Series(ctx.o).groupby(key).transform("first").to_numpy())


def _hour_vwap_cross(ctx, p):
    dw = ctx.bars(p["dwell_min"])
    mn = np.asarray(ctx.minute).astype(np.int64)
    key = ctx.cached("hr_key", lambda: ctx.day.astype(np.int64) * 100000 + mn // 60)
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    pv = pd.Series(tp * ctx.v).groupby(key).cumsum().to_numpy()
    vv = pd.Series(ctx.v).groupby(key).cumsum().to_numpy()
    hv = np.where(vv > 0, pv / np.where(vv > 0, vv, 1.0), np.nan)
    pos = (mn % 60) // ctx.tf
    below = (ctx.c < hv).astype(float)
    above = (ctx.c > hv).astype(float)
    wb = ctx.roll(below, dw, "min", include_current=False) == 1
    wa = ctx.roll(above, dw, "min", include_current=False) == 1
    up = wb & (ctx.c > hv) & (pos >= dw)
    dn = wa & (ctx.c < hv) & (pos >= dw)
    return up.astype(int) - dn.astype(int)


def _ib_vwap_cross(ctx, p):
    nb, dw = ctx.bars(p["ib_min"]), ctx.bars(p["dwell_min"])
    vw = ctx.vwap()
    mark = np.where(ctx.bar_in_day == nb - 1, vw, np.nan)
    ib = pd.Series(mark).groupby(ctx.day).transform("max").to_numpy()
    ib = np.where(ctx.bar_in_day >= nb, ib, np.nan)          # the frozen value is only used after the window ended
    below = (ctx.c < ib).astype(float)
    above = (ctx.c > ib).astype(float)
    wb = ctx.roll(below, dw, "min", include_current=False) == 1
    wa = ctx.roll(above, dw, "min", include_current=False) == 1
    up = wb & (ctx.c > ib)
    dn = wa & (ctx.c < ib)
    return up.astype(int) - dn.astype(int)


def _run_erase(ctx, p):
    k, trav = int(p["run"]), p["travel"]
    red = (ctx.c < ctx.o).astype(float)
    grn = (ctx.c > ctx.o).astype(float)
    allred = np.ones(ctx.n, bool)
    allgrn = np.ones(ctx.n, bool)
    for j in range(1, k + 1):
        allred &= ctx.prev(red, j) == 1
        allgrn &= ctx.prev(grn, j) == 1
    nb = ctx.bars(30)
    avg = ctx.cached(("avgrange", nb), lambda: ctx.roll(ctx.h - ctx.l, nb, "mean", include_current=False))
    start_open = ctx.prev(ctx.o, k)
    travel = np.abs(ctx.prev(ctx.c, 1) - start_open)
    big = travel >= trav * avg
    long = allred & big & (ctx.c > ctx.o) & (ctx.c > start_open)
    short = allgrn & big & (ctx.c < ctx.o) & (ctx.c < start_open)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _block_open_reclaim(ctx, p):
    blk = int(p["block"])
    dw = max(1, int(round(blk * p["dwell_frac"] / ctx.tf)))
    bo = _blk_open(ctx, blk)
    pos = (np.asarray(ctx.minute).astype(np.int64) % blk) // ctx.tf
    below = (ctx.c < bo).astype(float)
    above = (ctx.c > bo).astype(float)
    wb = ctx.roll(below, dw, "min", include_current=False) == 1
    wa = ctx.roll(above, dw, "min", include_current=False) == 1
    up = wb & (ctx.c > bo) & (pos >= dw)
    dn = wa & (ctx.c < bo) & (pos >= dw)
    return up.astype(int) - dn.astype(int)


def _swing_counts(ctx, frac):
    def build():
        c = ctx.c.tolist()
        day = ctx.day.tolist()
        dop = ctx.day_open.tolist()
        n = len(c)
        out = np.zeros(n)
        i = 0
        while i < n:
            j = i
            while j < n and day[j] == day[i]:
                j += 1
            thr = frac * dop[i]
            dirn, hi, lo, sw = 0, c[i], c[i], 0
            for t in range(i, j):
                x = c[t]
                if dirn == 0:
                    if x > hi:
                        hi = x
                    if x < lo:
                        lo = x
                    if x - lo >= thr:
                        dirn, hi = 1, x
                    elif hi - x >= thr:
                        dirn, lo = -1, x
                elif dirn == 1:
                    if x > hi:
                        hi = x
                    elif hi - x >= thr:
                        dirn, lo, sw = -1, x, sw + 1
                else:
                    if x < lo:
                        lo = x
                    elif x - lo >= thr:
                        dirn, hi, sw = 1, x, sw + 1
                out[t] = sw
            i = j
        return out
    return ctx.cached(("swings", frac), build)


def _swing_rotation_fade(ctx, p):
    sw = _swing_counts(ctx, p["swing_frac"])
    nb = ctx.bars(15)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    rot = sw >= p["min_swings"]
    short = rot & (ctx.c > hi)
    long = rot & (ctx.c < lo)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _three_inside(ctx, p):
    k = p["body_k"]
    body = np.abs(ctx.c - ctx.o)
    nb = ctx.bars(30)
    avg = ctx.cached(("avgbody", nb), lambda: ctx.roll(body, nb, "mean", include_current=False))
    o1, c1 = ctx.prev(ctx.o, 2), ctx.prev(ctx.c, 2)
    o2, c2 = ctx.prev(ctx.o, 1), ctx.prev(ctx.c, 1)
    bull = (c1 < o1) & ((o1 - c1) >= k * avg) & (c2 > o2) & (o2 >= c1) & (c2 <= o1) & (ctx.c > ctx.o) & (ctx.c > o1)
    bear = (c1 > o1) & ((c1 - o1) >= k * avg) & (c2 < o2) & (o2 <= c1) & (c2 >= o1) & (ctx.c < ctx.o) & (ctx.c < o1)
    return ctx.cross(bull).astype(int) - ctx.cross(bear).astype(int)


def _stick_sandwich(ctx, p):
    tol = p["tol"]
    o2, c2 = ctx.prev(ctx.o, 2), ctx.prev(ctx.c, 2)
    o1, c1 = ctx.prev(ctx.o, 1), ctx.prev(ctx.c, 1)
    near = np.abs(ctx.c - c2) <= tol * ctx.c
    long = (c2 < o2) & (c1 > o1) & (c1 > o2) & (ctx.c < ctx.o) & near
    short = (c2 > o2) & (c1 < o1) & (c1 < o2) & (ctx.c > ctx.o) & near
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _vwap_hold_other_side(ctx, p):
    n = ctx.bars(p["dwell_min"])
    vw = ctx.vwap()
    oc = ctx.other_close()
    omean = ctx.cached("other_mean", lambda: pd.Series(oc).groupby(ctx.day).transform(
        lambda z: z.expanding().mean()).to_numpy())
    above = (ctx.c > vw).astype(float)
    below = (ctx.c < vw).astype(float)
    wa = ctx.roll(above, n, "min", include_current=False) == 1
    wb = ctx.roll(below, n, "min", include_current=False) == 1
    long = wa & (ctx.l <= vw) & (ctx.c > vw) & (oc < omean)
    short = wb & (ctx.h >= vw) & (ctx.c < vw) & (oc > omean)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _nested_open_align(ctx, p):
    m = p["margin"]
    fo, so = _blk_open(ctx, int(p["fast"])), _blk_open(ctx, int(p["slow"]))
    up = (ctx.c > fo * (1 + m)) & (ctx.c > so * (1 + m))
    dn = (ctx.c < fo * (1 - m)) & (ctx.c < so * (1 - m))
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _point_thrust(ctx, p):
    pts = p["points"]
    body = ctx.c - ctx.o
    rng = ctx.h - ctx.l
    up = (body >= pts) & ((ctx.h - ctx.c) <= rng / 3.0)
    dn = (body <= -pts) & ((ctx.c - ctx.l) <= rng / 3.0)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


FAMILIES = [
    Family("E-1428", "Clock-hour anchored VWAP reclaim",
           "Desks that work orders by the clock hour benchmark the VWAP that restarts at each hour; after the price "
           "sat on one side of that hour's VWAP for a while, the first close back across it puts the hour's "
           "participants on the other side of their average cost, and their covering plus new entries push on.",
           {"dwell_min": [5, 10, 15]}, _hour_vwap_cross, source="assistant reasoning", author="agent"),
    Family("E-1429", "Frozen first-window VWAP cross",
           "The VWAP of the opening 30-90 minutes freezes into the average cost of the opening institutions' "
           "inventory; unlike the running session VWAP it no longer moves, so a first close back across it after a "
           "dwell flips that cohort between profit and loss and they defend or abandon it together; follow the cross.",
           {"ib_min": [30, 60, 90], "dwell_min": [5, 10, 20]}, _ib_vwap_cross, source="assistant reasoning",
           author="agent"),
    Family("E-1430", "Whole-run erase bar",
           "After a run of same-colour bars, a single bar that closes beyond the OPEN of the first bar of the run "
           "has erased the whole run in one auction: everyone who traded the run is under water at once and their "
           "exits join the new side; follow the erasing bar.",
           {"run": [2, 3, 4], "travel": [0.0, 1.0, 2.0]}, _run_erase, source="assistant reasoning", author="agent"),
    Family("E-1431", "Short clock-block open reclaim",
           "Chart traders and bots mark the open of every 10/15/30-minute candle; after price stayed on one side of "
           "the current candle's open for part of the candle, a close back across flips the candle's colour, "
           "triggering the stops and reversals of those positioned for the old colour; follow the flip.",
           {"block": [10, 15, 30], "dwell_frac": [0.4, 0.6]}, _block_open_reclaim, source="assistant reasoning",
           author="agent"),
    Family("E-1432", "Swing-count rotation fade",
           "A session whose price has already completed several full swings of a fixed size (counted with a "
           "zigzag) is a rotational auction where both edges are defended; a short-term break of the 15-minute "
           "box in such a day is one more swing end that liquidity providers lean against, so fade it.",
           {"swing_frac": [0.001, 0.0015, 0.002], "min_swings": [2, 3, 4]}, _swing_rotation_fade,
           source="assistant reasoning", author="agent"),
    Family("E-1433", "Three-inside confirmation",
           "A large bar, a smaller opposite bar inside its body (the push stalls), and a third bar that closes "
           "beyond the first bar's open shows the first bar's aggressors were fully absorbed and the other side "
           "took the whole range back; follow the confirming bar.",
           {"body_k": [0.5, 1.0, 1.5]}, _three_inside, source="assistant reasoning", author="agent"),
    Family("E-1434", "Equal-close stick sandwich",
           "Two same-colour bars closing at the same price with an opposite bar between them mean a resting order "
           "stopped the price at that level twice; sellers (buyers) pushed back to the same close and could not "
           "go through, so trade away from the level.",
           {"tol": [0.0, 0.00005, 0.0001]}, _stick_sandwich, source="assistant reasoning", author="agent"),
    Family("E-1435", "VWAP hold confirmed by the other market's side",
           "WIN and WDO move inversely when foreign flow drives both; a touch of VWAP that closes back on the "
           "trend side is a stronger hold when the other market sits on the opposite side of its own session "
           "average, because the macro flow agrees with the dip being bought (sold).",
           {"dwell_min": [10, 20, 30]}, _vwap_hold_other_side, source="assistant reasoning", author="agent"),
    Family("E-1436", "Nested clock-open alignment",
           "When the price is beyond the open of the current fast clock candle and of the current slow clock "
           "candle by a margin, every horizon of candle-reading desks sees the same colour and nobody is on the "
           "right side of both; follow the first bar where the alignment appears.",
           {"fast": [15, 30], "slow": [60, 120], "margin": [0.0005, 0.001]}, _nested_open_align,
           source="assistant reasoning", author="agent"),
    Family("E-1437", "Exit-scale point thrust",
           "A single bar that travels a fixed absolute number of index points (a size comparable to the trade "
           "scale, whatever the volatility regime) and closes in the top/bottom third is a stop cascade or "
           "parent-order burst that has not met resistance; follow it.",
           {"points": [60, 90, 120]}, _point_thrust, markets=("WIN",), source="assistant reasoning",
           author="agent"),
]
