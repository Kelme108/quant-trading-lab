"""Conveyor batch B-038 (agent, 2026-11-19). Gap-in break bars, neutral days, developing-POC stretch, break fatigue, Larry Williams 9.3, Raschke 80-20 and Turtle Soup Plus One, two-day value conflict, hourly Crabel stretch and same-half-hour return seasonality."""
from __future__ import annotations
import numpy as np
import pandas as pd
from b3.esteira import Family


# ----------------------------------------------------------------------------- shared helpers

def _days(ctx):
    return np.asarray(ctx.day).astype(int)


def _breaks(ctx, win_min):
    """First close beyond the high/low of the previous win_min minutes (one signal per break)."""
    def f():
        n = ctx.bars(win_min)
        hi = ctx.roll(ctx.h, n, "max", include_current=False)
        lo = ctx.roll(ctx.l, n, "min", include_current=False)
        return ctx.cross(ctx.c > hi), ctx.cross(ctx.c < lo), hi, lo
    return ctx.cached(("b038_breaks", win_min), f)


def _typ_move(ctx, minutes):
    """Median |close - close `minutes` earlier| at the same minute over the 20 sessions before."""
    def f():
        nb = ctx.bars(minutes)
        return ctx.same_minute(np.abs(ctx.c - ctx.prev(ctx.c, nb)), "median")
    return ctx.cached(("b038_typmove", minutes), f)


def _typ_range(ctx):
    return ctx.cached("b038_typrange", lambda: ctx.same_minute(ctx.h - ctx.l, "median"))


