"""Conveyor batch B-056 (agent, 2026-11-21). Mixed themes: same-time history anchors, volume-weighted and anchored
fair-value stretches, order-flow proxies (bar gaps, close location, return-volume correlation), trend significance."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _div(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    return np.where(b > 0, a / np.where(b > 0, b, 1.0), np.nan)


def _both(ctx, long, short):
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _path_dev_fade(ctx, p):
    n, k = int(p["n_sessions"]), p["k"]
    r = ctx.c / ctx.day_open - 1.0
    path = ctx.cached(("path", n), lambda: ctx.same_minute(r, "mean", n=n))
    scale = ctx.cached("abs_path", lambda: ctx.same_minute(np.abs(r), "mean"))
    dev = r - path
    ok = (ctx.minute >= 600) & (scale > 0)
    long = ok & (dev <= -k * scale)
    short = ok & (dev >= k * scale)
    return _both(ctx, long, short)


def _same_minute_sign(ctx, p):
    nb, th = ctx.bars(p["horizon_min"]), p["th"]
    ret = np.nan_to_num(ctx.c / ctx.prev(ctx.c, nb) - 1.0)
    sg = np.sign(ret)
    m = ctx.cached(("sgm", nb), lambda: ctx.same_minute(sg, "mean"))
    long = m >= th
    short = m <= -th
    return _both(ctx, long, short)


def _rolling_vwap_fade(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    sv = ctx.roll(ctx.v, nb, "sum")
    spv = ctx.roll(ctx.c * ctx.v, nb, "sum")
    rv = _div(spv, sv)
    sd = ctx.roll(ctx.c, nb, "std")
    z = _div(ctx.c - rv, sd)
    short = z >= k
    long = z <= -k
    return _both(ctx, long, short)


def _gap_pressure(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    g = np.nan_to_num(np.sign(ctx.o - ctx.prev(ctx.c, 1)))
    s = ctx.roll(g, nb, "mean")
    return _both(ctx, s >= th, s <= -th)


def _anchored_vwap_fade(ctx, p):
    anchor, k = p["anchor_min"], p["k"]
    act = ctx.minute >= anchor
    pv = np.where(act, ctx.c * ctx.v, 0.0)
    vv = np.where(act, ctx.v, 0.0)
    cpv = pd.Series(pv).groupby(ctx.day).cumsum().to_numpy()
    cv = pd.Series(vv).groupby(ctx.day).cumsum().to_numpy()
    av = _div(cpv, cv)
    dev = ctx.c - av
    ad = np.where(act, np.nan_to_num(np.abs(dev)), 0.0)
    cnt = pd.Series(act.astype(float)).groupby(ctx.day).cumsum().to_numpy()
    mad = _div(pd.Series(ad).groupby(ctx.day).cumsum().to_numpy(), cnt)
    ok = act & (cnt >= ctx.bars(30)) & (ctx.minutes_to_close >= 15) & (mad > 0)
    short = ok & (dev >= k * mad)
    long = ok & (dev <= -k * mad)
    return _both(ctx, long, short)


def _cmf_follow(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    rng = ctx.h - ctx.l
    clv = np.where(rng > 0, ((ctx.c - ctx.l) - (ctx.h - ctx.c)) / np.where(rng > 0, rng, 1.0), 0.0)
    cmf = _div(ctx.roll(clv * ctx.v, nb, "sum"), ctx.roll(ctx.v, nb, "sum"))
    return _both(ctx, cmf >= th, cmf <= -th)


def _ret_vol_corr(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    r1 = np.nan_to_num(ctx.c / ctx.prev(ctx.c, 1) - 1.0)
    v = ctx.v
    mr, mv = ctx.roll(r1, nb, "mean"), ctx.roll(v, nb, "mean")
    cov = ctx.roll(r1 * v, nb, "mean") - mr * mv
    corr = _div(cov, ctx.roll(r1, nb, "std") * ctx.roll(v, nb, "std"))
    move = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    long = (corr >= th) & (move > 0)
    short = (corr >= th) & (move < 0)
    return _both(ctx, long, short)


def _day_open_recross(ctx, p):
    nb = ctx.bars(p["away_min"])
    below = (ctx.c < ctx.day_open).astype(float)
    above = (ctx.c > ctx.day_open).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    up = was_below & (ctx.c > ctx.day_open)
    dn = was_above & (ctx.c < ctx.day_open)
    return up.astype(int) - dn.astype(int)


def _slope_tstat(ctx, p):
    nb = max(5, ctx.bars(p["win_min"]))
    th = p["th"]
    y = ctx.c - ctx.day_open
    i = ctx.bar_in_day.astype(float)
    sy = ctx.roll(y, nb, "sum")
    siy = ctx.roll(i * y, nb, "sum")
    si = ctx.roll(i, nb, "sum")
    syy = ctx.roll(y * y, nb, "sum")
    sxx = nb * (nb * nb - 1.0) / 12.0
    sxy = siy - si * sy / nb
    syyc = syy - sy * sy / nb
    slope = sxy / sxx
    ssres = syyc - slope * sxy
    se2 = np.where(ssres > 0, ssres / (nb - 2) / sxx, np.nan)
    t = slope / np.sqrt(se2)
    return _both(ctx, t >= th, t <= -th)


def _median_stretch(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    med = pd.Series(ctx.c).groupby(ctx.day).transform(lambda z: z.rolling(nb, min_periods=nb).median()).to_numpy()
    scale = ctx.roll(ctx.h - ctx.l, nb, "mean")
    st = _div(ctx.c - med, scale)
    stn = _div(med - ctx.c, scale)
    short = st >= k
    long = stn >= k
    return _both(ctx, long, short)


FAMILIES = [
    Family("E-558", "Typical-path deviation fade",
           "Intraday paths repeat loosely across sessions (scheduled flows); when today's move from the open runs well "
           "beyond the average path of the previous sessions at this minute, the extra part is non-scheduled and "
           "tends to revert.",
           {"n_sessions": [1, 5, 20], "k": [0.5, 1.0, 1.5]}, _path_dev_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-559", "Same-minute return sign persistence",
           "Recurring clients (hedges, index rebalancers, ADR arbitrage) trade the same time window every day; if the "
           "trailing move into this minute had the same sign in most of the last 20 sessions, follow that sign.",
           {"horizon_min": [15, 30, 60], "th": [0.3, 0.4, 0.5]}, _same_minute_sign, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-560", "Rolling-window VWAP stretch fade",
           "Liquidity takers who push price far from the last hour's volume-weighted fair value pay to do so; the "
           "dealers who absorb it revert price toward the rolling VWAP.",
           {"win_min": [60, 90, 120], "k": [1.5, 2.0, 2.5]}, _rolling_vwap_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-561", "Bar-gap pressure follow",
           "A bar that opens above the previous close means the book was swept by aggressive market buys between "
           "prints; a run of such gap-ups shows one-sided urgency that continues.",
           {"win_min": [10, 20, 30], "th": [0.3, 0.5, 0.7]}, _gap_pressure, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-562", "Afternoon-anchored VWAP stretch fade",
           "Afternoon participants start from a fresh cost basis; a stretch from the VWAP anchored at midday, measured "
           "against its own typical stretch, is a late chase that reverts.",
           {"anchor_min": [660, 720, 780], "k": [1.5, 2.0, 2.5]}, _anchored_vwap_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-563", "Chaikin money-flow thrust follow",
           "When bars close near their highs (or lows) on volume repeatedly, the volume-weighted close location shows "
           "persistent buying (selling) pressure that carries on.",
           {"win_min": [20, 40, 60], "th": [0.1, 0.2, 0.3]}, _cmf_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-564", "Return-volume correlation follow",
           "When volume rises with up-moves (and falls with pullbacks) the move is driven by informed demand and "
           "continues; positive return-volume correlation plus a net move gives the side.",
           {"win_min": [20, 30, 60], "th": [0.2, 0.3, 0.4]}, _ret_vol_corr, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-565", "Day-open recross follow",
           "The day's open is the price where the overnight imbalance resolved; after a long stay on one side, the "
           "first close through it shows the other side has taken control.",
           {"away_min": [30, 60, 90]}, _day_open_recross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-566", "Trend-significance follow",
           "A statistically significant slope of price over the window (t-stat of the regression) separates a real "
           "directional flow from noise; follow when the t-statistic first crosses the threshold.",
           {"win_min": [30, 45, 60], "th": [4.0, 6.0, 8.0]}, _slope_tstat, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-567", "Median-anchored range stretch fade",
           "The rolling median ignores the burst prints that drag a mean; a close several average bar-ranges away "
           "from the median is an overshoot by impatient flow and reverts.",
           {"win_min": [30, 60, 90], "k": [3.0, 4.0, 5.0]}, _median_stretch, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
