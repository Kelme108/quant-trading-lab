"""Conveyor batch B-035 (agent, 2026-11-19). New regime variables for fading short-term WIN breaks (frozen day range,
multi-day value, yesterday's volume, the open-noise band, daily reversal regime, volume-drought week, compact value,
unfilled gap zone), plus a follow off the session VWAP and a previous-hour value-migration hold."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


# ---------------------------------------------------------------------------------------------- helpers

def _breaks(ctx, nb):
    """First close above the previous nb bars' high (up) / below their low (dn)."""
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    return ctx.cross(ctx.c > hi), ctx.cross(ctx.c < lo)


def _fade(ctx, nb, regime):
    up, dn = _breaks(ctx, nb)
    regime = np.asarray(regime, bool)
    return (dn & regime).astype(int) - (up & regime).astype(int)


def _daily(ctx, x, how):
    """One value per session (index = session number)."""
    s = pd.Series(np.asarray(x, float)).groupby(ctx.day).agg(how)
    return s.reindex(range(int(ctx.day.max()) + 1)).to_numpy(float)


def _trail_mean(arr, n, lag=1):
    """out[d] = mean of arr[d-lag-n+1 .. d-lag]; NaN unless all n values exist (explicit loop, start-independent)."""
    out = np.full(len(arr), np.nan)
    for d in range(len(arr)):
        a, b = d - lag - n + 1, d - lag + 1
        if a < 0:
            continue
        w = arr[a:b]
        if len(w) == n and np.isfinite(w).all():
            out[d] = w.mean()
    return out


def _day_cumsum(ctx, x):
    return pd.Series(np.asarray(x, float)).groupby(ctx.day).cumsum().to_numpy()


# ---------------------------------------------------------------------------------------------- families

def _frozen_range(ctx, p):
    nb = ctx.bars(p["win_min"])
    sh = ctx.session_high(include_current=True)
    sl = ctx.session_low(include_current=True)
    new_ext = (ctx.h >= sh) | (ctx.l <= sl)
    idx = np.arange(ctx.n, dtype=float)
    last = pd.Series(np.where(new_ext, idx, np.nan)).groupby(ctx.day).ffill().to_numpy()
    age_min = (idx - last) * ctx.tf
    frozen = age_min >= p["frozen_min"]
    return _fade(ctx, nb, frozen)


def _multiday_value(ctx, p):
    nb = ctx.bars(p["win_min"])
    m = ctx.cached("b035_pm", lambda: ctx.prev_sessions(ctx.c, "mean"))
    sd = ctx.cached("b035_psd", lambda: ctx.prev_sessions(ctx.c, "sd"))
    inval = np.abs(ctx.c - m) < p["k"] * sd
    return _fade(ctx, nb, inval)


def _post_heavy_session(ctx, p):
    nb = ctx.bars(p["win_min"])
    dv = _daily(ctx, ctx.v, "sum")
    yest = np.concatenate([[np.nan], dv[:-1]])
    norm = _trail_mean(dv, 20, lag=1)
    ratio = (yest / norm)[ctx.day]
    return _fade(ctx, nb, ratio >= p["q"])


def _noise_band(ctx, p):
    nb = ctx.bars(p["win_min"])
    move = np.abs(ctx.c / ctx.day_open - 1.0)
    band = ctx.cached("b035_band", lambda: ctx.same_minute(move, "mean"))
    inside = (move < p["m"] * band) & (ctx.bar_in_day * ctx.tf >= 30)
    return _fade(ctx, nb, inside)


def _vwap_launch(ctx, p):
    nb = ctx.bars(p["win_min"])
    nt = ctx.bars(p["touch_min"])
    vw = ctx.vwap()
    touched = ((ctx.l <= vw) & (ctx.h >= vw)).astype(float)
    recent = ctx.roll(touched, nt, "max") >= 1.0
    up, dn = _breaks(ctx, nb)
    long = up & recent & (ctx.c > vw)
    short = dn & recent & (ctx.c < vw)
    return long.astype(int) - short.astype(int)


