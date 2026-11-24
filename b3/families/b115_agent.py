"""Conveyor batch B-115 (agent, 2026-11-24). Mixed theme: bar-size records, dry pullbacks, clock-hour structure, index/dollar confirmation, volume at levels."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _loc(ctx):
    rng = ctx.h - ctx.l
    return np.where(rng > 0, (ctx.c - ctx.l) / np.where(rng > 0, rng, 1.0), 0.5)


def _largest_bar(ctx, p):
    k = p["k"]
    rng = ctx.h - ctx.l
    med = ctx.cached("rng_med", lambda: ctx.same_minute(rng, "median"))
    pmax = ctx.cached("rng_pmax", lambda: pd.Series(rng).groupby(ctx.day).transform(lambda z: z.cummax().shift(1)).to_numpy())
    big = (rng > pmax) & (rng >= k * med) & (ctx.bar_in_day >= ctx.bars(30))
    loc = _loc(ctx)
    return (big & (loc >= 0.7) & (ctx.c > ctx.o)).astype(int) - (big & (loc <= 0.3) & (ctx.c < ctx.o)).astype(int)


def _dry_pullback(ctx, p):
    k, nb = p["vol_k"], ctx.bars(p["trend_min"])
    vw = ctx.vwap()
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    up_tr = ctx.roll((ctx.c > vw).astype(float), nb, "min", include_current=False) == 1
    dn_tr = ctx.roll((ctx.c < vw).astype(float), nb, "min", include_current=False) == 1
    # the trend window ends before the pullback bar; pullback bar = previous bar
    up_tr, dn_tr = ctx.prev(up_tr.astype(float), 1) == 1, ctx.prev(dn_tr.astype(float), 1) == 1
    o1, c1, v1, m1 = ctx.prev(ctx.o), ctx.prev(ctx.c), ctx.prev(ctx.v), ctx.prev(med)
    long = up_tr & (c1 < o1) & (v1 < k * m1) & (ctx.c > ctx.o) & (ctx.c > ctx.prev(ctx.h))
    short = dn_tr & (c1 > o1) & (v1 < k * m1) & (ctx.c < ctx.o) & (ctx.c < ctx.prev(ctx.l))
    return long.astype(int) - short.astype(int)


def _hour_candle(ctx, p):
    k = p["k"]
    nb = int(round(60 / ctx.tf))
    ret = ctx.c / ctx.prev(ctx.o, nb - 1) - 1.0
    typ = ctx.cached(("hr_abs", nb), lambda: ctx.same_minute(np.nan_to_num(np.abs(ret)), "mean"))
    last = (ctx.minute % 60) == (60 - ctx.tf)
    return (last & (ret >= k * typ) & (typ > 0)).astype(int) - (last & (ret <= -k * typ) & (typ > 0)).astype(int)


def _key_reversal(ctx, p):
    frac, k = p["frac"], p["vol_k"]
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    sl, sh = ctx.session_low(), ctx.session_high()
    loc = _loc(ctx)
    ok = (ctx.v >= k * med) & (ctx.bar_in_day >= ctx.bars(30))
    long = ok & (ctx.l < sl) & (loc >= frac) & (ctx.c > ctx.o)
    short = ok & (ctx.h > sh) & (loc <= 1 - frac) & (ctx.c < ctx.o)
    return long.astype(int) - short.astype(int)


def _acceleration(ctx, p):
    nb, m = ctx.bars(p["n_min"]), p["mult"]
    r1 = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    r2 = ctx.prev(ctx.c, nb) / ctx.prev(ctx.c, 2 * nb) - 1.0
    typ = ctx.cached(("abs_move", nb), lambda: ctx.prev_sessions(np.abs(np.nan_to_num(r1)), "mean"))
    long = (r1 > 0) & (r2 > 0) & (r1 >= m * r2) & (r1 >= typ)
    short = (r1 < 0) & (r2 < 0) & (-r1 >= m * -r2) & (-r1 >= typ)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _open_stretch_fade(ctx, p):
    k = p["k"]
    r = ctx.c / ctx.day_open - 1.0
    typ = ctx.cached("abs_ret_same_minute", lambda: ctx.same_minute(np.abs(r), "mean"))
    pr = ctx.prev(r)
    short = (pr >= k * typ) & (ctx.c < ctx.o) & (ctx.c < ctx.prev(ctx.c)) & (ctx.bar_in_day >= ctx.bars(15))
    long = (pr <= -k * typ) & (ctx.c > ctx.o) & (ctx.c > ctx.prev(ctx.c)) & (ctx.bar_in_day >= ctx.bars(15))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _vwap_cross_volume(ctx, p):
    k = p["vol_k"]
    vw = ctx.vwap()
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    c1, vw1 = ctx.prev(ctx.c), ctx.prev(vw)
    big = ctx.v >= k * med
    long = big & (c1 < vw1) & (ctx.c > vw) & (ctx.c > ctx.o)
    short = big & (c1 > vw1) & (ctx.c < vw) & (ctx.c < ctx.o)
    return long.astype(int) - short.astype(int)


def _prior_hour_break(ctx, p):
    b = p["buffer_frac"]
    key = ctx.day.astype(np.int64) * 24 + (ctx.minute // 60).astype(np.int64)
    hh = pd.Series(ctx.h).groupby(key).max()
    ll = pd.Series(ctx.l).groupby(key).min()
    ph = hh.reindex(key - 1).to_numpy()
    pl = ll.reindex(key - 1).to_numpy()
    up = ctx.cross(ctx.c > ph * (1 + b))
    dn = ctx.cross(ctx.c < pl * (1 - b))
    return up.astype(int) - dn.astype(int)


def _dollar_confirmed_break(ctx, p):
    nb = ctx.bars(p["look_min"])
    oc = ctx.other_close()
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    up = (ctx.c > hi) & (oc < ctx.prev(oc, nb))
    dn = (ctx.c < lo) & (oc > ctx.prev(oc, nb))
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _half_hour_burst(ctx, p):
    k = p["k"]
    rng = ctx.h - ctx.l
    med = ctx.cached("rng_med", lambda: ctx.same_minute(rng, "median"))
    mark = (ctx.minute % 30) == 0
    big = mark & (rng >= k * med) & (med > 0)
    loc = _loc(ctx)
    return (big & (loc >= 0.65) & (ctx.c > ctx.o)).astype(int) - (big & (loc <= 0.35) & (ctx.c < ctx.o)).astype(int)


FAMILIES = [
    Family("E-1148", "Largest bar of the session follow",
           "A bar whose range is the largest of the session so far and well above its usual size, closing near its extreme, "
           "is a burst of urgent orders (news or a large parent order); the follow-through outlasts the next minutes.",
           {"k": [1.5, 2.0, 3.0]}, _largest_bar, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1149", "Dry pullback in a VWAP-side trend",
           "When price has stayed on one side of VWAP, a counter-colour bar on thin volume is profit-taking, not reversal; "
           "the next bar breaking the pullback bar resumes the trend.",
           {"vol_k": [0.5, 0.7, 1.0], "trend_min": [20, 40]}, _dry_pullback, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1150", "Clock-hour candle follow",
           "Funds and index arbitrage desks rebalance on the hour; a clock-hour candle larger than usual for that hour, "
           "at its last bar, signals persistent flow carried into the next hour.",
           {"k": [0.75, 1.0, 1.5]}, _hour_candle, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1151", "Key reversal bar at a new session extreme",
           "A bar that sets a new session low (high) on above-normal volume yet closes in its top (bottom) part means the "
           "stops beyond the extreme were absorbed; the trapped side must cover.",
           {"frac": [0.6, 0.7, 0.8], "vol_k": [1.0, 1.5]}, _key_reversal, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1152", "Return acceleration follow",
           "When the last n minutes' move is a multiple of the preceding n minutes' move in the same direction and larger "
           "than typical, flow is accelerating as followers and stops join; follow.",
           {"n_min": [10, 20, 30], "mult": [2.0, 3.0]}, _acceleration, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1153", "Open-stretch fade on a turning bar",
           "A deviation from the day open beyond what is usual for the time of day tends to be partly retraced by "
           "liquidity providers; the first bar turning back toward the open is the entry.",
           {"k": [1.5, 2.0, 2.5]}, _open_stretch_fade, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1154", "High-volume VWAP crossing",
           "A bar that crosses VWAP on above-normal volume has institutional participation behind the cross, unlike a drift "
           "through VWAP; follow the crossing bar.",
           {"vol_k": [1.5, 2.0, 3.0]}, _vwap_cross_volume, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1155", "Previous clock-hour range break",
           "The prior hour's high and low are levels where stops sit; a close beyond them in the new hour starts a "
           "range expansion in that direction.",
           {"buffer_frac": [0.0, 0.0003, 0.0006]}, _prior_hour_break, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1156", "Index breakout confirmed by a falling dollar",
           "The index breaking its recent range while the dollar falls over the same window is a risk-on move confirmed "
           "across markets (foreign inflow); unconfirmed breaks are the ones that fail.",
           {"look_min": [20, 30, 60]}, _dollar_confirmed_break, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1157", "Half-hour mark range burst",
           "Scheduled data, auctions and algorithmic schedules concentrate at xx:00 and xx:30; a bar there with a far larger "
           "range than usual for that minute, closing at its extreme, carries information; follow.",
           {"k": [1.5, 2.0, 3.0]}, _half_hour_burst, markets=("WIN",), source="assistant reasoning", author="agent"),
]
