"""Conveyor batch B-123 (agent, 2026-11-24). Oscillator/flow-indicator state changes, trailing-band flips and
level-dwell ideas, each firing on a change of state so one setup gives one signal."""
from __future__ import annotations

import math

import numpy as np

from b3.esteira import Family


def _sgn(long, short):
    return np.asarray(long, bool).astype(int) - np.asarray(short, bool).astype(int)


def _cmf_cross(ctx, p):
    nb, th = ctx.bars(p["win_min"]), p["th"]
    rng = ctx.h - ctx.l
    with np.errstate(divide="ignore", invalid="ignore"):
        clv = np.where(rng > 0, ((ctx.c - ctx.l) - (ctx.h - ctx.c)) / rng, 0.0)
    sv = ctx.roll(ctx.v, nb, "sum")
    smf = ctx.roll(clv * ctx.v, nb, "sum")
    with np.errstate(divide="ignore", invalid="ignore"):
        cmf = np.where(sv > 0, smf / sv, np.nan)
    return _sgn(ctx.cross(cmf > th), ctx.cross(cmf < -th))


def _supertrend_flip(ctx, p):
    nb, m = ctx.bars(p["win_min"]), p["mult"]
    rng = ctx.h - ctx.l
    atr = ctx.roll(rng, nb, "mean")
    mid = (ctx.h + ctx.l) / 2.0
    up_b, dn_b = (mid + m * atr).tolist(), (mid - m * atr).tolist()
    c, day = ctx.c.tolist(), ctx.day.tolist()
    out = np.zeros(ctx.n, dtype=int)
    fub = flb = float("nan")
    trend = 0
    prev_day = None
    for i in range(ctx.n):
        u, d = up_b[i], dn_b[i]
        if day[i] != prev_day or math.isnan(u):
            prev_day = day[i]
            trend = 0
            fub, flb = u, d
            continue
        if math.isnan(fub):
            fub, flb = u, d
            continue
        new_trend = trend
        if c[i] > fub:
            new_trend = 1
        elif c[i] < flb:
            new_trend = -1
        if new_trend != trend and new_trend != 0:
            out[i] = new_trend
        trend = new_trend
        fub = min(u, fub) if c[i] < fub else u
        flb = max(d, flb) if c[i] > flb else d
    return out


def _stoch_zone_exit(ctx, p):
    nb, z = ctx.bars(p["win_min"]), p["zone"]
    hh, ll = ctx.roll(ctx.h, nb, "max"), ctx.roll(ctx.l, nb, "min")
    with np.errstate(divide="ignore", invalid="ignore"):
        k = np.where(hh - ll > 0, (ctx.c - ll) / (hh - ll), np.nan)
    kp = ctx.prev(k, 1)
    long = (kp < z) & (k >= z)
    short = (kp > 1 - z) & (k <= 1 - z)
    return _sgn(long, short)


def _trix_cross(ctx, p):
    n = ctx.bars(p["span_min"])
    e3 = ctx.cached(("trix_e3", n), lambda: ctx.ema(ctx.ema(ctx.ema(ctx.c, n), n), n))
    d = e3 - ctx.prev(e3, 1)
    return _sgn(ctx.cross(d > 0), ctx.cross(d < 0))


def _force_cross(ctx, p):
    n = ctx.bars(p["span_min"])
    fi = (ctx.c - ctx.prev(ctx.c, 1)) * ctx.v
    sm = ctx.ema(fi, n)
    return _sgn(ctx.cross(sm > 0), ctx.cross(sm < 0))


def _expanding_run(ctx, p):
    r, bf = int(p["run"]), p["body"]
    rng = ctx.h - ctx.l
    body = np.abs(ctx.c - ctx.o)
    big = (rng > ctx.prev(rng, 1)) & (body >= bf * rng) & (rng > 0)
    up = big & (ctx.c > ctx.o)
    dn = big & (ctx.c < ctx.o)
    ru = ctx.roll(up.astype(float), r, "sum") == r
    rd = ctx.roll(dn.astype(float), r, "sum") == r
    return _sgn(ctx.cross(ru), ctx.cross(rd))


def _keltner_reentry(ctx, p):
    nb, m = ctx.bars(p["win_min"]), p["mult"]
    ema = ctx.cached(("ema", nb), lambda: ctx.ema(ctx.c, nb))
    atr = ctx.roll(ctx.h - ctx.l, nb, "mean")
    upper, lower = ema + m * atr, ema - m * atr
    was_hi = ctx.prev(ctx.c, 1) > ctx.prev(upper, 1)
    was_lo = ctx.prev(ctx.c, 1) < ctx.prev(lower, 1)
    short = was_hi & (ctx.c <= upper)
    long = was_lo & (ctx.c >= lower)
    return _sgn(long, short)


