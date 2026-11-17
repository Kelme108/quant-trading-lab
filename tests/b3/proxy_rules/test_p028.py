"""P-028 WinSessionVarianceRatioSwitch on SYNTHETIC WIN session 5-minute bars (Sao Paulo time, bars from the calendar's
session open to its close): class constants, causality, live-window parity, the day's own A / B / VR / S / M against an
independent loop, the entry window, hand-built days (TREND long and short, REVERT short and long, the stop, the 30-minute
time exit, signals at the exit bar, the 5-entry cap) and no overnight position."""

import math
import random
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

from b3.backtest import BacktestConfig, run
from b3.calendar import B3SessionCalendar
from b3.checks import causality_problems, window_parity_problems
from b3.markets import market
from b3.proxy_rules import p028_win_session_variance_ratio_switch as mod
from b3.proxy_rules.p028_win_session_variance_ratio_switch import WinSessionVarianceRatioSwitch
from b3.strategy import tick_ceil, tick_floor

UTC = timezone.utc
CAL = B3SessionCalendar("WIN")
COLS = ["time", "open", "high", "low", "close", "volume"]
BASE = 120000.0
PRIOR_DAYS = 4                      # more than the 240-bar warm-up before the target day
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


def rows_of(day, closes, prev_close):
    s = CAL.session(day)
    rows, prev = [], prev_close
    for k, c in enumerate(closes):
        rows.append((pd.Timestamp((s.open + timedelta(minutes=5 * k)).astimezone(UTC)), prev, max(prev, c),
                     min(prev, c), c, 100.0))
        prev = c
    return rows, prev


def path(steps, n=N):
    """Closes of the target day: BASE plus the cumulative sum of `steps` ({bar index: close change})."""
    closes, cur = [], BASE
    for k in range(n):
        cur += steps.get(k, 0.0)
        closes.append(cur)
    return closes


def ramp(start, step, count):
    return {start + k: step for k in range(count)}


