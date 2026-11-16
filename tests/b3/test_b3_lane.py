"""WIN/WDO research lane (plan docs/plano-b3-reuso.md F1): B3 markets, Clear data loader, roll days and the
back-adjusted series, the history calendar, and the runner's b3 lane (own configs and ledger, returns against the
raw notional of 1 contract). Synthetic data only."""

import csv
import gzip
import json
from datetime import date, datetime, time, timedelta, timezone

import pandas as pd
import pytest

import b3.proxy_research as pr
from b3 import b3_data
from b3.calendar import SP_TZ, B3SessionCalendar, SessionRules
from b3.markets import B3_MARKETS, MARKETS, B3Market, ProxyStrategy, is_b3, market
from b3.strategies.proxies import OpeningRangeBreakout

UTC = timezone.utc
FIELDS = ("time_server", "open", "high", "low", "close", "tick_volume", "spread", "real_volume")


def sessions(days, close=time(18, 25), tf=5, skip_last=0):
    for d in days:
        t = datetime.combine(d, time(9, 0))
        end = datetime.combine(d, close) - timedelta(minutes=tf * skip_last)
        while t + timedelta(minutes=tf) <= end:
            yield t
            t += timedelta(minutes=tf)


def weekdays(start, n, holes=()):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5 and d not in holes:
            out.append(d)
        d += timedelta(days=1)
    return out


