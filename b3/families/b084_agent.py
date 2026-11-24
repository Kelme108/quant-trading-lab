"""Conveyor batch B-084 (agent, 2026-11-23). Mixed: round numbers, day-open, efficiency ratio, volume, oscillators."""
from __future__ import annotations

import numpy as np
from b3.esteira import Family


def _i(long, short):
    return np.asarray(long).astype(int) - np.asarray(short).astype(int)


def _round_number(ctx, p):
    k = p["step_frac"]
    mag = 10.0 ** np.floor(np.log10(np.maximum(ctx.c, 1.0)))
    step = mag * k
    lvl = np.round(ctx.c / step) * step
    short = (ctx.o < lvl) & (ctx.h >= lvl) & (ctx.c < lvl)
    long = (ctx.o > lvl) & (ctx.l <= lvl) & (ctx.c > lvl)
    return _i(long, short)


def _dayopen_reclaim(ctx, p):
    nb = ctx.bars(p["away_min"])
    do = ctx.day_open
    below = (ctx.c < do).astype(float)
    above = (ctx.c > do).astype(float)
    wb = ctx.roll(below, nb, "min", include_current=False) == 1
    wa = ctx.roll(above, nb, "min", include_current=False) == 1
    return _i(wb & (ctx.c > do), wa & (ctx.c < do))


def _eff_ratio(ctx, p):
    nb = ctx.bars(p["win_min"])
    th = p["th"]
    d = np.abs(ctx.c - ctx.prev(ctx.c, 1))
    path = ctx.roll(d, nb, "sum")
    net = ctx.c - ctx.prev(ctx.c, nb)
    er = np.abs(net) / np.where(path > 0, path, np.nan)
    fire = ctx.cross(er > th)
    return np.where(fire, np.sign(net), 0).astype(int)


def _volume_staircase(ctx, p):
    n = int(p["n"])
    up = np.ones(ctx.n, bool)
    dn = np.ones(ctx.n, bool)
    for i in range(n):
        c0, c1 = ctx.prev(ctx.c, i), ctx.prev(ctx.c, i + 1)
        v0, v1 = ctx.prev(ctx.v, i), ctx.prev(ctx.v, i + 1)
        up &= (c0 > c1) & (v0 > v1)
        dn &= (c0 < c1) & (v0 > v1)
    return _i(ctx.cross(up), ctx.cross(dn))


def _ha_flip(ctx, p):
    n = int(p["run"])
    hac = (ctx.o + ctx.h + ctx.l + ctx.c) / 4.0
    hao = (ctx.prev(ctx.o, 1) + ctx.prev(ctx.c, 1)) / 2.0
    up = (hac > hao).astype(float)
    dn = (hac < hao).astype(float)
    was_dn = ctx.roll(dn, n, "min", include_current=False) == 1
    was_up = ctx.roll(up, n, "min", include_current=False) == 1
    return _i(was_dn & (up == 1), was_up & (dn == 1))


