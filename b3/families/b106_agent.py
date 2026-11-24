"""Conveyor batch B-106 (agent, 2026-11-24). Mixed themes: clock drift, gap anchors, absorption, compression, regime, trend structure."""
from __future__ import annotations

import numpy as np

from b3.esteira import Family


def _ret(ctx):
    r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    return np.nan_to_num(r, nan=0.0)


def _clock_drift(ctx, p):
    k = p["k"]
    r = _ret(ctx)
    m = ctx.cached("cd_mean", lambda: ctx.same_minute(r, "mean"))
    a = ctx.cached("cd_abs", lambda: ctx.same_minute(np.abs(r), "mean"))
    t = m / (a + 1e-12)
    return ctx.cross(t > k).astype(int) - ctx.cross(t < -k).astype(int)


def _gap_hold_prior_close(ctx, p):
    g = p["gap_frac"]
    pc = ctx.prev_session_value("close")
    gap = ctx.day_open / pc - 1.0
    long = (gap >= g) & (ctx.l <= pc) & (ctx.c > pc)
    short = (gap <= -g) & (ctx.h >= pc) & (ctx.c < pc)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _absorption(ctx, p):
    k = p["vol_k"]
    nb = ctx.bars(30)
    rng = ctx.h - ctx.l
    med = ctx.cached("abs_vmed", lambda: ctx.same_minute(ctx.v, "median"))
    avg = ctx.roll(rng, nb, "mean", include_current=False)
    heavy = (ctx.v >= k * med) & (rng <= 0.7 * avg) & (rng > 0)
    at_hi = ctx.h >= ctx.session_high(False)
    at_lo = ctx.l <= ctx.session_low(False)
    return ctx.cross(heavy & at_lo).astype(int) - ctx.cross(heavy & at_hi).astype(int)


def _nr_break(ctx, p):
    n = int(p["n"])
    rng = ctx.h - ctx.l
    mn = ctx.roll(rng, n, "min")
    nr = (ctx.prev(rng, 1) == ctx.prev(mn, 1)) & (ctx.prev(rng, 1) > 0)
    long = nr & (ctx.c > ctx.prev(ctx.h, 1))
    short = nr & (ctx.c < ctx.prev(ctx.l, 1))
    return long.astype(int) - short.astype(int)


def _autocorr_regime(ctx, p):
    n, th = ctx.bars(p["win_min"]), p["th"]
    r = _ret(ctx)
    rp = np.nan_to_num(ctx.prev(r, 1), nan=0.0)
    num = ctx.roll(r * rp, n, "sum")
    den = ctx.roll(r * r, n, "sum") + 1e-18
    ac = num / den
    long = ((ac > th) & (r > 0)) | ((ac < -th) & (r < 0))
    short = ((ac > th) & (r < 0)) | ((ac < -th) & (r > 0))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _ribbon(ctx, p):
    f = int(p["fast"])
    e1 = ctx.cached(("rb", f), lambda: ctx.ema(ctx.c, f))
    e2 = ctx.cached(("rb", 2 * f), lambda: ctx.ema(ctx.c, 2 * f))
    e3 = ctx.cached(("rb", 4 * f), lambda: ctx.ema(ctx.c, 4 * f))
    up = (e1 > e2) & (e2 > e3)
    dn = (e1 < e2) & (e2 < e3)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _trend_day_break(ctx, p):
    k, nb = p["k"], ctx.bars(p["lookback_min"])
    r = ctx.c / ctx.day_open - 1.0
    typ = ctx.cached("abs_ret_same_minute", lambda: ctx.same_minute(np.abs(r), "mean"))
    rprev = ctx.prev(r, 1)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    long = (rprev <= -k * typ) & (ctx.c > hi)
    short = (rprev >= k * typ) & (ctx.c < lo)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _indecision_cluster(ctx, p):
    m, bf = int(p["m"]), p["body_frac"]
    rng = ctx.h - ctx.l
    small = ((np.abs(ctx.c - ctx.o) <= bf * rng) & (rng > 0)).astype(float)
    cl = ctx.roll(small, m, "min") == 1
    hi_c = ctx.prev(ctx.roll(ctx.h, m, "max"), 1)
    lo_c = ctx.prev(ctx.roll(ctx.l, m, "min"), 1)
    pcl = ctx.prev(cl.astype(float), 1) == 1
    long = pcl & (ctx.c > hi_c)
    short = pcl & (ctx.c < lo_c)
    return long.astype(int) - short.astype(int)


