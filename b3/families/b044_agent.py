"""Conveyor batch B-044 (agent, 2026-11-21). New tape-shape regimes for short-box break fades (kurtosis, range clustering, range evenness, reversion speed, ordinal entropy), break-bar and box-shape triggers, a bar-pressure indicator turn and the cash-open level."""
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
    return ctx.cached(("b044_box", nb), mk)


def _sig(long, short):
    long = np.nan_to_num(np.asarray(long, float), nan=0.0) > 0
    short = np.nan_to_num(np.asarray(short, float), nan=0.0) > 0
    return long.astype(int) - short.astype(int)


def _fade(ctx, reg, win_min=15):
    reg = np.nan_to_num(np.asarray(reg, float), nan=0.0) > 0
    _, _, up, dn = _box(ctx, win_min)
    return _sig(dn & reg, up & reg)


# E-438 ---------------------------------------------------------------------------------------------
def _low_kurtosis_fade(ctx, p):
    nb = ctx.bars(p["win_min"])

    def mk():
        x = ctx.c - ctx.prev(ctx.c)
        m1, m2 = ctx.roll(x, nb), ctx.roll(x ** 2, nb)
        m3, m4 = ctx.roll(x ** 3, nb), ctx.roll(x ** 4, nb)
        var = m2 - m1 ** 2
        c4 = m4 - 4 * m1 * m3 + 6 * m1 ** 2 * m2 - 3 * m1 ** 4
        with np.errstate(invalid="ignore", divide="ignore"):
            k = np.where(var > 0, c4 / var ** 2 - 3.0, np.nan)
        return k, ctx.prev_sessions(k, "mean")
    k, typ = ctx.cached(("b044_kurt", nb), mk)
    with np.errstate(invalid="ignore"):
        reg = (typ > 0) & (k < p["k"] * typ)
    return _fade(ctx, reg)


# E-439 ---------------------------------------------------------------------------------------------
def _outsized_break_bar_fade(ctx, p):
    hi, lo, up, dn = _box(ctx, p["win_min"])
    hgt = hi - lo
    with np.errstate(invalid="ignore"):
        big = (hgt > 0) & ((ctx.h - ctx.l) >= p["k"] * hgt)
    return _sig(dn & big, up & big)


# E-440 ---------------------------------------------------------------------------------------------
def _unclustered_vol_fade(ctx, p):
    nb = ctx.bars(p["win_min"])

    def mk():
        r = ctx.h - ctx.l
        r1 = ctx.prev(r)
        mx, my = ctx.roll(r1, nb), ctx.roll(r, nb)
        mxy, mxx, myy = ctx.roll(r1 * r, nb), ctx.roll(r1 * r1, nb), ctx.roll(r * r, nb)
        vx, vy = mxx - mx * mx, myy - my * my
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where((vx > 0) & (vy > 0), (mxy - mx * my) / np.sqrt(vx * vy), np.nan)
    corr = ctx.cached(("b044_racf", nb), mk)
    with np.errstate(invalid="ignore"):
        reg = corr < p["th"]
    return _fade(ctx, reg)


# E-441 ---------------------------------------------------------------------------------------------
def _close_box_inside_wick_fade(ctx, p):
    nb = ctx.bars(p["win_min"])
    hi, lo, _, _ = _box(ctx, p["win_min"])
    chi = ctx.roll(ctx.c, nb, "max", include_current=False)
    clo = ctx.roll(ctx.c, nb, "min", include_current=False)
    hgt = hi - lo
    with np.errstate(invalid="ignore"):
        up = ctx.cross(ctx.c > chi) & (ctx.c <= hi) & (hgt > 0) & (hi - chi >= p["f"] * hgt)
        dn = ctx.cross(ctx.c < clo) & (ctx.c >= lo) & (hgt > 0) & (clo - lo >= p["f"] * hgt)
    return _sig(dn, up)


# E-442 ---------------------------------------------------------------------------------------------
def _even_range_fade(ctx, p):
    nb = ctx.bars(p["win_min"])

    def mk():
        r = ctx.h - ctx.l
        mu, sd = ctx.roll(r, nb, "mean"), ctx.roll(r, nb, "std")
        with np.errstate(invalid="ignore", divide="ignore"):
            cv = np.where(mu > 0, sd / mu, np.nan)
        return cv, ctx.prev_sessions(cv, "mean")
    cv, typ = ctx.cached(("b044_rcv", nb), mk)
    with np.errstate(invalid="ignore"):
        reg = cv < p["k"] * typ
    return _fade(ctx, reg)


