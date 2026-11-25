"""Conveyor batch B-153 (agent, 2026-11-25). WIN: short-box breaks read through new conditions (edge age, wide initial balance, quiet day so far, VWAP-centred box, multi-touch edges, rejection wick, volume ebb, tight-for-the-hour box, rejected outside open) plus a grinding-extreme reversal."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


# ----------------------------------------------------------------------------------------------- helpers

def _box(ctx, win_min):
    """Box of the previous `win_min` minutes (current bar excluded) and its first close-breaks."""
    def make():
        nb = ctx.bars(win_min)
        hi = ctx.roll(ctx.h, nb, "max", include_current=False)
        lo = ctx.roll(ctx.l, nb, "min", include_current=False)
        up = ctx.cross(ctx.c > hi)
        dn = ctx.cross(ctx.c < lo)
        return up, dn, hi, lo
    return ctx.cached(("b153_box", win_min), make)


def _fade(up, dn, cond):
    cond = np.asarray(cond, bool)
    return (dn & cond).astype(int) - (up & cond).astype(int)


def _per_day(ctx, values, agg):
    s = pd.Series(np.asarray(values, float)).groupby(ctx.day).agg(agg)
    return s.reindex(range(int(ctx.day.max()) + 1))


def _elapsed(ctx):
    """Minutes since the session's first bar (bar count times timeframe)."""
    return ctx.bar_in_day * ctx.tf


# ----------------------------------------------------------------------------------------------- families

def _mature_edge_fade(ctx, p):
    m = ctx.bars(int(p["age_min"]))
    up, dn, hi, lo = _box(ctx, int(p["win_min"]))
    same_hi = hi == ctx.prev(hi, m)
    same_lo = lo == ctx.prev(lo, m)
    return _fade(up, dn, same_hi & same_lo)


def _grinding_extreme_reversal(ctx, p):
    f = float(p["f"])
    nb = ctx.bars(int(p["win_min"]))

    def make():
        nh = (ctx.h > ctx.session_high(False)).astype(float)
        nl = (ctx.l < ctx.session_low(False)).astype(float)
        return ctx.roll(nh, nb, "sum", include_current=False) / nb, ctx.roll(nl, nb, "sum", include_current=False) / nb
    fh, fl = ctx.cached(("b153_grind", nb), make)
    sell = ctx.cross(ctx.c < ctx.prev(ctx.l)) & (fh >= f)
    buy = ctx.cross(ctx.c > ctx.prev(ctx.h)) & (fl >= f)
    return buy.astype(int) - sell.astype(int)


def _wide_ib_fade(ctx, p):
    k = float(p["k"])
    ib_min = 60

    def make():
        mask = _elapsed(ctx) < ib_min
        H = _per_day(ctx, np.where(mask, ctx.h, np.nan), "max")
        L = _per_day(ctx, np.where(mask, ctx.l, np.nan), "min")
        R = H - L
        typ = R.rolling(20, min_periods=20).mean().shift(1)
        return R.to_numpy()[ctx.day], typ.to_numpy()[ctx.day]
    ib, typ = ctx.cached("b153_ib", make)
    after = _elapsed(ctx) >= ib_min
    wide = after & (ib >= k * typ) & (typ > 0)
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    return _fade(up, dn, wide)


def _quiet_day_fade(ctx, p):
    k = float(p["k"])

    def make():
        cumv = pd.Series(ctx.v).groupby(ctx.day).cumsum().to_numpy(float)
        typ = ctx.same_minute(cumv, "median")
        return cumv / np.where(typ > 0, typ, np.nan)
    ratio = ctx.cached("b153_cumv", make)
    quiet = (ratio <= k) & (_elapsed(ctx) >= 30)
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    return _fade(up, dn, quiet)


def _vwap_centred_box_fade(ctx, p):
    q = float(p["q"])
    up, dn, hi, lo = _box(ctx, int(p["win_min"]))
    vw = ctx.prev(ctx.vwap())
    w = hi - lo
    wn = np.where(w > 0, w, np.nan)
    centred = ((vw - lo) / wn >= q) & ((hi - vw) / wn >= q)
    return _fade(up, dn, centred)


def _multi_touch_fade(ctx, p):
    need = int(p["touches"])
    win = int(p["win_min"])
    nb = ctx.bars(win)
    up, dn, hi, lo = _box(ctx, win)

    def make():
        mr = ctx.roll(ctx.h - ctx.l, nb, "mean", include_current=False)
        tol = 0.25 * mr
        th = np.zeros(ctx.n)
        tl = np.zeros(ctx.n)
        for j in range(1, nb + 1):
            th += (ctx.prev(ctx.h, j) >= hi - tol)
            tl += (ctx.prev(ctx.l, j) <= lo + tol)
        return th, tl
    th, tl = ctx.cached(("b153_touch", win), make)
    sell = up & (th >= need)
    buy = dn & (tl >= need)
    return buy.astype(int) - sell.astype(int)


def _rejection_wick_break_fade(ctx, p):
    q = float(p["q"])
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    rng = ctx.h - ctx.l
    cl = (ctx.c - ctx.l) / np.where(rng > 0, rng, np.nan)
    sell = up & (cl <= q)
    buy = dn & (cl >= 1.0 - q)
    return buy.astype(int) - sell.astype(int)


