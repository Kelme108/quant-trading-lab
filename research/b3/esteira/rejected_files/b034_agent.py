"""Conveyor batch B-034 (agent, 2026-11-19). New state variables for WIN: steady-drift bursts, session net flow,
stale extremes, multi-day colour/volume/gap regimes, levels just short of the day extreme, jumpy tapes, the prior
clock hour's colour and a cross-session typical-dip buy."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


# ---------------------------------------------------------------------------------------------
# shared helpers (causal: every value at bar t uses bars <= t, or completed earlier sessions)
# ---------------------------------------------------------------------------------------------

def _breaks(ctx, nb):
    """(up, dn): the bar whose close first clears the previous nb bars' high / low."""
    def f():
        hi = ctx.roll(ctx.h, nb, "max", include_current=False)
        lo = ctx.roll(ctx.l, nb, "min", include_current=False)
        return ctx.cross(ctx.c > hi), ctx.cross(ctx.c < lo)
    return ctx.cached(("b034_breaks", nb), f)


def _n_days(ctx):
    return int(ctx.day.max()) + 1


def _per_day(ctx, x, how):
    """One value per session (index 0..n_days-1) of x aggregated with `how`."""
    s = pd.Series(np.asarray(x, float)).groupby(ctx.day).agg(how)
    return s.reindex(range(_n_days(ctx)))


# ---------------------------------------------------------------------------------------------
# E-338 drift-burst reversal
# ---------------------------------------------------------------------------------------------

def _drift_burst(ctx, p):
    n, th = ctx.bars(p["win_min"]), p["th"]
    r = ctx.c - ctx.prev(ctx.c, 1)
    m = ctx.roll(r, n, "mean")
    s = ctx.roll(r, n, "std")
    t = np.where(s > 0, m / np.where(s > 0, s, 1.0), 0.0) * np.sqrt(n)
    mv = ctx.c - ctx.prev(ctx.c, n)
    typ = ctx.cached(("b034_absmove", n), lambda: ctx.prev_sessions(np.abs(mv), "mean"))
    up = (t > th) & (mv > typ)
    dn = (t < -th) & (mv < -typ)
    return ctx.cross(dn).astype(int) - ctx.cross(up).astype(int)


# ---------------------------------------------------------------------------------------------
# E-339 session net-flow inventory micro-break fade
# ---------------------------------------------------------------------------------------------

def _netflow_fade(ctx, p):
    th = p["th"]
    up, dn = _breaks(ctx, ctx.bars(p["win_min"]))

    def share():
        sv = np.sign(ctx.c - ctx.o) * ctx.v
        cs = pd.Series(sv).groupby(ctx.day).cumsum().to_numpy()
        cv = pd.Series(ctx.v).groupby(ctx.day).cumsum().to_numpy()
        return cs / np.where(cv > 0, cv, np.nan)
    sh = ctx.cached("b034_netflow_share", share)
    ok = ctx.bar_in_day >= ctx.bars(30)
    short = up & ok & (sh > th)
    long = dn & ok & (sh < -th)
    return long.astype(int) - short.astype(int)


# ---------------------------------------------------------------------------------------------
# E-340 stale-extremes balance micro-break fade
# ---------------------------------------------------------------------------------------------

def _extreme_ages(ctx):
    def f():
        idx = np.arange(ctx.n)
        first = ctx.bar_in_day == 0
        sh, sl = ctx.session_high(False), ctx.session_low(False)
        new_hi = first | (ctx.h > sh)
        new_lo = first | (ctx.l < sl)
        last_hi = np.maximum.accumulate(np.where(new_hi, idx, -1))
        last_lo = np.maximum.accumulate(np.where(new_lo, idx, -1))
        return idx - last_hi, idx - last_lo
    return ctx.cached("b034_extreme_ages", f)


def _stale_extremes_fade(ctx, p):
    ns = ctx.bars(p["stale_min"])
    up, dn = _breaks(ctx, ctx.bars(p["win_min"]))
    age_hi, age_lo = _extreme_ages(ctx)
    stale = (age_hi >= ns) & (age_lo >= ns)
    return (dn & stale).astype(int) - (up & stale).astype(int)


# ---------------------------------------------------------------------------------------------
# E-341 session-colour streak micro-break fade
# ---------------------------------------------------------------------------------------------

def _colour_streak_fade(ctx, p):
    m = int(p["m"])
    up, dn = _breaks(ctx, ctx.bars(p["win_min"]))
    col = pd.Series(np.sign((_per_day(ctx, ctx.c, "last") - _per_day(ctx, ctx.o, "first")).to_numpy()))
    all_up = np.ones(len(col), dtype=bool)
    all_dn = np.ones(len(col), dtype=bool)
    for k in range(1, m + 1):
        lag = col.shift(k).to_numpy()
        all_up &= lag > 0
        all_dn &= lag < 0
    su, sd = all_up[ctx.day], all_dn[ctx.day]
    return (dn & sd).astype(int) - (up & su).astype(int)


# ---------------------------------------------------------------------------------------------
# E-342 just-below-the-day-extreme micro-break fade
# ---------------------------------------------------------------------------------------------