# E-443 ---------------------------------------------------------------------------------------------
def _fast_reversion_fade(ctx, p):
    nb = ctx.bars(p["win_min"])

    def mk():
        dev = ctx.c - ctx.roll(ctx.c, nb, "mean")
        d1 = ctx.prev(dev)
        mx, my = ctx.roll(d1, nb), ctx.roll(dev, nb)
        mxy, mxx = ctx.roll(d1 * dev, nb), ctx.roll(d1 * d1, nb)
        vx = mxx - mx * mx
        with np.errstate(invalid="ignore", divide="ignore"):
            phi = np.where(vx > 0, (mxy - mx * my) / vx, np.nan)
        return phi, ctx.prev_sessions(phi, "mean")
    phi, typ = ctx.cached(("b044_phi", nb), mk)
    with np.errstate(invalid="ignore"):
        reg = phi < typ - p["d"]
    return _fade(ctx, reg)


# E-444 ---------------------------------------------------------------------------------------------
def _bop_turn_fade(ctx, p):
    n = int(p["n"])
    bop = (ctx.c - ctx.o) / np.maximum(ctx.h - ctx.l, _TICK)
    s = ctx.roll(bop, n, "mean")
    s1 = ctx.prev(s)
    th = p["th"]
    with np.errstate(invalid="ignore"):
        short = (s1 > th) & (s <= th)
        long = (s1 < -th) & (s >= -th)
    return _sig(long, short)


# E-445 ---------------------------------------------------------------------------------------------
def _cash_open_level(ctx):
    after = ctx.minute >= 600                       # B3 cash-equity open, 10:00 Sao Paulo
    mark = np.asarray(ctx.cross(after), bool) & after
    lvl = pd.Series(np.where(mark, ctx.o, np.nan)).groupby(ctx.day).ffill().to_numpy()
    return lvl


def _cash_open_cross_fade(ctx, p):
    nb = ctx.bars(p["away_min"])
    L = ctx.cached("b044_cash_open", lambda: _cash_open_level(ctx))
    typ = ctx.cached("b044_typ_rng", lambda: ctx.prev_sessions(ctx.h - ctx.l, "mean"))
    L1 = ctx.prev(L)
    with np.errstate(invalid="ignore"):
        ok = np.isfinite(L1) & np.isfinite(L)
        dn = np.asarray(ctx.cross(ctx.c < L), bool) & ok
        up = np.asarray(ctx.cross(ctx.c > L), bool) & ok
        far_above = ctx.roll(ctx.c - L, nb, "max", include_current=False) >= p["k"] * typ
        far_below = ctx.roll(L - ctx.c, nb, "max", include_current=False) >= p["k"] * typ
    return _sig(dn & far_above, up & far_below)


# E-446 ---------------------------------------------------------------------------------------------
def _perm_entropy_fade(ctx, p):
    nb = ctx.bars(p["win_min"])

    def mk():
        a, b, d = ctx.prev(ctx.c, 2), ctx.prev(ctx.c, 1), ctx.c
        valid = np.isfinite(a) & np.isfinite(b)
        with np.errstate(invalid="ignore"):
            code = (b > a).astype(int) * 4 + (d > b).astype(int) * 2 + (d > a).astype(int)
        H = np.zeros(ctx.n)
        bad = np.zeros(ctx.n, bool)
        for k in (0, 1, 3, 4, 6, 7):
            ind = np.where(valid, (code == k).astype(float), np.nan)
            q = ctx.roll(ind, nb, "mean")
            bad |= ~np.isfinite(q)
            with np.errstate(invalid="ignore", divide="ignore"):
                H -= np.where(q > 0, q * np.log(np.where(q > 0, q, 1.0)), 0.0)
        H = np.where(bad, np.nan, H / np.log(6.0))
        return H, ctx.prev_sessions(H, "mean")
    H, typ = ctx.cached(("b044_pe", nb), mk)
    with np.errstate(invalid="ignore"):
        reg = H >= typ + p["d"]
    return _fade(ctx, reg)


