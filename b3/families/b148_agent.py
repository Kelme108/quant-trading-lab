"""Conveyor batch B-148 (agent, 2026-11-24). Classic oscillator/trend constructions not yet screened, plus volume-effort and clock-block ideas."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _ichimoku(ctx, p):
    n = ctx.bars(p["tenkan_min"])
    m = ctx.bars(3 * p["tenkan_min"])
    ten = (ctx.roll(ctx.h, n, "max") + ctx.roll(ctx.l, n, "min")) / 2.0
    kij = (ctx.roll(ctx.h, m, "max") + ctx.roll(ctx.l, m, "min")) / 2.0
    long = (ten > kij) & (ctx.c > kij)
    short = (ten < kij) & (ctx.c < kij)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _stoch(ctx, p):
    n = ctx.bars(p["window_min"])
    th = p["th"]
    hh, ll = ctx.roll(ctx.h, n, "max"), ctx.roll(ctx.l, n, "min")
    rng = hh - ll
    with np.errstate(invalid="ignore", divide="ignore"):
        k = np.where(rng > 0, (ctx.c - ll) / rng, np.nan)
    d = ctx.roll(k, 3, "mean")
    long = (k > d) & (d < th)
    short = (k < d) & (d > 1 - th)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _vortex(ctx, p):
    n = ctx.bars(p["window_min"])
    pc, ph, pl = ctx.prev(ctx.c), ctx.prev(ctx.h), ctx.prev(ctx.l)
    tr = np.fmax(np.fmax(ctx.h - ctx.l, np.abs(ctx.h - pc)), np.abs(ctx.l - pc))
    vmp, vmm = np.abs(ctx.h - pl), np.abs(ctx.l - ph)
    st = ctx.roll(tr, n, "sum")
    with np.errstate(invalid="ignore", divide="ignore"):
        vip = ctx.roll(vmp, n, "sum") / st
        vim = ctx.roll(vmm, n, "sum") / st
    mg = p["margin"]
    return ctx.cross(vip - vim > mg).astype(int) - ctx.cross(vim - vip > mg).astype(int)


def _trix(ctx, p):
    s = ctx.bars(p["span_min"])
    e3 = ctx.ema(ctx.ema(ctx.ema(ctx.c, s), s), s)
    t = e3 - ctx.prev(e3)
    return ctx.cross(t > 0).astype(int) - ctx.cross(t < 0).astype(int)


def _force(ctx, p):
    s = ctx.bars(p["span_min"])
    fi = (ctx.c - ctx.prev(ctx.c)) * ctx.v
    fe = ctx.ema(np.nan_to_num(fi, nan=0.0), s)
    return ctx.cross(fe > 0).astype(int) - ctx.cross(fe < 0).astype(int)


def _macd_hist(ctx, p):
    sc = p["scale"]
    f, sl, g = ctx.bars(12 * sc), ctx.bars(26 * sc), ctx.bars(9 * sc)
    macd = ctx.ema(ctx.c, f) - ctx.ema(ctx.c, max(sl, f + 1))
    hist = macd - ctx.ema(macd, g)
    return ctx.cross(hist > 0).astype(int) - ctx.cross(hist < 0).astype(int)


def _mfi(ctx, p):
    n = ctx.bars(p["window_min"])
    th = p["th"]
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    d = tp - ctx.prev(tp)
    flow = tp * ctx.v
    pos = np.where(np.isnan(d), np.nan, np.where(d > 0, flow, 0.0))
    neg = np.where(np.isnan(d), np.nan, np.where(d < 0, flow, 0.0))
    sp, sn = ctx.roll(pos, n, "sum"), ctx.roll(neg, n, "sum")
    with np.errstate(invalid="ignore", divide="ignore"):
        mfi = np.where(sp + sn > 0, 100.0 * sp / (sp + sn), np.nan)
    long = mfi > th
    short = mfi < 100 - th
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _absorption(ctx, p):
    k, r = p["vol_k"], p["range_k"]
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    rng = ctx.h - ctx.l
    typ = ctx.roll(rng, ctx.bars(60), "mean", include_current=False)
    mv = ctx.c - ctx.prev(ctx.c, ctx.bars(10))
    base = (ctx.v >= k * med) & (rng > 0) & (rng <= r * typ) & (np.abs(mv) >= 2.0 * typ)
    return ctx.cross(base & (mv < 0)).astype(int) - ctx.cross(base & (mv > 0)).astype(int)


def _us_open_surge(ctx, p):
    k, bf = p["vol_k"], p["body_frac"]
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    w = (ctx.minute >= 10 * 60 + 25) & (ctx.minute <= 11 * 60 + 40)
    rng = ctx.h - ctx.l
    body = ctx.c - ctx.o
    big = w & (ctx.v >= k * med) & (rng > 0) & (np.abs(body) >= bf * rng)
    return ctx.cross(big & (body > 0)).astype(int) - ctx.cross(big & (body < 0)).astype(int)


def _block_break(ctx, p):
    bm, mg = int(p["block_min"]), p["margin_frac"]
    key = ctx.day.astype(np.int64) * 10000 + (ctx.minute // bm).astype(np.int64)
    df = pd.DataFrame({"k": key, "h": ctx.h, "l": ctx.l})
    agg = df.groupby("k").agg(h=("h", "max"), l=("l", "min"))
    dk = agg.index.to_numpy() // 10000
    same = np.r_[False, dk[1:] == dk[:-1]]
    ph = pd.Series(np.where(same, agg["h"].shift(1).to_numpy(), np.nan), index=agg.index)
    pl = pd.Series(np.where(same, agg["l"].shift(1).to_numpy(), np.nan), index=agg.index)
    prh = pd.Series(key).map(ph).to_numpy(float)
    prl = pd.Series(key).map(pl).to_numpy(float)
    up = ctx.c > prh * (1 + mg)
    dn = ctx.c < prl * (1 - mg)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


A = "assistant reasoning"
FAMILIES = [
    Family("E-1478", "Ichimoku tenkan/kijun cross above the base line",
           "Midpoint of the short channel crossing the midpoint of a 3x longer channel, with price on the same side, "
           "marks a shift of the dominant flow that slower trend followers join.",
           {"tenkan_min": [10, 20, 30]}, _ichimoku, markets=("WIN",), source=A, author="agent"),
    Family("E-1479", "Stochastic %K/%D cross in the extreme zone",
           "A %K cross of %D inside the oversold/overbought zone shows the last push is losing force; "
           "late stop-chasers are exhausted, so fade into the middle of the range.",
           {"window_min": [15, 30, 60], "th": [0.1, 0.2]}, _stoch, markets=("WIN",), source=A, author="agent"),
    Family("E-1480", "Vortex indicator crossover",
           "Vortex compares upward and downward movement against true range; a crossover shows directional "
           "movement overtaking the opposite one and trend followers continue it.",
           {"window_min": [15, 30, 60], "margin": [0.0, 0.1]}, _vortex, markets=("WIN",), source=A, author="agent"),
    Family("E-1481", "Triple-smoothed momentum zero cross",
           "A triple EMA that turns up filters out one-bar noise; the turn marks a persistent shift in the "
           "net order flow that is slow to be recognised.",
           {"span_min": [10, 20, 40]}, _trix, markets=("WIN",), source=A, author="agent"),
    Family("E-1482", "Force index zero cross",
           "Price change times volume, smoothed: its sign change shows that volume is now behind the other side, "
           "which tends to persist while the aggressor keeps working the order.",
           {"span_min": [10, 20, 30]}, _force, markets=("WIN",), source=A, author="agent"),
    Family("E-1483", "MACD histogram sign change",
           "The histogram turns when momentum of the trend itself changes sign, before the EMAs cross; "
           "acting on it catches the start of the next leg.",
           {"scale": [0.5, 1.0, 2.0]}, _macd_hist, markets=("WIN",), source=A, author="agent"),
    Family("E-1484", "Money-flow index extreme re-entry",
           "Volume-weighted RSI returning from an extreme means the heavy-volume selling or buying is spent; "
           "the side that forced prices there has no more size, so fade back.",
           {"window_min": [15, 30, 60], "th": [10, 20]}, _mfi, source=A, author="agent"),
    Family("E-1485", "Effort without result absorption fade",
           "After a move, a bar with large volume but a small range shows a passive large player absorbing "
           "the aggressors; the move runs out and price goes the other way.",
           {"vol_k": [1.5, 2.0, 3.0], "range_k": [0.6, 0.8, 1.0]}, _absorption, markets=("WIN",), source=A, author="agent"),
    Family("E-1486", "US-open volume surge bar follow",
           "Around the New York cash open (10:30-11:30 local) index flow from US participants arrives; a "
           "strong-bodied bar with unusual volume is the first push of that flow and is followed.",
           {"vol_k": [2.0, 3.0, 4.0], "body_frac": [0.0, 0.5, 0.7]}, _us_open_surge, markets=("WIN",), source=A, author="agent"),
    Family("E-1487", "Previous clock-block high/low break follow",
           "The previous half-hour or hour block is a recent value area; a close outside it means the "
           "new block has rejected that value and breakout orders keep pushing.",
           {"block_min": [30, 60, 90], "margin_frac": [0.0, 0.0003, 0.0006]}, _block_break, markets=("WIN",), source=A, author="agent"),
]
