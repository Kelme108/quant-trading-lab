"""Conveyor batch B-016 (agent, 2026-11-18). Mixed themes: cross-market dollar regimes, session-midpoint hold,
hour-end painting, participation turns, wide indecision bars, round trips and fizzled day moves."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _move(ctx, nb):
    return ctx.c / ctx.prev(ctx.c, nb) - 1.0


def _typ_move(ctx, nb):
    return ctx.cached(("b016_typ_move", nb), lambda: ctx.prev_sessions(np.abs(_move(ctx, nb)), "mean"))


def _x_move(ctx, nb):
    x = ctx.other_close()
    return x / ctx.prev(x, nb) - 1.0


def _typ_x_move(ctx, nb):
    return ctx.cached(("b016_typ_x_move", nb), lambda: ctx.prev_sessions(np.abs(_x_move(ctx, nb)), "mean"))


def _incoherent_fade(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    w, x = _move(ctx, nb), _x_move(ctx, nb)
    tw, tx = _typ_move(ctx, nb), _typ_x_move(ctx, nb)
    up = (w > k * tw) & (x > k * tx)          # index up while the dollar also rises: no foreign risk-on behind it
    dn = (w < -k * tw) & (x < -k * tx)
    return ctx.cross(dn).astype(int) - ctx.cross(up).astype(int)


def _mid_hold(ctx, p):
    nb, k = ctx.bars(p["away_min"]), p["k"]
    sh, sl = ctx.session_high(False), ctx.session_low(False)
    mid = (sh + sl) / 2.0
    typ = ctx.cached("b016_abs_open_prev", lambda: ctx.prev_sessions(np.abs(ctx.c / ctx.day_open - 1.0), "mean"))
    wide = (sh - sl) / ctx.c >= k * typ
    above = (ctx.l > mid).astype(float)
    below = (ctx.h < mid).astype(float)
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    long = wide & was_above & (ctx.l <= mid) & (ctx.c > mid)
    short = wide & was_below & (ctx.h >= mid) & (ctx.c < mid)
    return long.astype(int) - short.astype(int)


def _hour_end_paint(ctx, p):
    tail_min, q = p["tail_min"], p["q"]
    key = (ctx.day.astype(np.int64) * 100 + (ctx.minute // 60).astype(np.int64))
    tail = (ctx.minute % 60) >= 60 - tail_min
    g = pd.DataFrame({"k": key, "h": ctx.h, "l": ctx.l, "c": ctx.c,
                      "th": np.where(tail, ctx.h, np.nan), "tl": np.where(tail, ctx.l, np.nan)})
    agg = g.groupby("k").agg(hh=("h", "max"), ll=("l", "min"), cc=("c", "last"), th=("th", "max"), tl=("tl", "min"))
    pk = ctx.prev(key.astype(float), 1)
    first = ~np.isnan(pk) & (pk != key)
    idx = np.where(np.isnan(pk), -1, pk).astype(np.int64)
    hh, ll, cc = (agg[c].reindex(idx).to_numpy() for c in ("hh", "ll", "cc"))
    th, tl = agg["th"].reindex(idx).to_numpy(), agg["tl"].reindex(idx).to_numpy()
    rng = hh - ll
    loc = np.where(rng > 0, (cc - ll) / np.where(rng > 0, rng, 1.0), np.nan)
    short = first & (rng > 0) & (th >= hh) & (loc >= 1.0 - q)     # last minutes printed the hour's high, closed on it
    long = first & (rng > 0) & (tl <= ll) & (loc <= q)
    return long.astype(int) - short.astype(int)


def _vol_pace_turn(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    vs = ctx.roll(ctx.v, nb, "sum")
    norm = ctx.cached(("b016_vsum_norm", nb), lambda: ctx.same_minute(vs, "median"))
    ratio = vs / norm
    m, typ = _move(ctx, nb), _typ_move(ctx, nb)
    up = (ratio > k) & (m > 0.5 * typ)
    dn = (ratio > k) & (m < -0.5 * typ)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _wide_doji_break(ctx, p):
    k, within = p["k"], int(p["within"])
    rng = ctx.h - ctx.l
    med = ctx.cached("b016_rng_med", lambda: ctx.same_minute(rng, "median"))
    loc = np.where(rng > 0, (ctx.c - ctx.l) / np.where(rng > 0, rng, 1.0), np.nan)
    doji = ((rng >= k * med) & (loc >= 1 / 3) & (loc <= 2 / 3)).astype(float)
    up = np.zeros(ctx.n, dtype=bool)
    dn = np.zeros(ctx.n, dtype=bool)
    for j in range(1, within + 1):
        dj = ctx.prev(doji, j) == 1
        up |= dj & (ctx.c > ctx.prev(ctx.h, j))
        dn |= dj & (ctx.c < ctx.prev(ctx.l, j))
    return ctx.cross(up & ~dn).astype(int) - ctx.cross(dn & ~up).astype(int)


def _volatile_dollar_follow(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    x = ctx.other_close()
    xr = (ctx.roll(x, nb, "max") - ctx.roll(x, nb, "min")) / x
    typ = ctx.cached(("b016_x_range_typ", nb), lambda: ctx.prev_sessions(xr, "mean"))
    hot = xr > k * typ
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    return ctx.cross(hot & (ctx.c > hi)).astype(int) - ctx.cross(hot & (ctx.c < lo)).astype(int)


def _macro_dip(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    xm, tx = _x_move(ctx, nb), _typ_x_move(ctx, nb)
    risk_on, risk_off = xm < -k * tx, xm > k * tx
    nd = max(3, ctx.bars(15))
    lo_prior = ctx.roll(ctx.l, nd, "min", include_current=False)
    hi_prior = ctx.roll(ctx.h, nd, "max", include_current=False)
    made_low = ctx.prev(ctx.l, 1) < ctx.prev(lo_prior, 1)
    made_high = ctx.prev(ctx.h, 1) > ctx.prev(hi_prior, 1)
    long = risk_on & made_low & (ctx.c > ctx.prev(ctx.h, 1))
    short = risk_off & made_high & (ctx.c < ctx.prev(ctx.l, 1))
    return long.astype(int) - short.astype(int)


def _round_trip(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    ref = ctx.prev(ctx.c, nb)
    typ = _typ_move(ctx, nb)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    short = (hi / ref - 1.0 > k * typ) & (ctx.c < ref)      # rallied far, now back below where it started
    long = (1.0 - lo / ref > k * typ) & (ctx.c > ref)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _dollar_reject(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    x = ctx.other_close()
    x1 = ctx.prev(x, 1)
    r1 = x / x1 - 1.0
    typ1 = ctx.cached("b016_x_r1_typ", lambda: ctx.prev_sessions(np.abs(r1), "mean"))
    xmax = ctx.prev(ctx.roll(x, nb, "max", include_current=False), 1)
    xmin = ctx.prev(ctx.roll(x, nb, "min", include_current=False), 1)
    usd_top = (x1 > xmax) & (r1 < -k * typ1)       # dollar printed a new high and is knocked back: buy the index
    usd_bot = (x1 < xmin) & (r1 > k * typ1)
    return usd_top.astype(int) - usd_bot.astype(int)


def _fizzle(ctx, p):
    nb, k, back = ctx.bars(60), p["k"], p["back"]
    r = ctx.c / ctx.day_open - 1.0
    typ = ctx.cached("b016_abs_open_sm", lambda: ctx.same_minute(np.abs(r), "mean"))
    z = r / typ
    zmax = ctx.roll(z, nb, "max", include_current=False)
    zmin = ctx.roll(z, nb, "min", include_current=False)
    short = (zmax >= k) & (z < back)
    long = (zmin <= -k) & (z > -back)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


FAMILIES = [
    Family("E-158", "Risk-incoherent index move fade",
           "WIN and WDO normally move against each other because foreign flow buys the index and sells the dollar "
           "together; when both rise (or fall) clearly over the same window, the index move has no foreign flow "
           "behind it, only local traders, and the dealers who absorbed it lean it back; fade the index move.",
           {"win_min": [10, 15, 30], "k": [0.5, 1.0, 1.5]}, _incoherent_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-159", "Session-midpoint first-touch hold",
           "On a day with a wide range, the midpoint of the session's high-low is the line day traders use to call "
           "the day bullish or bearish; after price has traded only in the upper half for a while, the first touch "
           "of the midpoint that closes back above meets the buyers defending the day's bias; trade away from it.",
           {"away_min": [15, 30, 60], "k": [1.0, 2.0, 3.0]}, _mid_hold, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-160", "Hour-end painting fade",
           "When the last minutes of a clock hour print the hour's high and the hour closes on it, short-term traders "
           "pushed the hourly candle's close (cosmetic marking for hourly charts and alerts) rather than new "
           "information; once the new hour starts the pushers stop and the price gives the mark back; fade it.",
           {"tail_min": [5, 10, 15], "q": [0.1, 0.2, 0.3]}, _hour_end_paint, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-161", "Participation turn follow",
           "When the volume of the last window crosses well above its normal level for that time of day while price "
           "has moved, new participants are entering on one side (an information or rebalancing event starting), "
           "and that flow is split over the following bars; follow the window's direction at the turn.",
           {"win_min": [15, 30, 60], "k": [1.5, 2.0, 2.5]}, _vol_pace_turn, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-162", "Wide indecision bar break follow",
           "A bar much wider than normal that closes in its middle third ran the stops on both sides and left both "
           "camps trapped near its extremes; the first close beyond its high (low) within a few bars shows which "
           "side gave up, and its exits plus the new entries push the price on; follow the break.",
           {"k": [1.5, 2.0, 2.5], "within": [3, 5, 8]}, _wide_doji_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-163", "Volatile-dollar index break follow",
           "When the dollar is trading a range far above normal, macro and foreign desks are repositioning across "
           "Brazilian assets; index breaks of the recent high/low in that regime carry macro order flow rather than "
           "local noise, so they extend; follow WIN breaks only while the dollar is volatile.",
           {"win_min": [10, 15, 30], "k": [1.5, 2.0, 2.5]}, _volatile_dollar_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-164", "Macro-backed dip buy",
           "A falling dollar over the last hour signals foreign money coming into Brazil, which keeps bidding for the "
           "index; a short-term index dip to a new 15-minute low in that regime is local selling the foreign flow "
           "absorbs, so the first bar closing above the previous bar's high is bought (mirror with a rising dollar).",
           {"win_min": [30, 60, 120], "k": [0.5, 1.0, 1.5]}, _macro_dip, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-165", "Round-trip rejection follow",
           "When price runs far from where it stood a window ago and then closes back below that starting price, the "
           "whole excursion was rejected: everyone who bought the run is under water and the responsive sellers "
           "have proven the higher prices unacceptable, so the return keeps going; follow the completed round trip.",
           {"win_min": [30, 60, 90], "k": [1.0, 1.5, 2.0]}, _round_trip, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-166", "Dollar-high rejection buys the index",
           "A new short-term dollar high that is knocked back sharply in the next bar shows FX dealers selling the "
           "dollar spike (foreign inflow or central-bank-sensitive supply); the index, priced off the same foreign "
           "flow, moves the other way with a lag, so buy WIN on the dollar rejection (mirror at a dollar low).",
           {"win_min": [15, 30, 60], "k": [1.0, 2.0, 3.0]}, _dollar_reject, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-167", "Fizzled day-move follow-through",
           "A move from the open that reached well beyond the usual distance for the time of day and has now fallen "
           "back near the open within the hour has failed: the trend-day buyers are trapped above and their exits "
           "push price further back; follow the fizzle in the direction of the retreat.",
           {"k": [1.0, 1.5, 2.0], "back": [0.0, 0.25, 0.5]}, _fizzle, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
