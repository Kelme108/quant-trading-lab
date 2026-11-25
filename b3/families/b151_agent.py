"""Conveyor batch B-151 (agent, 2026-11-25). Mixed regimes for WIN short-box breaks: opening gap side, volume concentration, FX-driven days, exit-scale box width, opening-auction size, box value skew, multi-day stretch, lunch box, one-bar traverse, post-spike aftershocks."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


# ----------------------------------------------------------------------------------------------- helpers

def _box(ctx, win_min):
    """Rolling box of the previous `win_min` minutes (excluding the current bar) and its first close-breaks."""
    def make():
        nb = ctx.bars(win_min)
        hi = ctx.roll(ctx.h, nb, "max", include_current=False)
        lo = ctx.roll(ctx.l, nb, "min", include_current=False)
        up = ctx.cross(ctx.c > hi)
        dn = ctx.cross(ctx.c < lo)
        return up, dn, hi, lo
    return ctx.cached(("b151_box", win_min), make)


def _per_day(ctx, values, agg):
    s = pd.Series(np.asarray(values, float)).groupby(ctx.day).agg(agg)
    return s.reindex(range(int(ctx.day.max()) + 1))


def _on_bars(ctx, per_day_series):
    return per_day_series.to_numpy()[ctx.day]


def _fade(up, dn, cond):
    return (dn & cond).astype(int) - (up & cond).astype(int)


# ----------------------------------------------------------------------------------------------- families

def _gap_side_fade(ctx, p):
    g = float(p["g"])
    pc = ctx.prev_session_value("close")
    rng = ctx.prev_session_value("high") - ctx.prev_session_value("low")
    gap = (ctx.day_open - pc) / np.where(rng > 0, rng, np.nan)
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    return (dn & (gap <= -g)).astype(int) - (up & (gap >= g)).astype(int)


def _spiky_volume_day_fade(ctx, p):
    k = float(p["k"])

    def make():
        v = np.maximum(np.nan_to_num(ctx.v, nan=0.0), 0.0)
        s1 = pd.Series(v).groupby(ctx.day).cumsum().to_numpy()
        s2 = pd.Series(v * v).groupby(ctx.day).cumsum().to_numpy()
        nb = pd.Series(np.ones(ctx.n)).groupby(ctx.day).cumsum().to_numpy()
        hhi = nb * s2 / np.where(s1 > 0, s1 * s1, np.nan)
        return hhi, ctx.same_minute(hhi, "median")
    hhi, typ = ctx.cached("b151_hhi", make)
    spiky = (hhi >= k * typ) & (ctx.bar_in_day >= ctx.bars(30))
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    return _fade(up, dn, spiky)


def _fx_driven_day_fade(ctx, p):
    k = float(p["k"])

    def make():
        sh = ctx.session_high(include_current=True)
        sl = ctx.session_low(include_current=True)
        win_r = (sh - sl) / sh
        w = pd.Series(ctx.other_close())
        g = w.groupby(ctx.day)
        wmax, wmin = g.cummax().to_numpy(), g.cummin().to_numpy()
        wdo_r = (wmax - wmin) / wmax
        ratio = np.where(wdo_r > 0, win_r / np.where(wdo_r > 0, wdo_r, 1.0), np.nan)
        return ratio, ctx.same_minute(ratio, "median")
    ratio, typ = ctx.cached("b151_fx_ratio", make)
    fx = (ratio <= k * typ) & (ctx.bar_in_day >= ctx.bars(30))
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    return _fade(up, dn, fx)


def _exit_scale_wide_box_fade(ctx, p):
    m = float(p["m"])
    up, dn, hi, lo = _box(ctx, int(p["win_min"]))
    wide = (hi - lo) >= m * 150.0            # 150 WIN points = the R$30 exit
    return _fade(up, dn, wide)


def _light_auction_day_fade(ctx, p):
    k = float(p["k"])

    def make():
        fv = pd.Series(np.asarray(ctx.v, float)).groupby(ctx.day).transform("first").to_numpy()
        return fv, ctx.prev_sessions(fv, "mean")
    fv, norm = ctx.cached("b151_first_vol", make)
    light = (fv <= k * norm) & (ctx.bar_in_day >= ctx.bars(30))
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    return _fade(up, dn, light)


def _box_value_skew(ctx, p):
    th = float(p["th"])
    win = int(p["win_min"])
    nb = ctx.bars(win)
    up, dn, hi, lo = _box(ctx, win)
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    vol = np.maximum(np.nan_to_num(ctx.v, nan=0.0), 1.0)
    pv = ctx.roll(tp * vol, nb, "sum", include_current=False)
    vv = ctx.roll(vol, nb, "sum", include_current=False)
    vw = pv / vv
    width = hi - lo
    pos = (vw - lo) / np.where(width > 0, width, np.nan)
    brk = up | dn
    return (brk & (pos >= 0.5 + th)).astype(int) - (brk & (pos <= 0.5 - th)).astype(int)


def _multiday_stretch_fade(ctx, p):
    k = float(p["k"])

    def make():
        C = _per_day(ctx, ctx.c, "last")
        m = _on_bars(ctx, C.rolling(10, min_periods=10).mean().shift(1))
        sd = _on_bars(ctx, C.rolling(10, min_periods=10).std(ddof=0).shift(1))
        return (ctx.c - m) / np.where(sd > 0, sd, np.nan)
    z = ctx.cached("b151_mdz", make)
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    return (dn & (z <= -k)).astype(int) - (up & (z >= k)).astype(int)


def _lunch_box_fade(ctx, p):
    start = int(p["start"])
    m = (ctx.minute >= start) & (ctx.minute < start + 60)
    hi = pd.Series(np.where(m, ctx.h, -np.inf)).groupby(ctx.day).cummax().to_numpy()
    lo = pd.Series(np.where(m, ctx.l, np.inf)).groupby(ctx.day).cummin().to_numpy()
    ok = np.isfinite(hi) & np.isfinite(lo)
    active = ok & (ctx.minute >= start + 60) & (ctx.minutes_to_close >= 30)
    up = ctx.cross(active & (ctx.c > np.where(ok, hi, np.nan)))
    dn = ctx.cross(active & (ctx.c < np.where(ok, lo, np.nan)))
    return dn.astype(int) - up.astype(int)


def _one_bar_traverse_fade(ctx, p):
    q = float(p["q"])
    up, dn, hi, lo = _box(ctx, int(p["win_min"]))
    width = hi - lo
    big = (ctx.h - ctx.l) >= q * width
    return _fade(up, dn, big & (width > 0))


def _aftershock_fade(ctx, p):
    k = float(p["k"])
    typ = ctx.cached("b151_vol_typ", lambda: ctx.same_minute(ctx.v, "median"))
    spike = ctx.v >= k * typ
    idx = np.arange(ctx.n, dtype=float)
    last = pd.Series(np.where(spike, idx, np.nan)).groupby(ctx.day).ffill().to_numpy()
    since = idx - last
    cool = (since >= 1) & (since <= ctx.bars(float(p["cool_min"])))
    up, dn, _, _ = _box(ctx, 10)
    return _fade(up, dn, cool)


FAMILIES = [
    Family("E-1508", "Gap-side box-break fade",
           "After an opening gap the overnight side is already positioned and gap traders hold the move; a short box "
           "break further in the gap's direction is late chasing that finds the gap holders taking profit, so it "
           "fades, while breaks against the gap are left alone.",
           {"g": [0.05, 0.1, 0.2], "win_min": [15, 30]}, _gap_side_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1509", "Spiky-volume day box-break fade",
           "When the session's volume so far is concentrated in a few bars (high Herfindahl share versus the usual at "
           "this minute), the day's real flow arrived in bursts and the tape between bursts is liquidity providers "
           "quoting a thin book; a short box break between bursts has no initiator behind it and reverts.",
           {"k": [1.1, 1.25, 1.5], "win_min": [15, 30]}, _spiky_volume_day_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1510", "FX-driven day index box-break fade",
           "When the dollar's range so far is large next to the index's range (versus the usual ratio at this "
           "minute), the day's information is in FX and index moves are hedge and arbitrage legs that mean-revert "
           "around the dollar; a short WIN box break on such a day has no equity initiator, so fade it.",
           {"k": [0.6, 0.75, 0.9], "win_min": [15, 30]}, _fx_driven_day_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1511", "Exit-scale wide box break fade",
           "A box whose width is several times the fixed 150-point exit is a rotation with defended edges far apart; "
           "a close beyond one edge meets the resting orders of the box's range traders and the fade target lies "
           "well inside the box, so a modest rotation back is enough; fade the break.",
           {"m": [1.5, 2.0, 3.0], "win_min": [30, 60]}, _exit_scale_wide_box_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1512", "Light opening-auction day box-break fade",
           "A small opening-auction print (versus the 20 previous sessions) means no overnight imbalance had to be "
           "matched: institutions came in without urgency and the day is left to intraday liquidity providers; short "
           "box breaks on such days lack initiative and rotate back.",
           {"k": [0.7, 0.85, 1.0], "win_min": [15, 30]}, _light_auction_day_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1513", "Box value-skew break trade",
           "Where the box's volume traded (its VWAP position inside the box) shows which prices were accepted; a "
           "break toward the accepted side is continuation of value, a break away from it is a probe the volume "
           "will not support; on any break, trade toward the side where the box's volume sits.",
           {"th": [0.1, 0.15, 0.2], "win_min": [15, 30]}, _box_value_skew, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1514", "Multi-day close-stretch box-break fade",
           "When price sits more than k standard deviations away from the mean of the last ten session closes, "
           "swing traders and multi-day mean-reversion desks are leaning against the stretch; a short box break that "
           "extends the stretch meets their orders and fades.",
           {"k": [0.5, 1.0, 1.5], "win_min": [15, 30]}, _multiday_stretch_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1515", "Lunch-box break fade",
           "The midday hour's range on B3 is set in thin trade; screened breakouts of this box lose clearly when "
           "followed, because the afternoon first probes it with stop orders that liquidity providers absorb before "
           "the US flow sets the real direction; fade the first close beyond the lunch box.",
           {"start": [690, 720, 750]}, _lunch_box_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1516", "One-bar box traverse fade",
           "A single bar that covers a large share of the recent box and closes beyond it is one aggressive order "
           "sweeping the book through every resting level; the sweeper is done once filled and the swept liquidity "
           "providers refill behind it, so the break gives part back; fade it.",
           {"q": [0.4, 0.6, 0.8], "win_min": [10, 20]}, _one_bar_traverse_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1517", "Post-spike aftershock break fade",
           "In the minutes after a bar with abnormal volume for its time (news or block execution), the market "
           "digests the spike and liquidity providers re-quote wide; small box breaks during the cooldown are "
           "aftershocks from late reactors, not new information, so fade them.",
           {"k": [2.0, 3.0, 4.0], "cool_min": [15, 30]}, _aftershock_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
