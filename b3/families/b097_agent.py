"""Conveyor batch B-097 (agent, 2026-11-24). Mixed less-explored mechanisms: prior-day bias, volume clock, block candles, dwell share."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family

SRC = "assistant reasoning"


def _i(x):
    return x.astype(int)


def _prior_clv_vwap(ctx, p):
    th = p["clv_th"]
    pc, ph, pl = ctx.prev_session_value("close"), ctx.prev_session_value("high"), ctx.prev_session_value("low")
    with np.errstate(all="ignore"):
        clv = np.where(ph > pl, (pc - pl) / (ph - pl), np.nan)
        vw = ctx.vwap()
        long = ctx.cross((ctx.c > vw) & (clv >= th))
        short = ctx.cross((ctx.c < vw) & (clv <= 1 - th))
    return _i(long) - _i(short)


def _tweezer(ctx, p):
    nb, tol = ctx.bars(p["lookback_min"]), p["tol_frac"]
    with np.errstate(all="ignore"):
        hi = ctx.roll(ctx.h, nb, "max", include_current=False)
        lo = ctx.roll(ctx.l, nb, "min", include_current=False)
        hi_p, lo_p = ctx.prev(hi, 1), ctx.prev(lo, 1)
        h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
        c1, o1 = ctx.prev(ctx.c, 1), ctx.prev(ctx.o, 1)
        short = (h1 >= hi_p) & (np.abs(ctx.h - h1) <= tol * ctx.c) & (c1 > o1) & (ctx.c < ctx.o)
        long = (l1 <= lo_p) & (np.abs(ctx.l - l1) <= tol * ctx.c) & (c1 < o1) & (ctx.c > ctx.o)
    return _i(long) - _i(short)


def _dryup_pullback(ctx, p):
    k = int(p["pull_bars"])
    ema = ctx.cached(("ema", ctx.bars(60)), lambda: ctx.ema(ctx.c, max(2, ctx.bars(60))))
    with np.errstate(all="ignore"):
        dn = np.ones(ctx.n, bool)
        up = np.ones(ctx.n, bool)
        for i in range(1, k + 1):
            dn &= ctx.prev(ctx.c, i) < ctx.prev(ctx.c, i + 1)
            up &= ctx.prev(ctx.c, i) > ctx.prev(ctx.c, i + 1)
        dry = np.ones(ctx.n, bool)
        for i in range(1, k):
            dry &= ctx.prev(ctx.v, i) <= ctx.prev(ctx.v, i + 1)
        long = dn & dry & (ctx.c > ctx.prev(ctx.h, 1)) & (ctx.c > ema)
        short = up & dry & (ctx.c < ctx.prev(ctx.l, 1)) & (ctx.c < ema)
    return _i(long) - _i(short)


def _volume_lean(ctx, p):
    n, th = ctx.bars(p["win_min"]), p["th"]
    with np.errstate(all="ignore"):
        vwapn = ctx.roll(ctx.c * ctx.v, n, "sum") / ctx.roll(ctx.v, n, "sum")
        lean = (vwapn - ctx.roll(ctx.c, n, "mean")) / ctx.c
        long = ctx.cross(lean > th)
        short = ctx.cross(lean < -th)
    return _i(long) - _i(short)


def _big_bar_failure(ctx, p):
    n = ctx.bars(p["lookback_min"])
    rng = ctx.h - ctx.l
    with np.errstate(all="ignore"):
        mx = ctx.roll(rng, n, "max")
        big1 = ctx.prev(rng, 1) >= ctx.prev(mx, 1)
        mid = (ctx.prev(ctx.h, 1) + ctx.prev(ctx.l, 1)) / 2
        up1 = ctx.prev(ctx.c, 1) > ctx.prev(ctx.o, 1)
        dn1 = ctx.prev(ctx.c, 1) < ctx.prev(ctx.o, 1)
        short = big1 & up1 & (ctx.c < mid)
        long = big1 & dn1 & (ctx.c > mid)
    return _i(long) - _i(short)


def _block_engulf(ctx, p):
    B, ratio = int(p["block_min"]), p["ratio"]
    blk = ctx.minute // B
    bo = pd.Series(ctx.o).groupby([ctx.day, blk]).transform("first").to_numpy()
    body = ctx.c - bo
    is_last = (ctx.minute % B) + ctx.tf >= B
    idx = np.nonzero(is_last)[0]
    out = np.zeros(ctx.n, int)
    if len(idx) < 2:
        return out
    b = body[idx]
    same = ctx.day[idx[1:]] == ctx.day[idx[:-1]]
    cur, prv = b[1:], b[:-1]
    long = same & (cur > 0) & (prv < 0) & (cur >= ratio * np.abs(prv))
    short = same & (cur < 0) & (prv > 0) & (-cur >= ratio * np.abs(prv))
    out[idx[1:]] = long.astype(int) - short.astype(int)
    return out


def _volume_clock(ctx, p):
    step, thr = p["step"], p["min_move"]
    day = ctx.day
    tot = pd.Series(ctx.v).groupby(day).sum()
    exp = tot.shift(1).rolling(20, min_periods=10).mean()
    E = exp.reindex(range(int(day.max()) + 1)).to_numpy()[day]
    cum = pd.Series(ctx.v).groupby(day).cumsum().to_numpy()
    out = np.zeros(ctx.n, int)
    with np.errstate(all="ignore"):
        k = np.floor(cum / (step * E))
        kp = ctx.prev(k, 1)
        kp = np.where(np.isnan(kp), 0.0, kp)
        mark = (k > kp) & ~np.isnan(k)
    idx = np.nonzero(mark)[0]
    if len(idx) < 2:
        return out
    cm = ctx.c[idx]
    prevc = np.r_[np.nan, cm[:-1]]
    same = np.r_[False, day[idx][1:] == day[idx][:-1]]
    ref = np.where(same, prevc, ctx.day_open[idx])
    ret = cm / ref - 1.0
    if thr == 0:
        sig = np.sign(np.nan_to_num(ret))
    else:
        sig = np.where(ret >= thr, 1, np.where(ret <= -thr, -1, 0))
    out[idx] = sig.astype(int)
    return out


def _dwell_break(ctx, p):
    n, s = ctx.bars(p["win_min"]), p["share"]
    nb = ctx.bars(15)
    vw = ctx.vwap()
    with np.errstate(all="ignore"):
        above = ctx.roll((ctx.c > vw).astype(float), n, "mean")
        below = ctx.roll((ctx.c < vw).astype(float), n, "mean")
        hi = ctx.roll(ctx.h, nb, "max", include_current=False)
        lo = ctx.roll(ctx.l, nb, "min", include_current=False)
        long = ctx.cross((above >= s) & (ctx.c > hi))
        short = ctx.cross((below >= s) & (ctx.c < lo))
    return _i(long) - _i(short)


def _first_bar_extension(ctx, p):
    k = p["k"]
    first = ctx.bar_in_day == 0
    fh = pd.Series(np.where(first, ctx.h, np.nan)).groupby(ctx.day).transform("max").to_numpy()
    fl = pd.Series(np.where(first, ctx.l, np.nan)).groupby(ctx.day).transform("min").to_numpy()
    with np.errstate(all="ignore"):
        r = fh - fl
        ok = (ctx.bar_in_day > 0) & (r > 0)
        long = ctx.cross(ok & (ctx.c > fh + k * r))
        short = ctx.cross(ok & (ctx.c < fl - k * r))
    return _i(long) - _i(short)


def _macd_peak_fade(ctx, p):
    n, shrink = ctx.bars(p["peak_min"]), p["shrink"]
    f, s = max(2, ctx.bars(10)), max(3, ctx.bars(30))
    with np.errstate(all="ignore"):
        macd = ctx.ema(ctx.c, f) - ctx.ema(ctx.c, s)
        am = np.abs(macd)
        pk = ctx.roll(am, n, "max")
        avg = ctx.roll(am, n, "mean")
        base = (pk >= 2 * avg) & (am <= shrink * pk)
        short = ctx.cross(base & (macd > 0))
        long = ctx.cross(base & (macd < 0))
    return _i(long) - _i(short)


FAMILIES = [
    Family("E-968", "Prior-day close location bias on VWAP cross",
           "A session that closed in the top (bottom) of its range leaves trapped shorts (longs) and carry-over "
           "bias; the next day's cross back across VWAP on that side is followed.",
           {"clv_th": [0.6, 0.7, 0.8]}, _prior_clv_vwap, source=SRC, author="agent"),
    Family("E-969", "Tweezer top/bottom at a range extreme",
           "Two consecutive bars of opposite colour printing the same extreme at an n-minute high/low show a "
           "defended level; stops sit behind it and the reversal is faded into.",
           {"lookback_min": [20, 40, 60], "tol_frac": [0.0001, 0.0002, 0.0004]}, _tweezer,
           source=SRC, author="agent"),
    Family("E-970", "Dry-up pullback resume",
           "In an EMA trend, a pullback of falling closes on shrinking volume lacks sellers; the first bar through "
           "the prior bar's extreme resumes the trend.",
           {"pull_bars": [2, 3, 4]}, _dryup_pullback, source=SRC, author="agent"),
    Family("E-971", "Volume-weighted lean cross",
           "When the n-minute volume-weighted average sits above the plain average, volume traded at higher prices: "
           "buyers are the aggressors; follow the crossing of the lean threshold.",
           {"win_min": [20, 40, 60], "th": [0.00005, 0.0001, 0.0002]}, _volume_lean,
           source=SRC, author="agent"),
    Family("E-972", "Largest-bar midpoint failure",
           "The widest bar of the last n minutes is a thrust; if the next bar closes back through its midpoint the "
           "thrust is rejected and late entrants are trapped, so fade it.",
           {"lookback_min": [30, 60, 90]}, _big_bar_failure, source=SRC, author="agent"),
    Family("E-973", "Clock-block engulfing candle follow",
           "A block candle (15/30/60 min) of one colour that engulfs the previous opposite block shows control "
           "changing hands at a timeframe where position traders act; follow it.",
           {"block_min": [15, 30, 60], "ratio": [1.0, 1.5]}, _block_engulf, source=SRC, author="agent"),
    Family("E-974", "Volume-clock mark momentum",
           "Sampling by traded volume (fractions of the typical session volume) instead of clock time, the move "
           "since the previous mark tends to be continued by the flow that produced it.",
           {"step": [0.1, 0.15, 0.2], "min_move": [0.0, 0.0005, 0.001]}, _volume_clock,
           source=SRC, author="agent"),
    Family("E-975", "VWAP dwell share breakout",
           "A price that spent most of the last hour on one side of VWAP is under persistent institutional "
           "pressure; a fresh 15-minute extreme on that side continues.",
           {"win_min": [30, 60, 90], "share": [0.8, 0.9]}, _dwell_break, source=SRC, author="agent"),
    Family("E-976", "First-bar range multiple extension",
           "The first bar of the session marks the initial auction range; a close a full multiple of that range "
           "beyond it shows one-sided participation and follows through.",
           {"k": [0.5, 1.0, 2.0]}, _first_bar_extension, source=SRC, author="agent"),
    Family("E-977", "MACD amplitude peak rollover fade",
           "When trend momentum (MACD magnitude) falls off its n-minute peak the push is spent; fade back toward "
           "the mean.",
           {"peak_min": [30, 60, 90], "shrink": [0.6, 0.8]}, _macd_peak_fade, source=SRC, author="agent"),
]
