"""Conveyor batch B-062 (agent, 2026-11-22). Mixed: cross-market lag, level reclaims, squeeze, wick absorption, climax, stretch, shocks."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _dollar_lead(ctx, p):
    nb, k = ctx.bars(p["move_min"]), p["k"]
    oc = ctx.other_close()
    ro = oc / ctx.prev(oc, nb) - 1.0
    rs = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    to = ctx.cached(("to", nb), lambda: ctx.prev_sessions(np.abs(ro), "mean"))
    ts = ctx.cached(("ts", nb), lambda: ctx.prev_sessions(np.abs(rs), "mean"))
    # WIN and the dollar move inversely: dollar falls -> index should rise
    long = (ro <= -k * to) & (rs < 0.5 * ts)
    short = (ro >= k * to) & (rs > -0.5 * ts)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _open_reclaim(ctx, p):
    nb = ctx.bars(p["away_min"])
    do = ctx.day_open
    was_below = ctx.roll((ctx.c < do).astype(float), nb, "min", include_current=False) == 1
    was_above = ctx.roll((ctx.c > do).astype(float), nb, "min", include_current=False) == 1
    up = was_below & (ctx.c > do)
    dn = was_above & (ctx.c < do)
    return up.astype(int) - dn.astype(int)


def _squeeze_release(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    nb = max(nb, 4)
    bw = ctx.roll(ctx.c, nb, "std") / ctx.c
    typ = ctx.cached(("bw_typ", nb), lambda: ctx.same_minute(np.nan_to_num(bw, nan=np.nan), "median"))
    sq = ctx.prev(bw, 1) < k * typ
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    return (sq & (ctx.c > hi)).astype(int) - (sq & (ctx.c < lo)).astype(int)


def _wick_absorb(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    lw = np.minimum(ctx.o, ctx.c) - ctx.l
    uw = ctx.h - np.maximum(ctx.o, ctx.c)
    rng = ctx.h - ctx.l
    s = ctx.roll(lw - uw, nb, "sum")
    r = ctx.roll(rng, nb, "sum")
    frac = np.where(r > 0, s / np.where(r > 0, r, 1), 0.0)
    long = (frac >= th) & (ctx.c > ctx.o)
    short = (frac <= -th) & (ctx.c < ctx.o)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _climax_reversal(ctx, p):
    k, nb = p["vol_k"], ctx.bars(p["lookback_min"])
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    rng = np.where(ctx.h > ctx.l, ctx.h - ctx.l, np.nan)
    loc = (ctx.c - ctx.l) / rng
    heavy = ctx.v > k * med
    short = heavy & (ctx.h > hi) & (loc < 0.3)
    long = heavy & (ctx.l < lo) & (loc > 0.7)
    return long.astype(int) - short.astype(int)


def _ema_stretch_fade(ctx, p):
    k, n = p["k"], int(p["ema_bars"])
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    avg = ctx.roll(ctx.h - ctx.l, n, "mean")
    z = (ctx.c - ema) / avg
    return ctx.cross(z <= -k).astype(int) - ctx.cross(z >= k).astype(int)


def _quiet_shock_fade(ctx, p):
    k = p["range_k"]
    rng = ctx.h - ctx.l
    rmed = ctx.cached("rng_med", lambda: ctx.same_minute(rng, "median"))
    vmed = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    shock = (rng > k * rmed) & (ctx.v < vmed)
    return (shock & (ctx.c < ctx.o)).astype(int) - (shock & (ctx.c > ctx.o)).astype(int)


def _range_triplet(ctx, p):
    m = p["min_body_frac"]
    rng = ctx.h - ctx.l
    r1, r2 = ctx.prev(rng, 1), ctx.prev(rng, 2)
    c1, o1 = ctx.prev(ctx.c, 1), ctx.prev(ctx.o, 1)
    c2, o2 = ctx.prev(ctx.c, 2), ctx.prev(ctx.o, 2)
    grow = (rng > r1) & (r1 > r2) & (r2 > 0)
    body = np.abs(ctx.c - ctx.o) >= m * rng
    up = grow & body & (ctx.c > ctx.o) & (c1 > o1) & (c2 > o2)
    dn = grow & body & (ctx.c < ctx.o) & (c1 < o1) & (c2 < o2)
    return up.astype(int) - dn.astype(int)


def _vwap_bar_through(ctx, p):
    k = p["body_k"]
    vw = ctx.vwap()
    body = np.abs(ctx.c - ctx.o)
    avg = ctx.roll(body, 20, "mean", include_current=False)
    big = body >= k * avg
    up = big & (ctx.o < vw) & (ctx.c > vw)
    dn = big & (ctx.o > vw) & (ctx.c < vw)
    return up.astype(int) - dn.astype(int)


def _prev_close_cross(ctx, p):
    nb = ctx.bars(p["away_min"])
    pc = ctx.prev_session_value("close")
    was_below = ctx.roll((ctx.c < pc).astype(float), nb, "min", include_current=False) == 1
    was_above = ctx.roll((ctx.c > pc).astype(float), nb, "min", include_current=False) == 1
    up = was_below & (ctx.c > pc)
    dn = was_above & (ctx.c < pc)
    return up.astype(int) - dn.astype(int)


FAMILIES = [
    Family("E-618", "Dollar-lead lag on the index",
           "WIN and WDO trade inversely and index futures react a bit later to a dollar move; when the dollar moves "
           "more than usual and WIN has not yet followed inversely, late index participants catch up.",
           {"move_min": [5, 10, 20], "k": [1.0, 1.5, 2.0]}, _dollar_lead, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-619", "Session-open price reclaim",
           "The session's opening print is a reference many traders watch; after trading on one side of it for a "
           "while, a close back across it shifts control.",
           {"away_min": [15, 30, 60]}, _open_reclaim, source="assistant reasoning", author="agent"),
    Family("E-620", "Bollinger squeeze release",
           "When closing-price dispersion is far below its usual size for the time of day, stops cluster just outside "
           "the box; a close beyond the box releases the compressed volatility.",
           {"win_min": [20, 30, 45], "k": [0.5, 0.7, 0.9]}, _squeeze_release, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-621", "Wick absorption balance",
           "Persistent long lower wicks over a window show passive buyers absorbing sells; a green bar after it "
           "means the sellers are spent (mirror for upper wicks).",
           {"win_min": [15, 30, 60], "th": [0.2, 0.3, 0.4]}, _wick_absorb, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-622", "Volume-climax reversal",
           "A very heavy bar that pokes to a new window extreme but closes away from it is a capitulation or "
           "exhaustion; the forced side is done, fade it.",
           {"vol_k": [2.0, 3.0, 4.0], "lookback_min": [20, 40]}, _climax_reversal, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-623", "EMA stretch fade in range units",
           "Price stretched several average bar-ranges away from its short EMA is an overshoot from impatient "
           "market orders; fade the first bar that gets there.",
           {"k": [2.0, 3.0, 4.0], "ema_bars": [10, 20]}, _ema_stretch_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-624", "Quiet shock bar fade",
           "A bar with a much larger range than usual but below-median volume moved on thin liquidity, not on real "
           "participation; fade its direction.",
           {"range_k": [1.5, 2.0, 3.0]}, _quiet_shock_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-625", "Range-expansion triplet follow",
           "Three same-colour bars with growing ranges mean participation is building in one direction; the next "
           "wave of followers keeps it going.",
           {"min_body_frac": [0.5, 0.6, 0.7]}, _range_triplet, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-626", "Single bar through VWAP",
           "One big-body bar that opens on one side of VWAP and closes on the other is an institutional-size "
           "push through the day's fair value; follow it.",
           {"body_k": [1.5, 2.0, 3.0]}, _vwap_bar_through, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-627", "Previous-close line reclaim",
           "The prior session settlement-like close is a reference for overnight positions; after the price stays on "
           "one side a while, a close across it shows those holders giving up or doubling down.",
           {"away_min": [15, 30, 60]}, _prev_close_cross, source="assistant reasoning", author="agent"),
]
