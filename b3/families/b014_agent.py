"""Conveyor batch B-014 (agent, 2026-11-18). Regime-conditioned fades (choppy, quiet, thin), channel/IB/hourly levels and swing-leg stretch on WIN."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _absdiff(ctx):
    return ctx.cached("absdiff1", lambda: np.nan_to_num(np.abs(ctx.c - ctx.prev(ctx.c, 1)), nan=0.0))


def _first_window(ctx, nb, x, how):
    s = pd.Series(np.where(ctx.bar_in_day < nb, x, np.nan))
    return s.groupby(ctx.day).transform(how).to_numpy()


# E-138 ------------------------------------------------------------------------------------------
def _er_micro_fade(ctx, p):
    nb = ctx.bars(p["win_min"])
    net = np.abs(ctx.c - ctx.prev(ctx.c, nb))
    path = ctx.roll(_absdiff(ctx), nb, "sum")
    er = np.where(path > 0, net / np.where(path > 0, path, 1.0), np.nan)
    choppy = er < p["er_th"]
    hi3 = ctx.roll(ctx.h, 3, "max", include_current=False)
    lo3 = ctx.roll(ctx.l, 3, "min", include_current=False)
    short = ctx.cross(choppy & (ctx.c > hi3))
    long = ctx.cross(choppy & (ctx.c < lo3))
    return long.astype(int) - short.astype(int)


# E-139 ------------------------------------------------------------------------------------------
def _regression_dip(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    x = ctx.bar_in_day.astype(float)
    y = ctx.c - ctx.day_open
    mx = ctx.roll(x, nb, "mean", include_current=False)
    my = ctx.roll(y, nb, "mean", include_current=False)
    mxx = ctx.roll(x * x, nb, "mean", include_current=False)
    mxy = ctx.roll(x * y, nb, "mean", include_current=False)
    myy = ctx.roll(y * y, nb, "mean", include_current=False)
    varx = mxx - mx * mx
    vary = myy - my * my
    cov = mxy - mx * my
    ok = (varx > 0) & (vary > 0)
    sx = np.where(ok, varx, 1.0)
    sy = np.where(ok, vary, 1.0)
    slope = cov / sx
    r2 = np.where(ok, cov * cov / (sx * sy), 0.0)
    sd = np.sqrt(np.clip(sy * (1.0 - r2), 0.0, None))
    line = my + slope * (x - mx)
    straight = ok & (r2 >= 0.6) & (sd > 0)
    long = ctx.cross(straight & (slope > 0) & (y < line - k * sd))
    short = ctx.cross(straight & (slope < 0) & (y > line + k * sd))
    return long.astype(int) - short.astype(int)


# E-140 ------------------------------------------------------------------------------------------
def _ib_extension_fade(ctx, p):
    nb, m = ctx.bars(p["ib_min"]), p["m"]
    ibh = _first_window(ctx, nb, ctx.h, "max")
    ibl = _first_window(ctx, nb, ctx.l, "min")
    w = ibh - ibl
    done = (ctx.bar_in_day >= nb) & (w > 0)
    pc = ctx.prev(ctx.c, 1)
    short = np.zeros(ctx.n, bool)
    long = np.zeros(ctx.n, bool)
    for j in (1, 2, 3, 4):
        up = ibh + j * m * w
        dn = ibl - j * m * w
        short |= done & (pc < up) & (ctx.h >= up) & (ctx.c < up)
        long |= done & (pc > dn) & (ctx.l <= dn) & (ctx.c > dn)
    return long.astype(int) - short.astype(int)


# E-141 ------------------------------------------------------------------------------------------
def _quiet_poke_fade(ctx, p):
    n30 = ctx.bars(30)
    rng30 = ctx.roll(ctx.h, n30, "max", include_current=False) - ctx.roll(ctx.l, n30, "min", include_current=False)
    typ = ctx.cached(("rng30_med", n30), lambda: ctx.same_minute(rng30, "median"))
    quiet = rng30 < p["q"] * typ
    lb = ctx.bars(p["lb_min"])
    hi = ctx.roll(ctx.h, lb, "max", include_current=False)
    lo = ctx.roll(ctx.l, lb, "min", include_current=False)
    short = quiet & (ctx.h > hi) & (ctx.c < hi)
    long = quiet & (ctx.l < lo) & (ctx.c > lo)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-142 ------------------------------------------------------------------------------------------
def _prev_hour_close_hold(ctx, p):
    hr = (ctx.minute // 60).astype(np.int64)
    key = ctx.day.astype(np.int64) * 100 + hr
    df = pd.DataFrame({"k": key, "o": ctx.o, "c": ctx.c, "h": ctx.h, "l": ctx.l})
    g = df.groupby("k").agg(o=("o", "first"), c=("c", "last"), h=("h", "max"), l=("l", "min"))
    pk = pd.Series(key - 1)
    po, pcl = pk.map(g["o"]).to_numpy(float), pk.map(g["c"]).to_numpy(float)
    ph, pl = pk.map(g["h"]).to_numpy(float), pk.map(g["l"]).to_numpy(float)
    prng = ph - pl
    strong = prng > 0
    body = pcl - po
    up_hour = strong & (body >= p["frac"] * prng)
    dn_hour = strong & (-body >= p["frac"] * prng)
    c1 = ctx.prev(ctx.c, 1)
    long = up_hour & (c1 > pcl) & (ctx.l <= pcl) & (ctx.c > pcl)
    short = dn_hour & (c1 < pcl) & (ctx.h >= pcl) & (ctx.c < pcl)
    return long.astype(int) - short.astype(int)


# E-143 ------------------------------------------------------------------------------------------
def _vacuum_bar_fade(ctx, p):
    rng = ctx.h - ctx.l
    tr = ctx.cached("rng_med", lambda: ctx.same_minute(rng, "median"))
    tv = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    body = ctx.c - ctx.o
    vac = (tr > 0) & (rng >= p["k"] * tr) & (ctx.v <= p["vr"] * tv) & (np.abs(body) >= 0.5 * rng)
    return (vac & (body < 0)).astype(int) - (vac & (body > 0)).astype(int)


# E-144 ------------------------------------------------------------------------------------------
def _calm_momentum(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    mom = ctx.c - ctx.prev(ctx.c, nb)
    typ = ctx.cached(("absmom", nb), lambda: ctx.prev_sessions(np.abs(mom), "mean"))
    n2 = ctx.bars(120)
    path = ctx.roll(_absdiff(ctx), n2, "sum", include_current=False)
    tpath = ctx.cached(("path_med", n2), lambda: ctx.same_minute(path, "median"))
    calm = path < tpath
    long = ctx.cross(mom >= k * typ) & calm
    short = ctx.cross(mom <= -k * typ) & calm
    return long.astype(int) - short.astype(int)


# E-145 ------------------------------------------------------------------------------------------
def _channel_mid_rotation(ctx, p):
    nb = ctx.bars(p["win_min"])
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    mid = 0.5 * (hi + lo)
    m = ctx.bars(15)
    top = ctx.roll((ctx.h >= hi).astype(float), m, "max", include_current=False) == 1
    bot = ctx.roll((ctx.l <= lo).astype(float), m, "max", include_current=False) == 1
    short = ctx.cross(ctx.c < mid) & top & ~bot
    long = ctx.cross(ctx.c > mid) & bot & ~top
    return long.astype(int) - short.astype(int)


# E-146 ------------------------------------------------------------------------------------------
def _leg_arrays(ctx, r):
    def build():
        n = ctx.n
        o, h, l, c, day = ctx.o, ctx.h, ctx.l, ctx.c, ctx.day
        length = np.full(n, np.nan)
        direction = np.zeros(n, dtype=np.int8)
        cur_day, d, start, hi, lo, ext = None, 0, 0.0, 0.0, 0.0, 0.0
        for t in range(n):
            if day[t] != cur_day:
                cur_day, d, start, hi, lo = day[t], 0, o[t], h[t], l[t]
            if d == 0:
                hi, lo = max(hi, h[t]), min(lo, l[t])
                if hi - start >= r * start and hi - start >= start - lo:
                    d, ext = 1, hi
                elif start - lo >= r * start:
                    d, ext = -1, lo
            elif d == 1:
                if h[t] > ext:
                    ext = h[t]
                if c[t] <= ext * (1.0 - r):
                    d, start, ext = -1, ext, l[t]
            else:
                if l[t] < ext:
                    ext = l[t]
                if c[t] >= ext * (1.0 + r):
                    d, start, ext = 1, ext, h[t]
            if d != 0:
                length[t] = abs(ext - start)
                direction[t] = d
        return length, direction
    return ctx.cached(("legs", r), build)


def _leg_stretch_fade(ctx, p):
    length, direction = _leg_arrays(ctx, p["r"])
    typ = ctx.cached(("leg_typ", p["r"]), lambda: ctx.prev_sessions(length, "mean"))
    stretched = length >= p["k"] * typ
    body = ctx.c - ctx.o
    short = ctx.cross(stretched & (direction == 1) & (body < 0))
    long = ctx.cross(stretched & (direction == -1) & (body > 0))
    return long.astype(int) - short.astype(int)


# E-147 ------------------------------------------------------------------------------------------
def _quiet_drift_fade(ctx, p):
    run = int(p["run"])
    rng = ctx.h - ctx.l
    tr = ctx.cached("rng_med", lambda: ctx.same_minute(rng, "median"))
    small = ((tr > 0) & (rng < p["q"] * tr)).astype(float)
    c1 = ctx.prev(ctx.c, 1)
    up = (ctx.c > c1).astype(float)
    dn = (ctx.c < c1).astype(float)
    all_small = ctx.roll(small, run, "min") == 1
    drift_up = all_small & (ctx.roll(up, run, "min") == 1)
    drift_dn = all_small & (ctx.roll(dn, run, "min") == 1)
    return ctx.cross(drift_dn).astype(int) - ctx.cross(drift_up).astype(int)


FAMILIES = [
    Family("E-138", "Choppy-window micro-break fade",
           "When Kaufman's efficiency ratio over the last 30-60 minutes is low, price is churning between liquidity "
           "providers on both sides and nobody initiates; a close beyond the previous three bars' high/low in such a "
           "window is a small order pushing through a thin quote, which the market makers fade, so fade it.",
           {"er_th": [0.15, 0.25, 0.35], "win_min": [30, 60]}, _er_micro_fade,
           markets=("WIN",), source="LuxAlgo - Kaufman Efficiency Ratio https://www.luxalgo.com/library/concept/kaufman-efficiency-ratio.md",
           author="agent"),
    Family("E-139", "Regression-channel dip in a straight trend",
           "When the closes of the last hour sit on a straight line (high R-squared), one participant is working a "
           "steady parent order; a close more than k residual deviations against that line is a short-term "
           "liquidity seller (buyer) the parent order absorbs, so buy the dip below a rising line (mirror).",
           {"win_min": [30, 60, 90], "k": [1.5, 2.0, 2.5]}, _regression_dip,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-140", "Initial-balance extension level fade",
           "Market Profile traders project multiples of the initial-balance width (first 30/60 minutes) beyond the IB "
           "high/low and scale out there; a bar reaching such an extension from the inside and closing back short of "
           "it shows those take-profits absorbing the push, so fade back toward the IB.",
           {"ib_min": [30, 60], "m": [0.5, 1.0]}, _ib_extension_fade,
           markets=("WIN",), source="LuxAlgo - Initial Balance https://www.luxalgo.com/library/concept/initial-balance/",
           author="agent"),
    Family("E-141", "Quiet-tape range poke fade",
           "When the realized range of the last 30 minutes is well below what is normal at that minute, no informed "
           "flow is active and the book is balanced; a bar poking beyond the recent high/low and closing back inside "
           "is a small stop run with nobody to follow it, so fade it.",
           {"q": [0.6, 0.8, 1.0], "lb_min": [10, 20]}, _quiet_poke_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-142", "Prior-hour close retest hold",
           "A completed hourly candle that closed strongly (large body for its range) leaves its close as the price "
           "where the hour's winners marked their position; a return to that close that holds on the hour's side "
           "meets their adds and the late counter-traders are trapped, so trade in the hour's direction.",
           {"frac": [0.3, 0.5, 0.7]}, _prev_hour_close_hold,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-143", "Vacuum-bar fade",
           "A bar with a range far above normal for its minute but only normal-or-less volume moved through an "
           "empty book (quotes pulled for a moment), not on new information; when quotes refill, liquidity providers "
           "lean the price back, so fade the bar's direction.",
           {"k": [1.5, 2.0, 2.5], "vr": [0.75, 1.0]}, _vacuum_bar_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-144", "Calm-regime momentum onset",
           "Volatility-managed momentum: a short-horizon move larger than usual is more likely informed when the "
           "preceding two hours were calm (summed absolute moves below normal for the minute), because noise traders "
           "and shock unwinds are absent; follow the move only in calm regimes.",
           {"win_min": [10, 15, 30], "k": [1.0, 1.5, 2.0]}, _calm_momentum,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-145", "Channel-midline rotation follow",
           "After price tags the edge of its recent channel and then closes back through the channel midline, the "
           "edge buyers are under water and the rotation traders target the opposite edge; follow the midline cross "
           "toward the other side.",
           {"win_min": [30, 60, 90]}, _channel_mid_rotation,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-146", "Swing-leg stretch fade",
           "A zigzag swing leg (reversal threshold r) whose length is far above the typical leg of the last 20 "
           "sessions has outrun the swing traders' usual targets; once a bar closes against the leg, their "
           "profit-taking and the late entrants' exits revert it, so fade the stretched leg.",
           {"r": [0.001, 0.002], "k": [2.0, 3.0]}, _leg_stretch_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-147", "Quiet-drift fade",
           "Several consecutive closes in one direction on bars much narrower than normal for their minute is quote "
           "shading by liquidity providers in an empty market, not initiative buying; with no committed side behind "
           "it the drift reverts, so fade the bar that completes the drift.",
           {"run": [3, 4, 5], "q": [0.5, 0.75]}, _quiet_drift_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
]
