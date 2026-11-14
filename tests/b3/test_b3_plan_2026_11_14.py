"""Plan of research/reviews/2026-11-14-veredito-1m-5m.md: stop slippage on the proxies, the data-quality rule,
the research scope (no 1m, no FX, no USDBRL), the event calendar, the proxy-rule screen and registry, the
program limits (3 per week, 15 rules without validation, project stop) and the pipeline's file guard.
Synthetic data only."""

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import b3.proxy_research as pr
from b3 import proxy_program as prog
from b3 import proxy_pipeline as pipe
from b3.backtest import BacktestConfig, run
from b3.events import event_times, mark_events
from b3.markets import incomplete_days, market, session_coverage
from b3.proxy_rules import RULES, rule_files
from b3.strategy_check import check_proxy_rule_source
from test_b3_proxy_research import lab, write_npy  # noqa: F401  (fixture)

UTC = timezone.utc


# ---- stop slippage -------------------------------------------------------------------------

def test_index_stop_slippage_scales_with_the_cost_scenario_and_fx_has_none():
    m = market("US500")
    assert [m.cost(s).stop_slippage_frac for s in ("optimistic", "base", "conservative", "stress")] == \
        pytest.approx([0.000025, 0.00005, 0.0001, 0.0002])
    assert market("DE40").cost("base").stop_slippage_frac == pytest.approx(0.00005)
    assert market("EURUSD").cost("base").stop_slippage_frac == 0.0


def test_stop_fill_moves_against_the_position():
    c = market("US500").cost("base")
    assert c.stop_fill(5000.0, "long", 0.01) == pytest.approx(5000.0 * (1 - 0.00005))
    assert c.stop_fill(5000.0, "short", 0.01) == pytest.approx(5000.0 * (1 + 0.00005))


def test_backtest_stop_exit_pays_the_slippage():
    from test_b3_proxy_rules import synthetic_sessions
    frame = synthetic_sessions("US500", days=45)
    rule = RULES["P-001"].on("US500")
    with_slip = run(frame, rule(), market("US500").cost("base"), BacktestConfig(max_entries_per_day=1))
    stops = [t for t in with_slip.trades if t.exit_reason == "stop_loss"]
    assert stops
    for t in stops:                                  # the touched price is the stop or a worse gap open
        if t.side == "long":
            assert t.exit_price <= t.stop_price * (1 - 0.00005) + 1e-9
        else:
            assert t.exit_price >= t.stop_price * (1 + 0.00005) - 1e-9


# ---- data quality and scope ----------------------------------------------------------------

def _bars(symbol, days, drop_from_day=None, keep_share=1.0):
    m = market(symbol)
    rows, d, n = [], date(2024, 3, 4), 0
    while n < days:
        if d.weekday() < 5:
            t0 = datetime.combine(d, m.open, m.zone)
            slots = 78
            keep = int(slots * keep_share) if n == drop_from_day else slots
            for k in range(keep):
                rows.append(pd.Timestamp((t0 + timedelta(minutes=5 * k)).astimezone(UTC)))
            n += 1
        d += timedelta(days=1)
    return pd.DataFrame({"time": pd.to_datetime(rows, utc=True)})


def test_session_coverage_and_incomplete_days():
    bars = _bars("US500", 5, drop_from_day=2, keep_share=0.8)
    cov = session_coverage(bars, market("US500"), 5)
    assert sorted(cov.round(3).tolist()) == [0.795, 1.0, 1.0, 1.0, 1.0]
    bad = incomplete_days(bars, market("US500"), 5, 0.9)
    assert len(bad) == 1 and list(bad)[0] == sorted(cov.index)[2]


def test_scope_file_excludes_1m_fx_and_usdbrl():
    scope = json.loads(pr.SCOPE_PATH.read_text(encoding="utf-8"))
    assert scope["approved_by_owner"] is True and scope["min_session_coverage"] == 0.9
    assert set(scope["markets"]) == {"US500", "USTEC", "US30", "US2000", "DE40"}
    for sym in ("USDBRL", "EURUSD", "GBPUSD", "USDJPY"):
        with pytest.raises(pr.OutOfScope):
            pr.check_scope(sym, 5, scope)
    with pytest.raises(pr.OutOfScope):
        pr.check_scope("US500", 1, scope)
    pr.check_scope("USTEC", 5, scope)


def test_runner_refuses_out_of_scope_and_reports_the_quality_rule(lab, monkeypatch):  # noqa: F811
    with pytest.raises(pr.OutOfScope):
        pr.evaluate("P-005", "US500", "exploration", data_dir=lab)          # a 1-minute rule
    out = pr.evaluate("P-001", "US500", "exploration", data_dir=lab)
    assert out["min_session_coverage"] == 0.9 and out["days_skipped_incomplete"] == 0
    assert out["stop_slippage_base_pct"] == pytest.approx(0.005)


# ---- events --------------------------------------------------------------------------------

