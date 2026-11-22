"""Conveyor batch B-063 (agent, 2026-11-22). Classic oscillators/indicators not yet used, plus a dollar-vs-index divergence,
a return-skewness fade and a volatility-ratio jump. All index-only because of the R$30/R$30 exit."""
from __future__ import annotations

import math

import numpy as np

from b3.esteira import Family


def _sgn(long, short):
    return long.astype(int) - short.astype(int)


def _first_of_day(day):
    f = np.ones(len(day), dtype=bool)
    f[1:] = day[1:] != day[:-1]
    return f


def _dollar_divergence(ctx, p):
    nb = ctx.bars(p["win_min"])
    k = p["k"]
    oc = ctx.other_close()
    rw = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    rd = oc / ctx.prev(oc, nb) - 1.0
    sw = ctx.cached(("sdw", nb), lambda: ctx.prev_sessions(rw, "sd"))
    sd = ctx.cached(("sdd", nb), lambda: ctx.prev_sessions(rd, "sd"))
    with np.errstate(all="ignore"):
        s = rw / sw + rd / sd
    s = np.where(np.isfinite(s), s, 0.0)
    # index and dollar normally move in opposite directions; both strongly up (or down) is an unusual joint move: fade it
    return _sgn(ctx.cross(s < -k), ctx.cross(s > k))


def _skew_fade(ctx, p):
    nb = max(4, ctx.bars(p["win_min"]))
    k = p["k"]
    r1 = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    m3 = ctx.roll(r1 ** 3, nb, "mean")
    sd = ctx.roll(r1, nb, "std")
    with np.errstate(all="ignore"):
        sk = np.where(sd > 0, m3 / sd ** 3, 0.0)
    sk = np.where(np.isfinite(sk), sk, 0.0)
    return _sgn(ctx.cross(sk < -k), ctx.cross(sk > k))


def _kama(c, day, n):
    out = np.full(len(c), np.nan)
    first = _first_of_day(day)
    fsc, ssc = 2.0 / 3.0, 2.0 / 31.0
    for i in range(len(c)):
        if first[i] or not np.isfinite(out[i - 1]):
            out[i] = c[i]
            continue
        j = i - n
        if j < 0 or day[j] != day[i]:
            out[i] = c[i]
            continue
        change = abs(c[i] - c[j])
        vol = np.abs(np.diff(c[j:i + 1])).sum()
        er = change / vol if vol > 0 else 0.0
        sc = (er * (fsc - ssc) + ssc) ** 2
        out[i] = out[i - 1] + sc * (c[i] - out[i - 1])
    return out


def _kama_cross(ctx, p):
    nb = max(3, ctx.bars(p["er_min"]))
    g = p["gap_k"]
    kama = ctx.cached(("kama", nb), lambda: _kama(ctx.c, ctx.day, nb))
    rng = ctx.roll(ctx.h - ctx.l, 14, "mean")
    long = ctx.cross(ctx.c > kama + g * rng)
    short = ctx.cross(ctx.c < kama - g * rng)
    return _sgn(long, short)


def _donchian_mid(ctx, p):
    nb = ctx.bars(p["win_min"])
    hi = ctx.roll(ctx.h, nb, "max")
    lo = ctx.roll(ctx.l, nb, "min")
    mid = (hi + lo) / 2.0
    return _sgn(ctx.cross(ctx.c > mid), ctx.cross(ctx.c < mid))


def _fisher(hl2, hi, lo, day, ):
    out = np.full(len(hl2), np.nan)
    first = _first_of_day(day)
    v = f = 0.0
    for i in range(len(hl2)):
        if first[i]:
            v = f = 0.0
        if not (np.isfinite(hi[i]) and np.isfinite(lo[i])) or hi[i] <= lo[i]:
            continue
        x = (hl2[i] - lo[i]) / (hi[i] - lo[i]) - 0.5
        v = min(0.999, max(-0.999, 0.66 * x + 0.67 * v))
        f = 0.5 * math.log((1 + v) / (1 - v)) + 0.5 * f
        out[i] = f
    return out


