"""Conveyor batch B-116 (agent, 2026-11-24). Mixed themes: prior-hour levels, pivots, wick/NR bars, volume delta, range budget, gaps."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _prior_hour_break(ctx, p):
    buf = p["buf"]
    hr = (ctx.minute // 60).astype(int)
    d = pd.DataFrame({"d": ctx.day, "hr": hr, "h": ctx.h, "l": ctx.l})
    agg = d.groupby(["d", "hr"]).agg(h=("h", "max"), l=("l", "min"))
    sh = agg.groupby(level=0).shift(1)
    idx = pd.MultiIndex.from_arrays([ctx.day, hr])
    ph = sh["h"].reindex(idx).to_numpy()
    pl = sh["l"].reindex(idx).to_numpy()
    up = ctx.cross(ctx.c > ph * (1 + buf))
    dn = ctx.cross(ctx.c < pl * (1 - buf))
    return up.astype(int) - dn.astype(int)


def _pivot_reclaim(ctx, p):
    nb = ctx.bars(p["hold_min"])
    pv = (ctx.prev_session_value("high") + ctx.prev_session_value("low") + ctx.prev_session_value("close")) / 3.0
    below = (ctx.c < pv).astype(float)
    above = (ctx.c > pv).astype(float)
    wb = ctx.roll(below, nb, "min", include_current=False) == 1
    wa = ctx.roll(above, nb, "min", include_current=False) == 1
    return (wb & (ctx.c > pv)).astype(int) - (wa & (ctx.c < pv)).astype(int)


def _pin_bar(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    rng = ctx.h - ctx.l
    typ = ctx.cached("rng_med", lambda: ctx.same_minute(rng, "median"))
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lower = np.minimum(ctx.o, ctx.c) - ctx.l
    upper = ctx.h - np.maximum(ctx.o, ctx.c)
    big = rng >= p["k"] * typ
    long = big & (ctx.l <= lo) & (lower >= 0.6 * rng) & (rng > 0)
    short = big & (ctx.h >= hi) & (upper >= 0.6 * rng) & (rng > 0)
    return long.astype(int) - short.astype(int)


def _narrow_range_break(ctx, p):
    n = int(p["n_bars"])
    rng = ctx.h - ctx.l
    mn = ctx.roll(rng, n, "min", include_current=False)
    r1 = ctx.prev(rng, 1)
    nr = r1 <= mn
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    return (nr & (ctx.c > h1)).astype(int) - (nr & (ctx.c < l1)).astype(int)


def _delta_divergence(ctx, p):
    nb = ctx.bars(p["win_min"])
    f = p["frac"]
    sv = np.sign(ctx.c - ctx.o) * ctx.v
    s = ctx.roll(sv, nb, "sum")
    tot = ctx.roll(ctx.v, nb, "sum")
    ratio = np.where(tot > 0, s / np.where(tot > 0, tot, 1), 0.0)
    hi = ctx.roll(ctx.h, nb, "max")
    lo = ctx.roll(ctx.l, nb, "min")
    short = (ctx.h >= hi) & (ratio < -f)
    long = (ctx.l <= lo) & (ratio > f)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _yesterday_path_cross(ctx, p):
    th = p["th"]
    r = ctx.c / ctx.day_open - 1.0
    ry = ctx.cached("ry1", lambda: ctx.same_minute(r, "median", n=1))
    diff = r - ry
    return ctx.cross(diff > th).astype(int) - ctx.cross(diff < -th).astype(int)


def _range_budget_fade(ctx, p):
    f = p["frac"]
    d = pd.DataFrame({"d": ctx.day, "h": ctx.h, "l": ctx.l})
    g = d.groupby("d")
    dr = (g["h"].max() - g["l"].min())
    avg = dr.rolling(5, min_periods=5).mean().shift(1)
    avg_bar = avg.reindex(range(int(ctx.day.max()) + 1)).to_numpy()[ctx.day]
    sh = ctx.session_high(include_current=True)
    sl = ctx.session_low(include_current=True)
    used = (sh - sl) >= f * avg_bar
    short = used & (ctx.h >= sh) & (ctx.c < ctx.o)
    long = used & (ctx.l <= sl) & (ctx.c > ctx.o)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _clv_thrust(ctx, p):
    k = p["k"]
    rng = ctx.h - ctx.l
    typ = ctx.cached("rng_med", lambda: ctx.same_minute(rng, "median"))
    vmed = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    clv = np.where(rng > 0, (2 * ctx.c - ctx.h - ctx.l) / np.where(rng > 0, rng, 1), 0.0)
    ok = (rng >= k * typ) & (ctx.v >= vmed)
    return ctx.cross(ok & (clv >= 0.9)).astype(int) - ctx.cross(ok & (clv <= -0.9)).astype(int)


def _gap_dayopen_bounce(ctx, p):
    g = p["gap"]
    nb = ctx.bars(p["wait_min"])
    gap = ctx.day_open / ctx.prev_session_value("close") - 1.0
    late = ctx.bar_in_day >= nb
    long = late & (gap >= g) & (ctx.l <= ctx.day_open) & (ctx.c > ctx.day_open)
    short = late & (gap <= -g) & (ctx.h >= ctx.day_open) & (ctx.c < ctx.day_open)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _volume_ramp(ctx, p):
    k = p["k"]
    v1, v2 = ctx.prev(ctx.v, 1), ctx.prev(ctx.v, 2)
    ramp = (ctx.v > k * v1) & (v1 > k * v2)
    bar = np.sign(ctx.c - ctx.o)
    return ctx.cross(ramp & (bar > 0)).astype(int) - ctx.cross(ramp & (bar < 0)).astype(int)


FAMILIES = [
    Family("E-1158", "Prior clock-hour high/low break",
           "Stops and breakout orders cluster beyond the previous clock hour's extremes; a first close beyond them "
           "releases that flow in the break direction.",
           {"buf": [0.0, 0.0003, 0.0006]}, _prior_hour_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1159", "Floor-pivot reclaim after a hold",
           "The classic pivot (H+L+C)/3 of yesterday is watched by many; after bars spent on one side, a close "
           "across it shifts control and should follow.",
           {"hold_min": [10, 20, 40]}, _pivot_reclaim, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1160", "Pin bar at a window extreme",
           "A large bar that probes a fresh window low (high) and closes with a long wick shows aggressive "
           "sellers (buyers) absorbed; fade into the wick.",
           {"lookback_min": [30, 60, 120], "k": [0.8, 1.2]}, _pin_bar, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1161", "Narrowest-bar break",
           "The narrowest bar of the last n bars marks a pause in participation; a close beyond its range "
           "restarts directional flow.",
           {"n_bars": [4, 7, 10]}, _narrow_range_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1162", "Signed-volume divergence fade",
           "A fresh window high reached while signed volume is net selling means buying is thin and sellers are "
           "absorbing; fade the extreme (and mirror).",
           {"win_min": [15, 30, 60], "frac": [0.05, 0.1, 0.2]}, _delta_divergence, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1163", "Yesterday's path outperformance follow",
           "When today's return since the open runs ahead of yesterday's return at the same minute by a margin, "
           "late participants chase the stronger session; follow the deviation.",
           {"th": [0.002, 0.003, 0.005]}, _yesterday_path_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1164", "Daily range budget exhaustion fade",
           "Once the session range reaches a share of the 5-session average daily range, new extremes meet "
           "profit-taking; fade a reversal-colored bar at the extreme.",
           {"frac": [0.8, 1.0, 1.2]}, _range_budget_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1165", "Close-location thrust follow",
           "A bar with above-typical range and volume closing at its very high (low) shows one side in full "
           "control through the close; follow it.",
           {"k": [1.0, 1.5, 2.0]}, _clv_thrust, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1166", "Gap-side day-open bounce",
           "On a gap day, the day's opening price is the level where gap holders defend; a dip to it that closes "
           "back on the gap side is a continuation entry.",
           {"gap": [0.0, 0.0005, 0.001], "wait_min": [15, 30, 60]}, _gap_dayopen_bounce, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1167", "Two-step volume ramp follow",
           "Volume rising bar after bar in one direction signals a crowd entering; the bar's color shows who is "
           "pressing, so follow it.",
           {"k": [1.2, 1.5, 2.0]}, _volume_ramp, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
