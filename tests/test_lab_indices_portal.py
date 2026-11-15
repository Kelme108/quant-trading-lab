"""lab/indices_portal.py and the Índices pages (docs/plano-portal-proxies.md): the payload follows from the files,
old logs without cycle_end still split into cycles, alerts, strict JSON, safe trade-file names, and the page
module stays in step with the server. Synthetic files in a temporary root."""

import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from lab import dashboard, indices_portal as ip

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "lab" / "dashboard_assets" / "indices.js"
NOW = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)


def _result(rule, sym, split, decision, gross, net, read_at, nan=False):
    m = {"trades": 100, "trades_per_year": 50.0, "mean_gross_pct": gross, "mean_net_pct": gross - 0.01,
         "net_return_pct": net, "net_return_excl_best_pct": net - 1, "max_drawdown_pct": 5.0,
         "profit_factor": float("inf"), "win_rate_pct": 50.0, "daily_sharpe_annualised": float("nan") if nan else 1.0,
         "positive_years_share": 0.5, "per_year_return_pct": {"2022": net}, "long_trades": 60, "short_trades": 40,
         "median_hold_min": 45.0, "exit_reasons": {"time_exit": 100}}
    return {"rule": rule, "strategy": rule.lower(), "strategy_hash": "abc", "symbol": sym, "split": split,
            "start_utc": "2017-04-01 00:00:00+00:00", "end_utc": "2024-01-01 00:00:00+00:00",
            "cost_round_trip_base_pct": 0.01, "prior_variants": 3, "read_at_utc": read_at,
            "gates": {"decision": decision, "fails": [] if decision == "passed" else ["base: net 1% <= bar 2%"], "net_bar_pct": 1.3},
            "scenarios": {s: dict(m) for s in ("optimistic", "base", "conservative", "stress")}}


@pytest.fixture
def root(tmp_path):
    px = tmp_path / "research" / "proxies"
    (px / "results").mkdir(parents=True)
    (px / "proposals").mkdir()
    (px / "trades").mkdir()
    (tmp_path / "b3" / "config").mkdir(parents=True)
    (tmp_path / "ops" / "state").mkdir(parents=True)
    shutil.copy(ROOT / "b3" / "config" / "proxy_program.json", tmp_path / "b3" / "config" / "proxy_program.json")
    shutil.copy(ROOT / "b3" / "config" / "scope_proxies.json", tmp_path / "b3" / "config" / "scope_proxies.json")
    reads = [("P-003", "US500", "exploration", "passed", 0.03, 5.0, "2026-11-14T10:00:00+00:00"),
             ("P-003", "US500", "validation", "passed", 0.02, 3.0, "2026-11-14T11:00:00+00:00"),
             ("P-008", "US500", "exploration", "rejected", -0.06, -20.0, "2026-11-14T16:39:32+00:00"),
             ("P-008", "USTEC", "exploration", "rejected", -0.03, -2.0, "2026-11-14T16:39:33+00:00")]
    ledger = []
    for i, (rule, sym, split, dec, g, n, at) in enumerate(reads):
        name = f"{rule}-{sym}-{split}-2026-11-14T00000{i}.json"
        (px / "results" / name).write_text(json.dumps(_result(rule, sym, split, dec, g, n, at, nan=i == 0)), encoding="utf-8")
        ledger.append({"rule": rule, "symbol": sym, "split": split, "decision": dec, "read_at_utc": at})
    (px / "trades" / "P-008-US500-exploration-2026-11-14T000002.json").write_text(
        json.dumps({"columns": ["entry_time"], "rows": [["2023-01-03T15:00:00+00:00"]]}), encoding="utf-8")
    (px / "ledger.jsonl").write_text("\n".join(json.dumps(x) for x in ledger) + "\n", encoding="utf-8")
    (px / "proposals" / "P-008.json").write_text(json.dumps({
        "rule_id": "P-008", "title": "Fade <b>open</b>", "markets": ["US500", "USTEC"], "timeframe_min": 5,
        "mechanism": "x" * 5000, "sources": [{"title": "s", "url": "javascript:alert(1)"}], "status": "registered",
        "registered_at_utc": "2026-11-14T16:38:40+00:00", "file_stem": "p008_fade"}), encoding="utf-8")
    log = [  # an old cycle without cycle_end, an error, then the weekly cap
        {"at_utc": "2026-11-14T16:30:00+00:00", "event": "agent", "agent": "proxy-research", "cost_usd": 1.0},
        {"at_utc": "2026-11-14T16:35:00+00:00", "event": "agent", "agent": "proxy-developer", "cost_usd": 0.5},
        {"at_utc": "2026-11-14T16:38:40+00:00", "event": "registered", "rule": "P-008"},
        {"at_utc": "2026-11-14T16:39:32+00:00", "event": "exploration", "rule": "P-008", "out": "rejected"},
        {"at_utc": "2026-11-20T09:00:00+00:00", "event": "agent", "agent": "proxy-research", "cost_usd": 1.06, "is_error": True, "result": "limit"},
        {"at_utc": "2026-11-20T09:00:01+00:00", "event": "cycle_error", "rule": "P-009", "error": "proxy-research failed: limit"},
        {"at_utc": "2026-11-20T10:00:00+00:00", "event": "program_stop", "reasons": ["3 rules already registered this week (cap 3)"]},
    ]
    (px / "pipeline_log.jsonl").write_text("\n".join(json.dumps(x) for x in log) + "\n", encoding="utf-8")
    return tmp_path


