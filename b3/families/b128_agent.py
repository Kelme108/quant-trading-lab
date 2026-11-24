"""Conveyor batch B-128 (agent, 2026-11-24). Mixed themes: cross-market lead, level reclaim, absorption, stretch fade,
end-of-day VWAP, lunch squeeze, thin-volume shocks, range midpoint, blow-off bars and chop-range fades."""
from __future__ import annotations

import numpy as np

from b3.esteira import Family


def _b(x):
    return np.asarray(x, bool)


def _dollar_lead(ctx, p):
    nb, k = ctx.bars(p["window_min"]), p["k"]
    oc = ctx.other_close()
    rx = oc / ctx.prev(oc, nb) - 1.0
    rs = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    tx = ctx.cached(("tx", nb), lambda: ctx.prev_sessions(np.abs(rx), "mean"))
    ts = ctx.cached(("ts", nb), lambda: ctx.prev_sessions(np.abs(rs), "mean"))
    long = (rx <= -k * tx) & (rs < 0.5 * ts)
    short = (rx >= k * tx) & (rs > -0.5 * ts)
    return ctx.cross(_b(long)).astype(int) - ctx.cross(_b(short)).astype(int)


def _day_open_reclaim(ctx, p):
    nb = ctx.bars(p["away_min"])
    below = (ctx.c < ctx.day_open).astype(float)
    above = (ctx.c > ctx.day_open).astype(float)
    was_b = ctx.roll(below, nb, "min", include_current=False) == 1
    was_a = ctx.roll(above, nb, "min", include_current=False) == 1
    up = was_b & (ctx.c > ctx.day_open)
    dn = was_a & (ctx.c < ctx.day_open)
    return up.astype(int) - dn.astype(int)


def _absorption_break(ctx, p):
    k, ratio = p["vol_k"], p["range_ratio"]
    rng = ctx.h - ctx.l
    medr = ctx.cached("medr", lambda: ctx.same_minute(rng, "median"))
    medv = ctx.cached("medv", lambda: ctx.same_minute(ctx.v, "median"))
    absorb = (ctx.v >= k * medv) & (rng <= ratio * medr) & (rng > 0)
    pa = ctx.prev(absorb.astype(float), 1) == 1
    long = pa & (ctx.c > ctx.prev(ctx.h, 1))
    short = pa & (ctx.c < ctx.prev(ctx.l, 1))
    return long.astype(int) - short.astype(int)


def _stretch_fade(ctx, p):
    n, k = ctx.bars(p["ema_min"]), p["k"]
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    atr = ctx.cached(("atr", n), lambda: ctx.roll(ctx.h - ctx.l, n, "mean"))
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.where(atr > 0, (ctx.c - ema) / atr, np.nan)
    pz = ctx.prev(z, 1)
    pc = ctx.prev(ctx.c, 1)
    short = (pz >= k) & (ctx.c < pc)
    long = (pz <= -k) & (ctx.c > pc)
    return long.astype(int) - short.astype(int)


def _eod_vwap_revert(ctx, p):
    k, start = p["k"], p["start_min"]
    vw = ctx.vwap()
    dev = ctx.c / vw - 1.0
    typ = ctx.cached("vwap_dev_typ", lambda: ctx.same_minute(np.abs(dev), "mean"))
    win = (ctx.minutes_to_close <= start) & (ctx.minutes_to_close >= 15)
    short = win & (dev >= k * typ)
    long = win & (dev <= -k * typ)
    return ctx.cross(_b(long)).astype(int) - ctx.cross(_b(short)).astype(int)


