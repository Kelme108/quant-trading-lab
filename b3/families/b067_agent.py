"""Conveyor batch B-067 (agent, 2026-11-22). Mixed themes: round levels, sweeps, narrow ranges, pivots, streaks, flow, hour-end drift."""
from __future__ import annotations

import numpy as np

from b3.esteira import Family


def _sgn(long, short):
    return long.astype(int) - short.astype(int)


def _round_level(ctx, p):
    unit = np.where(ctx.c > 30000, 1.0, 0.02)       # WIN in points, WDO scaled
    step = p["step"] * unit
    pc = ctx.prev(ctx.c, 1)
    with np.errstate(invalid="ignore"):
        up = (np.floor(pc / step) + 1.0) * step
        dn = np.floor(pc / step) * step
        short = (ctx.h >= up) & (ctx.c < up)
        long = (ctx.l <= dn) & (ctx.c > dn)
    return _sgn(long & ~np.isnan(pc), short & ~np.isnan(pc))


def _three_bar_sweep(ctx, p):
    rng = ctx.h - ctx.l
    avg = ctx.roll(rng, 20, "mean", include_current=False)
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    h2, l2 = ctx.prev(ctx.h, 2), ctx.prev(ctx.l, 2)
    big = rng >= p["k"] * avg
    long = (ctx.l < np.minimum(l1, l2)) & (ctx.c > h1) & big
    short = (ctx.h > np.maximum(h1, h2)) & (ctx.c < l1) & big
    return _sgn(long, short)


def _nr_break(ctx, p):
    n = int(p["n"])
    rng = ctx.h - ctx.l
    r1 = ctx.prev(rng, 1)
    mn = ctx.roll(rng, n, "min", include_current=True)
    nr = ctx.prev(mn, 1) == r1
    nr = nr & (r1 > 0)
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    return _sgn(nr & (ctx.c > h1), nr & (ctx.c < l1))


def _pivot_cross(ctx, p):
    n = int(p["ema_bars"])
    ph, pl, pc = ctx.prev_session_value("high"), ctx.prev_session_value("low"), ctx.prev_session_value("close")
    piv = (ph + pl + pc) / 3.0
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    up = ctx.cross((ctx.c > piv) & (ctx.c > ema))
    dn = ctx.cross((ctx.c < piv) & (ctx.c < ema))
    return _sgn(up, dn)


def _open_bounce(ctx, p):
    k = p["k"]
    typical = ctx.cached("abs_ret_same_minute", lambda: ctx.same_minute(np.abs(ctx.c / ctx.day_open - 1.0), "mean"))
    hi = ctx.session_high(include_current=False) / ctx.day_open - 1.0
    lo = ctx.day_open / ctx.session_low(include_current=False) - 1.0
    long = (hi >= k * typical) & (ctx.l <= ctx.day_open) & (ctx.c > ctx.day_open)
    short = (lo >= k * typical) & (ctx.h >= ctx.day_open) & (ctx.c < ctx.day_open)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _hh_hl_streak(ctx, p):
    n = int(p["n"])
    up = np.ones(ctx.n, bool)
    dn = np.ones(ctx.n, bool)
    for i in range(n):
        hi, hp = ctx.prev(ctx.h, i), ctx.prev(ctx.h, i + 1)
        li, lp = ctx.prev(ctx.l, i), ctx.prev(ctx.l, i + 1)
        up &= (hi > hp) & (li > lp)
        dn &= (hi < hp) & (li < lp)
    return _sgn(ctx.cross(up), ctx.cross(dn))


def _signed_flow(ctx, p):
    n, thr = int(p["n"]), p["thr"]
    rng = ctx.h - ctx.l
    loc = np.where(rng > 0, (2 * ctx.c - ctx.h - ctx.l) / np.where(rng > 0, rng, 1.0), 0.0)
    num = ctx.roll(loc * ctx.v, n, "sum")
    den = ctx.roll(ctx.v, n, "sum")
    with np.errstate(invalid="ignore", divide="ignore"):
        f = num / den
    return _sgn(ctx.cross(f > thr), ctx.cross(f < -thr))


def _hour_end_drift(ctx, p):
    nb = ctx.bars(p["span_min"])
    k = p["k"]
    move = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    typical = ctx.cached(("abs_move", nb), lambda: ctx.prev_sessions(np.abs(move), "mean"))
    at = (ctx.minute % 60) == 50
    return _sgn(at & (move >= k * typical), at & (move <= -k * typical))


