"""P-020 WinThinVolumeMoveFade on SYNTHETIC WIN session 5-minute bars (09:00 open, Sao Paulo time): class constants,
causality, live-window parity, hand-built days (long, short, stops, exits, thresholds, window, events, episodes, 6-entry
cap) and no overnight position. Nothing here is market data.

Hand-built sessions alternate the close between 120000 (even bar index k) and 120100 (odd k), so |R| = |C_t / C_(t-3) - 1|
is ~8.33e-4 on every bar and S15 ~ 8.33e-4: the trigger is ~1.2495e-3 (a 3-bar move of ~150 points). A shock at bar t sets
C_t = C_(t-3) -/+ 300 (|R| = 2.5e-3). Volume is 100 on every bar (rv = 1.0 exactly); `calm(t)` puts 200 on the bars after a
shock so that the mean-reversion move back (a 3-bar move of the opposite sign) is not itself a signal."""

import random
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import pytest

from b3.backtest import BacktestConfig, run
from b3.calendar import B3SessionCalendar
from b3.checks import causality_problems, window_parity_problems
from b3.markets import market
from b3.proxy_rules import p020_win_thin_volume_move_fade as mod
from b3.proxy_rules.p020_win_thin_volume_move_fade import WinThinVolumeMoveFade

UTC = timezone.utc
CAL = B3SessionCalendar("WIN")
COLS = ["time", "open", "high", "low", "close", "volume"]
PRIOR_DAYS = 25
TARGET = date(2026, 5, 13)           # ordinary session: no FOMC, CPI or NFP that day
FOMC_DAY = date(2026, 4, 29)         # statement 14:00 New York (EDT) = 15:00 Sao Paulo
CPI_DAY = date(2026, 2, 13)          # 08:30 New York (EST) = 10:30 Sao Paulo
NFP_DAY = date(2026, 2, 11)


def base_close(k):
    return 120000.0 if k % 2 == 0 else 120100.0