def test_payload_follows_from_the_files(root):
    d = ip.build_indices(root, NOW)
    assert tuple(d) == ip.INDICES_CONTRACT
    assert d["funnel"] == [{"split": "exploration", "read": 3, "passed": 1}, {"split": "validation", "read": 1, "passed": 1},
                           {"split": "final_test", "read": 0, "passed": 0}]
    s = d["summary"]
    assert (s["rules"], s["pairs_explored"], s["passed_validation"], s["pairs_at_3x_cost"]) == (2, 3, 1, 1)
    p3 = next(r for r in d["board"] if r["rule"] == "P-003")
    assert p3["exploration"]["gross_x_cost"] == pytest.approx(3.0) and p3["validation"]["decision"] == "passed"
    p8 = next(r for r in d["rules"] if r["id"] == "P-008")
    assert p8["origin"] == "agent" and p8["best"] == "rejected"
    assert len(p8["proposal"]["mechanism"]) <= ip.TEXT_LIMIT + 1
    assert p8["reads"][0]["trades_file"] == "P-008-US500-exploration-2026-11-14T000002.json"
    assert p8["reads"][1]["trades_file"] is None
    assert any(r["id"] == "P-001" and r["origin"] == "builtin" for r in d["rules"])


def test_strict_json_without_nan_or_infinity(root):
    text = json.dumps(ip.build_indices(root, NOW), allow_nan=False)
    assert "Infinity" not in text and "NaN" not in text


def test_old_logs_still_split_into_cycles_and_costs_add_up(root):
    c = ip.build_indices(root, NOW)["cycles"]
    assert [(x["rule"], x["outcome"]) for x in c["items"]] == [("P-009", "error"), ("P-008", "done")]
    assert c["total_cost_usd"] == pytest.approx(2.56) and c["errors"] == 1 and c["program_stop_count"] == 1


def test_alerts_validation_waiting_errors_pause_and_deadline(root):
    (root / "ops" / "state" / "STOP_PROXY_CYCLES").write_text("paused after 2 errors", encoding="utf-8")
    alerts = ip.build_indices(root, NOW)["alerts"]
    kinds = {a["kind"] for a in alerts}
    assert {"paused", "cycle_error"} <= kinds and "exchange_data_deadline" not in kinds   # 8 days left: not yet
    paused = next(a for a in alerts if a["kind"] == "paused")
    assert "STOP_PROXY_CYCLES" in paused["action"]
    later = ip.build_indices(root, datetime(2026, 11, 25, 12, 0, tzinfo=timezone.utc))["alerts"]
    deadline = next(a for a in later if a["kind"] == "exchange_data_deadline")
    assert deadline["days_left"] == 3 and "2026-11-28" in deadline["text"]
    gone = ip.build_indices(root, datetime(2026, 11, 29, 12, 0, tzinfo=timezone.utc))["alerts"]
    assert next(a for a in gone if a["kind"] == "exchange_data_deadline")["level"] == "bad"


def test_validation_pass_of_an_agent_rule_asks_the_owner(root):
    px = root / "research" / "proxies"
    (px / "proposals" / "P-009.json").write_text(json.dumps({"rule_id": "P-009", "status": "registered",
                                                            "registered_at_utc": "2026-11-17T10:00:00+00:00"}), encoding="utf-8")
    with (px / "ledger.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"rule": "P-009", "symbol": "USTEC", "split": "validation", "decision": "passed"}) + "\n")
    alerts = ip.build_indices(root, NOW)["alerts"]
    assert any(a["kind"] == "final_test_waiting" and a["rule"] == "P-009" for a in alerts)


def test_trade_file_names_are_checked(root):
    assert ip.trades_file("../ledger.jsonl", root)[0] == 400
    assert ip.trades_file("P-008-US500-exploration-2026-11-14T000002.json/../../x", root)[0] == 400
    assert ip.trades_file("P-008-USTEC-exploration-2026-11-14T000003.json", root)[0] == 404
    status, body = ip.trades_file("P-008-US500-exploration-2026-11-14T000002.json", root)
    assert status == 200 and body["rows"] and body["recalculated"] is False
    assert ip.trades_file("recalc/P-001-US500-exploration.json", root)[0] == 404


def test_empty_root_does_not_break(tmp_path):
    d = ip.build_indices(tmp_path, NOW)
    assert d["board"] == [] and d["funnel"][0]["read"] == 0 and d["cycles"]["items"] == []
    assert dashboard._indices_attention(tmp_path, NOW) == []


def test_page_contract_matches_the_server():
    listed = re.search(r"const IX_CONTRACT = \[(.*?)\];", JS.read_text(encoding="utf-8"), re.S).group(1)
    assert tuple(re.findall(r"'([^']+)'", listed)) == ip.INDICES_CONTRACT


def test_page_module_is_inlined_text_only_and_local():
    page = dashboard.render_page({"generated_at": "x"}, nonce="n", live=True)
    assert "/*__INDICES__*/" not in page and "function pageIndicesPlacar" in page
    text = JS.read_text(encoding="utf-8")
    for needle in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "http://", "https://", "<script", "@import"):
        assert needle not in text, needle
    for route in ("indices", "indices-placar", "indices-ciclos", "indices-mercados", "indices-regra"):
        assert f"id: '{route}'" in page


def test_only_https_sources_become_links():
    assert "ixSafeUrl" in JS.read_text(encoding="utf-8")
    assert re.search(r"const ixSafeUrl = \(u\) => /\^https:\\/\\//i", JS.read_text(encoding="utf-8"))


@pytest.mark.skipif(not shutil.which("node"), reason="needs Node")
def test_page_module_is_valid_javascript():
    r = subprocess.run(["node", "--check", str(JS)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_real_payload_is_small_and_fast():
    import time
    ip.build_indices()                         # warm imports and git cache
    t = time.perf_counter()
    d = ip.build_indices()
    assert time.perf_counter() - t < 1.0
    assert len(json.dumps(d, allow_nan=False)) < 1_000_000
