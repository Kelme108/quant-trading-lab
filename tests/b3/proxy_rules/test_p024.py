"""P-024 WinAbsorptionBarFade on SYNTHETIC WIN session 5-minute bars (09:00 open, Sao Paulo time): class constants,
causality, live-window parity, the baselines and P85 against an independent computation, hand-built days (short, long,
stops and clamps, thresholds, window, time exit, one position, 6-entry cap) and no overnight position. Nothing here is
market data.

Hand-built sessions: every bar of a PRIOR session has open = close = 120000, range 10 (high 120005, low 119995) and volume
100, so vol_norm = 1, rng_norm = 1, er = 1 and P85 = 1.0 exactly. TODAY's bars have volume 50 (vol_norm 0.5: never an
absorption bar) unless a test sets one. An absorption bar t is a bar with volume 300 (vol_norm 3, er 3) at the end of a
6-bar ramp from 120000: closes of bars t-6..t-1 climb to 120150 (+0.125% against the close of bar t-7), bar t closes
120150; the next bars fall back to 120000 by default. The first 5000 bars of a frame are the engine's warm-up, hence
PRIOR_DAYS = 46 sessions before the target day."""

import inspect
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from b3.backtest import BacktestConfig, run
from b3.calendar import B3SessionCalendar, SessionRules
from b3.checks import causality_problems, window_parity_problems
from b3.markets import market
from b3.proxy_rules import p024_win_absorption_bar_fade as mod
from b3.proxy_rules.p024_win_absorption_bar_fade import WinAbsorptionBarFade
from b3.strategy_check import check_proxy_rule_source

UTC = timezone.utc
CAL = B3SessionCalendar("WIN")
COLS = ["time", "open", "high", "low", "close", "volume"]
PRIOR_DAYS = 46
TARGET = date(2026, 5, 13)           # an ordinary session
BASE = 120000.0


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


def session_rows(day, closes=None, vols=None, lows=None, highs=None, default_vol=100.0):
    """The session's bars from 09:00: close = BASE unless in `closes`; open = previous close; volume `default_vol` unless
    in `vols`; high/low = body +/- 5 unless in `highs`/`lows`."""
    m = market("WIN")
    closes, vols, lows, highs = closes or {}, vols or {}, lows or {}, highs or {}
    t0 = datetime.combine(day, m.open, m.zone)
    rows, prev = [], None
    for k in range(nbars(day)):
        c = closes.get(k, BASE)
        o = c if prev is None else prev
        prev = c
        h = highs.get(k, max(o, c) + 5.0)
        lo = lows.get(k, min(o, c) - 5.0)
        rows.append((pd.Timestamp((t0 + timedelta(minutes=5 * k)).astimezone(UTC)), o, h, lo, c, vols.get(k, default_vol)))
    return rows


def hand_frame(target_day, closes=None, vols=None, lows=None, highs=None, prior=PRIOR_DAYS, today_vol=50.0):
    rows = []
    for d in trading_days_before(target_day, prior):
        rows += session_rows(d)
    rows += session_rows(target_day, closes, vols, lows, highs, default_vol=today_vol)
    return pd.DataFrame(rows, columns=COLS)


def ramp(t, final=BASE + 150.0, base=BASE):
    """Closes of bars t-6..t-1 climb (or fall) from `base` to `final`; bar t closes at `final` too."""
    out = {}
    for j in range(6):
        out[t - 6 + j] = base + round((final - base) * (j + 1) / 6.0 / 5.0) * 5.0
    out[t - 1] = final
    out[t] = final
    return out


def absorb(t, final=BASE + 150.0, vol=300.0):
    return ramp(t, final), {t: vol}


def merge(*parts):
    closes, vols = {}, {}
    for c, v in parts:
        closes.update(c)
        vols.update(v)
    return closes, vols


def short_day(t=30, **kw):
    closes, vols = absorb(t)
    return hand_frame(TARGET, closes, vols, **kw)


def trades_of(frame, scenario="optimistic"):
    return run(frame, WinAbsorptionBarFade.on("WIN")(), market("WIN").cost(scenario), BacktestConfig())


