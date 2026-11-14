"""P-008 LargeOpeningMoveReversal on SYNTHETIC session-only 5-minute bars: class constants, causality, live-window
parity, hand-built days (short fade, long fade, gap-fill exit, skipped days) and no overnight position."""

import random
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import pytest

from b3.backtest import BacktestConfig, run
from b3.checks import causality_problems, window_parity_problems
from b3.events import event_times
from b3.markets import market
from b3.proxy_rules import p008_large_opening_move_reversal as mod
from b3.proxy_rules.p008_large_opening_move_reversal import LargeOpeningMoveReversal

UTC = timezone.utc
BARS = 78                      # 09:30-16:00 in 5-minute bars
PRIOR_DAYS = 25                # more than warmup (1800 bars) / 78 sessions


def weekdays_before(day, n):
    out, d = [], day
    while len(out) < n:
        d -= timedelta(days=1)
        if d.weekday() < 5:
            out.append(d)
    return sorted(out)


def session_rows(symbol, day, bars):
    """bars: list of (open, high, low, close) for the session's 5-minute bars, from 09:30 New York."""
    m = market(symbol)
    t0 = datetime.combine(day, m.open, m.zone)
    return [(pd.Timestamp((t0 + timedelta(minutes=5 * k)).astimezone(UTC)), o, h, lo, c, 100.0)
            for k, (o, h, lo, c) in enumerate(bars)]


def flat(level, n=BARS):
    return [(level, level, level, level)] * n


def hand_frame(symbol, target_day, target_bars):
    """25 flat prior sessions at 5000 / 5005 alternating (|M| ~ 0.001; the last prior session closes at 5000.0),
    then the target session."""
    rows = []
    prior = weekdays_before(target_day, PRIOR_DAYS)
    for i, d in enumerate(prior):
        level = 5000.0 if (len(prior) - i) % 2 == 1 else 5005.0
        rows += session_rows(symbol, d, flat(level))
    rows += session_rows(symbol, target_day, target_bars)
    return pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])


def synthetic_sessions(symbol, days=45, seed=3, start=5000.0, step=0.5):
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


def up_day(c=5030.0, tail=None):
    """Opening bars 0..2 at c (+0.6% on prev close 5000), then `tail` bars or flat at c."""
    return flat(c, 3) + (tail if tail is not None else flat(c, BARS - 3))


def trade_of(frame, symbol="US500"):
    r = run(frame, LargeOpeningMoveReversal.on(symbol)(), market(symbol).cost("optimistic"), BacktestConfig())
    return r


def test_class_constants():
    s = LargeOpeningMoveReversal
    assert mod.RULE_ID == "P-008"
    assert s.name.startswith("P-008") and s.timeframe_min == 5
    assert s.warmup >= 20 * BARS + BARS
    assert s.rules.entry_start_after_open_min == 15 and s.rules.flatten_before_close_min == 5
    assert s.params["scale_lookback_sessions"] == 20 and s.params["threshold_mult"] == 1.5
    assert s.params["min_abs_move_frac"] == 0.002 and s.params["stop_extension_frac_of_move"] == 0.5
    assert s.params["signal_bar_in_day"] == 2 and s.params["time_exit_bar_in_day"] == 14
    assert s.params["max_hold_minutes"] == 60 and s.params["max_entries_per_day"] == 1
    assert "symbol" not in vars(s)


@pytest.mark.parametrize("symbol", ["US500", "USTEC"])
def test_causal_and_matches_the_live_window(symbol):
    strategy = LargeOpeningMoveReversal.on(symbol)()
    frame = synthetic_sessions(symbol, days=45)
    assert causality_problems(strategy, frame) == []
    assert window_parity_problems(strategy, frame, samples=60) == []
    # a frame that actually contains an entry day
    hand = hand_frame(symbol, date(2026, 3, 3), up_day(tail=flat(5030.0, 10) + flat(5000.0, BARS - 13)))
    assert causality_problems(strategy, hand) == []
    assert window_parity_problems(strategy, hand, samples=80) == []


@pytest.mark.parametrize("symbol", ["US500", "USTEC"])
def test_short_entry_after_a_large_up_open_with_the_extension_stop(symbol):
    r = trade_of(hand_frame(symbol, date(2026, 3, 3), up_day()), symbol)
    (t,) = r.trades
    # M = +0.6% >= 1.5 * ~0.1% and >= 0.2%; entry at the open of bar 3, stop = 5030 + 0.5 * 30
    assert (t.side, t.entry_price, t.stop_price, t.entry_reason) == ("short", 5030.0, 5045.0, "fade_large_up_open")
    assert t.entry_time.tz_convert(market(symbol).zone).strftime("%H:%M") == "09:45"
    # nothing happens afterwards: the time exit at the close of bar 14, filled at the open of bar 15 (10:45)
    assert t.exit_reason == "time_exit"
    assert t.exit_time.tz_convert(market(symbol).zone).strftime("%H:%M") == "10:45"