def _gt(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    with np.errstate(invalid="ignore"):
        return np.where(np.isfinite(a) & np.isfinite(b), a > b, False)


def _lt(a, b):
    return _gt(b, a)


def _b(x):
    """Boolean view of a float/bool array (NaN -> False)."""
    return np.nan_to_num(np.asarray(x, float), nan=0.0) > 0.5


def _pb(ctx, x, lag=1):
    """Boolean x of `lag` bars earlier in the same session."""
    return _b(ctx.prev(np.asarray(x, float), lag))


def _out(long, short):
    long = _b(long)
    short = _b(short)
    both = long & short
    return (long & ~both).astype(int) - (short & ~both).astype(int)


def _lookup(tab, day, col):
    """tab: DataFrame indexed by session 0..max, columns sorted ints; value at (day, col) per bar."""
    arr = tab.to_numpy(float)
    cols = np.asarray(tab.columns, dtype=np.int64)
    col = np.asarray(col, dtype=np.int64)
    if len(cols) == 0:
        return np.full(len(col), np.nan)
    j = np.clip(np.searchsorted(cols, col), 0, len(cols) - 1)
    out = arr[day, j]
    out = np.where(cols[j] == col, out, np.nan)
    return out


# ----------------------------------------------------------------------------- families

def _gap_in_break_fade(ctx, p):
    # break bar that opened already beyond the level and was sold (bought) inside the bar
    up, dn, hi, lo = _breaks(ctx, p["win_min"])
    pc = ctx.prev(ctx.c)
    short = up & _lt(ctx.c, ctx.o) & _gt(ctx.o, pc)
    long = dn & _gt(ctx.c, ctx.o) & _lt(ctx.o, pc)
    return _out(long, short)


def _neutral_day_break_fade(ctx, p):
    def f():
        nb = ctx.bars(p["ib_min"])
        d = _days(ctx)
        in_ib = ctx.bar_in_day < nb
        hh = pd.Series(np.where(in_ib, ctx.h, np.nan))
        ll = pd.Series(np.where(in_ib, ctx.l, np.nan))
        ib_h = hh.groupby(d).transform(lambda z: z.cummax().ffill()).to_numpy(float)
        ib_l = ll.groupby(d).transform(lambda z: z.cummin().ffill()).to_numpy(float)
        sh = ctx.session_high(include_current=True)
        sl = ctx.session_low(include_current=True)
        valid = ctx.bar_in_day >= nb
        return valid & _gt(sh, ib_h) & _lt(sl, ib_l)
    neutral = ctx.cached(("b038_neutral", p["ib_min"]), f)
    up, dn, _, _ = _breaks(ctx, p["win_min"])
    return _out(dn & neutral, up & neutral)


def _poc(ctx, bin_pts):
    def f():
        tp = (ctx.h + ctx.l + ctx.c) / 3.0
        tp = np.where(np.isfinite(tp), tp, 0.0)
        b = np.floor(tp / bin_pts).astype(np.int64)
        v = np.nan_to_num(ctx.v, nan=0.0)
        d = _days(ctx)
        out = np.full(ctx.n, np.nan)
        if ctx.n == 0:
            return out
        starts = np.r_[0, np.flatnonzero(np.diff(d)) + 1]
        ends = np.r_[starts[1:], ctx.n]
        for s, e in zip(starts, ends):
            u, inv = np.unique(b[s:e], return_inverse=True)
            m = np.zeros((e - s, len(u)))
            m[np.arange(e - s), inv] = v[s:e]
            idx = np.argmax(np.cumsum(m, axis=0), axis=1)
            out[s:e] = (u[idx] + 0.5) * bin_pts
        return out
    return ctx.cached(("b038_poc", bin_pts), f)


def _poc_stretch_fade(ctx, p):
    poc = _poc(ctx, p["bin"])
    typ = _typ_move(ctx, 30)
    dist = ctx.c - poc
    started = ctx.bar_in_day >= ctx.bars(60)
    long_c = _lt(dist, -p["k"] * typ) & _gt(ctx.c, ctx.prev(ctx.h))
    short_c = _gt(dist, p["k"] * typ) & _lt(ctx.c, ctx.prev(ctx.l))
    return _out(ctx.cross(long_c) & started, ctx.cross(short_c) & started)


def _break_fatigue_fade(ctx, p):
    up, dn, _, _ = _breaks(ctx, p["win_min"])
    n = ctx.bars(60)
    cu = ctx.roll(up.astype(float), n, "sum")
    cd = ctx.roll(dn.astype(float), n, "sum")
    short = up & _gt(cu, p["m"] - 0.5)
    long = dn & _gt(cd, p["m"] - 0.5)
    return _out(long, short)


def _lw_93(ctx, p):
    ema = ctx.ema(ctx.c, p["ema"])
    pe = ctx.prev(ema)
    rising = _gt(ema, pe)
    falling = _lt(ema, pe)
    c1, c2, c3 = ctx.prev(ctx.c, 1), ctx.prev(ctx.c, 2), ctx.prev(ctx.c, 3)
    set_l = _lt(c1, c3) & _lt(c2, c3) & _pb(ctx, rising)
    set_s = _gt(c1, c3) & _gt(c2, c3) & _pb(ctx, falling)
    long_c = set_l & rising & _gt(ctx.c, ctx.prev(ctx.h))
    short_c = set_s & falling & _lt(ctx.c, ctx.prev(ctx.l))
    return _out(ctx.cross(long_c), ctx.cross(short_c))


def _raschke_8020(ctx, p):
    f = p["f"]
    rng = ctx.h - ctx.l
    big = _gt(rng, p["k"] * _typ_range(ctx)) & _gt(rng, 0.0)
    bear = big & _gt(ctx.o - ctx.l, (1.0 - f) * rng) & _lt(ctx.c - ctx.l, f * rng)
    bull = big & _lt(ctx.o - ctx.l, f * rng) & _gt(ctx.c - ctx.l, (1.0 - f) * rng)
    pl, ph = ctx.prev(ctx.l), ctx.prev(ctx.h)
    long = _pb(ctx, bear) & _lt(ctx.l, pl) & _gt(ctx.c, pl)
    short = _pb(ctx, bull) & _gt(ctx.h, ph) & _lt(ctx.c, ph)
    return _out(long, short)


def _turtle_soup_plus_one(ctx, p):
    n = ctx.bars(p["lookback_min"])
    lo = ctx.roll(ctx.l, n, "min", include_current=False)
    hi = ctx.roll(ctx.h, n, "max", include_current=False)
    rlo = ctx.roll(ctx.l, 3, "min", include_current=False)
    rhi = ctx.roll(ctx.h, 3, "max", include_current=False)
    brk_dn = _lt(ctx.c, lo) & _gt(rlo, lo)        # close below a low made >= 4 bars ago
    brk_up = _gt(ctx.c, hi) & _lt(rhi, hi)
    long = _pb(ctx, brk_dn) & _gt(ctx.c, ctx.prev(lo))
    short = _pb(ctx, brk_up) & _lt(ctx.c, ctx.prev(hi))
    return _out(long, short)


def _two_day_value_conflict_fade(ctx, p):
    def f():
        vw = ctx.vwap()
        d = _days(ctx)
        per = pd.Series(np.asarray(vw, float)).groupby(d).last()
        per = per.reindex(range(int(d.max()) + 1)).shift(1)
        return per.to_numpy(float)[d]
    yvw = ctx.cached("b038_yvwap", f)
    vw = np.asarray(ctx.vwap(), float)
    lo = np.fmin(vw, yvw)
    hi = np.fmax(vw, yvw)
    gap = np.abs(vw - yvw)
    started = ctx.bar_in_day >= ctx.bars(30)
    conflict = started & _gt(ctx.c, lo) & _lt(ctx.c, hi) & _gt(gap, p["m"] * _typ_move(ctx, 30))
    up, dn, _, _ = _breaks(ctx, p["win_min"])
    return _out(dn & conflict, up & conflict)


def _hourly_stretch(ctx):
    def f():
        d = _days(ctx)
        hr = (np.asarray(ctx.minute) // 60).astype(np.int64)
        df = pd.DataFrame({"d": d, "hr": hr, "o": ctx.o, "h": ctx.h, "l": ctx.l})
        g = df.groupby(["d", "hr"], sort=True)
        hop = g["o"].transform("first").to_numpy(float)
        agg = g.agg(o=("o", "first"), h=("h", "max"), l=("l", "min"))
        st = np.minimum(agg["o"] - agg["l"], agg["h"] - agg["o"])
        tab = st.unstack("hr").reindex(range(int(d.max()) + 1)).sort_index(axis=1)
        avg = tab.rolling(20, min_periods=10).mean().shift(1)
        return hop, _lookup(avg, d, hr), hr
    return ctx.cached("b038_hstretch", f)


def _hourly_crabel_follow(ctx, p):
    hop, st, hr = _hourly_stretch(ctx)
    d = _days(ctx)
    lvl = p["m"] * st
    up = _gt(ctx.c, hop + lvl) & _gt(st, 0.0)
    dn = _lt(ctx.c, hop - lvl) & _gt(st, 0.0)
    key = pd.MultiIndex.from_arrays([d, hr])
    fu = pd.Series(up.astype(int)).groupby([d, hr]).cumsum().to_numpy() == 1
    fd = pd.Series(dn.astype(int)).groupby([d, hr]).cumsum().to_numpy() == 1
    del key
    return _out(up & fu, dn & fd)


def _half_hour_seasonality(ctx, p):
    def f():
        d = _days(ctx)
        blk = (np.asarray(ctx.minute) // 30).astype(np.int64)
        df = pd.DataFrame({"d": d, "b": blk, "o": ctx.o, "c": ctx.c})
        agg = df.groupby(["d", "b"], sort=True).agg(o=("o", "first"), c=("c", "last"))
        r = (agg["c"] - agg["o"]).unstack("b").reindex(range(int(d.max()) + 1)).sort_index(axis=1)
        n = p["n_sessions"]
        mp = max(5, n // 2)
        mu = r.rolling(n, min_periods=mp).mean().shift(1)
        sd = r.rolling(n, min_periods=mp).std(ddof=0).shift(1)
        nxt = ((np.asarray(ctx.minute) + ctx.tf) // 30).astype(np.int64)
        return _lookup(mu, d, nxt), _lookup(sd, d, nxt)
    mu, sd = ctx.cached(("b038_hks", p["n_sessions"]), f)
    last_bar = ((np.asarray(ctx.minute) + ctx.tf) % 30) == 0
    ok = last_bar & (np.nan_to_num(ctx.minutes_to_close, nan=0.0) > 30) & _gt(sd, 0.0)
    ratio = np.where(_gt(sd, 0.0), mu / np.where(_gt(sd, 0.0), sd, 1.0), np.nan)
    long = ok & _gt(ratio, p["th"])
    short = ok & _lt(ratio, -p["th"])
    return _out(long, short)


FAMILIES = [
    Family("E-378", "Gap-in break bar fade",
           "A short-term break that was printed by the bar's opening jump (the bar opened beyond the level, above the "
           "previous close) and then traded back against it inside the bar was made by a quote vacuum at the bar's open, "
           "not by buyers lifting offers: the buyers who chased the open are already under water within the bar and "
           "liquidity providers keep leaning on the gap, so fade the break (mirror for down-breaks).",
           {"win_min": [10, 15, 30]}, _gap_in_break_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-379", "Neutral-day micro-break fade",
           "Market Profile's neutral day: once the session has extended both above and below its initial balance, both "
           "the other-timeframe buyers and sellers have tried and been answered, so the day is traded responsively from "
           "both edges; a short-term break inside such a two-sided session has no initiator behind it and is faded "
           "(extension on BOTH sides, unlike the unextended or wide-IB interiors already screened).",
           {"ib_min": [30, 60], "win_min": [10, 15, 30]}, _neutral_day_break_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-380", "Developing-POC stretch fade",
           "Today's developing point of control is the price where most of today's contracts changed hands, i.e. the "
           "price both sides currently accept; after the first hour a move several typical half-hour moves away from it "
           "is carried by a thin crowd, and the first bar closing back beyond the previous bar's extreme starts the "
           "return toward the accepted price as responsive traders lean in (a stretch from today's POC, not VWAP or "
           "yesterday's POC).",
           {"bin": [50, 100, 200], "k": [1.0, 1.5, 2.0]}, _poc_stretch_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-381", "Repeated-break fatigue fade",
           "When the same side has already broken short-term highs several times within the last hour, each new break "
           "is bought mostly by late chasers while the early breakout buyers are taking profit into it and the stop pool "
           "above has been cleared repeatedly; the m-th same-side break inside an hour is therefore exhausted flow, so "
           "fade it on the break bar itself (mirror for lows).",
           {"win_min": [10, 15, 30], "m": [3, 4, 5]}, _break_fatigue_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-382", "Larry Williams setup 9.3 trigger",
           "Setup 9.3 (rising 9 EMA, two closes below a reference close, buy on the break of the last bar's high) is "
           "taught alongside 9.1/9.2 to Brazilian WIN day traders; the two-bar pullback traps short-term sellers whose "
           "stops sit just above, and the setup users' buy-stops at the same place fill together, so follow the trigger "
           "(mirror on a falling EMA).",
           {"ema": [9, 15, 21]}, _lw_93, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-383", "Raschke 80-20 reversal",
           "Raschke/Connors' 80-20: a large bar that opened in its top fifth and closed in its bottom fifth draws "
           "momentum sellers at its close; when the next bar trades below that bar's low and closes back above it, the "
           "sell-stops under the low have been run and found no follow-through, the late sellers are trapped, so buy "
           "the reclaim (mirror for a bar that opened low and closed high).",
           {"f": [0.2, 0.25, 0.3], "k": [0.75, 1.0, 1.5]}, _raschke_8020, markets=("WIN",),
           source="Eighty-Twenty setup (The Right Trader) https://therighttrader.com/learn/trading-strategies/eighty-twenty-setup",
           author="agent"),
    Family("E-384", "Turtle Soup Plus One",
           "Raschke's Turtle Soup Plus One on intraday bars: a close below a window low that was made at least four bars "
           "earlier triggers the breakout sellers and the stops of the old low's buyers; if the very next bar closes "
           "back above that old low, the break is a failed liquidity raid and the trapped breakout sellers cover, so "
           "buy the reclaim (mirror for highs); the one-bar wait and the old-level condition differ from fading the "
           "break bar itself.",
           {"lookback_min": [20, 30, 60]}, _turtle_soup_plus_one, markets=("WIN",),
           source="Turtle Soup (The Right Trader) https://therighttrader.com/learn/trading-strategies/turtle-soup",
           author="agent"),
    Family("E-385", "Two-day value conflict micro-break fade",
           "When price sits between today's session VWAP and yesterday's full-session VWAP while the two are clearly "
           "apart, the holders of today's inventory and of yesterday's inventory are on opposite sides of their cost and "
           "defend opposite edges; neither camp follows a short-term break inside that band and the other absorbs it, "
           "so fade breaks in the conflicted zone.",
           {"win_min": [10, 15, 30], "m": [0.5, 1.0, 2.0]}, _two_day_value_conflict_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-386", "Hourly Crabel stretch break follow",
           "Crabel's stretch (the average of the smaller of open-to-high and open-to-low) measures how far price "
           "normally wanders against the eventual direction from an open; applied to each clock hour with the same hour "
           "of the previous sessions, a first close beyond hour-open +/- m stretches means this hour has gone further "
           "than noise usually takes it, so a parent order is working that way; follow the first such close in the hour.",
           {"m": [1.0, 1.5, 2.0]}, _hourly_crabel_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-387", "Same-half-hour return seasonality follow",
           "Heston, Korajczyk and Sadka find returns persist at lags that are exact multiples of a trading day: the same "
           "half-hour keeps its sign across sessions because institutions rebalance and execute on fixed daily "
           "schedules; at the last bar before each half-hour, when that coming half-hour's mean return over the previous "
           "sessions is large relative to its dispersion, trade in its sign.",
           {"th": [0.1, 0.2, 0.3], "n_sessions": [10, 20]}, _half_hour_seasonality, markets=("WIN",),
           source="Intraday Patterns in the Cross-section of Stock Returns (Heston, Korajczyk, Sadka) https://arxiv.org/pdf/1005.3535.pdf",
           author="agent"),
]
