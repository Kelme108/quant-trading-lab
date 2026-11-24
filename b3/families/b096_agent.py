"""Conveyor batch B-096 (agent, 2026-11-24). Mixed themes: tape autocorrelation, wick pressure, day-open acceptance, volatility burst, trend persistence, hour-open reclaim, volume ladder, range midpoint, outside bar, low-volume extreme fade."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _ret(ctx):
    return ctx.c / ctx.prev(ctx.c, 1) - 1.0


def _lag(ctx, x, i):
    return x if i == 0 else ctx.prev(x, i)


def _autocorr_follow(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    r = _ret(ctx)
    with np.errstate(all="ignore"):
        ac = ctx.roll(r * ctx.prev(r, 1), nb, "mean") / ctx.roll(r * r, nb, "mean")
    long = (ac >= th) & (r > 0)
    short = (ac >= th) & (r < 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _wick_pressure(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    rng = ctx.h - ctx.l
    lw = np.minimum(ctx.o, ctx.c) - ctx.l
    uw = ctx.h - np.maximum(ctx.o, ctx.c)
    with np.errstate(all="ignore"):
        imb = np.where(rng > 0, (lw - uw) / rng, 0.0)
    m = ctx.roll(imb, nb, "mean")
    return ctx.cross(m >= th).astype(int) - ctx.cross(m <= -th).astype(int)


def _day_open_acceptance(ctx, p):
    k = p["k"]
    dev = ctx.c / ctx.day_open - 1.0
    typ = ctx.cached("dev_typ", lambda: ctx.prev_sessions(np.abs(dev), "mean"))
    g = pd.Series(dev).groupby(ctx.day)
    gmax = g.transform(lambda z: z.cummax().shift(1)).to_numpy()
    gmin = g.transform(lambda z: z.cummin().shift(1)).to_numpy()
    short = (gmax >= k * typ) & (ctx.c < ctx.day_open)
    long = (gmin <= -k * typ) & (ctx.c > ctx.day_open)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _vol_burst(ctx, p):
    th = p["ratio"]
    r = _ret(ctx)
    ns, nl = ctx.bars(p["short_min"]), ctx.bars(60)
    with np.errstate(all="ignore"):
        ratio = ctx.roll(r, ns, "std") / ctx.roll(r, nl, "std")
    cond = ratio >= th
    long = cond & (ctx.c > ctx.o) & (r > 0)
    short = cond & (ctx.c < ctx.o) & (r < 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _trend_persistence_resume(ctx, p):
    nb, mf = ctx.bars(p["win_min"]), p["m_frac"]
    nh = (ctx.h > ctx.session_high()).astype(float)
    nl = (ctx.l < ctx.session_low()).astype(float)
    s = ctx.roll(nh, nb, "sum") - ctx.roll(nl, nb, "sum")
    po, pc, ph, pl = ctx.prev(ctx.o, 1), ctx.prev(ctx.c, 1), ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    long = (s >= mf * nb) & (pc < po) & (ctx.c > ph)
    short = (s <= -mf * nb) & (pc > po) & (ctx.c < pl)
    return long.astype(int) - short.astype(int)


def _hour_open_reclaim(ctx, p):
    f = p["frac"]
    key = ctx.day.astype(np.int64) * 24 + (np.asarray(ctx.minute) // 60).astype(np.int64)
    ho = pd.Series(ctx.o).groupby(key).transform("first").to_numpy()
    below = (ctx.c < ho).astype(float)
    above = (ctx.c > ho).astype(float)
    cnt = (pd.Series(1.0, index=range(ctx.n)).groupby(key).cumcount() + 1).to_numpy(float)
    cb = pd.Series(below).groupby(key).cumsum().to_numpy()
    ca = pd.Series(above).groupby(key).cumsum().to_numpy()
    with np.errstate(all="ignore"):
        fb = (cb - below) / (cnt - 1)
        fa = (ca - above) / (cnt - 1)
    pc = ctx.prev(ctx.c, 1)
    ok = cnt >= 4
    long = ok & (fb >= f) & (ctx.c > ho) & (pc <= ho)
    short = ok & (fa >= f) & (ctx.c < ho) & (pc >= ho)
    return long.astype(int) - short.astype(int)


def _volume_ladder(ctx, p):
    k, g = int(p["bars"]), p["growth"]
    up = np.ones(ctx.n, bool)
    dn = np.ones(ctx.n, bool)
    for i in range(k):
        vi, vp = _lag(ctx, ctx.v, i), ctx.prev(ctx.v, i + 1)
        ci, oi = _lag(ctx, ctx.c, i), _lag(ctx, ctx.o, i)
        grow = vi >= g * vp
        up &= grow & (ci > oi)
        dn &= grow & (ci < oi)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _range_midpoint_cross(ctx, p):
    k = p["k"]
    sh, sl = ctx.session_high(), ctx.session_low()
    mid = (sh + sl) / 2.0
    with np.errstate(all="ignore"):
        rp = (sh - sl) / ctx.c
    typ = ctx.cached("rng_typ", lambda: ctx.same_minute(np.nan_to_num(rp), "median"))
    wide = rp >= k * typ
    long = wide & (ctx.c > mid)
    short = wide & (ctx.c < mid)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _outside_bar(ctx, p):
    f, m = p["close_frac"], p["range_mult"]
    rng = ctx.h - ctx.l
    avg = ctx.roll(rng, ctx.bars(30), "mean", include_current=False)
    outside = (ctx.h > ctx.prev(ctx.h, 1)) & (ctx.l < ctx.prev(ctx.l, 1)) & (rng >= m * avg) & (rng > 0)
    with np.errstate(all="ignore"):
        loc = (ctx.c - ctx.l) / rng
    return (outside & (loc >= 1 - f)).astype(int) - (outside & (loc <= f)).astype(int)


def _lowvol_extreme_fade(ctx, p):
    nb, k = ctx.bars(p["lookback_min"]), p["vol_k"]
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    av = ctx.roll(ctx.v, nb, "mean", include_current=False)
    quiet = ctx.v < k * av
    short = (ctx.h > hi) & quiet
    long = (ctx.l < lo) & quiet
    return long.astype(int) - short.astype(int)


W = ("WIN",)

FAMILIES = [
    Family("E-958", "Positive tape autocorrelation follow",
           "When successive bar returns have recently been positively correlated the tape is trending in small steps "
           "(orders sliced by large participants); the next bar in the last bar's direction follows.",
           {"win_min": [20, 30, 45], "th": [0.15, 0.25, 0.35]}, _autocorr_follow,
           source="assistant reasoning", author="agent", markets=W),
    Family("E-959", "Cumulative wick pressure follow",
           "Persistently longer lower wicks than upper wicks over a window show dips being absorbed by passive "
           "buyers; follow the side that keeps rejecting.",
           {"win_min": [15, 30, 60], "th": [0.2, 0.3, 0.4]}, _wick_pressure,
           source="assistant reasoning", author="agent", markets=W),
    Family("E-960", "Day-open acceptance after an excursion",
           "After the price strays far above (below) the day's open and then closes back under (over) it, the "
           "excursion was rejected and the other side takes control; follow the cross.",
           {"k": [1.0, 1.5, 2.0]}, _day_open_acceptance,
           source="assistant reasoning", author="agent", markets=W),
    Family("E-961", "Volatility burst direction follow",
           "A jump of short-term volatility over the hourly level marks new information or a large order arriving; "
           "the burst bar's direction tends to continue as others reprice.",
           {"ratio": [1.5, 2.0, 2.5], "short_min": [10, 15]}, _vol_burst,
           source="assistant reasoning", author="agent", markets=W),
    Family("E-962", "Persistent-trend resume bar",
           "When most recent bars keep making new session highs (lows), a one-bar pause that is immediately "
           "overtaken signals trend resumption by participants who missed the move.",
           {"win_min": [30, 60], "m_frac": [0.15, 0.25, 0.35]}, _trend_persistence_resume,
           source="assistant reasoning", author="agent", markets=W),
    Family("E-963", "Hour-open reclaim",
           "Many desks mark the hourly open; a close back through it after most of the hour spent on the other side "
           "shifts the hour's balance and invites follow-through.",
           {"frac": [0.6, 0.75, 0.9]}, _hour_open_reclaim,
           source="assistant reasoning", author="agent", markets=W),
    Family("E-964", "Rising-volume bar ladder follow",
           "Consecutive same-colour bars each with more volume than the last show aggressive participation "
           "building rather than fading; follow it.",
           {"bars": [2, 3, 4], "growth": [1.0, 1.2, 1.5]}, _volume_ladder,
           source="volume-price analysis (assistant reasoning)", author="agent", markets=W),
    Family("E-965", "Wide-range midpoint cross follow",
           "Once the session range is wider than usual for the time, the range midpoint is the balance line; a close "
           "through it shows the auction moving to the other half.",
           {"k": [0.8, 1.0, 1.3]}, _range_midpoint_cross,
           source="auction market theory (assistant reasoning)", author="agent", markets=W),
    Family("E-966", "Outside bar with strong close",
           "A bar that exceeds both extremes of the previous one and closes at one end means the opposite side was "
           "run over after being tested; follow the close.",
           {"close_frac": [0.2, 0.3, 0.4], "range_mult": [1.0, 1.5]}, _outside_bar,
           source="price-action literature (assistant reasoning)", author="agent", markets=W),
    Family("E-967", "Low-volume new extreme fade",
           "A new short-term high (low) made on thin volume lacks real participation and is a liquidity poke; "
           "fade it back into the range.",
           {"lookback_min": [20, 30, 60], "vol_k": [0.5, 0.7, 0.9]}, _lowvol_extreme_fade,
           source="volume-price analysis (assistant reasoning)", author="agent", markets=W),
]
