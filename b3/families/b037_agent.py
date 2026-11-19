"""Conveyor batch B-037 (agent, 2026-11-19). Break energy, in-value and in-yesterday interiors, clock-mark range position, open rotation, box-vs-day size, prior-close stretch, wide initial balance, choppy dollar and top-third rotation."""
from __future__ import annotations
import numpy as np
import pandas as pd
from b3.esteira import Family


# ----------------------------------------------------------------------------- shared helpers

def _breaks(ctx, win_min):
    """First close beyond the high/low of the previous win_min minutes (one signal per break)."""
    def f():
        n = ctx.bars(win_min)
        hi = ctx.roll(ctx.h, n, "max", include_current=False)
        lo = ctx.roll(ctx.l, n, "min", include_current=False)
        return ctx.cross(ctx.c > hi), ctx.cross(ctx.c < lo), hi, lo
    return ctx.cached(("b037_breaks", win_min), f)


def _typ_move(ctx, minutes):
    """Median |close - close `minutes` earlier| at the same minute over the 20 sessions before."""
    def f():
        nb = ctx.bars(minutes)
        return ctx.same_minute(np.abs(ctx.c - ctx.prev(ctx.c, nb)), "median")
    return ctx.cached(("b037_typmove", minutes), f)


def _typ_range(ctx):
    return ctx.cached("b037_typrange", lambda: ctx.same_minute(ctx.h - ctx.l, "median"))


def _out(long, short):
    long = np.nan_to_num(np.asarray(long, float), nan=0.0) > 0
    short = np.nan_to_num(np.asarray(short, float), nan=0.0) > 0
    both = long & short
    return long.astype(int) - short.astype(int) - 0 * both