def _fisher_hook(ctx, p):
    nb = max(3, ctx.bars(p["win_min"]))
    th = p["th"]
    hl2 = (ctx.h + ctx.l) / 2.0
    fi = ctx.cached(("fisher", nb), lambda: _fisher(hl2, ctx.roll(hl2, nb, "max"), ctx.roll(hl2, nb, "min"), ctx.day))
    f1, f2 = ctx.prev(fi, 1), ctx.prev(fi, 2)
    long = (f1 < -th) & (f2 >= f1) & (fi > f1)
    short = (f1 > th) & (f2 <= f1) & (fi < f1)
    return _sgn(long, short)


def _elder_ray(ctx, p):
    n, d = int(p["ema_bars"]), p["depth_k"]
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    rng = ctx.roll(ctx.h - ctx.l, 14, "mean")
    bull, bear = ctx.h - ema, ctx.l - ema
    rising = ema > ctx.prev(ema, 3)
    falling = ema < ctx.prev(ema, 3)
    long = rising & (bear <= -d * rng) & (bear > ctx.prev(bear, 1)) & (ctx.c > ctx.o)
    short = falling & (bull >= d * rng) & (bull < ctx.prev(bull, 1)) & (ctx.c < ctx.o)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _vortex(ctx, p):
    nb = max(2, ctx.bars(p["win_min"]))
    th = p["gap"]
    ph, pl, pc = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1), ctx.prev(ctx.c, 1)
    tr = np.maximum(ctx.h - ctx.l, np.maximum(np.abs(ctx.h - pc), np.abs(ctx.l - pc)))
    vp = ctx.roll(np.abs(ctx.h - pl), nb, "sum")
    vm = ctx.roll(np.abs(ctx.l - ph), nb, "sum")
    st = ctx.roll(tr, nb, "sum")
    with np.errstate(all="ignore"):
        d = np.where(st > 0, (vp - vm) / st, 0.0)
    d = np.where(np.isfinite(d), d, 0.0)
    return _sgn(ctx.cross(d > th), ctx.cross(d < -th))


def _ichimoku(ctx, p):
    a = ctx.bars(p["tenkan_min"])
    b = ctx.bars(p["tenkan_min"] * p["kijun_mult"])

    def mid(n):
        return (ctx.roll(ctx.h, n, "max") + ctx.roll(ctx.l, n, "min")) / 2.0

    ten, kij = mid(a), mid(b)
    return _sgn(ctx.cross(ten > kij), ctx.cross(ten < kij))


def _ao_saucer(ctx, p):
    fa, sl = ctx.bars(p["fast_min"]), ctx.bars(p["slow_min"])
    hl2 = (ctx.h + ctx.l) / 2.0
    ao = ctx.roll(hl2, fa, "mean") - ctx.roll(hl2, sl, "mean")
    a1, a2, a3 = ctx.prev(ao, 1), ctx.prev(ao, 2), ctx.prev(ao, 3)
    long = (ao > 0) & (a1 > 0) & (a2 > 0) & (a3 > a2) & (a2 > a1) & (ao > a1)
    short = (ao < 0) & (a1 < 0) & (a2 < 0) & (a3 < a2) & (a2 < a1) & (ao < a1)
    return _sgn(long, short)


def _vol_ratio_jump(ctx, p):
    sh = max(3, ctx.bars(p["short_min"]))
    k = p["k"]
    lg = max(sh * 3, ctx.bars(60))
    r1 = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    s_sh = ctx.roll(r1, sh, "std")
    s_lg = ctx.roll(r1, lg, "std")
    with np.errstate(all="ignore"):
        ratio = np.where(s_lg > 0, s_sh / s_lg, 0.0)
    ratio = np.where(np.isfinite(ratio), ratio, 0.0)
    drift = ctx.c - ctx.prev(ctx.c, sh)
    jump = ctx.cross(ratio > k)
    return _sgn(jump & (drift > 0), jump & (drift < 0))


