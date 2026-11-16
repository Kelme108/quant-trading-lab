"""P-014 WinVolumeShockReversal on SYNTHETIC WIN session 5-minute bars (09:00-18:25 Sao Paulo, 113 bars a day): class
constants, causality, live-window parity, hand-built days (long, short, stops, exits, filters, 4-entry cap) and no
overnight position."""

import random
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import pytest

from b3.backtest import BacktestConfig, run
from b3.calendar import B3SessionCalendar
from b3.checks import causality_problems, window_parity_problems
from b3.markets import market
from b3.proxy_rules import p014_win_volume_shock_reversal as mod
from b3.proxy_rules.p014_win_volume_shock_reversal import WinVolumeShockReversal

UTC = timezone.utc
BARS = 113                     # 09:00-18:25 in 5-minute bars
PRIOR_DAYS = 25                # 25 * 113 = 2825 bars > warmup (2500)
CAL = B3SessionCalendar("WIN")
DEFAULT = (120000.0, 120010.0, 119995.0, 120005.0, 100.0)       # |r| = 5 / 120000, volume 100
COLS = ["time", "open", "high", "low", "close", "volume"]


def trading_days_before(day, n):
    out, d = [], day
    while len(out) < n:
        d -= timedelta(days=1)
        if CAL.is_trading_day(d):
            out.append(d)
    return sorted(out)


def session_rows(day, overrides=None, skip=()):
    """The session's 113 bars from 09:00; `overrides` = {bar index: (o, h, l, c, v)}; `skip` = bar indices left out."""
    m = market("WIN")
    t0 = datetime.combine(day, m.open, m.zone)
    overrides = overrides or {}
    return [(pd.Timestamp((t0 + timedelta(minutes=5 * k)).astimezone(UTC)),) + tuple(overrides.get(k, DEFAULT))
            for k in range(BARS) if k not in skip]


def hand_frame(target_day, overrides=None, prior=PRIOR_DAYS, skip_in=0, skip=(24,)):
    """`prior` identical sessions of DEFAULT bars, then the target session with `overrides`. In the first `skip_in` prior
    sessions bar 24 (11:00) is missing."""
    rows = []
    for i, d in enumerate(trading_days_before(target_day, prior)):
        rows += session_rows(d, skip=skip if i < skip_in else ())
    rows += session_rows(target_day, overrides)
    return pd.DataFrame(rows, columns=COLS)


def synthetic_sessions(days=45, seed=3, start=120000.0, step=5.0):
    """Random sessions with heavy-tailed volume so that signals occur; only trading days."""
    m = market("WIN")
    rng = random.Random(seed)
    d, rows, prev = date(2026, 1, 5), [], start
    while len({r[0].date() for r in rows}) < days:
        if CAL.is_trading_day(d):
            t = datetime.combine(d, m.open, m.zone)
            end = datetime.combine(d, m.close, m.zone)
            while t + timedelta(minutes=5) <= end:
                o = prev + step * rng.randint(-3, 3)
                c = o + step * rng.randint(-6, 6)
                v = 600.0 if rng.random() < 0.1 else float(rng.randint(80, 120))
                rows.append((t, o, max(o, c) + step * rng.randint(0, 3), min(o, c) - step * rng.randint(0, 3), c, v))
                prev, t = c, t + timedelta(minutes=5)
        d += timedelta(days=1)
    return pd.DataFrame([(pd.Timestamp(r[0].astimezone(UTC)),) + r[1:] for r in rows], columns=COLS)


def trades_of(frame):
    return run(frame, WinVolumeShockReversal.on("WIN")(), market("WIN").cost("optimistic"), BacktestConfig())


def hhmm(ts):
    return ts.tz_convert(market("WIN").zone).strftime("%H:%M")


TARGET = date(2026, 5, 13)                                   # an ordinary session: no FOMC, 25 trading days of history
DOWN = (120100.0, 120100.0, 119900.0, 119900.0, 250.0)       # O 120100 -> C 119900, range 200, volume 2.5x
UP = (119900.0, 120100.0, 119900.0, 120100.0, 250.0)
AFTER_DOWN = (119900.0, 119910.0, 119895.0, 119905.0, 100.0)   # the entry bar: no retracement, no stop
AFTER_UP = (120100.0, 120105.0, 120090.0, 120095.0, 100.0)


