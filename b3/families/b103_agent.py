"""Conveyor batch B-103 (agent, 2026-11-24). Indicator-structure and cross-market ideas not yet screened: chandelier flip, vortex, Elder impulse, Fisher, dollar+index co-move, Keltner, skew flip, gap-and-go, prior-block break, regression residual."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _sgn(ctx, long, short):
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _chandelier_flip(ctx, p):
    nb, k = ctx.bars(p["n_min"]), p["k"]
    hh = ctx.roll(ctx.h, nb, "max")
    ll = ctx.roll(ctx.l, nb, "min")
    atr = ctx.roll(ctx.h - ctx.l, nb, "mean")
    short = ctx.c < hh - k * atr
    long = ctx.c > ll + k * atr
    return _sgn(ctx, long, short)


def _vortex_cross(ctx, p):
    nb, m = ctx.bars(p["n_min"]), p["margin"]
    ph, pl, pc = ctx.prev(ctx.h), ctx.prev(ctx.l), ctx.prev(ctx.c)
    vmp = np.abs(ctx.h - pl)
    vmm = np.abs(ctx.l - ph)
    tr = np.maximum(ctx.h - ctx.l, np.maximum(np.abs(ctx.h - pc), np.abs(ctx.l - pc)))
    s_tr = ctx.roll(tr, nb, "sum")
    with np.errstate(all="ignore"):
        vip = ctx.roll(vmp, nb, "sum") / s_tr
        vim = ctx.roll(vmm, nb, "sum") / s_tr
    return _sgn(ctx, vip > vim + m, vim > vip + m)


def _elder_impulse(ctx, p):
    n = int(p["ema_n"])
    e = ctx.ema(ctx.c, n)
    macd = ctx.ema(ctx.c, 12) - ctx.ema(ctx.c, 26)
    hist = macd - ctx.ema(macd, 9)
    green = (e > ctx.prev(e)) & (hist > ctx.prev(hist))
    red = (e < ctx.prev(e)) & (hist < ctx.prev(hist))
    return _sgn(ctx, green, red)


def _fisher_turn(ctx, p):
    nb, th = ctx.bars(p["n_min"]), p["th"]
    hi = ctx.roll(ctx.h, nb, "max")
    lo = ctx.roll(ctx.l, nb, "min")
    with np.errstate(all="ignore"):
        x = 2.0 * ((ctx.h + ctx.l) / 2.0 - lo) / (hi - lo) - 1.0
        x = np.clip(x, -0.999, 0.999)
        v = np.clip(ctx.ema(x, 3), -0.999, 0.999)
        fish = 0.5 * np.log((1.0 + v) / (1.0 - v))
    pf = ctx.prev(fish)
    long = (fish > pf) & (fish < -th)
    short = (fish < pf) & (fish > th)
    return _sgn(ctx, long, short)


def _dollar_index_comove_fade(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    w = ctx.other_close()
    both_hi = (ctx.c >= ctx.roll(ctx.c, nb, "max")) & (w >= ctx.roll(w, nb, "max"))
    both_lo = (ctx.c <= ctx.roll(ctx.c, nb, "min")) & (w <= ctx.roll(w, nb, "min"))
    return _sgn(ctx, both_lo, both_hi)


def _keltner_break(ctx, p):
    n, k = int(p["ema_n"]), p["k"]
    e = ctx.ema(ctx.c, n)
    atr = ctx.roll(ctx.h - ctx.l, n, "mean")
    return _sgn(ctx, ctx.c > e + k * atr, ctx.c < e - k * atr)


def _skew_flip(ctx, p):
    nb, th = ctx.bars(p["n_min"]), p["th"]
    mean = ctx.roll(ctx.c, nb, "mean")
    s = pd.Series(ctx.c).groupby(ctx.day).transform(lambda z: z.rolling(nb, min_periods=nb).median()).to_numpy()
    atr = ctx.roll(ctx.h - ctx.l, nb, "mean")
    with np.errstate(all="ignore"):
        sk = (mean - s) / atr
    return _sgn(ctx, sk > th, sk < -th)


def _gap_and_go(ctx, p):
    k = p["k"]
    atr = ctx.roll(ctx.h - ctx.l, 20, "mean", include_current=False)
    ph, pl = ctx.prev(ctx.h), ctx.prev(ctx.l)
    long = (ctx.o > ph + k * atr) & (ctx.c > ctx.o)
    short = (ctx.o < pl - k * atr) & (ctx.c < ctx.o)
    return long.astype(int) - short.astype(int)


def _prev_block_break(ctx, p):
    bm = int(p["block_min"])
    g = pd.DataFrame({"d": ctx.day, "b": ctx.minute // bm, "h": ctx.h, "l": ctx.l})
    a = g.groupby(["d", "b"]).agg(bh=("h", "max"), bl=("l", "min")).reset_index()
    a["ph"] = a.groupby("d")["bh"].shift(1)
    a["pl"] = a.groupby("d")["bl"].shift(1)
    m = g[["d", "b"]].merge(a[["d", "b", "ph", "pl"]], on=["d", "b"], how="left")
    ph, pl = m["ph"].to_numpy(float), m["pl"].to_numpy(float)
    return _sgn(ctx, ctx.c > ph, ctx.c < pl)


def _regression_resid_fade(ctx, p):
    nb, k = ctx.bars(p["n_min"]), p["k"]
    x = ctx.bar_in_day.astype(float)
    y = ctx.c - ctx.day_open
    mx, my = ctx.roll(x, nb, "mean"), ctx.roll(y, nb, "mean")
    mxy, mxx, myy = ctx.roll(x * y, nb, "mean"), ctx.roll(x * x, nb, "mean"), ctx.roll(y * y, nb, "mean")
    with np.errstate(all="ignore"):
        varx = mxx - mx * mx
        slope = (mxy - mx * my) / varx
        rv = (myy - my * my) - slope * slope * varx
        sd = np.sqrt(np.where(rv > 1e-9, rv, np.nan))
        z = (y - (my + slope * (x - mx))) / sd
    return _sgn(ctx, z < -k, z > k)


A = "assistant reasoning"

FAMILIES = [
    Family("E-1028", "Chandelier-exit flip follow",
           "A close that falls more than k average ranges below the rolling high is the break of a trailing stop "
           "that trend followers hold; their exits add to the move. Mirror for longs.",
           {"n_min": [20, 40, 60], "k": [1.5, 2.0, 3.0]}, _chandelier_flip, markets=("WIN",), source=A, author="agent"),
    Family("E-1029", "Vortex indicator cross follow",
           "Upward vs downward vortex movement (distance from the prior bar's extremes over true range) shows which "
           "side is extending; a cross with a margin marks control passing to that side.",
           {"n_min": [15, 30, 60], "margin": [0.0, 0.1, 0.2]}, _vortex_cross, markets=("WIN",), source=A, author="agent"),
    Family("E-1030", "Elder impulse colour flip follow",
           "When both the EMA slope and the MACD histogram slope point up, trend and momentum agree; the first bar of "
           "agreement is an entry for trend followers, and vice versa for shorts.",
           {"ema_n": [13, 21, 34]}, _elder_impulse, markets=("WIN",), source="Elder impulse system (assistant reasoning)", author="agent"),
    Family("E-1031", "Fisher transform turn from an extreme",
           "The Fisher transform stretches the price position in its rolling range; a turn of the line while it is "
           "far from zero marks the end of a one-sided push, so the next move is back toward the range middle.",
           {"n_min": [30, 60, 90], "th": [0.5, 1.0, 1.5]}, _fisher_turn, markets=("WIN",), source=A, author="agent"),
    Family("E-1032", "Index and dollar at the same extreme fade",
           "Index and dollar usually move inversely. When both make a new rolling high (or both a low) one of them is "
           "being pushed by flow that is not macro; the index leg tends to give back the move.",
           {"lookback_min": [30, 60, 120]}, _dollar_index_comove_fade, markets=("WIN",), source=A, author="agent"),
    Family("E-1033", "Keltner channel close-outside follow",
           "A close more than k average ranges away from its EMA is a volatility-adjusted thrust that attracts "
           "momentum orders; follow it.",
           {"ema_n": [20, 40, 60], "k": [1.5, 2.0, 2.5]}, _keltner_break, markets=("WIN",), source=A, author="agent"),
    Family("E-1034", "Mean-median skew flip follow",
           "When the rolling mean of closes moves above the rolling median, recent large up moves are skewing the "
           "window: a thrust by an aggressive buyer; follow the flip (mirror for sells).",
           {"n_min": [20, 40, 60], "th": [0.0, 0.1, 0.2]}, _skew_flip, markets=("WIN",), source=A, author="agent"),
    Family("E-1035", "Bar-to-bar gap and go",
           "A bar that opens beyond the prior bar's extreme and closes in the gap direction shows orders arriving "
           "with no resting liquidity to absorb them; follow.",
           {"k": [0.0, 0.25, 0.5]}, _gap_and_go, markets=("WIN",), source=A, author="agent"),
    Family("E-1036", "Previous clock-block range break follow",
           "The high/low of the just-finished 30/60/120 minute clock block is a level that many intraday traders "
           "watch; a close beyond it triggers stops and breakout orders.",
           {"block_min": [30, 60, 120]}, _prev_block_break, markets=("WIN",), source=A, author="agent"),
    Family("E-1037", "Regression-channel residual fade",
           "Price far from its rolling linear-regression line, in residual standard deviations, has overshot the "
           "local trend; it tends to snap back toward the line.",
           {"n_min": [30, 60, 90], "k": [2.0, 2.5, 3.0]}, _regression_resid_fade, markets=("WIN",), source=A, author="agent"),
]
