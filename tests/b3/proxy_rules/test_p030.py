"""P-030 MultiSessionTrendPullback on SYNTHETIC WIN session 5-minute bars: class constants, causality, live-window parity,
T and s against an independent computation, hand-built days (long in an up-trend, short in a down-trend, no trade against
the trend, the stop, the 45-minute exit, entry window, cooldown, the 4-entry cap) and no overnight position."""

import math
import random
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

from b3.backtest import BacktestConfig, run
from b3.calendar import B3SessionCalendar
from b3.checks import causality_problems, window_parity_problems
from b3.markets import market
from b3.proxy_rules import p030_multi_session_trend_pullback as mod
from b3.proxy_rules.p030_multi_session_trend_pullback import MultiSessionTrendPullback
from b3.strategy import tick_ceil, tick_floor

UTC = timezone.utc
CAL = B3SessionCalendar("WIN")
COLS = ["time", "open", "high", "low", "close", "volume"]
BASE = 120000.0
PRIOR_DAYS = 10                     # more than the 1000-bar warm-up (113 bars a day) before the target day
TARGET = date(2026, 5, 13)
OPT = market("WIN").cost("optimistic")


def nbars(day):
    s = CAL.session(day)
    return int((s.close - s.open).total_seconds() // 300)


N = nbars(TARGET)


def trading_days_before(day, n):
    out, d = [], day
    while len(out) < n:
        d -= timedelta(days=1)
        if CAL.is_trading_day(d):
            out.append(d)
    return sorted(out)


def rows_of(day, closes, prev_close):
    s = CAL.session(day)
    rows, prev = [], prev_close
    for k, c in enumerate(closes):
        rows.append((pd.Timestamp((s.open + timedelta(minutes=5 * k)).astimezone(UTC)), prev, max(prev, c),
                     min(prev, c), c, 100.0))
        prev = c
    return rows, prev


def prior_closes(n, sign, start):
    """A session drifting in direction `sign`: steps +10, -5 (times sign) alternately, so returns are not constant."""
    out, cur = [], start
    for k in range(n):
        cur += sign * (10.0 if k % 2 == 0 else -5.0)
        out.append(cur)
    return out


def hand_frame(steps, sign=1, prior=PRIOR_DAYS, n=N):
    """`prior` drifting sessions (sign +1 up, -1 down, 0 flat), then the target day: flat at the last close plus `steps`
    ({bar index: close change}); each bar opens at the previous close."""
    rows, prev = [], BASE
    for d in trading_days_before(TARGET, prior):
        closes = prior_closes(nbars(d), sign, prev) if sign else [prev] * nbars(d)
        r, prev = rows_of(d, closes, prev)
        rows += r
    closes, cur = [], prev
    for k in range(n):
        cur += steps.get(k, 0.0)
        closes.append(cur)
    r, _ = rows_of(TARGET, closes, prev)
    return pd.DataFrame(rows + r, columns=COLS), prev


def synthetic_sessions(days=20, seed=11, start=BASE, step=5.0):
    m = market("WIN")
    rng = random.Random(seed)
    d, rows, prev = date(2026, 1, 5), [], start
    while len({r[0].date() for r in rows}) < days:
        if CAL.is_trading_day(d):
            t = datetime.combine(d, m.open, m.zone)
            end = datetime.combine(d, m.close, m.zone)
            drift = -1 if len({r[0].date() for r in rows}) < 9 else 1       # down-trend first, then up-trend
            while t + timedelta(minutes=5) <= end:
                o = prev
                c = o + step * (rng.randint(-3, 3) + (1 if rng.random() < 0.15 else 0) * drift * 2)
                rows.append((t, o, max(o, c) + step * rng.randint(0, 1), min(o, c) - step * rng.randint(0, 1), c,
                             float(rng.randint(50, 500))))
                prev, t = c, t + timedelta(minutes=5)
        d += timedelta(days=1)
    return pd.DataFrame([(pd.Timestamp(r[0].astimezone(UTC)),) + r[1:] for r in rows], columns=COLS)


def strategy():
    return MultiSessionTrendPullback.on("WIN")()


def trades_for(steps, sign=1):
    frame, _ = hand_frame(steps, sign)
    return run(frame, strategy(), OPT, BacktestConfig()).trades


def prepared_target(steps, sign=1):
    frame, _ = hand_frame(steps, sign)
    out = strategy().prepare(frame)
    return out[out["local_date"] == TARGET].reset_index(drop=True)


def hhmm(ts):
    return ts.tz_convert(market("WIN").zone).strftime("%H:%M")


def at(bar):
    return hhmm(pd.Timestamp((CAL.session(TARGET).open + timedelta(minutes=5 * bar)).astimezone(UTC)))


def reference_T_s(frame, day):
    """Independent T and s for `day` from the 5 sessions before it."""
    local = frame["time"].dt.tz_convert(market("WIN").zone).dt.date
    days = sorted(set(local))
    k = days.index(day)
    tt, rets = 0.0, []
    for d in days[k - 5:k]:
        g = frame[local == d]
        tt += math.log(g["close"].iloc[-1] / g["open"].iloc[0])
        c = g["close"].to_numpy()
        rets += [math.log(c[j] / c[j - 1]) for j in range(1, len(c))]
    return tt, float(np.std(rets, ddof=1)) * math.sqrt(6)


def test_class_constants():
    s = MultiSessionTrendPullback
    assert mod.RULE_ID == "P-030"
    assert s.name.startswith("P-030") and s.timeframe_min == 5
    assert s.warmup >= 6 * 113 + 113
    assert (s.rules.entry_start_after_open_min, s.rules.entry_end_before_close_min,
            s.rules.flatten_before_close_min) == (60, 59, 5)
    assert s.params == {
        "trend_sessions": 5, "scale_sessions": 5, "pullback_bars": 6, "scale_horizon_bars": 6, "z_entry": 1.0,
        "stop_scale_mult": 1.5, "hold_bars": 9, "entry_start_minute_of_day": 600, "min_minutes_to_close_entry": 60,
        "flatten_minutes_to_close": 15, "cooldown_bars": 2, "max_entries_per_day": 4}
    assert "symbol" not in vars(s)
    assert N == 113


def test_causal_and_matches_the_live_window():
    s = strategy()
    frame = synthetic_sessions()
    prepared = s.prepare(frame)
    assert (prepared["tm_side"] > 0).any() and (prepared["tm_side"] < 0).any()
    assert causality_problems(s, frame) == []
    assert window_parity_problems(s, frame, samples=40) == []
    for steps, sign in (({15: -30.0}, 1), ({15: 30.0}, -1), ({15: -30.0, 25: -30.0, 60: -40.0}, 1)):
        hand, _ = hand_frame(steps, sign)
        assert (s.prepare(hand)["tm_side"] != 0).sum() >= 1
        assert causality_problems(s, hand) == []
        assert window_parity_problems(s, hand, samples=60) == []


def test_trend_and_scale_match_an_independent_computation():
    frame = synthetic_sessions(days=9, seed=5)
    out = strategy().prepare(frame)
    local = frame["time"].dt.tz_convert(market("WIN").zone).dt.date
    days = sorted(set(local))
    for k, d in enumerate(days):
        g = out[out["local_date"] == d]
        if k < 5:
            assert g["tm_trend"].isna().all() and (g["tm_raw"] == 0).all()
            continue
        tt, ss = reference_T_s(frame, d)
        assert np.allclose(g["tm_trend"], tt, rtol=0, atol=1e-12) and np.allclose(g["tm_scale"], ss, rtol=1e-9)
        c = g["close"].to_numpy()
        for j in range(len(g)):
            if j < 6:
                assert (g["tm_raw"].iloc[j] == 0)
                continue
            r = math.log(c[j] / c[j - 6])
            want = 1 if (tt > 0 and r <= -ss * (1 - 1e-9)) else -1 if (tt < 0 and r >= ss * (1 - 1e-9)) else 0
            assert g["tm_raw"].iloc[j] == want


def test_long_in_an_uptrend_with_the_stop_and_the_45_minute_exit():
    frame, last = hand_frame({15: -30.0})
    tt, ss = reference_T_s(frame, TARGET)
    assert tt > 0
    p = prepared_target({15: -30.0})
    assert p["tm_side"].to_numpy().nonzero()[0].tolist() == [15]
    (t,) = run(frame, strategy(), OPT, BacktestConfig()).trades
    close_t = last - 30.0
    assert (t.side, t.entry_price, t.entry_reason) == ("long", close_t, "trend_pullback_long")
    assert hhmm(t.entry_time) == at(16)
    assert t.stop_price == tick_floor(close_t * (1.0 - 1.5 * ss), 5.0)
    assert t.stop_price < close_t and t.stop_price % 5.0 == 0.0
    # decided at the close of bar 24 (9 bars after the signal bar), filled at the open of bar 25: 9 bars held = 45 minutes
    assert t.exit_reason == "time_exit_9_bars" and hhmm(t.exit_time) == at(25) and t.exit_price == close_t
    assert (t.exit_time - t.entry_time) == pd.Timedelta(minutes=45)


def test_short_in_a_downtrend_mirrors_with_a_stop_above():
    frame, last = hand_frame({15: 30.0}, sign=-1)
    tt, ss = reference_T_s(frame, TARGET)
    assert tt < 0
    (t,) = run(frame, strategy(), OPT, BacktestConfig()).trades
    close_t = last + 30.0
    assert (t.side, t.entry_price, t.entry_reason) == ("short", close_t, "trend_pullback_short")
    assert t.stop_price == tick_ceil(close_t * (1.0 + 1.5 * ss), 5.0)
    assert t.stop_price > close_t and t.stop_price % 5.0 == 0.0
    assert t.exit_reason == "time_exit_9_bars" and (t.exit_time - t.entry_time) == pd.Timedelta(minutes=45)


def test_never_trades_with_the_trend_nor_without_a_trend():
    assert trades_for({15: 30.0}, sign=1) == []             # a rally in an up-trend
    assert trades_for({15: -30.0}, sign=-1) == []           # a dip in a down-trend
    assert trades_for({15: -30.0}, sign=0) == []            # no trend and no scale
    assert (prepared_target({15: 30.0}, sign=1)["tm_raw"] == 0).all()


def test_a_small_pullback_below_one_scale_does_not_trade():
    frame, _ = hand_frame({})
    _, ss = reference_T_s(frame, TARGET)
    close = float(frame["close"].iloc[-1])
    small = 5.0 * math.floor(0.5 * ss * close / 5.0)         # about half a scale, on the grid
    assert 0 < small < ss * close
    assert prepared_target({15: -small})["tm_side"].eq(0).all()


def test_a_stop_is_hit_in_the_bar_and_exits_at_the_stop_price():
    frame, ss = None, None
    frame, last = hand_frame({15: -30.0, 16: -400.0})
    _, ss = reference_T_s(frame, TARGET)
    stop = tick_floor((last - 30.0) * (1.0 - 1.5 * ss), 5.0)
    (t, *_) = run(frame, strategy(), OPT, BacktestConfig()).trades
    assert t.side == "long" and t.exit_reason == "stop_loss" and t.exit_price == stop
    assert hhmm(t.exit_time) == at(17)
    frame, last = hand_frame({15: 30.0, 16: 400.0}, sign=-1)
    _, ss = reference_T_s(frame, TARGET)
    stop = tick_ceil((last + 30.0) * (1.0 + 1.5 * ss), 5.0)
    (t, *_) = run(frame, strategy(), OPT, BacktestConfig()).trades
    assert t.side == "short" and t.exit_reason == "stop_loss" and t.exit_price == stop


def test_entry_window_starts_at_10_and_ends_60_minutes_before_the_close():
    p = prepared_target({8: -30.0})                         # setup from bar 8; bar 11 closes at 10:00
    assert (p["tm_raw"].iloc[8:14] == 1).all()
    assert p["tm_side"].to_numpy().nonzero()[0].tolist() == [11]
    (t,) = trades_for({8: -30.0})
    assert hhmm(t.entry_time) == at(12) == "10:00"
    p = prepared_target({100: -30.0})                       # bar 100 closes with minutes_to_close == 60
    assert p["minutes_to_close"].iloc[100] == 60.0
    assert p["tm_side"].to_numpy().nonzero()[0].tolist() == [100]
    (t,) = trades_for({100: -30.0})
    assert hhmm(t.entry_time) == at(101) and hhmm(t.exit_time) == at(110)
    p = prepared_target({101: -30.0})                       # one bar later: minutes_to_close 55 -> no entry
    assert (p["tm_raw"].iloc[101:107] == 1).all() and (p["tm_side"] == 0).all()
    assert trades_for({101: -30.0}) == []


def test_cooldown_of_two_bars_and_at_most_four_entries_a_day():
    # first entry decided at bar 15, exit decided at bar 24 and stamped at the open of bar 25: bars 25 and 26 are cooldown
    p = prepared_target({15: -30.0, 25: -30.0})
    assert (p["tm_raw"].iloc[25:31] == 1).all()
    assert p["tm_side"].to_numpy().nonzero()[0].tolist() == [15, 27]
    # drops at 15, 27, 39, 51, 63: the 5th setup is not taken
    steps = {k: -30.0 for k in (15, 27, 39, 51, 63)}
    p = prepared_target(steps)
    assert p["tm_raw"].iloc[63] == 1
    assert p["tm_side"].to_numpy().nonzero()[0].tolist() == [15, 27, 39, 51]
    trades = trades_for(steps)
    assert len(trades) == 4 and all(t.side == "long" for t in trades)
    assert [hhmm(t.entry_time) for t in trades] == [at(k) for k in (16, 28, 40, 52)]
    for a, b in zip(trades, trades[1:]):
        assert a.exit_time <= b.entry_time
    assert strategy().params["max_entries_per_day"] == 4


def test_synthetic_sessions_trade_and_never_hold_overnight():
    frames = [synthetic_sessions(), hand_frame({k: -30.0 for k in (15, 27, 39, 51, 63)})[0]]
    for frame in frames:
        r = run(frame, strategy(), market("WIN").cost("base"), BacktestConfig())
        assert r.trades
        assert r.positions_held_overnight == 0
        zone = market("WIN").zone
        per_day = pd.Series([t.entry_time.tz_convert(zone).date() for t in r.trades]).value_counts()
        assert max(per_day) <= 4
        assert all(t.exit_time.tz_convert(zone).date() == t.entry_time.tz_convert(zone).date() for t in r.trades)
