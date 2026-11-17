"""P-026 WinCompressionBoxBreakout on SYNTHETIC WIN session 5-minute bars (Sao Paulo time, bars from the calendar's session
open to its close): class constants, causality, live-window parity, hand-built days (long, short, stop with its clamps,
the 20-session time-of-day norm, compression threshold, breakout tick, entry window, time exit, stop exit, the exit-bar
rule, the entry cap) and no overnight position."""

import random
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

from b3.backtest import BacktestConfig, run
from b3.calendar import B3SessionCalendar
from b3.checks import causality_problems, window_parity_problems
from b3.markets import market
from b3.proxy_rules import p026_win_compression_box_breakout as mod
from b3.proxy_rules.p026_win_compression_box_breakout import WinCompressionBoxBreakout
from b3.strategy import tick_ceil, tick_floor

UTC = timezone.utc
CAL = B3SessionCalendar("WIN")
COLS = ["time", "open", "high", "low", "close", "volume"]
BASE = 120000.0
PRIOR_DAYS = 25                     # > 20 sessions and more than the 2600-bar warm-up before the target day
TARGET = date(2026, 5, 13)          # an ordinary session day
N = int((CAL.session(TARGET).close - CAL.session(TARGET).open).total_seconds() // 300)   # bars of the session (113)
OPT = market("WIN").cost("optimistic")


def trading_days_before(day, n):
    out, d = [], day
    while len(out) < n:
        d -= timedelta(days=1)
        if CAL.is_trading_day(d):
            out.append(d)
    return sorted(out)


def rows_of(day, bars):
    s = CAL.session(day)
    return [(pd.Timestamp((s.open + timedelta(minutes=5 * k)).astimezone(UTC)), o, h, lo, c, 100.0)
            for k, (o, h, lo, c) in enumerate(bars)]


def flat_bar(level, half=5.0):
    return (level, level + half, level - half, level)


def target_bars(over=None, box_hi=30.0, box_lo=30.0):
    """A flat day at BASE whose every bar has High = BASE + box_hi and Low = BASE - box_lo (box width box_hi + box_lo);
    `over` replaces bars by index (a dict bar -> (open, high, low, close))."""
    bars = [(BASE, BASE + box_hi, BASE - box_lo, BASE) for _ in range(N)]
    for k, v in (over or {}).items():
        bars[k] = v
    return bars


def tail(level, first, last=N - 1, half=5.0):
    """Flat bars at `level` for bars first..last (an `over` dict)."""
    return {k: flat_bar(level, half) for k in range(first, last + 1)}


def hand_frame(bars, prior_half=50.0, prior=PRIOR_DAYS):
    """`prior` sessions of flat closes at BASE whose bars span +-prior_half (a number, or a function (day index, bar) ->
    half range), then the target day `bars`."""
    rows = []
    for k, d in enumerate(trading_days_before(TARGET, prior)):
        n = int((CAL.session(d).close - CAL.session(d).open).total_seconds() // 300)
        halves = [prior_half(k, j) if callable(prior_half) else prior_half for j in range(n)]
        rows += rows_of(d, [(BASE, BASE + h, BASE - h, BASE) for h in halves])
    rows += rows_of(TARGET, bars)
    return pd.DataFrame(rows, columns=COLS)


def synthetic_sessions(days=34, seed=5, start=BASE, step=5.0):
    """Random walk of 5-minute bars with a volatility that changes from bar to bar (compressed boxes happen)."""
    m = market("WIN")
    rng = random.Random(seed)
    d, rows, prev = date(2026, 1, 5), [], start
    while len({r[0].date() for r in rows}) < days:
        if CAL.is_trading_day(d):
            t = datetime.combine(d, m.open, m.zone)
            end = datetime.combine(d, m.close, m.zone)
            while t + timedelta(minutes=5) <= end:
                s = rng.choice((1, 1, 2, 4))
                o = prev
                c = o + step * s * rng.randint(-2, 2)
                rows.append((t, o, max(o, c) + step * s * rng.randint(0, 1), min(o, c) - step * s * rng.randint(0, 1),
                             c, float(rng.randint(50, 500))))
                prev, t = c, t + timedelta(minutes=5)
        d += timedelta(days=1)
    return pd.DataFrame([(pd.Timestamp(r[0].astimezone(UTC)),) + r[1:] for r in rows], columns=COLS)


def run_frame(frame):
    return run(frame, WinCompressionBoxBreakout.on("WIN")(), OPT, BacktestConfig())


def trades_for(bars, **kw):
    return run_frame(hand_frame(bars, **kw)).trades


def prepared_target(bars, **kw):
    out = WinCompressionBoxBreakout.on("WIN")().prepare(hand_frame(bars, **kw))
    return out[out["local_date"] == TARGET].reset_index(drop=True)


def hhmm(ts):
    return ts.tz_convert(market("WIN").zone).strftime("%H:%M")


def at(bar):
    """Clock time (HH:MM) of the open of target-day bar `bar`."""
    return hhmm(pd.Timestamp((CAL.session(TARGET).open + timedelta(minutes=5 * bar)).astimezone(UTC)))


# long break of the default 60-point box (High 120030) at bar 12, then a flat tail at 120035
UP_BREAK = {12: (BASE, BASE + 40.0, BASE - 30.0, BASE + 35.0), **tail(BASE + 35.0, 13)}
DOWN_BREAK = {12: (BASE, BASE + 30.0, BASE - 40.0, BASE - 35.0), **tail(BASE - 35.0, 13)}


def test_class_constants():
    s = WinCompressionBoxBreakout
    assert mod.RULE_ID == "P-026"
    assert s.name.startswith("P-026") and s.timeframe_min == 5
    assert s.warmup >= 21 * 113
    assert (s.rules.entry_start_after_open_min, s.rules.entry_end_before_close_min,
            s.rules.flatten_before_close_min) == (5, 74, 5)
    assert s.params == {
        "box_bars": 12, "baseline_sessions": 20, "compression_ratio_max": 0.8, "breakout_ticks": 1, "min_bar_in_day": 13,
        "min_minutes_to_close_at_signal": 75, "stop_at_box_fraction": 0.5, "min_stop_pct": 0.1, "max_stop_pct": 0.3,
        "hold_bars": 12, "max_entries_per_day": 4}
    assert "symbol" not in vars(s)
    assert N == 113


def test_causal_and_matches_the_live_window():
    strategy = WinCompressionBoxBreakout.on("WIN")()
    frame = synthetic_sessions()
    prepared = strategy.prepare(frame)
    assert (prepared["cb_side"] != 0).sum() >= 10          # the synthetic data really produce signals
    assert causality_problems(strategy, frame) == []
    assert window_parity_problems(strategy, frame, samples=60) == []
    for over in ({**UP_BREAK, **DOWN_BREAK, **tail(BASE - 35.0, 13, 30)}, UP_BREAK):
        hand = hand_frame(target_bars(over))
        assert (strategy.prepare(hand)["cb_side"] != 0).sum() >= 1
        assert causality_problems(strategy, hand) == []
        assert window_parity_problems(strategy, hand, samples=150) == []


def test_the_norm_is_the_time_of_day_median_of_the_box_width_of_the_previous_20_sessions():
    # 5 oldest sessions very wide (outside the 20), then 10 sessions of width 100 and 10 of width 300: median 200
    def half(k, j):
        return 500.0 if k < 5 else (50.0 if k < 15 else 150.0)

    t = prepared_target(target_bars(), prior_half=half)
    assert t["cb_norm"].iloc[:11].isna().all() and t["cb_norm"].iloc[11:].notna().all()
    assert np.allclose(t["cb_norm"].iloc[11:], 200.0 / BASE, rtol=0, atol=1e-15)
    assert np.allclose(t["cb_width"].iloc[11:], 60.0 / BASE, rtol=0, atol=1e-15)      # today's own box width
    # today is excluded: a different target day leaves the norm unchanged
    t2 = prepared_target(target_bars(box_hi=400.0, box_lo=400.0), prior_half=half)
    assert np.allclose(t2["cb_norm"].iloc[11:], t["cb_norm"].iloc[11:], rtol=0, atol=1e-15)
    # the norm is taken at the same minute_of_day: wide prior bars at 40..51 only move the norm of bars 51..62
    t3 = prepared_target(target_bars(), prior_half=lambda k, j: 300.0 if 40 <= j <= 51 else 50.0)
    assert abs(t3["cb_norm"].iloc[39] - 100.0 / BASE) < 1e-15
    assert abs(t3["cb_norm"].iloc[50] - 600.0 / BASE) < 1e-15
    assert abs(t3["cb_norm"].iloc[62] - 600.0 / BASE) < 1e-15       # box 51..62 still holds the wide bar 51
    assert abs(t3["cb_norm"].iloc[63] - 100.0 / BASE) < 1e-15


def test_fewer_than_20_prior_sessions_means_no_trading():
    t = prepared_target(target_bars(UP_BREAK), prior=19)
    assert t["cb_norm"].isna().all() and (t["cb_side"] == 0).all()
    t = prepared_target(target_bars(UP_BREAK), prior=20)
    assert t["cb_norm"].notna().iloc[11:].all() and (t["cb_side"] != 0).sum() == 1


def test_long_entry_with_the_midpoint_stop_clamped_to_at_least_0_10_percent_and_the_12_bar_time_exit():
    (t,) = trades_for(target_bars(UP_BREAK))
    close_t = BASE + 35.0
    assert (t.side, t.entry_price, t.entry_reason) == ("long", close_t, "compressed_box_break_up")
    assert hhmm(t.entry_time) == at(13)                     # filled at the open of the bar after the signal bar 12
    # box 119970..120030, midpoint 120000 is 35 points (0.029%) from the entry: clamped to 0.10% of the close
    assert t.stop_price == tick_floor(close_t - 0.001 * close_t, 5.0) == 119910.0
    assert t.stop_price < close_t and t.stop_price % 5.0 == 0.0
    # decided at the close of bar 24 (12 bars after the signal bar), filled at the open of bar 25: 12 bars held
    assert t.exit_reason == "time_exit_12_bars" and hhmm(t.exit_time) == at(25) and t.exit_price == close_t
    assert (t.exit_time - t.entry_time) == pd.Timedelta(minutes=60)


def test_short_entry_mirrors_with_a_stop_above():
    (t,) = trades_for(target_bars(DOWN_BREAK))
    close_t = BASE - 35.0
    assert (t.side, t.entry_price, t.entry_reason) == ("short", close_t, "compressed_box_break_down")
    assert hhmm(t.entry_time) == at(13)
    assert t.stop_price == tick_ceil(close_t + 0.001 * close_t, 5.0) == 120085.0
    assert t.stop_price > close_t and t.stop_price % 5.0 == 0.0
    assert t.exit_reason == "time_exit_12_bars" and hhmm(t.exit_time) == at(25) and t.exit_price == close_t


def test_stop_at_the_unclamped_midpoint_and_the_midpoint_rounding():
    # prior boxes of width 1000: a 300-point box (150 each side) is compressed; the midpoint is 155 points from the entry
    over = {12: (BASE, BASE + 160.0, BASE - 150.0, BASE + 155.0), **tail(BASE + 155.0, 13)}
    (t,) = trades_for(target_bars(over, box_hi=150.0, box_lo=150.0), prior_half=500.0)
    assert t.side == "long" and t.stop_price == BASE            # 155 is inside [0.10%, 0.30%] = [120.2, 360.5]
    # asymmetric box 119990..120405: the midpoint 120197.5 rounds DOWN to 120195 for a long (close 120410 = H + 1 tick)
    over = {12: (BASE, BASE + 415.0, BASE, BASE + 410.0), **tail(BASE + 410.0, 13, half=0.0)}
    bars = target_bars(over, box_hi=405.0, box_lo=10.0)
    (t,) = trades_for(bars, prior_half=400.0)
    assert t.side == "long" and t.stop_price == tick_floor((120405.0 + 119990.0) / 2.0, 5.0) == 120195.0
    # and UP for a short: box 119595..120010, midpoint 119802.5 rounds up to 119805 (close 119590 = L - 1 tick)
    over = {12: (BASE, BASE, BASE - 415.0, BASE - 410.0), **tail(BASE - 410.0, 13, half=0.0)}
    (t,) = trades_for(target_bars(over, box_hi=10.0, box_lo=405.0), prior_half=400.0)
    assert t.side == "short" and t.stop_price == tick_ceil((120010.0 + 119595.0) / 2.0, 5.0) == 119805.0


def test_stop_distance_is_clamped_to_at_most_0_30_percent():
    # box 119620..120380 (760 wide, 0.8 x 1000 = 800 norm): the midpoint is 385 points below the close, over 0.30%
    over = {12: (BASE, BASE + 390.0, BASE - 380.0, BASE + 385.0), **tail(BASE + 385.0, 13)}
    (t,) = trades_for(target_bars(over, box_hi=380.0, box_lo=380.0), prior_half=500.0)
    close_t = BASE + 385.0
    assert t.side == "long" and t.stop_price == tick_floor(close_t - 0.003 * close_t, 5.0) == 120020.0
    over = {12: (BASE, BASE + 380.0, BASE - 390.0, BASE - 385.0), **tail(BASE - 385.0, 13)}
    (t,) = trades_for(target_bars(over, box_hi=380.0, box_lo=380.0), prior_half=500.0)
    close_t = BASE - 385.0
    assert t.side == "short" and t.stop_price == tick_ceil(close_t + 0.003 * close_t, 5.0) == 119975.0


def test_compression_threshold_is_0_80_of_the_norm():
    # norm width 100: a box of width 80 is compressed (<=), width 85 is not
    over = {12: (BASE, BASE + 45.0, BASE - 40.0, BASE + 45.0), **tail(BASE + 45.0, 13)}
    (t,) = trades_for(target_bars(over, box_hi=40.0, box_lo=40.0))
    assert t.side == "long"
    over = {12: (BASE, BASE + 50.0, BASE - 40.0, BASE + 50.0), **tail(BASE + 50.0, 13)}
    assert trades_for(target_bars(over, box_hi=45.0, box_lo=40.0)) == []


def test_the_norm_is_for_the_time_of_day():
    # box of width 400 at bars 40..51 is compressed against a norm of 600 at that time, but not against 100
    over = {52: (BASE, BASE + 210.0, BASE - 5.0, BASE + 205.0), **tail(BASE + 205.0, 53)}
    bars = target_bars({**{k: (BASE, BASE + 200.0, BASE - 200.0, BASE) for k in range(40, 52)}, **over})
    (t,) = trades_for(bars, prior_half=lambda k, j: 300.0 if 40 <= j <= 51 else 50.0)
    assert t.side == "long" and hhmm(t.entry_time) == at(53) and t.stop_price == BASE
    assert trades_for(bars, prior_half=50.0) == []


def test_breakout_needs_one_tick_beyond_the_box():
    over = {12: (BASE, BASE + 30.0, BASE - 30.0, BASE + 30.0), **tail(BASE + 30.0, 13)}      # close = H: no
    assert trades_for(target_bars(over)) == []
    over = {12: (BASE, BASE + 35.0, BASE - 30.0, BASE + 30.0 + 4.0), **tail(BASE + 34.0, 13)}  # H + 4 points: no
    assert trades_for(target_bars(over)) == []
    assert len(trades_for(target_bars(UP_BREAK))) == 1                                         # H + 1 tick: yes
    over = {12: (BASE, BASE + 30.0, BASE - 30.0, BASE - 30.0), **tail(BASE - 30.0, 13)}      # close = L: no
    assert trades_for(target_bars(over)) == []


def test_the_first_signal_bar_is_the_13th_bar_of_the_session():
    over = {11: (BASE, BASE + 40.0, BASE - 30.0, BASE + 35.0), **tail(BASE + 35.0, 12)}
    assert trades_for(target_bars(over)) == []          # a break at bar 11 (12th bar): only 11 earlier bars
    prepared = prepared_target(target_bars(UP_BREAK))
    assert prepared["cb_side"].iloc[:12].eq(0).all() and prepared["cb_side"].iloc[12] == 1


def test_signal_window_ends_75_minutes_before_the_close():
    last = N - 16                                       # the bar whose close is 75 minutes before the close
    over = {last: (BASE, BASE + 40.0, BASE - 30.0, BASE + 35.0), **tail(BASE + 35.0, last + 1)}
    (t,) = trades_for(target_bars(over))
    assert hhmm(t.entry_time) == at(last + 1) and t.exit_reason == "time_exit_12_bars"
    over = {last + 1: (BASE, BASE + 40.0, BASE - 30.0, BASE + 35.0), **tail(BASE + 35.0, last + 2)}
    assert trades_for(target_bars(over)) == []          # the close of this bar is 70 minutes before the close


def test_the_stop_is_hit_and_a_signal_on_the_stop_bar_is_not_taken():
    # bar 13 trades down through the stop 119910 and closes at 120045, a fresh break (box bars 1..12: 119970..120040)
    over = {**UP_BREAK, 13: (BASE + 35.0, BASE + 50.0, BASE - 100.0, BASE + 45.0), **tail(BASE + 45.0, 14, half=0.0)}
    bars = target_bars(over)
    prepared = prepared_target(bars)
    assert prepared["cb_side"].iloc[12] == 1 and prepared["cb_side"].iloc[13] == 0
    (t,) = trades_for(bars)
    assert t.side == "long" and t.exit_reason == "stop_loss" and t.exit_price == 119910.0
    assert hhmm(t.exit_time) == at(14)                  # the stop fills at the close of the bar that hits it


def test_the_stop_checks_from_the_bar_after_the_signal_bar_only():
    # the signal bar's own low is below the stop but it is not the entry bar: no stop exit
    over = {12: (BASE, BASE + 40.0, BASE - 500.0, BASE + 35.0), **tail(BASE + 35.0, 13)}
    (t,) = trades_for(target_bars(over))
    assert t.exit_reason == "time_exit_12_bars"


def test_a_signal_on_the_time_exit_bar_is_not_taken_but_the_next_bar_is():
    over = {**UP_BREAK, **tail(BASE + 35.0, 13, 24, half=5.0),
            25: (BASE + 35.0, BASE + 50.0, BASE + 30.0, BASE + 45.0),      # re-break on the exit bar (bar 25): not taken
            26: (BASE + 45.0, BASE + 60.0, BASE + 40.0, BASE + 55.0),      # re-break on bar 26: taken
            **tail(BASE + 55.0, 27)}
    prepared = prepared_target(target_bars(over))
    assert list(np.flatnonzero(prepared["cb_side"].to_numpy())) == [12, 26]
    t1, t2 = trades_for(target_bars(over))
    assert (hhmm(t1.entry_time), hhmm(t1.exit_time)) == (at(13), at(25))
    assert hhmm(t2.entry_time) == at(27) and t2.entry_price == BASE + 55.0
    # box of bars 14..25: 120030..120050, midpoint 120040 is 15 points below: clamp to 0.10% of the close
    assert t2.stop_price == tick_floor((BASE + 55.0) * (1 - 0.001), 5.0)
    assert t1.exit_time <= t2.entry_time


def test_at_most_4_entries_a_day_enforced_by_the_rule():
    levels = [BASE, BASE + 35.0] + [BASE + 35.0 + 10.0 * j for j in range(1, 5)]
    over = {}
    for j in range(1, 6):                               # breaks at bars 12, 32, 52, 72, 92
        b = 12 + 20 * (j - 1)
        prev, new = levels[j - 1], levels[j]
        over[b] = (prev, new + 5.0, prev - 5.0, new)
        over.update(tail(new, b + 1, b + 19))
    bars = target_bars(over)
    prepared = prepared_target(bars)
    assert (prepared["cb_side"] != 0).sum() == 4
    trades = trades_for(bars)
    assert len(trades) == 4 and all(t.side == "long" for t in trades)
    assert [hhmm(t.entry_time) for t in trades] == [at(13 + 20 * j) for j in range(4)]
    for a, b in zip(trades, trades[1:]):
        assert a.exit_time <= b.entry_time


def test_synthetic_sessions_trade_and_never_hold_overnight():
    frames = [synthetic_sessions(), hand_frame(target_bars(UP_BREAK))]
    for frame in frames:
        r = run(frame, WinCompressionBoxBreakout.on("WIN")(), market("WIN").cost("base"), BacktestConfig())
        assert r.trades
        assert r.positions_held_overnight == 0
        per_day = pd.Series([t.entry_time.tz_convert(market("WIN").zone).date() for t in r.trades]).value_counts()
        assert max(per_day) <= 4
