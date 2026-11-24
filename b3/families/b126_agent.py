"""Conveyor batch B-126 (agent, 2026-11-24). Mixed intraday ideas on WIN: round numbers, compression, exhaustion, hour levels."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _lag(ctx, x, i):
    return x if i == 0 else ctx.prev(x, i)


def _round_number(ctx, p):
    s = float(p["step"])
    pc = ctx.prev(ctx.c, 1)
    up = (np.floor(pc / s) + 1.0) * s
    dn = np.ceil(pc / s) * s - s
    short = (ctx.h >= up) & (ctx.c < up)
    long = (ctx.l <= dn) & (ctx.c > dn)
    return long.astype(int) - short.astype(int)


def _nr_break(ctx, p):
    n = int(p["n"])
    rng = ctx.h - ctx.l
    narrow = (rng == ctx.roll(rng, n, "min")) & (rng > 0)
    pn = ctx.prev(narrow.astype(float), 1) == 1
    long = pn & (ctx.c > ctx.prev(ctx.h, 1))
    short = pn & (ctx.c < ctx.prev(ctx.l, 1))
    return long.astype(int) - short.astype(int)


def _lowvol_extreme(ctx, p):
    k = p["vol_k"]
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    quiet = ctx.v < k * med
    newhi = ctx.h > ctx.session_high()
    newlo = ctx.l < ctx.session_low()
    short = newhi & quiet & (ctx.c > ctx.o)
    long = newlo & quiet & (ctx.c < ctx.o)
    return long.astype(int) - short.astype(int)


def _shrinking_bodies(ctx, p):
    m = int(p["m"])
    d = ctx.c - ctx.o
    body = np.abs(d)
    up = np.ones(ctx.n, bool)
    dn = np.ones(ctx.n, bool)
    for i in range(m):
        di = _lag(ctx, d, i)
        up &= di > 0
        dn &= di < 0
        if i < m - 1:
            shrink = _lag(ctx, body, i) < _lag(ctx, body, i + 1)
            up &= shrink
            dn &= shrink
    return ctx.cross(dn).astype(int) - ctx.cross(up).astype(int)


def _squeeze_release(ctx, p):
    n, q = ctx.bars(p["n_min"]), p["q"]
    mu = ctx.roll(ctx.c, n, "mean")
    sd = ctx.roll(ctx.c, n, "std")
    width = 4.0 * sd / mu
    typ = ctx.cached(("bbw", n), lambda: ctx.prev_sessions(np.nan_to_num(width, nan=0.0), "mean"))
    squeezed = ctx.prev(width, 1) < q * typ
    long = squeezed & (ctx.c > mu + 2.0 * sd)
    short = squeezed & (ctx.c < mu - 2.0 * sd)
    return long.astype(int) - short.astype(int)


def _z_stretch(ctx, p):
    n, k = ctx.bars(p["n_min"]), p["k"]
    mu = ctx.roll(ctx.c, n, "mean")
    sd = ctx.roll(ctx.c, n, "std")
    with np.errstate(all="ignore"):
        z = np.where(sd > 0, (ctx.c - mu) / sd, 0.0)
    return ctx.cross(z < -k).astype(int) - ctx.cross(z > k).astype(int)


def _prev_hour_break(ctx, p):
    b = p["buffer_frac"]
    hr = (ctx.minute // 60).astype(int)
    df = pd.DataFrame({"d": ctx.day, "hr": hr, "h": ctx.h, "l": ctx.l})
    a = df.groupby(["d", "hr"]).agg(H=("h", "max"), L=("l", "min"))
    a = a.groupby(level=0).shift(1)
    idx = pd.MultiIndex.from_arrays([ctx.day, hr])
    ph = a["H"].reindex(idx).to_numpy()
    pl = a["L"].reindex(idx).to_numpy()
    up = ctx.cross(ctx.c > ph * (1 + b))
    dn = ctx.cross(ctx.c < pl * (1 - b))
    return up.astype(int) - dn.astype(int)


def _day_open_cross(ctx, p):
    nb = ctx.bars(p["away_min"])
    above = (ctx.c > ctx.day_open).astype(float)
    below = (ctx.c < ctx.day_open).astype(float)
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    up = was_below & (ctx.c > ctx.day_open)
    dn = was_above & (ctx.c < ctx.day_open)
    return up.astype(int) - dn.astype(int)


def _stoch_turn(ctx, p):
    n, th = ctx.bars(p["n_min"]), p["th"]
    hh = ctx.roll(ctx.h, n, "max")
    ll = ctx.roll(ctx.l, n, "min")
    with np.errstate(all="ignore"):
        k = np.where(hh > ll, (ctx.c - ll) / (hh - ll), 0.5)
    k = np.where(np.isnan(hh) | np.isnan(ll), 0.5, k)
    return ctx.cross(k > th).astype(int) * (ctx.prev(k, 1) <= th) - ctx.cross(k < 1 - th).astype(int) * (ctx.prev(k, 1) >= 1 - th)


def _gap_bar_follow(ctx, p):
    g = float(p["gap_pts"])
    ph, pl = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    long = (ctx.o >= ph + g) & (ctx.c > ctx.o)
    short = (ctx.o <= pl - g) & (ctx.c < ctx.o)
    return long.astype(int) - short.astype(int)


W = ("WIN",)

FAMILIES = [
    Family("E-1258", "Round-number touch rejection",
           "Index points at round multiples attract resting limit orders and psychological supply/demand; a bar that touches the next round level and closes back below it is absorbed, so fade.",
           {"step": [500, 1000, 2000]}, _round_number, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1259", "Narrowest-bar break follow",
           "The narrowest bar of the last n bars shows participants stepping aside; the first close beyond its extreme releases pent-up orders in that direction.",
           {"n": [5, 8, 12]}, _nr_break, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1260", "Low-volume new-extreme fade",
           "A new session high/low printed on below-typical volume lacks participation; late chasers are trapped, so fade the bar's direction.",
           {"vol_k": [0.5, 0.75, 1.0]}, _lowvol_extreme, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1261", "Shrinking-body run fade",
           "Same-colour bars with each body smaller than the last show a push losing force; the other side steps in, so fade.",
           {"m": [3, 4, 5]}, _shrinking_bodies, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1262", "Bollinger squeeze release follow",
           "Band width far below its typical size means volatility compression; the first close outside the band starts an expansion in that direction.",
           {"n_min": [20, 40, 60], "q": [0.6, 0.8]}, _squeeze_release, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1263", "Z-score stretch fade",
           "A close several standard deviations from its recent mean is a liquidity-driven overshoot that dealers fade back toward the mean.",
           {"n_min": [30, 60, 90], "k": [2.0, 2.5, 3.0]}, _z_stretch, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1264", "Previous clock-hour break follow",
           "The prior clock hour's high/low is a level traders watch; a close through it within the next hour shows a new hourly balance being resolved.",
           {"buffer_frac": [0.0, 0.0003, 0.0006]}, _prev_hour_break, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1265", "Day-open reclaim follow",
           "After trading on one side of the session open for a while, a close back across it flips the day's bias; follow the cross.",
           {"away_min": [15, 30, 60]}, _day_open_cross, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1266", "Stochastic exit-from-extreme turn",
           "A range-position oscillator leaving its extreme zone marks the end of a one-sided push inside the recent range; trade the bounce.",
           {"n_min": [30, 60, 120], "th": [0.1, 0.2]}, _stoch_turn, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1267", "Gap-open bar follow",
           "A bar that opens beyond the previous bar's extreme shows an aggressive order burst; if it closes in that direction the gap was not filled, so follow.",
           {"gap_pts": [5, 15, 30]}, _gap_bar_follow, markets=W, source="assistant reasoning", author="agent"),
]
