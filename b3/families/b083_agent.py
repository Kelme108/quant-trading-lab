"""Conveyor batch B-083 (agent, 2026-11-23). Mixed themes: exhaustion bars, pivots, RSI2, volume peaks, VWAP side, swing failure, alignment, block fades."""
from __future__ import annotations

import numpy as np

from b3.esteira import Family


def _d(long, short):
    return np.asarray(long).astype(int) - np.asarray(short).astype(int)


def _lower_low_exhaust(ctx, p):
    n = int(p["n"])
    ll = (ctx.l < ctx.prev(ctx.l, 1)).astype(float)
    hh = (ctx.h > ctx.prev(ctx.h, 1)).astype(float)
    sll = ctx.roll(ll, n, "sum") == n
    shh = ctx.roll(hh, n, "sum") == n
    pl = ctx.prev(sll.astype(float), 1) == 1
    ph = ctx.prev(shh.astype(float), 1) == 1
    long = pl & (ctx.h > ctx.prev(ctx.h, 1)) & (ctx.c > ctx.prev(ctx.c, 1))
    short = ph & (ctx.l < ctx.prev(ctx.l, 1)) & (ctx.c < ctx.prev(ctx.c, 1))
    return _d(long, short)


def _open_drive_bar(ctx, p):
    tol, k = p["tol"], p["k"]
    rng = ctx.h - ctx.l
    typ = ctx.cached("rng_med", lambda: ctx.same_minute(rng, "median"))
    big = (rng >= k * typ) & (rng > 0)
    long = big & ((ctx.o - ctx.l) <= tol * rng) & ((ctx.h - ctx.c) <= tol * rng)
    short = big & ((ctx.h - ctx.o) <= tol * rng) & ((ctx.c - ctx.l) <= tol * rng)
    return _d(ctx.cross(long), ctx.cross(short))


def _pivot_reject(ctx, p):
    b = p["buffer_frac"]
    H, L, C = ctx.prev_session_value("high"), ctx.prev_session_value("low"), ctx.prev_session_value("close")
    P = (H + L + C) / 3.0
    r1, s1 = 2 * P - L, 2 * P - H
    short = (ctx.h >= r1 * (1 + b)) & (ctx.c < r1)
    long = (ctx.l <= s1 * (1 - b)) & (ctx.c > s1)
    return _d(ctx.cross(long), ctx.cross(short))


def _rsi2_trend_dip(ctx, p):
    thr, n = p["rsi_thr"], int(p["ema_bars"])
    r = ctx.rsi(2)
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    long = (r < thr) & (ctx.c > ema)
    short = (r > 100 - thr) & (ctx.c < ema)
    return _d(ctx.cross(long), ctx.cross(short))


