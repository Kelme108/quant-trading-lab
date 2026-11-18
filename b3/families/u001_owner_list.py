"""Owner's list (2026-11-18, a public 'strategies list' post pasted in chat: 'agora vamos implementar essas estrategias
aqui para testar'). Only the ideas a WIN/WDO rule can see are here: bars (OHLCV) of ONE market plus session features.
Left out, with the reason:
- fake halt trap (no single-stock halts on index/dollar futures), dark pool footprints, big bid / Level 2, options chain
  spoofing, gamma squeeze, max pain, open interest fakeouts (no book, no options data in the bars);
- earnings overreaction, merger arbitrage, 'bagholder' -20% gaps (single-stock events);
- premarket VWAP reclaim, after-hours trap, closing-bell grab (B3 futures here trade the regular session only and the
  conveyor is flat before the close);
- FOMC fade (scheduled events are not in the conveyor's ctx yet);
- stop-loss hunting at the previous day's high/low = E-002 (already screened: too rare).
Every numeric choice is a round value around the post's own number; the grid only checks the plateau."""

from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family

SRC = "owner-pasted list of public trading setups (2026-11-18), adapted to B3 futures bars"


def _elapsed(ctx):
    """Minutes since the session open at the bar's close."""
    return (ctx.bar_in_day + 1) * ctx.tf


def _htf_trend(ctx, p):
    n = ctx.bars(p["htf_hours"] * 60)                    # 100 hours < 11 sessions: inside the 21-session window
    htf = ctx.cached(("htf_sma", n), lambda: pd.Series(ctx.c).rolling(n, min_periods=n).mean().to_numpy())
    ema = ctx.cached(("ema", p["ema_bars"]), lambda: ctx.ema(ctx.c, p["ema_bars"]))
    long = (ctx.c > htf) & ctx.cross(ctx.c > ema)
    short = (ctx.c < htf) & ctx.cross(ctx.c < ema)
    return long.astype(int) - short.astype(int)


def _vwap_wick(ctx, p):
    vw = ctx.vwap()
    rng = ctx.h - ctx.l
    lower = np.minimum(ctx.o, ctx.c) - ctx.l
    upper = ctx.h - np.maximum(ctx.o, ctx.c)
    med = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    heavy = ctx.v >= p["vol_k"] * med
    long = (rng > 0) & (ctx.l < vw) & (ctx.c > vw) & (lower >= p["wick_frac"] * rng) & heavy
    short = (rng > 0) & (ctx.h > vw) & (ctx.c < vw) & (upper >= p["wick_frac"] * rng) & heavy
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _first_hour_lock(ctx, p):
    lock_bar = ctx.bars(p["lock_min"]) - 1
    at_lock = np.where(ctx.bar_in_day == lock_bar, ctx.c, np.nan)
    lock_close = pd.Series(at_lock).groupby(ctx.day).transform("max").to_numpy()   # one value per session
    trend = np.where(ctx.bar_in_day > lock_bar, np.sign(lock_close - ctx.day_open), 0.0)
    ema = ctx.cached(("ema", p["ema_bars"]), lambda: ctx.ema(ctx.c, p["ema_bars"]))
    long = (trend > 0) & ctx.cross(ctx.c > ema)
    short = (trend < 0) & ctx.cross(ctx.c < ema)
    return long.astype(int) - short.astype(int)


def _broken_parabolic(ctx, p):
    k = int(p["run_bars"])
    green = (ctx.c > ctx.o).astype(float)
    red = (ctx.c < ctx.o).astype(float)
    run_up = ctx.roll(green, k, "min", include_current=False) == 1
    run_dn = ctx.roll(red, k, "min", include_current=False) == 1
    po, pc = ctx.prev(ctx.o), ctx.prev(ctx.c)
    bear_engulf = (ctx.c < ctx.o) & (ctx.o >= pc) & (ctx.c <= po)
    bull_engulf = (ctx.c > ctx.o) & (ctx.o <= pc) & (ctx.c >= po)
    return (run_dn & bull_engulf).astype(int) - (run_up & bear_engulf).astype(int)


def _rsi_exhaustion(ctx, p):
    r = ctx.rsi(int(p["rsi_n"]))
    rp = ctx.prev(r)
    hi, lo = p["level"], 100 - p["level"]
    short = (rp >= hi) & (ctx.c < ctx.o) & (ctx.c < ctx.prev(ctx.c))
    long = (rp <= lo) & (ctx.c > ctx.o) & (ctx.c > ctx.prev(ctx.c))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _absorption_follow(ctx, p):
    rng = ctx.h - ctx.l
    vmed = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    rmean = ctx.cached("rng_mean", lambda: ctx.same_minute(rng, "mean"))
    absorb = (ctx.v >= p["vol_k"] * vmed) & (rng <= p["range_k"] * rmean)
    drift = ctx.c - ctx.prev(ctx.c, ctx.bars(30))
    return (absorb & (drift > 0)).astype(int) - (absorb & (drift < 0)).astype(int)


