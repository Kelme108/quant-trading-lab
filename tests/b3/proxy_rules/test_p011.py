"""P-011 RoundNumberRejectionFade on SYNTHETIC session-only 5-minute bars: class constants, causality, live-window
parity, hand-built days (short and long rejection with the 0.15% stop, spent levels, window edges, two entries at most,
FOMC skip) and no overnight position."""

import random
from datetime import date, datetime, timedelta, timezone

import pandas as pd

from b3.backtest import BacktestConfig, run
from b3.checks import causality_problems, window_parity_problems
from b3.markets import market
from b3.proxy_rules import p011_round_number_rejection_fade as mod
from b3.proxy_rules.p011_round_number_rejection_fade import RoundNumberRejectionFade

UTC = timezone.utc
BARS = 78                      # 09:30-16:00 in 5-minute bars
PRIOR_DAYS = 4                 # 4 * 78 = 312 bars, more than warmup (240)
BASE = 5030.0
DAY = date(2026, 3, 11)        # a Wednesday, no FOMC statement (the 2026 March one is the 18th)


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


def day_bars(overrides, base=BASE, n=BARS):
    """Flat at `base`; bar k replaced by overrides[k] = (open, high, low, close); the bars after it stay flat at its close."""
    out, last = [], base
    for k in range(n):
        bar = overrides.get(k, (last, last, last, last))
        out.append(bar)
        last = bar[3]
    return out


def hand_frame(overrides, day=DAY, symbol="US500"):
    rows = []
    for d in weekdays_before(day, PRIOR_DAYS):
        rows += session_rows(symbol, d, day_bars({}))
    rows += session_rows(symbol, day, day_bars(overrides))
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
                c = o + step * rng.randint(-8, 8)
                rows.append((t, o, max(o, c) + step * rng.randint(0, 6), min(o, c) - step * rng.randint(0, 6), c,
                             float(rng.randint(50, 500))))
                prev, t = c, t + timedelta(minutes=5)
        d += timedelta(days=1)
    return pd.DataFrame([(pd.Timestamp(r[0].astimezone(UTC)),) + r[1:] for r in rows],
                        columns=["time", "open", "high", "low", "close", "volume"])


def result_of(frame, symbol="US500"):
    return run(frame, RoundNumberRejectionFade.on(symbol)(), market(symbol).cost("optimistic"), BacktestConfig())


def ny(ts, fmt="%H:%M"):
    return ts.tz_convert(market("US500").zone).strftime(fmt)


SHORT_REJECT = {20: (5040.0, 5050.5, 5039.0, 5048.0)}          # touches 5050 from below, closes under it
LONG_REJECT = {20: (5060.0, 5061.0, 5049.5, 5052.0)}           # touches 5050 from above, closes over it


def test_class_constants():
    s = RoundNumberRejectionFade
    assert mod.RULE_ID == "P-011"
    assert s.name.startswith("P-011") and s.timeframe_min == 5
    assert s.warmup >= 2 * BARS
    assert s.rules.entry_start_after_open_min == 30 and s.rules.flatten_before_close_min == 5
    assert s.rules.entry_end_before_close_min in (64, 65)
    p = s.params
    assert p["level_grid_points"] == 50 and p["touch_tolerance_points"] == 1.0
    assert p["stop_beyond_level_frac"] == 0.0015
    assert p["first_decision_bar_open_minute"] == 595 and p["last_decision_bar_open_minute"] == 890
    assert p["entry_start_after_open_min"] == 30 and p["entry_end_before_close_min"] == 65
    assert p["hold_bars"] == 12 and p["max_hold_minutes"] == 60 and p["max_entries_per_day"] == 2
    assert p["skip_fomc_days"] == 1 and p["flatten_before_close_min"] == 5
    assert "symbol" not in vars(s)


