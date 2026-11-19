"""Conveyor batch B-018 (agent, 2026-11-18). Mixed themes: seasonal liquidity clock, bar separation, morning value, retail
oscillators (Elder impulse, Woodies CCI, Ehlers Fisher, Elder force index), VWAP-agreement balance, yesterday-range
steps and close pinning."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _seasonal_range(ctx):
    return ctx.cached("b018_seas_rng", lambda: ctx.same_minute(ctx.h - ctx.l, "median"))


def _clock_fade(ctx, p):
    med = _seasonal_range(ctx)
    med_prev = ctx.prev(med, ctx.bars(30))
    falling = med < p["ratio"] * med_prev
    nb = ctx.bars(p["win_min"])
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    short = ctx.cross(falling & (ctx.c > hi))
    long = ctx.cross(falling & (ctx.c < lo))
    return long.astype(int) - short.astype(int)


def _separation_follow(ctx, p):
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    ov = np.minimum(ctx.h, h1) - np.maximum(ctx.l, l1)
    span = np.maximum(ctx.h, h1) - np.minimum(ctx.l, l1)
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = np.where(span > 0, ov / span, np.nan)
    ratio = np.clip(ratio, 0.0, None)
    sticky = ctx.roll(ratio, ctx.bars(p["win_min"]), "mean", include_current=False) >= p["q"]
    up = sticky & (ctx.l > h1)
    dn = sticky & (ctx.h < l1)
    return up.astype(int) - dn.astype(int)


def _morning_value(ctx, p):
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    morning = ctx.minute < 12 * 60
    pv = pd.Series(np.where(morning, tp * ctx.v, 0.0)).groupby(ctx.day).cumsum().to_numpy()
    vv = pd.Series(np.where(morning, ctx.v, 0.0)).groupby(ctx.day).cumsum().to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        mv = np.where(vv > 0, pv / vv, np.nan)
    nb = ctx.bars(60)
    mv60 = np.abs(ctx.c - ctx.prev(ctx.c, nb))
    scale = ctx.cached("b018_mv60", lambda: ctx.prev_sessions(mv60, "mean"))
    aft = (ctx.minute >= 13 * 60) & (ctx.minutes_to_close > 30)
    d = ctx.c - mv
    k = p["k"]
    short = aft & (d > k * scale) & (ctx.c < ctx.prev(ctx.l, 1))
    long = aft & (d < -k * scale) & (ctx.c > ctx.prev(ctx.h, 1))
    return long.astype(int) - short.astype(int)


def _elder_impulse(ctx, p):
    s = int(p["scale"])
    c = ctx.c
    e13 = ctx.ema(c, 13 * s)
    macd = ctx.ema(c, 12 * s) - ctx.ema(c, 26 * s)
    sig = ctx.ema(macd, 9 * s)
    hist = macd - sig
    de, dh = e13 - ctx.prev(e13, 1), hist - ctx.prev(hist, 1)
    green = (de > 0) & (dh > 0)
    red = (de < 0) & (dh < 0)
    was_red = ctx.prev(red.astype(float), 1) == 1
    was_green = ctx.prev(green.astype(float), 1) == 1
    long = green & was_red
    short = red & was_green
    return long.astype(int) - short.astype(int)


def _vwap_agreement_fade(ctx, p):
    nb = ctx.bars(p["win_min"])
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    spv = ctx.roll(tp * ctx.v, nb, "sum")
    sv = ctx.roll(ctx.v, nb, "sum")
    with np.errstate(invalid="ignore", divide="ignore"):
        rv = np.where(sv > 0, spv / sv, np.nan)
    med = _seasonal_range(ctx)
    bal = np.abs(rv - ctx.vwap()) < p["k"] * med
    n15 = ctx.bars(15)
    hi = ctx.roll(ctx.h, n15, "max", include_current=False)
    lo = ctx.roll(ctx.l, n15, "min", include_current=False)
    short = ctx.cross(bal & (ctx.c > hi))
    long = ctx.cross(bal & (ctx.c < lo))
    return long.astype(int) - short.astype(int)


def _yrange_steps(ctx, p):
    yr = ctx.prev_session_value("high") - ctx.prev_session_value("low")
    sh, sl = ctx.session_high(True), ctx.session_low(True)
    with np.errstate(invalid="ignore", divide="ignore"):
        j = np.floor((sh - sl) / (p["q"] * yr))
    step = (j > ctx.prev(j, 1)) & (ctx.bar_in_day >= ctx.bars(15))
    new_hi = ctx.h > ctx.session_high(False)
    new_lo = ctx.l < ctx.session_low(False)
    long = step & new_hi & ~new_lo
    short = step & new_lo & ~new_hi
    return long.astype(int) - short.astype(int)


def _force_index_dip(ctx, p):
    E = ctx.ema(ctx.c, ctx.bars(p["trend_min"]))
    up = E > ctx.prev(E, 1)
    dn = E < ctx.prev(E, 1)
    fi = ctx.ema((ctx.c - ctx.prev(ctx.c, 1)) * ctx.v, int(p["fi_span"]))
    fi1 = ctx.prev(fi, 1)
    long = up & (ctx.c > E) & (fi > 0) & (fi1 < 0)
    short = dn & (ctx.c < E) & (fi < 0) & (fi1 > 0)
    return long.astype(int) - short.astype(int)


def _cci_zlr(ctx, p):
    n, band = int(p["n"]), p["band"]
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    sma = ctx.roll(tp, n, "mean")
    sd = ctx.roll(tp, n, "std")
    with np.errstate(invalid="ignore", divide="ignore"):
        cci = np.where(sd > 0, (tp - sma) / (0.015 * 0.8 * sd), np.nan)
    c1, c2 = ctx.prev(cci, 1), ctx.prev(cci, 2)
    was_up = ctx.roll(cci, 6, "max", include_current=False) >= 100
    was_dn = ctx.roll(cci, 6, "min", include_current=False) <= -100
    long = was_up & (c1 > 0) & (c1 < band) & (c1 < c2) & (cci > c1)
    short = was_dn & (c1 < 0) & (c1 > -band) & (c1 > c2) & (cci < c1)
    return long.astype(int) - short.astype(int)


def _close_pin_release(ctx, p):
    med = _seasonal_range(ctx)
    dc = ctx.c - ctx.prev(ctx.c, 1)
    pinned = (np.abs(dc) <= 0.2 * med).astype(float)
    streak = ctx.roll(pinned, int(p["m"]), "min", include_current=False) == 1
    rel = streak & (np.abs(dc) >= p["k"] * med)
    long = rel & (dc > 0)
    short = rel & (dc < 0)
    return long.astype(int) - short.astype(int)


def _fisher_turn(ctx, p):
    n, th = int(p["n"]), p["th"]
    hi = ctx.roll(ctx.h, n, "max")
    lo = ctx.roll(ctx.l, n, "min")
    den = hi - lo
    with np.errstate(invalid="ignore", divide="ignore"):
        pos = np.where(den > 0, (ctx.c - lo) / den, 0.5)
    pos = np.where(np.isnan(den), np.nan, pos)
    x = ctx.ema(2.0 * pos - 1.0, 5)
    x = np.clip(x, -0.999, 0.999)
    with np.errstate(invalid="ignore", divide="ignore"):
        raw = 0.5 * np.log((1.0 + x) / (1.0 - x))
    fish = ctx.ema(raw, 3)
    f1, f2 = ctx.prev(fish, 1), ctx.prev(fish, 2)
    short = (f1 > th) & (fish < f1) & (f1 >= f2)
    long = (f1 < -th) & (fish > f1) & (f1 <= f2)
    return long.astype(int) - short.astype(int)


W = ("WIN",)
SRC = "assistant reasoning"

FAMILIES = [
    Family("E-178", "Liquidity-clock break fade",
           "When the seasonal bar range for this minute (20-session median) is clearly below its level 30 minutes "
           "earlier, the session is entering a quieter part of its daily liquidity clock (participants leaving); a close "
           "beyond the recent high/low then has no arriving flow behind it and is faded by liquidity providers.",
           {"ratio": [0.7, 0.8, 0.9], "win_min": [10, 15, 20]}, _clock_fade, markets=W, source=SRC, author="agent"),
    Family("E-179", "Separation-bar follow in a sticky tape",
           "When consecutive bars have overlapped heavily for a while, makers quote a two-sided book; a bar trading "
           "entirely beyond the previous bar (no overlap at all) means an initiator cleared every resting quote at once, "
           "and makers widen and step away in that direction, so follow the separation.",
           {"win_min": [15, 30, 60], "q": [0.35, 0.45, 0.55]}, _separation_follow, markets=W, source=SRC,
           author="agent"),
    Family("E-180", "Morning-value afternoon reversion",
           "The VWAP of the morning (before 12:00) is the price where the cash-session participants built the day's "
           "inventory; an afternoon stretch far from it is carried by the thinner afternoon crowd, and the first counter "
           "bar starts the return toward the morning value as morning holders defend and afternoon chasers exit.",
           {"k": [1.0, 1.5, 2.0]}, _morning_value, markets=W, source=SRC, author="agent"),
    Family("E-181", "Elder impulse colour flip follow",
           "Elder's Impulse System colours a bar green when both the 13-EMA and the MACD histogram rise and red when "
           "both fall, and its many users act on the colour; the first green bar after a red one means both inertia and "
           "momentum turned together, the red-bar sellers are stopped and impulse users buy at once, so follow it.",
           {"scale": [1, 2, 3]}, _elder_impulse, markets=W, source=SRC, author="agent"),
    Family("E-182", "VWAP-agreement balance micro-break fade",
           "When the volume-weighted price of the last window sits on top of the session VWAP, recent trade is "
           "happening at the day's average cost: the market is in balance around value and no one is migrating it; a "
           "close beyond the last 15 minutes' high/low in that state is a small push that responsive traders fade.",
           {"win_min": [30, 60, 90], "k": [1.0, 2.0, 3.0]}, _vwap_agreement_fade, markets=W, source=SRC,
           author="agent"),
    Family("E-183", "Yesterday-range step expansion follow",
           "Day traders gauge today's progress in units of yesterday's range; each time today's range crosses a "
           "further fixed fraction of it on a new session extreme, the stops of those who sized for a day like "
           "yesterday sit just beyond and expansion traders add, so follow the bar that makes the new step.",
           {"q": [0.15, 0.2, 0.25]}, _yrange_steps, markets=W, source=SRC, author="agent"),
    Family("E-184", "Elder force-index dip in an EMA trend",
           "Elder's force index (price change x volume, short EMA) going negative inside a rising trend shows a pullback "
           "with sellers committing volume; when it turns back positive while price still holds above the trend EMA, "
           "the volume-backed selling is done and trend holders resume, so buy (mirror in a down trend).",
           {"trend_min": [30, 60, 120], "fi_span": [2, 3, 5]}, _force_index_dip, markets=W, source=SRC,
           author="agent"),
    Family("E-185", "Woodies CCI zero-line reject",
           "In Woodies CCI, a CCI that was recently above +100 and pulls back toward but not through the zero line, "
           "then hooks up, marks a shallow correction inside an intact push; the CCI traders buy the hook together and "
           "the faders' stops sit just above, so follow the hook (mirror below zero).",
           {"n": [14, 20, 30], "band": [30, 50, 70]}, _cci_zlr, markets=W, source=SRC, author="agent"),
    Family("E-186", "Close-pin release follow",
           "Several bars in a row closing at almost the same price while still trading a range mean a large limit order "
           "is pinning that price and absorbing both sides; a bar that then closes a full typical range away shows the "
           "pin was filled or pulled, and the side it was holding back runs, so follow the release bar.",
           {"m": [3, 4, 5], "k": [0.5, 0.75, 1.0]}, _close_pin_release, markets=W, source=SRC, author="agent"),
    Family("E-187", "Ehlers Fisher transform extreme turn fade",
           "The Fisher transform of the price's position in its recent range turns the bounded position into a "
           "near-Gaussian score that makes extremes sharp; when it turns down from a high extreme, the short-term buyers "
           "who pushed price to the top of its window stopped paying up and the many Fisher users sell the turn, so "
           "fade (mirror from a low extreme).",
           {"n": [10, 20, 30], "th": [1.5, 2.0, 2.5]}, _fisher_turn, markets=W, source=SRC, author="agent"),
]