def _volume_ebb_fade(ctx, p):
    k = float(p["k"])
    win = int(p["win_min"])
    nb = ctx.bars(win)
    recent = ctx.roll(ctx.v, 3, "mean", include_current=True)
    base = ctx.roll(ctx.v, nb, "mean", include_current=False)
    ebb = (recent <= k * base) & (base > 0)
    up, dn, _, _ = _box(ctx, win)
    return _fade(up, dn, ebb)


def _tight_for_the_hour_fade(ctx, p):
    k = float(p["k"])
    win = int(p["win_min"])
    up, dn, hi, lo = _box(ctx, win)
    w = hi - lo
    typ = ctx.cached(("b153_wtyp", win), lambda: ctx.same_minute(w, "median"))
    tight = (w <= k * typ) & (typ > 0)
    return _fade(up, dn, tight)


def _rejected_outside_open_fade(ctx, p):
    buf = float(p["buf"])
    ph = ctx.prev_session_value("high")
    pl = ctx.prev_session_value("low")
    pr = ph - pl
    outside = (ctx.day_open > ph + buf * pr) | (ctx.day_open < pl - buf * pr)
    back_in = (ctx.c <= ph) & (ctx.c >= pl)
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    return _fade(up, dn, outside & back_in & (pr > 0))


FAMILIES = [
    Family("E-1528", "Mature-edge box break fade",
           "When both edges of the short box have not moved for a long stretch, range traders have had time to rest "
           "orders at them and the book on the far side is deep; the first close beyond such an old edge mostly "
           "triggers the stops parked there and then meets that resting inventory, so fade it.",
           {"age_min": [10, 20, 30], "win_min": [30, 60]}, _mature_edge_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1529", "Grinding new-extreme reversal",
           "A run in which a large share of recent bars each print a new session high (low) by small steps is "
           "late buyers chasing with no fresh size behind them; the first close below the previous bar's low (above "
           "its high) shows the chase stopped, and those chasers become sellers, so trade the reversal.",
           {"f": [0.3, 0.4, 0.5], "win_min": [20, 40]}, _grinding_extreme_reversal, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1530", "Wide initial-balance day box-break fade",
           "In Market Profile reading, a first hour whose range is wide versus the last 20 sessions' first hours "
           "means the larger players already set the day's boundaries early, which usually gives a range day; later "
           "short box breaks inside such a day are rotations that responsive traders fade, so fade them.",
           {"k": [1.0, 1.25, 1.5], "win_min": [15, 30]}, _wide_ib_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1531", "Quiet-day-so-far box-break fade",
           "When the session's volume so far is below the usual volume at this minute, institutions are not "
           "working orders and the tape is day-trader inventory; a short box break then has no large initiator to "
           "carry it and the liquidity providers lean it back into the box, so fade it.",
           {"k": [0.6, 0.8, 1.0], "win_min": [15, 30]}, _quiet_day_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1532", "VWAP-centred box break fade",
           "A short box with the session VWAP sitting well inside it is the market rotating around fair value, "
           "where both sides are content; a close out of such a box is a rotation's edge, not a new value search, "
           "and the value traders bring it back, so fade it.",
           {"q": [0.1, 0.2, 0.3], "win_min": [15, 30]}, _vwap_centred_box_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1533", "Multi-touch edge stop-run fade",
           "An edge tested by several bars collects a visible cluster of stops just beyond it; the close through it "
           "is mostly those stops being filled by the participants who rested liquidity there, and once the cluster "
           "is spent nobody is left to extend the move, so fade the break.",
           {"touches": [2, 3, 4], "win_min": [15, 30]}, _multi_touch_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1534", "Rejection-wick break bar fade",
           "A bar that closes beyond the box edge but in the lower (upper) part of its own range was sold (bought) "
           "back hard inside the same bar; the breakout buyers met supply above the edge and are already losing on "
           "most of their fills, so fade the break.",
           {"q": [0.4, 0.5, 0.6], "win_min": [15, 30]}, _rejection_wick_break_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1535", "Volume-ebb box break fade",
           "When the last few bars trade fewer contracts than the box's average bar, participation is draining as "
           "price drifts to the edge; a break made into that ebb is thin quotes being lifted, not an initiator, and "
           "the resting size of the box takes it back, so fade it.",
           {"k": [0.6, 0.8, 1.0], "win_min": [15, 30]}, _volume_ebb_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1536", "Tight-for-the-time box break fade",
           "A short box much narrower than the usual box at this minute of day means makers are quoting tight with "
           "little to absorb; a close beyond it covers few points and only reaches the next layer of their quotes, "
           "so it rotates back; fade breaks of boxes tight for the time of day.",
           {"k": [0.6, 0.8, 1.0], "win_min": [15, 30]}, _tight_for_the_hour_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1537", "Rejected outside-open day box-break fade",
           "A session that opens outside yesterday's range and then trades back inside it has rejected the "
           "overnight move; the gap traders are trapped and the market returns to yesterday's balance, where both "
           "sides trade the edges, so short box breaks after the return are faded.",
           {"buf": [0.0, 0.1], "win_min": [10, 15, 30]}, _rejected_outside_open_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