def test_class_constants():
    s = WinVolumeShockReversal
    assert mod.RULE_ID == "P-014"
    assert s.name.startswith("P-014") and s.timeframe_min == 5
    assert s.warmup >= 20 * BARS + BARS
    assert s.rules.flatten_before_close_min == 5 and s.rules.entry_end_before_close_min == 44
    assert s.params == {
        "timeframe_min": 5, "baseline_sessions": 20, "min_baseline_sessions": 15, "volume_mult": 2.0,
        "abs_return_mult": 1.5, "window_start_minute_of_day": 660, "min_minutes_to_close_at_signal": 45,
        "stop_range_mult": 1.0, "stop_min_frac": 0.0015, "stop_max_frac": 0.006, "max_hold_bars": 6,
        "skip_fomc_days": 1, "max_entries_per_day": 4}
    assert "symbol" not in vars(s)


def test_causal_and_matches_the_live_window():
    strategy = WinVolumeShockReversal.on("WIN")()
    frame = synthetic_sessions(days=45)
    assert causality_problems(strategy, frame) == []
    assert window_parity_problems(strategy, frame, samples=60) == []
    prepared = strategy.prepare(frame)
    assert (prepared["vs_side"] != 0).sum() > 20          # the synthetic data really produce signals
    # a frame with entry days, exits and a time exit inside the window
    hand = hand_frame(TARGET, {24: DOWN, 25: AFTER_DOWN, 40: UP, 41: AFTER_UP})
    assert causality_problems(strategy, hand) == []
    assert window_parity_problems(strategy, hand, samples=80) == []


def test_long_entry_after_a_high_volume_down_bar_with_the_range_stop():
    (t,) = trades_of(hand_frame(TARGET, {24: DOWN, 25: AFTER_DOWN})).trades
    # D = min(max(200, 0.0015 * 119900 = 179.85), 0.006 * 119900) = 200 -> stop = 119900 - 200
    assert (t.side, t.entry_price, t.stop_price, t.entry_reason) == ("long", 119900.0, 119700.0,
                                                                   "fade_high_volume_down_bar")
    assert hhmm(t.entry_time) == "11:05"                     # the open of bar 25, after the 11:00 bar closes
    # time exit: decided at the close of the bar 6 after the signal bar (30), filled at the open of bar 31 = 11:35
    assert t.exit_reason == "time_exit_30min" and hhmm(t.exit_time) == "11:35" and t.exit_price == 120000.0


def test_short_entry_after_a_high_volume_up_bar_with_the_range_stop():
    (t,) = trades_of(hand_frame(TARGET, {24: UP, 25: AFTER_UP})).trades
    assert (t.side, t.entry_price, t.stop_price, t.entry_reason) == ("short", 120100.0, 120300.0,
                                                                   "fade_high_volume_up_bar")
    assert t.exit_reason == "time_exit_30min" and hhmm(t.exit_time) == "11:35"


def test_stop_uses_the_minimum_and_maximum_fraction_and_rounds_away_from_the_price():
    # range 100 < 0.0015 * C: D = 0.0015 * 119900 = 179.85 -> long stop floor(119720.15) = 119720
    (t,) = trades_of(hand_frame(TARGET, {24: (120000.0, 120000.0, 119900.0, 119900.0, 250.0),
                                         25: AFTER_DOWN})).trades
    assert t.side == "long" and t.stop_price == 119720.0
    # short: C 120100, D = 180.15 -> ceil(120280.15) = 120285
    (t,) = trades_of(hand_frame(TARGET, {24: (120000.0, 120100.0, 120000.0, 120100.0, 250.0),
                                         25: AFTER_UP})).trades
    assert t.side == "short" and t.stop_price == 120285.0
    # range 1000 > 0.006 * C: D = 0.006 * 119000 = 714 -> long stop floor(118286) = 118285
    (t,) = trades_of(hand_frame(TARGET, {24: (119900.0, 119950.0, 118950.0, 119000.0, 250.0),
                                         25: (119000.0, 119010.0, 118990.0, 119005.0, 100.0)})).trades
    assert t.side == "long" and t.stop_price == 118285.0


