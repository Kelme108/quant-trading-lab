"""Conveyor batch B-033 (agent, 2026-11-19). New 'no initiator' regimes for fading short-term WIN breaks
(overnight tug of war, unextended initial balance, open inside prior value, open/VWAP conflict, seasonal book depth,
thin-book session), plus breaks judged by how they were approached and a cross-market level."""
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


def _avg_range(ctx):
    return ctx.cached("b033_avg_rng", lambda: ctx.prev_sessions(ctx.h - ctx.l, "mean"))


def _per_day(ctx, x, how):
    s = pd.Series(np.asarray(x, float)).groupby(ctx.day).agg(how)
    return s.reindex(range(int(ctx.day.max()) + 1))


def _ffill_day(ctx, x):
    return pd.Series(np.asarray(x, float)).groupby(ctx.day).ffill().to_numpy()


# ---------------------------------------------------------------------------------------------- families

def _tug_of_war(ctx, p):
    n, nb = int(p["n_sessions"]), ctx.bars(p["win_min"])
    op = _per_day(ctx, ctx.o, "first")
    cl = _per_day(ctx, ctx.c, "last")
    on = np.log(op / cl.shift(1))                              # today's overnight known at the open
    s = on.rolling(n, min_periods=n).sum().to_numpy()[ctx.day]
    up, dn = _breaks(ctx, nb)
    long = dn & (s < 0)
    short = up & (s > 0)
    return long.astype(int) - short.astype(int)


def _unextended_ib(ctx, p):
    nib, nb = ctx.bars(p["ib_min"]), ctx.bars(p["win_min"])
    first = ctx.bar_in_day < nib
    g = pd.DataFrame({"d": ctx.day, "h": np.where(first, ctx.h, np.nan), "l": np.where(first, ctx.l, np.nan)})
    ibh = g.groupby("d")["h"].transform("max").to_numpy()
    ibl = g.groupby("d")["l"].transform("min").to_numpy()
    done = ~first
    sh, sl = ctx.session_high(include_current=True), ctx.session_low(include_current=True)
    inside = done & (sh <= ibh) & (sl >= ibl)
    up, dn = _breaks(ctx, nb)
    return (dn & inside).astype(int) - (up & inside).astype(int)


def _rushed_approach(ctx, p):
    nb = ctx.bars(p["win_min"])
    mb = max(1, int(round(p["q"] * nb)))
    up, dn = _breaks(ctx, nb)
    lo_recent = ctx.roll(ctx.l, mb, "min")
    lo_win = ctx.roll(ctx.l, nb, "min")
    hi_recent = ctx.roll(ctx.h, mb, "max")
    hi_win = ctx.roll(ctx.h, nb, "max")
    short = up & (lo_recent <= lo_win)          # whole window crossed bottom to top within the last mb bars
    long = dn & (hi_recent >= hi_win)
    return long.astype(int) - short.astype(int)


def _open_vwap_conflict(ctx, p):
    nb, m = ctx.bars(p["win_min"]), p["m"]
    vw, op = ctx.vwap(), ctx.day_open
    conflict = ((ctx.c - op) * (ctx.c - vw) < 0) & (np.abs(vw - op) >= m * _avg_range(ctx))
    up, dn = _breaks(ctx, nb)
    return (dn & conflict).astype(int) - (up & conflict).astype(int)


def _open_in_prior_value(ctx, p):
    k, nb = p["k"], ctx.bars(p["win_min"])
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    V = _per_day(ctx, ctx.v, "sum")
    PV = _per_day(ctx, tp * ctx.v, "sum")
    P2 = _per_day(ctx, tp * tp * ctx.v, "sum")
    vw = PV / V
    sd = np.sqrt(np.maximum(P2 / V - vw * vw, 0.0))
    pvw = vw.shift(1).to_numpy()[ctx.day]
    psd = sd.shift(1).to_numpy()[ctx.day]
    in_value = (np.abs(ctx.day_open - pvw) <= k * psd) & (np.abs(ctx.c - pvw) <= k * psd)
    up, dn = _breaks(ctx, nb)
    return (dn & in_value).astype(int) - (up & in_value).astype(int)