def hhmm(ts):
    return ts.tz_convert(market("WIN").zone).strftime("%H:%M")


def at(k):
    return f"{(540 + 5 * k) // 60:02d}:{(540 + 5 * k) % 60:02d}"


def prepared_today(frame, day=TARGET):
    p = WinAbsorptionBarFade.on("WIN")().prepare(frame)
    return p[p["local_date"] == day].reset_index(drop=True)


def synthetic_sessions(days=46, seed=3, start=120000.0, step=5.0, move=18):
    """Random WIN sessions with wide bar moves (|6-bar run| >= 0.10% is common) and random volumes."""
    m = market("WIN")
    rng = random.Random(seed)
    d, rows, prev = date(2026, 1, 5), [], start
    while len({r[0].date() for r in rows}) < days:
        if CAL.is_trading_day(d):
            t = datetime.combine(d, m.open, m.zone)
            end = datetime.combine(d, m.close, m.zone)
            while t + timedelta(minutes=5) <= end:
                o = prev + step * rng.randint(-3, 3)
                c = o + step * rng.randint(-move, move)
                rows.append((t, o, max(o, c) + step * rng.randint(0, 3), min(o, c) - step * rng.randint(0, 3), c,
                             float(rng.randint(50, 500))))
                prev, t = c, t + timedelta(minutes=5)
        d += timedelta(days=1)
    return pd.DataFrame([(pd.Timestamp(r[0].astimezone(UTC)),) + r[1:] for r in rows], columns=COLS)


# ---------------------------------------------------------------------------------------------------------- constants
def test_class_constants():
    s = WinAbsorptionBarFade
    assert mod.RULE_ID == "P-024"
    assert s.name.startswith("P-024") and s.timeframe_min == 5
    assert isinstance(s.warmup, int) and s.warmup >= (20 + 20) * 113 + 113 - 113      # 20 + 20 sessions, plus today
    assert s.rules == SessionRules(entry_start_after_open_min=40, entry_end_before_close_min=59,
                                   flatten_before_close_min=5)
    assert s.params == {
        "baseline_sessions": 20, "er_percentile": 85, "min_vol_norm": 1.0, "run_bars": 6, "min_run_pct": 0.1,
        "min_bar_in_day": 7, "min_minutes_to_close_at_signal": 60, "stop_buffer_ticks": 2, "stop_lookback_bars": 7,
        "min_stop_pct": 0.1, "max_stop_pct": 0.3, "hold_bars": 9, "max_entries_per_day": 6, "range_floor_ticks": 1}
    assert "symbol" not in vars(s)
    assert nbars(TARGET) == 113
    assert check_proxy_rule_source(Path(inspect.getsourcefile(mod)), "P-024") == []


# ------------------------------------------------------------------------------------- causality and live-window parity
def test_causal_and_matches_the_live_window():
    strategy = WinAbsorptionBarFade.on("WIN")()
    frame = synthetic_sessions(days=60)
    assert causality_problems(strategy, frame) == []
    assert window_parity_problems(strategy, frame, samples=60) == []
    p = strategy.prepare(frame)
    late = p.iloc[strategy.warmup:]
    assert (late["ab_side"] > 0).sum() > 5 and (late["ab_side"] < 0).sum() > 5     # the check is not vacuous
    assert (late["ab_exit"] == 1).sum() > 5
    hand = short_day(30)
    assert causality_problems(strategy, hand) == []
    assert window_parity_problems(strategy, hand, samples=40) == []


