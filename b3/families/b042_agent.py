"""Conveyor batch B-042 (agent, 2026-11-21). Regime and level conditions not used before (price impact per contract, yesterday's settlement vs its VWAP, failed opening drive, dollar parked mid-box, yesterday's midpoint, the morning range, the futures-only evening, box rotation, braided EMAs, same-sign index/dollar day), each firing on a single bar."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


# ----------------------------------------------------------------------------------------------- helpers

def _box(ctx, win_min):
    """Rolling box of the previous `win_min` minutes (current bar excluded) and its first close-breaks."""
    def make():
        nb = ctx.bars(win_min)
        hi = ctx.roll(ctx.h, nb, "max", include_current=False)
        lo = ctx.roll(ctx.l, nb, "min", include_current=False)
        up = ctx.cross(ctx.c > hi)
        dn = ctx.cross(ctx.c < lo)
        return up, dn, hi, lo
    return ctx.cached(("b042_box", win_min), make)


def _fade(ctx, win_min, cond):
    """Sell an up-break, buy a down-break of the box, only where `cond` holds."""
    up, dn, _, _ = _box(ctx, win_min)
    cond = np.asarray(cond, bool)
    return (dn & cond).astype(int) - (up & cond).astype(int)


def _yesterday(ctx, values, agg):
    """Previous session's aggregate of `values` on every bar (NaN on the first session)."""
    s = pd.Series(np.asarray(values, float)).groupby(ctx.day).agg(agg)
    s = s.reindex(range(int(ctx.day.max()) + 1)).shift(1)
    return s.to_numpy()[ctx.day]


def _session_ffill(ctx, values):
    return pd.Series(np.asarray(values, float)).groupby(ctx.day).ffill().to_numpy()


# ----------------------------------------------------------------------------------------------- families

def _cheap_move_fade(ctx, p):
    k, wm = p["k"], p["win_min"]

    def make():
        nb = ctx.bars(wm)
        r = np.abs(ctx.c / ctx.prev(ctx.c, 1) - 1.0)
        sr = ctx.roll(r, nb, "sum")
        sv = ctx.roll(ctx.v, nb, "sum")
        with np.errstate(divide="ignore", invalid="ignore"):
            illiq = np.where(sv > 0, sr / sv, np.nan)
        typ = ctx.same_minute(illiq, "median")
        return illiq, typ
    illiq, typ = ctx.cached(("b042_illiq", wm), make)
    with np.errstate(invalid="ignore"):
        cond = illiq > k * typ
    return _fade(ctx, wm, cond)


def _settled_at_vwap_fade(ctx, p):
    th, wm = p["th"], p["win_min"]

    def make():
        yv = _yesterday(ctx, ctx.vwap(), "last")
        yc = _yesterday(ctx, ctx.c, "last")
        yh = _yesterday(ctx, ctx.h, "max")
        yl = _yesterday(ctx, ctx.l, "min")
        rng = yh - yl
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(rng > 0, np.abs(yc - yv) / rng, np.nan)
    dist = ctx.cached("b042_ydist", make)
    with np.errstate(invalid="ignore"):
        cond = dist < th
    return _fade(ctx, wm, cond)


def _failed_drive_fade(ctx, p):
    dm, wm = p["drive_min"], p["win_min"]
    nb = ctx.bars(dm)
    end_c = np.where(ctx.bar_in_day == nb - 1, ctx.c, np.nan)
    drive = _session_ffill(ctx, end_c) - ctx.day_open
    with np.errstate(invalid="ignore"):
        cond = (ctx.bar_in_day >= nb) & (np.sign(drive) * (ctx.c - ctx.day_open) < 0)
    return _fade(ctx, wm, cond)


