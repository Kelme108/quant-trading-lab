"""Conveyor batch B-121 (agent, 2026-11-24). Mixed themes: volume-normalised shocks, bar gaps, prior-day bias,
compression, balance-day extremes, VWAP slope, rolling VWAP, exhaustion counts, PTAX windows and the US open."""
from __future__ import annotations

import numpy as np
from b3.esteira import Family


def _thin_shock_fade(ctx, p):
    k, vk = p["k"], p["vol_k"]
    body = np.abs(ctx.c - ctx.o)
    avg = ctx.roll(body, ctx.bars(60), "mean", include_current=False)
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    shock = (body >= k * avg) & (ctx.v < vk * med)
    long = shock & (ctx.c < ctx.o)
    short = shock & (ctx.c > ctx.o)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _gap_hold(ctx, p):
    k = p["k"]
    avg = ctx.roll(ctx.h - ctx.l, ctx.bars(30), "mean", include_current=False)
    ph, pl = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    up = ((ctx.o - ph) >= k * avg) & (ctx.c > ph)
    dn = ((pl - ctx.o) >= k * avg) & (ctx.c < pl)
    return up.astype(int) - dn.astype(int)


def _prev_day_bias_open_cross(ctx, p):
    nb = ctx.bars(p["hold_min"])
    po, pc = ctx.prev_session_value("open"), ctx.prev_session_value("close")
    was_below = ctx.roll((ctx.c < ctx.day_open).astype(float), nb, "min", include_current=False) == 1
    was_above = ctx.roll((ctx.c > ctx.day_open).astype(float), nb, "min", include_current=False) == 1
    long = (pc > po) & was_below & (ctx.c > ctx.day_open)
    short = (pc < po) & was_above & (ctx.c < ctx.day_open)
    return long.astype(int) - short.astype(int)


def _squeeze_release(ctx, p):
    win, q = ctx.bars(p["win_min"]), p["q"]
    hi_p = ctx.roll(ctx.h, win, "max", include_current=False)
    lo_p = ctx.roll(ctx.l, win, "min", include_current=False)
    rng_now = ctx.roll(ctx.h, win, "max") - ctx.roll(ctx.l, win, "min")
    typical = ctx.cached(("sq_typ", win), lambda: ctx.prev_sessions(rng_now, "mean"))
    squeezed = (hi_p - lo_p) < q * typical
    up = squeezed & (ctx.c > hi_p)
    dn = squeezed & (ctx.c < lo_p)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _balance_day_extreme_fade(ctx, p):
    frac = p["frac"]
    sh, sl = ctx.session_high(False), ctx.session_low(False)
    prange = ctx.prev_session_value("high") - ctx.prev_session_value("low")
    narrow = ((sh - sl) < frac * prange) & (ctx.minute >= 11 * 60)
    short = narrow & (ctx.h > sh)
    long = narrow & (ctx.l < sl)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _vwap_slope_flip(ctx, p):
    nb = ctx.bars(p["slope_min"])
    vw = ctx.vwap()
    slope = vw - ctx.prev(vw, nb)
    valid = ~np.isnan(slope)
    up = ctx.cross((slope > 0) & valid) & (ctx.c > vw)
    dn = ctx.cross((slope < 0) & valid) & (ctx.c < vw)
    return up.astype(int) - dn.astype(int)


def _rolling_vs_session_vwap(ctx, p):
    n = ctx.bars(p["win_min"])
    vol = np.maximum(ctx.v, 1.0)
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    rv = ctx.roll(tp * vol, n, "sum") / ctx.roll(vol, n, "sum")
    vw = ctx.vwap()
    valid = ~np.isnan(ctx.prev(rv, 1))
    up = ctx.cross(rv > vw) & valid
    dn = ctx.cross(rv < vw) & valid
    return up.astype(int) - dn.astype(int)


