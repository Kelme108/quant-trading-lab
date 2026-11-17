"""P-025 AuctionPressureReversal on SYNTHETIC WIN session 1-minute bars (09:00 open, 18:25 close, Sao Paulo time, 2026 dates):
class constants, causality, live-window parity, impulse and scale against an independent computation (DST included),
hand-built days (short and long at each anchor, stops, thresholds, skipped anchors, one position, 3-entry cap, time exit,
flatten) and no overnight position. Nothing here is market data.

Hand-built sessions: every bar of a PRIOR session has open = close = 120000 (high/low +-5, volume 100) except the bar
that closes each anchor's 20-minute window (the bar opening at A+4): it closes at 120120, so the impulse of every anchor
of every prior session is +0.1% and SCALE = 0.001 (threshold 0.0005). TODAY starts flat too; a test sets the closes of
the anchor bars it wants (an open is the previous close). The first 14000 bars of a frame are the engine's warm-up, hence
26 sessions before the target day (565 bars each)."""

import inspect
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from b3.backtest import BacktestConfig, run
from b3.calendar import B3SessionCalendar, SessionRules
from b3.checks import causality_problems, window_parity_problems
from b3.markets import market
from b3.proxy_rules import p025_auction_pressure_reversal as mod
from b3.proxy_rules.p025_auction_pressure_reversal import AuctionPressureReversal
from b3.strategy_check import check_proxy_rule_source
from live.core.models import Position

UTC = timezone.utc
SP, NY = ZoneInfo("America/Sao_Paulo"), ZoneInfo("America/New_York")
CAL = B3SessionCalendar("WIN")
COLS = ["time", "open", "high", "low", "close", "volume"]
BASE = 120000.0
TARGET = date(2026, 5, 13)           # New York on EDT: A2 = 10:30, A3 = 17:00
TARGET_EST = date(2026, 11, 17)      # New York on EST: A2 = 11:30, A3 = 18:00
PRIOR_DAYS = 26


