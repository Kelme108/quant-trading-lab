"""Conveyor batch B-051 (agent, 2026-11-21). Fresh conditioners for window-edge breaks (clock hour, prior-day candle,
round numbers, prior-profile air pockets, window skew, prior-day path, weekday) plus weekday-based level ideas."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _breaks(ctx, win_min):
    """(up, dn): close beyond the high / low of the previous win_min minutes (current bar excluded)."""
    nb = ctx.bars(win_min)
    hi = ctx.cached(("bhi", nb), lambda: ctx.roll(ctx.h, nb, "max", include_current=False))
    lo = ctx.cached(("blo", nb), lambda: ctx.roll(ctx.l, nb, "min", include_current=False))
    return ctx.c > hi, ctx.c < lo


def _sess(ctx):
    def f():
        ud, st = np.unique(ctx.day, return_index=True)
        en = np.append(st[1:], ctx.n)
        wd = ctx.df["weekday"].to_numpy()[st].astype(float)
        return ud, st, en, wd, ctx.o[st].astype(float), ctx.c[en - 1].astype(float)
    return ctx.cached("sess", f)


def _to_bars(ctx, per_session):
    ud = _sess(ctx)[0]
    return np.asarray(per_session, float)[np.searchsorted(ud, ctx.day)]


# ---------------------------------------------------------------------------------------------
def _first_break_hour(ctx, p):
    up, dn = _breaks(ctx, p["win_min"])
    eu, ed = ctx.cross(up), ctx.cross(dn)
    ev = (eu | ed) & ((ctx.minute % 60) >= int(p["settle_min"]))
    hid = ctx.day.astype(np.int64) * 100 + (ctx.minute // 60).astype(np.int64)
    cnt = pd.Series(ev.astype(int)).groupby(hid).cumsum().to_numpy()
    first = ev & (cnt == 1)
    return (first & ed).astype(int) - (first & eu).astype(int)


def _prior_colour_break(ctx, p):
    up, dn = _breaks(ctx, p["win_min"])
    po, pc = ctx.prev_session_value("open"), ctx.prev_session_value("close")
    ph, pl = ctx.prev_session_value("high"), ctx.prev_session_value("low")
    body = (pc - po) / np.where(ph - pl > 0, ph - pl, np.nan)
    q = p["q"]
    long = ctx.cross(dn) & (body >= q)
    short = ctx.cross(up) & (body <= -q)
    return long.astype(int) - short.astype(int)


def _round_break(ctx, p):
    step = float(p["step"])
    up, dn = _breaks(ctx, p["win_min"])
    near = np.abs(ctx.c - np.round(ctx.c / step) * step) <= 0.1 * step
    return (ctx.cross(dn) & near).astype(int) - (ctx.cross(up) & near).astype(int)


def _thin_flag(ctx, binw, q):
    def f():
        b = np.floor(ctx.c / binw).astype(np.int64)
        thin = np.zeros(ctx.n, bool)
        ud, st = np.unique(ctx.day, return_index=True)
        en = np.append(st[1:], ctx.n)
        prev = None
        for i in range(len(ud)):
            s, e = st[i], en[i]
            bi = b[s:e]
            if prev is not None:
                u, vol = prev
                pos = np.minimum(np.searchsorted(u, bi), len(u) - 1)
                found = u[pos] == bi
                vv = np.where(found, vol[pos], 0.0)
                inside = (bi >= u[0]) & (bi <= u[-1])
                thin[s:e] = inside & (vv < q * np.median(vol))
            u2, inv = np.unique(bi, return_inverse=True)
            prev = (u2, np.bincount(inv, weights=ctx.v[s:e]))
        return thin
    return ctx.cached(("thin", binw, q), f)


def _air_pocket(ctx, p):
    thin = _thin_flag(ctx, float(p["bin_pts"]), float(p["q"]))
    d = ctx.c - ctx.prev(ctx.c, 1)
    ev = ctx.cross(thin)
    return (ev & (d > 0)).astype(int) - (ev & (d < 0)).astype(int)


def _mass_skew(ctx, p):
    nb = ctx.bars(p["win_min"])
    up, dn = _breaks(ctx, p["win_min"])
    hi = ctx.cached(("bhi", nb), lambda: ctx.roll(ctx.h, nb, "max", include_current=False))
    lo = ctx.cached(("blo", nb), lambda: ctx.roll(ctx.l, nb, "min", include_current=False))
    mean = ctx.roll(ctx.c, nb, "mean", include_current=False)
    rng = np.where(hi - lo > 0, hi - lo, np.nan)
    mass = (mean - lo) / rng
    q = p["q"]
    short = ctx.cross(up) & (mass <= q)
    long = ctx.cross(dn) & (mass >= 1 - q)
    return long.astype(int) - short.astype(int)


def _prior_path_break(ctx, p):
    def f():
        d = np.abs(np.diff(ctx.c, prepend=np.nan))
        d[ctx.bar_in_day == 0] = np.nan
        g = pd.Series(d).groupby(ctx.day).sum()
        first = pd.Series(ctx.c).groupby(ctx.day).first()
        last = pd.Series(ctx.c).groupby(ctx.day).last()
        er = (last - first).abs() / g.replace(0, np.nan)
        m = er.shift(1).rolling(15, min_periods=15).mean()
        cond = (er.shift(1) < float(p["k"]) * m)
        return np.nan_to_num(cond.astype(float).reindex(ctx.day).to_numpy()) > 0
    cond = ctx.cached(("pathcond", float(p["k"])), f)
    up, dn = _breaks(ctx, p["win_min"])
    return (ctx.cross(dn) & cond).astype(int) - (ctx.cross(up) & cond).astype(int)


def _weekend_edge_fade(ctx, p):
    wd = ctx.df["weekday"].to_numpy()
    edge = (wd == 0) | (wd == 4)
    late = ctx.bar_in_day >= ctx.bars(p["after_min"])
    up, dn = _breaks(ctx, p["win_min"])
    ok = edge & late
    return (ctx.cross(dn) & ok).astype(int) - (ctx.cross(up) & ok).astype(int)


def _midweek_follow(ctx, p):
    wd = ctx.df["weekday"].to_numpy()
    mid = (wd >= 1) & (wd <= 3)
    up, dn = _breaks(ctx, p["win_min"])
    return (ctx.cross(up) & mid).astype(int) - (ctx.cross(dn) & mid).astype(int)


def _weekday_bias(ctx, p):
    def f():
        ud, st, en, wd, opn, cls = _sess(ctx)
        dr = cls / opn - 1.0
        out = np.full(len(ud), np.nan)
        for i in range(len(ud)):
            j = np.arange(max(0, i - 20), i)
            j = j[wd[j] == wd[i]]
            if len(j) >= 2:
                out[i] = dr[j].mean()
        return _to_bars(ctx, out)
    bias = ctx.cached("wdbias", f)
    vw = ctx.vwap()
    late = ctx.bar_in_day >= ctx.bars(p["min_min"])
    th = p["th"]
    long = ctx.cross(ctx.c > vw) & late & (bias > th)
    short = ctx.cross(ctx.c < vw) & late & (bias < -th)
    return long.astype(int) - short.astype(int)


def _weekday_level_fade(ctx, p):
    def f():
        ud, st, en, wd, opn, cls = _sess(ctx)
        out = np.full(len(ud), np.nan)
        for i in range(len(ud)):
            for j in range(i - 1, max(-1, i - 21), -1):
                if wd[j] == wd[i]:
                    out[i] = cls[j]
                    break
        return _to_bars(ctx, out)
    lvl = ctx.cached("wdlevel", f)
    b = p["buf"]
    up = ctx.cross(ctx.c > lvl * (1 + b))
    dn = ctx.cross(ctx.c < lvl * (1 - b))
    return dn.astype(int) - up.astype(int)


FAMILIES = [
    Family("E-508", "First box break of each clock hour fade",
           "The first close beyond the recent range inside a clock hour is the probe of hourly-rebalancing flow against "
           "a thin book; later breaks in the hour carry more information, the first is faded by liquidity providers.",
           {"win_min": [15, 30, 60], "settle_min": [0, 10, 20]}, _first_break_hour,
           source="assistant reasoning", author="agent", markets=("WIN",)),
    Family("E-509", "Prior-day-candle-aligned dip/rip fade",
           "After a prior session that closed clearly up (down), a close below (above) the recent range is a dip (rip) "
           "against yesterday's carried positioning; swing holders buy (sell) it back.",
           {"win_min": [15, 30, 60], "q": [0.1, 0.3, 0.5]}, _prior_colour_break,
           source="assistant reasoning", author="agent", markets=("WIN",)),
    Family("E-510", "Round-number micro-break fade",
           "Closes that break the recent range right at a round index number run into resting limit orders and "
           "option-strike hedging at that number, so the break is faded.",
           {"win_min": [15, 30, 60], "step": [250, 500, 1000]}, _round_break,
           source="assistant reasoning", author="agent", markets=("WIN",)),
    Family("E-511", "Prior-profile air-pocket follow",
           "Price entering a price bin that traded little yesterday (low-volume node inside yesterday's range) meets "
           "little resting liquidity, so the move through it accelerates; follow the entry direction.",
           {"bin_pts": [100, 200, 300], "q": [0.25, 0.5]}, _air_pocket,
           source="auction market theory (low-volume nodes)", author="agent", markets=("WIN",)),
    Family("E-512", "Spike-away-from-the-mass break fade",
           "When most closes of the window sit at the opposite end of the box from the break, the break is a spike by "
           "few orders, not a drift of the crowd; the mass pulls price back.",
           {"win_min": [15, 30, 60], "q": [0.3, 0.4, 0.5]}, _mass_skew,
           source="assistant reasoning", author="agent", markets=("WIN",)),
    Family("E-513", "Day-after-choppy-path break fade",
           "After a session whose path efficiency was lower than its recent norm (much travel, little net move), "
           "participants keep rotating; breaks of short ranges are faded the next day.",
           {"win_min": [15, 30, 60], "k": [0.6, 0.8, 1.0]}, _prior_path_break,
           source="assistant reasoning", author="agent", markets=("WIN",)),
    Family("E-514", "Weekend-edge session micro-break fade",
           "On Mondays and Fridays participants are reluctant to carry risk across the weekend, so range breaks lack "
           "follow-through and are faded.",
           {"win_min": [15, 30, 60], "after_min": [0, 30, 60]}, _weekend_edge_fade,
           source="assistant reasoning", author="agent", markets=("WIN",)),
    Family("E-515", "Mid-week range break follow",
           "Tuesday to Thursday carry the institutional trend flow (no weekend positioning); a close beyond the "
           "recent range is followed.",
           {"win_min": [30, 60, 120]}, _midweek_follow,
           source="assistant reasoning", author="agent", markets=("WIN",)),
    Family("E-516", "Same-weekday bias VWAP cross",
           "Days of the same weekday share scheduled flows (data releases, fund rebalancing); when the last same-weekday "
           "sessions drifted one way, a cross of the session VWAP in that direction resumes the drift.",
           {"th": [0.0, 0.0005, 0.001], "min_min": [30, 60, 90]}, _weekday_bias,
           source="assistant reasoning", author="agent", markets=("WIN",)),
    Family("E-517", "Last-week same-weekday close level fade",
           "The close of the same weekday a week ago is a reference many swing traders watch; a cross of it is faded "
           "as price returns to the range it came from.",
           {"buf": [0.0, 0.0005, 0.001]}, _weekday_level_fade,
           source="assistant reasoning", author="agent", markets=("WIN",)),
]