def _stoch_turn(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    hh = ctx.roll(ctx.h, nb, "max")
    ll = ctx.roll(ctx.l, nb, "min")
    k = (ctx.c - ll) / np.where(hh > ll, hh - ll, np.nan)
    return _i(ctx.cross(k > th), ctx.cross(k < 1 - th))


def _vwap_slope_flip(ctx, p):
    nb = ctx.bars(p["win_min"])
    vw = ctx.vwap()
    s = vw - ctx.prev(vw, nb)
    return _i(ctx.cross((s > 0) & (ctx.c > vw)), ctx.cross((s < 0) & (ctx.c < vw)))


def _zscore_fade(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    m = ctx.roll(ctx.c, nb, "mean")
    sd = ctx.roll(ctx.c, nb, "std")
    z = (ctx.c - m) / np.where(sd > 0, sd, np.nan)
    return _i(ctx.cross(z < -th), ctx.cross(z > th))


def _ema_cross_vwap(ctx, p):
    f = int(p["fast"])
    s = 3 * f
    ef = ctx.cached(("ema", f), lambda: ctx.ema(ctx.c, f))
    es = ctx.cached(("ema", s), lambda: ctx.ema(ctx.c, s))
    vw = ctx.vwap()
    return _i(ctx.cross((ef > es) & (ctx.c > vw)), ctx.cross((ef < es) & (ctx.c < vw)))


def _climax_reversal(ctx, p):
    k, m = p["k"], int(p["m"])
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    heavy = ctx.v > k * med
    move = ctx.prev(ctx.c, 1) - ctx.prev(ctx.c, 1 + m)
    long = heavy & (move < 0) & (ctx.c > ctx.o) & (ctx.c > ctx.prev(ctx.h, 1))
    short = heavy & (move > 0) & (ctx.c < ctx.o) & (ctx.c < ctx.prev(ctx.l, 1))
    return _i(long, short)


FAMILIES = [
    Family("E-838", "Round-number touch rejection",
           "Resting orders cluster at round index/dollar levels; a bar that touches the nearest round level and closes back "
           "on the side it opened from means the level held, so trade away from it.",
           {"step_frac": [0.005, 0.01, 0.025]}, _round_number, source="assistant reasoning", author="agent"),
    Family("E-839", "Day-open reclaim follow",
           "After trading on one side of the session open for a while, a close back across it shifts the intraday "
           "average holder into profit/loss and the move follows.",
           {"away_min": [15, 30, 60]}, _dayopen_reclaim, source="assistant reasoning", author="agent"),
    Family("E-840", "Efficiency-ratio ignition follow",
           "When Kaufman's efficiency ratio jumps above a threshold the tape moves in one direction with little noise; "
           "slower participants chase and the move continues.",
           {"win_min": [20, 30, 60], "th": [0.5, 0.6, 0.7]}, _eff_ratio, source="assistant reasoning", author="agent"),
    Family("E-841", "Volume-confirmed staircase follow",
           "Consecutive closes in one direction each on rising volume show growing participation behind the move; follow it.",
           {"n": [2, 3, 4]}, _volume_staircase, source="assistant reasoning", author="agent"),
    Family("E-842", "Heikin-Ashi colour flip after a run",
           "A flip of smoothed candle colour after a run of the opposite colour marks a change of short-term control.",
           {"run": [3, 4, 5]}, _ha_flip, source="assistant reasoning", author="agent"),
    Family("E-843", "Stochastic extreme exit follow",
           "When the close leaves the bottom (top) zone of the recent range, sellers (buyers) are exhausted; trade the "
           "bounce away from the extreme.",
           {"win_min": [30, 60, 90], "th": [0.1, 0.2]}, _stoch_turn, source="assistant reasoning", author="agent"),
    Family("E-844", "VWAP slope flip with side agreement",
           "When the session VWAP changes slope and price sits on the same side, the average trade price is trending "
           "that way and money-flow follows.",
           {"win_min": [10, 20, 30]}, _vwap_slope_flip, source="assistant reasoning", author="agent"),
    Family("E-845", "Rolling z-score stretch fade",
           "Price stretched more than a few standard deviations from its recent mean is typically a liquidity-driven "
           "overshoot by impatient flow; fade it back.",
           {"win_min": [30, 60, 90], "th": [2.0, 2.5]}, _zscore_fade, source="assistant reasoning", author="agent"),
    Family("E-846", "EMA cross with VWAP agreement",
           "A fast/slow EMA cross while price is on the matching side of VWAP combines momentum and position vs average "
           "cost; follow the cross.",
           {"fast": [5, 9, 13]}, _ema_cross_vwap, source="assistant reasoning", author="agent"),
    Family("E-847", "Heavy-volume climax reversal bar",
           "A very heavy bar that engulfs the previous bar against a prior move is capitulation of the trapped side; "
           "follow the reversal bar.",
           {"k": [1.5, 2.0, 3.0], "m": [3, 5, 8]}, _climax_reversal, source="assistant reasoning", author="agent"),
]
