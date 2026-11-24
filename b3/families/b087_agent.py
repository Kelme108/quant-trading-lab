"""Conveyor batch B-087 (agent, 2026-11-23). Less-mined mechanisms: return-volume correlation, stale quotes, range share,
wick-chop regime, hour-open recross, semi-variance, volume POC, triple touch, candle soldiers, Tenkan/Kijun."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _ret(ctx):
    return ctx.c / ctx.prev(ctx.c, 1) - 1.0


def _retvol_corr(ctx, p):
    nb, thr = ctx.bars(p["win_min"]), p["corr_min"]
    r = _ret(ctx)
    v = ctx.v
    mr, mv = ctx.roll(r, nb, "mean"), ctx.roll(v, nb, "mean")
    cov = ctx.roll(r * v, nb, "mean") - mr * mv
    den = ctx.roll(r, nb, "std") * ctx.roll(v, nb, "std")
    corr = np.where(den > 0, cov / np.where(den > 0, den, 1.0), 0.0)
    net = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    long = (corr >= thr) & (net > 0)
    short = (corr >= thr) & (net < 0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _stale_break(ctx, p):
    nb, thr = ctx.bars(p["win_min"]), p["share"]
    pc = ctx.prev(ctx.c, 1)
    zero = ((ctx.c == pc) & ~np.isnan(pc)).astype(float)
    share = ctx.roll(zero, nb, "mean", include_current=False)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    ok = share >= thr
    return ctx.cross(ok & (ctx.c > hi)).astype(int) - ctx.cross(ok & (ctx.c < lo)).astype(int)


def _range_share(ctx, p):
    nb, thr = ctx.bars(p["win_min"]), p["share"]
    sh, sl = ctx.session_high(True), ctx.session_low(True)
    sr = sh - sl
    rn = ctx.roll(ctx.h, nb, "max") - ctx.roll(ctx.l, nb, "min")
    share = np.where(sr > 0, rn / np.where(sr > 0, sr, 1.0), 0.0)
    prog = ctx.bar_in_day >= 2 * nb
    pc = ctx.prev(ctx.c, nb)
    long = prog & (share >= thr) & (ctx.c > pc) & (ctx.h >= sh)
    short = prog & (share >= thr) & (ctx.c < pc) & (ctx.l <= sl)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _wick_chop_fade(ctx, p):
    nb, thr = ctx.bars(p["win_min"]), p["ratio"]
    rng = ctx.roll(ctx.h - ctx.l, nb, "mean")
    step = ctx.roll(np.abs(ctx.c - ctx.prev(ctx.c, 1)), nb, "mean")
    ratio = np.where(step > 0, rng / np.where(step > 0, step, 1.0), 0.0)
    m = ctx.roll(ctx.c, nb, "mean")
    sd = ctx.roll(ctx.c, nb, "std")
    z = np.where(sd > 0, (ctx.c - m) / np.where(sd > 0, sd, 1.0), 0.0)
    chop = ratio >= thr
    short = chop & (z >= 1.5)
    long = chop & (z <= -1.5)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _hour_open_recross(ctx, p):
    nb = ctx.bars(p["away_min"])
    d = pd.DataFrame({"d": ctx.day, "b": ctx.minute // 60, "o": ctx.o})
    g = d.groupby(["d", "b"])
    hopen = g["o"].transform("first").to_numpy()
    k = g.cumcount().to_numpy()
    below = (ctx.c < hopen).astype(float)
    above = (ctx.c > hopen).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    ok = k > nb
    up = ok & was_below & (ctx.c > hopen)
    dn = ok & was_above & (ctx.c < hopen)
    return up.astype(int) - dn.astype(int)


def _semivar_follow(ctx, p):
    nb, thr = ctx.bars(p["win_min"]), p["share"]
    r = _ret(ctx)
    up = ctx.roll(np.where(r > 0, r * r, 0.0), nb, "sum")
    dn = ctx.roll(np.where(r < 0, r * r, 0.0), nb, "sum")
    tot = up + dn
    ratio = np.where(tot > 0, up / np.where(tot > 0, tot, 1.0), 0.5)
    ratio = np.where(np.isnan(tot), 0.5, ratio)
    return ctx.cross(ratio >= thr).astype(int) - ctx.cross(ratio <= 1 - thr).astype(int)


def _poc_series(ctx):
    n = ctx.n
    out = np.full(n, np.nan)
    binsz = np.maximum(ctx.day_open * 0.0005, 1e-9)
    bins = np.floor(ctx.c / binsz).astype(np.int64)
    day = ctx.day
    cnt: dict = {}
    best, poc, cur = -1.0, 0, -1
    for i in range(n):
        if day[i] != cur:
            cur, cnt, best, poc = day[i], {}, -1.0, 0
        b = int(bins[i])
        w = cnt.get(b, 0.0) + ctx.v[i]
        cnt[b] = w
        if w > best:
            best, poc = w, b
        out[i] = (poc + 0.5) * binsz[i]
    return out


def _poc_magnet(ctx, p):
    k = p["k_atr"]
    nb = 30
    poc = ctx.cached("poc", lambda: _poc_series(ctx))
    atr = ctx.roll(ctx.h - ctx.l, nb, "mean")
    ok = ctx.bar_in_day >= nb
    dist = ctx.c - poc
    short = ok & (dist >= k * atr * np.sqrt(nb))
    long = ok & (dist <= -k * atr * np.sqrt(nb))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _triple_touch(ctx, p):
    nb = ctx.bars(p["win_min"])
    tol = p["tol_atr"]
    atr = ctx.roll(ctx.h - ctx.l, max(nb, 5), "mean")
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    th = np.zeros(ctx.n)
    tl = np.zeros(ctx.n)
    for i in range(1, nb + 1):
        ph, pl = ctx.prev(ctx.h, i), ctx.prev(ctx.l, i)
        th += (ph >= hi - tol * atr).astype(float)
        tl += (pl <= lo + tol * atr).astype(float)
    long = (th >= 3) & (ctx.c > hi)
    short = (tl >= 3) & (ctx.c < lo)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _soldiers(ctx, p):
    bf = p["body_frac"]
    nb = ctx.bars(p["ema_min"])
    ema = ctx.cached(("ema", nb), lambda: ctx.ema(ctx.c, nb))
    rng = ctx.h - ctx.l
    body = ctx.c - ctx.o
    strong_up = (body > 0) & (body >= bf * rng)
    strong_dn = (body < 0) & (-body >= bf * rng)
    o1, c1 = ctx.prev(ctx.o, 1), ctx.prev(ctx.c, 1)
    o2, c2 = ctx.prev(ctx.o, 2), ctx.prev(ctx.c, 2)
    up = (strong_up & (ctx.prev(strong_up.astype(float), 1) == 1) & (ctx.prev(strong_up.astype(float), 2) == 1)
          & (ctx.c > c1) & (c1 > c2) & (ctx.o >= o1) & (ctx.o <= c1) & (o1 >= o2) & (o1 <= c2)
          & (ctx.prev(ctx.c, 3) < ema))
    dn = (strong_dn & (ctx.prev(strong_dn.astype(float), 1) == 1) & (ctx.prev(strong_dn.astype(float), 2) == 1)
          & (ctx.c < c1) & (c1 < c2) & (ctx.o <= o1) & (ctx.o >= c1) & (o1 <= o2) & (o1 >= c2)
          & (ctx.prev(ctx.c, 3) > ema))
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _tenkan_kijun(ctx, p):
    n1 = ctx.bars(p["tenkan_min"])
    n2 = 3 * n1
    t = (ctx.roll(ctx.h, n1, "max") + ctx.roll(ctx.l, n1, "min")) / 2
    kj = (ctx.roll(ctx.h, n2, "max") + ctx.roll(ctx.l, n2, "min")) / 2
    up = (t > kj) & (ctx.c > kj)
    dn = (t < kj) & (ctx.c < kj)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


FAMILIES = [
    Family("E-868", "Return-volume correlation follow",
           "When bar returns and volumes correlate strongly positively over a window, volume arrives with the move "
           "(informed, aggressive flow); follow the net direction at the first crossing.",
           {"win_min": [20, 30, 45], "corr_min": [0.3, 0.4, 0.5]}, _retvol_corr,
           source="assistant reasoning", author="agent"),
    Family("E-869", "Stale-close share break",
           "A window with many unchanged closes means quoting is stale and the book is left alone; the first close "
           "beyond the window's range shows who finally acts; follow.",
           {"win_min": [10, 20, 30], "share": [0.2, 0.3, 0.4]}, _stale_break,
           source="assistant reasoning", author="agent", markets=("WIN",)),
    Family("E-870", "Range-share thrust at a session extreme",
           "When the last window covers most of the whole session range so far and sets a session extreme, one side "
           "has taken the day in one thrust with no balance; follow.",
           {"win_min": [10, 20, 30], "share": [0.5, 0.6, 0.7]}, _range_share,
           source="assistant reasoning", author="agent"),
    Family("E-871", "Wick-chop regime stretch fade",
           "Bar ranges much larger than the net bar-to-bar steps mean two-sided wicks: a mean-reverting regime where "
           "liquidity providers win; fade a 1.5 sigma stretch inside it.",
           {"win_min": [20, 30, 45], "ratio": [2.0, 2.5, 3.0]}, _wick_chop_fade,
           source="assistant reasoning", author="agent"),
    Family("E-872", "Hour-open recross follow",
           "The price at the start of each clock hour is a reference for hourly algos and desks; after a spell on one "
           "side, a close back across it moves the average hourly participant to the other side; follow.",
           {"away_min": [10, 15, 20]}, _hour_open_recross,
           source="assistant reasoning", author="agent"),
    Family("E-873", "Semi-variance dominance follow",
           "When the squared up-moves dominate the squared down-moves in a window, the volatility is upside-driven "
           "(buyers pay up); follow the first crossing of the dominance threshold.",
           {"win_min": [20, 30, 45], "share": [0.75, 0.8, 0.85]}, _semivar_follow,
           source="assistant reasoning", author="agent"),
    Family("E-874", "Volume point-of-control magnet fade",
           "The price bin with most volume today is the accepted value; price stretched far from it by impatient flow "
           "is pulled back as the auction rebalances; fade the stretch.",
           {"k_atr": [1.0, 1.5, 2.0]}, _poc_magnet,
           source="auction market theory (value area / point of control)", author="agent", markets=("WIN",)),
    Family("E-875", "Triple-touch ceiling/floor break",
           "Three or more highs (lows) stopping at the same level inside a window show resting limit orders there; "
           "a close through it consumes them and releases stops; follow.",
           {"win_min": [20, 30, 45], "tol_atr": [0.1, 0.2, 0.3]}, _triple_touch,
           source="assistant reasoning", author="agent", markets=("WIN",)),
    Family("E-876", "Three soldiers/crows reversal from the wrong side of the EMA",
           "Three strong, nested same-colour bodies that start from the far side of the EMA show a forced "
           "change of control after an exhausted move; trade the new direction.",
           {"body_frac": [0.5, 0.6, 0.7], "ema_min": [30, 60]}, _soldiers,
           source="candlestick literature (three white soldiers / black crows)", author="agent", markets=("WIN",)),
    Family("E-877", "Tenkan/Kijun cross with price agreement",
           "Midpoint of the short high/low channel crossing the midpoint of a 3x longer channel while price stays on "
           "that side shows short-horizon traders overtaking the slow ones (Ichimoku base lines); follow.",
           {"tenkan_min": [10, 15, 20]}, _tenkan_kijun,
           source="Ichimoku Kinko Hyo (assistant reasoning)", author="agent"),
]
