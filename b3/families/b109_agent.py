"""Conveyor batch B-109 (agent, 2026-11-24). Oscillator, channel, regression, volatility and round-number ideas."""
from __future__ import annotations

import numpy as np

from b3.esteira import Family


def _stoch_reentry(ctx, p):
    nb, lv = ctx.bars(p["n_min"]), p["level"]
    hh = ctx.roll(ctx.h, nb, "max")
    ll = ctx.roll(ctx.l, nb, "min")
    k = 100.0 * (ctx.c - ll) / np.where(hh > ll, hh - ll, np.nan)
    kp = ctx.prev(k, 1)
    long = (kp <= lv) & (k > lv)
    short = (kp >= 100 - lv) & (k < 100 - lv)
    return long.astype(int) - short.astype(int)


def _channel_mid(ctx, p):
    nb = ctx.bars(p["n_min"])
    hh = ctx.roll(ctx.h, nb, "max", include_current=False)
    ll = ctx.roll(ctx.l, nb, "min", include_current=False)
    mid = (hh + ll) / 2.0
    up = ctx.cross(ctx.c > mid)
    dn = ctx.cross(ctx.c < mid)
    return up.astype(int) - dn.astype(int)


def _slope_t(ctx, p):
    nb, thr = ctx.bars(p["n_min"]), p["t"]
    nb = max(nb, 6)
    x = ctx.bar_in_day.astype(float)
    y = ctx.c
    mx, my = ctx.roll(x, nb, "mean"), ctx.roll(y, nb, "mean")
    mxy, mxx, myy = ctx.roll(x * y, nb, "mean"), ctx.roll(x * x, nb, "mean"), ctx.roll(y * y, nb, "mean")
    cov = mxy - mx * my
    vx = mxx - mx * mx
    vy = myy - my * my
    den = np.sqrt(np.where((vx > 0) & (vy > 0), vx * vy, np.nan))
    r = np.clip(cov / den, -0.9999, 0.9999)
    t = r * np.sqrt((nb - 2) / (1 - r * r))
    up = ctx.cross(t > thr)
    dn = ctx.cross(t < -thr)
    return up.astype(int) - dn.astype(int)


def _nr_break(ctx, p):
    n = int(p["n_bars"])
    rng = ctx.h - ctx.l
    mr = ctx.roll(rng, n, "min")
    r1, m1 = ctx.prev(rng, 1), ctx.prev(mr, 1)
    nr = (r1 <= m1) & (r1 > 0)
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    return (nr & (ctx.c > h1)).astype(int) - (nr & (ctx.c < l1)).astype(int)


def _round_reject(ctx, p):
    step = float(p["step"])
    pc = ctx.prev(ctx.c, 1)
    lo = np.floor(pc / step) * step
    hi = lo + step
    short = (ctx.h >= hi) & (ctx.c < hi)
    long = (ctx.l <= lo) & (ctx.c > lo)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _gap_follow(ctx, p):
    k = p["gap_k"]
    rng = ctx.h - ctx.l
    m = ctx.roll(rng, 20, "mean")
    up = ((ctx.o - ctx.prev(ctx.h, 1)) >= k * m) & (ctx.c > ctx.o) & (m > 0)
    dn = ((ctx.prev(ctx.l, 1) - ctx.o) >= k * m) & (ctx.c < ctx.o) & (m > 0)
    return up.astype(int) - dn.astype(int)


def _volume_buildup(ctx, p):
    n, k = int(p["n_bars"]), p["vol_k"]
    c1, v1 = ctx.prev(ctx.c, 1), ctx.prev(ctx.v, 1)
    cu = ctx.roll((ctx.c > c1).astype(float), n, "sum")
    cd = ctx.roll((ctx.c < c1).astype(float), n, "sum")
    vu = ctx.roll((ctx.v > v1).astype(float), n, "sum")
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    big = ctx.v > k * med
    long = (cu == n) & (vu == n) & big
    short = (cd == n) & (vu == n) & big
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _pd_mid_cross(ctx, p):
    b = p["buffer_frac"]
    pm = (ctx.prev_session_value("high") + ctx.prev_session_value("low")) / 2.0
    up = ctx.cross(ctx.c > pm * (1 + b))
    dn = ctx.cross(ctx.c < pm * (1 - b))
    return up.astype(int) - dn.astype(int)


def _vol_expansion(ctx, p):
    ns, k = ctx.bars(p["short_min"]), p["k"]
    nl = ns * 6
    r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    s, lg = ctx.roll(r, ns, "std"), ctx.roll(r, nl, "std")
    ratio = s / np.where(lg > 0, lg, np.nan)
    move = ctx.c - ctx.prev(ctx.c, ns)
    on = ratio >= k
    fire = ctx.cross(on)
    return (fire & (move > 0)).astype(int) - (fire & (move < 0)).astype(int)


