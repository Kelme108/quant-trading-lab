"""P-009 MonthEndRebalancingLastHour on SYNTHETIC session-only 5-minute bars: class constants, causality, live-window
parity, hand-built month-end days (short and long entry with the 0.4% stop, stop hit, skipped days) and no overnight
position."""

import random
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import pytest

from b3.backtest import BacktestConfig, run
from b3.checks import causality_problems, window_parity_problems
from b3.events import event_times
from b3.markets import ProxySessionCalendar, market
from b3.proxy_rules import p009_month_end_rebalancing_last_hour as mod
from b3.proxy_rules.p009_month_end_rebalancing_last_hour import MonthEndRebalancingLastHour

UTC = timezone.utc
BARS = 78                      # 09:30-16:00 in 5-minute bars
PRIOR_DAYS = 32                # 32 * 78 = 2496 bars, more than warmup (2400)
SIGNAL_BAR = 65                # opens 14:55
ENTRY_BAR = 66                 # opens 15:00


def weekdays_before(day, n):
    out, d = [], day
    while len(out) < n:
        d -= timedelta(days=1)
        if d.weekday() < 5:
            out.append(d)
    return sorted(out)


def session_rows(symbol, day, bars):
    m = market(symbol)
    t0 = datetime.combine(day, m.open, m.zone)
    return [(pd.Timestamp((t0 + timedelta(minutes=5 * k)).astimezone(UTC)), o, h, lo, c, 100.0)
            for k, (o, h, lo, c) in enumerate(bars)]


def flat(level, n=BARS):
    return [(level, level, level, level)] * n


def hand_frame(target_day, target_bars, symbol="US500", overrides=None, prior_days=PRIOR_DAYS):
    """`prior_days` flat sessions at 5000 (the dict `overrides` replaces some of them), then the target session."""
    overrides = overrides or {}
    rows = []
    for d in weekdays_before(target_day, prior_days):
        rows += session_rows(symbol, d, overrides.get(d, flat(5000.0)))
    rows += session_rows(symbol, target_day, target_bars)
    return pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])


def synthetic_sessions(symbol, days=75, seed=3, start=5000.0, step=0.5):
    m = market(symbol)
    rng = random.Random(seed)
    d, rows, prev = date(2026, 1, 5), [], start
    while len({r[0].date() for r in rows}) < days:
        if d.weekday() < 5:
            t = datetime.combine(d, m.open, m.zone)
            end = datetime.combine(d, m.close, m.zone)
            while t + timedelta(minutes=5) <= end:
                o = prev + step * rng.randint(-3, 3)
                c = o + step * rng.randint(-6, 6)
                rows.append((t, o, max(o, c) + step * rng.randint(0, 3), min(o, c) - step * rng.randint(0, 3), c,
                             float(rng.randint(50, 500))))
                prev, t = c, t + timedelta(minutes=5)
        d += timedelta(days=1)
    return pd.DataFrame([(pd.Timestamp(r[0].astimezone(UTC)),) + r[1:] for r in rows],
                        columns=["time", "open", "high", "low", "close", "volume"])


def result_of(frame, symbol="US500"):
    return run(frame, MonthEndRebalancingLastHour.on(symbol)(), market(symbol).cost("optimistic"), BacktestConfig())


MONTH_END = date(2026, 3, 31)       # Tuesday; February 2026 ended on Friday the 27th


def test_class_constants():
    s = MonthEndRebalancingLastHour
    assert mod.RULE_ID == "P-009"
    assert s.name.startswith("P-009") and s.timeframe_min == 5
    assert s.warmup >= 22 * BARS + BARS
    assert s.rules.entry_start_after_open_min == 330 and s.rules.entry_end_before_close_min == 59
    assert s.rules.flatten_before_close_min == 5
    p = s.params
    assert p["last_sessions_of_month"] == 3 and p["signal_bar_open_minute_of_day"] == 895
    assert p["entry_minutes_before_close"] == 60 and p["mtd_threshold_frac"] == 0.005
    assert p["stop_frac"] == 0.004 and p["flatten_before_close_min"] == 5 and p["max_hold_minutes"] == 55
    assert p["max_entries_per_day"] == 1 and p["skip_fomc_days"] == 1
    assert "symbol" not in vars(s)