def _daily_reversal_regime(ctx, p):
    nb = ctx.bars(p["win_min"])
    cl = _daily(ctx, ctx.c, "last")
    r = np.diff(np.log(cl), prepend=np.nan)            # r[d] = close d vs close d-1
    n = 15
    ac = np.full(len(r), np.nan)
    for d in range(len(r)):
        a = d - n                                       # pairs (r[t], r[t-1]) for t = d-n .. d-1 (needs close d-n-2)
        if a - 1 < 0:
            continue
        x, y = r[a:d], r[a - 1:d - 1]
        if len(x) == n and np.isfinite(x).all() and np.isfinite(y).all() and x.std() > 0 and y.std() > 0:
            ac[d] = float(np.corrcoef(x, y)[0, 1])
    return _fade(ctx, nb, ac[ctx.day] < p["th"])


def _drought_week(ctx, p):
    nb = ctx.bars(p["win_min"])
    dv = _daily(ctx, ctx.v, "sum")
    r5 = _trail_mean(dv, 5, lag=1) / _trail_mean(dv, 20, lag=1)
    return _fade(ctx, nb, r5[ctx.day] < p["q"])


def _compact_value(ctx, p):
    nb = ctx.bars(p["win_min"])
    cv = _day_cumsum(ctx, ctx.v)
    m1 = _day_cumsum(ctx, ctx.v * ctx.c) / cv
    m2 = _day_cumsum(ctx, ctx.v * ctx.c * ctx.c) / cv
    sd_rel = np.sqrt(np.maximum(m2 - m1 * m1, 0.0)) / ctx.c
    norm = ctx.cached("b035_vsd", lambda: ctx.same_minute(sd_rel, "median"))
    compact = (sd_rel < p["k"] * norm) & (ctx.bar_in_day * ctx.tf >= 60)
    return _fade(ctx, nb, compact)


