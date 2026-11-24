"""Conveyor batch B-113 (agent, 2026-11-24). Gap retests, efficiency, wick pressure, exhaustion, VWAP slope, late-day flow."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _fvg_retest(ctx, p):
    nb = max(3, ctx.bars(p["lookback_min"]))
    long = np.zeros(ctx.n, bool)
    short = np.zeros(ctx.n, bool)
    for lag in range(3, nb + 1):
        l_j, h_j2 = ctx.prev(ctx.l, lag), ctx.prev(ctx.h, lag + 2)
        h_j, l_j2 = ctx.prev(ctx.h, lag), ctx.prev(ctx.l, lag + 2)
        long |= (l_j > h_j2) & (ctx.l <= l_j) & (ctx.c > h_j2) & (ctx.c > ctx.o)
        short |= (h_j < l_j2) & (ctx.h >= h_j) & (ctx.c < l_j2) & (ctx.c < ctx.o)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _prior_vwap_cross(ctx, p):
    nb = ctx.bars(p["confirm_min"])
    vw = ctx.vwap()
    last = pd.Series(vw).groupby(ctx.day).last()
    last = last.reindex(range(int(ctx.day.max()) + 1)).shift(1).to_numpy()[ctx.day]
    above = ctx.roll((ctx.c > last).astype(float), nb, "min") == 1
    below = ctx.roll((ctx.c < last).astype(float), nb, "min") == 1
    return ctx.cross(above).astype(int) - ctx.cross(below).astype(int)


def _er_onset(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    net = ctx.c - ctx.prev(ctx.c, nb)
    step = np.abs(ctx.c - ctx.prev(ctx.c, 1))
    path = ctx.roll(step, nb, "sum")
    er = np.abs(net) / np.where(path > 0, path, np.nan)
    f = ctx.cross(er >= th)
    return np.where(f, np.sign(net), 0).astype(int)


def _wick_pressure(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    top, bot = np.maximum(ctx.o, ctx.c), np.minimum(ctx.o, ctx.c)
    wick = ctx.roll((bot - ctx.l) - (ctx.h - top), nb, "sum")
    rng = ctx.roll(ctx.h - ctx.l, nb, "sum")
    imb = wick / np.where(rng > 0, rng, np.nan)
    return ctx.cross(imb >= th).astype(int) - ctx.cross(imb <= -th).astype(int)


def _shrinking_run(ctx, p):
    k_run, k = int(p["run"]), p["k"]
    body = np.abs(ctx.c - ctx.o)
    up = ctx.c > ctx.o
    dn = ctx.c < ctx.o
    avg = ctx.roll(body, 20, "mean")
    up_all, dn_all = up.copy(), dn.copy()
    shrink = np.ones(ctx.n, bool)
    for i in range(1, k_run):
        up_all &= ctx.prev(up.astype(float), i) == 1
        dn_all &= ctx.prev(dn.astype(float), i) == 1
    for i in range(0, k_run - 1):
        shrink &= ctx.prev(body, i) < ctx.prev(body, i + 1) if i else body < ctx.prev(body, 1)
    big = ctx.prev(body, k_run - 1) >= k * avg
    cond = shrink & big
    return ctx.cross(dn_all & cond).astype(int) - ctx.cross(up_all & cond).astype(int)


def _vwap_slope(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    vw = ctx.vwap()
    slope = vw / ctx.prev(vw, nb) - 1.0
    typ = ctx.cached(("vslope", nb), lambda: ctx.prev_sessions(np.abs(slope), "mean"))
    long = (slope >= k * typ) & (ctx.c > vw)
    short = (slope <= -k * typ) & (ctx.c < vw)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _late_vwap_fade(ctx, p):
    tail, k = p["tail_min"], p["k"]
    vw = ctx.vwap()
    dev = ctx.c / vw - 1.0
    typ = ctx.cached("devtyp", lambda: ctx.prev_sessions(np.abs(dev), "mean"))
    inwin = ctx.minutes_to_close <= tail
    short = inwin & (dev >= k * typ)
    long = inwin & (dev <= -k * typ)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _dry_then_surge(ctx, p):
    nb, k = ctx.bars(p["dry_min"]), p["k"]
    med = ctx.cached("vmed", lambda: ctx.same_minute(ctx.v, "median"))
    ratio = ctx.v / np.where(med > 0, med, np.nan)
    dry = ctx.roll(ratio, nb, "mean", include_current=False) <= 0.7
    surge = ratio >= k
    long = dry & surge & (ctx.c > ctx.o)
    short = dry & surge & (ctx.c < ctx.o)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _measured_move_fade(ctx, p):
    m = p["m"]
    pc = ctx.prev_session_value("close")
    rg = ctx.prev_session_value("high") - ctx.prev_session_value("low")
    short = ctx.c >= pc + m * rg
    long = ctx.c <= pc - m * rg
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _late_volume_surge(ctx, p):
    win, k = p["win_min"], p["k"]
    med = ctx.cached("vmed", lambda: ctx.same_minute(ctx.v, "median"))
    ratio = ctx.v / np.where(med > 0, med, np.nan)
    solid = np.abs(ctx.c - ctx.o) >= 0.5 * (ctx.h - ctx.l)
    base = (ctx.minutes_to_close <= win) & (ratio >= k) & solid
    long = base & (ctx.c > ctx.o)
    short = base & (ctx.c < ctx.o)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


W = ("WIN",)

FAMILIES = [
    Family("E-1128", "Fair-value-gap retest follow",
           "A three-bar gap (bar j low above the high two bars before) marks one-sided aggressive flow; a later "
           "pullback into the gap that closes back out in the gap's direction means the late side is still absent.",
           {"lookback_min": [10, 20, 30]}, _fvg_retest, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1129", "Prior-session VWAP hold-cross follow",
           "Yesterday's closing VWAP is the average cost of the last session's participants; a sustained close "
           "above/below it shows which side holds the better average today.",
           {"confirm_min": [5, 10, 20]}, _prior_vwap_cross, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1130", "Efficiency-ratio onset follow",
           "When net displacement becomes a large share of path length (Kaufman efficiency), a directional "
           "participant is working an order; follow the first bar where efficiency crosses the threshold.",
           {"win_min": [20, 30, 60], "th": [0.5, 0.6, 0.7]}, _er_onset, markets=W,
           source="assistant reasoning (Kaufman efficiency ratio)", author="agent"),
    Family("E-1131", "Wick-pressure imbalance follow",
           "Persistently longer lower wicks than upper wicks mean sellers are repeatedly absorbed by passive "
           "buyers; the imbalance crossing a threshold signals who is on the other side of the tape.",
           {"win_min": [15, 30, 60], "th": [0.3, 0.4, 0.5]}, _wick_pressure, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1132", "Shrinking-body run exhaustion fade",
           "A run of same-colour bars whose bodies keep shrinking after a big first bar shows momentum buyers "
           "(or sellers) running out of follow-through; fade it.",
           {"run": [3, 4], "k": [0.8, 1.2, 1.6]}, _shrinking_run, markets=W, source="assistant reasoning",
           author="agent"),
    Family("E-1133", "VWAP slope acceleration follow",
           "A session VWAP rising faster than usual with price above it means volume-weighted cost is migrating "
           "up; position takers on the wrong side must chase.",
           {"win_min": [30, 60], "k": [1.0, 1.5, 2.0]}, _vwap_slope, markets=W, source="assistant reasoning",
           author="agent"),
    Family("E-1134", "Closing-hour VWAP stretch fade",
           "In the last hour intraday day-traders flatten toward the day's average; a stretch from VWAP larger than "
           "usual in that window tends to be unwound by position squaring.",
           {"tail_min": [30, 45, 60], "k": [1.5, 2.0, 2.5]}, _late_vwap_fade, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1135", "Volume dry-up then expansion bar follow",
           "After a stretch of well below-normal volume, one bar of heavy volume with a clear colour is the first "
           "sign of an informed participant entering a thin book; follow it.",
           {"dry_min": [15, 30, 45], "k": [1.5, 2.0, 3.0]}, _dry_then_surge, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1136", "Prior-range measured-move fade",
           "A move from the previous close equal to a fraction of yesterday's whole range is a move the market "
           "rarely sustains without news; fade the first touch of that distance.",
           {"m": [0.3, 0.5, 0.75]}, _measured_move_fade, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1137", "Closing-flow volume surge follow",
           "Heavy-volume, full-bodied bars in the last 1-2 hours come from institutions needing to finish "
           "orders before the close; follow the direction of that urgency.",
           {"win_min": [60, 90, 120], "k": [1.5, 2.0, 3.0]}, _late_volume_surge, markets=W,
           source="assistant reasoning", author="agent"),
]
