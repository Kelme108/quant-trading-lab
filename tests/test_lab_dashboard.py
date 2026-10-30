import http.client
import json
import tempfile
import threading
import unittest
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from lab import dashboard, registry

NOW = datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)
PAIRS = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
SCENARIOS = {
    "pairs": [{"pair": p, "enabled": True} for p in PAIRS],
    "timeframes": [{"timeframe": "1h", "enabled": True}],
}
SPLITS = {"final_test": {"final_test_unlocked": False}, "pairs": {}}
BUDGET = {"max_variants_per_family": 3, "agent_budget_usd_per_call": 2.0, "max_agent_budget_usd_per_cycle": 12.0}
GOOD_CONFIG = {
    "dry_run": True, "trading_mode": "spot", "dry_run_wallet": 100, "stake_amount": "unlimited",
    "exchange": {"key": "", "secret": ""}, "api_server": {"enabled": False},
}


def iso(moment: datetime) -> str:
    return moment.isoformat()


class DashboardTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.tmp.name)
        (self.root / "user_data").mkdir()
        self.write_config(GOOD_CONFIG)
        self.db_path = self.root / "research" / "lab.sqlite"
        self.conn = registry.connect(self.db_path)

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def write_config(self, config: dict) -> None:
        (self.root / "user_data" / "config.dryrun.json").write_text(json.dumps(config), encoding="utf-8")

    def state(self, **kwargs) -> dict:
        return dashboard.build_state(
            db_path=self.db_path, root=self.root, now=NOW, splits=SPLITS, scenarios=SCENARIOS,
            budget=BUDGET, **kwargs,
        )

    def hypothesis(self, number: int, family: str = "Fam", status: str = "proposed") -> str:
        hid = f"H-{number:03d}"
        registry.add_hypothesis(
            self.conn, hypothesis_id=hid, family=family, ex_ante_rule=f"rule {number}",
            proposed_at_utc=iso(NOW), data_visible_at_proposal="t", status=status,
        )
        return hid

    def experiment(self, hid: str, pair: str, split: str, decision: str, reasons: list[str] | None = None,
                   metrics: dict | None = None, artifact: str | None = None) -> str:
        experiment_id = f"{hid}-{split}-{pair.replace('/', '-')}"
        registry.add_experiment(
            self.conn, experiment_id=experiment_id, hypothesis_id=hid, strategy_file="x.py",
            strategy_sha256="0" * 64, cost_scenario="multi", split=split, command="",
            created_at_utc=iso(NOW), pair=pair, artifact_path=artifact,
        )
        registry.record_metrics(self.conn, experiment_id, metrics or {})
        registry.set_experiment_status(self.conn, experiment_id, "completed", artifact_path=artifact)
        registry.record_decision(
            self.conn, experiment_id=experiment_id, decision=decision, reasons=reasons or [],
            gates_sha256="x", decided_at_utc=iso(NOW),
        )
        return experiment_id

    def all_pairs(self, hid: str, split: str, decision: str, **kwargs) -> None:
        for pair in PAIRS:
            self.experiment(hid, pair, split, decision, **kwargs)

    def cycle_file(self, name: str, started: datetime, outcome: str) -> None:
        directory = self.root / "research" / "experiments"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / name).write_text(
            f"# Cycle {iso(started)}\n\n- Agent spend this cycle: 0.50 USD (cap 12.00)\n- Outcome: {outcome}\n",
            encoding="utf-8",
        )

    def agent_run(self, status: str, started: datetime, agent: str = "validator", excerpt: str = "boom") -> None:
        registry.record_agent_run(
            self.conn, agent=agent, purpose="review", status=status, started_at_utc=iso(started),
            hypothesis_id="H-001", cost_usd=0.2, result_excerpt=excerpt,
        )

    def levels(self, state: dict) -> list[tuple[str, str]]:
        return [(item["level"], item["text"]) for item in state["attention"]]