def test_retracement_exit_at_the_next_open():
    # bar 27 closes at the signal bar's open (120100): decided at its close, filled at the open of bar 28 = 11:20
    ov = {24: DOWN, 25: AFTER_DOWN, 27: (119950.0, 120100.0, 119950.0, 120100.0, 100.0)}
    (t,) = trades_of(hand_frame(TARGET, ov)).trades
    assert t.side == "long" and t.exit_reason == "retracement" and hhmm(t.exit_time) == "11:20"
    assert t.exit_price == 120000.0
    # the entry bar itself may retrace: close of bar 25 at the signal open -> exit at the open of bar 26 = 11:10
    (t,) = trades_of(hand_frame(TARGET, {24: DOWN, 25: (119900.0, 120100.0, 119900.0, 120100.0, 100.0)})).trades
    assert t.exit_reason == "retracement" and hhmm(t.exit_time) == "11:10"
    # a short retraces when a close is at or below the signal bar's open
    (t,) = trades_of(hand_frame(TARGET, {24: UP, 25: AFTER_UP,
                                         26: (120100.0, 120100.0, 119900.0, 119900.0, 100.0)})).trades
    assert t.side == "short" and t.exit_reason == "retracement" and hhmm(t.exit_time) == "11:15"


def test_stop_is_hit_when_the_move_extends():
    ov = {24: DOWN, 25: AFTER_DOWN, 26: (119900.0, 119905.0, 119650.0, 119700.0, 100.0)}
    (t,) = trades_of(hand_frame(TARGET, ov)).trades
    assert t.side == "long" and t.exit_reason == "stop_loss" and t.stop_price == 119700.0
    assert t.exit_price == 119700.0 and hhmm(t.exit_time) == "11:15"


def test_thresholds_on_volume_and_on_the_body():
    # volume just below 2 x VBAR (200)
    assert trades_of(hand_frame(TARGET, {24: (120100.0, 120100.0, 119900.0, 119900.0, 199.0)})).trades == []
    assert len(trades_of(hand_frame(TARGET, {24: (120100.0, 120100.0, 119900.0, 119900.0, 200.0)})).trades) == 1
    # body equal to the slot's mean |r| (< 1.5 x) with a big volume: no signal; 2 x ABAR: signal
    small = (120000.0, 120005.0, 119995.0, 119995.0, 500.0)
    assert trades_of(hand_frame(TARGET, {24: small})).trades == []
    ok = (120000.0, 120005.0, 119990.0, 119990.0, 500.0)
    assert len(trades_of(hand_frame(TARGET, {24: ok})).trades) == 1
    # a doji never signals
    assert trades_of(hand_frame(TARGET, {24: (120000.0, 120100.0, 119900.0, 120000.0, 900.0)})).trades == []


def test_signal_window_starts_at_1100_and_ends_45_minutes_before_the_close():
    assert trades_of(hand_frame(TARGET, {23: DOWN})).trades == []                         # bar opens 10:55
    assert len(trades_of(hand_frame(TARGET, {24: DOWN})).trades) == 1                     # bar opens 11:00
    assert len(trades_of(hand_frame(TARGET, {103: DOWN})).trades) == 1                    # opens 17:35, closes 17:40
    assert trades_of(hand_frame(TARGET, {104: DOWN})).trades == []                        # opens 17:40, closes 17:45
    (t,) = trades_of(hand_frame(TARGET, {103: DOWN})).trades
    assert hhmm(t.entry_time) == "17:40"
    assert t.exit_reason in {"time_exit_30min", "retracement", "end_of_day_flatten"}


def test_no_trade_on_an_fomc_day():
    fomc = date(2026, 4, 29)
    assert CAL.is_trading_day(fomc)
    assert trades_of(hand_frame(fomc, {24: DOWN, 25: AFTER_DOWN})).trades == []
    assert len(trades_of(hand_frame(TARGET, {24: DOWN, 25: AFTER_DOWN})).trades) == 1