def _midline_cross(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    mid = (hi + lo) / 2.0
    return _sgn(ctx.cross(ctx.c > mid), ctx.cross(ctx.c < mid))


def _tweezer(ctx, p):
    tol = p["tol"]
    rng = ctx.h - ctx.l
    r1 = ctx.prev(rng, 1)
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    c1, o1 = ctx.prev(ctx.c, 1), ctx.prev(ctx.o, 1)
    c3 = ctx.prev(ctx.c, 3)
    top = (np.abs(ctx.h - h1) <= tol * r1) & (c1 > o1) & (ctx.c < ctx.o) & (c1 > c3) & (r1 > 0)
    bot = (np.abs(ctx.l - l1) <= tol * r1) & (c1 < o1) & (ctx.c > ctx.o) & (c1 < c3) & (r1 > 0)
    return _sgn(bot, top)


FAMILIES = [
    Family("E-668", "Round-number level rejection",
           "Stop and limit orders cluster at round index/dollar levels; a bar that pokes through a round level and closes back "
           "on the near side has run those stops without follow-through, so fade it.",
           {"step": [250, 500, 1000]}, _round_level, source="assistant reasoning", author="agent"),
    Family("E-669", "Three-bar low/high sweep reversal",
           "A bar that sweeps below the two previous lows and closes above the previous high traps sellers; buy it "
           "(mirror for sells), only when the bar is not tiny.",
           {"k": [0.5, 1.0, 1.5]}, _three_bar_sweep, source="assistant reasoning", author="agent"),
    Family("E-670", "Narrowest-range bar breakout",
           "When the previous bar has the smallest range of the last n bars, volatility is compressed; a close beyond "
           "its high/low starts the expansion in that direction.",
           {"n": [4, 7, 10]}, _nr_break, source="assistant reasoning (NR4/NR7 idea)", author="agent"),
    Family("E-671", "Floor-pivot cross with EMA side",
           "The previous session's pivot (H+L+C)/3 is a reference many desks use; a fresh cross of it that agrees with the "
           "short EMA side signals a bias shift for the session.",
           {"ema_bars": [10, 20, 40]}, _pivot_cross, source="assistant reasoning (floor pivots)", author="agent"),
    Family("E-672", "Day-open retest bounce",
           "After the session has traded well away from its opening price, the first retest of the open is a level of "
           "unfinished business; buyers/sellers who drove the move defend it, so follow the original side.",
           {"k": [0.5, 1.0, 1.5]}, _open_bounce, source="assistant reasoning", author="agent"),
    Family("E-673", "Higher-highs-and-higher-lows streak",
           "n consecutive bars each with higher high and higher low is orderly one-sided trading with no overlap; "
           "participants chasing keep it going a little longer.",
           {"n": [3, 4, 5]}, _hh_hl_streak, source="assistant reasoning (Dow structure)", author="agent"),
    Family("E-674", "Close-location volume flow cross",
           "Volume weighted by where each bar closes in its range measures who finished each bar in control; a cross of the "
           "n-bar flow above a threshold marks aggressive persistent buying (or selling).",
           {"n": [5, 10, 20], "thr": [0.3, 0.5]}, _signed_flow, source="assistant reasoning (Chaikin-style flow)",
           author="agent"),
    Family("E-675", "Hour-end drift follow",
           "Index and dollar flow tied to hourly rebalancing and algorithmic hourly benchmarks tends to push in the direction "
           "of the hour's move into its last 10 minutes; trade with it at minute :50.",
           {"span_min": [30, 45], "k": [0.5, 1.0, 1.5]}, _hour_end_drift, source="assistant reasoning", author="agent"),
    Family("E-676", "Range-midline cross follow",
           "The midpoint of the recent high-low range is the balance point of a Donchian channel; closing across it after "
           "trading on the other side shows supply or demand has taken over.",
           {"lookback_min": [30, 60, 120]}, _midline_cross, source="assistant reasoning (Donchian midline / Kijun)",
           author="agent"),
    Family("E-677", "Tweezer reversal after a push",
           "Two successive bars of opposite colour stopping at the same high (or low) after a push show a defended level; "
           "the pushers are rejected twice, so fade.",
           {"tol": [0.05, 0.1, 0.2]}, _tweezer, source="candlestick literature (tweezer top/bottom)", author="agent"),
]
