"""Conveyor batch B-104 (agent, 2026-11-24). Mixed themes: climax volume, range compression, cross-market lead,
round numbers, volume ramps, bands, squeeze release, low-participation highs, late-day carry, range midpoint."""
from __future__ import annotations

import numpy as np

from b3.esteira import Family


def _med_vol(ctx):
    return ctx.cached("vol_med20", lambda: ctx.same_minute(ctx.v, "median"))


def _d(long, short):
    return long.astype(int) - short.astype(int)


def _climax_fade(ctx, p):
    k, nb = p["vol_k"], ctx.bars(p["lookback_min"])
    rng = ctx.h - ctx.l
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    big = ctx.v > k * _med_vol(ctx)
    pos = np.where(rng > 0, (ctx.c - ctx.l) / np.where(rng > 0, rng, 1.0), 0.5)
    short = big & (ctx.h > hi) & (pos >= 0.8) & (ctx.c > ctx.o)
    long = big & (ctx.l < lo) & (pos <= 0.2) & (ctx.c < ctx.o)
    return _d(ctx.cross(long), ctx.cross(short))


def _nr_break(ctx, p):
    n = int(p["n"])
    rng = ctx.h - ctx.l
    rmin = ctx.roll(rng, n, "min")
    narrow = ctx.prev(rng, 1) <= ctx.prev(rmin, 1)
    long = narrow & (ctx.c > ctx.prev(ctx.h, 1))
    short = narrow & (ctx.c < ctx.prev(ctx.l, 1))
    return _d(long, short)


def _dollar_lead(ctx, p):
    nb, k = ctx.bars(p["move_min"]), p["k"]
    oc = ctx.other_close()
    rw = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    rd = oc / ctx.prev(oc, nb) - 1.0
    tw = ctx.cached(("tw", nb), lambda: ctx.prev_sessions(np.abs(rw), "mean"))
    td = ctx.cached(("td", nb), lambda: ctx.prev_sessions(np.abs(rd), "mean"))
    long = (rd <= -k * td) & (rw < 0.5 * tw)
    short = (rd >= k * td) & (rw > -0.5 * tw)
    return _d(ctx.cross(long), ctx.cross(short))


def _round_number(ctx, p):
    step = float(p["step_pts"])
    pc = ctx.prev(ctx.c, 1)
    up_lvl = np.ceil(pc / step) * step
    dn_lvl = np.floor(pc / step) * step
    short = (ctx.h >= up_lvl) & (ctx.c < up_lvl)
    long = (ctx.l <= dn_lvl) & (ctx.c > dn_lvl)
    return _d(long, short)


def _volume_ramp(ctx, p):
    n, k = int(p["ramp_bars"]), p["vol_k"]
    upc = (ctx.c > ctx.prev(ctx.c, 1)).astype(float)
    dnc = (ctx.c < ctx.prev(ctx.c, 1)).astype(float)
    vup = (ctx.v > ctx.prev(ctx.v, 1)).astype(float)
    big = ctx.v > k * _med_vol(ctx)
    long = (ctx.roll(upc * vup, n, "min") == 1) & big
    short = (ctx.roll(dnc * vup, n, "min") == 1) & big
    return _d(ctx.cross(long), ctx.cross(short))


