"""Conveyor batch B-003 (agent, 2026-11-17). Mixed WIN themes: pivot levels, range exhaustion, trend-filtered dips, volume regimes, clock-time momentum, retracements."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _per_session_prev(ctx, values, agg):
    """Per bar: `agg` of `values` over the PREVIOUS session (NaN on the first one)."""
    per = pd.Series(np.asarray(values, float)).groupby(ctx.day).agg(agg)
    per = per.reindex(range(int(ctx.day.max()) + 1)).shift(1)
    return per.to_numpy()[ctx.day]


def _typical_abs_move(ctx, nb):
    def f():
        r = ctx.c / ctx.prev(ctx.c, nb) - 1.0
        return r, ctx.prev_sessions(np.abs(r), "mean")
    return ctx.cached(("b003_absmove", nb), f)


def _rel_cum_volume(ctx):
    def f():
        cumv = pd.Series(ctx.v).groupby(ctx.day).cumsum().to_numpy()
        typ = ctx.same_minute(cumv, "median")
        return cumv / typ
    return ctx.cached("b003_relcumv", f)


# E-019 ---------------------------------------------------------------------------------------
def _pivot_reject(ctx, p):
    H, L, C = ctx.prev_session_value("high"), ctx.prev_session_value("low"), ctx.prev_session_value("close")
    P = (H + L + C) / 3.0
    levels = [P]
    if p["n_levels"] >= 3:
        levels += [2 * P - L, 2 * P - H]
    if p["n_levels"] >= 5:
        levels += [P + (H - L), P - (H - L)]
    pc = ctx.prev(ctx.c, 1)
    long = np.zeros(ctx.n, dtype=bool)
    short = np.zeros(ctx.n, dtype=bool)
    for lv in levels:
        long |= (pc > lv) & (ctx.l <= lv) & (ctx.c > lv)
        short |= (pc < lv) & (ctx.h >= lv) & (ctx.c < lv)
    both = long & short
    long, short = long & ~both, short & ~both
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-020 ---------------------------------------------------------------------------------------
def _range_exhaustion_fade(ctx, p):
    k = p["k"]

    def adr_f():
        rng = pd.Series(ctx.h).groupby(ctx.day).max() - pd.Series(ctx.l).groupby(ctx.day).min()
        rng = rng.reindex(range(int(ctx.day.max()) + 1))
        return rng.rolling(20, min_periods=20).mean().shift(1).to_numpy()[ctx.day]
    adr = ctx.cached("b003_adr", adr_f)
    hi_prev, lo_prev = ctx.session_high(False), ctx.session_low(False)
    rng_now = ctx.session_high(True) - ctx.session_low(True)
    tired = rng_now >= k * adr
    short = tired & (ctx.h > hi_prev)
    long = tired & (ctx.l < lo_prev)
    both = long & short
    long, short = long & ~both, short & ~both
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-021 ---------------------------------------------------------------------------------------
def _trend_dip_rsi2(ctx, p):
    th, nb = p["rsi_th"], ctx.bars(p["ema_min"])
    rsi = ctx.rsi(2)
    ema = ctx.cached(("b003_ema", nb), lambda: ctx.ema(ctx.c, nb))
    long = (rsi <= th) & (ctx.c > ema)
    short = (rsi >= 100 - th) & (ctx.c < ema)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-022 ---------------------------------------------------------------------------------------
def _heavy_balance_break(ctx, p):
    nb, vk = ctx.bars(p["win_min"]), p["vol_k"]
    med = ctx.cached("b003_vmed", lambda: ctx.same_minute(ctx.v, "median"))
    vsum = ctx.roll(ctx.v, nb, "sum", include_current=False)
    vtyp = ctx.roll(med, nb, "sum", include_current=False)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)

    def width_f():
        w = hi / lo - 1.0
        return w, ctx.prev_sessions(w, "mean")
    w, wtyp = ctx.cached(("b003_width", nb), width_f)
    setup = (vsum >= vk * vtyp) & (w <= wtyp)
    long = setup & (ctx.c > hi)
    short = setup & (ctx.c < lo)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-023 ---------------------------------------------------------------------------------------
def _half_hour_momentum(ctx, p):
    nb, k = ctx.bars(p["horizon_min"]), p["k"]
    r, typ = _typical_abs_move(ctx, nb)
    mark = ((ctx.minute + ctx.tf) % 30) == 0          # the bar closes at :00 or :30
    long = mark & (r >= k * typ)
    short = mark & (r <= -k * typ)
    return long.astype(int) - short.astype(int)


# E-024 ---------------------------------------------------------------------------------------
def _hv_bar_level_hold(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    med = ctx.cached("b003_vmed", lambda: ctx.same_minute(ctx.v, "median"))
    ratio = ctx.v / med
    mid = (ctx.h + ctx.l) / 2.0
    best = np.full(ctx.n, -np.inf)
    lvl = np.full(ctx.n, np.nan)
    for lag in range(2, nb + 2):                      # skip the bar just before: the level must be older
        rv, pm = ctx.prev(ratio, lag), ctx.prev(mid, lag)
        upd = rv > best
        best = np.where(upd, rv, best)
        lvl = np.where(upd, pm, lvl)
    ok = best >= 2.0
    pc = ctx.prev(ctx.c, 1)
    long = ok & (pc > lvl) & (ctx.l <= lvl) & (ctx.c > lvl)
    short = ok & (pc < lvl) & (ctx.h >= lvl) & (ctx.c < lvl)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-025 ---------------------------------------------------------------------------------------
def _run_length_fade(ctx, p):
    run, k = int(p["run"]), p["k"]
    up = np.ones(ctx.n, dtype=bool)
    dn = np.ones(ctx.n, dtype=bool)
    for j in range(run):
        a, b = ctx.prev(ctx.c, j) if j else ctx.c, ctx.prev(ctx.c, j + 1)
        up &= a > b
        dn &= a < b
    r, typ = _typical_abs_move(ctx, run)
    short = up & (r >= k * typ)
    long = dn & (r <= -k * typ)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-026 ---------------------------------------------------------------------------------------
def _busy_session_break(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    rel = _rel_cum_volume(ctx)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    long = (rel >= k) & (ctx.c > hi)
    short = (rel >= k) & (ctx.c < lo)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-027 ---------------------------------------------------------------------------------------
def _day_retracement_hold(ctx, p):
    f, k = p["frac"], p["k"]
    hi, lo = ctx.session_high(True), ctx.session_low(True)
    pos_hi = pd.Series(np.where(ctx.h >= hi, ctx.bar_in_day, -1)).groupby(ctx.day).cummax().to_numpy()
    pos_lo = pd.Series(np.where(ctx.l <= lo, ctx.bar_in_day, -1)).groupby(ctx.day).cummax().to_numpy()
    rng = hi - lo
    typ = ctx.cached("b003_rngtyp", lambda: ctx.same_minute(rng, "median"))
    big = rng >= k * typ
    lv_up = hi - f * rng
    lv_dn = lo + f * rng
    long = big & (pos_hi > pos_lo) & (ctx.l <= lv_up) & (ctx.c > lv_up)
    short = big & (pos_lo > pos_hi) & (ctx.h >= lv_dn) & (ctx.c < lv_dn)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-028 ---------------------------------------------------------------------------------------
def _quiet_session_fade(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    rel = _rel_cum_volume(ctx)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    short = (rel <= k) & (ctx.c > hi)
    long = (rel <= k) & (ctx.c < lo)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


_OSLER = ("Currency Orders and Exchange Rate Dynamics (Osler 2003, JF) "
          "https://ideas.repec.org/a/bla/jfinan/v58y2003i5p1791-1819.html")
_RSI2 = "RSI(2) - StockCharts ChartSchool https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2"

FAMILIES = [
    Family("E-019", "Floor-pivot touch rejection",
           "Floor-trader pivots (P, R1/S1, R2/S2 from yesterday's H/L/C) are plotted by most retail platforms, so "
           "take-profit and fresh limit orders rest there; a bar that reaches a pivot from one side and closes back "
           "on that side shows the resting orders absorbed the push, so trade away from the level.",
           {"n_levels": [1, 3, 5]}, _pivot_reject, markets=("WIN",), source=_OSLER, author="agent"),
    Family("E-020", "Range-exhaustion extreme fade",
           "Once today's range already equals a large share of the 20-session average daily range, day traders' "
           "targets are met and fresh momentum buyers are scarce; a new session extreme made then is more likely "
           "to be the profit-takers' exit than a new leg, so fade it.",
           {"k": [0.75, 1.0, 1.25]}, _range_exhaustion_fade, markets=("WIN",), source="assistant reasoning",
           author="agent"),
    Family("E-021", "Trend-filtered RSI(2) dip",
           "Connors-style: inside a trend defined by a long intraday EMA, a 2-period RSI extreme against the trend is "
           "short-horizon liquidity selling (or buying) by impatient traders, which trend holders absorb; buy the dip "
           "above the EMA, sell the pop below it.",
           {"rsi_th": [5, 10, 20], "ema_min": [60, 120, 240]}, _trend_dip_rsi2, markets=("WIN",), source=_RSI2,
           author="agent"),
    Family("E-022", "Heavy-volume balance break",
           "A window that trades much more volume than usual for its time of day while the price stays inside a "
           "normal-width range means a large participant is accumulating against passive liquidity; when the "
           "range finally breaks, the side that was absorbing has won, so follow the break.",
           {"win_min": [15, 30, 60], "vol_k": [1.2, 1.5, 2.0]}, _heavy_balance_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-023", "Half-hour mark momentum",
           "Execution algorithms and discretionary desks re-evaluate on clock marks; at each :00/:30 bar close, a "
           "trailing move larger than typical for its horizon means a parent order is still being worked into the "
           "next slice, so follow its sign.",
           {"horizon_min": [30, 60, 120], "k": [0.5, 1.0, 1.5]}, _half_hour_momentum, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-024", "High-volume bar level hold",
           "The midpoint of the most abnormal-volume bar of the last hour or two is where a large participant "
           "transacted; when price returns to it and closes back on its side, that participant defends the price "
           "(adds or covers), so trade the bounce away from the level.",
           {"lookback_min": [30, 60, 120]}, _hv_bar_level_hold, markets=("WIN",), source="assistant reasoning",
           author="agent"),
    Family("E-025", "Consecutive-close run fade",
           "A run of N consecutive same-direction closes that also covers more ground than usual is driven by "
           "short-term chasers and market-order bursts that exhaust the near book; liquidity providers then lean "
           "against it, so fade the bar that completes the run.",
           {"run": [4, 5, 6], "k": [0.5, 1.0, 1.5]}, _run_length_fade, markets=("WIN",), source="assistant reasoning",
           author="agent"),
    Family("E-026", "Busy-session range break",
           "A session whose cumulative volume is well above normal for the minute is an information day: informed "
           "flow is persistent, so a close beyond the recent high/low on such a day is followed by more of the "
           "same flow; follow the break only on busy days.",
           {"win_min": [15, 30, 60], "k": [1.2, 1.5, 2.0]}, _busy_session_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-027", "Day-range retracement hold",
           "After a day leg larger than usual, a pullback to a fixed share (38/50/62%) of the day's range is where "
           "missed participants and many retail Fibonacci users place their entries; a bar that reaches it and "
           "closes back in the leg's direction resumes the leg.",
           {"frac": [0.382, 0.5, 0.618], "k": [0.75, 1.0, 1.25]}, _day_retracement_hold, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-028", "Quiet-session range fade",
           "On a session with cumulative volume well below normal for the minute there is no informed flow; a "
           "close beyond the recent high/low is noise pushed by small orders into thin books and mean-reverts as "
           "market makers re-center, so fade the break only on quiet days.",
           {"win_min": [15, 30, 60], "k": [0.6, 0.75, 0.9]}, _quiet_session_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
