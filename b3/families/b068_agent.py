"""Conveyor batch B-068 (agent, 2026-11-22). Indicator-style triggers not yet screened: Vortex, MFI, KAMA, Elder ray,
regression t-stat, volume-gated rolling VWAP, MA ribbon, converging triangle, absorption bar, body acceleration."""
from __future__ import annotations

import numpy as np

from b3.esteira import Family


def _sgn(long, short):
    return long.astype(int) - short.astype(int)


def _vortex(ctx, p):
    n, m = int(p["n"]), p["margin"]
    pc = ctx.prev(ctx.c, 1)
    tr = np.maximum(ctx.h - ctx.l, np.maximum(np.abs(ctx.h - pc), np.abs(ctx.l - pc)))
    vmp = np.abs(ctx.h - ctx.prev(ctx.l, 1))
    vmm = np.abs(ctx.l - ctx.prev(ctx.h, 1))
    st = ctx.roll(tr, n, "sum")
    with np.errstate(all="ignore"):
        vip = ctx.roll(vmp, n, "sum") / st
        vim = ctx.roll(vmm, n, "sum") / st
    return _sgn(ctx.cross(vip - vim > m), ctx.cross(vim - vip > m))


def _mfi(ctx, p):
    n, lo = int(p["n"]), p["lo"]
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    mf = tp * ctx.v
    d = tp - ctx.prev(tp, 1)
    pos = ctx.roll(np.where(d > 0, mf, 0.0), n, "sum")
    neg = ctx.roll(np.where(d < 0, mf, 0.0), n, "sum")
    den = pos + neg
    with np.errstate(all="ignore"):
        mfi = np.where(den > 0, 100.0 * pos / den, np.nan)
    return _sgn(ctx.cross(mfi > lo), ctx.cross(mfi < 100.0 - lo))


def _kama_turn(ctx, p):
    n, m = int(p["n"]), p["min_turn"]
    c = ctx.c
    ad = np.abs(c - ctx.prev(c, 1))
    den = ctx.roll(ad, n, "sum")
    num = np.abs(c - ctx.prev(c, n))
    with np.errstate(all="ignore"):
        er = np.where(den > 0, num / den, np.nan)
    sc_fast, sc_slow = 2.0 / 3.0, 2.0 / 31.0
    N = len(c)
    k = np.full(N, np.nan)
    day = ctx.day
    for i in range(N):
        same = i > 0 and day[i] == day[i - 1] and not np.isnan(k[i - 1])
        if same:
            e = er[i] if not np.isnan(er[i]) else 0.0
            sc = (e * (sc_fast - sc_slow) + sc_slow) ** 2
            k[i] = k[i - 1] + sc * (c[i] - k[i - 1])
        elif not np.isnan(er[i]):
            k[i] = c[i]
    d = k - ctx.prev(k, 1)
    avg = ctx.roll(ad, n, "mean")
    up = (d > m * avg) & (ctx.prev(d, 1) <= 0) & (c > k)
    dn = (d < -m * avg) & (ctx.prev(d, 1) >= 0) & (c < k)
    return _sgn(up, dn)


def _elder_ray(ctx, p):
    span, k = int(p["span"]), int(p["trend_lag"])
    e = ctx.cached(("ema", span), lambda: ctx.ema(ctx.c, span))
    bear = ctx.l - e
    bull = ctx.h - e
    up_tr = e > ctx.prev(e, k)
    dn_tr = e < ctx.prev(e, k)
    long = up_tr & (bear < 0) & (bear > ctx.prev(bear, 1)) & (ctx.prev(bear, 1) <= ctx.prev(bear, 2)) & (ctx.c > ctx.o)
    short = dn_tr & (bull > 0) & (bull < ctx.prev(bull, 1)) & (ctx.prev(bull, 1) >= ctx.prev(bull, 2)) & (ctx.c < ctx.o)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _reg_tstat(ctx, p):
    n = max(6, ctx.bars(p["n_min"]))
    k = p["k"]
    x = ctx.bar_in_day.astype(float)
    y = ctx.c - ctx.day_open
    sy = ctx.roll(y, n, "sum")
    sxy_g = ctx.roll(x * y, n, "sum")
    syy = ctx.roll(y * y, n, "sum")
    x0 = ctx.prev(x, n - 1)                       # first bar index of the window
    sxy = sxy_g - x0 * sy                          # sum of (x - x0) * y
    sx = n * (n - 1) / 2.0
    sxx = sum(j * j for j in range(n))
    cxy = sxy - sx * sy / n
    cxx = sxx - sx * sx / n
    cyy = syy - sy * sy / n
    with np.errstate(all="ignore"):
        slope = cxy / cxx
        sse = np.maximum(cyy - slope * cxy, 1e-12)
        se = np.sqrt(sse / (n - 2) / cxx)
        t = slope / se
    return _sgn(ctx.cross(t > k), ctx.cross(t < -k))


def _rolling_vwap_gate(ctx, p):
    n = max(3, ctx.bars(p["n_min"]))
    vk = p["vol_k"]
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    sv = ctx.roll(ctx.v, n, "sum")
    with np.errstate(all="ignore"):
        rv = ctx.roll(tp * ctx.v, n, "sum") / sv
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    heavy = ctx.v >= vk * med
    up = (ctx.c > rv) & (ctx.prev(ctx.c, 1) <= ctx.prev(rv, 1)) & heavy & (rv > ctx.prev(rv, 1))
    dn = (ctx.c < rv) & (ctx.prev(ctx.c, 1) >= ctx.prev(rv, 1)) & heavy & (rv < ctx.prev(rv, 1))
    return _sgn(up, dn)