def _opposite_push_conviction(ctx, p):
    nb, r = ctx.bars(p["win_min"]), p["ratio"]
    lo_prev = ctx.roll(ctx.l, nb, "min", include_current=False)
    hi_prev = ctx.roll(ctx.h, nb, "max", include_current=False)
    v_lo = np.full(ctx.n, np.nan)
    v_hi = np.full(ctx.n, np.nan)
    for j in range(nb, 0, -1):                  # the most recent bar that set the extreme wins
        lj, hj, vj = ctx.prev(ctx.l, j), ctx.prev(ctx.h, j), ctx.prev(ctx.v, j)
        v_lo = np.where(lj == lo_prev, vj, v_lo)
        v_hi = np.where(hj == hi_prev, vj, v_hi)
    up, dn = _breaks(ctx, nb)
    short = up & (ctx.v < r * v_lo)             # the push to the low carried more size than this break
    long = dn & (ctx.v < r * v_hi)
    return long.astype(int) - short.astype(int)


def _deep_minute(ctx, p):
    q, nb = p["q"], ctx.bars(p["win_min"])
    rng = ctx.h - ctx.l
    sv = ctx.cached("b033_sm_v", lambda: ctx.same_minute(ctx.v, "median"))
    sr = ctx.cached("b033_sm_r", lambda: ctx.same_minute(rng, "median"))
    dm = np.where(sr > 0, sv / np.where(sr > 0, sr, 1.0), np.nan)
    avg = ctx.cached("b033_avg_v", lambda: ctx.prev_sessions(ctx.v, "mean")) / _avg_range(ctx)
    deep = dm >= q * avg
    up, dn = _breaks(ctx, nb)
    return (dn & deep).astype(int) - (up & deep).astype(int)


