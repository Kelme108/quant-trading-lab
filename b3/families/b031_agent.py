"""Conveyor batch B-031 (agent, 2026-11-19). Mixed themes on WIN: statistical stretch, range regime, bounce regime,
candle, prior-close inventory, absorption structure, open magnet, point-and-figure, stale tape, hourly anchored value."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


# ---------------------------------------------------------------------------------------------
# shared helpers (all causal: same-session rolling windows or the 20 sessions before)
# ---------------------------------------------------------------------------------------------

def _typ_range(ctx):
    return ctx.cached("b031_typ_rng", lambda: ctx.same_minute(ctx.h - ctx.l, "median"))


def _win_hi_lo(ctx, nb):
    hi = ctx.cached(("b031_hi", nb), lambda: ctx.roll(ctx.h, nb, "max", include_current=False))
    lo = ctx.cached(("b031_lo", nb), lambda: ctx.roll(ctx.l, nb, "min", include_current=False))
    return hi, lo


# E-308 -----------------------------------------------------------------------------------------
def _flat_channel_stretch(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    x = ctx.bar_in_day.astype(float)
    y = ctx.c - ctx.day_open
    sx = ctx.roll(x, nb, "sum")
    sy = ctx.roll(y, nb, "sum")
    sxx = ctx.roll(x * x, nb, "sum")
    sxy = ctx.roll(x * y, nb, "sum")
    syy = ctx.roll(y * y, nb, "sum")
    with np.errstate(invalid="ignore", divide="ignore"):
        den = nb * sxx - sx ** 2
        b = np.where(den > 0, (nb * sxy - sx * sy) / den, np.nan)
        a = (sy - b * sx) / nb
        fit = a + b * x
        sse = np.maximum(syy - a * sy - b * sxy, 0.0)
        sd = np.sqrt(sse / nb)
        flat = np.abs(b) * nb < 2.0 * sd
        long = flat & (sd > 0) & (y < fit - k * sd)
        short = flat & (sd > 0) & (y > fit + k * sd)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-309 -----------------------------------------------------------------------------------------
def _wide_box_break_fade(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    hi, lo = _win_hi_lo(ctx, nb)
    box = hi - lo
    typ = ctx.cached(("b031_box_typ", nb), lambda: ctx.same_minute(box, "median"))
    wide = box > k * typ
    long = ctx.cross(ctx.c < lo) & wide
    short = ctx.cross(ctx.c > hi) & wide
    return long.astype(int) - short.astype(int)


# E-310 -----------------------------------------------------------------------------------------
def _bounce_regime_bar_fade(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    r = ctx.c - ctx.prev(ctx.c, 1)
    r1 = ctx.prev(r, 1)
    num = ctx.roll(r * r1, nb, "mean")
    den = ctx.roll(r * r, nb, "mean")
    with np.errstate(invalid="ignore", divide="ignore"):
        ac = np.where(den > 0, num / den, np.nan)
    big = (ctx.h - ctx.l) >= k * _typ_range(ctx)
    bounce = ac < -0.1
    up = big & bounce & (ctx.c > ctx.o)
    dn = big & bounce & (ctx.c < ctx.o)
    return ctx.cross(dn).astype(int) - ctx.cross(up).astype(int)


# E-311 -----------------------------------------------------------------------------------------
def _harami_after_wide_fade(ctx, p):
    k, ratio = p["k"], p["ratio"]
    rng = ctx.h - ctx.l
    r1, t1 = ctx.prev(rng, 1), ctx.prev(_typ_range(ctx), 1)
    h1, l1, o1, c1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1), ctx.prev(ctx.o, 1), ctx.prev(ctx.c, 1)
    wide1 = r1 >= k * t1
    inside = (ctx.h <= h1) & (ctx.l >= l1) & (rng <= ratio * r1)
    short = wide1 & inside & (c1 > o1)
    long = wide1 & inside & (c1 < o1)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-312 -----------------------------------------------------------------------------------------
def _prior_close_imbalance_fade(ctx, p):
    th, nb = p["th"], ctx.bars(p["brk_min"])

    def imbalance():
        mtc = np.nan_to_num(ctx.minutes_to_close, nan=1e9)
        tail = mtc <= 30
        sv = np.where(tail, ctx.v * np.sign(ctx.c - ctx.o), 0.0)
        vv = np.where(tail, ctx.v, 0.0)
        per = pd.DataFrame({"d": ctx.day, "sv": sv, "v": vv}).groupby("d").sum()
        per = per.reindex(range(int(ctx.day.max()) + 1), fill_value=0.0)
        val = (per["sv"] / per["v"].where(per["v"] > 0)).shift(1)
        return val.to_numpy()[ctx.day]

    imb = ctx.cached("b031_close_imb", imbalance)
    early = ctx.bar_in_day < ctx.bars(180)
    hi, lo = _win_hi_lo(ctx, nb)
    short = early & (imb > th) & ctx.cross(ctx.c > hi)
    long = early & (imb < -th) & ctx.cross(ctx.c < lo)
    return long.astype(int) - short.astype(int)


# E-313 -----------------------------------------------------------------------------------------
def _red_bars_rising_lows(ctx, p):
    m = int(p["m"])
    pl, ph = ctx.prev(ctx.l, 1), ctx.prev(ctx.h, 1)
    absorb_buy = ((ctx.c < ctx.o) & (ctx.l > pl)).astype(float)     # red bar, yet a higher low
    absorb_sell = ((ctx.c > ctx.o) & (ctx.h < ph)).astype(float)    # green bar, yet a lower high
    long = ctx.roll(absorb_buy, m, "min") == 1
    short = ctx.roll(absorb_sell, m, "min") == 1
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-314 -----------------------------------------------------------------------------------------
def _flat_day_open_magnet(ctx, p):
    nb, m = ctx.bars(p["win_min"]), p["m"]
    dev = ctx.c - ctx.day_open
    typ = ctx.cached("b031_absdev_typ", lambda: ctx.same_minute(np.abs(dev), "mean"))
    flat_before = np.abs(ctx.prev(dev, nb)) <= 0.5 * ctx.prev(typ, nb)
    short = flat_before & (dev >= m * typ)
    long = flat_before & (dev <= -m * typ)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-315 -----------------------------------------------------------------------------------------
def _pnf_double_top(ctx, p):
    frac, rev = p["frac"], int(p["rev"])

    def run():
        box = frac * ctx.day_open
        with np.errstate(invalid="ignore", divide="ignore"):
            q = np.floor(ctx.c / box)
        q = q.tolist()
        d = ctx.day.tolist()
        out = np.zeros(ctx.n, dtype=np.int8)
        cur = None
        dirn, top, bot, ptop, pbot, fired = 0, 0.0, 0.0, None, None, False
        for i in range(ctx.n):
            qi = q[i]
            if d[i] != cur:
                cur = d[i]
                dirn, ptop, pbot, fired = 0, None, None, False
                top = bot = qi
                continue
            if qi != qi:        # NaN
                continue
            if dirn == 0:
                if qi > top:
                    dirn, top = 1, qi
                elif qi < bot:
                    dirn, bot = -1, qi
            elif dirn == 1:
                if qi > top:
                    top = qi
                elif qi <= top - rev:
                    ptop, dirn, bot, fired = top, -1, qi, False
            else:
                if qi < bot:
                    bot = qi
                elif qi >= bot + rev:
                    pbot, dirn, top, fired = bot, 1, qi, False
            if not fired:
                if dirn == 1 and ptop is not None and top > ptop:
                    out[i], fired = 1, True
                elif dirn == -1 and pbot is not None and bot < pbot:
                    out[i], fired = -1, True
        return out

    return ctx.cached(("b031_pnf", frac, rev), run).astype(int)


# E-316 -----------------------------------------------------------------------------------------
def _stale_tape_break_fade(ctx, p):
    nb, k = ctx.bars(p["win_min"]), p["k"]
    zero = (ctx.c == ctx.prev(ctx.c, 1)).astype(float)
    share = ctx.cached(("b031_zero_share", nb), lambda: ctx.roll(zero, nb, "mean"))
    norm = ctx.cached(("b031_zero_norm", nb), lambda: ctx.prev_sessions(share, "mean"))
    stale = (norm > 0) & (share > k * norm)
    hi, lo = _win_hi_lo(ctx, ctx.bars(15))
    long = ctx.cross(ctx.c < lo) & stale
    short = ctx.cross(ctx.c > hi) & stale
    return long.astype(int) - short.astype(int)


# E-317 -----------------------------------------------------------------------------------------
def _hour_vwap_stretch_fade(ctx, p):
    k, age = p["k"], p["min_age_min"]

    def bands():
        tp = (ctx.h + ctx.l + ctx.c) / 3.0
        vol = np.maximum(ctx.v, 1.0)
        block = ctx.day.astype(np.int64) * 100 + (ctx.minute // 60).astype(np.int64)
        df = pd.DataFrame({"b": block, "pv": tp * vol, "pv2": tp * tp * vol, "v": vol})
        g = df.groupby("b")
        cv = g["v"].cumsum().to_numpy()
        vw = g["pv"].cumsum().to_numpy() / cv
        var = g["pv2"].cumsum().to_numpy() / cv - vw ** 2
        return vw, np.sqrt(np.maximum(var, 0.0))

    vw, sd = ctx.cached("b031_hour_vwap", bands)
    old = (ctx.minute % 60) >= age
    short = old & (sd > 0) & (ctx.c > vw + k * sd)
    long = old & (sd > 0) & (ctx.c < vw - k * sd)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


FAMILIES = [
    Family("E-308", "Flat-channel regression stretch fade",
           "When the least-squares line through the last window's closes is nearly flat (its total rise is small next to "
           "the residual scatter), the market is a horizontal channel worked by liquidity providers; a close that "
           "stretches k residual sds off the line is a passing order the providers absorb, so fade back toward the line "
           "(no trend required, unlike the trend-dip of E-139).",
           {"win_min": [30, 60, 90], "k": [2.0, 2.5, 3.0]}, _flat_channel_stretch,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-309", "Wide-box micro-break fade",
           "If the last window's high-low box is already much wider than the same window usually is at this minute, the "
           "move inside it has spent the day traders' range; a further close beyond the box edge is a late chaser in an "
           "overextended window that the responsive side leans against, so fade it (window width regime, not the "
           "session-range schedule of E-267).",
           {"win_min": [15, 30, 60], "k": [1.5, 2.0, 2.5]}, _wide_box_break_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-310", "Bounce-regime big-bar fade",
           "When today's recent one-bar returns are clearly negatively autocorrelated (each move is partly undone on the "
           "next bar), price changes are dominated by inventory-managing liquidity providers (Roll's bid-ask bounce at a "
           "larger scale); a bar of unusually large range in that regime is a transient push they unwind, so fade its "
           "direction.",
           {"win_min": [30, 60, 90], "k": [1.5, 2.0, 2.5]}, _bounce_regime_bar_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-311", "Harami after a wide bar fade",
           "A wide bar followed at once by a small bar inside it means the wide bar's aggressor got no follow-through: "
           "the next participants traded only within its range and the chasers who entered at its close are not being "
           "rewarded; their exits push price back, so fade the wide bar's direction (the opposite of following an "
           "inside-bar break, E-005).",
           {"k": [1.5, 2.0, 2.5], "ratio": [0.4, 0.5, 0.6]}, _harami_after_wide_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-312", "Prior-close order-imbalance inventory fade",
           "A one-sided volume imbalance in the last 30 minutes of yesterday (volume on up bars against down bars) left "
           "market makers holding the opposite inventory overnight; they unload it during today's first hours as "
           "liquidity traders arrive, so rallies after a buy-imbalance close are sold and dips after a sell-imbalance "
           "close are bought: fade early micro-breaks in that direction (signed volume, not yesterday's price push of "
           "E-152).",
           {"th": [0.1, 0.2, 0.3], "brk_min": [10, 20, 30]}, _prior_close_imbalance_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-313", "Red bars, rising lows",
           "Several consecutive bars that close below their open yet each make a higher low show sellers hitting the bid "
           "into every bar's close while a passive buyer keeps raising the floor; the aggressive sellers are being "
           "absorbed without progress and the absorber wins, so buy (mirror: green bars with lower highs, sell).",
           {"m": [2, 3, 4]}, _red_bars_rising_lows,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-314", "Flat-day open-magnet stretch fade",
           "When the price was still near the session open a short while ago (the day has not chosen a side), a fast "
           "move to an unusually large distance from the open for this minute is a burst, not a trend: the open stays "
           "the day's reference for the two-sided participants, who fade it back toward the open.",
           {"win_min": [15, 30, 60], "m": [0.75, 1.0, 1.5]}, _flat_day_open_magnet,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-315", "Point-and-figure double-top break follow",
           "Point-and-figure chartists (Dorsey) buy when an X column rises above the previous X column's top and sell "
           "when an O column falls below the previous O column's bottom; their simultaneous orders and the stops of "
           "the counter side resting at those columns push the first boxes of the break, so follow it (one signal per "
           "column; boxes as a fraction of the session open).",
           {"frac": [0.0003, 0.0005, 0.0008], "rev": [2, 3]}, _pnf_double_top,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-316", "Stale-tape micro-break fade",
           "A high share of bars that close exactly at the previous close (Lesmond's zero-return measure) means the "
           "price is pinned by thick resting orders and few informed trades arrive; a 15-minute break in such a stale "
           "tape is a small order poking through a refilling book, so fade it.",
           {"win_min": [30, 60, 90], "k": [1.2, 1.5, 2.0]}, _stale_tape_break_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-317", "Clock-hour anchored VWAP stretch fade",
           "Execution algorithms restart their schedules at each clock hour and benchmark the hour's VWAP; a close far "
           "outside that hour's volume-weighted band (k volume-weighted sds) is an impatient order ahead of the "
           "schedule, and the hour's benchmark traders fill against it, pulling price back to the hour's value (an "
           "hourly anchor, not the session VWAP of P-016).",
           {"k": [1.5, 2.0, 2.5], "min_age_min": [15, 30]}, _hour_vwap_stretch_fade,
           markets=("WIN",), source="assistant reasoning", author="agent"),
]