# E-447 ---------------------------------------------------------------------------------------------
def _rising_floor_follow(ctx, p):
    nb = ctx.bars(p["win_min"])
    half = max(1, nb // 2)
    hi, lo, up, dn = _box(ctx, p["win_min"])
    lo_recent = ctx.roll(ctx.l, half, "min", include_current=False)
    hi_recent = ctx.roll(ctx.h, half, "max", include_current=False)
    hgt = hi - lo
    with np.errstate(invalid="ignore"):
        long = up & (hgt > 0) & (lo_recent - lo >= p["f"] * hgt)
        short = dn & (hgt > 0) & (hi - hi_recent >= p["f"] * hgt)
    return _sig(long, short)


FAMILIES = [
    Family("E-438", "Low-kurtosis tape micro-break fade",
           "When the recent 1-bar price changes are thin-tailed compared with the previous sessions (low excess "
           "kurtosis), the tape is made of small two-way trades with no jumps from informed size; a 15-minute box "
           "break in that tape is a drift of liquidity providers' quotes rather than news, and they lean it back, so fade it.",
           {"k": [0.5, 0.75, 1.0], "win_min": [30, 60, 120]}, _low_kurtosis_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-439", "Outsized break-bar fade",
           "A break of the short box made by a single bar whose own range is a large share of (or bigger than) the whole "
           "box spends the move in one burst of market orders that runs the stops behind the edge; once those stops are "
           "filled no initiator is left and the stop-run sellers (buyers) are the other side, so fade the break bar.",
           {"k": [0.5, 0.75, 1.0], "win_min": [10, 15, 30]}, _outsized_break_bar_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-440", "Unclustered-volatility micro-break fade",
           "Volatility normally clusters: a wide bar is followed by another when information arrives. When the lag-1 "
           "correlation of bar ranges in the recent window is low, ranges are random noise rather than an information "
           "flow, so a 15-minute box break carries no news and the passive side takes it back; fade it.",
           {"th": [0.0, 0.15, 0.3], "win_min": [30, 60, 120]}, _unclustered_vol_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-441", "Close-box break inside the wick box fade",
           "A close beyond the highest (lowest) close of the window that is still inside the window's wick high (low) "
           "only reaches prices that were already offered and rejected intrabar; the sellers who printed the wick are "
           "still there and chart traders who buy the closing break are the liquidity, so fade it.",
           {"f": [0.1, 0.2, 0.3], "win_min": [10, 15, 30]}, _close_box_inside_wick_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-442", "Even-range tape micro-break fade",
           "When bar ranges over the window are much more uniform than usual (low coefficient of variation versus the "
           "previous sessions), price is being walked by steady quoting with no bursts; a 15-minute box break in that "
           "tape is the regular oscillation reaching an edge, not an expansion, so fade it.",
           {"k": [0.7, 0.8, 0.9], "win_min": [30, 60, 120]}, _even_range_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-443", "Fast-reverting deviation micro-break fade",
           "Fit the AR(1) coefficient of the price's deviation from its rolling mean: when it is below its usual level, "
           "deviations die out faster than normal, i.e. inventory-holding market makers are actively pulling price back "
           "to the mean; a 15-minute box break in that state is a deviation they will absorb, so fade it.",
           {"d": [0.0, 0.05, 0.1], "win_min": [30, 60, 120]}, _fast_reversion_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-444", "Balance-of-power exhaustion turn fade",
           "The rolling mean of (close-open)/(high-low) measures how consistently bars close in the buyers' (sellers') "
           "favour; when a stretch of one-sided bar pressure ends (the mean falls back through its threshold), the "
           "aggressive side has finished and the late chasers are offside, so trade against the stretch on the turn.",
           {"n": [10, 14, 20], "th": [0.15, 0.2, 0.25]}, _bop_turn_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-445", "Cash-open price cross fade",
           "WIN trades from 09:00 but the cash equities open at 10:00, and the price at that moment is where index "
           "arbitrage and fund rebalancing set their reference; when price returns from well away and closes through "
           "that level, the arbitrage desks defend it as a pivot, so the cross fails more often than not: fade it.",
           {"away_min": [10, 20, 30], "k": [1.0, 2.0, 3.0]}, _cash_open_cross_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-446", "High ordinal-entropy tape micro-break fade",
           "Permutation entropy of the order of three consecutive closes measures how random the tape is; when it is above "
           "its usual level, no ordinal pattern (trend runs) dominates, so nobody is working a directional order and a "
           "15-minute box break is noise that the two-sided book absorbs: fade it.",
           {"d": [0.0, 0.01, 0.02], "win_min": [30, 60, 120]}, _perm_entropy_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-447", "Rising-floor box break follow",
           "A box whose lows rose markedly in its second half while the top held (ascending-triangle shape) shows buyers "
           "lifting their bids under a fixed seller; when the close breaks the top the seller is exhausted and the stops "
           "of shorts who sold the flat top are bought, so follow the break (mirror for a falling ceiling).",
           {"f": [0.25, 0.4, 0.55], "win_min": [10, 15, 30]}, _rising_floor_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
