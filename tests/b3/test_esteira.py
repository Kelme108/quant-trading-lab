"""Conveyor (b3/esteira.py) on synthetic data only. Nothing here is market data."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from b3 import esteira as es
from b3 import pattern_search as ps
from b3.instruments import instrument_for

WIN = instrument_for("WIN")
NO_COST = {"fees_per_side_brl": 0.0, "slippage_ticks_per_side": 0.0, "stop_extra_ticks": 0.0}
EX = {"target_brl": 30.0, "stop_brl": 30.0, "max_hold_min": 10}
T0 = pd.Timestamp("2026-11-10T12:30:00Z").value          # 09:30 Sao Paulo
MIN = es.MIN_NS


def minutes(prices, flatten_after: int | None = None, day=1):
    """One session of 1-minute bars; prices = list of (open, high, low, close)."""
    n = len(prices)
    t = T0 + np.arange(n) * MIN
    o, h, l, c = (np.array([p[i] for p in prices], float) for i in range(4))
    cut = T0 + (flatten_after if flatten_after is not None else 10_000) * MIN
    return es.Minutes(t, o, h, l, c, np.full(n, day), np.full(n, cut, dtype=np.int64))


def flat(n, px=100000.0):
    return [(px, px + 10, px - 10, px)] * n


def test_target_needs_one_tick_through_and_fills_at_the_target():
    p = flat(20)
    p[3] = (100000, 100150, 99990, 100100)          # touches the target (150 pts = BRL 30) exactly: no fill
    p[5] = (100100, 100155, 100050, 100120)         # one tick through: fills at 100150
    t = es.simulate(np.array([T0]), np.array([1]), minutes(p), EX, WIN, NO_COST, 10)
    assert t.loc[0, "reason"] == "target"
    assert t.loc[0, "exit"] == 100150
    assert t.loc[0, "net_brl"] == pytest.approx(30.0)
    assert t.loc[0, "exit_ns"] == T0 + 6 * MIN


def test_stop_is_checked_before_the_target_in_the_same_minute():
    p = flat(20)
    p[2] = (100000, 100200, 99800, 100000)
    t = es.simulate(np.array([T0]), np.array([1]), minutes(p), EX, WIN, NO_COST, 10)
    assert t.loc[0, "reason"] == "stop"
    assert t.loc[0, "net_brl"] == pytest.approx(-30.0)


def test_stop_fills_at_a_gap_open_beyond_the_stop():
    p = flat(20)
    p[4] = (99700, 99750, 99650, 99700)             # gaps through the stop (99850)
    t = es.simulate(np.array([T0]), np.array([1]), minutes(p), EX, WIN, NO_COST, 10)
    assert t.loc[0, "reason"] == "stop" and t.loc[0, "exit"] == 99700


def test_short_side_mirrors():
    p = flat(20)
    p[3] = (100000, 100010, 99845, 99900)           # 100000 - 150 - 5 = 99845: one tick through
    t = es.simulate(np.array([T0]), np.array([-1]), minutes(p), EX, WIN, NO_COST, 10)
    assert t.loc[0, "reason"] == "target" and t.loc[0, "net_brl"] == pytest.approx(30.0)


def test_time_exit_at_the_open_of_the_minute_after_the_limit():
    p = flat(20)
    p[10] = (100050, 100060, 100040, 100050)
    t = es.simulate(np.array([T0]), np.array([1]), minutes(p), EX, WIN, NO_COST, 10)
    assert t.loc[0, "reason"] == "time"
    assert t.loc[0, "exit"] == 100050 and t.loc[0, "exit_ns"] == T0 + 10 * MIN


def test_flatten_before_the_time_limit():
    p = flat(20)
    p[4] = (100020, 100030, 100010, 100020)
    t = es.simulate(np.array([T0]), np.array([1]), minutes(p, flatten_after=4), EX, WIN, NO_COST, 10)
    assert t.loc[0, "reason"] == "flatten" and t.loc[0, "exit"] == 100020


def test_costs_are_charged():
    cost = {"fees_per_side_brl": 0.25, "slippage_ticks_per_side": 1.0, "stop_extra_ticks": 0.0}
    t = es.simulate(np.array([T0]), np.array([1]), minutes(flat(20)), EX, WIN, cost, 10)
    # entry +5 pts, exit -5 pts on a flat path: -10 pts = BRL -2, fees BRL 0.50
    assert t.loc[0, "net_brl"] == pytest.approx(-2.5)


def test_one_position_at_a_time_and_daily_cap():
    m = minutes(flat(60))
    e = T0 + np.array([0, 3, 12, 25, 40]) * MIN       # 3 lands inside the first trade (exits at 10)
    t = es.simulate(e, np.ones(5, int), m, EX, WIN, NO_COST, 10)
    assert list((t["entry_ns"] - T0) // MIN) == [0, 12, 25, 40]
    t2 = es.simulate(e, np.ones(5, int), m, EX, WIN, NO_COST, 2)
    assert len(t2) == 2


def test_signal_without_a_minute_bar_is_skipped():
    t = es.simulate(np.array([T0 - 5 * MIN]), np.array([1]), minutes(flat(20)), EX, WIN, NO_COST, 10)
    assert t.empty


# ---- screen pieces -----------------------------------------------------------------------------

def test_neighbours_are_one_step_on_one_parameter():
    g = {"a": [1, 2, 3], "b": [10, 20]}
    assert sorted(map(str, es.neighbours(g, {"a": 2, "b": 10}))) == sorted(map(str, [
        {"a": 1, "b": 10}, {"a": 3, "b": 10}, {"a": 2, "b": 20}]))
    assert es.neighbours(g, {"a": 1, "b": 10}) == [{"a": 2, "b": 10}, {"a": 1, "b": 20}]


def _row(a, net, tpy=800, slices=6):
    return {"tf": 5, "params": {"a": a}, "measured": {"trades_per_year": tpy, "mean_net_brl": net, "positive_slices": slices}}


SC = {"min_trades_per_year": 500, "mean_net_brl_measured_gt": 0.0, "min_positive_slices": 5,
      "plateau_min_positive_neighbour_share": 0.6667}


def test_screen_rejects_an_isolated_peak_and_keeps_a_plateau():
    rows = es.screen_family_rows([_row(1, -1.0), _row(2, 3.0), _row(3, -0.5)], {"a": [1, 2, 3]}, SC)
    assert rows[1]["fails"] == ["plateau"]
    rows = es.screen_family_rows([_row(1, 0.5), _row(2, 3.0), _row(3, 0.2)], {"a": [1, 2, 3]}, SC)
    assert rows[1]["passed_screen"] and rows[0]["passed_screen"]


def test_screen_needs_frequency_positive_net_and_slices():
    rows = es.screen_family_rows([_row(1, 1.0, tpy=300), _row(2, 1.0, slices=4), _row(3, 1.0)], {"a": [1, 2, 3]}, SC)
    assert "trades_per_year" in rows[0]["fails"]
    assert "positive_slices" in rows[1]["fails"]
    assert rows[2]["passed_screen"]


def test_overlap_counts_same_side_entries_within_five_minutes():
    a = pd.DataFrame({"entry_ns": T0 + np.array([0, 60, 120]) * MIN, "side": [1, 1, -1]})
    b = pd.DataFrame({"entry_ns": T0 + np.array([3, 200, 121]) * MIN, "side": [1, 1, 1]})
    assert es.overlap(a, b) == pytest.approx(1 / 3)


def test_family_limits():
    cfg = es.load_config()
    f = es.Family("E-T", "t", "h", {"a": [1, 2], "b": [1], "c": [1], "d": [1]}, lambda ctx, p: ctx.c * 0)
    assert any("parameters" in w for w in es.validate_family(f, cfg))
    f = es.Family("E-T", "t", "h", {"a": list(range(6))}, lambda ctx, p: ctx.c * 0)
    assert any("values" in w for w in es.validate_family(f, cfg))
    f = es.Family("E-T", "t", "h", {"a": [1, 2]}, lambda ctx, p: ctx.c * 0, timeframes=(15,))
    assert any("timeframes" in w for w in es.validate_family(f, cfg))
    f = es.Family("E-T", "t", "h", {"a": [1, 2]}, lambda ctx, p: ctx.c * 0)
    assert es.validate_family(f, cfg) == []


# ---- causality / live window ---------------------------------------------------------------------

def synthetic_frame(n_days=30, per_day=20, seed=1) -> ps.Frame:
    rng = np.random.default_rng(seed)
    n = n_days * per_day
    c = 100000 + np.cumsum(rng.choice([-10, -5, 0, 5, 10], n)).astype(float)
    o = np.r_[c[0], c[:-1]]
    h, l = np.maximum(o, c) + 5, np.minimum(o, c) - 5
    day = np.repeat(np.arange(n_days), per_day)
    bar = np.tile(np.arange(per_day), n_days)
    times = pd.Timestamp("2026-01-05T12:00:00Z") + pd.to_timedelta(day, "D") + pd.to_timedelta(bar * 5, "min")
    dates = (pd.Timestamp("2026-01-05") + pd.to_timedelta(day, "D")).date
    df = pd.DataFrame({"time": times, "open": o, "high": h, "low": l, "close": c, "volume": rng.integers(100, 1000, n),
                       "local_date": dates, "minute_of_day": 540 + bar * 5, "bar_in_day": bar,
                       "minutes_to_close": (per_day - bar - 1) * 5.0, "wdo_close": 5000.0})
    df["day_open"] = df.groupby("local_date")["open"].transform("first")
    now = times.astype("int64").to_numpy() + 5 * MIN
    ok = np.ones(n, bool)
    nxt = np.r_[day[1:] == day[:-1], False]
    return ps.Frame(5, df, None, None, day, now, ok, np.zeros(n, bool), nxt)


def test_causal_family_passes_the_checks():
    f = es.Family("E-T", "t", "h", {"n": [3]}, lambda ctx, p: np.sign(ctx.c - ctx.prev(ctx.c, p["n"])))
    assert es.check_family(f, synthetic_frame()) == []


def test_helpers_used_by_families_pass_the_checks():
    def sig(ctx, p):
        z = (ctx.c - ctx.vwap()) / ctx.prev_sessions(ctx.c - ctx.vwap(), "sd")
        hi = ctx.session_high()
        ema = ctx.ema(ctx.c, 5)
        vol = ctx.v / ctx.same_minute(ctx.v)
        pdh = ctx.prev_session_value("high")
        r = ctx.roll(ctx.c, 4, "max", include_current=False)
        return np.where((z > 0) & (ctx.c > ema) & (vol > 0) & (ctx.c < hi + 1e9) & (pdh > 0) & (r > 0), 1, 0)
    f = es.Family("E-T", "t", "h", {"k": [1]}, sig)
    assert es.check_family(f, synthetic_frame()) == []


def test_look_ahead_is_caught():
    def peek(ctx, p):
        nxt = np.r_[ctx.c[1:], ctx.c[-1]]
        return np.sign(nxt - ctx.c)
    f = es.Family("E-T", "t", "h", {"k": [1]}, peek)
    probs = es.check_family(f, synthetic_frame())
    assert probs and probs[0].startswith("look-ahead")


def test_a_signal_needing_the_whole_history_is_caught_by_the_window_check():
    def whole(ctx, p):
        k = np.arange(ctx.n) // 7                    # counts every bar since the first one loaded
        return np.where(k % 2 == 0, 1, -1)
    f = es.Family("E-T", "t", "h", {"k": [1]}, whole)
    probs = es.check_family(f, synthetic_frame())
    assert probs and probs[0].startswith("window")


def test_signal_must_be_minus_one_zero_or_one():
    f = es.Family("E-T", "t", "h", {"k": [1]}, lambda ctx, p: ctx.c - ctx.c + 2)
    with pytest.raises(ValueError):
        es.directions(f, synthetic_frame(), {"k": 1})
