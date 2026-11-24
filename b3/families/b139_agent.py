"""Conveyor batch B-139 (agent, 2026-11-24). Mixed themes: gap, prior-day location, rolling VWAP, price-time trend, wicks, session midpoint, volume acceleration, skew, up-bar share, staircase lows/highs."""
from __future__ import annotations

import numpy as np
from b3.esteira import Family


def _sgn(ctx, long, short):
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _gap_fade(ctx, p):
    k, nb = p["gap_range_frac"], ctx.bars(p["window_min"])
    pc = ctx.prev_session_value("close")
    rng = ctx.prev_session_value("high") - ctx.prev_session_value("low")
    with np.errstate(invalid="ignore", divide="ignore"):
        g = (ctx.day_open - pc) / rng
    early = ctx.bar_in_day < nb
    pl, ph = ctx.prev(ctx.l, 1), ctx.prev(ctx.h, 1)
    short = early & (g >= k) & (ctx.c < ctx.o) & (ctx.c < pl) & (ctx.c > pc)
    long = early & (g <= -k) & (ctx.c > ctx.o) & (ctx.c > ph) & (ctx.c < pc)
    return _sgn(ctx, long, short)


def _prior_close_bias(ctx, p):
    thr, n = p["thr"], int(p["ema_bars"])
    pc = ctx.prev_session_value("close")
    pdh, pdl = ctx.prev_session_value("high"), ctx.prev_session_value("low")
    with np.errstate(invalid="ignore", divide="ignore"):
        pos = (pc - pdl) / (pdh - pdl)
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    early = ctx.bar_in_day < ctx.bars(180)
    long = early & (pos >= thr) & (ctx.c > ema)
    short = early & (pos <= 1 - thr) & (ctx.c < ema)
    return _sgn(ctx, long, short)


def _rolling_vwap(ctx, p):
    nb = ctx.bars(p["win_min"])
    pv = ctx.roll(ctx.c * ctx.v, nb, "sum")
    vv = ctx.roll(ctx.v, nb, "sum")
    with np.errstate(invalid="ignore", divide="ignore"):
        rv = pv / vv
    return _sgn(ctx, ctx.c > rv, ctx.c < rv)