def _volume_peak_follow(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    vmax = ctx.roll(ctx.v, nb, "max")
    peak = (ctx.v >= vmax) & (ctx.v > 0)
    body = np.abs(ctx.c - ctx.o) >= 0.5 * (ctx.h - ctx.l)
    return _d(peak & body & (ctx.c > ctx.o), peak & body & (ctx.c < ctx.o))


def _new_high_below_vwap(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    vw = ctx.vwap()
    hi = ctx.roll(ctx.c, nb, "max", include_current=False)
    lo = ctx.roll(ctx.c, nb, "min", include_current=False)
    short = (ctx.c > hi) & (ctx.c < vw)
    long = (ctx.c < lo) & (ctx.c > vw)
    return _d(ctx.cross(long), ctx.cross(short))


def _vwap_retest(ctx, p):
    nb, k = ctx.bars(p["stretch_min"]), p["k"]
    vw = ctx.vwap()
    dist = (ctx.c - vw) / ctx.c
    scale = ctx.cached("vwap_dist_scale", lambda: ctx.prev_sessions(np.abs(dist), "mean"))
    up = ctx.roll(dist, nb, "max", include_current=False) >= k * scale
    dn = ctx.roll(dist, nb, "min", include_current=False) <= -k * scale
    long = up & (ctx.l <= vw) & (ctx.c > vw)
    short = dn & (ctx.h >= vw) & (ctx.c < vw)
    return _d(ctx.cross(long), ctx.cross(short))


def _swing_failure(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    newhi = ctx.prev(ctx.h, 1) > ctx.prev(hi, 1)
    newlo = ctx.prev(ctx.l, 1) < ctx.prev(lo, 1)
    short = newhi & (ctx.c < ctx.prev(ctx.l, 1))
    long = newlo & (ctx.c > ctx.prev(ctx.h, 1))
    return _d(long, short)


def _momentum_alignment(ctx, p):
    m, k = p["base_min"], p["k"]
    a, b, c3 = ctx.bars(m), ctx.bars(3 * m), ctx.bars(6 * m)
    r1 = ctx.c / ctx.prev(ctx.c, a) - 1.0
    r2 = ctx.c / ctx.prev(ctx.c, b) - 1.0
    r3 = ctx.c / ctx.prev(ctx.c, c3) - 1.0
    typ = ctx.cached(("abs_mv", c3), lambda: ctx.prev_sessions(np.abs(r3), "mean"))
    up = (r1 > 0) & (r2 > 0) & (r3 >= k * typ)
    dn = (r1 < 0) & (r2 < 0) & (r3 <= -k * typ)
    return _d(ctx.cross(up), ctx.cross(dn))


def _block_fade(ctx, p):
    k = p["k"]
    nb = ctx.bars(30)
    start = (ctx.minute % 30) < ctx.tf
    ret = ctx.prev(ctx.c, 1) / ctx.prev(ctx.c, nb) - 1.0
    typ = ctx.cached(("blk_typ", nb), lambda: ctx.prev_sessions(np.abs(ret), "mean"))
    short = start & (ret >= k * typ)
    long = start & (ret <= -k * typ)
    return _d(long, short)


def _range_exhaust_dummy(ctx, p):
    return np.zeros(ctx.n, dtype=int)


FAMILIES = [
    Family("E-828", "Directional-streak exhaustion turn",
           "After n consecutive bars each making a lower low (or higher high), the first bar that reverses with a higher high "
           "and higher close shows sellers (buyers) are spent; trade the turn.",
           {"n": [3, 4, 5]}, _lower_low_exhaust, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-829", "Open-drive bar follow",
           "A larger-than-usual bar that opens at one extreme and closes at the other shows one side controlled the whole bar "
           "with no pullback; follow it.",
           {"tol": [0.1, 0.2, 0.3], "k": [1.0, 1.5]}, _open_drive_bar, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-830", "Floor-pivot R1/S1 rejection",
           "Classic floor-trader pivots from the prior session are watched levels; a poke through R1/S1 that closes back "
           "inside is a failed push; fade it.",
           {"buffer_frac": [0.0, 0.0005, 0.001]}, _pivot_reject, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-831", "RSI(2) dip inside an EMA trend",
           "A very short-term oversold reading while price is above its EMA is a brief shakeout of weak hands in an "
           "uptrend; buy it (mirror for sells).",
           {"rsi_thr": [5, 10, 20], "ema_bars": [30, 60]}, _rsi2_trend_dip, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-832", "Highest-volume bar follow",
           "The bar with the highest volume of the window and a body over half its range shows aggressive one-sided "
           "participation; follow its direction.",
           {"lookback_min": [30, 60, 90]}, _volume_peak_follow, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-833", "New closing high below VWAP fade",
           "A rally to a new window closing high that is still below the session VWAP runs into volume-weighted supply "
           "from trapped longs; fade it (mirror for lows above VWAP).",
           {"lookback_min": [15, 30, 60]}, _new_high_below_vwap, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-834", "VWAP retest after a stretch",
           "After price stretched far from VWAP, a pullback that touches VWAP and closes back on the trend side shows "
           "institutional buyers (sellers) defending their average price; follow.",
           {"stretch_min": [30, 60], "k": [1.5, 2.0, 3.0]}, _vwap_retest, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-835", "Two-bar swing failure",
           "A bar that makes a new window extreme and is then fully engulfed by a close beyond its opposite end traps "
           "breakout traders; trade against the failed break.",
           {"lookback_min": [20, 30, 45]}, _swing_failure, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-836", "Multi-horizon momentum alignment",
           "When short, medium and long horizon returns turn to the same sign with a long-horizon move above normal, "
           "participants of different horizons agree and the move should extend.",
           {"base_min": [5, 10, 15], "k": [0.5, 1.0, 1.5]}, _momentum_alignment, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-837", "Half-hour block return fade",
           "Algorithms and desks rebalance on the half hour; a larger-than-usual move in the block just ended tends to be "
           "partly reversed as the new block starts.",
           {"k": [0.75, 1.0, 1.5]}, _block_fade, markets=("WIN",), source="assistant reasoning", author="agent"),
]
