"""Conveyor batch B-046 (agent, 2026-11-21). Mixed themes: day-to-day clock seasonality, robust/ATR/Bollinger stretch fades,
shock and jump-dominated moves, counter-position breaks, US-open drive, up-close share."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _sgn(long, short):
    return long.astype(int) - short.astype(int)


def _same_clock_drift(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    move = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    hist = ctx.cached(("hist_move", nb), lambda: ctx.same_minute(move, "mean", n=5))
    typ = ctx.cached(("typ_move", nb), lambda: ctx.same_minute(np.abs(move), "mean", n=20))
    long = (hist >= k * typ) & (move > 0)
    short = (hist <= -k * typ) & (move < 0)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _robust_z_fade(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    med = ctx.cached(("med", n), lambda: pd.Series(ctx.c).groupby(ctx.day).transform(
        lambda z: z.rolling(n, min_periods=n).median()).to_numpy())
    mad = ctx.cached(("mad", n), lambda: ctx.roll(np.abs(ctx.c - med), n, "mean"))
    z = np.where(mad > 0, (ctx.c - med) / np.where(mad > 0, mad, 1.0), 0.0)
    return _sgn(ctx.cross(z <= -k), ctx.cross(z >= k))


def _upclose_share_fade(ctx, p):
    n, th = ctx.bars(p["win_min"]), p["th"]
    up = (ctx.c > ctx.prev(ctx.c, 1)).astype(float)
    up = np.where(np.isnan(ctx.prev(ctx.c, 1)), np.nan, up)
    share = ctx.roll(up, n, "mean")
    hi = ctx.roll(ctx.c, n, "max")
    lo = ctx.roll(ctx.c, n, "min")
    short = (share >= th) & (ctx.c >= hi)
    long = (share <= 1 - th) & (ctx.c <= lo)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _atr_burst(ctx, p):
    ns, th = ctx.bars(p["short_min"]), p["th"]
    nl = ctx.bars(60)
    rng = ctx.h - ctx.l
    s = ctx.roll(rng, ns, "mean")
    lg = ctx.roll(rng, nl, "mean")
    burst = (lg > 0) & (s >= th * lg)
    col = np.sign(ctx.c - ctx.o)
    cr = ctx.cross(burst)
    return np.where(cr & (col > 0), 1, 0) - np.where(cr & (col < 0), 1, 0)


def _sigma_shock_fade(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    ret = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    sd = ctx.roll(ret, n, "std", include_current=False)
    long = (sd > 0) & (ret <= -k * sd)
    short = (sd > 0) & (ret >= k * sd)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _counter_position_break(ctx, p):
    n, q = ctx.bars(p["win_min"]), p["q"]
    hi = ctx.roll(ctx.c, n, "max", include_current=False)
    lo = ctx.roll(ctx.c, n, "min", include_current=False)
    sh, sl = ctx.session_high(True), ctx.session_low(True)
    rng = sh - sl
    pos = np.where(rng > 0, (ctx.c - sl) / np.where(rng > 0, rng, 1.0), 0.5)
    short = (ctx.c > hi) & (pos < q)
    long = (ctx.c < lo) & (pos > 1 - q)
    return _sgn(ctx.cross(long), ctx.cross(short))


def _jump_move_fade(ctx, p):
    n, th = ctx.bars(p["win_min"]), p["th"]
    ret = ctx.c / ctx.prev(ctx.c, 1) - 1.0
    ab = np.abs(ret)
    mx = ctx.roll(ab, n, "max")
    sm = ctx.roll(ab, n, "sum")
    share = np.where(sm > 0, mx / np.where(sm > 0, sm, 1.0), 0.0)
    net = ctx.c / ctx.prev(ctx.c, n) - 1.0
    sd = ctx.cached("ret_sd", lambda: ctx.prev_sessions(ret, "sd"))
    big = np.abs(net) >= 1.5 * np.sqrt(n) * sd
    cond = (share >= th) & big
    return _sgn(ctx.cross(cond & (net < 0)), ctx.cross(cond & (net > 0)))


def _keltner_fade(ctx, p):
    n, k = ctx.bars(p["ema_min"]), p["k"]
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    atr = ctx.cached(("atr", n), lambda: ctx.roll(ctx.h - ctx.l, n, "mean"))
    return _sgn(ctx.cross(ctx.c < ema - k * atr), ctx.cross(ctx.c > ema + k * atr))


def _us_open_drive(ctx, p):
    nb, k = ctx.bars(p["span_min"]), p["k"]
    move = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    typ = ctx.cached(("typ_us", nb), lambda: ctx.same_minute(np.abs(move), "mean", n=20))
    t0 = p["span_min"] - ctx.tf
    inwin = np.zeros(ctx.n, bool)
    for anchor in (630, 690):          # NY cash open at 10:30 or 11:30 São Paulo depending on US daylight saving
        inwin |= (ctx.minute >= anchor + t0) & (ctx.minute < anchor + t0 + 20)
    big = np.abs(move) >= k * typ
    up = inwin & big & (move > 0)
    dn = inwin & big & (move < 0)
    return _sgn(ctx.cross(up), ctx.cross(dn))


def _bollinger_reentry(ctx, p):
    n, m = ctx.bars(p["win_min"]), p["m"]
    mean = ctx.cached(("bmean", n), lambda: ctx.roll(ctx.c, n, "mean"))
    sd = ctx.cached(("bsd", n), lambda: ctx.roll(ctx.c, n, "std"))
    up_b, dn_b = mean + m * sd, mean - m * sd
    pc = ctx.prev(ctx.c, 1)
    short = (pc > ctx.prev(up_b, 1)) & (ctx.c <= up_b) & (ctx.c < pc)
    long = (pc < ctx.prev(dn_b, 1)) & (ctx.c >= dn_b) & (ctx.c > pc)
    return _sgn(long, short)


FAMILIES = [
    Family("E-458", "Recent same-clock window drift follow",
           "Index flows repeat at the same clock times (index arbitrage, institutional schedules); when the average "
           "move over the same clock window of the last 5 sessions is large and today's move agrees, follow it.",
           {"win_min": [15, 30, 60], "k": [0.5, 1.0, 1.5]}, _same_clock_drift,
           source="assistant reasoning (intraday return seasonality, Heston-Korajczyk-Sadka idea)", author="agent"),
    Family("E-459", "Robust median/MAD stretch fade",
           "A price far from its rolling median in mean-absolute-deviation units is stretched by a few aggressive "
           "orders, not by a shift in value; liquidity providers pull it back.",
           {"win_min": [30, 60, 120], "k": [2.5, 3.0, 3.5]}, _robust_z_fade,
           source="assistant reasoning", author="agent"),
    Family("E-460", "Up-close share extreme fade",
           "When nearly every close in a window is up and the price sits at the window high, buyers are exhausted "
           "(one-sided tape); fade the first such bar.",
           {"win_min": [30, 45, 60], "th": [0.7, 0.75, 0.8]}, _upclose_share_fade,
           source="assistant reasoning", author="agent"),
    Family("E-461", "Range-burst direction follow",
           "When the short-term average bar range jumps well above the hourly average, an informed order is working; "
           "follow the colour of the bar that makes the burst start.",
           {"short_min": [5, 10], "th": [1.5, 2.0, 2.5]}, _atr_burst,
           source="assistant reasoning (volatility expansion)", author="agent"),
    Family("E-462", "Rolling-sigma shock bar fade",
           "A single bar return far beyond the recent bar-return sigma is usually a sweep of thin liquidity that "
           "partly reverses; fade it.",
           {"win_min": [60, 120], "k": [3.0, 4.0, 5.0]}, _sigma_shock_fade,
           source="assistant reasoning", author="agent"),
    Family("E-463", "Counter-position window break fade",
           "A break of the recent window extreme against the session's location (rally breaks near the day low, "
           "dip breaks near the day high) is a counter-trend push; the larger flow resumes.",
           {"win_min": [15, 30, 60], "q": [0.2, 0.3, 0.4]}, _counter_position_break,
           source="assistant reasoning", author="agent"),
    Family("E-464", "Jump-dominated move fade",
           "A move driven by one outsized bar rather than steady pressure is a liquidity gap or a single order; "
           "it tends to retrace, unlike gradual moves.",
           {"win_min": [15, 30, 60], "th": [0.35, 0.5, 0.65]}, _jump_move_fade,
           source="assistant reasoning (jump vs continuous price moves)", author="agent"),
    Family("E-465", "EMA-Keltner stretch fade",
           "Price beyond an EMA by several average bar ranges is overextended relative to its own trend; sellers or "
           "buyers of the other side step in.",
           {"ema_min": [30, 60, 120], "k": [2.0, 3.0, 4.0]}, _keltner_fade,
           source="assistant reasoning (Keltner channel)", author="agent"),
    Family("E-466", "US cash-open drive follow",
           "The US cash open (10:30 or 11:30 in Sao Paulo time depending on daylight saving) brings foreign flow "
           "to the index; a larger-than-usual first move after it tends to be followed.",
           {"span_min": [5, 10, 15], "k": [0.0, 0.5, 1.0]}, _us_open_drive,
           markets=("WIN",), source="assistant reasoning (US open flow)", author="agent"),
    Family("E-467", "Bollinger band re-entry fade",
           "A close back inside a Bollinger band after an excursion means the push failed; mean reversion toward the "
           "band centre follows.",
           {"win_min": [30, 60, 120], "m": [2.0, 2.5, 3.0]}, _bollinger_reentry,
           source="assistant reasoning (Bollinger bands)", author="agent"),
]