def _keltner_reentry(ctx, p):
    n, k = int(p["n_bars"]), p["k"]
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    atr = ctx.roll(ctx.h - ctx.l, n, "mean")
    up, dn = ema + k * atr, ema - k * atr
    pc = ctx.prev(ctx.c, 1)
    short = (pc > ctx.prev(up, 1)) & (ctx.c < up)
    long = (pc < ctx.prev(dn, 1)) & (ctx.c > dn)
    return long.astype(int) - short.astype(int)


def _hour_range_pos(ctx, p):
    # close back across the midpoint of the last completed 30-minute window's range, after being on the far side
    nb, nbk = ctx.bars(p["n_min"]), int(p["hold_bars"])
    hh = ctx.roll(ctx.h, nb, "max", include_current=False)
    ll = ctx.roll(ctx.l, nb, "min", include_current=False)
    width = hh - ll
    pos = (ctx.c - ll) / np.where(width > 0, width, np.nan)
    inside_hi = ctx.roll((pos > 1.0).astype(float), nbk, "sum", include_current=False)
    inside_lo = ctx.roll((pos < 0.0).astype(float), nbk, "sum", include_current=False)
    short = (inside_hi >= 1) & (pos < 1.0) & (pos > 0.0)
    long = (inside_lo >= 1) & (pos > 0.0) & (pos < 1.0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


FAMILIES = [
    Family("E-1088", "Stochastic re-entry from the extreme",
           "When the close-in-range oscillator leaves its oversold/overbought zone, the stretched side has run out of "
           "aggressors and the snap-back has room; fade the exit from the zone.",
           {"n_min": [15, 30, 60], "level": [10, 20]}, _stoch_reentry,
           source="assistant reasoning", author="agent"),
    Family("E-1089", "Channel midpoint cross",
           "A close across the midpoint of the previous N-minute high/low channel shows that buyers or sellers took "
           "the middle of the recent auction; follow the cross.",
           {"n_min": [30, 60, 120]}, _channel_mid, source="assistant reasoning", author="agent"),
    Family("E-1090", "Regression-slope t-stat trend start",
           "When the least-squares slope of the recent closes becomes statistically steep, a persistent order flow "
           "(metaorder) is working; follow the first crossing of the t threshold.",
           {"n_min": [30, 60, 120], "t": [2.0, 3.0, 4.0]}, _slope_t, source="assistant reasoning", author="agent"),
    Family("E-1091", "Narrowest-range bar break",
           "The narrowest bar of the last N bars marks a pause in two-sided trade; a close beyond its high or low "
           "releases the compressed order flow.",
           {"n_bars": [5, 8, 12]}, _nr_break, source="Crabel NR4/NR7 narrow-range days (concept applied to bars)",
           author="agent"),
    Family("E-1092", "Round-number rejection",
           "Limit orders cluster at round index levels; a bar that touches one and closes back on the other side shows "
           "the resting orders held, so trade away from the level.",
           {"step": [250, 500, 1000]}, _round_reject, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1093", "Bar-open gap follow",
           "A bar opening beyond the previous bar's extreme by a fraction of the typical range means a sweep of "
           "resting liquidity between bars; if it also closes in that direction, follow.",
           {"gap_k": [0.1, 0.25, 0.5]}, _gap_follow, source="assistant reasoning", author="agent"),
    Family("E-1094", "Volume build-up run",
           "Several consecutive bars with rising volume and rising closes, above the usual volume for the hour, show "
           "participation growing with the move; follow it.",
           {"n_bars": [2, 3, 4], "vol_k": [0.8, 1.2]}, _volume_buildup, source="volume-price analysis (Wyckoff effort/result)",
           author="agent"),
    Family("E-1095", "Prior-session midpoint cross",
           "The midpoint of yesterday's range is the fair value many desks anchor to; a close through it with a small "
           "buffer signals that today is taking value in that direction.",
           {"buffer_frac": [0.0, 0.0003, 0.0006]}, _pd_mid_cross, source="auction market theory (value area)",
           author="agent"),
    Family("E-1096", "Short-term volatility expansion follow",
           "When the short-term return volatility jumps above its own recent norm, new information is being priced; "
           "follow the direction of the move that came with it.",
           {"short_min": [5, 10, 20], "k": [1.5, 2.0, 2.5]}, _vol_expansion, source="assistant reasoning",
           author="agent"),
    Family("E-1097", "Keltner band re-entry fade",
           "A close outside the EMA plus/minus a multiple of the average bar range is an overextension; the first "
           "close back inside the band marks exhausted momentum, so fade it.",
           {"n_bars": [20, 40], "k": [1.5, 2.0, 2.5]}, _keltner_reentry, source="Keltner channel (practitioner)",
           author="agent"),
]
