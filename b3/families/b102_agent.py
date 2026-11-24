"""Conveyor batch B-102 (agent, 2026-11-24). Mixed themes: band fade, open recross, bar-colour share, lead-lag, session-window volume, rolling VWAP, autocorrelation regime, streak failure, EMA fan, volatility expansion."""
from __future__ import annotations

import numpy as np

from b3.esteira import Family


def _d(long, short):
    return long.astype(int) - short.astype(int)


def _zband_fade(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    m = ctx.roll(ctx.c, n, "mean")
    s = ctx.roll(ctx.c, n, "std")
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.where(s > 0, (ctx.c - m) / s, 0.0)
    z = np.nan_to_num(z)
    return _d(ctx.cross(z < -k), ctx.cross(z > k))


def _open_recross(ctx, p):
    nb = ctx.bars(p["away_min"])
    below = (ctx.c < ctx.day_open).astype(float)
    above = (ctx.c > ctx.day_open).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    up = was_below & (ctx.c > ctx.day_open)
    dn = was_above & (ctx.c < ctx.day_open)
    return _d(up, dn)


def _colour_share_fade(ctx, p):
    nb, q = ctx.bars(p["win_min"]), p["q"]
    up = ctx.roll((ctx.c > ctx.o).astype(float), nb, "mean")
    dn = ctx.roll((ctx.c < ctx.o).astype(float), nb, "mean")
    return _d(ctx.cross(dn >= q), ctx.cross(up >= q))


def _win_leads_dollar(ctx, p):
    nb, k = ctx.bars(p["move_min"]), p["k"]
    oc = ctx.other_close()
    rw = oc / ctx.prev(oc, nb) - 1.0
    rd = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    tw = ctx.cached(("tw", nb), lambda: ctx.prev_sessions(np.nan_to_num(np.abs(rw)), "mean"))
    td = ctx.cached(("td", nb), lambda: ctx.prev_sessions(np.nan_to_num(np.abs(rd)), "mean"))
    with np.errstate(divide="ignore", invalid="ignore"):
        zw = np.where(tw > 0, rw / tw, np.nan)
        zd = np.where(td > 0, rd / td, np.nan)
    short = (zw >= k) & (zd >= 0)      # index up but dollar did not fall: dollar should drop
    long = (zw <= -k) & (zd <= 0)
    return _d(ctx.cross(long), ctx.cross(short))


def _us_open_surge(ctx, p):
    k, q = p["vol_k"], p["close_loc"]
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    rng = ctx.h - ctx.l
    with np.errstate(divide="ignore", invalid="ignore"):
        loc = np.where(rng > 0, (ctx.c - ctx.l) / rng, 0.5)
    win = (ctx.minute >= 10 * 60 + 25) & (ctx.minute < 12 * 60)
    surge = win & (ctx.v >= k * med)
    long = surge & (loc >= q) & (ctx.c > ctx.o)
    short = surge & (loc <= 1 - q) & (ctx.c < ctx.o)
    return _d(ctx.cross(long), ctx.cross(short))


def _rolling_vwap_cross(ctx, p):
    n = ctx.bars(p["win_min"])
    pv = ctx.roll(ctx.c * ctx.v, n, "sum") / ctx.roll(ctx.v, n, "sum")
    sv = ctx.vwap()
    long = (ctx.c > pv) & (ctx.c > sv)
    short = (ctx.c < pv) & (ctx.c < sv)
    return _d(ctx.cross(long), ctx.cross(short))


def _autocorr_regime(ctx, p):
    n, th = ctx.bars(p["win_min"]), p["th"]
    r = np.nan_to_num(ctx.c / ctx.prev(ctx.c, 1) - 1.0)
    r1 = np.nan_to_num(ctx.prev(r, 1))
    num = ctx.roll(r * r1, n, "mean")
    den = ctx.roll(r * r, n, "mean")
    mabs = ctx.roll(np.abs(r), n, "mean")
    with np.errstate(divide="ignore", invalid="ignore"):
        ac = np.where(den > 0, num / den, 0.0)
    ac = np.nan_to_num(ac)
    big = np.abs(r) > mabs
    long = big & (((ac > th) & (r > 0)) | ((ac < -th) & (r < 0)))
    short = big & (((ac > th) & (r < 0)) | ((ac < -th) & (r > 0)))
    return _d(long, short)


def _streak_failure(ctx, p):
    n = int(p["streak"])
    ph, pl = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    hh = (ctx.h > ph).astype(float)
    ll = (ctx.l < pl).astype(float)
    run_up = ctx.roll(hh, n, "min", include_current=False) == 1
    run_dn = ctx.roll(ll, n, "min", include_current=False) == 1
    short = run_up & (ctx.h <= ph) & (ctx.c < pl)
    long = run_dn & (ctx.l >= pl) & (ctx.c > ph)
    return _d(long, short)


def _ema_fan(ctx, p):
    b = p["base_min"]
    s1, s2, s3 = ctx.bars(b), ctx.bars(2 * b), ctx.bars(4 * b)
    e1 = ctx.cached(("ema", s1), lambda: ctx.ema(ctx.c, s1))
    e2 = ctx.cached(("ema", s2), lambda: ctx.ema(ctx.c, s2))
    e3 = ctx.cached(("ema", s3), lambda: ctx.ema(ctx.c, s3))
    up = (e1 > e2) & (e2 > e3) & (ctx.c > e1)
    dn = (e1 < e2) & (e2 < e3) & (ctx.c < e1)
    return _d(ctx.cross(up), ctx.cross(dn))


def _vol_expansion(ctx, p):
    k, nb = p["k"], ctx.bars(p["base_min"])
    tr = ctx.h - ctx.l
    s3 = ctx.roll(tr, 3, "mean")
    base = ctx.prev(ctx.roll(tr, nb, "mean"), 3)
    net = ctx.c - ctx.prev(ctx.c, 3)
    exp = s3 > k * base
    return _d(ctx.cross(exp & (net > 0)), ctx.cross(exp & (net < 0)))


FAMILIES = [
    Family("E-1018", "Rolling z-score band fade",
           "A close more than k standard deviations from its own rolling mean is a stretched, mostly liquidity-driven move; "
           "the other side is momentum chasers who get faded back toward the mean.",
           {"win_min": [30, 60], "k": [2.0, 2.5, 3.0]}, _zband_fade, source="assistant reasoning", author="agent"),
    Family("E-1019", "Session-open recross follow",
           "After trading on one side of the session open price for a while, a close back through it flips the day's "
           "winners and losers: those holding the old side must cover, so follow the cross.",
           {"away_min": [30, 60, 90]}, _open_recross, source="assistant reasoning", author="agent"),
    Family("E-1020", "Bar-colour share exhaustion fade",
           "When most bars of a window share one colour the move is crowded; buyers or sellers are spent and "
           "the first cross of the share threshold marks a fade point.",
           {"win_min": [30, 45, 60], "q": [0.7, 0.8]}, _colour_share_fade, source="assistant reasoning", author="agent"),
    Family("E-1021", "Index leads the dollar",
           "The index and the dollar are negatively related; when the index moves strongly and the dollar has not "
           "yet reacted, slower dollar participants catch up in the opposite direction.",
           {"move_min": [10, 20, 30], "k": [1.0, 1.5, 2.0]}, _win_leads_dollar, markets=("WDO",),
           source="assistant reasoning", author="agent"),
    Family("E-1022", "US-open volume surge follow",
           "Around the US cash open a heavy-volume bar closing near its extreme shows large institutional flow "
           "arriving; slower participants chase in its direction.",
           {"vol_k": [2.0, 3.0, 4.0], "close_loc": [0.6, 0.7, 0.8]}, _us_open_surge, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1023", "Rolling VWAP and session VWAP agreement",
           "A close crossing above both the short-window volume-weighted price and the session VWAP means recent and "
           "day-long buyers are in profit together; follow the alignment.",
           {"win_min": [15, 30, 60]}, _rolling_vwap_cross, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1024", "Autocorrelation regime bar trade",
           "Return autocorrelation shifts between trending and mean-reverting tapes; when the recent lag-1 "
           "autocorrelation is positive follow large bars, when negative fade them.",
           {"win_min": [60, 120], "th": [0.1, 0.2, 0.3]}, _autocorr_regime, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1025", "Higher-high streak failure",
           "After a streak of consecutive higher highs, a bar that fails to extend and closes below the prior low "
           "shows late buyers trapped; trade the reversal.",
           {"streak": [2, 3, 4]}, _streak_failure, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1026", "EMA fan alignment onset",
           "When three EMAs line up in order with the close beyond the fastest, a trend has just become orderly; "
           "trend followers join as the alignment forms.",
           {"base_min": [5, 10, 15]}, _ema_fan, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1027", "Volatility expansion direction follow",
           "When the last three bars' average range jumps well above the recent base, new information is "
           "being priced; the net direction of those bars tends to continue.",
           {"k": [1.5, 2.0, 2.5], "base_min": [60, 120]}, _vol_expansion, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
