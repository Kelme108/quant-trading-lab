"""Conveyor batch B-064 (agent, 2026-11-22). Mixed theme: path-efficiency fade, bar-structure breaks, volume ramps, VWAP slope/side, smoothed-average turns."""
from __future__ import annotations

import numpy as np
from b3.esteira import Family


def _sgn(ctx, long, short):
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _er_fade(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    d = ctx.c - ctx.prev(ctx.c, nb)
    path = ctx.roll(np.abs(ctx.c - ctx.prev(ctx.c, 1)), nb, "sum")
    er = np.abs(d) / np.where(path > 0, path, np.nan)
    typical = ctx.cached(("erabs", nb), lambda: ctx.prev_sessions(np.abs(d), "mean"))
    up = (er >= th) & (d >= 1.5 * typical)
    dn = (er >= th) & (d <= -1.5 * typical)
    return _sgn(ctx, dn, up)


def _higher_low_break(ctx, p):
    n = int(p["run"])
    hl = (ctx.l > ctx.prev(ctx.l, 1)).astype(float)
    lh = (ctx.h < ctx.prev(ctx.h, 1)).astype(float)
    r_up = ctx.roll(hl, n, "sum", include_current=False) == n
    r_dn = ctx.roll(lh, n, "sum", include_current=False) == n
    short = r_up & (ctx.c < ctx.prev(ctx.l, 1))
    long = r_dn & (ctx.c > ctx.prev(ctx.h, 1))
    return long.astype(int) - short.astype(int)


def _vol_expansion(ctx, p):
    s, th = ctx.bars(p["short_min"]), p["th"]
    rng = ctx.h - ctx.l
    ratio = ctx.roll(rng, s, "mean") / ctx.roll(rng, ctx.bars(60), "mean")
    net = ctx.c - ctx.prev(ctx.c, s)
    cond = ratio >= th
    return _sgn(ctx, cond & (net > 0), cond & (net < 0))


def _volume_ramp(ctx, p):
    n = int(p["n"])
    vr = ctx.v > ctx.prev(ctx.v, 1)
    up = ((ctx.c > ctx.o) & vr).astype(float)
    dn = ((ctx.c < ctx.o) & vr).astype(float)
    return _sgn(ctx, ctx.roll(up, n, "sum") == n, ctx.roll(dn, n, "sum") == n)


def _outside_bar(ctx, p):
    f, k = p["frac"], p["range_k"]
    rng = ctx.h - ctx.l
    avg = ctx.roll(rng, 20, "mean", include_current=False)
    outside = (ctx.h > ctx.prev(ctx.h, 1)) & (ctx.l < ctx.prev(ctx.l, 1)) & (rng >= k * avg) & (rng > 0)
    loc = (ctx.c - ctx.l) / np.where(rng > 0, rng, np.nan)
    return (outside & (loc >= 1 - f)).astype(int) - (outside & (loc <= f)).astype(int)


def _stall_fade(ctx, p):
    n, frac = int(p["n"]), p["frac"]
    up = (ctx.c > ctx.prev(ctx.c, 1)).astype(float)
    dn = (ctx.c < ctx.prev(ctx.c, 1)).astype(float)
    body = np.abs(ctx.c - ctx.o)
    avg = ctx.roll(body, n, "mean", include_current=False)
    stall = (body <= frac * avg) & (avg > 0)
    run_up = ctx.roll(up, n, "sum", include_current=False) == n
    run_dn = ctx.roll(dn, n, "sum", include_current=False) == n
    return _sgn(ctx, run_dn & stall, run_up & stall)


def _vwap_slope_flip(ctx, p):
    nb = ctx.bars(p["win_min"])
    vw = ctx.vwap()
    sl = vw - ctx.prev(vw, nb)
    return _sgn(ctx, (sl > 0) & (ctx.c > vw), (sl < 0) & (ctx.c < vw))


def _dema_turn(ctx, p):
    n = ctx.bars(p["span_min"])
    e1 = ctx.cached(("e1", n), lambda: ctx.ema(ctx.c, n))
    e2 = ctx.cached(("e2", n), lambda: ctx.ema(e1, n))
    dema = 2 * e1 - e2
    sl = dema - ctx.prev(dema, 1)
    return _sgn(ctx, sl > 0, sl < 0)


def _contraction_break(ctx, p):
    n = int(p["n"])
    rng = ctx.h - ctx.l
    dec = (rng < ctx.prev(rng, 1)).astype(float)
    run = ctx.roll(dec, n, "sum", include_current=False) == n
    return (run & (ctx.c > ctx.prev(ctx.h, 1))).astype(int) - (run & (ctx.c < ctx.prev(ctx.l, 1))).astype(int)


def _vwap_opposed_fade(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    vw = ctx.vwap()
    hi = ctx.roll(ctx.c, nb, "max", include_current=False)
    lo = ctx.roll(ctx.c, nb, "min", include_current=False)
    short = (ctx.c > hi) & (ctx.c < vw)
    long = (ctx.c < lo) & (ctx.c > vw)
    return _sgn(ctx, long, short)


FAMILIES = [
    Family("E-638", "Straight-line move fade",
           "A very efficient (near straight-line) move far larger than usual leaves late chasers with no pullback cushion; "
           "liquidity providers fade it.",
           {"win_min": [15, 30, 45], "th": [0.5, 0.6, 0.7]}, _er_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-639", "Higher-low run structure break",
           "A run of rising lows is a staircase of dip buyers; the first close under the last low strands them and "
           "the move follows (mirror for lower highs).",
           {"run": [3, 4, 5]}, _higher_low_break, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-640", "Range-expansion onset follow",
           "When recent bar ranges jump relative to the last hour, new information or forced flow is arriving; "
           "follow the net direction of the burst.",
           {"short_min": [10, 15, 20], "th": [1.5, 2.0]}, _vol_expansion, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-641", "Rising-volume close ramp follow",
           "Consecutive same-colour bars each on more volume than the last show aggression building; follow.",
           {"n": [2, 3, 4]}, _volume_ramp, markets=("WIN",), source="volume-price analysis (assistant reasoning)", author="agent"),
    Family("E-642", "Wide outside-bar close follow",
           "A wide bar engulfing the prior range that closes near one end settles the auction in that direction.",
           {"frac": [0.25, 0.33, 0.4], "range_k": [1.0, 1.5, 2.0]}, _outside_bar, markets=("WIN",),
           source="price-action literature", author="agent"),
    Family("E-643", "Stalled-run exhaustion fade",
           "After a run of same-direction closes, a bar with a tiny body shows the aggressor ran out of volume; fade it.",
           {"n": [3, 4, 5], "frac": [0.3, 0.5]}, _stall_fade, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-644", "VWAP slope flip with price side",
           "When the session VWAP turns up while price is above it, the average cost of the day's volume is rising "
           "with price: buyers are in control; mirror for sells.",
           {"win_min": [15, 30, 60]}, _vwap_slope_flip, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-645", "Double-EMA slope turn follow",
           "A double-exponential average removes most lag; its slope turning marks a trend change earlier than a "
           "single EMA cross.",
           {"span_min": [10, 20, 30]}, _dema_turn, markets=("WIN",), source="assistant reasoning (DEMA, Mulloy)", author="agent"),
    Family("E-646", "Contracting-range break follow",
           "Several bars of strictly shrinking range mean participants are withdrawing; the first close beyond the last "
           "bar releases stored order flow.",
           {"n": [2, 3, 4]}, _contraction_break, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-647", "VWAP-opposed close-extreme fade",
           "A new short-term close high while price is below the day's VWAP is a rally into trapped-buyer supply; "
           "fade it (mirror above VWAP).",
           {"lookback_min": [20, 30, 60]}, _vwap_opposed_fade, markets=("WIN",), source="assistant reasoning", author="agent"),
]
