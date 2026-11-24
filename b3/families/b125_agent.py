"""Conveyor batch B-125 (agent, 2026-11-24). Mixed themes: seasonality, regime autocorrelation, absorption, volume peaks, volatility expansion, range traversal, late VWAP, z-score fade, confirmation bar, percentile rank."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _bool(x):
    return np.asarray(x, bool)


def _seasonal_drift(ctx, p):
    nb = ctx.bars(p["horizon_min"])
    k = p["k"]
    s = pd.Series(ctx.c)
    fwd = (s.groupby(ctx.day).shift(-nb) / s - 1.0).to_numpy()
    mu = ctx.cached(("fwd_mu", nb), lambda: ctx.same_minute(np.nan_to_num(fwd), "mean"))
    sd = ctx.cached(("fwd_sd", nb), lambda: ctx.same_minute(np.nan_to_num(np.abs(fwd)), "mean"))
    with np.errstate(all="ignore"):
        z = mu / sd
    z = np.nan_to_num(z)
    return ctx.cross(z >= k).astype(int) - ctx.cross(z <= -k).astype(int)


def _autocorr_regime(ctx, p):
    n = ctx.bars(p["win_min"])
    th = p["th"]
    r = np.nan_to_num(ctx.c / ctx.prev(ctx.c, 1) - 1.0)
    r1 = np.nan_to_num(ctx.prev(r, 1))
    num = ctx.roll(r * r1, n, "mean")
    den = ctx.roll(r * r, n, "mean")
    with np.errstate(all="ignore"):
        ac = num / den
    ac = np.nan_to_num(ac)
    big = np.abs(r) > ctx.roll(np.abs(r), n, "mean")
    sgn = np.sign(r)
    long = ((ac >= th) & big & (sgn > 0)) | ((ac <= -th) & big & (sgn < 0))
    short = ((ac >= th) & big & (sgn < 0)) | ((ac <= -th) & big & (sgn > 0))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _absorption(ctx, p):
    n = ctx.bars(p["lookback_min"])
    k = p["vol_k"]
    rng = ctx.h - ctx.l
    vmed = ctx.cached("v_med_abs", lambda: ctx.same_minute(ctx.v, "median"))
    rmed = ctx.cached("r_med_abs", lambda: ctx.same_minute(rng, "median"))
    heavy = (ctx.v > k * vmed) & (rng < 0.8 * rmed)
    hi = ctx.roll(ctx.h, n, "max")
    lo = ctx.roll(ctx.l, n, "min")
    short = heavy & (ctx.h >= hi)
    long = heavy & (ctx.l <= lo)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _max_volume_bar(ctx, p):
    warm = ctx.bars(p["warm_min"])
    q = p["close_q"]
    cm = pd.Series(ctx.v).groupby(ctx.day).cummax().to_numpy()
    prevmax = pd.Series(ctx.v).groupby(ctx.day).transform(lambda z: z.cummax().shift(1)).to_numpy()
    newmax = (ctx.v > prevmax) & (ctx.bar_in_day >= warm)
    rng = np.maximum(ctx.h - ctx.l, 1e-9)
    loc = (ctx.c - ctx.l) / rng
    long = newmax & (loc >= 1 - q)
    short = newmax & (loc <= q)
    return long.astype(int) - short.astype(int)


def _vol_expansion(ctx, p):
    ns, nl = ctx.bars(5), ctx.bars(p["long_min"])
    k = p["k"]
    rng = ctx.h - ctx.l
    a = ctx.roll(rng, max(ns, 2), "mean")
    b = ctx.roll(rng, max(nl, 4), "mean")
    with np.errstate(all="ignore"):
        ratio = np.nan_to_num(a / b)
    up = ctx.cross(ratio >= k) & (ctx.c > ctx.o)
    dn = ctx.cross(ratio >= k) & (ctx.c < ctx.o)
    return up.astype(int) - dn.astype(int)


def _range_traverse(ctx, p):
    n = ctx.bars(p["win_min"])
    lo_th = p["lo"]
    sh = ctx.session_high(include_current=True)
    sl = ctx.session_low(include_current=True)
    wide = (sh - sl) >= 0.004 * ctx.day_open
    with np.errstate(all="ignore"):
        pos = np.nan_to_num((ctx.c - sl) / np.maximum(sh - sl, 1e-9), nan=0.5)
    was_lo = ctx.roll((pos <= lo_th).astype(float), n, "max", include_current=False) == 1
    was_hi = ctx.roll((pos >= 1 - lo_th).astype(float), n, "max", include_current=False) == 1
    long = wide & was_lo & (pos >= 0.5)
    short = wide & was_hi & (pos <= 0.5)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _late_vwap_cross(ctx, p):
    vw = ctx.vwap()
    late = ctx.minutes_to_close <= p["late_min"]
    up = late & (ctx.c > vw)
    dn = late & (ctx.c < vw)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _ema_z_fade(ctx, p):
    n, k = int(p["ema_bars"]), p["k"]
    ema = ctx.cached(("ema_z", n), lambda: ctx.ema(ctx.c, n))
    dev = ctx.c - ema
    sd = ctx.roll(dev, 3 * n, "std")
    with np.errstate(all="ignore"):
        z = np.nan_to_num(dev / sd)
    return ctx.cross(z <= -k).astype(int) - ctx.cross(z >= k).astype(int)


def _confirm_bar(ctx, p):
    k = p["k"]
    rng = ctx.h - ctx.l
    typ = ctx.cached("rng_typ_cb", lambda: ctx.same_minute(rng, "mean"))
    o1, c1, h1, l1, r1 = (ctx.prev(x, 1) for x in (ctx.o, ctx.c, ctx.h, ctx.l, rng))
    mid1 = (h1 + l1) / 2
    big_up = (c1 > o1) & (r1 >= k * ctx.prev(typ, 1)) & (c1 >= l1 + 0.75 * r1)
    big_dn = (c1 < o1) & (r1 >= k * ctx.prev(typ, 1)) & (c1 <= h1 - 0.75 * r1)
    long = big_up & (ctx.l >= mid1) & (rng < r1) & (ctx.c > ctx.o)
    short = big_dn & (ctx.h <= mid1) & (rng < r1) & (ctx.c < ctx.o)
    return long.astype(int) - short.astype(int)


def _rank_fade(ctx, p):
    n = ctx.bars(p["win_min"])
    th = p["th"]
    n = max(n, 5)
    s = pd.Series(ctx.c)
    rank = s.groupby(ctx.day).transform(
        lambda z: z.rolling(n, min_periods=n).apply(lambda w: (w[:-1] < w[-1]).mean(), raw=True)).to_numpy()
    rank = np.nan_to_num(rank, nan=0.5)
    return ctx.cross(rank <= 1 - th).astype(int) * 0 + ctx.cross(rank <= 1 - th).astype(int) - ctx.cross(rank >= th).astype(int)


FAMILIES = [
    Family("E-1248", "Seasonal same-minute forward drift",
           "Intraday flows (opening hedges, lunch, US open, closing auction) recur at the same clock minute; if the "
           "last 20 sessions' average forward return from this minute is large relative to its typical size, "
           "the same flow should recur: trade in that direction.",
           {"horizon_min": [15, 30], "k": [0.3, 0.5, 0.7]}, _seasonal_drift,
           source="assistant reasoning", author="agent"),
    Family("E-1249", "Autocorrelation-regime bar follow/fade",
           "When recent bar returns show positive lag-1 autocorrelation, participants are chasing and a large bar "
           "is followed; when negative, liquidity providers dominate and a large bar is faded.",
           {"win_min": [30, 60], "th": [0.15, 0.25, 0.35]}, _autocorr_regime,
           source="assistant reasoning", author="agent"),
    Family("E-1250", "Absorption bar at a rolling extreme",
           "A heavy-volume bar with a small range at a rolling high/low means aggressive orders were absorbed by "
           "passive liquidity; the aggressor is trapped, so fade.",
           {"lookback_min": [15, 30, 60], "vol_k": [1.5, 2.0, 3.0]}, _absorption,
           source="assistant reasoning (effort versus result, volume-price analysis)", author="agent"),
    Family("E-1251", "Session-max volume bar with extreme close",
           "The largest volume bar of the session closing near its high or low shows a decisive aggressor with "
           "no immediate rejection; follow it.",
           {"warm_min": [30, 60], "close_q": [0.2, 0.3, 0.4]}, _max_volume_bar,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1252", "Volatility expansion bar follow",
           "When short-term range jumps relative to the longer average, a new information flow has arrived; "
           "the direction of the expansion bar is followed.",
           {"long_min": [30, 60], "k": [1.5, 2.0, 2.5]}, _vol_expansion,
           markets=("WIN",), source="assistant reasoning (volatility clustering)", author="agent"),
    Family("E-1253", "Day-range traversal",
           "On a day with a wide range, price travelling from one end of the session range to its middle within "
           "a short time shows the other side has been overwhelmed; follow the traversal.",
           {"win_min": [30, 60, 90], "lo": [0.15, 0.25]}, _range_traverse,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1254", "Late-session VWAP cross",
           "Late in the session, institutional benchmark traders chase the VWAP; a cross of the VWAP in the "
           "last hours drags price toward the close in that direction.",
           {"late_min": [60, 90, 120]}, _late_vwap_cross,
           markets=("WIN",), source="assistant reasoning (VWAP benchmark execution)", author="agent"),
    Family("E-1255", "EMA deviation z-score fade",
           "A close stretched several standard deviations from its short EMA, measured against its own recent "
           "deviations, is an overshoot by impatient flow; fade back toward the mean.",
           {"ema_bars": [20, 40], "k": [2.0, 2.5, 3.0]}, _ema_z_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1256", "Impulse bar confirmation hold",
           "A strong closing bar followed by a smaller bar that holds above its midpoint and closes in the same "
           "direction shows buyers/sellers accepted the move; follow.",
           {"k": [1.0, 1.5, 2.0]}, _confirm_bar,
           markets=("WIN",), source="assistant reasoning (price-action confirmation)", author="agent"),
    Family("E-1257", "Rolling close-rank extreme fade",
           "A close that ranks at the very top (bottom) of the closes of the last hour is an extension of "
           "short-term supply/demand; fade it as it mean-reverts.",
           {"win_min": [30, 60], "th": [0.95, 0.98, 1.0]}, _rank_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
]