FAMILIES = [
    Family("E-628", "Joint index-and-dollar move fade",
           "The index and the dollar normally move in opposite directions; when both rise (or fall) strongly together "
           "the index move lacks its usual macro backing and the unusual co-move tends to unwind.",
           {"win_min": [10, 20, 30], "k": [1.5, 2.0, 2.5]}, _dollar_divergence, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-629", "Return-skewness extreme fade",
           "Strong skew of recent 1-bar returns means a few jump bars dominated a window; the jump is liquidity "
           "driven and partly reverts.",
           {"win_min": [30, 60, 90], "k": [1.0, 1.5, 2.0]}, _skew_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-630", "Kaufman adaptive average cross follow",
           "KAMA slows down in noise and speeds up in efficient moves, so a close crossing it by a margin marks a "
           "trend the noise filter accepts; follow it.",
           {"er_min": [10, 20, 30], "gap_k": [0.0, 0.25, 0.5]}, _kama_cross, markets=("WIN",),
           source="Kaufman adaptive moving average (assistant reasoning)", author="agent"),
    Family("E-631", "Donchian midline cross follow",
           "The midpoint of the N-minute high-low channel is the balance level; a close crossing it shifts the "
           "side holding the recent range and trend followers join.",
           {"win_min": [20, 30, 45, 60, 90]}, _donchian_mid, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-632", "Fisher transform extreme hook",
           "The Fisher transform stretches the tails of the price position in its range; a turn out of a strong "
           "extreme shows exhaustion of a push, so trade the hook.",
           {"win_min": [30, 60, 90], "th": [1.0, 1.5, 2.0]}, _fisher_hook, markets=("WIN",),
           source="Ehlers Fisher transform (assistant reasoning)", author="agent"),
    Family("E-633", "Elder-ray pullback in a rising EMA",
           "In a trending EMA, bear (bull) power dipping deeply and turning marks the end of a pullback by "
           "counter-trend traders; resume the trend.",
           {"ema_bars": [13, 26, 40], "depth_k": [0.5, 1.0, 1.5]}, _elder_ray, markets=("WIN",),
           source="Elder ray (assistant reasoning)", author="agent"),
    Family("E-634", "Vortex indicator gap cross follow",
           "Vortex compares upward and downward travel against true range; a clear gap between the two shows one "
           "side owning the movement, and followers extend it.",
           {"win_min": [15, 30, 60], "gap": [0.0, 0.1, 0.2]}, _vortex, markets=("WIN",),
           source="Botes and Siepman vortex indicator (assistant reasoning)", author="agent"),
    Family("E-635", "Ichimoku tenkan-kijun cross follow",
           "Midpoints of two high-low windows are robust to closes; the short one crossing the long one shows "
           "the recent range shifting direction.",
           {"tenkan_min": [9, 15, 30], "kijun_mult": [2, 3, 4]}, _ichimoku, markets=("WIN",),
           source="Ichimoku Kinko Hyo (assistant reasoning)", author="agent"),
    Family("E-636", "Awesome oscillator saucer",
           "Inside a positive (negative) AO regime, two weakening bars followed by a strengthening one show "
           "momentum pausing and resuming; trade the resumption.",
           {"fast_min": [5, 10, 15], "slow_min": [30, 60, 90]}, _ao_saucer, markets=("WIN",),
           source="Bill Williams awesome oscillator (assistant reasoning)", author="agent"),
    Family("E-637", "Volatility-ratio jump follow",
           "When short-term volatility jumps relative to the last hour, new information is arriving; the direction "
           "of the short move is followed before it is fully priced.",
           {"short_min": [5, 10, 15], "k": [1.5, 2.0, 2.5]}, _vol_ratio_jump, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
