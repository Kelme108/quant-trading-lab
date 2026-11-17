"""P-017 WinStopSweepFailureFade on SYNTHETIC WIN session 1-minute bars (Sao Paulo time, bars from the calendar's
session open to its close): class constants, causality, live-window parity, hand-built days (short, long, stops, exits,
filters, event blocks, entry cap) and no overnight position."""

import random
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import pytest

from b3.backtest import BacktestConfig, run
from b3.calendar import B3SessionCalendar
from b3.checks import causality_problems, window_parity_problems
from b3.markets import market
from b3.proxy_rules import p017_win_stop_sweep_failure_fade as mod
from b3.proxy_rules.p017_win_stop_sweep_failure_fade import WinStopSweepFailureFade

UTC = timezone.utc
CAL = B3SessionCalendar("WIN")
COLS = ["time", "open", "high", "low", "close", "volume"]
BASE = (120000.0, 120005.0, 119995.0, 120000.0)
PRIOR_DAYS = 2                      # 2 flat sessions > warmup (700 bars)
TARGET = date(2026, 5, 13)          # ordinary day (no FOMC; CPI of that month was the day before; NFP is early in the month)


def trading_days_before(day, n):
    out, d = [], day
    while len(out) < n:
        d -= timedelta(days=1)
        if CAL.is_trading_day(d):
            out.append(d)
    return sorted(out)


