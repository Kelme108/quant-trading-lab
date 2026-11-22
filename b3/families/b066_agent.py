"""Conveyor batch B-066 (agent, 2026-11-22). Pivot levels, round numbers, clock-block structure, seasonal drift, volume dryness."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _sig(ctx, long, short):
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


def _prev_block(ctx, bm):
    """High, low, close of the previous COMPLETE clock block (bm minutes) of the same session."""
    def build():
        key = (ctx.minute // bm).astype(int)
        df = pd.DataFrame({"d": ctx.day, "k": key, "h": ctx.h, "l": ctx.l, "c": ctx.c})
        agg = df.groupby(["d", "k"], sort=False).agg(h=("h", "max"), l=("l", "min"), c=("c", "last")).reset_index()
        for col in ("h", "l", "c"):
            agg["p" + col] = agg.groupby("d")[col].shift(1)
        m = df[["d", "k"]].merge(agg[["d", "k", "ph", "pl", "pc"]], on=["d", "k"], how="left")
        return m["ph"].to_numpy(float), m["pl"].to_numpy(float), m["pc"].to_numpy(float)
    return ctx.cached(("pblock", bm), build)


def _pivot_reject(ctx, p):
    m = p["margin_frac"]
    hi, lo, cl = ctx.prev_session_value("high"), ctx.prev_session_value("low"), ctx.prev_session_value("close")
    pv = (hi + lo + cl) / 3.0
    if int(p["level"]) == 1:
        r, s = 2 * pv - lo, 2 * pv - hi
    else:
        r, s = pv + (hi - lo), pv - (hi - lo)
    short = (ctx.h >= r * (1 + m)) & (ctx.c < r)
    long = (ctx.l <= s * (1 - m)) & (ctx.c > s)
    return _sig(ctx, long, short)


def _round_reject(ctx, p):
    step, near = float(p["step"]), float(p["near"])
    up = np.ceil(ctx.c / step) * step
    dn = np.floor(ctx.c / step) * step
    short = (ctx.h >= up - near) & (ctx.c < up - near) & (ctx.c < up)
    long = (ctx.l <= dn + near) & (ctx.c > dn + near) & (ctx.c > dn)
    return _sig(ctx, long, short)


def _block_break(ctx, p):
    ph, pl, _ = _prev_block(ctx, int(p["block_min"]))
    with np.errstate(invalid="ignore"):
        long = ctx.c > ph
        short = ctx.c < pl
    return _sig(ctx, long, short)


def _hour_turn(ctx, p):
    nb, k = ctx.bars(p["lookback_min"]), p["k"]
    move = ctx.c / ctx.prev(ctx.c, nb) - 1.0
    typical = ctx.cached(("abs_move_h", nb), lambda: ctx.prev_sessions(np.abs(move), "mean"))
    first = (ctx.minute % 60) < ctx.tf
    with np.errstate(invalid="ignore"):
        long = first & (move >= k * typical)
        short = first & (move <= -k * typical)
    return long.astype(int) - short.astype(int)


def _seasonal_drift(ctx, p):
    thr = p["thr"]
    nb = ctx.bars(30)

    def build():
        s = pd.Series(ctx.c)
        fut = s.groupby(ctx.day).shift(-nb).to_numpy()
        fwd = fut / ctx.c - 1.0
        return ctx.same_minute(fwd, "mean"), ctx.same_minute(fwd, "median")
    mean, med = ctx.cached(("seasfwd", nb), build)
    with np.errstate(invalid="ignore"):
        long = (mean >= thr) & (med > 0)
        short = (mean <= -thr) & (med < 0)
    return _sig(ctx, long, short)


def _weak_volume_extreme(ctx, p):
    nb, k = ctx.bars(p["lookback_min"]), p["vol_k"]
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    med = ctx.cached("vol_med_b066", lambda: ctx.same_minute(ctx.v, "median"))
    weak = ctx.v < k * med
    with np.errstate(invalid="ignore"):
        short = weak & (ctx.h > hi)
        long = weak & (ctx.l < lo)
    return _sig(ctx, long, short)


def _range_exhaust(ctx, p):
    m = p["mult"]
    rng = ctx.prev_session_value("high") - ctx.prev_session_value("low")
    ext = (ctx.c - ctx.day_open) / rng
    with np.errstate(invalid="ignore"):
        short = (ext >= m) & (ctx.c < ctx.o)
        long = (ext <= -m) & (ctx.c > ctx.o)
    return _sig(ctx, long, short)


def _vwap_z_fade(ctx, p):
    k = p["z"]
    dev = ctx.c - ctx.vwap()
    sd = ctx.cached("devsd", lambda: pd.Series(dev).groupby(ctx.day).transform(
        lambda z: z.expanding(min_periods=30).std(ddof=0)).to_numpy())
    z = dev / np.where(sd > 0, sd, np.nan)
    with np.errstate(invalid="ignore"):
        short = z >= k
        long = z <= -k
    return _sig(ctx, long, short)


def _pd_mid_reclaim(ctx, p):
    nb = ctx.bars(p["away_min"])
    mid = (ctx.prev_session_value("high") + ctx.prev_session_value("low")) / 2.0
    below = (ctx.c < mid).astype(float)
    above = (ctx.c > mid).astype(float)
    was_below = ctx.roll(below, nb, "min", include_current=False) == 1
    was_above = ctx.roll(above, nb, "min", include_current=False) == 1
    up = was_below & (ctx.c > mid)
    dn = was_above & (ctx.c < mid)
    return up.astype(int) - dn.astype(int)


def _block_close_follow(ctx, p):
    bm, q = int(p["block_min"]), p["q"]
    ph, pl, pc = _prev_block(ctx, bm)
    rng = ph - pl
    loc = (pc - pl) / np.where(rng > 0, rng, np.nan)
    first = (ctx.minute % bm) < ctx.tf
    with np.errstate(invalid="ignore"):
        long = first & (loc >= 1 - q) & (ctx.c > ctx.o)
        short = first & (loc <= q) & (ctx.c < ctx.o)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-658", "Classic pivot R/S rejection",
           "Floor-trader pivot levels (R1/S1, R2/S2) from the previous session are watched by many desks; a poke "
           "through one that closes back inside means resting orders absorbed the push, so fade it.",
           {"level": [1, 2], "margin_frac": [0.0, 0.0005]}, _pivot_reject, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-659", "Round-number rejection",
           "Index round numbers (every 500/1000 points) hold clustered limit orders and option-strike hedging; a bar "
           "that reaches the next round level and closes back below it (or mirror) is rejected supply/demand.",
           {"step": [500, 1000], "near": [0, 50, 100]}, _round_reject, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-660", "Previous clock-block range break",
           "The range of the previous 15/30/60-minute clock block is a reference for desks that schedule by the clock; "
           "a close beyond it in the next block shows that block's balance being rejected; follow.",
           {"block_min": [15, 30, 60]}, _block_break, source="assistant reasoning", author="agent"),
    Family("E-661", "Hour-turn continuation",
           "Funds and execution algos rebalance at the top of the hour; when the move into the hour is larger than "
           "usual, the first bar of the new hour keeps the direction of that flow; follow.",
           {"lookback_min": [30, 60], "k": [0.5, 1.0, 1.5]}, _hour_turn, source="assistant reasoning", author="agent"),
    Family("E-662", "Same-minute seasonal drift",
           "If over the last 20 sessions the next 30 minutes from this clock minute drifted one way on average and in "
           "the median, recurring scheduled flow (opens, data, rebalancing) may repeat; trade that drift.",
           {"thr": [0.0002, 0.0004, 0.0006]}, _seasonal_drift, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-663", "Weak-volume new extreme fade",
           "A new window high/low printed on below-normal volume for the minute lacks participation; it is a "
           "liquidity poke, not acceptance, and tends to revert.",
           {"lookback_min": [30, 60], "vol_k": [0.5, 0.75, 1.0]}, _weak_volume_extreme, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-664", "Previous-range exhaustion reversal",
           "When the day has already travelled a set fraction of yesterday's whole range from the open, the typical "
           "daily range budget is spent; a bar closing against the move starts the give-back.",
           {"mult": [0.5, 0.75, 1.0]}, _range_exhaust, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-665", "VWAP deviation z-score fade",
           "Distance from VWAP scaled by its own session dispersion marks statistically stretched prices; "
           "market-order chasers overshoot and liquidity providers pull price back toward the day's fair value.",
           {"z": [1.5, 2.0, 2.5]}, _vwap_z_fade, markets=("WIN",), source="assistant reasoning", author="agent"),
    Family("E-666", "Previous-day midpoint reclaim",
           "The midpoint of yesterday's range is the balance point of the previous auction; after dwelling on one "
           "side, a close across it means the market re-accepts the other half; follow.",
           {"away_min": [10, 20, 30]}, _pd_mid_reclaim, source="assistant reasoning", author="agent"),
    Family("E-667", "Block close-location persistence",
           "A clock block that closes in the top (bottom) slice of its range leaves one side unfilled; when the "
           "next block opens with a bar in the same direction, the unfilled orders continue the move; follow.",
           {"block_min": [15, 30, 60], "q": [0.2, 0.3]}, _block_close_follow, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
