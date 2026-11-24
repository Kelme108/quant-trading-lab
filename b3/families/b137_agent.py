"""Conveyor batch B-137 (agent, 2026-11-24). Mixed themes: seasonal profile, efficiency, autocorrelation regime, levels, volume, oscillators."""
from __future__ import annotations

import numpy as np

from b3.esteira import Family


def _seasonal_dev_fade(ctx, p):
    k = p["k"]
    r = ctx.c / ctx.day_open - 1.0
    m = ctx.cached("sea_m", lambda: ctx.same_minute(r, "mean"))
    a = ctx.cached("sea_a", lambda: ctx.same_minute(np.abs(r), "mean"))
    dev = r - m
    ok = a > 0
    short = ok & (dev > k * a)
    long = ok & (dev < -k * a)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _efficiency_follow(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    net = ctx.c - ctx.prev(ctx.c, nb)
    step = np.abs(ctx.c - ctx.prev(ctx.c, 1))
    path = ctx.roll(step, nb, "sum")
    er = np.where(path > 0, np.abs(net) / np.where(path > 0, path, 1.0), 0.0)
    long = (er > th) & (net > 0)
    short = (er > th) & (net < 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _autocorr_regime(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    ret = ctx.c - ctx.prev(ctx.c, 1)
    num = ctx.roll(ret * ctx.prev(ret, 1), nb, "mean")
    den = ctx.roll(ret * ret, nb, "mean")
    ac = np.where(den > 0, num / np.where(den > 0, den, 1.0), 0.0)
    bar = np.sign(ctx.c - ctx.o)
    long = ((ac > th) & (bar > 0)) | ((ac < -th) & (bar < 0))
    short = ((ac > th) & (bar < 0)) | ((ac < -th) & (bar > 0))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _prev_close_reclaim(ctx, p):
    nb = ctx.bars(p["away_min"])
    pc = ctx.prev_session_value("close")
    below = (ctx.c < pc).astype(float)
    above = (ctx.c > pc).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    up = was_below & (ctx.c > pc)
    dn = was_above & (ctx.c < pc)
    return up.astype(int) - dn.astype(int)


def _widest_bar_follow(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    rng = ctx.h - ctx.l
    widest = (rng >= ctx.roll(rng, nb, "max")) & (rng > 0)
    pos = np.where(rng > 0, (ctx.c - ctx.l) / np.where(rng > 0, rng, 1.0), 0.5)
    long = widest & (pos >= 0.75)
    short = widest & (pos <= 0.25)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _lowvol_bar_break(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    minv = ctx.roll(ctx.v, nb, "min")
    lowvol = ctx.prev(minv, 1) == ctx.prev(ctx.v, 1)
    long = lowvol & (ctx.c > ctx.prev(ctx.h, 1))
    short = lowvol & (ctx.c < ctx.prev(ctx.l, 1))
    return long.astype(int) - short.astype(int)


def _cci_reentry_fade(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    sma = ctx.roll(tp, nb, "mean")
    md = ctx.roll(np.abs(tp - sma), nb, "mean")
    cci = np.where(md > 0, (tp - sma) / (0.015 * np.where(md > 0, md, 1.0)), 0.0)
    prev = ctx.prev(cci, 1)
    short = (prev > th) & (cci <= th)
    long = (prev < -th) & (cci >= -th)
    return long.astype(int) - short.astype(int)


def _cmf_extreme_follow(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    rng = ctx.h - ctx.l
    clv = np.where(rng > 0, ((ctx.c - ctx.l) - (ctx.h - ctx.c)) / np.where(rng > 0, rng, 1.0), 0.0)
    sv = ctx.roll(ctx.v, nb, "sum")
    cmf = np.where(sv > 0, ctx.roll(clv * ctx.v, nb, "sum") / np.where(sv > 0, sv, 1.0), 0.0)
    return ctx.cross(cmf > th).astype(int) - ctx.cross(cmf < -th).astype(int)


def _ha_flip(ctx, p):
    n = int(p["run_bars"])
    hac = (ctx.o + ctx.h + ctx.l + ctx.c) / 4.0
    hao = (ctx.prev(ctx.o, 1) + ctx.prev(ctx.c, 1)) / 2.0
    red = np.nan_to_num((hac < hao).astype(float))
    green = np.nan_to_num((hac > hao).astype(float))
    was_red = ctx.roll(red, n, "min", include_current=False) == 1
    was_green = ctx.roll(green, n, "min", include_current=False) == 1
    long = was_red & (green == 1)
    short = was_green & (red == 1)
    return long.astype(int) - short.astype(int)


def _ema_stack(ctx, p):
    f = int(p["fast"])
    ef = ctx.cached(("ema", f), lambda: ctx.ema(ctx.c, f))
    em = ctx.cached(("ema", 2 * f), lambda: ctx.ema(ctx.c, 2 * f))
    es = ctx.cached(("ema", 4 * f), lambda: ctx.ema(ctx.c, 4 * f))
    long = (ef > em) & (em > es)
    short = (ef < em) & (em < es)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


FAMILIES = [
    Family("E-1368", "Seasonal-profile deviation fade",
           "Price's move from the open, compared with its own average at the same minute over 20 sessions, "
           "measures an abnormal intraday excursion; liquidity providers fade the excess back toward the usual profile.",
           {"k": [0.75, 1.0, 1.5]}, _seasonal_dev_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1369", "Efficiency-ratio trend start follow",
           "When net movement is close to total path length (Kaufman efficiency), flow is one-sided and "
           "slow participants keep chasing; follow the first bar where efficiency crosses the threshold.",
           {"win_min": [20, 30, 60], "th": [0.5, 0.6, 0.7]}, _efficiency_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1370", "Autocorrelation-regime bar follow/fade",
           "Rolling lag-1 return autocorrelation tells whether the tape is trending (follow the last bar) or "
           "bouncing (fade it); trade the bar's direction accordingly when the regime is clear.",
           {"win_min": [30, 60, 90], "th": [0.15, 0.25]}, _autocorr_regime, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1371", "Previous-close reclaim after dwell",
           "After trading on one side of yesterday's close for a while, the first close back across it shows "
           "overnight-position holders switching sides; follow the cross.",
           {"away_min": [15, 30, 60]}, _prev_close_reclaim,
           source="assistant reasoning", author="agent"),
    Family("E-1372", "Widest-bar close-extreme follow",
           "The widest bar of the recent window closing in its top or bottom quarter shows aggressive one-sided "
           "orders that did not meet resistance; follow it.",
           {"lookback_min": [30, 60, 90]}, _widest_bar_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1373", "Lowest-volume bar break",
           "A bar with the lowest volume of the window marks a pause in participation; the close that "
           "breaks its range shows who resumes first, follow that side.",
           {"lookback_min": [20, 30, 60]}, _lowvol_bar_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1374", "CCI band re-entry fade",
           "A CCI excursion beyond its band followed by a return inside suggests the stretched move is "
           "exhausted and late entrants are trapped; fade back.",
           {"win_min": [30, 60], "th": [100, 150, 200]}, _cci_reentry_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1375", "Chaikin money-flow extreme follow",
           "Volume-weighted close location strongly positive or negative over a window means closes keep "
           "landing near the bar extreme on volume; follow the cross.",
           {"win_min": [30, 60, 90], "th": [0.2, 0.3, 0.4]}, _cmf_extreme_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1376", "Heikin-Ashi colour flip after a run",
           "A smoothed candle changing colour after a run of the opposite colour marks a turn that the "
           "smoothing filters from noise; follow the flip.",
           {"run_bars": [3, 4, 5]}, _ha_flip, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1377", "Triple-EMA stack alignment follow",
           "Fast above middle above slow EMA all in order means trends at several horizons agree; follow the "
           "bar where the stack first aligns.",
           {"fast": [5, 8, 13]}, _ema_stack, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