def test_causal_and_matches_the_live_window():
    strategy = MonthEndRebalancingLastHour.on("US500")()
    frame = synthetic_sessions("US500", days=75)
    assert causality_problems(strategy, frame) == []
    assert window_parity_problems(strategy, frame, samples=150) == []
    # frames that actually contain entry days (short and long)
    for level in (5030.0, 4970.0):
        hand = hand_frame(MONTH_END, flat(level))
        assert causality_problems(strategy, hand) == []
        assert window_parity_problems(strategy, hand, samples=200) == []


def test_short_entry_after_a_month_up_with_the_stop_0_4_percent_away():
    # R = 5030 / 5000 - 1 = +0.6% >= 0.5% -> short at the open of the 15:00 bar, stop = ceil(5030 * 1.004)
    (t,) = result_of(hand_frame(MONTH_END, flat(5030.0))).trades
    assert (t.side, t.entry_price, t.stop_price, t.entry_reason) == ("short", 5030.0, 5050.12, "month_up_sell_flow")
    assert t.entry_time.tz_convert(market("US500").zone).strftime("%H:%M") == "15:00"
    assert t.exit_reason == "end_of_day_flatten"
    assert t.exit_time.tz_convert(market("US500").zone).strftime("%H:%M") == "15:55"


def test_long_entry_after_a_month_down_with_the_stop_0_4_percent_away():
    # R = 4970 / 5000 - 1 = -0.6% -> long, stop = floor(4970 * 0.996)
    (t,) = result_of(hand_frame(MONTH_END, flat(4970.0))).trades
    assert (t.side, t.entry_price, t.stop_price, t.entry_reason) == ("long", 4970.0, 4950.12, "month_down_buy_flow")
    assert t.exit_reason == "end_of_day_flatten"


def test_stop_is_rounded_away_from_the_price():
    # 5030.01 * 1.004 = 5050.13004 -> ceil to 5050.14 ; 4969.99 * 0.996 = 4950.11204 -> floor to 4950.11
    (t,) = result_of(hand_frame(MONTH_END, flat(5030.01))).trades
    assert t.side == "short" and t.stop_price == 5050.14
    (t,) = result_of(hand_frame(MONTH_END, flat(4969.99))).trades
    assert t.side == "long" and t.stop_price == 4950.11


def test_entry_only_on_the_signal_bar_the_move_before_and_after_does_not_matter():
    # flat 5000 until the signal bar closes at 5030; the rest of the day is flat at 5030 as well
    bars = flat(5000.0, SIGNAL_BAR) + flat(5030.0, BARS - SIGNAL_BAR)
    (t,) = result_of(hand_frame(MONTH_END, bars)).trades
    assert t.side == "short" and t.entry_time.tz_convert(market("US500").zone).strftime("%H:%M") == "15:00"
    # at the signal bar the day is back at the reference: nothing, even if earlier bars were far away
    bars = flat(5100.0, SIGNAL_BAR - 1) + flat(5000.0, BARS - SIGNAL_BAR + 1)
    assert result_of(hand_frame(MONTH_END, bars)).trades == []


def test_stop_is_hit_when_the_price_runs_away_and_there_is_no_second_entry():
    bars = flat(5030.0, ENTRY_BAR + 2) + [(5030.0, 5060.0, 5030.0, 5058.0)] + flat(5058.0, BARS - ENTRY_BAR - 3)
    r = result_of(hand_frame(MONTH_END, bars))
    (t,) = r.trades
    assert t.side == "short" and t.exit_reason == "stop_loss" and t.stop_price == 5050.12


def test_reference_is_the_last_close_of_the_previous_months_last_session():
    # February 27th trades at 5100 all day and closes at 5000: the reference is 5000, so 5030 is +0.6% (short)
    feb27 = date(2026, 2, 27)
    overrides = {feb27: flat(5100.0, BARS - 1) + flat(5000.0, 1)}
    (t,) = result_of(hand_frame(MONTH_END, flat(5030.0), overrides=overrides)).trades
    assert t.side == "short"
    # and a last close of 5100 makes the same 5030 a -1.4% month (long)
    overrides = {feb27: flat(5000.0, BARS - 1) + flat(5100.0, 1)}
    trades = result_of(hand_frame(MONTH_END, flat(5030.0), overrides=overrides)).trades
    assert {t.side for t in trades} == {"long"}                       # Mar 27, 30 (5000: -2%) and Mar 31 (5030: -1.4%)
    assert trades[-1].entry_time.tz_convert(market("US500").zone).date() == MONTH_END