# --------------------------------------------------------------- baselines and P85 against an independent computation
def expected_er_by_session(frame):
    """er of every bar of the last 21 sessions of `frame`, computed with loops: baseline = median of the slot over the
    20 previous sessions that hold it. Returns {date: {slot: er}} and the ordered session list."""
    local = frame["time"].dt.tz_convert(market("WIN").zone)
    f = frame.assign(day=local.dt.date, slot=local.dt.hour * 60 + local.dt.minute)
    f["rng"] = np.maximum(f["high"] - f["low"], 5.0) / f["close"]
    days = list(dict.fromkeys(f["day"]))
    vol = {(r.day, r.slot): r.volume for r in f.itertuples()}
    rng = {(r.day, r.slot): r.rng for r in f.itertuples()}
    out = {}
    for s in range(len(days) - 21, len(days)):
        prev = days[s - 20:s]
        res = {}
        for r in f[f["day"] == days[s]].itertuples():
            mv = np.median([vol[(d, r.slot)] for d in prev if (d, r.slot) in vol])
            mr = np.median([rng[(d, r.slot)] for d in prev if (d, r.slot) in rng])
            res[r.slot] = (r.volume / mv, (r.rng / mr), (r.volume / mv) / (r.rng / mr))
        out[days[s]] = res
    return out, days


def test_vol_norm_er_and_p85_match_an_independent_computation_and_ignore_today():
    frame = synthetic_sessions(days=46, seed=5)
    p = WinAbsorptionBarFade.on("WIN")().prepare(frame)
    exp, days = expected_er_by_session(frame)
    today = days[-1]
    rows = p[p["local_date"] == today]
    slots = rows["minute_of_day"].tolist()
    assert np.allclose(rows["ab_vol_norm"].to_numpy(), [exp[today][s][0] for s in slots], rtol=1e-12)
    assert np.allclose(rows["ab_er"].to_numpy(), [exp[today][s][2] for s in slots], rtol=1e-12)
    # P85: the in-window bars (bar_in_day >= 7, minutes_to_close >= 60 at the close) of the 20 previous sessions
    pool = []
    for d in days[-21:-1]:
        s = CAL.session(d)
        for slot, (_, _, er) in exp[d].items():
            bar_in_day = (slot - 540) // 5
            to_close = (s.close - datetime.combine(d, market("WIN").open, market("WIN").zone)).total_seconds() / 60 - (
                slot - 540 + 5)
            if bar_in_day >= 7 and to_close >= 60:
                pool.append(er)
    assert len(pool) > 1500
    assert rows["ab_p85"].nunique() == 1
    assert rows["ab_p85"].iloc[0] == pytest.approx(np.percentile(pool, 85), rel=1e-12)
    # today's own bars never enter its P85 or its baselines: scramble today's volumes and ranges, P85 is unchanged
    changed = frame.copy()
    mask = frame["time"].dt.tz_convert(market("WIN").zone).dt.date == today
    changed.loc[mask, "volume"] = 9999.0
    changed.loc[mask, "high"] = changed.loc[mask, "high"] + 500.0
    p2 = WinAbsorptionBarFade.on("WIN")().prepare(changed)
    assert p2[p2["local_date"] == today]["ab_p85"].iloc[0] == pytest.approx(rows["ab_p85"].iloc[0], rel=1e-15)


def test_no_p85_and_no_signal_before_20_earlier_sessions_exist():
    # (the backtester itself decides only after `warmup` bars, so the signal columns are read here)
    closes, vols = absorb(30)
    p20 = prepared_today(hand_frame(TARGET, closes, vols, prior=20))
    assert p20.loc[30, "ab_side"] == -1 and (p20["ab_side"] != 0).sum() == 1 and p20["ab_p85"].iloc[0] == 1.0
    p19 = prepared_today(hand_frame(TARGET, closes, vols, prior=19))
    assert (p19["ab_side"] == 0).all() and p19["ab_p85"].isna().all()


def test_range_is_floored_at_one_tick():
    closes, _ = absorb(30)
    frame = hand_frame(TARGET, closes, {30: 300.0}, highs={30: BASE + 150.0}, lows={30: BASE + 150.0})   # H == L
    p = prepared_today(frame)
    # rng = 5 / 120150 against a baseline of 10 / 120000: rng_norm = 0.49937..., er = 3 / rng_norm
    assert p.loc[30, "ab_er"] == pytest.approx(3.0 / ((5.0 / 120150.0) / (10.0 / 120000.0)), rel=1e-12)


