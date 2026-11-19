"""Conveyor batch B-026 (agent, 2026-11-19). Mixed WIN ideas: hourly candle carry, break-bar participation, the
pre-New-York lull, marginal breaks, stacked daily extremes, indecisive tape, counter-drift breaks, spent volume
quota, flat value and range ahead of schedule."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


# ---------------------------------------------------------------------------------------------
# shared helpers (all causal, session-bounded)
# ---------------------------------------------------------------------------------------------

def _rng_med(ctx):
    return ctx.cached("b026_rng_med", lambda: ctx.same_minute(ctx.h - ctx.l, "median"))


def _micro(ctx, win_min):
    nb = ctx.bars(win_min)
    hi = ctx.cached(("b026_hi", nb), lambda: ctx.roll(ctx.h, nb, "max", include_current=False))
    lo = ctx.cached(("b026_lo", nb), lambda: ctx.roll(ctx.l, nb, "min", include_current=False))
    up = ctx.cross(ctx.c > hi)
    dn = ctx.cross(ctx.c < lo)
    return hi, lo, up, dn


def _fade(up, dn, cond):
    return (dn & cond).astype(int) - (up & cond).astype(int)


# ---------------------------------------------------------------------------------------------
# families
# ---------------------------------------------------------------------------------------------

def _hour_close_carry(ctx, p):
    nb = ctx.bars(60)
    hi = ctx.roll(ctx.h, nb, "max")
    lo = ctx.roll(ctx.l, nb, "min")
    rng = hi - lo
    typ = ctx.cached(("b026_hr_typ", nb), lambda: ctx.prev_sessions(rng, "mean"))
    mark = ((ctx.minute + ctx.tf) % 60) == 0                  # the bar that closes a clock hour
    with np.errstate(invalid="ignore", divide="ignore"):
        loc = np.where(rng > 0, (ctx.c - lo) / np.where(rng > 0, rng, 1.0), 0.5)
    big = rng >= p["k"] * typ
    long = mark & big & (loc >= 1.0 - p["q"])
    short = mark & big & (loc <= p["q"])
    return long.astype(int) - short.astype(int)


def _low_volume_break_fade(ctx, p):
    _, _, up, dn = _micro(ctx, p["win_min"])
    vmed = ctx.cached("b026_vmed", lambda: ctx.same_minute(ctx.v, "median"))
    thin = ctx.v < p["q"] * vmed
    return _fade(up, dn, thin)


def _pre_ny_lull_fade(ctx, p):
    _, _, up, dn = _micro(ctx, p["win_min"])
    lull = (ctx.minute >= 9 * 60 + 30) & (ctx.minute + ctx.tf <= 10 * 60 + 25)
    return _fade(up, dn, lull)


def _marginal_break_fade(ctx, p):
    hi, lo, up, dn = _micro(ctx, p["win_min"])
    d = p["f"] * _rng_med(ctx)
    short = up & ((ctx.c - hi) <= d)
    long = dn & ((lo - ctx.c) <= d)
    return long.astype(int) - short.astype(int)


def _stacked_daily_extreme_fade(ctx, p):
    _, _, up, dn = _micro(ctx, 15)
    n = int(p["n_sessions"])
    nd = int(ctx.day.max()) + 1
    dh = pd.Series(ctx.h).groupby(ctx.day).max().reindex(range(nd))
    dl = pd.Series(ctx.l).groupby(ctx.day).min().reindex(range(nd))
    dist_h = np.full(ctx.n, np.inf)
    dist_l = np.full(ctx.n, np.inf)
    for j in range(1, n + 1):
        lh = dh.shift(j).to_numpy()[ctx.day]
        ll = dl.shift(j).to_numpy()[ctx.day]
        dist_h = np.fmin(dist_h, np.where(np.isnan(lh), np.inf, np.abs(ctx.c - lh)))
        dist_l = np.fmin(dist_l, np.where(np.isnan(ll), np.inf, np.abs(ctx.c - ll)))
    d = p["k"] * _rng_med(ctx)
    short = up & (dist_h <= d)
    long = dn & (dist_l <= d)
    return long.astype(int) - short.astype(int)


def _indecisive_tape_fade(ctx, p):
    _, _, up, dn = _micro(ctx, 15)
    rng = ctx.h - ctx.l
    with np.errstate(invalid="ignore", divide="ignore"):
        br = np.where(rng > 0, np.abs(ctx.c - ctx.o) / np.where(rng > 0, rng, 1.0), 0.0)
    avg = ctx.roll(br, ctx.bars(p["win_min"]), "mean", include_current=False)
    return _fade(up, dn, avg < p["th"])


def _counter_drift_fade(ctx, p):
    _, _, up, dn = _micro(ctx, 15)
    nb = ctx.bars(120)
    drift = ctx.c - ctx.prev(ctx.c, nb)
    typ = ctx.cached(("b026_drift_typ", nb), lambda: ctx.prev_sessions(np.abs(drift), "mean"))
    short = up & (drift <= -p["k"] * typ)
    long = dn & (drift >= p["k"] * typ)
    return long.astype(int) - short.astype(int)


def _volume_quota_fade(ctx, p):
    _, _, up, dn = _micro(ctx, p["win_min"])
    nd = int(ctx.day.max()) + 1
    tot = pd.Series(ctx.v).groupby(ctx.day).sum().reindex(range(nd))
    typ = tot.shift(1).rolling(20, min_periods=10).mean().to_numpy()[ctx.day]
    cumv = pd.Series(ctx.v).groupby(ctx.day).cumsum().to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        share = cumv / typ
    return _fade(up, dn, share >= p["q"])


def _flat_value_fade(ctx, p):
    _, _, up, dn = _micro(ctx, p["win_min"])
    vw = ctx.vwap()
    slope = vw - ctx.prev(vw, ctx.bars(30))
    flat = np.abs(slope) < p["k"] * _rng_med(ctx)
    return _fade(up, dn, flat)


def _range_ahead_fade(ctx, p):
    _, _, up, dn = _micro(ctx, p["win_min"])
    rso = ctx.session_high(include_current=True) - ctx.session_low(include_current=True)
    typ = ctx.cached("b026_rso_typ", lambda: ctx.same_minute(rso, "mean"))
    return _fade(up, dn, rso >= p["k"] * typ)


SRC = "assistant reasoning"

FAMILIES = [
    Family("E-258", "Hourly candle close-location carry",
           "Desks and chart traders read hourly candles; an hour that was wider than usual and closed in its top "
           "(bottom) slice ends with buyers (sellers) still lifting at the bell, i.e. a parent order not finished. "
           "The faders who sold the hour's high are offside as the next hour opens, so follow the close side.",
           {"q": [0.2, 0.25, 0.33], "k": [0.8, 1.0, 1.2]}, _hour_close_carry, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-259", "Low-volume micro-break fade",
           "A close through the recent high/low printed on far less volume than usual for that minute was not "
           "pushed by informed size, only by a few small orders into a thin book; the liquidity providers who "
           "were run over re-quote and lean back, so fade the break.",
           {"win_min": [10, 15, 20], "q": [0.5, 0.7, 0.9]}, _low_volume_break_fade, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-260", "Pre-New-York lull micro-break fade",
           "Between the settled B3 open and the New York cash open, large index participants wait for US price "
           "discovery; breaks of the recent high/low in this window are local noise traded against market makers "
           "who are happy to provide liquidity, so they revert. Fade breaks only in the 9:30-10:25 lull.",
           {"win_min": [5, 10, 15]}, _pre_ny_lull_fade, markets=("WIN",), source=SRC, author="agent"),
    Family("E-261", "Marginal-break fade",
           "A close that clears the recent high/low by only a sliver triggers the breakout orders and the stops "
           "resting just beyond, but no buyer is paying up past them; once that small pool is filled there is "
           "nobody left on the break side and the resting liquidity pushes price back, so fade small breaks.",
           {"win_min": [10, 15, 30], "f": [0.1, 0.2, 0.3]}, _marginal_break_fade, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-262", "Stacked daily-extreme micro-break fade",
           "Each of the last few sessions' highs and lows is a level where swing traders keep take-profit and "
           "fresh limit orders; a 15-minute break that runs into ANY of them (not only yesterday's or the channel "
           "edge) meets that resting supply/demand and stalls, so fade breaks that end near a stacked old extreme.",
           {"n_sessions": [3, 5, 10], "k": [1.0, 2.0, 3.0]}, _stacked_daily_extreme_fade, markets=("WIN",),
           source=SRC, author="agent"),
    Family("E-263", "Indecisive-tape micro-break fade",
           "When the recent bars are mostly small bodies inside their ranges, every bar is a two-way fight that "
           "the passive side wins; a break of the 15-minute extreme in such a tape is one more probe that the "
           "same passive traders absorb, so fade it.",
           {"win_min": [30, 60], "th": [0.3, 0.35, 0.4]}, _indecisive_tape_fade, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-264", "Counter-drift micro-break fade",
           "After a two-hour drift larger than usual, a 15-minute break against the drift is short covering or "
           "a dip-buyer's probe, while the participant behind the drift is still working the order; that order "
           "leans on the counter break, so fade it back toward the drift.",
           {"k": [0.5, 1.0, 1.5]}, _counter_drift_fade, markets=("WIN",), source=SRC, author="agent"),
    Family("E-265", "Spent volume-quota micro-break fade",
           "Once the session has already traded most of a typical full day's volume, the day's big orders have "
           "been executed; later breaks of the recent high/low are not backed by fresh size and the participants "
           "who are done (and now take profit) meet them, so fade breaks after the volume quota is spent.",
           {"win_min": [10, 15, 30], "q": [0.6, 0.75, 0.9]}, _volume_quota_fade, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-266", "Flat-value micro-break fade",
           "A session VWAP that has barely moved for half an hour means volume keeps trading at the same value "
           "on both sides: neither buyers nor sellers are moving value; a break of the recent high/low then "
           "trades away from accepted value and responsive traders return it, so fade breaks when value is flat.",
           {"win_min": [10, 15, 30], "k": [0.5, 1.0, 2.0]}, _flat_value_fade, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-267", "Range-ahead-of-schedule micro-break fade",
           "When today's range is already much wider than the usual range at this minute, day traders' targets "
           "are met early and the move is ahead of its normal schedule; new breaks then mostly carry late chasers "
           "who meet profit-takers, so fade breaks of the recent high/low on such days.",
           {"win_min": [15, 30], "k": [1.2, 1.5, 2.0]}, _range_ahead_fade, markets=("WIN",), source=SRC,
           author="agent"),
]