class StateTests(DashboardTestCase):
    def test_a_missing_database_gives_an_empty_state_and_a_warning(self) -> None:
        self.db_path = self.root / "nowhere" / "lab.sqlite"
        state = self.state()
        self.assertFalse(state["database"]["found"])
        self.assertEqual(state["hypotheses"], [])
        self.assertTrue(any("lab.sqlite" in text for _, text in self.levels(state)))

    def test_the_state_is_json_serializable_without_nan(self) -> None:
        self.hypothesis(1)
        json.dumps(self.state(), allow_nan=False)

    def test_funnel_counts_valid_hypotheses_only_and_stage_by_stage(self) -> None:
        winner, loser, invalid = self.hypothesis(1), self.hypothesis(2), self.hypothesis(3, status="invalid: x")
        self.all_pairs(winner, "exploration", "candidate_for_portfolio")
        self.all_pairs(winner, "validation", "candidate_for_portfolio")
        self.all_pairs(loser, "exploration", "rejected")
        self.all_pairs(invalid, "exploration", "candidate_for_portfolio")
        portfolio_dir = self.root / "research" / "portfolio"
        portfolio_dir.mkdir(parents=True)
        (portfolio_dir / "20261030T000000Z.json").write_text(
            json.dumps({"included": [{"hypothesis_id": winner}], "evaluations": []}), encoding="utf-8"
        )
        funnel = {row["key"]: row["count"] for row in self.state()["funnel"]}
        self.assertEqual(
            funnel,
            {"registered": 2, "explored": 2, "explore_passed": 1, "validation_run": 1,
             "validation_passed": 1, "in_portfolio": 1},
        )

    def test_a_hypothesis_passing_on_only_some_pairs_does_not_pass_the_stage(self) -> None:
        hid = self.hypothesis(1)
        self.experiment(hid, "BTC/USDT", "exploration", "candidate_for_portfolio")
        self.experiment(hid, "ETH/USDT", "exploration", "rejected")
        funnel = {row["key"]: row["count"] for row in self.state()["funnel"]}
        self.assertEqual((funnel["explored"], funnel["explore_passed"]), (0, 0))

    def test_gate_failures_count_each_gate_once_per_cell_and_skip_invalid_hypotheses(self) -> None:
        reasons = [
            "lookahead: pass (has_bias=False)",
            "max_drawdown[optimistic]: FAIL (60% <= 25.0%)",
            "max_drawdown[base]: FAIL (80% <= 25.0%)",
            "minimum_trades[base]: inconclusive (13 < 30)",
            "benchmark_comparison: reported (cash=0.0%)",
        ]
        valid, invalid = self.hypothesis(1), self.hypothesis(2, status="invalid: x")
        self.all_pairs(valid, "exploration", "rejected", reasons=reasons)
        self.all_pairs(invalid, "exploration", "rejected", reasons=reasons)
        failures = {row["gate"]: row for row in self.state()["gate_failures"]}
        self.assertEqual(failures["max_drawdown"]["fail"], 3)
        self.assertEqual(failures["minimum_trades"]["inconclusive"], 3)
        self.assertNotIn("lookahead", failures)
        self.assertNotIn("benchmark_comparison", failures)
        self.assertEqual(self.state()["gate_failures"][0]["gate"], "max_drawdown")

    def test_cells_carry_return_cost_curve_and_failing_gates(self) -> None:
        hid = self.hypothesis(1)
        self.experiment(
            hid, "BTC/USDT", "exploration", "rejected", reasons=["max_drawdown[base]: FAIL (80% <= 25.0%)"],
            metrics={"trades__base": 31, "net_profit_quote__base": 52.0, "net_profit_quote__optimistic": 60.0,
                     "net_profit_quote__stress": -5.0, "max_drawdown_pct__base": 80.0,
                     "benchmark_buy_and_hold_return_pct": 1253.0},
        )
        cell = self.state()["hypotheses"][0]["cells"][0]
        self.assertEqual((cell["pair"], cell["split"], cell["trades"]), ("BTC/USDT", "exploration", 31))
        self.assertAlmostEqual(cell["return_pct"], 52.0)  # 52 USDT on a 100 USDT wallet
        self.assertEqual(cell["profit_by_cost"]["stress"], -5.0)
        self.assertIsNone(cell["profit_by_cost"]["conservative"])
        self.assertEqual(cell["failing_gates"], [{"gate": "max_drawdown", "kind": "fail"}])

    def test_the_equity_curve_is_rebuilt_from_the_export(self) -> None:
        trades = [
            {"open_date": "2020-01-01 00:00:00+00:00", "close_date": "2020-01-03 00:00:00+00:00", "profit_abs": 10.0},
            {"open_date": "2020-01-04 00:00:00+00:00", "close_date": "2020-01-05 00:00:00+00:00", "profit_abs": -4.0},
        ]
        archive = self.root / "export.zip"
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("r.json", json.dumps({"strategy": {"S": {"trades": trades, "starting_balance": 100.0}}}))
        hid = self.hypothesis(1)
        self.experiment(hid, "BTC/USDT", "exploration", "rejected", artifact="export.zip")
        equity = self.state()["hypotheses"][0]["cells"][0]["equity"]
        self.assertEqual([round(p[1], 2) for p in equity], [100.0, 110.0, 106.0])
        self.assertLess(equity[0][0], equity[1][0])

    def test_family_meters_and_the_rising_bar(self) -> None:
        for number in (1, 2):
            self.hypothesis(number, family="Fam")
        family = self.state()["families"][0]
        self.assertEqual((family["family"], family["used"], family["cap"]), ("Fam", 2, 3))
        self.assertGreater(family["next_bar_quote"], dashboard.gates.load_gates()["net_profit"]["base_threshold_quote"])

    def test_agent_spend_and_recent_runs(self) -> None:
        self.agent_run("completed", NOW)
        self.agent_run("completed", NOW)
        agents = self.state()["agents"]
        self.assertAlmostEqual(agents["total_cost_usd"], 0.4)
        self.assertEqual(len(agents["recent"]), 2)

    def test_cycle_reports_are_listed_newest_first(self) -> None:
        self.cycle_file("cycle-1.md", NOW - timedelta(days=2), "completed")
        self.cycle_file("cycle-2.md", NOW - timedelta(days=1), "STOPPED - GuardAbort: x")
        cycles = self.state()["cycles"]
        self.assertEqual([c["file"] for c in cycles], ["cycle-2.md", "cycle-1.md"])
        self.assertEqual(cycles[0]["spend_usd"], 0.5)