def _close_count_exhaustion(ctx, p):
    n, frac = int(p["n_bars"]), p["frac"]
    need = float(np.ceil(frac * n))
    pc = ctx.prev(ctx.c, 1)
    ups = ctx.roll((ctx.c > pc).astype(float), n, "sum")
    dns = ctx.roll((ctx.c < pc).astype(float), n, "sum")
    short = ups >= need
    long = dns >= need
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _ptax_window_fade(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    t_end = ctx.minute + ctx.tf
    at = np.isin(t_end, [10 * 60 + 10, 11 * 60 + 10, 12 * 60 + 10, 13 * 60 + 10])
    move = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    typical = ctx.cached(("ptax_typ", nb), lambda: ctx.prev_sessions(np.abs(move), "mean"))
    big = at & (np.abs(move) >= k * typical)
    return (big & (move < 0)).astype(int) - (big & (move > 0)).astype(int)


def _us_open_impulse(ctx, p):
    w, k = int(p["win_min"]), p["k"]
    nb = ctx.bars(w)
    t_end = ctx.minute + ctx.tf
    at = (t_end == 10 * 60 + 30 + w) | (t_end == 11 * 60 + 30 + w)
    move = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    typical = ctx.cached(("us_typ", nb), lambda: ctx.prev_sessions(np.abs(move), "mean"))
    ok = at & (np.abs(move) >= k * typical)
    return (ok & (move > 0)).astype(int) - (ok & (move < 0)).astype(int)


FAMILIES = [
    Family("E-1208", "Thin-volume shock bar fade",
           "A bar with an outsized body on below-normal volume for the minute was pushed by few participants; "
           "liquidity providers who took the other side see it revert.",
           {"k": [2.0, 3.0, 4.0], "vol_k": [0.7, 1.0]}, _thin_shock_fade,
           source="assistant reasoning", author="agent"),
    Family("E-1209", "Held bar gap follow",
           "A bar opening beyond the previous bar's extreme and closing still beyond it shows resting orders "
           "overwhelmed at the open of the bar; the imbalance continues.",
           {"k": [0.1, 0.25, 0.5]}, _gap_hold,
           source="assistant reasoning", author="agent"),
    Family("E-1210", "Prior-day bias day-open cross",
           "After an up (down) previous session, returning above (below) the day's open after a spell on the other "
           "side signals that the prior day's holders are back in control.",
           {"hold_min": [10, 20, 30]}, _prev_day_bias_open_cross,
           source="assistant reasoning", author="agent"),
    Family("E-1211", "Volatility squeeze release",
           "When the recent window range is small versus typical for 20 sessions, resting stops pile up on both "
           "sides; the first close beyond the window releases them in that direction.",
           {"win_min": [15, 30, 60], "q": [0.5, 0.7, 0.9]}, _squeeze_release,
           source="assistant reasoning", author="agent"),
    Family("E-1212", "Balance-day extreme fade",
           "On a session whose range after 11:00 is still small against the previous day's, a new session extreme "
           "attracts breakout buyers into a two-sided market; fade the poke.",
           {"frac": [0.5, 0.7, 0.9]}, _balance_day_extreme_fade,
           source="assistant reasoning", author="agent"),
    Family("E-1213", "VWAP slope flip",
           "When the session VWAP turns direction and price sits on that side, the average cost of the day's "
           "volume is moving with price; follow the first bar of agreement.",
           {"slope_min": [10, 20, 30]}, _vwap_slope_flip,
           source="assistant reasoning", author="agent"),
    Family("E-1214", "Rolling VWAP vs session VWAP cross",
           "Recent volume-weighted price crossing the whole-session VWAP shows that recent flow is paid at a "
           "different level than the day's average; follow the change.",
           {"win_min": [15, 30, 60]}, _rolling_vs_session_vwap,
           source="assistant reasoning", author="agent"),
    Family("E-1215", "One-sided close count exhaustion",
           "When nearly every recent close is higher (lower) than the one before, the move is crowded and "
           "late buyers (sellers) have no one left to recruit; fade it.",
           {"n_bars": [8, 10, 12], "frac": [0.75, 0.9]}, _close_count_exhaustion,
           source="assistant reasoning", author="agent"),
    Family("E-1216", "PTAX window move fade",
           "Dollar flow tied to the PTAX fixing windows (10, 11, 12, 13h) is mechanical, not informational; a large "
           "move inside the window tends to revert once the window closes.",
           {"win_min": [10, 15], "k": [1.0, 1.5, 2.0]}, _ptax_window_fade, markets=("WDO",),
           source="assistant reasoning", author="agent"),
    Family("E-1217", "US-open impulse follow",
           "At the New York cash open (10:30 or 11:30 Brasilia time) foreign flow enters; the first minutes' "
           "direction in the index future is followed by the rest of the participants.",
           {"win_min": [5, 10, 15], "k": [0.0, 0.5, 1.0]}, _us_open_impulse, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
