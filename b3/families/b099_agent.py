"""Conveyor batch B-099 (agent, 2026-11-24). Classic indicator-state changes not yet screened: TRIX, Hull-style EMA,
QStick, Awesome Oscillator, candle soldiers/crows, EMA ribbon, PVT, Market Facilitation, RVI, Pretty Good Oscillator."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _sig(ctx, up, dn):
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _tr(ctx):
    pc = ctx.prev(ctx.c, 1)
    return np.fmax(ctx.h - ctx.l, np.fmax(np.abs(ctx.h - pc), np.abs(ctx.l - pc)))


def _trix(ctx, p):
    n = ctx.bars(p["span_min"])
    lc = np.log(ctx.c)
    e3 = ctx.ema(ctx.ema(ctx.ema(lc, n), n), n)
    tx = e3 - ctx.prev(e3, 1)
    return _sig(ctx, tx > 0, tx < 0)


def _hull(ctx, p):
    n = ctx.bars(p["span_min"])
    raw = 2 * ctx.ema(ctx.c, max(1, n // 2)) - ctx.ema(ctx.c, n)
    hm = ctx.ema(raw, max(2, int(round(np.sqrt(n)))))
    s1, s2 = ctx.prev(hm, 1), ctx.prev(hm, 2)
    up = (hm > s1) & (s1 <= s2)
    dn = (hm < s1) & (s1 >= s2)
    return up.astype(int) - dn.astype(int)


def _qstick(ctx, p):
    q = ctx.roll(ctx.c - ctx.o, ctx.bars(p["win_min"]), "mean")
    return _sig(ctx, q > 0, q < 0)


def _ao(ctx, p):
    med = (ctx.h + ctx.l) / 2
    ao = ctx.roll(med, ctx.bars(p["fast_min"]), "mean") - ctx.roll(med, ctx.bars(p["slow_min"]), "mean")
    return _sig(ctx, ao > 0, ao < 0)


def _soldiers(ctx, p):
    f = p["body_frac"]
    rng = ctx.h - ctx.l
    body = ctx.c - ctx.o
    su = (body >= f * rng) & (rng > 0)
    sd = (-body >= f * rng) & (rng > 0)
    up = su & ctx.prev(su.astype(float), 1).astype(bool) & ctx.prev(su.astype(float), 2).astype(bool)
    up &= (ctx.c > ctx.prev(ctx.c, 1)) & (ctx.prev(ctx.c, 1) > ctx.prev(ctx.c, 2))
    dn = sd & ctx.prev(sd.astype(float), 1).astype(bool) & ctx.prev(sd.astype(float), 2).astype(bool)
    dn &= (ctx.c < ctx.prev(ctx.c, 1)) & (ctx.prev(ctx.c, 1) < ctx.prev(ctx.c, 2))
    return _sig(ctx, up, dn)


def _ribbon(ctx, p):
    m = p["fast_min"]
    f, mi, s = (ctx.ema(ctx.c, ctx.bars(m * k)) for k in (1, 2.5, 6))
    up = (f > mi) & (mi > s)
    dn = (f < mi) & (mi < s)
    return _sig(ctx, up, dn)


def _pvt(ctx, p):
    ret = np.nan_to_num(ctx.c / ctx.prev(ctx.c, 1) - 1.0, nan=0.0)
    pvt = pd.Series(ctx.v * ret).groupby(ctx.day).cumsum().to_numpy()
    e = ctx.ema(pvt, ctx.bars(p["span_min"]))
    return _sig(ctx, pvt > e, pvt < e)


def _mfi_green(ctx, p):
    k = p["vol_k"]
    mf = (ctx.h - ctx.l) / np.maximum(ctx.v, 1.0)
    green = (mf > ctx.prev(mf, 1)) & (ctx.v > ctx.prev(ctx.v, 1))
    big = ctx.v > k * ctx.cached("vmed_mfi", lambda: ctx.same_minute(ctx.v, "median"))
    g = green & big
    return np.where(g & (ctx.c > ctx.o), 1, 0) - np.where(g & (ctx.c < ctx.o), 1, 0)


def _rvi(ctx, p):
    n, th = ctx.bars(p["span_min"]), p["band"]
    sd = ctx.roll(ctx.c, 10, "std")
    d = ctx.c - ctx.prev(ctx.c, 1)
    u = ctx.ema(np.where(d > 0, sd, 0.0), n)
    dd = ctx.ema(np.where(d < 0, sd, 0.0), n)
    rvi = 100 * u / np.maximum(u + dd, 1e-12)
    return _sig(ctx, rvi > 50 + th, rvi < 50 - th)


def _pgo(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    pgo = (ctx.c - ctx.roll(ctx.c, n, "mean")) / np.maximum(ctx.ema(_tr(ctx), n), 1e-9)
    return _sig(ctx, pgo > k, pgo < -k)


FAMILIES = [
    Family("E-988", "TRIX zero-cross follow",
           "Triple-smoothed log-price slope changing sign filters noise out; participants chasing the confirmed turn keep pushing.",
           {"span_min": [5, 10, 15]}, _trix, source="assistant reasoning", author="agent"),
    Family("E-989", "Hull-style EMA slope turn follow",
           "A low-lag average changing slope marks the earliest trend turn; late counter-trend traders get squeezed.",
           {"span_min": [15, 30, 60]}, _hull, source="assistant reasoning", author="agent"),
    Family("E-990", "QStick zero-cross follow",
           "The mean candle body (close minus open) changing sign shows aggressors switching side; follow them.",
           {"win_min": [10, 15, 30]}, _qstick, source="assistant reasoning", author="agent"),
    Family("E-991", "Awesome Oscillator zero-cross follow",
           "Median-price fast/slow average crossing means momentum has changed hands; trend followers add.",
           {"fast_min": [5, 8, 10], "slow_min": [21, 34, 55]}, _ao, source="assistant reasoning", author="agent"),
    Family("E-992", "Three soldiers / three crows continuation",
           "Three full-body bars in a row with rising closes show persistent one-sided aggression, not yet exhausted.",
           {"body_frac": [0.5, 0.6, 0.7]}, _soldiers, source="assistant reasoning", author="agent"),
    Family("E-993", "EMA ribbon alignment follow",
           "When fast, mid and slow EMAs line up in order, short and medium horizons agree; follow the first aligned bar.",
           {"fast_min": [3, 5, 8]}, _ribbon, source="assistant reasoning", author="agent"),
    Family("E-994", "Price-volume trend cross follow",
           "Cumulative volume weighted by return rising above its own average shows volume backing the move.",
           {"span_min": [15, 30, 60]}, _pvt, source="assistant reasoning", author="agent"),
    Family("E-995", "Market-facilitation green bar follow",
           "A bar with rising range per volume AND rising volume (Bill Williams green bar) shows real participation; follow its colour.",
           {"vol_k": [0.8, 1.0, 1.5]}, _mfi_green, source="assistant reasoning", author="agent"),
    Family("E-996", "Relative volatility index band cross follow",
           "When volatility concentrates on up closes rather than down closes, buyers dominate the risk; follow the crossing.",
           {"span_min": [10, 15, 30], "band": [5, 10]}, _rvi, source="assistant reasoning", author="agent"),
    Family("E-997", "Pretty Good Oscillator breakout follow",
           "Distance from the moving average in average-range units beyond k means a break from the mean that attracts momentum orders.",
           {"win_min": [15, 30, 60], "k": [2.0, 3.0, 4.0]}, _pgo, source="assistant reasoning", author="agent"),
]
