"""Conveyor batch B-150 (agent, 2026-11-25). Box-structure fades (mature edges, open straddle, inner contraction, alternating breaks, far-edge dwell), session volume tails, yesterday's early extremes, VWAP fly-through, and two follows (narrow prior day, coiled top)."""
from __future__ import annotations
import numpy as np
import pandas as pd
from b3.esteira import Family


# ----------------------------------------------------------------------------- shared helpers

def _gt(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    with np.errstate(invalid="ignore"):
        return np.where(np.isfinite(a) & np.isfinite(b), a > b, False)


def _lt(a, b):
    return _gt(b, a)


def _eq(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    with np.errstate(invalid="ignore"):
        return np.where(np.isfinite(a) & np.isfinite(b), a == b, False)


def _out(long, short):
    long = np.nan_to_num(np.asarray(long, float), nan=0.0) > 0
    short = np.nan_to_num(np.asarray(short, float), nan=0.0) > 0
    both = long & short
    return (long & ~both).astype(int) - (short & ~both).astype(int)


def _box(ctx, win_min):
    """High/low of the previous win_min minutes (current bar excluded)."""
    def f():
        n = ctx.bars(win_min)
        return (ctx.roll(ctx.h, n, "max", include_current=False),
                ctx.roll(ctx.l, n, "min", include_current=False))
    return ctx.cached(("b150_box", win_min), f)


def _breaks(ctx, win_min):
    """First close beyond the box high/low (one signal per break)."""
    def f():
        hi, lo = _box(ctx, win_min)
        return hi, lo, ctx.cross(_gt(ctx.c, hi)), ctx.cross(_lt(ctx.c, lo))
    return ctx.cached(("b150_breaks", win_min), f)


def _edge_share(ctx, win_min, side, frac):
    """Share of the window's closes lying in the top (side=+1) or bottom (side=-1) `frac` of the box."""
    def f():
        n = ctx.bars(win_min)
        hi, lo = _box(ctx, win_min)
        ht = hi - lo
        cnt = np.zeros(ctx.n)
        for k in range(1, n + 1):
            ck = ctx.prev(ctx.c, k)
            if side > 0:
                cnt += _gt(ck, hi - frac * ht - 1e-9) | _eq(ck, hi - frac * ht)
            else:
                cnt += _lt(ck, lo + frac * ht + 1e-9)
        return np.where(_gt(ht, 0.0), cnt / n, np.nan)
    return ctx.cached(("b150_share", win_min, side, frac), f)


def _typ_range(ctx):
    return ctx.cached("b150_typrange", lambda: ctx.same_minute(ctx.h - ctx.l, "median"))


# ----------------------------------------------------------------------------- families

def _mature_box_fade(ctx, p):
    hi, lo, up, dn = _breaks(ctx, p["win_min"])
    a = ctx.bars(p["age_min"])
    mature = _eq(ctx.prev(hi, a), hi) & _eq(ctx.prev(lo, a), lo)
    return _out(dn & mature, up & mature)


def _volume_tail_fade(ctx, p):
    def f():
        below = np.full(ctx.n, np.nan)
        above = np.full(ctx.n, np.nan)
        day = np.asarray(ctx.day)
        starts = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
        ends = np.r_[starts[1:], ctx.n]
        for s, e in zip(starts, ends):
            cs, vs = ctx.c[s:e], ctx.v[s:e]
            m = e - s
            tri = np.tril(np.ones((m, m), dtype=bool))
            lt = ((cs[None, :] < cs[:, None]) & tri).astype(float)
            gt = ((cs[None, :] > cs[:, None]) & tri).astype(float)
            tot = np.cumsum(vs)
            tot = np.where(tot > 0, tot, np.nan)
            below[s:e] = (lt @ vs) / tot
            above[s:e] = (gt @ vs) / tot
        return below, above
    below, above = ctx.cached("b150_voltail", f)
    _, _, up, dn = _breaks(ctx, p["win_min"])
    started = ctx.bar_in_day >= ctx.bars(30)
    short = up & _gt(below, p["q"]) & started
    long = dn & _gt(above, p["q"]) & started
    return _out(long, short)


def _open_straddle_fade(ctx, p):
    hi, lo, up, dn = _breaks(ctx, p["win_min"])
    ht = hi - lo
    pos = (ctx.day_open - lo) / np.where(_gt(ht, 0.0), ht, np.nan)
    ok = _gt(pos, p["m"]) & _lt(pos, 1.0 - p["m"])
    return _out(dn & ok, up & ok)


def _inner_contraction_fade(ctx, p):
    n = ctx.bars(p["win_min"])
    k = max(1, n // 2)
    h2 = ctx.roll(ctx.h, k, "max", include_current=False)
    l2 = ctx.roll(ctx.l, k, "min", include_current=False)
    h1 = ctx.prev(ctx.roll(ctx.h, max(1, n - k), "max", include_current=False), k)
    l1 = ctx.prev(ctx.roll(ctx.l, max(1, n - k), "min", include_current=False), k)
    contracting = _lt(h2, h1) & _gt(l2, l1) & ~_gt(h2 - l2, p["r"] * (h1 - l1))
    up = ctx.cross(_gt(ctx.c, h2)) & _lt(ctx.c, h1) & contracting
    dn = ctx.cross(_lt(ctx.c, l2)) & _gt(ctx.c, l1) & contracting
    return _out(dn, up)


def _yday_early_extremes_fade(ctx, p):
    def f():
        df = pd.DataFrame({"d": ctx.day, "h": ctx.h, "l": ctx.l})
        b = np.asarray(ctx.bar_in_day, float)
        ih = df.groupby("d")["h"].idxmax()
        il = df.groupby("d")["l"].idxmin()
        late = np.maximum(b[ih.to_numpy()], b[il.to_numpy()]) * ctx.tf
        per = pd.Series(late, index=ih.index).reindex(range(int(np.max(ctx.day)) + 1)).shift(1)
        return per.to_numpy()[ctx.day]
    last_ext = ctx.cached("b150_yday_late", f)
    early = ~_gt(last_ext, p["early_min"]) & np.isfinite(last_ext)
    _, _, up, dn = _breaks(ctx, p["win_min"])
    return _out(dn & early, up & early)


def _vwap_flythrough_fade(ctx, p):
    vw = ctx.vwap()
    dev = ctx.c - vw
    d = p["k"] * _typ_range(ctx)
    m = ctx.bars(p["m_min"])
    mn = ctx.roll(dev, m, "min", include_current=False)
    mx = ctx.roll(dev, m, "max", include_current=False)
    short = ctx.cross(_gt(dev, d)) & _lt(mn, -d)
    long = ctx.cross(_lt(dev, -d)) & _gt(mx, d)
    return _out(long, short)


def _alternating_break_fade(ctx, p):
    _, _, up, dn = _breaks(ctx, p["win_min"])
    e = up.astype(float) - dn.astype(float)
    b = np.asarray(ctx.bar_in_day, float)
    s = pd.DataFrame({"d": ctx.day, "e": np.where(e != 0, e, np.nan), "b": np.where(e != 0, b, np.nan)})
    g = s.groupby("d")
    last_e = g["e"].transform(lambda z: z.ffill().shift(1)).to_numpy(float)
    last_b = g["b"].transform(lambda z: z.ffill().shift(1)).to_numpy(float)
    recent = ~_gt(b - last_b, ctx.bars(p["within_min"])) & np.isfinite(last_b)
    short = up & _eq(last_e, -1.0) & recent
    long = dn & _eq(last_e, 1.0) & recent
    return _out(long, short)


def _far_edge_dwell_fade(ctx, p):
    _, _, up, dn = _breaks(ctx, p["win_min"])
    low_share = _edge_share(ctx, p["win_min"], -1, 0.5)
    high_share = _edge_share(ctx, p["win_min"], 1, 0.5)
    short = up & ~_lt(low_share, p["q"]) & np.isfinite(low_share)
    long = dn & ~_lt(high_share, p["q"]) & np.isfinite(high_share)
    return _out(long, short)


def _narrow_prior_day_follow(ctx, p):
    def f():
        R = pd.Series(ctx.h).groupby(ctx.day).max() - pd.Series(ctx.l).groupby(ctx.day).min()
        R = R.reindex(range(int(np.max(ctx.day)) + 1))
        r1 = R.shift(1)
        avg = r1.rolling(19, min_periods=19).mean()
        return (r1 / avg).to_numpy()[ctx.day]
    ratio = ctx.cached("b150_narrow_ratio", f)
    narrow = _lt(ratio, p["r"])
    _, _, up, dn = _breaks(ctx, p["win_min"])
    return _out(up & narrow, dn & narrow)


def _coiled_edge_follow(ctx, p):
    _, _, up, dn = _breaks(ctx, p["win_min"])
    top = _edge_share(ctx, p["win_min"], 1, 0.25)
    bot = _edge_share(ctx, p["win_min"], -1, 0.25)
    long = up & ~_lt(top, p["q"]) & np.isfinite(top)
    short = dn & ~_lt(bot, p["q"]) & np.isfinite(bot)
    return _out(long, short)


FAMILIES = [
    Family("E-1498", "Mature-box micro-break fade",
           "When neither edge of the short box has moved for a while, both edges are levels that resting liquidity "
           "has already defended; the first close beyond such a mature edge is usually a small order poking through "
           "and the defenders' remaining size pushes it back inside, so fade it.",
           {"win_min": [30, 60], "age_min": [10, 15, 20]}, _mature_box_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1499", "Session volume-tail break fade",
           "A box break made where almost all of today's volume traded on the other side (e.g. above the price at "
           "which 90% of the session's contracts changed hands) is a move into the thin tail of the day's "
           "distribution; responsive traders treat it as out of value and sell it back, so fade it.",
           {"win_min": [15, 30], "q": [0.85, 0.9, 0.95]}, _volume_tail_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1500", "Day-open straddle box break fade",
           "When the short box sits across the day's opening price, the market is still rotating around the "
           "session's first reference and no side has taken control of the day; a break of such a box is noise "
           "around the open, so fade it back into the box.",
           {"win_min": [15, 30, 60], "m": [0.1, 0.25, 0.4]}, _open_straddle_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1501", "Inner-contraction break fade inside the outer box",
           "When the second half of a window trades inside a much narrower range than the first half, a close "
           "beyond the narrow inner range that is still inside the outer range runs straight into the first half's "
           "extremes where earlier sellers/buyers sit; the release fails short of them, so fade it.",
           {"win_min": [20, 30, 60], "r": [0.5, 0.7, 0.9]}, _inner_contraction_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1502", "Day after early-set extremes micro-break fade",
           "When the previous session set both its high and its low early and then spent hours inside that range, "
           "participants carry a balanced, two-sided view into today; short box breaks on such days meet those "
           "range traders and fade back.",
           {"early_min": [90, 120, 180], "win_min": [15, 30]}, _yday_early_extremes_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1503", "VWAP fly-through overshoot fade",
           "When price races from well below the session VWAP to well above it within minutes (or the reverse), "
           "the move is driven by short covering and stops rather than by new value; once the flow is spent, price "
           "drifts back toward the VWAP, so fade the overshoot on the far side.",
           {"m_min": [10, 20, 30], "k": [1.0, 2.0, 3.0]}, _vwap_flythrough_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1504", "Alternating box-break fade",
           "If the last box break of the session went the other way only a short time ago, the tape is rotating "
           "between both edges; breakout traders keep getting trapped and liquidity providers fade each new break, "
           "so fade a break that reverses the previous break's direction.",
           {"win_min": [15, 30, 60], "within_min": [30, 60, 120]}, _alternating_break_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1505", "Far-edge dwell break fade",
           "When most of the window's closes sat in the half of the box opposite to the break, price accepted the "
           "far side and the break is a sudden excursion with no time spent building at the broken edge; the "
           "accepted side pulls it back, so fade it.",
           {"win_min": [15, 30, 60], "q": [0.5, 0.6, 0.7]}, _far_edge_dwell_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1506", "Narrow prior day box-break follow",
           "After a session whose range was well below its recent average (Crabel's narrow-range idea), volatility "
           "tends to expand the next day and positions built in the quiet day are offside on a break; follow "
           "short box breaks on the day after a narrow day.",
           {"r": [0.7, 0.8, 0.9], "win_min": [15, 30, 60]}, _narrow_prior_day_follow, markets=("WIN",),
           source="NR4/NR7 Narrow-range Bars https://www.luxalgo.com/library/concept/nr4-nr7-narrow-range-bars.md",
           author="agent"),
    Family("E-1507", "Coiled-edge break follow",
           "When a large share of the window's closes press against the box top without breaking it, buyers keep "
           "absorbing the offers there; the first close through that edge clears the last of the supply and "
           "stops above it, so follow the break (mirror at the bottom).",
           {"win_min": [15, 30, 60], "q": [0.3, 0.4, 0.5]}, _coiled_edge_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
