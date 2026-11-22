"""Conveyor batch B-045 (agent, 2026-11-21). Mostly WIN micro-break fades with new context filters (volume, value side, depth, prior close, time), plus band re-entry and z-score reversals."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _edges(ctx, nb):
    hi = ctx.cached(("hi", nb), lambda: ctx.roll(ctx.h, nb, "max", include_current=False))
    lo = ctx.cached(("lo", nb), lambda: ctx.roll(ctx.l, nb, "min", include_current=False))
    return hi, lo


def _out(ctx, long, short):
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _thin_break(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["vol_k"]
    hi, lo = _edges(ctx, nb)
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    thin = ctx.v < k * med
    return _out(ctx, (ctx.l < lo) & thin, (ctx.h > hi) & thin)


def _value_aligned(ctx, p):
    nb = ctx.bars(p["win_min"])
    hi, lo = _edges(ctx, nb)
    vw = ctx.vwap()
    return _out(ctx, (ctx.l < lo) & (ctx.c > vw), (ctx.h > hi) & (ctx.c < vw))


def _overshoot(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    hi, lo = _edges(ctx, nb)
    avg = ctx.roll(ctx.h - ctx.l, nb, "mean", include_current=False)
    return _out(ctx, ctx.c < lo - k * avg, ctx.c > hi + k * avg)


def _vwap_band(ctx, p):
    nb, m = ctx.bars(p["win_min"]), p["m"]
    pv = ctx.roll(ctx.c * ctx.v, nb, "sum")
    vs = ctx.roll(ctx.v, nb, "sum")
    vw = pv / np.where(vs > 0, vs, np.nan)
    sd = ctx.roll(ctx.c, nb, "std")
    below = (ctx.c < vw - m * sd).astype(float)
    above = (ctx.c > vw + m * sd).astype(float)
    pb, pa = ctx.prev(below, 1), ctx.prev(above, 1)
    long = (pb == 1) & (below == 0) & (sd > 0)
    short = (pa == 1) & (above == 0) & (sd > 0)
    return long.astype(int) - short.astype(int)


def _final_hour(ctx, p):
    nb, fin = ctx.bars(p["win_min"]), p["final_min"]
    hi, lo = _edges(ctx, nb)
    late = (ctx.minutes_to_close <= fin) & (ctx.minutes_to_close > 10)
    return _out(ctx, (ctx.l < lo) & late, (ctx.h > hi) & late)


def _prior_close_carry(ctx, p):
    nb, q = ctx.bars(p["win_min"]), p["q"]
    hi, lo = _edges(ctx, nb)
    pdh, pdl, pdc = (ctx.prev_session_value(x) for x in ("high", "low", "close"))
    rng = pdh - pdl
    loc = (pdc - pdl) / np.where(rng > 0, rng, np.nan)
    return _out(ctx, (ctx.l < lo) & (loc >= q), (ctx.h > hi) & (loc <= 1 - q))


def _reclaim(ctx, p):
    nb = ctx.bars(p["win_min"])
    hi, lo = _edges(ctx, nb)
    brk_dn = (ctx.l < lo).astype(float)
    brk_up = (ctx.h > hi).astype(float)
    lo1, hi1 = ctx.prev(lo, 1), ctx.prev(hi, 1)
    long = (ctx.prev(brk_dn, 1) == 1) & (ctx.c > lo1) & (ctx.c > ctx.o)
    short = (ctx.prev(brk_up, 1) == 1) & (ctx.c < hi1) & (ctx.c < ctx.o)
    return long.astype(int) - short.astype(int)


def _zscore(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    mu = ctx.roll(ctx.c, nb, "mean")
    sd = ctx.roll(ctx.c, nb, "std")
    z = (ctx.c - mu) / np.where(sd > 0, sd, np.nan)
    return _out(ctx, z < -k, z > k)


def _beyond_or(ctx, p):
    ob, nb = ctx.bars(p["or_min"]), ctx.bars(p["win_min"])
    first = ctx.bar_in_day < ob
    g = pd.DataFrame({"d": ctx.day, "h": np.where(first, ctx.h, np.nan), "l": np.where(first, ctx.l, np.nan)})
    orh = g.groupby("d")["h"].transform("max").to_numpy()
    orl = g.groupby("d")["l"].transform("min").to_numpy()
    hi, lo = _edges(ctx, nb)
    done = ctx.bar_in_day >= ob
    long = done & (ctx.c < orl) & (ctx.l < lo)
    short = done & (ctx.c > orh) & (ctx.h > hi)
    return _out(ctx, long, short)


def _move_turn(ctx, p):
    nb, k = ctx.bars(p["move_min"]), p["k"]
    move = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    sd = ctx.cached(("mv_sd", nb), lambda: ctx.prev_sessions(move, "sd"))
    big_dn = ctx.prev(move, 1) <= -k * sd
    big_up = ctx.prev(move, 1) >= k * sd
    long = big_dn & (ctx.c > ctx.o) & (sd > 0)
    short = big_up & (ctx.c < ctx.o) & (sd > 0)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-448", "Thin-volume micro-break fade",
           "A break of the recent low/high made on volume well below the usual for that minute has no real "
           "participation behind it; the stops it touches are the only flow and the price returns.",
           {"win_min": [15, 30, 60], "vol_k": [0.5, 0.7, 1.0]}, _thin_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-449", "Value-aligned micro-break fade",
           "A dip to a new short-term low that still closes above the session VWAP is a pullback inside buyer "
           "control (mirror for highs below VWAP); trapped counter-trend sellers fuel the bounce.",
           {"win_min": [10, 20, 30, 60]}, _value_aligned, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-450", "Overshoot-depth fade",
           "A close beyond the recent extreme by more than a multiple of the average bar range is a stop-run "
           "overshoot, exhausting the aggressive side; fade it.",
           {"win_min": [15, 30, 60], "k": [0.5, 1.0, 1.5]}, _overshoot, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-451", "Rolling-VWAP envelope re-entry fade",
           "When the close comes back inside a volume-weighted rolling envelope after an excursion outside it, "
           "the excursion has been rejected and the price reverts toward the rolling value.",
           {"win_min": [30, 60, 90], "m": [1.5, 2.0, 2.5]}, _vwap_band, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-452", "Final-hour micro-break fade",
           "In the last hour before the close, day traders flatten and breaks of the recent range lack follow-"
           "through; fade the poke beyond the range.",
           {"win_min": [10, 20, 30], "final_min": [45, 60, 90]}, _final_hour, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-453", "Prior-close-carry dip buy",
           "After a session that closed near its high, dips to short-term lows early on the next session meet "
           "carried-over demand (mirror after a weak close).",
           {"win_min": [15, 30, 60], "q": [0.6, 0.7, 0.8]}, _prior_close_carry, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-454", "Break-then-reclaim fade",
           "A break of the recent extreme followed one bar later by a close back inside with a bar in the "
           "opposite direction confirms the failed break; enter after the confirmation.",
           {"win_min": [15, 30, 60]}, _reclaim, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-455", "Rolling z-score extreme fade",
           "A close far from its own rolling mean in standard-deviation terms is a short-lived liquidity "
           "dislocation that tends to revert.",
           {"win_min": [30, 60, 120], "k": [2.0, 2.5, 3.0]}, _zscore, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-456", "Beyond-opening-range micro-break fade",
           "Once the price sits outside the opening range, a further short-term extreme is a late chase by "
           "breakout traders who are the liquidity for fade traders.",
           {"or_min": [15, 30, 60], "win_min": [10, 20, 30]}, _beyond_or, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-457", "Large-move reversal-bar fade",
           "After a bar-window move that is large relative to the last 20 sessions' dispersion, the first bar "
           "closing against it signals that the impulsive flow has stopped; fade the move.",
           {"move_min": [5, 10, 15], "k": [2.0, 3.0, 4.0]}, _move_turn, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
