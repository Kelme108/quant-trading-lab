"""Conveyor batch B-048 (agent, 2026-11-21). Multi-session level edges (closes, last hour, robust 2nd extremes, weekly pivots) faded on a touch, plus trend-quality and trailing-line follow ideas."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _per_session(ctx, arr, agg):
    s = pd.Series(np.asarray(arr, float)).groupby(ctx.day).agg(agg)
    return s.reindex(range(int(ctx.day.max()) + 1))


def _to_bars(ctx, s):
    return s.to_numpy()[ctx.day]


def _roll_prev_sessions(ctx, arr, agg, n, how):
    r = _per_session(ctx, arr, agg).shift(1).rolling(n, min_periods=n)
    return _to_bars(ctx, r.max() if how == "max" else r.min())


def _edge_fade(ctx, hi, lo, k):
    br = ctx.cached("bar_range_mean", lambda: ctx.prev_sessions(ctx.h - ctx.l, "mean"))
    tol = k * br
    zh, zl = hi - tol, lo + tol
    short = (ctx.h >= zh) & (ctx.c < zh)
    long = (ctx.l <= zl) & (ctx.c > zl)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _close_extreme_fade(ctx, p):
    n = int(p["n_sessions"])
    hi = _roll_prev_sessions(ctx, ctx.c, "last", n, "max")
    lo = _roll_prev_sessions(ctx, ctx.c, "last", n, "min")
    return _edge_fade(ctx, hi, lo, p["k"])


def _last_hour_edge_fade(ctx, p):
    n = int(p["n_sessions"])
    late = ctx.minutes_to_close <= 60
    hi = _roll_prev_sessions(ctx, np.where(late, ctx.h, np.nan), "max", n, "max")
    lo = _roll_prev_sessions(ctx, np.where(late, ctx.l, np.nan), "min", n, "min")
    return _edge_fade(ctx, hi, lo, p["k"])


def _second_extreme_fade(ctx, p):
    n = int(p["n_sessions"])
    ph = _per_session(ctx, ctx.h, "max").shift(1)
    pl = _per_session(ctx, ctx.l, "min").shift(1)
    hi2 = ph.rolling(n, min_periods=n).apply(lambda x: np.sort(x)[-2], raw=True)
    lo2 = pl.rolling(n, min_periods=n).apply(lambda x: np.sort(x)[1], raw=True)
    return _edge_fade(ctx, _to_bars(ctx, hi2), _to_bars(ctx, lo2), p["k"])


def _price_time_corr(ctx, p):
    n = ctx.bars(p["win_min"])
    th = p["th"]
    x = ctx.bar_in_day.astype(float)
    y = ctx.c - ctx.day_open
    sx = ctx.roll(x, n, "sum")
    sy = ctx.roll(y, n, "sum")
    sxy = ctx.roll(x * y, n, "sum")
    sxx = ctx.roll(x * x, n, "sum")
    syy = ctx.roll(y * y, n, "sum")
    with np.errstate(all="ignore"):
        den = np.sqrt(np.maximum(n * sxx - sx * sx, 0.0) * np.maximum(n * syy - sy * sy, 0.0))
        r = np.where(den > 0, (n * sxy - sx * sy) / den, np.nan)
    return ctx.cross(r >= th).astype(int) - ctx.cross(r <= -th).astype(int)


def _supertrend(ctx, n, m):
    def build():
        prev_c = ctx.prev(ctx.c, 1)
        tr = np.maximum(ctx.h - ctx.l, np.maximum(np.abs(ctx.h - prev_c), np.abs(ctx.l - prev_c)))
        tr = np.where(np.isnan(prev_c), ctx.h - ctx.l, tr)
        atr = ctx.ema(tr, n)
        hl2 = (ctx.h + ctx.l) / 2.0
        ub, lb = (hl2 + m * atr).tolist(), (hl2 - m * atr).tolist()
        c, day, a, mid = ctx.c.tolist(), ctx.day.tolist(), atr.tolist(), hl2.tolist()
        N = len(c)
        trend = [0] * N
        fub, flb = [0.0] * N, [0.0] * N
        for i in range(N):
            if a[i] != a[i] or (i > 0 and day[i] != day[i - 1]):
                if a[i] == a[i]:
                    fub[i], flb[i] = ub[i], lb[i]
                    trend[i] = 1 if c[i] > mid[i] else -1
                continue
            if i == 0 or trend[i - 1] == 0:
                fub[i], flb[i] = ub[i], lb[i]
                trend[i] = 1 if c[i] > mid[i] else -1
                continue
            fub[i] = ub[i] if (ub[i] < fub[i - 1] or c[i - 1] > fub[i - 1]) else fub[i - 1]
            flb[i] = lb[i] if (lb[i] > flb[i - 1] or c[i - 1] < flb[i - 1]) else flb[i - 1]
            t = trend[i - 1]
            if t == -1 and c[i] > fub[i - 1]:
                t = 1
            elif t == 1 and c[i] < flb[i - 1]:
                t = -1
            trend[i] = t
        return np.array(trend, dtype=int)
    return ctx.cached(("supertrend", n, m), build)


def _supertrend_flip(ctx, p):
    t = _supertrend(ctx, int(p["atr_n"]), float(p["mult"]))
    pt = ctx.prev(t.astype(float), 1)
    up = (t == 1) & (pt == -1)
    dn = (t == -1) & (pt == 1)
    return up.astype(int) - dn.astype(int)


def _weekly_pivot_fade(ctx, p):
    n = int(p["n_sessions"])
    hn = _roll_prev_sessions(ctx, ctx.h, "max", n, "max")
    ln = _roll_prev_sessions(ctx, ctx.l, "min", n, "min")
    cl = _to_bars(ctx, _per_session(ctx, ctx.c, "last").shift(1))
    piv = (hn + ln + cl) / 3.0
    r1 = 2 * piv - ln
    s1 = 2 * piv - hn
    return _edge_fade(ctx, r1, s1, p["k"])


def _dema_turn(ctx, p):
    n = int(p["span"])
    e1 = ctx.ema(ctx.c, n)
    e2 = ctx.ema(np.nan_to_num(e1, nan=0.0) + np.where(np.isnan(e1), ctx.c, 0.0), n)
    dema = 2 * e1 - e2
    d1 = dema - ctx.prev(dema, 1)
    d1p = ctx.prev(d1, 1)
    up = (d1 > 0) & (d1p <= 0)
    dn = (d1 < 0) & (d1p >= 0)
    return up.astype(int) - dn.astype(int)


def _rvi_cross(ctx, p):
    n = int(p["n"])
    co = ctx.c - ctx.o
    hl = ctx.h - ctx.l
    def sm(x):
        return (x + 2 * ctx.prev(x, 1) + 2 * ctx.prev(x, 2) + ctx.prev(x, 3)) / 6.0
    num = ctx.roll(sm(co), n, "mean")
    den = ctx.roll(sm(hl), n, "mean")
    with np.errstate(all="ignore"):
        rvi = np.where(den > 0, num / den, np.nan)
    sig = (rvi + 2 * ctx.prev(rvi, 1) + 2 * ctx.prev(rvi, 2) + ctx.prev(rvi, 3)) / 6.0
    pr, ps_ = ctx.prev(rvi, 1), ctx.prev(sig, 1)
    up = (rvi > sig) & (pr <= ps_) & (rvi < 0)
    dn = (rvi < sig) & (pr >= ps_) & (rvi > 0)
    return up.astype(int) - dn.astype(int)


def _kama(ctx, n):
    def build():
        c, day = ctx.c, ctx.day
        lag = ctx.prev(c, n)
        ad = np.abs(c - ctx.prev(c, 1))
        vol = ctx.roll(ad, n, "sum")
        with np.errstate(all="ignore"):
            er = np.where(vol > 0, np.abs(c - lag) / vol, np.nan)
        fast, slow = 2.0 / 3.0, 2.0 / 31.0
        sc = ((er * (fast - slow) + slow) ** 2).tolist()
        cl, dl = c.tolist(), day.tolist()
        out = [float("nan")] * len(cl)
        for i in range(len(cl)):
            if sc[i] != sc[i]:
                continue
            if i == 0 or dl[i] != dl[i - 1] or out[i - 1] != out[i - 1]:
                out[i] = cl[i]
            else:
                out[i] = out[i - 1] + sc[i] * (cl[i] - out[i - 1])
        return np.array(out)
    return ctx.cached(("kama", n), build)


def _kama_cross(ctx, p):
    k = _kama(ctx, int(p["n"]))
    flt = p["slope_bars"]
    sl = k - ctx.prev(k, int(flt))
    up = ctx.cross((ctx.c > k) & (sl > 0))
    dn = ctx.cross((ctx.c < k) & (sl < 0))
    return up.astype(int) - dn.astype(int)


def _hilo_break(ctx, p):
    n = int(p["n"])
    hm = ctx.roll(ctx.h, n, "mean", include_current=False)
    lm = ctx.roll(ctx.l, n, "mean", include_current=False)
    up = ctx.cross(ctx.c > hm)
    dn = ctx.cross(ctx.c < lm)
    return up.astype(int) - dn.astype(int)


W = ("WIN",)
FAMILIES = [
    Family("E-478", "Multi-session closing-extreme touch fade",
           "The highest/lowest SESSION CLOSE of the last n sessions is where overnight holders last accepted price; "
           "a bar that probes that line and closes back away from it meets passive supply/demand, so fade it.",
           {"n_sessions": [3, 5, 10], "k": [0.0, 1.0, 2.0]}, _close_extreme_fade, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-479", "Multi-session last-hour edge touch fade",
           "The extremes printed in the final hour of recent sessions are where late positions were squeezed in or "
           "out; a probe of that edge that closes back is a stale-level rejection, fade it.",
           {"n_sessions": [3, 5, 10], "k": [0.0, 1.0, 2.0]}, _last_hour_edge_fade, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-480", "Second-extreme robust edge fade",
           "The single most extreme daily high/low of the last n sessions is often a one-off spike; the SECOND "
           "most extreme is the level the market keeps defending. A probe that closes back is fade material.",
           {"n_sessions": [10, 15, 20], "k": [0.0, 1.0, 2.0]}, _second_extreme_fade, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-481", "Price-time correlation trend onset",
           "When session price correlates almost perfectly with time over a window, the move is orderly "
           "(one-sided flow, few pullbacks); the first bar where this trend quality is reached marks a persistent "
           "program, follow it.",
           {"win_min": [30, 60, 90], "th": [0.85, 0.9, 0.95]}, _price_time_corr, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-482", "Supertrend flip follow",
           "An ATR-based trailing line flips only when price travels against the trend by several ranges, "
           "which means stops of the old trend are run and new-direction orders enter; follow the flip.",
           {"atr_n": [10, 20], "mult": [2.0, 3.0]}, _supertrend_flip, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-483", "Multi-session floor-pivot R1/S1 touch fade",
           "Pivots built from the last n sessions' high, low and close are used by many discretionary traders; "
           "R1/S1 act as self-fulfilling turning points, so a touch that closes back is faded.",
           {"n_sessions": [5, 10, 20], "k": [0.0, 1.0, 2.0]}, _weekly_pivot_fade, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-484", "Double-EMA slope turn follow",
           "A double exponential average removes most lag; its slope changing sign is an early sign that "
           "short-term order flow has turned, before slower averages show it.",
           {"span": [10, 20, 40]}, _dema_turn, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-485", "Relative Vigor Index signal cross from the wrong side",
           "RVI measures how far bars close from their open relative to their range; a cross of its smoothed "
           "signal while still on the opposite side of zero marks the first bar-shape evidence that conviction "
           "has switched.",
           {"n": [5, 10, 20]}, _rvi_cross, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-486", "Adaptive-average (KAMA) cross follow",
           "Kaufman's adaptive average hugs price when the move is efficient and flattens in noise, so a close "
           "through it with the average already sloping that way happens mainly in efficient moves; follow it.",
           {"n": [10, 20, 30], "slope_bars": [2, 3]}, _kama_cross, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-487", "Average-high/low activator break",
           "A close beyond the mean of the last n highs (or lows) means price left the area where recent supply "
           "(demand) was working; the Gann Hi-Lo activator logic says follow it.",
           {"n": [5, 10, 20]}, _hilo_break, markets=W,
           source="assistant reasoning", author="agent"),
]
