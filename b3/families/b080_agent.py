"""Conveyor batch B-080 (agent, 2026-11-23). Mixed themes: late-day momentum, autocorrelation regime, absorption, day-open and midrange crossings, dwell, trend statistics."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _intraday_momentum(ctx, p):
    nb = ctx.bars(p["first_min"])
    late = p["late_min"]
    mark = np.where(ctx.bar_in_day == nb - 1, ctx.c, np.nan)
    fc = pd.Series(mark).groupby(ctx.day).transform("max").to_numpy()
    ret = fc / ctx.day_open - 1.0
    valid = ctx.bar_in_day >= nb
    fire = ctx.cross(ctx.minutes_to_close <= late) | ctx.cross(ctx.minutes_to_close <= late / 2.0)
    fire = fire & valid
    return (fire & (ret > 0)).astype(int) - (fire & (ret < 0)).astype(int)


def _autocorr_regime(ctx, p):
    nb = ctx.bars(p["win_min"])
    th = p["th"]
    r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    prod = r * ctx.prev(r, 1)
    rho = ctx.roll(prod, nb, "mean") / ctx.roll(r * r, nb, "mean")
    big = np.abs(r) >= ctx.roll(np.abs(r), nb, "mean")
    fade = ctx.cross((rho < -th) & big)
    follow = ctx.cross((rho > th) & big)
    s = np.sign(np.nan_to_num(r))
    return (follow * s - fade * s).astype(int)


def _absorption(ctx, p):
    nb = ctx.bars(p["look_min"])
    k = p["vol_k"]
    rng = ctx.h - ctx.l
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    hi = ctx.roll(ctx.h, nb, "max")
    lo = ctx.roll(ctx.l, nb, "min")
    avg = ctx.roll(rng, nb, "mean", include_current=False)
    heavy = (ctx.v > k * med) & (rng < 0.8 * avg)
    width = hi - lo
    low_zone = ctx.l <= lo + 0.15 * width
    high_zone = ctx.h >= hi - 0.15 * width
    return (heavy & low_zone).astype(int) - (heavy & high_zone).astype(int)


def _day_open_recross(ctx, p):
    nb = ctx.bars(p["away_min"])
    below = (ctx.c < ctx.day_open).astype(float)
    above = (ctx.c > ctx.day_open).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    up = was_below & (ctx.c > ctx.day_open)
    dn = was_above & (ctx.c < ctx.day_open)
    return up.astype(int) - dn.astype(int)


def _record_bar_fade(ctx, p):
    warm = ctx.bars(p["warm_min"])
    q = p["q"]
    rng = ctx.h - ctx.l
    prior = pd.Series(rng).groupby(ctx.day).transform(lambda z: z.cummax().shift(1)).to_numpy()
    loc = np.where(rng > 0, (ctx.c - ctx.l) / np.where(rng > 0, rng, 1.0), 0.5)
    rec = (rng > prior) & (ctx.bar_in_day >= warm)
    short = rec & (ctx.c > ctx.o) & (loc >= 1 - q)
    long = rec & (ctx.c < ctx.o) & (loc <= q)
    return long.astype(int) - short.astype(int)


def _range_dwell(ctx, p):
    nb = ctx.bars(p["win_min"])
    m = ctx.bars(p["dwell_min"])
    hi = ctx.roll(ctx.h, nb, "max")
    lo = ctx.roll(ctx.l, nb, "min")
    w = hi - lo
    pos = np.where(w > 0, (ctx.c - lo) / np.where(w > 0, w, 1.0), 0.5)
    pos = np.where(np.isnan(hi), np.nan, pos)
    top = ctx.roll(pos, m, "min") >= 0.8
    bot = ctx.roll(pos, m, "max") <= 0.2
    return ctx.cross(top).astype(int) - ctx.cross(bot).astype(int)


def _midrange_cross(ctx, p):
    wf = p["width_frac"]
    warm = ctx.bars(p["warm_min"])
    sh = ctx.session_high(include_current=True)
    sl = ctx.session_low(include_current=True)
    mid = (sh + sl) / 2.0
    wide = ((sh - sl) / ctx.day_open >= wf) & (ctx.bar_in_day >= warm)
    up = ctx.cross((ctx.c > mid) & wide)
    dn = ctx.cross((ctx.c < mid) & wide)
    return up.astype(int) - dn.astype(int)


def _ema_stack(ctx, p):
    f = p["fast_min"]
    e1 = ctx.cached(("ema", f), lambda: ctx.ema(ctx.c, ctx.bars(f)))
    e2 = ctx.cached(("ema", 2 * f), lambda: ctx.ema(ctx.c, ctx.bars(2 * f)))
    e3 = ctx.cached(("ema", 4 * f), lambda: ctx.ema(ctx.c, ctx.bars(4 * f)))
    long = (e1 > e2) & (e2 > e3) & (ctx.c > e1)
    short = (e1 < e2) & (e2 < e3) & (ctx.c < e1)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _trend_tstat(ctx, p):
    nb = max(4, ctx.bars(p["win_min"]))
    th = p["th"]
    x = pd.Series(np.arange(ctx.n, dtype=float))
    r = pd.Series(ctx.c).rolling(nb).corr(x).to_numpy()
    r = np.clip(r, -0.999999, 0.999999)
    t = r * np.sqrt((nb - 2) / (1 - r * r))
    ok = ctx.bar_in_day >= nb - 1
    return ctx.cross((t > th) & ok).astype(int) - ctx.cross((t < -th) & ok).astype(int)


def _efficiency_follow(ctx, p):
    nb = ctx.bars(p["win_min"])
    th = p["th"]
    d = np.abs(ctx.c - ctx.prev(ctx.c, 1))
    path = ctx.roll(d, nb, "sum")
    net = ctx.c - ctx.prev(ctx.c, nb)
    er = np.abs(net) / np.where(path > 0, path, np.nan)
    hi = er >= th
    return (ctx.cross(hi & (net > 0)).astype(int) - ctx.cross(hi & (net < 0)).astype(int))


FAMILIES = [
    Family("E-798", "First-window return predicts late-day move",
           "Intraday momentum: the first-window return of the session pushes institutional rebalancing and late hedging "
           "the same way; buy/sell when the last hours begin in the direction of the opening-window move.",
           {"first_min": [30, 60, 90], "late_min": [60, 90, 120]}, _intraday_momentum, markets=("WIN",),
           source="Gao, Han, Li, Zhou: Market Intraday Momentum (assistant reasoning)", author="agent"),
    Family("E-799", "Return autocorrelation regime switch",
           "When the rolling lag-1 autocorrelation of bar returns is strongly positive, a big bar is followed by more "
           "flow in its direction; when strongly negative, liquidity providers fade it. Trade the regime.",
           {"win_min": [30, 60, 90], "th": [0.1, 0.2, 0.3]}, _autocorr_regime, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-800", "Heavy-volume small-range absorption at the range edge",
           "Big volume with a small range at the edge of the recent range means passive orders absorb the aggressors; "
           "trade away from the edge.",
           {"look_min": [30, 60, 90], "vol_k": [1.5, 2.0, 3.0]}, _absorption, markets=("WIN",),
           source="volume spread analysis (assistant reasoning)", author="agent"),
    Family("E-801", "Day-open recross follow",
           "The session open is a reference many participants watch; after a long stay on one side, a close back "
           "across it flips the day's bias.",
           {"away_min": [20, 40, 60]}, _day_open_recross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-802", "Session-record range bar exhaustion fade",
           "A bar with the widest range of the session that closes at its extreme is a climax where the last "
           "aggressors enter; fade it.",
           {"warm_min": [30, 60, 90], "q": [0.2, 0.3]}, _record_bar_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-803", "Range-edge dwell continuation",
           "Closes that stay in the top (bottom) fifth of the recent range for a while show persistent one-sided "
           "demand; follow when the dwell starts.",
           {"win_min": [60, 120], "dwell_min": [10, 20, 30]}, _range_dwell, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-804", "Session midrange cross follow",
           "Once the day has a wide range, the midpoint of high and low is the balance line; a close across it "
           "shows control moving to the other side.",
           {"width_frac": [0.003, 0.005, 0.008], "warm_min": [30, 60]}, _midrange_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-805", "EMA stack alignment follow",
           "When fast, medium and slow EMAs line up in order and price is beyond the fast one, trend followers "
           "across horizons agree; enter on the alignment.",
           {"fast_min": [5, 10, 15]}, _ema_stack, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-806", "Regression t-statistic trend follow",
           "A statistically strong linear trend over the window (high t-stat of price on time) marks a one-way "
           "flow; join when the t-stat first exceeds the bar.",
           {"win_min": [30, 60, 90], "th": [4.0, 6.0, 8.0]}, _trend_tstat, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-807", "Kaufman efficiency-ratio surge follow",
           "When price covers a window almost in a straight line (efficiency ratio high), little counter-flow "
           "exists; follow the direction on the first crossing.",
           {"win_min": [15, 30, 60], "th": [0.5, 0.6, 0.7]}, _efficiency_follow, markets=("WIN",),
           source="Kaufman adaptive moving average (assistant reasoning)", author="agent"),
]