def test_long_entry_after_a_large_down_open_with_the_extension_stop():
    down = flat(4970.0, 3) + flat(4970.0, BARS - 3)
    (t,) = trade_of(hand_frame("US500", date(2026, 3, 3), down)).trades
    assert (t.side, t.entry_price, t.stop_price, t.entry_reason) == ("long", 4970.0, 4955.0, "fade_large_down_open")
    assert t.exit_reason == "time_exit"


def test_stop_is_rounded_away_from_the_price():
    # C = 5030.01, prev 5000: 5030.01 + 0.5 * 30.01 = 5045.015 -> short stop ceil to 5045.02
    (t,) = trade_of(hand_frame("US500", date(2026, 3, 3), flat(5030.01, BARS))).trades
    assert t.side == "short" and t.stop_price == 5045.02
    # C = 4969.99: 4969.99 - 0.5 * 30.01 = 4954.985 -> long stop floor to 4954.98
    (t,) = trade_of(hand_frame("US500", date(2026, 3, 3), flat(4969.99, BARS))).trades
    assert t.side == "long" and t.stop_price == 4954.98


def test_gap_fill_exit_at_the_next_open():
    tail = flat(5030.0, 3) + flat(5000.0, 1) + flat(5001.0, BARS - 7)       # bar 6 closes at prev_close
    (t,) = trade_of(hand_frame("US500", date(2026, 3, 3), up_day(tail=tail))).trades
    assert t.side == "short" and t.exit_reason == "gap_filled"
    assert t.exit_time.tz_convert(market("US500").zone).strftime("%H:%M") == "10:05"      # open of bar 7
    assert t.exit_price == 5001.0


def test_stop_is_hit_when_the_move_extends():
    tail = flat(5030.0, 2) + [(5030.0, 5050.0, 5030.0, 5048.0)] + flat(5048.0, BARS - 6)
    (t,) = trade_of(hand_frame("US500", date(2026, 3, 3), up_day(tail=tail))).trades
    assert t.side == "short" and t.exit_reason == "stop_loss" and t.stop_price == 5045.0


def test_no_trade_when_the_move_is_too_small_or_not_large_against_its_history():
    # +0.18% is above 1.5 * S but below the 0.2% floor
    assert trade_of(hand_frame("US500", date(2026, 3, 3), flat(5009.0, BARS))).trades == []
    # +0.3% but the 20-day scale is large (~0.5% moves every day): not >= 1.5 * S
    rows, prior = [], weekdays_before(date(2026, 3, 3), PRIOR_DAYS)
    for i, d in enumerate(prior):
        rows += session_rows("US500", d, flat(5000.0 if (len(prior) - i) % 2 == 1 else 5025.0))
    rows += session_rows("US500", date(2026, 3, 3), flat(5015.0))
    frame = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])
    assert trade_of(frame).trades == []


def test_no_trade_on_cpi_or_nfp_days():
    assert date(2026, 3, 11) in {t.tz_convert("America/New_York").date() for t in event_times("CPI")}
    assert date(2026, 3, 6) in {t.tz_convert("America/New_York").date() for t in event_times("NFP")}
    assert trade_of(hand_frame("US500", date(2026, 3, 11), up_day())).trades == []       # CPI
    assert trade_of(hand_frame("US500", date(2026, 3, 6), up_day())).trades == []        # NFP
    assert len(trade_of(hand_frame("US500", date(2026, 3, 3), up_day())).trades) == 1    # ordinary day


def test_no_trade_before_twenty_sessions_of_history():
    rows, prior = [], weekdays_before(date(2026, 3, 3), 10)
    for i, d in enumerate(prior):
        rows += session_rows("US500", d, flat(5000.0 if (len(prior) - i) % 2 == 1 else 5005.0))
    rows += session_rows("US500", date(2026, 3, 3), up_day())
    frame = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])
    prepared = LargeOpeningMoveReversal.on("US500")().prepare(frame)
    assert prepared["move_scale"].isna().all()


@pytest.mark.parametrize("symbol", ["US500", "USTEC"])
def test_never_holds_overnight(symbol):
    frames = [synthetic_sessions(symbol, days=45),
              hand_frame(symbol, date(2026, 3, 3), up_day(tail=flat(5030.0, BARS - 3)))]
    for frame in frames:
        r = run(frame, LargeOpeningMoveReversal.on(symbol)(), market(symbol).cost("base"), BacktestConfig())
        assert r.positions_held_overnight == 0