def test_baseline_needs_15_of_the_previous_20_sessions_with_the_slot():
    strategy = WinVolumeShockReversal.on("WIN")()

    def vbar_at_signal_slot(frame):
        prepared = strategy.prepare(frame)
        row = prepared[(prepared["local_date"] == TARGET) & (prepared["minute_of_day"] == 660)].iloc[0]
        return row["vbar"], row["abar"]

    v, a = vbar_at_signal_slot(hand_frame(TARGET, {24: DOWN}, prior=15))
    assert v == 100.0 and a == pytest.approx(5.0 / 120000.0)
    v, a = vbar_at_signal_slot(hand_frame(TARGET, {24: DOWN}, prior=14))
    assert pd.isna(v) and pd.isna(a)
    # 20 earlier sessions, the 11:00 bar missing in 5 of them -> 15 left -> baseline exists; missing in 6 -> none
    assert vbar_at_signal_slot(hand_frame(TARGET, {24: DOWN}, prior=20, skip_in=5))[0] == 100.0
    assert pd.isna(vbar_at_signal_slot(hand_frame(TARGET, {24: DOWN}, prior=20, skip_in=6))[0])
    # only the last 20 sessions count: a very old session with another volume is ignored
    rows = session_rows(trading_days_before(TARGET, 21)[0], {24: (120000.0, 120010.0, 119995.0, 120005.0, 9999.0)})
    frame = pd.concat([pd.DataFrame(rows, columns=COLS), hand_frame(TARGET, {24: DOWN}, prior=20)], ignore_index=True)
    assert vbar_at_signal_slot(frame)[0] == 100.0


def test_baseline_is_by_time_of_day_and_excludes_today():
    strategy = WinVolumeShockReversal.on("WIN")()
    # volume 300 at 11:00 in every earlier session: a 250-volume bar is no shock there (< 600)
    rows = []
    for d in trading_days_before(TARGET, PRIOR_DAYS):
        rows += session_rows(d, {24: (120000.0, 120010.0, 119995.0, 120005.0, 300.0)})
    rows += session_rows(TARGET, {24: DOWN})
    assert trades_of(pd.DataFrame(rows, columns=COLS)).trades == []
    prepared = strategy.prepare(pd.DataFrame(rows, columns=COLS))
    today = prepared[(prepared["local_date"] == TARGET) & (prepared["minute_of_day"] == 660)].iloc[0]
    assert today["vbar"] == 300.0                             # today's own 250 is not in it


def test_max_four_entries_a_day_and_signals_only_after_the_exit_bar():
    def shock(k):                                              # shock at k, entry bar k+1, retracement close at k+2
        return {k: DOWN, k + 1: AFTER_DOWN, k + 2: (119950.0, 120100.0, 119950.0, 120100.0, 100.0)}

    ov = {}
    for k in (24, 34, 44, 54, 64):                             # five shocks, each exits at the open of k+3
        ov.update(shock(k))
    r = trades_of(hand_frame(TARGET, ov))
    assert len(r.trades) == 4
    assert [hhmm(t.entry_time) for t in r.trades] == ["11:05", "11:55", "12:45", "13:35"]
    assert all(t.exit_reason == "retracement" for t in r.trades)
    # a shock on the exit bar (k+3, whose open is the exit fill) is not counted; one on k+4 is
    on_exit_bar = {**shock(24), 27: DOWN}
    assert len(trades_of(hand_frame(TARGET, on_exit_bar)).trades) == 1
    after_exit_bar = {**shock(24), 28: DOWN}
    assert len(trades_of(hand_frame(TARGET, after_exit_bar)).trades) == 2
    # a shock while the position is open is ignored (and does not add an entry)
    while_open = {24: DOWN, 25: AFTER_DOWN, 26: DOWN, 27: AFTER_DOWN}
    assert len(trades_of(hand_frame(TARGET, while_open)).trades) == 1


def test_synthetic_sessions_trade_and_never_hold_overnight():
    frames = [synthetic_sessions(days=45),
              hand_frame(TARGET, {103: DOWN, 104: AFTER_DOWN})]
    for frame in frames:
        r = run(frame, WinVolumeShockReversal.on("WIN")(), market("WIN").cost("base"), BacktestConfig())
        assert r.trades
        assert r.positions_held_overnight == 0
        assert max(pd.Series([t.entry_time.tz_convert(market("WIN").zone).date() for t in r.trades]).value_counts()) <= 4