# -------------------------------------------------------------------------------------------------- entries and stops
def test_short_entry_after_an_absorbed_rally_with_the_clamped_stop_and_the_45_minute_time_exit():
    (t,) = trades_of(short_day(30)).trades
    # max high of bars 24..30 = 120155, +2 ticks = 120165: distance 15 < 0.10% of 120150 (120.15) -> 120270.15 -> 120275
    assert (t.side, t.entry_price, t.stop_price, t.entry_reason) == ("short", 120150.0, 120275.0, "fade_absorbed_rally")
    assert hhmm(t.entry_time) == at(31) == "11:35"                 # the open of the bar after the signal bar
    # 9 bars held (31..39): decided at the close of bar 39, filled at the open of bar 40 (12:20)
    assert t.exit_reason == "time_exit_45min" and hhmm(t.exit_time) == at(40) == "12:20" and t.exit_price == BASE


def test_long_entry_after_an_absorbed_drop_with_the_clamped_stop():
    closes, vols = absorb(30, final=BASE - 150.0)
    (t,) = trades_of(hand_frame(TARGET, closes, vols)).trades
    # min low of bars 24..30 = 119845, -2 ticks = 119835: distance 15 -> 0.10% of 119850 = 119.85 -> 119730.15 -> 119730
    assert (t.side, t.entry_price, t.stop_price, t.entry_reason) == ("long", 119850.0, 119730.0, "fade_absorbed_drop")
    assert hhmm(t.entry_time) == at(31)
    assert t.exit_reason == "time_exit_45min" and hhmm(t.exit_time) == at(40) and t.exit_price == BASE


@pytest.mark.parametrize("highs, stop", [
    ({27: 120270.0}, 120280.0),      # raw 120280: distance 130 > 120.15 -> kept
    ({27: 120500.0}, 120510.0),      # raw 120510: distance 360 < 0.30% (360.45) -> kept
    ({27: 120700.0}, 120515.0),      # raw 120710: distance 560 -> clamped at 360.45 -> ceil(120510.45)
    ({27: 120260.0}, 120275.0),      # raw 120270: distance 120 < 120.15 -> clamped up
])
def test_short_stop_distance_is_clamped_to_010_030_percent_and_rounded_away_from_the_price(highs, stop):
    closes, vols = absorb(30)
    (t,) = trades_of(hand_frame(TARGET, closes, vols, highs=highs)).trades
    assert t.side == "short" and t.stop_price == stop and t.stop_price > t.entry_price


@pytest.mark.parametrize("lows, stop", [
    ({27: 119700.0}, 119690.0),      # raw 119690: distance 160 > 119.85 -> kept
    ({27: 119520.0}, 119510.0),      # raw 119510: distance 340 < 0.30% (359.55) -> kept
    ({27: 119300.0}, 119490.0),      # raw 119290: distance 560 -> clamped at 359.55 -> floor(119490.45)
    ({27: 119740.0}, 119730.0),      # raw 119730: distance 120 > 119.85 -> kept
    ({27: 119750.0}, 119730.0),      # raw 119740: distance 110 < 119.85 -> clamped up -> floor(119730.15)
])
def test_long_stop_distance_is_clamped_to_010_030_percent_and_rounded_away_from_the_price(lows, stop):
    closes, vols = absorb(30, final=BASE - 150.0)
    (t,) = trades_of(hand_frame(TARGET, closes, vols, lows=lows)).trades
    assert t.side == "long" and t.stop_price == stop and t.stop_price < t.entry_price


def test_stop_uses_the_7_bars_t_minus_6_to_t_only():
    closes, vols = absorb(30)
    (t,) = trades_of(hand_frame(TARGET, closes, vols, highs={23: 120400.0})).trades      # bar t-7: outside
    assert t.stop_price == 120275.0
    (t,) = trades_of(hand_frame(TARGET, closes, vols, highs={24: 120400.0})).trades      # bar t-6: inside
    assert t.stop_price == 120410.0
    # the signal bar itself (a wide bar needs more volume to stay an absorption bar: er = 3000/100 / (245/10) > 1)
    (t,) = trades_of(hand_frame(TARGET, closes, {30: 3000.0}, highs={30: 120400.0})).trades
    assert t.stop_price == 120410.0


