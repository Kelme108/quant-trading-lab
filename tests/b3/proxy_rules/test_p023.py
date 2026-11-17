"""P-023 WinMetaorderGrindContinuation on SYNTHETIC WIN session 1-minute bars (Sao Paulo time, bars from the calendar's
session open to its close): class constants, causality, live-window parity, hand-built grind days (long, short, stop,
signal exit, time exit, jump filter, thresholds, freshness, entry window, entry cap, the 20-session scale) and no
overnight position."""

import random
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

from b3.backtest import BacktestConfig, run
from b3.calendar import B3SessionCalendar
from b3.checks import causality_problems, window_parity_problems
from b3.markets import market
from b3.proxy_rules import p023_win_metaorder_grind_continuation as mod
from b3.proxy_rules.p023_win_metaorder_grind_continuation import WinMetaorderGrindContinuation
from b3.strategy import tick_ceil, tick_floor

UTC = timezone.utc
CAL = B3SessionCalendar("WIN")
COLS = ["time", "open", "high", "low", "close", "volume"]
BASE = 120000.0
PRIOR_DAYS = 22                     # > 20 sessions and more than the 12000-bar warm-up before the target day
TARGET = date(2026, 5, 13)          # an ordinary session day
N = int((CAL.session(TARGET).close - CAL.session(TARGET).open).total_seconds() // 60)   # bars of the session (565)


def trading_days_before(day, n):
    out, d = [], day
    while len(out) < n:
        d -= timedelta(days=1)
        if CAL.is_trading_day(d):
            out.append(d)
    return sorted(out)


def prior_closes(k, n):
    """Square wave of period 60 bars and amplitude 150 points on a per-day level (level changes from day to day, so a
    ratio across sessions would differ): every 30-bar move is +-150 and no single-bar share can build a setup."""
    level = BASE + 500.0 * (k % 3)
    return [level + (150.0 if (j // 30) % 2 else 0.0) for j in range(n)]


def session_frame_rows(day, closes, prev_close):
    s = CAL.session(day)
    rows, prev = [], prev_close
    for k, c in enumerate(closes):
        o = prev
        rows.append((pd.Timestamp((s.open + timedelta(minutes=k)).astimezone(UTC)), o, max(o, c), min(o, c), c, 100.0))
        prev = c
    return rows, prev


def path(moves, n=N):
    """Closes of the target day: BASE plus the cumulative sum of `moves` ({bar index: close change})."""
    closes, cur = [], BASE
    for k in range(n):
        cur += moves.get(k, 0.0)
        closes.append(cur)
    return closes


def ramp(start, step, count, skip=()):
    return {start + k: step for k in range(count) if k not in skip}


def hand_frame(target_closes, prior=PRIOR_DAYS):
    rows, prev = [], BASE
    for k, d in enumerate(trading_days_before(TARGET, prior)):
        r, prev = session_frame_rows(d, prior_closes(k, int((CAL.session(d).close - CAL.session(d).open)
                                                           .total_seconds() // 60)), prev)
        rows += r
    r, prev = session_frame_rows(TARGET, target_closes, prev)
    rows += r
    return pd.DataFrame(rows, columns=COLS)


def expected_scale(prior=PRIOR_DAYS):
    """Independent S: pooled median of the within-session 30-bar moves of the 20 sessions before the target."""
    pooled = []
    for k in range(prior - 20, prior):
        c = np.array(prior_closes(k, N))
        pooled += list(np.abs(c[30:] / c[:-30] - 1.0))
    return float(np.median(pooled))


def synthetic_sessions(days=26, seed=11, start=BASE, step=5.0):
    """Random walk of one-minute closes moving by -1, 0 or +1 tick-steps (many small same-sign minutes happen)."""
    m = market("WIN")
    rng = random.Random(seed)
    d, rows, prev = date(2026, 1, 5), [], start
    while len({r[0].date() for r in rows}) < days:
        if CAL.is_trading_day(d):
            t = datetime.combine(d, m.open, m.zone)
            end = datetime.combine(d, m.close, m.zone)
            while t + timedelta(minutes=1) <= end:
                o = prev
                c = o + step * rng.choice((-1, 0, 1))
                rows.append((t, o, max(o, c) + step * rng.randint(0, 1), min(o, c) - step * rng.randint(0, 1), c,
                             float(rng.randint(50, 500))))
                prev, t = c, t + timedelta(minutes=1)
        d += timedelta(days=1)
    return pd.DataFrame([(pd.Timestamp(r[0].astimezone(UTC)),) + r[1:] for r in rows], columns=COLS)


def trades_of(frame):
    return run(frame, WinMetaorderGrindContinuation.on("WIN")(), market("WIN").cost("optimistic"), BacktestConfig())


def trades_for(moves):
    return trades_of(hand_frame(path(moves))).trades


def prepared_target(moves, prior=PRIOR_DAYS):
    strategy = WinMetaorderGrindContinuation.on("WIN")()
    out = strategy.prepare(hand_frame(path(moves), prior))
    return out[out["local_date"] == TARGET].reset_index(drop=True)


def hhmm(ts):
    return ts.tz_convert(market("WIN").zone).strftime("%H:%M")


def at(bar):
    """Clock time (HH:MM) of the open of target-day bar `bar`."""
    return hhmm(pd.Timestamp((CAL.session(TARGET).open + timedelta(minutes=bar)).astimezone(UTC)))


G = 100                      # first return of the hand-built grinds
UP = ramp(G, 20.0, 12)       # 12 up minutes of +20: D = 10 at bar G + 9 (close 120200), R30 = +0.167% >= S, no jump


def test_class_constants():
    s = WinMetaorderGrindContinuation
    assert mod.RULE_ID == "P-023"
    assert s.name.startswith("P-023") and s.timeframe_min == 1
    assert s.warmup >= 20 * 565 + 565
    assert (s.rules.entry_start_after_open_min, s.rules.entry_end_before_close_min,
            s.rules.flatten_before_close_min) == (1, 44, 10)
    assert s.params == {
        "window_bars": 30, "net_sign_threshold": 10, "min_move_over_scale": 1.0, "max_single_bar_share": 0.5,
        "scale_lookback_sessions": 20, "scale_return_bars": 30, "stop_over_scale": 1.0, "signal_exit_net_sign": 0,
        "time_exit_bars": 30, "min_bar_in_day": 30, "last_entry_minutes_to_close": 45, "flat_minutes_to_close": 10,
        "max_entries_per_day": 4}
    assert "symbol" not in vars(s)
    assert N == 565


def test_causal_and_matches_the_live_window():
    strategy = WinMetaorderGrindContinuation.on("WIN")()
    frame = synthetic_sessions()
    prepared = strategy.prepare(frame)
    assert (prepared["gp_side"] != 0).sum() >= 10          # the synthetic data really produce signals
    assert causality_problems(strategy, frame) == []
    assert window_parity_problems(strategy, frame, samples=40) == []
    moves = {**UP, **ramp(300, -20.0, 12)}
    hand = hand_frame(path(moves))
    assert (strategy.prepare(hand)["gp_side"] != 0).sum() == 2
    assert causality_problems(strategy, hand) == []
    assert window_parity_problems(strategy, hand, samples=40) == []


def test_the_scale_is_the_pooled_within_session_median_of_the_previous_20_sessions():
    t = prepared_target({})
    assert t["gp_scale"].nunique() == 1
    assert abs(t["gp_scale"].iloc[0] - expected_scale()) < 1e-12
    assert 0.0012 < expected_scale() < 0.00126
    # more sessions before the target change nothing but the window: the 20 sessions right before it are used
    t23 = prepared_target({}, prior=PRIOR_DAYS + 1)
    assert t23["gp_scale"].nunique() == 1 and np.isfinite(t23["gp_scale"].iloc[0])


def test_fewer_than_20_prior_sessions_means_no_trading():
    t = prepared_target(UP, prior=19)
    assert t["gp_scale"].isna().all() and (t["gp_side"] == 0).all() and (t["gp_long_setup"] == 0).all()
    t = prepared_target(UP, prior=20)
    assert t["gp_scale"].notna().all() and (t["gp_side"] != 0).sum() == 1


def test_window_features_count_signs_ignore_zeros_and_take_the_largest_move():
    t = prepared_target({**ramp(100, 20.0, 12, skip=(3, 7)), 103: -10.0, 107: -30.0})
    row = t.iloc[109]                                   # window = returns of bars 80..109: 8 up, 2 down, 20 zero
    assert row["gp_d"] == 6
    c = t["close"].to_numpy()
    rets = c[1:] / c[:-1] - 1.0                         # rets[k - 1] = return of bar k
    assert abs(row["gp_maxr"] - np.abs(rets[79:109]).max()) < 1e-15
    assert abs(row["gp_maxr"] - 30.0 / c[106]) < 1e-15  # the -30 minute is the largest
    assert t["gp_d"].iloc[:30].isna().all() and t["gp_d"].iloc[30:].notna().all()
    assert abs(t["gp_r30"].iloc[109] - (t["close"].iloc[109] / t["close"].iloc[79] - 1.0)) < 1e-15


def test_long_entry_with_the_stop_one_scale_below_and_the_30_bar_time_exit():
    (t,) = trades_for(UP)
    close_t = BASE + 200.0
    assert (t.side, t.entry_price, t.entry_reason) == ("long", close_t, "grind_up_long")
    assert at(110) == hhmm(t.entry_time)                           # filled at the open of the bar after the signal bar 109
    assert t.stop_price == tick_floor(close_t * (1.0 - expected_scale()), 5.0)
    assert t.stop_price < close_t and t.stop_price % 5.0 == 0.0
    # decided at the close of bar 139 (30 bars after the signal bar), filled at the open of bar 140
    assert t.exit_reason == "time_exit_30_bars" and hhmm(t.exit_time) == at(140) and t.exit_price == BASE + 240.0


def test_short_entry_mirrors_with_a_stop_above():
    (t,) = trades_for(ramp(G, -20.0, 12))
    close_t = BASE - 200.0
    assert (t.side, t.entry_price, t.entry_reason) == ("short", close_t, "grind_down_short")
    assert hhmm(t.entry_time) == at(110)
    assert t.stop_price == tick_ceil(close_t * (1.0 + expected_scale()), 5.0)
    assert t.stop_price > close_t and t.stop_price % 5.0 == 0.0
    assert t.exit_reason == "time_exit_30_bars" and hhmm(t.exit_time) == at(140) and t.exit_price == BASE - 240.0


def test_signal_exit_when_the_net_sign_count_falls_to_zero():
    # 12 up minutes, then down minutes of -10: D = 12 - m at bar 111 + m, so D = 0 at bar 123 -> exit at the open of 124
    (t,) = trades_for({**UP, **ramp(112, -10.0, 12)})
    assert t.side == "long" and t.exit_reason == "persistence_died_long"
    assert hhmm(t.exit_time) == at(124) and t.exit_price == BASE + 240.0 - 120.0
    # short side: D >= 0
    (t,) = trades_for({**ramp(G, -20.0, 12), **ramp(112, 10.0, 12)})
    assert t.side == "short" and t.exit_reason == "persistence_died_short"
    assert hhmm(t.exit_time) == at(124) and t.exit_price == BASE - 240.0 + 120.0


def test_the_stop_is_hit_and_the_same_setup_is_not_traded_again():
    stop = tick_floor((BASE + 200.0) * (1.0 - expected_scale()), 5.0)
    (t,) = trades_for({**UP, 112: -300.0})                     # bar 112 closes 119940, below the stop
    assert t.side == "long" and t.exit_reason == "stop_loss" and t.exit_price == stop
    assert hhmm(t.exit_time) == at(113)                        # the bar's close
    stop_s = tick_ceil((BASE - 200.0) * (1.0 + expected_scale()), 5.0)
    (t,) = trades_for({**ramp(G, -20.0, 12), 112: 300.0})
    assert t.side == "short" and t.exit_reason == "stop_loss" and t.exit_price == stop_s


def test_a_move_carried_by_one_large_minute_is_rejected():
    assert trades_for({100: 150.0, **ramp(101, 5.0, 12)}) == []         # R30 = 210, MAXR = 150 > 0.5 x R30
    (t,) = trades_for({100: 60.0, **ramp(101, 10.0, 12)})               # R30 = 180, MAXR = 60 <= 90: taken
    assert t.side == "long"
    assert trades_for({100: -150.0, **ramp(101, -5.0, 12)}) == []       # the short mirror


def test_thresholds_on_the_net_sign_count_and_on_the_size_of_the_move():
    assert trades_for(ramp(G, 5.0, 12)) == []                           # D = 12 but R30 = 60 points < S x price (~150)
    assert trades_for(ramp(G, 20.0, 9)) == []                           # a 180-point grind but D = 9 < 10
    assert len(trades_for(ramp(G, 20.0, 10))) == 1                      # D = 10 exactly
    # downs count against D: 12 ups and 2 downs -> D = 10 trades; 11 ups and 2 downs -> D = 9 does not
    assert len(trades_for({**ramp(G, 20.0, 14), 103: -5.0, 107: -5.0})) == 1
    assert trades_for({**ramp(G, 20.0, 13), 103: -5.0, 107: -5.0}) == []


def test_fresh_setup_only_and_a_new_entry_needs_a_new_fresh_setup():
    # a 100-minute grind keeps the setup true past the time exit at bar 139: no re-entry until it turns false
    moves = {**ramp(G, 20.0, 100), **ramp(300, 20.0, 12)}
    prepared = prepared_target(moves)
    assert prepared["gp_long_setup"].iloc[109:200].min() == 1                # true all along the grind
    trades = trades_for(moves)
    assert [t.exit_reason for t in trades] == ["time_exit_30_bars", "time_exit_30_bars"]
    assert [hhmm(t.entry_time) for t in trades] == [at(110), at(310)]
    assert hhmm(trades[0].exit_time) == at(140)


def test_signal_window_ends_45_minutes_before_the_close():
    last = N - 46                                       # the bar whose close is 45 minutes before the close
    (t,) = trades_for(ramp(last - 9, 20.0, 12))
    assert hhmm(t.entry_time) == at(last + 1) and t.exit_reason == "time_exit_30_bars"
    assert trades_for(ramp(last - 8, 20.0, 12)) == []   # the setup first holds at minutes_to_close = 44


def test_at_most_4_entries_a_day_enforced_by_the_rule():
    moves = {}
    for j in range(5):
        moves.update(ramp(40 + 90 * j, 20.0, 12))
    strategy = WinMetaorderGrindContinuation.on("WIN")()
    prepared = strategy.prepare(hand_frame(path(moves)))
    assert (prepared["gp_side"] != 0).sum() == 4
    trades = trades_for(moves)
    assert len(trades) == 4 and all(t.side == "long" for t in trades)
    assert [hhmm(t.entry_time) for t in trades] == [at(50 + 90 * j) for j in range(4)]


def test_both_sides_share_the_cap_and_only_one_position_is_open():
    moves = {**ramp(40, 20.0, 12), **ramp(130, -20.0, 12), **ramp(220, 20.0, 12), **ramp(310, -20.0, 12),
             **ramp(400, 20.0, 12)}
    trades = trades_for(moves)
    assert [t.side for t in trades] == ["long", "short", "long", "short"]
    for a, b in zip(trades, trades[1:]):
        assert a.exit_time <= b.entry_time


def test_synthetic_sessions_trade_and_never_hold_overnight():
    frames = [synthetic_sessions(), hand_frame(path(UP))]
    for frame in frames:
        r = run(frame, WinMetaorderGrindContinuation.on("WIN")(), market("WIN").cost("base"), BacktestConfig())
        assert r.trades
        assert r.positions_held_overnight == 0
        per_day = pd.Series([t.entry_time.tz_convert(market("WIN").zone).date() for t in r.trades]).value_counts()
        assert max(per_day) <= 4
