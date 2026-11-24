"""Conveyor batch B-146 (agent, 2026-11-24). Mixed themes: trend quality, swing structure, jump fade, stale extremes, volume pace."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _ffill_day(ctx, x):
    return pd.Series(np.asarray(x, float)).groupby(ctx.day).ffill().to_numpy()


def _er_ignition(ctx, p):
    nb, thr = ctx.bars(p["n_min"]), p["thr"]
    with np.errstate(all="ignore"):
        net = ctx.c - ctx.prev(ctx.c, nb)
        sabs = ctx.roll(np.abs(ctx.c - ctx.prev(ctx.c, 1)), nb, "sum")
        er = np.abs(net) / np.where(sabs > 0, sabs, np.nan)
        long = ctx.cross((er >= thr) & (net > 0))
        short = ctx.cross((er >= thr) & (net < 0))
    return long.astype(int) - short.astype(int)


def _swing_break(ctx, p):
    k, max_age = int(p["strength"]), p["max_age_min"]
    with np.errstate(all="ignore"):
        ch, cl = ctx.prev(ctx.h, k), ctx.prev(ctx.l, k)
        ph = np.ones(ctx.n, bool)
        pl = np.ones(ctx.n, bool)
        for m in range(0, 2 * k + 1):
            if m == k:
                continue
            ph &= ch > ctx.prev(ctx.h, m) if m else ch > ctx.h
            pl &= cl < ctx.prev(ctx.l, m) if m else cl < ctx.l
        last_ph = _ffill_day(ctx, np.where(ph, ch, np.nan))
        last_pl = _ffill_day(ctx, np.where(pl, cl, np.nan))
        age_h = (ctx.bar_in_day - _ffill_day(ctx, np.where(ph, ctx.bar_in_day, np.nan))) * ctx.tf
        age_l = (ctx.bar_in_day - _ffill_day(ctx, np.where(pl, ctx.bar_in_day, np.nan))) * ctx.tf
        long = ctx.cross((ctx.c > last_ph) & (age_h <= max_age))
        short = ctx.cross((ctx.c < last_pl) & (age_l <= max_age))
    return long.astype(int) - short.astype(int)


def _jump_fade(ctx, p):
    nb, share = ctx.bars(p["n_min"]), p["share"]
    with np.errstate(all="ignore"):
        ret = ctx.c - ctx.o
        a = np.abs(ret)
        rs = ctx.roll(a, nb, "sum")
        rm = ctx.roll(a, nb, "max")
        jump = (a >= rm) & (a >= share * rs) & (a > 0)
        long = ctx.cross(jump & (ret < 0))
        short = ctx.cross(jump & (ret > 0))
    return long.astype(int) - short.astype(int)


def _signed_volume_divergence(ctx, p):
    nb = ctx.bars(p["n_min"])
    with np.errstate(all="ignore"):
        hi = ctx.roll(ctx.h, nb, "max", include_current=False)
        lo = ctx.roll(ctx.l, nb, "min", include_current=False)
        sv = ctx.roll(np.sign(ctx.c - ctx.o) * ctx.v, nb, "sum")
        short = ctx.cross((ctx.h > hi) & (sv < 0))
        long = ctx.cross((ctx.l < lo) & (sv > 0))
    return long.astype(int) - short.astype(int)


def _stale_extreme_break(ctx, p):
    nb = ctx.bars(p["stale_min"])
    with np.errstate(all="ignore"):
        sh, sl = ctx.session_high(False), ctx.session_low(False)
        first = ctx.bar_in_day == 0
        nh = (ctx.h > sh) | first
        nl = (ctx.l < sl) | first
        age_h = ctx.bar_in_day - ctx.prev(_ffill_day(ctx, np.where(nh, ctx.bar_in_day, np.nan)), 1)
        age_l = ctx.bar_in_day - ctx.prev(_ffill_day(ctx, np.where(nl, ctx.bar_in_day, np.nan)), 1)
        long = ctx.cross((ctx.c > sh) & (age_h >= nb))
        short = ctx.cross((ctx.c < sl) & (age_l >= nb))
    return long.astype(int) - short.astype(int)


def _bigbar_mid_hold(ctx, p):
    k, n = p["k"], int(p["avg_n"])
    with np.errstate(all="ignore"):
        rng = ctx.h - ctx.l
        avg = ctx.roll(rng, n, "mean", include_current=False)
        h1, l1, o1, c1 = (ctx.prev(x, 1) for x in (ctx.h, ctx.l, ctx.o, ctx.c))
        big = ctx.prev(rng, 1) >= k * ctx.prev(avg, 1)
        mid = (h1 + l1) / 2.0
        long = big & (c1 > o1) & (ctx.l <= mid) & (ctx.c > mid) & (ctx.c > ctx.o)
        short = big & (c1 < o1) & (ctx.h >= mid) & (ctx.c < mid) & (ctx.c < ctx.o)
    return long.astype(int) - short.astype(int)


def _prev_vwap_cross(ctx, p):
    b = p["buffer_frac"]
    vw = ctx.vwap()
    per = pd.Series(vw).groupby(ctx.day).last()
    per = per.reindex(range(int(ctx.day.max()) + 1)).shift(1)
    pv = per.to_numpy()[ctx.day]
    with np.errstate(all="ignore"):
        long = ctx.cross(ctx.c > pv * (1 + b))
        short = ctx.cross(ctx.c < pv * (1 - b))
    return long.astype(int) - short.astype(int)


def _marubozu_break(ctx, p):
    nb, w = ctx.bars(p["n_min"]), p["wick_frac"]
    with np.errstate(all="ignore"):
        hi = ctx.roll(ctx.h, nb, "max", include_current=False)
        lo = ctx.roll(ctx.l, nb, "min", include_current=False)
        rng = ctx.h - ctx.l
        long = (ctx.c > hi) & (ctx.c > ctx.o) & ((ctx.h - ctx.c) <= w * rng)
        short = (ctx.c < lo) & (ctx.c < ctx.o) & ((ctx.c - ctx.l) <= w * rng)
        out = ctx.cross(long).astype(int) - ctx.cross(short).astype(int)
    return out


def _second_entry(ctx, p):
    n, lb = int(p["ema_bars"]), int(p["lookback"])
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    with np.errstate(all="ignore"):
        ll = (ctx.l < ctx.prev(ctx.l, 1)).astype(float)
        hh = (ctx.h > ctx.prev(ctx.h, 1)).astype(float)
        cl = ctx.roll(ll, lb, "sum")
        ch = ctx.roll(hh, lb, "sum")
        long = (ctx.c > ema) & (cl >= 2) & (ctx.c > ctx.prev(ctx.h, 1)) & (ctx.c > ctx.o)
        short = (ctx.c < ema) & (ch >= 2) & (ctx.c < ctx.prev(ctx.l, 1)) & (ctx.c < ctx.o)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _pace_vwap_cross(ctx, p):
    k = p["pace_k"]
    cv = pd.Series(ctx.v).groupby(ctx.day).cumsum().to_numpy()
    typ = ctx.cached("cumvol_same_minute", lambda: ctx.same_minute(cv, "mean"))
    vw = ctx.vwap()
    with np.errstate(all="ignore"):
        heavy = cv >= k * typ
        long = ctx.cross(heavy & (ctx.c > vw))
        short = ctx.cross(heavy & (ctx.c < vw))
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-1458", "Efficiency-ratio trend ignition",
           "When price covers a window almost in a straight line (net move close to the sum of bar moves) a "
           "directional parent order is being worked without pushback; follow the first bar the ratio gets high.",
           {"n_min": [15, 30, 45], "thr": [0.5, 0.6, 0.7]}, _er_ignition, markets=("WIN",),
           source="assistant reasoning (Kaufman efficiency ratio)", author="agent"),
    Family("E-1459", "Confirmed swing-point break",
           "A close through the latest confirmed fractal swing high/low (fresh enough) takes out the stops sitting "
           "behind the swing; follow it.",
           {"strength": [2, 3, 4], "max_age_min": [30, 60, 90]}, _swing_break, markets=("WIN",),
           source="assistant reasoning (market structure break)", author="agent"),
    Family("E-1460", "Single-bar jump dominance fade",
           "When one bar is the largest in the window and makes up a big share of all movement, it is a liquidity "
           "gap/stop burst rather than a trend; the next side to trade is the liquidity provider, so fade it.",
           {"n_min": [10, 20, 30], "share": [0.4, 0.5, 0.6]}, _jump_fade, markets=("WIN",),
           source="assistant reasoning (jump vs diffusion)", author="agent"),
    Family("E-1461", "New extreme on opposing signed volume",
           "A new window high made while the colour-signed volume of the window is net selling (low: net buying) "
           "shows the extreme was reached by passive fills, not initiative; fade it.",
           {"n_min": [20, 30, 60]}, _signed_volume_divergence, markets=("WIN",),
           source="assistant reasoning (volume-price divergence)", author="agent"),
    Family("E-1462", "Stale session-extreme break",
           "A session high/low untouched for a long time accumulates resting stops and breakout orders; a close "
           "through it after the stale period releases them in that direction.",
           {"stale_min": [30, 60, 90]}, _stale_extreme_break, markets=("WIN",),
           source="assistant reasoning (resting stops at old extremes)", author="agent"),
    Family("E-1463", "Big-bar midpoint hold",
           "After an unusually large bar, a pullback into its midpoint that closes back beyond it in the bar's "
           "direction shows the aggressors keep control of the half-way level; follow.",
           {"k": [1.5, 2.0, 3.0], "avg_n": [10, 20, 40]}, _bigbar_mid_hold, markets=("WIN",),
           source="assistant reasoning (50% retrace of impulse bar)", author="agent"),
    Family("E-1464", "Prior-session VWAP line cross",
           "Yesterday's VWAP is the average price of the previous session's participants; the first close beyond "
           "it shifts who is in profit across sessions; follow the cross.",
           {"buffer_frac": [0.0, 0.0005, 0.001]}, _prev_vwap_cross,
           source="assistant reasoning (multi-session value anchor)", author="agent"),
    Family("E-1465", "Marubozu window breakout",
           "A bar that closes at its extreme and takes the window's high/low leaves no counter-trading inside the "
           "bar: aggressors paid every price; follow it.",
           {"n_min": [20, 30, 60], "wick_frac": [0.05, 0.15]}, _marubozu_break, markets=("WIN",),
           source="assistant reasoning (full-body breakout)", author="agent"),
    Family("E-1466", "Second-entry pullback in an EMA trend",
           "In a trend (price on one side of the EMA) a pullback with at least two counter-trend bar extremes, "
           "ended by a bar closing through the prior bar, is the second attempt that shakes out weak hands; "
           "trade with the trend.",
           {"ema_bars": [20, 40], "lookback": [6, 10]}, _second_entry, markets=("WIN",),
           source="assistant reasoning (price-action second entry)", author="agent"),
    Family("E-1467", "Heavy-day VWAP side change",
           "When the session's cumulative volume runs well above its usual pace, VWAP is a heavily defended "
           "benchmark; a close across it flips the benchmarked algos' side; follow the cross.",
           {"pace_k": [1.2, 1.5, 2.0]}, _pace_vwap_cross,
           source="assistant reasoning (volume pace and VWAP benchmark)", author="agent"),
]
