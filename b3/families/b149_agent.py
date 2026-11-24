"""Conveyor batch B-149 (agent, 2026-11-24). Mixed: seasonal drift, CUSUM, volume-weighted mean spread, absorption, stalls, harami, CLV."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _seasonal_drift(ctx, p):
    h, k = ctx.bars(p["h_min"]), p["k"]
    n = ctx.n

    def build():
        f = np.full(n, np.nan)
        if n > h:
            f[:-h] = ctx.c[h:] / ctx.c[:-h] - 1.0
            same = ctx.day[h:] == ctx.day[:-h]
            f[:-h] = np.where(same, f[:-h], np.nan)
        return f
    fwd = ctx.cached(("fwd", h), build)
    m = ctx.cached(("fwd_mean", h), lambda: ctx.same_minute(fwd, "mean"))
    a = ctx.cached(("fwd_abs", h), lambda: ctx.same_minute(np.abs(fwd), "mean"))
    strong = np.abs(m) > k * a
    long = strong & (m > 0)
    short = strong & (m < 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _cusum(ctx, p):
    hh = p["h_sigma"]
    r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    sig = ctx.cached("ret_sd", lambda: ctx.prev_sessions(r, "sd"))
    out = np.zeros(ctx.n, dtype=int)
    day = ctx.day.tolist()
    rl, sl = r.tolist(), sig.tolist()
    sp = sm = 0.0
    for i in range(ctx.n):
        if i == 0 or day[i] != day[i - 1]:
            sp = sm = 0.0
        x, s = rl[i], sl[i]
        if x != x or s != s or s <= 0:
            continue
        sp = max(0.0, sp + x - 0.5 * s)
        sm = min(0.0, sm + x + 0.5 * s)
        if sp > hh * s:
            out[i] = 1
            sp = sm = 0.0
        elif sm < -hh * s:
            out[i] = -1
            sp = sm = 0.0
    return out


def _vwma_spread(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    vol = np.maximum(ctx.v, 1.0)
    vwma = ctx.roll(ctx.c * vol, n, "sum") / ctx.roll(vol, n, "sum")
    sma = ctx.roll(ctx.c, n, "mean")
    scale = ctx.roll(ctx.h - ctx.l, n, "mean")
    z = (vwma - sma) / np.where(scale > 0, scale, np.nan)
    return ctx.cross(z > k).astype(int) - ctx.cross(z < -k).astype(int)


def _absorption(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    rng = ctx.h - ctx.l
    eff = np.where(rng > 0, ctx.v / np.where(rng > 0, rng, 1.0), np.nan)
    base = ctx.roll(eff, n, "mean", include_current=False)
    heavy = eff > k * base
    lo = ctx.roll(ctx.l, n, "min", include_current=False)
    hi = ctx.roll(ctx.h, n, "max", include_current=False)
    mid = (ctx.h + ctx.l) / 2.0
    long = heavy & (ctx.l <= lo) & (ctx.c >= mid)
    short = heavy & (ctx.h >= hi) & (ctx.c <= mid)
    return long.astype(int) - short.astype(int)


def _stall_break(ctx, p):
    m, q = int(p["m"]), p["q"]
    mx = ctx.roll(ctx.c, m, "max", include_current=False)
    mn = ctx.roll(ctx.c, m, "min", include_current=False)
    avg = ctx.prev(ctx.roll(ctx.h - ctx.l, 20, "mean"), 1)
    dead = (mx - mn) <= q * avg
    up = dead & (ctx.c > mx)
    dn = dead & (ctx.c < mn)
    return up.astype(int) - dn.astype(int)


def _prior_close_excursion(ctx, p):
    k = p["k"]
    pc = ctx.prev_session_value("close")
    r = ctx.c / pc - 1.0
    typ = ctx.cached("pc_abs", lambda: ctx.same_minute(np.abs(r), "mean"))
    return ctx.cross(r > k * typ).astype(int) - ctx.cross(r < -k * typ).astype(int)


def _harami(ctx, p):
    k = p["k"]
    body = np.abs(ctx.c - ctx.o)
    avgb = ctx.roll(body, 20, "mean")
    po, pc = ctx.prev(ctx.o, 1), ctx.prev(ctx.c, 1)
    pb, pavg = ctx.prev(body, 1), ctx.prev(avgb, 1)
    inside = (np.maximum(ctx.o, ctx.c) <= np.maximum(po, pc)) & (np.minimum(ctx.o, ctx.c) >= np.minimum(po, pc))
    big = (pb >= k * pavg) & (pavg > 0)
    opp = (ctx.c - ctx.o) * (pc - po) < 0
    cond = inside & big & opp
    short = cond & (pc > po)
    long = cond & (pc < po)
    return long.astype(int) - short.astype(int)


def _clv_smooth(ctx, p):
    n, th = ctx.bars(p["win_min"]), p["th"]
    rng = ctx.h - ctx.l
    clv = np.where(rng > 0, (2 * ctx.c - ctx.h - ctx.l) / np.where(rng > 0, rng, 1.0), 0.0)
    m = ctx.roll(clv, n, "mean")
    return ctx.cross(m > th).astype(int) - ctx.cross(m < -th).astype(int)


def _drift_shortfall(ctx, p):
    # price has moved against the typical same-minute drift sign for the day so far, then turns back with it
    n, k = ctx.bars(p["win_min"]), p["k"]
    ret = ctx.c / ctx.prev(ctx.c, n) - 1.0
    typ = ctx.cached(("absn", n), lambda: ctx.prev_sessions(np.abs(ret), "mean"))
    dn_move = ret <= -k * typ
    up_move = ret >= k * typ
    # first close back through the previous bar's extreme after the n-bar move
    long = dn_move & (ctx.c > ctx.prev(ctx.h, 1)) & (ctx.prev(ctx.c, 1) < ctx.prev(ctx.o, 1))
    short = up_move & (ctx.c < ctx.prev(ctx.l, 1)) & (ctx.prev(ctx.c, 1) > ctx.prev(ctx.o, 1))
    return long.astype(int) - short.astype(int)


def _range_rank_follow(ctx, p):
    n, q = ctx.bars(p["win_min"]), p["q"]
    rng = ctx.h - ctx.l
    thr = ctx.roll(rng, n, "mean", include_current=False)
    sd = ctx.roll(rng, n, "std", include_current=False)
    wide = rng > thr + q * sd
    top = ctx.roll(ctx.c, n, "max", include_current=False)
    bot = ctx.roll(ctx.c, n, "min", include_current=False)
    up = wide & (ctx.c > top)
    dn = wide & (ctx.c < bot)
    return up.astype(int) - dn.astype(int)


FAMILIES = [
    Family("E-1488", "Same-minute seasonal drift follow",
           "A given minute of the day tends to carry the same sign of forward drift over the last 20 sessions (scheduled "
           "flows: opening, lunch, US open); when the average forward return is consistent, ride it.",
           {"h_min": [15, 30, 60], "k": [0.3, 0.4, 0.5]}, _seasonal_drift,
           source="assistant reasoning (intraday seasonality)", author="assistant" if False else "agent"),
    Family("E-1489", "CUSUM drift detection follow",
           "A one-sided cumulative sum of returns above a drift allowance detects a persistent order flow earlier than "
           "a fixed lookback; slow positions keep building after the detection.",
           {"h_sigma": [3.0, 4.0, 5.0]}, _cusum, source="assistant reasoning (CUSUM change detection)", author="agent"),
    Family("E-1490", "Volume-weighted vs simple mean spread cross",
           "When the volume-weighted mean price rises above the simple mean, the volume is trading at higher prices "
           "than the time average: buyers are the aggressive side.",
           {"win_min": [20, 30, 60], "k": [0.05, 0.1, 0.2]}, _vwma_spread,
           source="assistant reasoning", author="agent"),
    Family("E-1491", "Absorption bar at a window extreme",
           "Heavy volume per point of range at a new window low (high) with the close in the upper (lower) half means "
           "passive orders absorbed the aggressors; trade the other way.",
           {"win_min": [30, 60], "k": [1.5, 2.0, 3.0]}, _absorption,
           source="assistant reasoning (volume-price absorption)", author="agent"),
    Family("E-1492", "Flat-close stall break",
           "A string of closes inside a very narrow band means both sides wait; the first close beyond the band shows "
           "who gave up and the move carries.",
           {"m": [3, 4, 5], "q": [0.5, 1.0]}, _stall_break, source="assistant reasoning", author="agent"),
    Family("E-1493", "Prior-close excursion break",
           "Distance travelled from yesterday's settlement beyond what is normal for this minute of the day marks "
           "directional repricing of overnight information; follow the first crossing.",
           {"k": [1.0, 1.5, 2.0]}, _prior_close_excursion, source="assistant reasoning", author="agent"),
    Family("E-1494", "Harami reversal after a big bar",
           "A small opposite bar contained inside a large bar's body shows the large bar's push has lost follow-up; "
           "its late participants are trapped.",
           {"k": [1.5, 2.0, 3.0]}, _harami, source="candlestick literature (harami)", author="agent"),
    Family("E-1495", "Smoothed close-location cross",
           "The average position of closes within their own bar ranges shows persistent buying or selling pressure "
           "independent of volume; follow when it becomes one-sided.",
           {"win_min": [10, 20, 40], "th": [0.2, 0.3]}, _clv_smooth, source="assistant reasoning", author="agent"),
    Family("E-1496", "Bounce through the prior bar after a typical-size drop",
           "After a normal-size move in one direction, a bar against it closing through the previous bar's extreme "
           "after a counter-colour bar marks the end of the push; trade the reversal.",
           {"win_min": [10, 20, 30], "k": [1.0, 1.5]}, _drift_shortfall, source="assistant reasoning", author="agent"),
    Family("E-1497", "Wide bar closing beyond the window's closes",
           "A bar whose range is above average plus a number of sd that also closes beyond every close of the window "
           "is a range expansion with direction; follow it.",
           {"win_min": [20, 40, 60], "q": [0.5, 1.0, 1.5]}, _range_rank_follow, source="assistant reasoning", author="agent"),
]
