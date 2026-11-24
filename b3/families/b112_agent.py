"""Conveyor batch B-112 (agent, 2026-11-24). Oscillator/indicator-state ideas not yet screened: Qstick, TRIX, DeMarker,
Dual Thrust, positive-volume index, EMA ribbon, awesome oscillator, VWAP-side dominance, drift t-stat, mean-median skew."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _dir(ctx, up, dn):
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _qstick(ctx, p):
    nb = ctx.bars(p["win_min"])
    q = ctx.roll(ctx.c - ctx.o, nb, "mean")
    return _dir(ctx, q > 0, q < 0)


def _trix(ctx, p):
    n = max(2, ctx.bars(p["span_min"]))
    e3 = ctx.cached(("trix", n), lambda: ctx.ema(ctx.ema(ctx.ema(ctx.c, n), n), n))
    t = e3 - ctx.prev(e3, 1)
    return _dir(ctx, t > 0, t < 0)


def _demarker(ctx, p):
    nb = ctx.bars(p["win_min"])
    lo = p["lo"]
    up = np.maximum(ctx.h - ctx.prev(ctx.h, 1), 0.0)
    dn = np.maximum(ctx.prev(ctx.l, 1) - ctx.l, 0.0)
    su, sd = ctx.roll(up, nb, "mean"), ctx.roll(dn, nb, "mean")
    den = su + sd
    with np.errstate(divide="ignore", invalid="ignore"):
        dem = np.where(den > 0, su / den, np.nan)
    return _dir(ctx, dem > lo, dem < 1.0 - lo)


def _dual_thrust(ctx, p):
    n, k = int(p["n_sessions"]), p["k"]
    s = pd.DataFrame({"d": ctx.day, "h": ctx.h, "l": ctx.l, "c": ctx.c}).groupby("d").agg(
        hh=("h", "max"), ll=("l", "min"), hc=("c", "max"), lc=("c", "min"))
    s = s.reindex(range(int(ctx.day.max()) + 1)).shift(1)
    hh = s["hh"].rolling(n, min_periods=n).max()
    ll = s["ll"].rolling(n, min_periods=n).min()
    hc = s["hc"].rolling(n, min_periods=n).max()
    lc = s["lc"].rolling(n, min_periods=n).min()
    r = np.maximum(hh - lc, hc - ll).to_numpy()[ctx.day]
    upper, lower = ctx.day_open + k * r, ctx.day_open - k * r
    return _dir(ctx, ctx.c > upper, ctx.c < lower)


def _pvi(ctx, p):
    n = max(2, ctx.bars(p["ema_min"]))
    lr = np.log(ctx.c / ctx.prev(ctx.c, 1))
    vup = ctx.v > ctx.prev(ctx.v, 1)
    inc = np.where(vup & np.isfinite(lr), lr, 0.0)
    pvi = pd.Series(inc).groupby(ctx.day).cumsum().to_numpy()
    ema = ctx.ema(pvi, n)
    return _dir(ctx, pvi > ema, pvi < ema)


def _ribbon(ctx, p):
    a = max(2, ctx.bars(p["base_min"]))
    e1 = ctx.cached(("e", a), lambda: ctx.ema(ctx.c, a))
    e2 = ctx.cached(("e", 2 * a), lambda: ctx.ema(ctx.c, 2 * a))
    e3 = ctx.cached(("e", 4 * a), lambda: ctx.ema(ctx.c, 4 * a))
    return _dir(ctx, (e1 > e2) & (e2 > e3), (e1 < e2) & (e2 < e3))


def _ao(ctx, p):
    fast, slow = ctx.bars(5), ctx.bars(p["slow_min"])
    mp = (ctx.h + ctx.l) / 2.0
    ao = ctx.roll(mp, fast, "mean") - ctx.roll(mp, slow, "mean")
    return _dir(ctx, ao > 0, ao < 0)


def _vwap_dominance(ctx, p):
    nb, f = ctx.bars(p["win_min"]), p["frac"]
    vw = ctx.vwap()
    above = ctx.roll((ctx.c > vw).astype(float), nb, "mean", include_current=False)
    below = ctx.roll((ctx.c < vw).astype(float), nb, "mean", include_current=False)
    long = (above >= f) & (ctx.l <= vw) & (ctx.c > vw)
    short = (below >= f) & (ctx.h >= vw) & (ctx.c < vw)
    return _dir(ctx, long, short)


def _drift_t(ctx, p):
    th = p["th"]
    minbars = ctx.bars(30)
    lr = np.log(ctx.c / ctx.prev(ctx.c, 1))
    lr = np.where(np.isfinite(lr), lr, 0.0)
    cs = pd.Series(lr).groupby(ctx.day).cumsum().to_numpy()
    cs2 = pd.Series(lr * lr).groupby(ctx.day).cumsum().to_numpy()
    cnt = pd.Series(np.ones(ctx.n)).groupby(ctx.day).cumsum().to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where((cs2 > 0) & (cnt >= minbars), cs / np.sqrt(cs2), 0.0)
    return _dir(ctx, t > th, t < -th)


def _mean_median(ctx, p):
    nb = ctx.bars(p["win_min"])
    mean = ctx.roll(ctx.c, nb, "mean")
    med = pd.Series(ctx.c).groupby(ctx.day).transform(lambda z: z.rolling(nb, min_periods=nb).median()).to_numpy()
    gap = mean - med
    return _dir(ctx, gap > 0, gap < 0)


FAMILIES = [
    Family("E-1118", "Qstick zero-line cross follow",
           "The average bar body (close minus open) over a window turning positive means buyers have been winning "
           "the inside of the bars, not just the close; the aggressor side keeps pushing for a few more minutes.",
           {"win_min": [10, 20, 30]}, _qstick, source="assistant reasoning (Chande Qstick indicator)", author="assistant"
           if False else "agent"),
    Family("E-1119", "TRIX zero-line cross follow",
           "A triple-smoothed EMA turning up filters out noise; when even that slow line turns, the trend change "
           "is real and later participants chase it.",
           {"span_min": [5, 8, 12]}, _trix, source="assistant reasoning (Hutson TRIX)", author="agent"),
    Family("E-1120", "DeMarker exit from extreme, follow",
           "DeMarker compares new highs with new lows bar by bar; leaving the exhausted zone (below lo or above "
           "1-lo) shows the pressure that dominated has stopped, so trade the turn.",
           {"win_min": [10, 20, 30], "lo": [0.2, 0.3]}, _demarker, source="assistant reasoning (DeMark DeMarker)",
           author="agent"),
    Family("E-1121", "Dual Thrust open-trigger break",
           "The range of the last sessions sets how far the day must travel from its open to be a trending day; "
           "a close beyond open +/- k of that range attracts breakout orders and follows.",
           {"n_sessions": [3, 5], "k": [0.15, 0.25, 0.35]}, _dual_thrust,
           source="assistant reasoning (Dual Thrust system, Michael Chalek)", author="agent"),
    Family("E-1122", "Positive-volume-index trend cross follow",
           "Price moves on rising volume are made by the crowd; when that crowd-driven cumulative move crosses "
           "its own average, the crowd changes direction and later followers continue.",
           {"ema_min": [15, 30, 45]}, _pvi, source="assistant reasoning (Dysart positive volume index)", author="agent"),
    Family("E-1123", "EMA ribbon stack onset",
           "Three EMAs of doubling length lining up in order marks every horizon agreeing on direction for the "
           "first time; slower holders then join.",
           {"base_min": [3, 5, 8]}, _ribbon, source="assistant reasoning (EMA ribbon / Guppy idea)", author="agent"),
    Family("E-1124", "Awesome oscillator zero cross",
           "The 5-bar mean of the median price crossing a longer mean shows momentum overtaking the slower "
           "average of the market's fair price; follow it.",
           {"slow_min": [20, 34, 50]}, _ao, source="assistant reasoning (Bill Williams awesome oscillator)", author="agent"),
    Family("E-1125", "VWAP-side dominance dip",
           "When price spent nearly the whole window on one side of VWAP, institutional benchmark buyers or "
           "sellers are in control; a touch of VWAP that closes back on that side is where they add.",
           {"win_min": [30, 60, 90], "frac": [0.8, 0.9]}, _vwap_dominance,
           source="assistant reasoning (VWAP execution benchmark)", author="agent"),
    Family("E-1126", "Session-drift t-stat cross follow",
           "The day's cumulative return divided by its own realised noise is a signal-to-noise ratio; when it "
           "crosses a high level the drift is statistically distinct from a random walk and tends to persist.",
           {"th": [1.5, 2.0, 2.5]}, _drift_t, source="assistant reasoning (time-series momentum t-statistic)",
           author="agent"),
    Family("E-1127", "Mean-median price skew flip follow",
           "The mean of closes sitting above their median means the recent window has a tail of high prints "
           "not yet in the middle of the distribution; price drifts toward the tail.",
           {"win_min": [20, 30, 45]}, _mean_median, source="assistant reasoning (Pearson skewness mean-median)",
           author="agent"),
]
