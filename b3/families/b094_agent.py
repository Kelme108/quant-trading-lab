"""Conveyor batch B-094 (agent, 2026-11-24). Round numbers, double tests, volume ladders, stale extremes, trend-to-noise,
efficiency-ratio chop, OBV divergence, floor-pivot offsets, wick clusters and stochastic re-entry on WIN."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family

_W = ("WIN",)


def _round_number(ctx, p):
    step = float(p["step"])
    pc = ctx.prev(ctx.c, 1)
    up = np.floor(pc / step) * step + step
    dn = np.ceil(pc / step) * step - step
    short = (ctx.h >= up) & (pc < up) & (ctx.c < up)
    long = (ctx.l <= dn) & (pc > dn) & (ctx.c > dn)
    return long.astype(int) - short.astype(int)


def _double_test(ctx, p):
    tol = p["tol"]
    nb = ctx.bars(p["lookback_min"])
    sh = ctx.session_high(include_current=False)
    sl = ctx.session_low(include_current=False)
    lowmin = ctx.roll(ctx.l, nb, "min", include_current=False)
    highmax = ctx.roll(ctx.h, nb, "max", include_current=False)
    top = (ctx.h <= sh) & (ctx.h >= sh * (1 - tol)) & (ctx.c < ctx.o) & ((sh - lowmin) >= 2 * tol * sh)
    bot = (ctx.l >= sl) & (ctx.l <= sl * (1 + tol)) & (ctx.c > ctx.o) & ((highmax - sl) >= 2 * tol * sl)
    return ctx.cross(bot).astype(int) - ctx.cross(top).astype(int)


def _volume_ladder(ctx, p):
    k = int(p["k"])
    col = np.sign(ctx.c - ctx.o)
    up = col > 0
    dn = col < 0
    for i in range(k - 1):
        vi, vj = ctx.prev(ctx.v, i), ctx.prev(ctx.v, i + 1)
        ci = ctx.prev(col, i + 1)
        up = up & (vi > vj) & (ci > 0)
        dn = dn & (vi > vj) & (ci < 0)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _stale_break(ctx, p):
    nb = ctx.bars(p["drought_min"])
    sh = ctx.session_high(include_current=False)
    sl = ctx.session_low(include_current=False)
    hi_nb = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo_nb = ctx.roll(ctx.l, nb, "min", include_current=False)
    up = (ctx.c > sh) & (hi_nb < sh)
    dn = (ctx.c < sl) & (lo_nb > sl)
    return up.astype(int) - dn.astype(int)


def _trend_noise(ctx, p):
    nb = max(3, ctx.bars(p["window_min"]))
    k = p["k"]
    x = ctx.bar_in_day.astype(float)
    y = ctx.c - ctx.day_open
    sxy = ctx.roll(x * y, nb, "sum")
    sy = ctx.roll(y, nb, "sum")
    xbar = ctx.roll(x, nb, "mean")
    sxx = nb * (nb * nb - 1) / 12.0
    slope = (sxy - xbar * sy) / sxx
    sd = ctx.roll(ctx.c, nb, "std")
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(sd > 0, slope * (nb - 1) / sd, np.nan)
    return ctx.cross(r > k).astype(int) - ctx.cross(r < -k).astype(int)


def _er_chop_fade(ctx, p):
    nb = max(2, ctx.bars(p["window_min"]))
    thr = p["er_max"]
    dc = np.abs(ctx.c - ctx.prev(ctx.c, 1))
    path = ctx.roll(dc, nb, "sum")
    net = np.abs(ctx.c - ctx.prev(ctx.c, nb))
    with np.errstate(divide="ignore", invalid="ignore"):
        er = np.where(path > 0, net / path, np.nan)
    hi = ctx.roll(ctx.c, nb, "max")
    lo = ctx.roll(ctx.c, nb, "min")
    chop = er < thr
    short = chop & (ctx.c >= hi) & (hi > lo)
    long = chop & (ctx.c <= lo) & (hi > lo)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _obv_divergence(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    sv = np.nan_to_num(np.sign(ctx.c - ctx.prev(ctx.c, 1)) * ctx.v)
    obv = pd.Series(sv).groupby(ctx.day).cumsum().to_numpy()
    ph = ctx.roll(ctx.c, nb, "max", include_current=False)
    pl = ctx.roll(ctx.c, nb, "min", include_current=False)
    oh = ctx.roll(obv, nb, "max", include_current=False)
    ol = ctx.roll(obv, nb, "min", include_current=False)
    short = (ctx.c > ph) & (obv < oh)
    long = (ctx.c < pl) & (obv > ol)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _pivot_offset(ctx, p):
    k = p["k"]
    pdh, pdl, pdc = ctx.prev_session_value("high"), ctx.prev_session_value("low"), ctx.prev_session_value("close")
    piv = (pdh + pdl + pdc) / 3.0
    rg = pdh - pdl
    up, dn = piv + k * rg, piv - k * rg
    pc = ctx.prev(ctx.c, 1)
    short = (ctx.h >= up) & (pc < up) & (ctx.c < up)
    long = (ctx.l <= dn) & (pc > dn) & (ctx.c > dn)
    return long.astype(int) - short.astype(int)


def _wick_cluster(ctx, p):
    nb = ctx.bars(p["window_min"])
    k = int(p["k"])
    rng = ctx.h - ctx.l
    upper = ctx.h - np.maximum(ctx.o, ctx.c)
    lower = np.minimum(ctx.o, ctx.c) - ctx.l
    upw = ((upper > 0.5 * rng) & (rng > 0)).astype(float)
    dnw = ((lower > 0.5 * rng) & (rng > 0)).astype(float)
    cu = ctx.roll(upw, nb, "sum")
    cd = ctx.roll(dnw, nb, "sum")
    short = (cu >= k) & (upw > 0)
    long = (cd >= k) & (dnw > 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _stoch_reentry(ctx, p):
    nb = max(3, ctx.bars(p["window_min"]))
    lvl = p["level"]
    hh = ctx.roll(ctx.h, nb, "max")
    ll = ctx.roll(ctx.l, nb, "min")
    with np.errstate(divide="ignore", invalid="ignore"):
        kk = np.where(hh > ll, (ctx.c - ll) / (hh - ll), np.nan)
    pk = ctx.prev(kk, 1)
    short = (pk >= lvl) & (kk < lvl)
    long = (pk <= 1 - lvl) & (kk > 1 - lvl)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-938", "Round-number rejection",
           "Index levels at round thousands/halves attract resting orders and stops; a bar that pokes through a round "
           "number and closes back on the original side is a failed attempt to cross it, so fade it.",
           {"step": [250, 500, 1000]}, _round_number, markets=_W, source="assistant reasoning", author="agent"),
    Family("E-939", "Double top/bottom test",
           "A second test of the session extreme after a pullback, ending in a bar against the extreme, shows the first "
           "push was not absorbed by new aggressors; fade the second test.",
           {"tol": [0.0003, 0.0005, 0.0008], "lookback_min": [30, 60]}, _double_test, markets=_W,
           source="assistant reasoning", author="agent"),
    Family("E-940", "Rising-volume bar ladder",
           "Consecutive same-colour bars with growing volume show participation building with the move (not fading); "
           "follow the ladder.",
           {"k": [2, 3, 4]}, _volume_ladder, markets=_W, source="assistant reasoning", author="agent"),
    Family("E-941", "Stale extreme break",
           "A session high/low untouched for a long time holds stops of those who faded it; a close through it forces "
           "covering and follows through.",
           {"drought_min": [30, 60, 90, 120]}, _stale_break, markets=_W, source="assistant reasoning", author="agent"),
    Family("E-942", "Trend-to-noise cross",
           "A regression slope large relative to price dispersion marks a clean directional drift; its first crossing of "
           "a threshold flags orderly flow that tends to persist.",
           {"window_min": [15, 30, 45], "k": [1.5, 2.0, 2.5]}, _trend_noise, markets=_W,
           source="assistant reasoning", author="agent"),
    Family("E-943", "Efficiency-ratio chop fade",
           "When Kaufman's efficiency ratio is low the market is moving sideways without net direction; an extreme of "
           "the window in that regime is an excursion that mean-reverts.",
           {"window_min": [20, 40, 60], "er_max": [0.15, 0.25, 0.35]}, _er_chop_fade, markets=_W,
           source="Kaufman efficiency ratio (assistant reasoning)", author="agent"),
    Family("E-944", "OBV divergence fade",
           "A new price extreme not confirmed by signed cumulative volume means the push lacked aggressive flow; fade it.",
           {"lookback_min": [15, 30, 60]}, _obv_divergence, markets=_W, source="assistant reasoning", author="agent"),
    Family("E-945", "Floor-pivot offset rejection",
           "Levels at fixed fractions of yesterday's range around the pivot are widely tracked by floor-pivot users; "
           "a poke and close back is a failed attempt, fade it.",
           {"k": [0.25, 0.5, 0.75, 1.0]}, _pivot_offset, markets=_W, source="floor pivot points (assistant reasoning)",
           author="agent"),
    Family("E-946", "Wick cluster rejection",
           "Several bars in a short window closing far from their highs (or lows) show repeated rejection by the other "
           "side; trade against the rejected direction.",
           {"window_min": [15, 30, 60], "k": [2, 3]}, _wick_cluster, markets=_W, source="assistant reasoning",
           author="agent"),
    Family("E-947", "Stochastic extreme re-entry",
           "When the close falls back from the top (or rises from the bottom) of its recent range, momentum buyers "
           "(sellers) are losing control; fade the re-entry.",
           {"window_min": [30, 60, 90], "level": [0.8, 0.9]}, _stoch_reentry, markets=_W,
           source="stochastic oscillator (assistant reasoning)", author="agent"),
]
