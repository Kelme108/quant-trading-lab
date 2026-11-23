"""Conveyor batch B-074 (agent, 2026-11-23). Mixed themes: inter-bar gaps, return skew, bar-size structure, trend efficiency, cross-market spread, prior-session volume level, VWAP slope."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _gap_fill(ctx, p):
    k = p["k"]
    rng = ctx.h - ctx.l
    avg = ctx.prev(ctx.roll(rng, ctx.bars(p["win_min"]), "mean"), 1)
    gap = ctx.o - ctx.prev(ctx.c, 1)
    long = (gap <= -k * avg) & (ctx.c > ctx.o) & (avg > 0)
    short = (gap >= k * avg) & (ctx.c < ctx.o) & (avg > 0)
    return long.astype(int) - short.astype(int)


def _skew_exhaust(ctx, p):
    nb = ctx.bars(p["win_min"])
    r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    m3 = ctx.roll(r ** 3, nb, "mean")
    m2 = ctx.roll(r ** 2, nb, "mean")
    with np.errstate(all="ignore"):
        sk = m3 / np.where(m2 > 0, m2 ** 1.5, np.nan)
    th = p["th"]
    return ctx.cross(sk < -th).astype(int) - ctx.cross(sk > th).astype(int)


def _widest_bar_confirm(ctx, p):
    nb = ctx.bars(p["win_min"])
    rng = ctx.h - ctx.l
    body = np.abs(ctx.c - ctx.o)
    widest = (rng >= ctx.roll(rng, nb, "max")).astype(float)
    w1 = ctx.prev(widest, 1) == 1
    strong = ctx.prev(body, 1) >= p["frac"] * ctx.prev(rng, 1)
    up = w1 & strong & (ctx.prev(ctx.c, 1) > ctx.prev(ctx.o, 1)) & (ctx.c > ctx.prev(ctx.h, 1))
    dn = w1 & strong & (ctx.prev(ctx.c, 1) < ctx.prev(ctx.o, 1)) & (ctx.c < ctx.prev(ctx.l, 1))
    return up.astype(int) - dn.astype(int)


def _er_resume(ctx, p):
    nb = ctx.bars(p["n_min"])
    dc = ctx.c - ctx.prev(ctx.c, 1)
    sumabs = ctx.roll(np.abs(dc), nb, "sum")
    net = ctx.c - ctx.prev(ctx.c, nb)
    with np.errstate(all="ignore"):
        er = np.abs(net) / np.where(sumabs > 0, sumabs, np.nan)
    ok = er >= p["th"]
    up = ok & (net > 0) & (ctx.prev(ctx.c, 1) < ctx.prev(ctx.c, 2)) & (dc > 0)
    dn = ok & (net < 0) & (ctx.prev(ctx.c, 1) > ctx.prev(ctx.c, 2)) & (dc < 0)
    return up.astype(int) - dn.astype(int)


def _flatline_break(ctx, p):
    m, bk = int(p["m"]), p["big_k"]
    dc = ctx.c - ctx.prev(ctx.c, 1)
    ab = np.abs(dc)
    avg = ctx.roll(ab, ctx.bars(60), "mean")
    small = (ab <= 0.25 * avg).astype(float)
    flat = ctx.roll(small, m, "sum", include_current=False) == m
    big = (ab >= bk * avg) & (avg > 0)
    return np.where(flat & big, np.sign(dc), 0).astype(int)


def _spread_diverge(ctx, p):
    th = p["th"]
    own = ctx.c / ctx.day_open - 1.0
    oc = ctx.other_close()
    first = pd.Series(oc).groupby(ctx.day).transform("first").to_numpy()
    other = oc / first - 1.0
    so = ctx.cached("sd_own", lambda: ctx.prev_sessions(own, "sd"))
    st = ctx.cached("sd_other", lambda: ctx.prev_sessions(other, "sd"))
    with np.errstate(all="ignore"):
        d = own / so + other / st
    d = np.where((so > 0) & (st > 0) & (ctx.bar_in_day >= ctx.bars(p["min_after"])), d, np.nan)
    return ctx.cross(d < -th).astype(int) - ctx.cross(d > th).astype(int)


def _poc_cross(ctx, p):
    nb = ctx.bars(p["away_min"])
    df = pd.DataFrame({"d": ctx.day, "c": ctx.c, "v": ctx.v})
    idx = df.groupby("d")["v"].idxmax()
    lv = df.loc[idx.to_numpy()].set_index("d")["c"]
    lv = lv.reindex(range(int(ctx.day.max()) + 1)).shift(1).to_numpy()[ctx.day]
    below = (ctx.c < lv).astype(float)
    above = (ctx.c > lv).astype(float)
    wb = ctx.roll(below, nb, "min", include_current=False) == 1
    wa = ctx.roll(above, nb, "min", include_current=False) == 1
    up = wb & (ctx.c > lv)
    dn = wa & (ctx.c < lv)
    return up.astype(int) - dn.astype(int)


def _vwap_slope_pullback(ctx, p):
    k = p["k"]
    vw = ctx.vwap()
    slope = vw / ctx.prev(vw, ctx.bars(p["win_min"])) - 1.0
    long = (slope >= k) & (ctx.l <= vw) & (ctx.c > vw)
    short = (slope <= -k) & (ctx.h >= vw) & (ctx.c < vw)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _decel_stairs(ctx, p):
    n, k = int(p["n"]), p["k"]
    rng = ctx.h - ctx.l
    avg = ctx.roll(rng, ctx.bars(60), "mean")
    body = ctx.c - ctx.o
    up = np.ones(ctx.n, bool)
    dn = np.ones(ctx.n, bool)
    for j in range(1, n + 1):
        bj = ctx.prev(body, j)
        up &= bj > 0
        dn &= bj < 0
        if j > 1:
            bprev = ctx.prev(body, j - 1)
            up &= bprev < bj
            dn &= bprev > bj
    move = ctx.prev(ctx.c, 1) - ctx.prev(ctx.o, n)
    short = up & (move >= k * avg) & (body < 0) & (ctx.c < ctx.prev(ctx.c, 1))
    long = dn & (-move >= k * avg) & (body > 0) & (ctx.c > ctx.prev(ctx.c, 1))
    return long.astype(int) - short.astype(int)


def _prior_loc_bias(ctx, p):
    th = p["th"]
    pdh, pdl, pdc = ctx.prev_session_value("high"), ctx.prev_session_value("low"), ctx.prev_session_value("close")
    with np.errstate(all="ignore"):
        loc = (pdc - pdl) / np.where(pdh > pdl, pdh - pdl, np.nan)
    early = ctx.bar_in_day < ctx.bars(p["win_min"])
    vw = ctx.vwap()
    long = early & (loc >= th) & ctx.cross(ctx.c > vw)
    short = early & (loc <= 1 - th) & ctx.cross(ctx.c < vw)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-738", "Inter-bar gap fill with confirmation",
           "A bar opening far from the prior close is a thin-book dislocation; when the same bar already closes back "
           "toward the prior close, the gap is being filled and the fill continues.",
           {"k": [0.3, 0.5, 0.75], "win_min": [30, 60]}, _gap_fill, source="assistant reasoning", author="agent"),
    Family("E-739", "Return-skew jump exhaustion",
           "Strongly negative (positive) skew of recent bar returns means the window was driven by a few jump bars; "
           "jump-driven displacement tends to be partly given back, so buy negative skew, sell positive.",
           {"win_min": [30, 60, 90], "th": [1.0, 1.5, 2.0]}, _skew_exhaust, source="assistant reasoning", author="agent"),
    Family("E-740", "Widest-bar confirmation break",
           "The widest strong-body bar of the recent window marks an aggressive participant; a next bar that closes "
           "beyond its extreme shows no one absorbed it, so follow.",
           {"win_min": [15, 30, 60], "frac": [0.5, 0.7]}, _widest_bar_confirm, source="assistant reasoning", author="agent"),
    Family("E-741", "Efficient-trend one-bar pullback resume",
           "In a smooth, efficient trend (high Kaufman efficiency ratio) a single counter bar is profit-taking, "
           "not reversal; the first bar back with the trend is the entry.",
           {"n_min": [30, 60], "th": [0.2, 0.3, 0.4]}, _er_resume, source="assistant reasoning", author="agent"),
    Family("E-742", "Flatline then expansion bar",
           "A run of near-zero closes means resting liquidity is balanced; the first bar of a decisive move out of "
           "the stall signals one side was pulled and the move follows.",
           {"m": [3, 4, 5], "big_k": [1.5, 2.0]}, _flatline_break, source="assistant reasoning", author="agent"),
    Family("E-743", "Index-dollar same-direction divergence fade",
           "WIN and WDO usually move inversely; when both are up (or both down) on the day relative to their own "
           "typical size, one leg is mispriced against the relation and the market reverts toward it.",
           {"th": [1.0, 1.5, 2.0], "min_after": [60, 120]}, _spread_diverge, source="assistant reasoning", author="agent"),
    Family("E-744", "Prior-session max-volume level cross",
           "The close of the heaviest-volume bar of the previous session is where most inventory changed hands; "
           "after staying on one side, a close through it means that inventory is trapped and price follows.",
           {"away_min": [15, 30, 60]}, _poc_cross, source="auction market theory (volume at price)", author="agent"),
    Family("E-745", "Rising-VWAP touch pullback",
           "When the session VWAP itself is sloping up (down) by a meaningful amount, institutional buying (selling) "
           "is steady, and a dip to VWAP that closes back above (below) is where they add.",
           {"win_min": [30, 60], "k": [0.0003, 0.0006, 0.001]}, _vwap_slope_pullback, source="assistant reasoning", author="agent"),
    Family("E-746", "Decelerating staircase reversal",
           "A run of same-colour bars with shrinking bodies shows buyers (sellers) running out of force; the first "
           "opposite bar closing below the prior close starts the unwind.",
           {"n": [3, 4], "k": [1.0, 2.0, 3.0]}, _decel_stairs, source="assistant reasoning", author="agent"),
    Family("E-747", "Prior-close location bias VWAP entry",
           "A session closing in the top (bottom) of its range leaves overnight holders with a bias; in the early "
           "part of the next session a close back through VWAP in that direction is where the bias gets traded.",
           {"th": [0.7, 0.8], "win_min": [90, 180, 300]}, _prior_loc_bias, source="assistant reasoning", author="agent"),
]
