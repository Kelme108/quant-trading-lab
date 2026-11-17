"""P-029 WinLowVolumeNodeTraversal on SYNTHETIC WIN session 1-minute bars (Sao Paulo time, bars from the calendar's session
open to its close): class constants, causality, live-window parity, hand-built days (long, short, stop, target, time exit,
profile conditions, target distance, entry window, entry cap) and no overnight position."""

import random
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

from b3.backtest import BacktestConfig, run
from b3.calendar import B3SessionCalendar
from b3.checks import causality_problems, window_parity_problems
from b3.markets import market
from b3.proxy_rules import p029_win_low_volume_node_traversal as mod
from b3.proxy_rules.p029_win_low_volume_node_traversal import WinLowVolumeNodeTraversal

UTC = timezone.utc
CAL = B3SessionCalendar("WIN")
COLS = ["time", "open", "high", "low", "close", "volume"]
FLAT = (120020.0, 120045.0, 120005.0, 120020.0)
PRIOR_DAYS = 3                      # 3 flat sessions (1695 bars) > the 1200-bar warm-up
TARGET = date(2026, 5, 13)
N = int((CAL.session(TARGET).close - CAL.session(TARGET).open).total_seconds() // 60)    # 565 bars
OPT = market("WIN").cost("optimistic")


def trading_days_before(day, n):
    out, d = [], day
    while len(out) < n:
        d -= timedelta(days=1)
        if CAL.is_trading_day(d):
            out.append(d)
    return sorted(out)


def lvl(k):
    """The middle of price bucket k (50 points): bars at lvl(k) with high lvl+25 and low lvl-15 stay inside bucket k."""
    return 50.0 * k + 20.0


def zone_bar(k, v=100.0):
    return (lvl(k), lvl(k) + 25.0, lvl(k) - 15.0, lvl(k), v)


def move_bar(o, c, v=10.0):
    return (o, max(o, c), min(o, c), c, v)


def day_bars(first, second, trig_close, a1=30, b1=30, a2=10, extra=0, trig_vol=10.0, post=(), pad=0):
    """Zone `first` for a1 bars (after `extra` bars in bucket first+1), a move to zone `second` (b1 bars), a move back, a2
    bars in `first`, the trigger bar closing at `trig_close`, then `post` (o, h, l, c, v) bars, then flat to the close."""
    bars = [zone_bar(first + 1) for _ in range(extra)] + [zone_bar(first) for _ in range(a1)]
    bars.append(move_bar(lvl(first), lvl(second)))
    bars += [zone_bar(second) for _ in range(b1 - 1)]
    bars.append(move_bar(lvl(second), lvl(first)))
    bars += [zone_bar(first) for _ in range(a2)]
    bars += [zone_bar(first, 1.0) for _ in range(pad)]          # low-volume padding that delays the trigger
    t = len(bars)
    bars.append(move_bar(lvl(first), trig_close, trig_vol))
    bars += list(post)
    last = bars[-1][3]
    bars += [(last, last + 3.0, last - 3.0, last, 100.0)] * (N - len(bars))
    return bars, t


def rows_of(day, bars):
    s = CAL.session(day)
    return [(pd.Timestamp((s.open + timedelta(minutes=k)).astimezone(UTC)),) + tuple(b[:4]) + (b[4],)
            for k, b in enumerate(bars)]


def hand_frame(bars, prior=PRIOR_DAYS):
    rows = []
    for d in trading_days_before(TARGET, prior):
        rows += rows_of(d, [zone_bar(2400)] * N)
    rows += rows_of(TARGET, bars)
    return pd.DataFrame(rows, columns=COLS)


def synthetic_sessions(days=6, seed=7, start=120000.0):
    """Price stays in a zone for 25-45 bars with a large volume, then crosses to another zone in 1-3 low-volume bars:
    high- and low-volume nodes and traversals happen."""
    m = market("WIN")
    rng = random.Random(seed)
    d, rows, prev = date(2026, 1, 5), [], start
    while len({r[0].date() for r in rows}) < days:
        if CAL.is_trading_day(d):
            t = datetime.combine(d, m.open, m.zone)
            end = datetime.combine(d, m.close, m.zone)
            center = round(prev / 5.0) * 5.0
            left = rng.randint(25, 45)
            while t + timedelta(minutes=1) <= end:
                if left > 0:
                    o = prev
                    c = center + 5.0 * rng.randint(-5, 5)
                    h, lo, v = max(o, c) + 5.0 * rng.randint(0, 3), min(o, c) - 5.0 * rng.randint(0, 3), float(rng.randint(80, 200))
                    left -= 1
                else:
                    center += rng.choice((-1, 1)) * 5.0 * rng.randint(50, 80)
                    left = rng.randint(25, 45)
                    o = prev
                    c = o + (center - o) * rng.choice((0.3, 0.5, 1.0))
                    c = round(c / 5.0) * 5.0
                    h, lo, v = max(o, c), min(o, c), float(rng.randint(5, 20))
                rows.append((t, o, h, lo, c, v))
                prev, t = c, t + timedelta(minutes=1)
        d += timedelta(days=1)
    return pd.DataFrame([(pd.Timestamp(r[0].astimezone(UTC)),) + r[1:] for r in rows], columns=COLS)


def run_frame(frame, cost=OPT):
    return run(frame, WinLowVolumeNodeTraversal.on("WIN")(), cost, BacktestConfig())


def trades_for(bars):
    return run_frame(hand_frame(bars)).trades


def prepared_target(bars):
    out = WinLowVolumeNodeTraversal.on("WIN")().prepare(hand_frame(bars))
    return out[out["local_date"] == TARGET].reset_index(drop=True)


def hhmm(ts):
    return ts.tz_convert(market("WIN").zone).strftime("%H:%M")


def at(bar):
    return hhmm(pd.Timestamp((CAL.session(TARGET).open + timedelta(minutes=bar)).astimezone(UTC)))


def flat_bars(level, count, v=10.0, half=3.0):
    return [(level, level + half, level - half, level, v)] * count


# long day: zones 2400 (first) and 2406 (second); trigger closes at 120070 (bucket 2401); T = 2406 * 50 = 120300
def long_day(post=(), **kw):
    return day_bars(2400, 2406, 120070.0, post=post, **kw)


# the long entry fills at the open of bar t + 1 = 72; the trigger bar is 71
LONG_UP = [(120070.0, 120080.0, 120065.0, 120075.0, 10.0), (120075.0, 120105.0, 120070.0, 120100.0, 10.0),
           (120100.0, 120205.0, 120095.0, 120200.0, 10.0), (120200.0, 120315.0, 120195.0, 120310.0, 10.0)]


def test_class_constants():
    s = WinLowVolumeNodeTraversal
    assert mod.RULE_ID == "P-029"
    assert s.name.startswith("P-029") and s.timeframe_min == 1
    assert s.warmup >= 2 * 565
    assert (s.rules.entry_start_after_open_min, s.rules.entry_end_before_close_min,
            s.rules.flatten_before_close_min) == (60, 60, 5)
    assert s.params == {
        "bucket_points": 50, "hvn_frac_of_poc": 0.5, "lvn_frac_of_poc": 0.2, "warmup_min_after_open": 60,
        "last_entry_min_before_close": 60, "min_target_distance_points": 200, "stop_points": 100, "max_hold_bars": 60,
        "flat_min_before_close": 5, "max_entries_per_day": 4}
    assert "symbol" not in vars(s)
    assert N == 565


def test_causal_and_matches_the_live_window():
    strategy = WinLowVolumeNodeTraversal.on("WIN")()
    frame = synthetic_sessions()
    prepared = strategy.prepare(frame)
    assert (prepared["lv_side"] != 0).sum() >= 3          # the synthetic data really produce signals
    assert causality_problems(strategy, frame) == []
    assert window_parity_problems(strategy, frame, samples=80) == []
    for bars, _ in (long_day(post=LONG_UP), day_bars(2406, 2400, 120270.0, post=[
            (120270.0, 120275.0, 120245.0, 120250.0, 10.0), (120250.0, 120255.0, 120040.0, 120045.0, 10.0)])):
        hand = hand_frame(bars)
        assert (strategy.prepare(hand)["lv_side"] != 0).sum() == 1
        assert causality_problems(strategy, hand) == []
        assert window_parity_problems(strategy, hand, samples=300) == []


def test_long_entry_with_the_stop_100_points_below_and_exit_at_the_target():
    bars, t = long_day(post=LONG_UP)
    assert t == 71
    prepared = prepared_target(bars)
    assert list(np.flatnonzero(prepared["lv_side"].to_numpy())) == [71]
    assert prepared["lv_target"].iloc[71] == 120300.0 and prepared["lv_stop"].iloc[71] == 119970.0
    (tr,) = trades_for(bars)
    assert (tr.side, tr.entry_price, tr.entry_reason) == ("long", 120070.0, "lvn_traversal_up")
    assert hhmm(tr.entry_time) == at(72)                       # the open of bar t + 1
    assert tr.stop_price == 119970.0 and tr.stop_price % 5.0 == 0.0 and tr.stop_price < 120070.0
    # bar 75 closes at 120310 >= T: EXIT decided there, filled at the open of bar 76
    assert tr.exit_reason == "target_reached" and hhmm(tr.exit_time) == at(76)
    assert tr.exit_price == 120310.0


def test_short_entry_mirrors_with_the_stop_100_points_above_and_exit_at_the_target():
    post = [(120270.0, 120275.0, 120245.0, 120250.0, 10.0), (120250.0, 120255.0, 120200.0, 120205.0, 10.0),
            (120205.0, 120210.0, 120040.0, 120045.0, 10.0)]
    bars, t = day_bars(2406, 2400, 120270.0, post=post)        # trigger: bucket 2406 -> 2405; T = 2401 * 50 = 120050
    prepared = prepared_target(bars)
    assert list(np.flatnonzero(prepared["lv_side"].to_numpy())) == [t]
    assert prepared["lv_target"].iloc[t] == 120050.0 and prepared["lv_stop"].iloc[t] == 120370.0
    (tr,) = trades_for(bars)
    assert (tr.side, tr.entry_price, tr.entry_reason) == ("short", 120270.0, "lvn_traversal_down")
    assert hhmm(tr.entry_time) == at(t + 1)
    assert tr.stop_price == 120370.0 and tr.stop_price % 5.0 == 0.0 and tr.stop_price > 120270.0
    assert tr.exit_reason == "target_reached" and hhmm(tr.exit_time) == at(t + 4) and tr.exit_price == 120045.0


def test_the_stop_is_hit_from_the_entry_bar_on():
    post = [(120070.0, 120075.0, 119960.0, 120020.0, 10.0)]    # trades down through 119970 on the entry bar
    bars, _ = long_day(post=post)
    (tr,) = trades_for(bars)
    assert tr.exit_reason == "stop_loss" and tr.exit_price == 119970.0 and hhmm(tr.exit_time) == at(73)
    # the signal bar's own low below the stop is not the entry bar: no stop exit
    bars, t = long_day(post=LONG_UP)
    bars[t] = (120020.0, 120070.0, 119900.0, 120070.0, 10.0)
    (tr,) = trades_for(bars)
    assert tr.exit_reason == "target_reached"


def test_time_exit_60_bars_after_the_entry_bar():
    bars, t = long_day(post=flat_bars(120070.0, 100))
    (tr,) = trades_for(bars)
    entry_bar = t + 1
    assert tr.exit_reason == "time_exit_60_bars"
    assert hhmm(tr.exit_time) == at(entry_bar + 60 + 1)        # decided at the close of the bar 60 after the entry bar
    assert tr.exit_price == 120070.0
    short_post = flat_bars(120270.0, 100)
    bars, t = day_bars(2406, 2400, 120270.0, post=short_post)
    (tr,) = trades_for(bars)
    assert tr.side == "short" and tr.exit_reason == "time_exit_60_bars" and hhmm(tr.exit_time) == at(t + 1 + 60 + 1)


def test_the_flat_exit_at_the_session_end():
    s = N - 62                                           # bar 503: its close is 61 minutes before the close; the 60-bar exit would fall after the flatten
    bars, t = long_day(pad=s - 71, post=flat_bars(120070.0, 100))
    assert t == s
    (tr,) = trades_for(bars)
    assert tr.exit_reason == "end_of_day_flatten" and hhmm(tr.exit_time) == at(N - 5)


def test_target_distance_is_at_least_200_points():
    # HVN bucket 2405 (T = 120250): a close at 120070 is 180 points away -> no trade; at 120050 exactly 200 -> trade
    bars, _ = day_bars(2400, 2405, 120070.0, post=LONG_UP)
    assert trades_for(bars) == []
    bars, _ = day_bars(2400, 2405, 120050.0, post=flat_bars(120050.0, 10))
    (tr,) = trades_for(bars)
    assert tr.side == "long" and tr.entry_price == 120050.0 and tr.stop_price == 119950.0


def test_the_bucket_below_the_close_must_be_an_hvn_and_the_close_bucket_an_lvn():
    # jump over the LVN: close in bucket 2402, bucket 2401 (below) is not an HVN
    bars, _ = long_day(post=LONG_UP)
    bars2, t = day_bars(2400, 2406, 120120.0, post=LONG_UP)
    assert trades_for(bars2) == [] and (prepared_target(bars2)["lv_side"] == 0).all()
    # bucket 2401 holds 1200 of volume (> 20% of the profile maximum): not an LVN
    bars3, _ = day_bars(2400, 2406, 120070.0, extra=12, post=LONG_UP)
    assert trades_for(bars3) == []
    # the same day with only 2 bars in bucket 2401 (<= 20%) trades
    bars4, _ = day_bars(2400, 2406, 120070.0, extra=2, post=LONG_UP)
    assert len(trades_for(bars4)) == 1
    # no HVN above: without the visit to the 2406 zone the first-zone profile has nothing above
    bars5, _ = day_bars(2400, 2401, 120070.0, post=LONG_UP)
    assert (prepared_target(bars5)["lv_side"] == 0).all()


def test_the_signal_bar_is_not_in_its_own_profile():
    bars, t = long_day(post=LONG_UP, trig_vol=1.0e7)      # if bar t counted, bucket 2401 would hold the maximum
    assert list(np.flatnonzero(prepared_target(bars)["lv_side"].to_numpy())) == [t]


def test_hvn_threshold_is_half_the_maximum():
    # zone 2406 holds 30 bars x 100 = ~3000 vs zone 2400 ~ 4000: HVN (>= 50%); with 12 bars it is below 50%
    bars, _ = day_bars(2400, 2406, 120070.0, b1=12, post=LONG_UP)
    assert (prepared_target(bars)["lv_side"] == 0).all()
    bars, _ = day_bars(2400, 2406, 120070.0, b1=22, post=LONG_UP)
    assert (prepared_target(bars)["lv_side"] != 0).sum() == 1


def test_signal_window_60_minutes_after_the_open_and_more_than_60_before_the_close():
    # first allowed bar: the close of bar 59 is 60 minutes after the open
    bars, t = day_bars(2400, 2406, 120070.0, a1=20, b1=20, a2=18, post=LONG_UP)
    assert t == 59 and len(trades_for(bars)) == 1
    bars, t = day_bars(2400, 2406, 120070.0, a1=20, b1=20, a2=17, post=LONG_UP)
    assert t == 58 and trades_for(bars) == []
    # last allowed bar: the close of bar 503 is 61 minutes before the close; bar 504 closes exactly 60 before: refused
    bars, t = day_bars(2400, 2406, 120070.0, pad=503 - 71, post=flat_bars(120070.0, 3))
    assert t == 503 and len(trades_for(bars)) == 1
    bars, t = day_bars(2400, 2406, 120070.0, pad=504 - 71, post=flat_bars(120070.0, 3))
    assert t == 504 and trades_for(bars) == []


def test_at_most_4_entries_a_day_enforced_by_the_rule():
    cycle = [(120020.0, 120070.0, 120020.0, 120070.0, 1.0),     # up-bar: the signal bar
             (120070.0, 120075.0, 119960.0, 120020.0, 1.0),     # entry bar: hits the stop 119970, closes back in 2400
             zone_bar(2400), zone_bar(2400)]
    bars, t = day_bars(2400, 2406, 120070.0, post=[])
    bars = bars[:t] + cycle * 5 + [zone_bar(2400)] * (N - t - 20)
    prepared = prepared_target(bars)
    assert (prepared["lv_side"] != 0).sum() == 4
    trades = trades_for(bars)
    assert len(trades) == 4 and all(x.side == "long" and x.exit_reason == "stop_loss" for x in trades)
    for a, b in zip(trades, trades[1:]):
        assert a.exit_time <= b.entry_time


def test_synthetic_sessions_trade_and_never_hold_overnight():
    for frame in (synthetic_sessions(), hand_frame(long_day(post=LONG_UP)[0])):
        r = run(frame, WinLowVolumeNodeTraversal.on("WIN")(), market("WIN").cost("base"), BacktestConfig())
        assert r.trades
        assert r.positions_held_overnight == 0
        per_day = pd.Series([x.entry_time.tz_convert(market("WIN").zone).date() for x in r.trades]).value_counts()
        assert max(per_day) <= 4
