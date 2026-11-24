"""Conveyor batch B-120 (agent, 2026-11-24). Indicator-style and structural rules not yet in the screened list."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from b3.esteira import Family


def _lag(ctx, x, k):
    return x if k == 0 else ctx.prev(x, k)


def _dir(ctx, long, short):
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _soldiers(ctx, p):
    nbars, bf = int(p["bars"]), p["body_frac"]
    rng = ctx.h - ctx.l
    body = ctx.c - ctx.o
    with np.errstate(invalid="ignore"):
        up = (body > 0) & (body >= bf * rng) & (rng > 0)
        dn = (body < 0) & (-body >= bf * rng) & (rng > 0)
        for k in range(1, nbars):
            up = up & (_lag(ctx, up.astype(float), k) == 1) & (_lag(ctx, ctx.c, k - 1) > ctx.prev(ctx.c, k))
            dn = dn & (_lag(ctx, dn.astype(float), k) == 1) & (_lag(ctx, ctx.c, k - 1) < ctx.prev(ctx.c, k))
    return _dir(ctx, up, dn)


def _close_channel(ctx, p):
    nb, vk = ctx.bars(p["lookback_min"]), p["vol_k"]
    hi = ctx.roll(ctx.c, nb, "max", include_current=False)
    lo = ctx.roll(ctx.c, nb, "min", include_current=False)
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    with np.errstate(invalid="ignore"):
        busy = ctx.v >= vk * med if vk > 0 else np.ones(ctx.n, bool)
        return _dir(ctx, (ctx.c > hi) & busy, (ctx.c < lo) & busy)


def _dpo_fade(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    sma = ctx.roll(ctx.c, nb, "mean")
    sd = ctx.roll(ctx.c, nb, "std")
    lagged = ctx.prev(sma, max(1, nb // 2 + 1))
    with np.errstate(invalid="ignore", divide="ignore"):
        z = (ctx.c - lagged) / sd
        return _dir(ctx, z < -k, z > k)


def _obv_lead(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    step = np.nan_to_num(np.sign(ctx.c - ctx.prev(ctx.c, 1))) * ctx.v
    obv = pd.Series(step).groupby(ctx.day).cumsum().to_numpy()
    ohi = ctx.roll(obv, nb, "max", include_current=False)
    olo = ctx.roll(obv, nb, "min", include_current=False)
    phi = ctx.roll(ctx.c, nb, "max", include_current=False)
    plo = ctx.roll(ctx.c, nb, "min", include_current=False)
    with np.errstate(invalid="ignore"):
        long = (obv > ohi) & (ctx.c <= phi) & (ctx.c > ctx.prev(ctx.c, 1))
        short = (obv < olo) & (ctx.c >= plo) & (ctx.c < ctx.prev(ctx.c, 1))
        return _dir(ctx, long, short)


def _tii(ctx, p):
    n, w, th = ctx.bars(p["sma_min"]), ctx.bars(p["win_min"]), p["th"]
    sma = ctx.roll(ctx.c, n, "mean")
    with np.errstate(invalid="ignore"):
        above = np.where(np.isnan(sma), np.nan, (ctx.c > sma).astype(float))
        share = ctx.roll(above, w, "mean")
        return _dir(ctx, share >= th, share <= 1 - th)


def _vwap_band_break(ctx, p):
    k, mn = p["k"], ctx.bars(p["min_min"])
    d = ctx.c - ctx.vwap()
    d = np.nan_to_num(d)
    g1 = pd.Series(d).groupby(ctx.day).cumsum().to_numpy()
    g2 = pd.Series(d * d).groupby(ctx.day).cumsum().to_numpy()
    cnt = ctx.bar_in_day + 1.0
    sd = np.sqrt(np.maximum(g2 / cnt - (g1 / cnt) ** 2, 0.0))
    ok = (ctx.bar_in_day >= mn) & (sd > 0)
    return _dir(ctx, ok & (d > k * sd), ok & (d < -k * sd))


def _bb_break(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    m = ctx.roll(ctx.c, nb, "mean", include_current=False)
    s = ctx.roll(ctx.c, nb, "std", include_current=False)
    with np.errstate(invalid="ignore"):
        return _dir(ctx, ctx.c > m + k * s, ctx.c < m - k * s)


def _resid_fade(ctx, p):
    m, k = ctx.bars(p["win_min"]), p["k"]
    L = ctx.bars(60)
    wd = ctx.other_close()
    with np.errstate(invalid="ignore", divide="ignore"):
        rw = ctx.c / ctx.prev(ctx.c, 1) - 1.0
        rd = wd / ctx.prev(wd, 1) - 1.0
        cov = ctx.roll(rw * rd, L) - ctx.roll(rw, L) * ctx.roll(rd, L)
        var = ctx.roll(rd * rd, L) - ctx.roll(rd, L) ** 2
        beta = np.where(var > 0, cov / var, np.nan)
        res = rw - ctx.prev(beta, 1) * rd
        s = ctx.roll(res, m, "sum")
        sd = ctx.roll(res, L, "std")
        z = s / (sd * math.sqrt(m))
        return _dir(ctx, z < -k, z > k)


def _largest_bar_retrace(ctx, p):
    N, mult = ctx.bars(p["lookback_min"]), p["mult"]
    rng = ctx.h - ctx.l
    best = np.full(ctx.n, -1.0)
    bopen = np.full(ctx.n, np.nan)
    bdir = np.zeros(ctx.n)
    with np.errstate(invalid="ignore"):
        for k in range(1, N + 1):
            r = ctx.cached(("prev_rng", k), lambda k=k: ctx.prev(rng, k))
            ok = ctx.cached(("prev_o", k), lambda k=k: ctx.prev(ctx.o, k))
            ck = ctx.cached(("prev_c", k), lambda k=k: ctx.prev(ctx.c, k))
            better = r > best
            best = np.where(better, r, best)
            bopen = np.where(better, ok, bopen)
            bdir = np.where(better, np.sign(ck - ok), bdir)
        avg = ctx.roll(rng, N, "mean", include_current=False)
        big = best >= mult * avg
        short = big & (bdir > 0) & (ctx.c < bopen)
        long = big & (bdir < 0) & (ctx.c > bopen)
        return _dir(ctx, long, short)


def _ema_slice(ctx, p):
    n, bf = int(p["ema_bars"]), p["body_frac"]
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    e1 = ctx.prev(ema, 1)
    rng = ctx.h - ctx.l
    body = ctx.c - ctx.o
    with np.errstate(invalid="ignore"):
        long = (ctx.o < e1) & (ctx.c > e1) & (body >= bf * rng) & (rng > 0)
        short = (ctx.o > e1) & (ctx.c < e1) & (-body >= bf * rng) & (rng > 0)
        return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-1198", "Three soldiers / three crows",
           "Consecutive full-bodied bars each closing beyond the last show one side taking every auction; late "
           "counter-traders must cover or capitulate, so the push continues.",
           {"bars": [3, 4], "body_frac": [0.5, 0.6, 0.7]}, _soldiers, source="assistant reasoning", author="agent"),
    Family("E-1199", "Highest-close channel break with volume",
           "A close (not a wick) beyond every close of the last window is accepted value; with normal-or-higher "
           "volume the stops and breakout orders behind it feed the move.",
           {"lookback_min": [20, 30, 60], "vol_k": [0.0, 1.0, 1.5]}, _close_channel, source="assistant reasoning",
           author="agent"),
    Family("E-1200", "Detrended price oscillator extreme fade",
           "Price far from a lagged moving average (cycle-removed) in units of its own dispersion is an "
           "over-extension that liquidity providers fade.",
           {"win_min": [30, 60], "k": [1.5, 2.0, 2.5]}, _dpo_fade, source="assistant reasoning (DPO indicator)",
           author="agent"),
    Family("E-1201", "OBV leads price",
           "When on-balance volume makes a new window extreme while price has not, informed flow is ahead of price "
           "and the close should catch up.",
           {"lookback_min": [20, 30, 60]}, _obv_lead, source="assistant reasoning (OBV, Granville)", author="agent"),
    Family("E-1202", "Trend intensity index threshold cross",
           "When almost every recent close sits on one side of a slow average, persistent one-sided "
           "participation is under way; the cross into that state marks trend onset.",
           {"sma_min": [30, 60], "win_min": [15, 30], "th": [0.8, 0.9]}, _tii, source="assistant reasoning (TII)",
           author="agent"),
    Family("E-1203", "VWAP sigma-band break follow",
           "A close more than k session-deviations from VWAP is a value migration, not a stretch; institutions "
           "chasing VWAP-benchmarked orders keep buying/selling into it.",
           {"k": [1.5, 2.0, 2.5], "min_min": [30, 60]}, _vwap_band_break, source="assistant reasoning", author="agent"),
    Family("E-1204", "Bollinger close-outside follow",
           "A close outside a volatility band built from prior bars signals range expansion; the breakout is "
           "followed by trend-chasers.",
           {"win_min": [20, 30, 60], "k": [2.0, 2.5]}, _bb_break, source="assistant reasoning (Bollinger bands)",
           author="agent"),
    Family("E-1205", "Dollar-beta residual overshoot fade",
           "The part of the index move not explained by the rolling dollar beta is idiosyncratic noise from "
           "order flow, not macro; it tends to revert.",
           {"win_min": [10, 20, 30], "k": [2.0, 2.5, 3.0]}, _resid_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1206", "Largest-bar open retraced",
           "When price fully retraces the biggest recent impulse bar back through its open, those who chased it are "
           "trapped and their exits push the retrace on.",
           {"lookback_min": [30, 60, 90], "mult": [1.5, 2.0, 3.0]}, _largest_bar_retrace, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1207", "Single-bar EMA slice follow",
           "A strong bar that opens on one side of the EMA and closes on the other shows decisive control "
           "change in one auction; follow it.",
           {"ema_bars": [20, 30, 50], "body_frac": [0.5, 0.7]}, _ema_slice, source="assistant reasoning",
           author="agent"),
]