class AttentionTests(DashboardTestCase):
    def test_a_clean_state_with_fresh_data_needs_no_attention(self) -> None:
        for pair in PAIRS:
            self.feather(pair, NOW - timedelta(hours=2))
        self.assertEqual(self.state()["attention"], [])

    def feather(self, pair: str, last: datetime) -> None:
        path = self.root / "user_data" / "data" / "binance" / f"{pair.replace('/', '_')}-1h.feather"
        path.parent.mkdir(parents=True, exist_ok=True)
        dates = pd.date_range(end=pd.Timestamp(last), periods=48, freq="1h", tz="UTC")
        pd.DataFrame({"date": dates, "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0}).to_feather(path)

    def test_stale_and_missing_data_are_warned_about(self) -> None:
        self.feather("BTC/USDT", NOW - timedelta(days=10))
        self.feather("ETH/USDT", NOW - timedelta(hours=1))
        texts = [text for _, text in self.levels(self.state())]
        self.assertTrue(any("BTC/USDT" in t and "10 dias" in t and "expand-data" in t for t in texts))
        self.assertTrue(any("BNB/USDT" in t for t in texts))
        self.assertFalse(any("ETH/USDT" in t for t in texts))

    def test_unsafe_config_is_critical(self) -> None:
        self.write_config({**GOOD_CONFIG, "dry_run": False, "exchange": {"key": "abc", "secret": ""}, "trading_mode": "futures"})
        critical = [text for level, text in self.levels(self.state()) if level == "critical"]
        self.assertEqual(len(critical), 3)
        self.assertTrue(any("dry_run" in t for t in critical))
        self.assertTrue(any("chave" in t for t in critical))
        self.assertTrue(any("futures" in t for t in critical))

    def test_an_unlocked_final_test_is_a_warning(self) -> None:
        state = dashboard.build_state(
            db_path=self.db_path, root=self.root, now=NOW, scenarios=SCENARIOS, budget=BUDGET,
            splits={"final_test": {"final_test_unlocked": True}, "pairs": {}},
        )
        self.assertTrue(any(level == "warning" and "teste final" in text for level, text in self.levels(state)))

    def test_a_recent_guard_violation_is_critical_until_a_later_cycle_completes(self) -> None:
        self.agent_run("guard_violation", NOW - timedelta(hours=3), excerpt="wrote a stray file")
        self.assertTrue(any(l == "critical" and "stray file" in t for l, t in self.levels(self.state())))

        self.cycle_file("cycle-ok.md", NOW - timedelta(hours=1), "completed")
        self.assertFalse(any("stray file" in t for _, t in self.levels(self.state())))

    def test_a_violation_after_the_last_completed_cycle_stays_critical(self) -> None:
        self.cycle_file("cycle-ok.md", NOW - timedelta(hours=5), "completed")
        self.agent_run("guard_violation", NOW - timedelta(hours=1), excerpt="newer problem")
        self.assertTrue(any(l == "critical" and "newer problem" in t for l, t in self.levels(self.state())))

    def test_old_incidents_age_out_after_a_week(self) -> None:
        self.agent_run("failed", NOW - timedelta(days=9), excerpt="ancient")
        self.assertFalse(any("ancient" in t for _, t in self.levels(self.state())))

    def test_the_latest_stopped_cycle_is_flagged_until_a_good_one_follows(self) -> None:
        self.cycle_file("cycle-1.md", NOW - timedelta(hours=2), "STOPPED - BudgetExhausted: cap")
        self.assertTrue(any("último ciclo parou" in t for _, t in self.levels(self.state())))
        self.cycle_file("cycle-2.md", NOW - timedelta(hours=1), "completed")
        self.assertFalse(any("último ciclo parou" in t for _, t in self.levels(self.state())))

    def test_failed_experiments_warn_only_while_unresolved(self) -> None:
        hid = self.hypothesis(1)
        experiment_id = self.experiment(hid, "BTC/USDT", "exploration", "rejected")
        registry.set_experiment_status(self.conn, experiment_id, "failed")
        self.assertTrue(any("'failed'" in t for _, t in self.levels(self.state())))
        self.cycle_file("cycle-ok.md", NOW + timedelta(minutes=1), "completed")
        self.assertFalse(any("'failed'" in t for _, t in self.levels(self.state())))


class SafetyOfThePageTests(DashboardTestCase):
    def test_the_registry_is_opened_read_only(self) -> None:
        conn = dashboard.open_readonly(self.db_path)
        try:
            with self.assertRaises(Exception) as caught:
                conn.execute("DELETE FROM hypotheses")
            self.assertIn("readonly", str(caught.exception).lower())
        finally:
            conn.close()

    def test_untrusted_text_cannot_close_the_script_element(self) -> None:
        hid = self.hypothesis(1)
        registry.set_hypothesis_status(self.conn, hid, "x")
        evil = "</script><img src=x onerror=alert(1)>& "
        self.conn.execute("UPDATE hypotheses SET ex_ante_rule = ?, notes = ? WHERE id = ?", (evil, evil, hid))
        self.conn.commit()
        state = self.state()
        page = dashboard.render_page(state, nonce="abc", live=True)
        self.assertNotIn("</script><img", page)
        self.assertNotIn("onerror=alert(1)>", page)
        embedded = page.split('id="state">', 1)[1].split("</script>", 1)[0]
        self.assertEqual(json.loads(embedded)["hypotheses"][0]["rule"], evil)

    def test_the_static_export_has_no_nonce_and_is_not_live(self) -> None:
        out = dashboard.export_html(self.root / "out" / "d.html", self.state())
        page = out.read_text(encoding="utf-8")
        self.assertIn("const LIVE = false;", page)
        self.assertNotIn("nonce=", page)
        self.assertNotIn("__STATE__", page)
        self.assertNotIn("__NONCE_ATTR__", page)

    def test_the_page_loads_nothing_from_the_network(self) -> None:
        import re

        page = dashboard.ASSET_PATH.read_text(encoding="utf-8")
        urls = set(re.findall(r"https?://[^\s'\"`)<>]+", page))
        # An SVG namespace is an identifier, not a request; the FreqUI address is
        # shown to the reader as text. Nothing else may appear.
        self.assertEqual(urls, {"http://www.w3.org/2000/svg", "http://127.0.0.1:8080"})
        for needle in ("<link", "@import", "<img", "<iframe", "<script src"):
            self.assertNotIn(needle, page)

    def test_the_page_inserts_text_only_with_text_nodes(self) -> None:
        page = dashboard.ASSET_PATH.read_text(encoding="utf-8")
        for forbidden in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval("):
            self.assertNotIn(forbidden, page)


class ServerTests(DashboardTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.hypothesis(1)
        state = self.state()
        self.server = dashboard.create_server(lambda: state, 0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        super().tearDown()

    def request(self, method: str, path: str, host: str | None = None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        connection.putrequest(method, path, skip_host=True)
        connection.putheader("Host", host or f"127.0.0.1:{self.port}")
        connection.endheaders()
        response = connection.getresponse()
        body = response.read()
        headers = dict(response.getheaders())
        connection.close()
        return response.status, headers, body

    def test_it_listens_on_loopback_only(self) -> None:
        self.assertEqual(self.server.server_address[0], "127.0.0.1")

    def test_state_endpoint_returns_json(self) -> None:
        status, headers, body = self.request("GET", "/api/state")
        self.assertEqual(status, 200)
        self.assertIn("application/json", headers["Content-Type"])
        self.assertEqual(json.loads(body)["hypotheses"][0]["id"], "H-001")
        self.assertEqual(headers["Cache-Control"], "no-store")

    def test_the_page_carries_a_nonce_csp_that_matches_its_script(self) -> None:
        status, headers, body = self.request("GET", "/")
        csp = headers["Content-Security-Policy"]
        nonce = csp.split("'nonce-", 1)[1].split("'", 1)[0]
        self.assertEqual(status, 200)
        self.assertIn(f'<script nonce="{nonce}">', body.decode("utf-8"))
        self.assertIn("default-src 'none'", csp)
        self.assertNotIn("unsafe-eval", csp)
        self.assertNotIn("script-src 'unsafe-inline'", csp)
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")

    def test_each_page_load_gets_a_fresh_nonce(self) -> None:
        first = self.request("GET", "/")[1]["Content-Security-Policy"]
        second = self.request("GET", "/")[1]["Content-Security-Policy"]
        self.assertNotEqual(first, second)

    def test_a_foreign_host_header_is_refused(self) -> None:
        for host in ("evil.example", f"evil.example:{self.port}", "127.0.0.1", f"127.0.0.1.evil.example:{self.port}"):
            self.assertEqual(self.request("GET", "/api/state", host=host)[0], 403, host)

    def test_localhost_by_name_is_accepted(self) -> None:
        self.assertEqual(self.request("GET", "/healthz", host=f"localhost:{self.port}")[0], 200)

    def test_anything_but_get_and_head_is_refused(self) -> None:
        for method in ("POST", "PUT", "DELETE", "PATCH", "OPTIONS"):
            status, headers, _ = self.request(method, "/api/state")
            self.assertEqual(status, 405, method)
            self.assertEqual(headers["Allow"], "GET, HEAD")

    def test_head_returns_no_body_and_unknown_paths_404(self) -> None:
        self.assertEqual(self.request("HEAD", "/")[2], b"")
        self.assertEqual(self.request("GET", "/etc/passwd")[0], 404)
        self.assertEqual(self.request("GET", "/../../etc/passwd")[0], 404)

    def test_a_failing_provider_returns_500_without_leaking_details(self) -> None:
        self.server.provider = lambda: (_ for _ in ()).throw(RuntimeError("secret detail"))
        status, _, body = self.request("GET", "/api/state")
        self.assertEqual(status, 500)
        self.assertNotIn(b"secret detail", body)
        self.assertEqual(self.request("GET", "/healthz")[0], 200)

    def test_the_provider_cache_reuses_a_recent_build(self) -> None:
        calls = []
        provider = dashboard.StateProvider(lambda: calls.append(1) or {"n": len(calls)}, ttl_seconds=60)
        provider(), provider(), provider()
        self.assertEqual(len(calls), 1)
        expired = dashboard.StateProvider(lambda: calls.append(1) or {"n": len(calls)}, ttl_seconds=-1)
        expired(), expired()
        self.assertEqual(len(calls), 3)


if __name__ == "__main__":
    unittest.main()
