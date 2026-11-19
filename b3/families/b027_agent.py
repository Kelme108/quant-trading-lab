"""Conveyor batch B-027 (agent, 2026-11-19). Mixed themes: exact-tick tweezers, VSA no-demand bars, scheduled
volatility ahead (calm/ramp), dollar-unbacked stretches, value-slope disagreement, candle-open stop runs,
seasonal break outcomes, spike-made ceilings and a dollar-at-value regime."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


# ----------------------------------------------------------------------------- helpers (causal unless noted)

def _breaks(ctx, mins):
    nb = ctx.bars(mins)

    def f():
        hi = ctx.roll(ctx.h, nb, "max", include_current=False)
        lo = ctx.roll(ctx.l, nb, "min", include_current=False)
        return ctx.cross(ctx.c > hi), ctx.cross(ctx.c < lo)
    return ctx.cached(("b027_brk", nb), f)


def _fwd_range(ctx, kb):
    """Range of the NEXT kb bars of the same session. Future-looking: only ever fed to same_minute, which uses
    the sessions BEFORE the bar's session, so a signal never sees its own session's future."""
    d = pd.Series(ctx.day[::-1].copy())
    hr = pd.Series(ctx.h[::-1].copy())
    lr = pd.Series(ctx.l[::-1].copy())
    fh = hr.groupby(d).transform(lambda z: z.rolling(kb, min_periods=kb).max().shift(1))
    fl = lr.groupby(d).transform(lambda z: z.rolling(kb, min_periods=kb).min().shift(1))
    return (fh - fl).to_numpy()[::-1].copy()


def _fwd_close(ctx, kb):
    """Close kb bars later in the same session (future-looking: only fed to same_minute, see above)."""
    d = pd.Series(ctx.day[::-1].copy())
    cr = pd.Series(ctx.c[::-1].copy())
    return cr.groupby(d).shift(kb).to_numpy()[::-1].copy()


def _sched_ratio(ctx, mins):
    """Seasonal (20 prior sessions, same minute) range expected over the next `mins` vs the last `mins`."""
    kb = ctx.bars(mins)

    def f():
        fwd = _fwd_range(ctx, kb)
        back = ctx.roll(ctx.h, kb, "max", True) - ctx.roll(ctx.l, kb, "min", True)
        a = ctx.same_minute(fwd, "mean")
        b = ctx.same_minute(back, "mean")
        with np.errstate(divide="ignore", invalid="ignore"):
            return a / b
    return ctx.cached(("b027_sched", kb), f)


def _wdo_session_mean(ctx):
    def f():
        w = pd.Series(ctx.other_close())
        return w.groupby(ctx.day).transform(lambda z: z.expanding().mean()).to_numpy()
    return ctx.cached("b027_wdo_mean", f)


# ----------------------------------------------------------------------------- signals

def _tweezer(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    wmax = ctx.roll(ctx.h, nb, "max", include_current=True)
    wmin = ctx.roll(ctx.l, nb, "min", include_current=True)
    mid = (ctx.h + ctx.l) / 2.0
    top = np.isclose(ctx.h, h1, rtol=0.0, atol=1e-6) & (ctx.h >= wmax) & (ctx.c < ctx.o) & (ctx.c < mid)
    bot = np.isclose(ctx.l, l1, rtol=0.0, atol=1e-6) & (ctx.l <= wmin) & (ctx.c > ctx.o) & (ctx.c > mid)
    return ctx.cross(bot).astype(int) - ctx.cross(top).astype(int)


def _calm_ahead_fade(ctx, p):
    ratio = _sched_ratio(ctx, p["horizon_min"])
    up, dn = _breaks(ctx, 15)
    calm = ratio < p["q"]
    return (dn & calm).astype(int) - (up & calm).astype(int)


def _dollar_unbacked(ctx, p):
    k = p["k"]
    vw = ctx.vwap()
    dev = ctx.c - vw
    sc = ctx.cached("b027_vwdev_sc", lambda: ctx.prev_sessions(np.abs(dev), "mean"))
    w, wm = ctx.other_close(), _wdo_session_mean(ctx)
    upx = (dev > k * sc) & (w > wm)
    dnx = (dev < -k * sc) & (w < wm)
    short = upx & (ctx.c < ctx.prev(ctx.l, 1))
    long = dnx & (ctx.c > ctx.prev(ctx.h, 1))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _vsa_no_demand(ctx, p):
    nb = ctx.bars(p["trend_min"])
    rng = ctx.h - ctx.l
    r1 = ctx.prev(rng, 1)
    vmin2 = np.minimum(ctx.prev(ctx.v, 1), ctx.prev(ctx.v, 2))
    c1 = ctx.prev(ctx.c, 1)
    at_hi = ctx.h >= ctx.roll(ctx.h, nb, "max", include_current=True)
    at_lo = ctx.l <= ctx.roll(ctx.l, nb, "min", include_current=True)
    no_demand = (ctx.c > c1) & (rng < r1) & (ctx.v < vmin2) & at_hi
    no_supply = (ctx.c < c1) & (rng < r1) & (ctx.v < vmin2) & at_lo
    return ctx.cross(no_supply).astype(int) - ctx.cross(no_demand).astype(int)


def _counter_slope(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    vw = ctx.vwap()
    sl = vw - ctx.prev(vw, nb)
    sc = ctx.cached(("b027_slope_sc", nb), lambda: ctx.prev_sessions(np.abs(sl), "mean"))
    up, dn = _breaks(ctx, p["win_min"])
    short = up & (sl < -k * sc)
    long = dn & (sl > k * sc)
    return long.astype(int) - short.astype(int)


def _ramp_follow(ctx, p):
    ratio = _sched_ratio(ctx, p["horizon_min"])
    up, dn = _breaks(ctx, 15)
    ramp = ratio > p["r"]
    return (up & ramp).astype(int) - (dn & ramp).astype(int)


def _candle_open_fade(ctx, p):
    blk = int(p["block_min"])
    first = (ctx.minute % blk) == 0
    up, dn = _breaks(ctx, p["win_min"])
    return (dn & first).astype(int) - (up & first).astype(int)


def _seasonal_break_outcome(ctx, p):
    kb = ctx.bars(p["fwd_min"])
    th = p["th"]

    def f():
        up, dn = _breaks(ctx, 15)
        fc = _fwd_close(ctx, kb)
        sc = ctx.prev_sessions(np.abs(ctx.c - ctx.prev(ctx.c, kb)), "mean")
        with np.errstate(divide="ignore", invalid="ignore"):
            out = (fc - ctx.c) / sc
        signed = np.where(up, out, np.where(dn, -out, np.nan))
        valid = (up | dn) & np.isfinite(signed)
        s_out = ctx.same_minute(np.where(valid, signed, 0.0), "mean")
        s_cnt = ctx.same_minute(valid.astype(float), "mean")
        nb30 = ctx.bars(30)
        num = ctx.roll(s_out, nb30, "sum")
        den = ctx.roll(s_cnt, nb30, "sum")
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(den > 0, num / den, np.nan)
    avg = ctx.cached(("b027_sbo", kb), f)
    up, dn = _breaks(ctx, 15)
    fails = avg < -th
    return (dn & fails).astype(int) - (up & fails).astype(int)


def _spike_ceiling(ctx, p):
    nb, share = ctx.bars(p["win_min"]), p["share"]
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    mr = ctx.roll(ctx.h - ctx.l, nb, "max", include_current=False)
    spike = (hi - lo > 0) & (mr >= share * (hi - lo))
    up, dn = _breaks(ctx, p["win_min"])
    return (dn & spike).astype(int) - (up & spike).astype(int)


def _dollar_at_value(ctx, p):
    w, wm = ctx.other_close(), _wdo_session_mean(ctx)
    z = np.abs(w - wm)
    sc = ctx.cached("b027_wdo_z_sc", lambda: ctx.prev_sessions(z, "mean"))
    calm = z < p["q"] * sc
    up, dn = _breaks(ctx, p["win_min"])
    return (dn & calm).astype(int) - (up & calm).astype(int)


FAMILIES = [
    Family("E-268", "Tweezer extreme fade",
           "Two consecutive bars that stop at exactly the same high (low) at the top (bottom) of the recent window "
           "show one resting limit order capping two separate pushes; when the second bar closes down in its lower "
           "half, the buyers who pushed into it are trapped under an offer that did not move, so fade (mirror at lows).",
           {"lookback_min": [15, 30, 60]}, _tweezer, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-269", "Scheduled-calm-ahead micro-break fade",
           "The intraday volatility schedule is very stable across sessions; when the range usually traded over the "
           "NEXT minutes at this time of day is well below the range of the minutes just gone (the active window is "
           "ending, e.g. after the open or before lunch), no fresh initiators are due, so a 15-minute break made then "
           "has nobody to extend it and liquidity providers lean it back; fade it.",
           {"horizon_min": [15, 30, 60], "q": [0.7, 0.8, 0.9]}, _calm_ahead_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-270", "Dollar-unbacked VWAP stretch turn fade",
           "Foreign flow lifts the index and sells the dollar together, so a WIN stretch far above its session VWAP "
           "is backed when WDO trades below its own session average; when WIN is stretched above value while WDO "
           "still sits above its average, the stretch is local flow, and the first bar closing below the previous "
           "low starts the unwind back to value; fade it (mirror below VWAP).",
           {"k": [1.0, 1.5, 2.0]}, _dollar_unbacked, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-271", "VSA no-demand / no-supply bar fade",
           "Volume Spread Analysis: an up bar at the top of the recent window on a narrower range than the previous "
           "bar and less volume than either of the two previous bars shows professional money is not buying the "
           "rise; the push is carried by the last small buyers only, so sell it (no-supply bar at the low: buy).",
           {"trend_min": [10, 20, 30]}, _vsa_no_demand, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-272", "Counter-VWAP-slope new-extreme fade",
           "The session VWAP's slope over the window shows where volume-weighted value is migrating; a new window high "
           "while value is migrating down means price is probing up on little volume while the volume keeps trading "
           "lower; the day's value-setters sell the probe, so fade it (mirror for a new low while value rises).",
           {"win_min": [15, 30, 60], "k": [0.0, 0.5, 1.0]}, _counter_slope, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-273", "Scheduled-volatility-ramp break follow",
           "When the range usually traded over the next minutes at this time of day is much larger than the range "
           "just gone (the NYSE open, scheduled US data, the European close), informed participants are about to "
           "arrive on schedule; a 15-minute break made as the ramp starts is the first of their orders and the "
           "liquidity providers widen instead of leaning, so follow the break.",
           {"horizon_min": [15, 30, 60], "r": [1.1, 1.25, 1.4]}, _ramp_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-274", "Candle-open stop-run fade",
           "Chart traders reset stops and bracket orders at the open of each new 15/30/60-minute candle just beyond "
           "the last minutes' extreme; a break printed on the very first bar of a new candle is that one-off burst "
           "of reset stops and brackets being triggered, not an initiator, and once it is filled the price reverts; "
           "fade breaks made on a candle's first bar.",
           {"block_min": [15, 30, 60], "win_min": [10, 15, 30]}, _candle_open_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-275", "Seasonal break-outcome fade",
           "Who dominates each half hour of the session (liquidity providers or breakout traders) repeats from day to "
           "day; when over the last 20 sessions the 15-minute breaks made in the trailing half hour of this time of "
           "day were, on average, given back within the next minutes, today's break at the same time meets the same "
           "providers, so fade it.",
           {"fwd_min": [10, 20, 30], "th": [0.0, 0.1, 0.2]}, _seasonal_break_outcome, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-276", "Spike-made ceiling break fade",
           "When most of the window's range was made by one bar, its high (low) is the tip of a single burst that was "
           "never accepted: the burst ran into resting orders there and price left at once; a later close through "
           "that tip meets the same untouched orders and no accepted value behind it, so fade the break.",
           {"win_min": [15, 30, 60], "share": [0.5, 0.6, 0.7]}, _spike_ceiling, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-277", "Dollar-at-value micro-break fade",
           "When WDO trades near its own session average price, the dollar is in balance and foreign desks are not "
           "repositioning across both markets; with the macro side idle, a short-term WIN break is local flow that "
           "index liquidity providers absorb, so fade it (a level-of-the-dollar regime, not its volatility).",
           {"q": [0.25, 0.5, 0.75], "win_min": [10, 15, 30]}, _dollar_at_value, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
