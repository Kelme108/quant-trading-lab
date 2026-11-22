"""Conveyor batch B-055 (agent, 2026-11-21). Mixed WIN rules: multi-horizon stretch fade, regime-conditioned follow,
clock-block structure, double-stochastic MACD, gap bars, efficiency collapse, TRIX, block-end extremes, dwell-slip."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family

np.seterr(all="ignore")


def _fire(ctx, long, short):
    return ctx.cross(np.asarray(long, bool)).astype(int) - ctx.cross(np.asarray(short, bool)).astype(int)


def _multi_stretch(ctx, p):
    m, k = ctx.bars(p["base_min"]), p["k"]
    r1 = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    sd = ctx.cached("sd1", lambda: ctx.prev_sessions(r1, "sd"))
    zs = []
    for mult in (1, 2, 4):
        nb = m * mult
        rr = ctx.c / ctx.prev(ctx.c, nb) - 1.0
        zs.append(rr / (sd * np.sqrt(nb)))
    up = (zs[0] > k) & (zs[1] > k) & (zs[2] > k)
    dn = (zs[0] < -k) & (zs[1] < -k) & (zs[2] < -k)
    return _fire(ctx, dn, up)


def _persist_follow(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    num = ctx.roll(r * ctx.prev(r, 1), nb, "mean")
    den = ctx.roll(r * r, nb, "mean")
    ac = num / den
    long = (ac > th) & (ctx.c > ctx.prev(ctx.h, 1))
    short = (ac > th) & (ctx.c < ctx.prev(ctx.l, 1))
    return _fire(ctx, long, short)


def _block_streak(ctx, p):
    blk, run = int(p["blk_min"]), int(p["run"])
    key = ctx.day.astype(np.int64) * 10000 + (ctx.minute // blk)
    first_o = pd.Series(ctx.o).groupby(key).transform("first").to_numpy()
    last = (ctx.minute % blk) == (blk - ctx.tf)
    col = np.sign(ctx.c - first_o)
    out = np.zeros(ctx.n, int)
    pday, pcol, streak = -1, 0.0, 0
    for i in np.flatnonzero(last):
        d, cc = ctx.day[i], col[i]
        if d == pday and cc == pcol and cc != 0:
            streak += 1
        else:
            streak = 1 if cc != 0 else 0
        pday, pcol = d, cc
        if streak == run:
            out[i] = -int(cc)
    return out


def _stoch(ctx, x, n):
    lo, hi = ctx.roll(x, n, "min"), ctx.roll(x, n, "max")
    return np.where(hi - lo > 1e-12, (x - lo) / (hi - lo) * 100.0, np.nan)


def _schaff(ctx, p):
    cyc, lv = p["cycle_min"], p["lo"]
    n = max(3, ctx.bars(cyc))
    fast = max(2, ctx.bars(cyc / 2.0))
    macd = ctx.ema(ctx.c, fast) - ctx.ema(ctx.c, n)
    s1 = ctx.ema(_stoch(ctx, macd, n), 3)
    stc = ctx.ema(_stoch(ctx, s1, n), 3)
    return _fire(ctx, stc > lv, stc < 100.0 - lv)


def _gap_reversal(ctx, p):
    k = p["k"]
    typ = ctx.cached("rng_mean", lambda: ctx.prev_sessions(ctx.h - ctx.l, "mean"))
    pc = ctx.prev(ctx.c, 1)
    gap = ctx.o - pc
    short = (gap >= k * typ) & (ctx.c < ctx.o)
    long = (-gap >= k * typ) & (ctx.c > ctx.o)
    return long.astype(int) - short.astype(int)


def _eff_collapse(ctx, p):
    nb, hi = ctx.bars(p["win_min"]), p["hi"]
    move = ctx.c - ctx.prev(ctx.c, nb)
    path = ctx.roll(np.abs(ctx.c - ctx.prev(ctx.c, 1)), nb, "sum")
    er = np.abs(move) / path
    peak = ctx.roll(er, max(2, nb // 2), "max", include_current=False)
    base = (er < hi - 0.2) & (peak > hi)
    return _fire(ctx, base & (move < 0), base & (move > 0))


def _trix(ctx, p):
    n = ctx.bars(p["n_min"])
    e3 = ctx.ema(ctx.ema(ctx.ema(ctx.c, n), n), n)
    tx = e3 / ctx.prev(e3, 1) - 1.0
    return _fire(ctx, tx > 0, tx < 0)


def _block_end_extreme(ctx, p):
    blk, k = int(p["blk_min"]), p["k"]
    key = ctx.day.astype(np.int64) * 10000 + (ctx.minute // blk)
    bh = pd.Series(ctx.h).groupby(key).cummax().to_numpy()
    bl = pd.Series(ctx.l).groupby(key).cummin().to_numpy()
    rng = bh - bl
    typ = ctx.cached("rng_mean", lambda: ctx.prev_sessions(ctx.h - ctx.l, "mean")) * np.sqrt(blk / ctx.tf)
    last = (ctx.minute % blk) == (blk - ctx.tf)
    cond = last & (rng > 0) & (rng >= k * typ)
    pos = (ctx.c - bl) / rng
    short = cond & (pos >= 0.9)
    long = cond & (pos <= 0.1)
    return long.astype(int) - short.astype(int)


def _top_dwell(ctx, p):
    nb, m = ctx.bars(p["win_min"]), ctx.bars(p["dwell_min"])
    hi, lo = ctx.roll(ctx.h, nb, "max"), ctx.roll(ctx.l, nb, "min")
    pos = np.where(hi - lo > 0, (ctx.c - lo) / (hi - lo), np.nan)
    top = (pos >= 0.9).astype(float)
    bot = (pos <= 0.1).astype(float)
    top = np.where(np.isnan(pos), np.nan, top)
    bot = np.where(np.isnan(pos), np.nan, bot)
    dwell_top = ctx.roll(top, m, "mean", include_current=False) >= 0.8
    dwell_bot = ctx.roll(bot, m, "mean", include_current=False) >= 0.8
    short = dwell_top & (pos < 0.8)
    long = dwell_bot & (pos > 0.2)
    return _fire(ctx, long, short)


def _vwap_slice(ctx, p):
    k, vk = p["k"], p["vol_k"]
    body = np.abs(ctx.c - ctx.o)
    typ = ctx.cached("body_mean", lambda: ctx.prev_sessions(body, "mean"))
    vmean = ctx.cached("vol_mean", lambda: ctx.prev_sessions(ctx.v, "mean"))
    vw = ctx.prev(ctx.vwap(), 1)
    big = (body >= k * typ) & (ctx.v >= vk * vmean)
    long = big & (ctx.o < vw) & (ctx.c > vw)
    short = big & (ctx.o > vw) & (ctx.c < vw)
    return _fire(ctx, long, short)


FAMILIES = [
    Family("E-548", "Multi-horizon stretch agreement fade",
           "When the 1x, 2x and 4x horizon returns are all stretched the same way in volatility units, late chasers "
           "have pushed the index beyond what liquidity providers need; the next 30 minutes tend to give part back.",
           {"base_min": [5, 10, 15], "k": [1.5, 2.0, 2.5]}, _multi_stretch, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-549", "Persistence-regime bar-break follow",
           "When the rolling lag-1 return autocorrelation is positive (orders are being sliced and executed in one "
           "direction), a close beyond the previous bar's extreme is more likely to continue than to bounce.",
           {"win_min": [30, 60, 90], "th": [0.05, 0.1, 0.2]}, _persist_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-550", "Clock-block colour streak exhaustion fade",
           "After several consecutive clock-aligned blocks of the same colour, the participants who wanted that "
           "direction are done; fade the move at the block close that completes the streak.",
           {"blk_min": [10, 15, 30], "run": [2, 3, 4]}, _block_streak, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-551", "Schaff-style double-stochastic MACD turn follow",
           "Stochastic of a stochastic of the MACD gives an early, bounded cycle signal; a cross out of the low zone "
           "marks the start of a push that momentum followers extend.",
           {"cycle_min": [10, 20, 30], "lo": [15, 25, 35]}, _schaff, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-552", "Gap-bar reversal toward the prior close",
           "A bar that opens far from the previous close (stops or a large market order) and closes back against the "
           "gap shows the impulse had no follow-up; the gap tends to fill.",
           {"k": [0.25, 0.5, 1.0]}, _gap_reversal, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-553", "Efficiency-collapse trend-end fade",
           "A very efficient (one-way) run followed by a collapse of the path-efficiency ratio means the one-sided "
           "flow has stopped; price tends to revert toward the middle of the run.",
           {"win_min": [30, 60, 90], "hi": [0.5, 0.6, 0.7]}, _eff_collapse, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-554", "TRIX zero-cross follow",
           "The one-bar rate of change of a triple-smoothed EMA filters out noise; its zero cross marks a persistent "
           "change of direction that trend followers act on.",
           {"n_min": [5, 10, 15]}, _trix, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-555", "Block-end extreme close fade",
           "A clock block that is wide for its length and closes at its own extreme was driven by late urgency; the "
           "next block usually retraces part of it.",
           {"blk_min": [15, 30, 60], "k": [1.0, 1.5, 2.0]}, _block_end_extreme, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-556", "Range-top dwell then slip fade",
           "After price has sat at the top (bottom) of its rolling range for several minutes, the first clear slip "
           "back shows buyers (sellers) gave up; the dwell was distribution, so follow the slip.",
           {"win_min": [30, 60, 90], "dwell_min": [5, 10, 15]}, _top_dwell, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-557", "Single-bar VWAP slice follow",
           "One large bar that opens on one side of the session VWAP and closes on the other, on above-average "
           "volume, is an institutional shift of the day's average price; follow it.",
           {"k": [1.0, 1.5, 2.0], "vol_k": [0.0, 1.0, 1.5]}, _vwap_slice, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