def hand_frame(target_closes, prior=PRIOR_DAYS):
    """`prior` flat sessions at BASE (no bar moves), then the target day: each bar opens at the previous close."""
    rows, prev = [], BASE
    for d in trading_days_before(TARGET, prior):
        n = int((CAL.session(d).close - CAL.session(d).open).total_seconds() // 300)
        r, prev = rows_of(d, [BASE] * n, prev)
        rows += r
    r, prev = rows_of(TARGET, target_closes, prev)
    rows += r
    return pd.DataFrame(rows, columns=COLS)


def synthetic_sessions(days=14, seed=21, start=BASE, step=5.0):
    """Random walk of 5-minute bars moving by -3..+3 ticks per bar."""
    m = market("WIN")
    rng = random.Random(seed)
    d, rows, prev = date(2026, 1, 5), [], start
    while len({r[0].date() for r in rows}) < days:
        if CAL.is_trading_day(d):
            t = datetime.combine(d, m.open, m.zone)
            end = datetime.combine(d, m.close, m.zone)
            while t + timedelta(minutes=5) <= end:
                o = prev
                c = o + step * rng.randint(-3, 3)
                rows.append((t, o, max(o, c) + step * rng.randint(0, 1), min(o, c) - step * rng.randint(0, 1), c,
                             float(rng.randint(50, 500))))
                prev, t = c, t + timedelta(minutes=5)
        d += timedelta(days=1)
    return pd.DataFrame([(pd.Timestamp(r[0].astimezone(UTC)),) + r[1:] for r in rows], columns=COLS)


def strategy():
    return WinSessionVarianceRatioSwitch.on("WIN")()


def trades_for(steps_or_closes):
    closes = steps_or_closes if isinstance(steps_or_closes, list) else path(steps_or_closes)
    return run(hand_frame(closes), strategy(), OPT, BacktestConfig()).trades


def prepared_target(steps_or_closes):
    closes = steps_or_closes if isinstance(steps_or_closes, list) else path(steps_or_closes)
    out = strategy().prepare(hand_frame(closes))
    return out[out["local_date"] == TARGET].reset_index(drop=True)


def hhmm(ts):
    return ts.tz_convert(market("WIN").zone).strftime("%H:%M")


def at(bar):
    """Clock time (HH:MM) of the open of target-day bar `bar` (0-based)."""
    return hhmm(pd.Timestamp((CAL.session(TARGET).open + timedelta(minutes=5 * bar)).astimezone(UTC)))


def reference(opens_closes):
    """Independent per-bar (A, B, VR, S, M, raw side) of ONE session, from the proposal's formulas (t counted from 1)."""
    out = []
    o1 = opens_closes[0][0]
    cl = [c for _, c in opens_closes]
    r = [math.log(cl[0] / o1)] + [math.log(cl[j] / cl[j - 1]) for j in range(1, len(cl))]
    for t in range(1, len(cl) + 1):
        a = sum(x * x for x in r[:t]) / t
        if t >= 4:
            b = sum((r[j - 1] + r[j - 2] + r[j - 3]) ** 2 for j in range(3, t + 1)) / (t - 2)
            m = math.log(cl[t - 1] / cl[t - 4])
        else:
            b = (sum((r[j - 1] + r[j - 2] + r[j - 3]) ** 2 for j in range(3, t + 1)) / (t - 2)) if t >= 3 else math.nan
            m = math.nan
        if t < 4 or a == 0:
            out.append((a, b, math.nan, math.nan, m, 0))
            continue
        vr, s = b / (3 * a), math.sqrt(3 * a)
        side = 0
        if abs(m) >= 0.75 * s * (1 - 1e-9) and m != 0:
            if vr >= 1.15 * (1 - 1e-9):
                side = 1 if m > 0 else -1
            elif vr <= 0.87 * (1 + 1e-9):
                side = -1 if m > 0 else 1
        out.append((a, b, vr, s, m, side))
    return out


# TREND: every bar +5 up to bar 23, flat afterwards. REVERT: a zigzag of +-10 then three equal steps at bars 21..23.
UP_RAMP = ramp(0, 5.0, 24)
DOWN_RAMP = ramp(0, -5.0, 24)


def zigzag(final_sign):
    steps = {k: (-10.0 if k % 2 == 0 else 10.0) * final_sign * -1 for k in range(21)}   # bar 20 has the sign -final
    steps.update({k: 10.0 * final_sign for k in (21, 22, 23)})
    return steps


def test_class_constants():
    s = WinSessionVarianceRatioSwitch
    assert mod.RULE_ID == "P-028"
    assert s.name.startswith("P-028") and s.timeframe_min == 5
    assert s.warmup >= 113 + 24                              # a whole session plus the 24-bar statistic build-up
    assert (s.rules.entry_start_after_open_min, s.rules.entry_end_before_close_min,
            s.rules.flatten_before_close_min) == (5, 44, 5)
    assert s.params == {
        "vr_lag_bars": 3, "min_bar_in_day_at_signal": 24, "vr_trend_min": 1.15, "vr_revert_max": 0.87, "move_bars": 3,
        "move_min_scale": 0.75, "stop_pct": 0.3, "hold_bars": 6, "min_minutes_to_close_at_signal": 45,
        "max_entries_per_day": 5}
    assert "symbol" not in vars(s)
    assert N == 113


def test_causal_and_matches_the_live_window():
    s = strategy()
    frame = synthetic_sessions()
    prepared = s.prepare(frame)
    assert (prepared["vr_side"] != 0).sum() >= 10          # the synthetic data really produce signals
    assert (prepared["vr_side"] > 0).any() and (prepared["vr_side"] < 0).any()
    assert causality_problems(s, frame) == []
    assert window_parity_problems(s, frame, samples=40) == []
    for steps in (UP_RAMP, zigzag(1), {**zigzag(-1), **ramp(60, 5.0, 24)}):
        hand = hand_frame(path(steps))
        assert (s.prepare(hand)["vr_side"] != 0).sum() >= 1
        assert causality_problems(s, hand) == []
        assert window_parity_problems(s, hand, samples=80) == []


def test_the_statistics_use_only_todays_bars_and_match_the_formulas():
    frame = synthetic_sessions(days=6, seed=4)
    out = strategy().prepare(frame)
    for _, g in out.groupby("local_date"):
        ref = reference(list(zip(g["open"], g["close"])))
        a, b = g["vr_ratio"].to_numpy(), g["vr_move"].to_numpy()
        for k, (ra, rb, rvr, rs, rm, rside) in enumerate(ref):
            if k >= 3:
                assert abs(b[k] - rm) < 1e-15 and abs(g["vr_scale"].iloc[k] - rs) < 1e-12
                assert abs(a[k] - rvr) < 1e-9 * max(1.0, abs(rvr))
            assert g["vr_raw"].iloc[k] == rside
    # the first bar's return uses its open; nothing carries over from the previous session
    first = out[out["local_date"] == out["local_date"].iloc[0]].iloc[:5]
    only = strategy().prepare(frame[frame["time"] >= first["time"].iloc[0]].reset_index(drop=True))
    day2 = out["local_date"].unique()[1]
    a1 = out[out["local_date"] == day2]["vr_ratio"].to_numpy()
    a2 = only[only["local_date"] == day2]["vr_ratio"].to_numpy()
    assert np.allclose(a1, a2, equal_nan=True, rtol=0, atol=1e-12)
    # on this data both regimes and the no-trade band occur, and the band never produces a raw signal
    ratio = out["vr_ratio"]
    assert (ratio >= 1.15).any() and (ratio <= 0.87).any()
    band = (ratio > 0.87) & (ratio < 1.15)
    assert band.any() and (out.loc[band, "vr_raw"] == 0).all()


def test_the_regimes_of_the_hand_built_days():
    t = prepared_target(UP_RAMP)
    assert t["vr_ratio"].iloc[23] > 2.9 and t["vr_raw"].iloc[23] == 1
    t = prepared_target(zigzag(1))
    assert t["vr_ratio"].iloc[23] <= 0.87 and t["vr_move"].iloc[23] > 0
    assert t["vr_move"].iloc[23] >= 0.75 * t["vr_scale"].iloc[23] and t["vr_raw"].iloc[23] == -1
    t = prepared_target(zigzag(-1))
    assert t["vr_ratio"].iloc[23] <= 0.87 and t["vr_move"].iloc[23] < 0 and t["vr_raw"].iloc[23] == 1
    t = prepared_target(DOWN_RAMP)
    assert t["vr_ratio"].iloc[23] > 2.9 and t["vr_raw"].iloc[23] == -1


def test_trend_long_with_the_stop_and_the_30_minute_time_exit():
    (t,) = trades_for(UP_RAMP)
    close_t = BASE + 120.0                                   # close of bar 23
    assert (t.side, t.entry_price, t.entry_reason) == ("long", close_t, "variance_ratio_long")
    assert hhmm(t.entry_time) == at(24)                      # the open of the bar after the signal bar 23
    assert t.stop_price == tick_floor(close_t * (1.0 - 0.003), 5.0)
    assert t.stop_price < close_t and t.stop_price % 5.0 == 0.0
    # decided at the close of bar 29 (6 bars after the signal bar), filled at the open of bar 30: 6 bars = 30 minutes held
    assert t.exit_reason == "time_exit_6_bars" and hhmm(t.exit_time) == at(30) and t.exit_price == close_t
    assert (t.exit_time - t.entry_time) == pd.Timedelta(minutes=30)


def test_trend_short_mirrors_with_a_stop_above():
    (t,) = trades_for(DOWN_RAMP)
    close_t = BASE - 120.0
    assert (t.side, t.entry_price, t.entry_reason) == ("short", close_t, "variance_ratio_short")
    assert hhmm(t.entry_time) == at(24)
    assert t.stop_price == tick_ceil(close_t * (1.0 + 0.003), 5.0)
    assert t.stop_price > close_t and t.stop_price % 5.0 == 0.0
    assert t.exit_reason == "time_exit_6_bars" and hhmm(t.exit_time) == at(30) and t.exit_price == close_t


def test_revert_regime_fades_the_move_on_both_sides():
    (t,) = trades_for(zigzag(1))                             # last 15 minutes up in a mean-reverting day -> SHORT
    close_t = path(zigzag(1))[23]
    assert (t.side, t.entry_price, t.entry_reason) == ("short", close_t, "variance_ratio_short")
    assert hhmm(t.entry_time) == at(24) and t.stop_price == tick_ceil(close_t * 1.003, 5.0) and t.stop_price > close_t
    assert t.exit_reason == "time_exit_6_bars" and hhmm(t.exit_time) == at(30)
    (t,) = trades_for(zigzag(-1))                            # last 15 minutes down -> LONG
    close_t = path(zigzag(-1))[23]
    assert (t.side, t.entry_price, t.entry_reason) == ("long", close_t, "variance_ratio_long")
    assert t.stop_price == tick_floor(close_t * 0.997, 5.0) and t.stop_price < close_t and t.stop_price % 5.0 == 0.0
    assert t.exit_reason == "time_exit_6_bars" and hhmm(t.exit_time) == at(30)


def test_no_signal_before_the_24th_bar_and_none_on_a_flat_day():
    # a ramp over bars 0..14 would signal at bar 14 (VR = 3, M = 3 steps) but the first 2 hours only build the statistic
    t = prepared_target(ramp(0, 5.0, 15))
    assert t["vr_raw"].iloc[14] == 1 and (t["vr_side"].iloc[:24] == 0).all()
    assert trades_for(ramp(0, 5.0, 15)) == []
    assert trades_for({}) == []                              # A = 0: no signal at all
    assert (prepared_target({})["vr_raw"] == 0).all()
    # the 24th bar (bar_in_day 23) is the first allowed signal bar
    assert prepared_target(UP_RAMP)["vr_side"].to_numpy().nonzero()[0].tolist() == [23]


def test_signal_window_ends_45_minutes_before_the_close():
    t = prepared_target(ramp(0, 5.0, N))
    assert t["minutes_to_close"].iloc[103] == 45.0 and t["minutes_to_close"].iloc[104] == 40.0
    late = prepared_target(ramp(0, 5.0, N))
    assert (late["vr_raw"].iloc[104:] == 1).all()            # the raw setup holds to the end ...
    assert (late["vr_side"].iloc[104:] == 0).all()           # ... but no signal after minutes_to_close < 45
    assert late["vr_side"].iloc[:104].astype(bool).sum() >= 1
    trades = trades_for(ramp(0, 5.0, N))
    assert max(t.entry_time for t in trades) <= pd.Timestamp(
        (CAL.session(TARGET).close - timedelta(minutes=45)).astimezone(UTC))


def test_a_stop_is_hit_in_the_bar_and_exits_at_the_stop_price():
    stop = tick_floor((BASE + 120.0) * (1.0 - 0.003), 5.0)
    (t, *_) = trades_for({**UP_RAMP, 24: -400.0})            # the entry bar itself closes 400 points lower
    assert t.side == "long" and t.exit_reason == "stop_loss" and t.exit_price == stop
    assert hhmm(t.exit_time) == at(25)                       # stamped at the close of the bar that hit the stop
    stop_s = tick_ceil((BASE - 120.0) * (1.0 + 0.003), 5.0)
    (t, *_) = trades_for({**DOWN_RAMP, 24: 400.0})
    assert t.side == "short" and t.exit_reason == "stop_loss" and t.exit_price == stop_s
    # a move smaller than 0.30% does not stop out: 300 points of 120120 is 0.2497%
    (t, *_) = trades_for({**UP_RAMP, 25: -300.0, 26: 300.0})
    assert t.exit_reason == "time_exit_6_bars"


def test_five_entries_a_day_at_most_and_a_signal_at_the_exit_bar_is_allowed():
    s = strategy()
    p = prepared_target(ramp(0, 5.0, N))
    assert (p["vr_raw"].iloc[23:104] == 1).all()
    # entries decided at 23 and then at every exit bar (the 7th bar after the previous signal bar): 30, 37, 44, 51
    assert p["vr_side"].to_numpy().nonzero()[0].tolist() == [23, 30, 37, 44, 51]
    assert p["vr_raw"].iloc[58] == 1 and p["vr_side"].iloc[58] == 0     # a 6th setup is not taken
    trades = trades_for(ramp(0, 5.0, N))
    assert len(trades) == 5 and all(t.side == "long" for t in trades)
    assert [hhmm(t.entry_time) for t in trades] == [at(k) for k in (24, 31, 38, 45, 52)]
    assert [hhmm(t.exit_time) for t in trades] == [at(k) for k in (30, 37, 44, 51, 58)]
    for a, b in zip(trades, trades[1:]):
        assert a.exit_time <= b.entry_time
    assert s.params["max_entries_per_day"] == 5


def test_synthetic_sessions_trade_and_never_hold_overnight():
    frames = [synthetic_sessions(), hand_frame(path(ramp(0, 5.0, N)))]
    for frame in frames:
        r = run(frame, strategy(), market("WIN").cost("base"), BacktestConfig())
        assert r.trades
        assert r.positions_held_overnight == 0
        per_day = pd.Series([t.entry_time.tz_convert(market("WIN").zone).date() for t in r.trades]).value_counts()
        assert max(per_day) <= 5
        assert all(t.exit_time.tz_convert(market("WIN").zone).date()
                   == t.entry_time.tz_convert(market("WIN").zone).date() for t in r.trades)