def _dollar_midbox_fade(ctx, p):
    wm, q = p["win_min"], p["q"]
    nb = ctx.bars(wm)
    w = ctx.other_close()
    whi = ctx.roll(w, nb, "max", include_current=False)
    wlo = ctx.roll(w, nb, "min", include_current=False)
    width = whi - wlo
    with np.errstate(divide="ignore", invalid="ignore"):
        pos = np.where(width > 0, (w - 0.5 * (whi + wlo)) / width, np.nan)
        cond = np.abs(pos) <= q
    return _fade(ctx, wm, cond)


def _yday_mid_poke_fade(ctx, p):
    f = p["f"]
    pdh, pdl = ctx.prev_session_value("high"), ctx.prev_session_value("low")
    mid = 0.5 * (pdh + pdl)
    buf = f * (pdh - pdl)
    pc = ctx.prev(ctx.c, 1)
    with np.errstate(invalid="ignore"):
        short = (pc < mid) & (ctx.h >= mid + buf) & (ctx.c < mid)
        long = (pc > mid) & (ctx.l <= mid - buf) & (ctx.c > mid)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _inside_morning_fade(ctx, p):
    m_end, wm = p["morning_end"], p["win_min"]
    am = ctx.minute < m_end
    mh = pd.Series(np.where(am, ctx.h, np.nan)).groupby(ctx.day).cummax().to_numpy()
    ml = pd.Series(np.where(am, ctx.l, np.nan)).groupby(ctx.day).cummin().to_numpy()
    mh, ml = _session_ffill(ctx, mh), _session_ffill(ctx, ml)
    with np.errstate(invalid="ignore"):
        cond = (~am) & (ctx.c < mh) & (ctx.c > ml)
    return _fade(ctx, wm, cond)


def _evening_fade(ctx, p):
    start, wm = p["start"], p["win_min"]
    cond = (ctx.minute >= start) & (ctx.minutes_to_close >= 15)
    return _fade(ctx, wm, cond)


def _box_rotation_fade(ctx, p):
    wm, th = p["win_min"], p["th"]
    nb = ctx.bars(wm)
    if nb < 2:
        return np.zeros(ctx.n, dtype=int)
    _, _, hi, lo = _box(ctx, wm)
    mid = 0.5 * (hi + lo)
    cnt = np.zeros(ctx.n)
    with np.errstate(invalid="ignore"):
        for j in range(1, nb):
            a = ctx.prev(ctx.c, j) - mid
            b = ctx.prev(ctx.c, j + 1) - mid
            cnt += (a * b < 0)
        cond = (cnt / (nb - 1)) >= th
    return _fade(ctx, wm, cond)


def _braided_ema_fade(ctx, p):
    m, wm = p["m"], p["win_min"]

    def make():
        fast, slow = ctx.ema(ctx.c, 9), ctx.ema(ctx.c, 21)
        d = np.sign(fast - slow)
        pd_ = ctx.prev(d, 1)
        with np.errstate(invalid="ignore"):
            flip = ((d * pd_) < 0).astype(float)
        flip[np.isnan(d) | np.isnan(pd_)] = 0.0
        return flip
    flip = ctx.cached("b042_flip", make)
    crosses = ctx.roll(flip, ctx.bars(wm), "sum")
    with np.errstate(invalid="ignore"):
        cond = crosses >= m
    return _fade(ctx, 15, cond)


def _same_sign_day_fade(ctx, p):
    k, wm = p["k"], p["win_min"]

    def make():
        w = ctx.other_close()
        wopen = pd.Series(w).groupby(ctx.day).transform("first").to_numpy()
        with np.errstate(divide="ignore", invalid="ignore"):
            r2 = np.where(np.isnan(w), np.nan, w / wopen - 1.0)
        typ2 = ctx.same_minute(np.abs(r2), "median")
        return r2, typ2
    r2, typ2 = ctx.cached("b042_wdo_day", make)
    r1 = ctx.c / ctx.day_open - 1.0
    with np.errstate(invalid="ignore"):
        cond = (r1 * r2 > 0) & (np.abs(r2) >= k * typ2)
    return _fade(ctx, wm, cond)