def test_event_calendar_times_in_utc():
    fomc = event_times("FOMC")
    assert len(fomc) == 79                                             # 2017-2026, March 2020 cancelled
    assert pd.Timestamp("2023-12-13 19:00", tz="UTC") in fomc         # 14:00 New York in winter
    assert pd.Timestamp("2023-07-26 18:00", tz="UTC") in fomc         # 14:00 New York in summer
    cpi = event_times("CPI")
    assert pd.Timestamp("2024-05-15 12:30", tz="UTC") in cpi           # 08:30 New York (EDT)
    assert not any(t.strftime("%Y-%m") == "2025-11" for t in cpi)      # October 2025 CPI never published
    assert all(fomc[i] < fomc[i + 1] for i in range(len(fomc) - 1))


def test_mark_events_counts_minutes_from_the_release_to_the_bar_close():
    times = pd.date_range("2023-12-13 18:45", periods=5, freq="5min", tz="UTC")
    out = mark_events(pd.DataFrame({"time": times}), ["FOMC"], 5)
    assert out["FOMC_today"].all()
    since = out["FOMC_min_since"]                    # bar closes 18:50, 18:55, 19:00, 19:05, 19:10 UTC
    assert since.iloc[:2].isna().all()
    assert since.iloc[2:].tolist() == [0.0, 5.0, 10.0]


# ---- proxy rule screen and registry ----------------------------------------------------------

GOOD = '''"""ok"""
from __future__ import annotations
import pandas as pd
from b3.calendar import SessionRules
from b3.markets import ProxyStrategy
from b3.strategy import ENTER_LONG, HOLD, tick_floor
from live.core.models import Signal

RULE_ID = "P-099"


class Example(ProxyStrategy):
    name = "P-099_example"
    timeframe_min = 5
    warmup = 200
    rules = SessionRules(entry_start_after_open_min=30, entry_end_before_close_min=60, flatten_before_close_min=5)
    params = {"x": 1}

    def decide(self, row, position):
        return Signal(HOLD)
'''


def test_proxy_rule_screen_accepts_a_good_file_and_rejects_bad_ones(tmp_path):
    good = tmp_path / "p099_example.py"
    good.write_text(GOOD, encoding="utf-8")
    assert check_proxy_rule_source(good, "P-099") == []
    bad = tmp_path / "p099_bad.py"
    bad.write_text(GOOD.replace("import pandas as pd", "import os").replace('timeframe_min = 5', 'timeframe_min = 1')
                   .replace('    params = {"x": 1}\n', '    params = {"x": 1}\n    symbol = "US500"\n'), encoding="utf-8")
    problems = check_proxy_rule_source(bad, "P-099")
    assert any("import of 'os'" in p for p in problems)
    assert any("timeframe_min" in p for p in problems)
    assert any("symbol" in p for p in problems)
    wrong_id = tmp_path / "p098_example.py"
    wrong_id.write_text(GOOD, encoding="utf-8")
    assert any("P-098" in p or "RULE_ID" in p for p in check_proxy_rule_source(wrong_id, "P-098"))
    leak = tmp_path / "p099_leak.py"
    leak.write_text(GOOD.replace("from b3.markets import ProxyStrategy", "from b3.markets import ProxyStrategy, load_bars"),
                    encoding="utf-8")
    assert any("only ProxyStrategy" in p for p in check_proxy_rule_source(leak, "P-099"))


def test_registry_holds_the_builtin_rules_and_only_well_named_files():
    assert {f"P-00{i}" for i in range(1, 8)} <= set(RULES)
    assert all(p.stem.startswith("p") and p.stem[1:4].isdigit() for p in rule_files())


# ---- program limits ----------------------------------------------------------------------------

def _program():
    return prog.load_program()


def _props(n, day):
    return [{"rule_id": f"P-{8 + i:03d}", "status": "registered", "registered_at_utc": f"{day}T10:00:00+00:00"}
            for i in range(n)]


def test_program_file_records_the_owner_decisions():
    cfg = _program()
    assert cfg["max_new_rules_per_week"] == 3 and cfg["stop_after_rules_without_validation_pass"] == 15
    assert cfg["project_stop"] == cfg["project_stop"] | {"new_rules": 15, "days": 30}
    assert cfg["exchange_data"]["deadline"] == "2026-11-28"


def test_weekly_cap():
    st = prog.status(date(2026, 11, 18), program=_program(), props=_props(2, "2026-11-17"), ledger=[])
    assert st.can_register and st.registered_this_week == 2
    st = prog.status(date(2026, 11, 18), program=_program(), props=_props(3, "2026-11-16"), ledger=[])
    assert not st.can_register and "this week" in st.reasons[0]
    st = prog.status(date(2026, 11, 23), program=_program(), props=_props(3, "2026-11-16"), ledger=[])
    assert st.can_register                                          # a new ISO week


