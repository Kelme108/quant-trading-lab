"""Conveyor batch B-010 (agent, 2026-11-18). Mixed ideas: candle indecision/harami, gap fill, regression channel, post-lunch box, DiNapoli RePo, initial-balance edge, Force Index, Ichimoku, Chaikin."""
from __future__ import annotations

import numpy as np
import pandas as pd

from b3.esteira import Family


def _typ_range(ctx):
    return ctx.cached("rng_med_sm", lambda: ctx.same_minute(ctx.h - ctx.l, "median"))


def _typ_move(ctx, nb):
    def fn():
        mv = np.abs(ctx.c - ctx.prev(ctx.c, nb))
        return ctx.prev_sessions(mv, "mean")
    return ctx.cached(("absmove_prev", nb), fn)


# E-089 -------------------------------------------------------------------------------------------
def _wide_doji_after_run(ctx, p):
    nb, k = ctx.bars(p["run_min"]), p["k"]
    rng = ctx.h - ctx.l
    trng = _typ_range(ctx)
    body = np.abs(ctx.c - ctx.o)
    doji = (trng > 0) & (rng >= trng) & (body <= 0.2 * rng)
    move = ctx.o - ctx.prev(ctx.c, nb)
    typ = _typ_move(ctx, nb)
    short = doji & (move > k * typ)
    long = doji & (move < -k * typ)
    return long.astype(int) - short.astype(int)


# E-090 -------------------------------------------------------------------------------------------
def _gap_fill_break(ctx, p):
    g, nb = p["gap_frac"], ctx.bars(p["window_min"])
    pc = ctx.prev_session_value("close")
    do = ctx.day_open
    gap_up = do > pc * (1 + g)
    gap_dn = do < pc * (1 - g)
    sl = ctx.session_low(include_current=False)
    sh = ctx.session_high(include_current=False)
    open_up = sl > pc            # gap up not filled yet
    open_dn = sh < pc
    lo = ctx.roll(ctx.l, nb, "min", include_current=False)
    hi = ctx.roll(ctx.h, nb, "max", include_current=False)
    short = ctx.cross(gap_up & open_up & (ctx.c < lo))
    long = ctx.cross(gap_dn & open_dn & (ctx.c > hi))
    return long.astype(int) - short.astype(int)


# E-091 -------------------------------------------------------------------------------------------
def _reg_channel_pullback(ctx, p):
    n, k = max(4, ctx.bars(p["win_min"])), p["k"]

    def fit():
        j = ctx.bar_in_day.astype(float)
        sy = ctx.roll(ctx.c, n, "sum")
        sjy = ctx.roll(j * ctx.c, n, "sum")
        j0 = j - (n - 1)
        sxy = sjy - j0 * sy
        xbar = (n - 1) / 2.0
        sxx = n * (n * n - 1) / 12.0
        b = (sxy - xbar * sy) / sxx
        end = sy / n + b * (n - 1 - xbar)
        var_y = ctx.roll(ctx.c, n, "std") ** 2
        res = np.maximum(var_y - b * b * sxx / n, 0.0)
        return b, end, np.sqrt(res)

    b, end, sd = ctx.cached(("regch", n), fit)
    bp, sdp = ctx.prev(b, 1), ctx.prev(sd, 1)
    centre = ctx.prev(end, 1) + bp
    up = (bp * (n - 1) > 2.0 * sdp) & (sdp > 0)
    dn = (-bp * (n - 1) > 2.0 * sdp) & (sdp > 0)
    lower, upper = centre - k * sdp, centre + k * sdp
    long = ctx.cross(up & (ctx.l <= lower) & (ctx.c > lower))
    short = ctx.cross(dn & (ctx.h >= upper) & (ctx.c < upper))
    return long.astype(int) - short.astype(int)