def _decelerating_approach(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    t = max(1, nb // 3)
    m_rec = ctx.roll(ctx.c, t, "mean")
    m_mid = ctx.prev(m_rec, t)
    m_old = ctx.prev(m_rec, 2 * t)
    curv = m_rec - 2.0 * m_mid + m_old
    a = _avg_range(ctx)
    up, dn = _breaks(ctx, nb)
    short = up & (m_rec > m_old) & (curv < -k * a)
    long = dn & (m_rec < m_old) & (curv > k * a)
    return long.astype(int) - short.astype(int)


def _thin_session(ctx, p):
    q, nb = p["q"], ctx.bars(p["win_min"])
    cumv = pd.Series(ctx.v).groupby(ctx.day).cumsum().to_numpy()
    srng = ctx.session_high(include_current=True) - ctx.session_low(include_current=True)
    imp = np.where(cumv > 0, srng / np.where(cumv > 0, cumv, 1.0), np.nan)
    typ = ctx.cached("b033_sm_imp", lambda: ctx.same_minute(imp, "median"))
    thin = (imp >= q * typ) & (ctx.bar_in_day >= ctx.bars(30))
    up, dn = _breaks(ctx, nb)
    return (dn & thin).astype(int) - (up & thin).astype(int)


def _dollar_extreme_level(ctx, p):
    age_min = ctx.bars(p["min_age_min"])
    w = ctx.other_close()
    ws = pd.Series(w).groupby(ctx.day)
    wmax = _ffill_day(ctx, ws.cummax().to_numpy())
    wmin = _ffill_day(ctx, ws.cummin().to_numpy())
    new_hi = w > ctx.prev(wmax, 1)
    new_lo = w < ctx.prev(wmin, 1)
    bid = ctx.bar_in_day.astype(float)
    sig = np.zeros(ctx.n, dtype=int)
    pc = ctx.prev(ctx.c, 1)
    for upd in (new_hi, new_lo):
        L = _ffill_day(ctx, np.where(upd, ctx.c, np.nan))       # WIN price when the dollar set its extreme
        age = bid - _ffill_day(ctx, np.where(upd, bid, np.nan))
        old = age >= age_min
        long = old & (pc > L) & (ctx.l <= L) & (ctx.c > L)
        short = old & (pc < L) & (ctx.h >= L) & (ctx.c < L)
        sig = sig + ctx.cross(long).astype(int) - ctx.cross(short).astype(int)
    return np.clip(sig, -1, 1)


SRC_TUG = ("A Tug of War: Overnight Versus Intraday Expected Returns (Lou, Polk, Skouras) "
           "https://personal.lse.ac.uk/polk/research/TugOfWar.pdf")
SRC_DALTON = ("Mind Over Markets - Dalton (Volume Profile), opening types "
              "https://leveltrading.blogspot.com/2014/03/opening-types-pg267-open-drive-if.html")
SRC_IB = "Initial Balance https://www.luxalgo.com/library/concept/initial-balance/"

FAMILIES = [
    Family("E-328", "Overnight tug-of-war micro-break fade",
           "Lou/Polk/Skouras: overnight and intraday returns pull in opposite directions because individuals push "
           "prices overnight while institutions trade during the day against that flow. When the last few sessions' "
           "overnight returns sum clearly one way, intraday institutions lean against it, so short-term breaks in the "
           "overnight direction are faded (up-breaks sold after overnight gains, down-breaks bought after losses).",
           {"n_sessions": [3, 5, 10], "win_min": [10, 15, 30]}, _tug_of_war, markets=("WIN",),
           source=SRC_TUG, author="agent"),
    Family("E-329", "Unextended initial-balance micro-break fade",
           "Dalton: while the session has not yet extended beyond its initial balance (first 30-90 minutes), the "
           "opening institutions' range is holding and the day is still in balance, with responsive traders at both "
           "IB edges; short-term breaks inside the IB are small pushes they absorb, so fade them until the first "
           "range extension.",
           {"ib_min": [30, 60, 90], "win_min": [10, 15, 30]}, _unextended_ib, markets=("WIN",),
           source=SRC_IB, author="agent"),
    Family("E-330", "Rushed-approach micro-break fade",
           "A break of the window high reached by a traverse of the whole window from its low within a few bars is a "
           "burst of urgent market orders that emptied the book on the way up; the burst is the move and it arrives "
           "at the level spent, while the resting offers above remain, so the break reverts; fade it (mirror).",
           {"win_min": [15, 30, 60], "q": [0.2, 0.33, 0.5]}, _rushed_approach, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-331", "Open-VWAP conflict micro-break fade",
           "When price sits between the session open and a clearly separated session VWAP, the two most-watched "
           "intraday references give opposite verdicts: open-anchored day traders and VWAP-anchored desks take "
           "opposite sides, so neither camp follows a short-term break and the other absorbs it; fade breaks in "
           "that conflicted zone.",
           {"win_min": [10, 15, 30], "m": [1.0, 2.0, 4.0]}, _open_vwap_conflict, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-332", "Open-inside-prior-value micro-break fade",
           "Dalton: an open inside yesterday's value area that stays accepted there signals a balance day in which "
           "yesterday's extremes usually hold and responsive traders dominate; while the session opened and still "
           "trades inside yesterday's volume-weighted value band, short-term breaks lack an initiator and are faded.",
           {"k": [0.5, 1.0, 1.5], "win_min": [10, 15, 30]}, _open_in_prior_value, markets=("WIN",),
           source=SRC_DALTON, author="agent"),
    Family("E-333", "Opposite-push conviction fade",
           "Compare the size behind the two ends of the window: a close through the window high on a bar trading "
           "much less than the bar that set the window low means the down push had more conviction than the up "
           "break; the heavier participant is still on the other side and leans on the light breakers; fade (mirror).",
           {"win_min": [15, 30, 60], "ratio": [0.5, 0.75, 1.0]}, _opposite_push_conviction, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-334", "Seasonal deep-book minute micro-break fade",
           "At times of day when volume per point of range (20-session same-minute medians) is high next to the "
           "session average, the book is deep: many contracts trade for little price change because liquidity "
           "providers quote size; a short-term break at those minutes pushes into refilled depth and reverts.",
           {"q": [1.0, 1.25, 1.5], "win_min": [10, 15, 30]}, _deep_minute, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-335", "Decelerating-approach break fade",
           "If the window's closes rose but the latest third rose less than the one before (negative curvature), "
           "buying pressure is fading as price arrives at the high; the break is the last small push of a slowing "
           "move, the parent order behind the rise is finishing, and the late breakout buyers are the exit; fade "
           "(mirror for a decelerating fall).",
           {"win_min": [15, 30, 60], "k": [0.0, 0.5, 1.0]}, _decelerating_approach, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-336", "Thin-book session micro-break fade",
           "When today's range per contract traded so far is far above its usual value at this minute, the session's "
           "moves are being made by small orders through a thin book rather than by size; such impact-driven moves "
           "overshoot and liquidity providers who re-quote pull them back, so short-term breaks on such sessions "
           "are faded.",
           {"q": [1.25, 1.5, 2.0], "win_min": [10, 15, 30]}, _thin_session, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-337", "WIN price at the dollar's session extreme hold",
           "The WIN price printed when WDO set its latest session high (low) marks the index level at the peak of "
           "the day's risk-off (risk-on) flow, where foreign desks finished hedging; when WIN later returns to it and "
           "closes back on its side, those desks defend the level instead of adding, so trade away from it.",
           {"min_age_min": [10, 30, 60]}, _dollar_extreme_level, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