def nbars(day):
    s = CAL.session(day)
    return int((s.close - s.open).total_seconds() // 300)


def trading_days_before(day, n):
    out, d = [], day
    while len(out) < n:
        d -= timedelta(days=1)
        if CAL.is_trading_day(d):
            out.append(d)
    return sorted(out)


def session_rows(day, closes=None, vols=None, lows=None, highs=None, skip=()):
    """The session's bars from 09:00: close = base pattern unless in `closes`; open = previous close; volume 100 unless in
    `vols`; high/low = body +/- 5 unless in `highs`/`lows`; bar indices in `skip` are left out."""
    m = market("WIN")
    closes, vols, lows, highs = closes or {}, vols or {}, lows or {}, highs or {}
    t0 = datetime.combine(day, m.open, m.zone)
    rows, prev = [], None
    for k in range(nbars(day)):
        c = closes.get(k, base_close(k))
        o = c if prev is None else prev
        prev = c
        if k in skip:
            continue
        h = highs.get(k, max(o, c) + 5.0)
        lo = lows.get(k, min(o, c) - 5.0)
        rows.append((pd.Timestamp((t0 + timedelta(minutes=5 * k)).astimezone(UTC)), o, h, lo, c, vols.get(k, 100.0)))
    return rows


def hand_frame(target_day, closes=None, vols=None, lows=None, highs=None, prior=PRIOR_DAYS, skip_in=0, skip=(),
               prior_closes=None, prior_vols=None):
    """`prior` plain sessions (optionally with `prior_closes`/`prior_vols`; bar `skip` missing in the first `skip_in`),
    then the target session with the overrides."""
    rows = []
    for i, d in enumerate(trading_days_before(target_day, prior)):
        rows += session_rows(d, prior_closes, prior_vols, skip=skip if i < skip_in else ())
    rows += session_rows(target_day, closes, vols, lows, highs)
    return pd.DataFrame(rows, columns=COLS)


def calm(t, n=12, v=200.0):
    return {t + j: v for j in range(1, n + 1)}


def drop(t):
    return {t: base_close(t - 3) - 300.0}


def rally(t):
    return {t: base_close(t - 3) + 300.0}


def synthetic_sessions(days=45, seed=3, start=120000.0, step=5.0):
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
                rows.append((t, o, max(o, c) + step * rng.randint(0, 3), min(o, c) - step * rng.randint(0, 3), c,
                             float(rng.randint(50, 500))))
                prev, t = c, t + timedelta(minutes=5)
        d += timedelta(days=1)
    return pd.DataFrame([(pd.Timestamp(r[0].astimezone(UTC)),) + r[1:] for r in rows], columns=COLS)


def trades_of(frame, scenario="optimistic"):
    return run(frame, WinThinVolumeMoveFade.on("WIN")(), market("WIN").cost(scenario), BacktestConfig())


def hhmm(ts):
    return ts.tz_convert(market("WIN").zone).strftime("%H:%M")


def at(k):
    return f"{(540 + 5 * k) // 60:02d}:{(540 + 5 * k) % 60:02d}"


def prepared_today(frame, day=TARGET):
    p = WinThinVolumeMoveFade.on("WIN")().prepare(frame)
    return p[p["local_date"] == day].reset_index(drop=True)


def test_class_constants():
    s = WinThinVolumeMoveFade
    assert mod.RULE_ID == "P-020"
    assert s.name.startswith("P-020") and s.timeframe_min == 5
    assert s.warmup >= 20 * 113 + 113
    assert s.rules.entry_start_after_open_min == 5 and s.rules.entry_end_before_close_min == 44
    assert s.rules.flatten_before_close_min == 5
    assert s.params == {
        "timeframe_min": 5, "move_lookback_bars": 3, "scale_lookback_sessions": 20, "volume_baseline_sessions": 20,
        "min_volume_baseline_sessions": 15, "move_mult": 1.5, "max_relative_volume": 1.0,
        "window_start_minute_of_day": 615, "min_minutes_to_close_at_signal": 45, "stop_min_frac": 0.002,
        "stop_max_frac": 0.005, "stop_move_mult": 1.0, "target_retrace_frac": 0.5, "max_hold_bars": 6,
        "event_block_after_min": 30, "fomc_block_before_min": 15, "max_entries_per_day": 6}
    assert "symbol" not in vars(s)
    assert nbars(TARGET) == 113


def test_causal_and_matches_the_live_window():
    strategy = WinThinVolumeMoveFade.on("WIN")()
    frame = synthetic_sessions(days=45)
    assert causality_problems(strategy, frame) == []
    assert window_parity_problems(strategy, frame, samples=60) == []
    assert (strategy.prepare(frame)["tv_side"] != 0).sum() > 20          # the synthetic data really produce signals
    hand = hand_frame(TARGET, {**drop(30), **rally(45)}, vols=calm(30, 10))
    assert causality_problems(strategy, hand) == []
    assert window_parity_problems(strategy, hand, samples=80) == []


def test_scale_s15_is_the_pooled_mean_of_the_last_20_sessions_after_1015_and_ignores_older_ones():
    days = trading_days_before(TARGET, PRIOR_DAYS)[-20:]
    vals = [abs(base_close(k) / base_close(k - 3) - 1) for d in days for k in range(15, nbars(d))]
    expected = sum(vals) / len(vals)
    wild_early = {5: 125000.0, 9: 90000.0}                       # before 10:15: not in S15
    frame = hand_frame(TARGET, prior_closes=wild_early)
    s15 = prepared_today(frame)["tv_s15"]
    assert s15.iloc[0] == pytest.approx(expected, rel=1e-9) and s15.nunique() == 1
    assert 1.2e-3 < 1.5 * expected < 1.3e-3
    # a 21st (older) session with absurd closes is outside the 20 sessions
    old = trading_days_before(TARGET, 21)[0]
    rows = session_rows(old, {k: 90000.0 + 3000.0 * (k % 7) for k in range(3, 113)})
    frame = pd.concat([pd.DataFrame(rows, columns=COLS), hand_frame(TARGET, prior=20, prior_closes=wild_early)],
                      ignore_index=True)
    assert prepared_today(frame)["tv_s15"].iloc[0] == pytest.approx(expected, rel=1e-9)
    # the first bars of today and the days that are in the 20 sessions only
    assert prepared_today(hand_frame(TARGET))["tv_ret"].iloc[:3].isna().all()


def test_no_signal_before_20_sessions_exist():
    # (the backtester itself decides only after `warmup` bars, so the signal columns are read here)
    ov = dict(closes=drop(30), vols=calm(30))
    p20 = prepared_today(hand_frame(TARGET, prior=20, **ov))
    assert p20.loc[30, "tv_side"] == 1 and (p20["tv_side"] != 0).sum() == 1
    p19 = prepared_today(hand_frame(TARGET, prior=19, **ov))
    assert (p19["tv_side"] == 0).all() and p19["tv_s15"].isna().all()
    assert not p20["tv_s15"].isna().any()


def test_long_entry_after_a_thin_drop_with_the_move_stop_and_the_half_retrace_target():
    (t,) = trades_of(hand_frame(TARGET, drop(30), calm(30))).trades
    # R_30 = 119800 / 120100 - 1 = -2.5e-3; D = min(max(300, 0.002 * 119800 = 239.6), 599) = 300 -> stop 119500
    assert (t.side, t.entry_price, t.stop_price, t.entry_reason) == ("long", 119800.0, 119500.0, "fade_thin_volume_drop")
    assert hhmm(t.entry_time) == at(31) == "11:35"                # the open of the bar after the signal bar
    # target M = (119800 + 120100) / 2 = 119950: the entry bar closes at 120100 -> exit at the open of bar 32
    assert t.exit_reason == "target_half_retrace" and hhmm(t.exit_time) == at(32) and t.exit_price == 120100.0


def test_short_entry_after_a_thin_rally_with_the_move_stop_and_the_half_retrace_target():
    (t,) = trades_of(hand_frame(TARGET, rally(31), calm(31))).trades
    # R_31 = 120300 / 120000 - 1; D = min(max(300, 240.6), 601.5) = 300 -> stop ceil(120600)
    assert (t.side, t.entry_price, t.stop_price, t.entry_reason) == ("short", 120300.0, 120600.0,
                                                                   "fade_thin_volume_rally")
    assert hhmm(t.entry_time) == at(32)
    assert t.exit_reason == "target_half_retrace" and hhmm(t.exit_time) == at(33) and t.exit_price == 120000.0


@pytest.mark.parametrize("closes, side, stop", [
    ({30: 119900.0}, "long", 119660.0),      # |dC| 200 < 0.002 * C: D = 239.8 -> floor(119660.2)
    ({30: 119300.0}, "long", 118700.0),      # |dC| 800 > 0.005 * C: D = 596.5 -> floor(118703.5)
    ({31: 120200.0}, "short", 120445.0),     # D = 0.002 * 120200 = 240.4 -> ceil(120440.4)
    ({31: 120800.0}, "short", 121405.0),     # D = 0.005 * 120800 = 604 -> ceil(121404)
])
def test_stop_distance_is_clamped_and_rounded_away_from_the_price(closes, side, stop):
    t0 = 30 if side == "long" else 31
    (t,) = trades_of(hand_frame(TARGET, closes, calm(t0))).trades
    assert t.side == side and t.stop_price == stop
    assert (t.stop_price < t.entry_price) if side == "long" else (t.stop_price > t.entry_price)


FLAT_AFTER = {k: 119800.0 for k in range(30, 113)}        # the drop at 30 and then no move at all


def test_time_exit_at_the_open_of_the_sixth_bar_after_the_entry_bar():
    (t,) = trades_of(hand_frame(TARGET, FLAT_AFTER, calm(30))).trades
    assert t.side == "long" and hhmm(t.entry_time) == at(31)
    # decided at the close of bar 36 (signal bar + 6), filled at the open of bar 37 = the 6th bar after the entry bar 31
    assert t.exit_reason == "time_exit_30min" and hhmm(t.exit_time) == at(37) == "12:05" and t.exit_price == 119800.0


def test_stop_exit_and_the_stop_wins_when_one_bar_hits_both_stop_and_target():
    (t,) = trades_of(hand_frame(TARGET, FLAT_AFTER, calm(30), lows={32: 119490.0})).trades
    assert t.exit_reason == "stop_loss" and t.stop_price == 119500.0 and t.exit_price == 119500.0
    # bar 32 also closes at 120000 >= M = 119950, but its low reached the stop first
    closes = {**FLAT_AFTER, 32: 120000.0}
    (t,) = trades_of(hand_frame(TARGET, closes, calm(30), lows={32: 119490.0})).trades
    assert t.exit_reason == "stop_loss" and t.exit_price == 119500.0
    # a short: the stop is above
    closes = {k: 120300.0 for k in range(31, 113)}
    (t,) = trades_of(hand_frame(TARGET, closes, calm(31), highs={33: 120610.0})).trades
    assert t.side == "short" and t.exit_reason == "stop_loss" and t.exit_price == 120600.0


def test_target_exit_when_a_later_bar_closes_back_at_half_the_move():
    # bars 31..33 stay at 119800 (below M = 119950); bar 34 closes at 119950 = M -> exit at the open of bar 35
    closes = {**{k: 119800.0 for k in range(30, 34)}, 34: 119950.0, **{k: 119950.0 for k in range(35, 113)}}
    (t,) = trades_of(hand_frame(TARGET, closes, calm(30))).trades
    assert t.exit_reason == "target_half_retrace" and hhmm(t.exit_time) == at(35) and t.exit_price == 119950.0
    # one tick lower: no target; the time exit comes instead
    closes[34] = 119945.0
    closes.update({k: 119945.0 for k in range(35, 113)})
    (t,) = trades_of(hand_frame(TARGET, closes, calm(30))).trades
    assert t.exit_reason == "time_exit_30min"


def test_move_threshold_is_1p5_times_s15():
    assert 1.2495e-3 > abs(119950.0 / 120100.0 - 1) and abs(119940.0 / 120100.0 - 1) > 1.2495e-3
    assert trades_of(hand_frame(TARGET, {30: 119980.0}, calm(30))).trades == []       # |R| 1.0e-3
    assert trades_of(hand_frame(TARGET, {30: 119950.0}, calm(30))).trades == []       # 150 points: 1.2490e-3 < 1.2495e-3
    assert len(trades_of(hand_frame(TARGET, {30: 119940.0}, calm(30))).trades) == 1   # 160 points
    assert trades_of(hand_frame(TARGET, {31: 120140.0}, calm(31))).trades == []       # 140 points: 1.1667e-3
    assert len(trades_of(hand_frame(TARGET, {31: 120160.0}, calm(31))).trades) == 1


def test_relative_volume_must_be_at_most_one():
    drop30 = drop(30)
    assert len(trades_of(hand_frame(TARGET, drop30)).trades) >= 1                                  # rv = 300 / 300 = 1.0
    assert len(trades_of(hand_frame(TARGET, drop30, {28: 101.0, 29: 99.0, **calm(30)})).trades) == 1   # sum still 300
    assert trades_of(hand_frame(TARGET, drop30, {30: 101.0, **calm(30)})).trades == []             # 301 / 300
    assert len(trades_of(hand_frame(TARGET, drop30, {28: 50.0, 29: 50.0, 30: 50.0, **calm(30)})).trades) == 1
    assert trades_of(hand_frame(TARGET, drop30, {28: 100.0, 29: 100.0, 30: 250.0, **calm(30)})).trades == []


def test_volume_baseline_is_by_slot_over_20_sessions_and_excludes_today():
    heavy = {28: 300.0, 29: 300.0, 30: 300.0}
    prior_vols = dict(prior_vols=heavy)
    # baselines 300 + 300 + 300: today's 100 + 100 + 100 is thin, 300 x 3 is exactly normal, one more contract is not
    assert len(trades_of(hand_frame(TARGET, drop(30), {**calm(30)}, **prior_vols)).trades) == 1
    assert len(trades_of(hand_frame(TARGET, drop(30), {28: 300.0, 29: 300.0, 30: 300.0, **calm(30)}, **prior_vols)).trades) == 1
    assert trades_of(hand_frame(TARGET, drop(30), {28: 300.0, 29: 300.0, 30: 301.0, **calm(30)}, **prior_vols)).trades == []
    p = prepared_today(hand_frame(TARGET, drop(30), {28: 300.0, 29: 300.0, 30: 301.0}, **prior_vols))
    assert p.loc[30, "tv_vbar"] == 300.0                           # today's own volume is not in its baseline
    assert p.loc[30, "tv_rv"] == pytest.approx(901.0 / 900.0)
    # a different baseline in one slot: 50 + 100 + 100 = 250 < 300 -> rv = 1.2 -> no trade
    assert trades_of(hand_frame(TARGET, drop(30), calm(30), prior_vols={28: 50.0})).trades == []


def test_volume_baseline_needs_15_of_the_20_previous_sessions_with_the_slot():
    # bar 28 (the slot of t-2) is missing in the oldest 5 or 6 of the 20 previous sessions
    ok = hand_frame(TARGET, drop(30), calm(30), prior=20, skip_in=5, skip=(28,))
    assert prepared_today(ok).loc[30, "tv_side"] == 1 and prepared_today(ok).loc[30, "tv_vbar"] == 100.0
    bad = hand_frame(TARGET, drop(30), calm(30), prior=20, skip_in=6, skip=(28,))
    assert (prepared_today(bad)["tv_side"] == 0).all()
    assert pd.isna(prepared_today(bad).loc[28, "tv_vbar"]) and not pd.isna(prepared_today(bad).loc[30, "tv_vbar"])


def test_signal_window_starts_at_1015_and_ends_45_minutes_before_the_close():
    assert trades_of(hand_frame(TARGET, {14: 119800.0}, calm(14))).trades == []          # bar opens 10:10
    (t,) = trades_of(hand_frame(TARGET, {15: 119700.0}, calm(15))).trades               # bar opens 10:15
    assert hhmm(t.entry_time) == "10:20"
    (t,) = trades_of(hand_frame(TARGET, drop(103), calm(103))).trades                    # opens 17:35, closes 17:40
    assert hhmm(t.entry_time) == "17:40"
    assert trades_of(hand_frame(TARGET, drop(104), calm(104))).trades == []              # opens 17:40, closes 17:45
    assert t.exit_reason in {"target_half_retrace", "time_exit_30min", "end_of_day_flatten"}


def test_only_the_first_bar_of_an_episode_signals():
    # bars 14 and 15 both meet the conditions; bar 14 is outside the window, bar 15 is not the first bar of the episode
    assert trades_of(hand_frame(TARGET, {14: 119800.0, 15: 119700.0}, calm(15))).trades == []
    p = prepared_today(hand_frame(TARGET, {14: 119800.0, 15: 119700.0}, calm(15)))
    assert bool(p.loc[14, "tv_both"]) and bool(p.loc[15, "tv_both"]) and not bool(p.loc[16, "tv_both"])
    assert (p["tv_side"] == 0).all()
    # ... and with only bar 15 it trades
    assert len(trades_of(hand_frame(TARGET, {15: 119700.0}, calm(15))).trades) == 1


def test_signal_ignored_while_in_position_and_after_the_exit_only_if_later_than_the_exit_bar_and_fresh():
    # shock at 30 -> entry 31 -> target hit at the close of 31 -> exit fill at the open of bar 32 (the exit bar)
    # a second shock ON the exit bar (32) is ignored; bar 33 meets the conditions too but is not the first of its episode;
    # bar 35 would be fresh but its volume is high
    ov = {**drop(30), 32: 119800.0}
    (t,) = trades_of(hand_frame(TARGET, ov, {35: 150.0})).trades
    assert hhmm(t.entry_time) == at(31)
    p = prepared_today(hand_frame(TARGET, ov, {35: 150.0}))
    assert bool(p.loc[32, "tv_both"]) and bool(p.loc[33, "tv_both"]) and not bool(p.loc[35, "tv_both"])
    # a shock on bar 33, the first bar after the exit bar, counts
    ov = {**drop(30), 33: 119500.0}
    r = trades_of(hand_frame(TARGET, ov, {36: 200.0}))
    assert [hhmm(t.entry_time) for t in r.trades] == [at(31), at(34)]
    assert r.trades[1].stop_price == 119200.0
    # a fresh shock while the position is open (time-exit path, no target) is ignored and adds no entry
    ov = {**FLAT_AFTER, **{k: 119600.0 for k in range(34, 113)}}
    frame = hand_frame(TARGET, ov)
    (t,) = trades_of(frame).trades
    assert hhmm(t.entry_time) == at(31) and t.exit_reason == "time_exit_30min"
    p = prepared_today(frame)
    assert bool(p.loc[34, "tv_both"]) and not bool(p.loc[33, "tv_both"]) and p.loc[34, "tv_side"] == 0


def test_at_most_six_entries_a_day():
    shocks = [30, 38, 46, 54, 62, 70, 78]
    closes, vols = {}, {}
    for t in shocks:
        closes.update(drop(t))
        vols.update(calm(t, 5))
    r = trades_of(hand_frame(TARGET, closes, vols))
    assert [hhmm(t.entry_time) for t in r.trades] == [at(k + 1) for k in shocks[:6]]
    assert all(t.exit_reason == "target_half_retrace" for t in r.trades)
    # the rule counts the entries itself: the backtest above ran with the default BacktestConfig()


@pytest.mark.parametrize("day", [CPI_DAY, NFP_DAY])
def test_no_entry_within_30_minutes_after_a_cpi_or_nfp_release(day):
    # release 10:30 Sao Paulo = the close of bar 17; min_since is measured to the close of the signal bar
    def n_trades(t):
        return len(trades_of(hand_frame(day, {t: base_close(t - 3) - 300.0}, calm(t))).trades)

    assert nbars(day) >= 83
    assert n_trades(16) == 1            # opens 10:20, closes 10:25, before the release
    assert n_trades(17) == 0            # closes 10:30: min_since = 0
    assert n_trades(22) == 0            # 10:55: 25
    assert n_trades(23) == 0            # 11:00: 30 (inclusive)
    assert n_trades(24) == 1            # 11:05: 35
    # the first bar of an episode blocked by the release makes the next bar not fresh
    both = {**{23: base_close(20) - 300.0}, 24: base_close(21) - 300.0}
    assert trades_of(hand_frame(day, both, calm(24))).trades == []


def test_no_entry_from_15_minutes_before_an_fomc_release_on_an_fomc_day():
    # release 15:00 Sao Paulo (14:00 EDT): the signal bar closing 14:40 (bar 67) may still enter, 14:45 (bar 68) may not
    def n_trades(day, t):
        return len(trades_of(hand_frame(day, {t: base_close(t - 3) - 300.0}, calm(t))).trades)

    assert n_trades(FOMC_DAY, 60) == 1
    assert n_trades(FOMC_DAY, 67) == 1
    assert n_trades(FOMC_DAY, 68) == 0
    assert n_trades(FOMC_DAY, 70) == 0
    assert n_trades(FOMC_DAY, 100) == 0
    assert n_trades(date(2026, 5, 13), 68) == 1      # the same bar on an ordinary day


def test_synthetic_sessions_trade_and_never_hold_overnight():
    frames = [synthetic_sessions(days=45),
              hand_frame(TARGET, drop(103), calm(103)),
              hand_frame(TARGET, FLAT_AFTER, calm(30))]
    for frame in frames:
        for scenario in ("base", "optimistic"):
            r = trades_of(frame, scenario)
            assert r.trades
            assert r.positions_held_overnight == 0
            per_day = pd.Series([t.entry_time.tz_convert(market("WIN").zone).date() for t in r.trades]).value_counts()
            assert max(per_day) <= 6
