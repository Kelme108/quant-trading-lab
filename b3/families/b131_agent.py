"""Conveyor batch B-131 (agent, 2026-11-24). Mixed themes on WIN: VWAP slope, bar gaps, rolling VWAP, volume ladder,
gap fill, bar overlap, large-bar dips, outside bars, wick pressure, opening-range midpoint."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _vwap_slope_pullback(ctx, p):
    nb, k = ctx.bars(p["slope_min"]), p["k"]
    vw = ctx.vwap()
    slope = vw / ctx.prev(vw, nb) - 1.0
    typ = ctx.cached(("vslope", nb), lambda: ctx.prev_sessions(np.abs(slope), "mean"))
    long = (slope >= k * typ) & (ctx.l <= vw) & (ctx.c > vw)
    short = (slope <= -k * typ) & (ctx.h >= vw) & (ctx.c < vw)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _bar_gap_fade(ctx, p):
    k = p["k"]
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    typ = ctx.cached("rng_mean", lambda: ctx.prev_sessions(ctx.h - ctx.l, "mean"))
    gap_up = (ctx.l - h1) > k * typ
    gap_dn = (l1 - ctx.h) > k * typ
    return gap_dn.astype(int) - gap_up.astype(int)


def _rolling_vwap_cross(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    pv = ctx.roll(ctx.c * ctx.v, nb, "sum")
    vs = ctx.roll(ctx.v, nb, "sum")
    with np.errstate(divide="ignore", invalid="ignore"):
        rv = np.where(vs > 0, pv / vs, np.nan)
    avg = ctx.roll(ctx.h - ctx.l, nb, "mean")
    valid = ~np.isnan(ctx.prev(rv, 1))
    up = valid & ((ctx.c - rv) > k * avg)
    dn = valid & ((rv - ctx.c) > k * avg)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _volume_ladder(ctx, p):
    n, vk = int(p["n"]), p["vol_k"]
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    up = np.ones(ctx.n, bool)
    dn = np.ones(ctx.n, bool)
    for i in range(n):
        vi, vj = ctx.prev(ctx.v, i), ctx.prev(ctx.v, i + 1)
        ci, cj = ctx.prev(ctx.c, i), ctx.prev(ctx.c, i + 1)
        up &= (vi > vj) & (ci > cj)
        dn &= (vi > vj) & (ci < cj)
    big = ctx.v >= vk * med
    return ctx.cross(up & big).astype(int) - ctx.cross(dn & big).astype(int)


def _gap_fill_mid(ctx, p):
    gmin, lim = p["gap_min"], p["limit_min"]
    pc = ctx.prev_session_value("close")
    gap = ctx.day_open / pc - 1.0
    mid = (ctx.day_open + pc) / 2.0
    early = ctx.bar_in_day * ctx.tf < lim
    long = (gap <= -gmin) & (ctx.c > mid) & (ctx.c < pc) & early
    short = (gap >= gmin) & (ctx.c < mid) & (ctx.c > pc) & early
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _low_overlap_run(ctx, p):
    n, ovmax = int(p["n"]), p["ov_max"]
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    rng = ctx.h - ctx.l
    with np.errstate(divide="ignore", invalid="ignore"):
        ov = np.clip(np.minimum(ctx.h, h1) - np.maximum(ctx.l, l1), 0, None) / np.where(rng > 0, rng, np.nan)
    up = np.ones(ctx.n, bool)
    dn = np.ones(ctx.n, bool)
    for i in range(n):
        oi = ctx.prev(ov, i)
        ci, cj = ctx.prev(ctx.c, i), ctx.prev(ctx.c, i + 1)
        up &= (oi <= ovmax) & (ci > cj)
        dn &= (oi <= ovmax) & (ci < cj)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _trend_big_bar_dip(ctx, p):
    k, n = p["k"], ctx.bars(p["ema_min"])
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    avg = ctx.cached("avg_rng20", lambda: ctx.roll(ctx.h - ctx.l, 20, "mean", include_current=False))
    body = ctx.c - ctx.o
    long = (ctx.c > ema) & (body <= -k * avg)
    short = (ctx.c < ema) & (body >= k * avg)
    return long.astype(int) - short.astype(int)


def _outside_bar(ctx, p):
    q = p["q"]
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    rng = ctx.h - ctx.l
    pos = np.where(rng > 0, (ctx.c - ctx.l) / np.where(rng > 0, rng, 1.0), 0.5)
    out = (ctx.h > h1) & (ctx.l < l1)
    return (out & (pos >= 1 - q)).astype(int) - (out & (pos <= q)).astype(int)


def _wick_pressure(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    lw = np.minimum(ctx.o, ctx.c) - ctx.l
    uw = ctx.h - np.maximum(ctx.o, ctx.c)
    num = ctx.roll(lw - uw, nb, "sum")
    den = ctx.roll(ctx.h - ctx.l, nb, "sum")
    with np.errstate(divide="ignore", invalid="ignore"):
        net = np.where(den > 0, num / den, np.nan)
    return ctx.cross(net >= th).astype(int) - ctx.cross(net <= -th).astype(int)


def _or_mid_cross(ctx, p):
    nb = ctx.bars(p["range_min"])
    first = ctx.bar_in_day < nb
    g = pd.DataFrame({"d": ctx.day, "h": np.where(first, ctx.h, np.nan), "l": np.where(first, ctx.l, np.nan)})
    orh = g.groupby("d")["h"].transform("max").to_numpy()
    orl = g.groupby("d")["l"].transform("min").to_numpy()
    mid = (orh + orl) / 2.0
    done = ~first
    up = ctx.cross(ctx.c > mid) & done
    dn = ctx.cross(ctx.c < mid) & done
    return up.astype(int) - dn.astype(int)


W = ("WIN",)
FAMILIES = [
    Family("E-1308", "VWAP slope pullback",
           "When the session VWAP is rising unusually fast, institutional buyers benchmarked to VWAP defend it; a dip "
           "touching VWAP that closes back above is a continuation entry (mirrored for sells).",
           {"slope_min": [30, 60], "k": [1.0, 1.5, 2.0]}, _vwap_slope_pullback, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1309", "Bar-gap vacuum fade",
           "A bar whose whole range lies beyond the previous bar's range crossed an empty book; the overshoot "
           "tends to be partly given back, so fade the gap bar.",
           {"k": [0.0, 0.25, 0.5]}, _bar_gap_fade, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1310", "Rolling VWAP cross follow",
           "A close that moves away from the volume-weighted average price of the last N minutes shows recent "
           "volume is being done at worse prices for the other side; follow the cross.",
           {"win_min": [15, 30, 60], "k": [0.0, 0.5, 1.0]}, _rolling_vwap_cross, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1311", "Volume ladder follow",
           "Rising volume on each of several consecutive closes in one direction means participation is building "
           "behind the move rather than fading; follow.",
           {"n": [2, 3, 4], "vol_k": [1.0, 1.5]}, _volume_ladder, markets=W, source="assistant reasoning",
           author="agent"),
    Family("E-1312", "Gap-fill midpoint continuation",
           "After an opening gap, positioning from the prior session is trapped; once price retraces half the gap "
           "early in the session, the fill toward yesterday's close tends to be completed.",
           {"gap_min": [0.001, 0.002, 0.004], "limit_min": [90, 180]}, _gap_fill_mid, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1313", "Low-overlap trending bars",
           "Consecutive bars that barely overlap their predecessor mean one side is taking all the liquidity "
           "offered at every price; follow that directional run.",
           {"n": [2, 3], "ov_max": [0.3, 0.5, 0.7]}, _low_overlap_run, markets=W, source="assistant reasoning",
           author="agent"),
    Family("E-1314", "Large-bar dip in trend",
           "In a trend (price on one side of a slow EMA) a single oversized counter-trend bar is mostly a "
           "liquidity flush by weak hands; trade back with the trend at its close.",
           {"k": [1.0, 1.5, 2.0], "ema_min": [60, 120]}, _trend_big_bar_dip, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1315", "Outside bar strong close",
           "A bar that takes out both the previous high and low and closes near one end has cleared stops on both "
           "sides and shown who won; follow the close.",
           {"q": [0.2, 0.3, 0.4]}, _outside_bar, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1316", "Wick pressure accumulation",
           "A rolling excess of lower over upper wicks shows sellers repeatedly rejected by resting bids (or the "
           "reverse); follow the side that keeps defending.",
           {"win_min": [10, 20, 30], "th": [0.3, 0.4, 0.5]}, _wick_pressure, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1317", "Opening-range midpoint cross",
           "After the opening range is set, its midpoint is the balance point; a close crossing it shows the "
           "auction leaning to that side, so follow each crossing.",
           {"range_min": [15, 30, 60]}, _or_mid_cross, markets=W, source="assistant reasoning", author="agent"),
]
