"""Conveyor batch B-072 (agent, 2026-11-22). Mixed theme: absorption, round numbers, day-open, wicks, bands, flow."""
from __future__ import annotations

import numpy as np
from b3.esteira import Family


def _atr(ctx, n):
    def f():
        pc = ctx.prev(ctx.c, 1)
        tr = ctx.h - ctx.l
        gap = np.where(np.isfinite(pc), np.maximum(np.abs(ctx.h - pc), np.abs(ctx.l - pc)), 0.0)
        return ctx.roll(np.maximum(tr, gap), n, "mean")
    return ctx.cached(("atr", n), f)


def _absorb(ctx, p):
    k, nb = p["vol_k"], ctx.bars(p["move_min"])
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    rng = ctx.h - ctx.l
    body = np.abs(ctx.c - ctx.o)
    ab = (ctx.v > k * med) & (rng > 0) & (body <= 0.25 * rng)
    move = ctx.c - ctx.prev(ctx.c, nb)
    atr = _atr(ctx, max(nb, 5))
    long = ab & (move <= -atr)
    short = ab & (move >= atr)
    return long.astype(int) - short.astype(int)


def _round_hold(ctx, p):
    step, t = float(p["step"]), float(p["touch_pts"])
    lvl = np.round(ctx.c / step) * step
    long = (ctx.l <= lvl + t) & (ctx.o > lvl + t) & (ctx.c > lvl + t)
    short = (ctx.h >= lvl - t) & (ctx.o < lvl - t) & (ctx.c < lvl - t)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _open_recross(ctx, p):
    k, nb = p["k"], ctx.bars(p["lookback_min"])
    r = ctx.c / ctx.day_open - 1.0
    typical = ctx.cached("abs_ret_same_minute", lambda: ctx.same_minute(np.abs(r), "mean"))
    up_before = ctx.roll(r, nb, "max", include_current=False) >= k * typical
    dn_before = ctx.roll(r, nb, "min", include_current=False) <= -k * typical
    short = up_before & (ctx.c < ctx.day_open)
    long = dn_before & (ctx.c > ctx.day_open)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _wick_skew(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    lower = np.minimum(ctx.o, ctx.c) - ctx.l
    upper = ctx.h - np.maximum(ctx.o, ctx.c)
    rng = ctx.h - ctx.l
    with np.errstate(invalid="ignore", divide="ignore"):
        skew = (ctx.roll(lower, nb, "sum") - ctx.roll(upper, nb, "sum")) / ctx.roll(rng, nb, "sum")
    return ctx.cross(skew > th).astype(int) - ctx.cross(skew < -th).astype(int)


def _keltner_follow(ctx, p):
    n, k = int(p["ema_bars"]), p["k"]
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    atr = _atr(ctx, n)
    return ctx.cross(ctx.c > ema + k * atr).astype(int) - ctx.cross(ctx.c < ema - k * atr).astype(int)


def _keltner_reentry(ctx, p):
    n, k = int(p["ema_bars"]), p["k"]
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    atr = _atr(ctx, n)
    up, lo = ema + k * atr, ema - k * atr
    pc = ctx.prev(ctx.c, 1)
    short = (pc > ctx.prev(up, 1)) & (ctx.c <= up)
    long = (pc < ctx.prev(lo, 1)) & (ctx.c >= lo)
    return long.astype(int) - short.astype(int)


def _squeeze_break(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    bw = ctx.roll(ctx.c, nb, "std") / ctx.c
    med = ctx.cached(("bw_med", nb), lambda: ctx.same_minute(bw, "median"))
    sq = ctx.prev(bw <= k * med, 1) == 1
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    long = sq & (ctx.c > hi)
    short = sq & (ctx.c < lo)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _tp_thrust(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    sd = ctx.roll(tp, nb, "std")
    with np.errstate(invalid="ignore", divide="ignore"):
        z = (tp - ctx.roll(tp, nb, "mean")) / sd
    return ctx.cross(z > th).astype(int) - ctx.cross(z < -th).astype(int)


def _mfi_exit(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    d = tp - ctx.prev(tp, 1)
    pos = np.where(d > 0, tp * ctx.v, 0.0)
    neg = np.where(d < 0, tp * ctx.v, 0.0)
    P, N = ctx.roll(pos, nb, "sum"), ctx.roll(neg, nb, "sum")
    with np.errstate(invalid="ignore", divide="ignore"):
        mfi = 100.0 * P / (P + N)
    pm = ctx.prev(mfi, 1)
    long = (pm < th) & (mfi >= th)
    short = (pm > 100 - th) & (mfi <= 100 - th)
    return long.astype(int) - short.astype(int)


def _stair(ctx, p):
    m, vw = int(p["m"]), int(p["vwap_side"])
    up = ((ctx.h > ctx.prev(ctx.h, 1)) & (ctx.l > ctx.prev(ctx.l, 1))).astype(float)
    dn = ((ctx.h < ctx.prev(ctx.h, 1)) & (ctx.l < ctx.prev(ctx.l, 1))).astype(float)
    lu = ctx.roll(up, m, "sum") == m
    ld = ctx.roll(dn, m, "sum") == m
    if vw:
        v = ctx.vwap()
        lu = lu & (ctx.c > v)
        ld = ld & (ctx.c < v)
    return ctx.cross(lu).astype(int) - ctx.cross(ld).astype(int)


FAMILIES = [
    Family("E-718", "Absorption bar after a run",
           "A heavy-volume bar with a tiny body after a directional run means aggressive orders were absorbed by "
           "passive size; the run's participants are trapped, so fade it.",
           {"vol_k": [1.5, 2.0, 3.0], "move_min": [10, 20, 30]}, _absorb,
           source="assistant reasoning (volume spread analysis)", author="agent"),
    Family("E-719", "Round-number bounce",
           "Index points at round multiples attract resting orders and option hedging; a bar that dips to the level "
           "and closes clear above it (or the mirror) is a defended level.",
           {"step": [500, 1000, 2500], "touch_pts": [50, 100]}, _round_hold, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-720", "Day-open recross continuation",
           "After the day traded well on one side of its open, a close back through the open means the day's early "
           "buyers/sellers lost control; follow the cross.",
           {"k": [0.5, 1.0, 1.5], "lookback_min": [30, 60, 120]}, _open_recross,
           source="assistant reasoning", author="agent"),
    Family("E-721", "Wick skew flow",
           "Over a window, long lower tails versus upper tails show dip buying being absorbed; follow the side "
           "whose tails dominate.",
           {"win_min": [15, 30, 60], "th": [0.2, 0.3, 0.4]}, _wick_skew, source="assistant reasoning (candle tails)",
           author="agent"),
    Family("E-722", "Keltner channel break follow",
           "A close beyond EMA plus k ATR is a volatility expansion that stop orders and trend followers extend.",
           {"ema_bars": [20, 40], "k": [1.5, 2.0, 2.5]}, _keltner_follow, source="Keltner channel (classic technical analysis)",
           author="agent"),
    Family("E-723", "Keltner channel re-entry fade",
           "A close that stretched beyond the channel and returns inside marks an exhausted push; fade back toward the mean.",
           {"ema_bars": [20, 40], "k": [2.0, 2.5, 3.0]}, _keltner_reentry, source="Keltner channel (classic technical analysis)",
           author="agent"),
    Family("E-724", "Bandwidth squeeze break",
           "When n-bar price dispersion is low versus its same-minute norm, liquidity providers are crowded and a "
           "break of the window range releases pent-up flow.",
           {"win_min": [20, 30, 60], "k": [0.5, 0.7, 0.9]}, _squeeze_break, source="Bollinger bandwidth squeeze",
           author="agent"),
    Family("E-725", "Typical-price z thrust",
           "A typical-price z-score crossing a threshold shows a statistically unusual push relative to the recent "
           "window; momentum traders continue it.",
           {"win_min": [30, 60, 120], "th": [1.5, 2.0, 2.5]}, _tp_thrust, source="CCI-style momentum (assistant variant)",
           author="agent"),
    Family("E-726", "MFI exit from extreme zone",
           "Money-flow ratio leaving an extreme zone shows one-sided volume has dried up, so price tends to revert.",
           {"win_min": [15, 30, 60], "th": [15, 20, 25]}, _mfi_exit, source="Money Flow Index (Quong & Soudack)",
           author="agent"),
    Family("E-727", "Stair-step highs and lows",
           "Consecutive bars each making higher highs and higher lows (or lower both) is an orderly trend that "
           "late participants chase; follow the m-th step.",
           {"m": [2, 3, 4], "vwap_side": [0, 1]}, _stair, source="assistant reasoning (Dow-style swing sequence)",
           author="agent"),
]
