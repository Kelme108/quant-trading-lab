"""Conveyor batch B-052 (agent, 2026-11-21). Mixed WIN ideas: inter-bar gap flow, multi-day VWAP channel edges,
bar-pattern conditioned micro-break fades, pocket-pivot volume, Awesome Oscillator saucer, session-extreme upthrust,
time-block fades and two high/low-increment oscillators."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _rng_med(ctx):
    return ctx.cached("b052_rng_med", lambda: ctx.same_minute(ctx.h - ctx.l, "median"))


def _micro(ctx, win_min):
    nb = ctx.bars(win_min)
    hi = ctx.cached(("b052_hi", nb), lambda: ctx.roll(ctx.h, nb, "max", include_current=False))
    lo = ctx.cached(("b052_lo", nb), lambda: ctx.roll(ctx.l, nb, "min", include_current=False))
    up = ctx.cross(ctx.c > hi)
    dn = ctx.cross(ctx.c < lo)
    return hi, lo, up, dn


def _gap_break_fade(ctx, p):
    _, _, up, dn = _micro(ctx, p["win_min"])
    nb = ctx.bars(p["win_min"])
    gap = np.nan_to_num(ctx.o - ctx.prev(ctx.c, 1))
    gs = ctx.roll(gap, nb, "sum")
    d = p["gap_k"] * _rng_med(ctx)
    short = up & (gs >= d)
    long = dn & (gs <= -d)
    return long.astype(int) - short.astype(int)


def _vwap_channel_fade(ctx, p):
    _, _, up, dn = _micro(ctx, 15)
    n = int(p["n_sessions"])
    nd = int(ctx.day.max()) + 1
    vl = pd.Series(ctx.vwap()).groupby(ctx.day).last().reindex(range(nd))
    ch = vl.rolling(n, min_periods=n).max().shift(1).to_numpy()[ctx.day]
    cl = vl.rolling(n, min_periods=n).min().shift(1).to_numpy()[ctx.day]
    d = p["k"] * _rng_med(ctx)
    short = up & (ctx.h >= ch - d)
    long = dn & (ctx.l <= cl + d)
    return long.astype(int) - short.astype(int)


def _inside_primed_fade(ctx, p):
    _, _, up, dn = _micro(ctx, p["win_min"])
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    h2, l2 = ctx.prev(ctx.h, 2), ctx.prev(ctx.l, 2)
    inside = (h1 <= h2) & (l1 >= l2) & ((h1 - l1) <= p["q"] * _rng_med(ctx))
    return (dn & inside).astype(int) - (up & inside).astype(int)


def _vpop_fade(ctx, p):
    _, _, up, dn = _micro(ctx, p["win_min"])
    body = ctx.c - ctx.o
    d = p["body_k"] * _rng_med(ctx)
    prev_red = ctx.prev(ctx.c, 1) < ctx.prev(ctx.o, 1)
    prev_green = ctx.prev(ctx.c, 1) > ctx.prev(ctx.o, 1)
    short = up & prev_red & (body >= d)
    long = dn & prev_green & (-body >= d)
    return long.astype(int) - short.astype(int)


def _pocket_pivot(ctx, p):
    nb = ctx.bars(p["n_min"])
    k = p["k"]
    dv = np.where(ctx.c < ctx.o, ctx.v, 0.0)
    uv = np.where(ctx.c > ctx.o, ctx.v, 0.0)
    mdv = ctx.roll(dv, nb, "max", include_current=False)
    muv = ctx.roll(uv, nb, "max", include_current=False)
    vw = ctx.vwap()
    long = (ctx.c > ctx.o) & (mdv > 0) & (ctx.v > k * mdv) & (ctx.c > vw)
    short = (ctx.c < ctx.o) & (muv > 0) & (ctx.v > k * muv) & (ctx.c < vw)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _ao_saucer(ctx, p):
    slow = ctx.bars(p["slow_min"])
    fast = max(2, slow // 7)
    med = (ctx.h + ctx.l) / 2.0
    ao = ctx.roll(med, fast, "mean") - ctx.roll(med, slow, "mean")
    a1, a2 = ctx.prev(ao, 1), ctx.prev(ao, 2)
    big = np.abs(ao) >= p["min_k"] * _rng_med(ctx)
    long = (ao > 0) & (a2 > a1) & (ao > a1) & big
    short = (ao < 0) & (a2 < a1) & (ao < a1) & big
    return long.astype(int) - short.astype(int)


def _upthrust_pair(ctx, p):
    nh = (ctx.h > ctx.session_high(include_current=False)).astype(float)
    nl = (ctx.l < ctx.session_low(include_current=False)).astype(float)
    old = ctx.bar_in_day >= ctx.bars(p["age_min"])
    short = (ctx.prev(nh, 1) == 1) & (ctx.c < ctx.prev(ctx.l, 1)) & old
    long = (ctx.prev(nl, 1) == 1) & (ctx.c > ctx.prev(ctx.h, 1)) & old
    return long.astype(int) - short.astype(int)


def _time_block_fade(ctx, p):
    _, _, up, dn = _micro(ctx, p["win_min"])
    st = p["start_min"]
    inb = (ctx.minute >= st) & (ctx.minute < st + 90)
    return (dn & inb).astype(int) - (up & inb).astype(int)


def _demarker_fade(ctx, p):
    nb = ctx.bars(p["n_min"])
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    dmax = np.where(ctx.h > h1, ctx.h - h1, 0.0)
    dmin = np.where(l1 > ctx.l, l1 - ctx.l, 0.0)
    a = ctx.roll(dmax, nb, "mean")
    b = ctx.roll(dmin, nb, "mean")
    den = a + b
    dem = np.where(den > 0, a / np.where(den > 0, den, 1.0), np.nan)
    th = p["th"]
    short = ctx.cross(dem >= th)
    long = ctx.cross(dem <= 1.0 - th)
    return long.astype(int) - short.astype(int)


def _tsi_fade(ctx, p):
    r = int(p["r"])
    s = max(2, r // 2)
    m = ctx.c - ctx.prev(ctx.c, 1)
    num = ctx.ema(ctx.ema(m, r), s)
    den = ctx.ema(ctx.ema(np.abs(m), r), s)
    with np.errstate(invalid="ignore", divide="ignore"):
        tsi = 100.0 * num / den
    th = p["th"]
    short = ctx.cross(tsi >= th)
    long = ctx.cross(tsi <= -th)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-518", "Gap-driven micro-break fade",
           "A short-range break that was built by open-vs-previous-close gaps (aggressive market orders jumping the "
           "book) rather than by trading inside bars is a liquidity-taking spike; the book refills and price returns.",
           {"win_min": [10, 15, 20], "gap_k": [0.25, 0.5, 1.0]}, _gap_break_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-519", "Multi-day session-VWAP channel edge fade",
           "The highest and lowest session VWAPs of recent sessions bound where participants agreed on value; a "
           "short-range break that reaches that edge meets inventory holders and tends to fail.",
           {"n_sessions": [5, 10, 20], "k": [2, 4, 8]}, _vwap_channel_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-520", "Inside-bar-primed micro-break fade",
           "A short-range break on the bar right after a small inside bar is a release of a coil by a few stop orders, "
           "not a conviction move; fade it.",
           {"win_min": [10, 15, 20], "q": [0.5, 0.75, 1.0]}, _inside_primed_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-521", "V-pop micro-break fade",
           "A big bar that breaks a short-range extreme right after an opposite-colour bar is a one-bar squeeze of "
           "stops with no second wave behind it; fade the pop.",
           {"win_min": [10, 15, 20], "body_k": [0.5, 1.0, 1.5]}, _vpop_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-522", "Pocket-pivot volume follow",
           "An up bar on more volume than every down bar of the recent window, above VWAP, shows buyers absorbing all "
           "the selling seen lately (and the mirror for sells); follow it.",
           {"n_min": [10, 20, 30], "k": [1.0, 1.5]}, _pocket_pivot, markets=("WIN",),
           source="assistant reasoning (O'Neil pocket pivot)", author="agent"),
    Family("E-523", "Awesome Oscillator saucer follow",
           "In an established momentum phase (AO on one side of zero), two shrinking bars followed by a re-growing one "
           "mark a pause that ended; trade with the phase.",
           {"slow_min": [30, 60, 90], "min_k": [0.0, 0.5, 1.0]}, _ao_saucer, markets=("WIN",),
           source="assistant reasoning (Bill Williams AO saucer)", author="agent"),
    Family("E-524", "Session-extreme two-bar upthrust fade",
           "A new session high (low) followed at once by a close under its low (over its high) traps breakout buyers "
           "(sellers) at the day's edge; their exits feed the reversal.",
           {"age_min": [15, 30, 60]}, _upthrust_pair, markets=("WIN",),
           source="assistant reasoning (Wyckoff upthrust)", author="agent"),
    Family("E-525", "Time-block micro-break fade",
           "Liquidity and participant mix change through the day; in some 90-minute blocks short-range breaks mostly "
           "fail because the flow behind them is thin.",
           {"start_min": [600, 690, 780, 870], "win_min": [10, 20]}, _time_block_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-526", "DeMarker extreme fade",
           "DeMarker measures how often highs are pushed up versus lows pushed down bar to bar; a reading near an "
           "extreme means one side has been extending the range for too long to continue at the same pace.",
           {"n_min": [30, 60, 90], "th": [0.65, 0.75, 0.85]}, _demarker_fade, markets=("WIN",),
           source="assistant reasoning (DeMark DeMarker)", author="agent"),
    Family("E-527", "True Strength Index extreme fade",
           "A double-smoothed momentum ratio at an extreme means price moved almost one-directionally for a long "
           "stretch; late followers become the supply (demand) for the reversal.",
           {"r": [13, 25], "th": [20, 30, 40]}, _tsi_fade, markets=("WIN",),
           source="assistant reasoning (Blau TSI)", author="agent"),
]
