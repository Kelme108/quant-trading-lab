"""Conveyor batch B-065 (agent, 2026-11-22). Less common smoothing/structure constructions: Qstick, BoP, KST-lite, zigzag flip, Hull, TMA, Elder impulse, up-close share."""
from __future__ import annotations

import numpy as np

from b3.esteira import Family


def _qstick(ctx, p):
    n, th = int(p["n"]), p["frac"]
    q = ctx.roll(ctx.c - ctx.o, n, "mean")
    rg = ctx.roll(ctx.h - ctx.l, n, "mean")
    up = q > th * rg
    dn = q < -th * rg
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _bop_fade(ctx, p):
    n, th = int(p["n"]), p["th"]
    rg = ctx.h - ctx.l
    bop = np.where(rg > 0, (ctx.c - ctx.o) / np.where(rg > 0, rg, 1.0), 0.0)
    sm = ctx.roll(bop, n, "mean")
    short = ctx.cross(sm > th)
    long = ctx.cross(sm < -th)
    return long.astype(int) - short.astype(int)


def _kst_lite(ctx, p):
    u = int(p["unit"])
    s = np.zeros(ctx.n)
    for i in (1, 2, 3, 4):
        s = s + i * (ctx.c / ctx.prev(ctx.c, u * i) - 1.0)
    return ctx.cross(s > 0).astype(int) - ctx.cross(s < 0).astype(int)


def _zigzag_flip(ctx, p):
    k = p["k"]
    out = np.zeros(ctx.n, dtype=int)
    c, day = ctx.c, ctx.day
    d = 0
    ref = 0.0
    last_day = -1
    for i in range(ctx.n):
        if day[i] != last_day:
            last_day = day[i]
            d = 0
            ref = c[i]
            continue
        b = k * ref
        if d >= 0:
            if c[i] > ref:
                ref = c[i]
            elif c[i] <= ref - b:
                if d == 1:
                    out[i] = -1
                d = -1
                ref = c[i]
        if d <= 0 and out[i] == 0:
            if c[i] < ref:
                ref = c[i]
            elif c[i] >= ref + b:
                if d == -1:
                    out[i] = 1
                d = 1
                ref = c[i]
    return out


def _roc_accel(ctx, p):
    u = int(p["bars"])
    roc = ctx.c / ctx.prev(ctx.c, u) - 1.0
    acc = roc - ctx.prev(roc, u)
    up = (roc > 0) & (acc > 0)
    dn = (roc < 0) & (acc < 0)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _elder_impulse(ctx, p):
    f = int(p["fast"])
    s = 2 * f + 2
    ema = ctx.ema(ctx.c, f * 2)
    macd = ctx.ema(ctx.c, f) - ctx.ema(ctx.c, s)
    hist = macd - ctx.ema(macd, f)
    green = (ema > ctx.prev(ema, 1)) & (hist > ctx.prev(hist, 1))
    red = (ema < ctx.prev(ema, 1)) & (hist < ctx.prev(hist, 1))
    return ctx.cross(green).astype(int) - ctx.cross(red).astype(int)


def _tma_turn(ctx, p):
    n = int(p["n"])
    t = ctx.roll(ctx.roll(ctx.c, n, "mean"), n, "mean")
    sl = t - ctx.prev(t, 1)
    return ctx.cross(sl > 0).astype(int) - ctx.cross(sl < 0).astype(int)


def _wma(ctx, x, n):
    num = np.zeros(ctx.n)
    for j in range(n):
        num = num + (n - j) * (x if j == 0 else ctx.prev(x, j))
    return num / (n * (n + 1) / 2.0)


