"""Conveyor batch B-100 (agent, 2026-11-24). Mixed theme: seasonality, regime switches, bands, intermarket, bar structure."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _seasonal_drift(ctx, p):
    nb, k = ctx.bars(p["horizon_min"]), p["k"]
    s = pd.Series(ctx.c)
    fwd = (s.groupby(ctx.day).shift(-nb) / s - 1.0).to_numpy()   # only read from PRIOR sessions by same_minute
    drift = ctx.cached(("sd_mean", nb), lambda: ctx.same_minute(fwd, "mean"))
    ab = ctx.cached(("sd_abs", nb), lambda: ctx.same_minute(np.abs(fwd), "mean"))
    long = drift > k * ab
    short = drift < -k * ab
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _autocorr_switch(ctx, p):
    n, th = ctx.bars(p["win_min"]), p["th"]
    r = ctx.c - ctx.prev(ctx.c, 1)
    r1 = ctx.prev(r, 1)
    num = ctx.roll(r * r1, n, "sum")
    den = ctx.roll(r * r, n, "sum")
    ac = np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)
    avg_abs = ctx.roll(np.abs(r), n, "mean")
    big = np.abs(r) >= avg_abs
    long = big & (((ac <= -th) & (r < 0)) | ((ac >= th) & (r > 0)))
    short = big & (((ac <= -th) & (r > 0)) | ((ac >= th) & (r < 0)))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _vwap_band_fade(ctx, p):
    k = p["k"]
    warm = ctx.bars(p["min_min"])
    vw = ctx.vwap()
    dev = ctx.c - vw
    cs = pd.Series(dev * dev).groupby(ctx.day).cumsum().to_numpy()
    sd = np.sqrt(cs / (ctx.bar_in_day + 1.0))
    ok = ctx.bar_in_day >= warm
    short = ok & (dev > k * sd) & (sd > 0)
    long = ok & (dev < -k * sd) & (sd > 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _profile_deviation(ctx, p):
    k = p["k"]
    warm = ctx.bars(p["min_min"])
    r = ctx.c / ctx.day_open - 1.0
    prof = ctx.cached("pd_prof", lambda: ctx.same_minute(r, "mean"))
    typ = ctx.cached("pd_typ", lambda: ctx.same_minute(np.abs(r), "mean"))
    dev = r - prof
    ok = ctx.bar_in_day >= warm
    short = ok & (dev > k * typ)
    long = ok & (dev < -k * typ)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _slope_tstat(ctx, p):
    n, th = max(4, ctx.bars(p["win_min"])), p["th"]
    y = ctx.c - ctx.day_open
    x = ctx.bar_in_day.astype(float)
    sx = ctx.roll(x, n, "sum")
    sy = ctx.roll(y, n, "sum")
    sxx = ctx.roll(x * x, n, "sum")
    sxy = ctx.roll(x * y, n, "sum")
    syy = ctx.roll(y * y, n, "sum")
    cxx = sxx - sx * sx / n
    cxy = sxy - sx * sy / n
    cyy = syy - sy * sy / n
    slope = np.where(cxx > 0, cxy / np.where(cxx > 0, cxx, 1.0), np.nan)
    sse = cyy - slope * cxy
    ok = (sse > 1e-9) & (cxx > 0)
    se = np.sqrt(np.where(ok, sse, 1.0) / (n - 2) / np.where(cxx > 0, cxx, 1.0))
    t = np.where(ok, slope / se, np.nan)
    return ctx.cross(t > th).astype(int) - ctx.cross(t < -th).astype(int)


def _intermarket_confirm(ctx, p):
    nb, k = ctx.bars(p["move_min"]), p["k"]
    oc = ctx.other_close()
    wr = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    dr = oc / ctx.prev(oc, nb) - 1.0
    tw = ctx.cached(("im_w", nb), lambda: ctx.prev_sessions(np.abs(wr), "mean"))
    td = ctx.cached(("im_d", nb), lambda: ctx.prev_sessions(np.abs(dr), "mean"))
    long = (wr >= k * tw) & (dr <= -k * td)
    short = (wr <= -k * tw) & (dr >= k * td)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _ema_ribbon(ctx, p):
    f = ctx.bars(p["base_min"])
    m = int(p["slow_mult"])
    e1 = ctx.cached(("rb", f), lambda: ctx.ema(ctx.c, max(f, 2)))
    e2 = ctx.cached(("rb", 2 * f), lambda: ctx.ema(ctx.c, 2 * f))
    e3 = ctx.cached(("rb", m * f), lambda: ctx.ema(ctx.c, m * f))
    long = (ctx.c > e1) & (e1 > e2) & (e2 > e3)
    short = (ctx.c < e1) & (e1 < e2) & (e2 < e3)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _low_overlap_trend(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    rng = ctx.h - ctx.l
    inter = np.maximum(0.0, np.minimum(ctx.h, h1) - np.maximum(ctx.l, l1))
    ov = np.where(rng > 0, inter / np.where(rng > 0, rng, 1.0), 1.0)
    ov = np.where(np.isnan(h1), np.nan, ov)
    avg = ctx.roll(ov, nb, "mean")
    net = ctx.c - ctx.prev(ctx.c, nb)
    long = (avg <= th) & (net > 0) & (ctx.c > ctx.o)
    short = (avg <= th) & (net < 0) & (ctx.c < ctx.o)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _stall_release(ctx, p):
    nb, q = ctx.bars(p["win_min"]), p["frac"]
    flat = (ctx.c == ctx.prev(ctx.c, 1)).astype(float)
    flat = np.where(np.isnan(ctx.prev(ctx.c, 1)), np.nan, flat)
    stalled = ctx.roll(flat, nb, "mean") >= q
    was = ctx.prev(stalled.astype(float), 1) == 1
    d = ctx.c - ctx.prev(ctx.c, 1)
    long = was & (d > 0)
    short = was & (d < 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _busy_day_ema_cross(ctx, p):
    k, n = p["k"], max(2, ctx.bars(p["ema_min"]))
    cv = pd.Series(ctx.v).groupby(ctx.day).cumsum().to_numpy()
    typ = ctx.cached("cv_typ", lambda: ctx.same_minute(cv, "median"))
    busy = cv >= k * typ
    ema = ctx.cached(("bd_ema", n), lambda: ctx.ema(ctx.c, n))
    vw = ctx.vwap()
    long = busy & (ctx.c > ema) & (ctx.c > vw)
    short = busy & (ctx.c < ema) & (ctx.c < vw)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


FAMILIES = [
    Family("E-998", "Seasonal minute-of-day drift follow",
           "The forward return from a given minute of the day has a persistent sign (scheduled flows, fixings, "
           "participant rhythm); when the last 20 sessions agree strongly, take that side.",
           {"horizon_min": [10, 20, 30], "k": [0.4, 0.6, 0.8]}, _seasonal_drift,
           source="assistant reasoning", author="agent"),
    Family("E-999", "Autocorrelation regime switch",
           "When recent bar returns are negatively autocorrelated the market is in a bounce regime (fade the big bar); "
           "when positively autocorrelated it is in a push regime (follow the big bar).",
           {"win_min": [30, 60, 90], "th": [0.15, 0.25, 0.35]}, _autocorr_switch,
           source="assistant reasoning", author="agent"),
    Family("E-1000", "VWAP standard-deviation band fade",
           "Price stretching beyond k standard deviations of its own session distance to VWAP is an outlier for "
           "that day's volatility; liquidity providers anchored to VWAP lean against it.",
           {"k": [1.5, 2.0, 2.5], "min_min": [30, 60]}, _vwap_band_fade,
           source="assistant reasoning", author="agent"),
    Family("E-1001", "Intraday-profile deviation fade",
           "Compared with the average path of the last 20 sessions at the same minute, a day that has run much "
           "further than the usual profile has pulled forward the move; fade the excess.",
           {"k": [0.75, 1.0, 1.5], "min_min": [30, 60, 120]}, _profile_deviation,
           source="assistant reasoning", author="agent"),
    Family("E-1002", "Regression-slope t-stat trend follow",
           "A statistically significant linear slope of recent closes (t-stat) separates a real directional "
           "flow from noise; follow when the t-stat first crosses the threshold.",
           {"win_min": [20, 30, 45], "th": [3.0, 4.0, 5.0]}, _slope_tstat,
           source="assistant reasoning", author="agent"),
    Family("E-1003", "Index-dollar inverse confirmation follow",
           "WIN rising while the dollar falls (or vice versa), both by more than usual, is the macro risk-on/off "
           "link agreeing with itself; foreign flow keeps pushing the index the same way.",
           {"move_min": [10, 20, 30], "k": [1.0, 1.5, 2.0]}, _intermarket_confirm,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1004", "Three-EMA ribbon alignment follow",
           "When price and three EMAs of increasing length line up in order, short, medium and slow holders are "
           "all on the same side; the first aligned bar starts a trend leg.",
           {"base_min": [3, 5, 8], "slow_mult": [4, 6, 8]}, _ema_ribbon,
           source="assistant reasoning", author="agent"),
    Family("E-1005", "Low-overlap trend-bar follow",
           "Consecutive bars that barely overlap the previous bar's range mean one side is absorbing all "
           "liquidity without negotiation; follow the net move.",
           {"win_min": [5, 10, 15], "th": [0.3, 0.4, 0.5]}, _low_overlap_trend,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1006", "Stalled-close release follow",
           "A stretch where many bars close at exactly the same price means resting orders are pinning the "
           "tape; the first bar that closes away from the pin shows which side gave in.",
           {"win_min": [10, 15, 20], "frac": [0.2, 0.3, 0.4]}, _stall_release,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1007", "Busy-day EMA and VWAP agreement follow",
           "On sessions where cumulative volume runs well above the same-time norm, trends persist; price "
           "regaining both its EMA and VWAP on the same side is a pullback ending.",
           {"k": [1.1, 1.3, 1.6], "ema_min": [20, 30, 60]}, _busy_day_ema_cross,
           markets=("WIN",), source="assistant reasoning", author="agent"),
]