def _ribbon(ctx, p):
    a, m = int(p["base"]), int(p["mult"])
    e1 = ctx.cached(("ema", a), lambda: ctx.ema(ctx.c, a))
    e2 = ctx.cached(("ema", a * m), lambda: ctx.ema(ctx.c, a * m))
    e3 = ctx.cached(("ema", a * m * m), lambda: ctx.ema(ctx.c, a * m * m))
    up = (ctx.c > e1) & (e1 > e2) & (e2 > e3)
    dn = (ctx.c < e1) & (e1 < e2) & (e2 < e3)
    return _sgn(ctx.cross(up), ctx.cross(dn))


def _triangle(ctx, p):
    half = max(2, ctx.bars(p["n_min"]) // 2)
    ratio = p["ratio"]
    hi = ctx.roll(ctx.h, half, "max")
    lo = ctx.roll(ctx.l, half, "min")
    hi1, lo1 = ctx.prev(hi, 1), ctx.prev(lo, 1)
    hi0, lo0 = ctx.prev(hi, half + 1), ctx.prev(lo, half + 1)
    conv = (hi1 < hi0) & (lo1 > lo0) & ((hi1 - lo1) <= ratio * (hi0 - lo0))
    return _sgn(ctx.cross(conv & (ctx.c > hi1)), ctx.cross(conv & (ctx.c < lo1)))


def _absorption(ctx, p):
    vk = p["vol_k"]
    m = max(2, ctx.bars(p["m_min"]))
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    rng = ctx.h - ctx.l
    doji = (np.abs(ctx.c - ctx.o) <= 0.25 * rng) & (rng > 0)
    a = doji & (ctx.v >= vk * med)
    ha = ctx.roll(np.where(a, ctx.h, -1e18), m, "max", include_current=False)
    la = ctx.roll(np.where(a, ctx.l, 1e18), m, "min", include_current=False)
    long = (ha > -1e17) & (ctx.c > ha)
    short = (la < 1e17) & (ctx.c < la)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _accel(ctx, p):
    run, k = int(p["run"]), p["k"]
    body = np.abs(ctx.c - ctx.o)
    avg = ctx.roll(body, 20, "mean", include_current=False)
    inc = body >= k * avg
    up = (ctx.c > ctx.o) & inc
    dn = (ctx.c < ctx.o) & inc
    for j in range(run - 1):
        bj, bj1 = ctx.prev(body, j), ctx.prev(body, j + 1)
        up = up & (bj > bj1) & (ctx.prev(ctx.c, j + 1) > ctx.prev(ctx.o, j + 1))
        dn = dn & (bj > bj1) & (ctx.prev(ctx.c, j + 1) < ctx.prev(ctx.o, j + 1))
    return _sgn(ctx.cross(up), ctx.cross(dn))


W = ("WIN",)
FAMILIES = [
    Family("E-678", "Vortex indicator cross",
           "VI+ over VI- measures which side's bar-to-bar excursions dominate; a cross with a margin marks directional "
           "control that trend followers and stop orders extend.",
           {"n": [10, 14, 20], "margin": [0.0, 0.1, 0.2]}, _vortex, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-679", "MFI oversold/overbought exit",
           "Volume-weighted RSI leaving an extreme means forced sellers/buyers are exhausted; take the reversal.",
           {"n": [10, 14, 20], "lo": [15, 20, 25]}, _mfi, markets=W, source="assistant reasoning", author="agent"),
    Family("E-680", "KAMA slope turn",
           "The adaptive average ignores noise and only turns when efficient movement appears; a turn with price on "
           "the new side signals a new directional leg.",
           {"n": [10, 20, 30], "min_turn": [0.0, 0.1, 0.2]}, _kama_turn, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-681", "Elder-ray pullback turn",
           "In a rising EMA, bear power (low minus EMA) turning up from below shows sellers failing to push under "
           "the trend average; buy the turn (mirror for sells).",
           {"span": [8, 13, 21], "trend_lag": [1, 3, 5]}, _elder_ray, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-682", "Regression slope t-stat break",
           "A statistically strong linear trend over a window (large slope t-stat) means persistent one-sided "
           "flow; follow its first crossing of the threshold.",
           {"n_min": [30, 60, 90], "k": [3.0, 5.0, 8.0]}, _reg_tstat, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-683", "Heavy-volume rolling-VWAP cross",
           "A cross of the rolling VWAP on above-typical volume, with the VWAP itself sloping that way, means the "
           "recent average cost basis is being reclaimed by active participants.",
           {"n_min": [30, 60, 120], "vol_k": [0.8, 1.0, 1.5]}, _rolling_vwap_gate, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-684", "EMA ribbon full alignment",
           "When price and three geometric EMAs line up in order, short, medium and long horizons agree; the first "
           "bar of alignment starts a trend leg.",
           {"base": [3, 5, 8], "mult": [2, 3]}, _ribbon, markets=W, source="assistant reasoning", author="agent"),
    Family("E-685", "Converging triangle break",
           "Lower highs and higher lows with a shrinking range compress resting orders at both edges; the close "
           "beyond the recent half-window edge releases it.",
           {"n_min": [20, 40, 60], "ratio": [0.5, 0.7, 0.9]}, _triangle, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-686", "Heavy-volume doji absorption break",
           "A high-volume bar with a tiny body means large orders absorbed the flow without moving price; a close "
           "beyond its range shows which side was absorbed and follows.",
           {"vol_k": [1.5, 2.0, 3.0], "m_min": [15, 30, 60]}, _absorption, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-687", "Growing-body run follow",
           "Same-colour bars with ever larger bodies show urgency building (market orders chasing); the bar that "
           "extends the acceleration is followed.",
           {"run": [3, 4], "k": [0.8, 1.0, 1.5]}, _accel, markets=W, source="assistant reasoning", author="agent"),
]