def _hull_turn(ctx, p):
    n = int(p["n"])
    n2, sq = max(2, n // 2), max(2, int(round(n ** 0.5)))
    raw = 2 * _wma(ctx, ctx.c, n2) - _wma(ctx, ctx.c, n)
    hull = _wma(ctx, raw, sq)
    sl = hull - ctx.prev(hull, 1)
    return ctx.cross(sl > 0).astype(int) - ctx.cross(sl < 0).astype(int)


def _upclose_share(ctx, p):
    n, th = int(p["n"]), p["th"]
    up = (ctx.c > ctx.prev(ctx.c, 1)).astype(float)
    dn = (ctx.c < ctx.prev(ctx.c, 1)).astype(float)
    su = ctx.roll(up, n, "mean")
    sd = ctx.roll(dn, n, "mean")
    return ctx.cross(su >= th).astype(int) - ctx.cross(sd >= th).astype(int)


def _pr_hook(ctx, p):
    n, th = ctx.bars(p["lookback_min"]), p["th"]
    hi = ctx.roll(ctx.h, n, "max")
    lo = ctx.roll(ctx.l, n, "min")
    f = (ctx.c - lo) / np.where(hi > lo, hi - lo, np.nan)
    pf = ctx.prev(f, 1)
    long = (pf <= th) & (f > th) & (f < 0.5)
    short = (pf >= 1 - th) & (f < 1 - th) & (f > 0.5)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-648", "Qstick body-sum follow",
           "A rolling mean of candle bodies large relative to the mean range shows persistent one-sided aggression "
           "that is slow to be absorbed; follow the onset.",
           {"n": [8, 12, 20], "frac": [0.1, 0.2, 0.3]}, _qstick, source="assistant reasoning", author="agent"),
    Family("E-649", "Smoothed balance-of-power extreme fade",
           "When the smoothed (close-open)/(high-low) ratio is extreme, one side has pushed every bar to the edge; "
           "late chasers are exposed and the move tends to give back.",
           {"n": [10, 15, 20], "th": [0.3, 0.4, 0.5]}, _bop_fade, source="assistant reasoning", author="agent"),
    Family("E-650", "KST-lite multi-horizon ROC zero cross",
           "A weighted sum of four rate-of-change horizons crossing zero marks a trend change that several time "
           "scales of participants agree on; follow it.",
           {"unit": [3, 5, 8]}, _kst_lite, source="assistant reasoning", author="agent"),
    Family("E-651", "Zigzag reversal confirmation follow",
           "After a swing is confirmed by a retrace of a fixed fraction of price, the reversal has trapped the "
           "previous trend's late entrants; follow the new swing direction.",
           {"k": [0.0015, 0.002, 0.003]}, _zigzag_flip, source="assistant reasoning", author="agent"),
    Family("E-652", "Rate-of-change acceleration onset",
           "When momentum is positive and its change over the same horizon turns positive too, buying pressure is "
           "building, not fading; follow the onset of acceleration.",
           {"bars": [5, 10, 15]}, _roc_accel, source="assistant reasoning", author="agent"),
    Family("E-653", "Elder impulse colour onset",
           "Slope of an EMA and slope of the MACD histogram both rising means trend and momentum agree; the first "
           "bar of agreement is an entry for trend followers.",
           {"fast": [5, 8, 12]}, _elder_impulse, source="Elder impulse system (Come Into My Trading Room), assistant reasoning",
           author="agent"),
    Family("E-654", "Triangular moving average slope turn",
           "A doubly smoothed average filters bar noise; when its slope changes sign the underlying drift has "
           "changed and positions of slower participants lag behind.",
           {"n": [8, 12, 20]}, _tma_turn, source="assistant reasoning", author="agent"),
    Family("E-655", "Hull average slope turn",
           "The Hull average reacts with little lag; a slope turn catches turns early, before slower averages, "
           "so slower trend followers become the fuel.",
           {"n": [10, 20, 30]}, _hull_turn, source="Hull moving average (A. Hull), assistant reasoning", author="agent"),
    Family("E-656", "Up-close share thrust follow",
           "When nearly all recent closes are higher than the previous close, buy orders arrive steadily "
           "(metered execution of a large order); follow the first bar the share crosses the threshold.",
           {"n": [10, 20, 30], "th": [0.65, 0.7, 0.75]}, _upclose_share, source="assistant reasoning", author="agent"),
    Family("E-657", "Range-position hook out of the extreme",
           "After the close sits in the lowest (highest) slice of the rolling range and then lifts out of it while "
           "still in the lower (upper) half, the extreme was rejected; fade back toward the middle.",
           {"lookback_min": [30, 60, 90], "th": [0.1, 0.15, 0.2]}, _pr_hook, source="assistant reasoning", author="agent"),
]