def test_causal_and_matches_the_live_window():
    strategy = RoundNumberRejectionFade.on("US500")()
    frame = synthetic_sessions("US500", days=45)
    assert causality_problems(strategy, frame) == []
    assert window_parity_problems(strategy, frame, samples=150) == []
    for overrides in (SHORT_REJECT, LONG_REJECT):
        hand = hand_frame(overrides)
        assert causality_problems(strategy, hand) == []
        assert window_parity_problems(strategy, hand, samples=200) == []


def test_short_rejection_at_resistance_with_the_stop_0_15_percent_above_the_level():
    # Cp 5030 < 5050, high 5050.5 >= 5049, close 5048 < 5050, high < 5057.575 -> short at the open of bar 21 (11:15)
    (t,) = result_of(hand_frame(SHORT_REJECT)).trades
    assert (t.side, t.entry_price, t.stop_price, t.entry_reason) == ("short", 5048.0, 5057.58, "resistance_rejection")
    assert ny(t.entry_time) == "11:15"
    # time exit at the open of the 12th bar after the entry bar: bar 33 = 12:15 (60 minutes)
    assert ny(t.exit_time) == "12:15" and t.exit_reason == "time_exit_60min"


def test_long_rejection_at_support_with_the_stop_0_15_percent_below_the_level():
    # Cp 5070 > 5050, low 5049.5 <= 5051, close 5052 > 5050, low > 5042.425 -> long, stop = floor(5042.425)
    (t,) = result_of(_long_frame()).trades
    assert (t.side, t.entry_price, t.stop_price, t.entry_reason) == ("long", 5052.0, 5042.42, "support_rejection")
    assert ny(t.entry_time) == "11:15" and ny(t.exit_time) == "12:15"


def _long_frame():
    rows = []
    for d in weekdays_before(DAY, PRIOR_DAYS):
        rows += session_rows("US500", d, day_bars({}, base=5070.0))
    rows += session_rows("US500", DAY, day_bars(LONG_REJECT, base=5070.0))
    return pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])


def test_a_touch_that_closes_through_the_level_is_not_traded_and_spends_the_level():
    through = {20: (5040.0, 5053.0, 5039.0, 5052.0)}                                  # closes above 5050
    assert result_of(hand_frame(through)).trades == []
    # later the level is tested again from above with a textbook rejection: spent, so no trade
    again = dict(through)
    again[30] = (5052.0, 5053.0, 5049.5, 5051.0)
    assert result_of(hand_frame(again)).trades == []
    # the same bar 30 on a day without the first touch is a long entry (Cp 5060 > 5050)
    fresh ={29: (5060.0, 5060.0, 5060.0, 5060.0), 30: (5060.0, 5061.0, 5049.5, 5051.0)}
    (t,) = result_of(hand_frame(fresh)).trades
    assert t.side == "long"


def test_a_bar_that_reaches_the_stop_level_is_not_traded():
    # level 5050: stop level 5057.575. High 5058 reaches it -> no trade; high 5057.5 does not -> short
    assert result_of(hand_frame({20: (5040.0, 5058.0, 5039.0, 5048.0)})).trades == []
    (t,) = result_of(hand_frame({20: (5040.0, 5057.5, 5039.0, 5048.0)})).trades
    assert t.side == "short" and t.stop_price == 5057.58


def test_touch_tolerance_is_one_point():
    # high 5049.0 touches 5050 (>= 5049); 5048.9 does not
    (t,) = result_of(hand_frame({20: (5040.0, 5049.0, 5039.0, 5045.0)})).trades
    assert t.side == "short"
    assert result_of(hand_frame({20: (5040.0, 5048.9, 5039.0, 5045.0)})).trades == []