# -------------------------------------------------------------------------------------------------------- thresholds
@pytest.mark.parametrize("final, trades", [(BASE + 120.0, 1), (BASE + 115.0, 0), (BASE - 120.0, 1), (BASE - 115.0, 0)])
def test_run_threshold_is_0p10_percent_over_6_bars(final, trades):
    closes, vols = absorb(30, final=final)
    r = trades_of(hand_frame(TARGET, closes, vols))
    assert len(r.trades) == trades
    if trades:
        assert r.trades[0].side == ("short" if final > BASE else "long")


def test_run_is_measured_from_close_t_minus_7_to_close_t_minus_1():
    # bar t itself closes far above: the run excludes it; bar t-7 (the base) and t-1 decide
    closes, vols = absorb(30)
    closes[30] = BASE + 300.0
    vols[30] = 3000.0                             # a wide bar t needs more volume to keep er >= P85
    assert len(trades_of(hand_frame(TARGET, closes, vols)).trades) == 1
    closes, vols = absorb(30, final=BASE + 115.0)
    closes[30] = BASE + 300.0                     # run(30) = 115 / 120000: still below the threshold
    vols[30] = 3000.0
    assert trades_of(hand_frame(TARGET, closes, vols)).trades == []
    closes, vols = absorb(30)
    closes[23] = BASE + 100.0                     # the base moves up: 120150 / 120100 - 1 = 0.04%
    assert trades_of(hand_frame(TARGET, closes, vols)).trades == []


def test_volume_and_effort_thresholds():
    closes, _ = absorb(30)
    n = lambda vols, **kw: len(trades_of(hand_frame(TARGET, closes, vols, **kw)).trades)
    assert n({30: 100.0}) == 1                                                    # vol_norm = 1.0, er = 1.0 = P85: both inclusive
    assert n({30: 99.0}) == 0                                                     # vol_norm 0.99
    assert n({30: 99.0}, highs={30: BASE + 150.0}, lows={30: BASE + 150.0}) == 0  # er = 1.98 >= P85 but vol_norm < 1
    assert n({30: 100.0}, highs={30: BASE + 165.0}) == 0                          # range 20: er = 0.5 < P85 = 1
    assert n({30: 100.0}, highs={30: BASE + 150.0}, lows={30: BASE + 150.0}) == 1  # range floored: er = 2
    assert n({30: 1000.0}, highs={30: BASE + 400.0}) == 0                         # er = 10 / (255 / 10) < 1 despite vol_norm 10


def test_absorption_bar_must_be_heavy_against_its_slot_baseline_not_against_the_day():
    # the baseline of slot 30 is 400 in every earlier session: today's 300 is vol_norm 0.75 -> no signal
    closes, vols = absorb(30)
    rows = []
    for d in trading_days_before(TARGET, PRIOR_DAYS):
        rows += session_rows(d, vols={30: 400.0})
    rows += session_rows(TARGET, closes, vols, default_vol=50.0)
    assert trades_of(pd.DataFrame(rows, columns=COLS)).trades == []
    rows = []
    for d in trading_days_before(TARGET, PRIOR_DAYS):
        rows += session_rows(d, vols={30: 400.0})
    rows += session_rows(TARGET, closes, {30: 400.0}, default_vol=50.0)
    assert len(trades_of(pd.DataFrame(rows, columns=COLS)).trades) == 1


def heavy_prior_frame(every, heavy_vol, closes, vols):
    """Prior session i has volume `heavy_vol` on the bars k with k % every == i % every: each slot is heavy in 1 of `every`
    sessions, so the slot medians stay 100 and a heavy bar has vol_norm = heavy_vol / 100 and er = heavy_vol / 100."""
    rows = []
    for i, d in enumerate(trading_days_before(TARGET, PRIOR_DAYS)):
        rows += session_rows(d, vols={k: heavy_vol for k in range(113) if k % every == i % every})
    rows += session_rows(TARGET, closes, vols, default_vol=50.0)
    return pd.DataFrame(rows, columns=COLS)


