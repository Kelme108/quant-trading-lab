"""Conveyor batch B-059 (agent, 2026-11-22). Multi-day average-extreme band pokes, projected-range levels and a few
oscillator/candle hooks not yet screened (ZLEMA, CMO, RVI, StochRSI, stochastic CG, PVT, ribbon, piercing)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _ud(ctx, long, short):
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-588 ----------------------------------------------------------------------------------------
def _avg_extreme_band(ctx, p):
    n, buf = int(p["n"]), float(p["buf"])
    nd = int(ctx.day.max()) + 1
    hs = pd.Series(ctx.h).groupby(ctx.day).max().reindex(range(nd))
    ls = pd.Series(ctx.l).groupby(ctx.day).min().reindex(range(nd))

    def lvl(s):
        return s.rolling(n, min_periods=n).mean().shift(1).to_numpy()[ctx.day]

    mh, ml, rg = lvl(hs), lvl(ls), lvl(hs - ls)
    top, bot = mh + buf * rg, ml - buf * rg
    short = (ctx.h > top) & (ctx.c < top)
    long = (ctx.l < bot) & (ctx.c > bot)
    return _ud(ctx, long & ~short, short & ~long)


# E-589 ----------------------------------------------------------------------------------------
def _zlema_turn(ctx, p):
    span = max(2, ctx.bars(p["span_min"]))
    ms = float(p["min_slope"])
    lag = max(1, (span - 1) // 2)
    x = ctx.c + (ctx.c - ctx.prev(ctx.c, lag))
    z = ctx.ema(x, span)
    slope = (z - ctx.prev(z, 1)) / ctx.c
    up = (slope > ms) & (ctx.c > z)
    dn = (slope < -ms) & (ctx.c < z)
    return _ud(ctx, up, dn)


# E-590 ----------------------------------------------------------------------------------------
def _cmo_fade(ctx, p):
    n, th = max(3, ctx.bars(p["win_min"])), float(p["th"])
    d = ctx.c - ctx.prev(ctx.c, 1)
    up = np.where(np.isnan(d), np.nan, np.maximum(d, 0.0))
    dn = np.where(np.isnan(d), np.nan, np.maximum(-d, 0.0))
    su, sd = ctx.roll(up, n, "sum"), ctx.roll(dn, n, "sum")
    with np.errstate(divide="ignore", invalid="ignore"):
        cmo = (su - sd) / (su + sd)
    pc = ctx.prev(cmo, 1)
    with np.errstate(invalid="ignore"):
        short = (pc >= th) & (cmo < th)
        long = (pc <= -th) & (cmo > -th)
    return long.astype(int) - short.astype(int)


# E-591 ----------------------------------------------------------------------------------------
def _rvi_cross(ctx, p):
    n, th = max(3, ctx.bars(p["win_min"])), float(p["th"])
    sd = ctx.roll(ctx.c, n, "std")
    d = ctx.c - ctx.prev(ctx.c, 1)
    u = np.where(d > 0, sd, np.where(np.isnan(sd), np.nan, 0.0))
    w = np.where(d < 0, sd, np.where(np.isnan(sd), np.nan, 0.0))
    eu, ew = ctx.ema(u, n), ctx.ema(w, n)
    with np.errstate(divide="ignore", invalid="ignore"):
        rvi = 100.0 * eu / (eu + ew)
    with np.errstate(invalid="ignore"):
        return _ud(ctx, rvi > th, rvi < 100.0 - th)


# E-592 ----------------------------------------------------------------------------------------
def _piercing(ctx, p):
    n, fr = max(3, ctx.bars(p["lookback_min"])), float(p["frac"])
    lown = ctx.prev(ctx.roll(ctx.l, n, "min"), 1)
    highn = ctx.prev(ctx.roll(ctx.h, n, "max"), 1)
    o1, c1, l1, h1 = ctx.prev(ctx.o, 1), ctx.prev(ctx.c, 1), ctx.prev(ctx.l, 1), ctx.prev(ctx.h, 1)
    with np.errstate(invalid="ignore"):
        long = (c1 < o1) & (ctx.c > ctx.o) & (ctx.o <= c1) & (ctx.c > c1 + fr * (o1 - c1)) & (l1 <= lown)
        short = (c1 > o1) & (ctx.c < ctx.o) & (ctx.o >= c1) & (ctx.c < c1 - fr * (c1 - o1)) & (h1 >= highn)
    return long.astype(int) - short.astype(int)


# E-593 ----------------------------------------------------------------------------------------
def _ribbon(ctx, p):
    u, sep = int(p["unit"]), float(p["sep"])
    e = [ctx.cached(("b059_ema", u * m), lambda m=m: ctx.ema(ctx.c, max(2, u * m))) for m in (1, 2, 3, 5)]
    with np.errstate(invalid="ignore"):
        gap = (e[0] - e[3]) / ctx.c
        up = (e[0] > e[1]) & (e[1] > e[2]) & (e[2] > e[3]) & (gap >= sep)
        dn = (e[0] < e[1]) & (e[1] < e[2]) & (e[2] < e[3]) & (-gap >= sep)
    return _ud(ctx, up, dn)


# E-594 ----------------------------------------------------------------------------------------
def _stoch_rsi(ctx, p):
    n, t = int(p["n"]), float(p["th"]) / 100.0
    r = ctx.rsi(n)
    lo, hi = ctx.roll(r, n, "min"), ctx.roll(r, n, "max")
    rng = hi - lo
    with np.errstate(divide="ignore", invalid="ignore"):
        sr = np.where(rng > 0, (r - lo) / np.where(rng > 0, rng, 1.0), np.nan)
    pv = ctx.prev(sr, 1)
    with np.errstate(invalid="ignore"):
        long = (pv <= t) & (sr > t)
        short = (pv >= 1 - t) & (sr < 1 - t)
    return long.astype(int) - short.astype(int)


# E-595 ----------------------------------------------------------------------------------------
def _td_projection(ctx, p):
    buf = float(p["buf"])
    po, ph, pl, pc = (ctx.prev_session_value(k) for k in ("open", "high", "low", "close"))
    x = np.where(pc < po, ph + 2 * pl + pc, np.where(pc > po, 2 * ph + pl + pc, ph + pl + 2 * pc))
    proj_h, proj_l = x / 2.0 - pl, x / 2.0 - ph
    rg = ph - pl
    top, bot = proj_h + buf * rg, proj_l - buf * rg
    with np.errstate(invalid="ignore"):
        short = (ctx.h > top) & (ctx.c < top)
        long = (ctx.l < bot) & (ctx.c > bot)
    return _ud(ctx, long & ~short, short & ~long)


# E-596 ----------------------------------------------------------------------------------------
def _stoch_cg(ctx, p):
    n, t = max(4, ctx.bars(p["win_min"])), float(p["th"])
    num = np.zeros(ctx.n)
    den = np.zeros(ctx.n)
    for i in range(n):
        pi = ctx.c if i == 0 else ctx.prev(ctx.c, i)
        num = num + (i + 1) * pi
        den = den + pi
    cg = -num / den
    lo, hi = ctx.roll(cg, n, "min"), ctx.roll(cg, n, "max")
    rng = hi - lo
    with np.errstate(divide="ignore", invalid="ignore"):
        s = np.where(rng > 0, (cg - lo) / np.where(rng > 0, rng, 1.0), np.nan)
    pv = ctx.prev(s, 1)
    with np.errstate(invalid="ignore"):
        long = (pv <= t) & (s > t)
        short = (pv >= 1 - t) & (s < 1 - t)
    return long.astype(int) - short.astype(int)


# E-597 ----------------------------------------------------------------------------------------
def _pvt_cross(ctx, p):
    span = max(3, ctx.bars(p["span_min"]))
    with np.errstate(invalid="ignore", divide="ignore"):
        inc = np.nan_to_num(ctx.v * (ctx.c / ctx.prev(ctx.c, 1) - 1.0), nan=0.0)
    pvt = pd.Series(inc).groupby(ctx.day).cumsum().to_numpy()
    sig = ctx.ema(pvt, span)
    with np.errstate(invalid="ignore"):
        return _ud(ctx, pvt > sig, pvt < sig)


FAMILIES = [
    Family("E-588", "Mean-of-daily-highs/lows band poke fade",
           "The average of the last n sessions' highs (lows) is a level where recent days' rallies (dips) typically "
           "ended; a bar that pokes through it and closes back is a failed push into resting supply/demand; fade it.",
           {"n": [5, 10, 20], "buf": [0.0, 0.1, 0.2]}, _avg_extreme_band, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-589", "Zero-lag EMA slope turn follow",
           "A zero-lag EMA turns before a plain EMA; when its slope turns with price on the same side, short-horizon "
           "momentum followers pile in for a few more bars.",
           {"span_min": [10, 20, 40], "min_slope": [0.0, 0.0001, 0.0002]}, _zlema_turn, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-590", "Chande momentum extreme fade",
           "When nearly all price change in the window has been one-directional (CMO beyond a threshold) and it first "
           "relaxes, the one-sided flow is fading and the pullback side takes over; trade the relaxation.",
           {"win_min": [30, 60, 90], "th": [0.5, 0.65, 0.8]}, _cmo_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-591", "Relative volatility index cross follow",
           "Volatility concentrated in up-closes (or down-closes) shows where the large flow sits; follow when the "
           "relative volatility index moves beyond a threshold.",
           {"win_min": [20, 40, 60], "th": [55, 60, 65]}, _rvi_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-592", "Piercing line / dark-cloud cover at a window extreme",
           "A bar that reverses more than a fraction of the previous opposite body right at a window extreme shows "
           "aggressive counter flow absorbing the move; trade the reversal.",
           {"lookback_min": [20, 40, 60], "frac": [0.5, 0.6, 0.75]}, _piercing, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-593", "EMA ribbon alignment onset follow",
           "When four EMAs (u, 2u, 3u, 5u bars) first line up in order with a minimum spread, trend followers at all "
           "horizons agree; the first aligned bar is an entry in that direction.",
           {"unit": [3, 5, 8], "sep": [0.0, 0.0003, 0.0006]}, _ribbon, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-594", "Stochastic RSI hook out of the extreme",
           "RSI at the bottom (top) of its own recent range then rising (falling) back through the threshold marks a "
           "momentum turn inside the window; trade the turn.",
           {"n": [7, 14], "th": [5, 10, 20]}, _stoch_rsi, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-595", "Prior-session projected-range level fade",
           "The projected high/low computed from the previous session's open, high, low and close (DeMark range "
           "projection) is a level watched by a minority of traders; a poke that closes back is fading.",
           {"buf": [0.0, 0.1, 0.25]}, _td_projection, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-596", "Stochastic centre-of-gravity turn",
           "The recency-weighted centre of gravity of prices turns before price itself; when it turns out of the "
           "extreme of its own window, the swing in that window is ending.",
           {"win_min": [10, 20, 30], "th": [0.1, 0.2, 0.3]}, _stoch_cg, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-597", "Price-volume-trend EMA cross follow",
           "Cumulating volume times return weighs moves by participation; the PVT crossing its EMA means volume is "
           "now backing the new direction.",
           {"span_min": [15, 30, 60]}, _pvt_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
