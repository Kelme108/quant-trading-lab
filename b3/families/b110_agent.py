"""Conveyor batch B-110 (agent, 2026-11-24). Mixed themes: time-of-day drift, clock anchors, event boxes, chains of
inside bars, extreme-count pressure, yesterday's path, MA ribbon, Elder ray, ease of movement, AO saucer."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from b3.esteira import Family


def _ud(long, short):
    return np.asarray(long, bool).astype(int) - np.asarray(short, bool).astype(int)


def _same_minute_drift(ctx, p):
    hb = ctx.bars(p["horizon_min"])
    k = p["t_min"]

    def build():
        nxt = np.full(ctx.n, np.nan)
        if hb < ctx.n:
            nxt[:-hb] = ctx.c[hb:]
            same = np.zeros(ctx.n, bool)
            same[:-hb] = ctx.day[hb:] == ctx.day[:-hb]
            nxt = np.where(same, nxt, np.nan)
        ret = np.nan_to_num(nxt / ctx.c - 1.0)
        m = ctx.same_minute(ret, "mean")
        m2 = ctx.same_minute(ret * ret, "mean")
        sd = np.sqrt(np.maximum(m2 - m * m, 0.0))
        return np.where(sd > 0, m / (sd / math.sqrt(20) + 1e-18), 0.0)

    t = np.nan_to_num(ctx.cached(("smd", hb), build))
    return _ud(ctx.cross(t > k), ctx.cross(t < -k))


def _clock_anchor_cross(ctx, p):
    a, nb = p["anchor_min"], ctx.bars(p["away_min"])
    m = ctx.minute >= a
    first = pd.Series(np.where(m, ctx.o, np.nan)).groupby(ctx.day).transform("first").to_numpy()
    av = np.where(m, first, np.nan)
    below = (ctx.c < av).astype(float)
    above = (ctx.c > av).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    return _ud(was_below & (ctx.c > av), was_above & (ctx.c < av))


def _nested_chain_break(ctx, p):
    k = int(p["k"])
    ok = np.ones(ctx.n, bool)
    for i in range(1, k + 1):
        ok &= (ctx.prev(ctx.h, i) <= ctx.prev(ctx.h, i + 1)) & (ctx.prev(ctx.l, i) >= ctx.prev(ctx.l, i + 1))
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    return _ud(ok & (ctx.c > h1), ok & (ctx.c < l1))


def _us_open_box(ctx, p):
    t0, win = p["start_min"], p["win_min"]
    inbox = (ctx.minute >= t0) & (ctx.minute < t0 + 15)
    g = pd.DataFrame({"d": ctx.day, "h": np.where(inbox, ctx.h, np.nan), "l": np.where(inbox, ctx.l, np.nan)})
    bh = g.groupby("d")["h"].transform("max").to_numpy()
    bl = g.groupby("d")["l"].transform("min").to_numpy()
    active = (ctx.minute >= t0 + 15) & (ctx.minute < t0 + 15 + win)
    return _ud(ctx.cross(active & (ctx.c > bh)), ctx.cross(active & (ctx.c < bl)))


def _extreme_count_pressure(ctx, p):
    nb = ctx.bars(p["win_min"])
    thr = max(2, int(math.ceil(p["frac"] * nb)))
    nh = (ctx.h > ctx.session_high(False)).astype(float)
    nl = (ctx.l < ctx.session_low(False)).astype(float)
    ch = ctx.roll(nh, nb, "sum")
    cl = ctx.roll(nl, nb, "sum")
    return _ud(ctx.cross(ch >= thr), ctx.cross(cl >= thr))


def _yesterday_path_cross(ctx, p):
    nb = ctx.bars(p["away_min"])
    yp = ctx.cached("yday_path", lambda: ctx.same_minute(ctx.c, "mean", n=1))
    below = (ctx.c < yp).astype(float)
    above = (ctx.c > yp).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    return _ud(was_below & (ctx.c > yp), was_above & (ctx.c < yp))


def _ma_ribbon(ctx, p):
    b = p["base_min"]
    e = [ctx.cached(("ema", s), lambda s=s: ctx.ema(ctx.c, s)) for s in [ctx.bars(b * m) for m in (1, 2, 4, 8)]]
    bull = (e[0] > e[1]) & (e[1] > e[2]) & (e[2] > e[3])
    bear = (e[0] < e[1]) & (e[1] < e[2]) & (e[2] < e[3])
    return _ud(ctx.cross(bull), ctx.cross(bear))


def _elder_ray(ctx, p):
    s = ctx.bars(p["ema_min"])
    ema = ctx.cached(("ema", s), lambda: ctx.ema(ctx.c, s))
    bull_pw, bear_pw = ctx.h - ema, ctx.l - ema
    up = (ema > ctx.prev(ema, 1)) & (bear_pw < 0) & (bear_pw > ctx.prev(bear_pw, 1)) & (ctx.c > ctx.o)
    dn = (ema < ctx.prev(ema, 1)) & (bull_pw > 0) & (bull_pw < ctx.prev(bull_pw, 1)) & (ctx.c < ctx.o)
    return _ud(ctx.cross(up), ctx.cross(dn))


def _ease_of_movement(ctx, p):
    nb = ctx.bars(p["win_min"])
    mid = (ctx.h + ctx.l) / 2.0
    dm = np.nan_to_num(mid - ctx.prev(mid, 1))
    eom = np.where(ctx.v > 0, dm * (ctx.h - ctx.l) / np.where(ctx.v > 0, ctx.v, 1.0), 0.0)
    s = ctx.roll(eom, nb, "mean")
    return _ud(ctx.cross(s > 0), ctx.cross(s < 0))


def _ao_saucer(ctx, p):
    f = ctx.bars(p["fast_min"])
    sl = max(f + 1, ctx.bars(p["fast_min"] * p["slow_mult"]))
    mid = (ctx.h + ctx.l) / 2.0
    ao = ctx.roll(mid, f, "mean") - ctx.roll(mid, sl, "mean")
    a1, a2, a3 = ctx.prev(ao, 1), ctx.prev(ao, 2), ctx.prev(ao, 3)
    up = (ao > 0) & (a1 > 0) & (ao > a1) & (a1 < a2) & (a2 < a3)
    dn = (ao < 0) & (a1 < 0) & (ao < a1) & (a1 > a2) & (a2 > a3)
    return _ud(up, dn)


FAMILIES = [
    Family("E-1098", "Same-minute drift persistence",
           "Intraday returns show time-of-day periodicity: a clock slot whose forward return was consistently one "
           "sign over the last 20 sessions (t-stat) keeps attracting the same-side flow (recurring institutional "
           "and hedging orders); trade the historical sign when the t-stat first exceeds the threshold.",
           {"horizon_min": [15, 30, 60], "t_min": [1.5, 2.0, 2.5]}, _same_minute_drift,
           source="assistant reasoning", author="agent"),
    Family("E-1099", "Clock-anchor level cross",
           "The price at a fixed clock time (10:00, 11:00, 12:00) is an anchor many traders reference as the "
           "morning/midday reference; after the price stays on one side for a while, the first close across it "
           "shows the other side taking control; follow it.",
           {"anchor_min": [600, 660, 720], "away_min": [5, 10, 20]}, _clock_anchor_cross,
           source="assistant reasoning", author="agent"),
    Family("E-1100", "Nested inside-bar chain break",
           "A chain of successively nested bars is a deeper compression than one inside bar: resting stops pile "
           "up beyond the mother bar's edges and a close beyond the last bar releases them.",
           {"k": [2, 3, 4]}, _nested_chain_break, source="assistant reasoning", author="agent"),
    Family("E-1101", "US-open box edge break",
           "Orders around the US cash open and data releases arrive in the 15 minutes after 10:30/11:00/11:30; "
           "the box of those minutes marks where foreign flow was absorbed, and a close beyond its edge in the "
           "following hours shows that flow winning; follow.",
           {"start_min": [630, 660, 690], "win_min": [60, 120, 180]}, _us_open_box, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1102", "Session-extreme count pressure",
           "When most of the last bars each print a new session high (or low), buyers (sellers) are being "
           "chased repeatedly by late participants and stops; the persistent pressure keeps going, so follow the "
           "first time the count reaches the threshold.",
           {"win_min": [15, 30, 60], "frac": [0.5, 0.7, 0.9]}, _extreme_count_pressure, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1103", "Yesterday's-path cross",
           "The close of the previous session at the same clock minute is a moving reference for anyone anchoring "
           "on yesterday; staying on one side then crossing signals today's balance flipping versus yesterday; "
           "follow the cross.",
           {"away_min": [10, 20, 30]}, _yesterday_path_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1104", "Four-EMA ribbon onset",
           "When four exponential averages with doubling spans fall into strict order, trends of every horizon "
           "agree and trend-following funds add; follow the first bar the ordering completes.",
           {"base_min": [5, 10, 15]}, _ma_ribbon, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1105", "Elder-ray pullback in a rising EMA",
           "In a trending EMA, a bar whose low dips under the EMA but where the bear power is already improving "
           "and the close is up shows sellers losing force against the trend; buy it (mirror for sells).",
           {"ema_min": [13, 26, 39]}, _elder_ray, markets=("WIN",), source="Elder, Bull and Bear Power (assistant reasoning)", author="agent"),
    Family("E-1106", "Ease-of-movement zero cross",
           "Ease of movement relates price change to volume per unit range: sustained positive values mean price "
           "advances with little resistance; a zero cross to positive means liquidity on the offer thinned out; follow.",
           {"win_min": [10, 20, 30]}, _ease_of_movement, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1107", "Awesome-oscillator saucer",
           "Inside an up-momentum regime (fast median mean above slow), two falling oscillator bars followed by a "
           "rising bar mark a pause where dip buyers re-enter; the saucer resumes the trend (mirror for sells).",
           {"fast_min": [5, 10, 15], "slow_mult": [5, 7, 10]}, _ao_saucer, markets=("WIN",),
           source="Williams, Awesome Oscillator saucer (assistant reasoning)", author="agent"),
]