def _rip_and_dip(ctx, p):
    nb = ctx.bars(p["or_min"])
    first = ctx.bar_in_day < nb
    g = pd.DataFrame({"d": ctx.day, "h": np.where(first, ctx.h, np.nan), "l": np.where(first, ctx.l, np.nan)})
    orh = g.groupby("d")["h"].transform("max").to_numpy()
    orl = g.groupby("d")["l"].transform("min").to_numpy()
    early = (~first) & (_elapsed(ctx) <= 120)
    h2, l2 = ctx.prev(ctx.h, 2), ctx.prev(ctx.l, 2)
    c1, c2, h1, l1 = ctx.prev(ctx.c, 1), ctx.prev(ctx.c, 2), ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    long = early & (h2 > orh) & (c1 < c2) & (ctx.c > h1) & (ctx.c > orh)
    short = early & (l2 < orl) & (c1 > c2) & (ctx.c < l1) & (ctx.c < orl)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _flag_fake_break(ctx, p):
    f, m = int(p["flag_bars"]), ctx.bars(30)
    move = ctx.c / ctx.prev(ctx.c, m) - 1.0
    typical = ctx.cached(("abs_move", m), lambda: ctx.prev_sessions(np.abs(move), "mean"))
    imp = ctx.prev(move, f)                                          # the impulse that ended f bars ago
    flag_lo = ctx.roll(ctx.l, f, "min", include_current=False)
    flag_hi = ctx.roll(ctx.h, f, "max", include_current=False)
    long = (imp >= p["k"] * typical) & (ctx.l < flag_lo) & (ctx.c > flag_lo)
    short = (imp <= -p["k"] * typical) & (ctx.h > flag_hi) & (ctx.c < flag_hi)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _opening_reversal(ctx, p):
    at = ctx.bar_in_day == ctx.bars(p["rev_min"]) - 1
    r = ctx.c / ctx.day_open - 1.0
    typical = ctx.cached("abs_r_same_minute", lambda: ctx.same_minute(np.abs(r), "mean"))
    short = at & (r >= p["k"] * typical)
    long = at & (r <= -p["k"] * typical)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-119", "Higher-timeframe trend, EMA reclaim entry",
           "Trade only in the direction of the long moving average of hourly closes (the post: 100 EMA on 1H; here "
           "the 50/100-hour simple mean); enter when price closes back across a short EMA in that direction.",
           {"htf_hours": [50, 100], "ema_bars": [10, 20, 30]}, _htf_trend, source=SRC + " #1 EMA bias", author="owner-list"),
    Family("E-120", "VWAP wick rejection on heavy volume",
           "Not the first touch: a bar that pierces the session VWAP, leaves a long wick and closes back on its side "
           "with volume well above normal for the minute shows larger players defending the level; trade the bounce.",
           {"wick_frac": [0.5, 0.67], "vol_k": [1.5, 2.0, 3.0]}, _vwap_wick, source=SRC + " #1 VWAP bounce", author="owner-list"),
    Family("E-121", "First-hour trend lock",
           "The direction of the first 30-60 minutes sets the day; afterwards only trade in that direction, entering "
           "when price closes back across a short EMA.",
           {"lock_min": [30, 60], "ema_bars": [10, 20, 30]}, _first_hour_lock, source=SRC + " #1 first hour trend lock",
           author="owner-list"),
    Family("E-122", "Broken parabolic (engulfing after a run)",
           "After several bars in a row of one colour, the first engulfing bar the other way marks exhaustion; fade it.",
           {"run_bars": [4, 5, 6]}, _broken_parabolic, source=SRC + " #2 broken parabolic", author="owner-list"),
    Family("E-123", "RSI exhaustion reversal",
           "RSI at an extreme (80-90+ or below 10-20) stretches the rubber band; the first bar that closes against "
           "the move starts the snap back.",
           {"level": [80, 85, 90], "rsi_n": [7, 14]}, _rsi_exhaustion, source=SRC + " #2 RSI exhaustion", author="owner-list"),
    Family("E-124", "Volume spike without movement, follow the drift",
           "A bar with very high volume but a small range during a slow grind is a large player filling orders "
           "(refill); trade with the grind's direction.",
           {"vol_k": [2.0, 3.0, 4.0], "range_k": [0.5, 0.75]}, _absorption_follow, source=SRC + " #3 market maker refill",
           author="owner-list"),
    Family("E-125", "Opening-range rip and dip",
           "In the first two hours, a break of the opening range, a one-bar dip, then a close back above the dip "
           "bar's high continues the break (mirror for shorts).",
           {"or_min": [5, 15, 30]}, _rip_and_dip, source=SRC + " #4 1-min rip & dip (opening range instead of premarket)",
           author="owner-list"),
    Family("E-126", "Flag fake breakdown",
           "After an impulse, a flag forms; the first poke beyond the flag against the impulse that closes back "
           "inside traps the breakout sellers and the real move follows the impulse.",
           {"flag_bars": [3, 6, 10], "k": [1.0, 1.5]}, _flag_fake_break, source=SRC + " #6 retail fakeouts",
           author="owner-list"),
    Family("E-127", "Opening reversal (the '9:45' reversal at B3's open)",
           "Early-session moves overshoot; 15-45 minutes after the open, fade a move from the open larger than usual "
           "for that time of day.",
           {"rev_min": [15, 30, 45], "k": [1.0, 1.5]}, _opening_reversal, source=SRC + " #6 9:45 reversal",
           author="owner-list"),
]