def _lunch_squeeze_break(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    hi = ctx.roll(ctx.h, n, "max")
    lo = ctx.roll(ctx.l, n, "min")
    rn = hi - lo
    typ = ctx.cached(("typr", n), lambda: ctx.same_minute(rn, "median"))
    sq = ctx.prev(rn, 1) < k * typ
    win = (ctx.minute >= 11 * 60 + 30) & (ctx.minute < 15 * 60)
    long = sq & win & (ctx.c > ctx.prev(hi, 1))
    short = sq & win & (ctx.c < ctx.prev(lo, 1))
    return ctx.cross(_b(long)).astype(int) - ctx.cross(_b(short)).astype(int)


def _thin_shock_fade(ctx, p):
    k, m = p["k"], p["vol_m"]
    nb = ctx.bars(60)
    ret = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    sd = ctx.roll(ret, nb, "std", include_current=False)
    med = ctx.cached("medv", lambda: ctx.same_minute(ctx.v, "median"))
    thin = ctx.v < m * med
    short = thin & (sd > 0) & (ret >= k * sd)
    long = thin & (sd > 0) & (ret <= -k * sd)
    return long.astype(int) - short.astype(int)


def _range_mid_cross(ctx, p):
    nb = ctx.bars(p["away_min"])
    mid = (ctx.session_high(include_current=True) + ctx.session_low(include_current=True)) / 2.0
    below = (ctx.c < mid).astype(float)
    above = (ctx.c > mid).astype(float)
    was_b = ctx.roll(below, nb, "min", include_current=False) == 1
    was_a = ctx.roll(above, nb, "min", include_current=False) == 1
    ok = ctx.bar_in_day >= ctx.bars(30)
    up = ok & was_b & (ctx.c > mid)
    dn = ok & was_a & (ctx.c < mid)
    return up.astype(int) - dn.astype(int)


def _blowoff_fade(ctx, p):
    n = ctx.bars(p["lookback_min"])
    r = ctx.h - ctx.l
    c1, c2 = ctx.prev(ctx.c, 1), ctx.prev(ctx.c, 2)
    r1, r2 = ctx.prev(r, 1), ctx.prev(r, 2)
    expand = (r > r1) & (r1 > r2)
    hi = ctx.roll(ctx.h, n, "max", include_current=False)
    lo = ctx.roll(ctx.l, n, "min", include_current=False)
    up = expand & (ctx.c > c1) & (c1 > c2) & (ctx.h > hi)
    dn = expand & (ctx.c < c1) & (c1 < c2) & (ctx.l < lo)
    return ctx.cross(_b(dn)).astype(int) - ctx.cross(_b(up)).astype(int)


def _chop_range_fade(ctx, p):
    n, er_max = ctx.bars(p["n_min"]), p["er_max"]
    net = np.abs(ctx.c - ctx.prev(ctx.c, n))
    path = ctx.roll(np.abs(ctx.c - ctx.prev(ctx.c, 1)), n, "sum")
    with np.errstate(divide="ignore", invalid="ignore"):
        er = np.where(path > 0, net / path, np.nan)
    hi = ctx.roll(ctx.h, n, "max", include_current=False)
    lo = ctx.roll(ctx.l, n, "min", include_current=False)
    chop = er <= er_max
    short = chop & (ctx.c > hi)
    long = chop & (ctx.c < lo)
    return ctx.cross(_b(long)).astype(int) - ctx.cross(_b(short)).astype(int)


FAMILIES = [
    Family("E-1278", "Dollar-lead catch-up",
           "A strong move of the dollar contract that the index has not yet matched is an inverse-correlation lag: "
           "arbitrageurs and macro desks transmit it to WIN within minutes; trade WIN in the implied direction.",
           {"window_min": [5, 10, 20], "k": [1.5, 2.0, 3.0]}, _dollar_lead, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1279", "Day-open reclaim",
           "After the price spent a while on one side of the session open, a close back across it shows the "
           "opening-auction participants flipping from trapped to in control; follow the cross.",
           {"away_min": [20, 40, 60]}, _day_open_reclaim, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1280", "Absorption bar break",
           "A bar with heavy volume but a small range means one side absorbed the other's orders; the next close "
           "beyond that bar's extreme shows which side was left holding.",
           {"vol_k": [1.5, 2.0, 3.0], "range_ratio": [0.4, 0.6, 0.8]}, _absorption_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1281", "ATR-stretch snap-back",
           "When the price is stretched several average bar-ranges from its EMA, the first bar that closes back toward "
           "it shows the chasers are exhausted; fade toward the mean.",
           {"ema_min": [30, 60], "k": [2.0, 2.5, 3.0]}, _stretch_fade, markets=("WIN",),
           source="assistant reasoning (Keltner-style stretch)", author="agent"),
    Family("E-1282", "Final-hour VWAP reversion",
           "In the last hour, institutional benchmark orders (VWAP) and position squaring pull the price toward the "
           "day's VWAP when it has strayed further than usual for that minute.",
           {"k": [1.5, 2.0, 2.5], "start_min": [45, 75, 105]}, _eod_vwap_revert, markets=("WIN",),
           source="assistant reasoning (VWAP benchmark execution)", author="agent"),
    Family("E-1283", "Lunch squeeze break",
           "A midday range much narrower than usual for the same time shows liquidity withdrawn; the first close "
           "beyond it is the side that commits when the afternoon flow arrives.",
           {"win_min": [15, 30, 45], "k": [0.6, 0.8, 1.0]}, _lunch_squeeze_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1284", "Thin-volume shock fade",
           "A bar return several standard deviations large but on below-normal volume is a small order moving a thin "
           "book, not information; the move tends to retrace.",
           {"k": [2.0, 2.5, 3.0], "vol_m": [0.8, 1.0, 1.5]}, _thin_shock_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1285", "Session-range midpoint cross",
           "The midpoint of the day's range is the balance level; after the price lived on one side of it, a close "
           "through it shows the other side taking over the day's auction.",
           {"away_min": [10, 20, 30]}, _range_mid_cross, markets=("WIN",), source="auction market theory (balance area)",
           author="agent"),
    Family("E-1286", "Expanding-bar blow-off fade",
           "Three consecutive closes in one direction with growing bar ranges that print a fresh extreme look like a "
           "climactic stop-run; fade it.",
           {"lookback_min": [20, 30, 60]}, _blowoff_fade, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1287", "Choppy-regime range fade",
           "When Kaufman's efficiency ratio is low the market is mean-reverting noise; a close beyond the recent "
           "range in such a regime is a false break and should be faded.",
           {"n_min": [30, 60], "er_max": [0.15, 0.25, 0.35]}, _chop_range_fade, markets=("WIN",),
           source="Kaufman efficiency ratio (assistant reasoning)", author="agent"),
]
