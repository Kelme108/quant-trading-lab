"""Conveyor batch B-132 (agent, 2026-11-24). Mixed themes: clock levels, cross-market lead, regimes, range position."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _sgn(long, short):
    return long.astype(int) - short.astype(int)


def _hour_open_reclaim(ctx, p):
    nb = ctx.bars(p["away_min"])
    ho = pd.Series(np.where(ctx.minute % 60 == 0, ctx.o, np.nan)).groupby(ctx.day).ffill().to_numpy()
    below = (ctx.c < ho).astype(float)
    above = (ctx.c > ho).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    up = was_below & (ctx.c > ho)
    dn = was_above & (ctx.c < ho)
    return _sgn(up, dn)


def _dollar_lead(ctx, p):
    nb, k = ctx.bars(p["move_min"]), p["k"]
    oc = ctx.other_close()
    ro = oc / ctx.prev(oc, nb) - 1.0
    rw = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    ao = ctx.cached(("ao", nb), lambda: ctx.prev_sessions(np.abs(ro), "mean"))
    aw = ctx.cached(("aw", nb), lambda: ctx.prev_sessions(np.abs(rw), "mean"))
    long = (ro <= -k * ao) & (rw <= 0.25 * aw)
    short = (ro >= k * ao) & (rw >= -0.25 * aw)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _squeeze_expansion(ctx, p):
    nl, ratio = ctx.bars(p["long_min"]), p["ratio"]
    ns = max(2, nl // 4)
    rng = ctx.h - ctx.l
    short_avg = ctx.roll(rng, ns, "mean", include_current=False)
    long_avg = ctx.roll(rng, nl, "mean", include_current=False)
    squeezed = short_avg <= ratio * long_avg
    big = rng >= 2.0 * long_avg
    body = np.abs(ctx.c - ctx.o) >= 0.6 * rng
    ok = squeezed & big & body & (rng > 0)
    return _sgn(ok & (ctx.c > ctx.o), ok & (ctx.c < ctx.o))


def _band_reentry(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    m = ctx.roll(ctx.c, n, "mean")
    s = ctx.roll(ctx.c, n, "std")
    up, lo = m + k * s, m - k * s
    pc, pu, pl = ctx.prev(ctx.c, 1), ctx.prev(up, 1), ctx.prev(lo, 1)
    short = (pc > pu) & (ctx.c <= up) & (s > 0)
    long = (pc < pl) & (ctx.c >= lo) & (s > 0)
    return _sgn(long, short)


def _day_open_hold(ctx, p):
    e = p["excursion"]
    sh = ctx.session_high(include_current=False)
    sl = ctx.session_low(include_current=False)
    do = ctx.day_open
    long = (sh >= do * (1 + e)) & (sl > do * (1 - e / 2)) & (ctx.l <= do) & (ctx.c > do)
    short = (sl <= do * (1 - e)) & (sh < do * (1 + e / 2)) & (ctx.h >= do) & (ctx.c < do)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _bar_gap_fade(ctx, p):
    k = p["k"]
    n = ctx.bars(30)
    avg = ctx.roll(ctx.h - ctx.l, n, "mean", include_current=False)
    gap = ctx.o - ctx.prev(ctx.c, 1)
    long = (gap <= -k * avg) & (ctx.c > ctx.o) & (avg > 0)
    short = (gap >= k * avg) & (ctx.c < ctx.o) & (avg > 0)
    return _sgn(long, short)


def _donchian_mid_cross(ctx, p):
    n = ctx.bars(p["win_min"])
    hi = ctx.roll(ctx.h, n, "max", include_current=False)
    lo = ctx.roll(ctx.l, n, "min", include_current=False)
    mid = (hi + lo) / 2
    wide = (hi - lo) >= 4 * ctx.roll(ctx.h - ctx.l, n, "mean", include_current=False)
    up = (ctx.c > mid) & wide
    dn = (ctx.c < mid) & wide
    return _sgn(ctx.cross(up), ctx.cross(dn))


def _range_traverse(ctx, p):
    f, nb = p["frac"], ctx.bars(p["win_min"])
    sh = ctx.session_high(include_current=True)
    sl = ctx.session_low(include_current=True)
    span = sh - sl
    pos = np.where(span > 0, (ctx.c - sl) / np.where(span > 0, span, 1.0), np.nan)
    big = span >= 3 * ctx.roll(ctx.h - ctx.l, nb, "mean")
    was_low = ctx.roll(pos, nb, "min", include_current=False) <= f
    was_high = ctx.roll(pos, nb, "max", include_current=False) >= 1 - f
    up = big & was_low & (pos >= 1 - f)
    dn = big & was_high & (pos <= f)
    return _sgn(ctx.cross(up), ctx.cross(dn))


def _rising_participation(ctx, p):
    n = int(p["bars"])
    up = np.ones(ctx.n, bool)
    dn = np.ones(ctx.n, bool)
    for j in range(n):
        cj, cj1 = ctx.prev(ctx.c, j), ctx.prev(ctx.c, j + 1)
        vj, vj1 = ctx.prev(ctx.v, j), ctx.prev(ctx.v, j + 1)
        up &= (cj > cj1) & (vj > vj1)
        dn &= (cj < cj1) & (vj > vj1)
    return _sgn(ctx.cross(up), ctx.cross(dn))


def _autocorr_regime(ctx, p):
    n, th = ctx.bars(p["win_min"]), p["th"]
    r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    r1 = ctx.prev(r, 1)
    num = ctx.roll(r * r1, n, "mean")
    den = ctx.roll(r * r, n, "mean")
    ac = np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)
    pos = ac >= th
    neg = ac <= -th
    long = (pos & (r > 0)) | (neg & (r < 0))
    short = (pos & (r < 0)) | (neg & (r > 0))
    return _sgn(ctx.cross(long), ctx.cross(short))


FAMILIES = [
    Family("E-1318", "Hour-open reclaim",
           "The open of the clock hour is a reference many intraday traders watch; after a spell entirely on one side, "
           "the first close across it marks a change of control for that hour; follow.",
           {"away_min": [10, 20, 30]}, _hour_open_reclaim, source="assistant reasoning", author="assistant"),
    Family("E-1319", "Dollar-led index catch-up",
           "WIN and the dollar move inversely; when the dollar makes an unusual move and the index has not yet responded, "
           "index traders lag the FX desk; follow the dollar's implication.",
           {"move_min": [5, 10, 20], "k": [1.5, 2.0]}, _dollar_lead, markets=("WIN",), source="assistant reasoning",
           author="assistant"),
    Family("E-1320", "Squeeze expansion bar",
           "After a few unusually quiet bars, a wide full-bodied bar shows resting liquidity was absorbed and a new "
           "regime of volatility starts; follow its direction.",
           {"long_min": [20, 40, 60], "ratio": [0.5, 0.7]}, _squeeze_expansion, markets=("WIN",),
           source="assistant reasoning", author="assistant"),
    Family("E-1321", "Band re-entry fade",
           "A close outside a rolling mean +/- k sd band followed by a close back inside means the push found no "
           "followers; fade it back toward the mean.",
           {"win_min": [20, 40, 60], "k": [2.0, 2.5]}, _band_reentry, markets=("WIN",), source="assistant reasoning",
           author="assistant"),
    Family("E-1322", "Day-open hold after an excursion",
           "After the session has traveled away from the day open, a retest of the open that is rejected shows the "
           "initial side still owns the day; follow it.",
           {"excursion": [0.002, 0.003, 0.005]}, _day_open_hold, markets=("WIN",), source="assistant reasoning",
           author="assistant"),
    Family("E-1323", "Bar-open gap fill fade",
           "A bar opening far from the prior close by more than the usual range, that then closes back toward it, "
           "is a liquidity gap being filled; fade the gap direction.",
           {"k": [0.5, 1.0, 1.5]}, _bar_gap_fade, markets=("WIN",), source="assistant reasoning", author="assistant"),
    Family("E-1324", "Donchian midline cross",
           "In a wide recent channel the midpoint separates buyers' from sellers' control; a close crossing it "
           "shifts the balance; follow.",
           {"win_min": [30, 60, 90]}, _donchian_mid_cross, markets=("WIN",), source="assistant reasoning",
           author="assistant"),
    Family("E-1325", "Session-range traverse",
           "When the price crosses from one end of an already wide session range to the other, the earlier side has "
           "capitulated; follow the traverse.",
           {"frac": [0.2, 0.3], "win_min": [30, 60, 90]}, _range_traverse, markets=("WIN",),
           source="assistant reasoning", author="assistant"),
    Family("E-1326", "Rising participation run",
           "Consecutive higher (lower) closes each on more volume than the last mean new participants keep joining "
           "the move; follow it.",
           {"bars": [2, 3, 4]}, _rising_participation, markets=("WIN",), source="volume-price analysis",
           author="assistant"),
    Family("E-1327", "Autocorrelation regime switch",
           "When recent bar-to-bar returns trend (positive autocorrelation) the next bar's direction is followed; when "
           "they chop (negative), it is faded; the regime picks the side.",
           {"win_min": [30, 60], "th": [0.1, 0.2, 0.3]}, _autocorr_regime, markets=("WIN",),
           source="assistant reasoning", author="assistant"),
]