def test_no_trade_when_the_month_to_date_move_is_below_half_a_percent():
    assert result_of(hand_frame(MONTH_END, flat(5024.0))).trades == []        # +0.48%
    assert result_of(hand_frame(MONTH_END, flat(4976.0))).trades == []        # -0.48%
    assert len(result_of(hand_frame(MONTH_END, flat(5026.0))).trades) == 1    # +0.52%
    assert len(result_of(hand_frame(MONTH_END, flat(4974.0))).trades) == 1    # -0.52%


def test_only_the_last_three_sessions_of_the_month_trade():
    big_move = flat(5030.0)
    # Tue Mar 31, Mon Mar 30 and Fri Mar 27 are the last three sessions; Thu Mar 26 is the fourth from the end
    for day in (date(2026, 3, 31), date(2026, 3, 30), date(2026, 3, 27)):
        assert len(result_of(hand_frame(day, big_move)).trades) == 1, day
    for day in (date(2026, 3, 26), date(2026, 3, 18), date(2026, 3, 2)):
        assert result_of(hand_frame(day, big_move)).trades == [], day


def test_the_calendars_closed_days_move_the_window():
    closed = frozenset({date(2026, 3, 31)})
    cal = ProxySessionCalendar(market("US500"), MonthEndRebalancingLastHour.rules, closed_days=closed)
    strategy = MonthEndRebalancingLastHour.on("US500")(calendar=cal)
    prepared = strategy.prepare(hand_frame(date(2026, 3, 26), flat(5030.0)))
    assert bool(prepared["month_end_zone"].iloc[-1])                  # 27th and 30th remain: the 3rd from the end
    default = MonthEndRebalancingLastHour.on("US500")().prepare(hand_frame(date(2026, 3, 26), flat(5030.0)))
    assert not bool(default["month_end_zone"].iloc[-1])


def test_month_boundary_across_the_year():
    # 2025-12-31 is a Wednesday: the reference is the close of the last session of November 2025
    day = date(2025, 12, 31)
    (t,) = result_of(hand_frame(day, flat(5030.0))).trades
    assert t.side == "short"


def test_no_trade_on_fomc_days():
    assert date(2024, 1, 31) in {t.tz_convert("America/New_York").date() for t in event_times("FOMC")}
    assert result_of(hand_frame(date(2024, 1, 31), flat(5030.0))).trades == []          # FOMC, last session of January
    assert len(result_of(hand_frame(date(2024, 1, 30), flat(5030.0))).trades) == 1      # the day before: trades


def test_no_trade_on_a_half_day_without_the_1455_bar():
    bars = flat(5030.0, 42)                    # session closes at 13:00 -> no 14:55 bar
    assert result_of(hand_frame(MONTH_END, bars)).trades == []


def test_no_trade_without_a_previous_month_in_the_data():
    rows = []
    for d in [date(2026, 3, 2) + timedelta(days=k) for k in range(30) if (date(2026, 3, 2) + timedelta(days=k)).weekday() < 5
              and (date(2026, 3, 2) + timedelta(days=k)).month == 3]:
        rows += session_rows("US500", d, flat(5030.0))
    frame = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])
    prepared = MonthEndRebalancingLastHour.on("US500")().prepare(frame)
    assert prepared["ref_close"].isna().all() and prepared["mtd_move"].isna().all()


def test_never_holds_overnight():
    frames = [synthetic_sessions("US500", days=75), hand_frame(MONTH_END, flat(5030.0)),
              hand_frame(MONTH_END, flat(5030.0, ENTRY_BAR + 2) + [(5030.0, 5060.0, 5030.0, 5058.0)]
                         + flat(5058.0, BARS - ENTRY_BAR - 3))]
    for frame in frames:
        r = run(frame, MonthEndRebalancingLastHour.on("US500")(), market("US500").cost("base"), BacktestConfig())
        assert r.positions_held_overnight == 0
