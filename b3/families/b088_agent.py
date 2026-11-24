"""Conveyor batch B-088 (agent, 2026-11-23). Mixed mechanisms: regime-switch autocorrelation, bar overlap, volatility onset,
two-bar spring, yesterday-range completion, leg retracement, narrow-body cluster, relative-volume day, illiquidity impact,
volume-price correlation."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _dir(ctx, long, short):
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _typ_range(ctx):
    return ctx.cached("typ_rng_sm", lambda: ctx.same_minute(ctx.h - ctx.l, "median"))


def _ac_switch(ctx, p):
    n, thr = ctx.bars(p["win_min"]), p["thr"]
    r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    r1 = ctx.prev(r, 1)
    num = ctx.roll(r * r1, n, "mean")
    den = ctx.roll(r * r, n, "mean")
    with np.errstate(all="ignore"):
        ac = num / den
        sd = np.sqrt(den)
        big = np.abs(r) >= sd
        mr = ac < -thr
        mo = ac > thr
        long = big & (((r < 0) & mr) | ((r > 0) & mo))
        short = big & (((r > 0) & mr) | ((r < 0) & mo))
    return _dir(ctx, long, short)


def _low_overlap(ctx, p):
    thr = p["thr"]
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    rng = ctx.h - ctx.l
    with np.errstate(all="ignore"):
        ov = np.where(rng > 0, np.maximum(0.0, np.minimum(ctx.h, h1) - np.maximum(ctx.l, l1)) / rng, np.nan)
        m = ctx.roll(ov, 3, "mean")
        net = ctx.c - ctx.prev(ctx.c, 3)
        long = (m < thr) & (net > 0) & (ctx.c > ctx.o)
        short = (m < thr) & (net < 0) & (ctx.c < ctx.o)
    return _dir(ctx, long, short)


def _vol_onset(ctx, p):
    w, k = ctx.bars(p["win_min"]), p["k"]
    rr = ctx.roll(ctx.h, w, "max") - ctx.roll(ctx.l, w, "min")
    typ = ctx.cached(("rr_typ", w), lambda: ctx.same_minute(rr, "median"))
    with np.errstate(all="ignore"):
        on = rr >= k * typ
        net = ctx.c - ctx.prev(ctx.c, w)
        long = on & (net > 0)
        short = on & (net < 0)
    return _dir(ctx, long, short)


def _spring(ctx, p):
    k = p["k"]
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    mid1 = (h1 + l1) / 2
    big = (ctx.h - ctx.l) >= k * _typ_range(ctx)
    with np.errstate(all="ignore"):
        long = big & (ctx.l < l1) & (ctx.c > mid1) & (ctx.c > ctx.o)
        short = big & (ctx.h > h1) & (ctx.c < mid1) & (ctx.c < ctx.o)
    return _dir(ctx, long, short)


def _yday_range_done(ctx, p):
    frac = p["frac"]
    prng = ctx.prev_session_value("high") - ctx.prev_session_value("low")
    shi, slo = ctx.session_high(False), ctx.session_low(False)
    with np.errstate(all="ignore"):
        done = (shi - slo) >= frac * prng
        mid = (ctx.h + ctx.l) / 2
        short = done & (ctx.h > shi) & (ctx.c < mid) & (ctx.c < ctx.o)
        long = done & (ctx.l < slo) & (ctx.c > mid) & (ctx.c > ctx.o)
    return _dir(ctx, long, short)


def _leg_retrace(ctx, p):
    m = max(1, ctx.bars(p["n_min"]) // 2)
    frac = p["frac"]
    avg = ctx.cached("avg_rng_ps", lambda: ctx.prev_sessions(ctx.h - ctx.l, "mean"))
    thr = 2.0 * np.sqrt(2 * m) * avg
    hi_r = ctx.roll(ctx.h, m, "max")
    lo_r = ctx.roll(ctx.l, m, "min")
    lo_b = ctx.prev(lo_r, m)
    hi_b = ctx.prev(hi_r, m)
    with np.errstate(all="ignore"):
        up_leg = (hi_r - lo_b) >= thr
        lv_up = hi_r - frac * (hi_r - lo_b)
        long = up_leg & (ctx.l <= lv_up) & (ctx.c > lv_up) & (ctx.c > ctx.o)
        dn_leg = (hi_b - lo_r) >= thr
        lv_dn = lo_r + frac * (hi_b - lo_r)
        short = dn_leg & (ctx.h >= lv_dn) & (ctx.c < lv_dn) & (ctx.c < ctx.o)
    return _dir(ctx, long, short)


def _narrow_cluster(ctx, p):
    cn, vm = int(p["cluster_n"]), p["vmult"]
    rng = ctx.h - ctx.l
    body = np.abs(ctx.c - ctx.o)
    with np.errstate(all="ignore"):
        narrow = ((body <= 0.25 * rng) & (rng > 0)).astype(float)
        cl = ctx.prev(ctx.roll(narrow, cn, "sum"), 1) == cn
        vavg = ctx.prev(ctx.roll(ctx.v, cn, "mean"), 1)
        trig = cl & (body >= 0.6 * rng) & (rng > 0) & (ctx.v >= vm * vavg)
        long = trig & (ctx.c > ctx.o)
        short = trig & (ctx.c < ctx.o)
    return _dir(ctx, long, short)


def _relvol_dip(ctx, p):
    k, n = p["k"], ctx.bars(p["ema_min"])
    cumv = pd.Series(ctx.v).groupby(ctx.day).cumsum().to_numpy()
    typ = ctx.cached("cumv_sm", lambda: ctx.same_minute(cumv, "mean"))
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    with np.errstate(all="ignore"):
        busy = cumv >= k * typ
        long = busy & (ctx.c > ctx.day_open) & (ctx.c > ema)
        short = busy & (ctx.c < ctx.day_open) & (ctx.c < ema)
    return _dir(ctx, long, short)


def _impact_fade(ctx, p):
    k = p["k"]
    rng = ctx.h - ctx.l
    ill = rng / (ctx.v + 1.0)
    typ = ctx.cached("ill_sm", lambda: ctx.same_minute(ill, "median"))
    with np.errstate(all="ignore"):
        thin = (ill >= k * typ) & (rng >= _typ_range(ctx))
        long = thin & (ctx.c < ctx.o)
        short = thin & (ctx.c > ctx.o)
    return _dir(ctx, long, short)


def _vp_corr(ctx, p):
    n, thr = ctx.bars(p["win_min"]), p["thr"]
    x = ctx.c - ctx.o
    y = ctx.v
    with np.errstate(all="ignore"):
        mx, my = ctx.roll(x, n, "mean"), ctx.roll(y, n, "mean")
        cov = ctx.roll(x * y, n, "mean") - mx * my
        sx = np.sqrt(np.maximum(ctx.roll(x * x, n, "mean") - mx * mx, 0))
        sy = np.sqrt(np.maximum(ctx.roll(y * y, n, "mean") - my * my, 0))
        cor = cov / (sx * sy)
        sl = ctx.c - ctx.prev(ctx.c, n)
        long = (cor >= thr) & (sl > 0) & (ctx.c > ctx.o)
        short = (cor <= -thr) & (sl < 0) & (ctx.c < ctx.o)
    return _dir(ctx, long, short)


S = "assistant reasoning"
FAMILIES = [
    Family("E-878", "Autocorrelation regime switch",
           "When recent 1-bar returns are negatively autocorrelated, a large bar is noise from liquidity takers and "
           "reverts; when positively autocorrelated it is a continuing flow. Fade or follow by the measured sign.",
           {"win_min": [60, 90, 120], "thr": [0.15, 0.25, 0.35]}, _ac_switch, markets=("WIN",), source=S, author="agent"),
    Family("E-879", "Low-overlap bar sequence follow",
           "Three bars barely overlapping means one side takes every price level without giving any back; follow it.",
           {"thr": [0.2, 0.35, 0.5]}, _low_overlap, markets=("WIN",), source=S, author="agent"),
    Family("E-880", "Volatility onset direction follow",
           "When the short-window range jumps above its same-minute norm, informed flow has arrived; the net direction "
           "of the window continues for a while.",
           {"win_min": [10, 20], "k": [1.5, 2.0, 2.5]}, _vol_onset, markets=("WIN",), source=S, author="agent"),
    Family("E-881", "Two-bar spring",
           "A sizable bar that sweeps the previous bar's extreme and closes beyond its midpoint traps stop-loss "
           "orders on the wrong side; trade the reversal.",
           {"k": [0.5, 1.0, 1.5]}, _spring, markets=("WIN",), source=S, author="agent"),
    Family("E-882", "Yesterday's range completion fade",
           "Once today's range matches a fraction of yesterday's full range, new extremes that close back against "
           "their bar lose buyers/sellers; fade the poke.",
           {"frac": [0.8, 1.0, 1.2]}, _yday_range_done, markets=("WIN",), source=S, author="agent"),
    Family("E-883", "Leg retracement resume",
           "After a clear leg, a pullback to a fraction of it that turns back is where trend traders re-enter; follow "
           "the resumption.",
           {"n_min": [20, 30, 60], "frac": [0.382, 0.5, 0.618]}, _leg_retrace, markets=("WIN",), source=S, author="agent"),
    Family("E-884", "Narrow-body cluster resolved by volume",
           "A cluster of indecision bars followed by a full-body bar on higher volume shows resting orders have been "
           "consumed; follow the resolving bar.",
           {"cluster_n": [2, 3], "vmult": [1.0, 1.5, 2.0]}, _narrow_cluster, markets=("WIN",), source=S, author="agent"),
    Family("E-885", "Heavy-volume day trend-side EMA follow",
           "On a day with cumulative volume above its norm, the side of the day open carries real participation; "
           "follow closes on that side of a short EMA.",
           {"k": [1.2, 1.5], "ema_min": [10, 20, 30]}, _relvol_dip, markets=("WIN",), source=S, author="agent"),
    Family("E-886", "Thin-book impact fade (Amihud)",
           "A bar with a large range per contract traded moved a thin book, not real demand; liquidity providers "
           "take the other side and price reverts.",
           {"k": [2.0, 3.0, 4.0]}, _impact_fade, markets=("WIN",), source=S, author="agent"),
    Family("E-887", "Volume-price correlation follow",
           "When bar bodies and volume correlate strongly over a window, volume confirms direction (or its opposite "
           "for negative); follow a bar in that direction.",
           {"win_min": [20, 30, 60], "thr": [0.3, 0.5]}, _vp_corr, markets=("WIN",), source=S, author="agent"),
]
