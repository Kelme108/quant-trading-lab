"""Conveyor batch B-047 (agent, 2026-11-21). Mixed micro-structure, regime and seasonality ideas on WIN."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family

SRC = "assistant reasoning"


def _seasonal_dev(ctx, p):
    k = p["k"]
    r = ctx.c / ctx.day_open - 1.0
    seas = ctx.cached("seas_r", lambda: ctx.same_minute(r, "mean"))
    typ = ctx.cached("seas_abs", lambda: ctx.same_minute(np.abs(r), "mean"))
    dev = r - seas
    ok = (typ > 0) & (ctx.bar_in_day >= ctx.bars(30))
    short = ok & (dev > k * typ)
    long = ok & (dev < -k * typ)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _autocorr_fade(ctx, p):
    n, th = ctx.bars(p["win_min"]), p["th"]
    ret = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    den = ctx.roll(ret ** 2, n, "mean")
    num = ctx.roll(ret * ctx.prev(ret, 1), n, "mean")
    ac = num / np.where(den > 0, den, np.nan)
    sd = np.sqrt(den)
    reg = ac < -th
    short = reg & (ret > 1.5 * sd)
    long = reg & (ret < -1.5 * sd)
    return long.astype(int) - short.astype(int)


def _upfrac_fade(ctx, p):
    n, q = ctx.bars(p["win_min"]), p["q"]
    up = ctx.roll((ctx.c > ctx.o).astype(float), n, "mean")
    dn = ctx.roll((ctx.c < ctx.o).astype(float), n, "mean")
    return ctx.cross(dn >= q).astype(int) - ctx.cross(up >= q).astype(int)


def _boll_reentry(ctx, p):
    n, m = ctx.bars(p["win_min"]), p["m"]
    mu = ctx.roll(ctx.c, n, "mean")
    sd = ctx.roll(ctx.c, n, "std")
    up, lo = mu + m * sd, mu - m * sd
    short = (ctx.prev(ctx.c, 1) > ctx.prev(up, 1)) & (ctx.c < up)
    long = (ctx.prev(ctx.c, 1) < ctx.prev(lo, 1)) & (ctx.c > lo)
    return long.astype(int) - short.astype(int)


def _vol_expansion(ctx, p):
    ns, k = ctx.bars(p["short_min"]), p["k"]
    nl = ctx.bars(60)
    rng = ctx.h - ctx.l
    ratio = ctx.roll(rng, ns, "mean") / ctx.roll(rng, nl, "mean")
    d = np.sign(ctx.c - ctx.prev(ctx.c, ns))
    cond = ratio > k
    return ctx.cross(cond & (d > 0)).astype(int) - ctx.cross(cond & (d < 0)).astype(int)


def _ema_stretch(ctx, p):
    n, k = ctx.bars(p["ema_min"]), p["k"]
    ema = ctx.ema(ctx.c, n)
    atr = ctx.roll(ctx.h - ctx.l, n, "mean")
    dist = ctx.c - ema
    return ctx.cross(dist < -k * atr).astype(int) - ctx.cross(dist > k * atr).astype(int)


def _rolling_vwap_cross(ctx, p):
    n, vk = ctx.bars(p["win_min"]), p["vol_k"]
    pv = ctx.roll(ctx.c * ctx.v, n, "sum")
    vv = ctx.roll(ctx.v, n, "sum")
    vw = pv / np.where(vv > 0, vv, np.nan)
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    heavy = ctx.v >= vk * med
    pc, pvw = ctx.prev(ctx.c, 1), ctx.prev(vw, 1)
    long = heavy & (ctx.c > vw) & (pc <= pvw)
    short = heavy & (ctx.c < vw) & (pc >= pvw)
    return long.astype(int) - short.astype(int)


def _donchian_mid(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    hi, lo = ctx.roll(ctx.h, n, "max"), ctx.roll(ctx.l, n, "min")
    width = hi - lo
    typ = ctx.cached(("w", n), lambda: ctx.prev_sessions(width, "mean"))
    mid = (hi + lo) / 2.0
    wide = width > k * typ
    pc, pm = ctx.prev(ctx.c, 1), ctx.prev(mid, 1)
    long = wide & (ctx.c > mid) & (pc <= pm)
    short = wide & (ctx.c < mid) & (pc >= pm)
    return long.astype(int) - short.astype(int)


def _prev_mid_reclaim(ctx, p):
    nb = ctx.bars(p["away_min"])
    mid = (ctx.prev_session_value("high") + ctx.prev_session_value("low")) / 2.0
    below = (ctx.c < mid).astype(float)
    above = (ctx.c > mid).astype(float)
    was_below = ctx.roll(below, nb, "mean", include_current=False) == 1
    was_above = ctx.roll(above, nb, "mean", include_current=False) == 1
    return (was_below & (ctx.c > mid)).astype(int) - (was_above & (ctx.c < mid)).astype(int)


def _seasonal_drift(ctx, p):
    h, q = ctx.bars(p["h_min"]), p["q"]
    s = pd.Series(ctx.c)
    fwd = (s.groupby(ctx.day).shift(-h) / s - 1.0).to_numpy()
    m = ctx.same_minute(fwd, "mean")
    a = ctx.same_minute(np.abs(fwd), "mean")
    cons = np.abs(m) / np.where(a > 0, a, np.nan)
    ok = cons >= q
    return ctx.cross(ok & (m > 0)).astype(int) - ctx.cross(ok & (m < 0)).astype(int)


FAMILIES = [
    Family("E-468", "Seasonal-path deviation fade",
           "Against the typical same-minute path of the day-return over 20 sessions, a day running far from it is "
           "stretched versus what intraday flow usually does; fade it.",
           {"k": [0.75, 1.0, 1.5]}, _seasonal_dev, markets=("WIN",), source=SRC, author="agent"),
    Family("E-469", "Negative-autocorrelation regime fade",
           "When the rolling lag-1 return autocorrelation is clearly negative, bar moves are bid-ask bounce and "
           "liquidity-taker overshoots; a large bar is faded by market makers.",
           {"win_min": [30, 60, 90], "th": [0.1, 0.2, 0.3]}, _autocorr_fade, markets=("WIN",), source=SRC, author="agent"),
    Family("E-470", "One-sided bar-colour fraction fade",
           "When almost all recent bars close one colour, aggressive flow is crowded on one side and the "
           "marginal buyer or seller is spent; fade the first time the fraction reaches the level.",
           {"win_min": [15, 30, 60], "q": [0.7, 0.8, 0.9]}, _upfrac_fade, markets=("WIN",), source=SRC, author="agent"),
    Family("E-471", "Bollinger band re-entry",
           "A close outside a rolling mean +/- m sigma band followed by a close back inside shows the push was "
           "absorbed; fade back toward the mean.",
           {"win_min": [20, 40, 60], "m": [2.0, 2.5, 3.0]}, _boll_reentry, markets=("WIN",), source=SRC, author="agent"),
    Family("E-472", "Volatility expansion direction follow",
           "When the short-window average range jumps well above the hour's average, new information is being "
           "priced in; follow the direction of the short window.",
           {"short_min": [5, 10, 15], "k": [1.5, 2.0, 2.5]}, _vol_expansion, markets=("WIN",), source=SRC, author="agent"),
    Family("E-473", "EMA stretch in range units fade",
           "A close far from its own EMA, measured in average bar ranges, is an inventory-driven stretch that "
           "mean-reverts as liquidity providers lean against it.",
           {"ema_min": [30, 60, 90], "k": [2.0, 3.0, 4.0]}, _ema_stretch, markets=("WIN",), source=SRC, author="agent"),
    Family("E-474", "Rolling-VWAP cross on heavy volume",
           "A close across the trailing-hour volume-weighted price on heavier than usual volume marks a shift in "
           "the cost basis of recent participants; follow it.",
           {"win_min": [30, 60, 120], "vol_k": [1.0, 1.5, 2.0]}, _rolling_vwap_cross, markets=("WIN",), source=SRC, author="agent"),
    Family("E-475", "Wide-window Donchian midline cross",
           "In a window wider than usual, a close crossing the high-low midpoint shows the balance point "
           "migrating; follow it.",
           {"win_min": [30, 60, 90], "k": [0.8, 1.0, 1.2]}, _donchian_mid, markets=("WIN",), source=SRC, author="agent"),
    Family("E-476", "Prior-session midpoint reclaim",
           "The midpoint of yesterday's range is a fair-value reference for today's participants; after trading "
           "on one side for a while, the first close across it hands control to the other side.",
           {"away_min": [10, 20, 40]}, _prev_mid_reclaim, markets=("WIN",), source=SRC, author="agent"),
    Family("E-477", "Seasonal minute-of-day forward drift",
           "If over the last 20 sessions the forward return from this minute has had a consistent sign (net drift "
           "close to its average absolute size), recurring flow (rebalancing, hedging) may repeat; trade it.",
           {"h_min": [15, 30, 60], "q": [0.3, 0.4, 0.5]}, _seasonal_drift, markets=("WIN",), source=SRC, author="agent"),
]