def _price_time_corr(ctx, p):
    nb, thr = max(3, ctx.bars(p["win_min"])), p["thr"]
    x = ctx.bar_in_day.astype(float)
    mx = ctx.roll(x, nb, "mean")
    mc = ctx.roll(ctx.c, nb, "mean")
    mxc = ctx.roll(x * ctx.c, nb, "mean")
    sc = ctx.roll(ctx.c, nb, "std")
    sx = np.sqrt((nb * nb - 1) / 12.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        corr = (mxc - mx * mc) / (sx * sc)
    return _sgn(ctx, corr >= thr, corr <= -thr)


def _wick_pressure(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    lower = np.minimum(ctx.o, ctx.c) - ctx.l
    upper = ctx.h - np.maximum(ctx.o, ctx.c)
    rng = ctx.h - ctx.l
    with np.errstate(invalid="ignore", divide="ignore"):
        w = np.where(rng > 0, (lower - upper) / rng, 0.0)
    s = ctx.roll(w, nb, "mean")
    return _sgn(ctx, s >= k, s <= -k)


def _midpoint_recross(ctx, p):
    nb = ctx.bars(p["dwell_min"])
    mid = (ctx.session_high(True) + ctx.session_low(True)) / 2.0
    below = (ctx.c < mid).astype(float)
    above = (ctx.c > mid).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    return (was_below & (ctx.c > mid)).astype(int) - (was_above & (ctx.c < mid)).astype(int)


def _volume_acceleration(ctx, p):
    ns = ctx.bars(p["short_min"])
    nl = ns * 6
    k = p["k"]
    sv = ctx.roll(ctx.v, ns, "mean")
    lv = ctx.roll(ctx.v, nl, "mean")
    ret = ctx.c - ctx.prev(ctx.c, ns)
    hot = sv > k * lv
    return _sgn(ctx, hot & (ret > 0), hot & (ret < 0))


def _skew_rebound(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    m1 = ctx.roll(r, nb, "mean")
    m2 = ctx.roll(r * r, nb, "mean")
    m3 = ctx.roll(r * r * r, nb, "mean")
    var = m2 - m1 * m1
    with np.errstate(invalid="ignore", divide="ignore"):
        sk = np.where(var > 0, (m3 - 3 * m1 * m2 + 2 * m1 ** 3) / np.power(np.where(var > 0, var, 1.0), 1.5), np.nan)
    return _sgn(ctx, sk <= -k, sk >= k)


def _upbar_share(ctx, p):
    nb, thr = ctx.bars(p["win_min"]), p["thr"]
    share = ctx.roll((ctx.c > ctx.o).astype(float), nb, "mean")
    dn = ctx.roll((ctx.c < ctx.o).astype(float), nb, "mean")
    return _sgn(ctx, share >= thr, dn >= thr)


def _staircase(ctx, p):
    nb, f = ctx.bars(p["win_min"]), p["frac"]
    hl = (ctx.l > ctx.prev(ctx.l, 1)).astype(float)
    lh = (ctx.h < ctx.prev(ctx.h, 1)).astype(float)
    a = ctx.roll(hl, nb, "mean")
    b = ctx.roll(lh, nb, "mean")
    return _sgn(ctx, a >= f, b >= f)


FAMILIES = [
    Family("E-1388", "Opening gap fade on the first counter bar",
           "A session opening far from yesterday's close (relative to yesterday's range) is a thin-book jump; the first "
           "decisive bar back toward the prior close shows gap holders giving up, and the gap tends to be filled.",
           {"gap_range_frac": [0.15, 0.3, 0.5], "window_min": [30, 60, 90]}, _gap_fade,
           source="assistant reasoning", author="agent"),
    Family("E-1389", "Prior-close location bias entry",
           "When yesterday closed in the top (bottom) of its range, overnight holders carry that bias into the next "
           "session; a close back above (below) a short EMA in the first three hours is the entry in that direction.",
           {"thr": [0.7, 0.8, 0.9], "ema_bars": [10, 20, 30]}, _prior_close_bias, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1390", "Rolling-window VWAP cross follow",
           "A volume-weighted average over only the last n minutes is the recent average cost; a close across it shows "
           "the latest participants changing from underwater to profitable (or the reverse) and they follow.",
           {"win_min": [30, 60, 120]}, _rolling_vwap, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1391", "Price-time correlation trend follow",
           "Correlation between price and time near +1 means an orderly staircase advance that slow participants keep "
           "chasing; follow the first bar where it crosses the threshold.",
           {"win_min": [20, 30, 45], "thr": [0.8, 0.9]}, _price_time_corr, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1392", "Wick pressure accumulation follow",
           "Averaged over a window, long lower wicks and short upper wicks mean dips are repeatedly absorbed by "
           "resting buyers; trade with the absorbing side when the average crosses the threshold.",
           {"win_min": [10, 20, 30], "k": [0.2, 0.3, 0.4]}, _wick_pressure, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1393", "Session-range midpoint recross follow",
           "The middle of today's high-low range is the balance point of the day's auction; after price spent a while "
           "on one side, a close through it shows the other side taking control.",
           {"dwell_min": [10, 20, 30]}, _midpoint_recross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1394", "Volume acceleration direction follow",
           "Short-term average volume jumping well above the longer average shows urgent participation; the direction "
           "of price over that short window is the side that is urgent, and it keeps pushing.",
           {"short_min": [5, 10], "k": [1.5, 2.0, 3.0]}, _volume_acceleration, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1395", "Return-skew rebound",
           "Strongly negative skew in recent returns means a few big down bars among small up bars, a liquidation "
           "profile; sellers are forced, not informed, and the price rebounds (mirror for positive skew).",
           {"win_min": [30, 60], "k": [1.0, 1.5, 2.0]}, _skew_rebound, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1396", "Up-bar share breadth follow",
           "When most recent bars close above their open the tape shows steady small buyers lifting offers; a share "
           "crossing the threshold marks a persistent one-sided flow that continues.",
           {"win_min": [10, 20], "thr": [0.7, 0.8]}, _upbar_share, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1397", "Staircase higher-lows follow",
           "A window where most bars make a higher low (or lower high) shows dips bought a little higher each time; "
           "pullback buyers are stepping up and the stair continues.",
           {"win_min": [8, 12, 20], "frac": [0.7, 0.8, 0.9]}, _staircase, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
