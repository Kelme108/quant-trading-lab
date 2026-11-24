"""Conveyor batch B-101 (agent, 2026-11-24). Mixed themes: seasonality, clock anchors, regime (variance ratio),
bands, balance, bar-count asymmetry, lunch range, acceleration, RSI re-entry and climax bars."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _sgn(ctx, long, short):
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _fwd_drift(ctx, p):
    m = ctx.bars(p["horizon_min"])
    th = p["th"]
    lc = pd.Series(ctx.c)
    fut = lc.groupby(ctx.day).shift(-m).to_numpy()
    fwd = fut / ctx.c - 1.0
    key = ("fwd", m)
    mean = ctx.cached(("fm", key), lambda: ctx.same_minute(fwd, "mean"))
    ab = ctx.cached(("fa", key), lambda: ctx.same_minute(np.abs(fwd), "mean"))
    z = mean / np.where(ab > 0, ab, np.nan)
    return _sgn(ctx, z > th, z < -th)


def _anchor_impulse(ctx, p):
    a, m, k = int(p["anchor"]), p["move_min"], p["k"]
    nb = ctx.bars(m)
    s = pd.Series(np.where(ctx.minute == a, ctx.o, np.nan))
    oa = s.groupby(ctx.day).transform("first").to_numpy()
    ret = ctx.c / oa - 1.0
    mv = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    typ = ctx.cached(("absmv", nb), lambda: ctx.prev_sessions(np.abs(mv), "mean"))
    win = (ctx.minute >= a + m - ctx.tf) & (ctx.minute < a + m + 90)
    return _sgn(ctx, win & (ret > k * typ), win & (ret < -k * typ))


def _variance_ratio(ctx, p):
    nw, th, q = ctx.bars(p["win_min"]), p["th"], 4
    lc = np.log(ctx.c)
    r1 = lc - ctx.prev(lc, 1)
    rq = lc - ctx.prev(lc, q)
    v1 = ctx.roll(r1 ** 2, nw, "mean")
    vq = ctx.roll(rq ** 2, nw, "mean")
    vr = vq / (q * np.where(v1 > 0, v1, np.nan))
    cond = vr > th
    return _sgn(ctx, cond & (rq > 0), cond & (rq < 0))


def _boll_reentry(ctx, p):
    n, k = ctx.bars(p["period_min"]), p["k"]
    mean = ctx.roll(ctx.c, n, "mean")
    sd = ctx.roll(ctx.c, n, "std")
    up, dn = mean + k * sd, mean - k * sd
    was_out_up = ctx.prev(ctx.c, 1) > ctx.prev(up, 1)
    was_out_dn = ctx.prev(ctx.c, 1) < ctx.prev(dn, 1)
    short = was_out_up & (ctx.c <= up)
    long = was_out_dn & (ctx.c >= dn)
    return long.astype(int) - short.astype(int)


def _mid_cross(ctx, p):
    nb, r = ctx.bars(p["side_min"]), p["min_range"]
    sh, sl = ctx.session_high(True), ctx.session_low(True)
    mid = (sh + sl) / 2.0
    wide = (sh - sl) / ctx.day_open > r
    below = (ctx.c < mid).astype(float)
    above = (ctx.c > mid).astype(float)
    wb = ctx.roll(below, nb, "min", include_current=False) == 1
    wa = ctx.roll(above, nb, "min", include_current=False) == 1
    return (wb & wide & (ctx.c > mid)).astype(int) - (wa & wide & (ctx.c < mid)).astype(int)


def _upshare_fade(ctx, p):
    nb, q, k = ctx.bars(p["win_min"]), p["q"], p["k"]
    up = (ctx.c > ctx.o).astype(float)
    share = ctx.roll(up, nb, "mean")
    net = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    typ = ctx.cached(("absnet", nb), lambda: ctx.prev_sessions(np.abs(net), "mean"))
    short = (share >= q) & (net < k * typ)
    long = (share <= 1 - q) & (net > -k * typ)
    return _sgn(ctx, long, short)


def _lunch_break(ctx, p):
    L, until = int(p["lunch_len"]), int(p["until"])
    inw = (ctx.minute >= 840 - L) & (ctx.minute < 840)
    g = pd.DataFrame({"d": ctx.day, "h": np.where(inw, ctx.h, np.nan), "l": np.where(inw, ctx.l, np.nan)})
    hi = g.groupby("d")["h"].transform("max").to_numpy()
    lo = g.groupby("d")["l"].transform("min").to_numpy()
    win = (ctx.minute >= 840) & (ctx.minute < until)
    return _sgn(ctx, win & (ctx.c > hi), win & (ctx.c < lo))


def _accel(ctx, p):
    nb, k = ctx.bars(p["move_min"]), p["k"]
    r1 = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    r0 = ctx.prev(ctx.c, nb) / ctx.prev(ctx.c, 2 * nb) - 1.0
    typ = ctx.cached(("absr1", nb), lambda: ctx.prev_sessions(np.abs(r1), "mean"))
    long = (r0 > 0) & (r1 > 1.5 * r0) & (r1 > k * typ)
    short = (r0 < 0) & (r1 < 1.5 * r0) & (r1 < -k * typ)
    return _sgn(ctx, long, short)


def _rsi_reentry(ctx, p):
    n, th = int(p["n"]), p["th"]
    r = ctx.rsi(n)
    pr = ctx.prev(r, 1)
    short = (pr > th) & (r <= th)
    long = (pr < 100 - th) & (r >= 100 - th)
    return long.astype(int) - short.astype(int)


def _climax_fade(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    ar = np.abs(ctx.c / ctx.o - 1.0)
    mx = ctx.roll(ar, nb, "max")
    typ = ctx.cached("typ_ar", lambda: ctx.prev_sessions(ar, "mean"))
    big = (ar >= mx - 1e-12) & (ar > k * typ) & (ar > 0)
    return _sgn(ctx, big & (ctx.c < ctx.o), big & (ctx.c > ctx.o))


W = ("WIN",)

FAMILIES = [
    Family("E-1008", "Same-minute forward-drift seasonality",
           "Order flow tied to the clock (index rebalancing, ETF/institutional schedules) repeats at the same time of "
           "day; when the 20-session average forward move from this minute is consistently one-signed, trade it.",
           {"horizon_min": [15, 30, 45], "th": [0.3, 0.4, 0.5]}, _fwd_drift, markets=W,
           source="assistant reasoning (time-of-day return seasonality)", author="agent"),
    Family("E-1009", "US-open anchor impulse follow",
           "The US cash open (10:30 or 11:30 Brasilia time depending on DST) brings foreign flow; a move away from the "
           "price at that anchor larger than usual shows that flow is directional, so follow it.",
           {"anchor": [630, 690], "move_min": [15, 30], "k": [0.25, 0.5, 1.0]}, _anchor_impulse, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1010", "Variance-ratio trending regime follow",
           "When 4-bar return variance exceeds 4x the 1-bar variance, returns are positively autocorrelated "
           "(trend regime, herding stops and momentum orders); follow the direction of the latest 4-bar move.",
           {"win_min": [60, 90, 120], "th": [1.5, 2.0, 2.5]}, _variance_ratio, markets=W,
           source="assistant reasoning (Lo-MacKinlay variance ratio)", author="agent"),
    Family("E-1011", "Bollinger band re-entry fade",
           "A close outside the Bollinger band that returns inside on the next bar is a failed extension; "
           "the late breakers are trapped and price tends to go back toward the mean.",
           {"period_min": [20, 40, 60], "k": [2.0, 2.5]}, _boll_reentry, markets=W,
           source="assistant reasoning (Bollinger band re-entry)", author="agent"),
    Family("E-1012", "Session-range midpoint cross follow",
           "After price spent a long time on one side of the day's range midpoint, a close through it moves the "
           "fair-value reference of the session; the side that lost it must cover or liquidate, so follow.",
           {"side_min": [20, 40, 60], "min_range": [0.003, 0.006]}, _mid_cross, markets=W,
           source="assistant reasoning (auction midpoint)", author="agent"),
    Family("E-1013", "Persistent up-bars without progress fade",
           "When most bars of the window close up yet the net move is small, passive sellers are absorbing the "
           "buying with limit orders; the stalled side gives up, so fade it (mirror for down bars).",
           {"win_min": [20, 30, 45], "q": [0.65, 0.75], "k": [0.5, 1.0]}, _upshare_fade, markets=W,
           source="assistant reasoning (absorption)", author="agent"),
    Family("E-1014", "Lunch-range break follow",
           "From about 12:00 to 14:00 B3 liquidity is thin and the range compresses; the first close beyond the "
           "lunch high/low after 14:00 (US data, afternoon desks back) releases stops and starts the afternoon trend.",
           {"lunch_len": [60, 90, 120], "until": [900, 960]}, _lunch_break, markets=W,
           source="assistant reasoning (intraday liquidity seasonality)", author="agent"),
    Family("E-1015", "Momentum acceleration follow",
           "A move whose latest leg is much faster than the previous leg of the same length shows new aggressive "
           "participants joining; momentum followers and stops add to it, so follow the acceleration.",
           {"move_min": [10, 20, 30], "k": [0.5, 1.0, 1.5]}, _accel, markets=W,
           source="assistant reasoning (second-derivative momentum)", author="agent"),
    Family("E-1016", "RSI extreme re-entry fade",
           "An RSI that was beyond 70/80 and falls back below the threshold shows the push is losing its buyers; "
           "the first re-entry marks the turn, so trade against the prior extreme (mirror at 30/20).",
           {"n": [7, 14], "th": [70, 80]}, _rsi_reentry, markets=W,
           source="assistant reasoning (Wilder RSI failure swing)", author="agent"),
    Family("E-1017", "Largest-bar climax fade",
           "When the current bar is the largest-bodied bar of the last hour(s) and far above normal size, it is "
           "typically forced flow (stops, market orders) at the end of a move; liquidity providers lean against it.",
           {"win_min": [30, 60, 90], "k": [2.0, 3.0]}, _climax_fade, markets=W,
           source="assistant reasoning (climax bar)", author="agent"),
]