def _gt(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    with np.errstate(invalid="ignore"):
        return np.where(np.isfinite(a) & np.isfinite(b), a > b, False)


def _lt(a, b):
    return _gt(b, a)


# ----------------------------------------------------------------------------- families

def _low_energy_break_fade(ctx, p):
    up, dn, _, _ = _breaks(ctx, p["win_min"])
    small = _lt(ctx.h - ctx.l, p["q"] * _typ_range(ctx))
    return _out(dn & small, up & small)


def _value_interior_break_fade(ctx, p):
    def f():
        tp = (ctx.h + ctx.l + ctx.c) / 3.0
        g = lambda x: pd.Series(x).groupby(ctx.day).cumsum().to_numpy(float)
        cv = g(ctx.v)
        cv = np.where(cv > 0, cv, np.nan)
        m = g(ctx.v * tp) / cv
        var = g(ctx.v * tp * tp) / cv - m * m
        return m, np.sqrt(np.clip(var, 0.0, None))
    m, sd = ctx.cached("b037_vwsd", f)
    up, dn, _, _ = _breaks(ctx, p["win_min"])
    started = ctx.bar_in_day >= ctx.bars(30)
    inside = _lt(np.abs(ctx.c - m), p["k"] * sd) & _gt(sd, 0.0) & started
    return _out(dn & inside, up & inside)


def _clock_mark_range_position_fade(ctx, p):
    mark = (ctx.minute % 30) == ((30 - ctx.tf) % 30)          # bar that closes on :00 / :30
    sh = ctx.session_high(include_current=True)
    sl = ctx.session_low(include_current=True)
    rng = sh - sl
    pos = (ctx.c - sl) / np.where(rng > 0, rng, np.nan)
    dm = np.abs(ctx.c - ctx.day_open)
    typ = ctx.same_minute(dm, "median")
    balanced = _lt(dm, p["m"] * typ)
    started = ctx.bar_in_day >= ctx.bars(60)
    ok = mark & balanced & started
    short = ok & _gt(pos, 1.0 - p["q"])
    long = ok & _lt(pos, p["q"])
    return _out(long, short)


def _open_rotation_break_fade(ctx, p):
    def f():
        s = np.sign(ctx.c - ctx.day_open)
        ps_ = ctx.prev(s)
        cr = np.nan_to_num(s * ps_, nan=0.0) < 0
        return ctx.roll(cr.astype(float), ctx.bars(120), "sum")
    cnt = ctx.cached("b037_opencross", f)
    up, dn, _, _ = _breaks(ctx, p["win_min"])
    rot = _gt(cnt, p["m"] - 0.5)
    return _out(dn & rot, up & rot)


def _yesterday_interior_break_fade(ctx, p):
    yh = ctx.prev_session_value("high")
    yl = ctx.prev_session_value("low")
    typ = _typ_move(ctx, 30)
    room = np.minimum(yh - ctx.c, ctx.c - yl)
    deep = _gt(room, p["k"] * typ)
    up, dn, _, _ = _breaks(ctx, p["win_min"])
    return _out(dn & deep, up & deep)


def _narrow_box_wide_day_fade(ctx, p):
    up, dn, hi, lo = _breaks(ctx, p["win_min"])
    sr = ctx.session_high(False) - ctx.session_low(False)
    box = hi - lo
    small = _lt(box, p["q"] * sr) & _gt(box, 0.0)
    started = ctx.bar_in_day >= ctx.bars(60)
    ok = small & started
    return _out(dn & ok, up & ok)


def _prior_close_stretch_break_fade(ctx, p):
    pc = ctx.prev_session_value("close")
    d = ctx.c - pc
    typ = _typ_move(ctx, 60)
    up, dn, _, _ = _breaks(ctx, p["win_min"])
    short = up & _gt(d, p["k"] * typ)
    long = dn & _lt(d, -p["k"] * typ)
    return _out(long, short)


def _wide_ib_interior_break_fade(ctx, p):
    nb = ctx.bars(p["ib_min"])
    def f():
        in_ib = ctx.bar_in_day < nb
        hh = np.where(in_ib, ctx.h, np.nan)
        ll = np.where(in_ib, ctx.l, np.nan)
        ibh = pd.Series(hh).groupby(ctx.day).transform("max").to_numpy(float)
        ibl = pd.Series(ll).groupby(ctx.day).transform("min").to_numpy(float)
        # transform over the whole session is causal only after the IB is complete: mask before
        done = ctx.bar_in_day >= nb
        return np.where(done, ibh, np.nan), np.where(done, ibl, np.nan)
    ibh, ibl = ctx.cached(("b037_ib", p["ib_min"]), f)
    sr = ctx.session_high(True) - ctx.session_low(True)
    typ_sr = ctx.same_minute(sr, "median")
    wide = _gt(ibh - ibl, p["k"] * typ_sr)
    inside = _gt(ctx.c, ibl) & _lt(ctx.c, ibh)
    up, dn, _, _ = _breaks(ctx, 15)
    ok = wide & inside
    return _out(dn & ok, up & ok)


def _choppy_dollar_break_fade(ctx, p):
    def f():
        w = ctx.other_close()
        n = ctx.bars(30)
        path = ctx.roll(np.abs(w - ctx.prev(w)), n, "sum")
        net = np.abs(w - ctx.prev(w, n))
        return net / np.where(path > 0, path, np.nan)
    eff = ctx.cached("b037_wdo_eff", f)
    up, dn, _, _ = _breaks(ctx, p["win_min"])
    chop = _lt(eff, p["th"])
    return _out(dn & chop, up & chop)


def _top_third_exit_rotation(ctx, p):
    sh = ctx.session_high(include_current=True)
    sl = ctx.session_low(include_current=True)
    rng = sh - sl
    pos = (ctx.c - sl) / np.where(rng > 0, rng, np.nan)
    nb = ctx.bars(p["stay_min"])
    pmin = ctx.prev(ctx.roll(pos, nb, "min"))
    pmax = ctx.prev(ctx.roll(pos, nb, "max"))
    typ = ctx.same_minute(rng, "median")
    big = _gt(rng, p["k"] * typ)
    short = _gt(pmin, 2.0 / 3.0) & _lt(pos, 2.0 / 3.0) & big
    long = _lt(pmax, 1.0 / 3.0) & _gt(pos, 1.0 / 3.0) & big
    return _out(ctx.cross(long), ctx.cross(short))


SRC = "assistant reasoning"

FAMILIES = [
    Family("E-368", "Low-energy break-bar fade",
           "A close through the recent high/low printed by a bar whose range is small for its minute of day means the "
           "level gave way to a trickle of orders, not to an initiative burst; nobody with size is behind it, so liquidity "
           "providers lean on it and price returns into the box; fade the break.",
           {"win_min": [15, 30, 60], "q": [0.5, 0.75, 1.0]}, _low_energy_break_fade,
           markets=("WIN",), source=SRC, author="agent"),
    Family("E-369", "Value-interior micro-break fade",
           "While the close is within k volume-weighted standard deviations of today's volume-weighted mean, price is "
           "still inside the session's accepted value, where responsive traders on both sides are active; a short-term "
           "break there is rotation inside value rather than initiative, so fade it.",
           {"win_min": [15, 30, 60], "k": [0.5, 1.0, 1.5]}, _value_interior_break_fade,
           markets=("WIN",), source=SRC, author="agent"),
    Family("E-370", "Clock-mark range-position fade on balanced days",
           "At each :00/:30 mark desks and slicers reassess; on a day whose move from the open is not larger than usual "
           "for the minute, a close near the top (bottom) of the day's range at the mark is where the day's responsive "
           "sellers (buyers) rest, so lean against the range position toward the middle.",
           {"q": [0.1, 0.2, 0.3], "m": [0.5, 1.0, 1.5]}, _clock_mark_range_position_fade,
           markets=("WIN",), source=SRC, author="agent"),
    Family("E-371", "Opening-price rotation regime micro-break fade",
           "When price has crossed the session open several times in the last two hours, the day traders' zero line is "
           "being contested and neither side holds inventory; short-term breaks in that regime are pushed by stops and "
           "rotate back, so fade them only while the open keeps being crossed.",
           {"m": [2, 4, 6], "win_min": [15, 30]}, _open_rotation_break_fade,
           markets=("WIN",), source=SRC, author="agent"),
    Family("E-372", "Deep inside yesterday's range micro-break fade",
           "Far from both of yesterday's extremes (more than k typical 30-minute moves from each), no reference level "
           "or stop pool is nearby to pull price; a short-term break there has nothing to run to and is absorbed by "
           "traders working inside yesterday's accepted range, so fade it.",
           {"win_min": [15, 30, 60], "k": [1, 2, 3]}, _yesterday_interior_break_fade,
           markets=("WIN",), source=SRC, author="agent"),
    Family("E-373", "Narrow box inside a wide day break fade",
           "A recent box that is only a small share of the day's already wide range is a pause inside a market whose "
           "real edges are far away; its break triggers only local stops, while the day's larger participants trade "
           "the wider edges, so the break reverts into the box.",
           {"win_min": [15, 30], "q": [0.2, 0.3, 0.4]}, _narrow_box_wide_day_fade,
           markets=("WIN",), source=SRC, author="agent"),
    Family("E-374", "Break away from the prior close when already stretched",
           "Yesterday's settlement-close is the overnight inventory's reference; when price is already more than k "
           "typical hourly moves away from it, a further short-term break away is chased by late momentum traders "
           "while holders of the overnight inventory take profit, so fade the break back toward the prior close.",
           {"win_min": [15, 30, 60], "k": [1, 2, 3]}, _prior_close_stretch_break_fade,
           markets=("WIN",), source=SRC, author="agent"),
    Family("E-375", "Wide initial-balance interior micro-break fade",
           "A first hour (or half hour) whose range already covers most of a typical day's range-to-date has set "
           "broad value early, with longer-timeframe traders active at both edges; later short-term breaks that stay "
           "inside that initial balance are noise between the edges and revert, so fade them.",
           {"ib_min": [30, 60], "k": [0.6, 0.8, 1.0]}, _wide_ib_interior_break_fade,
           markets=("WIN",), source=SRC, author="agent"),
    Family("E-376", "Choppy-dollar index micro-break fade",
           "Macro and foreign flow moves the dollar with direction; when the dollar's last 30 minutes have been a "
           "path with little net progress (low efficiency), no macro flow is driving Brazil assets, so a WIN short-term "
           "break is local flow that market makers fade back into the box.",
           {"win_min": [15, 30], "th": [0.2, 0.3, 0.4]}, _choppy_dollar_break_fade,
           markets=("WIN",), source=SRC, author="agent"),
    Family("E-377", "Top-third exit rotation follow",
           "After price has stayed in the top third of the day's (normal-or-wider) range for a while, the first close "
           "back below it shows the buyers who held it there have stopped defending; their exits and the responsive "
           "sellers rotate price toward the middle of the range, so sell the exit (mirror from the bottom third).",
           {"stay_min": [15, 30, 60], "k": [0.5, 1.0]}, _top_third_exit_rotation,
           markets=("WIN",), source=SRC, author="agent"),
]