def write_rates(path, rows):
    with gzip.open(path, "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        for r in rows:
            w.writerow(r)


def server_epoch(local_naive: datetime) -> int:
    """MT5 server clock = Sao Paulo wall clock written as if UTC."""
    return int(local_naive.replace(tzinfo=UTC).timestamp())


def write_win(folder, days, roll_on=None, gap=500.0, short_day=None):
    """WIN_S_N (raw) 5m + D1, and WIN_S_ (proportional) D1 with one roll at `roll_on`."""
    import random
    rng = random.Random(3)
    rows5, daily_n, daily_a, price = [], [], [], 120_000.0
    for d in days:
        if roll_on and d == roll_on:
            price += gap                          # the new contract trades `gap` points higher
        day_rows = []
        for t in sessions([d], skip_last=(60 if d == short_day else 0)):
            o = price
            c = o + 5 * rng.randint(-6, 6)
            day_rows.append((server_epoch(t), o, max(o, c) + 5, min(o, c) - 5, c, 50, 1, 300))
            price = c
        rows5 += day_rows
        daily_n.append((server_epoch(datetime.combine(d, time(0))), day_rows[0][1], 0, 0, day_rows[-1][4], 1, 1, 1))
    k = (daily_n[0][4] + gap) / daily_n[0][4] if roll_on else 1.0
    for r in daily_n:
        before = roll_on and datetime.fromtimestamp(r[0], UTC).date() < roll_on
        f = k if before else 1.0
        daily_a.append((r[0], r[1] * f, 0, 0, round(r[4] * f / 5) * 5 if before else r[4], 1, 1, 1))
    write_rates(folder / "WIN_S_N-M5.csv.gz", rows5)
    write_rates(folder / "WIN_S_N-D1.csv.gz", daily_n)
    write_rates(folder / "WIN_S_-D1.csv.gz", daily_a)


def test_b3_markets_use_b3_costs_and_instruments():
    win = market("WIN")
    assert isinstance(win, B3Market) and is_b3("win") and not is_b3("US500")
    assert set(B3_MARKETS) == {"WIN", "WDO"} and not set(B3_MARKETS) & set(MARKETS)
    assert win.instrument().point_value_brl == 0.20 and win.instrument().tick_size == 5.0
    base = win.cost("base")
    assert base.fees_per_side_brl == 0.25 and base.slippage_ticks_per_side == 1.0 and base.stop_extra_ticks == 1.0
    assert [win.cost(s).stop_extra_ticks for s in ("optimistic", "base", "conservative", "stress")] == [0, 1, 2, 4]
    assert market("WDO").cost("base").fees_per_side_brl == 1.00


def test_a_proxy_rule_binds_to_win_with_the_b3_calendar():
    rule = OpeningRangeBreakout.on("WIN")
    s = rule()
    assert isinstance(s.calendar, B3SessionCalendar) and s.instrument().tick_size == 5.0
    assert s.hash != OpeningRangeBreakout.on("WDO")().hash


def test_back_adjustment_moves_earlier_bars_by_the_gap_and_keeps_the_grid():
    t = pd.to_datetime(["2024-01-02 13:00", "2024-01-03 13:00", "2024-01-04 13:00"], utc=True)
    bars = pd.DataFrame({"time": t, "open": [100.0, 105, 210], "high": [110.0, 110, 215], "low": [95.0, 100, 205],
                         "close": [105.0, 108, 212], "volume": 1.0})
    out = b3_data.back_adjusted(bars, [{"day": date(2024, 1, 4), "gap_points": 100.0}])
    assert list(out["close"]) == [205.0, 208.0, 212.0]
    assert list(out["adj_offset"]) == [100.0, 100.0, 0.0]
    assert list(out["close"] - out["adj_offset"]) == list(bars["close"])


def test_roll_days_are_found_from_the_adjusted_series(tmp_path):
    days = weekdays(date(2025, 3, 3), 12)
    write_win(tmp_path, days, roll_on=days[6], gap=500.0)
    rolls = b3_data.roll_days("WIN", tmp_path)
    assert [r["day"] for r in rolls] == [days[6]]
    assert rolls[0]["gap_points"] % 5 == 0 and rolls[0]["gap_points"] > 0


def test_history_calendar_infers_closures_and_skips_incomplete_days(tmp_path):
    hole = date(2025, 3, 5)
    days = weekdays(date(2025, 3, 3), 10, holes={hole})
    write_win(tmp_path, days, short_day=days[3])
    bars = b3_data.load_b3_bars("WIN", "5m", tmp_path)
    rules = SessionRules()
    cal = b3_data.history_calendar("WIN", bars, rules)
    assert not cal.is_trading_day(hole) and cal.is_trading_day(days[0])
    assert cal.session(days[0]).close.time() == time(18, 25)
    cov = b3_data.session_coverage(bars, cal, 5)
    assert cov[days[0]] == pytest.approx(1.0) and cov[days[3]] < 0.9
    skipped = b3_data.incomplete_days(bars, cal, 5, 0.9)
    assert skipped == frozenset({days[3]})
    assert not b3_data.history_calendar("WIN", bars, rules, skipped).is_trading_day(days[3])


def test_session_only_drops_after_hours_bars(tmp_path):
    days = weekdays(date(2025, 3, 3), 3)
    write_win(tmp_path, days)
    bars = b3_data.load_b3_bars("WIN", "5m", tmp_path)
    extra = bars.iloc[[-1]].assign(time=bars["time"].iloc[-1] + pd.Timedelta(hours=1))
    cal = b3_data.history_calendar("WIN", bars, SessionRules())
    out = b3_data.session_only_b3(pd.concat([bars, extra], ignore_index=True), cal, 5)
    assert len(out) == len(bars)


@pytest.fixture
def lane(tmp_path, monkeypatch):
    splits = {"approved_by_owner": True, "final_test_unlocked": False, "symbols": {"WIN": {
        "exploration": {"start_utc": "2025-03-03T03:00:00Z", "end_utc": "2025-04-14T03:00:00Z"},
        "validation": {"start_utc": "2025-04-14T03:00:00Z", "end_utc": "2025-05-01T03:00:00Z"},
        "final_test": {"start_utc": "2025-05-01T03:00:00Z", "end_utc": None}}}}
    gates = json.loads((pr.ROOT / "b3/config/gates_b3.json").read_text(encoding="utf-8"))
    scope = json.loads((pr.ROOT / "b3/config/scope_b3.json").read_text(encoding="utf-8"))
    for name, cfg in (("splits", splits), ("gates", gates), ("scope", scope)):
        (tmp_path / f"{name}.json").write_text(json.dumps(cfg), encoding="utf-8")
    monkeypatch.setattr(pr, "B3_SPLITS_PATH", tmp_path / "splits.json")
    monkeypatch.setattr(pr, "B3_GATES_PATH", tmp_path / "gates.json")
    monkeypatch.setattr(pr, "B3_SCOPE_PATH", tmp_path / "scope.json")
    monkeypatch.setattr(pr, "B3_OUT_DIR", tmp_path / "out")
    monkeypatch.setattr(pr, "B3_LEDGER", tmp_path / "out" / "ledger.jsonl")
    monkeypatch.setattr(pr, "OUT_DIR", tmp_path / "proxies_out")       # must stay untouched
    monkeypatch.setattr(pr, "LEDGER", tmp_path / "proxies_out" / "ledger.jsonl")
    days = weekdays(date(2025, 3, 3), 45)
    write_win(tmp_path, days, roll_on=days[20], gap=1500.0)
    return tmp_path


def test_the_b3_lane_records_in_its_own_ledger_with_raw_notional_returns(lane):
    out = pr.evaluate("P-001", "WIN", "exploration", data_dir=lane)
    assert out["lane"] == "b3" and out["symbol"] == "WIN" and out["data_symbol"] == "WIN$N"
    assert out["roll_days_in_split"] == 1 and out["cost_round_trip_base_pct"] == pytest.approx(
        100 * 2 * (0.25 + 1.0) / (120_000 * 0.2), rel=0.1)
    base = out["scenarios"]["base"]
    assert base["trades"] > 0 and base["positions_held_overnight"] == 0
    nets = [out["scenarios"][s]["net_return_pct"] for s in ("optimistic", "base", "conservative", "stress")]
    assert nets == sorted(nets, reverse=True)
    rows = pr.ledger_rows(pr.B3_LEDGER)
    assert [(r["rule"], r["symbol"], r["split"]) for r in rows] == [("P-001", "WIN", "exploration")]
    assert not (lane / "proxies_out").exists()
    trades = json.loads(next((lane / "out" / "trades").glob("P-001-WIN-exploration-*.json")).read_text(encoding="utf-8"))
    entry, gross = trades["rows"][0][3], trades["rows"][0][5]
    assert entry > 100_000 and abs(gross) < 5           # a share of ~R$24k of notional, in percent
    out2 = pr.evaluate("P-002", "WIN", "exploration", data_dir=lane, family="test-family")
    assert out2["prior_variants"] == 1 and pr.ledger_rows(pr.B3_LEDGER)[-1]["family"] == "test-family"


def test_the_b3_lane_locks_the_final_test_and_reads_validation_once(lane):
    with pytest.raises(pr.NotApproved):
        pr.evaluate("P-001", "WIN", "final_test", data_dir=lane)
    pr.evaluate("P-001", "WIN", "validation", data_dir=lane)
    with pytest.raises(pr.AlreadyRead):
        pr.evaluate("P-001", "WIN", "validation", data_dir=lane)


class AdjustedORB(OpeningRangeBreakout):
    name = "test_adjusted_orb"
    price_series = "back_adjusted"


def test_back_adjusted_rules_report_raw_prices_and_the_same_points(lane, monkeypatch):
    monkeypatch.setitem(pr.RULES, "T-ADJ", AdjustedORB)
    monkeypatch.setitem(pr.RULES, "T-RAW", type("RawORB", (OpeningRangeBreakout,), {"name": "test_raw_orb"}))
    a = pr.evaluate("T-ADJ", "WIN", "exploration", data_dir=lane, record=False)
    r = pr.evaluate("T-RAW", "WIN", "exploration", data_dir=lane, record=False)
    assert a["price_series"] == "back_adjusted"
    ta, tr = a["trades_base"]["rows"], r["trades_base"]["rows"]
    assert [x[:5] for x in ta] == [x[:5] for x in tr]      # same times, sides and RAW prices
    assert [x[5] for x in ta] == pytest.approx([x[5] for x in tr])


def test_real_b3_configs_are_approved_and_lock_the_final_test():
    for path in (pr.B3_SPLITS_PATH, pr.B3_GATES_PATH, pr.B3_SCOPE_PATH):
        cfg = json.loads(path.read_text(encoding="utf-8"))
        assert cfg["approved_by_owner"] is True and "2026-11-16" in cfg["_approved"]
    s = json.loads(pr.B3_SPLITS_PATH.read_text(encoding="utf-8"))
    assert s["final_test_unlocked"] is False and s["chosen_scenario"] == "A_five_years"
    assert s["symbols"]["WIN"]["validation"]["start_utc"] == s["symbols"]["WIN"]["exploration"]["end_utc"]


# ---------------------------------------------------------------------------------------------
# Agent program on the b3 lane (b3/config/b3_program.json, owner D5 a 2026-11-16)
# ---------------------------------------------------------------------------------------------

def test_the_agent_program_runs_on_the_b3_lane():
    from b3 import proxy_program as prog
    assert prog.active_lane() == "b3"
    cfg = prog.load_program(prog.LANES["b3"]["program"])
    assert cfg["approved_by_owner"] is True and cfg["scope"]["markets"] == ["WIN", "WDO"]
    assert cfg["max_new_rules_per_week"] == 3 and cfg["stop_after_rules_without_validation_pass"] == 15
    st = prog.status(date(2026, 11, 17), program=cfg, props=[], ledger=[])
    assert st.can_register and not st.notices                   # exchange data deadline is met, no proxy notice
    assert prog.next_rule_id() >= "P-013"                      # P-012 (interrupted) is in the proxy folder


def test_the_b3_context_holds_exploration_facts_only(tmp_path, monkeypatch):
    from b3 import proxy_program as prog
    lanes = {k: dict(v) for k, v in prog.LANES.items()}
    lanes["b3"]["context"] = tmp_path
    monkeypatch.setattr(prog, "LANES", lanes)
    cfg = prog.load_program(lanes["b3"]["program"])
    path = prog.write_context("P-099", prog.status(date(2026, 11, 17), program=cfg, props=[], ledger=[]), cfg)
    text = path.read_text(encoding="utf-8")
    assert "WIN" in text and "WDO" in text and "gates_b3.json" in text
    assert "| validation" not in text and "final_test" not in text
    assert "| C-" not in text                                  # crypto reads go in their own short table


def test_synthetic_sessions_sit_on_the_contract_grid():
    from b3 import proxy_pipeline as pipe
    f = pipe.synthetic_sessions("WIN", days=3)
    assert ((f["close"] / 5.0).round() * 5.0 == f["close"]).all() and f["close"].iloc[0] > 100_000
    g = pipe.synthetic_sessions("WDO", days=3)
    assert ((g["close"] / 0.5).round() * 0.5 == g["close"]).all()


def test_the_b3_scope_allows_only_1_5_and_15_minute_signals():
    scope = json.loads(pr.B3_SCOPE_PATH.read_text(encoding="utf-8"))
    assert scope["timeframes_min"] == [1, 5, 15] and scope["focus_timeframes_min"] == [1, 5]
    for tf in (1, 5, 15):
        pr.check_scope("WIN", tf, scope)
    with pytest.raises(pr.OutOfScope):
        pr.check_scope("WIN", 60, scope)
    hourly = type("H", (), {"params": {"strategy_timeframe": "1h"}, "timeframe_min": 5})
    assert pr.signal_timeframe_min(hourly) == 60          # a ported crypto strategy is judged by its own candles


def test_new_b3_rules_alternate_1_and_5_minutes(tmp_path, monkeypatch):
    """Owner 2026-11-16: half of the new WIN/WDO rules on 1 minute, half on 5, alternating from P-013."""
    from b3 import proxy_program as prog
    cfg = prog.load_program(prog.LANES["b3"]["program"])
    assert [prog.assigned_timeframe(f"P-{n:03d}", cfg) for n in range(13, 19)] == [1, 5, 1, 5, 1, 5]
    good = json.loads((prog.LANES["b3"]["proposals"] / "P-013.json").read_text(encoding="utf-8"))
    good = {k: v for k, v in good.items() if k in prog.PROPOSAL_KEYS} | {"expected_trades_per_year": 600}
    assert prog.validate_proposal(good, "P-013", cfg, ["WIN", "WDO"]) == []
    rare = dict(good, expected_trades_per_year=246)                 # P-004's once a day is too rare (owner)
    assert any("at least 500" in x for x in prog.validate_proposal(rare, "P-013", cfg, ["WIN", "WDO"]))
    bad = dict(good, timeframe_min=5)
    assert any("must be 1 for P-013" in x for x in prog.validate_proposal(bad, "P-013", cfg, ["WIN", "WDO"]))
    lanes = {k: dict(v) for k, v in prog.LANES.items()}
    lanes["b3"]["context"] = tmp_path
    monkeypatch.setattr(prog, "LANES", lanes)
    text = prog.write_context("P-014", prog.status(date(2026, 11, 17), program=cfg, props=[], ledger=[]), cfg).read_text(encoding="utf-8")
    assert "Timeframe of P-014: 5 minutes, fixed" in text and "at least 500 trades per year" in text