# E-092 -------------------------------------------------------------------------------------------
def _post_lunch_box_break(ctx, p):
    end, until = int(p["box_end"]), int(p["until_min"])
    start = 12 * 60
    inbox = (ctx.minute >= start) & (ctx.minute + ctx.tf <= end)
    g = pd.DataFrame({"d": ctx.day, "h": np.where(inbox, ctx.h, np.nan), "l": np.where(inbox, ctx.l, np.nan)})
    bh = g.groupby("d")["h"].transform("max").to_numpy()
    bl = g.groupby("d")["l"].transform("min").to_numpy()
    after = (ctx.minute >= end) & (ctx.minute < end + until)
    long = ctx.cross(after & (ctx.c > bh))
    short = ctx.cross(after & (ctx.c < bl))
    return long.astype(int) - short.astype(int)


# E-093 -------------------------------------------------------------------------------------------
def _harami_after_large_bar(ctx, p):
    k, ratio = p["k"], p["ratio"]
    rng = ctx.h - ctx.l
    trng = _typ_range(ctx)
    h1, l1, o1, c1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1), ctx.prev(ctx.o, 1), ctx.prev(ctx.c, 1)
    r1, t1 = h1 - l1, ctx.prev(trng, 1)
    big = (t1 > 0) & (r1 >= k * t1) & (np.abs(c1 - o1) >= 0.6 * r1)
    inside = (ctx.h <= h1) & (ctx.l >= l1) & (rng <= ratio * r1)
    short = big & (c1 > o1) & inside & (ctx.c < ctx.o)
    long = big & (c1 < o1) & inside & (ctx.c > ctx.o)
    return long.astype(int) - short.astype(int)


# E-094 -------------------------------------------------------------------------------------------
def _run_length(ctx, cond):
    s = pd.Series(np.asarray(cond, bool).astype(int))
    brk = (~np.asarray(cond, bool)) | (ctx.bar_in_day == 0)
    block = np.cumsum(brk)
    return s.groupby(block).cumsum().to_numpy()


def _double_repo(ctx, p):
    thrust, m = int(p["thrust"]), int(p["window"])
    dma = ctx.prev(ctx.roll(ctx.c, 3, "mean"), 3)          # 3x3 displaced moving average
    above = ctx.c > dma
    below = ctx.c < dma
    run_a = _run_length(ctx, above)
    run_b = _run_length(ctx, below)
    x_dn = (ctx.prev(above.astype(float), 1) == 1) & below
    x_up = (ctx.prev(below.astype(float), 1) == 1) & above
    first_dn = x_dn & (ctx.prev(run_a, 1) >= thrust)        # first penetration after an up-thrust
    first_up = x_up & (ctx.prev(run_b, 1) >= thrust)
    had_dn = ctx.roll(first_dn.astype(float), m, "max", include_current=False) == 1
    had_up = ctx.roll(first_up.astype(float), m, "max", include_current=False) == 1
    short = x_dn & had_dn & ~first_dn
    long = x_up & had_up & ~first_up
    return long.astype(int) - short.astype(int)


# E-095 -------------------------------------------------------------------------------------------
def _ib_edge_reject(ctx, p):
    nb, k = ctx.bars(p["ib_min"]), p["k"]
    first = ctx.bar_in_day < nb
    g = pd.DataFrame({"d": ctx.day, "h": np.where(first, ctx.h, np.nan), "l": np.where(first, ctx.l, np.nan)})
    ibh = g.groupby("d")["h"].transform("max").to_numpy()
    ibl = g.groupby("d")["l"].transform("min").to_numpy()
    done = ~first
    d = k * _typ_range(ctx)
    sh = ctx.session_high(include_current=True)
    sl = ctx.session_low(include_current=True)
    mid = (ctx.h + ctx.l) / 2.0
    h1, l1 = ctx.prev(ctx.h, 1), ctx.prev(ctx.l, 1)
    short = done & (sh <= ibh) & (ctx.h >= ibh - d) & (h1 < ibh - d) & (ctx.c < mid)
    long = done & (sl >= ibl) & (ctx.l <= ibl + d) & (l1 > ibl + d) & (ctx.c > mid)
    return long.astype(int) - short.astype(int)