def _below_day_extreme_fade(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    up, dn = _breaks(ctx, nb)

    def typ():
        hi = ctx.roll(ctx.h, nb, "max", include_current=False)
        lo = ctx.roll(ctx.l, nb, "min", include_current=False)
        return ctx.prev_sessions(hi - lo, "mean")
    tr = ctx.cached(("b034_winrange", nb), typ)
    sh, sl = ctx.session_high(False), ctx.session_low(False)
    ok = ctx.bar_in_day >= nb
    short = up & ok & (sh > ctx.c) & (sh - ctx.c <= k * tr)
    long = dn & ok & (sl < ctx.c) & (ctx.c - sl <= k * tr)
    return long.astype(int) - short.astype(int)


# ---------------------------------------------------------------------------------------------
# E-343 fat-tailed-window micro-break fade
# ---------------------------------------------------------------------------------------------

def _fat_tail_fade(ctx, p):
    n, th = ctx.bars(p["win_min"]), p["th"]
    up, dn = _breaks(ctx, ctx.bars(15))
    r = ctx.c - ctx.prev(ctx.c, 1)
    m2 = ctx.roll(r ** 2, n, "mean")
    m4 = ctx.roll(r ** 4, n, "mean")
    kurt = np.where(m2 > 0, m4 / np.where(m2 > 0, m2, 1.0) ** 2, 0.0)
    jumpy = kurt > th
    return (dn & jumpy).astype(int) - (up & jumpy).astype(int)


# ---------------------------------------------------------------------------------------------
# E-344 day-after-heavy-volume micro-break fade
# ---------------------------------------------------------------------------------------------

def _after_heavy_volume_fade(ctx, p):
    k = p["k"]
    up, dn = _breaks(ctx, ctx.bars(p["win_min"]))
    tv = _per_day(ctx, ctx.v, "sum")
    base = tv.shift(2).rolling(15, min_periods=15).mean()
    ratio = (tv.shift(1) / base).to_numpy()
    heavy = (ratio >= k)[ctx.day]
    return (dn & heavy).astype(int) - (up & heavy).astype(int)


# ---------------------------------------------------------------------------------------------
# E-345 typical-worst-dip buy on a directional day
# ---------------------------------------------------------------------------------------------

def _typical_dip(ctx, p):
    f, k = p["f"], p["k"]
    sh, sl = ctx.session_high(True), ctx.session_low(True)
    dd, ru = sh - ctx.c, ctx.c - sl

    def refs():
        tdd = _per_day(ctx, dd, "max").shift(1).rolling(15, min_periods=15).mean().to_numpy()[ctx.day]
        tru = _per_day(ctx, ru, "max").shift(1).rolling(15, min_periods=15).mean().to_numpy()[ctx.day]
        return tdd, tru
    tdd, tru = ctx.cached("b034_typical_dd", refs)
    mv = ctx.c - ctx.day_open
    typ = ctx.cached("b034_absmove_open", lambda: ctx.same_minute(np.abs(mv), "mean"))
    long = (mv > k * typ) & (dd >= f * tdd)
    short = (mv < -k * typ) & (ru >= f * tru)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# ---------------------------------------------------------------------------------------------
# E-346 previous-clock-hour colour micro-break fade
# ---------------------------------------------------------------------------------------------

def _prev_hour_colour_fade(ctx, p):
    k = p["k"]
    up, dn = _breaks(ctx, ctx.bars(p["win_min"]))

    def frac():
        key = ctx.day.astype(np.int64) * 24 + (np.asarray(ctx.minute) // 60).astype(np.int64)
        g = pd.DataFrame({"key": key, "o": ctx.o, "h": ctx.h, "l": ctx.l, "c": ctx.c}).groupby("key")
        o1, c1 = g["o"].first(), g["c"].last()
        rng = g["h"].max() - g["l"].min()
        fr = ((c1 - o1) / rng.where(rng > 0)).to_dict()
        return pd.Series(key - 1).map(fr).to_numpy(float)
    fr = ctx.cached("b034_prev_hour_frac", frac)
    short = up & (fr <= -k)
    long = dn & (fr >= k)
    return long.astype(int) - short.astype(int)


# ---------------------------------------------------------------------------------------------
# E-347 incoherent-overnight-gap day micro-break fade
# ---------------------------------------------------------------------------------------------

def _incoherent_gap_fade(ctx, p):
    k = p["k"]
    up, dn = _breaks(ctx, ctx.bars(p["win_min"]))

    def gaps():
        g1 = _per_day(ctx, ctx.o, "first") - _per_day(ctx, ctx.c, "last").shift(1)
        w = ctx.other_close()
        g2 = _per_day(ctx, w, "first") - _per_day(ctx, w, "last").shift(1)
        t1 = g1.abs().shift(1).rolling(15, min_periods=15).mean()
        t2 = g2.abs().shift(1).rolling(15, min_periods=15).mean()
        return g1.to_numpy(), g2.to_numpy(), t1.to_numpy(), t2.to_numpy()
    g1, g2, t1, t2 = ctx.cached("b034_gaps", gaps)
    flag = (np.sign(g1) == np.sign(g2)) & (g1 != 0) & (np.abs(g1) >= k * t1) & (np.abs(g2) >= k * t2) \
        & np.isfinite(t1) & np.isfinite(t2)
    on = flag[ctx.day]
    return (dn & on).astype(int) - (up & on).astype(int)


SRC = "assistant reasoning"

FAMILIES = [
    Family("E-338", "Drift-burst reversal",
           "A move that is both larger than usual for its horizon and unusually steady (its bar returns have a high "
           "mean-to-dispersion t-statistic) is a drift burst: one impatient order is lifting through a book that "
           "liquidity providers keep refilling; once it stops, the providers holding the opposite inventory lean the "
           "price back, so fade the bar where the burst t-statistic first gets large.",
           {"win_min": [20, 30, 45], "th": [2.0, 2.5, 3.0]}, _drift_burst, markets=("WIN",),
           source="assistant reasoning (drift-burst idea of Christensen, Oomen and Reno)", author="agent"),
    Family("E-339", "Session net-flow inventory micro-break fade",
           "When most of today's volume so far traded on bars closing up, market makers have been selling all day "
           "and carry a large short inventory; a further short-term up-break is one more buyer they must fill, and "
           "they lean against it to unload, so fade breaks in the direction of a lopsided session net flow (mirror).",
           {"th": [0.05, 0.1, 0.2], "win_min": [10, 15, 30]}, _netflow_fade, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-340", "Stale-extremes balance micro-break fade",
           "When neither the session high nor the session low has been touched for a long time, the day's range is "
           "set and accepted and trading rotates inside it; a short-term break in that state reaches no stop pool "
           "and no new initiator, so the responsive side inside the range absorbs it; fade it.",
           {"stale_min": [30, 60, 90], "win_min": [10, 15, 30]}, _stale_extremes_fade, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-341", "Session-colour streak micro-break fade",
           "After several sessions in a row that each closed above their own open, the intraday buyers have been "
           "paid repeatedly and are fully positioned while day traders now expect the same colour; fresh up-breaks "
           "are their late adds that meet profit-taking, so fade breaks in the streak's direction (mirror).",
           {"m": [2, 3, 4], "win_min": [10, 15, 30]}, _colour_streak_fade, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-342", "Just-below-the-day-extreme micro-break fade",
           "A short-term break that stops just short of the session high runs straight into the offers and "
           "take-profits resting under the day's top, the most visible level of the day, without reaching the stops "
           "above it; the small breakers are capped there, so fade breaks that land within a short distance under "
           "the session extreme (mirror at the low).",
           {"k": [0.25, 0.5, 1.0], "win_min": [10, 15, 30]}, _below_day_extreme_fade, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-343", "Fat-tailed-window micro-break fade",
           "When the recent bar returns are strongly fat-tailed (high kurtosis), price is moving in a few jumps "
           "where quotes were pulled rather than by steady trade; a short-term break in that tape is usually one "
           "more liquidity gap that closes when quotes refill, so fade it.",
           {"win_min": [60, 90, 120], "th": [4, 6, 8]}, _fat_tail_fade, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-344", "Day-after-heavy-volume micro-break fade",
           "A session that traded far more contracts than usual completed a large transfer of positions "
           "(rebalancing, capitulation, an information event); the next day is digestion with the large parents "
           "already done, so its short-term breaks carry no initiator and responsive traders fade them.",
           {"k": [1.2, 1.5, 2.0], "win_min": [10, 15, 30]}, _after_heavy_volume_fade, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-345", "Typical-worst-dip buy on a directional day",
           "On a day trading above its open by more than usual for the minute, a pullback from the session high "
           "that reaches a set share of the typical worst pullback of recent sessions is where swing and day "
           "traders who know the market's usual dip size rest their buy orders; their size absorbs the profit-takers, "
           "so buy the dip (mirror for a rally on a down day).",
           {"f": [0.3, 0.5, 0.7], "k": [0.0, 0.5, 1.0]}, _typical_dip, markets=("WIN",), source=SRC, author="agent"),
    Family("E-346", "Previous-clock-hour colour micro-break fade",
           "A completed clock hour that closed decisively red tells hourly-chart desks that sellers own the hour; "
           "during the next hour, a short-term up-break is a counter-trend probe that those desks sell into, so fade "
           "breaks against the colour of the last completed hour (mirror after a green hour).",
           {"k": [0.2, 0.4, 0.6], "win_min": [10, 15, 30]}, _prev_hour_colour_fade, markets=("WIN",), source=SRC,
           author="agent"),
    Family("E-347", "Incoherent-overnight-gap day micro-break fade",
           "WIN and WDO normally gap in opposite directions because overnight foreign flow buys one and sells the "
           "other; when both gapped the same way, the overnight move was not foreign flow and gives the day no "
           "informed parent order to work, so local liquidity providers run the session and its short-term breaks "
           "are faded.",
           {"k": [0.0, 0.5, 1.0], "win_min": [10, 15, 30]}, _incoherent_gap_fade, markets=("WIN",), source=SRC,
           author="agent"),
]
