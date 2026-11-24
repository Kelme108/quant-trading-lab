"""Conveyor batch B-075 (agent, 2026-11-23). Mixed themes: cross-market lead, yesterday-same-minute, compression, regimes."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _dollar_lead(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    oc = ctx.other_close()
    rw = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    rd = oc / ctx.prev(oc, nb) - 1.0
    typ = ctx.cached(("typ_rd", nb), lambda: ctx.prev_sessions(np.abs(rd), "mean"))
    long = (rd <= -k * typ) & (rw < -0.5 * rd)
    short = (rd >= k * typ) & (rw > -0.5 * rd)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _yday_minute_cross(ctx, p):
    nb = ctx.bars(p["away_min"])
    y = ctx.cached("yday_c", lambda: ctx.same_minute(ctx.c, "mean", n=1))
    below = (ctx.c < y).astype(float)
    above = (ctx.c > y).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    up = was_below & (ctx.c > y)
    dn = was_above & (ctx.c < y)
    return up.astype(int) - dn.astype(int)


def _compression_break(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    sd = ctx.roll(r, nb, "std")
    typ = ctx.cached(("typ_sd", nb), lambda: ctx.prev_sessions(np.nan_to_num(sd, nan=0.0), "mean"))
    comp = (sd < k * typ) & (typ > 0)
    comp_prev = ctx.prev(comp.astype(float), 1) == 1
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    long = comp_prev & (ctx.c > hi)
    short = comp_prev & (ctx.c < lo)
    return long.astype(int) - short.astype(int)


def _shock_follow(ctx, p):
    k, bf = p["k"], p["body_frac"]
    rng = ctx.h - ctx.l
    med = ctx.cached("rng_med", lambda: ctx.same_minute(rng, "median"))
    body = np.abs(ctx.c - ctx.o)
    shock = (rng > k * med) & (rng > 0) & (body >= bf * rng)
    sh1 = ctx.prev(shock.astype(float), 1) == 1
    bull1 = ctx.prev((ctx.c > ctx.o).astype(float), 1) == 1
    bear1 = ctx.prev((ctx.c < ctx.o).astype(float), 1) == 1
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    long = sh1 & bull1 & (ctx.c > h1)
    short = sh1 & bear1 & (ctx.c < l1)
    return long.astype(int) - short.astype(int)


def _final_hour_open_cross(ctx, p):
    w, b = p["w_min"], p["buf"]
    late = ctx.minutes_to_close <= w
    up = late & (ctx.c > ctx.day_open * (1 + b))
    dn = late & (ctx.c < ctx.day_open * (1 - b))
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _vwap_band_fade(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    dev = ctx.c - ctx.vwap()
    sd = ctx.roll(dev, nb, "std")
    dev1, sd1 = ctx.prev(dev, 1), ctx.prev(sd, 1)
    short = (dev1 > k * sd1) & (dev <= k * sd)
    long = (dev1 < -k * sd1) & (dev >= -k * sd)
    return long.astype(int) - short.astype(int)


def _double_marubozu(ctx, p):
    f = p["body_frac"]
    rng = ctx.h - ctx.l
    body = np.abs(ctx.c - ctx.o)
    maru = (rng > 0) & (body >= f * rng)
    bull = maru & (ctx.c > ctx.o)
    bear = maru & (ctx.c < ctx.o)
    b1 = ctx.prev(bull.astype(float), 1) == 1
    s1 = ctx.prev(bear.astype(float), 1) == 1
    return ctx.cross(bull & b1).astype(int) - ctx.cross(bear & s1).astype(int)


def _absorption_fade(ctx, p):
    vk, rk = p["vol_k"], p["rng_k"]
    nb = ctx.bars(30)
    rng = ctx.h - ctx.l
    vmed = ctx.cached("v_med", lambda: ctx.same_minute(ctx.v, "median"))
    rmed = ctx.cached("rng_med", lambda: ctx.same_minute(rng, "median"))
    hi = ctx.roll(ctx.h, nb, "max")
    lo = ctx.roll(ctx.l, nb, "min")
    pos = (ctx.c - lo) / np.where(hi > lo, hi - lo, np.nan)
    absorb = (ctx.v > vk * vmed) & (rng < rk * rmed)
    short = absorb & (pos > 0.8)
    long = absorb & (pos < 0.2)
    return long.astype(int) - short.astype(int)


def _autocorr_regime(ctx, p):
    nb, th, k = ctx.bars(p["win_min"]), p["th"], p["k"]
    r = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    prod = r * ctx.prev(r, 1)
    ac = ctx.roll(prod, nb, "mean") / ctx.roll(r * r, nb, "mean")
    sd = ctx.roll(r, nb, "std")
    big = np.abs(r) >= k * sd
    sg = np.sign(r)
    fade = (ac < -th) & big
    follow = (ac > th) & big
    long = (fade & (sg < 0)) | (follow & (sg > 0))
    short = (fade & (sg > 0)) | (follow & (sg < 0))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _weak_volume_extreme(ctx, p):
    vk, age = p["vol_k"], ctx.bars(p["min_age_min"])
    avg = ctx.roll(ctx.v, ctx.bars(20), "mean", include_current=False)
    old = ctx.bar_in_day >= age
    sh, sl = ctx.session_high(), ctx.session_low()
    short = old & (ctx.h > sh) & (ctx.v < vk * avg)
    long = old & (ctx.l < sl) & (ctx.v < vk * avg)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-748", "Dollar-led index catch-up",
           "WDO and WIN are inversely linked; when the dollar makes an unusual move and the index has not yet "
           "responded by half, slower index participants catch up in the opposite direction.",
           {"win_min": [5, 10, 15], "k": [1.0, 1.5, 2.0]}, _dollar_lead, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-749", "Yesterday same-minute price cross",
           "Participants anchor on where price stood at the same time yesterday; after a stretch on one side, "
           "crossing that level shifts the day's bias.",
           {"away_min": [15, 30, 60]}, _yday_minute_cross, source="assistant reasoning", author="agent"),
    Family("E-750", "Volatility compression range break",
           "When bar-to-bar volatility falls well below its recent norm, stops pile up around the small range; "
           "the first close beyond it releases the energy.",
           {"win_min": [15, 30, 45], "k": [0.5, 0.7, 0.85]}, _compression_break, source="assistant reasoning",
           author="agent"),
    Family("E-751", "Shock-bar extreme follow-through",
           "After a wide-range full-body bar, a next close beyond its extreme shows no one absorbed the move; "
           "late traders chase.",
           {"k": [1.5, 2.0, 3.0], "body_frac": [0.5, 0.7]}, _shock_follow, source="assistant reasoning",
           author="agent"),
    Family("E-752", "Late-session day-open cross",
           "In the last hour, a close crossing the day's open decides the winners and losers of the day; "
           "position squaring pushes price the same way into the close.",
           {"w_min": [60, 90, 120], "buf": [0.0, 0.0005, 0.001]}, _final_hour_open_cross,
           source="assistant reasoning", author="agent"),
    Family("E-753", "VWAP sigma-band re-entry fade",
           "A stretch beyond a deviation band around VWAP draws in value buyers; the first close back inside the "
           "band means the push is exhausted, so trade back toward VWAP.",
           {"win_min": [30, 60, 90], "k": [1.5, 2.0, 2.5]}, _vwap_band_fade, source="assistant reasoning",
           author="agent"),
    Family("E-754", "Double marubozu follow",
           "Two consecutive almost wickless bars the same way show an aggressor taking liquidity at every price; "
           "the move continues for a while.",
           {"body_frac": [0.7, 0.8, 0.9]}, _double_marubozu, source="assistant reasoning", author="agent"),
    Family("E-755", "Absorption at the range edge",
           "Heavy volume with little range at the edge of the last half hour means passive orders absorbed the "
           "aggressors; fade back into the range.",
           {"vol_k": [1.5, 2.0, 3.0], "rng_k": [0.5, 0.75]}, _absorption_fade, source="assistant reasoning",
           author="agent"),
    Family("E-756", "Autocorrelation regime switch",
           "When recent returns are negatively autocorrelated (noise from liquidity takers) a big bar is faded; "
           "when positively autocorrelated (herding) it is followed.",
           {"win_min": [30, 60], "th": [0.1, 0.2], "k": [1.0, 1.5]}, _autocorr_regime,
           source="assistant reasoning", author="agent"),
    Family("E-757", "Weak-volume new extreme fade",
           "A new session high or low made on below-average volume lacks participation; it is a probe that "
           "tends to retrace.",
           {"vol_k": [0.5, 0.7, 0.9], "min_age_min": [30, 60]}, _weak_volume_extreme,
           source="assistant reasoning", author="agent"),
]
