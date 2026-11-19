"""Conveyor batch B-030 (agent, 2026-11-19). Mixed WIN ideas: broadening structure, the volume of the bar that made
the level, stale-level breaks, light-participation days, the flattening hour, the day after a trend day, bar overlap,
the intraday range-completion schedule, long detachment from VWAP and the window's volume centre."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


# ---------------------------------------------------------------------------------------------
# shared helpers (all causal, session-bounded)
# ---------------------------------------------------------------------------------------------

def _micro(ctx, win_min):
    nb = ctx.bars(win_min)
    hi = ctx.cached(("b030_hi", nb), lambda: ctx.roll(ctx.h, nb, "max", include_current=False))
    lo = ctx.cached(("b030_lo", nb), lambda: ctx.roll(ctx.l, nb, "min", include_current=False))
    up = ctx.cross(ctx.c > hi)
    dn = ctx.cross(ctx.c < lo)
    return hi, lo, up, dn


def _day_cumsum(ctx, x):
    return pd.Series(np.asarray(x, float)).groupby(ctx.day).cumsum().to_numpy()


def _sig(long, short):
    long = np.asarray(long, bool)
    short = np.asarray(short, bool)
    both = long & short
    return (long & ~both).astype(int) - (short & ~both).astype(int)


# ---------------------------------------------------------------------------------------------
# families
# ---------------------------------------------------------------------------------------------

def _broadening_fade(ctx, p):
    nb = ctx.bars(p["block_min"])
    ha = ctx.roll(ctx.h, nb, "max", include_current=False)
    la = ctx.roll(ctx.l, nb, "min", include_current=False)
    hb, lb = ctx.prev(ha, nb), ctx.prev(la, nb)
    broad = (ha > hb) & (la < lb)
    _, _, up, dn = _micro(ctx, p["win_min"])
    return _sig(dn & broad, up & broad)


def _level_bar_volume(ctx, nb):
    def calc():
        bh = np.full(ctx.n, -np.inf)
        bl = np.full(ctx.n, np.inf)
        vh = np.full(ctx.n, np.nan)
        vl = np.full(ctx.n, np.nan)
        for j in range(1, nb + 1):
            hj, lj, vj = ctx.prev(ctx.h, j), ctx.prev(ctx.l, j), ctx.prev(ctx.v, j)
            mh = hj > bh
            ml = lj < bl
            bh = np.where(mh, hj, bh)
            vh = np.where(mh, vj, vh)
            bl = np.where(ml, lj, bl)
            vl = np.where(ml, vj, vl)
        return vh, vl
    return ctx.cached(("b030_lvlvol", nb), calc)


def _weaker_than_level(ctx, p):
    nb = ctx.bars(p["win_min"])
    _, _, up, dn = _micro(ctx, p["win_min"])
    vh, vl = _level_bar_volume(ctx, nb)
    k = p["k"]
    short = up & (ctx.v < k * vh)
    long = dn & (ctx.v < k * vl)
    return _sig(long, short)


def _stale_level_follow(ctx, p):
    nb = ctx.bars(p["win_min"])
    m = min(max(1, ctx.bars(p["win_min"] * p["frac"])), nb - 1) if nb > 1 else 1
    hi, lo, up, dn = _micro(ctx, p["win_min"])
    hr = ctx.roll(ctx.h, m, "max", include_current=False)
    lr = ctx.roll(ctx.l, m, "min", include_current=False)
    long = up & (hr < hi)
    short = dn & (lr > lo)
    return _sig(long, short)


def _light_day_fade(ctx, p):
    cumv = ctx.cached("b030_cumv", lambda: _day_cumsum(ctx, ctx.v))
    typ = ctx.cached("b030_cumv_typ", lambda: ctx.same_minute(cumv, "median"))
    light = (cumv < p["q"] * typ) & (ctx.bar_in_day >= ctx.bars(30))
    _, _, up, dn = _micro(ctx, p["win_min"])
    return _sig(dn & light, up & light)


def _flatten_hour_fade(ctx, p):
    late = ctx.minutes_to_close <= p["horizon_min"]
    _, _, up, dn = _micro(ctx, p["win_min"])
    return _sig(dn & late, up & late)


def _after_trend_day_fade(ctx, p):
    ph, pl, pc = ctx.prev_session_value("high"), ctx.prev_session_value("low"), ctx.prev_session_value("close")
    rng = ph - pl
    with np.errstate(invalid="ignore", divide="ignore"):
        loc = np.where(rng > 0, (pc - pl) / rng, np.nan)
    q = p["q"]
    trend = (loc >= 1 - q) | (loc <= q)
    _, _, up, dn = _micro(ctx, p["win_min"])
    return _sig(dn & trend, up & trend)


def _overlap(ctx):
    def calc():
        h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
        inter = np.minimum(ctx.h, h1) - np.maximum(ctx.l, l1)
        union = np.maximum(ctx.h, h1) - np.minimum(ctx.l, l1)
        with np.errstate(invalid="ignore", divide="ignore"):
            ov = np.where(union > 0, np.maximum(inter, 0.0) / np.where(union > 0, union, 1.0), 1.0)
        return np.where(np.isnan(h1), np.nan, ov)
    return ctx.cached("b030_ov", calc)


def _overlap_fade(ctx, p):
    nb = ctx.bars(p["win_min"])
    ov = _overlap(ctx)
    ovm = ctx.roll(ov, nb, "mean", include_current=False)
    typ = ctx.cached("b030_ov_typ", lambda: ctx.prev_sessions(ov, "mean"))
    sticky = ovm > p["k"] * typ
    _, _, up, dn = _micro(ctx, p["win_min"])
    return _sig(dn & sticky, up & sticky)


def _late_extreme_fade(ctx, p):
    def sched():
        sh = pd.Series(ctx.h).groupby(ctx.day).cummax().to_numpy()
        sl = pd.Series(ctx.l).groupby(ctx.day).cummin().to_numpy()
        fh = pd.Series(ctx.h).groupby(ctx.day).transform("max").to_numpy()
        fl = pd.Series(ctx.l).groupby(ctx.day).transform("min").to_numpy()
        fin = fh - fl
        with np.errstate(invalid="ignore", divide="ignore"):
            frac = np.where(fin > 0, (sh - sl) / np.where(fin > 0, fin, 1.0), np.nan)
        # only earlier sessions' completion fractions are used (same_minute excludes the current session)
        return ctx.same_minute(frac, "mean")
    s = ctx.cached("b030_range_sched", sched)
    ripe = s >= p["q"]
    nh = ctx.cross(ctx.h > ctx.session_high(include_current=False))
    nl = ctx.cross(ctx.l < ctx.session_low(include_current=False))
    return _sig(nl & ripe, nh & ripe)


def _detached_vwap_fade(ctx, p):
    nb = ctx.bars(p["away_min"])
    vw = ctx.vwap()
    above = (ctx.l > vw).astype(float)
    below = (ctx.h < vw).astype(float)
    far_up = ctx.roll(above, nb, "min", include_current=False) == 1
    far_dn = ctx.roll(below, nb, "min", include_current=False) == 1
    _, _, up, dn = _micro(ctx, p["win_min"])
    return _sig(dn & far_dn, up & far_up)


def _volume_centre_fade(ctx, p):
    nb = ctx.bars(p["win_min"])
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    sv = ctx.roll(ctx.v, nb, "sum")
    with np.errstate(invalid="ignore", divide="ignore"):
        wv = ctx.roll(tp * ctx.v, nb, "sum") / np.where(sv > 0, sv, np.nan)
    sm = ctx.roll(tp, nb, "mean")
    width = ctx.roll(ctx.h, nb, "max") - ctx.roll(ctx.l, nb, "min")
    with np.errstate(invalid="ignore", divide="ignore"):
        skew = (wv - sm) / np.where(width > 0, width, np.nan)
    skew = ctx.prev(skew, 1)                    # the window that ends at the bar before the break
    _, _, up, dn = _micro(ctx, p["win_min"])
    th = p["th"]
    return _sig(dn & (skew > th), up & (skew < -th))


FAMILIES = [
    Family("E-298", "Broadening-window micro-break fade",
           "When the last block made both a higher high and a lower low than the block before it, the market is a "
           "megaphone: two-sided stop runs by players who push each edge to trigger the other side and then reverse; "
           "a further short-term break in that state is one more head-fake that the responsive side sells (buys), so "
           "fade it.",
           {"block_min": [20, 30, 60], "win_min": [10, 15, 30]}, _broadening_fade, markets=("WIN",),
           source="broadening formation megaphone https://www.chartguys.com/chart-patterns/broadening-formation-megaphone",
           author="agent"),
    Family("E-299", "Weaker-than-the-level break fade",
           "The bar that set the recent high was where the seller who capped it traded; a later close through that high "
           "on less volume than that bar means the breakers are smaller than the participant who defended the level, "
           "so his remaining size and the breakout buyers' stops reverse the break (mirror at the low).",
           {"win_min": [15, 30, 60], "k": [0.5, 0.75, 1.0]}, _weaker_than_level, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-300", "Stale micro-level break follow",
           "A window high made early in the window and not approached in the recent part of it has had time to collect "
           "the stops of shorts and the buy-stops of breakout traders; the first close through such a stale level "
           "releases that pile at once and the market orders carry the price on, unlike a level made a few bars ago.",
           {"win_min": [30, 60, 90], "frac": [0.3, 0.5, 0.7]}, _stale_level_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-301", "Light-participation day micro-break fade",
           "When the session's cumulative volume is well below its usual level for the time of day, the large "
           "institutional parent orders are absent and the book is run by local liquidity providers; short-term breaks "
           "then carry no initiator behind them and are leaned back, so fade them on light days.",
           {"q": [0.6, 0.75, 0.9], "win_min": [10, 15, 30]}, _light_day_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-302", "Flattening-hour micro-break fade",
           "In the last hour or two before the close, day traders who must be flat stop opening positions and only "
           "unwind, and position takers have done their day; short-term breaks then are bursts of liquidation into a "
           "book that refills, not new information, so fade them.",
           {"horizon_min": [60, 90, 120], "win_min": [10, 15, 30]}, _flatten_hour_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-303", "Day-after-trend-day micro-break fade",
           "A session that closed at its high or low was a trend day (Raschke, Crabel); the next session usually "
           "digests it in a range while the trend-day holders take profit and late entrants rebalance, so its "
           "short-term breaks are faded.",
           {"q": [0.1, 0.2, 0.3], "win_min": [10, 15, 30]}, _after_trend_day_fade, markets=("WIN",),
           source="Capturing Trend Days https://www.traderslog.com/?p=823", author="agent"),
    Family("E-304", "High bar-overlap micro-break fade",
           "When consecutive bars overlap far more than usual, every bar trades back through the previous one: the "
           "auction is rotating two-way with liquidity providers on both sides; a close beyond the window extreme in "
           "such a tape is one more rotation reaching an edge, so fade it.",
           {"win_min": [15, 30, 60], "k": [1.1, 1.25, 1.4]}, _overlap_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-305", "Range-completion-schedule late extreme fade",
           "The share of the day's final range already traded by each minute is stable across sessions; a new session "
           "high/low made at a time when, on recent days, the range was normally almost complete is an overshoot by "
           "late chasers that the day's done participants sell (buy) into, so fade it.",
           {"q": [0.6, 0.7, 0.8, 0.9]}, _late_extreme_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-306", "Long-detached-from-VWAP micro-break fade",
           "After price has traded entirely on one side of the session VWAP for a long time, everyone who traded at value "
           "is in profit and benchmark desks are behind; a new short-term break further away is where those holders "
           "take profit and VWAP-benchmarked orders lean against it, so fade the break (not the VWAP cross of E-001).",
           {"away_min": [30, 60, 90], "win_min": [10, 15, 30]}, _detached_vwap_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-307", "Window volume-centre lag break fade",
           "If the window's volume-weighted price sits below its plain average price, most contracts changed hands at "
           "the low side of the window: the up-moves came on little volume; an up-break of such a window is a light "
           "probe away from where the size traded and returns to it, so fade it (mirror for down-breaks).",
           {"win_min": [15, 30, 60], "th": [0.05, 0.1, 0.15]}, _volume_centre_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
