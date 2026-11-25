"""Conveyor batch B-152 (agent, 2026-11-25). WIN short-box breaks read through new regimes: nested boxes, flat opens, multi-day range contraction, light break bars, yesterday's closing band, multi-session variance ratio, marginal closes, open-hugging days, spent range budget and the day's dominant break side."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


# ----------------------------------------------------------------------------------------------- helpers

def _box(ctx, win_min):
    """Rolling box of the previous `win_min` minutes (excluding the current bar) and its first close-breaks."""
    def make():
        nb = ctx.bars(win_min)
        hi = ctx.roll(ctx.h, nb, "max", include_current=False)
        lo = ctx.roll(ctx.l, nb, "min", include_current=False)
        up = ctx.cross(ctx.c > hi)
        dn = ctx.cross(ctx.c < lo)
        return up, dn, hi, lo
    return ctx.cached(("b152_box", win_min), make)


def _per_day(ctx, values, agg):
    s = pd.Series(np.asarray(values, float)).groupby(ctx.day).agg(agg)
    return s.reindex(range(int(ctx.day.max()) + 1))


def _on_bars(ctx, per_day_series):
    return per_day_series.to_numpy()[ctx.day]


def _fade(up, dn, cond):
    cond = np.asarray(cond, bool)
    return (dn & cond).astype(int) - (up & cond).astype(int)


def _daily_range_stats(ctx):
    def make():
        H = _per_day(ctx, ctx.h, "max")
        L = _per_day(ctx, ctx.l, "min")
        R = H - L
        r5 = _on_bars(ctx, R.rolling(5, min_periods=5).mean().shift(1))
        r20 = _on_bars(ctx, R.rolling(20, min_periods=20).mean().shift(1))
        return r5, r20
    return ctx.cached("b152_drange", make)


# ----------------------------------------------------------------------------------------------- families

def _nested_box_fade(ctx, p):
    q = float(p["q"])
    up, dn, _, _ = _box(ctx, 10)
    _, _, HI, LO = _box(ctx, int(p["big_min"]))
    W = HI - LO
    Wn = np.where(W > 0, W, np.nan)
    room_up = (HI - ctx.c) / Wn
    room_dn = (ctx.c - LO) / Wn
    return (dn & (room_dn >= q)).astype(int) - (up & (room_up >= q)).astype(int)


def _flat_open_fade(ctx, p):
    g = float(p["g"])
    pc = ctx.prev_session_value("close")
    rng = ctx.prev_session_value("high") - ctx.prev_session_value("low")
    gap = np.abs(ctx.day_open - pc) / np.where(rng > 0, rng, np.nan)
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    return _fade(up, dn, gap <= g)


def _range_contraction_fade(ctx, p):
    k = float(p["k"])
    r5, r20 = _daily_range_stats(ctx)
    ratio = r5 / np.where(r20 > 0, r20, np.nan)
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    return _fade(up, dn, ratio <= k)


def _light_break_bar_fade(ctx, p):
    k = float(p["k"])
    win = int(p["win_min"])
    nb = ctx.bars(win)
    vm = ctx.roll(ctx.v, nb, "mean", include_current=False)
    up, dn, _, _ = _box(ctx, win)
    return _fade(up, dn, (ctx.v <= k * vm) & (vm > 0))


def _closing_band_fade(ctx, p):
    tail = float(p["tail_min"])

    def make():
        mask = ctx.minutes_to_close <= tail
        hf = _per_day(ctx, np.where(mask, ctx.h, np.nan), "max").shift(1)
        lf = _per_day(ctx, np.where(mask, ctx.l, np.nan), "min").shift(1)
        return _on_bars(ctx, hf), _on_bars(ctx, lf)
    hf, lf = ctx.cached(("b152_close_band", tail), make)
    inside = (ctx.c <= hf) & (ctx.c >= lf)
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    return _fade(up, dn, inside)


def _variance_ratio_regime_fade(ctx, p):
    k = float(p["k"])
    q = int(p["q"])

    def make():
        lr = np.log(ctx.c)
        r1 = lr - ctx.prev(lr, 1)
        rq = lr - ctx.prev(lr, q)
        a = ctx.prev_sessions(rq * rq, "mean")
        b = ctx.prev_sessions(r1 * r1, "mean")
        return a / np.where(b > 0, q * b, np.nan)
    vr = ctx.cached(("b152_vr", q), make)
    up, dn, _, _ = _box(ctx, 20)
    return _fade(up, dn, vr <= k)


def _marginal_close_fade(ctx, p):
    k = float(p["k"])
    win = int(p["win_min"])
    nb = ctx.bars(win)
    up, dn, hi, lo = _box(ctx, win)
    mr = ctx.roll(ctx.h - ctx.l, nb, "mean", include_current=False)
    up_ok = up & ((ctx.c - hi) <= k * mr)
    dn_ok = dn & ((lo - ctx.c) <= k * mr)
    return dn_ok.astype(int) - up_ok.astype(int)


def _open_hugging_fade(ctx, p):
    k = float(p["k"])

    def make():
        r = np.abs(ctx.c / ctx.day_open - 1.0)
        return r, ctx.same_minute(r, "mean")
    r, typ = ctx.cached("b152_open_dist", make)
    hug = (r <= k * typ) & (ctx.bar_in_day >= ctx.bars(30))
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    return _fade(up, dn, hug)


def _range_budget_spent_fade(ctx, p):
    k = float(p["k"])
    _, r20 = _daily_range_stats(ctx)
    sr = ctx.session_high(include_current=True) - ctx.session_low(include_current=True)
    spent = sr >= k * r20
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    return _fade(up, dn, spent)


def _minority_break_fade(ctx, p):
    m = float(p["m"])
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    cu = pd.Series(up.astype(float)).groupby(ctx.day).cumsum().to_numpy()
    cd = pd.Series(dn.astype(float)).groupby(ctx.day).cumsum().to_numpy()
    cu_prev = cu - up.astype(float)
    cd_prev = cd - dn.astype(float)
    sell = up & ((cd - cu_prev) >= m)
    buy = dn & ((cu - cd_prev) >= m)
    return buy.astype(int) - sell.astype(int)


FAMILIES = [
    Family("E-1518", "Nested-box interior break fade",
           "A 10-minute box break that still sits far from both edges of the surrounding 60-90 minute box has not "
           "reached any level where the larger players rest orders; it is a rotation inside the bigger auction and the "
           "range traders of the large box lean against it, so fade it.",
           {"q": [0.2, 0.3, 0.4], "big_min": [60, 90]}, _nested_box_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1519", "Flat-open day box-break fade",
           "When the session opens almost exactly at yesterday's close, no overnight information needs to be priced "
           "and nobody arrives with urgent inventory; the day is run by intraday liquidity providers and a short box "
           "break has no initiator behind it, so fade it.",
           {"g": [0.05, 0.1, 0.2], "win_min": [15, 30]}, _flat_open_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1520", "Multi-day range contraction break fade",
           "When the last five sessions' average range is small next to the 20-session average, the market is in a "
           "multi-day compression where participants trade both edges and wait; intraday short box breaks in such a "
           "regime are rotations that get sold or bought back, so fade them.",
           {"k": [0.7, 0.85, 1.0], "win_min": [15, 30]}, _range_contraction_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1521", "Light break-bar volume fade",
           "A close beyond the box made on a bar trading fewer contracts than the box's average bar is not an "
           "aggressor clearing the book, just thin quotes giving way; the resting size of the box is still there, so "
           "the break leans back inside; fade it.",
           {"k": [0.5, 0.75, 1.0], "win_min": [15, 30]}, _light_break_bar_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1522", "Inside yesterday's closing band break fade",
           "The range of yesterday's final minutes is where the last inventory was set and carried overnight; while "
           "price trades inside that band its holders are near break-even and defend it on both sides, so short box "
           "breaks there rotate back; fade them.",
           {"tail_min": [30, 60, 90], "win_min": [15, 30]}, _closing_band_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1523", "Multi-session variance-ratio regime break fade",
           "A variance ratio below one over the previous 20 sessions (multi-bar returns smaller than the sum of 1-bar "
           "ones) shows the market has recently been dominated by liquidity providers whose quotes reverse moves; in "
           "that regime a 20-minute box break is reversed too, so fade it.",
           {"k": [0.8, 0.9, 1.0], "q": [5, 10]}, _variance_ratio_regime_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1524", "Marginal-close break fade",
           "A bar that closes only a hair beyond the box edge (less than a fraction of the average bar range) shows "
           "the breakout side could not hold prices clearly through the level by the close; the stops are spent and "
           "the edge sellers (buyers) are still there, so fade the marginal break.",
           {"k": [0.1, 0.25, 0.5], "win_min": [15, 30]}, _marginal_close_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1525", "Open-hugging day break fade",
           "When after the first half hour price is still close to the day's open versus the usual distance at this "
           "minute, the day has found no direction and the open acts as a magnet for both sides; short box breaks "
           "away from it are absorbed, so fade them.",
           {"k": [0.25, 0.5, 0.75], "win_min": [15, 30]}, _open_hugging_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1526", "Spent range budget break fade",
           "Once the session range has reached most of the 20-session average daily range, day traders treat the day's "
           "travel as done and take profit at the edges while fresh initiators are scarce; a further short box break "
           "is met by that profit taking, so fade it.",
           {"k": [0.6, 0.8, 1.0], "win_min": [15, 30]}, _range_budget_spent_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1527", "Minority-side break fade",
           "Counting the day's short box breaks on each side shows which side has been winning the session's "
           "auctions; a break on the side that has broken clearly fewer times is a counter-move into the dominant "
           "side's resting orders, so fade it, i.e. trade with the side that has been breaking more.",
           {"m": [1, 2, 3], "win_min": [15, 30]}, _minority_break_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