# E-096 -------------------------------------------------------------------------------------------
def _force_index_pullback(ctx, p):
    n, k = ctx.bars(p["trend_min"]), p["k"]

    def fi_fn():
        dc = ctx.c - ctx.prev(ctx.c, 1)
        dc = np.where(np.isnan(dc), 0.0, dc)
        return ctx.ema(dc * ctx.v, 2)

    fi = ctx.cached("force2", fi_fn)
    typ = ctx.cached("force2_typ", lambda: ctx.prev_sessions(np.abs(fi), "mean"))
    em = ctx.cached(("ema", n), lambda: ctx.ema(ctx.c, n))
    sl = ctx.bars(10)
    up = (ctx.c > em) & (em > ctx.prev(em, sl))
    dn = (ctx.c < em) & (em < ctx.prev(em, sl))
    long = ctx.cross(up & (fi < -k * typ))
    short = ctx.cross(dn & (fi > k * typ))
    return long.astype(int) - short.astype(int)


# E-097 -------------------------------------------------------------------------------------------
def _ichimoku_tk(ctx, p):
    s = p["scale"]
    nt, nk = int(round(9 * s)), int(round(26 * s))
    ten = (ctx.roll(ctx.h, nt, "max") + ctx.roll(ctx.l, nt, "min")) / 2.0
    kij = (ctx.roll(ctx.h, nk, "max") + ctx.roll(ctx.l, nk, "min")) / 2.0
    chik = ctx.prev(ctx.c, nk)
    long = ctx.cross((ten > kij) & (ctx.c > kij) & (ctx.c > chik))
    short = ctx.cross((ten < kij) & (ctx.c < kij) & (ctx.c < chik))
    return long.astype(int) - short.astype(int)


# E-098 -------------------------------------------------------------------------------------------
def _chaikin_cross(ctx, p):
    s, k = p["scale"], p["k"]
    nf, ns = max(2, int(round(3 * s))), int(round(10 * s))

    def ad_fn():
        rng = ctx.h - ctx.l
        with np.errstate(invalid="ignore", divide="ignore"):
            clv = np.where(rng > 0, ((ctx.c - ctx.l) - (ctx.h - ctx.c)) / rng, 0.0)
        return pd.Series(clv * ctx.v).groupby(ctx.day).cumsum().to_numpy()

    ad = ctx.cached("ad_line", ad_fn)
    osc = ctx.ema(ad, nf) - ctx.ema(ad, ns)
    typ = ctx.cached(("chaikin_typ", nf, ns), lambda: ctx.prev_sessions(np.abs(osc), "mean"))
    long = ctx.cross(osc > k * typ)
    short = ctx.cross(osc < -k * typ)
    return long.astype(int) - short.astype(int)


