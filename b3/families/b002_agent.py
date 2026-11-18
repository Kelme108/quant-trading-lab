"""Conveyor batch B-002 (agent, 2026-11-17). Ten WIN ideas: bar shape, level retests, flow divergence, swing structure, late-day timing."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _ffill(ctx, x):
    """Forward-fill inside the session (causal)."""
    return pd.Series(np.asarray(x, float)).groupby(ctx.day).ffill().to_numpy()


def _rng_med(ctx):
    return ctx.cached("rng_med_same_minute", lambda: ctx.same_minute(ctx.h - ctx.l, "median"))


# E-009 ---------------------------------------------------------------------------------------
def _pin_bar(ctx, p):
    wf = p["wick_frac"]
    rng = ctx.h - ctx.l
    med = _rng_med(ctx)
    body = np.abs(ctx.c - ctx.o)
    lw = np.minimum(ctx.o, ctx.c) - ctx.l
    uw = ctx.h - np.maximum(ctx.o, ctx.c)
    ok = (rng > 0) & (rng >= med) & (body <= 0.25 * rng)
    long = ok & (lw >= wf * rng)
    short = ok & (uw >= wf * rng)
    return long.astype(int) - short.astype(int)


# E-010 ---------------------------------------------------------------------------------------
def _strong_close(ctx, p):
    k = p["k"]
    rng = ctx.h - ctx.l
    med = _rng_med(ctx)
    body = np.abs(ctx.c - ctx.o)
    ok = (rng > 0) & (rng >= k * med) & (body >= 0.7 * rng)
    long = ok & (ctx.c > ctx.o) & ((ctx.h - ctx.c) <= 0.1 * rng)
    short = ok & (ctx.c < ctx.o) & ((ctx.c - ctx.l) <= 0.1 * rng)
    return long.astype(int) - short.astype(int)


# E-011 ---------------------------------------------------------------------------------------
def _break_retest(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    m = ctx.bars(30)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    bu = ctx.cross(ctx.c > hi)
    bd = ctx.cross(ctx.c < lo)
    lvl_u = _ffill(ctx, np.where(bu, hi, np.nan))
    t_u = _ffill(ctx, np.where(bu, ctx.bar_in_day, np.nan))
    lvl_d = _ffill(ctx, np.where(bd, lo, np.nan))
    t_d = _ffill(ctx, np.where(bd, ctx.bar_in_day, np.nan))
    age_u = ctx.bar_in_day - t_u
    age_d = ctx.bar_in_day - t_d
    long = (age_u >= 2) & (age_u <= m) & (ctx.l <= lvl_u) & (ctx.c > lvl_u)
    short = (age_d >= 2) & (age_d <= m) & (ctx.h >= lvl_d) & (ctx.c < lvl_d)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-012 ---------------------------------------------------------------------------------------
def _clv_divergence(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    rng = ctx.h - ctx.l
    clv = np.where(rng > 0, ((ctx.c - ctx.l) - (ctx.h - ctx.c)) / np.where(rng > 0, rng, 1.0), 0.0)
    flow = ctx.roll(clv * ctx.v, nb, "sum")
    vol = ctx.roll(ctx.v, nb, "sum")
    f = flow / np.where(vol > 0, vol, np.nan)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    long = (ctx.l < lo) & (f > 0.1)
    short = (ctx.h > hi) & (f < -0.1)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-013 ---------------------------------------------------------------------------------------
def _pause_extreme(ctx, p):
    nb = ctx.bars(p["pause_min"])
    sh = ctx.session_high(include_current=False)
    sl = ctx.session_low(include_current=False)
    first = ctx.bar_in_day == 0
    newh = first | (ctx.h > sh)
    newl = first | (ctx.l < sl)
    last_h = ctx.prev(_ffill(ctx, np.where(newh, ctx.bar_in_day, np.nan)), 1)
    last_l = ctx.prev(_ffill(ctx, np.where(newl, ctx.bar_in_day, np.nan)), 1)
    long = (ctx.c > sh) & ((ctx.bar_in_day - last_h) >= nb)
    short = (ctx.c < sl) & ((ctx.bar_in_day - last_l) >= nb)
    return long.astype(int) - short.astype(int)


# E-014 ---------------------------------------------------------------------------------------
def _run_engulf(ctx, p):
    k = int(p["run_bars"])
    pc = ctx.prev(ctx.c, 1)
    dn = (ctx.c < pc).astype(float)
    up = (ctx.c > pc).astype(float)
    dn_run = ctx.roll(dn, k, "min", include_current=False) == 1
    up_run = ctx.roll(up, k, "min", include_current=False) == 1
    long = dn_run & (ctx.c > ctx.prev(ctx.h, 1)) & (ctx.c > ctx.o)
    short = up_run & (ctx.c < ctx.prev(ctx.l, 1)) & (ctx.c < ctx.o)
    return long.astype(int) - short.astype(int)


# E-015 ---------------------------------------------------------------------------------------
def _late_trend_break(ctx, p):
    w = p["window_min"]
    late = (ctx.minutes_to_close <= w) & (ctx.minutes_to_close > 10)
    r = ctx.c / ctx.day_open - 1.0
    typ = ctx.cached("abs_ret_same_minute", lambda: ctx.same_minute(np.abs(r), "mean"))
    nb = ctx.bars(15)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    long = late & (r > typ) & ctx.cross(ctx.c > hi)
    short = late & (r < -typ) & ctx.cross(ctx.c < lo)
    return long.astype(int) - short.astype(int)


# E-016 ---------------------------------------------------------------------------------------
def _double_test_hold(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    rb = ctx.bars(5)
    tol = 0.25 * _rng_med(ctx)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    rlo = ctx.roll(ctx.l, rb, "min", include_current=False)
    rhi = ctx.roll(ctx.h, rb, "max", include_current=False)
    long = (rlo > lo + 2 * tol) & (ctx.l <= lo + tol) & (ctx.l >= lo) & (ctx.c > ctx.o)
    short = (rhi < hi - 2 * tol) & (ctx.h >= hi - tol) & (ctx.h <= hi) & (ctx.c < ctx.o)
    return long.astype(int) - short.astype(int)


# E-017 ---------------------------------------------------------------------------------------
def _flag_break(ctx, p):
    k, fb = p["impulse_k"], int(p["flag_bars"])
    rng = ctx.h - ctx.l
    med = _rng_med(ctx)
    L = fb + 1
    bh, bl, bo, bc = ctx.prev(ctx.h, L), ctx.prev(ctx.l, L), ctx.prev(ctx.o, L), ctx.prev(ctx.c, L)
    br, bm = ctx.prev(rng, L), ctx.prev(med, L)
    big = (br > 0) & (br >= k * bm)
    up = big & (bc > bo) & ((bh - bc) <= 0.3 * br)
    dn = big & (bc < bo) & ((bc - bl) <= 0.3 * br)
    flag_up = np.ones(ctx.n, bool)
    flag_dn = np.ones(ctx.n, bool)
    for j in range(1, fb + 1):
        hj, lj, rj = ctx.prev(ctx.h, j), ctx.prev(ctx.l, j), ctx.prev(rng, j)
        small = rj <= 0.5 * br
        flag_up &= small & (hj <= bh) & (lj >= bl + 0.4 * br)
        flag_dn &= small & (lj >= bl) & (hj <= bh - 0.4 * br)
    long = up & flag_up & (ctx.c > bh)
    short = dn & flag_dn & (ctx.c < bl)
    return long.astype(int) - short.astype(int)


# E-018 ---------------------------------------------------------------------------------------
def _last_two(ctx, ev, val):
    last = _ffill(ctx, np.where(ev, val, np.nan))
    idx = np.flatnonzero(ev)
    prev_ev = pd.Series(val[idx]).groupby(ctx.day[idx]).shift(1).to_numpy()
    arr = np.full(ctx.n, np.nan)
    arr[idx] = prev_ev
    return last, _ffill(ctx, arr)


def _structure_break(ctx, p):
    w = int(p["width"])
    cand_l, cand_h = ctx.prev(ctx.l, w), ctx.prev(ctx.h, w)
    left_l = ctx.prev(ctx.roll(ctx.l, w, "min", include_current=False), w)
    left_h = ctx.prev(ctx.roll(ctx.h, w, "max", include_current=False), w)
    right_l = ctx.roll(ctx.l, w, "min")
    right_h = ctx.roll(ctx.h, w, "max")
    ev_l = (cand_l < left_l) & (cand_l <= right_l)
    ev_h = (cand_h > left_h) & (cand_h >= right_h)
    pl, pl_prev = _last_two(ctx, ev_l, cand_l)
    ph, ph_prev = _last_two(ctx, ev_h, cand_h)
    long = ctx.cross(ctx.c > ph) & (pl > pl_prev)
    short = ctx.cross(ctx.c < pl) & (ph < ph_prev)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-009", "Pin-bar rejection",
           "A bar of at least typical range with a small body and a long wick on one side shows that aggressive orders "
           "pushed the price there and were absorbed by resting liquidity; the absorbed side is exhausted, follow the "
           "close away from the wick.",
           {"wick_frac": [0.55, 0.65, 0.75]}, _pin_bar, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-010", "Strong-close bar follow",
           "A bar of typical-or-larger range that is almost all body and closes at its extreme means aggressive orders "
           "were still being filled at the bell of the bar; a parent order still being worked continues into the next "
           "bars, so follow it.",
           {"k": [0.75, 1.0, 1.5]}, _strong_close, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-011", "Break-and-retest",
           "After a close beyond the recent high/low, a pullback that touches the broken level and closes back on the "
           "breakout side shows old resistance acting as support (late sellers covering, missed buyers stepping in); "
           "enter on the retest rather than the break.",
           {"lookback_min": [20, 30, 60]}, _break_retest, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-012", "Close-location flow divergence",
           "A new recent low while the volume-weighted close location of the same window is positive means bars keep "
           "closing high on volume: passive buyers absorb the sellers making the low; fade the extreme.",
           {"lookback_min": [15, 30, 60]}, _clv_divergence, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-013", "Session extreme after a pause",
           "When the session high/low has stood untouched for a long time, stops and breakout orders pile up beyond it; "
           "the first close through it after the pause releases them, follow the break.",
           {"pause_min": [30, 60, 90]}, _pause_extreme, markets=("WIN",),
           source="Osler, Currency orders and exchange rate dynamics (stop-loss clustering beyond levels) "
                  "https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.html",
           author="agent"),
    Family("E-014", "Engulfing reversal after a run",
           "After several consecutive closes in one direction, a bar that reverses and closes beyond the previous bar's "
           "extreme shows the short-term momentum traders are trapped and the other side took control; follow the "
           "reversal.",
           {"run_bars": [3, 4, 5]}, _run_engulf, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-015", "Late-day trend breakout",
           "Late-informed traders and rebalancers finish their orders near the close in the direction of the day; in the "
           "last hour or two, on a day already moving more than usual, follow a break of the 15-minute high/low in the "
           "day's direction.",
           {"window_min": [60, 90, 120]}, _late_trend_break, markets=("WIN",),
           source="Intraday Momentum: The First Half-Hour Return Predicts the Last Half-Hour Return "
                  "https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/",
           author="agent"),
    Family("E-016", "Double test that holds",
           "A return to the recent low (high) after moving away, that does not break it and closes in the bounce "
           "direction, shows resting orders still defend the level and sellers cannot push through; trade the hold.",
           {"lookback_min": [20, 30, 60]}, _double_test_hold, markets=("WIN",), source="assistant reasoning",
           author="agent"),
    Family("E-017", "Flag after an impulse bar",
           "A large impulse bar followed by small bars that hold its far half means the impulse side is not being "
           "unwound; a close beyond the impulse bar's extreme resumes the move as the pause traders give up.",
           {"impulse_k": [1.5, 2.0, 2.5], "flag_bars": [2, 3]}, _flag_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-018", "Swing-structure break",
           "After a higher swing low (lower swing high), a close through the last swing high (low) completes an intraday "
           "trend structure that swing traders watch; their entries and the stops of the counter side push it on.",
           {"width": [2, 3, 4]}, _structure_break, markets=("WIN",), source="assistant reasoning", author="agent"),
]