def test_p85_is_the_gate_on_effort_to_result():
    closes, vols = absorb(30)
    # 20% of the in-window bars of every earlier session have er = 3.00: P85 = 3.00 and today's er = 3 / 0.99875 = 3.00375
    frame = heavy_prior_frame(5, 300.0, closes, vols)
    assert prepared_today(frame)["ab_p85"].iloc[0] == pytest.approx(3.0, rel=1e-9)
    assert len(trades_of(frame).trades) == 1
    # a little heavier earlier bars: P85 = 3.01 > 3.00375 -> no trade although vol_norm = 3 >= 1
    frame = heavy_prior_frame(5, 301.0, closes, vols)
    assert prepared_today(frame)["ab_p85"].iloc[0] == pytest.approx(3.01, rel=1e-9)
    assert trades_of(frame).trades == []
    # only 10% heavy bars: the 85th percentile is back at 1.0 and the same day trades
    frame = heavy_prior_frame(10, 2000.0, closes, vols)
    assert prepared_today(frame)["ab_p85"].iloc[0] == pytest.approx(1.0, rel=1e-9)
    assert len(trades_of(frame).trades) == 1


# ------------------------------------------------------------------------------------------------------------ window
def test_signal_window_starts_at_bar_in_day_7_and_ends_60_minutes_before_the_close():
    closes, vols = absorb(7)
    (t,) = trades_of(hand_frame(TARGET, closes, vols)).trades                 # bar 7 closes 09:40: the first possible signal
    assert hhmm(t.entry_time) == at(8) == "09:40"
    p = prepared_today(hand_frame(TARGET, closes, vols))
    assert np.isnan(p.loc[6, "ab_run"]) and not np.isnan(p.loc[7, "ab_run"])
    closes = {k: BASE + 25.0 * k for k in range(1, 6)}                        # bar 6: run needs a bar t-7 of today
    assert trades_of(hand_frame(TARGET, closes, {6: 300.0})).trades == []
    closes, vols = absorb(100)                                                # bar 100 closes 17:25: 60 minutes to the close
    (t,) = trades_of(hand_frame(TARGET, closes, vols)).trades
    assert hhmm(t.entry_time) == at(101) == "17:25"
    assert t.exit_reason == "time_exit_45min" and hhmm(t.exit_time) == at(110)       # 18:10, before the 18:20 flatten
    closes, vols = absorb(101)                                                # closes 17:30: 55 minutes to the close
    assert trades_of(hand_frame(TARGET, closes, vols)).trades == []


def test_the_first_bars_of_the_session_do_not_borrow_yesterdays_closes():
    # run(t) uses bars of today only: a signal at bar 3 or bar 6 is impossible even after a big overnight gap
    rows = []
    for d in trading_days_before(TARGET, PRIOR_DAYS):
        rows += session_rows(d, closes={k: BASE - 300.0 for k in range(100, 113)})
    rows += session_rows(TARGET, {k: BASE for k in range(0, 8)}, {3: 300.0, 6: 300.0}, default_vol=50.0)
    p = prepared_today(pd.DataFrame(rows, columns=COLS))
    assert p["ab_run"].iloc[:7].isna().all() and (p["ab_side"] == 0).all()


# ----------------------------------------------------------------------------------------------------------- exits
def test_stop_exit_fills_at_the_stop_and_the_stop_is_checked_from_the_entry_bar_to_the_last_held_bar():
    closes, vols = absorb(30)
    (t,) = trades_of(hand_frame(TARGET, closes, vols, highs={31: 120280.0})).trades        # the entry bar itself
    assert t.exit_reason == "stop_loss" and t.exit_price == 120275.0 and hhmm(t.exit_time) == at(32)
    (t,) = trades_of(hand_frame(TARGET, closes, vols, highs={39: 120280.0})).trades        # the 9th held bar
    assert t.exit_reason == "stop_loss" and t.exit_price == 120275.0
    (t,) = trades_of(hand_frame(TARGET, closes, vols, highs={40: 120280.0})).trades        # after the exit decision
    assert t.exit_reason == "time_exit_45min" and hhmm(t.exit_time) == at(40)
    closes, vols = absorb(30, final=BASE - 150.0)
    (t,) = trades_of(hand_frame(TARGET, closes, vols, lows={35: 119720.0})).trades
    assert t.side == "long" and t.exit_reason == "stop_loss" and t.exit_price == 119730.0