FAMILIES = [
    Family("E-089", "Wide doji after a run",
           "After a move larger than usual, a bar of at least typical range that closes almost where it opened shows "
           "the move's aggressors met a counter side able to absorb a full bar of two-way trade; the trend side has "
           "stopped making progress while late chasers are long at the top of the doji, so fade the run at the doji's close.",
           {"run_min": [10, 20, 30], "k": [1.0, 1.5, 2.0]}, _wide_doji_after_run, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-090", "Unfilled-gap fill break",
           "An overnight gap leaves the prior close as an obvious untraded target: gap-fill traders and dealers who "
           "marked inventory at yesterday's close lean against the gap; while the gap is still open, a close through "
           "the recent short-term low (gap up) shows the gap side losing control, so follow it toward the prior close.",
           {"gap_frac": [0.001, 0.002, 0.004], "window_min": [10, 20, 30]}, _gap_fill_break,
           source="assistant reasoning", author="agent"),
    Family("E-091", "Regression-channel edge pullback with the slope",
           "Inside a clearly sloped least-squares channel of recent closes, a bar that reaches the lower edge (k "
           "residual sd below the extrapolated line) in an up-channel and closes back inside is a pullback that "
           "trend-line traders buy and that has not broken the trend's statistical path; trade back toward the line (mirror).",
           {"win_min": [30, 60, 120], "k": [1.5, 2.0, 2.5]}, _reg_channel_pullback, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-092", "Post-lunch box break",
           "From 12:00 the B3 lunch lull builds a range set by small local orders; when desks and US-session flow "
           "return after it, the first closes beyond the lunch box show where returning size is going, and the stops "
           "of lunch range traders sit just outside it, so follow the break in the window after the box.",
           {"box_end": [810, 840, 870], "until_min": [60, 120, 180]}, _post_lunch_box_break, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-093", "Harami after a large bar",
           "A large full-body bar followed at once by a small opposite-colour bar inside it means the burst's "
           "aggressors got no follow-through: the next bar's whole trade happened inside the burst while the other "
           "side closed it lower; those who chased the large bar's close are trapped, so trade the harami's direction.",
           {"k": [1.5, 2.0, 2.5], "ratio": [0.3, 0.5, 0.7]}, _harami_after_large_bar, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-094", "DiNapoli Double RePo after a thrust",
           "After a thrust of many closes on one side of the 3x3 displaced average, DiNapoli's Double RePo (close "
           "through the 3x3, close back, close through again within a few bars) shows the thrust's side failed twice "
           "to resume; its holders give up on the second penetration, so trade the reversal.",
           {"thrust": [5, 8, 12], "window": [5, 8, 12]}, _double_repo, markets=("WIN",),
           source="Education on Double RePo on 15min chart in EUR/USD past week (TradingView) "
                  "https://tw.tradingview.com/chart/EURUSD/S1gEffZF-Education-on-Double-RePo-on-15min-chart-in-EUR-USD-past-week",
           author="agent"),
    Family("E-095", "Initial-balance edge rejection",
           "The first-hour range (initial balance) is the reference Market Profile users and local day traders mark; "
           "while it is still unbroken, a fresh approach to its edge that fails to trade through and closes back in "
           "the bar's inner half meets responsive traders defending the balance, so fade back into the range.",
           {"ib_min": [30, 60, 90], "k": [0.5, 1.0, 1.5]}, _ib_edge_reject, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-096", "Elder Force Index pullback in trend",
           "Elder's rule: in a trend (price on the rising side of a rising EMA), a sharply negative 2-bar Force "
           "Index (price drop times volume) is a burst of impatient selling against the trend that longer-horizon "
           "trend holders absorb; buy when it first plunges (mirror in a down trend).",
           {"trend_min": [30, 60, 120], "k": [0.5, 1.0, 2.0]}, _force_index_pullback, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-097", "Ichimoku Tenkan/Kijun cross with Chikou agreement",
           "Ichimoku is a default overlay for many Brazilian retail traders; the Tenkan crossing the Kijun with price "
           "beyond the Kijun and the lagging span above price 26 bars ago is the textbook strong buy, so its users "
           "enter together at the same bar and the midrange-based stops of the other side sit just behind; follow it.",
           {"scale": [1.0, 2.0, 3.0]}, _ichimoku_tk, markets=("WIN",),
           source="assistant reasoning", author="agent"),
    Family("E-098", "Chaikin oscillator thrust",
           "The Chaikin oscillator (fast minus slow EMA of the session accumulation/distribution line) rises when "
           "recent volume is being printed with closes near bar highs: size is accepting higher prices bar after bar; "
           "when it first rises well above its usual size, accumulation is under way and continues, so follow it (mirror).",
           {"scale": [1.0, 2.0, 4.0], "k": [0.5, 1.0, 1.5]}, _chaikin_cross, markets=("WIN",),
           source="assistant reasoning", author="agent"),
]
