"""Conveyor batch B-135 (agent, 2026-11-24). Regime-conditioned fades, key reversals, regression trend and
persistence ideas on WIN, steered away from plain level/VWAP/z-score themes already screened."""
from __future__ import annotations

import numpy as np
from b3.esteira import Family


def _out(long, short):
    return np.asarray(long, bool).astype(int) - np.asarray(short, bool).astype(int)


def _autocorr_fade(ctx, p):
    nb = ctx.bars(p["win_min"])
    th = p["th"]
    r = ctx.c - ctx.prev(ctx.c, 1)
    r1 = ctx.prev(r, 1)
    num = ctx.roll(r * r1, nb, "mean")
    den = ctx.roll(r * r, nb, "mean")
    sd = np.sqrt(den)
    with np.errstate(divide="ignore", invalid="ignore"):
        ac = num / den
    reg = ac < -th
    big = np.abs(r) > sd
    long = reg & big & (r < 0)
    short = reg & big & (r > 0)
    return _out(ctx.cross(long), ctx.cross(short))


def _key_reversal(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    long = (ctx.l < lo) & (ctx.c > ctx.prev(ctx.h, 1))
    short = (ctx.h > hi) & (ctx.c < ctx.prev(ctx.l, 1))
    return _out(long, short)


def _rsi_chop_recross(ctx, p):
    th = p["th"]
    nb = ctx.bars(30)
    rsi = ctx.rsi(14)
    d = np.abs(ctx.c - ctx.prev(ctx.c, 1))
    path = ctx.roll(d, nb, "sum")
    with np.errstate(divide="ignore", invalid="ignore"):
        er = np.abs(ctx.c - ctx.prev(ctx.c, nb)) / path
    chop = er < p["er_max"]
    pr = ctx.prev(rsi, 1)
    long = chop & (pr < th) & (rsi >= th)
    short = chop & (pr > 100 - th) & (rsi <= 100 - th)
    return _out(long, short)


def _reg_tstat(ctx, p):
    nb = ctx.bars(p["win_min"])
    if nb < 5:
        return np.zeros(ctx.n, int)
    y = ctx.c / ctx.day_open - 1.0
    x = ctx.bar_in_day.astype(float)
    sy = ctx.roll(y, nb, "sum")
    sxy = ctx.roll(x * y, nb, "sum")
    syy = ctx.roll(y * y, nb, "sum")
    sxx = nb * (nb * nb - 1) / 12.0
    xbar = x - (nb - 1) / 2.0
    slope = (sxy - xbar * sy) / sxx
    rss = (syy - sy * sy / nb) - slope * slope * sxx
    with np.errstate(divide="ignore", invalid="ignore"):
        t = slope * np.sqrt(sxx) / np.sqrt(np.where(rss > 1e-14, rss, np.nan) / (nb - 2))
    return _out(ctx.cross(t > p["th"]), ctx.cross(t < -p["th"]))


def _climax_nofollow(ctx, p):
    k = p["k"]
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    v1, o1, c1 = ctx.prev(ctx.v, 1), ctx.prev(ctx.o, 1), ctx.prev(ctx.c, 1)
    m1 = ctx.prev(med, 1)
    big = v1 > k * m1
    short = big & (c1 > o1) & (ctx.c < c1) & (ctx.c < ctx.o)
    long = big & (c1 < o1) & (ctx.c > c1) & (ctx.c > ctx.o)
    return _out(long, short)


def _walk_band(ctx, p):
    nb = ctx.bars(p["win_min"])
    m = ctx.bars(p["hold_min"])
    hi = ctx.roll(ctx.h, nb, "max")
    lo = ctx.roll(ctx.l, nb, "min")
    rng = hi - lo
    with np.errstate(divide="ignore", invalid="ignore"):
        pos = (ctx.c - lo) / rng
    top = (pos >= 0.8).astype(float)
    bot = (pos <= 0.2).astype(float)
    top[np.isnan(pos)] = 0.0
    bot[np.isnan(pos)] = 0.0
    up = ctx.roll(top, m, "min") == 1
    dn = ctx.roll(bot, m, "min") == 1
    return _out(ctx.cross(up), ctx.cross(dn))


def _ema_turn(ctx, p):
    span = ctx.bars(p["ema_min"])
    m = ctx.bars(p["run_min"])
    ema = ctx.cached(("ema", span), lambda: ctx.ema(ctx.c, span))
    s = ema - ctx.prev(ema, 1)
    dn = (s < 0).astype(float)
    up = (s > 0).astype(float)
    was_dn = ctx.roll(dn, m, "min", include_current=False) == 1
    was_up = ctx.roll(up, m, "min", include_current=False) == 1
    return _out(was_dn & (s > 0), was_up & (s < 0))


def _ha_flip(ctx, p):
    m = int(p["m"])
    hac = (ctx.o + ctx.h + ctx.l + ctx.c) / 4.0
    hao = (ctx.prev(ctx.o, 1) + ctx.prev(ctx.c, 1)) / 2.0
    green = (hac > hao).astype(float)
    red = (hac < hao).astype(float)
    green[np.isnan(hao)] = 0.0
    red[np.isnan(hao)] = 0.0
    was_red = ctx.roll(red, m, "min", include_current=False) == 1
    was_green = ctx.roll(green, m, "min", include_current=False) == 1
    return _out(was_red & (green == 1), was_green & (red == 1))


def _body_eff_fade(ctx, p):
    nb = ctx.bars(p["win_min"])
    body = ctx.roll(ctx.c - ctx.o, nb, "sum")
    rng = ctx.roll(ctx.h - ctx.l, nb, "sum")
    with np.errstate(divide="ignore", invalid="ignore"):
        be = body / rng
    th = p["th"]
    return _out(ctx.cross(be < -th), ctx.cross(be > th))


def _gap_close_bounce(ctx, p):
    # bar opens beyond the previous bar's extreme by k typical ranges and closes back toward it: fade the gap
    k = p["k"]
    rng = ctx.h - ctx.l
    typ = ctx.roll(rng, ctx.bars(p["win_min"]), "mean", include_current=False)
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    up_gap = (ctx.o > h1 + k * typ) & (ctx.c < ctx.o)
    dn_gap = (ctx.o < l1 - k * typ) & (ctx.c > ctx.o)
    return _out(dn_gap, up_gap)


FAMILIES = [
    Family("E-1348", "Negative-autocorrelation regime bounce",
           "When recent bar-to-bar changes alternate in sign (negative lag-1 autocorrelation), liquidity providers "
           "are being paid for bouncing; a bar larger than the recent std is likely to partly reverse.",
           {"win_min": [30, 60, 90], "th": [0.1, 0.2, 0.3]}, _autocorr_fade,
           source="assistant reasoning", author="agent", markets=("WIN",)),
    Family("E-1349", "Key reversal bar at a lookback extreme",
           "A bar that sweeps the N-bar low (high) and closes above the previous bar's high (below its low) shows "
           "stops were run and absorbed; follow the reversal.",
           {"lookback_min": [10, 20, 30, 60]}, _key_reversal,
           source="assistant reasoning", author="agent", markets=("WIN",)),
    Family("E-1350", "RSI(14) recross in a choppy tape",
           "In a low-efficiency (choppy) tape an RSI exit from an extreme marks the end of an overshoot; "
           "trade the return toward the middle.",
           {"th": [20, 25, 30], "er_max": [0.2, 0.3]}, _rsi_chop_recross,
           source="assistant reasoning", author="agent", markets=("WIN",)),
    Family("E-1351", "Regression-slope t-stat trend start",
           "A statistically significant slope of the intraday path (t-stat crossing a threshold) separates a "
           "persistent one-sided flow from noise; follow it as institutional execution continues.",
           {"win_min": [30, 60], "th": [4, 6, 8]}, _reg_tstat,
           source="assistant reasoning", author="agent", markets=("WIN",)),
    Family("E-1352", "Volume climax without follow-through",
           "A high-volume directional bar followed by a bar that closes back against it marks exhausted "
           "aggressors; fade the climax.",
           {"k": [1.5, 2.0, 3.0]}, _climax_nofollow,
           source="volume-price analysis (climax bars)", author="agent", markets=("WIN",)),
    Family("E-1353", "Walking the rolling band",
           "Staying in the top (bottom) fifth of the rolling range for several consecutive bars shows persistent "
           "one-sided demand; follow the start of the walk.",
           {"win_min": [30, 60], "hold_min": [10, 20]}, _walk_band,
           source="assistant reasoning", author="agent", markets=("WIN",)),
    Family("E-1354", "Smoothed-price turn after a run",
           "After the EMA has fallen (risen) for several bars, its first upward (downward) tick shows selling "
           "pressure has stopped; trade the turn.",
           {"ema_min": [10, 20, 30], "run_min": [5, 10]}, _ema_turn,
           source="assistant reasoning", author="agent", markets=("WIN",)),
    Family("E-1355", "Heikin-Ashi colour flip after a run",
           "A Heikin-Ashi candle that changes colour after a run of the opposite colour filters noise and marks a "
           "change of the dominant side.",
           {"m": [3, 4, 5]}, _ha_flip,
           source="Heikin-Ashi charting practice (assistant reasoning)", author="agent", markets=("WIN",)),
    Family("E-1356", "Body-efficiency exhaustion fade",
           "When nearly all of the recent range is captured by same-direction candle bodies, the move is "
           "one-sided and stretched; fade the first time the efficiency crosses the threshold.",
           {"win_min": [15, 30, 60], "th": [0.4, 0.5, 0.6]}, _body_eff_fade,
           source="assistant reasoning", author="agent", markets=("WIN",)),
    Family("E-1357", "Bar-open gap rejection",
           "A bar that opens beyond the previous bar's extreme by a multiple of the typical range and closes back "
           "inside its own open direction shows the gap was an overreaction by market orders; fade it.",
           {"k": [0.25, 0.5, 1.0], "win_min": [30, 60]}, _gap_close_bounce,
           source="assistant reasoning", author="agent", markets=("WIN",)),
]
