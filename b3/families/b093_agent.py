"""Conveyor batch B-093 (agent, 2026-11-24). Mixed bar-shape, volume, block and rolling-VWAP ideas on WIN/WDO."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _loc(ctx):
    rng = ctx.h - ctx.l
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(rng > 0, (ctx.c - ctx.l) / rng, 0.5)


def _confirmed_pin(ctx, p):
    w, k = p["wick_frac"], p["range_k"]
    rng = ctx.h - ctx.l
    avg = ctx.roll(rng, 20, "mean", include_current=False)
    with np.errstate(divide="ignore", invalid="ignore"):
        wl = np.where(rng > 0, (np.minimum(ctx.o, ctx.c) - ctx.l) / rng, 0.0)
        wu = np.where(rng > 0, (ctx.h - np.maximum(ctx.o, ctx.c)) / rng, 0.0)
    pin_l = ((wl >= w) & (rng >= k * avg)).astype(float)
    pin_h = ((wu >= w) & (rng >= k * avg)).astype(float)
    long = (ctx.prev(pin_l, 1) == 1) & (ctx.c > ctx.prev(ctx.h, 1))
    short = (ctx.prev(pin_h, 1) == 1) & (ctx.c < ctx.prev(ctx.l, 1))
    return long.astype(int) - short.astype(int)


def _thin_move_fade(ctx, p):
    k, vf = p["range_k"], p["vol_frac"]
    rng = ctx.h - ctx.l
    avg = ctx.roll(rng, 20, "mean", include_current=False)
    vavg = ctx.roll(ctx.v, 20, "mean", include_current=False)
    thin_big = (rng >= k * avg) & (ctx.v < vf * vavg)
    long = thin_big & (ctx.c < ctx.o)
    short = thin_big & (ctx.c > ctx.o)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _close_loc_persist(ctx, p):
    n = int(p["n_bars"])
    loc = _loc(ctx)
    up = (loc >= p["loc_th"]).astype(float)
    dn = (loc <= 1 - p["loc_th"]).astype(float)
    long = ctx.roll(up, n, "min") == 1
    short = ctx.roll(dn, n, "min") == 1
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _rising_vwap_touch(ctx, p):
    nb, tol = ctx.bars(p["slope_min"]), p["tol"]
    vw = ctx.vwap()
    rising = vw > ctx.prev(vw, nb)
    falling = vw < ctx.prev(vw, nb)
    long = rising & (ctx.l <= vw * (1 + tol)) & (ctx.c > vw)
    short = falling & (ctx.h >= vw * (1 - tol)) & (ctx.c < vw)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _rolling_vwap_cross(ctx, p):
    nb, b = ctx.bars(p["win_min"]), p["buffer_frac"]
    pv = ctx.roll(ctx.c * ctx.v, nb, "sum")
    vv = ctx.roll(ctx.v, nb, "sum")
    with np.errstate(divide="ignore", invalid="ignore"):
        rv = np.where(vv > 0, pv / vv, np.nan)
    long = ctx.c > rv * (1 + b)
    short = ctx.c < rv * (1 - b)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _shrinking_range_break(ctx, p):
    n, nb = int(p["n_shrink"]), ctx.bars(p["ema_min"])
    rng = ctx.h - ctx.l
    dec = (rng < ctx.prev(rng, 1)).astype(float)
    run = (ctx.roll(dec, n, "min") == 1).astype(float)
    ema = ctx.ema(ctx.c, max(2, nb))
    pr = ctx.prev(run, 1) == 1
    long = pr & (ctx.c > ctx.prev(ctx.h, 1)) & (ctx.c > ema)
    short = pr & (ctx.c < ctx.prev(ctx.l, 1)) & (ctx.c < ema)
    return long.astype(int) - short.astype(int)


def _selling_climax(ctx, p):
    nb, k = ctx.bars(p["lookback_min"]), p["vol_k"]
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    vavg = ctx.roll(ctx.v, 20, "mean", include_current=False)
    mid = (ctx.h + ctx.l) / 2
    heavy = ctx.v >= k * vavg
    long = (ctx.l < lo) & heavy & (ctx.c > mid)
    short = (ctx.h > hi) & heavy & (ctx.c < mid)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _block_candle_follow(ctx, p):
    blk, f = int(p["block_min"]), p["body_frac"]
    key = ctx.day.astype(np.int64) * 10000 + (ctx.minute // blk)
    df = pd.DataFrame({"k": key, "o": ctx.o, "h": ctx.h, "l": ctx.l})
    g = df.groupby("k")
    bo = g["o"].transform("first").to_numpy()
    bh = g["h"].cummax().to_numpy()
    bl = g["l"].cummin().to_numpy()
    last = ((ctx.minute + ctx.tf) % blk) == 0
    body = np.abs(ctx.c - bo)
    rng = bh - bl
    strong = (rng > 0) & (body >= f * rng)
    long = last & strong & (ctx.c > bo)
    short = last & strong & (ctx.c < bo)
    return long.astype(int) - short.astype(int)


def _late_volume_break(ctx, p):
    k, mtc = p["vol_k"], p["late_min"]
    med = ctx.cached("vol_med_b093", lambda: ctx.same_minute(ctx.v, "median"))
    late = ctx.minutes_to_close <= mtc
    heavy = ctx.v >= k * med
    long = late & heavy & (ctx.c > ctx.prev(ctx.h, 1))
    short = late & heavy & (ctx.c < ctx.prev(ctx.l, 1))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _close_channel_break(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["vol_k"]
    mx = ctx.roll(ctx.c, nb, "max", include_current=False)
    mn = ctx.roll(ctx.c, nb, "min", include_current=False)
    vavg = ctx.roll(ctx.v, 20, "mean", include_current=False)
    ok = ctx.v >= k * vavg
    long = (ctx.c > mx) & ok
    short = (ctx.c < mn) & ok
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _stale_wide_bar_reversal(ctx, p):
    """Bar closing in its own opposite third after the prior bar closed at an N-bar extreme."""
    nb = ctx.bars(p["lookback_min"])
    hi = ctx.roll(ctx.c, nb, "max")
    lo = ctx.roll(ctx.c, nb, "min")
    at_hi = ctx.prev((ctx.c >= hi).astype(float), 1) == 1
    at_lo = ctx.prev((ctx.c <= lo).astype(float), 1) == 1
    loc = _loc(ctx)
    th = p["loc_th"]
    short = at_hi & (loc <= th) & (ctx.c < ctx.o)
    long = at_lo & (loc >= 1 - th) & (ctx.c > ctx.o)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-928", "Confirmed pin bar",
           "A long-wick rejection bar shows one side absorbed; waiting for the next bar to close beyond the pin's "
           "extreme filters out unconfirmed wicks and trades with the trapped side's exit.",
           {"wick_frac": [0.5, 0.6, 0.7], "range_k": [1.0, 1.5]}, _confirmed_pin,
           source="assistant reasoning", author="agent"),
    Family("E-929", "Thin-volume wide bar fade",
           "A wide bar on below-average volume is a move without participation (a sweep of thin liquidity); "
           "price tends to give it back.",
           {"range_k": [1.5, 2.0, 2.5], "vol_frac": [0.7, 1.0]}, _thin_move_fade,
           source="assistant reasoning", author="agent"),
    Family("E-930", "Close-location persistence",
           "Several consecutive bars closing near their highs (lows) reveal steady aggressive buying (selling) "
           "that keeps absorbing the offer; follow its onset.",
           {"n_bars": [3, 4, 5], "loc_th": [0.65, 0.75]}, _close_loc_persist,
           source="assistant reasoning", author="agent"),
    Family("E-931", "Sloped-VWAP touch bounce",
           "When session VWAP has been rising, institutional buyers benchmarked to it defend it; a touch that "
           "closes back above is a low-risk continuation (mirror for falling VWAP).",
           {"slope_min": [30, 60, 90], "tol": [0.0, 0.0003]}, _rising_vwap_touch,
           source="assistant reasoning", author="agent"),
    Family("E-932", "Rolling-VWAP cross",
           "A short-window volume-weighted average tracks the recent cost basis of active traders; a decisive "
           "close through it flips who is underwater.",
           {"win_min": [30, 60, 120], "buffer_frac": [0.0, 0.0005]}, _rolling_vwap_cross,
           source="assistant reasoning", author="agent"),
    Family("E-933", "Shrinking-range ladder break",
           "Successively smaller bars show sellers/buyers drying up; the first bar breaking the last bar's extreme "
           "in the EMA trend direction resumes the trend.",
           {"n_shrink": [2, 3, 4], "ema_min": [30, 60]}, _shrinking_range_break,
           source="assistant reasoning", author="agent"),
    Family("E-934", "Volume climax at a range extreme",
           "A heavy-volume push to a new N-minute extreme that closes back in the opposite half of its range is "
           "exhaustion: aggressive orders were absorbed by passive liquidity.",
           {"lookback_min": [30, 60], "vol_k": [1.5, 2.0, 3.0]}, _selling_climax,
           source="assistant reasoning", author="agent"),
    Family("E-935", "Strong block candle follow",
           "When a 15/30/60-minute block closes with a body filling most of its range, one side controlled "
           "the whole block; the next block tends to start in the same direction.",
           {"block_min": [15, 30, 60], "body_frac": [0.6, 0.75]}, _block_candle_follow,
           source="assistant reasoning", author="agent"),
    Family("E-936", "Late-session heavy-volume break",
           "Heavy volume breaking the prior bar's extreme near the close comes from position-squaring flows that "
           "are price-insensitive and keep pushing into the close.",
           {"vol_k": [1.5, 2.0, 3.0], "late_min": [60, 90]}, _late_volume_break,
           source="assistant reasoning", author="agent"),
    Family("E-937", "Close-only channel break on volume",
           "Using closes (not wicks) ignores spikes; a close beyond all recent closes with above-average volume is "
           "an accepted price, not a poke, so it should follow through.",
           {"win_min": [20, 40, 60], "vol_k": [1.0, 1.5]}, _close_channel_break,
           source="assistant reasoning", author="agent"),
]