def test_fifteen_rules_without_validation_stop_and_project_stop():
    props = _props(15, "2026-11-01")
    st = prog.status(date(2026, 11, 20), program=_program(), props=props, ledger=[])
    assert not st.can_register and any("none passed validation" in r for r in st.reasons)
    ledger = [{"rule": "P-010", "symbol": "US500", "split": "validation", "decision": "passed"}]
    st = prog.status(date(2026, 11, 20), program=_program(), props=props, ledger=ledger)
    assert any("project stop" in r for r in st.reasons) and st.validation_passes == [("P-010", "US500")]
    st = prog.status(date(2026, 12, 14), program=_program(), props=[], ledger=[])
    assert not st.can_register and "project stop" in st.reasons[0]
    st = prog.status(date(2026, 12, 14), program=_program(), props=[],
                     ledger=[{"rule": "P-009", "symbol": "USTEC", "split": "final_test", "decision": "passed"}])
    assert st.can_register


def test_invalid_proposals_do_not_count():
    props = _props(3, "2026-11-17")
    props[0]["status"] = "invalid"
    st = prog.status(date(2026, 11, 18), program=_program(), props=props, ledger=[])
    assert st.can_register and st.registered_this_week == 2


def _proposal(rid="P-008"):
    return {"rule_id": rid, "title": "A test rule", "class_name": "TestRule", "file_stem": f"p{rid[2:]}_test_rule",
            "markets": ["US500", "USTEC"], "timeframe_min": 5, "ex_ante_rule": "x" * 120, "parameters": {"a": 1},
            "mechanism": "m" * 80, "why_gross_beats_3x_cost": "g" * 80, "expected_trades_per_year": 120,
            "expected_median_hold_min": 60, "novelty_vs_tried": "n" * 40,
            "sources": [{"title": "t", "url": "https://example.org"}], "data_visible_at_proposal": "context"}


def test_validate_proposal():
    assert prog.validate_proposal(_proposal(), "P-008", _program()) == []
    bad = _proposal() | {"markets": ["EURUSD"], "expected_median_hold_min": 10, "timeframe_min": 1}
    problems = prog.validate_proposal(bad, "P-008", _program())
    assert len(problems) == 3
    assert prog.validate_proposal(_proposal() | {"extra": 1}, "P-008", _program())
    assert prog.validate_proposal(_proposal() | {"status": "registered"}, "P-008", _program()) == []
    assert prog.validate_proposal(_proposal(), "P-009", _program())


def test_next_rule_id_skips_builtin_and_proposed():
    assert prog.next_rule_id(props=[], builtin=list(RULES)) == f"P-{max(int(r[2:]) for r in RULES) + 1:03d}"
    assert prog.next_rule_id(props=[{"rule_id": "P-011"}], builtin=["P-001", "P-007"]) == "P-012"


def test_context_has_exploration_only(tmp_path, monkeypatch):
    monkeypatch.setattr(prog, "CONTEXT_DIR", tmp_path)
    path = prog.write_context("P-099", prog.status(date(2026, 11, 18), program=_program(), props=[], ledger=[]))
    text = path.read_text(encoding="utf-8")
    assert "exploration" in text.lower()
    assert "validation" not in text.lower().replace("validation pass", "")


def test_errored_and_failed_proposals_do_not_count():
    props = _props(3, "2026-11-17")
    props[0]["status"], props[1]["status"] = "error", "implementation_failed"
    st = prog.status(date(2026, 11, 18), program=_program(), props=props, ledger=[])
    assert st.counted_rules == ["P-010"] and st.registered_this_week == 1


def test_two_cycle_errors_in_a_row_pause_the_pipeline(tmp_path, monkeypatch):
    monkeypatch.setattr(pipe, "LOG", tmp_path / "log.jsonl")
    monkeypatch.setattr(pipe, "STOP_FILE", tmp_path / "STOP")
    monkeypatch.setattr(prog, "PROPOSALS", tmp_path)
    (tmp_path / "P-009.json").write_text(json.dumps({"rule_id": "P-009"}), encoding="utf-8")
    pipe.CURRENT["rule"] = "P-009"
    pipe.after_error(RuntimeError("boom"))
    assert json.loads((tmp_path / "P-009.json").read_text(encoding="utf-8"))["status"] == "error"
    assert not (tmp_path / "STOP").exists()
    pipe.log("cycle_end", outcome="done")
    pipe.after_error(RuntimeError("boom"))
    assert not (tmp_path / "STOP").exists()                        # not two in a row
    pipe.after_error(RuntimeError("boom again"))
    assert "boom again" in (tmp_path / "STOP").read_text(encoding="utf-8")
    pipe.CURRENT.clear()


# ---- pipeline guard ------------------------------------------------------------------------------

def test_guard_rejects_files_outside_the_allowed_set(monkeypatch):
    state = {"now": {"a.txt"}}
    monkeypatch.setattr(pipe, "changed_paths", lambda: state["now"])
    before = {"a.txt"}
    state["now"] = {"a.txt", "research/proxies/proposals/P-008.json", "x/__pycache__/m.pyc"}
    pipe.guard(before, {"research/proxies/proposals/P-008.json"}, "agent")
    state["now"] = state["now"] | {"b3/markets.py"}
    with pytest.raises(pipe.CycleError):
        pipe.guard(before, {"research/proxies/proposals/P-008.json"}, "agent")