def _band_reentry(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    m = ctx.roll(ctx.c, nb, "mean")
    sd = ctx.roll(ctx.c, nb, "std")
    lo, hi = m - k * sd, m + k * sd
    pc = ctx.prev(ctx.c, 1)
    long = (pc < ctx.prev(lo, 1)) & (ctx.c > lo)
    short = (pc > ctx.prev(hi, 1)) & (ctx.c < hi)
    return _d(long, short)


def _squeeze_release(ctx, p):
    q, k = p["q"], p["k"]
    nb = ctx.bars(30)
    r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    sd = ctx.roll(r, max(nb, 3), "std")
    typ = ctx.cached(("sd_typ", nb), lambda: ctx.same_minute(np.nan_to_num(sd, nan=0.0), "median"))
    squeeze = (ctx.prev(sd, 1) < q * ctx.prev(typ, 1)) & (ctx.prev(sd, 1) > 0)
    blast = np.abs(r) > k * ctx.prev(sd, 1)
    return np.where(squeeze & blast & (r > 0), 1, 0) - np.where(squeeze & blast & (r < 0), 1, 0)


def _dry_high_fade(ctx, p):
    k = p["vol_k"]
    sh = ctx.session_high(include_current=False)
    sl = ctx.session_low(include_current=False)
    quiet = ctx.v < k * _med_vol(ctx)
    ok = ctx.bar_in_day >= ctx.bars(30)
    short = ok & quiet & (ctx.h > sh) & (ctx.c < ctx.o)
    long = ok & quiet & (ctx.l < sl) & (ctx.c > ctx.o)
    return _d(long, short)


def _late_carry(ctx, p):
    m, nb = p["last_min"], ctx.bars(p["ema_min"])
    ema = ctx.cached(("ema_l", nb), lambda: ctx.ema(ctx.c, nb))
    late = ctx.minutes_to_close <= m
    long = late & (ctx.c > ctx.day_open) & (ctx.c > ema)
    short = late & (ctx.c < ctx.day_open) & (ctx.c < ema)
    return _d(ctx.cross(long), ctx.cross(short))


def _midpoint_hold(ctx, p):
    nb = ctx.bars(p["hold_min"])
    mid = (ctx.session_high(include_current=True) + ctx.session_low(include_current=True)) / 2.0
    ok = ctx.bar_in_day >= ctx.bars(60)
    above = (ctx.c > mid).astype(float)
    below = (ctx.c < mid).astype(float)
    long = ok & (ctx.roll(above, nb, "min") == 1)
    short = ok & (ctx.roll(below, nb, "min") == 1)
    return _d(ctx.cross(long), ctx.cross(short))


FAMILIES = [
    Family("E-1038", "Volume-climax bar at a fresh extreme fade",
           "A bar with several times the usual volume that pokes to a new range extreme and closes at its end is "
           "late aggressive flow exhausting itself; the other side absorbs it and price snaps back.",
           {"vol_k": [2.0, 3.0, 4.0], "lookback_min": [20, 30, 60]}, _climax_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1039", "Narrowest-bar break",
           "A bar with the smallest range of the last n bars shows a pause in order flow; the first close beyond its "
           "high/low is where waiting orders resolve.",
           {"n": [5, 8, 12]}, _nr_break, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1040", "Dollar-lead catch-up",
           "The index and the dollar move inversely; when the dollar moves sharply and the index has not yet "
           "responded, arbitrage and macro flow pull the index the other way.",
           {"move_min": [5, 10, 20], "k": [1.0, 1.5, 2.0]}, _dollar_lead, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1041", "Round-number rejection",
           "Round index levels hold clustered resting orders; a bar that touches the next round number and closes "
           "back under it (or the one below and closes over) is fading into that liquidity.",
           {"step_pts": [250, 500, 1000]}, _round_number, markets=("WIN",), source="assistant reasoning",
           author="agent"),
    Family("E-1042", "Volume-ramp run follow",
           "Consecutive closes in one direction, each on more volume than the last and above the usual size, mean "
           "participation is growing with the move; follow it.",
           {"ramp_bars": [2, 3, 4], "vol_k": [0.8, 1.2, 1.6]}, _volume_ramp, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1043", "Bollinger band re-entry fade",
           "A close outside a k-sigma band followed by a close back inside signals an overextension that has lost "
           "its push; trade back toward the mean.",
           {"win_min": [20, 30, 60], "k": [2.0, 2.5, 3.0]}, _band_reentry, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1044", "Squeeze release follow",
           "After volatility falls well below its usual level for the hour, the first bar that is large relative "
           "to that quiet marks stops and new orders being hit together; follow it.",
           {"q": [0.5, 0.7], "k": [1.5, 2.0, 3.0]}, _squeeze_release, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1045", "Low-participation new extreme fade",
           "A new session high or low printed on well below normal volume and closed against its direction lacks "
           "real buyers or sellers behind it; fade it.",
           {"vol_k": [0.5, 0.75, 1.0]}, _dry_high_fade, markets=("WIN",), source="assistant reasoning",
           author="agent"),
    Family("E-1046", "Late-day trend carry",
           "In the last hours, institutions and day traders reduce risk in the direction of the day's drift; a "
           "reclaim of a short EMA on the day's side is a continuation entry.",
           {"last_min": [60, 90, 120], "ema_min": [10, 20, 30]}, _late_carry, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1047", "Session-range midpoint hold",
           "Once the day's range is built, holding on one side of its midpoint for a while shows that side controls "
           "the balance; follow the first confirmation.",
           {"hold_min": [10, 20, 30]}, _midpoint_hold, markets=("WIN",), source="assistant reasoning",
           author="agent"),
]
