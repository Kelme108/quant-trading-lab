"""Conveyor batch B-022 (agent, 2026-11-18). Mixed WIN ideas: opening-auction level, break-bar quality, value side,
the session's own break-failure memory, spent hourly range, settlement pin, new-extreme balance, multi-day edges,
steady participation and fixed-point take-profit clusters."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


# ---------------------------------------------------------------------------------------------
# shared helpers (all causal, session-bounded)
# ---------------------------------------------------------------------------------------------

def _rng_med(ctx):
    return ctx.cached("b022_rng_med", lambda: ctx.same_minute(ctx.h - ctx.l, "median"))


def _micro(ctx, win_min):
    nb = ctx.bars(win_min)
    hi = ctx.cached(("b022_hi", nb), lambda: ctx.roll(ctx.h, nb, "max", include_current=False))
    lo = ctx.cached(("b022_lo", nb), lambda: ctx.roll(ctx.l, nb, "min", include_current=False))
    up = ctx.cross(ctx.c > hi)
    dn = ctx.cross(ctx.c < lo)
    return hi, lo, up, dn


def _day_cumsum(ctx, x):
    return pd.Series(np.asarray(x, float)).groupby(ctx.day).cumsum().to_numpy()


# ---------------------------------------------------------------------------------------------
# families
# ---------------------------------------------------------------------------------------------

def _open_auction_hold(ctx, p):
    nb = ctx.bars(p["away_min"])
    op = ctx.day_open
    above = (ctx.l > op).astype(float)
    below = (ctx.h < op).astype(float)
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    long = was_above & (ctx.l <= op) & (ctx.c > op)
    short = was_below & (ctx.h >= op) & (ctx.c < op)
    return long.astype(int) - short.astype(int)


def _creep_break_fade(ctx, p):
    _, _, up, dn = _micro(ctx, p["win_min"])
    small = (ctx.h - ctx.l) < p["q"] * _rng_med(ctx)
    return (dn & small).astype(int) - (up & small).astype(int)


def _counter_value_fade(ctx, p):
    _, _, up, dn = _micro(ctx, p["win_min"])
    vw = ctx.vwap()
    d = p["k"] * _rng_med(ctx)
    short = up & (ctx.c < vw - d)
    long = dn & (ctx.c > vw + d)
    return long.astype(int) - short.astype(int)


def _break_failure_memory(ctx, p):
    hi, lo, up, dn = _micro(ctx, p["win_min"])
    m = ctx.bars(10)
    lvl_u, lvl_d = ctx.prev(hi, m), ctx.prev(lo, m)
    b_u = ctx.prev(up.astype(float), m) == 1
    b_d = ctx.prev(dn.astype(float), m) == 1
    mn = ctx.roll(ctx.c, m, "min")            # bars t-m+1..t: the m bars after the break at t-m
    mx = ctx.roll(ctx.c, m, "max")
    fail = (b_u & (mn < lvl_u)) | (b_d & (mx > lvl_d))
    seen = b_u | b_d
    cf, cs = _day_cumsum(ctx, fail), _day_cumsum(ctx, seen)
    with np.errstate(invalid="ignore", divide="ignore"):
        share = np.where(cs > 0, cf / np.maximum(cs, 1), 0.0)
    regime = (cs >= 3) & (share >= p["th"])
    return (dn & regime).astype(int) - (up & regime).astype(int)


def _spent_hour_fade(ctx, p):
    _, _, up, dn = _micro(ctx, p["win_min"])
    nb = ctx.bars(60)
    hr = ctx.roll(ctx.h, nb, "max") - ctx.roll(ctx.l, nb, "min")
    typ = ctx.cached(("b022_hr_typ", nb), lambda: ctx.prev_sessions(hr, "mean"))
    spent = hr >= p["k"] * typ
    return (dn & spent).astype(int) - (up & spent).astype(int)


def _settlement_pin_fade(ctx, p):
    _, _, up, dn = _micro(ctx, p["win_min"])
    pc = ctx.prev_session_value("close")
    near = np.abs(ctx.c - pc) <= p["k"] * _rng_med(ctx)
    return (dn & near).astype(int) - (up & near).astype(int)


def _extreme_count_dip(ctx, p):
    nh = ctx.h > ctx.session_high(include_current=False)
    nl = ctx.l < ctx.session_low(include_current=False)
    ch, cl = _day_cumsum(ctx, nh), _day_cumsum(ctx, nl)
    tot = ch + cl
    with np.errstate(invalid="ignore", divide="ignore"):
        bal = np.where(tot > 0, (ch - cl) / np.maximum(tot, 1), 0.0)
    ok = tot >= 5
    c1, c2 = ctx.prev(ctx.c, 1), ctx.prev(ctx.c, 2)
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    long = ok & (bal >= p["th"]) & (c1 < c2) & (ctx.c > h1)
    short = ok & (bal <= -p["th"]) & (c1 > c2) & (ctx.c < l1)
    return long.astype(int) - short.astype(int)


def _multiday_edge_fade(ctx, p):
    _, _, up, dn = _micro(ctx, 15)
    n = int(p["n_sessions"])
    nd = int(ctx.day.max()) + 1
    dh = pd.Series(ctx.h).groupby(ctx.day).max().reindex(range(nd))
    dl = pd.Series(ctx.l).groupby(ctx.day).min().reindex(range(nd))
    ch = dh.rolling(n, min_periods=n).max().shift(1).to_numpy()[ctx.day]
    cl = dl.rolling(n, min_periods=n).min().shift(1).to_numpy()[ctx.day]
    d = p["k"] * _rng_med(ctx)
    short = up & (ctx.h >= ch - d)
    long = dn & (ctx.l <= cl + d)
    return long.astype(int) - short.astype(int)


def _steady_participation(ctx, p):
    nb = ctx.bars(p["win_min"])
    vm = ctx.roll(ctx.v, nb, "mean")
    vs = ctx.roll(ctx.v, nb, "std")
    with np.errstate(invalid="ignore", divide="ignore"):
        cv = vs / np.where(vm > 0, vm, np.nan)
    cv_typ = ctx.cached(("b022_cv", nb), lambda: ctx.prev_sessions(cv, "mean"))
    move = ctx.c - ctx.prev(ctx.c, nb)
    mv_typ = ctx.cached(("b022_mv", nb), lambda: ctx.prev_sessions(np.abs(move), "mean"))
    steady = cv < p["q"] * cv_typ
    long = steady & (move > mv_typ)
    short = steady & (move < -mv_typ)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _fixed_target_fade(ctx, p):
    nb = ctx.bars(p["win_min"])
    lo = ctx.roll(ctx.l, nb, "min")
    hi = ctx.roll(ctx.h, nb, "max")
    short = ctx.cross(ctx.c - lo >= p["pts"])
    long = ctx.cross(hi - ctx.c >= p["pts"])
    both = short & long
    return (long & ~both).astype(int) - (short & ~both).astype(int)


FAMILIES = [
    Family("E-218", "Opening-auction price hold",
           "The session's first trade is set by the opening auction, where the overnight orders were matched; desks "
           "that missed it rest orders back at that price. After price has traded entirely on one side of the open for "
           "a while, the first bar that touches it and closes back on the old side shows those orders absorbing the "
           "pullback traders, so the move resumes away from the open (a hold, not the colour flip of E-077).",
           {"away_min": [10, 20, 30]}, _open_auction_hold, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-219", "Creep-break fade",
           "A close beyond the recent high/low made by a bar much narrower than normal for its minute is not an "
           "initiative order sweeping the book, just quotes inching past the level; with no aggressive side and the "
           "resting liquidity of the range still in place, liquidity providers lean it back inside, so fade it.",
           {"win_min": [10, 15, 30], "q": [0.5, 0.75, 1.0]}, _creep_break_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-220", "Counter-value micro-break fade",
           "A short-term break upward made while price is clearly below the session VWAP pushes into prices the day's "
           "average participant already sold at; the holders of the day's inventory (short below value) add there and "
           "the break buyers are a small local push, so fade breaks made against the value side (mirror).",
           {"win_min": [10, 15, 30], "k": [0, 1, 2]}, _counter_value_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-221", "Session break-failure memory fade",
           "Each session has its own character, set by who is trading it: when most of today's earlier short-term "
           "breaks closed back through the broken level within ten minutes, today's book is run by responsive "
           "liquidity providers and the breakout traders keep losing; the next break is faded on that evidence alone.",
           {"win_min": [10, 15, 30], "th": [0.5, 0.6, 0.7]}, _break_failure_memory, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-222", "Spent-hour micro-break fade",
           "When the last 60 minutes already covered far more range than a typical hour, the hour's directional flow "
           "and the short-term traders' range expectations are used up; a further short-term break then meets "
           "profit-takers and no fresh initiators, so fade it.",
           {"win_min": [10, 15, 30], "k": [1.5, 2.0, 2.5]}, _spent_hour_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-223", "Prior-settlement pin micro-break fade",
           "Yesterday's close/settlement is the zero line of variation margin and of many option and hedge books; "
           "dealers hedging near it buy dips and sell rallies, which pins price around it, so short-term breaks made "
           "while price sits close to yesterday's close are faded.",
           {"win_min": [10, 15, 30], "k": [2, 4, 6]}, _settlement_pin_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-224", "New-extreme balance dip buy",
           "Counting today's bars that set a new session high against those that set a new session low measures who "
           "has been initiating all day; when the count is lopsided toward highs, the dips are profit-taking against a "
           "persistent buyer, and the first close above the previous high after a lower close resumes the day (mirror).",
           {"th": [0.4, 0.6, 0.8]}, _extreme_count_dip, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-225", "Multi-day channel edge micro-break fade",
           "Swing traders rest take-profits and fresh counter orders at the high/low of the last 5-20 sessions; a "
           "short-term intraday break reaching that multi-day edge meets their size rather than the thin intraday "
           "book, so fade breaks made at or near the multi-session channel edge (mirror at the low).",
           {"n_sessions": [5, 10, 20], "k": [2, 4, 8]}, _multiday_edge_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-226", "Steady-participation move follow",
           "TWAP/POV execution algorithms slice a parent order into evenly sized trades, so a window with unusually "
           "uniform per-bar volume (low coefficient of variation) and a larger-than-usual move is the footprint of a "
           "scheduled order still being worked, not a burst; follow the move when that steady regime appears.",
           {"win_min": [20, 30, 60], "q": [0.6, 0.75, 0.9]}, _steady_participation, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-227", "Fixed-point target cluster fade",
           "WIN day traders commonly use fixed point targets (150/200/300 points) from their entry near a recent "
           "swing low; when price has risen that many points from the window's low, their take-profit sells cluster "
           "there and the late buyers meet them, so fade the bar where the run first reaches the distance (mirror).",
           {"pts": [150, 200, 300], "win_min": [15, 30, 60]}, _fixed_target_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
