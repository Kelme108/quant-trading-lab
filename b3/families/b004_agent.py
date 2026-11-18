"""Conveyor batch B-004 (agent, 2026-11-18). Mixed WIN themes: trailing-stop flips, prior value band, signed volume, momentum divergence, second-entry pullbacks, horizon alignment, acceptance, anchored VWAP, narrow days, rotational edges."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


# shared helpers --------------------------------------------------------------------------------
def _session_start(ctx):
    d = ctx.day
    s = np.ones(ctx.n, dtype=bool)
    s[1:] = d[1:] != d[:-1]
    return s


def _adr(ctx):
    def f():
        rng = pd.Series(ctx.h).groupby(ctx.day).max() - pd.Series(ctx.l).groupby(ctx.day).min()
        rng = rng.reindex(range(int(ctx.day.max()) + 1))
        return rng.rolling(20, min_periods=20).mean().shift(1).to_numpy()[ctx.day]
    return ctx.cached("b004_adr", f)


def _rsi14(ctx):
    def f():
        dlt = ctx.c - ctx.prev(ctx.c, 1)
        up = np.where(np.isnan(dlt), np.nan, np.maximum(dlt, 0.0))
        dn = np.where(np.isnan(dlt), np.nan, np.maximum(-dlt, 0.0))
        au, ad = ctx.ema(up, 27), ctx.ema(dn, 27)          # Wilder alpha 1/14 == span 27
        with np.errstate(divide="ignore", invalid="ignore"):
            return 100.0 * au / (au + ad)
    return ctx.cached("b004_rsi14", f)


# E-029 Parabolic SAR flip ----------------------------------------------------------------------
def _sar_flip(ctx, p):
    step, amax = float(p["af"]), 0.2
    h, l = ctx.h.tolist(), ctx.l.tolist()
    start = _session_start(ctx).tolist()
    out = np.zeros(ctx.n, dtype=int)
    trend, sar, ep, af, first = 1, 0.0, 0.0, step, 0
    for i in range(ctx.n):
        if start[i]:
            trend, sar, ep, af, first = 1, l[i], h[i], step, i
            continue
        sar = sar + af * (ep - sar)
        if trend == 1:
            lim = l[i - 1] if i - 1 == first else min(l[i - 1], l[i - 2])
            sar = min(sar, lim)
            if l[i] < sar:
                trend, sar, ep, af = -1, ep, l[i], step
                out[i] = -1
            elif h[i] > ep:
                ep, af = h[i], min(af + step, amax)
        else:
            lim = h[i - 1] if i - 1 == first else max(h[i - 1], h[i - 2])
            sar = max(sar, lim)
            if h[i] > sar:
                trend, sar, ep, af = 1, ep, h[i], step
                out[i] = 1
            elif l[i] < ep:
                ep, af = l[i], min(af + step, amax)
    return out


# E-030 Prior-session value band re-entry -------------------------------------------------------
def _prev_value_band(ctx, p):
    k = p["k"]

    def f():
        tp = (ctx.h + ctx.l + ctx.c) / 3.0
        g = pd.DataFrame({"d": ctx.day, "pv": tp * ctx.v, "v": ctx.v, "p2v": tp * tp * ctx.v}).groupby("d").sum()
        g = g.reindex(range(int(ctx.day.max()) + 1))
        with np.errstate(divide="ignore", invalid="ignore"):
            m = g["pv"] / g["v"]
            var = g["p2v"] / g["v"] - m * m
        sd = np.sqrt(np.maximum(var, 0.0))
        return m.shift(1).to_numpy()[ctx.day], sd.shift(1).to_numpy()[ctx.day]
    m, sd = ctx.cached("b004_prev_value", f)
    up, lo = m + k * sd, m - k * sd
    pc = ctx.prev(ctx.c, 1)
    short = (pc > up) & (ctx.c < up) & (ctx.c > m)
    long = (pc < lo) & (ctx.c > lo) & (ctx.c < m)
    return long.astype(int) - short.astype(int)


# E-031 Signed-volume imbalance follow ----------------------------------------------------------
def _signed_volume(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    sv = ctx.v * np.sign(ctx.c - ctx.o)
    with np.errstate(divide="ignore", invalid="ignore"):
        imb = ctx.roll(sv, nb, "sum") / ctx.roll(ctx.v, nb, "sum")
    mv = ctx.c - ctx.prev(ctx.c, nb)
    long = ctx.cross((imb >= k) & (mv > 0))
    short = ctx.cross((imb <= -k) & (mv < 0))
    return long.astype(int) - short.astype(int)


# E-032 RSI divergence at a new extreme ---------------------------------------------------------
def _rsi_divergence(ctx, p):
    nb, gap = ctx.bars(p["lookback_min"]), p["gap"]
    rsi = _rsi14(ctx)
    hh = ctx.roll(ctx.h, nb, "max", include_current=False)
    ll = ctx.roll(ctx.l, nb, "min", include_current=False)
    rmax = ctx.roll(rsi, nb, "max", include_current=False)
    rmin = ctx.roll(rsi, nb, "min", include_current=False)
    short = (ctx.h > hh) & (rsi < rmax - gap)
    long = (ctx.l < ll) & (rsi > rmin + gap)
    both = long & short
    long, short = long & ~both, short & ~both
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-033 Second-entry pullback (H2/L2) -----------------------------------------------------------
def _second_entry(ctx, p):
    nb = ctx.bars(p["ema_min"])
    ema = ctx.cached(("b004_ema", nb), lambda: ctx.ema(ctx.c, nb))
    slope = ema - ctx.prev(ema, ctx.bars(5))
    uo = ((ctx.c > ema) & (slope > 0)).tolist()
    do = ((ctx.c < ema) & (slope < 0)).tolist()
    h, l = ctx.h.tolist(), ctx.l.tolist()
    start = _session_start(ctx).tolist()
    out = np.zeros(ctx.n, dtype=int)
    peak = trough = 0.0
    cu = cd = 0
    pu = pdn = False
    for i in range(ctx.n):
        if start[i]:
            peak, trough, cu, cd, pu, pdn = h[i], l[i], 0, 0, False, False
            continue
        if not uo[i] or h[i] > peak:
            peak, cu, pu = h[i], 0, False
        elif h[i] < h[i - 1]:
            pu = True
        elif pu and h[i] > h[i - 1]:
            cu += 1
            pu = False
            if cu == 2:
                out[i] = 1
        if not do[i] or l[i] < trough:
            trough, cd, pdn = l[i], 0, False
        elif l[i] > l[i - 1]:
            pdn = True
        elif pdn and l[i] < l[i - 1]:
            cd += 1
            pdn = False
            if cd == 2:
                out[i] = -1 if out[i] == 0 else 0
    return out


# E-034 Multi-horizon momentum alignment --------------------------------------------------------
def _horizon_alignment(ctx, p):
    sm, k = p["short_min"], p["k"]
    s1, s2, s3 = ctx.bars(sm), ctx.bars(3 * sm), ctx.bars(12 * sm)
    r1 = ctx.c / ctx.prev(ctx.c, s1) - 1.0
    r2 = ctx.c / ctx.prev(ctx.c, s2) - 1.0
    r3 = ctx.c / ctx.prev(ctx.c, s3) - 1.0
    typ = ctx.cached(("b004_abs_r", s3), lambda: ctx.prev_sessions(np.abs(r3), "mean"))
    long = (r1 > 0) & (r2 > 0) & (r3 > 0) & (r3 >= k * typ)
    short = (r1 < 0) & (r2 < 0) & (r3 < 0) & (r3 <= -k * typ)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-035 Acceptance near the session extreme -----------------------------------------------------
def _acceptance_break(ctx, p):
    nb, k = ctx.bars(p["hold_min"]), p["k"]
    atr = ctx.cached("b004_bar_range", lambda: ctx.prev_sessions(ctx.h - ctx.l, "mean"))
    sh, sl = ctx.session_high(False), ctx.session_low(False)
    lmin = ctx.roll(ctx.l, nb, "min", include_current=False)
    hmax = ctx.roll(ctx.h, nb, "max", include_current=False)
    long = (lmin >= sh - k * atr) & (ctx.c > sh)
    short = (hmax <= sl + k * atr) & (ctx.c < sl)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-036 Anchored-VWAP reclaim from the session extreme ------------------------------------------
def _avwap_reclaim(ctx, p):
    nb = ctx.bars(p["min_age_min"])

    def f():
        tp = (ctx.h + ctx.l + ctx.c) / 3.0
        pv = tp * ctx.v
        cpv = pd.Series(pv).groupby(ctx.day).cumsum().to_numpy()
        cv = pd.Series(ctx.v).groupby(ctx.day).cumsum().to_numpy()
        cpv_ex, cv_ex = cpv - pv, cv - ctx.v
        idx = np.arange(ctx.n)
        shi, slo = ctx.session_high(True), ctx.session_low(True)
        pos_hi = pd.Series(np.where(ctx.h >= shi, idx, -1)).groupby(ctx.day).cummax().to_numpy()
        pos_lo = pd.Series(np.where(ctx.l <= slo, idx, -1)).groupby(ctx.day).cummax().to_numpy()
        with np.errstate(divide="ignore", invalid="ignore"):
            av_hi = (cpv - cpv_ex[pos_hi]) / (cv - cv_ex[pos_hi])
            av_lo = (cpv - cpv_ex[pos_lo]) / (cv - cv_ex[pos_lo])
        return idx, pos_hi, pos_lo, av_hi, av_lo
    idx, pos_hi, pos_lo, av_hi, av_lo = ctx.cached("b004_avwap", f)
    pc = ctx.prev(ctx.c, 1)
    ok_hi = (idx - pos_hi >= nb) & (ctx.prev(pos_hi, 1) == pos_hi)
    ok_lo = (idx - pos_lo >= nb) & (ctx.prev(pos_lo, 1) == pos_lo)
    long = ok_hi & (pc < ctx.prev(av_hi, 1)) & (ctx.c > av_hi)
    short = ok_lo & (pc > ctx.prev(av_lo, 1)) & (ctx.c < av_lo)
    both = long & short
    return (long & ~both).astype(int) - (short & ~both).astype(int)


# E-037 Narrow-day extreme break follow ---------------------------------------------------------
def _narrow_day_break(ctx, p):
    k = p["k"]
    adr = _adr(ctx)
    rng_now = ctx.session_high(True) - ctx.session_low(True)
    ok = (rng_now <= k * adr) & (ctx.bar_in_day >= ctx.bars(60))
    long = ok & (ctx.c > ctx.session_high(False))
    short = ok & (ctx.c < ctx.session_low(False))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-038 Rotational-market edge fade -------------------------------------------------------------
def _rotation_edge_fade(ctx, p):
    nb, rate = ctx.bars(p["win_min"]), p["rate"]
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    mid = (hi + lo) / 2.0
    s = np.sign(ctx.c - mid)
    ps_ = ctx.prev(s, 1)
    chg = (~np.isnan(s) & ~np.isnan(ps_) & (s != 0) & (s != ps_)).astype(float)
    cnt = ctx.roll(chg, nb, "sum")
    rot = cnt >= rate * p["win_min"] / 60.0
    with np.errstate(divide="ignore", invalid="ignore"):
        pos = (ctx.c - lo) / (hi - lo)
    short = rot & (pos >= 0.85) & (ctx.c <= hi)
    long = rot & (pos <= 0.15) & (ctx.c >= lo)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


_SAR = ("Parabolic SAR - StockCharts ChartSchool "
        "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/parabolic-sar")
_AVWAP = "Anchored VWAP - TrendSpider Learning Center https://trendspider.com/learning-center/anchored-vwap/"

FAMILIES = [
    Family("E-029", "Parabolic SAR flip follow",
           "The Parabolic SAR is a trailing stop plotted by most retail platforms; when price trades through it the "
           "trend-followers using it are stopped and reverse at the same price, and their combined stop-and-reverse "
           "orders push the first bars of the new direction, so follow the flip.",
           {"af": [0.01, 0.02, 0.03]}, _sar_flip, markets=("WIN",), source=_SAR, author="agent"),
    Family("E-030", "Prior-session value band re-entry",
           "Yesterday's volume-weighted mean +/- k volume-weighted sd is the price zone the market accepted (Market "
           "Profile value area); a close back inside it from outside means the excursion was rejected by responsive "
           "traders, who push price back toward yesterday's value centre, so fade toward it.",
           {"k": [0.5, 0.75, 1.0]}, _prev_value_band, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-031", "Signed-volume imbalance follow",
           "When most of the recent volume traded on bars closing in one direction and the price moved that way, "
           "order flow is one-sided; order flow is persistent because large parents are split over time, so the "
           "imbalance crossing a high share predicts more of the same flow.",
           {"win_min": [10, 20, 30], "k": [0.3, 0.4, 0.5]}, _signed_volume, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-032", "RSI divergence at a new extreme",
           "A new recent high made with a 14-period RSI well below its recent peak means the push is weaker than the "
           "previous one: fewer aggressive buyers are left and the late entrants are the first to exit, so fade the "
           "new extreme (mirror for lows).",
           {"lookback_min": [30, 60, 90], "gap": [5, 10, 15]}, _rsi_divergence, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-033", "Second-entry pullback (H2/L2)",
           "In an EMA-defined trend, the first attempt to resume after a pullback (H1) often fails as counter-trend "
           "traders sell it; when the second attempt (H2) breaks the prior bar's high, the counter-trend side has "
           "failed twice and covers while trend traders re-enter, so follow it.",
           {"ema_min": [20, 40, 60]}, _second_entry, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-034", "Multi-horizon momentum alignment",
           "Traders on different horizons (minutes, quarter-hours, hours) act on their own trend; the bar where the "
           "short, middle and long trailing returns first all agree is when every horizon's flow points the same way, "
           "leaving no natural seller, so follow the alignment.",
           {"short_min": [5, 10, 15], "k": [0.0, 0.5, 1.0]}, _horizon_alignment, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-035", "Acceptance near the session extreme",
           "When price spends a while just under the session high without pulling back (accepted, not rejected), "
           "sellers there are being absorbed and stops build above; the close through the high then releases them, "
           "so follow the break only after such acceptance.",
           {"hold_min": [10, 20, 30], "k": [2.0, 3.0, 4.0]}, _acceptance_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-036", "Anchored-VWAP reclaim from the session extreme",
           "The VWAP anchored at today's high is the average cost of everyone who traded since the top; a close back "
           "above it after a while puts that whole cohort of sellers under water, so they cover and buyers regain "
           "control (mirror at the low); follow the reclaim.",
           {"min_age_min": [15, 30, 60]}, _avwap_reclaim, markets=("WIN",), source=_AVWAP, author="agent"),
    Family("E-037", "Narrow-day extreme break follow",
           "After the first hour, a session whose range is still small next to the 20-session average has not met "
           "day traders' range expectations; range is mean-reverting across days, so a close through the session "
           "extreme on such a day starts the expected expansion; follow it.",
           {"k": [0.4, 0.5, 0.6]}, _narrow_day_break, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-038", "Rotational-market edge fade",
           "When price keeps crossing the midpoint of its recent range many times per hour, the market is in balance "
           "with liquidity providers on both edges; a close near (not beyond) an edge meets their resting orders and "
           "rotates back, so fade the edge touch only in rotational conditions.",
           {"win_min": [30, 60, 90], "rate": [4, 6, 8]}, _rotation_edge_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
