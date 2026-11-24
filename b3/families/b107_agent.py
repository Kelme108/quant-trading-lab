"""Conveyor batch B-107 (agent, 2026-11-24). Mixed themes: round numbers, lunch range, absorption, cross-market co-move,
bands, compression, seasonality of bar colour, smoothed momentum, channel midpoint."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _out(long, short):
    return np.asarray(long, bool).astype(int) - np.asarray(short, bool).astype(int)


def _round_poke(ctx, p):
    s = float(p["step"])
    pc = ctx.prev(ctx.c, 1)
    up = (np.floor(pc / s) + 1.0) * s
    dn = np.floor(pc / s) * s
    short = (ctx.h >= up) & (ctx.c < up)
    long = (ctx.l <= dn) & (ctx.c > dn)
    return _out(long & ~short, short & ~long)


def _lunch_break(ctx, p):
    end = 13 * 60
    start = end - int(p["window_min"])
    inw = (ctx.minute >= start) & (ctx.minute < end)
    g = pd.DataFrame({"d": ctx.day, "h": np.where(inw, ctx.h, np.nan), "l": np.where(inw, ctx.l, np.nan)})
    hi = g.groupby("d")["h"].transform("max").to_numpy()
    lo = g.groupby("d")["l"].transform("min").to_numpy()
    after = (ctx.minute >= end) & (ctx.minute < 15 * 60 + 30)
    return _out(ctx.cross(after & (ctx.c > hi)), ctx.cross(after & (ctx.c < lo)))


def _absorption(ctx, p):
    k = p["vol_k"]
    rng = ctx.h - ctx.l
    med = ctx.cached("v_med", lambda: ctx.same_minute(ctx.v, "median"))
    typ = ctx.cached("rng_med", lambda: ctx.same_minute(rng, "median"))
    ab = ((ctx.v >= k * med) & (rng <= 0.6 * typ) & (typ > 0)).astype(float)
    pa = ctx.prev(ab, 1) == 1
    return _out(pa & (ctx.c > ctx.prev(ctx.h, 1)), pa & (ctx.c < ctx.prev(ctx.l, 1)))


def _comove_fade(ctx, p):
    nb, k = ctx.bars(p["move_min"]), p["k"]
    oc = ctx.other_close()
    wr = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    orr = oc / ctx.prev(oc, nb) - 1.0
    tw = ctx.cached(("tw", nb), lambda: ctx.prev_sessions(np.abs(wr), "mean"))
    to = ctx.cached(("to", nb), lambda: ctx.prev_sessions(np.abs(orr), "mean"))
    both_up = (wr > k * tw) & (orr > k * to)
    both_dn = (wr < -k * tw) & (orr < -k * to)
    return _out(ctx.cross(both_dn), ctx.cross(both_up))


def _keltner_reentry(ctx, p):
    n, k = int(p["n"]), p["k"]
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    atr = ctx.cached(("atr", n), lambda: ctx.roll(ctx.h - ctx.l, n, "mean"))
    up, dn = ema + k * atr, ema - k * atr
    pc = ctx.prev(ctx.c, 1)
    short = (pc > ctx.prev(up, 1)) & (ctx.c < up)
    long = (pc < ctx.prev(dn, 1)) & (ctx.c > dn)
    return _out(long, short)


def _squeeze_release(ctx, p):
    n, k = int(p["n"]), p["k"]
    sd = ctx.cached(("sd", n), lambda: ctx.roll(ctx.c, n, "std"))
    mean = ctx.cached(("mn", n), lambda: ctx.roll(ctx.c, n, "mean"))
    width = 4.0 * sd / mean
    typ = ctx.cached(("wt", n), lambda: ctx.prev_sessions(width, "mean"))
    sq = (width < k * typ).astype(float)
    up, dn = mean + 2 * sd, mean - 2 * sd
    ps = ctx.prev(sq, 1) == 1
    return _out(ps & (ctx.c > ctx.prev(up, 1)), ps & (ctx.c < ctx.prev(dn, 1)))


def _narrow_range(ctx, p):
    n = int(p["n"])
    rng = ctx.h - ctx.l
    nr = ((rng <= ctx.roll(rng, n, "min")) & (rng > 0)).astype(float)
    pn = ctx.prev(nr, 1) == 1
    return _out(pn & (ctx.c > ctx.prev(ctx.h, 1)), pn & (ctx.c < ctx.prev(ctx.l, 1)))


def _season_colour(ctx, p):
    th = p["th"]
    sg = np.sign(ctx.c - ctx.o)
    m = ctx.cached("sg_m", lambda: ctx.same_minute(sg, "mean"))
    return _out(ctx.cross(m >= th), ctx.cross(m <= -th))


def _trix_cross(ctx, p):
    n = int(p["n"])

    def f():
        e = ctx.ema(ctx.ema(ctx.ema(ctx.c, n), n), n)
        return e / ctx.prev(e, 1) - 1.0
    t = ctx.cached(("trix", n), f)
    return _out(ctx.cross(t > 0), ctx.cross(t < 0))


def _donchian_mid(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["width_k"]
    hi = ctx.roll(ctx.h, nb, "max")
    lo = ctx.roll(ctx.l, nb, "min")
    w = hi - lo
    typ = ctx.cached(("dw", nb), lambda: ctx.prev_sessions(w, "mean"))
    mid = (hi + lo) / 2.0
    wide = w >= k * typ
    return _out(ctx.cross(wide & (ctx.c > mid)), ctx.cross(wide & (ctx.c < mid)))


FAMILIES = [
    Family("E-1068", "Round-number poke rejection",
           "Index points at multiples of 250/500/1000 attract resting orders; a bar that pokes the next round level and "
           "closes back is a failed push through offers/bids there. Fade it.",
           {"step": [250, 500, 1000]}, _round_poke, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1069", "Lunch-range break follow",
           "The thin 12-13h range holds balanced inventory; the first close beyond it after 13h is the return of "
           "participants with direction, follow.",
           {"window_min": [45, 60, 90]}, _lunch_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1070", "Absorption bar break",
           "High volume with a small range means one side absorbed the other's aggression; the break of that bar on the "
           "next bar shows which side ran out.",
           {"vol_k": [1.5, 2.0, 3.0]}, _absorption, markets=("WIN",),
           source="volume spread analysis (assistant reasoning)", author="agent"),
    Family("E-1071", "Index and dollar rising together fade",
           "The index and the dollar normally move opposite; a joint unusual move in one direction is flow or "
           "risk-off noise that tends to revert on the index.",
           {"move_min": [10, 20, 30], "k": [0.75, 1.0, 1.5]}, _comove_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1072", "Keltner band re-entry fade",
           "A close outside an ATR band around the EMA followed by a close back inside marks a spent stretch; fade "
           "toward the mean.",
           {"n": [10, 20, 30], "k": [1.5, 2.0, 2.5]}, _keltner_reentry,
           source="Keltner channel practice (assistant reasoning)", author="agent"),
    Family("E-1073", "Band squeeze release follow",
           "Bollinger width far below its usual level means compression; the first close beyond the band after it "
           "releases the stored move in that direction.",
           {"n": [20, 30], "k": [0.5, 0.7, 0.9]}, _squeeze_release,
           source="Bollinger band squeeze (assistant reasoning)", author="agent"),
    Family("E-1074", "Narrowest-bar break (NR4/NR7)",
           "A bar with the narrowest range of the last n bars shows quiet; the next bar closing beyond it starts the "
           "expansion (Crabel).",
           {"n": [4, 7, 10]}, _narrow_range,
           source="Crabel NR7 (assistant reasoning)", author="agent"),
    Family("E-1075", "Same-minute bar-colour seasonality",
           "If bars at this minute of the day were mostly one colour over the last 20 sessions, scheduled flows "
           "(news, opening of other markets) repeat; trade that colour.",
           {"th": [0.4, 0.5, 0.6]}, _season_colour,
           source="intraday seasonality (assistant reasoning)", author="agent"),
    Family("E-1076", "TRIX zero-line cross",
           "Triple-smoothed rate of change filters noise; a zero cross marks a persistent turn in drift that "
           "slower participants chase.",
           {"n": [5, 9, 14]}, _trix_cross,
           source="TRIX oscillator (assistant reasoning)", author="agent"),
    Family("E-1077", "Wide channel midpoint cross follow",
           "When the rolling high-low channel is wider than usual, crossing its midpoint shows control moving to the "
           "other half of an active range; follow.",
           {"win_min": [30, 60], "width_k": [0.8, 1.0, 1.2]}, _donchian_mid,
           source="Donchian channel (assistant reasoning)", author="agent"),
]
