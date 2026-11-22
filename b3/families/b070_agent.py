"""Conveyor batch B-070 (agent, 2026-11-22). Mostly fades of stretched or exhausted moves, scaled by same-minute typical sizes."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _sgn(long, short):
    return long.astype(int) - short.astype(int)


def _fade_cross(ctx, up, dn):
    """up: stretched upward -> short; dn: stretched downward -> long. One signal per onset."""
    return _sgn(ctx.cross(dn), ctx.cross(up))


def _vol_decay_run(ctx, p):
    n = int(p["run"])
    pv = ctx.prev(ctx.v, 1)
    lowv = ctx.v < pv
    up = ctx.roll(((ctx.c > ctx.o) & lowv).astype(float), n, "sum") == n
    dn = ctx.roll(((ctx.c < ctx.o) & lowv).astype(float), n, "sum") == n
    return _fade_cross(ctx, up, dn)


def _open_extension(ctx, p):
    k = p["k"]
    r = ctx.c / ctx.day_open - 1.0
    typ = ctx.cached("abs_r_sm", lambda: ctx.same_minute(np.abs(r), "mean"))
    ok = typ > 0
    return _fade_cross(ctx, ok & (r > k * typ), ok & (r < -k * typ))


def _squeeze_false_release(ctx, p):
    nb, mb, m = ctx.bars(30), ctx.bars(p["memory_min"]), p["mult"]
    mean = ctx.roll(ctx.c, nb, "mean")
    sd = ctx.roll(ctx.c, nb, "std")
    wmin = ctx.roll(sd, mb, "min")
    squeezed = ctx.prev(sd, 1) <= 1.1 * ctx.prev(wmin, 1)
    up = squeezed & (ctx.c > mean + m * sd) & (sd > 0)
    dn = squeezed & (ctx.c < mean - m * sd) & (sd > 0)
    return _fade_cross(ctx, up, dn)


def _lunch_vwap_fade(ctx, p):
    k = p["k"]
    vw = ctx.vwap()
    dev = (ctx.c - vw) / vw
    typ = ctx.cached("abs_dev_sm", lambda: ctx.same_minute(np.abs(dev), "mean"))
    lunch = (ctx.minute >= 12 * 60) & (ctx.minute < 14 * 60 + 30)
    ok = lunch & (typ > 0)
    return _fade_cross(ctx, ok & (dev > k * typ), ok & (dev < -k * typ))


def _extension_rollover(ctx, p):
    k, f = p["k"], p["retrace"]
    pc = ctx.prev_session_value("close")
    e = ctx.c / pc - 1.0
    typ = ctx.cached("abs_e_ps", lambda: ctx.prev_sessions(np.abs(e), "mean"))
    g = pd.Series(e).groupby(ctx.day)
    emax = g.cummax().to_numpy()
    emin = g.cummin().to_numpy()
    short = (emax >= k * typ) & (e <= (1 - f) * emax) & (emax > 0)
    long = (emin <= -k * typ) & (e >= (1 - f) * emin) & (emin < 0)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _ema_z_fade(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    d = ctx.c - ctx.ema(ctx.c, nb)
    sd = ctx.roll(d, nb, "std")
    z = d / np.where(sd > 0, sd, np.nan)
    return _fade_cross(ctx, z > k, z < -k)


def _morning_extreme_poke(ctx, p):
    end = int(p["morning_end_min"])
    morn = ctx.minute < end
    g = pd.DataFrame({"d": ctx.day, "h": np.where(morn, ctx.h, np.nan), "l": np.where(morn, ctx.l, np.nan)})
    mh = g.groupby("d")["h"].transform("max").to_numpy()
    ml = g.groupby("d")["l"].transform("min").to_numpy()
    aft = ctx.minute >= end + 60
    short = aft & (ctx.h > mh) & (ctx.c < mh)
    long = aft & (ctx.l < ml) & (ctx.c > ml)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _effort_no_result_break(ctx, p):
    m, r = int(p["rising"]), p["narrow"]
    rising = (ctx.v > ctx.prev(ctx.v, 1)).astype(float)
    ok = ctx.roll(rising, m, "sum", include_current=False) == m
    hh = ctx.roll(ctx.h, m, "max", include_current=False)
    ll = ctx.roll(ctx.l, m, "min", include_current=False)
    avg = ctx.roll(ctx.h - ctx.l, ctx.bars(30), "mean", include_current=False)
    narrow = (hh - ll) < r * avg
    base = ok & narrow
    return _sgn(ctx.cross(base & (ctx.c > hh)), ctx.cross(base & (ctx.c < ll)))


def _spike_fade(ctx, p):
    k = p["k"]
    ret = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    typ = ctx.cached("abs_ret_sm", lambda: ctx.same_minute(np.abs(ret), "mean"))
    ok = typ > 0
    return _fade_cross(ctx, ok & (ret > k * typ), ok & (ret < -k * typ))


def _hourly_vwap_fade(ctx, p):
    k, m = p["k"], int(p["min_into_hour"])
    key = ctx.day.astype(np.int64) * 24 + (ctx.minute // 60).astype(np.int64)
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    df = pd.DataFrame({"k": key, "pv": tp * ctx.v, "v": ctx.v})
    g = df.groupby("k")
    hv = (g["pv"].cumsum() / g["v"].cumsum().replace(0, np.nan)).to_numpy()
    dev = (ctx.c - hv) / hv
    typ = ctx.cached("abs_hdev_sm", lambda: ctx.same_minute(np.abs(np.nan_to_num(dev)), "mean"))
    ok = ((ctx.minute % 60) >= m) & (typ > 0)
    return _fade_cross(ctx, ok & (dev > k * typ), ok & (dev < -k * typ))


FAMILIES = [
    Family("E-698", "Volume-fading run fade",
           "A run of same-colour bars each on less volume than the one before is a push with no new participants; "
           "the other side absorbs it, so fade the run.",
           {"run": [3, 4, 5]}, _vol_decay_run, source="assistant reasoning", author="agent"),
    Family("E-699", "Day-open extension fade",
           "Distance from the session open beyond what is typical for that minute of day marks a stretched move "
           "that liquidity providers fade back toward the open.",
           {"k": [1.0, 1.5, 2.0]}, _open_extension, source="assistant reasoning", author="agent"),
    Family("E-700", "Squeeze false-release fade",
           "After a volatility squeeze, a first close outside the band is often a stop-run; fade it back inside.",
           {"memory_min": [30, 60, 90], "mult": [1.5, 2.0, 2.5]}, _squeeze_false_release, source="assistant reasoning",
           author="agent"),
    Family("E-701", "Lunch-hour VWAP stretch fade",
           "In the thin midday session stretches away from VWAP lack follow-through and revert as institutions "
           "benchmark to VWAP.",
           {"k": [1.0, 1.5, 2.0]}, _lunch_vwap_fade, source="assistant reasoning", author="agent"),
    Family("E-702", "Prior-close extension rollover",
           "After a big extension from yesterday's close, a retrace of a large part of it shows the late "
           "participants are trapped; follow the move back toward the prior close.",
           {"k": [1.0, 1.5, 2.0], "retrace": [0.3, 0.5, 0.7]}, _extension_rollover, source="assistant reasoning",
           author="agent"),
    Family("E-703", "EMA distance z-score fade",
           "A price far from its EMA in units of its own recent deviation is statistically stretched; fade back to the mean.",
           {"win_min": [20, 40, 60], "k": [2.0, 2.5, 3.0]}, _ema_z_fade, source="assistant reasoning", author="agent"),
    Family("E-704", "Morning extreme afternoon poke rejection",
           "The morning high/low is a level that resting orders defend; an afternoon poke beyond it that closes "
           "back inside is a failed breakout.",
           {"morning_end_min": [630, 660, 720]}, _morning_extreme_poke, source="assistant reasoning", author="agent"),
    Family("E-705", "Effort without result break",
           "Rising volume while price stays in a narrow range means a large player is working an order; the "
           "break of that range shows the direction of the size.",
           {"rising": [2, 3, 4], "narrow": [1.5, 2.0, 3.0]}, _effort_no_result_break, source="assistant reasoning",
           author="agent"),
    Family("E-706", "Same-minute spike fade",
           "A one-bar return many times larger than typical for that minute is usually a thin-book overshoot; "
           "fade it.",
           {"k": [2.5, 3.0, 4.0, 5.0]}, _spike_fade, source="assistant reasoning", author="agent"),
    Family("E-707", "Hourly VWAP stretch fade",
           "Traders and algos benchmark by clock hour; a price stretched from the current hour's VWAP late in the "
           "hour reverts as the hour rolls.",
           {"k": [1.5, 2.0, 2.5], "min_into_hour": [15, 30, 45]}, _hourly_vwap_fade, source="assistant reasoning",
           author="agent"),
]
