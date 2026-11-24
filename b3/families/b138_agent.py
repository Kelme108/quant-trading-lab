"""Conveyor batch B-138 (agent, 2026-11-24). Mixed single-market price/volume rules: bands, levels, bar shape, volatility."""
from __future__ import annotations

import numpy as np

from b3.esteira import Family


def _boll_reentry(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    m = ctx.roll(ctx.c, nb, "mean")
    s = ctx.roll(ctx.c, nb, "std")
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.where(s > 0, (ctx.c - m) / s, np.nan)
    pz = ctx.prev(z, 1)
    short = (pz > k) & (z < k)
    long = (pz < -k) & (z > -k)
    return long.astype(int) - short.astype(int)


def _open_recross(ctx, p):
    nb = ctx.bars(p["stay_min"])
    above = (ctx.c > ctx.day_open).astype(float)
    below = (ctx.c < ctx.day_open).astype(float)
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    short = was_above & (ctx.c < ctx.day_open)
    long = was_below & (ctx.c > ctx.day_open)
    return long.astype(int) - short.astype(int)


def _round_number(ctx, p):
    step = float(p["step"])
    pc = ctx.prev(ctx.c, 1)
    up = np.ceil(pc / step) * step
    dn = np.floor(pc / step) * step
    short = (ctx.h >= up) & (ctx.c < up) & (ctx.c < ctx.o)
    long = (ctx.l <= dn) & (ctx.c > dn) & (ctx.c > ctx.o)
    return long.astype(int) - short.astype(int)


def _spike_climax(ctx, p):
    k, q = p["k"], p["q"]
    med = ctx.cached("vol_med20", lambda: ctx.same_minute(ctx.v, "median"))
    rng = ctx.h - ctx.l
    with np.errstate(divide="ignore", invalid="ignore"):
        pos = np.where(rng > 0, (ctx.c - ctx.l) / rng, 0.5)
    spike = ctx.v > k * med
    short = spike & (pos > 1 - q) & (ctx.c > ctx.o)
    long = spike & (pos < q) & (ctx.c < ctx.o)
    return long.astype(int) - short.astype(int)


def _nr_break(ctx, p):
    n = int(p["n"])
    rng = ctx.h - ctx.l
    rmin = ctx.roll(rng, n, "min")
    nr = (rng <= rmin).astype(float)
    pnr = ctx.prev(nr, 1) == 1
    long = pnr & (ctx.c > ctx.prev(ctx.h, 1))
    short = pnr & (ctx.c < ctx.prev(ctx.l, 1))
    return long.astype(int) - short.astype(int)


def _gap_fade(ctx, p):
    k = p["k"]
    nb = ctx.bars(p["win_min"])
    avg = ctx.roll(ctx.h - ctx.l, nb, "mean", include_current=False)
    gap = ctx.o - ctx.prev(ctx.c, 1)
    short = (gap > k * avg) & (avg > 0) & (ctx.c < ctx.o)
    long = (gap < -k * avg) & (avg > 0) & (ctx.c > ctx.o)
    return long.astype(int) - short.astype(int)


def _vol_expansion(ctx, p):
    ns = ctx.bars(p["short_min"])
    nl = 4 * ns
    r = p["ratio"]
    ret = ctx.c - ctx.prev(ctx.c, 1)
    ss = ctx.roll(ret, ns, "std")
    sl = ctx.roll(ret, nl, "std")
    with np.errstate(divide="ignore", invalid="ignore"):
        cond = (sl > 0) & (ss / sl > r)
    d = np.sign(ctx.c - ctx.prev(ctx.c, ns))
    d = np.nan_to_num(d)
    return np.where(ctx.cross(cond), d, 0).astype(int)


def _extreme_streak(ctx, p):
    m = int(p["streak"])
    ll = (ctx.l < ctx.prev(ctx.l, 1)).astype(float)
    hh = (ctx.h > ctx.prev(ctx.h, 1)).astype(float)
    pll = ctx.prev(ctx.roll(ll, m, "sum"), 1) == m
    phh = ctx.prev(ctx.roll(hh, m, "sum"), 1) == m
    long = pll & (ctx.c > ctx.prev(ctx.h, 1))
    short = phh & (ctx.c < ctx.prev(ctx.l, 1))
    return long.astype(int) - short.astype(int)


def _ema_cross(ctx, p):
    f = int(p["fast"])
    fast = ctx.cached(("ema", f), lambda: ctx.ema(ctx.c, f))
    slow = ctx.cached(("ema", 3 * f), lambda: ctx.ema(ctx.c, 3 * f))
    valid = ~np.isnan(slow)
    long = ctx.cross(valid & (fast > slow))
    short = ctx.cross(valid & (fast < slow))
    return long.astype(int) - short.astype(int)


def _close_high_volume(ctx, p):
    nb, vk = ctx.bars(p["n_min"]), p["vol_k"]
    hi = ctx.roll(ctx.c, nb, "max", include_current=False)
    lo = ctx.roll(ctx.c, nb, "min", include_current=False)
    vm = ctx.roll(ctx.v, nb, "mean", include_current=False)
    big = ctx.v > vk * vm
    long = ctx.cross((ctx.c > hi) & big)
    short = ctx.cross((ctx.c < lo) & big)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-1378", "Bollinger band re-entry fade",
           "A close beyond k standard deviations of the recent closes and back inside next bar is an overshoot "
           "that liquidity providers absorb; fade it back to the mean.",
           {"win_min": [20, 40, 60], "k": [2.0, 2.5]}, _boll_reentry, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1379", "Session-open price recross follow",
           "After price held one side of the session open for a while, a close across it shows buyers or sellers "
           "who defended the open have given up; follow the cross.",
           {"stay_min": [15, 30, 60]}, _open_recross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1380", "Round-number rejection",
           "Round index levels hold resting orders; a bar that touches the level and closes back away from it "
           "with its body shows those orders absorbed the push; fade.",
           {"step": [250, 500, 1000]}, _round_number, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1381", "Volume-spike climax bar fade",
           "A bar with volume far above normal for the time that closes at its extreme against the "
           "body direction is a climax: late aggressors are trapped; fade it.",
           {"k": [2.0, 3.0, 4.0], "q": [0.2, 0.3]}, _spike_climax, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1382", "Narrowest-range bar breakout",
           "The narrowest bar of the last n bars marks compression; a close beyond its high or low releases "
           "the stored energy in that direction.",
           {"n": [5, 10, 20]}, _nr_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1383", "Bar-open gap fade",
           "A bar opening far from the previous close (relative to the usual bar range) is a thin-book jump; "
           "if the bar closes back toward the previous close the jump is being retraced; fade it.",
           {"k": [0.5, 1.0, 1.5], "win_min": [30, 60]}, _gap_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1384", "Volatility-expansion direction follow",
           "When short-term volatility jumps above the longer-term level, a regime of directional order flow "
           "starts; follow the direction of the short window.",
           {"short_min": [15, 30], "ratio": [1.5, 2.0, 2.5]}, _vol_expansion, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1385", "Extreme streak exhaustion reversal",
           "After m consecutive bars each making a new lower low (higher high), a bar closing beyond the previous "
           "bar's opposite extreme shows the pressure is spent; trade the reversal.",
           {"streak": [3, 4, 5]}, _extreme_streak, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1386", "Fast-slow EMA cross follow",
           "A fast EMA crossing a slower one (3x) marks a change in the recent drift that slower participants "
           "chase; follow the cross.",
           {"fast": [3, 5, 8]}, _ema_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1387", "Closing-extreme break on heavy bars",
           "A close beyond every close of the last n minutes on above-average volume is a break with participation "
           "rather than a thin poke; follow it.",
           {"n_min": [20, 40, 60], "vol_k": [1.0, 1.5]}, _close_high_volume, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
