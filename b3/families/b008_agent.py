"""Conveyor batch B-008 (agent, 2026-11-18). Mixed themes: bar gaps, Aroon timing, volume clock, Brazilian PFR setup,
hidden divergence, VWAP skew, overnight gap and prior-close carry, VWAP slope, daily-candle colour."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from b3.esteira import Family


def _typ_range(ctx):
    return ctx.cached("b008_typ_range", lambda: ctx.prev_sessions(ctx.h - ctx.l, "mean"))


# E-069 ---------------------------------------------------------------------------------------------
def _bar_gap_fade(ctx, p):
    k = p["k"]
    pc = ctx.prev(ctx.c, 1)
    typ = _typ_range(ctx)
    gap = ctx.o - pc
    ok = typ > 0
    up = ok & (gap >= k * typ) & (ctx.c >= ctx.o)        # opened above the last trade and never gave it back
    dn = ok & (gap <= -k * typ) & (ctx.c <= ctx.o)
    return dn.astype(int) - up.astype(int)


# E-070 ---------------------------------------------------------------------------------------------
def _bars_since(ctx, x, n, how):
    ext = ctx.roll(x, n + 1, how)
    since = np.full(ctx.n, np.nan)
    for lag in range(n, -1, -1):                          # most recent lag written last, so it wins
        xv = x if lag == 0 else ctx.prev(x, lag)
        since = np.where(xv == ext, float(lag), since)
    return since


def _aroon_cross(ctx, p):
    n, th = int(p["n"]), float(p["th"])
    sh = ctx.cached(("b008_since_h", n), lambda: _bars_since(ctx, ctx.h, n, "max"))
    sl = ctx.cached(("b008_since_l", n), lambda: _bars_since(ctx, ctx.l, n, "min"))
    osc = 100.0 * (n - sh) / n - 100.0 * (n - sl) / n
    long = ctx.cross(osc >= th)
    short = ctx.cross(osc <= -th)
    return long.astype(int) - short.astype(int)


# E-071 ---------------------------------------------------------------------------------------------
def _volume_clock(ctx, p):
    m, k = float(p["m"]), float(p["k"])
    cumv = ctx.cached("b008_cumv", lambda: pd.Series(ctx.v).groupby(ctx.day).cumsum().to_numpy())
    mb = ctx.cached("b008_vmean", lambda: ctx.prev_sessions(ctx.v, "mean"))
    B = m * mb
    with np.errstate(divide="ignore", invalid="ignore"):
        bucket = np.where(B > 0, np.floor(cumv / B), np.nan)
    new = bucket > ctx.prev(bucket, 1)
    s = pd.Series(np.where(new, ctx.c, np.nan))
    anc = s.groupby(ctx.day).transform(lambda z: z.shift(1).ffill()).to_numpy()
    anc = np.where(np.isnan(anc), ctx.day_open, anc)      # first bucket of the session starts at the open
    move = ctx.c - anc
    scale = _typ_range(ctx) * math.sqrt(m)
    long = new & (move >= k * scale)
    short = new & (move <= -k * scale)
    return long.astype(int) - short.astype(int)


# E-072 ---------------------------------------------------------------------------------------------
def _pfr(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    l1, l2 = ctx.prev(ctx.l, 1), ctx.prev(ctx.l, 2)
    h1, h2 = ctx.prev(ctx.h, 1), ctx.prev(ctx.h, 2)
    c1 = ctx.prev(ctx.c, 1)
    lo_n = ctx.roll(ctx.l, nb, "min")
    hi_n = ctx.roll(ctx.h, nb, "max")
    buy = (ctx.l < l1) & (ctx.l < l2) & (ctx.c > c1) & (ctx.l <= lo_n)
    sell = (ctx.h > h1) & (ctx.h > h2) & (ctx.c < c1) & (ctx.h >= hi_n)
    return ctx.cross(buy).astype(int) - ctx.cross(sell).astype(int)


# E-073 ---------------------------------------------------------------------------------------------
def _hidden_div(ctx, p):
    nb = ctx.bars(p["window_min"])
    rsi = ctx.rsi(14)
    vw = ctx.vwap()
    lo_now = ctx.roll(ctx.l, nb, "min")
    hi_now = ctx.roll(ctx.h, nb, "max")
    rlo_now = ctx.roll(rsi, nb, "min")
    rhi_now = ctx.roll(rsi, nb, "max")
    lo_prev, hi_prev = ctx.prev(lo_now, nb), ctx.prev(hi_now, nb)
    rlo_prev, rhi_prev = ctx.prev(rlo_now, nb), ctx.prev(rhi_now, nb)
    bull = (ctx.c > vw) & (lo_now > lo_prev) & (rlo_now < rlo_prev) & (ctx.c > ctx.prev(ctx.h, 1))
    bear = (ctx.c < vw) & (hi_now < hi_prev) & (rhi_now > rhi_prev) & (ctx.c < ctx.prev(ctx.l, 1))
    return ctx.cross(bull).astype(int) - ctx.cross(bear).astype(int)


# E-074 ---------------------------------------------------------------------------------------------
def _vwap_skew(ctx, p):
    th, nb = float(p["th"]), int(p["brk_bars"])
    sh = ctx.session_high(include_current=True)
    sl = ctx.session_low(include_current=True)
    rng = sh - sl
    with np.errstate(divide="ignore", invalid="ignore"):
        skew = np.where(rng > 0, (ctx.vwap() - (sh + sl) / 2.0) / rng, np.nan)
    started = ctx.bar_in_day >= ctx.bars(30)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    long = started & (skew >= th) & ctx.cross(ctx.c > hi)
    short = started & (skew <= -th) & ctx.cross(ctx.c < lo)
    return long.astype(int) - short.astype(int)


# E-075 ---------------------------------------------------------------------------------------------
def _gap_direction_break(ctx, p):
    g, nb = float(p["gap_frac"]), ctx.bars(p["window_min"])
    pc = ctx.prev_session_value("close")
    gap = ctx.day_open / pc - 1.0
    up_ok = (gap > g) & (ctx.session_low(include_current=True) > pc)      # gap up still unfilled
    dn_ok = (gap < -g) & (ctx.session_high(include_current=True) < pc)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    long = up_ok & ctx.cross(ctx.c > hi)
    short = dn_ok & ctx.cross(ctx.c < lo)
    return long.astype(int) - short.astype(int)


# E-076 ---------------------------------------------------------------------------------------------
def _vwap_slope_turn(ctx, p):
    nb, k = ctx.bars(p["window_min"]), float(p["k"])
    vw = ctx.vwap()
    slope = vw - ctx.prev(vw, nb)
    thr = k * _typ_range(ctx)
    long = ctx.cross(slope >= thr) & (ctx.c > vw)
    short = ctx.cross(slope <= -thr) & (ctx.c < vw)
    return long.astype(int) - short.astype(int)


# E-077 ---------------------------------------------------------------------------------------------
def _day_candle_flip(ctx, p):
    nb = ctx.bars(p["away_min"])
    below = (ctx.c < ctx.day_open).astype(float)
    above = (ctx.c > ctx.day_open).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    long = was_below & (ctx.c > ctx.day_open)
    short = was_above & (ctx.c < ctx.day_open)
    return long.astype(int) - short.astype(int)


# E-078 ---------------------------------------------------------------------------------------------
def _close_location_carry(ctx, p):
    q, nb = float(p["q"]), ctx.bars(p["window_min"])
    ph, pl, pc = ctx.prev_session_value("high"), ctx.prev_session_value("low"), ctx.prev_session_value("close")
    with np.errstate(divide="ignore", invalid="ignore"):
        clv = np.where(ph > pl, (pc - pl) / (ph - pl), np.nan)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    long = (clv >= 1.0 - q) & ctx.cross(ctx.c > hi)
    short = (clv <= q) & ctx.cross(ctx.c < lo)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-069", "Bar-open gap fill fade",
           "A bar that opens well away from the previous bar's last trade and keeps the gap at its close was printed "
           "through an empty book (liquidity providers pulled quotes for a moment), not by new information; once "
           "quotes refill, the vacuum is closed by passive traders leaning back toward the last trade, so fade the gap.",
           {"k": [0.1, 0.2, 0.4]}, _bar_gap_fade, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-070", "Aroon crossover follow",
           "Chande's Aroon measures how recently the window's high and low were made and is a stock trend trigger on "
           "retail platforms; when the oscillator swings to a strong positive (negative) value, the latest extreme is "
           "fresh while the opposite one is stale, and the timing-based trend followers who use it enter together, "
           "extending the move; follow the cross.",
           {"n": [14, 25, 50], "th": [50, 70, 90]}, _aroon_cross, markets=("WIN",), source="assistant reasoning",
           author="agent"),
    Family("E-071", "Volume-clock bucket move follow",
           "In volume time (buckets of a fixed number of contracts, Easley/Lopez de Prado), a bucket whose price change "
           "is large means the contracts in it were traded mostly by one side; informed parents are split across "
           "buckets, so the next bucket keeps the sign; follow a large completed bucket.",
           {"m": [10, 20, 40], "k": [0.5, 1.0, 1.5]}, _volume_clock, markets=("WIN",), source="assistant reasoning",
           author="agent"),
    Family("E-072", "PFR reversal-close bar (Stormer)",
           "The PFR (preco de fechamento de reversao) is one of the most traded Brazilian retail setups: a bar that "
           "makes a low below the two previous lows (and the recent low) but closes above the previous close shows the "
           "sellers' push failing inside one bar; the sellers who sold the new low are trapped and the many setup "
           "users buy right after it, so follow the reversal (mirror for highs).",
           {"lookback_min": [10, 20, 40]}, _pfr, markets=("WIN",),
           source="MY BOX by Gustavo - TradingView (PFR rules) https://www.tradingview.com/script/xNSlj2AU/",
           author="agent"),
    Family("E-073", "Hidden RSI divergence continuation",
           "On the buying side of the VWAP, a higher price low made while the RSI makes a lower low means the pullback "
           "was sharp but did not cost the trend any ground: momentum-based sellers were absorbed by trend holders; "
           "the first close above the prior bar's high resumes the trend (mirror below the VWAP).",
           {"window_min": [15, 30, 60]}, _hidden_div, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-074", "VWAP skew in the day's range",
           "When the session VWAP sits well above the midpoint of the day's range, most of today's contracts traded in "
           "the upper part: buyers own the day's inventory and lower prices were rejected quickly; short-term breaks "
           "up in such a session are carried by that inventory owner, so follow a short-term high break only when "
           "the volume skew agrees (mirror).",
           {"th": [0.1, 0.2, 0.3], "brk_bars": [3, 5, 8]}, _vwap_skew, markets=("WIN",), source="assistant reasoning",
           author="agent"),
    Family("E-075", "Unfilled opening-gap direction break",
           "An overnight gap that has not been filled at all during the session is overnight information that local "
           "traders failed to reverse; the gap side holds the inventory, so intraday breaks in the gap direction are "
           "followed while breaks against it are not traded; follow N-minute highs (lows) on unfilled gap-up (down) days.",
           {"gap_frac": [0.0, 0.001, 0.002], "window_min": [15, 30, 60]}, _gap_direction_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-076", "Session-VWAP slope turn",
           "The session VWAP is the average cost of everyone who traded today; when its slope turns clearly positive "
           "with price above it, the average participant is being forced to pay up and late shorts are losing on the "
           "day's average, so VWAP-benchmarked execution and covering keep lifting price; follow the slope turn (mirror).",
           {"window_min": [15, 30, 60], "k": [0.1, 0.25, 0.5]}, _vwap_slope_turn, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-077", "Daily-candle colour flip follow",
           "The session open is the zero line of every day trader's daily candle and of intraday P&L for the day; after "
           "price has stayed on one side of it for a while, a close back across flips the daily candle's colour on "
           "every chart, triggering day traders' bias changes and the stops of those positioned for the old colour; "
           "follow the flip.",
           {"away_min": [15, 30, 60]}, _day_candle_flip, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-078", "Prior-session close-location carry break",
           "A session that closed near its high means buyers were still adding into the close (late informed or "
           "rebalancing flow not yet finished); that flow carries into the next session, so today's short-term high "
           "breaks are followed after a strong close and low breaks after a weak close (mirror).",
           {"q": [0.2, 0.3, 0.4], "window_min": [15, 30, 60]}, _close_location_carry, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