def session_rows(day, overrides=None):
    """The session's 1-minute bars from the calendar's open to its close; `overrides` = {bar index: (o, h, l, c)}."""
    s = CAL.session(day)
    n = int((s.close - s.open).total_seconds() // 60)
    overrides = overrides or {}
    return [(pd.Timestamp((s.open + timedelta(minutes=k)).astimezone(UTC)),) + tuple(overrides.get(k, BASE)) + (100.0,)
            for k in range(n)]


def hand_frame(target_day, overrides=None, prior=PRIOR_DAYS):
    rows = []
    for d in trading_days_before(target_day, prior):
        rows += session_rows(d)
    rows += session_rows(target_day, overrides)
    return pd.DataFrame(rows, columns=COLS)


def synthetic_sessions(days=5, seed=3, start=120000.0, step=5.0, spread=14):
    m = market("WIN")
    rng = random.Random(seed)
    d, rows, prev = date(2026, 1, 5), [], start
    while len({r[0].date() for r in rows}) < days:
        if CAL.is_trading_day(d):
            t = datetime.combine(d, m.open, m.zone)
            end = datetime.combine(d, m.close, m.zone)
            while t + timedelta(minutes=1) <= end:
                o = prev + step * rng.randint(-2, 2)
                c = o + step * rng.randint(-spread, spread)
                rows.append((t, o, max(o, c) + step * rng.randint(0, 6), min(o, c) - step * rng.randint(0, 6), c,
                             float(rng.randint(50, 500))))
                prev, t = c, t + timedelta(minutes=1)
        d += timedelta(days=1)
    return pd.DataFrame([(pd.Timestamp(r[0].astimezone(UTC)),) + r[1:] for r in rows], columns=COLS)


def trades_of(frame):
    return run(frame, WinStopSweepFailureFade.on("WIN")(), market("WIN").cost("optimistic"), BacktestConfig())


def hhmm(ts):
    return ts.tz_convert(market("WIN").zone).strftime("%H:%M")


def flat(first, last, price, spread=5.0):
    return {k: (price, price + spread, price - spread, price) for k in range(first, last + 1)}


def short_event(b, hi_age=30, lo_age=40, lo=119900.0, break_high=120230.0, break_close=120210.0, fail_at=1,
                fail_close=120190.0, hold_until=None, hold=120190.0):
    """An up-sweep: swing low `lo` at b - lo_age, swing high 120200 at b - hi_age, break bar b (high above 120200), the
    failure bar at b + fail_at (earlier bars close above 120195), the entry bar after it and flat bars at `hold`."""
    ov = {b - lo_age: (120000.0, 120005.0, lo, 120000.0), b - hi_age: (120000.0, 120200.0, 119995.0, 120000.0),
          b: (120000.0, break_high, 119995.0, break_close)}
    for k in range(1, fail_at):
        ov[b + k] = (break_close, break_close + 5, break_close - 5, break_close)
    ov[b + fail_at] = (break_close if fail_at > 1 else break_close, 120215.0, fail_close - 5, fail_close)
    last = hold_until if hold_until is not None else b + fail_at + 60
    ov.update(flat(b + fail_at + 1, last, hold))
    return ov


def long_event(b, hi_age=40, lo_age=30, hi=120100.0, break_low=119770.0, break_close=119790.0, hold_until=None):
    """A down-sweep: swing high `hi` at b - hi_age, swing low 119800 at b - lo_age, break bar b (low below 119800 that
    closes at 119790, no failure yet), failure bar b + 1 (close 119810), then flat bars at 119810."""
    ov = {b - hi_age: (120000.0, hi, 119995.0, 120000.0), b - lo_age: (120000.0, 120005.0, 119800.0, 120000.0),
          b: (120000.0, 120005.0, break_low, break_close),
          b + 1: (break_close, 119815.0, 119785.0, 119810.0)}
    last = hold_until if hold_until is not None else b + 61
    ov.update(flat(b + 2, last, 119810.0))
    return ov


B = 100                                                      # a break bar at 10:40: window and event rules satisfied


def test_class_constants():
    s = WinStopSweepFailureFade
    assert mod.RULE_ID == "P-017"
    assert s.name.startswith("P-017") and s.timeframe_min == 1
    assert s.warmup >= 60 + 565
    assert s.rules.entry_end_before_close_min == 44 and s.rules.flatten_before_close_min == 5
    assert s.params == {
        "timeframe_min": 1, "level_lookback_bars": 60, "min_level_age_bars": 15, "min_range_frac": 0.002,
        "failure_window_bars": 5, "failure_close_ticks_inside": 1, "max_sweep_excursion_frac": 0.0025,
        "stop_ticks_beyond_sweep": 2, "min_stop_frac": 0.0012, "max_stop_frac": 0.004, "max_hold_bars": 30,
        "window_start_minute_of_day": 615, "min_minutes_to_close_at_signal": 45, "event_block_after_min": 30,
        "fomc_block_before_min": 15, "max_entries_per_day": 6}
    assert "symbol" not in vars(s)


def test_causal_and_matches_the_live_window():
    strategy = WinStopSweepFailureFade.on("WIN")()
    frame = synthetic_sessions(days=4)
    prepared = strategy.prepare(frame)
    assert (prepared["sw_side"] != 0).sum() >= 3          # the synthetic data really produce signals
    assert causality_problems(strategy, frame) == []
    assert window_parity_problems(strategy, frame, samples=60) == []
    ov = short_event(B, hold_until=B + 9)
    ov[B + 10] = (120190.0, 120190.0, 120040.0, 120045.0)
    hand = hand_frame(TARGET, {**ov, **long_event(300)})
    assert (strategy.prepare(hand)["sw_side"] != 0).sum() == 2
    assert causality_problems(strategy, hand) == []
    assert window_parity_problems(strategy, hand, samples=80) == []


def test_short_entry_after_an_up_sweep_with_the_stop_beyond_the_sweep_and_the_midpoint_target():
    ov = short_event(B, hold_until=B + 9)
    ov[B + 10] = (120190.0, 120190.0, 120040.0, 120045.0)             # closes below M = (120200 + 119900) / 2 = 120050
    ov[B + 11] = (120045.0, 120050.0, 120040.0, 120045.0)
    (t,) = trades_of(hand_frame(TARGET, ov)).trades
    # X = 120230, C_f = 120190: stop = ceil(max(120240, 120190 * 1.0012 = 120334.2)) = 120335
    assert (t.side, t.entry_price, t.stop_price, t.entry_reason) == ("short", 120190.0, 120335.0,
                                                                   "up_sweep_failure_short")
    assert hhmm(t.entry_time) == "10:42"                              # the open of the bar after the failure bar (B + 1)
    assert t.exit_reason == "target_midpoint" and hhmm(t.exit_time) == "10:51" and t.exit_price == 120045.0


def test_long_entry_after_a_down_sweep_with_the_stop_beyond_the_sweep():
    ov = long_event(B, hold_until=B + 9)
    ov[B + 10] = (119810.0, 119960.0, 119810.0, 119955.0)             # closes above M = (120100 + 119800) / 2 = 119950
    ov[B + 11] = (119955.0, 119960.0, 119950.0, 119955.0)
    (t,) = trades_of(hand_frame(TARGET, ov)).trades
    # X = 119770, C_f = 119810: stop = floor(min(119760, 119810 * 0.9988 = 119666.2)) = 119665
    assert (t.side, t.entry_price, t.stop_price, t.entry_reason) == ("long", 119810.0, 119665.0,
                                                                   "down_sweep_failure_long")
    assert hhmm(t.entry_time) == "10:42"
    assert t.exit_reason == "target_midpoint" and hhmm(t.exit_time) == "10:51" and t.exit_price == 119955.0


def test_stop_beyond_the_sweep_extreme_when_it_is_farther_than_the_minimum_stop():
    # X = 120400 (excursion 200 <= 0.25%), C_f = 120190: X + 2 ticks = 120410 > 120334.2 -> stop 120410
    (t,) = trades_of(hand_frame(TARGET, short_event(B, break_high=120400.0))).trades
    assert t.side == "short" and t.stop_price == 120410.0
    # the long side mirrors: X = 119600, C_f = 119810 -> min(119590, 119666.2) = 119590
    ov = long_event(B)
    ov[B] = (120000.0, 120005.0, 119600.0, 119790.0)
    (t,) = trades_of(hand_frame(TARGET, ov)).trades
    assert t.side == "long" and t.stop_price == 119590.0


def test_the_stop_is_hit_and_the_event_is_not_traded_again():
    ov = short_event(B)
    ov[B + 5] = (120190.0, 120340.0, 120190.0, 120300.0)               # reaches the stop 120335
    ov[B + 6] = (120300.0, 120305.0, 120180.0, 120185.0)               # closes below Lhi - 1 tick again: not a new event
    r = trades_of(hand_frame(TARGET, ov))
    (t,) = r.trades
    assert t.side == "short" and t.exit_reason == "stop_loss" and t.exit_price == 120335.0
    assert hhmm(t.exit_time) == "10:46"


def test_time_exit_at_the_open_of_the_30th_bar_after_the_entry_bar():
    # failure bar B + 1 = 10:41; entry bar B + 2 (10:42); decided at the close of B + 31, filled at the open of B + 32 = 11:12
    (t,) = trades_of(hand_frame(TARGET, short_event(B))).trades
    assert t.exit_reason == "time_exit_30_bars" and hhmm(t.entry_time) == "10:42" and hhmm(t.exit_time) == "11:12"
    assert t.exit_price == 120190.0
    # one bar earlier is not enough: the time exit is decided 30 bars after the failure bar
    (t,) = trades_of(hand_frame(TARGET, {**short_event(B), B + 32: (120190.0, 120195.0, 120185.0, 120190.0)})).trades
    assert hhmm(t.exit_time) == "11:12"


def test_the_failure_may_come_on_the_break_bar_itself_and_up_to_b_plus_4():
    def count(ov):
        return len(trades_of(hand_frame(TARGET, ov)).trades)

    (t,) = trades_of(hand_frame(TARGET, short_event(B, break_close=120190.0))).trades   # the break bar closes inside
    assert hhmm(t.entry_time) == "10:41"                                              # failure at b: fill at the open of b + 1
    assert count(short_event(B, fail_at=4)) == 1                                      # the failure bar is b + 4
    assert count(short_event(B, fail_at=5)) == 0                                      # b + 5 is too late


def test_the_failure_close_must_be_one_tick_inside_the_level():
    assert len(trades_of(hand_frame(TARGET, short_event(B, fail_close=120195.0, hold=120195.0))).trades) == 1   # Lhi - 1 tick
    assert trades_of(hand_frame(TARGET, short_event(B, fail_close=120200.0, hold=120200.0))).trades == []      # on the level
    # same for the long side (Llo + 1 tick = 119805)
    ov = long_event(B)
    ov[B + 1] = (119790.0, 119815.0, 119785.0, 119800.0)
    ov.update(flat(B + 2, B + 61, 119800.0))
    assert trades_of(hand_frame(TARGET, ov)).trades == []


def test_sweep_excursion_cap_and_stop_distance_cap():
    # excursion X - Lhi = 300 <= 0.25% of 120200 (300.5): a trade; 320: void
    assert len(trades_of(hand_frame(TARGET, short_event(B, break_high=120500.0))).trades) == 1
    assert trades_of(hand_frame(TARGET, short_event(B, break_high=120520.0))).trades == []
    # stop 120510 against a close of 120000 is 0.425% > 0.40%: skipped; against a close of 120190 it is fine
    skip = short_event(B, break_high=120500.0, fail_close=120000.0, hold=120000.0)
    assert trades_of(hand_frame(TARGET, skip)).trades == []
    ok = short_event(B, break_high=120400.0, fail_close=120000.0, hold=120000.0)    # stop 120410: 0.342%
    (t,) = trades_of(hand_frame(TARGET, ok)).trades
    assert t.stop_price == 120410.0


def test_the_range_must_be_at_least_0_20_percent():
    # Lhi = 120200: 0.20% = 240.4; the swing low 119960 gives R = 240 (no event), 119955 gives R = 245 (event)
    assert trades_of(hand_frame(TARGET, short_event(B, lo=119960.0))).trades == []
    assert len(trades_of(hand_frame(TARGET, short_event(B, lo=119955.0))).trades) == 1


def test_the_level_must_be_standing_for_15_bars_and_inside_the_60_bar_lookback():
    assert trades_of(hand_frame(TARGET, short_event(B, hi_age=14))).trades == []
    assert len(trades_of(hand_frame(TARGET, short_event(B, hi_age=15))).trades) == 1
    assert len(trades_of(hand_frame(TARGET, short_event(B, hi_age=59, lo_age=58))).trades) == 1
    assert len(trades_of(hand_frame(TARGET, short_event(B, hi_age=60, lo_age=40))).trades) == 1   # b-60 is the oldest bar
    assert trades_of(hand_frame(TARGET, short_event(B, hi_age=61, lo_age=40))).trades == []       # b-61 left the lookback


def test_the_levels_need_60_bars_of_the_same_session():
    # break bar at bar_in_day 59: no levels yet (and the previous session never counts)
    assert trades_of(hand_frame(TARGET, short_event(59, hi_age=30, lo_age=40))).trades == []
    ov = short_event(75 - 2)                                                  # failure bar 74 opens 10:14 (614): too early
    assert trades_of(hand_frame(TARGET, ov)).trades == []
    assert len(trades_of(hand_frame(TARGET, short_event(75 - 1))).trades) == 1  # failure bar 75 opens 10:15 (615)


def test_signal_window_ends_45_minutes_before_the_close():
    s = CAL.session(TARGET)
    n = int((s.close - s.open).total_seconds() // 60)
    last_ok = n - 46                                   # the bar whose close is 45 minutes before the close
    ok = trades_of(hand_frame(TARGET, short_event(last_ok - 1, hold_until=n - 1)))
    assert len(ok.trades) == 1
    assert trades_of(hand_frame(TARGET, short_event(last_ok, hold_until=n - 1))).trades == []


def test_same_bar_long_and_short_failures_cancel_and_a_lone_one_trades():
    both = {**short_event(B, hold_until=B + 6), **{B + 0: (120000.0, 120230.0, 119870.0, 120000.0)}}
    both[B - 40] = (120000.0, 120005.0, 119900.0, 120000.0)
    both[B + 1] = (120000.0, 120005.0, 119995.0, 120000.0)
    both.update(flat(B + 2, B + 61, 120000.0))
    assert trades_of(hand_frame(TARGET, both)).trades == []
    lone = dict(both)
    lone[B] = (120000.0, 120230.0, 119870.0, 119895.0)      # closes below Llo + 1 tick: only the up failure fires
    (t,) = trades_of(hand_frame(TARGET, lone)).trades
    assert t.side == "short" and t.stop_price == 120240.0 and hhmm(t.entry_time) == "10:41"


def test_a_break_while_a_position_is_open_is_ignored():
    ov = short_event(B)
    ov[B + 10] = (120190.0, 120195.0, 119890.0, 120190.0)     # a down-break with an instant failure, position still open
    r = trades_of(hand_frame(TARGET, ov))
    assert len(r.trades) == 1 and r.trades[0].side == "short"


def test_cpi_and_nfp_block_entries_for_30_minutes_after_the_release():
    # 2026-01-13: CPI 08:30 New York = 10:30 Sao Paulo. The failure bar's close is the minute that counts.
    cpi_day, nfp_day = date(2026, 1, 13), date(2026, 1, 9)
    for day in (cpi_day, nfp_day):
        assert CAL.is_trading_day(day)
        assert trades_of(hand_frame(day, short_event(101))).trades == []      # failure bar 10:41, close 10:42 (12 min)
        # failure bar opens 10:59 (k = 119), closes 11:00: exactly 30 minutes after the release -> blocked
        assert trades_of(hand_frame(day, short_event(118))).trades == []
        # failure bar opens 11:00, closes 11:01: 31 minutes -> allowed
        assert len(trades_of(hand_frame(day, short_event(119))).trades) == 1
    assert len(trades_of(hand_frame(TARGET, short_event(118))).trades) == 1


def test_fomc_blocks_from_15_minutes_before_the_release_and_30_minutes_after():
    fomc = date(2026, 1, 28)                 # 14:00 New York = 16:00 Sao Paulo
    assert CAL.is_trading_day(fomc)
    assert len(trades_of(hand_frame(fomc, short_event(402))).trades) == 1            # failure bar opens 15:43, closes 15:44
    assert trades_of(hand_frame(fomc, short_event(403))).trades == []                # closes 15:45 = release - 15 min
    assert trades_of(hand_frame(fomc, short_event(448))).trades == []                # closes 16:30 = release + 30 min
    assert trades_of(hand_frame(fomc, short_event(449))).trades == []                # "from 15 minutes before ... on": all day


def test_at_most_6_entries_a_day_enforced_by_the_rule():
    def block(s):                            # 66 bars from s: swing low s+5, swing high s+12, break s+60, failure s+61,
        ov = {s + 5: (120000.0, 120005.0, 119900.0, 120000.0), s + 12: (120000.0, 120200.0, 119995.0, 120000.0),
              s + 60: (120000.0, 120230.0, 119995.0, 120210.0),
              s + 61: (120210.0, 120215.0, 120185.0, 120190.0),
              s + 62: (120190.0, 120195.0, 120185.0, 120190.0),
              s + 63: (120190.0, 120190.0, 120040.0, 120045.0)}       # entry bar s+62; target close at s+63; exit open s+64
        return ov

    ov = {}
    for j in range(7):
        ov.update(block(15 + 66 * j))
    strategy = WinStopSweepFailureFade.on("WIN")()
    prepared = strategy.prepare(hand_frame(TARGET, ov))
    assert (prepared["sw_side"] != 0).sum() == 6
    r = trades_of(hand_frame(TARGET, ov))
    assert len(r.trades) == 6
    assert all(t.side == "short" and t.exit_reason == "target_midpoint" for t in r.trades)
    assert [hhmm(t.entry_time) for t in r.trades][0] == hhmm(
        pd.Timestamp((CAL.session(TARGET).open + timedelta(minutes=15 + 62)).astimezone(UTC)))
    # with six blocks only, all six are taken
    ov6 = {}
    for j in range(6):
        ov6.update(block(15 + 66 * j))
    assert len(trades_of(hand_frame(TARGET, ov6)).trades) == 6


def test_synthetic_sessions_trade_and_never_hold_overnight():
    frames = [synthetic_sessions(days=5), hand_frame(TARGET, short_event(B))]
    for frame in frames:
        r = run(frame, WinStopSweepFailureFade.on("WIN")(), market("WIN").cost("base"), BacktestConfig())
        assert r.trades
        assert r.positions_held_overnight == 0
        per_day = pd.Series([t.entry_time.tz_convert(market("WIN").zone).date() for t in r.trades]).value_counts()
        assert max(per_day) <= 6
