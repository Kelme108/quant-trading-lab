"""Conveyor batch B-009 (agent, 2026-11-18). Mixed WIN ideas: VWAP hold, volume confirmation, retail BR setups (Didi, 9.2, 123), Heikin-Ashi, range release, level magnet, activity onset, path efficiency."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _b(x):
    return np.asarray(x, dtype=bool)


def _vwap_touch_hold(ctx, p):
    nb = ctx.bars(p["away_min"])
    vw = ctx.vwap()
    above = (ctx.l > vw).astype(float)
    below = (ctx.h < vw).astype(float)
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    long = was_above & (ctx.l <= vw) & (ctx.c > vw)
    short = was_below & (ctx.h >= vw) & (ctx.c < vw)
    return long.astype(int) - short.astype(int)


def _vwma_sma_cross(ctx, p):
    n, k = ctx.bars(p["win_min"]), p["k"]
    vsum = ctx.roll(ctx.v, n, "sum")
    pv = ctx.roll(ctx.c * ctx.v, n, "sum")
    with np.errstate(invalid="ignore", divide="ignore"):
        vwma = np.where(vsum > 0, pv / vsum, np.nan)
    sma = ctx.roll(ctx.c, n, "mean")
    vpc = vwma - sma
    typ = ctx.cached(("vpc_typ", n), lambda: ctx.prev_sessions(np.abs(vpc), "mean"))
    long = ctx.cross((vpc > k * typ) & (ctx.c > sma))
    short = ctx.cross((vpc < -k * typ) & (ctx.c < sma))
    return long.astype(int) - short.astype(int)


def _heikin_ashi_flip(ctx, p):
    run = int(p["run"])
    hac = (ctx.o + ctx.h + ctx.l + ctx.c) / 4.0
    y = pd.Series(hac).groupby(ctx.day).transform(lambda z: z.ewm(alpha=0.5, adjust=False).mean()).to_numpy()
    hao = ctx.prev(y, 1)
    hao = np.where(np.isnan(hao), (ctx.o + ctx.c) / 2.0, hao)
    green = hac > hao
    red = hac < hao
    was_red = ctx.roll(red.astype(float), run, "min", include_current=False) == 1
    was_green = ctx.roll(green.astype(float), run, "min", include_current=False) == 1
    long = was_red & green
    short = was_green & red
    return long.astype(int) - short.astype(int)


def _didi_needle(ctx, p):
    s = p["scale"]
    n3, n8, n20 = max(2, int(round(3 * s))), int(round(8 * s)), int(round(20 * s))
    m3 = ctx.roll(ctx.c, n3, "mean")
    m8 = ctx.roll(ctx.c, n8, "mean")
    m20 = ctx.roll(ctx.c, n20, "mean")
    lo_m = np.minimum(np.minimum(m3, m8), m20)
    hi_m = np.maximum(np.maximum(m3, m8), m20)
    needle = (lo_m >= ctx.l) & (hi_m <= ctx.h)
    was_needle = ctx.prev(needle.astype(float), 1) == 1
    long = was_needle & (m3 > m8) & (m8 > m20) & (ctx.c > ctx.prev(ctx.h, 1))
    short = was_needle & (m3 < m8) & (m8 < m20) & (ctx.c < ctx.prev(ctx.l, 1))
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _narrow_streak_release(ctx, p):
    k, q = int(p["streak"]), p["q"]
    rng = ctx.h - ctx.l
    typ = ctx.cached("rng_med_sm", lambda: ctx.same_minute(rng, "median"))
    narrow = (rng < q * typ).astype(float)
    streak = ctx.roll(narrow, k, "min", include_current=False) == 1
    wide = (typ > 0) & (rng >= typ)
    mid = (ctx.h + ctx.l) / 2.0
    long = streak & wide & (ctx.c > ctx.o) & (ctx.c > mid)
    short = streak & wide & (ctx.c < ctx.o) & (ctx.c < mid)
    return long.astype(int) - short.astype(int)


def _setup_92(ctx, p):
    n = int(p["ema"])
    ema = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    pe = ctx.prev(ema, 1)
    rising = ema > pe
    falling = ema < pe
    sig_up = rising & (ctx.c < ctx.prev(ctx.l, 1))
    sig_dn = falling & (ctx.c > ctx.prev(ctx.h, 1))
    long = (ctx.prev(sig_up.astype(float), 1) == 1) & rising & (ctx.h > ctx.prev(ctx.h, 1))
    short = (ctx.prev(sig_dn.astype(float), 1) == 1) & falling & (ctx.l < ctx.prev(ctx.l, 1))
    return long.astype(int) - short.astype(int)


def _level_magnet(ctx, p):
    k = p["k"]
    nb = ctx.bars(15)
    mv = np.abs(ctx.c - ctx.prev(ctx.c, nb))
    typ = ctx.cached("abs15_prev", lambda: ctx.prev_sessions(mv, "mean"))
    d = k * typ
    ph, pl = ctx.prev_session_value("high"), ctx.prev_session_value("low")
    pc, po = ctx.prev_session_value("close"), ctx.prev_session_value("open")
    levels = [ph, pl, pc, po, (ph + pl) / 2.0]
    sh = ctx.session_high(include_current=True)
    sl = ctx.session_low(include_current=True)
    up = np.zeros(ctx.n, dtype=bool)
    dn = np.zeros(ctx.n, dtype=bool)
    for L in levels:
        up |= (L > sh) & (L - ctx.c <= d)
        dn |= (L < sl) & (ctx.c - L <= d)
    long = ctx.cross(up)
    short = ctx.cross(dn)
    return long.astype(int) - short.astype(int)


def _activity_onset(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    vs = ctx.roll(ctx.v, nb, "sum")
    typ = ctx.cached(("vsum_med", nb), lambda: ctx.same_minute(vs, "median"))
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = np.where(typ > 0, vs / typ, np.nan)
    mv = ctx.c - ctx.prev(ctx.c, nb)
    tm = ctx.cached(("absmv_prev", nb), lambda: ctx.prev_sessions(np.abs(mv), "mean"))
    on = ctx.cross(ratio > k)
    long = on & (mv > 0.5 * tm)
    short = on & (mv < -0.5 * tm)
    return long.astype(int) - short.astype(int)


def _path_efficiency(ctx, p):
    k = p["k"]

    def eff_fn():
        pc = ctx.prev(ctx.c, 1)
        step = np.where(np.isnan(pc), np.abs(ctx.c - ctx.o), np.abs(ctx.c - pc))
        path = pd.Series(step).groupby(ctx.day).cumsum().to_numpy()
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(path > 0, (ctx.c - ctx.day_open) / path, 0.0)

    eff = ctx.cached("sess_eff", eff_fn)
    typ = ctx.cached("sess_eff_typ", lambda: ctx.same_minute(np.abs(eff), "mean"))
    with np.errstate(invalid="ignore", divide="ignore"):
        z = np.where(typ > 0, eff / typ, np.nan)
    ok = ctx.bar_in_day >= ctx.bars(30)
    long = ctx.cross(ok & (z > k))
    short = ctx.cross(ok & (z < -k))
    return long.astype(int) - short.astype(int)


def _setup_123(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    lmin = ctx.roll(ctx.l, nb, "min")
    hmax = ctx.roll(ctx.h, nb, "max")
    l1, l2, l3 = ctx.prev(ctx.l, 1), ctx.prev(ctx.l, 2), ctx.prev(ctx.l, 3)
    h1, h2, h3 = ctx.prev(ctx.h, 1), ctx.prev(ctx.h, 2), ctx.prev(ctx.h, 3)
    bottom = (l2 < l3) & (l2 < l1) & (l2 <= ctx.prev(lmin, 2))
    top = (h2 > h3) & (h2 > h1) & (h2 >= ctx.prev(hmax, 2))
    long = bottom & (ctx.h > h1)
    short = top & (ctx.l < l1)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-079", "VWAP first-touch hold",
           "After price has traded entirely on one side of the session VWAP for a while, VWAP-benchmarked buyers "
           "(sellers) who missed the move rest orders at the day's average cost; the first bar that touches VWAP and "
           "closes back on the old side shows them absorbing the pullback sellers, so the move resumes away from VWAP "
           "(the hold, not the cross of E-001).",
           {"away_min": [15, 30, 60]}, _vwap_touch_hold, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-080", "VWMA-SMA volume confirmation cross",
           "Dormeier's VPC: when the volume-weighted mean of recent closes rises clearly above the plain mean, the "
           "heavy-volume bars are the higher-priced ones, i.e. size is paying up rather than drifting; with price above "
           "the mean, the side committing volume is the side of the trend, so follow the cross (mirror).",
           {"win_min": [10, 20, 40], "k": [0.25, 0.5, 1.0]}, _vwma_sma_cross, markets=("WIN",),
           source="Volume Price Confirmation Indicator (VPCI) concept, LuxAlgo https://www.luxalgo.com/library/concept/vpci/",
           author="agent"),
    Family("E-081", "Heikin-Ashi colour flip after a run",
           "Heikin-Ashi candles are a default chart type for many retail WIN traders, who hold while the candles stay "
           "one colour and reverse on the first opposite-colour candle; after a run of red HA candles the first green "
           "one triggers their covering and new longs together, and the shorts' stops sit just above, so follow it.",
           {"run": [3, 5, 8]}, _heikin_ashi_flip, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-082", "Agulhada do Didi",
           "Didi Aguiar's 'needle' (3, 8 and 20-bar averages all crossed by one candle, then fanning out in order) is "
           "one of the most watched Brazilian retail setups; it marks the end of a compression, and the many users "
           "buy when the next candle breaks the needle candle's high in the order 3>8>20, so follow the fan-out (mirror).",
           {"scale": [1.0, 1.5, 2.0]}, _didi_needle, markets=("WIN",),
           source="Agulhada do Didi ideas, TradingView https://br.tradingview.com/ideas/agulhadadodidi/", author="agent"),
    Family("E-083", "Narrow-range streak release",
           "Several consecutive bars with a range well below normal for their minute mean liquidity providers are "
           "quoting a balanced book with no initiative flow; the first bar of at least normal range that closes "
           "strongly in one direction is the first initiative order to clear that book, and the quotes pulled by "
           "the burst let it travel, so follow the release bar.",
           {"streak": [3, 4, 6], "q": [0.5, 0.6, 0.7]}, _narrow_streak_release, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-084", "Larry Williams setup 9.2 trigger",
           "Setup 9.2 (rising 9 EMA, a bar closing below the previous low, buy on the break of that bar's high) is "
           "taught to most Brazilian WIN day traders; their buy-stops cluster one tick above the pullback bar, so the "
           "trigger break fills them together while the pullback sellers' stops are at the same place; follow it (mirror).",
           {"ema": [7, 9, 12]}, _setup_92, markets=("WIN",),
           source="Setup 9.1, 9.2 e 9.3 de Larry Williams, Awake Trader https://www.awaketrader.com/pt/educacao/setup-9-1-9-2-9-3-larry-williams",
           author="agent"),
    Family("E-085", "Untested prior-session level magnet",
           "Stops and breakout orders accumulate just beyond yesterday's high, low, close, open and midpoint while "
           "they stay untouched today; when price comes within a typical 15-minute move of such a level, short-term "
           "traders run it toward that liquidity before it is touched, so follow the approach toward the level.",
           {"k": [0.5, 1.0, 1.5]}, _level_magnet, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-086", "Activity-regime onset follow",
           "When the volume of the last window first rises well above what that window normally trades at this time "
           "of day, a participant with an order to execute has arrived; such parent orders keep trading for longer "
           "than the window, so follow the window's price direction at the onset of the busy regime.",
           {"win_min": [15, 30, 60], "k": [1.25, 1.5, 2.0]}, _activity_onset, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-087", "Session path-efficiency trend follow",
           "The share of today's total price path that is net progress from the open measures how one-sided the day "
           "is; when it rises well above its usual value for the minute, the counter side is not rotating price back, "
           "which means a persistent informed or rebalancing flow, so follow the direction when efficiency jumps.",
           {"k": [1.0, 1.5, 2.0]}, _path_efficiency, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-088", "Setup 123 local-bottom trigger",
           "The '123' (middle of three candles makes the lowest low, here also the lowest of the window, entry on the "
           "break of the third candle's high) is a Stormer-popularised Brazilian setup; the clustered buy-stops of its "
           "users fill together at the trigger, and the sellers of the local low are trapped with stops above, so "
           "follow the trigger (mirror for tops).",
           {"lookback_min": [10, 20, 40]}, _setup_123, markets=("WIN",),
           source="Setup 123 Scalper script, TradingView https://www.tradingview.com/script/w8h6Oynm/", author="agent"),
]
