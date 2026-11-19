"""Conveyor batch B-025 (agent, 2026-11-18). Multi-session anchors (prior opens, closes, IB edges, swing points,
peak-volume prices, daily MAs, rolling VWAP, range quartiles), a crowd-indicator fade and a closing-range break."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


# ----------------------------------------------------------------------------------------------- helpers

def _n_days(ctx):
    return int(ctx.day.max()) + 1


def _per_session(ctx, x, how):
    """One value per session (index 0..D-1) of x aggregated with `how`."""
    per = pd.Series(np.asarray(x, float)).groupby(ctx.day).agg(how)
    return per.reindex(range(_n_days(ctx)))


def _on_bars(ctx, per):
    return np.asarray(per, float)[ctx.day]


def _typ_range(ctx):
    return ctx.cached("b025_typ_rng", lambda: ctx.prev_sessions(ctx.h - ctx.l, "mean"))


def _poke_fade(ctx, levels, tol):
    """Short: previous close below a level, the bar trades at least `tol` above it and closes back below.
    Long: the mirror. One bar per setup."""
    pc = ctx.prev(ctx.c, 1)
    short = np.zeros(ctx.n, bool)
    long = np.zeros(ctx.n, bool)
    for L in levels:
        short |= (pc < L) & (ctx.h >= L + tol) & (ctx.c < L)
        long |= (pc > L) & (ctx.l <= L - tol) & (ctx.c > L)
    both = short & long
    return ctx.cross(long & ~both).astype(int) - ctx.cross(short & ~both).astype(int)


def _hold(ctx, levels, tol):
    """Long: the previous bar stayed clearly above a level, this bar comes within `tol` of it (or touches)
    and closes above it. Short: the mirror."""
    pl, ph = ctx.prev(ctx.l, 1), ctx.prev(ctx.h, 1)
    long = np.zeros(ctx.n, bool)
    short = np.zeros(ctx.n, bool)
    for L in levels:
        long |= (pl > L + tol) & (ctx.l <= L + tol) & (ctx.c > L)
        short |= (ph < L - tol) & (ctx.h >= L - tol) & (ctx.c < L)
    both = short & long
    return ctx.cross(long & ~both).astype(int) - ctx.cross(short & ~both).astype(int)


# ----------------------------------------------------------------------------------------------- signals

def _prior_open_poke(ctx, p):
    n = int(p["n_sessions"])
    per = _per_session(ctx, ctx.o, "first")
    levels = [_on_bars(ctx, per.shift(j)) for j in range(1, n + 1)]
    return _poke_fade(ctx, levels, p["k"] * _typ_range(ctx))


def _rolling_vwap_hold(ctx, p):
    n = int(p["n_sessions"])
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    pv = tp * ctx.v
    per_pv = _per_session(ctx, pv, "sum").shift(1).rolling(n, min_periods=n).sum()
    per_v = _per_session(ctx, ctx.v, "sum").shift(1).rolling(n, min_periods=n).sum()
    cum_pv = pd.Series(pv).groupby(ctx.day).cumsum().to_numpy()
    cum_v = pd.Series(ctx.v).groupby(ctx.day).cumsum().to_numpy()
    den = _on_bars(ctx, per_v) + cum_v
    vw = np.where(den > 0, (_on_bars(ctx, per_pv) + cum_pv) / np.where(den > 0, den, 1.0), np.nan)
    return _hold(ctx, [vw], p["k"] * _typ_range(ctx))


def _range_quartile_poke(ctx, p):
    n = int(p["n_sessions"])
    hi = _on_bars(ctx, _per_session(ctx, ctx.h, "max").shift(1).rolling(n, min_periods=n).max())
    lo = _on_bars(ctx, _per_session(ctx, ctx.l, "min").shift(1).rolling(n, min_periods=n).min())
    levels = [lo + q * (hi - lo) for q in (0.25, 0.5, 0.75)]
    return _poke_fade(ctx, levels, p["k"] * _typ_range(ctx))


def _prior_ib_poke(ctx, p):
    nb = ctx.bars(p["ib_min"])
    n = int(p["n_sessions"])
    first = ctx.bar_in_day < nb
    ph = _per_session(ctx, np.where(first, ctx.h, np.nan), "max")
    pl = _per_session(ctx, np.where(first, ctx.l, np.nan), "min")
    levels = []
    for j in range(1, n + 1):
        levels.append(_on_bars(ctx, ph.shift(j)))
        levels.append(_on_bars(ctx, pl.shift(j)))
    return _poke_fade(ctx, levels, 0.0)


def _vortex_fade(ctx, p):
    n = int(p["n"])
    h1, l1, c1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1), ctx.prev(ctx.c, 1)
    vmp = np.abs(ctx.h - l1)
    vmm = np.abs(ctx.l - h1)
    tr = np.maximum(ctx.h, c1) - np.minimum(ctx.l, c1)
    st = ctx.roll(tr, n, "sum")
    st = np.where(st > 0, st, np.nan)
    vip = ctx.roll(vmp, n, "sum") / st
    vim = ctx.roll(vmm, n, "sum") / st
    bull = vip > vim
    bear = vim > vip
    return ctx.cross(bear).astype(int) - ctx.cross(bull).astype(int)


def _peak_volume_hold(ctx, p):
    n = int(p["n_sessions"])
    mask = (ctx.bar_in_day * ctx.tf >= 15) & (ctx.minutes_to_close >= 30)
    vv = pd.Series(np.where(mask, ctx.v, -1.0))
    idx = vv.groupby(ctx.day).idxmax()
    per = pd.Series(ctx.c[idx.to_numpy().astype(int)], index=idx.index).reindex(range(_n_days(ctx)))
    levels = [_on_bars(ctx, per.shift(j)) for j in range(1, n + 1)]
    return _hold(ctx, levels, p["k"] * _typ_range(ctx))


def _daily_ma_poke(ctx, p):
    n = int(p["n_days"])
    per = _per_session(ctx, ctx.c, "last").shift(1).rolling(n, min_periods=n).mean()
    return _poke_fade(ctx, [_on_bars(ctx, per)], p["k"] * _typ_range(ctx))


def _prior_swing_poke(ctx, p):
    w = int(p["w"])
    win = 2 * w + 1
    g_h = pd.Series(ctx.h).groupby(ctx.day)
    g_l = pd.Series(ctx.l).groupby(ctx.day)
    rmax = g_h.transform(lambda z: z.rolling(win, center=True, min_periods=win).max()).to_numpy()
    rmin = g_l.transform(lambda z: z.rolling(win, center=True, min_periods=win).min()).to_numpy()
    sw_h = ctx.h == rmax
    sw_l = ctx.l == rmin
    days, starts = np.unique(ctx.day, return_index=True)
    ends = np.append(starts[1:], ctx.n)
    levels_by_day = {}
    for d, a, b in zip(days, starts, ends):
        lv = np.concatenate([ctx.h[a:b][sw_h[a:b]], ctx.l[a:b][sw_l[a:b]]])
        levels_by_day[int(d)] = np.unique(lv)
    pc = ctx.prev(ctx.c, 1)
    long = np.zeros(ctx.n, bool)
    short = np.zeros(ctx.n, bool)
    for d, a, b in zip(days, starts, ends):
        L = levels_by_day.get(int(d) - 1)
        if L is None or not len(L):
            continue
        L = L[None, :]
        pcs, hs, ls, cs = pc[a:b, None], ctx.h[a:b, None], ctx.l[a:b, None], ctx.c[a:b, None]
        short[a:b] = ((pcs < L) & (hs >= L) & (cs < L)).any(axis=1)
        long[a:b] = ((pcs > L) & (ls <= L) & (cs > L)).any(axis=1)
    both = short & long
    return ctx.cross(long & ~both).astype(int) - ctx.cross(short & ~both).astype(int)


def _closing_range_break(ctx, p):
    tail = float(p["tail_min"])
    mask = ctx.minutes_to_close <= tail
    th = _on_bars(ctx, _per_session(ctx, np.where(mask, ctx.h, np.nan), "max").shift(1))
    tl = _on_bars(ctx, _per_session(ctx, np.where(mask, ctx.l, np.nan), "min").shift(1))
    started = ctx.bar_in_day >= ctx.bars(10)
    up = ctx.cross(started & (ctx.c > th))
    dn = ctx.cross(started & (ctx.c < tl))
    return up.astype(int) - dn.astype(int)


def _prior_close_hold(ctx, p):
    n = int(p["n_sessions"])
    per = _per_session(ctx, ctx.c, "last")
    levels = [_on_bars(ctx, per.shift(j)) for j in range(1, n + 1)]
    return _hold(ctx, levels, p["k"] * _typ_range(ctx))


# ----------------------------------------------------------------------------------------------- families

FAMILIES = [
    Family("E-248", "Prior-sessions opening-price poke fade",
           "The opening-auction prices of the last few sessions are where each day's overnight orders were matched, and "
           "desks that anchor on them keep resting orders there; a bar that trades through such a price and closes back "
           "meets those resting orders, so the small break buyers (sellers) are trapped; fade back from the level.",
           {"n_sessions": [3, 5, 10], "k": [0.0, 0.25, 0.5]}, _prior_open_poke, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-249", "Multi-session rolling VWAP hold",
           "The volume-weighted price of the last few sessions plus today is the average cost of the swing holders; when "
           "price returns to it from one side and closes back on that side, those holders defend their cost basis (add or "
           "cover) instead of the intraday traders who pushed into it; trade away from the level.",
           {"n_sessions": [2, 3, 5], "k": [0.25, 0.5, 1.0]}, _rolling_vwap_hold, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-250", "Multi-day range quartile poke fade",
           "Swing traders grid their orders on the quarter, half and three-quarter marks of the last few sessions' range; "
           "a bar that pokes through one of those marks and closes back has met that resting size, and the intraday push "
           "through it has no follow-through; fade it.",
           {"n_sessions": [3, 5, 10], "k": [0.0, 0.25, 0.5]}, _range_quartile_poke, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-251", "Prior-sessions initial-balance edge fade",
           "The first-hour high/low of recent sessions is the range that the opening institutions defended on those days, "
           "and Market Profile users carry it forward as reference; a later poke through such an old edge that closes back "
           "is absorbed by the same responsive traders, so fade it.",
           {"ib_min": [30, 60, 90], "n_sessions": [1, 2, 3]}, _prior_ib_poke, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-252", "Vortex cross fade",
           "The Vortex indicator cross is a stock retail trend trigger that fires after the short swing already happened; "
           "the traders who enter on it supply the liquidity the earlier movers exit into, so the swing reverts; fade the cross.",
           {"n": [14, 21, 28]}, _vortex_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-253", "Prior sessions' peak-volume price hold",
           "The price of the heaviest-volume bar of each recent session (outside the auctions) is where the largest "
           "participant of that day transacted; that participant defends or re-enters there, so a return to the price "
           "that closes back on its side is held; trade away from the level.",
           {"n_sessions": [3, 5, 10], "k": [0.25, 0.5, 1.0]}, _peak_volume_hold, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-254", "Daily moving-average poke fade",
           "The 5/9/20-day moving averages of daily closes are plotted on almost every WIN daily chart, and swing traders "
           "rest entries and exits on them; an intraday poke through the daily average that closes back meets that resting "
           "size, not an empty book, so fade it.",
           {"n_days": [5, 9, 20], "k": [0.0, 0.25, 0.5]}, _daily_ma_poke, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-255", "Prior-session swing-point poke fade",
           "Yesterday's intraday swing highs and lows are the levels chart traders mark overnight, with stops and fresh "
           "orders just around them; a poke through one that closes back means the stops were taken and the resting "
           "counter orders won, so the late breakout traders are trapped; fade it.",
           {"w": [2, 3, 5]}, _prior_swing_poke, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-256", "Prior closing-range break follow",
           "The high/low of yesterday's last half hour to hour bounds the price where the overnight positions were "
           "opened, and those holders' stops sit just beyond it; a close through the closing range forces them out and "
           "their exits extend the move, so follow the break.",
           {"tail_min": [30, 60, 90]}, _closing_range_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-257", "Prior settlement-close hold",
           "Each recent session's close is the zero line of variation margin for positions opened that day; holders "
           "defend it to avoid paying margin, so a return to such a close that ends the bar back on its side is held; "
           "trade away from the level.",
           {"n_sessions": [3, 5, 10], "k": [0.25, 0.5, 1.0]}, _prior_close_hold, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
