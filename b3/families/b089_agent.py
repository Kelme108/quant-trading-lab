"""Conveyor batch B-089 (agent, 2026-11-23). Mixed themes: compression breaks, acceleration, volume confirmation, clock-hour levels, extreme recency, shock windows."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _flag(x):
    return np.nan_to_num(np.asarray(x, float), nan=0.0) > 0


def _nr_break(ctx, p):
    n = int(p["n"])
    rng = ctx.h - ctx.l
    nr = ((rng <= ctx.roll(rng, n, "min")) & (rng > 0)).astype(float)
    was = _flag(ctx.prev(nr, 1))
    long = was & (ctx.c > ctx.prev(ctx.h, 1))
    short = was & (ctx.c < ctx.prev(ctx.l, 1))
    return long.astype(int) - short.astype(int)


def _accel(ctx, p):
    nb, k = ctx.bars(p["move_min"]), p["k"]
    r1 = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    r0 = ctx.prev(ctx.c, nb) / ctx.prev(ctx.c, 2 * nb) - 1.0
    typ = ctx.cached(("abs_r", nb), lambda: ctx.prev_sessions(np.abs(r1), "mean"))
    with np.errstate(invalid="ignore"):
        long = (r1 >= k * typ) & (r0 > 0) & (r1 > 2 * r0)
        short = (r1 <= -k * typ) & (r0 < 0) & (r1 < 2 * r0)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _hh_hl_run(ctx, p):
    n = int(p["n"])
    ph, pl = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    with np.errstate(invalid="ignore"):
        up = ((ctx.h > ph) & (ctx.l > pl)).astype(float)
        dn = ((ctx.h < ph) & (ctx.l < pl)).astype(float)
    long = ctx.roll(up, n, "sum") >= n
    short = ctx.roll(dn, n, "sum") >= n
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _spike_confirm(ctx, p):
    k = p["vol_k"]
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    with np.errstate(invalid="ignore"):
        spike = (ctx.v >= k * med).astype(float)
    sp = _flag(ctx.prev(spike, 1))
    pdir = ctx.prev(np.sign(ctx.c - ctx.o), 1)
    pc = ctx.prev(ctx.c, 1)
    long = sp & (np.nan_to_num(pdir) > 0) & (ctx.c > pc)
    short = sp & (np.nan_to_num(pdir) < 0) & (ctx.c < pc)
    return long.astype(int) - short.astype(int)


def _late_trend_high(ctx, p):
    nb, w = ctx.bars(p["lookback_min"]), p["window_min"]
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    late = ctx.minutes_to_close <= w
    with np.errstate(invalid="ignore"):
        long = late & (ctx.c > hi) & (ctx.c > ctx.day_open)
        short = late & (ctx.c < lo) & (ctx.c < ctx.day_open)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _prev_hour_break(ctx, p):
    b = p["buffer_frac"]
    d = pd.DataFrame({"d": ctx.day, "hr": (ctx.minute // 60).astype(int), "h": ctx.h, "l": ctx.l})
    agg = d.groupby(["d", "hr"]).agg(h=("h", "max"), l=("l", "min"))
    prev_h = agg["h"].groupby(level=0).shift(1)
    prev_l = agg["l"].groupby(level=0).shift(1)
    idx = pd.MultiIndex.from_arrays([d["d"].to_numpy(), d["hr"].to_numpy()])
    ph = prev_h.reindex(idx).to_numpy()
    pl = prev_l.reindex(idx).to_numpy()
    with np.errstate(invalid="ignore"):
        up = ctx.cross(ctx.c > ph * (1 + b))
        dn = ctx.cross(ctx.c < pl * (1 - b))
    return up.astype(int) - dn.astype(int)


def _volume_ramp(ctx, p):
    n = int(p["n"])
    pv = ctx.prev(ctx.v, 1)
    with np.errstate(invalid="ignore"):
        up = ((ctx.c > ctx.o) & (ctx.v > pv)).astype(float)
        dn = ((ctx.c < ctx.o) & (ctx.v > pv)).astype(float)
    long = ctx.roll(up, n, "sum") >= n
    short = ctx.roll(dn, n, "sum") >= n
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _disp_sigma(ctx, p):
    k = p["k"]
    r = ctx.c / ctx.day_open - 1.0
    typ = ctx.cached("abs_ret_same_minute", lambda: ctx.same_minute(np.abs(r), "mean"))
    typ = np.where(typ > 0, typ, np.nan)
    with np.errstate(invalid="ignore"):
        z = r / typ
        long = z >= k
        short = z <= -k
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _extreme_recency(ctx, p):
    mb, n = ctx.bars(p["gap_min"]), int(p["ema_bars"])
    ar = np.arange(ctx.n, dtype=float)
    new_hi = ctx.h >= ctx.session_high(include_current=True)
    new_lo = ctx.l <= ctx.session_low(include_current=True)
    hi_idx = pd.Series(np.where(new_hi, ar, np.nan)).groupby(ctx.day).ffill().to_numpy()
    lo_idx = pd.Series(np.where(new_lo, ar, np.nan)).groupby(ctx.day).ffill().to_numpy()
    since_hi, since_lo = ar - hi_idx, ar - lo_idx
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    with np.errstate(invalid="ignore"):
        long = (since_hi - since_lo >= mb) & (ctx.c > ema)
        short = (since_lo - since_hi >= mb) & (ctx.c < ema)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _shock_window(ctx, p):
    k = p["k"]
    rng = ctx.h - ctx.l
    med = ctx.cached("rng_med", lambda: ctx.same_minute(rng, "median"))
    win = (ctx.minute >= 10 * 60 + 30) & (ctx.minute < 12 * 60)
    with np.errstate(invalid="ignore"):
        shock = win & (rng >= k * med) & (med > 0)
        long = shock & (ctx.c > ctx.o) & (ctx.c >= ctx.l + 0.7 * rng)
        short = shock & (ctx.c < ctx.o) & (ctx.c <= ctx.h - 0.7 * rng)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-888", "Narrowest-range bar break",
           "A bar with the smallest range of the last n bars marks compression; the next close beyond its extreme releases stored orders in that direction.",
           {"n": [4, 6, 8]}, _nr_break, source="assistant reasoning", author="agent"),
    Family("E-889", "Return acceleration follow",
           "A move that is both large for the instrument and more than twice as fast as the previous equal window shows forced flow still arriving; follow it.",
           {"move_min": [5, 10, 15], "k": [0.5, 1.0, 1.5]}, _accel, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-890", "Higher-high higher-low run",
           "Several bars in a row that each raise both high and low (or lower both) show one-sided participation that has not met resistance; follow the onset.",
           {"n": [3, 4, 5]}, _hh_hl_run, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-891", "Volume spike confirmation follow",
           "After a bar with volume far above normal, a next close beyond the spike bar's close confirms the aggressor won; follow.",
           {"vol_k": [2.0, 3.0, 4.0]}, _spike_confirm, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-892", "Late-session trend-side new extreme",
           "In the final hour, fresh extremes in the direction of the day's drift come from institutions rebalancing into the close; follow.",
           {"lookback_min": [15, 30], "window_min": [60, 90]}, _late_trend_high, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-893", "Prior clock-hour range break",
           "The previous clock hour's high and low are levels watched by intraday traders; a close beyond them triggers stops and follow-through.",
           {"buffer_frac": [0.0, 0.0003, 0.0006]}, _prev_hour_break, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-894", "Rising-volume directional run",
           "Consecutive bars of the same colour each on more volume than the last show growing commitment, not exhaustion; follow the onset.",
           {"n": [2, 3, 4]}, _volume_ramp, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-895", "Day-displacement sigma cross follow",
           "When the day's move from the open exceeds a typical same-time move by k times, the day is trending and late participants chase it.",
           {"k": [1.0, 1.5, 2.0]}, _disp_sigma, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-896", "Extreme recency tilt follow",
           "If the session low is set much more recently than the session high, sellers gave up last; a close above a short EMA follows that tilt (and the reverse).",
           {"gap_min": [30, 60, 90], "ema_bars": [10, 20]}, _extreme_recency, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-897", "Equity-open window range shock follow",
           "Between 10:30 and 12:00 the US cash open brings foreign flow; a bar with a range far above normal and a strong close shows it, and the move continues.",
           {"k": [1.5, 2.0, 3.0]}, _shock_window, markets=("WIN",), source="assistant reasoning", author="agent"),
]
