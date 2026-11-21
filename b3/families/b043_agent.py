"""Conveyor batch B-043 (agent, 2026-11-21). New regime filters for short-box breaks (cross-market decorrelation, bar shape, volume evenness, momentum), plus level, profile and day-type ideas."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family

_TICK = 5.0     # WIN tick in points (all families here are WIN only)


def _box(ctx, win_min):
    """Short box of the last win_min minutes (excluding the bar) and the bars where a close first breaks it."""
    nb = ctx.bars(win_min)

    def mk():
        hi = ctx.roll(ctx.h, nb, "max", include_current=False)
        lo = ctx.roll(ctx.l, nb, "min", include_current=False)
        with np.errstate(invalid="ignore"):
            up = ctx.cross(ctx.c > hi)
            dn = ctx.cross(ctx.c < lo)
        return hi, lo, np.asarray(up, bool), np.asarray(dn, bool)
    return ctx.cached(("b043_box", nb), mk)


def _sig(long, short):
    long = np.nan_to_num(np.asarray(long, float), nan=0.0) > 0
    short = np.nan_to_num(np.asarray(short, float), nan=0.0) > 0
    return long.astype(int) - short.astype(int)


# E-428 ---------------------------------------------------------------------------------------------
def _decorrelated_fade(ctx, p):
    nb = ctx.bars(p["win_min"])
    oc = ctx.other_close()
    with np.errstate(divide="ignore", invalid="ignore"):
        x = np.log(ctx.c / ctx.prev(ctx.c))
        y = np.log(oc / ctx.prev(oc))
        x = np.where(np.isfinite(x), x, np.nan)
        y = np.where(np.isfinite(y), y, np.nan)
        mx, my = ctx.roll(x, nb), ctx.roll(y, nb)
        mxy, mxx, myy = ctx.roll(x * y, nb), ctx.roll(x * x, nb), ctx.roll(y * y, nb)
        vx, vy = mxx - mx * mx, myy - my * my
        corr = np.where((vx > 0) & (vy > 0), (mxy - mx * my) / np.sqrt(vx * vy), np.nan)
        reg = corr > p["th"]
    _, _, up, dn = _box(ctx, 15)
    return _sig(dn & reg, up & reg)


# E-429 ---------------------------------------------------------------------------------------------
def _absorbed_break_fade(ctx, p):
    ratio = ctx.v / np.maximum(ctx.h - ctx.l, _TICK)
    typ = ctx.cached("b043_vpr_med", lambda: ctx.same_minute(ratio, "median"))
    with np.errstate(invalid="ignore"):
        heavy = ratio >= p["k"] * typ
    _, _, up, dn = _box(ctx, p["win_min"])
    return _sig(dn & heavy, up & heavy)


# E-430 ---------------------------------------------------------------------------------------------
def _wicky_tape_fade(ctx, p):
    nb = ctx.bars(p["reg_min"])
    bs = np.abs(ctx.c - ctx.o) / np.maximum(ctx.h - ctx.l, _TICK)
    mbs = ctx.roll(bs, nb, "mean")
    with np.errstate(invalid="ignore"):
        reg = mbs < p["q"]
    _, _, up, dn = _box(ctx, 15)
    return _sig(dn & reg, up & reg)


# E-431 ---------------------------------------------------------------------------------------------
def _toward_vwap_follow(ctx, p):
    hi, lo, up, dn = _box(ctx, p["win_min"])
    vw = ctx.vwap()
    hgt = hi - lo
    with np.errstate(invalid="ignore"):
        long = up & (hgt > 0) & (vw - ctx.c >= p["k"] * hgt)
        short = dn & (hgt > 0) & (ctx.c - vw >= p["k"] * hgt)
    return _sig(long, short)


# E-432 ---------------------------------------------------------------------------------------------
def _hvn_ahead(ctx, binw, nahead=2):
    n = ctx.n
    up_avg, dn_avg, mean_bin = np.full(n, np.nan), np.full(n, np.nan), np.full(n, np.nan)
    day = ctx.day
    starts = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
    ends = np.r_[starts[1:], n]
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    for s, e in zip(starts, ends):
        b = np.floor(tp[s:e] / binw).astype(np.int64)
        cb = np.floor(ctx.c[s:e] / binw).astype(np.int64)
        lo_b = min(b.min(), cb.min()) - nahead - 1
        hi_b = max(b.max(), cb.max()) + nahead + 1
        rows = e - s
        M = np.zeros((rows, hi_b - lo_b + 1))
        M[np.arange(rows), b - lo_b] = np.nan_to_num(ctx.v[s:e])
        C = np.cumsum(M, axis=0) - M                       # profile of the session BEFORE this bar
        tot = C.sum(axis=1)
        occ = (C > 0).sum(axis=1)
        cs = np.concatenate([np.zeros((rows, 1)), np.cumsum(C, axis=1)], axis=1)
        i = cb - lo_b
        r = np.arange(rows)
        up_avg[s:e] = (cs[r, i + 1 + nahead] - cs[r, i + 1]) / nahead
        dn_avg[s:e] = (cs[r, i] - cs[r, i - nahead]) / nahead
        mean_bin[s:e] = np.where(occ > 0, tot / np.maximum(occ, 1), np.nan)
    return up_avg, dn_avg, mean_bin


def _hvn_break_fade(ctx, p):
    up_avg, dn_avg, mb = ctx.cached(("b043_hvn", p["bin_pts"]), lambda: _hvn_ahead(ctx, p["bin_pts"]))
    _, _, up, dn = _box(ctx, 15)
    with np.errstate(invalid="ignore"):
        short = up & (up_avg >= p["m"] * mb)
        long = dn & (dn_avg >= p["m"] * mb)
    return _sig(long, short)


# E-433 ---------------------------------------------------------------------------------------------
def _one_sided_ib_follow(ctx, p):
    nb = ctx.bars(p["ib_min"])
    first = ctx.bar_in_day < nb
    ibh = pd.Series(np.where(first, ctx.h, np.nan)).groupby(ctx.day).transform("max").to_numpy()
    ibl = pd.Series(np.where(first, ctx.l, np.nan)).groupby(ctx.day).transform("min").to_numpy()
    done = ~first
    sh = ctx.session_high(include_current=True)
    sl = ctx.session_low(include_current=True)
    with np.errstate(invalid="ignore"):
        ext_up, ext_dn = sh > ibh, sl < ibl
    _, _, up, dn = _box(ctx, p["win_min"])
    long = up & done & ext_up & ~ext_dn
    short = dn & done & ext_dn & ~ext_up
    return _sig(long, short)


# E-434 ---------------------------------------------------------------------------------------------
def _daily_streak_fade(ctx, p):
    m = int(p["m"])
    nd = int(ctx.day.max()) + 1
    dc = pd.Series(ctx.c).groupby(ctx.day).last().reindex(range(nd))
    r = dc.diff()
    down = pd.Series(True, index=r.index)
    upk = pd.Series(True, index=r.index)
    for k in range(1, m + 1):
        rk = r.shift(k)
        down &= (rk < 0)
        upk &= (rk > 0)
    down = down.to_numpy()[ctx.day]
    upk = upk.to_numpy()[ctx.day]
    _, _, up, dn = _box(ctx, p["win_min"])
    return _sig(dn & down, up & upk)


# E-435 ---------------------------------------------------------------------------------------------
def _prev_hour_bars(ctx):
    hr = (ctx.minute // 60).astype(np.int64)
    key = ctx.day.astype(np.int64) * 100 + hr
    s = pd.DataFrame({"k": key, "o": ctx.o, "h": ctx.h, "l": ctx.l, "c": ctx.c})
    agg = s.groupby("k", sort=True).agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"))
    kk = agg.index.to_numpy()
    same = np.r_[False, (kk[1:] // 100) == (kk[:-1] // 100)]
    prev = agg.shift(1)
    prev.loc[~same, :] = np.nan
    mp = prev.reindex(key)
    return mp["o"].to_numpy(float), mp["h"].to_numpy(float), mp["l"].to_numpy(float), mp["c"].to_numpy(float)


def _hour_wick_fade(ctx, p):
    po, ph, pl, pc = ctx.cached("b043_prev_hour", lambda: _prev_hour_bars(ctx))
    f = p["f"]
    rng = ph - pl
    btop, bbot = np.maximum(po, pc), np.minimum(po, pc)
    with np.errstate(invalid="ignore"):
        zone_up = (rng > 0) & (ph - btop >= f * rng) & (ctx.c > btop) & (ctx.c <= ph)
        zone_dn = (rng > 0) & (bbot - pl >= f * rng) & (ctx.c < bbot) & (ctx.c >= pl)
    _, _, up, dn = _box(ctx, p["win_min"])
    return _sig(dn & zone_dn, up & zone_up)


# E-436 ---------------------------------------------------------------------------------------------
def _neutral_rsi_fade(ctx, p):
    def mk():
        d = ctx.c - ctx.prev(ctx.c)
        ag = ctx.roll(np.where(np.isfinite(d), np.maximum(d, 0.0), np.nan), 14)
        al = ctx.roll(np.where(np.isfinite(d), np.maximum(-d, 0.0), np.nan), 14)
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(ag + al > 0, 100.0 * ag / (ag + al), 50.0 + 0.0 * ag)
    rsi = ctx.cached("b043_rsi14", mk)
    with np.errstate(invalid="ignore"):
        neutral = np.abs(rsi - 50.0) < p["band"]
    _, _, up, dn = _box(ctx, p["win_min"])
    return _sig(dn & neutral, up & neutral)


# E-437 ---------------------------------------------------------------------------------------------
def _even_volume_fade(ctx, p):
    nb = ctx.bars(p["win_min"])

    def mk():
        mu = ctx.roll(ctx.v, nb, "mean")
        sd = ctx.roll(ctx.v, nb, "std")
        with np.errstate(invalid="ignore", divide="ignore"):
            cv = np.where(mu > 0, sd / mu, np.nan)
        return cv, ctx.prev_sessions(cv, "mean")
    cv, typ = ctx.cached(("b043_cv", nb), mk)
    with np.errstate(invalid="ignore"):
        reg = cv < p["k"] * typ
    _, _, up, dn = _box(ctx, 15)
    return _sig(dn & reg, up & reg)


FAMILIES = [
    Family("E-428", "Index-dollar decorrelation micro-break fade",
           "WIN and WDO normally move against each other minute by minute because foreign flow trades both; when the "
           "rolling correlation of their 1-bar returns rises to near zero or positive, that macro flow is absent and "
           "each book is run by local liquidity providers, so a 15-minute box break in WIN has no persistent initiator "
           "behind it and is leaned back; fade it.",
           {"win_min": [30, 60, 120], "th": [-0.3, -0.15, 0.0]}, _decorrelated_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-429", "Absorbed break-bar fade",
           "A close through the short box made by a bar that traded far more contracts per point of range than usual "
           "for its minute means the breakers met a large passive order that filled them without letting price run; "
           "the absorber holds the other side and the breakers are offside, so fade the break bar.",
           {"k": [1.0, 1.5, 2.0], "win_min": [10, 15, 30]}, _absorbed_break_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-430", "Wick-dominated tape micro-break fade",
           "When recent bars close near where they opened while trading both ways inside the bar (small average body "
           "share of the range), every push inside a bar is answered within the same bar by resting liquidity; a "
           "15-minute box break in such a two-way tape is one more intrabar-style probe that gets answered, so fade it.",
           {"q": [0.35, 0.4, 0.45], "reg_min": [30, 60, 120]}, _wicky_tape_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-431", "Break toward the session VWAP follow",
           "A short-box break that points toward a session VWAP lying several box heights away has room to run and a "
           "magnet ahead: benchmarked desks behind the VWAP are buyers (sellers) on the way back to value and the "
           "box's stops sit behind the break; follow only breaks in the direction of VWAP.",
           {"k": [0.5, 1.0, 2.0], "win_min": [10, 15, 30]}, _toward_vwap_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-432", "Break into today's heavy-volume zone fade",
           "A short-box break whose next price bins already traded much more volume today than the session's average "
           "bin runs into the inventory of everyone who transacted there; those holders sell their break-even on the "
           "way up (buy it on the way down), so the break stalls in the heavy zone and reverts; fade it.",
           {"bin_pts": [50, 100, 200], "m": [1.0, 1.5, 2.0]}, _hvn_break_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-433", "One-sided initial-balance extension break follow",
           "When the session has extended beyond only one side of its initial balance, the other-timeframe participant "
           "has shown its hand in that direction and the opposite side has not even tested its edge; short-box breaks "
           "in the extension direction carry that initiator's continuing orders, so follow only those.",
           {"ib_min": [30, 60, 90], "win_min": [10, 15, 30]}, _one_sided_ib_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-434", "Multi-day streak break fade",
           "After one or more consecutive down (up) daily closes, short-term holders are already loaded with the "
           "multi-day move and swing traders look for the bounce (short-horizon daily reversal); intraday breaks that "
           "extend the streak's direction are the last weak hands and get bought (sold), so fade only those breaks.",
           {"m": [1, 2, 3], "win_min": [10, 15, 30]}, _daily_streak_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-435", "Prior-hour rejection-wick zone break fade",
           "A completed clock hour with a long upper (lower) wick shows sellers (buyers) who rejected those prices an "
           "hour ago; a short-box break that carries the price back into that wick zone meets the same resting "
           "orders that made the wick, so fade the break while it is still inside the zone.",
           {"f": [0.3, 0.4, 0.5], "win_min": [10, 15, 30]}, _hour_wick_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-436", "Neutral-momentum break fade",
           "A short-box break that happens while the 14-bar RSI is still near 50 is a level giving way without any "
           "accumulated one-sided pressure behind it: the buyers and sellers of the last bars are balanced, so the "
           "break is a stop poke rather than a move, and the balanced book takes it back; fade it.",
           {"band": [10, 15, 20], "win_min": [10, 15, 30]}, _neutral_rsi_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-437", "Even-volume tape micro-break fade",
           "When bar volumes over the last window are much more even than usual (low coefficient of variation versus "
           "the previous sessions), trade is coming from steady market makers and time-sliced algos with no bursts of "
           "informed size; a 15-minute box break in that tape has no one-off initiator behind it, so fade it.",
           {"k": [0.7, 0.8, 0.9], "win_min": [30, 60, 120]}, _even_volume_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
