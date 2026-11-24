"""Conveyor batch B-136 (agent, 2026-11-24). Mixed themes: distribution shape, relative volume, semivariance,
time-in-range, volume/return correlation, clock-relative quiet breaks, overlap, range-vs-close vol, volume-bar level, doji."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _d(ctx, long, short):
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _ret(ctx):
    return ctx.c / ctx.prev(ctx.c, 1) - 1.0


def _skew_cross(ctx, p):
    n = ctx.bars(p["win_min"])
    mean = ctx.roll(ctx.c, n, "mean")
    med = pd.Series(ctx.c).groupby(ctx.day).transform(lambda z: z.rolling(n, min_periods=n).median()).to_numpy()
    return _d(ctx, (mean > med) & (ctx.c > mean), (mean < med) & (ctx.c < mean))


def _relvol_break(ctx, p):
    k = p["k"]
    nb = ctx.bars(p["win_min"])
    cumv = pd.Series(ctx.v).groupby(ctx.day).cumsum().to_numpy()
    typ = ctx.cached("cumv_typ", lambda: ctx.same_minute(cumv, "mean"))
    rv = cumv / typ
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    return _d(ctx, (rv >= k) & (ctx.c > hi) & (ctx.c > ctx.day_open),
              (rv >= k) & (ctx.c < lo) & (ctx.c < ctx.day_open))


def _semivar(ctx, p):
    n, th = ctx.bars(p["win_min"]), p["th"]
    r = _ret(ctx)
    ru = np.where(np.isnan(r), np.nan, np.where(r > 0, r * r, 0.0))
    rd = np.where(np.isnan(r), np.nan, np.where(r < 0, r * r, 0.0))
    su, sd = ctx.roll(ru, n, "sum"), ctx.roll(rd, n, "sum")
    share = su / (su + sd)
    return _d(ctx, share >= th, share <= 1 - th)


def _upper_half_share(ctx, p):
    n, th = ctx.bars(p["win_min"]), p["th"]
    hi, lo = ctx.roll(ctx.h, n, "max"), ctx.roll(ctx.l, n, "min")
    above = np.where(np.isnan(hi), np.nan, (ctx.c > (hi + lo) / 2).astype(float))
    share = ctx.roll(above, n, "mean")
    return _d(ctx, share >= th, share <= 1 - th)


def _retvol_corr(ctx, p):
    n, th = ctx.bars(p["win_min"]), p["th"]
    r = _ret(ctx)
    v = ctx.v
    mr, mv = ctx.roll(r, n, "mean"), ctx.roll(v, n, "mean")
    mrv = ctx.roll(r * v, n, "mean")
    vr = ctx.roll(r * r, n, "mean") - mr * mr
    vv = ctx.roll(v * v, n, "mean") - mv * mv
    with np.errstate(invalid="ignore", divide="ignore"):
        corr = (mrv - mr * mv) / np.sqrt(vr * vv)
    net = ctx.roll(r, n, "sum")
    return _d(ctx, (corr >= th) & (net > 0), (corr >= th) & (net < 0))


def _dead_tape_break(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    rng = ctx.h - ctx.l
    typ = ctx.cached("rng_typ", lambda: ctx.same_minute(rng, "mean"))
    avg = ctx.roll(rng, nb, "mean", include_current=False)
    typ_w = ctx.roll(typ, nb, "mean", include_current=False)
    quiet = avg < k * typ_w
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    return _d(ctx, quiet & (ctx.c > hi), quiet & (ctx.c < lo))


def _low_overlap(ctx, p):
    n, th = ctx.bars(p["win_min"]), p["th"]
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    inter = np.clip(np.minimum(ctx.h, h1) - np.maximum(ctx.l, l1), 0, None)
    union = np.maximum(ctx.h, h1) - np.minimum(ctx.l, l1)
    with np.errstate(invalid="ignore", divide="ignore"):
        ov = np.where(union > 0, inter / union, np.nan)
    ovm = ctx.roll(ov, n, "mean")
    net = ctx.c - ctx.prev(ctx.c, n)
    return _d(ctx, (ovm <= th) & (net > 0), (ovm <= th) & (net < 0))


def _whipsaw_fade(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    r = _ret(ctx)
    lr = np.log(ctx.h / ctx.l)
    park = ctx.roll(lr * lr, n, "sum") / (4 * np.log(2))
    cc = ctx.roll(r * r, n, "sum")
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = park / cc
    hi, lo = ctx.roll(ctx.h, n, "max"), ctx.roll(ctx.l, n, "min")
    with np.errstate(invalid="ignore", divide="ignore"):
        pos = (ctx.c - lo) / (hi - lo)
    return _d(ctx, (ratio >= k) & (pos <= 0.15), (ratio >= k) & (pos >= 0.85))


def _maxvol_level(ctx, p):
    b = p["buf"]
    g = pd.Series(ctx.v).groupby(ctx.day).cummax().to_numpy()
    isnew = ctx.v >= g
    mid = pd.Series(np.where(isnew, (ctx.h + ctx.l) / 2, np.nan))
    lvl = mid.groupby(ctx.day).ffill().to_numpy()
    return _d(ctx, ctx.c > lvl * (1 + b), ctx.c < lvl * (1 - b))


def _doji_pause(ctx, p):
    nb, k = ctx.bars(p["move_min"]), p["k"]
    move = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    typ = ctx.cached(("abs_move", nb), lambda: ctx.prev_sessions(np.abs(move), "mean"))
    rng = ctx.h - ctx.l
    doji = (np.abs(ctx.c - ctx.o) <= 0.25 * rng) & (rng > 0)
    d1, m1, t1 = ctx.prev(doji.astype(float), 1) == 1, ctx.prev(move, 1), ctx.prev(typ, 1)
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    return np.where(d1 & (m1 >= k * t1) & (ctx.c > h1), 1, 0) - np.where(d1 & (m1 <= -k * t1) & (ctx.c < l1), 1, 0)


W = ("WIN",)
FAMILIES = [
    Family("E-1358", "Mean-median skew cross",
           "When the rolling mean of closes moves above the rolling median while price is above the mean, recent "
           "prices are pulling the distribution up: a late trend of buyers lifting offers; follow.",
           {"win_min": [20, 30, 45]}, _skew_cross, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1359", "Relative cumulative volume break",
           "A session whose cumulative volume runs ahead of its usual pace has participants with size; a break of "
           "the recent range on the day's side of the open continues as they keep working orders.",
           {"k": [1.2, 1.5, 2.0], "win_min": [30, 60]}, _relvol_break, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1360", "Semivariance imbalance follow",
           "When nearly all recent squared returns come from up bars (or down bars), the move is one-sided pressure "
           "rather than noise; follow the dominant side.",
           {"win_min": [20, 30, 60], "th": [0.7, 0.8]}, _semivar, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1361", "Time spent in the upper half of the range",
           "Closing in the upper (lower) half of the rolling range for most of the window shows persistent "
           "acceptance of higher (lower) prices; follow when the share crosses the threshold.",
           {"win_min": [30, 60, 90], "th": [0.8, 0.9]}, _upper_half_share, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1362", "Volume-confirmed return follow",
           "When bar returns correlate positively with volume in a window that is net up (down), size is pushing "
           "price rather than absorbing it; follow.",
           {"win_min": [30, 60, 90], "th": [0.2, 0.3, 0.4]}, _retvol_corr, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1363", "Clock-relative dead tape break",
           "A window much quieter than the same clock time usually is, followed by a close beyond its range, means "
           "liquidity providers stepped away and a directional order is moving a thin book; follow.",
           {"win_min": [15, 30], "k": [0.5, 0.65, 0.8]}, _dead_tape_break, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1364", "Low bar-overlap trend",
           "Consecutive bars that barely overlap mean price is travelling without two-way trade; one-sided "
           "auction continues in the direction of the net move.",
           {"win_min": [10, 15, 30], "th": [0.3, 0.4, 0.5]}, _low_overlap, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1365", "Whipsaw-regime edge fade",
           "When intrabar ranges are large relative to close-to-close changes (Parkinson/close-vol ratio), price is "
           "whipsawing; a close at the window's extreme is likely to revert.",
           {"win_min": [20, 30, 60], "k": [1.5, 2.0, 3.0]}, _whipsaw_fade, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1366", "Session peak-volume bar level",
           "The bar with the most volume so far in the session marks where the most size changed hands; a close "
           "away from its midpoint shows which side lost, and price follows that side.",
           {"buf": [0.0002, 0.0005, 0.001]}, _maxvol_level, markets=W, source="assistant reasoning", author="agent"),
    Family("E-1367", "Doji pause continuation",
           "After a larger-than-usual move, a doji bar is a pause by profit-takers; a close beyond the doji in the "
           "direction of the move signals the trend resuming.",
           {"move_min": [10, 20, 30], "k": [1.0, 1.5]}, _doji_pause, markets=W, source="assistant reasoning", author="agent"),
]
