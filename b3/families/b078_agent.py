"""Conveyor batch B-078 (agent, 2026-11-23). Mixed: minute seasonality, PTAX windows, liquidity-impact, volume-bar and clock-mark ideas."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _ff(x):
    return np.nan_to_num(np.asarray(x, float), nan=0.0)


def _minute_seasonal_sign(ctx, p):
    q = p["q"]
    sg = np.sign(ctx.c - ctx.o)
    sm = ctx.cached("sm_sign", lambda: ctx.same_minute(sg, "mean"))
    long = sm >= q
    short = sm <= -q
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _seasonal_path_dev(ctx, p):
    k = p["k"]
    r = ctx.c / ctx.day_open - 1.0
    seas = ctx.cached("seas_path", lambda: ctx.same_minute(r, "mean"))
    typ = ctx.cached("seas_typ", lambda: ctx.same_minute(np.abs(r), "mean"))
    dev = r - seas
    short = (dev >= k * typ) & (typ > 0)
    long = (dev <= -k * typ) & (typ > 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _equal_close_stall(ctx, p):
    eq, k = int(p["eq_bars"]), p["k"]
    nb = ctx.bars(10)
    flat = (ctx.c == ctx.prev(ctx.c, 1)).astype(float)
    stalled = ctx.roll(flat, eq, "min") == 1
    move = ctx.c / ctx.prev(ctx.c, nb + eq) - 1.0
    typ = ctx.cached(("abs_mv_eq", nb, eq), lambda: ctx.prev_sessions(np.abs(move), "mean"))
    long = stalled & (move >= k * typ)
    short = stalled & (move <= -k * typ)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _heavy_bar_range_break(ctx, p):
    age = p["min_age"]
    g = pd.Series(ctx.v).groupby(ctx.day)
    vmax = g.cummax().to_numpy()
    is_max = ctx.v >= vmax
    hi_at = pd.Series(np.where(is_max, ctx.h, np.nan)).groupby(ctx.day).ffill().to_numpy()
    lo_at = pd.Series(np.where(is_max, ctx.l, np.nan)).groupby(ctx.day).ffill().to_numpy()
    old = ctx.bar_in_day * ctx.tf >= age
    long = old & (ctx.c > hi_at)
    short = old & (ctx.c < lo_at)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _impact_spike_fade(ctx, p):
    n, k = ctx.bars(p["n_min"]), p["k"]
    mv = ctx.c / ctx.prev(ctx.c, n) - 1.0
    vs = ctx.roll(ctx.v, n, "sum")
    imp = np.abs(mv) / (vs + 1.0)
    typ = ctx.cached(("imp_typ", n), lambda: ctx.same_minute(imp, "median"))
    spike = (imp >= k * typ) & (typ > 0) & (np.abs(mv) > 0)
    short = spike & (mv > 0)
    long = spike & (mv < 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _yesterday_echo(ctx, p):
    nb, k = ctx.bars(p["n_min"]), p["k"]
    mv = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    y = ctx.cached(("yday_mv", nb), lambda: ctx.same_minute(mv, "mean", n=1))
    typ = ctx.cached(("abs_mv_echo", nb), lambda: ctx.prev_sessions(np.abs(mv), "mean"))
    long = (mv >= k * typ) & (y >= k * typ)
    short = (mv <= -k * typ) & (y <= -k * typ)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _ptax_window_fade(ctx, p):
    w, k = int(p["window_min"]), p["k"]
    nb = ctx.bars(w)
    end_min = ctx.minute + ctx.tf
    at_end = np.isin(end_min, [h * 60 + w for h in (10, 11, 12, 13)])
    mv = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    typ = ctx.cached(("ptax_typ", nb), lambda: ctx.same_minute(np.abs(mv), "mean"))
    short = at_end & (mv >= k * typ) & (typ > 0)
    long = at_end & (mv <= -k * typ) & (typ > 0)
    return long.astype(int) - short.astype(int)


def _vwap_side_clock(ctx, p):
    sp, k = int(p["spacing_min"]), p["k"]
    end_min = ctx.minute + ctx.tf
    mark = (end_min % sp == 0) & (end_min >= 600) & (end_min <= 1020)
    vw = ctx.vwap()
    dist = (ctx.c - vw) / vw
    nb = ctx.bars(30)
    mv = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    typ = ctx.cached(("abs_mv_clock", nb), lambda: ctx.prev_sessions(np.abs(mv), "mean"))
    long = mark & (dist >= k * typ)
    short = mark & (dist <= -k * typ)
    return long.astype(int) - short.astype(int)


def _tweezer(ctx, p):
    f, nb = p["tol_frac"], ctx.bars(p["look_min"])
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    o1, c1 = ctx.prev(ctx.o, 1), ctx.prev(ctx.c, 1)
    rng1 = h1 - l1
    hmax = ctx.prev(ctx.roll(ctx.h, nb, "max"), 1)
    lmin = ctx.prev(ctx.roll(ctx.l, nb, "min"), 1)
    short = (np.abs(ctx.h - h1) <= f * rng1) & (rng1 > 0) & (c1 > o1) & (ctx.c < ctx.o) & (h1 >= hmax)
    long = (np.abs(ctx.l - l1) <= f * rng1) & (rng1 > 0) & (c1 < o1) & (ctx.c > ctx.o) & (l1 <= lmin)
    return long.astype(int) - short.astype(int)


def _heavy_bar_trap(ctx, p):
    k = p["vol_k"]
    med = ctx.cached("vol_med_trap", lambda: ctx.same_minute(ctx.v, "median"))
    heavy = (ctx.v >= k * med) & (med > 0)
    up_h = _ff(ctx.prev((heavy & (ctx.c > ctx.o)).astype(float), 1)) == 1
    dn_h = _ff(ctx.prev((heavy & (ctx.c < ctx.o)).astype(float), 1)) == 1
    o1 = ctx.prev(ctx.o, 1)
    short = up_h & (ctx.c < o1)
    long = dn_h & (ctx.c > o1)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-778", "Minute-of-day seasonal sign",
           "If the same minute of the day closed the same colour in most of the last 20 sessions, recurring scheduled "
           "flows (fixings, rebalancing, opening of other markets) at that clock time may repeat; follow the habit.",
           {"q": [0.3, 0.4, 0.5]}, _minute_seasonal_sign, source="assistant reasoning", author="assistant" if False else "agent"),
    Family("E-779", "Seasonal-path deviation fade",
           "Compare the day's return from the open with the average path of the last 20 sessions at the same minute; "
           "a large excess over that typical path is overshoot against the usual flow, so fade it.",
           {"k": [0.75, 1.0, 1.5]}, _seasonal_path_dev, source="assistant reasoning", author="agent"),
    Family("E-780", "Equal-close stall after a move",
           "Bars closing exactly on the previous close show the aggressors stepping away after a move; "
           "the prior direction resumes once the pause passes.",
           {"eq_bars": [1, 2, 3], "k": [0.5, 1.0, 1.5]}, _equal_close_stall, source="assistant reasoning", author="agent"),
    Family("E-781", "Session heavy-volume bar range break",
           "The session's highest-volume bar so far marks where most positions were built; a close beyond its range "
           "leaves those holders offside and they must exit in the break direction.",
           {"min_age": [30, 60, 90]}, _heavy_bar_range_break, source="assistant reasoning", author="agent"),
    Family("E-782", "Price-impact spike fade",
           "A move that needed little volume per point (impact far above the usual at that minute) is a liquidity "
           "vacuum, not conviction; it tends to retrace once liquidity returns.",
           {"n_min": [5, 10, 15], "k": [2.0, 3.0]}, _impact_spike_fade, source="Amihud illiquidity (assistant adaptation)",
           author="agent"),
    Family("E-783", "Yesterday-window echo follow",
           "When the last window's move is large and the same clock window moved the same way yesterday, a recurring "
           "participant flow is probably in progress; follow it.",
           {"n_min": [15, 30, 60], "k": [0.5, 1.0]}, _yesterday_echo, source="assistant reasoning", author="agent"),
    Family("E-784", "PTAX window move fade",
           "Dollar flows around the four PTAX fixing windows (10, 11, 12, 13h) push the price temporarily; after the "
           "window ends the push is not information and tends to fade.",
           {"window_min": [10, 15], "k": [0.25, 0.5, 1.0]}, _ptax_window_fade, markets=("WDO",),
           source="assistant reasoning (PTAX fixing windows)", author="agent"),
    Family("E-785", "VWAP side at clock marks",
           "At round clock marks, being clearly on one side of the session VWAP means the volume-weighted average "
           "holder is on the other side and the drift keeps that side; follow it.",
           {"spacing_min": [60, 90, 120], "k": [0.25, 0.5, 0.75]}, _vwap_side_clock, source="assistant reasoning",
           author="agent"),
    Family("E-786", "Tweezer reversal at a window extreme",
           "Two consecutive bars stopping at the same high (low) after the first was strong marks a defended level "
           "at the window extreme; fade the second bar's reversal colour.",
           {"tol_frac": [0.0, 0.1, 0.2], "look_min": [15, 30, 60]}, _tweezer, source="candlestick literature (tweezer)",
           author="agent"),
    Family("E-787", "Heavy-volume bar trap",
           "A heavy-volume directional bar fully retraced by the next bar's close through its open traps the "
           "aggressors; the retrace direction continues.",
           {"vol_k": [1.5, 2.0, 3.0]}, _heavy_bar_trap, source="assistant reasoning", author="agent"),
]
