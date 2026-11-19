"""Conveyor batch B-020 (agent, 2026-11-18). Mixed WIN themes: chart-type triggers (Renko), session flow sign,
multi-session cost level, index drift asymmetry, stalled extremes, retracement speed, block volatility breakout,
tweezer extremes, price-impact asymmetry and HH/HL staircases."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from b3.esteira import Family


def _typ_range(ctx):
    return ctx.cached("typ_bar_range_prev", lambda: ctx.prev_sessions(ctx.h - ctx.l, "mean"))


# E-198 ---------------------------------------------------------------------------------------
def _renko_reversal(ctx, p):
    k = float(p["k"])
    typ = _typ_range(ctx)
    c = ctx.c.tolist()
    day = ctx.day.tolist() if hasattr(ctx.day, "tolist") else list(ctx.day)
    tb = typ.tolist()
    out = np.zeros(ctx.n, dtype=int)
    hi = lo = 0.0
    d = 0
    for i in range(ctx.n):
        if i == 0 or day[i] != day[i - 1]:
            hi = lo = c[i]
            d = 0
            continue
        b = k * tb[i]
        if not (b > 0) or math.isnan(b):
            continue
        x = c[i]
        nd = d
        if d >= 0 and x >= hi + b:
            m = math.floor((x - hi) / b)
            hi += m * b
            lo = hi - b
            nd = 1
        elif d <= 0 and x <= lo - b:
            m = math.floor((lo - x) / b)
            lo -= m * b
            hi = lo + b
            nd = -1
        elif d == 1 and x <= lo - b:          # two bricks below the last top
            m = math.floor((lo - x) / b)
            lo -= m * b
            hi = lo + b
            nd = -1
        elif d == -1 and x >= hi + b:         # two bricks above the last bottom
            m = math.floor((x - hi) / b)
            hi += m * b
            lo = hi - b
            nd = 1
        if d != 0 and nd != d:
            out[i] = nd
        d = nd
    return out


# E-199 ---------------------------------------------------------------------------------------
def _session_flow_flip(ctx, p):
    nb = ctx.bars(p["away_min"])
    sv = np.sign(ctx.c - ctx.o) * ctx.v
    cum = ctx.cached("cum_signed_vol", lambda: pd.Series(sv).groupby(ctx.day).cumsum().to_numpy())
    vmed = ctx.cached("vol_med", lambda: ctx.same_minute(ctx.v, "median"))
    margin = p["margin"] * vmed
    was_neg = ctx.roll((cum < 0).astype(float), nb, "min", include_current=False) == 1
    was_pos = ctx.roll((cum > 0).astype(float), nb, "min", include_current=False) == 1
    up = was_neg & (cum > margin)
    dn = was_pos & (cum < -margin)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


# E-200 ---------------------------------------------------------------------------------------
def _multi_session_vwap_hold(ctx, p):
    ns, nb = int(p["sessions"]), ctx.bars(p["away_min"])

    def build():
        tp = (ctx.h + ctx.l + ctx.c) / 3.0
        df = pd.DataFrame({"d": ctx.day, "pv": tp * ctx.v, "v": ctx.v})
        per = df.groupby("d")[["pv", "v"]].sum().reindex(range(int(ctx.day.max()) + 1), fill_value=0.0)
        prior = per.rolling(ns, min_periods=ns).sum().shift(1)
        cpv = df.groupby("d")["pv"].cumsum().to_numpy()
        cv = df.groupby("d")["v"].cumsum().to_numpy()
        ppv = prior["pv"].to_numpy()[ctx.day]
        pvv = prior["v"].to_numpy()[ctx.day]
        with np.errstate(invalid="ignore", divide="ignore"):
            return (cpv + ppv) / (cv + pvv)

    mv = ctx.cached(("msvwap", ns), build)
    above = ctx.roll((ctx.c > mv).astype(float), nb, "min", include_current=False) == 1
    below = ctx.roll((ctx.c < mv).astype(float), nb, "min", include_current=False) == 1
    long = above & (ctx.l <= mv) & (ctx.c > mv)
    short = below & (ctx.h >= mv) & (ctx.c < mv)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-201 ---------------------------------------------------------------------------------------
def _long_only_dip(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    cond = ctx.c < lo
    return ctx.cross(cond).astype(int)


# E-202 ---------------------------------------------------------------------------------------
def _stalled_extreme_exit(ctx, p):
    nb, q = ctx.bars(p["hold_min"]), p["q"]
    sh, sl = ctx.session_high(include_current=True), ctx.session_low(include_current=True)
    rng = sh - sl
    typ = ctx.cached("sess_rng_med", lambda: ctx.same_minute(rng, "median"))
    wide = rng >= 0.75 * typ
    top = ctx.c >= sh - q * rng
    bot = ctx.c <= sl + q * rng
    sh1, sl1 = ctx.prev(sh, 1), ctx.prev(sl, 1)
    in_top = ctx.roll(top.astype(float), nb, "min", include_current=False) == 1
    in_bot = ctx.roll(bot.astype(float), nb, "min", include_current=False) == 1
    no_new_hi = (sh1 == ctx.prev(sh, nb)) & (ctx.h <= sh1)
    no_new_lo = (sl1 == ctx.prev(sl, nb)) & (ctx.l >= sl1)
    short = wide & in_top & no_new_hi & (ctx.c < sh - q * rng)
    long = wide & in_bot & no_new_lo & (ctx.c > sl + q * rng)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-203 ---------------------------------------------------------------------------------------
def _fast_deep_retrace(ctx, p):
    W, frac = ctx.bars(p["win_min"]), p["frac"]
    n = ctx.n
    out = np.zeros(n, dtype=int)
    if n < W + 1:
        return out
    hv = np.lib.stride_tricks.sliding_window_view(ctx.h, W)
    lv = np.lib.stride_tricks.sliding_window_view(ctx.l, W)
    t = np.arange(W - 1, n)
    ih = np.full(n, -1, dtype=np.int64)
    il = np.full(n, -1, dtype=np.int64)
    ih[W - 1:] = t - (W - 1) + np.argmax(hv, axis=1)
    il[W - 1:] = t - (W - 1) + np.argmin(lv, axis=1)
    hi = ctx.roll(ctx.h, W, "max")
    lo = ctx.roll(ctx.l, W, "min")
    leg = hi - lo
    big = leg >= math.sqrt(W) * _typ_range(ctx)
    idx = np.arange(n)
    valid = (ctx.bar_in_day >= W - 1) & big
    up_leg = valid & (ih > il)
    dn_leg = valid & (il > ih)
    s_up, d_up = idx - ih, ih - il
    s_dn, d_dn = idx - il, il - ih
    short = up_leg & (s_up >= 1) & (2 * s_up <= d_up) & (ctx.c <= hi - frac * leg)
    long = dn_leg & (s_dn >= 1) & (2 * s_dn <= d_dn) & (ctx.c >= lo + frac * leg)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-204 ---------------------------------------------------------------------------------------
def _block_vol_breakout(ctx, p):
    B, k = int(p["block_min"]), p["k"]

    def build():
        blk = (ctx.minute // B).astype(int)
        g = pd.DataFrame({"d": ctx.day, "b": blk, "o": ctx.o, "h": ctx.h, "l": ctx.l})
        bo = g.groupby(["d", "b"])["o"].transform("first").to_numpy()
        br = g.groupby(["d", "b"]).agg(hh=("h", "max"), ll=("l", "min"))
        br["r"] = br["hh"] - br["ll"]
        br["pr"] = br.groupby(level=0)["r"].shift(1)
        pr = br["pr"].reindex(pd.MultiIndex.from_arrays([np.asarray(ctx.day), blk])).to_numpy()
        return bo, pr

    bo, pr = ctx.cached(("block", B), build)
    ok = np.isfinite(pr) & (pr > 0)
    up = ok & (ctx.c > bo + k * pr)
    dn = ok & (ctx.c < bo - k * pr)
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


# E-205 ---------------------------------------------------------------------------------------
def _tweezer_extreme(ctx, p):
    nb = ctx.bars(p["lookback_min"])
    tol = np.maximum(p["tol"] * _typ_range(ctx), 5.0)
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    mid1 = (h1 + l1) / 2.0
    lo_prior = ctx.roll(ctx.l, nb, "min", include_current=False)
    hi_prior = ctx.roll(ctx.h, nb, "max", include_current=False)
    long = (l1 <= lo_prior) & (np.abs(ctx.l - l1) <= tol) & (ctx.c > ctx.o) & (ctx.c > mid1)
    short = (h1 >= hi_prior) & (np.abs(ctx.h - h1) <= tol) & (ctx.c < ctx.o) & (ctx.c < mid1)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-206 ---------------------------------------------------------------------------------------
def _impact_asymmetry(ctx, p):
    W, k = ctx.bars(p["win_min"]), p["k"]
    ret = ctx.c - ctx.o
    imp = np.abs(ret) / np.maximum(ctx.v, 1.0)
    up, dn = ret > 0, ret < 0
    s_up = ctx.roll(np.where(up, imp, 0.0), W, "sum")
    s_dn = ctx.roll(np.where(dn, imp, 0.0), W, "sum")
    n_up = ctx.roll(up.astype(float), W, "sum")
    n_dn = ctx.roll(dn.astype(float), W, "sum")
    with np.errstate(invalid="ignore", divide="ignore"):
        m_up = s_up / n_up
        m_dn = s_dn / n_dn
        ratio = m_up / m_dn
    enough = (n_up >= 3) & (n_dn >= 3) & (m_up > 0) & (m_dn > 0)
    mean = ctx.roll(ctx.c, W, "mean")
    long = enough & (ratio >= k) & (ctx.c > mean)
    short = enough & (ratio <= 1.0 / k) & (ctx.c < mean)
    return ctx.cross(long).astype(int) - ctx.cross(short).astype(int)


# E-207 ---------------------------------------------------------------------------------------
def _staircase(ctx, p):
    m = int(p["m"])
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    hh = (ctx.h > h1) & (ctx.l > l1)
    ll = (ctx.h < h1) & (ctx.l < l1)
    up = ctx.roll(hh.astype(float), m, "min") == 1
    dn = ctx.roll(ll.astype(float), m, "min") == 1
    return ctx.cross(up).astype(int) - ctx.cross(dn).astype(int)


FAMILIES = [
    Family("E-198", "Renko brick reversal follow",
           "Renko charts are a common chart type for Brazilian WIN day traders (Profit offers them by default), and "
           "they treat a two-brick reversal as the trigger to flip; their stop-and-reverse orders and the stops of "
           "the old-direction holders all fire on the same close, so the first bars after the reversal brick move "
           "with it; follow the reversal brick (brick = k x typical bar range of the last 20 sessions).",
           {"k": [2, 3, 4]}, _renko_reversal, markets=("WIN",),
           source="InfoMoney, 'Grafico de Renko reduz subjetividade e facilita leitura do trade, diz Junior Vianna' "
                  "https://www.infomoney.com.br/mercados/grafico-de-renko-reduz-subjetividade-facilita-leitura-do-trade-diz-junior-vianna/",
           author="agent"),
    Family("E-199", "Session signed-volume zero cross follow",
           "The running sum of today's volume signed by bar colour is the session's net aggressor balance; after it "
           "has been negative for a while, crossing to clearly positive means buyers have absorbed every contract "
           "the sellers pushed today and now own the day's net flow; parent orders behind a flow that large keep "
           "working, so follow the flip (mirror).",
           {"away_min": [15, 30, 60], "margin": [0.0, 1.0, 2.0]}, _session_flow_flip, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-200", "Multi-session VWAP touch hold",
           "The VWAP of the last few sessions plus today is the average cost of swing traders who hold WIN for "
           "days; after price has stayed on one side of it, the first touch that closes back on that side meets "
           "those holders defending their cost basis (adding, not exiting), so price moves away from the level.",
           {"sessions": [3, 5, 10], "away_min": [15, 30]}, _multi_session_vwap_hold, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-201", "Long-only short-term dip buy",
           "Short-horizon moves in an equity index are asymmetric: sell-offs are carried by stop and hedging flow "
           "that overshoots while short sellers cover quickly, and the index has a positive drift; buying the "
           "close that first breaks the recent low (and never shorting the mirror) takes the side of the "
           "overshooting forced seller in the direction of the drift.",
           {"lookback_min": [10, 20, 30, 60]}, _long_only_dip, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-202", "Stalled-extreme exit follow",
           "When price sits in the top part of the day's range for a while without printing a new session high, "
           "the buyers waiting for a breakout are long near the top with no progress; the first close out of that "
           "top zone shows the breakout will not come, and their exits plus the sellers who capped the high push "
           "price down; follow the exit (mirror at the low).",
           {"hold_min": [10, 20, 30], "q": [0.15, 0.2, 0.3]}, _stalled_extreme_exit, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-203", "Fast deep retracement follow",
           "A retracement that takes back a large share of the window's leg in less than half the time the leg "
           "took is not profit-taking: the counter side now trades with more urgency than the leg's side ever "
           "did and the leg's late buyers are under water at once; follow the retracement direction.",
           {"win_min": [30, 60, 90], "frac": [0.5, 0.6, 0.7]}, _fast_deep_retrace, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-204", "Block-open volatility breakout",
           "Larry Williams' volatility breakout applied to intraday blocks: a move from the block's open larger "
           "than a fraction of the previous block's range is more than the noise the last block showed, i.e. "
           "new directional flow; breakout users enter at the same level, so follow the first close beyond "
           "open +/- k x previous-block range.",
           {"block_min": [15, 30, 60], "k": [0.5, 0.75, 1.0]}, _block_vol_breakout, markets=("WIN",),
           source="WH SelfInvest, 'Trading strategy: Larry Williams Volatility Break-out' "
                  "https://whselfinvest.com/en-be/trading-platform/free-trading-strategies/tradingsystem/56-volatility-break-out-larry-williams-free",
           author="agent"),
    Family("E-205", "Tweezer extreme hold",
           "Two consecutive bars whose lows match within a tick or two at the window low show a resting buyer "
           "filling at that exact price twice; when the second bar closes up and above the first bar's midpoint, "
           "the sellers failed to clear that bid and their stops sit just under it, so trade the bounce "
           "(mirror at the high).",
           {"lookback_min": [15, 30, 60], "tol": [0.05, 0.1, 0.2]}, _tweezer_extreme, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-206", "Price-impact asymmetry follow",
           "When up bars move much more per contract traded than down bars, offers are thin (sellers have pulled "
           "their quotes) while bids absorb the selling; the path of least resistance is up because each buy "
           "moves price further than each sell, so follow the side with the higher per-contract impact once the "
           "asymmetry appears with price on that side of its window mean (mirror).",
           {"win_min": [20, 40, 60], "k": [1.5, 2.0, 3.0]}, _impact_asymmetry, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-207", "Higher-high higher-low staircase follow",
           "Several bars in a row each making both a higher high and a higher low is a clean staircase: trailing "
           "stops of longs ratchet under each low while the shorts' stops sit just over each high, so every new "
           "high fills buy-stops and no bar gives the shorts a chance to exit lower; follow the bar that completes "
           "the staircase (mirror).",
           {"m": [3, 4, 5]}, _staircase, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
