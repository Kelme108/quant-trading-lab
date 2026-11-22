"""Portal section 'Esteira' (lab/esteira_portal.py): regroups the conveyor's files, read-only."""
import json
from datetime import datetime, timezone

from lab import esteira_portal as ep


def _w(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")


def _jl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def _root(tmp_path):
    _w(tmp_path / "b3/config/esteira_b3.json", {"limits": {"max_agent_cost_usd_per_day": 15.0, "budget_day_starts_at_hour": 21,
                                                           "max_families_per_day": 100},
                                                "screen": {"min_trades_per_year": 500, "_x": "hidden"},
                                                "default_exit": {"target_brl": 30.0, "stop_brl": 30.0, "max_hold_min": 30}})
    _w(tmp_path / "b3/config/exit_menu.json", {"exits": {"S2": {"what": "s2", "stop": ["V", 1.5], "target": ["V", 0.75], "hold_min": 60}}})
    _w(tmp_path / "b3/config/exit_brl.json", {"exits": {"B1": {"what": "b1", "stop": ["brl", 90.0], "target": ["brl", 35.0], "hold_min": 60}}})
    _w(tmp_path / "b3/config/gates_b3.json", {"cost_basis": "measured", "multiple_testing": {"method": "t_stat_expected_max", "t_floor": 3.0}})
    log = tmp_path / "research/b3/esteira/cycle_log.jsonl"
    _jl(log, [
        {"at_utc": "2026-11-21T23:00:05+00:00", "event": "agent", "cost_usd": 1.5},     # 20:00 SP -> previous night
        {"at_utc": "2026-11-21T23:00:09+00:00", "event": "cycle_end", "outcome": "rejected"},
        {"at_utc": "2026-11-22T01:00:05+00:00", "event": "agent", "cost_usd": 2.0},     # 22:00 SP -> tonight
        {"at_utc": "2026-11-22T01:00:06+00:00", "event": "registered", "batch": 7, "families": ["E-1", "E-2"], "rejected": {}},
        {"at_utc": "2026-11-22T01:02:00+00:00", "event": "screen", "batch": 7, "out": "E-1 WIN: 18 variants, 1 pass the screen, selected x\nE-2 WIN: 18 variants, 0 pass the screen, selected -"},
        {"at_utc": "2026-11-22T01:02:01+00:00", "event": "batch_done", "batch": 7, "selected": ["E-1|WIN|1m|k=1"]},
        {"at_utc": "2026-11-22T01:05:00+00:00", "event": "exit_brl", "exit": 0, "picks": ["a", "b"]},
        {"at_utc": "2026-11-22T01:05:01+00:00", "event": "cycle_end", "outcome": "done"},
        {"at_utc": "2026-11-22T02:00:01+00:00", "event": "usage_limit", "detail": "limit"},
    ])
    _jl(tmp_path / "research/b3/esteira/families.jsonl", [
        {"family": "E-1", "screened_at_utc": "2026-11-22T01:02:00+00:00", "rejected": None},
        {"family": "E-2", "screened_at_utc": "2026-11-22T01:02:00+00:00", "rejected": ["bad"]}])
    _jl(tmp_path / "research/b3/esteira/ledger.jsonl", [{"variant": "a"}, {"variant": "b"}, {"variant": "c"}])
    _w(tmp_path / "research/b3/esteira/runs/20261122T010000Z.json", {"families": {"E-1": {"markets": {"WIN": {"rows": [
        {"variant": "a", "fails": ["plateau", "trades_per_year"]}, {"variant": "b", "fails": ["plateau"]}, {"variant": "c", "fails": []}]}}}}})
    _w(tmp_path / "research/b3/esteira/selected.json", [{"variant": "c", "status": "awaiting_demo", "measured": {"hit_rate": 0.6}}])
    pick = {"variant": "E-1|WIN|1m|k=1", "exit": "B1", "measured": {"hit_rate": 0.7, "mean_net_brl": 3.0, "trades": 900},
            "measured_p90_mean_net_brl": 1.0, "random_mean_net_brl": -1.0}
    bad = dict(pick, variant="E-2|WIN|1m|k=2", measured_p90_mean_net_brl=-0.5)
    _w(tmp_path / "ops/state/exit_brl/20261122T010500Z.json", {"run": "r1", "n_versions_read": 90, "families": {
        "E-1": {"title": "t1", "WIN": {"pick": pick, "candidates": 3}}, "E-2": {"title": "t2", "WIN": {"pick": bad}}}})
    return tmp_path


def test_state_regroups_the_conveyor_files(tmp_path):
    s = ep.esteira_state(_root(tmp_path), now=datetime(2026, 11, 22, 3, 0, tzinfo=timezone.utc))
    json.dumps(s, allow_nan=False)
    assert s["status"]["budget"]["spent_usd"] == 2.0          # the 20:00 call belongs to the previous night
    assert s["status"]["budget"]["cap_usd"] == 15.0
    assert [n["cost_usd"] for n in s["nights"]] == [2.0, 1.5]
    assert s["totals"]["families"] == 2 and s["totals"]["families_rejected"] == 1 and s["totals"]["screen_reads"] == 3
    assert s["screen"]["variants"] == 3 and s["screen"]["passed"] == 1
    assert s["screen"]["fails"][0]["key"] == "plateau" and s["screen"]["fails"][0]["count"] == 2
    assert s["screen_rules"] == {"min_trades_per_year": 500}
    ep_ = s["exit_picks"]
    assert ep_["picks"] == 2 and ep_["good"] == 1 and ep_["top"][0]["family"] == "E-1" and ep_["top"][0]["menu"] == "R$"
    assert ep_["top"][0]["exit_what"] == "b1"
    assert set(s["exits"]) == {"S2", "B1"}
    c = s["cycles"]
    assert c[0]["outcome"] == "limite de uso"
    assert c[1]["outcome"] == "done" and c[1]["batch"] == 7 and c[1]["variants"] == 36 and c[1]["passed"] == 1
    assert c[1]["cost_usd"] == 2.0 and c[1]["exit_brl"] == {"ok": True, "picks": 2}
    assert s["gates"]["cost_basis"] == "measured"


def test_state_survives_an_empty_tree(tmp_path):
    s = ep.esteira_state(tmp_path)
    assert s["cycles"] == [] and s["exit_picks"]["picks"] == 0 and s["totals"]["families"] == 0
