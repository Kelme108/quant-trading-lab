"""Conveyor batch B-130 (agent, 2026-11-24). Mixed themes: cross-market lead, VWAP chop/bands, day-open and prior-close
revisits, lunch range, clock-hour open, squeeze, acceleration, low-volume wide bars."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _dir(ctx, long, short):
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _dollar_lead(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    oc = ctx.other_close()
    wr = oc / ctx.prev(oc, nb) - 1.0
    own = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    typ = ctx.cached(("wtyp", nb), lambda: ctx.prev_sessions(np.nan_to_num(np.abs(wr)), "mean"))
    ok = typ > 0
    long = ok & (wr <= -k * typ) & (own >= 0)
    short = ok & (wr >= k * typ) & (own <= 0)
    return _dir(ctx, long, short)


def _vwap_chop_fade(ctx, p):
    m = p["min_crosses"]
    nb, ne = ctx.bars(60), ctx.bars(20)
    vw = ctx.vwap()
    s = np.sign(ctx.c - vw)
    ps_ = ctx.prev(s, 1)
    ch = ((s != ps_) & ~np.isnan(ps_)).astype(float)
    cnt = ctx.roll(ch, nb, "sum")
    hi = ctx.roll(ctx.h, ne, "max")
    lo = ctx.roll(ctx.l, ne, "min")
    chop = cnt >= m
    short = chop & (ctx.h >= hi) & (ctx.c < ctx.o)
    long = chop & (ctx.l <= lo) & (ctx.c > ctx.o)
    return long.astype(int) - short.astype(int)


def _day_open_revisit(ctx, p):
    k = p["k"]
    r = ctx.c / ctx.day_open - 1.0
    typ = ctx.cached("absr_sm", lambda: ctx.same_minute(np.abs(r), "mean"))
    up = (ctx.session_high(False) / ctx.day_open - 1.0)
    dn = (1.0 - ctx.session_low(False) / ctx.day_open)
    ok = typ > 0
    short = ok & (up >= k * typ) & (ctx.c < ctx.day_open)
    long = ok & (dn >= k * typ) & (ctx.c > ctx.day_open)
    return _dir(ctx, long, short)


def _lunch_break(ctx, p):
    w = p["range_min"]
    m = (ctx.minute >= 780 - w) & (ctx.minute < 780)
    g = pd.DataFrame({"d": ctx.day, "h": np.where(m, ctx.h, np.nan), "l": np.where(m, ctx.l, np.nan)})
    hh = g.groupby("d")["h"].transform("max").to_numpy()
    ll = g.groupby("d")["l"].transform("min").to_numpy()
    done = (ctx.minute >= 780) & (ctx.minute < 960)
    return _dir(ctx, done & (ctx.c > hh), done & (ctx.c < ll))


def _hour_open_cross(ctx, p):
    m = p["min_into_hour"]
    ho = pd.Series(np.where((ctx.minute % 60) < ctx.tf, ctx.o, np.nan)).groupby(ctx.day).ffill().to_numpy()
    late = (ctx.minute % 60) >= m
    return ctx.cross(ctx.c > ho).astype(int) * late - ctx.cross(ctx.c < ho).astype(int) * late


def _vwap_band_fade(ctx, p):
    k = p["k"]
    mp = ctx.bars(60)
    dev = ctx.c - ctx.vwap()
    sd = pd.Series(dev).groupby(ctx.day).transform(lambda z: z.expanding(mp).std(ddof=0)).to_numpy()
    z = np.where(sd > 0, dev / sd, np.nan)
    return _dir(ctx, z <= -k, z >= k)


def _squeeze_break(ctx, p):
    k = p["ratio"]
    nb = ctx.bars(30)
    rng = ctx.h - ctx.l
    avg = ctx.prev(ctx.roll(rng, nb, "mean"), 1)
    typ = ctx.cached("rng_med", lambda: ctx.same_minute(rng, "median"))
    sq = (typ > 0) & (avg < k * typ)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    return _dir(ctx, sq & (ctx.c > hi), sq & (ctx.c < lo))


def _prior_close_reclaim(ctx, p):
    f = p["away_frac"]
    pc = ctx.prev_session_value("close")
    lo_s, hi_s = ctx.session_low(False), ctx.session_high(False)
    long = (lo_s < pc * (1 - f)) & (ctx.c > pc)
    short = (hi_s > pc * (1 + f)) & (ctx.c < pc)
    return _dir(ctx, long, short)


def _wide_lowvol_fade(ctx, p):
    k, vk = p["range_k"], p["vol_k"]
    nb = ctx.bars(30)
    rng = ctx.h - ctx.l
    avg = ctx.roll(rng, nb, "mean", include_current=False)
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    wide = (rng > k * avg) & (ctx.v < vk * med)
    short = wide & (ctx.c > ctx.o)
    long = wide & (ctx.c < ctx.o)
    return long.astype(int) - short.astype(int)


def _accel(ctx, p):
    n, k = ctx.bars(p["leg_min"]), p["k"]
    r1 = ctx.c / ctx.prev(ctx.c, n) - 1.0
    r2 = ctx.prev(ctx.c, n) / ctx.prev(ctx.c, 2 * n) - 1.0
    typ = ctx.cached(("acc_typ", n), lambda: ctx.prev_sessions(np.nan_to_num(np.abs(r1)), "mean"))
    long = (r1 > 0) & (r2 > 0) & (r1 >= k * r2) & (r1 >= typ) & (typ > 0)
    short = (r1 < 0) & (r2 < 0) & (r1 <= k * r2) & (r1 <= -typ) & (typ > 0)
    return _dir(ctx, long, short)


FAMILIES = [
    Family("E-1298", "Dollar-led index catch-up",
           "WDO and WIN trade inversely; when the dollar makes an unusual move over a window and the index has not yet "
           "moved against it, slower index participants catch up in the opposite direction.",
           {"win_min": [5, 10, 20], "k": [1.0, 1.5, 2.0]}, _dollar_lead, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1299", "VWAP whipsaw-regime extreme fade",
           "Many VWAP crossings in the last hour mean balanced two-way trade; a fresh 20-minute extreme bar in that "
           "regime is likely to be rejected, so fade it on the bar's colour.",
           {"min_crosses": [3, 4, 6]}, _vwap_chop_fade, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1300", "Day-open revisit after a big excursion",
           "After the price strays far from the day's open and closes back through it, the day's initial balance is "
           "lost and the other side gains control; follow the cross.",
           {"k": [0.5, 1.0, 1.5]}, _day_open_revisit, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1301", "Lunch-range breakout",
           "The thin midday range is a coiled balance; the first close beyond it after 13:00 follows the arrival of "
           "afternoon liquidity and US-session flow.",
           {"range_min": [30, 60, 90]}, _lunch_break, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1302", "Clock-hour open cross",
           "Algorithms and desks reference the open of each clock hour; a cross of that level well into the hour "
           "signals the direction of the hour's remaining flow.",
           {"min_into_hour": [10, 20, 30]}, _hour_open_cross, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1303", "VWAP z-score band fade",
           "Deviation from VWAP beyond k session standard deviations is stretched against the volume-weighted "
           "average price that institutional benchmark orders pull toward; fade it.",
           {"k": [1.5, 2.0, 2.5]}, _vwap_band_fade, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1304", "Volatility squeeze break",
           "When recent bar ranges are small versus the typical for that time of day, liquidity providers have "
           "tightened; the break of the 30-minute range releases stored stops.",
           {"ratio": [0.5, 0.7, 0.9]}, _squeeze_break, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-1305", "Prior-close reclaim after a dip",
           "The previous close is the reference of the overnight positions; after trading away from it by a margin, "
           "a close back across it shows the excursion was absorbed; follow the reclaim.",
           {"away_frac": [0.002, 0.004, 0.006]}, _prior_close_reclaim, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1306", "Wide bar on light volume fade",
           "A range much wider than recent bars on below-typical volume is a thin-book air pocket rather than "
           "conviction; the move retraces.",
           {"range_k": [1.5, 2.0, 2.5], "vol_k": [0.7, 1.0]}, _wide_lowvol_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-1307", "Two-leg momentum acceleration",
           "When the latest leg of a move is several times the size of the previous leg in the same direction and "
           "larger than typical, forced flows are chasing; follow it.",
           {"leg_min": [5, 10, 15], "k": [1.5, 2.0, 3.0]}, _accel, markets=("WIN",), source="assistant reasoning",
           author="agent"),
]
