"""Conveyor batch B-127 (agent, 2026-11-24). Less-used mechanisms: noise-regime fade, double tests, floor pivots,
day-over-day path, anchored VWAP, choppiness, prior-close bias, flag break, ADR budget, impulse-midpoint retest."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from b3.esteira import Family


def _atr(ctx, n=20):
    return ctx.cached(("b127atr", n), lambda: ctx.roll(ctx.h - ctx.l, n, "mean"))


def _fire(ctx, long, short):
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _noise_ratio_fade(ctx, p):
    nb = max(6, ctx.bars(p["win_min"]))
    thr = p["ratio"]
    m = ctx.bars(5) if ctx.tf == 1 else 1
    with np.errstate(all="ignore"):
        pk = np.log(ctx.h / ctx.l) ** 2 / (4 * math.log(2))
        cc = np.log(ctx.c / ctx.prev(ctx.c, 1)) ** 2
        ratio = ctx.roll(pk, nb, "mean") / ctx.roll(cc, nb, "mean")
        sd = np.sqrt(ctx.roll(cc, nb, "mean")) * math.sqrt(m)
        z = np.log(ctx.c / ctx.prev(ctx.c, m)) / sd
    long = (ratio > thr) & (z <= -1.5)
    short = (ratio > thr) & (z >= 1.5)
    return _fire(ctx, long, short)


def _double_test(ctx, p):
    w = max(5, ctx.bars(p["win_min"]))
    tol = p["tol_k"] * _atr(ctx, 20)
    old_lo = ctx.roll(ctx.prev(ctx.l, 3), w, "min")
    old_hi = ctx.roll(ctx.prev(ctx.h, 3), w, "max")
    near_lo_prev = np.fmin(ctx.prev(ctx.l, 1), ctx.prev(ctx.l, 2))
    near_hi_prev = np.fmax(ctx.prev(ctx.h, 1), ctx.prev(ctx.h, 2))
    with np.errstate(all="ignore"):
        long = (np.abs(ctx.l - old_lo) <= tol) & (ctx.c > ctx.o) & (near_lo_prev > old_lo + 2 * tol)
        short = (np.abs(ctx.h - old_hi) <= tol) & (ctx.c < ctx.o) & (near_hi_prev < old_hi - 2 * tol)
    return _fire(ctx, long, short)


def _floor_pivot(ctx, p):
    ph, pl, pc = ctx.prev_session_value("high"), ctx.prev_session_value("low"), ctx.prev_session_value("close")
    piv = (ph + pl + pc) / 3.0
    if int(p["level"]) == 1:
        res, sup = 2 * piv - pl, 2 * piv - ph
    else:
        res, sup = piv + (ph - pl), piv - (ph - pl)
    b = p["buffer"]
    with np.errstate(all="ignore"):
        short = (ctx.h > res * (1 + b)) & (ctx.c < res)
        long = (ctx.l < sup * (1 - b)) & (ctx.c > sup)
    return _fire(ctx, long, short)


def _path_relative(ctx, p):
    n, k = int(p["sessions"]), p["k"]
    r = ctx.c / ctx.day_open - 1.0
    ref = ctx.cached(("b127ref", n), lambda: ctx.same_minute(r, "mean", n=n))
    typ = ctx.cached("b127typ", lambda: ctx.same_minute(np.abs(r), "mean", n=20))
    diff = r - ref
    with np.errstate(all="ignore"):
        up = (diff > k * typ) & (typ > 0)
        dn = (diff < -k * typ) & (typ > 0)
    return _fire(ctx, up, dn)


def _anchored(ctx):
    def build():
        tp = ((ctx.h + ctx.l + ctx.c) / 3.0).tolist()
        h, l, v, day = ctx.h.tolist(), ctx.l.tolist(), ctx.v.tolist(), ctx.day.tolist()
        n = ctx.n
        alo, ahi = [math.nan] * n, [math.nan] * n
        slo, shi = [0] * n, [0] * n
        cur = None
        for i in range(n):
            if day[i] != cur:
                cur = day[i]
                rl, rh = math.inf, -math.inf
                pl_ = vl = ph_ = vh = 0.0
                al = ah = i
            w = tp[i] * v[i]
            if l[i] <= rl:
                rl, pl_, vl, al = l[i], w, v[i], i
            else:
                pl_ += w
                vl += v[i]
            if h[i] >= rh:
                rh, ph_, vh, ah = h[i], w, v[i], i
            else:
                ph_ += w
                vh += v[i]
            if vl > 0:
                alo[i] = pl_ / vl
            if vh > 0:
                ahi[i] = ph_ / vh
            slo[i], shi[i] = i - al, i - ah
        return np.array(alo), np.array(ahi), np.array(slo), np.array(shi)
    return ctx.cached("b127anch", build)


def _anchored_test(ctx, p):
    alo, ahi, slo, shi = _anchored(ctx)
    m = ctx.bars(p["age_min"])
    with np.errstate(all="ignore"):
        long = (slo >= m) & (ctx.l <= alo) & (ctx.c > alo)
        short = (shi >= m) & (ctx.h >= ahi) & (ctx.c < ahi)
    return _fire(ctx, long, short)


def _chop_edge(ctx, p):
    nb = max(6, ctx.bars(p["win_min"]))
    thr = p["ci"]
    rng = ctx.h - ctx.l
    hi, lo = ctx.roll(ctx.h, nb, "max"), ctx.roll(ctx.l, nb, "min")
    with np.errstate(all="ignore"):
        ci = 100 * np.log10(ctx.roll(rng, nb, "sum") / (hi - lo)) / math.log10(nb)
        pos = (ctx.c - lo) / (hi - lo)
    long = (ci > thr) & (pos <= 0.15) & (ctx.c > ctx.o)
    short = (ci > thr) & (pos >= 0.85) & (ctx.c < ctx.o)
    return _fire(ctx, long, short)


def _prior_close_bias(ctx, p):
    nb = ctx.bars(p["ema_min"])
    q = p["q"]
    ph, pl, pc = ctx.prev_session_value("high"), ctx.prev_session_value("low"), ctx.prev_session_value("close")
    with np.errstate(all="ignore"):
        loc = (pc - pl) / (ph - pl)
    ema = ctx.cached(("b127ema", nb), lambda: ctx.ema(ctx.c, nb))
    long = (loc >= 1 - q) & (ctx.c > ema)
    short = (loc <= q) & (ctx.c < ema)
    return _fire(ctx, long, short)


def _flag_break(ctx, p):
    k, m = p["k"], int(p["m"])
    rng = ctx.h - ctx.l
    atr_i = ctx.prev(_atr(ctx, 20), m + 1)
    ri = ctx.prev(rng, m + 1)
    oi, ci_, hi_, li = ctx.prev(ctx.o, m + 1), ctx.prev(ctx.c, m + 1), ctx.prev(ctx.h, m + 1), ctx.prev(ctx.l, m + 1)
    flag_rng = ctx.roll(rng, m, "max", include_current=False)
    flag_lo = ctx.roll(ctx.l, m, "min", include_current=False)
    flag_hi = ctx.roll(ctx.h, m, "max", include_current=False)
    with np.errstate(all="ignore"):
        big = ri >= k * atr_i
        tight = flag_rng < 0.5 * ri
        long = big & (ci_ > oi) & tight & (flag_lo > li + 0.5 * ri) & (ctx.c > flag_hi) & (ctx.c > ctx.o)
        short = big & (ci_ < oi) & tight & (flag_hi < hi_ - 0.5 * ri) & (ctx.c < flag_lo) & (ctx.c < ctx.o)
    return _fire(ctx, long, short)


def _adr_budget(ctx, p):
    k = p["k"]

    def build():
        s = pd.Series(ctx.h - ctx.l)
        hi = pd.Series(ctx.h).groupby(ctx.day).max()
        lo = pd.Series(ctx.l).groupby(ctx.day).min()
        adr = (hi - lo).shift(1).rolling(20, min_periods=20).mean()
        adr = adr.reindex(range(int(ctx.day.max()) + 1))
        return adr.to_numpy()[ctx.day]
    adr = ctx.cached("b127adr", build)
    up = ctx.c > ctx.day_open + k * adr
    dn = ctx.c < ctx.day_open - k * adr
    return _fire(ctx, up, dn)


def _impulse_mid_retest(ctx, p):
    k, m = p["k"], int(p["m"])
    rng = ctx.h - ctx.l
    atr = _atr(ctx, 20)
    long = np.zeros(ctx.n, bool)
    short = np.zeros(ctx.n, bool)
    with np.errstate(all="ignore"):
        for j in range(2, m + 1):
            hj, lj, oj, cj = ctx.prev(ctx.h, j), ctx.prev(ctx.l, j), ctx.prev(ctx.o, j), ctx.prev(ctx.c, j)
            big = (hj - lj) >= k * ctx.prev(atr, j)
            mid = (hj + lj) / 2.0
            held_up = ctx.roll(ctx.l, j - 1, "min", include_current=False) > mid
            held_dn = ctx.roll(ctx.h, j - 1, "max", include_current=False) < mid
            long |= big & (cj > oj) & (cj >= lj + 0.67 * (hj - lj)) & held_up & (ctx.l <= mid) & (ctx.c > mid) & (ctx.c > ctx.o)
            short |= big & (cj < oj) & (cj <= lj + 0.33 * (hj - lj)) & held_dn & (ctx.h >= mid) & (ctx.c < mid) & (ctx.c < ctx.o)
    return _fire(ctx, long, short)


FAMILIES = [
    Family("E-1268", "Noise-regime move fade",
           "When intrabar (Parkinson) variance far exceeds close-to-close variance, price is bouncing inside bars between "
           "quoters; a 5-minute move of 1.5 sigma in that regime is liquidity noise, so fade it.",
           {"win_min": [20, 30, 60], "ratio": [1.5, 2.0, 3.0]}, _noise_ratio_fade,
           source="assistant reasoning (range-based vs close-based volatility estimators)", author="agent"),
    Family("E-1269", "Equal-low / equal-high double test",
           "A second probe into the same low (high) after leaving it shows the same resting demand (supply) defending the "
           "level; buy the bullish bar at the retest, sell the bearish bar at an equal high.",
           {"win_min": [30, 60, 90], "tol_k": [0.25, 0.5, 1.0]}, _double_test, markets=("WIN",),
           source="assistant reasoning (double bottom/top)", author="agent"),
    Family("E-1270", "Floor-pivot S1/R1 rejection",
           "Floor-trader pivot levels from yesterday's H/L/C are watched by many discretionary traders; a poke beyond the "
           "level that closes back is absorbed by resting orders, so fade it.",
           {"level": [1, 2], "buffer": [0.0, 0.0005, 0.001]}, _floor_pivot, markets=("WIN",),
           source="assistant reasoning (floor pivot points)", author="agent"),
    Family("E-1271", "Relative-to-usual-path follow",
           "Today's move since the open compared with the average path of the same clock minute over recent sessions "
           "isolates unusual strength; when it exceeds the typical size, fresh flow is winning and continues.",
           {"sessions": [5, 10, 20], "k": [0.5, 1.0, 1.5]}, _path_relative,
           source="assistant reasoning (seasonal intraday profile deviation)", author="agent"),
    Family("E-1272", "Anchored-VWAP support test",
           "VWAP anchored at the session low (high) is the average cost of everyone who bought (sold) since the turn; a dip "
           "to it that closes back above (below) is where those holders defend, so follow the turn.",
           {"age_min": [15, 30, 60]}, _anchored_test, markets=("WIN",),
           source="assistant reasoning (anchored VWAP)", author="agent"),
    Family("E-1273", "Choppiness range-edge fade",
           "A high choppiness index means the window is a sideways range; a bar turning back at the bottom (top) of that "
           "range is a range-trader's entry back toward the middle.",
           {"win_min": [14, 20, 30], "ci": [50.0, 58.0, 65.0]}, _chop_edge,
           source="assistant reasoning (choppiness index)", author="agent"),
    Family("E-1274", "Prior-close-location EMA turn",
           "Yesterday closing in the top (bottom) of its range leaves carried positions with the same bias; an intraday "
           "close back over (under) the short EMA is the dip-buyer's entry in that direction.",
           {"ema_min": [10, 20, 30], "q": [0.2, 0.33]}, _prior_close_bias, markets=("WIN",),
           source="assistant reasoning (close location value of the prior session)", author="agent"),
    Family("E-1275", "Impulse flag break",
           "After an outsized bar, a few narrow bars held in its upper (lower) half show profit-taking without give-back; "
           "the close beyond the flag releases the next leg.",
           {"k": [1.5, 2.0, 3.0], "m": [2, 3, 4]}, _flag_break, markets=("WIN",),
           source="assistant reasoning (flag/pennant continuation)", author="agent"),
    Family("E-1276", "Average-daily-range budget breach",
           "Moves from the open of a fraction of the 20-session average daily range show a day with above-normal "
           "participation; stops and chasers beyond that distance keep the push going.",
           {"k": [0.2, 0.35, 0.5]}, _adr_budget,
           source="assistant reasoning (average daily range multiples from the open)", author="agent"),
    Family("E-1277", "Impulse-bar midpoint retest",
           "A big bar closing in its top (bottom) third, followed by a pullback to its midpoint that holds and closes back "
           "above (below), shows the impulse buyers (sellers) defending half the bar; follow the impulse.",
           {"k": [1.5, 2.0, 3.0], "m": [3, 5, 8]}, _impulse_mid_retest, markets=("WIN",),
           source="assistant reasoning (50% retest of an impulse candle)", author="agent"),
]
