"""Conveyor batch B-041 (agent, 2026-11-21). Mixed themes: clock painting, prior-session levels and regimes, cross-market range mix, stalled breaks, afternoon anchors, dominant-volume side."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


# ----------------------------------------------------------------------------------------------- helpers

def _box(ctx, win_min):
    """Rolling box of the previous `win_min` minutes (excluding the current bar) and its first close-breaks."""
    def make():
        nb = ctx.bars(win_min)
        hi = ctx.roll(ctx.h, nb, "max", include_current=False)
        lo = ctx.roll(ctx.l, nb, "min", include_current=False)
        up = ctx.cross(ctx.c > hi)
        dn = ctx.cross(ctx.c < lo)
        return up, dn, hi, lo
    return ctx.cached(("b041_box", win_min), make)


def _per_day(ctx, values, agg):
    """Per-session aggregate as a pandas Series indexed 0..max(day)."""
    s = pd.Series(np.asarray(values, float)).groupby(ctx.day).agg(agg)
    return s.reindex(range(int(ctx.day.max()) + 1))


def _on_bars(ctx, per_day_series):
    return per_day_series.to_numpy()[ctx.day]


# ----------------------------------------------------------------------------------------------- families

def _five_min_paint_fade(ctx, p):
    # 1-minute bars only: the last minute of each 5-minute clock block closes through the recent box
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    last_min = (ctx.minute % 5) == 4
    return (dn & last_min).astype(int) - (up & last_min).astype(int)


def _yday_close_range_fade(ctx, p):
    tail = float(p["tail_min"])
    mask = ctx.minutes_to_close <= tail
    hi_d = _per_day(ctx, np.where(mask, ctx.h, np.nan), "max").shift(1)
    lo_d = _per_day(ctx, np.where(mask, ctx.l, np.nan), "min").shift(1)
    yh, yl = _on_bars(ctx, hi_d), _on_bars(ctx, lo_d)
    short = (ctx.h > yh) & (ctx.c < yh)
    long = (ctx.l < yl) & (ctx.c > yl)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _wide_cpr_fade(ctx, p):
    k = float(p["k"])
    H = _per_day(ctx, ctx.h, "max")
    L = _per_day(ctx, ctx.l, "min")
    C = _per_day(ctx, ctx.c, "last")
    pivot = (H + L + C) / 3.0
    bc = (H + L) / 2.0
    width = (2.0 * (pivot - bc).abs()) / C
    today = width.shift(1)                                   # yesterday's CPR width
    norm = width.shift(1).rolling(20, min_periods=20).mean()  # average of the 20 sessions before
    wide = _on_bars(ctx, today) >= k * _on_bars(ctx, norm)
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    return (dn & wide).astype(int) - (up & wide).astype(int)


def _equity_specific_follow(ctx, p):
    k = float(p["k"])
    sh = ctx.session_high(include_current=True)
    sl = ctx.session_low(include_current=True)
    win_r = (sh - sl) / sh
    w = pd.Series(ctx.other_close())
    g = w.groupby(ctx.day)
    wmax, wmin = g.cummax().to_numpy(), g.cummin().to_numpy()
    wdo_r = (wmax - wmin) / wmax
    ratio = np.where(wdo_r > 0, win_r / np.where(wdo_r > 0, wdo_r, 1.0), np.nan)
    typ = ctx.cached("b041_rng_ratio_typ", lambda: ctx.same_minute(ratio, "median"))
    hot = (ratio >= k * typ) & (ctx.bar_in_day >= ctx.bars(30))
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    return (up & hot).astype(int) - (dn & hot).astype(int)


def _stalled_break_fade(ctx, p):
    up, dn, hi, lo = _box(ctx, int(p["win_min"]))
    pu = ctx.prev(up.astype(float)) == 1
    pd_ = ctx.prev(dn.astype(float)) == 1
    h1, l1, c1 = ctx.prev(ctx.h), ctx.prev(ctx.l), ctx.prev(ctx.c)
    hi1, lo1 = ctx.prev(hi), ctx.prev(lo)
    short = pu & (ctx.h <= h1) & (ctx.c < c1) & (ctx.c >= hi1)   # no extension, weaker close, still outside
    long = pd_ & (ctx.l >= l1) & (ctx.c > c1) & (ctx.c <= lo1)
    return long.astype(int) - short.astype(int)


def _lunch_avwap_hold(ctx, p):
    anchor = int(p["anchor_min"])
    m = ctx.minute >= anchor
    tp = (ctx.h + ctx.l + ctx.c) / 3.0
    vol = np.maximum(ctx.v, 1.0)
    pv = pd.Series(np.where(m, tp * vol, 0.0)).groupby(ctx.day).cumsum().to_numpy()
    vv = pd.Series(np.where(m, vol, 0.0)).groupby(ctx.day).cumsum().to_numpy()
    av = np.where(vv > 0, pv / np.where(vv > 0, vv, 1.0), np.nan)
    active = ctx.minute >= anchor + 30
    c1, av1 = ctx.prev(ctx.c), ctx.prev(av)
    long = active & (c1 > av1) & (ctx.l <= av) & (ctx.c > av)
    short = active & (c1 < av1) & (ctx.h >= av) & (ctx.c < av)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _away_day_follow(ctx, p):
    th = float(p["th"])
    sh = ctx.session_high(include_current=True)
    sl = ctx.session_low(include_current=True)
    pdh, pdl = ctx.prev_session_value("high"), ctx.prev_session_value("low")
    rng = sh - sl
    ov = np.clip(np.minimum(sh, pdh) - np.maximum(sl, pdl), 0.0, None) / np.where(rng > 0, rng, np.nan)
    side = np.sign((sh + sl) / 2.0 - (pdh + pdl) / 2.0)
    away = (ov <= th) & (ctx.bar_in_day >= ctx.bars(60))
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    return (up & away & (side > 0)).astype(int) - (dn & away & (side < 0)).astype(int)


def _dominant_bar_side_follow(ctx, p):
    typ = ctx.cached("b041_vol_typ", lambda: ctx.same_minute(ctx.v, "median"))
    vr = np.nan_to_num(ctx.v / np.where(typ > 0, typ, np.nan), nan=0.0)
    rec = pd.Series(vr).groupby(ctx.day).cummax().to_numpy()
    is_rec = (vr >= rec) & (vr > 0)
    sg = np.where(is_rec, np.sign(ctx.c - ctx.o), np.nan)
    side = pd.Series(sg).groupby(ctx.day).ffill().to_numpy()
    side_prev = ctx.prev(side)                                   # record set at least one bar before
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    return (up & (side_prev > 0)).astype(int) - (dn & (side_prev < 0)).astype(int)


def _prev_hour_break_fade(ctx, p):
    hour = (ctx.minute // 60).astype(int)
    key = ctx.day.astype(np.int64) * 100 + hour
    hmax = pd.Series(ctx.h).groupby(key).max()
    hmin = pd.Series(ctx.l).groupby(key).min()
    pk = pd.Series(key - 1)
    ph = pk.map(hmax).to_numpy(float)
    pl = pk.map(hmin).to_numpy(float)
    rng = ph - pl
    typ = ctx.cached("b041_hour_rng_typ", lambda: ctx.prev_sessions(rng, "mean"))
    ok = rng <= float(p["k"]) * typ                              # previous hour not unusually wide
    up = ctx.cross(ctx.c > ph) & ok
    dn = ctx.cross(ctx.c < pl) & ok
    return dn.astype(int) - up.astype(int)


def _giveback_regime_fade(ctx, p):
    th = float(p["th"])
    H = _per_day(ctx, ctx.h, "max")
    L = _per_day(ctx, ctx.l, "min")
    C = _per_day(ctx, ctx.c, "last")
    cl = (C - L) / (H - L).where(H > L)
    avg = _on_bars(ctx, cl.rolling(5, min_periods=5).mean().shift(1))
    weak = avg <= 0.5 - th                                       # recent sessions keep closing near their lows
    strong = avg >= 0.5 + th
    up, dn, _, _ = _box(ctx, int(p["win_min"]))
    return (dn & strong).astype(int) - (up & weak).astype(int)


FAMILIES = [
    Family("E-408", "Five-minute candle-close painting fade",
           "Many WIN chart traders and bots read 5-minute candles, so the final minute of each 5-minute block is "
           "where short-term players push the price to paint a breakout close; a 1-minute close through the recent "
           "box printed exactly in that minute is cosmetic demand, not a build-up of orders, and liquidity providers "
           "take it back once the new block opens, so fade it.",
           {"win_min": [10, 15, 20]}, _five_min_paint_fade, timeframes=(1,), markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-409", "Yesterday's closing-hour range edge fade",
           "The high and low of yesterday's last trading window bound where the closing flows (index funds, "
           "day-trade flattening, settlement hedgers) were matched; those participants rest orders at the edges "
           "the next day, so a bar that pokes beyond either edge and closes back inside meets that resting "
           "inventory, and price rotates back into the closing range; fade the poke.",
           {"tail_min": [30, 60, 90]}, _yday_close_range_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-410", "Wide-CPR day micro-break fade",
           "The central pivot range (pivot vs. high-low midpoint from yesterday) is wide when yesterday closed far "
           "from its middle; pivot traders read a wide CPR as a sideways day and quote both sides; on such days "
           "short-term box breaks hit passive traders who expect rotation, so the break fades back into the box.",
           {"k": [0.75, 1.0, 1.25], "win_min": [15, 30]}, _wide_cpr_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-411", "Equity-specific day box-break follow",
           "When the index's range so far is large next to the dollar's range (compared with the usual ratio at "
           "this minute), the day's moves come from equity-specific information, not FX flow; informed equity "
           "orders are split and persistent, so a box break on such a day has informed flow behind it; follow it.",
           {"k": [1.25, 1.5, 2.0], "win_min": [15, 30]}, _equity_specific_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-412", "Stalled-break fade",
           "A close through the recent box followed at once by a bar that makes no further extreme and closes weaker, "
           "while still outside the box, shows the breakout buyers did not get any follow-through: the stops are "
           "used up and nobody new is paying up; the late breakout entrants exit before the box defenders even need "
           "to act, so fade the stall (before it fails back inside).",
           {"win_min": [10, 20, 30]}, _stalled_break_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-413", "Lunch-anchored VWAP touch hold",
           "The VWAP anchored at the B3 midday lull is the average cost of everyone who positioned for the "
           "afternoon (European close, US session flow); when price returns to it from one side and closes back "
           "on that side, that cohort defends its break-even, so trade away from the anchored level.",
           {"anchor_min": [660, 720, 780]}, _lunch_avwap_hold, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-414", "Away-from-yesterday day box-break follow",
           "When little of today's range overlaps yesterday's range, the market has left yesterday's value and is "
           "looking for new participants (initiative, not responsive, trade); box breaks in the direction away from "
           "yesterday are with the initiative side, whose orders keep arriving, so follow only those breaks.",
           {"th": [0.2, 0.35, 0.5], "win_min": [15, 30]}, _away_day_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-415", "Dominant-volume bar side box-break follow",
           "The bar with the most abnormal volume of the session so far (versus its time of day) marks where the "
           "day's largest participant acted, and its colour shows its side; that participant usually still has "
           "inventory to work, so box breaks in the same direction have it behind them; follow only those breaks.",
           {"win_min": [15, 30, 60]}, _dominant_bar_side_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-416", "Previous clock-hour extreme close-through fade",
           "The high and low of the hour that just finished are the stops and breakout alerts of hourly-candle "
           "traders; when that hour was not unusually wide, the first close beyond its extreme is mostly those "
           "mechanical orders firing together, after which the hour's range players lean against it; fade the close.",
           {"k": [1.0, 1.5, 2.0]}, _prev_hour_break_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-417", "Multi-day close-location giveback regime fade",
           "When the last five sessions mostly closed near their lows, rallies have been sold into every day by "
           "holders using strength to reduce; that supply is still there, so an upward box break is sold into "
           "again and fades (mirror when sessions keep closing near their highs and dips are bought).",
           {"th": [0.1, 0.15, 0.2], "win_min": [15, 30]}, _giveback_regime_fade, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