def _vwap_hug_departure(ctx, p):
    nb, b = ctx.bars(p["hug_min"]), p["band"]
    vw = ctx.vwap()
    dev = (ctx.c - vw) / vw
    hug = ctx.roll(np.abs(dev), nb, "max", include_current=False) <= b
    return ctx.cross(hug & (dev > b)).astype(int) - ctx.cross(hug & (dev < -b)).astype(int)


def _dual_anchor(ctx, p):
    b = p["buffer_frac"]
    pc = ctx.prev_session_value("close")
    hi = np.maximum(pc, ctx.day_open) * (1 + b)
    lo = np.minimum(pc, ctx.day_open) * (1 - b)
    return ctx.cross(ctx.c > hi).astype(int) - ctx.cross(ctx.c < lo).astype(int)


W = ("WIN",)
FAMILIES = [
    Family("E-1058", "Same-clock drift sign",
           "Some minutes of the session show a repeatable drift (scheduled flows, fixings, routine order slicing); "
           "the 20-session mean bar return at this clock minute, relative to its typical size, gives the side.",
           {"k": [0.2, 0.3, 0.4]}, _clock_drift, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1059", "Gap held at the prior close",
           "After a gap the prior close is where gap-fill traders step in; a dip to it that closes back on the gap "
           "side shows the fill was refused, so the gap direction resumes.",
           {"gap_frac": [0.001, 0.002, 0.003]}, _gap_hold_prior_close, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1060", "Heavy-volume small-range absorption at the extreme",
           "Large volume with a narrow range at a fresh session extreme means passive orders absorb the aggressors; "
           "the aggressors are trapped and the price turns.",
           {"vol_k": [1.5, 2.0, 3.0]}, _absorption, markets=W,
           source="volume-price analysis (assistant reasoning)", author="agent"),
    Family("E-1061", "Narrowest-range bar break (NR-N)",
           "The narrowest bar of the last N bars marks a coil; the close beyond it releases stored volatility in "
           "that direction (Crabel NR4/NR7).",
           {"n": [4, 7, 10]}, _nr_break, markets=W,
           source="Crabel narrow-range patterns (assistant reasoning)", author="agent"),
    Family("E-1062", "Return autocorrelation regime",
           "Where recent bar returns are positively autocorrelated, orders are being sliced and the last bar's "
           "direction continues; where negative, bid-ask bounce dominates and it reverts.",
           {"win_min": [30, 60, 90], "th": [0.1, 0.2, 0.3]}, _autocorr_regime, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1063", "EMA ribbon alignment onset",
           "When three EMAs (f, 2f, 4f) first line up in order, the trend is broad across horizons and trend "
           "followers join; follow.",
           {"fast": [5, 8, 12]}, _ribbon, markets=W,
           source="practitioner EMA ribbon use (assistant reasoning)", author="agent"),
    Family("E-1064", "Trend-day structure break reversal",
           "On a day already trending beyond its usual size, a close beyond the recent counter-side extreme shows "
           "the trend holders giving up and late trend chasers are trapped.",
           {"k": [0.75, 1.0, 1.5], "lookback_min": [15, 30, 45]}, _trend_day_break, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1065", "Indecision cluster break",
           "Several small-body bars in a row mean buyers and sellers are balanced; the close beyond the cluster "
           "shows which side gave way.",
           {"m": [2, 3, 4], "body_frac": [0.3, 0.4]}, _indecision_cluster, markets=W,
           source="candlestick literature (assistant reasoning)", author="agent"),
    Family("E-1066", "VWAP hug then departure",
           "Price hugging the session VWAP means the fair value is agreed; the first close outside a thin band "
           "after a long hug shows a new imbalance, so follow it.",
           {"hug_min": [20, 30, 45], "band": [0.0004, 0.0007, 0.001]}, _vwap_hug_departure, markets=W,
           source="assistant reasoning", author="agent"),
    Family("E-1067", "Dual-anchor cross follow",
           "Prior close and today's open are the two reference prices; a close beyond both means everyone who "
           "bought or sold since yesterday is in profit or loss together, so the move follows.",
           {"buffer_frac": [0.0, 0.0003, 0.0006]}, _dual_anchor, markets=W,
           source="assistant reasoning", author="agent"),
]