def _prev_hour_vwap_hold(ctx, p):
    hr = (np.asarray(ctx.minute) // 60).astype(int)
    key = np.asarray(ctx.day).astype(int) * 24 + hr
    g = pd.DataFrame({"k": key, "pv": ctx.v * ctx.c, "v": ctx.v}).groupby("k").sum()
    hv = g["pv"] / g["v"].replace(0.0, np.nan)
    p1 = hv.reindex(key - 1).to_numpy(float)
    p2 = hv.reindex(key - 2).to_numpy(float)
    adr = _trail_mean(_daily(ctx, ctx.h, "max") - _daily(ctx, ctx.l, "min"), 20, lag=1)[ctx.day]
    mig = p1 - p2
    long = ctx.cross((ctx.l <= p1) & (ctx.c > p1)) & (mig > p["k"] * adr)
    short = ctx.cross((ctx.h >= p1) & (ctx.c < p1)) & (mig < -p["k"] * adr)
    return long.astype(int) - short.astype(int)


def _gap_zone(ctx, p):
    nb = ctx.bars(p["win_min"])
    op = _daily(ctx, ctx.o, "first")
    cl = _daily(ctx, ctx.c, "last")
    gap = op - np.concatenate([[np.nan], cl[:-1]])
    typ = _trail_mean(np.abs(gap), 19, lag=1)          # gaps of the 19 sessions before (each needs its prior close)
    pc = ctx.prev_session_value("close")
    gp = gap[ctx.day]
    big = np.abs(gp) >= p["g"] * typ[ctx.day]
    sl = ctx.session_low(include_current=True)
    sh = ctx.session_high(include_current=True)
    zone_up = (gp > 0) & (sl > pc) & (ctx.c > pc) & (ctx.c < ctx.day_open)
    zone_dn = (gp < 0) & (sh < pc) & (ctx.c < pc) & (ctx.c > ctx.day_open)
    return _fade(ctx, nb, big & (zone_up | zone_dn))


FAMILIES = [
    Family("E-348", "Frozen day-range micro-break fade",
           "When neither the session high nor the session low has moved for a long time, the day's range is "
           "established and both edges are held by responsive traders; a short-term break inside that frozen range "
           "reaches no level with stops behind it and the small breaker is leaned back by liquidity providers, so fade it.",
           {"frozen_min": [30, 60, 90], "win_min": [10, 15, 30]}, _frozen_range,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-349", "Multi-day value micro-break fade",
           "When the price sits near the mean price of the last 20 sessions (inside k multi-day sds), it is at the "
           "swing traders' accepted value: they sell above and buy below it and no multi-day initiator is pushing; "
           "short-term breaks there are local pushes the multi-day holders absorb, so fade them.",
           {"k": [0.25, 0.5, 1.0], "win_min": [10, 15, 30]}, _multiday_value,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-350", "Post-heavy-volume-session micro-break fade",
           "A session that traded far more contracts than the 20-session norm was an event day whose large orders "
           "were executed then; the next session is digestion by dealers rebuilding inventory with no parent order "
           "left to work, so its short-term breaks are faded (yesterday's volume, not its range or close).",
           {"q": [1.1, 1.25, 1.5], "win_min": [10, 15, 30]}, _post_heavy_session,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-351", "Inside-noise-band micro-break fade",
           "Moves from the open that stay inside the average absolute move for this minute (the Zarattini/Aziz noise "
           "area) are the territory of liquidity providers; while price is still inside that band, a break of the "
           "recent high/low is noise they lean back, so fade it (the complement regime of following an exit, E-128).",
           {"m": [0.5, 0.75, 1.0], "win_min": [10, 15, 30]}, _noise_band,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-352", "VWAP-launch break follow",
           "A short-term break made soon after the price touched the session VWAP, on the VWAP side it now trades, "
           "starts from the day's average cost: benchmark buyers who filled at value hold the inventory behind it and "
           "nobody is trapped above, so the push away from value carries; follow the break (not the touch-hold of E-079).",
           {"touch_min": [10, 20, 30], "win_min": [10, 15, 30]}, _vwap_launch,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-353", "Daily-reversal-regime micro-break fade",
           "When the last 15 daily close-to-close returns are negatively autocorrelated, each day undoes the last: the "
           "multi-day market is run by mean-reverting swing traders rather than trend flow; in that regime intraday "
           "short-term breaks also lack follow-through and are faded (daily-scale autocorrelation, not intraday).",
           {"th": [-0.2, -0.1, 0.0], "win_min": [10, 15, 30]}, _daily_reversal_regime,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-354", "Volume-drought week micro-break fade",
           "When the last 5 sessions traded clearly fewer contracts than the 20-session norm, institutional "
           "participants are away (holidays, waiting for an event) and the book is run by local market makers; "
           "short-term breaks then have no size behind them and are leaned back, so fade them.",
           {"q": [0.8, 0.9, 1.0], "win_min": [10, 15, 30]}, _drought_week,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-355", "Compact-value session micro-break fade",
           "When today's volume-weighted dispersion of trade around the session VWAP is small next to its usual value "
           "at this minute, the day's volume is concentrated at one value that both sides accept; a short-term break "
           "away from that compact value is a probe the value traders return, so fade it.",
           {"k": [0.5, 0.7, 0.9], "win_min": [10, 15, 30]}, _compact_value,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-356", "Previous-hour VWAP hold after value migration",
           "When the last completed clock hour's VWAP stepped well above the hour before, value is migrating up and the "
           "last hour's buyers hold inventory at that VWAP; the first bar that dips to it and closes back above meets "
           "their defence, so buy (mirror for a downward step).",
           {"k": [0.05, 0.1, 0.2]}, _prev_hour_vwap_hold,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-357", "Unfilled gap-zone micro-break fade",
           "While price trades inside a meaningful overnight gap that has not been filled (between yesterday's close and "
           "today's open), it is in a zone with no inventory from either session, where gap-fill traders and gap "
           "holders both trade responsively; short-term breaks inside it are absorbed, so fade them.",
           {"g": [0.5, 1.0, 1.5], "win_min": [10, 15, 30]}, _gap_zone,
           markets=("WIN",), source="assistant reasoning", author="agent"),
]