def _prev_close_cross(ctx, p):
    nb = ctx.bars(p["away_min"])
    pc = ctx.prev_session_value("close")
    below = (ctx.c < pc).astype(float)
    above = (ctx.c > pc).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    up = was_below & (ctx.c > pc)
    dn = was_above & (ctx.c < pc)
    return _sgn(up, dn)


def _range_top_dwell(ctx, p):
    nb, k = ctx.bars(p["win_min"]), ctx.bars(p["dwell_min"])
    hh, ll = ctx.roll(ctx.h, nb, "max"), ctx.roll(ctx.l, nb, "min")
    with np.errstate(divide="ignore", invalid="ignore"):
        pos = np.where(hh - ll > 0, (ctx.c - ll) / (hh - ll), np.nan)
    top = (pos >= 0.8).astype(float)
    bot = (pos <= 0.2).astype(float)
    up = ctx.roll(top, k, "sum") == k
    dn = ctx.roll(bot, k, "sum") == k
    return _sgn(ctx.cross(up), ctx.cross(dn))


def _emv_cross(ctx, p):
    nb = ctx.bars(p["win_min"])
    mid = (ctx.h + ctx.l) / 2.0
    rng = ctx.h - ctx.l
    with np.errstate(divide="ignore", invalid="ignore"):
        emv = np.where(ctx.v > 0, (mid - ctx.prev(mid, 1)) * rng / ctx.v, np.nan)
    sm = ctx.roll(emv, nb, "mean")
    return _sgn(ctx.cross(sm > 0), ctx.cross(sm < 0))


FAMILIES = [
    Family("E-1228", "Chaikin money-flow threshold cross",
           "Volume-weighted close location over a window shows whether aggressors close bars near highs or lows; when it "
           "crosses a clear positive/negative level, persistent one-sided aggression is under way and should follow.",
           {"win_min": [20, 30, 45], "th": [0.1, 0.2, 0.3]}, _cmf_cross,
           source="assistant reasoning", author="agent"),
    Family("E-1229", "ATR trailing-band (SuperTrend) flip",
           "A close through a ratcheting ATR band means the pullback buyers/sellers who were defending the trend gave up; "
           "stop-triggered flow follows the flip.",
           {"win_min": [30, 60], "mult": [1.5, 2.0, 3.0]}, _supertrend_flip,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1230", "Stochastic leaving an extreme zone",
           "When the close returns from the bottom (top) zone of the recent range, the push that held it there is spent "
           "and sidelined participants resume the other way; follow the exit.",
           {"win_min": [30, 60, 90], "zone": [0.1, 0.2, 0.3]}, _stoch_zone_exit,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1231", "TRIX direction change",
           "A triple-smoothed EMA changing slope filters noise; its turn marks a shift of the dominant flow that "
           "slower participants then chase.",
           {"span_min": [10, 20, 30]}, _trix_cross,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1232", "Force-index zero cross",
           "Price change times volume, smoothed, switches sign when the side that trades size takes over; the loser "
           "side must cover/chase in the same direction.",
           {"span_min": [10, 20, 30]}, _force_cross,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1233", "Expanding-range same-colour run",
           "Consecutive full-body bars each wider than the last show aggression escalating; counterparties are being "
           "forced to chase or cover, so the move continues.",
           {"run": [2, 3, 4], "body": [0.4, 0.5, 0.6]}, _expanding_run,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1234", "Keltner band re-entry fade",
           "A close outside an ATR band around the EMA is a stretch; when the next bar closes back inside, the stretched "
           "side failed to attract follow-through and price reverts toward the mean.",
           {"win_min": [30, 60], "mult": [1.5, 2.0, 2.5]}, _keltner_reentry,
           source="assistant reasoning", author="agent"),
    Family("E-1235", "Previous-close cross after a stay",
           "Yesterday's settlement is the reference for positions carried overnight; after trading on one side for a "
           "while, a cross to the other side flips the carried positions' P&L and forces them to act.",
           {"away_min": [5, 10, 20]}, _prev_close_cross,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1236", "Range-edge dwell follow",
           "Closing in the top (bottom) fifth of the recent range for several bars in a row means the market is accepting "
           "prices at the extreme, not rejecting them; buyers (sellers) in control keep pushing.",
           {"win_min": [30, 60, 90], "dwell_min": [5, 10, 15]}, _range_top_dwell,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1237", "Ease-of-movement zero cross",
           "Price displacement per unit of volume turns positive when price moves up easily on little volume resistance "
           "(few sellers); a sign change shows resistance has vanished on one side.",
           {"win_min": [10, 20, 30]}, _emv_cross,
           markets=("WIN",), source="assistant reasoning", author="agent"),
]
