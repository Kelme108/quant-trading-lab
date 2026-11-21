"""Conveyor batch B-039 (agent, 2026-11-21). Round-trip hour, counter-leg position, day after an inside day, double-tested box, volatile-tape liquidity provision, Ease-of-Movement and Chaikin flow crosses, doji-regime days, opening half-hour and snap-back breaks."""
from __future__ import annotations
import numpy as np
import pandas as pd
from b3.esteira import Family


# ----------------------------------------------------------------------------- shared helpers

def _breaks(ctx, win_min):
    """First close beyond the high/low of the previous win_min minutes (one signal per break)."""
    def f():
        n = ctx.bars(win_min)
        hi = ctx.roll(ctx.h, n, "max", include_current=False)
        lo = ctx.roll(ctx.l, n, "min", include_current=False)
        return ctx.cross(ctx.c > hi), ctx.cross(ctx.c < lo), hi, lo
    return ctx.cached(("b039_breaks", win_min), f)


def _typ_move(ctx, minutes):
    """Median |close - close `minutes` earlier| at the same minute over the 20 sessions before."""
    def f():
        nb = ctx.bars(minutes)
        return ctx.same_minute(np.abs(ctx.c - ctx.prev(ctx.c, nb)), "median")
    return ctx.cached(("b039_typmove", minutes), f)


def _typ_range(ctx):
    return ctx.cached("b039_typrange", lambda: ctx.same_minute(ctx.h - ctx.l, "median"))


def _out(long, short):
    long = np.nan_to_num(np.asarray(long, float), nan=0.0) > 0
    short = np.nan_to_num(np.asarray(short, float), nan=0.0) > 0
    both = long & short
    return (long & ~both).astype(int) - (short & ~both).astype(int)


