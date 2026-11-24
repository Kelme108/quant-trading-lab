"""Conveyor batch B-140 (agent, 2026-11-24). Indicator-regime ideas: Aroon, efficiency ratio, choppiness, autocorrelation regime, Heikin-Ashi flips, regression t-stat, session midline, volume expansion, prior VWAP level, money-flow."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _sgn(long, short):
    return long.astype(int) - short.astype(int)


def _aroon_osc(ctx, n):
    def calc():
        def age(arr, fn):
            s = pd.Series(arr)
            return s.groupby(ctx.day).transform(
                lambda z: z.rolling(n + 1, min_periods=n + 1).apply(lambda a: fn(a), raw=True)).to_numpy()
        up = age(ctx.h, lambda a: 100.0 * np.argmax(a) / n)
        dn = age(ctx.l, lambda a: 100.0 * np.argmin(a) / n)
        return up - dn
    return ctx.cached(("aroon", n), calc)


def _aroon_cross(ctx, p):
    n = max(3, ctx.bars(p["win_min"]))
    osc = _aroon_osc(ctx, n)
    th = p["thr"]
    return _sgn(ctx.cross(osc > th), ctx.cross(osc < -th))


def _er_follow(ctx, p):
    n = max(2, ctx.bars(p["win_min"]))
    th = p["er_min"]
    step = np.abs(ctx.c - ctx.prev(ctx.c, 1))
    path = ctx.cached(("path", n), lambda: ctx.roll(step, n, "sum"))
    net = ctx.c - ctx.prev(ctx.c, n)
    with np.errstate(divide="ignore", invalid="ignore"):
        er = np.abs(net) / path
    return _sgn(ctx.cross((er > th) & (net > 0)), ctx.cross((er > th) & (net < 0)))


def _chop_follow(ctx, p):
    n = max(3, ctx.bars(p["win_min"]))
    th = p["chop_max"]
    pc = ctx.prev(ctx.c, 1)
    tr = np.fmax(ctx.h - ctx.l, np.fmax(np.abs(ctx.h - pc), np.abs(ctx.l - pc)))
    trs = ctx.roll(tr, n, "sum")
    rng = ctx.roll(ctx.h, n, "max") - ctx.roll(ctx.l, n, "min")
    with np.errstate(divide="ignore", invalid="ignore"):
        chop = 100.0 * np.log10(trs / rng) / np.log10(n)
    net = ctx.c - ctx.prev(ctx.c, n)
    return _sgn(ctx.cross((chop < th) & (net > 0)), ctx.cross((chop < th) & (net < 0)))


def _autocorr_regime(ctx, p):
    n = max(8, ctx.bars(p["win_min"]))
    th = p["rho"]
    r = ctx.c - ctx.prev(ctx.c, 1)
    num = ctx.roll(r * ctx.prev(r, 1), n, "sum")
    den = ctx.roll(r * r, n, "sum")
    with np.errstate(divide="ignore", invalid="ignore"):
        rho = num / den
    big = np.abs(r) > ctx.roll(np.abs(r), n, "mean", include_current=False)
    trend = rho > th
    chop = rho < -th
    long = big & ((trend & (r > 0)) | (chop & (r < 0)))
    short = big & ((trend & (r < 0)) | (chop & (r > 0)))
    return _sgn(ctx.cross(long), ctx.cross(short))


def _ha_flip(ctx, p):
    k = int(p["run"])
    hac = (ctx.o + ctx.h + ctx.l + ctx.c) / 4.0
    hao = (ctx.prev(ctx.o, 1) + ctx.prev(ctx.c, 1)) / 2.0
    green = (hac > hao).astype(float)
    red = (hac < hao).astype(float)
    was_red = ctx.roll(red, k, "min", include_current=False) == 1
    was_green = ctx.roll(green, k, "min", include_current=False) == 1
    long = was_red & (green == 1)
    short = was_green & (red == 1)
    return _sgn(long, short)


def _reg_t(ctx, p):
    n = max(6, ctx.bars(p["win_min"]))
    th = p["t_min"]
    y = ctx.c - ctx.day_open
    x = ctx.bar_in_day.astype(float)
    sy = ctx.roll(y, n, "sum")
    sxy = ctx.roll(x * y, n, "sum")
    syy = ctx.roll(y * y, n, "sum")
    sx = ctx.roll(x, n, "sum")
    sxx_c = n * (n * n - 1) / 12.0
    slope = (sxy - sx * sy / n) / sxx_c
    sse = (syy - sy * sy / n) - slope * slope * sxx_c
    with np.errstate(divide="ignore", invalid="ignore"):
        se = np.sqrt(np.maximum(sse, 1e-12) / (n - 2) / sxx_c)
        t = slope / se
    return _sgn(ctx.cross(t > th), ctx.cross(t < -th))


def _session_mid_cross(ctx, p):
    m = p["min_range"]
    after = ctx.minute >= 9 * 60 + int(p["after_min"])
    sh = ctx.session_high(include_current=False)
    sl = ctx.session_low(include_current=False)
    mid = (sh + sl) / 2.0
    wide = (sh - sl) / ctx.day_open >= m
    ok = after & wide
    return _sgn(ctx.cross(ok & (ctx.c > mid)), ctx.cross(ok & (ctx.c < mid)))


def _vol_expand(ctx, p):
    ns = ctx.bars(p["short_min"])
    nl = ctx.bars(60)
    k = p["k"]
    vs = ctx.roll(ctx.v, ns, "mean")
    vl = ctx.roll(ctx.v, nl, "mean", include_current=False)
    net = ctx.c - ctx.prev(ctx.c, ns)
    bar = ctx.c - ctx.o
    hot = vs > k * vl
    return _sgn(ctx.cross(hot & (net > 0) & (bar > 0)), ctx.cross(hot & (net < 0) & (bar < 0)))


def _prev_vwap_cross(ctx, p):
    b = p["buffer_frac"]

    def last_vwap():
        vw = pd.Series(ctx.vwap())
        per = vw.groupby(ctx.day).last()
        per = per.reindex(range(int(ctx.day.max()) + 1)).shift(1)
        return per.to_numpy()[ctx.day]
    lvl = ctx.cached("prev_vwap", last_vwap)
    return _sgn(ctx.cross(ctx.c > lvl * (1 + b)), ctx.cross(ctx.c < lvl * (1 - b)))


def _cmf_follow(ctx, p):
    n = max(3, ctx.bars(p["win_min"]))
    th = p["cmf"]
    rng = ctx.h - ctx.l
    with np.errstate(divide="ignore", invalid="ignore"):
        clv = np.where(rng > 0, ((ctx.c - ctx.l) - (ctx.h - ctx.c)) / rng, 0.0)
    cmf = ctx.roll(clv * ctx.v, n, "sum") / ctx.roll(ctx.v, n, "sum")
    return _sgn(ctx.cross(cmf > th), ctx.cross(cmf < -th))


W = ("WIN",)

FAMILIES = [
    Family("E-1398", "Aroon oscillator extreme cross",
           "When the newest high is far fresher than the newest low in the window, trend followers keep adding; "
           "follow the Aroon oscillator crossing its extreme band.",
           {"win_min": [30, 60, 90], "thr": [50, 70, 90]}, _aroon_cross, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1399", "Efficiency-ratio trend onset",
           "A high Kaufman efficiency ratio means price moved with little retracement, i.e. one-sided flow that "
           "is still being absorbed; follow the first bar where it crosses the floor.",
           {"win_min": [20, 40], "er_min": [0.5, 0.6, 0.7]}, _er_follow, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1400", "Low-choppiness trend follow",
           "A low choppiness index says the true range is nearly all net travel; trend traders pile in, so follow "
           "the window direction when it drops below the threshold.",
           {"win_min": [30, 60], "chop_max": [38, 45, 50]}, _chop_follow, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1401", "Autocorrelation-regime bar trade",
           "Short-run return autocorrelation switches sign by regime: follow a large bar when recent bars "
           "trended, fade it when recent bars mean-reverted (bid-ask bounce / inventory flow).",
           {"win_min": [30, 60, 90], "rho": [0.2, 0.3, 0.4]}, _autocorr_regime, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1402", "Heikin-Ashi colour flip after a run",
           "A smoothed candle changing colour after a run of the opposite colour marks the turn of the dominant "
           "side; trade the flip.",
           {"run": [2, 3, 4]}, _ha_flip, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1403", "Regression-slope t-stat trend break-in",
           "A statistically strong linear drift since the open (high t-stat of the slope over the window) "
           "identifies persistent order-splitting; follow when it first crosses.",
           {"win_min": [30, 60], "t_min": [4, 6, 8]}, _reg_t, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1404", "Session midline cross on a wide day",
           "On a day with a wide range so far, price crossing the midpoint of the session range shifts the "
           "balance toward the other half; follow the cross.",
           {"min_range": [0.003, 0.006, 0.01], "after_min": [60, 120, 180]}, _session_mid_cross, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1405", "Volume expansion follow",
           "A sudden rise of short-term volume over the last hour's average, with price and bar pointing the same "
           "way, shows urgent participants; follow them.",
           {"short_min": [5, 10], "k": [1.5, 2.0, 3.0]}, _vol_expand, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1406", "Yesterday's final VWAP cross follow",
           "The previous session's final VWAP is the average price of all traders yesterday; a close clearly "
           "beyond it puts yesterday's participants in profit or loss and drives them.",
           {"buffer_frac": [0.0005, 0.001, 0.002]}, _prev_vwap_cross, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1407", "Chaikin money-flow band cross",
           "Volume-weighted close location over the window shows who closes bars at their extremes; a cross "
           "beyond the band means sustained buying or selling pressure, follow.",
           {"win_min": [30, 60], "cmf": [0.1, 0.2, 0.3]}, _cmf_follow, markets=W,
           source="assistant reasoning", author="agent"),
]