def nbars(day):
    s = CAL.session(day)
    return int((s.close - s.open).total_seconds() // 60)


def trading_days_before(day, n):
    out, d = [], day
    while len(out) < n:
        d -= timedelta(days=1)
        if CAL.is_trading_day(d):
            out.append(d)
    return sorted(out)


def anchors(day):
    """Minute of the Sao Paulo day of A1, A2, A3, from the tz database (independent of the rule)."""
    out = [600]
    for h, m in ((9, 30), (16, 0)):
        t = datetime(day.year, day.month, day.day, h, m, tzinfo=NY).astimezone(SP)
        out.append(t.hour * 60 + t.minute)
    return out


def k_post(day, a):
    """Bar index (from the 09:00 open) of the bar opening at A+4, a in 1..3."""
    return anchors(day)[a - 1] + 4 - 540


def k_pre(day, a):
    return anchors(day)[a - 1] - 15 - 540


def session_rows(day, closes=None, highs=None, lows=None, drop=()):
    m = market("WIN")
    closes, highs, lows = closes or {}, highs or {}, lows or {}
    t0 = datetime.combine(day, m.open, m.zone)
    rows, prev = [], None
    for k in range(nbars(day)):
        c = closes.get(k, BASE)
        o = c if prev is None else prev
        prev = c
        if k in drop:
            continue
        h = highs.get(k, max(o, c) + 5.0)
        lo = lows.get(k, min(o, c) - 5.0)
        rows.append((pd.Timestamp((t0 + timedelta(minutes=k)).astimezone(UTC)), o, h, lo, c, 100.0))
    return rows


def hand_frame(target, deltas=None, closes=None, highs=None, lows=None, drop=(), prior=PRIOR_DAYS, prior_delta=120.0,
               prior_drop=()):
    """deltas: {anchor: close of its signal bar minus BASE} for today; closes/highs/lows/drop: bar-index overrides."""
    rows = []
    days = trading_days_before(target, prior)
    for i, d in enumerate(days):
        cl = {k_post(d, a): BASE + prior_delta for a in (1, 2, 3)}
        rows += session_rows(d, cl, drop=prior_drop if i == len(days) - 1 else ())
    cl = {k_post(target, a): BASE + delta for a, delta in (deltas or {}).items()}
    cl.update(closes or {})
    rows += session_rows(target, cl, highs, lows, drop)
    return pd.DataFrame(rows, columns=COLS)


def strategy_on_win():
    return AuctionPressureReversal.on("WIN")()


class Result:
    def __init__(self, trades, positions_held_overnight):
        self.trades, self.positions_held_overnight = trades, positions_held_overnight


def trades_of(frame, scenario="optimistic", last_day_only=True):
    """Backtest; by default only the trades entered on the frame's LAST session (the hand-built target day: the prior
    sessions after the warm-up trade too, since their impulses equal the scale)."""
    r = run(frame, strategy_on_win(), market("WIN").cost(scenario), BacktestConfig())
    trades = r.trades
    if last_day_only:
        last = frame["time"].iloc[-1].tz_convert(market("WIN").zone).date()
        trades = [t for t in trades if t.entry_time.tz_convert(market("WIN").zone).date() == last]
    return Result(trades, r.positions_held_overnight)


def hhmm(ts):
    return ts.tz_convert(market("WIN").zone).strftime("%H:%M")


def prepared_today(frame, day=TARGET):
    p = strategy_on_win().prepare(frame)
    return p[p["local_date"] == day].reset_index(drop=True)


def synthetic_sessions(days=36, seed=3, start=120000.0, step=5.0, first_day=date(2026, 9, 28)):
    """Random WIN 1-minute sessions; the default range crosses the US switch to standard time (2026-11-01)."""
    m = market("WIN")
    rng = random.Random(seed)
    d, rows, prev = first_day, [], start
    count = 0
    while count < days:
        if CAL.is_trading_day(d):
            t = datetime.combine(d, m.open, m.zone)
            end = datetime.combine(d, m.close, m.zone)
            while t + timedelta(minutes=1) <= end:
                o = prev + step * rng.randint(-1, 1)
                c = o + step * rng.randint(-3, 3)
                rows.append((pd.Timestamp(t.astimezone(UTC)), o, max(o, c) + step * rng.randint(0, 2),
                             min(o, c) - step * rng.randint(0, 2), c, float(rng.randint(50, 500))))
                prev, t = c, t + timedelta(minutes=1)
            count += 1
        d += timedelta(days=1)
    return pd.DataFrame(rows, columns=COLS)


def targeted_parity_problems(strategy, frame, per_kind=6):
    """Live window against full history on the bars that carry an entry or a time exit (a random sample would rarely land on
    one: they are about 0.5% of the bars)."""
    full = strategy.prepare(frame.reset_index(drop=True))
    rows = list(full.itertuples(index=False, name="Row"))
    window = strategy.warmup + 4
    entries = [int(k) for k in np.flatnonzero((full["ap_side"] != 0).to_numpy()) if k >= window - 1]
    exits = [int(k) for k in np.flatnonzero((full["ap_exit"] == 1).to_numpy()) if k >= window - 1]
    assert entries and exits
    problems = []
    for k in entries[:per_kind] + entries[-per_kind:] + exits[:per_kind] + exits[-per_kind:]:
        part = frame.iloc[k - window + 1:k + 1].reset_index(drop=True)
        last = next(strategy.prepare(part).tail(1).itertuples(index=False, name="Row"))
        price = rows[k].close
        for position in (None, Position("X", 1.0, price, None), Position("X", -1.0, price, None)):
            a, b = strategy.decide(rows[k], position), strategy.decide(last, position)
            if (a.action, a.stop_price) != (b.action, b.stop_price):
                problems.append(f"bar {k}: full {a} vs window {b}")
    return problems


# ---------------------------------------------------------------------------------------------------------- constants
def test_class_constants():
    s = AuctionPressureReversal
    assert mod.RULE_ID == "P-025"
    assert s.name.startswith("P-025") and s.timeframe_min == 1
    assert isinstance(s.warmup, int) and s.warmup >= 20 * 570 + 570
    assert s.rules == SessionRules(entry_start_after_open_min=60, entry_end_before_close_min=15,
                                   flatten_before_close_min=5)
    assert s.params == {
        "cash_open_minute_sao_paulo": 600, "nyse_open_minute_new_york": 570, "nyse_close_minute_new_york": 960,
        "pre_anchor_min": 15, "post_anchor_min": 5, "scale_lookback_sessions": 20, "threshold_mult_of_scale": 0.5,
        "stop_min_pct": 0.2, "stop_impulse_mult": 1.0, "hold_min": 25, "max_entries_per_day": 3,
        "entry_start_after_open_min": 60, "entry_end_before_close_min": 15, "flatten_before_close_min": 5}
    assert "symbol" not in vars(s)
    assert nbars(TARGET) == 565
    assert check_proxy_rule_source(Path(inspect.getsourcefile(mod)), "P-025") == []


# ------------------------------------------------------------------------------------- causality and live-window parity
def test_causal_and_matches_the_live_window():
    strategy = strategy_on_win()
    frame = synthetic_sessions()
    assert len(frame) > strategy.warmup + 4 + 3000
    assert causality_problems(strategy, frame) == []
    assert window_parity_problems(strategy, frame, samples=25) == []
    p = strategy.prepare(frame)
    late = p.iloc[strategy.warmup:]
    assert (late["ap_side"] > 0).sum() > 5 and (late["ap_side"] < 0).sum() > 5 and (late["ap_exit"] == 1).sum() > 5
    assert targeted_parity_problems(strategy, frame) == []


def test_hand_built_days_are_causal_and_match_the_live_window():
    strategy = strategy_on_win()
    frame = hand_frame(TARGET, {1: 120.0, 2: -120.0, 3: 120.0})
    assert causality_problems(strategy, frame, n_cuts=4) == []
    assert targeted_parity_problems(strategy, frame, per_kind=2) == []


# ---------------------------------------------------------- impulse and scale against an independent computation
def test_impulse_and_scale_match_an_independent_computation_across_the_dst_switch():
    frame = synthetic_sessions(days=36, seed=11)
    p = strategy_on_win().prepare(frame)
    local = frame["time"].dt.tz_convert(SP)
    f = frame.assign(day=local.dt.date, minute=local.dt.hour * 60 + local.dt.minute)
    opens = {(r.day, r.minute): r.open for r in f.itertuples()}
    closes = {(r.day, r.minute): r.close for r in f.itertuples()}
    days = list(dict.fromkeys(f["day"]))
    expected = {}
    for a in (1, 2, 3):
        hist = []
        for d in days:
            A = anchors(d)[a - 1]
            if (d, A - 15) in opens and (d, A + 4) in closes:
                imp = closes[(d, A + 4)] / opens[(d, A - 15)] - 1
                scale = float(np.median(hist[-20:])) if len(hist) >= 20 else np.nan
                expected[(d, a)] = (imp, scale)
                hist.append(abs(imp))
    got = p[p["ap_anchor"] > 0]
    assert len(got) == len(expected) == 3 * 36
    for r in got.itertuples():
        imp, scale = expected[(r.local_date, r.ap_anchor)]
        assert r.ap_imp == pytest.approx(imp, rel=1e-12, abs=1e-15)
        if np.isnan(scale):
            assert np.isnan(r.ap_scale)
        else:
            assert r.ap_scale == pytest.approx(scale, rel=1e-12)
    assert sum(1 for v in expected.values() if not np.isnan(v[1])) == 3 * 16
    # the signal bar of each anchor is the bar opening at A+4, and the anchors follow New York's clock
    rows = p[p["ap_anchor"] > 0]
    for r in rows.itertuples():
        assert r.minute_of_day == anchors(r.local_date)[r.ap_anchor - 1] + 4
    edt = rows[rows["local_date"] == date(2026, 10, 30)]
    est = rows[rows["local_date"] == date(2026, 11, 4)]
    assert edt.set_index("ap_anchor")["minute_of_day"].to_dict() == {1: 604, 2: 634, 3: 1024}
    assert est.set_index("ap_anchor")["minute_of_day"].to_dict() == {1: 604, 2: 694, 3: 1084}


def test_anchor_clock_on_the_two_hand_days():
    for day, minutes in ((TARGET, [604, 634, 1024]), (TARGET_EST, [604, 694, 1084])):
        p = prepared_today(hand_frame(day), day)
        assert p[p["ap_anchor"] > 0].sort_values("ap_anchor")["minute_of_day"].tolist() == minutes
        assert [k_post(day, a) + 540 for a in (1, 2, 3)] == minutes


def test_impulse_uses_the_open_of_bar_a_minus_15_and_the_close_of_bar_a_plus_4():
    k1 = k_pre(TARGET, 1)
    closes = {k1 - 1: BASE + 100.0, k1: BASE - 500.0, k_post(TARGET, 1): BASE + 220.0}
    p = prepared_today(hand_frame(TARGET, closes=closes))
    row = p.iloc[k_post(TARGET, 1)]
    assert row["ap_anchor"] == 1 and row["ap_imp"] == pytest.approx(120220.0 / 120100.0 - 1, rel=1e-12)
    assert row["ap_scale"] == pytest.approx(0.001, rel=1e-9)


def test_scale_needs_20_earlier_sessions_that_had_the_anchor():
    d = {1: 120.0}
    p20 = prepared_today(hand_frame(TARGET, d, prior=20))
    assert p20.loc[k_post(TARGET, 1), "ap_side"] == -1 and (p20["ap_side"] != 0).sum() == 1
    assert p20.loc[k_post(TARGET, 1), "ap_scale"] == pytest.approx(0.001, rel=1e-9)
    p19 = prepared_today(hand_frame(TARGET, d, prior=19))
    assert (p19["ap_side"] == 0).all() and np.isnan(p19.loc[k_post(TARGET, 1), "ap_scale"])
    # 20 earlier sessions but the latest one lacks the bar of A1's window: only 19 values for A1, still 20 for A2
    prior_drop = {k_pre(trading_days_before(TARGET, 1)[0], 1)}
    p = prepared_today(hand_frame(TARGET, {1: 120.0, 2: 120.0}, prior=20, prior_drop=prior_drop))
    assert np.isnan(p.loc[k_post(TARGET, 1), "ap_scale"]) and p.loc[k_post(TARGET, 1), "ap_side"] == 0
    assert p.loc[k_post(TARGET, 2), "ap_side"] == -1
    # with 21 earlier sessions the one that lacks the bar is skipped and the 20 before it are used
    p = prepared_today(hand_frame(TARGET, {1: 120.0}, prior=21, prior_drop=prior_drop))
    assert p.loc[k_post(TARGET, 1), "ap_side"] == -1


def test_scale_is_the_median_of_the_last_20_values_and_ignores_older_ones_and_today():
    # 25 earlier sessions: the 5 oldest have impulse 1% (old), the 20 newest 0.1%: scale = 0.001, today's 0.06% passes
    rows = []
    days = trading_days_before(TARGET, 25)
    for i, d in enumerate(days):
        rows += session_rows(d, {k_post(d, a): BASE + (1200.0 if i < 5 else 120.0) for a in (1, 2, 3)})
    rows += session_rows(TARGET, {k_post(TARGET, 1): BASE + 72.0})
    p = prepared_today(pd.DataFrame(rows, columns=COLS))
    assert p.loc[k_post(TARGET, 1), "ap_scale"] == pytest.approx(0.001, rel=1e-9)
    assert p.loc[k_post(TARGET, 1), "ap_side"] == -1
    # today's own impulse never enters its scale: a huge move today leaves the scale as it was
    rows = rows[:-nbars(TARGET)] + session_rows(TARGET, {k_post(TARGET, 1): BASE + 5000.0})
    p = prepared_today(pd.DataFrame(rows, columns=COLS))
    assert p.loc[k_post(TARGET, 1), "ap_scale"] == pytest.approx(0.001, rel=1e-9)


# -------------------------------------------------------------------------------------------------- entries and stops
def test_short_after_an_up_impulse_at_the_cash_open_with_the_floor_stop_and_the_25_minute_time_exit():
    (t,) = trades_of(hand_frame(TARGET, {1: 120.0})).trades
    # impulse 120/120000 = 0.10% < the 0.20% floor: distance 0.2% of 120120 = 240.24 -> 120360.24 -> 120365
    assert (t.side, t.entry_price, t.stop_price, t.entry_reason) == ("short", 120120.0, 120365.0, "fade_up_impulse")
    assert hhmm(t.entry_time) == "10:05"                       # the open of the bar after the signal bar (10:04)
    assert t.exit_reason == "time_exit_25min" and hhmm(t.exit_time) == "10:30" and t.exit_price == BASE


def test_long_after_a_down_impulse_at_the_cash_open_with_the_floor_stop():
    (t,) = trades_of(hand_frame(TARGET, {1: -120.0})).trades
    # 0.2% of 119880 = 239.76 -> 119640.24 -> floor 119640
    assert (t.side, t.entry_price, t.stop_price, t.entry_reason) == ("long", 119880.0, 119640.0, "fade_down_impulse")
    assert hhmm(t.entry_time) == "10:05"
    assert t.exit_reason == "time_exit_25min" and hhmm(t.exit_time) == "10:30" and t.exit_price == BASE


@pytest.mark.parametrize("delta, side, stop", [
    (360.0, "short", 120725.0),      # |impulse| 0.30% > 0.20%: distance 0.003 * 120360 = 361.08 -> 120721.08 -> ceil
    (-360.0, "long", 119280.0),      # 0.003 * 119640 = 358.92 -> 119281.08 -> floor
    (240.0, "short", 120485.0),      # 0.2% impulse = the floor: 0.002 * 120240 = 240.48 -> 120480.48 -> 120485
    (-240.0, "long", 119520.0),      # 0.002 * 119760 = 239.52 -> 119520.48 -> 119520
])
def test_stop_distance_is_the_larger_of_the_impulse_and_0p20_percent_rounded_away_from_the_entry(delta, side, stop):
    (t,) = trades_of(hand_frame(TARGET, {1: delta})).trades
    assert t.side == side and t.stop_price == stop
    assert (t.stop_price > t.entry_price) if side == "short" else (t.stop_price < t.entry_price)


def test_entry_at_the_nyse_open_and_at_the_closing_call_on_an_edt_day():
    (t,) = trades_of(hand_frame(TARGET, {2: -120.0})).trades
    assert t.side == "long" and hhmm(t.entry_time) == "10:35" and hhmm(t.exit_time) == "11:00"
    (t,) = trades_of(hand_frame(TARGET, {3: 120.0})).trades
    assert t.side == "short" and hhmm(t.entry_time) == "17:05" and hhmm(t.exit_time) == "17:30"
    assert t.exit_reason == "time_exit_25min" and t.stop_price == 120365.0


def test_est_day_moves_the_nyse_anchors_one_hour_later_and_the_last_entry_is_flattened_before_the_close():
    (t,) = trades_of(hand_frame(TARGET_EST, {2: 120.0})).trades
    assert t.side == "short" and hhmm(t.entry_time) == "11:35" and hhmm(t.exit_time) == "12:00"
    (t,) = trades_of(hand_frame(TARGET_EST, {3: -120.0})).trades
    # A3 = 18:00: signal 18:04, entry 18:05 (before 18:10 = close - 15), flatten at 18:20 before the 25-minute exit
    assert t.side == "long" and hhmm(t.entry_time) == "18:05"
    assert t.exit_reason == "end_of_day_flatten" and hhmm(t.exit_time) == "18:20" and t.exit_price == BASE


# -------------------------------------------------------------------------------------------------------- thresholds
@pytest.mark.parametrize("delta, trades", [(60.0, 1), (55.0, 0), (-60.0, 1), (-55.0, 0), (0.0, 0)])
def test_threshold_is_half_the_scale_inclusive(delta, trades):
    r = trades_of(hand_frame(TARGET, {1: delta}))
    assert len(r.trades) == trades
    if trades:
        assert r.trades[0].side == ("short" if delta > 0 else "long")


def test_the_threshold_is_relative_to_each_anchors_own_scale():
    # the prior impulses of A2 are 0.3%: A2's threshold is 0.15%, so 0.1% trades at A1 and A3 but not at A2
    rows = []
    for d in trading_days_before(TARGET, PRIOR_DAYS):
        rows += session_rows(d, {k_post(d, 1): BASE + 120.0, k_post(d, 2): BASE + 360.0, k_post(d, 3): BASE + 120.0})
    rows += session_rows(TARGET, {k_post(TARGET, a): BASE + 120.0 for a in (1, 2, 3)})
    r = trades_of(pd.DataFrame(rows, columns=COLS))
    assert [hhmm(t.entry_time) for t in r.trades] == ["10:05", "17:05"]


# --------------------------------------------------------------------------------------------------- skipped anchors
def test_anchor_is_skipped_when_a_bar_of_its_window_is_missing():
    deltas = {1: 120.0}
    assert len(trades_of(hand_frame(TARGET, deltas)).trades) == 1
    assert trades_of(hand_frame(TARGET, deltas, drop={k_pre(TARGET, 1)})).trades == []       # the bar opening at A-15
    assert trades_of(hand_frame(TARGET, deltas, drop={k_post(TARGET, 1)})).trades == []      # the bar opening at A+4
    p = prepared_today(hand_frame(TARGET, deltas, drop={k_pre(TARGET, 1)}))
    assert (p["ap_anchor"] == 1).sum() == 0 and (p["ap_side"] == 0).all()


# ------------------------------------------------------------------------------------------ position handling and cap
def test_three_entries_one_per_anchor_each_closed_by_the_time_exit():
    frame = hand_frame(TARGET, {1: 120.0, 2: -120.0, 3: 120.0})
    r = trades_of(frame)
    assert [(t.side, hhmm(t.entry_time), hhmm(t.exit_time)) for t in r.trades] == [
        ("short", "10:05", "10:30"), ("long", "10:35", "11:00"), ("short", "17:05", "17:30")]
    p = prepared_today(frame)
    assert (p["ap_side"] != 0).sum() == 3 and (p["ap_exit"] == 1).sum() == 3
    r = trades_of(hand_frame(TARGET_EST, {1: 120.0, 2: -120.0, 3: 120.0}))
    assert [(t.side, hhmm(t.entry_time), hhmm(t.exit_time)) for t in r.trades] == [
        ("short", "10:05", "10:30"), ("long", "11:35", "12:00"), ("short", "18:05", "18:20")]
    assert r.trades[2].exit_reason == "end_of_day_flatten"


def test_an_anchor_that_finds_the_position_open_is_skipped():
    deltas = {1: 120.0, 2: 120.0}
    assert len(trades_of(hand_frame(TARGET, deltas)).trades) == 2          # exit 10:30 < A2 signal bar 10:34
    # five missing bars (10:10-10:14) push the 25th bar after the signal to 10:34, A2's own signal bar: the position is
    # still open there (it is exited at the next open) and A2 is skipped
    frame = hand_frame(TARGET, deltas, drop=set(range(70, 75)))
    r = trades_of(frame)
    (t,) = r.trades
    assert hhmm(t.entry_time) == "10:05" and t.exit_reason == "time_exit_25min" and hhmm(t.exit_time) == "10:35"
    p = prepared_today(frame)
    assert (p["ap_side"] != 0).sum() == 1 and (p["ap_exit"] == 1).sum() == 1


def test_a_stop_exit_fills_at_the_stop_and_is_checked_from_the_entry_bar_to_the_last_held_bar():
    deltas = {1: 120.0}                                                # short at 10:05, stop 120365, entry bar k = 65
    (t,) = trades_of(hand_frame(TARGET, deltas, highs={65: 120370.0})).trades          # the entry bar itself
    assert t.exit_reason == "stop_loss" and t.exit_price == 120365.0 and hhmm(t.exit_time) == "10:06"
    (t,) = trades_of(hand_frame(TARGET, deltas, highs={75: 120370.0})).trades
    assert t.exit_reason == "stop_loss" and hhmm(t.exit_time) == "10:16"
    (t,) = trades_of(hand_frame(TARGET, deltas, highs={89: 120370.0})).trades          # 10:29, the last held bar
    assert t.exit_reason == "stop_loss" and hhmm(t.exit_time) == "10:30"
    (t,) = trades_of(hand_frame(TARGET, deltas, highs={90: 120370.0})).trades          # after the exit decision
    assert t.exit_reason == "time_exit_25min" and hhmm(t.exit_time) == "10:30"
    (t,) = trades_of(hand_frame(TARGET, {1: -120.0}, lows={70: 119630.0})).trades
    assert t.side == "long" and t.exit_reason == "stop_loss" and t.exit_price == 119640.0


def test_after_a_stop_the_bar_that_hit_it_can_signal():
    # with 5 bars missing (10:10-10:14) the A1 position is still open at bar k = 94 (10:34), A2's signal bar, where its time
    # exit would be decided; a high of 120370 in that very bar stops it out first (the stop is processed before the
    # decision), so the book is flat at that bar's close and A2's signal in the same bar is taken (entry at 10:35)
    frame = hand_frame(TARGET, {1: 120.0, 2: 120.0}, drop=set(range(70, 75)), highs={94: 120370.0})
    t1, t2 = trades_of(frame).trades
    assert t1.exit_reason == "stop_loss" and t1.exit_price == 120365.0 and hhmm(t1.exit_time) == "10:35"
    assert t2.side == "short" and hhmm(t2.entry_time) == "10:35" and t2.entry_price == 120120.0
    p = prepared_today(frame)
    assert (p["ap_side"] != 0).sum() == 2 and (p["ap_exit"] == 1).sum() == 1      # the 2nd entry's own time exit


# ------------------------------------------------------------------------------------------------ no overnight, volume
def test_synthetic_sessions_trade_and_never_hold_overnight():
    frames = [synthetic_sessions(days=36, seed=3), hand_frame(TARGET, {1: 120.0, 2: -120.0, 3: 120.0}),
              hand_frame(TARGET_EST, {3: -120.0})]
    for frame in frames:
        for scenario in ("base", "optimistic"):
            r = trades_of(frame, scenario, last_day_only=False)
            assert r.trades
            assert r.positions_held_overnight == 0
            per_day = pd.Series([t.entry_time.tz_convert(market("WIN").zone).date() for t in r.trades]).value_counts()
            assert max(per_day) <= 3
    r = trades_of(synthetic_sessions(days=36, seed=3), last_day_only=False)
    assert {t.side for t in r.trades} == {"long", "short"}
    assert all((t.stop_price < t.entry_price) if t.side == "long" else (t.stop_price > t.entry_price) for t in r.trades)
    assert all(t.stop_price % 5.0 == 0 for t in r.trades)
