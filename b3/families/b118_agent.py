"""Conveyor batch B-118 (agent, 2026-11-24). Mixed themes: ribbons, wick pressure, staircase structure, volume surge, t-stat of the day."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _ribbon(ctx, p):
    n = max(2, ctx.bars(p["fast_min"]))
    e1 = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    e2 = ctx.cached(("ema", 2 * n), lambda: ctx.ema(ctx.c, 2 * n))
    e3 = ctx.cached(("ema", 4 * n), lambda: ctx.ema(ctx.c, 4 * n))
    up = (e1 > e2) & (e2 > e3) & (ctx.c > e1)
    dn = (e1 < e2) & (e2 < e3) & (ctx.c < e1)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _wick_pressure(ctx, p):
    nb, thr = ctx.bars(p["win_min"]), p["thr"]
    rng = ctx.h - ctx.l
    safe = np.where(rng > 0, rng, np.nan)
    lw = (np.minimum(ctx.o, ctx.c) - ctx.l) / safe
    uw = (ctx.h - np.maximum(ctx.o, ctx.c)) / safe
    w = np.nan_to_num(lw - uw)
    m = ctx.roll(w, nb, "mean")
    return ctx.cross(m > thr).astype(int) - ctx.cross(m < -thr).astype(int)


def _z_recover(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    mu = ctx.roll(ctx.c, nb, "mean")
    sd = ctx.roll(ctx.c, nb, "std")
    z = np.where(sd > 0, (ctx.c - mu) / np.where(sd > 0, sd, 1.0), np.nan)
    nb2 = ctx.bars(15)
    zmin = ctx.roll(z, nb2, "min", include_current=False)
    zmax = ctx.roll(z, nb2, "max", include_current=False)
    long = (z > 0) & (zmin < -k)
    short = (z < 0) & (zmax > k)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _eod_vwap_fade(ctx, p):
    k, tail = p["k"], p["tail_min"]
    dev = ctx.c - ctx.vwap()
    scale = ctx.roll(ctx.h - ctx.l, ctx.bars(30), "mean")
    late = ctx.minutes_to_close <= tail
    short = late & (dev > k * scale) & (ctx.c < ctx.o)
    long = late & (dev < -k * scale) & (ctx.c > ctx.o)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _staircase(ctx, p):
    m = ctx.bars(p["block_min"])
    lo0 = ctx.roll(ctx.l, m, "min", include_current=False)
    hi0 = ctx.roll(ctx.h, m, "max", include_current=False)
    hi_1 = ctx.prev(hi0, m)
    lo1, lo2 = ctx.prev(lo0, m), ctx.prev(lo0, 2 * m)
    hi2 = ctx.prev(hi0, 2 * m)
    up = (lo2 < lo1) & (lo1 < lo0) & (ctx.c > hi0)
    dn = (hi2 > hi_1) & (hi_1 > hi0) & (ctx.c < lo0)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _rsi_centre(ctx, p):
    low, n = p["low"], int(p["rsi_n"])
    r = ctx.rsi(n)
    nb = ctx.bars(30)
    rmin = ctx.roll(r, nb, "min", include_current=False)
    rmax = ctx.roll(r, nb, "max", include_current=False)
    long = (r > 50) & (rmin < low)
    short = (r < 50) & (rmax > 100 - low)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _marubozu_run(ctx, p):
    f, run = p["body_frac"], int(p["run"])
    body = np.abs(ctx.c - ctx.o)
    rng = ctx.h - ctx.l
    big = (rng > 0) & (body >= f * rng)
    up = ((ctx.c > ctx.o) & big).astype(float)
    dn = ((ctx.c < ctx.o) & big).astype(float)
    a = ctx.roll(up, run, "sum") == run
    b = ctx.roll(dn, run, "sum") == run
    return ctx.cross(a).astype(int) - ctx.cross(b).astype(int)


def _surge_direction(ctx, p):
    m, k = ctx.bars(p["surge_min"]), p["k"]
    vs = ctx.roll(ctx.v, m, "sum")
    base = ctx.prev(ctx.roll(ctx.v, ctx.bars(60), "mean"), m)
    ratio = np.where(base > 0, vs / (m * np.where(base > 0, base, 1.0)), np.nan)
    d = np.sign(ctx.c - ctx.prev(ctx.c, m))
    fire = ctx.cross(ratio > k)
    return (fire & (d > 0)).astype(int) - (fire & (d < 0)).astype(int)


def _midpoint_rise(ctx, p):
    n = int(p["n"])
    mid = (ctx.h + ctx.l) / 2.0
    d = mid - ctx.prev(mid, 1)
    up = (ctx.roll((d > 0).astype(float), n, "sum") == n) & (ctx.c > mid)
    dn = (ctx.roll((d < 0).astype(float), n, "sum") == n) & (ctx.c < mid)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _day_tstat(ctx, p):
    k = p["k"]
    ret = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    sd = ctx.cached("ret_sd", lambda: ctx.prev_sessions(ret, "sd"))
    t = (ctx.c / ctx.day_open - 1.0) / (sd * np.sqrt(ctx.bar_in_day + 1.0))
    ok = ctx.bar_in_day >= ctx.bars(p["min_min"])
    return ctx.cross(ok & (t > k)).astype(int) - ctx.cross(ok & (t < -k)).astype(int)


FAMILIES = [
    Family("E-1178", "EMA ribbon alignment onset",
           "When fast, medium and slow EMAs (n, 2n, 4n) line up with price above them for the first time, trend "
           "followers and slow hedgers keep adding in that direction; follow the onset.",
           {"fast_min": [5, 10, 20]}, _ribbon, source="assistant reasoning", author="agent"),
    Family("E-1179", "Net wick-pressure follow",
           "Persistent lower wicks over a window mean sellers are repeatedly absorbed by passive buyers (and vice "
           "versa); when the average wick imbalance crosses a threshold, trade with the absorbers.",
           {"win_min": [15, 30, 60], "thr": [0.1, 0.2, 0.3]}, _wick_pressure, source="assistant reasoning", author="agent"),
    Family("E-1180", "Z-score recovery through the mean",
           "After a stretch below (above) the rolling mean, the first close back through the mean shows the forced "
           "flow has ended; follow the return leg.",
           {"win_min": [60, 120], "k": [1.5, 2.0]}, _z_recover, source="assistant reasoning", author="agent"),
    Family("E-1181", "Closing-hour VWAP stretch fade",
           "Near the close, benchmark-driven (VWAP) execution and position squaring pull price toward VWAP; fade a "
           "stretched price when a bar turns back toward it.",
           {"k": [2.0, 3.0, 4.0], "tail_min": [60, 120, 180]}, _eod_vwap_fade, source="assistant reasoning", author="agent"),
    Family("E-1182", "Block staircase break",
           "Block lows rising three blocks in a row show steady passive demand; a close over the latest block high "
           "means supply is exhausted. Mirror for sellers.",
           {"block_min": [5, 10, 15]}, _staircase, source="assistant reasoning (Dow-style higher lows)", author="agent"),
    Family("E-1183", "RSI centre-line recovery",
           "After RSI visits a weak zone and then crosses 50, momentum has flipped and the late shorts cover; "
           "follow the flip.",
           {"low": [30, 35, 40], "rsi_n": [9, 14]}, _rsi_centre, source="assistant reasoning", author="agent"),
    Family("E-1184", "Marubozu run follow",
           "Consecutive bars with bodies filling most of their range mean one side is hitting through the book with "
           "no pushback; follow.",
           {"body_frac": [0.6, 0.7, 0.8], "run": [2, 3]}, _marubozu_run, source="assistant reasoning", author="agent"),
    Family("E-1185", "Short-window volume surge direction",
           "A sudden surge of volume over a few minutes versus the last hour signals informed or forced flow; the "
           "net price direction of the surge is the side that is winning.",
           {"surge_min": [3, 5, 10], "k": [2.0, 3.0, 4.0]}, _surge_direction, source="assistant reasoning", author="agent"),
    Family("E-1186", "Rising bar-midpoint run",
           "Bar midpoints (high+low)/2 rising several bars in a row with the close above the midpoint show whole "
           "ranges migrating up, stronger than close-to-close runs; follow.",
           {"n": [3, 4, 5]}, _midpoint_rise, source="assistant reasoning", author="agent"),
    Family("E-1187", "Day-move t-statistic follow",
           "Normalising the move since the open by the typical bar volatility and sqrt(time) isolates drifts too "
           "persistent to be noise; follow when the t-statistic crosses a threshold.",
           {"k": [1.5, 2.0, 2.5], "min_min": [15, 30, 60]}, _day_tstat, source="assistant reasoning", author="agent"),
]
