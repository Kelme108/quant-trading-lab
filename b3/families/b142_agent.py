"""Conveyor batch B-142 (agent, 2026-11-24). Regime statistics (autocorrelation, regression, price-volume), bands and compression."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from b3.esteira import Family


def _ret(ctx):
    return ctx.c / ctx.prev(ctx.c, 1) - 1.0


def _regress(ctx, nb):
    """Rolling least-squares line of close on bar_in_day over nb bars (inside one session). Returns fit_end, resid sd, t-stat."""
    def build():
        x = ctx.bar_in_day.astype(float)
        c = pd.Series(ctx.c)
        mc = c.rolling(nb, min_periods=nb).mean().to_numpy()
        mx = pd.Series(x).rolling(nb, min_periods=nb).mean().to_numpy()
        mxc = pd.Series(x * ctx.c).rolling(nb, min_periods=nb).mean().to_numpy()
        mcc = pd.Series(ctx.c * ctx.c).rolling(nb, min_periods=nb).mean().to_numpy()
        varx = (nb * nb - 1) / 12.0
        slope = (mxc - mx * mc) / varx
        varc = np.maximum(mcc - mc * mc, 0.0)
        resid = np.maximum(varc - slope * slope * varx, 0.0)
        sd = np.sqrt(resid)
        fit_end = mc + slope * (nb - 1) / 2.0
        with np.errstate(divide="ignore", invalid="ignore"):
            t = slope * math.sqrt(varx) * math.sqrt(max(nb - 2, 1)) / np.where(sd > 0, sd, np.nan)
        ok = ctx.bar_in_day >= nb - 1
        return (np.where(ok, fit_end, np.nan), np.where(ok, sd, np.nan), np.where(ok, t, np.nan))
    return ctx.cached(("regress", nb), build)


def _autocorr_regime(ctx, p):
    nb = max(8, ctx.bars(p["win_min"]))
    th = p["th"]
    r = _ret(ctx)
    r1 = ctx.prev(r, 1)
    ac = pd.Series(r).rolling(nb, min_periods=nb).corr(pd.Series(r1)).to_numpy()
    ac = np.where(ctx.bar_in_day >= nb + 1, ac, np.nan)
    up, dn = r > 0, r < 0
    long = ((ac < -th) & dn) | ((ac > th) & up)
    short = ((ac < -th) & up) | ((ac > th) & dn)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _regression_channel_fade(ctx, p):
    nb = max(8, ctx.bars(p["win_min"]))
    k = p["k"]
    fit, sd, _ = _regress(ctx, nb)
    short = ctx.c > fit + k * sd
    long = ctx.c < fit - k * sd
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _slope_t_follow(ctx, p):
    nb = max(8, ctx.bars(p["win_min"]))
    th = p["th"]
    _, _, t = _regress(ctx, nb)
    return ctx.cross(t > th).astype(int) - ctx.cross(t < -th).astype(int)


def _ribbon_onset(ctx, p):
    a = max(2, ctx.bars(p["base_min"]))
    f = ctx.cached(("ema", a), lambda: ctx.ema(ctx.c, a))
    m = ctx.cached(("ema", 2 * a), lambda: ctx.ema(ctx.c, 2 * a))
    s = ctx.cached(("ema", 4 * a), lambda: ctx.ema(ctx.c, 4 * a))
    up = (f > m) & (m > s) & (ctx.c > f)
    dn = (f < m) & (m < s) & (ctx.c < f)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _triangle_break(ctx, p):
    nb = max(6, ctx.bars(p["win_min"]))
    half = nb // 2
    ratio = p["ratio"]
    hi_all = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo_all = ctx.roll(ctx.l, nb, "min", include_current=False)
    hi_rec = ctx.roll(ctx.h, half, "max", include_current=False)
    lo_rec = ctx.roll(ctx.l, half, "min", include_current=False)
    squeeze = (hi_all > hi_rec) & (lo_all < lo_rec) & ((hi_rec - lo_rec) <= ratio * (hi_all - lo_all))
    long = squeeze & (ctx.c > hi_rec)
    short = squeeze & (ctx.c < lo_rec)
    return long.astype(int) - short.astype(int)


def _keltner_reentry(ctx, p):
    n = max(6, ctx.bars(p["ema_min"]))
    k = p["k"]
    mid = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    atr = ctx.cached(("atr", n), lambda: ctx.roll(ctx.h - ctx.l, n, "mean"))
    up, lo = mid + k * atr, mid - k * atr
    short = (ctx.prev(ctx.c, 1) > ctx.prev(up, 1)) & (ctx.c < up)
    long = (ctx.prev(ctx.c, 1) < ctx.prev(lo, 1)) & (ctx.c > lo)
    return long.astype(int) - short.astype(int)


def _vwap_sigma_reentry(ctx, p):
    k, m = p["k"], max(5, ctx.bars(p["warm_min"]))
    dev = ctx.c - ctx.vwap()
    sd = pd.Series(dev).groupby(ctx.day).transform(lambda z: z.expanding(min_periods=m).std(ddof=0)).to_numpy()
    d1, s1 = ctx.prev(dev, 1), ctx.prev(sd, 1)
    short = (d1 > k * s1) & (dev < k * sd)
    long = (d1 < -k * s1) & (dev > -k * sd)
    return long.astype(int) - short.astype(int)


def _shock_confirm_fade(ctx, p):
    nb = max(6, ctx.bars(p["win_min"]))
    k = p["k"]
    r = _ret(ctx)
    sd = ctx.roll(r, nb, "std", include_current=False)
    z = r / np.where(sd > 0, sd, np.nan)
    z1 = ctx.prev(z, 1)
    mid1 = (ctx.prev(ctx.o, 1) + ctx.prev(ctx.c, 1)) / 2.0
    short = (z1 >= k) & (ctx.c < mid1)
    long = (z1 <= -k) & (ctx.c > mid1)
    return long.astype(int) - short.astype(int)


def _price_volume_corr(ctx, p):
    nb = max(8, ctx.bars(p["win_min"]))
    th = p["th"]
    r = _ret(ctx)
    cr = pd.Series(r).rolling(nb, min_periods=nb).corr(pd.Series(ctx.v)).to_numpy()
    cr = np.where(ctx.bar_in_day >= nb, cr, np.nan)
    return ctx.cross(cr > th).astype(int) - ctx.cross(cr < -th).astype(int)


def _three_down_reclaim(ctx, p):
    n = int(p["run"])
    d = np.sign(ctx.c - ctx.prev(ctx.c, 1))
    down_run = np.ones(ctx.n, bool)
    up_run = np.ones(ctx.n, bool)
    for j in range(1, n + 1):
        dj = ctx.prev(d, j)
        down_run &= dj < 0
        up_run &= dj > 0
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    long = down_run & (ctx.c > h1)
    short = up_run & (ctx.c < l1)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-1418", "Return autocorrelation regime",
           "When lag-1 return autocorrelation over a window is clearly negative, bar moves are being absorbed by liquidity providers: "
           "fade the bar; when clearly positive, orders are being worked in slices: follow it.",
           {"win_min": [60, 90, 120], "th": [0.2, 0.3, 0.4]}, _autocorr_regime, source="assistant reasoning", author="agent"),
    Family("E-1419", "Regression-channel edge fade",
           "Price that stretches more than k residual deviations from the rolling least-squares line is overextended relative to its own trend; fade back.",
           {"win_min": [30, 60, 90], "k": [2.0, 2.5, 3.0]}, _regression_channel_fade, source="assistant reasoning", author="agent"),
    Family("E-1420", "Trend-slope t-statistic follow",
           "A statistically significant rolling slope (high t-stat) means directional flow is persistent rather than noise; follow when it first crosses.",
           {"win_min": [30, 60, 90], "th": [3.0, 4.0, 6.0]}, _slope_t_follow, source="assistant reasoning", author="agent"),
    Family("E-1421", "EMA ribbon alignment onset",
           "When fast, medium and slow EMAs line up in order with price on the fast side, participants at all horizons are on the same side; follow the first alignment.",
           {"base_min": [5, 10, 15]}, _ribbon_onset, source="assistant reasoning", author="agent"),
    Family("E-1422", "Converging-triangle break",
           "Lower highs and higher lows with a shrinking range compress resting orders on both sides; a close outside the recent half-range releases them.",
           {"win_min": [20, 40, 60], "ratio": [0.4, 0.6, 0.8]}, _triangle_break, source="assistant reasoning", author="agent"),
    Family("E-1423", "ATR-band re-entry fade",
           "A close outside an EMA +/- k*average-range band followed by a close back inside marks an exhausted push; fade toward the mean.",
           {"ema_min": [30, 60, 90], "k": [3.0, 4.0, 5.0]}, _keltner_reentry, source="Keltner channel literature (re-entry variant)", author="agent"),
    Family("E-1424", "VWAP sigma-band re-entry fade",
           "Distance from VWAP measured in the session's own deviation of that distance: after a close beyond k sigma, the first close back inside is a sign the stretch is over; fade toward VWAP.",
           {"k": [1.5, 2.0, 2.5], "warm_min": [30, 60]}, _vwap_sigma_reentry, source="assistant reasoning", author="agent"),
    Family("E-1425", "Shock bar confirmed retrace fade",
           "A bar with an extreme return z-score often comes from a single aggressive order; when the next bar closes back through the shock bar's midpoint the shock is being reversed, so fade it.",
           {"win_min": [30, 60, 90], "k": [2.0, 2.5, 3.0]}, _shock_confirm_fade, source="assistant reasoning", author="agent"),
    Family("E-1426", "Price-volume correlation sign follow",
           "If volume systematically rises on up bars (positive return-volume correlation) buyers are the aggressive side; if on down bars, sellers are. Follow the side on which volume concentrates.",
           {"win_min": [30, 60, 90], "th": [0.3, 0.4, 0.5]}, _price_volume_corr, source="volume-price analysis literature", author="agent"),
    Family("E-1427", "Run exhaustion reclaim",
           "After a run of consecutive down (up) closes, a close above the previous bar's high (below its low) shows the run's sellers (buyers) have stopped; trade the reclaim.",
           {"run": [3, 4, 5]}, _three_down_reclaim, source="assistant reasoning", author="agent"),
]
