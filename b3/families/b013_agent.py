"""Conveyor batch B-013 (agent, 2026-11-18). Mixed themes: noise-area break from the open, Ichimoku cloud break, multi-session stretch fade, asymmetric-volatility breaks, DiNapoli double repo, opening-gap fade, seasonal volatility ramp, slot reversal propensity, inside-yesterday balance fade, midday balance break."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _ffill_day(ctx, x):
    return pd.Series(np.asarray(x, float)).groupby(ctx.day).ffill().to_numpy()


def _fwd_in_day(ctx, x, k):
    """x of k bars LATER in the same session. Only ever fed into same_minute (previous sessions only)."""
    return pd.Series(np.asarray(x, float)).groupby(ctx.day).shift(-k).to_numpy()


# E-128 -------------------------------------------------------------------------------------------
def _noise_area_break(ctx, p):
    m = float(p["m"])
    r = ctx.c / ctx.day_open - 1.0
    sig = ctx.cached("noise_sigma14", lambda: ctx.same_minute(np.abs(r), "mean", n=14))
    pc = ctx.prev_session_value("close")
    up_ref = np.fmax(ctx.day_open, pc)
    dn_ref = np.fmin(ctx.day_open, pc)
    upper = up_ref * (1.0 + m * sig)
    lower = dn_ref * (1.0 - m * sig)
    live = ctx.bar_in_day >= ctx.bars(15)
    with np.errstate(invalid="ignore"):
        long = ctx.cross(live & (ctx.c > upper))
        short = ctx.cross(live & (ctx.c < lower))
    return long.astype(int) - short.astype(int)


# E-129 -------------------------------------------------------------------------------------------
def _ichimoku_cloud_break(ctx, p):
    kj = ctx.bars(p["base_min"])
    tk = max(2, int(round(kj * 9 / 26)))
    sb = 2 * kj

    def mid(n):
        return (ctx.roll(ctx.h, n, "max") + ctx.roll(ctx.l, n, "min")) / 2.0

    tenkan, kijun, spanb_raw = mid(tk), mid(kj), mid(sb)
    span_a = ctx.prev((tenkan + kijun) / 2.0, kj)      # plotted kj bars ahead = value from kj bars ago
    span_b = ctx.prev(spanb_raw, kj)
    top = np.maximum(span_a, span_b)
    bot = np.minimum(span_a, span_b)
    with np.errstate(invalid="ignore"):
        long = ctx.cross((ctx.c > top) & (tenkan > kijun))
        short = ctx.cross((ctx.c < bot) & (tenkan < kijun))
    return long.astype(int) - short.astype(int)


# E-130 -------------------------------------------------------------------------------------------
def _multi_session_stretch_fade(ctx, p):
    k = float(p["k"])
    mu = ctx.cached("c_prev20_mean", lambda: ctx.prev_sessions(ctx.c, "mean"))
    sd = ctx.cached("c_prev20_sd", lambda: ctx.prev_sessions(ctx.c, "sd"))
    with np.errstate(invalid="ignore", divide="ignore"):
        z = np.where(sd > 0, (ctx.c - mu) / sd, np.nan)
        l1, h1 = ctx.prev(ctx.l, 1), ctx.prev(ctx.h, 1)
        short = ctx.cross((z > k) & (ctx.c < l1))
        long = ctx.cross((z < -k) & (ctx.c > h1))
    return long.astype(int) - short.astype(int)


# E-131 -------------------------------------------------------------------------------------------
def _asym_vol_break(ctx, p):
    nb, q = ctx.bars(p["lookback_min"]), float(p["q"])
    path = ctx.roll(np.abs(ctx.c - ctx.prev(ctx.c, 1)), nb, "sum")
    norm = ctx.cached(("path_sm", nb), lambda: ctx.same_minute(path, "median"))
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    with np.errstate(invalid="ignore"):
        calm = path <= q * norm
        wild = path >= norm / q
        long = ctx.cross(ctx.c > hi) & calm
        short = ctx.cross(ctx.c < lo) & wild
    return long.astype(int) - short.astype(int)


# E-132 -------------------------------------------------------------------------------------------
def _double_repo(ctx, p):
    T, W = int(p["thrust"]), int(p["window_bars"])
    dma = ctx.prev(ctx.roll(ctx.c, 3, "mean"), 3)          # 3x3 displaced moving average
    with np.errstate(invalid="ignore"):
        s = np.where(np.isnan(dma), 0, np.where(ctx.c > dma, 1, np.where(ctx.c < dma, -1, 0))).astype(int)
    day = ctx.day
    out = np.zeros(ctx.n, dtype=int)
    run_up = run_dn = 0
    pen_dn = pen_up = -10**9          # bar of the first penetration after an up (down) thrust
    prev_s = 0
    for i in range(ctx.n):
        if i == 0 or day[i] != day[i - 1]:
            run_up = run_dn = 0
            pen_dn = pen_up = -10**9
            prev_s = 0
        si = s[i]
        if si == -1 and prev_s == 1:                         # close back below the 3x3
            if run_up >= T:
                pen_dn = i
            elif i - pen_dn <= W:
                out[i] = -1                                  # second penetration after an up thrust: sell
                pen_dn = -10**9
        if si == 1 and prev_s == -1:
            if run_dn >= T:
                pen_up = i
            elif i - pen_up <= W:
                out[i] = 1
                pen_up = -10**9
        if si == 1:
            run_up += 1
            run_dn = 0
        elif si == -1:
            run_dn += 1
            run_up = 0
        else:
            run_up = run_dn = 0
        prev_s = si
    return out


# E-133 -------------------------------------------------------------------------------------------
def _gap_fade(ctx, p):
    k, nb = float(p["k"]), ctx.bars(p["window_min"])
    pc = ctx.prev_session_value("close")
    gap = ctx.day_open / pc - 1.0
    typ = ctx.cached("gap_prev20", lambda: ctx.prev_sessions(np.abs(gap), "mean"))
    early = ctx.bar_in_day < nb
    l1, h1 = ctx.prev(ctx.l, 1), ctx.prev(ctx.h, 1)
    with np.errstate(invalid="ignore"):
        up_gap = gap > k * typ
        dn_gap = gap < -k * typ
        short = ctx.cross(early & up_gap & (ctx.c > pc) & (ctx.c < l1))
        long = ctx.cross(early & dn_gap & (ctx.c < pc) & (ctx.c > h1))
    return long.astype(int) - short.astype(int)


# E-134 -------------------------------------------------------------------------------------------
def _vol_ramp_break(ctx, p):
    nb, k = ctx.bars(p["lookback_min"]), float(p["k"])
    hz = ctx.bars(30)

    def ramp_fn():
        past = ctx.roll(ctx.h, hz, "max") - ctx.roll(ctx.l, hz, "min")
        fut = _fwd_in_day(ctx, past, hz)                    # range of the next 30 min (previous sessions only)
        pm = ctx.same_minute(past, "median")
        fm = ctx.same_minute(fut, "median")
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(pm > 0, fm / pm, np.nan)

    ramp = ctx.cached(("vol_ramp", hz), ramp_fn)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    with np.errstate(invalid="ignore"):
        up = ramp >= k
        long = ctx.cross(ctx.c > hi) & up
        short = ctx.cross(ctx.c < lo) & up
    return long.astype(int) - short.astype(int)


# E-135 -------------------------------------------------------------------------------------------
def _slot_reversal(ctx, p):
    hz, th = ctx.bars(p["horizon_min"]), float(p["th"])

    def prop_fn():
        past = ctx.c - ctx.prev(ctx.c, hz)
        fut = _fwd_in_day(ctx, ctx.c, hz) - ctx.c           # next-horizon move (previous sessions only)
        num = ctx.same_minute(np.sign(past) * fut, "mean")
        den = ctx.same_minute(np.abs(fut), "mean")
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(den > 0, num / den, np.nan)

    prop = ctx.cached(("slot_prop", hz), prop_fn)
    past = ctx.c - ctx.prev(ctx.c, hz)
    typ = ctx.cached(("absmove_prev20", hz), lambda: ctx.prev_sessions(np.abs(past), "mean"))
    with np.errstate(invalid="ignore"):
        rev = prop < -th
        short = ctx.cross(rev & (past > typ))
        long = ctx.cross(rev & (past < -typ))
    return long.astype(int) - short.astype(int)


# E-136 -------------------------------------------------------------------------------------------
def _inside_yesterday_fade(ctx, p):
    q, nb = float(p["q"]), ctx.bars(p["start_min"])
    pdh, pdl = ctx.prev_session_value("high"), ctx.prev_session_value("low")
    rng = pdh - pdl
    sh, sl = ctx.session_high(include_current=True), ctx.session_low(include_current=True)
    l1, h1 = ctx.prev(ctx.l, 1), ctx.prev(ctx.h, 1)
    with np.errstate(invalid="ignore"):
        inside = (ctx.bar_in_day >= nb) & (sh < pdh) & (sl > pdl) & (rng > 0)
        top = ctx.c >= pdh - q * rng
        bottom = ctx.c <= pdl + q * rng
        short = ctx.cross(inside & top & (ctx.c < l1))
        long = ctx.cross(inside & bottom & (ctx.c > h1))
    return long.astype(int) - short.astype(int)


# E-137 -------------------------------------------------------------------------------------------
def _midday_balance_break(ctx, p):
    end = int(p["end_minute"])
    inwin = (ctx.minute >= 12 * 60) & (ctx.minute + ctx.tf <= end)
    hmask = pd.Series(np.where(inwin, ctx.h, np.nan)).groupby(ctx.day).cummax().to_numpy()
    lmask = pd.Series(np.where(inwin, ctx.l, np.nan)).groupby(ctx.day).cummin().to_numpy()
    bh, bl = _ffill_day(ctx, hmask), _ffill_day(ctx, lmask)
    after = (ctx.minute >= end) & (ctx.minutes_to_close > 30)
    with np.errstate(invalid="ignore"):
        long = ctx.cross(after & (ctx.c > bh))
        short = ctx.cross(after & (ctx.c < bl))
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-128", "Noise-area break from the open",
           "Zarattini/Aziz/Barbon: moves from the open (or yesterday's close, whichever is farther) that stay inside "
           "the average absolute move for that minute are noise traded by liquidity providers; a close outside that "
           "band means a real supply/demand imbalance (informed or rebalancing flow) that keeps working in the same "
           "direction, so follow the first close outside the noise area.",
           {"m": [0.75, 1.0, 1.25]}, _noise_area_break, markets=("WIN",),
           source="Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY) "
                  "https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/",
           author="agent"),
    Family("E-129", "Ichimoku cloud break with Tenkan/Kijun alignment",
           "The Ichimoku cloud is a default overlay for many retail traders, who treat a close out of the cloud with "
           "Tenkan above Kijun as a trend start; their entries and the stops of those leaning on the cloud edge fire "
           "together at the break, so follow the first close outside the cloud when the two lines agree (mirror).",
           {"base_min": [26, 52, 78]}, _ichimoku_cloud_break, markets=("WIN",),
           source="Ichimoku Kumo Breakout https://doc.stocksharp.com/en/api-examples/0011_Ichimoku_Kumo_Breakout",
           author="agent"),
    Family("E-130", "Multi-session price stretch fade",
           "When the price sits far above its own 20-session mean (in 20-session standard deviations), swing holders "
           "are deep in profit and new multi-day buyers are scarce; the first intraday bar that closes below the "
           "previous bar's low starts their profit-taking, so fade the stretch on that counter bar (mirror).",
           {"k": [1.0, 1.5, 2.0]}, _multi_session_stretch_fade, markets=("WIN",), source="assistant reasoning",
           author="agent"),
    Family("E-131", "Asymmetric-volatility break (calm rallies, turbulent sell-offs)",
           "Index futures rise in calm tape (steady real-money buying while volatility sellers supply liquidity) and "
           "fall in turbulence (volatility feedback, hedgers and risk managers selling into it); so follow a break of "
           "the recent high only when the recent path is quieter than usual for the minute, and a break of the low "
           "only when it is busier than usual.",
           {"lookback_min": [15, 30, 60], "q": [0.7, 0.85, 1.0]}, _asym_vol_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-132", "DiNapoli double repo reversal",
           "After a thrust of consecutive closes above the 3x3 displaced average, a close below it, a close back above "
           "and a second close below within a few bars shows the thrust buyers failing twice to resume; the late "
           "buyers of the bounce are trapped and DiNapoli users sell together, so follow the reversal (mirror).",
           {"thrust": [6, 8, 10], "window_bars": [5, 8, 12]}, _double_repo, markets=("WIN",),
           source="Education on Double RePo on 15min chart in EUR USD "
                  "https://tw.tradingview.com/chart/EURUSD/S1gEffZF-Education-on-Double-RePo-on-15min-chart-in-EUR-USD-past-week",
           author="agent"),
    Family("E-133", "Opening-gap fade in the first hours",
           "A gap larger than usual is set by overnight orders placed at the open without two-sided local liquidity; "
           "once the opening orders are filled, local day traders and market makers lean back toward yesterday's "
           "close, so in the first part of the session sell each bar that closes below the previous low while price "
           "is still above yesterday's close on a gap up (mirror).",
           {"k": [0.5, 1.0, 1.5], "window_min": [60, 90, 120]}, _gap_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-134", "Seasonal volatility-ramp breakout",
           "At minutes where the next 30 minutes have usually been much more volatile than the last 30 (ahead of the "
           "US open, data times, the closing call), scheduled participants are about to arrive and liquidity "
           "providers widen; a break of the recent high/low just then is carried by the incoming flow, so follow "
           "breaks only when the historical volatility ramp ahead is steep.",
           {"lookback_min": [15, 30, 60], "k": [1.1, 1.25, 1.5]}, _vol_ramp_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-135", "Slot reversal propensity fade",
           "Some minutes of the day are dominated by liquidity providers (moves there have reversed over the last 20 "
           "sessions: the move before the minute predicted the opposite move after it); a larger-than-usual move "
           "into such a minute is absorbed by the same providers, so fade it only in slots with a measured reversal "
           "propensity.",
           {"horizon_min": [10, 20, 30], "th": [0.1, 0.2, 0.3]}, _slot_reversal, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-136", "Inside-yesterday balance edge fade",
           "While today's whole range stays inside yesterday's (after the first part of the session), the market "
           "accepts yesterday's value and nobody initiates; responsive sellers work the top part of yesterday's range "
           "and buyers the bottom, so a counter bar in the outer part of yesterday's range starts a rotation back "
           "toward its middle (mirror).",
           {"q": [0.15, 0.25, 0.35], "start_min": [30, 60, 90]}, _inside_yesterday_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-137", "Midday balance break",
           "From 12:00 the market trades in a low-liquidity midday balance while local desks are at lunch; when they "
           "and the US afternoon flow return, the first close outside that balance shows which side the afternoon "
           "initiative is on, and the stops resting just beyond the tight midday range push it on; follow it.",
           {"end_minute": [810, 840, 870]}, _midday_balance_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