FAMILIES = [
    Family("E-418", "Cheap-move (high price impact per contract) micro-break fade",
           "When the recent price change per contract traded (Amihud impact) is high for the time of day, the book "
           "is thin and a few small market orders move the price a lot; a short-box break made then costs the "
           "pushers little and carries no conviction, and the liquidity providers who refill the book lean "
           "against it, so fade the break back into the box.",
           {"k": [1.0, 1.25, 1.5], "win_min": [15, 30]}, _cheap_move_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-419", "Yesterday settled at its VWAP micro-break fade",
           "When yesterday closed near its own volume-weighted price, the day's buyers and sellers ended near "
           "break-even with no trapped inventory to unwind today; with no carry-over pressure, short-term box "
           "breaks are not fed by forced exits and the two-sided players fade them back into the box.",
           {"th": [0.1, 0.2, 0.3], "win_min": [15, 30]}, _settled_at_vwap_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-420", "Failed-opening-drive day micro-break fade",
           "When the price is back on the other side of the session open from the direction of the opening drive, "
           "the early initiative traders have been proved wrong and the day becomes two-sided: they exit into "
           "strength and weakness while responsive traders re-centre; short-box breaks on such days are absorbed, "
           "so fade them.",
           {"drive_min": [15, 30, 45], "win_min": [15, 30]}, _failed_drive_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-421", "Dollar parked mid-box index break fade",
           "If the mini dollar sits in the middle of its own recent box when the index breaks its box, there is "
           "no macro or foreign-flow push behind the index move (foreign flows move both markets at once); the "
           "break is local order-book noise that index market makers take back, so fade it.",
           {"win_min": [10, 15, 30], "q": [0.25, 0.5]}, _dollar_midbox_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-422", "Yesterday's range-midpoint poke fade",
           "The midpoint of yesterday's high-low range is the fair price of yesterday's auction, and range traders "
           "rest orders there; a bar that comes from one side, trades through the midpoint and closes back on its "
           "side shows the resting orders absorbed the push, so trade away from the level.",
           {"f": [0.0, 0.01, 0.02]}, _yday_mid_poke_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-423", "Inside-morning-range afternoon micro-break fade",
           "After the morning has set the session's working range, afternoon participants (lighter local flow "
           "before the US session) trade inside it against its edges; a short-box break that still sits inside "
           "the morning range is a rotation, not a new leg, and the morning-range players fade it.",
           {"morning_end": [660, 720, 780], "win_min": [15, 30]}, _inside_morning_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-424", "Futures-only evening micro-break fade",
           "Once the B3 cash-equity session and the settlement window are over, the index future trades without "
           "spot arbitrage flow or index-fund orders; what is left is day traders squaring positions in a thin "
           "book, so short-box breaks then are inventory noise that reverts; fade them.",
           {"start": [1020, 1050, 1080], "win_min": [10, 15, 30]}, _evening_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-425", "Rotating-box micro-break fade",
           "A box whose closes keep crossing its own midpoint is a two-sided auction in which both sides keep "
           "being filled; a break out of such a box is usually the last swing of the rotation hitting stops just "
           "outside, after which the rotation resumes, so fade the break.",
           {"win_min": [15, 30], "th": [0.2, 0.3, 0.4]}, _box_rotation_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-426", "Braided-EMA micro-break fade",
           "When the 9- and 21-bar EMAs have crossed back and forth several times recently, the moving-average "
           "trend followers have been whipsawed and stopped repeatedly and nobody holds a trend position; a "
           "15-minute box break then has no trend money behind it and fades back into the box.",
           {"m": [2, 3, 4], "win_min": [60, 120]}, _braided_ema_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-427", "Same-sign index and dollar day micro-break fade",
           "The index and the dollar usually move in opposite directions because foreign flows drive both; on a "
           "day when both are up (or down) since the open by a clear margin, the two markets are driven by "
           "separate local flows instead of one persistent foreign flow, so index box breaks lack a lasting push "
           "and fade.",
           {"k": [0.5, 1.0, 1.5], "win_min": [15, 30]}, _same_sign_day_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
