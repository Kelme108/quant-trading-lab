"""Conveyor batch B-091 (agent, 2026-11-24). Mixed batch: band fades, stretch fades, squeeze release, run structure,
dollar lead-lag, calendar seasonality, new-extreme clustering."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _d(a, b):
    return a.astype(int) - b.astype(int)


def _vwap_band_fade(ctx, p):
    nb = ctx.bars(p["win_min"])
    k = p["k"]
    d = ctx.c - ctx.vwap()
    sd = ctx.roll(d, nb, "std")
    ok = sd > 0
    long = ok & (d < -k * sd)
    short = ok & (d > k * sd)
    return _d(ctx.cross(long), ctx.cross(short))


def _ema_stretch_fade(ctx, p):
    n, k = int(p["ema_bars"]), p["k"]
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    atr = ctx.roll(ctx.h - ctx.l, n, "mean")
    dev = np.where(atr > 0, (ctx.c - ema) / np.where(atr > 0, atr, 1.0), 0.0)
    return _d(ctx.cross(dev < -k), ctx.cross(dev > k))


def _boll_reentry(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    m = ctx.roll(ctx.c, nb, "mean")
    sd = ctx.roll(ctx.c, nb, "std")
    up, lo = m + k * sd, m - k * sd
    short = (ctx.prev(ctx.c, 1) > ctx.prev(up, 1)) & (ctx.c < up)
    long = (ctx.prev(ctx.c, 1) < ctx.prev(lo, 1)) & (ctx.c > lo)
    return _d(long, short)


def _squeeze_release(ctx, p):
    k, nb = p["k"], ctx.bars(p["win_min"])
    width = ctx.roll(ctx.c, nb, "std") / ctx.c
    med = ctx.cached(("width_med", nb), lambda: ctx.same_minute(width, "median"))
    sq = ctx.prev((width < k * med).astype(float), 1) == 1
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    return _d(ctx.cross(sq & (ctx.c > hi)), ctx.cross(sq & (ctx.c < lo)))


def _staircase(ctx, p):
    m = int(p["m"])
    up = ((ctx.l > ctx.prev(ctx.l, 1)) & (ctx.c > ctx.prev(ctx.c, 1))).astype(float)
    dn = ((ctx.h < ctx.prev(ctx.h, 1)) & (ctx.c < ctx.prev(ctx.c, 1))).astype(float)
    su = ctx.roll(up, m, "sum") == m
    sd = ctx.roll(dn, m, "sum") == m
    return _d(ctx.cross(su), ctx.cross(sd))


def _dollar_lead_lag(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    oc = ctx.other_close()
    ro = np.nan_to_num(oc / ctx.prev(oc, nb) - 1.0)
    rw = np.nan_to_num(ctx.c / ctx.prev(ctx.c, nb) - 1.0)
    typ = ctx.cached(("abs_o", nb), lambda: ctx.prev_sessions(np.abs(ro), "mean"))
    big_up = ro >= k * typ
    big_dn = ro <= -k * typ
    short = big_up & (typ > 0) & (rw >= 0)
    long = big_dn & (typ > 0) & (rw <= 0)
    return _d(ctx.cross(long), ctx.cross(short))


def _seasonal_bar(ctx, p):
    k = p["k"]
    r = (ctx.c / ctx.o - 1.0)
    nr = pd.Series(r).groupby(ctx.day).shift(-1).to_numpy()
    m = ctx.cached("seas_m", lambda: ctx.same_minute(nr, "mean"))
    a = ctx.cached("seas_a", lambda: ctx.same_minute(np.abs(nr), "mean"))
    long = m > k * a
    short = m < -k * a
    return _d(ctx.cross(long), ctx.cross(short))


def _new_extreme_cluster(ctx, p):
    nb, m = ctx.bars(p["win_min"]), int(p["m"])
    nh = (ctx.h > ctx.session_high()).astype(float)
    nl = (ctx.l < ctx.session_low()).astype(float)
    ch = ctx.roll(nh, nb, "sum") >= m
    cl = ctx.roll(nl, nb, "sum") >= m
    return _d(ctx.cross(ch & ~cl), ctx.cross(cl & ~ch))


def _open_stretch_fade(ctx, p):
    k = p["k"]
    r = ctx.c / ctx.day_open - 1.0
    typ = ctx.cached("abs_ret_sm", lambda: ctx.same_minute(np.abs(r), "mean"))
    z = np.where(typ > 0, r / np.where(typ > 0, typ, 1.0), 0.0)
    short = (z >= k) & (ctx.c < ctx.o)
    long = (z <= -k) & (ctx.c > ctx.o)
    return _d(ctx.cross(long), ctx.cross(short))


def _bar_range_ratio_follow(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    rng = ctx.h - ctx.l
    avg = ctx.roll(rng, nb, "mean", include_current=False)
    big = (rng >= k * avg) & (avg > 0)
    prior_dn = ctx.prev(ctx.c, 1) < ctx.prev(ctx.o, 1)
    prior_up = ctx.prev(ctx.c, 1) > ctx.prev(ctx.o, 1)
    # a wide bar that retraces the previous bar's body fully (engulf in range terms) with a close at its extreme
    pos = np.where(rng > 0, (ctx.c - ctx.l) / np.where(rng > 0, rng, 1.0), 0.5)
    long = big & prior_dn & (pos >= 0.8) & (ctx.c > ctx.prev(ctx.o, 1))
    short = big & prior_up & (pos <= 0.2) & (ctx.c < ctx.prev(ctx.o, 1))
    return _d(long, short)


FAMILIES = [
    Family("E-908", "VWAP sigma-band fade",
           "Price far below/above VWAP in units of its own recent deviation is stretched; liquidity providers "
           "anchored to VWAP lean against it and price snaps back.",
           {"win_min": [30, 60], "k": [1.5, 2.0, 2.5]}, _vwap_band_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-909", "EMA stretch in ATR units fade",
           "A close several average bar-ranges away from a short EMA is an overextension from forced liquidation "
           "or chasing; fade the first bar that gets there.",
           {"ema_bars": [20, 30, 40], "k": [1.5, 2.0, 3.0]}, _ema_stretch_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-910", "Bollinger band re-entry",
           "A close outside the band followed by a close back inside shows the push was absorbed; trade back "
           "toward the mean.",
           {"win_min": [20, 40], "k": [2.0, 2.5]}, _boll_reentry, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-911", "Volatility squeeze release",
           "When recent dispersion is far below its typical level for this time of day, resting orders pile up "
           "on both sides; the first range break releases stops and continues.",
           {"k": [0.6, 0.8, 1.0], "win_min": [10, 20]}, _squeeze_release, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-912", "Staircase of higher lows",
           "Consecutive bars each with higher low and higher close show persistent absorption of sellers; "
           "participants chasing keep it going.",
           {"m": [3, 4, 5]}, _staircase, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-913", "Dollar lead, index lag",
           "WIN and WDO are negatively linked through foreign flow; after a large WDO move that WIN has not yet "
           "mirrored, the index catches up in the opposite direction.",
           {"win_min": [5, 10, 15], "k": [1.0, 1.5, 2.0]}, _dollar_lead_lag, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-914", "Minute-of-day seasonality",
           "Scheduled flows (opening auctions, fixings, hedging) repeat at the same clock minute; follow the "
           "sign of the average next-bar return at this minute over the last 20 sessions when it is consistent.",
           {"k": [0.25, 0.35, 0.45]}, _seasonal_bar, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-915", "New-extreme clustering",
           "Several fresh session highs (lows) inside a short window mean one side is repeatedly lifting the "
           "offer; stop-driven flow persists.",
           {"win_min": [15, 30], "m": [2, 3, 4]}, _new_extreme_cluster, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-916", "Day-open stretch fade with reversal bar",
           "When the price is far from the session open relative to the typical distance at this time, and a "
           "bar turns against it, late chasers are trapped; fade back toward the open.",
           {"k": [1.5, 2.0, 2.5]}, _open_stretch_fade, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-917", "Wide reversal bar through prior body",
           "A bar much wider than recent ones that closes near its extreme and through the previous opposite "
           "bar's open shows aggressive new flow overpowering the last move; follow it.",
           {"win_min": [10, 20], "k": [1.5, 2.0, 2.5]}, _bar_range_ratio_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
