"""Conveyor batch B-060 (agent, 2026-11-22). Mixed theme: moving-average / oscillator crosses, streak breaks, open recross, volatility-normalised drift, squeeze breaks, autocorrelation regime."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _ema_cross(ctx, p):
    f = int(p["fast"])
    s = int(round(f * p["ratio"]))
    fast = ctx.cached(("ema", f), lambda: ctx.ema(ctx.c, f))
    slow = ctx.cached(("ema", s), lambda: ctx.ema(ctx.c, s))
    ok = ~np.isnan(slow) & ~np.isnan(fast)
    up = ctx.cross(ok & (fast > slow))
    dn = ctx.cross(ok & (fast < slow))
    return up.astype(int) - dn.astype(int)


def _streak_break(ctx, p):
    n = int(p["n"])
    lh = (ctx.h < ctx.prev(ctx.h, 1)).astype(float)
    hl = (ctx.l > ctx.prev(ctx.l, 1)).astype(float)
    s_lh = ctx.roll(lh, n, "min")
    s_hl = ctx.roll(hl, n, "min")
    long = (ctx.prev(s_lh, 1) == 1) & (ctx.c > ctx.prev(ctx.h, 1))
    short = (ctx.prev(s_hl, 1) == 1) & (ctx.c < ctx.prev(ctx.l, 1))
    return long.astype(int) - short.astype(int)


def _open_recross(ctx, p):
    k = p["k"]
    do = ctx.day_open
    slo = ctx.session_low(include_current=False)
    shi = ctx.session_high(include_current=False)
    long = ctx.cross(ctx.c > do) & (slo <= do * (1 - k))
    short = ctx.cross(ctx.c < do) & (shi >= do * (1 + k))
    return long.astype(int) - short.astype(int)


def _extreme_count(ctx, p):
    nb = ctx.bars(p["win_min"])
    th = p["frac"]
    hh = (ctx.h > ctx.prev(ctx.h, 1)).astype(float)
    ll = (ctx.l < ctx.prev(ctx.l, 1)).astype(float)
    score = ctx.roll(hh - ll, nb, "sum")
    up = ctx.cross(score >= th * nb)
    dn = ctx.cross(score <= -th * nb)
    return up.astype(int) - dn.astype(int)


def _boll_reentry(ctx, p):
    n, k = int(p["n"]), p["k"]
    m = ctx.roll(ctx.c, n, "mean")
    sd = ctx.roll(ctx.c, n, "std")
    up, lo = m + k * sd, m - k * sd
    short = (ctx.prev(ctx.c, 1) > ctx.prev(up, 1)) & (ctx.c < up)
    long = (ctx.prev(ctx.c, 1) < ctx.prev(lo, 1)) & (ctx.c > lo)
    return long.astype(int) - short.astype(int)


def _autocorr_regime(ctx, p):
    n, th = int(p["n"]), p["th"]
    nb = ctx.bars(n)
    nb = max(nb, 8)
    ret = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    pr = ctx.prev(ret, 1)
    with np.errstate(all="ignore"):
        cov = ctx.roll(ret * pr, nb, "mean") - ctx.roll(ret, nb, "mean") * ctx.roll(pr, nb, "mean")
        corr = cov / (ctx.roll(ret, nb, "std") * ctx.roll(pr, nb, "std"))
        big = np.abs(ret) > 1.5 * ctx.roll(np.abs(ret), nb, "mean", include_current=False)
        long = big & (((corr < -th) & (ret < 0)) | ((corr > th) & (ret > 0)))
        short = big & (((corr < -th) & (ret > 0)) | ((corr > th) & (ret < 0)))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _drift_tstat(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    ret = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    with np.errstate(all="ignore"):
        tot = ctx.roll(ret, nb, "sum")
        sd = ctx.roll(ret, nb, "std")
        z = tot / (sd * np.sqrt(nb))
    return ctx.cross(z >= th).astype(int) - ctx.cross(z <= -th).astype(int)


def _rsi_mid(ctx, p):
    n, d = int(p["n"]), p["d"]
    r = ctx.rsi(n)
    up = ctx.cross(r > 50 + d)
    dn = ctx.cross(r < 50 - d)
    return up.astype(int) - dn.astype(int)


def _squeeze_break(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    hi = ctx.roll(ctx.c, nb, "max", include_current=False)
    lo = ctx.roll(ctx.c, nb, "min", include_current=False)
    hi_l = ctx.roll(ctx.c, 4 * nb, "max", include_current=False)
    lo_l = ctx.roll(ctx.c, 4 * nb, "min", include_current=False)
    with np.errstate(all="ignore"):
        narrow = (hi - lo) < k * (hi_l - lo_l)
    long = narrow & (ctx.c > hi)
    short = narrow & (ctx.c < lo)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _trix_cross(ctx, p):
    s = int(p["span"])
    e1 = ctx.ema(ctx.c, s)
    e2 = ctx.ema(e1, s)
    e3 = ctx.ema(e2, s)
    with np.errstate(all="ignore"):
        trix = e3 / ctx.prev(e3, 1) - 1.0
    ok = ~np.isnan(trix)
    return ctx.cross(ok & (trix > 0)).astype(int) - ctx.cross(ok & (trix < 0)).astype(int)


def _gap_fill_dummy(ctx, p):
    return np.zeros(ctx.n, dtype=int)


def _hl_balance(ctx, p):
    """Close-vs-open of the whole N-bar window plus last-bar confirmation: window body sum aligned with a bar that
    closes beyond the previous bar's midpoint after a counter bar."""
    nb = ctx.bars(p["win_min"])
    body = ctx.c - ctx.o
    net = ctx.roll(body, nb, "sum")
    rng = ctx.roll(ctx.h - ctx.l, nb, "mean")
    with np.errstate(all="ignore"):
        trend_up = net > p["k"] * rng * np.sqrt(nb)
        trend_dn = net < -p["k"] * rng * np.sqrt(nb)
    pmid = (ctx.prev(ctx.h, 1) + ctx.prev(ctx.l, 1)) / 2
    counter_up = ctx.prev(ctx.c, 1) < ctx.prev(ctx.o, 1)
    counter_dn = ctx.prev(ctx.c, 1) > ctx.prev(ctx.o, 1)
    long = trend_up & counter_up & (ctx.c > pmid) & (ctx.c > ctx.o)
    short = trend_dn & counter_dn & (ctx.c < pmid) & (ctx.c < ctx.o)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-598", "Dual-EMA cross follow",
           "A fast EMA crossing a slower one inside the session marks the point where recent buyers or sellers "
           "outweigh the earlier ones; late counter-traders get stopped and the move extends.",
           {"fast": [5, 9, 13], "ratio": [2, 3]}, _ema_cross,
           source="assistant reasoning", author="agent"),
    Family("E-599", "Lower-high streak break",
           "After several consecutive lower highs sellers are leaning on every rally; the first close above the last "
           "high squeezes them (mirror for higher lows).",
           {"n": [3, 4, 5]}, _streak_break, source="assistant reasoning", author="agent"),
    Family("E-600", "Day-open recross after an excursion",
           "After trading away from the day's open the price closes back through it: the open drive failed and the "
           "other side owns the session; follow the recross.",
           {"k": [0.001, 0.002, 0.003]}, _open_recross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-601", "New-extreme count pressure",
           "When most recent bars keep making higher highs rather than lower lows, participation is one-sided; "
           "follow the crossing of that count.",
           {"win_min": [15, 30, 45], "frac": [0.3, 0.5]}, _extreme_count, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-602", "Bollinger re-entry fade",
           "A close outside the Bollinger band followed by a close back inside shows the stretch was rejected; "
           "chasers are trapped and the price reverts toward the mean.",
           {"n": [20, 30, 40], "k": [2.0, 2.5]}, _boll_reentry, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-603", "Autocorrelation-regime bar trade",
           "When consecutive returns have recently been negatively correlated, a big bar overshoots and is faded; "
           "when positively correlated, it is followed.",
           {"n": [30, 60], "th": [0.1, 0.2]}, _autocorr_regime, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-604", "Volatility-normalised drift follow",
           "A window return large relative to its own noise (t-stat of drift) reflects persistent one-way order "
           "flow rather than random jitter; follow when it first crosses.",
           {"win_min": [10, 20, 30], "th": [1.5, 2.0, 2.5]}, _drift_tstat, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-605", "RSI midline cross follow",
           "RSI crossing 50 (with an optional dead band) shows average gains overtaking average losses; "
           "momentum traders pile in.",
           {"n": [7, 14, 21], "d": [0, 5]}, _rsi_mid, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-606", "Close-range squeeze break",
           "When the closing-price range of the last window is much narrower than that of four windows, "
           "the market is coiled; a close outside it releases stop and breakout orders.",
           {"win_min": [15, 30], "k": [0.4, 0.6]}, _squeeze_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-607", "TRIX zero-cross follow",
           "The slope of a triple-smoothed EMA changing sign filters noise and signals a durable change in "
           "direction; follow it.",
           {"span": [5, 9, 14]}, _trix_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