def test_decision_bars_run_from_595_to_890_inclusive():
    reject = (5040.0, 5050.5, 5039.0, 5048.0)
    # bar 4 opens 09:50 (minute 590): not a decision bar, and the level is spent for bar 6
    assert result_of(hand_frame({4: reject, 6: (5040.0, 5050.5, 5039.0, 5048.0)})).trades == []
    # bar 5 opens 09:55 (minute 595): fill at 10:00
    (t,) = result_of(hand_frame({5: reject})).trades
    assert ny(t.entry_time) == "10:00"
    # bar 64 opens 14:50 (minute 890): fill at 14:55, flattened by the engine at 15:55
    (t,) = result_of(hand_frame({64: reject})).trades
    assert ny(t.entry_time) == "14:55" and t.exit_reason == "end_of_day_flatten" and ny(t.exit_time) == "15:55"
    # bar 65 opens 14:55 (minute 895): too late
    assert result_of(hand_frame({65: reject})).trades == []


def test_long_and_short_on_the_same_bar_means_no_trade():
    # Cp 5030; the bar touches 5000 (long: low 4999.5, close 5025 > 5000) and 5050 (short: high 5050.5, close < 5050)
    assert result_of(hand_frame({20: (5030.0, 5050.5, 4999.5, 5025.0)})).trades == []


def test_a_candidate_while_a_position_is_open_is_not_traded_and_the_level_is_spent():
    overrides = dict(SHORT_REJECT)
    overrides[25] = (5010.0, 5011.0, 4999.5, 5002.0)       # long-looking rejection of 5000 while the short is open
    overrides[26] = (5048.0, 5048.0, 5048.0, 5048.0)
    overrides[40] = (5010.0, 5011.0, 4999.5, 5002.0)       # 5000 again, flat now: spent
    (t,) = result_of(hand_frame(overrides)).trades
    assert t.side == "short" and ny(t.exit_time) == "12:15" and t.exit_reason == "time_exit_60min"


def stopped_out(level, a, b):
    stop_hit = level * 1.0015 + 1.0
    return {a: (level - 10.0, level + 0.5, level - 11.0, level - 2.0),
            b: (level - 2.0, stop_hit, level - 3.0, stop_hit - 1.0)}


def test_at_most_two_entries_per_day():
    overrides = {}
    for level, a in ((5050.0, 20), (5100.0, 25), (5150.0, 30)):
        overrides.update(stopped_out(level, a, a + 1))
    frame = hand_frame(overrides)
    r = result_of(frame)
    assert [t.side for t in r.trades] == ["short", "short"]
    assert [t.exit_reason for t in r.trades] == ["stop_loss", "stop_loss"]
    prepared = RoundNumberRejectionFade.on("US500")().prepare(frame)
    assert int((prepared["rn_side"] != 0).sum()) == 2
    # the same sequence on the next day starts counting again
    two_days = pd.concat([hand_frame(overrides), hand_frame(overrides, day=DAY + timedelta(days=1)).iloc[-BARS:]],
                         ignore_index=True)
    assert int((RoundNumberRejectionFade.on("US500")().prepare(two_days)["rn_side"] != 0).sum()) == 4


def test_no_trade_on_fomc_days():
    fomc = date(2024, 1, 31)
    assert result_of(hand_frame(SHORT_REJECT, day=fomc)).trades == []
    assert len(result_of(hand_frame(SHORT_REJECT, day=date(2024, 1, 30))).trades) == 1


def test_trades_on_synthetic_data_and_never_holds_overnight():
    frame = synthetic_sessions("US500", days=45)
    r = run(frame, RoundNumberRejectionFade.on("US500")(), market("US500").cost("base"), BacktestConfig())
    assert r.trades
    assert r.positions_held_overnight == 0
    per_day = {}
    for t in r.trades:
        per_day[ny(t.entry_time, "%Y-%m-%d")] = per_day.get(ny(t.entry_time, "%Y-%m-%d"), 0) + 1
    assert max(per_day.values()) <= 2
    for h in (hand_frame(SHORT_REJECT), hand_frame({64: (5040.0, 5050.5, 5039.0, 5048.0)})):
        assert run(h, RoundNumberRejectionFade.on("US500")(), market("US500").cost("base"),
                   BacktestConfig()).positions_held_overnight == 0
