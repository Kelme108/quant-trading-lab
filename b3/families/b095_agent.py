"""Conveyor batch B-095 (agent, 2026-11-24). Classic oscillator / structure / thrust ideas on the index."""
from __future__ import annotations

import numpy as np

from b3.esteira import Family


def _out(ctx, long, short):
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _stoch_fade(ctx, p):
    nb, th = ctx.bars(p["lookback_min"]), p["th"]
    hi = ctx.roll(ctx.h, nb, "max")
    lo = ctx.roll(ctx.l, nb, "min")
    with np.errstate(all="ignore"):
        k = np.where(hi > lo, (ctx.c - lo) / (hi - lo) * 100.0, np.nan)
        return _out(ctx, k > th, k < 100.0 - th)


def _macd_hist(ctx, p):
    f = ctx.bars(p["fast_min"])
    s = max(f + 1, int(round(f * p["slow_ratio"])))
    g = max(2, int(round(f * 0.75)))
    macd = ctx.ema(ctx.c, f) - ctx.ema(ctx.c, s)
    sig = ctx.ema(macd, g)
    hist = macd - sig
    with np.errstate(all="ignore"):
        return _out(ctx, hist > 0, hist < 0)


def _ha(ctx):
    def build():
        o, h, l, c, d = ctx.o, ctx.h, ctx.l, ctx.c, ctx.day
        hac = (o + h + l + c) / 4.0
        hao = np.empty(len(c))
        for i in range(len(c)):
            if i == 0 or d[i] != d[i - 1]:
                hao[i] = (o[i] + c[i]) / 2.0
            else:
                hao[i] = (hao[i - 1] + hac[i - 1]) / 2.0
        return hac, hao
    return ctx.cached("ha", build)


def _ha_flip(ctx, p):
    n = int(p["n"])
    hac, hao = _ha(ctx)
    green = (hac > hao).astype(float)
    red = (hac < hao).astype(float)
    was_red = ctx.roll(red, n, "min", include_current=False) == 1
    was_green = ctx.roll(green, n, "min", include_current=False) == 1
    long = was_red & (green == 1)
    short = was_green & (red == 1)
    return long.astype(int) - short.astype(int)


