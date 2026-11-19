"""Conveyor batch B-021 (agent, 2026-11-18). Mixed WIN themes: regime-filtered micro-break fades (location, seasonal
autocorrelation, overhead volume, two-sided sessions), cross-day compression, Renko reversals, vol-managed momentum
and daily-candle shape. Every signal fires on a change and uses bars <= t only."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


# ----------------------------------------------------------------------------------------------- shared helpers

def _elapsed(ctx):
    return ctx.bar_in_day * ctx.tf


def _range_so_far(ctx):
    def f():
        rs = ctx.session_high(include_current=True) - ctx.session_low(include_current=True)
        return rs, ctx.same_minute(rs, "median")
    return ctx.cached("b021_rs", f)


def _daily_range_avg(ctx):
    """Mean full-session range of the 20 sessions before this one (each session's final range; only past sessions
    enter prev_sessions, so the value at bar t never depends on today's bars)."""
    def f():
        h = pd.Series(ctx.h).groupby(ctx.day).transform("max").to_numpy()
        l = pd.Series(ctx.l).groupby(ctx.day).transform("min").to_numpy()
        return ctx.prev_sessions(h - l, "mean")
    return ctx.cached("b021_dra", f)


def _bar_range_typ(ctx):
    return ctx.cached("b021_tr", lambda: ctx.same_minute(ctx.h - ctx.l, "median"))


# ----------------------------------------------------------------------------------------------- E-208

def _wick_ceiling_fade(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    tr = _bar_range_typ(ctx)
    maxc, maxh = ctx.roll(ctx.c, nb, "max", include_current=False), ctx.roll(ctx.h, nb, "max", include_current=False)
    minc, minl = ctx.roll(ctx.c, nb, "min", include_current=False), ctx.roll(ctx.l, nb, "min", include_current=False)
    short = (ctx.c > maxc) & (ctx.c < maxh) & (maxh - maxc >= k * tr)
    long = (ctx.c < minc) & (ctx.c > minl) & (minc - minl >= k * tr)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# ----------------------------------------------------------------------------------------------- E-209

def _post_narrow_follow(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    avg = _daily_range_avg(ctx)
    yday = ctx.prev_session_value("high") - ctx.prev_session_value("low")
    narrow = yday <= k * avg
    up = (ctx.c > ctx.roll(ctx.h, nb, "max", include_current=False)) & narrow
    dn = (ctx.c < ctx.roll(ctx.l, nb, "min", include_current=False)) & narrow
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


# ----------------------------------------------------------------------------------------------- E-210

def _mid_range_fade(ctx, p):
    nb, q = ctx.bars(p["win_min"]), p["q"]
    rs, typ = _range_so_far(ctx)
    sl = ctx.session_low(include_current=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        pos = np.where(rs > 0, (ctx.c - sl) / rs, np.nan)
    ok = (np.abs(pos - 0.5) <= q) & (rs >= typ)
    up = ctx.c > ctx.roll(ctx.h, nb, "max", include_current=False)
    dn = ctx.c < ctx.roll(ctx.l, nb, "min", include_current=False)
    return ctx.cross(dn & ok).astype(int) - ctx.cross(up & ok).astype(int)


# ----------------------------------------------------------------------------------------------- E-211

def _seasonal_rho(ctx):
    def f():
        r = ctx.c - ctx.prev(ctx.c, 1)
        num = ctx.same_minute(r * ctx.prev(r, 1), "mean")
        den = ctx.same_minute(r * r, "mean")
        nb = ctx.bars(30)
        with np.errstate(invalid="ignore", divide="ignore"):
            return ctx.roll(num, nb, "mean") / ctx.roll(den, nb, "mean")
    return ctx.cached("b021_rho", f)


def _seasonal_reversal_fade(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    reg = _seasonal_rho(ctx) <= -th
    up = ctx.c > ctx.roll(ctx.h, nb, "max", include_current=False)
    dn = ctx.c < ctx.roll(ctx.l, nb, "min", include_current=False)
    return ctx.cross(dn & reg).astype(int) - ctx.cross(up & reg).astype(int)


# ----------------------------------------------------------------------------------------------- E-212

def _overhead_shares(ctx, nb):
    def f():
        tp = (ctx.h + ctx.l + ctx.c) / 3.0
        above = np.zeros(ctx.n)
        below = np.zeros(ctx.n)
        tot = np.zeros(ctx.n)
        for k in range(1, nb + 1):
            tpk, vk = ctx.prev(tp, k), ctx.prev(ctx.v, k)
            valid = ~np.isnan(tpk) & ~np.isnan(vk)
            v0 = np.where(valid, vk, 0.0)
            tot += v0
            above += np.where(valid & (tpk > ctx.c), v0, 0.0)
            below += np.where(valid & (tpk < ctx.c), v0, 0.0)
        full = (ctx.bar_in_day >= nb) & (tot > 0)
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(full, above / tot, np.nan), np.where(full, below / tot, np.nan)
    return ctx.cached(("b021_over", nb), f)


def _overhead_supply_fade(ctx, p):
    q = p["q"]
    above, below = _overhead_shares(ctx, ctx.bars(p["win_min"]))
    nb = ctx.bars(15)
    up = ctx.c > ctx.roll(ctx.h, nb, "max", include_current=False)
    dn = ctx.c < ctx.roll(ctx.l, nb, "min", include_current=False)
    short = up & (above >= q)
    long = dn & (below >= q)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# ----------------------------------------------------------------------------------------------- E-213

def _daily_tail_bias(ctx, p):
    q = p["q"]
    rs, typ = _range_so_far(ctx)
    sh, sl = ctx.session_high(include_current=True), ctx.session_low(include_current=True)
    upper = sh - np.maximum(ctx.day_open, ctx.c)
    lower = np.minimum(ctx.day_open, ctx.c) - sl
    ok = (_elapsed(ctx) >= 60) & (rs >= typ) & (rs > 0)
    bear = ok & (upper - lower >= q * rs)
    bull = ok & (lower - upper >= q * rs)
    short = bear & (ctx.c < ctx.prev(ctx.l, 1))
    long = bull & (ctx.c > ctx.prev(ctx.h, 1))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# ----------------------------------------------------------------------------------------------- E-214

def _renko_flips(ctx, frac):
    def f():
        b = (frac * _daily_range_avg(ctx)).tolist()
        c = ctx.c.tolist()
        day = np.asarray(ctx.day).tolist()
        n = ctx.n
        flip = np.zeros(n, dtype=np.int8)
        prior = np.zeros(n, dtype=np.int64)
        prevday, top, bot, d, streak = None, 0.0, 0.0, 0, 0
        for i in range(n):
            ci, bi = c[i], b[i]
            if day[i] != prevday:
                prevday, top, bot, d, streak = day[i], ci, ci, 0, 0
                continue
            if not (bi > 0) or ci != ci:
                continue
            if ci >= top + bi:
                k = int((ci - top) // bi)
                bot, top = top + (k - 1) * bi, top + k * bi
                if d == -1:
                    flip[i], prior[i], streak = 1, streak, k
                else:
                    streak += k
                d = 1
            elif ci <= bot - bi:
                k = int((bot - ci) // bi)
                top, bot = bot - (k - 1) * bi, bot - k * bi
                if d == 1:
                    flip[i], prior[i], streak = -1, streak, k
                else:
                    streak += k
                d = -1
        return flip, prior
    return ctx.cached(("b021_renko", frac), f)


def _renko_reversal_follow(ctx, p):
    flip, prior = _renko_flips(ctx, p["frac"])
    fire = (flip != 0) & (prior >= int(p["run"]))
    return np.where(fire, flip, 0).astype(int)


# ----------------------------------------------------------------------------------------------- E-215

def _two_sided_session_fade(ctx, p):
    nbl, nb = ctx.bars(p["lookback_min"]), ctx.bars(p["win_min"])
    shp, slp = ctx.session_high(include_current=False), ctx.session_low(include_current=False)
    late = _elapsed(ctx) >= 30
    new_hi = ((ctx.h > shp) & late).astype(float)
    new_lo = ((ctx.l < slp) & late).astype(float)
    two = (ctx.roll(new_hi, nbl, "max") == 1) & (ctx.roll(new_lo, nbl, "max") == 1)
    up = (ctx.c > ctx.roll(ctx.h, nb, "max", include_current=False)) & (ctx.h <= shp)
    dn = (ctx.c < ctx.roll(ctx.l, nb, "min", include_current=False)) & (ctx.l >= slp)
    return ctx.cross(dn & two).astype(int) - ctx.cross(up & two).astype(int)


# ----------------------------------------------------------------------------------------------- E-216

def _calming_momentum(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    mv = ctx.c - ctx.prev(ctx.c, nb)
    typ = ctx.cached(("b021_absmv", nb), lambda: ctx.same_minute(np.abs(mv), "mean"))
    r = np.abs(ctx.c - ctx.prev(ctx.c, 1))
    vr = ctx.roll(r, nb, "mean")
    vb = ctx.prev(vr, nb)
    calm = vr < vb
    up = (mv >= k * typ) & calm
    dn = (mv <= -k * typ) & calm
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


# ----------------------------------------------------------------------------------------------- E-217

def _open_drive_pullback(ctx, p):
    q, pb = p["q"], int(p["pb"])
    rs, typ = _range_so_far(ctx)
    sl = ctx.session_low(include_current=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        pos_open = np.where(rs > 0, (ctx.day_open - sl) / rs, np.nan)
    vw = ctx.vwap()
    ok = (_elapsed(ctx) >= 60) & (rs >= typ)
    drive_up = ok & (pos_open <= q) & (ctx.c > vw)
    drive_dn = ok & (pos_open >= 1.0 - q) & (ctx.c < vw)
    down_pb = np.ones(ctx.n, dtype=bool)
    up_pb = np.ones(ctx.n, dtype=bool)
    for k in range(1, pb + 1):
        ck, ck1 = ctx.prev(ctx.c, k), ctx.prev(ctx.c, k + 1)
        down_pb &= ck < ck1
        up_pb &= ck > ck1
    long = drive_up & down_pb & (ctx.c > ctx.prev(ctx.h, 1))
    short = drive_dn & up_pb & (ctx.c < ctx.prev(ctx.l, 1))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


FAMILIES = [
    Family("E-208", "Wick-ceiling closing-high fade",
           "A new N-minute closing high that still sits below the window's intrabar high means closes are climbing back "
           "into a zone where sellers already rejected prices with a wick; those sellers' resting offers are still above "
           "and the buyers chasing the closing high meet them, so fade the closing-basis break (mirror for lows).",
           {"win_min": [15, 30, 60], "k": [0.5, 1.0, 1.5]}, _wick_ceiling_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-209", "Post-narrow-session break follow",
           "Crabel's narrow-range idea across sessions: after a session whose range was well below the 20-session "
           "average, volatility is compressed and range expansion is due; day traders sized for a quiet day keep tight "
           "stops just beyond short-term extremes, so today's breaks of the recent high/low extend; follow them only on "
           "the day after a narrow session.",
           {"k": [0.6, 0.75, 0.9], "win_min": [15, 30, 60]}, _post_narrow_follow,
           markets=("WIN",), source="NR4/NR7 Narrow-range Bars (LuxAlgo) https://www.luxalgo.com/library/concept/nr4-nr7-narrow-range-bars.md",
           author="agent"),
    Family("E-210", "Mid-range micro-break fade",
           "On a day with a normal-or-wide range, a break of the last few minutes' high/low that happens in the middle "
           "of the session range is not at any level anyone watches: no stops or breakout orders sit there, only a "
           "small push through quotes that liquidity providers lean back on; fade breaks made mid-range.",
           {"win_min": [5, 10, 20], "q": [0.15, 0.25, 0.35]}, _mid_range_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-211", "Seasonal reversal-regime micro-break fade",
           "Some times of day are dominated by liquidity provision (bar returns reverse), others by order-flow "
           "continuation; the lag-1 autocorrelation of bar returns at this minute over the last 20 sessions measures "
           "which; where it is negative, a close beyond the recent high/low is quote bouncing that market makers "
           "reverse, so fade it only in the reversal-prone times of day.",
           {"win_min": [5, 10, 15], "th": [0.0, 0.05, 0.1]}, _seasonal_reversal_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-212", "Overhead-supply break-even fade",
           "When a large share of the last hours' volume traded above the current price, many of those buyers are under "
           "water; a rally to a new 15-minute high brings price back toward their cost and they sell to get out at "
           "break-even, capping the push; fade the break into heavy overhead volume (mirror: trapped shorts below).",
           {"win_min": [60, 120, 180], "q": [0.4, 0.5, 0.6]}, _overhead_supply_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-213", "Developing daily-candle tail bias",
           "After the first hour, a session whose high stands far above both its open and the current price is drawing "
           "a long upper tail on every daily chart: higher prices were tried and rejected, and day traders read the "
           "day as bearish; the first bar closing below the previous low joins that rejection (mirror for a long lower "
           "tail).",
           {"q": [0.3, 0.4, 0.5]}, _daily_tail_bias,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-214", "Renko reversal after a brick run",
           "Renko charts are widely used by WIN day traders; bricks sized from the typical daily range turn colour only "
           "after a two-brick move against the run. After a run of several bricks the run's holders exit on the first "
           "reversal brick and Renko users reverse at the same time, so follow the reversal brick.",
           {"frac": [0.05, 0.075, 0.1], "run": [2, 3, 4]}, _renko_reversal_follow,
           markets=("WIN",), source="How to Trade Using Renko Charts | Renko-Based Trading Strategies (Optimus Futures) "
           "https://optimusfutures.com/blog/how-to-trade-using-renko-charts/", author="agent"),
    Family("E-215", "Two-sided-session micro-break fade",
           "When, after the opening half hour, the session has extended both its high and its low within the recent "
           "window, both stop pools were swept and the day is rotating around value with responsive traders on both "
           "sides; a short-term break that does not reach a new session extreme is then reabsorbed, so fade it.",
           {"lookback_min": [60, 120, 180], "win_min": [5, 10, 15]}, _two_sided_session_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-216", "Calming-tape momentum follow",
           "Volatility-managed momentum: a move larger than usual for its horizon made while bar-to-bar volatility is "
           "falling is orderly, persistent flow (a parent order being worked), not a forced burst that reverts; follow "
           "the move at the bar it becomes large while the tape is calming.",
           {"win_min": [15, 30, 60], "k": [1.0, 1.5, 2.0]}, _calming_momentum,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-217", "Open-drive day pullback resumption",
           "A session whose open is still near its low an hour or more in (and price above VWAP) is an open-drive day: "
           "initiative buyers lifted from the first trade and nobody could push below the open. A short pullback of "
           "one to three lower closes is profit-taking, and the first close above the previous high is the drive "
           "resuming; follow it (mirror for an open near the high).",
           {"q": [0.1, 0.2, 0.3], "pb": [1, 2, 3]}, _open_drive_pullback,
           markets=("WIN",), source="assistant reasoning", author="agent"),
]
