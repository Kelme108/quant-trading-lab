"""Conveyor batch B-073 (agent, 2026-11-23). Mixed themes: dwell/structure filters, cross-market sides, volume pace, range asymmetry."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _gcum(x, day):
    return pd.Series(np.asarray(x, float)).groupby(day).cumsum().to_numpy()


def _dwell_dip(ctx, p):
    k, n = p["share"], int(p["ema_bars"])
    cnt = ctx.bar_in_day + 1.0
    sa = _gcum(ctx.c > ctx.day_open, ctx.day) / cnt
    sb = _gcum(ctx.c < ctx.day_open, ctx.day) / cnt
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    pc, pe = ctx.prev(ctx.c, 1), ctx.prev(ema, 1)
    late = ctx.minute >= 630
    long = late & (sa >= k) & (pc <= pe) & (ctx.c > ema)
    short = late & (sb >= k) & (pc >= pe) & (ctx.c < ema)
    return long.astype(int) - short.astype(int)


def _early_extreme_vwap(ctx, p):
    early, start = p["early_min"], p["start_hour"]
    day = ctx.day
    hi_new = ctx.h >= ctx.session_high(True)
    lo_new = ctx.l <= ctx.session_low(True)
    hi_bar = pd.Series(np.where(hi_new, ctx.bar_in_day, np.nan)).groupby(day).ffill().to_numpy()
    lo_bar = pd.Series(np.where(lo_new, ctx.bar_in_day, np.nan)).groupby(day).ffill().to_numpy()
    hi_early = hi_bar * ctx.fr.tf < early
    lo_early = lo_bar * ctx.fr.tf < early
    vw = ctx.vwap()
    late = ctx.minute >= start * 60
    short = late & hi_early & ~lo_early & (ctx.c < vw)
    long = late & lo_early & ~hi_early & (ctx.c > vw)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _other_side_vwap(ctx, p):
    nb = max(2, ctx.bars(p["other_min"]))
    oth = ctx.other_close()
    oema = ctx.cached(("oema", nb), lambda: ctx.ema(oth, nb))
    vw = ctx.vwap()
    long = (ctx.c > vw) & (oth < oema)
    short = (ctx.c < vw) & (oth > oema)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _pos_divergence(ctx, p):
    k = p["gap"]
    oth = ctx.other_close()
    g = pd.Series(oth).groupby(ctx.day)
    ohi, olo = g.cummax().to_numpy(), g.cummin().to_numpy()
    shi, slo = ctx.session_high(True), ctx.session_low(True)
    with np.errstate(all="ignore"):
        pos = (ctx.c - slo) / (shi - slo)
        opos = (oth - olo) / (ohi - olo)
    div = pos - (1.0 - opos)
    ok = ctx.minute >= 600
    long = ok & (div <= -k)
    short = ok & (div >= k)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _updown_range(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    rng = ctx.h - ctx.l
    up = ctx.roll(np.where(ctx.c > ctx.o, rng, 0.0), n, "sum")
    dn = ctx.roll(np.where(ctx.c < ctx.o, rng, 0.0), n, "sum")
    with np.errstate(all="ignore"):
        bal = (up - dn) / (up + dn)
    return ctx.cross(bal >= k).astype(int) - ctx.cross(bal <= -k).astype(int)


def _hh_ll_balance(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    hh = (ctx.h > ctx.prev(ctx.h, 1)).astype(float)
    ll = (ctx.l < ctx.prev(ctx.l, 1)).astype(float)
    bal = ctx.roll(hh, n, "mean") - ctx.roll(ll, n, "mean")
    return ctx.cross(bal >= k).astype(int) - ctx.cross(bal <= -k).astype(int)


def _v_turn(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    c1, c2 = ctx.prev(ctx.c, n), ctx.prev(ctx.c, 2 * n)
    r_now, r_old = ctx.c / c1 - 1.0, c1 / c2 - 1.0
    typ = ctx.cached(("absr", n), lambda: ctx.prev_sessions(np.abs(r_now), "mean"))
    long = (r_now >= k * typ) & (r_old <= -k * typ)
    short = (r_now <= -k * typ) & (r_old >= k * typ)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _volume_pace(ctx, p):
    k = p["pace"]
    cumv = _gcum(ctx.v, ctx.day)
    typ = ctx.cached("cumv_med", lambda: ctx.same_minute(cumv, "median"))
    with np.errstate(all="ignore"):
        busy = (cumv / typ) >= k
    vw = ctx.vwap()
    ok = ctx.minute >= 600
    long = ok & busy & (ctx.c > vw) & (ctx.c > ctx.day_open)
    short = ok & busy & (ctx.c < vw) & (ctx.c < ctx.day_open)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _recovery_adr(ctx, p):
    k = p["frac"]
    d = ctx.day.astype(int)
    per = pd.DataFrame({"h": ctx.h, "l": ctx.l, "d": d}).groupby("d").agg(hh=("h", "max"), ll=("l", "min"))
    adr = (per["hh"] - per["ll"]).rolling(20, min_periods=20).mean().shift(1)
    adr_b = adr.reindex(np.arange(d.max() + 1)).to_numpy()[d]
    shi, slo = ctx.session_high(True), ctx.session_low(True)
    long = ((ctx.c - slo) >= k * adr_b) & ((shi - ctx.c) >= k * adr_b)
    # price is k ADR above the low AND k ADR below the high: a recovery inside a wide range
    up_leg = ctx.c > ctx.vwap()
    long = long & up_leg
    short = ((ctx.c - slo) >= k * adr_b) & ((shi - ctx.c) >= k * adr_b) & ~up_leg
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _volume_peak_failure(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    rmax = ctx.roll(ctx.v, n, "max")
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    peak = (ctx.v >= rmax) & (ctx.v >= k * med)
    day = ctx.day
    up_low = pd.Series(np.where(peak & (ctx.c > ctx.o), ctx.l, np.nan)).groupby(day).ffill(limit=n).to_numpy()
    dn_high = pd.Series(np.where(peak & (ctx.c < ctx.o), ctx.h, np.nan)).groupby(day).ffill(limit=n).to_numpy()
    short = ctx.c < up_low
    long = ctx.c > dn_high
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


FAMILIES = [
    Family("E-728", "Open-dwell share dip entry",
           "When most of the session's bars closed on one side of the day open, the day is a one-sided auction; a dip "
           "through a short EMA that closes back on the dominant side is cheap continuation for the trend participants.",
           {"share": [0.75, 0.85, 0.95], "ema_bars": [10, 20, 30]}, _dwell_dip,
           source="assistant reasoning", author="agent"),
    Family("E-729", "Early-extreme survival VWAP cross",
           "If the day's high (low) formed early and the opposite extreme formed later, the day is a trend day; "
           "after the morning, a close through VWAP in the trend direction means trapped early buyers (sellers) give up.",
           {"early_min": [45, 60, 90], "start_hour": [11, 12, 13]}, _early_extreme_vwap,
           source="assistant reasoning", author="agent"),
    Family("E-730", "VWAP cross confirmed by the other market's side",
           "A cross of the own VWAP is more reliable when the other contract (usually negatively correlated) sits on its "
           "opposite side of its short EMA: both markets then express the same risk flow.",
           {"other_min": [10, 20, 40]}, _other_side_vwap,
           source="assistant reasoning", author="agent"),
    Family("E-731", "Day-range position divergence versus the other market",
           "Index and dollar usually share inverse range positions inside the day. When the index sits far lower in its "
           "day range than the dollar implies, the laggard converges.",
           {"gap": [0.5, 0.7, 0.9]}, _pos_divergence,
           source="assistant reasoning", author="agent"),
    Family("E-732", "Up-bar versus down-bar range balance follow",
           "When the range printed by up bars dominates the range printed by down bars over a window, buyers cause the "
           "wider moves and the imbalance persists.",
           {"win_min": [20, 30, 45], "k": [0.4, 0.55, 0.7]}, _updown_range,
           source="assistant reasoning", author="agent"),
    Family("E-733", "Higher-high versus lower-low frequency balance",
           "A window with many bars making higher highs and few making lower lows shows one side continually "
           "extending the price; the first time the balance gets lopsided marks control.",
           {"win_min": [15, 30, 45], "k": [0.3, 0.45, 0.6]}, _hh_ll_balance,
           source="assistant reasoning", author="agent"),
    Family("E-734", "V-turn after a sharp opposite move",
           "A large move in the opposite direction of the one just before it, both beyond what is typical, signals "
           "that the earlier side was absorbed; follow the turn.",
           {"win_min": [10, 20, 30], "k": [0.75, 1.0, 1.5]}, _v_turn,
           source="assistant reasoning", author="agent"),
    Family("E-735", "Busy-volume pace with VWAP and open side",
           "When cumulative session volume runs well ahead of its typical pace, participation is unusually high; "
           "price on the same side of VWAP and day open carries conviction that persists.",
           {"pace": [1.3, 1.6, 2.0]}, _volume_pace,
           source="assistant reasoning", author="agent"),
    Family("E-736", "Mid-range recovery measured in average daily range",
           "Price that sits at least a fraction of the typical daily range away from both session extremes is in the "
           "middle of an expanded day; the VWAP side then gives the continuation direction.",
           {"frac": [0.25, 0.35, 0.45]}, _recovery_adr,
           source="assistant reasoning", author="agent"),
    Family("E-737", "Volume-peak bar failure",
           "The highest-volume bar of a window shows where aggressive participants committed; a close beyond the "
           "extreme of that bar against its direction traps them and forces exits.",
           {"win_min": [30, 60], "k": [1.5, 2.0, 3.0]}, _volume_peak_failure,
           source="assistant reasoning", author="agent"),
]