def test_signals_while_in_a_position_are_ignored_and_the_bar_after_the_time_exit_may_signal():
    # position 31..39 (exit filled at the open of bar 40, decided at the close of 39)
    ok = merge(absorb(30), absorb(39))                       # bar 39: ignored (the exit is decided at its close)
    r = trades_of(hand_frame(TARGET, *ok))
    assert [hhmm(t.entry_time) for t in r.trades] == [at(31)]
    mid = merge(absorb(30), absorb(38))                      # bar 38: inside the position
    assert [hhmm(t.entry_time) for t in trades_of(hand_frame(TARGET, *mid)).trades] == [at(31)]
    nxt = merge(absorb(30), absorb(40))                      # bar 40: flat at its close -> entry at the open of bar 41
    r = trades_of(hand_frame(TARGET, *nxt))
    assert [hhmm(t.entry_time) for t in r.trades] == [at(31), at(41)]
    assert hhmm(r.trades[0].exit_time) == at(40)
    # an opposite signal in the position does not reverse it either
    closes, vols = merge(absorb(30), absorb(37, final=BASE - 150.0))
    r = trades_of(hand_frame(TARGET, closes, vols))
    assert [t.side for t in r.trades] == ["short"]


def test_after_a_stop_the_bar_that_hit_it_can_signal():
    # bar 33 reaches the short stop 120275 (high 120280) and is itself an absorption bar after a run from 120075 to 120200
    closes, vols = absorb(30)
    closes[32] = BASE + 200.0
    closes[33] = BASE + 200.0
    vols[33] = 3000.0
    r = trades_of(hand_frame(TARGET, closes, vols, highs={33: BASE + 280.0}, lows={33: BASE + 195.0}))
    t1, t2 = r.trades
    assert t1.exit_reason == "stop_loss" and t1.exit_price == 120275.0 and hhmm(t1.exit_time) == at(34)
    assert t2.side == "short" and hhmm(t2.entry_time) == at(34) and t2.entry_price == 120200.0
    # bars 27..33: max high 120280, +2 ticks = 120290, distance 90 -> 0.10% of 120200 = 120.2 -> ceil(120320.2)
    assert t2.stop_price == 120325.0


def test_at_most_six_entries_a_day_without_a_backtest_cap():
    ts = [20, 32, 44, 56, 68, 80, 92]
    closes, vols = merge(*[absorb(t) for t in ts])
    r = trades_of(hand_frame(TARGET, closes, vols))
    assert [hhmm(t.entry_time) for t in r.trades] == [at(k + 1) for k in ts[:6]]
    assert all(t.exit_reason == "time_exit_45min" for t in r.trades)
    p = prepared_today(hand_frame(TARGET, closes, vols))
    assert (p["ab_side"] != 0).sum() == 6 and p.loc[92, "ab_side"] == 0 and bool(p.loc[92, "ab_absorb"])


# ------------------------------------------------------------------------------------------------ no overnight, volume
def test_synthetic_sessions_trade_and_never_hold_overnight():
    frames = [synthetic_sessions(days=70), short_day(30), short_day(100)]
    for frame in frames:
        for scenario in ("base", "optimistic"):
            r = trades_of(frame, scenario)
            assert r.trades
            assert r.positions_held_overnight == 0
            per_day = pd.Series([t.entry_time.tz_convert(market("WIN").zone).date() for t in r.trades]).value_counts()
            assert max(per_day) <= 6
    r = trades_of(synthetic_sessions(days=70))
    assert {t.side for t in r.trades} == {"long", "short"}
    assert all((t.stop_price < t.entry_price) if t.side == "long" else (t.stop_price > t.entry_price) for t in r.trades)
