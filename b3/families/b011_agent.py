"""Conveyor batch B-011 (agent, 2026-11-18). Mixed ideas: round numbers, prior-session POC, morning star, Choppiness onset, late-session intraday momentum, volume-climax stall, Raschke Anti, Hoffman IRB, prior-hour extremes, Williams squat."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _typ_range(ctx):
    return ctx.cached("rng_med_sm", lambda: ctx.same_minute(ctx.h - ctx.l, "median"))


def _typ_vol(ctx):
    return ctx.cached("vol_med_sm", lambda: ctx.same_minute(ctx.v, "median"))


def _typ_move(ctx, nb):
    def fn():
        mv = np.abs(ctx.c - ctx.prev(ctx.c, nb))
        return ctx.prev_sessions(mv, "mean")
    return ctx.cached(("absmove_prev", nb), fn)


def _ffill_day(ctx, x, limit):
    return pd.Series(np.asarray(x, float)).groupby(ctx.day).ffill(limit=limit).to_numpy()


# E-099 -------------------------------------------------------------------------------------------
def _round_number_reject(ctx, p):
    step, k = float(p["step"]), p["k"]
    m = k * _typ_range(ctx)
    lu = np.floor(ctx.o / step) * step + step          # first round level above the bar's open
    ld = np.ceil(ctx.o / step) * step - step           # first round level below the bar's open
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    short = (ctx.h >= lu) & (h1 < lu) & (ctx.c < lu - m)
    long = (ctx.l <= ld) & (l1 > ld) & (ctx.c > ld + m)
    return long.astype(int) - short.astype(int)


# E-100 -------------------------------------------------------------------------------------------
def _prev_poc(ctx, bin_):
    def fn():
        b = np.round(ctx.c / bin_)
        df = pd.DataFrame({"d": ctx.day, "b": b, "v": ctx.v})
        s = df.groupby(["d", "b"])["v"].sum()
        idx = s.groupby(level=0).idxmax()
        poc = pd.Series([t[1] for t in idx.values], index=idx.index, dtype=float) * bin_
        poc = poc.reindex(range(int(ctx.day.max()) + 1)).shift(1)
        return poc.to_numpy()[ctx.day]
    return ctx.cached(("prev_poc", bin_), fn)


def _poc_reject(ctx, p):
    bin_, k = float(p["bin"]), p["k"]
    poc = _prev_poc(ctx, bin_)
    m = k * _typ_range(ctx)
    c1, h1, l1 = ctx.prev(ctx.c, 1), ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    long = (c1 > poc) & (l1 > poc) & (ctx.l <= poc) & (ctx.c > poc + m)
    short = (c1 < poc) & (h1 < poc) & (ctx.h >= poc) & (ctx.c < poc - m)
    return long.astype(int) - short.astype(int)


# E-101 -------------------------------------------------------------------------------------------
def _morning_star(ctx, p):
    k, nb = p["k"], ctx.bars(p["run_min"])
    trng = _typ_range(ctx)
    o2, c2, o1, c1 = ctx.prev(ctx.o, 2), ctx.prev(ctx.c, 2), ctx.prev(ctx.o, 1), ctx.prev(ctx.c, 1)
    b2 = np.abs(c2 - o2)
    t2 = ctx.prev(trng, 2)
    big = (t2 > 0) & (b2 >= k * t2)
    small = np.abs(c1 - o1) <= 0.3 * b2
    mid2 = (o2 + c2) / 2.0
    minc = ctx.prev(ctx.roll(ctx.c, nb, "min"), 2)
    maxc = ctx.prev(ctx.roll(ctx.c, nb, "max"), 2)
    long = big & (c2 < o2) & small & (ctx.c > ctx.o) & (ctx.c > mid2) & (c2 <= minc)
    short = big & (c2 > o2) & small & (ctx.c < ctx.o) & (ctx.c < mid2) & (c2 >= maxc)
    return long.astype(int) - short.astype(int)


# E-102 -------------------------------------------------------------------------------------------
def _chop_onset(ctx, p):
    n, th = int(p["n"]), p["th"]

    def chop_fn():
        pc = ctx.prev(ctx.c, 1)
        tr = np.fmax(ctx.h, pc) - np.fmin(ctx.l, pc)
        s = ctx.roll(tr, n, "sum")
        span = ctx.roll(ctx.h, n, "max") - ctx.roll(ctx.l, n, "min")
        with np.errstate(invalid="ignore", divide="ignore"):
            ch = np.where(span > 0, 100.0 * np.log10(s / span) / np.log10(n), np.nan)
        return ch

    chop = ctx.cached(("chop", n), chop_fn)
    had = ctx.roll(chop, n, "max", include_current=False) > 61.8
    onset = ctx.cross(chop < th) & had
    dirn = ctx.c - ctx.prev(ctx.c, n)
    long = onset & (dirn > 0)
    short = onset & (dirn < 0)
    return long.astype(int) - short.astype(int)


# E-103 -------------------------------------------------------------------------------------------
def _late_intraday_momentum(ctx, p):
    nb, late = ctx.bars(p["first_min"]), float(p["late_min"])
    ref = np.where(ctx.bar_in_day == nb - 1, ctx.c, np.nan)
    first = pd.Series(ref).groupby(ctx.day).ffill().to_numpy()
    r1 = first - ctx.prev_session_value("close")
    em = ctx.cached(("ema", ctx.bars(10)), lambda: ctx.ema(ctx.c, ctx.bars(10)))
    window = (ctx.minutes_to_close <= late) & (ctx.minutes_to_close > 10) & (ctx.bar_in_day >= nb)
    long = ctx.cross(window & (r1 > 0) & (ctx.c > em))
    short = ctx.cross(window & (r1 < 0) & (ctx.c < em))
    return long.astype(int) - short.astype(int)


# E-104 -------------------------------------------------------------------------------------------
def _climax_stall(ctx, p):
    k, nb = p["k"], ctx.bars(p["run_min"])
    vm = _typ_vol(ctx)
    vmax = ctx.roll(ctx.v, nb, "max")
    clim = (vm > 0) & (ctx.v >= k * vm) & (ctx.v >= vmax)
    run = ctx.c - ctx.prev(ctx.c, nb)
    typ = _typ_move(ctx, nb)
    up1 = ctx.prev((clim & (run > typ)).astype(float), 1) == 1
    dn1 = ctx.prev((clim & (run < -typ)).astype(float), 1) == 1
    v1, h1, l1, c1 = ctx.prev(ctx.v, 1), ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1), ctx.prev(ctx.c, 1)
    quiet = ctx.v < 0.6 * v1
    short = up1 & quiet & (ctx.h <= h1) & (ctx.c < c1)
    long = dn1 & quiet & (ctx.l >= l1) & (ctx.c > c1)
    return long.astype(int) - short.astype(int)


# E-105 -------------------------------------------------------------------------------------------
def _raschke_anti(ctx, p):
    s, band = int(p["scale"]), p["band"]

    def stoch():
        nk, nd = 7 * s, 10 * s
        hh, ll = ctx.roll(ctx.h, nk, "max"), ctx.roll(ctx.l, nk, "min")
        with np.errstate(invalid="ignore", divide="ignore"):
            raw = np.where(hh > ll, 100.0 * (ctx.c - ll) / (hh - ll), 50.0)
        raw = np.where(np.isnan(hh), np.nan, raw)
        kk = ctx.roll(raw, 4, "mean")
        dd = ctx.roll(kk, nd, "mean")
        return kk, dd

    kk, dd = ctx.cached(("anti", s), stoch)
    k1, k2, d1 = ctx.prev(kk, 1), ctx.prev(kk, 2), ctx.prev(dd, 1)
    d_up = dd > ctx.prev(dd, 3)
    d_dn = dd < ctx.prev(dd, 3)
    long = d_up & (k1 < k2) & (kk > k1) & (k1 <= d1 + band)
    short = d_dn & (k1 > k2) & (kk < k1) & (k1 >= d1 - band)
    return long.astype(int) - short.astype(int)


# E-106 -------------------------------------------------------------------------------------------
def _hoffman_irb(ctx, p):
    n, k = int(p["ema_bars"]), p["k"]
    em = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    slope = em - ctx.prev(em, 5)
    trng = _typ_range(ctx)
    up = (trng > 0) & (slope > k * trng)
    dn = (trng > 0) & (slope < -k * trng)
    rng = ctx.h - ctx.l
    bull = up & (rng > 0) & (np.maximum(ctx.o, ctx.c) <= ctx.h - 0.45 * rng)
    bear = dn & (rng > 0) & (np.minimum(ctx.o, ctx.c) >= ctx.l + 0.45 * rng)
    hi = ctx.prev(_ffill_day(ctx, np.where(bull, ctx.h, np.nan), 3), 1)
    lo = ctx.prev(_ffill_day(ctx, np.where(bear, ctx.l, np.nan), 3), 1)
    long = ctx.cross(ctx.c > hi)
    short = ctx.cross(ctx.c < lo)
    return long.astype(int) - short.astype(int)


# E-107 -------------------------------------------------------------------------------------------
def _prev_hour_levels(ctx):
    def fn():
        df = pd.DataFrame({"d": ctx.day, "hr": ctx.minute // 60, "h": ctx.h, "l": ctx.l})
        g = df.groupby(["d", "hr"]).agg(hh=("h", "max"), ll=("l", "min")).reset_index()
        g["ph"] = g.groupby("d")["hh"].shift(1)
        g["pl"] = g.groupby("d")["ll"].shift(1)
        m = df.merge(g[["d", "hr", "ph", "pl"]], on=["d", "hr"], how="left")
        return m["ph"].to_numpy(float), m["pl"].to_numpy(float)
    return ctx.cached("prev_hour_hl", fn)


def _prev_hour_reject(ctx, p):
    k = p["k"]
    ph, pl = _prev_hour_levels(ctx)
    m = k * _typ_range(ctx)
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    short = (ctx.h >= ph) & (h1 < ph) & (ctx.c < ph - m)
    long = (ctx.l <= pl) & (l1 > pl) & (ctx.c > pl + m)
    return long.astype(int) - short.astype(int)


# E-108 -------------------------------------------------------------------------------------------
def _squat_break(ctx, p):
    k, m = p["k"], int(p["m"])
    rng = ctx.h - ctx.l
    with np.errstate(invalid="ignore", divide="ignore"):
        mfi = np.where(ctx.v > 0, rng / ctx.v, np.nan)
    vm = _typ_vol(ctx)
    squat = (ctx.v > ctx.prev(ctx.v, 1)) & (mfi < ctx.prev(mfi, 1)) & (vm > 0) & (ctx.v >= k * vm)
    hi = ctx.prev(_ffill_day(ctx, np.where(squat, ctx.h, np.nan), m), 1)
    lo = ctx.prev(_ffill_day(ctx, np.where(squat, ctx.l, np.nan), m), 1)
    long = ctx.cross(ctx.c > hi)
    short = ctx.cross(ctx.c < lo)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-099", "Round-number rejection",
           "Retail and discretionary WIN traders anchor take-profits, limit entries and option strikes on round index "
           "levels (multiples of 250/500/1000 points), so resting liquidity clusters there; the first bar that reaches "
           "the level from below and closes back under it shows that liquidity absorbing the push, so fade away from it.",
           {"step": [250, 500, 1000], "k": [0.0, 0.25, 0.5]}, _round_number_reject, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-100", "Prior-session POC rejection",
           "Yesterday's point of control (the price bin with the most volume) is where the largest share of yesterday's "
           "inventory was built; those holders defend their cost, so the first touch of it from one side that closes "
           "back on that side meets their orders and price moves away from the level.",
           {"bin": [50, 100, 200], "k": [0.0, 0.25, 0.5]}, _poc_reject, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-101", "Morning/evening star after a run",
           "A large bar making the lowest close of a run, followed by a small indecision bar and then a bar closing back "
           "above the large bar's body midpoint, shows the run's last burst found no follow-through and buyers retook "
           "half its ground; the late sellers of the burst are trapped, so follow the three-bar reversal (mirror).",
           {"k": [1.0, 1.5, 2.0], "run_min": [15, 30, 60]}, _morning_star, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-102", "Choppiness-index trend onset",
           "Dreiss' Choppiness Index compares the summed true range to the net high-low span; after a choppy stretch "
           "(above 61.8) a fall below a low threshold means the bars have started to line up in one direction, i.e. "
           "the balance broke and one side is now initiating; follow the direction of the window's move.",
           {"n": [10, 14, 20], "th": [35, 40, 45]}, _chop_onset, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-103", "Late-session intraday momentum (first-window sign)",
           "Gao, Han, Li and Zhou: the market's first half-hour return from the prior close predicts the last "
           "half-hour, because institutional rebalancing and informed orders delayed to the close trade the same way; "
           "in the closing window, enter in the sign of the opening return whenever price is on that side of a short EMA.",
           {"first_min": [30, 60], "late_min": [60, 90, 120]}, _late_intraday_momentum, markets=("WIN",),
           source="Intraday Momentum: The First Half-Hour Return Predicts the Last Half-Hour Return (Alpha Architect) "
                  "https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/",
           author="agent"),
    Family("E-104", "Volume-climax stall fade",
           "At the end of a run, the bar with the highest volume of the window (and far above normal for its minute) is "
           "the buying climax where the last chasers and stops are filled; when the next bar trades much less, fails to "
           "extend and closes below the climax close, demand is spent, so fade the run (mirror for a selling climax).",
           {"k": [2.0, 3.0, 4.0], "run_min": [15, 30]}, _climax_stall, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-105", "Raschke Anti stochastic hook",
           "Raschke's 'Anti': the slow %D sets the momentum trend, the fast %K pulls back toward it and then hooks back "
           "in the trend direction; the hook marks the end of the counter-trend correction, when trend traders re-enter "
           "and the correction traders cover, so follow the hook (mirror).",
           {"scale": [1, 2, 3], "band": [0, 5, 10]}, _raschke_anti, markets=("WIN",),
           source="Anti setup discussion (MQL5 forum) https://www.mql5.com/en/forum/198172", author="agent"),
    Family("E-106", "Hoffman inventory retracement bar",
           "In a steep EMA trend, a bar whose open and close sit at least 45% below its high is counter-trend inventory "
           "being worked by short-term sellers while institutions pause; a close above that bar's high within three "
           "bars shows the counter-trend selling is done and the trend side resumes, so follow it (mirror).",
           {"ema_bars": [10, 20, 40], "k": [0.5, 1.0, 1.5]}, _hoffman_irb, markets=("WIN",),
           source="The inventory retracement bar (IRB) (WH SelfInvest) "
                  "https://www.whselfinvest.de/en-de/trading-platform/trader-tools/technical-analysis/13-rob-hoffman-irb-inventory-retracement-bar",
           author="agent"),
    Family("E-107", "Previous clock-hour extreme rejection",
           "Hourly candles are what most desks and chart traders read, so the completed previous hour's high and low "
           "hold resting orders and take-profits; the first bar of the session that pokes through such a level and "
           "closes back inside meets that liquidity and the poke's buyers are trapped, so fade back into the hour's range.",
           {"k": [0.0, 0.25, 0.5]}, _prev_hour_reject, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-108", "Williams squat-bar break",
           "Bill Williams' squat bar (volume up while range per contract falls) is a standoff where heavy two-sided trade "
           "makes no progress; whichever side then closes beyond the squat bar's range within a few bars has absorbed "
           "the other, whose stops sit just beyond it, so follow the break.",
           {"k": [1.0, 1.5, 2.0], "m": [1, 3, 5]}, _squat_break, markets=("WIN",),
           source="Market facilitation index (Wikipedia) https://en.wikipedia.org/wiki/Market_facilitation_index",
           author="agent"),
]
