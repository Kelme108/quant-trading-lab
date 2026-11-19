"""Conveyor batch B-017 (agent, 2026-11-18). Mixed themes: post-settlement drift, indecision clusters at extremes,
the dollar-priced index, heavy-churn balance, failed VWAP reversion, failed-breakout re-breaks, alternating tape,
overnight dollar gaps, the London close and absorbed heavy counter bars."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _ffill_day(ctx, x):
    return pd.Series(np.asarray(x, float)).groupby(ctx.day).ffill().to_numpy()


def _cumsum_day(ctx, x):
    return pd.Series(np.asarray(x, float)).groupby(ctx.day).cumsum().to_numpy()


def _typ_move(ctx, nb):
    def f():
        m = ctx.c / ctx.prev(ctx.c, nb) - 1.0
        return ctx.prev_sessions(np.abs(m), "mean")
    return ctx.cached(("b017_typ_move", nb), f)


def _b(x):
    return np.nan_to_num(np.asarray(x, float), nan=0.0) > 0.5


# E-168 ---------------------------------------------------------------------------------------------------------
def _post_settlement_fade(ctx, p):
    k = p["k"]
    mtc = ctx.minutes_to_close
    in_win = (mtc < 85) & (mtc >= 70)                    # 17:00-17:15 settlement window on an 18:25 close
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    pv = _cumsum_day(ctx, np.where(in_win, tp * ctx.v, 0.0))
    vv = _cumsum_day(ctx, np.where(in_win, ctx.v, 0.0))
    anchor = np.where(vv > 0, pv / np.where(vv > 0, vv, 1.0), np.nan)
    after = (mtc < 70) & (mtc > 10)
    typ = _typ_move(ctx, ctx.bars(15))
    dev = ctx.c / anchor - 1.0
    c1 = ctx.prev(ctx.c, 1)
    short = after & (dev > k * typ) & (ctx.c < c1)
    long = after & (dev < -k * typ) & (ctx.c > c1)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-169 ---------------------------------------------------------------------------------------------------------
def _indecision_cluster(ctx, p):
    nb, m = ctx.bars(p["lookback_min"]), int(p["m"])
    rng = ctx.h - ctx.l
    med = ctx.cached("b017_rng_med", lambda: ctx.same_minute(ctx.h - ctx.l, "median"))
    body = np.abs(ctx.c - ctx.o)
    indec = ((rng > 0) & (body <= 0.3 * rng) & (rng >= 0.5 * med)).astype(float)
    cnt = ctx.roll(indec, 3, "sum", include_current=False)
    cl_h = ctx.roll(ctx.h, 3, "max", include_current=False)
    cl_l = ctx.roll(ctx.l, 3, "min", include_current=False)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    at_top = cl_h >= hi
    at_bot = cl_l <= lo
    short = at_top & (cnt >= m) & (ctx.c < cl_l)
    long = at_bot & (cnt >= m) & (ctx.c > cl_h)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-170 ---------------------------------------------------------------------------------------------------------
def _usd_index_break(ctx, p):
    nb = ctx.bars(p["win_min"])
    x = ctx.other_close()
    r = ctx.c / x
    rh = ctx.roll(r, nb, "max", include_current=False)
    rl = ctx.roll(r, nb, "min", include_current=False)
    ch = ctx.roll(ctx.h, nb, "max", include_current=False)
    cl = ctx.roll(ctx.l, nb, "min", include_current=False)
    up = (r > rh) & (ctx.c <= ch)            # new high in dollars, not yet in reais
    dn = (r < rl) & (ctx.c >= cl)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


# E-171 ---------------------------------------------------------------------------------------------------------
def _heavy_churn_fade(ctx, p):
    k, nb = p["k"], ctx.bars(p["win_min"])
    cv = _cumsum_day(ctx, ctx.v)
    cv_norm = ctx.cached("b017_cv_norm", lambda: ctx.same_minute(cv, "median"))
    sh, sl = ctx.session_high(True), ctx.session_low(True)
    srng = (sh - sl) / ctx.c
    srng_norm = ctx.cached("b017_srng_norm", lambda: ctx.same_minute(srng, "median"))
    churn = (cv >= k * cv_norm) & (srng <= srng_norm) & (ctx.bar_in_day >= ctx.bars(30))
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    short = churn & (ctx.h > hi) & (ctx.c < ctx.o)
    long = churn & (ctx.l < lo) & (ctx.c > ctx.o)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-172 ---------------------------------------------------------------------------------------------------------
def _failed_vwap_reversion(ctx, p):
    m, nb = p["m"], ctx.bars(p["win_min"])
    vw = ctx.vwap()
    d = ctx.c / vw - 1.0
    unit = ctx.cached("b017_vw_unit", lambda: ctx.prev_sessions(np.abs(ctx.c / ctx.vwap() - 1.0), "mean"))
    z = d / unit
    zmax = ctx.roll(z, nb, "max", include_current=False)
    zmin = ctx.roll(z, nb, "min", include_current=False)
    up = ctx.cross(z > m) & (zmax > m) & (zmin < 0.5 * m)       # was out, came back toward VWAP, out again
    dn = ctx.cross(z < -m) & (zmin < -m) & (zmax > -0.5 * m)
    return up.astype(int) - dn.astype(int)


# E-173 ---------------------------------------------------------------------------------------------------------
def _failed_break_rebreak(ctx, p):
    nb, wb = ctx.bars(p["lookback_min"]), ctx.bars(p["within_min"])
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    fail_up = (ctx.h > hi) & (ctx.c < hi)
    fail_dn = (ctx.l < lo) & (ctx.c > lo)
    bid = ctx.bar_in_day.astype(float)
    fh = _ffill_day(ctx, np.where(fail_up, ctx.h, np.nan))
    fl = _ffill_day(ctx, np.where(fail_dn, ctx.l, np.nan))
    age_h = bid - _ffill_day(ctx, np.where(fail_up, bid, np.nan))
    age_l = bid - _ffill_day(ctx, np.where(fail_dn, bid, np.nan))
    c1 = ctx.prev(ctx.c, 1)
    long = (ctx.c > fh) & (c1 <= fh) & (age_h >= 1) & (age_h <= wb)
    short = (ctx.c < fl) & (c1 >= fl) & (age_l >= 1) & (age_l <= wb)
    return long.astype(int) - short.astype(int)


# E-174 ---------------------------------------------------------------------------------------------------------
def _alternating_tape_end(ctx, p):
    n = int(p["n"])
    s = np.sign(ctx.c - ctx.prev(ctx.c, 1))
    s1 = ctx.prev(s, 1)
    alt = (s * s1 == -1).astype(float)
    alt_prev = ctx.roll(alt, n, "min", include_current=False) == 1       # bars t-n..t-1 each flipped sign
    zh = ctx.roll(ctx.h, n + 1, "max", include_current=False)
    zl = ctx.roll(ctx.l, n + 1, "min", include_current=False)
    long = alt_prev & (s > 0) & (s1 > 0) & (ctx.c > zh)
    short = alt_prev & (s < 0) & (s1 < 0) & (ctx.c < zl)
    return long.astype(int) - short.astype(int)


# E-175 ---------------------------------------------------------------------------------------------------------
def _dollar_gap_catch(ctx, p):
    k, wb = p["k"], ctx.bars(p["window_min"])
    x = ctx.other_close()
    nd = int(ctx.day.max()) + 1
    x_last = pd.Series(x).groupby(ctx.day).last().reindex(range(nd)).shift(1).to_numpy()[ctx.day]
    x_first = pd.Series(np.where(ctx.bar_in_day == 0, x, np.nan)).groupby(ctx.day).transform("max").to_numpy()
    x_first = np.where(ctx.bar_in_day >= 0, x_first, np.nan)      # first bar of the session is in the past at t>=0
    gx = x_first / x_last - 1.0
    gw = ctx.day_open / ctx.prev_session_value("close") - 1.0
    tx = ctx.cached("b017_tgx", lambda: ctx.prev_sessions(np.abs(gx), "mean"))
    tw = ctx.cached("b017_tgw", lambda: ctx.prev_sessions(np.abs(gw), "mean"))
    zx, zw = gx / tx, gw / tw
    early = (ctx.bar_in_day >= 1) & (ctx.bar_in_day <= wb)
    risk_off = (zx > k) & (zw > -0.5 * zx)      # dollar gapped up, the index did not price half of it
    risk_on = (zx < -k) & (zw < -0.5 * zx)
    short = early & risk_off & (ctx.c < ctx.prev(ctx.l, 1))
    long = early & risk_on & (ctx.c > ctx.prev(ctx.h, 1))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-176 ---------------------------------------------------------------------------------------------------------
def _london_close_fade(ctx, p):
    k, a = p["k"], int(p["anchor_min"])
    win = ctx.bars(60)
    p1 = _ffill_day(ctx, np.where(ctx.minute + ctx.tf <= a, ctx.c, np.nan))          # close at the anchor
    p0 = _ffill_day(ctx, np.where(ctx.minute + ctx.tf <= a - 60, ctx.c, np.nan))     # close one hour before
    move = p1 / p0 - 1.0
    typ = _typ_move(ctx, win)
    inwin = (ctx.minute >= a) & (ctx.minute < a + 60)
    short = inwin & (move > k * typ) & (ctx.c < ctx.prev(ctx.l, 1))
    long = inwin & (move < -k * typ) & (ctx.c > ctx.prev(ctx.h, 1))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-177 ---------------------------------------------------------------------------------------------------------
def _absorbed_heavy_counter(ctx, p):
    k, sb = p["k"], ctx.bars(p["slope_min"])
    vw = ctx.vwap()
    slope = vw - ctx.prev(vw, sb)
    med = ctx.cached("b017_v_med", lambda: ctx.same_minute(ctx.v, "median"))
    heavy1 = ctx.prev(ctx.v, 1) >= k * ctx.prev(med, 1)
    o1, c1, h1, l1 = ctx.prev(ctx.o, 1), ctx.prev(ctx.c, 1), ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    up = (ctx.c > vw) & (slope > 0)
    dn = (ctx.c < vw) & (slope < 0)
    long = up & heavy1 & (c1 < o1) & (ctx.c > h1)
    short = dn & heavy1 & (c1 > o1) & (ctx.c < l1)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-168", "Post-settlement drift fade",
           "WIN's daily settlement price is set from the 17:00-17:15 window; after it, the cash market is closed and "
           "index arbitrage is gone, so a futures-only drift away from the settlement-window average is thin "
           "speculative flow that dealers lean against (they hedge at tomorrow's cash open); fade a stretch from that "
           "average on the first bar closing back toward it.",
           {"k": [0.5, 1.0, 1.5]}, _post_settlement_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-169", "Indecision cluster at an extreme, break against",
           "Several normal-size small-body bars sitting at the high of the last hour show buyers and sellers trading "
           "two-way at the top with no buyer paying up; when price then closes below the cluster's low, the buyers who "
           "stood in the cluster are trapped and the push is over, so sell (mirror at the low).",
           {"lookback_min": [30, 60, 90], "m": [2, 3]}, _indecision_cluster, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-170", "Dollar-priced index break follow",
           "Foreign investors, the marginal Ibovespa buyers, watch the index in dollars (WIN / WDO); a new window high "
           "of that ratio while WIN in reais is still under its own window high means foreign holders already see a "
           "breakout and their stops/entries trigger, which then lifts WIN; follow it (mirror).",
           {"win_min": [15, 30, 60]}, _usd_index_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-171", "Heavy-churn session edge fade",
           "A session trading far more contracts than usual for the minute while its range is no wider than usual is "
           "dominated by two-sided size (hedgers, arbitrage, market makers) absorbing both directions; in that regime "
           "a bar that pokes to a new short-term extreme but closes against its open meets that absorption, so fade it.",
           {"k": [1.2, 1.5], "win_min": [15, 30, 60]}, _heavy_churn_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-172", "Failed VWAP-band reversion follow",
           "A stretch from the session VWAP draws mean-reversion traders; when price reverts toward VWAP and then "
           "stretches out beyond the band again, the faders of the first stretch are trapped a second time and their "
           "stops plus the trend side's adds carry the move; follow the second exit from the band (mirror).",
           {"m": [1.0, 1.5, 2.0], "win_min": [30, 60]}, _failed_vwap_reversion, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-173", "Failed-breakout high re-break follow",
           "A poke above the recent high that closes back inside invites fade traders who put their stops just above "
           "the poke's high; a later close above that failure high within the next minutes runs those stops and shows "
           "the breakout side has absorbed the faders, so follow it (mirror at lows).",
           {"lookback_min": [15, 30, 60], "within_min": [15, 30, 60]}, _failed_break_rebreak, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-174", "Alternating-tape end follow",
           "A run of closes that flip sign every bar is quote bouncing by liquidity providers with no initiator; two "
           "same-sign closes in a row that also clear the alternating zone's high mark the first initiative order "
           "breaking the bounce, and makers pull quotes in its direction; follow it (mirror).",
           {"n": [3, 4, 5]}, _alternating_tape_end, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-175", "Overnight dollar-gap index catch-down",
           "An opening dollar gap well above normal is overnight risk-off news priced by FX dealers; when WIN opened "
           "without pricing at least half of it, foreign equity desks sell the index during the morning to catch up, "
           "so sell WIN counter bars (close below the prior low) early in the session (mirror for a dollar gap down).",
           {"k": [0.5, 1.0, 1.5], "window_min": [60, 120, 180]}, _dollar_gap_catch, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-176", "London-close move fade",
           "European desks that trade Brazilian exposure flatten into the London close (12:30 or 13:30 in Sao Paulo, "
           "by season); a WIN hour that moved much more than usual into that time carried their closing flow, which "
           "then stops, so in the following hour fade the move on the first bar closing back past the prior bar.",
           {"k": [0.5, 1.0, 1.5], "anchor_min": [750, 780, 810]}, _london_close_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-177", "Absorbed heavy counter bar in a session trend",
           "In a session trend (price on the rising side of a rising VWAP), a counter bar on heavy volume is a large "
           "seller hitting bids; when the very next bar closes above that bar's high, the trend side absorbed the "
           "whole sale and the seller is under water at once, so the trend resumes; follow it (mirror).",
           {"k": [1.5, 2.0, 3.0], "slope_min": [30, 60]}, _absorbed_heavy_counter, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
