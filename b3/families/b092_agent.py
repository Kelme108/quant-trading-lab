"""Conveyor batch B-092 (agent, 2026-11-24). Mixed theme: cross-market lead/lag, band fades, channel and ribbon trend, flow, regime."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _sgn(long, short):
    return long.astype(int) - short.astype(int)


def _dollar_lead(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    ow = ctx.other_close()
    with np.errstate(all="ignore"):
        ro = ow / ctx.prev(ow, nb) - 1.0
        rw = ctx.c / ctx.prev(ctx.c, nb) - 1.0
        typ = ctx.cached(("abs_ro", nb, "o"), lambda: ctx.prev_sessions(np.abs(ro), "mean"))
        short = (ro >= k * typ) & (rw >= 0)
        long = (ro <= -k * typ) & (rw <= 0)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _boll_reentry(ctx, p):
    nb, k = ctx.bars(p["n_min"]), p["k"]
    m = ctx.roll(ctx.c, nb, "mean")
    s = ctx.roll(ctx.c, nb, "std")
    up, lo = m + k * s, m - k * s
    short = (ctx.prev(ctx.c, 1) > ctx.prev(up, 1)) & (ctx.c < up)
    long = (ctx.prev(ctx.c, 1) < ctx.prev(lo, 1)) & (ctx.c > lo)
    return _sgn(long, short)


def _vwap_sigma_fade(ctx, p):
    k = p["k"]
    vw = ctx.vwap()
    dev = ctx.c - vw
    g = pd.DataFrame({"d": ctx.day, "x": dev, "x2": dev * dev})
    cnt = g.groupby("d").cumcount().to_numpy() + 1.0
    s1 = g.groupby("d")["x"].cumsum().to_numpy()
    s2 = g.groupby("d")["x2"].cumsum().to_numpy()
    with np.errstate(all="ignore"):
        sd = np.sqrt(np.maximum(s2 / cnt - (s1 / cnt) ** 2, 0.0))
    sd = np.where(cnt >= ctx.bars(30), sd, np.nan)
    up, lo = vw + k * sd, vw - k * sd
    short = (ctx.prev(ctx.c, 1) > ctx.prev(up, 1)) & (ctx.c < up)
    long = (ctx.prev(ctx.c, 1) < ctx.prev(lo, 1)) & (ctx.c > lo)
    return _sgn(long, short)


def _donchian_mid(ctx, p):
    nb = ctx.bars(p["n_min"])
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    mid = (hi + lo) / 2
    return _sgn(ctx.cross(ctx.c > mid), ctx.cross(ctx.c < mid))


def _cmf_cross(ctx, p):
    nb, th = ctx.bars(p["n_min"]), p["th"]
    rng = ctx.h - ctx.l
    with np.errstate(all="ignore"):
        mfm = np.where(rng > 0, ((ctx.c - ctx.l) - (ctx.h - ctx.c)) / rng, 0.0)
        cmf = ctx.roll(mfm * ctx.v, nb, "sum") / ctx.roll(ctx.v, nb, "sum")
    return _sgn(ctx.cross(cmf > th), ctx.cross(cmf < -th))


def _autocorr_regime(ctx, p):
    nb, th, k = ctx.bars(p["n_min"]), p["th"], p["k"]
    r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    r1 = ctx.prev(r, 1)
    with np.errstate(all="ignore"):
        ac = ctx.roll(r * r1, nb, "mean") / ctx.roll(r * r, nb, "mean")
        big = np.abs(r) >= k * ctx.roll(np.abs(r), nb, "mean", include_current=False)
        s = np.sign(r)
        trend = big & (ac > th)
        mean_rev = big & (ac < -th)
        long = (trend & (s > 0)) | (mean_rev & (s < 0))
        short = (trend & (s < 0)) | (mean_rev & (s > 0))
    return _sgn(ctx.cross(long), ctx.cross(short))


def _ribbon(ctx, p):
    f = int(p["fast"])
    e1 = ctx.cached(("ema", f), lambda: ctx.ema(ctx.c, f))
    e2 = ctx.cached(("ema", int(f * 2.5)), lambda: ctx.ema(ctx.c, int(f * 2.5)))
    e3 = ctx.cached(("ema", int(f * 6)), lambda: ctx.ema(ctx.c, int(f * 6)))
    up = (ctx.c > e1) & (e1 > e2) & (e2 > e3)
    dn = (ctx.c < e1) & (e1 < e2) & (e2 < e3)
    return _sgn(ctx.cross(up), ctx.cross(dn))


def _compress_expand(ctx, p):
    ratio, k = p["ratio"], p["k"]
    rng = ctx.h - ctx.l
    short_atr = ctx.roll(rng, ctx.bars(5), "mean", include_current=False)
    long_atr = ctx.roll(rng, ctx.bars(30), "mean", include_current=False)
    with np.errstate(all="ignore"):
        squeezed = short_atr <= ratio * long_atr
        expand = rng >= k * long_atr
        body = ctx.c - ctx.o
        long = squeezed & expand & (body > 0) & (ctx.c >= ctx.h - 0.25 * rng)
        short = squeezed & expand & (body < 0) & (ctx.c <= ctx.l + 0.25 * rng)
    return _sgn(long, short)


def _session_mid_cross(ctx, p):
    th = p["th"]
    sh, sl = ctx.session_high(False), ctx.session_low(False)
    mid = (sh + sl) / 2
    wide = (sh - sl) / ctx.day_open >= th
    return _sgn(ctx.cross((ctx.c > mid) & wide), ctx.cross((ctx.c < mid) & wide))


def _ratio_z(ctx, p):
    nb, k = ctx.bars(p["n_min"]), p["k"]
    with np.errstate(all="ignore"):
        ratio = np.log(ctx.c) - np.log(ctx.other_close())
        m = ctx.roll(ratio, nb, "mean")
        s = ctx.roll(ratio, nb, "std")
        z = np.where(s > 0, (ratio - m) / s, np.nan)
    return _sgn(ctx.cross(z <= -k), ctx.cross(z >= k))


def _range_hold_dummy(ctx, p):  # placeholder kept unused
    return np.zeros(ctx.n, dtype=int)


FAMILIES = [
    Family("E-918", "Dollar leads index (inverse lag)",
           "WIN and WDO move inversely and the dollar futures often reprice first; when WDO moves unusually far over a "
           "short window while WIN has not yet moved against it, slower index participants catch up in the opposite direction.",
           {"win_min": [5, 10, 15], "k": [1.0, 1.5, 2.0]}, _dollar_lead, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-919", "Bollinger band re-entry fade",
           "A close outside a rolling 2-sigma band that closes back inside is an overshoot whose stop-driven buyers/sellers are exhausted; fade toward the mean.",
           {"n_min": [30, 60, 90], "k": [2.0, 2.5]}, _boll_reentry, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-920", "VWAP sigma-band re-entry fade",
           "Session VWAP with the session's own deviation band marks where intraday inventory is stretched; a close back inside the band after an excursion means the push is spent.",
           {"k": [1.5, 2.0, 2.5]}, _vwap_sigma_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-921", "Donchian midpoint cross",
           "The midpoint of the N-minute channel is the balance price; a close crossing it shows buyers or sellers taking control of the range.",
           {"n_min": [30, 60, 120]}, _donchian_mid, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-922", "Chaikin money flow threshold cross",
           "Volume-weighted close location over the window shows accumulation or distribution; crossing a threshold marks informed flow whose move should continue.",
           {"n_min": [30, 60], "th": [0.1, 0.2, 0.3]}, _cmf_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-923", "Autocorrelation-regime big-bar trade",
           "When recent bar returns are positively autocorrelated a large bar is followed, when negatively autocorrelated it is faded; the rolling regime selects the side.",
           {"n_min": [60, 120], "th": [0.1, 0.2], "k": [1.0, 1.5]}, _autocorr_regime, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-924", "Three-EMA ribbon alignment onset",
           "When price and three EMAs line up in order, short- and long-horizon traders agree on direction; the first bar of full alignment starts a leg.",
           {"fast": [5, 8, 12]}, _ribbon, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-925", "Compression then expansion bar",
           "After a few bars much quieter than the last 30 minutes, a wide bar closing at its extreme shows resting liquidity was consumed; follow the release.",
           {"ratio": [0.5, 0.7], "k": [1.5, 2.0]}, _compress_expand, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-926", "Wide-day session midpoint cross",
           "On days that have already ranged widely, the midpoint of the session range is the acceptance line; a close across it shows the day's control flipping.",
           {"th": [0.004, 0.006, 0.008]}, _session_mid_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-927", "Index-vs-dollar ratio mean reversion",
           "The log ratio of WIN to WDO is anchored by the common macro driver; a stretched ratio z-score means one leg overshot, and WIN tends to be the leg that reverts.",
           {"n_min": [60, 120], "k": [1.5, 2.0, 2.5]}, _ratio_z, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