def _gt(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    with np.errstate(invalid="ignore"):
        return np.where(np.isfinite(a) & np.isfinite(b), a > b, False)


def _lt(a, b):
    return _gt(b, a)


def _ge(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    with np.errstate(invalid="ignore"):
        return np.where(np.isfinite(a) & np.isfinite(b), a >= b, False)


def _daily(ctx):
    """Per-session open/high/low/close indexed by session number (missing sessions are NaN)."""
    def f():
        df = pd.DataFrame({"d": ctx.day, "o": ctx.o, "h": ctx.h, "l": ctx.l, "c": ctx.c})
        g = df.groupby("d").agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"))
        return g.reindex(range(int(ctx.day.max()) + 1))
    return ctx.cached("b039_daily", f)


# ----------------------------------------------------------------------------- families

def _round_trip_hour_fade(ctx, p):
    up, dn, _, _ = _breaks(ctx, p["win_min"])
    r60 = np.abs(ctx.c - ctx.prev(ctx.c, ctx.bars(60)))
    flat = _lt(r60, p["q"] * _typ_move(ctx, 60))
    return _out(dn & flat, up & flat)


def _counter_leg_break_fade(ctx, p):
    def f():
        n = ctx.bars(120)
        hi = ctx.roll(ctx.h, n, "max")
        lo = ctx.roll(ctx.l, n, "min")
        rng = hi - lo
        return (ctx.c - lo) / np.where(rng > 0, rng, np.nan)
    pos = ctx.cached("b039_pos120", f)
    up, dn, _, _ = _breaks(ctx, p["win_min"])
    th = p["th"]
    return _out(dn & _gt(pos, 1.0 - th), up & _lt(pos, th))


def _after_inside_day_fade(ctx, p):
    g = _daily(ctx)
    s = p["slack"]
    yh, yl = g["h"].shift(1).to_numpy(), g["l"].shift(1).to_numpy()
    yyh, yyl = g["h"].shift(2).to_numpy(), g["l"].shift(2).to_numpy()
    r2 = yyh - yyl
    inside_day = _ge(yyh + s * r2, yh) & _ge(yl, yyl - s * r2) & _gt(r2, 0.0)
    regime = inside_day[ctx.day]
    up, dn, _, _ = _breaks(ctx, p["win_min"])
    return _out(dn & regime, up & regime)


def _double_tested_box_fade(ctx, p):
    win, tol = p["win_min"], p["tol"]

    def f():
        n = ctx.bars(win)
        _, _, hi, lo = _breaks(ctx, win)
        box = hi - lo
        top, bot = hi - tol * box, lo + tol * box
        ch = np.zeros(ctx.n)
        cl = np.zeros(ctx.n)
        for j in range(1, n + 1):
            ch += _ge(ctx.prev(ctx.h, j), top)
            cl += _ge(bot, ctx.prev(ctx.l, j))
        return (ch >= 2) & (cl >= 2) & _gt(box, 0.0)
    two_sided = ctx.cached(("b039_dtbox", win, tol), f)
    up, dn, _, _ = _breaks(ctx, win)
    return _out(dn & two_sided, up & two_sided)


def _volatile_tape_fade(ctx, p):
    def f():
        n = ctx.bars(30)
        r = ctx.roll(ctx.h, n, "max") - ctx.roll(ctx.l, n, "min")
        return r, ctx.same_minute(r, "median")
    r30, typ = ctx.cached("b039_rng30", f)
    vol = _gt(r30, p["k"] * typ)
    up, dn, _, _ = _breaks(ctx, p["win_min"])
    return _out(dn & vol, up & vol)


def _emv_cross_follow(ctx, p):
    span = int(p["span"])

    def f():
        mid = (ctx.h + ctx.l) / 2.0
        dm = mid - ctx.prev(mid)
        vv = np.where(ctx.v > 0, ctx.v, np.nan)
        emv = dm * (ctx.h - ctx.l) / vv
        es = ctx.ema(np.nan_to_num(emv, nan=0.0), span)
        return es, ctx.prev_sessions(es, "sd")
    es, sd = ctx.cached(("b039_emv", span), f)
    k = p["k"]
    long = ctx.cross(_gt(es, k * sd))
    short = ctx.cross(_lt(es, -k * sd))
    return _out(long, short)


def _chaikin_cross_follow(ctx, p):
    sc = int(p["scale"])

    def f():
        rng = ctx.h - ctx.l
        clv = np.where(rng > 0, ((ctx.c - ctx.l) - (ctx.h - ctx.c)) / np.where(rng > 0, rng, 1.0), 0.0)
        adl = pd.Series(clv * ctx.v).groupby(ctx.day).cumsum().to_numpy(float)
        osc = ctx.ema(adl, 3 * sc) - ctx.ema(adl, 10 * sc)
        return osc, ctx.prev_sessions(osc, "sd")
    osc, sd = ctx.cached(("b039_chaikin", sc), f)
    k = p["k"]
    long = ctx.cross(_gt(osc, k * sd))
    short = ctx.cross(_lt(osc, -k * sd))
    return _out(long, short)


def _doji_regime_fade(ctx, p):
    n = int(p["n_sessions"])
    g = _daily(ctx)
    rng = (g["h"] - g["l"]).where(lambda x: x > 0)
    body = (g["c"] - g["o"]).abs() / rng
    avg = body.rolling(n, min_periods=n).mean().shift(1).to_numpy()
    regime = _lt(avg, p["th"])[ctx.day]
    up, dn, _, _ = _breaks(ctx, 15)
    return _out(dn & regime, up & regime)


def _opening_half_hour_fade(ctx, p):
    up, dn, _, _ = _breaks(ctx, p["win_min"])
    early = (ctx.bar_in_day * ctx.tf < p["end_min"]) & (ctx.bar_in_day >= ctx.bars(p["win_min"]))
    return _out(dn & early, up & early)


def _snap_back_break_fade(ctx, p):
    up, dn, _, _ = _breaks(ctx, p["win_min"])
    o1, c1 = ctx.prev(ctx.o), ctx.prev(ctx.c)
    lim = p["k"] * _typ_range(ctx)
    was_down = _gt(o1 - c1, lim) & _gt(o1 - c1, 0.0)
    was_up = _gt(c1 - o1, lim) & _gt(c1 - o1, 0.0)
    return _out(dn & was_up, up & was_down)


FAMILIES = [
    Family("E-388", "Round-trip-hour micro-break fade",
           "When the close is back near where it was an hour ago (net hourly change small next to its usual size at this minute), the hour's buyers and sellers have cancelled out and nobody holds a directional parent order; a short-term break of the recent high/low in that state is a local push that the two-way hour absorbs, so fade it (rolling-hour net change, not the move from the open or the VWAP slope).",
           {"win_min": [10, 15, 30], "q": [0.25, 0.5, 0.75]}, _round_trip_hour_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-389", "Counter-leg micro-break fade",
           "An up-break of the recent short-term high made while the close is still in the lower part of the last two hours' range is a relief rally inside a larger down leg: short covering triggers it, while the sellers who built the two-hour leg still hold inventory and sell into the bounce; fade it (mirror for down-breaks high in the two-hour range).",
           {"win_min": [10, 15, 30], "th": [0.4, 0.5, 0.6]}, _counter_leg_break_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-390", "Day-after-inside-day micro-break fade",
           "A session whose whole range stayed inside the session before it was a contraction day: other-timeframe traders did not initiate and the two-day range is the frame everyone trades; the next session's short-term breaks happen inside that balance, without new initiative behind them, and revert as responsive traders lean on them.",
           {"slack": [0.0, 0.1, 0.2], "win_min": [10, 15, 30]}, _after_inside_day_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-391", "Double-tested box break fade",
           "A recent box whose top AND bottom were each touched at least twice is a rectangle that both sides defend with resting orders; the first close through one edge mostly fills the stops parked just beyond it, after which the defenders who held the edge twice re-establish it, so the break reverts into the box.",
           {"win_min": [20, 30, 45], "tol": [0.1, 0.15, 0.2]}, _double_tested_box_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-392", "Volatile-tape micro-break fade (liquidity-provision premium)",
           "Nagel: the return to providing liquidity (short-term reversal) rises sharply when volatility is high, because intermediaries withdraw and the remaining liquidity is priced dearly; when the last half hour's range is far above its usual size at this minute, short-term breaks are demand for immediacy into a thin book, so fading them earns that elevated premium.",
           {"win_min": [10, 15, 30], "k": [1.25, 1.5, 2.0]}, _volatile_tape_fade, markets=("WIN",),
           source="Evaporating Liquidity (Nagel, NBER w17653) https://www.nber.org/papers/W17653", author="agent"),
    Family("E-393", "Ease-of-Movement threshold cross follow",
           "Arms' Ease of Movement measures how far the bar midpoint moves per contract traded; when its smoothed value crosses a clear threshold, price is rising (falling) with little volume needed, i.e. the opposite side has stepped back from the book; while that withdrawal lasts the move continues, so follow the cross.",
           {"span": [10, 14, 20], "k": [0.25, 0.5, 1.0]}, _emv_cross_follow, markets=("WIN",),
           source="Ease of Movement Indicator https://www.incrediblecharts.com/indicators/ease_of_movement.php", author="agent"),
    Family("E-394", "Doji-regime micro-break fade",
           "When recent sessions have mostly closed near where they opened (small average daily body versus daily range), each day's excursions are given back by the close: the market is in a multi-day regime where intraday pushes are taken back by responsive traders; short-term breaks in such a regime are faded (daily open-to-close body share, not daily return autocorrelation or today's own candle).",
           {"n_sessions": [5, 10, 15], "th": [0.4, 0.45, 0.5]}, _doji_regime_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-395", "Opening half-hour micro-break fade",
           "In the first minutes after the open the book is still being rebuilt after the auction and liquidity is thinnest, so overnight orders arriving piecemeal push small boxes back and forth; a short-term break in that window is order-arrival noise that the market makers re-quoting the book pull back, so fade it until the opening period is over.",
           {"win_min": [5, 10, 15], "end_min": [30, 45, 60]}, _opening_half_hour_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-396", "Snap-back break fade",
           "A close through the recent high printed right after a clearly down bar is a V-shaped snap: the break comes from a one-bar reversal of a selling bar (stops of the dip sellers plus a burst of market buys), not from a build-up of buyers; the urgent orders are spent within the bar and the box's sellers return, so fade it (mirror after an up bar).",
           {"win_min": [10, 15, 30], "k": [0.0, 0.5, 1.0]}, _snap_back_break_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-397", "Chaikin oscillator threshold cross follow",
           "The Chaikin oscillator (fast minus slow EMA of today's accumulation/distribution line) turns when volume starts closing bars on the other side of their ranges; a cross beyond a clear threshold means accumulation (distribution) is accelerating, a parent order being worked through the session, which keeps pushing for a while, so follow it.",
           {"scale": [1, 2, 3], "k": [0.5, 1.0, 1.5]}, _chaikin_cross_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
