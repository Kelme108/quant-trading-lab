"""Conveyor batch B-124 (agent, 2026-11-24). Mixed WIN/WDO ideas: autocorrelation regime, VWAP slope, volatility
expansion, clock-relative range, jump dominance, decelerating runs, VWAP bands, day-open recross, late VWAP pull,
efficiency ratio."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _ac_regime(ctx, p):
    nb, thr = ctx.bars(p["win_min"]), p["thr"]
    r = ctx.c - ctx.prev(ctx.c, 1)
    prod = r * ctx.prev(r, 1)
    ac = ctx.roll(prod, nb, "mean") / ctx.roll(r * r, nb, "mean")
    big = np.abs(r) >= ctx.roll(np.abs(r), nb, "mean", include_current=False)
    long = big & (((ac > thr) & (r > 0)) | ((ac < -thr) & (r < 0)))
    short = big & (((ac > thr) & (r < 0)) | ((ac < -thr) & (r > 0)))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _vwap_slope_dip(ctx, p):
    nb, thr = ctx.bars(p["win_min"]), p["slope"]
    vw = ctx.vwap()
    sl = vw / ctx.prev(vw, nb) - 1.0
    long = (sl > thr) & (ctx.l <= vw) & (ctx.c > vw)
    short = (sl < -thr) & (ctx.h >= vw) & (ctx.c < vw)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _vol_expansion(ctx, p):
    k, nl = p["k"], ctx.bars(p["long_min"])
    rng = ctx.h - ctx.l
    ns = ctx.bars(3)
    ratio = ctx.roll(rng, ns, "mean") / ctx.roll(rng, nl, "mean")
    body = np.abs(ctx.c - ctx.o) >= 0.5 * rng
    cond = (ratio > k) & body & (rng > 0)
    long = cond & (ctx.c > ctx.o)
    short = cond & (ctx.c < ctx.o)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _clock_range_fade(ctx, p):
    k = p["k"]
    rng = ctx.h - ctx.l
    med = ctx.cached("rng_med_b124", lambda: ctx.same_minute(rng, "median"))
    big = (rng >= k * med) & (med > 0)
    long = big & (ctx.c < ctx.o)
    short = big & (ctx.c > ctx.o)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _jump_dominance_fade(ctx, p):
    nb, share = ctx.bars(p["win_min"]), p["share"]
    d = ctx.c - ctx.prev(ctx.c, 1)
    s = ctx.roll(np.abs(d), nb, "sum")
    dom = (np.abs(d) >= share * s) & (s > 0)
    long = dom & (d < 0)
    short = dom & (d > 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _decel_run_fade(ctx, p):
    run = int(p["run"])
    rng = ctx.h - ctx.l
    up = np.ones(ctx.n, bool)
    dn = np.ones(ctx.n, bool)
    for j in range(run):
        c0, c1 = ctx.prev(ctx.c, j), ctx.prev(ctx.c, j + 1)
        r0, r1 = ctx.prev(rng, j), ctx.prev(rng, j + 1)
        up &= (c0 > c1) & (r0 < r1)
        dn &= (c0 < c1) & (r0 < r1)
    return ctx.cross(dn).astype(int) - ctx.cross(up).astype(int)


def _vwap_band_reentry(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    dev = ctx.c - ctx.vwap()
    sd = ctx.roll(dev, nb, "std")
    z = dev / sd
    zp = ctx.prev(z, 1)
    short = (zp > k) & (z < k)
    long = (zp < -k) & (z > -k)
    return long.astype(int) - short.astype(int)


def _day_open_recross(ctx, p):
    k = p["k"]
    r = ctx.c / ctx.day_open - 1.0
    typ = ctx.cached("abs_ret_b124", lambda: ctx.same_minute(np.abs(r), "mean"))
    mx = pd.Series(r).groupby(ctx.day).cummax().to_numpy()
    mn = pd.Series(r).groupby(ctx.day).cummin().to_numpy()
    mxp, mnp = ctx.prev(mx, 1), ctx.prev(mn, 1)
    short = (mxp >= k * typ) & (typ > 0) & (ctx.c < ctx.day_open)
    long = (mnp <= -k * typ) & (typ > 0) & (ctx.c > ctx.day_open)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _late_vwap_pull(ctx, p):
    k, start = p["k"], p["start_min"]
    dev = ctx.c / ctx.vwap() - 1.0
    typ = ctx.cached("abs_dev_b124", lambda: ctx.same_minute(np.abs(dev), "mean"))
    late = ctx.minute >= start
    long = late & (typ > 0) & (dev < -k * typ)
    short = late & (typ > 0) & (dev > k * typ)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _efficiency_follow(ctx, p):
    nb, thr = ctx.bars(p["win_min"]), p["thr"]
    d = np.abs(ctx.c - ctx.prev(ctx.c, 1))
    path = ctx.roll(d, nb, "sum")
    net = ctx.c - ctx.prev(ctx.c, nb)
    er = np.abs(net) / path
    long = (er > thr) & (net > 0)
    short = (er > thr) & (net < 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


FAMILIES = [
    Family("E-1238", "Autocorrelation regime switch",
           "When recent bar-to-bar changes are positively autocorrelated the tape is trending (follow a large bar); when "
           "negatively autocorrelated it is bouncing between quoters (fade a large bar).",
           {"win_min": [30, 60, 90], "thr": [0.1, 0.2, 0.3]}, _ac_regime, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1239", "Rising-VWAP dip touch",
           "In a session whose VWAP is climbing, institutional buyers benchmarked to VWAP step in on a touch; a wick to "
           "VWAP that closes above it is a buy (mirror for falling VWAP).",
           {"win_min": [20, 30, 60], "slope": [0.0005, 0.001, 0.0015]}, _vwap_slope_dip, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1240", "Volatility-expansion bar follow",
           "When the last few bars' range jumps relative to the recent average and the bar has a solid body, new "
           "information is being priced and the direction tends to persist a few minutes.",
           {"k": [1.5, 2.0, 2.5], "long_min": [30, 60]}, _vol_expansion, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1241", "Outsized-for-the-clock bar fade",
           "A bar whose range is several times the usual range at that time of day is often a liquidity sweep or "
           "market-order burst; liquidity providers fade it back.",
           {"k": [2.0, 3.0, 4.0]}, _clock_range_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1242", "Single-bar jump dominance fade",
           "When one bar accounts for a large share of all the movement of the window, the move is a jump (a shock or "
           "a stop run) rather than a trend, and tends to retrace.",
           {"win_min": [30, 60, 90], "share": [0.25, 0.35, 0.5]}, _jump_dominance_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1243", "Decelerating run exhaustion fade",
           "A run of consecutive higher closes with each bar's range smaller than the last shows buyers running out of "
           "force; the first break of the pattern marks a pause or reversal.",
           {"run": [3, 4, 5]}, _decel_run_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1244", "VWAP deviation band re-entry",
           "A close back inside a band of k standard deviations around VWAP after trading outside means the stretch "
           "failed to attract follow-through; revert toward VWAP.",
           {"win_min": [60, 90, 120], "k": [1.5, 2.0, 2.5]}, _vwap_band_reentry, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1245", "Day-open recross follow",
           "After a day has moved clearly above (below) its open, a close back through the open invalidates the day's "
           "bias and shifts control to the other side; follow the recross.",
           {"k": [0.5, 1.0, 1.5]}, _day_open_recross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1246", "Late-session VWAP pull",
           "Late in the session, accounts executing at VWAP and position squaring pull price back toward VWAP when it "
           "is stretched beyond its usual late-day distance.",
           {"k": [1.0, 1.5, 2.0], "start_min": [900, 930, 960]}, _late_vwap_pull, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1247", "Efficiency-ratio trend onset follow",
           "When net movement over a window is nearly all of the path travelled (Kaufman efficiency ratio high), the "
           "tape has one-sided flow that tends to persist for a few more minutes.",
           {"win_min": [20, 30, 60], "thr": [0.5, 0.6, 0.7]}, _efficiency_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