def _donchian_mid(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    hi = ctx.roll(ctx.h, nb, "max")
    lo = ctx.roll(ctx.l, nb, "min")
    mid = (hi + lo) / 2.0
    with np.errstate(all="ignore"):
        return _out(ctx, ctx.c > mid, ctx.c < mid)


def _range_mid_cross(ctx, p):
    frac = p["min_range_frac"]
    sh, sl = ctx.session_high(True), ctx.session_low(True)
    mid = (sh + sl) / 2.0
    ok = (ctx.bar_in_day >= ctx.bars(60)) & ((sh - sl) / ctx.day_open >= frac)
    with np.errstate(all="ignore"):
        return _out(ctx, ok & (ctx.c > mid), ok & (ctx.c < mid))


def _vol_burst(ctx, p):
    ns = ctx.bars(p["short_min"])
    nl = 4 * ns
    r = p["ratio"]
    d = ctx.c - ctx.prev(ctx.c, 1)
    sd_s = ctx.roll(d, ns, "std")
    sd_l = ctx.roll(d, nl, "std")
    move = ctx.c - ctx.prev(ctx.c, ns)
    with np.errstate(all="ignore"):
        burst = (sd_s > r * sd_l) & (sd_l > 0)
        return _out(ctx, burst & (move > 0), burst & (move < 0))


def _vol_ladder(ctx, p):
    n, k = int(p["n"]), p["vol_k"]
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    up = np.ones(ctx.n, bool)
    dn = np.ones(ctx.n, bool)
    rv = np.ones(ctx.n, bool)
    with np.errstate(all="ignore"):
        for i in range(n):
            up &= ctx.prev(ctx.c, i) > ctx.prev(ctx.c, i + 1)
            dn &= ctx.prev(ctx.c, i) < ctx.prev(ctx.c, i + 1)
            rv &= ctx.prev(ctx.v, i) > ctx.prev(ctx.v, i + 1)
        rv &= ctx.v > k * med
        return _out(ctx, up & rv, dn & rv)


def _body_thrust(ctx, p):
    nb, k = ctx.bars(p["lookback_min"]), p["k"]
    body = np.abs(ctx.c - ctx.o)
    mb = ctx.roll(body, max(2, nb), "mean", include_current=False)
    hi3 = ctx.roll(ctx.h, 3, "max", include_current=False)
    lo3 = ctx.roll(ctx.l, 3, "min", include_current=False)
    with np.errstate(all="ignore"):
        big = body > k * mb
        return _out(ctx, big & (ctx.c > ctx.o) & (ctx.c > hi3), big & (ctx.c < ctx.o) & (ctx.c < lo3))


def _tenkan_kijun(ctx, p):
    nt = ctx.bars(p["tenkan_min"])
    nk = 3 * nt
    ten = (ctx.roll(ctx.h, nt, "max") + ctx.roll(ctx.l, nt, "min")) / 2.0
    kij = (ctx.roll(ctx.h, nk, "max") + ctx.roll(ctx.l, nk, "min")) / 2.0
    with np.errstate(all="ignore"):
        return _out(ctx, ten > kij, ten < kij)


def _ladder_lows(ctx, p):
    k = int(p["k"])
    ema = ctx.cached(("ema30",), lambda: ctx.ema(ctx.c, ctx.bars(30)))
    up = np.ones(ctx.n, bool)
    dn = np.ones(ctx.n, bool)
    with np.errstate(all="ignore"):
        for i in range(k):
            up &= ctx.prev(ctx.l, i) > ctx.prev(ctx.l, i + 1)
            dn &= ctx.prev(ctx.h, i) < ctx.prev(ctx.h, i + 1)
        return _out(ctx, up & (ctx.c > ema), dn & (ctx.c < ema))


FAMILIES = [
    Family("E-948", "Stochastic %K re-entry fade",
           "Price closing back out of the bottom/top of its recent range band is where short-term sellers/buyers "
           "have exhausted; the mean-reverting flow of the next minutes fades the extreme.",
           {"lookback_min": [30, 60, 90], "th": [10, 20]}, _stoch_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-949", "MACD histogram zero-cross follow",
           "A turn of momentum acceleration (MACD histogram sign change) shows participants leaning the same way; "
           "later traders chase it.",
           {"fast_min": [10, 20, 30], "slow_ratio": [2.0, 2.6]}, _macd_hist, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-950", "Heikin-Ashi colour flip after a run",
           "A smoothed candle changing colour after several opposite ones marks the end of the pullback leg and "
           "the resumption of the new direction.",
           {"n": [3, 4, 5]}, _ha_flip, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-951", "Donchian midline cross follow",
           "The midpoint of the recent high-low channel is the price accepted by both sides; a close across it "
           "shifts value and the flow continues.",
           {"lookback_min": [30, 60, 90]}, _donchian_mid, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-952", "Developed day-range midpoint cross follow",
           "After a day range has developed, the midpoint separates buyer from seller control; crossing it "
           "brings late trend-followers.",
           {"min_range_frac": [0.003, 0.005, 0.008]}, _range_mid_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-953", "Realized-volatility burst follow",
           "When short-window realized volatility jumps well above the longer window, information has arrived "
           "and the direction of the burst keeps going for a while.",
           {"short_min": [10, 15, 20], "ratio": [1.5, 2.0, 2.5]}, _vol_burst, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-954", "Rising-volume close ladder follow",
           "Consecutive higher closes with each bar trading more volume than the last mean growing participation "
           "in one direction, not a drift on thinning interest.",
           {"n": [2, 3, 4], "vol_k": [0.8, 1.2]}, _vol_ladder, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-955", "Body-expansion thrust follow",
           "A bar body several times the recent average that also closes beyond the last three bars shows "
           "aggressive orders sweeping the book; follow-through.",
           {"lookback_min": [10, 20], "k": [2.0, 3.0]}, _body_thrust, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-956", "Tenkan/Kijun channel-mid cross follow",
           "The fast channel midpoint crossing the slow one is a trend-change signal many chartists share.",
           {"tenkan_min": [10, 15, 20, 30]}, _tenkan_kijun, markets=("WIN",),
           source="Ichimoku conventions, assistant reasoning", author="agent"),
    Family("E-957", "Rising-lows ladder above the EMA",
           "A staircase of higher lows while above the 30-minute EMA means dips are bought each time; the "
           "buyers' bids keep stepping up.",
           {"k": [3, 4, 5]}, _ladder_lows, markets=("WIN",), source="assistant reasoning", author="agent"),
]
