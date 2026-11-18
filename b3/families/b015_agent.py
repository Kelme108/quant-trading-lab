"""Conveyor batch B-015 (agent, 2026-11-18). Regime, sweep, volatility-shape, prior-session and hour-scale ideas on WIN."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from b3.esteira import Family


def _deep_book_break_fade(ctx, p):
    w, q = ctx.bars(p["win_min"]), p["q"]
    rs = ctx.roll(ctx.h - ctx.l, w, "sum")
    vs = ctx.roll(ctx.v, w, "sum")
    impact = rs / np.maximum(vs, 1.0)
    typ = ctx.cached(("impact_typ", w), lambda: ctx.prev_sessions(impact, "mean"))
    deep = impact < q * typ
    hi = ctx.roll(ctx.h, ctx.bars(5), "max", include_current=False)
    lo = ctx.roll(ctx.l, ctx.bars(5), "min", include_current=False)
    short = ctx.cross(ctx.c > hi) & deep
    long = ctx.cross(ctx.c < lo) & deep
    return long.astype(int) - short.astype(int)


def _double_sweep(ctx, p):
    w, m = ctx.bars(p["win_min"]), ctx.bars(p["within_min"])
    hi = ctx.roll(ctx.h, w, "max", include_current=False)
    lo = ctx.roll(ctx.l, w, "min", include_current=False)
    upb = (ctx.h > hi).astype(float)
    dnb = (ctx.l < lo).astype(float)
    rec_up = ctx.roll(upb, m, "max", include_current=False) == 1
    rec_dn = ctx.roll(dnb, m, "max", include_current=False) == 1
    short = ctx.cross(ctx.c < lo) & rec_up
    long = ctx.cross(ctx.c > hi) & rec_dn
    return long.astype(int) - short.astype(int)


def _vol_decay_retrace(ctx, p):
    k, qb = p["k"], ctx.bars(p["quiet_min"])
    s = ctx.bars(30)
    adc = np.abs(ctx.c - ctx.prev(ctx.c, 1))
    act = ctx.roll(adc, s, "sum")
    typ = ctx.cached(("act_typ", s), lambda: ctx.prev_sessions(act, "mean"))
    act_lag = ctx.prev(act, qb)
    move = ctx.prev(ctx.c, qb) - ctx.prev(ctx.c, qb + s)
    quiet_rate = ctx.roll(adc, qb, "mean")
    storm_rate = act_lag / s
    cond = (act_lag > k * typ) & (np.abs(move) > 0.5 * act_lag) & (quiet_rate < 0.5 * storm_rate)
    fire = ctx.cross(cond)
    return (fire & (move < 0)).astype(int) - (fire & (move > 0)).astype(int)


def _cc_range_ratio(ctx, p):
    w, k = ctx.bars(p["win_min"]), p["k"]
    lr = np.log(ctx.c / ctx.prev(ctx.c, 1))
    cc = ctx.roll(lr ** 2, w, "mean")
    hl = np.log(ctx.h / np.maximum(ctx.l, 1e-9))
    pk = ctx.roll(hl ** 2, w, "mean") / (4.0 * math.log(2.0))
    ratio = np.where(pk > 0, cc / np.where(pk > 0, pk, 1.0), np.nan)
    mv = ctx.c - ctx.prev(ctx.c, w)
    long = ctx.cross((ratio > k) & (mv > 0))
    short = ctx.cross((ratio > k) & (mv < 0))
    return long.astype(int) - short.astype(int)


def _closing_hour_reversal(ctx, p):
    k, nb = p["k"], ctx.bars(p["window_min"])
    nd = int(ctx.day.max()) + 1
    df = pd.DataFrame({"d": ctx.day, "c": ctx.c, "m": ctx.minutes_to_close})
    ref = df[df["m"] > 60].groupby("d")["c"].last()
    last = df.groupby("d")["c"].last()
    L = (last / ref - 1.0).reindex(range(nd))
    lprev = L.shift(1).to_numpy()[ctx.day]
    typ = L.abs().rolling(20, min_periods=20).mean().shift(1).to_numpy()[ctx.day]
    early = ctx.bar_in_day < nb
    up = lprev > k * typ
    dn = lprev < -k * typ
    short = early & up & ctx.cross(ctx.c < ctx.prev(ctx.l, 1))
    long = early & dn & ctx.cross(ctx.c > ctx.prev(ctx.h, 1))
    return long.astype(int) - short.astype(int)


def _prev_hour_overreaction(ctx, p):
    k, fm = p["k"], p["fade_min"]
    key = ctx.day.astype(np.int64) * 24 + (ctx.minute // 60).astype(np.int64)
    g = pd.DataFrame({"k": key, "o": ctx.o, "c": ctx.c}).groupby("k")
    ret = g["c"].last() / g["o"].first() - 1.0
    prevret = pd.Series(key - 1).map(ret).to_numpy(float)
    typ = ctx.cached("prev_hour_typ", lambda: ctx.prev_sessions(np.abs(prevret), "mean"))
    big = np.abs(prevret) > k * typ
    early = (ctx.minute % 60) < fm
    short = big & early & (prevret > 0) & ctx.cross(ctx.c < ctx.prev(ctx.l, 1))
    long = big & early & (prevret < 0) & ctx.cross(ctx.c > ctx.prev(ctx.h, 1))
    return long.astype(int) - short.astype(int)


def _reacceleration(ctx, p):
    w, k = ctx.bars(p["win_min"]), p["k"]
    t = max(1, w // 3)
    m = ctx.c - ctx.prev(ctx.c, w)
    typ = ctx.cached(("mom_typ", w), lambda: ctx.prev_sessions(np.abs(m), "mean"))
    s = ctx.c - ctx.prev(ctx.c, t)
    sp = ctx.prev(s, t)
    spp = ctx.prev(s, 2 * t)
    up = (m > k * typ) & (sp > 0) & (sp < spp) & (s > sp)
    dn = (m < -k * typ) & (sp < 0) & (sp > spp) & (s < sp)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


def _leverage_asymmetry(ctx, p):
    w, k = ctx.bars(p["win_min"]), p["k"]
    ret = ctx.c - ctx.prev(ctx.c, w)
    typ = ctx.cached(("ret_typ", w), lambda: ctx.prev_sessions(np.abs(ret), "mean"))
    adc = np.abs(ctx.c - ctx.prev(ctx.c, 1))
    vol_now = ctx.roll(adc, w, "mean")
    vol_before = ctx.prev(vol_now, w)
    short = (ret > typ) & (vol_now > k * vol_before)
    long = (ret < -typ) & (vol_now * k < vol_before)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _post_wide_day_fade(ctx, p):
    k, w = p["k"], ctx.bars(p["win_min"])
    nd = int(ctx.day.max()) + 1
    df = pd.DataFrame({"d": ctx.day, "h": ctx.h, "l": ctx.l})
    D = (df.groupby("d")["h"].max() - df.groupby("d")["l"].min()).reindex(range(nd))
    prev_d = D.shift(1).to_numpy()[ctx.day]
    avg = D.rolling(20, min_periods=20).mean().shift(1).to_numpy()[ctx.day]
    wide = prev_d > k * avg
    hi = ctx.roll(ctx.h, w, "max", include_current=False)
    lo = ctx.roll(ctx.l, w, "min", include_current=False)
    short = wide & ctx.cross(ctx.c > hi)
    long = wide & ctx.cross(ctx.c < lo)
    return long.astype(int) - short.astype(int)


def _squeeze_release(ctx, p):
    n, km = ctx.bars(p["win_min"]), p["kc_mult"]
    sd = ctx.roll(ctx.c, n, "std")
    atr = ctx.roll(ctx.h - ctx.l, n, "mean")
    mean = ctx.roll(ctx.c, n, "mean")
    valid = np.isfinite(sd) & np.isfinite(atr)
    on = valid & (2.0 * sd < km * atr)
    was_on = ctx.prev(on.astype(float), 1) == 1
    fire = valid & ~on & was_on
    return (fire & (ctx.c > mean)).astype(int) - (fire & (ctx.c < mean)).astype(int)


FAMILIES = [
    Family("E-148", "Deep-book micro-break fade",
           "When the last hour's price impact (range per contract traded) is well below its 20-session norm, the book is "
           "deep and liquidity providers absorb small pushes; a close beyond the last 5 minutes' high/low in such a "
           "regime is a small order moving through refilled quotes and reverts, so fade it.",
           {"win_min": [30, 60, 90], "q": [0.6, 0.8, 1.0]}, _deep_book_break_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-149", "Double-sided sweep, follow the second break",
           "A break of the recent high soon followed by a close below the recent low has run the stops on both sides; "
           "the first-side breakout buyers are now trapped and liquidating together with the fresh breakdown sellers, "
           "so the second break carries; follow it (mirror).",
           {"win_min": [10, 20, 30], "within_min": [10, 20, 30]}, _double_sweep, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-150", "Volatility-decay retracement after a storm",
           "A 30-minute burst of abnormal activity with a directional move, followed by a quiet stretch at half the "
           "storm's pace, means the forced flow is done and the market makers who took the other side now hold "
           "inventory they lean back on; once the calm sets in, trade against the storm's move.",
           {"k": [1.5, 2.0, 2.5], "quiet_min": [10, 15, 20]}, _vol_decay_retrace, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-151", "Close-to-close vs range variance ratio trend follow",
           "When close-to-close variance rises above the Parkinson range variance of the same bars, bars are closing "
           "near their extremes instead of rotating inside them: a one-sided order is lifting each bar's close; the "
           "crossing of that ratio marks persistent flow, so follow the window's direction.",
           {"win_min": [20, 30, 60], "k": [0.8, 1.0, 1.2]}, _cc_range_ratio, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-152", "Yesterday's closing-hour push reversal",
           "A last hour that moved much more than usual is closing-benchmark and rebalancing flow, not information; "
           "the inventory dealers took on at the close is unwound in the next morning, so in the first part of today's "
           "session trade counter bars against yesterday's closing-hour push.",
           {"k": [0.75, 1.0, 1.5], "window_min": [60, 90, 120]}, _closing_hour_reversal, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-153", "Previous clock-hour overreaction fade",
           "A completed clock hour that moved far more than a typical hour attracted hourly-chart chasers at its "
           "close; in the first minutes of the next hour the first bar closing beyond the previous bar against that "
           "hour shows the chasers are not being followed, and their exits revert the overreaction; fade the hour.",
           {"k": [1.0, 1.5, 2.0], "fade_min": [10, 20, 30]}, _prev_hour_overreaction, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-154", "Momentum re-acceleration follow",
           "In a move larger than usual for its horizon, a slowdown of the short-term speed WITHOUT a pullback that is "
           "followed by a renewed speed-up shows the parent order resumed after a pause rather than meeting supply; "
           "a re-accelerating move still has an active initiator, so follow it (mirror).",
           {"win_min": [30, 60, 90], "k": [0.5, 1.0, 1.5]}, _reacceleration, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-155", "Leverage-effect asymmetry fade",
           "In an equity index, volatility normally rises when price falls and fades when it rises; an up move with "
           "rising volatility is a short squeeze of forced buyers, and a down move with falling volatility is orderly "
           "selling with no fear behind it; both lack the usual participants, so fade them.",
           {"win_min": [15, 30, 60], "k": [1.25, 1.5, 2.0]}, _leverage_asymmetry, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-156", "Post-wide-day consolidation fade",
           "After a session whose range was much wider than the 20-session average, day traders cut size and dealers "
           "rebuild inventory; the next session tends to consolidate inside the shock, so short-term breaks of the "
           "recent high/low are not followed and are faded on that next day only.",
           {"k": [1.25, 1.5, 2.0], "win_min": [15, 30, 60]}, _post_wide_day_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-157", "Bollinger-inside-Keltner squeeze release",
           "When the close-based standard deviation band sits inside the range-based Keltner channel, closes are "
           "pinned while bars still trade (two-sided absorption); the first bar where the bands expand back out is "
           "when one side stops absorbing, and the many squeeze-indicator users enter with the momentum; follow the "
           "side of the close relative to the mean.",
           {"win_min": [20, 40, 60], "kc_mult": [1.0, 1.5, 2.0]}, _squeeze_release, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
