"""Conveyor batch B-023 (agent, 2026-11-18). New regime and level filters for short-term breaks (inter-market non-confirmation, higher-timeframe candle, prior-session type, overnight gap, volume distribution, jump share, early-extreme order), plus a contrarian MACD trigger."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from b3.esteira import Family


def _brk(ctx, minutes):
    """(up, dn): the bar whose close first goes beyond the previous `minutes` high/low."""
    nb = ctx.bars(minutes)

    def f():
        hi = ctx.roll(ctx.h, nb, "max", include_current=False)
        lo = ctx.roll(ctx.l, nb, "min", include_current=False)
        return ctx.cross(ctx.c > hi), ctx.cross(ctx.c < lo)
    return ctx.cached(("brk", nb), f)


def _fade(up, dn, cond_short, cond_long):
    short = up & cond_short
    long = dn & cond_long
    return long.astype(int) - short.astype(int)


# E-228 ------------------------------------------------------------------------------------------
def _smt_divergence(ctx, p):
    nb = ctx.bars(p["win_min"])
    q = p["q"]
    w = ctx.other_close()
    whi = ctx.roll(w, nb, "max", include_current=False)
    wlo = ctx.roll(w, nb, "min", include_current=False)
    rng = whi - wlo
    with np.errstate(invalid="ignore", divide="ignore"):
        pos = np.where(rng > 0, (w - wlo) / rng, np.nan)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    up = ctx.cross(ctx.c > hi)
    dn = ctx.cross(ctx.c < lo)
    # a WIN high should come with a dollar near its low (foreign flow); a dollar still high = no confirmation
    return _fade(up, dn, pos >= q, pos <= 1.0 - q)


# E-229 ------------------------------------------------------------------------------------------
def _htf_inside(ctx, p):
    bm = int(p["block_min"])
    blk = (ctx.minute // bm).astype(int)
    df = pd.DataFrame({"d": ctx.day, "b": blk, "h": ctx.h, "l": ctx.l})
    agg = df.groupby(["d", "b"]).agg(h=("h", "max"), l=("l", "min"))
    prev = agg.groupby(level=0).shift(1)
    idx = pd.MultiIndex.from_arrays([ctx.day, blk])
    ph = prev["h"].reindex(idx).to_numpy()
    pl = prev["l"].reindex(idx).to_numpy()
    up, dn = _brk(ctx, p["brk_min"])
    return _fade(up, dn, ctx.c < ph, ctx.c > pl)


# E-230 ------------------------------------------------------------------------------------------
def _after_doji(ctx, p):
    yo, yc = ctx.prev_session_value("open"), ctx.prev_session_value("close")
    yh, yl = ctx.prev_session_value("high"), ctx.prev_session_value("low")
    with np.errstate(invalid="ignore", divide="ignore"):
        body = np.abs(yc - yo) / (yh - yl)
    bal = body <= p["th"]
    up, dn = _brk(ctx, p["brk_min"])
    return _fade(up, dn, bal, bal)


# E-231 ------------------------------------------------------------------------------------------
def _heavy_ceiling(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    with np.errstate(invalid="ignore", divide="ignore"):
        heavy = (med > 0) & (ctx.v >= k * med)
    hh = ctx.roll(np.where(heavy, ctx.h, -1e18), nb, "max", include_current=False)
    ll = ctx.roll(np.where(heavy, ctx.l, 1e18), nb, "min", include_current=False)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    up = ctx.cross(ctx.c > hi)
    dn = ctx.cross(ctx.c < lo)
    return _fade(up, dn, hh >= hi, ll <= lo)


# E-232 ------------------------------------------------------------------------------------------
def _no_gap_day(ctx, p):
    pc = ctx.prev_session_value("close")
    with np.errstate(invalid="ignore", divide="ignore"):
        gap = np.abs(ctx.day_open / pc - 1.0)
    typ = ctx.cached("gap_typ", lambda: ctx.prev_sessions(gap, "mean"))
    small = gap <= p["k"] * typ
    up, dn = _brk(ctx, p["brk_min"])
    return _fade(up, dn, small, small)


# E-233 ------------------------------------------------------------------------------------------
def _macd_fade(ctx, p):
    s, k = int(p["scale"]), p["k"]
    macd = ctx.ema(ctx.c, 12 * s) - ctx.ema(ctx.c, 26 * s)
    sig = ctx.ema(macd, 9 * s)
    typ = ctx.prev_sessions(np.abs(macd), "mean")
    bull = ctx.cross(macd > sig) & (macd > k * typ)
    bear = ctx.cross(macd < sig) & (macd < -k * typ)
    return bear.astype(int) - bull.astype(int)


# E-234 ------------------------------------------------------------------------------------------
def _front_loaded(ctx, p):
    nb1 = ctx.bars(60)
    first = ctx.bar_in_day < nb1
    g = pd.Series(ctx.v).groupby(ctx.day)
    cumv = g.cumsum().to_numpy()
    fvc = pd.Series(np.where(first, ctx.v, 0.0)).groupby(ctx.day).cumsum().to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        share = np.where(cumv > 0, fvc / cumv, np.nan)
    typ = ctx.cached("share_typ", lambda: ctx.same_minute(share, "median"))
    loaded = (~first) & (share >= p["k"] * typ)
    up, dn = _brk(ctx, p["brk_min"])
    return _fade(up, dn, loaded, loaded)


# E-235 ------------------------------------------------------------------------------------------
def _off_peak(ctx, p):
    seas = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    avg = ctx.cached("vol_avg", lambda: ctx.prev_sessions(ctx.v, "mean"))
    off = seas <= p["q"] * avg
    up, dn = _brk(ctx, p["brk_min"])
    return _fade(up, dn, off, off)


# E-236 ------------------------------------------------------------------------------------------
def _jump_free(ctx, p):
    nb = ctx.bars(p["win_min"])
    lc = np.log(ctx.c)
    r = lc - ctx.prev(lc, 1)
    rv = ctx.roll(r * r, nb, "sum")
    bv = (math.pi / 2.0) * ctx.roll(np.abs(r) * np.abs(ctx.prev(r, 1)), nb, "sum")
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = np.where(rv > 0, bv / rv, np.nan)
    diffusive = ratio >= p["th"]
    up, dn = _brk(ctx, 10)
    return _fade(up, dn, diffusive, diffusive)


# E-237 ------------------------------------------------------------------------------------------
def _early_extreme(ctx, p):
    nb = ctx.bars(p["first_min"])
    first = ctx.bar_in_day < nb
    hm = pd.Series(np.where(first, ctx.h, -np.inf))
    lm = pd.Series(np.where(first, ctx.l, np.inf))
    ih = hm.groupby(ctx.day).transform(lambda z: int(np.argmax(z.to_numpy()))).to_numpy()
    il = lm.groupby(ctx.day).transform(lambda z: int(np.argmin(z.to_numpy()))).to_numpy()
    after = ctx.bar_in_day >= nb
    high_first = after & (ih < il)
    low_first = after & (il < ih)
    up, dn = _brk(ctx, p["brk_min"])
    return _fade(up, dn, high_first, low_first)


SRC = "assistant reasoning"

FAMILIES = [
    Family("E-228", "Dollar non-confirmation (SMT) extreme fade",
           "Foreign flow buys the index and sells the dollar together, so a real WIN breakout to a new window high "
           "comes with WDO near its own window low; when WIN breaks out while WDO still sits in the upper part of "
           "its range, the break is local flow the macro side does not confirm, and dealers lean it back; fade (mirror).",
           {"win_min": [15, 30, 60], "q": [0.3, 0.5, 0.7]}, _smt_divergence, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-229", "Inside-higher-timeframe-candle micro-break fade",
           "A short-term break that still closes inside the previous completed 15/30/60-minute candle is no break "
           "at all for the traders reading that higher timeframe: their resting orders and stops sit at that candle's "
           "high/low, not here, so the small breakout buyers get no follow-through and the move reverts; fade it.",
           {"block_min": [15, 30, 60], "brk_min": [5, 10, 15]}, _htf_inside, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-230", "Day-after-balanced-session micro-break fade",
           "A session that closed almost where it opened (small body for its range) ended in balance: both sides "
           "accepted the range and nobody carried conviction overnight; the next session's participants trade "
           "responsively, so its short-term breaks lack an initiator and are faded.",
           {"th": [0.15, 0.25, 0.35], "brk_min": [10, 15, 30]}, _after_doji, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-231", "Heavy-volume ceiling break fade",
           "When the recent window's high was printed by a bar trading well above normal volume for its minute, a "
           "large seller showed size at that price; a later close just above it runs into that same participant's "
           "remaining offers rather than an empty book, so the break is absorbed and reverts (mirror at lows).",
           {"win_min": [15, 30, 60], "k": [1.25, 1.5, 2.0]}, _heavy_ceiling, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-232", "No-overnight-news day micro-break fade",
           "A session opening almost at yesterday's close (gap small next to the 20-session typical gap) brought no "
           "overnight information to be priced, so no informed parent order is being worked during the day; "
           "intraday breaks are then local noise that liquidity providers fade.",
           {"k": [0.25, 0.5, 0.75], "brk_min": [10, 15, 30]}, _no_gap_day, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-233", "Late MACD signal-cross fade",
           "A MACD signal-line cross in the direction the MACD already sits (bullish cross above zero, bearish below) "
           "is a late, crowded retail trigger arriving after the move; the short-term traders who buy it are the "
           "liquidity the earlier movers exit into, so fade the cross.",
           {"scale": [1, 2, 3], "k": [0.0, 0.5, 1.0]}, _macd_fade, markets=("WIN",), source=SRC, author="agent"),
    Family("E-234", "Front-loaded-session micro-break fade",
           "When the first hour took a larger share of the session's volume than usual for the time, the day's "
           "information was traded early and the rest of the session is digestion by responsive traders; later "
           "short-term breaks have no new initiator behind them, so fade them.",
           {"k": [1.1, 1.25, 1.5], "brk_min": [10, 15, 30]}, _front_loaded, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-235", "Off-peak-minute micro-break fade",
           "At minutes whose seasonal volume (20-session median) sits well below the session average, the "
           "participants who carry information (institutional desks, foreign flow) are mostly absent; breaks then are "
           "small orders through quotes that market makers fade, regardless of whether liquidity is rising or falling.",
           {"q": [0.6, 0.8, 1.0], "brk_min": [10, 15, 30]}, _off_peak, markets=("WIN",), source=SRC, author="agent"),
    Family("E-236", "Jump-free tape micro-break fade",
           "When bipower variation explains all of the recent realized variance, the price moved by many small "
           "steps and no jump (no news, no forced burst): a diffusive, maker-dominated tape; a 10-minute break in "
           "that regime is one more random step that liquidity providers lean back on, so fade it.",
           {"win_min": [30, 60, 90], "th": [0.8, 0.9, 1.0]}, _jump_free, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-237", "Early-extreme side micro-break fade",
           "The day's high or low is often set early; when the first hour made its high before its low, the early "
           "high is the extreme the morning sellers defend and the day's bias is down, so after the first hour "
           "short-term breaks upward toward it are faded (mirror when the low came first).",
           {"first_min": [30, 60, 90], "brk_min": [10, 15, 30]}, _early_extreme, markets=("WIN",), source=SRC,
           author="agent"),
]
