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

    def test_archived_hypotheses_are_flagged_and_never_reach_the_strategy_lists(self) -> None:
        alive = self.hypothesis(1, status="exploration: candidate")
        dead = self.hypothesis(2, status="rejected at exploration")
        frozen = self.hypothesis(3, status="not approved at validation")
        (self.root / "research" / "forward").mkdir(parents=True, exist_ok=True)
        (self.root / "research" / "forward" / f"{frozen}-freeze.json").write_text("{}", encoding="utf-8")
        state = self.state()
        flags = {h["id"]: h["archived"] for h in state["hypotheses"]}
        self.assertEqual(flags, {alive: False, dead: True, frozen: False})  # a bot in dry-run stays visible
        self.assertEqual(state["archived_count"], 1)
        self.assertNotIn(dead, {row["id"] for row in state["strategies"]})

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


class PanelDataTests(DashboardTestCase):
    def test_cells_say_which_scenario_broke_which_gate(self) -> None:
        hid = self.hypothesis(1)
        self.experiment(hid, "BNB/USDT", "exploration", "rejected", reasons=[
            "net_profit[base]: pass (net_profit_quote=5 > required 1.0000, after 0 prior variant(s) in family)",
            "net_profit[conservative]: FAIL (net_profit_quote=-5 > required 1.0000, after 0 prior variant(s) in family)",
        ])
        detail = self.state()["hypotheses"][0]["cells"][0]["failing_detail"]
        self.assertEqual(detail, [{"gate": "net_profit", "scenario": "conservative", "kind": "fail"}])

    def test_families_separate_registered_from_tested(self) -> None:
        tested, untested = self.hypothesis(1, family="A"), self.hypothesis(2, family="A")
        self.all_pairs(tested, "exploration", "rejected")
        family = self.state()["families"][0]
        self.assertEqual((family["used"], family["tested"], family["cap"]), (2, 1, 3))

    def test_experiment_count_is_explained_by_cells_and_earlier_attempts(self) -> None:
        hid = self.hypothesis(1)
        self.experiment(hid, "BTC/USDT", "exploration", "rejected")
        registry.add_experiment(
            self.conn, experiment_id="rerun", hypothesis_id=hid, strategy_file="x.py", strategy_sha256="0" * 64,
            cost_scenario="multi", split="exploration", command="", created_at_utc=iso(NOW + timedelta(minutes=1)),
            pair="BTC/USDT",
        )
        registry.set_experiment_status(self.conn, "rerun", "completed")
        registry.record_decision(self.conn, experiment_id="rerun", decision="rejected", reasons=[],
                                 gates_sha256="x", decided_at_utc=iso(NOW))
        experiments = self.state()["experiments"]
        self.assertEqual((experiments["total"], experiments["cells"], experiments["earlier_attempts"]), (2, 1, 1))

    def test_a_superseded_stopped_cycle_stays_listed_as_resolved(self) -> None:
        self.cycle_file("cycle-1.md", NOW - timedelta(hours=3), "STOPPED - GuardAbort: x wrote outside ['a/b.tmp']")
        self.cycle_file("cycle-2.md", NOW - timedelta(hours=1), "completed")
        item = next(i for i in self.state()["attention"] if i["kind"] == "stopped_cycle")
        self.assertTrue(item["resolved"] and item["guard"])
        self.assertEqual(item["paths"], ["a/b.tmp"])
        self.assertEqual(item["anchor"], "sec-ciclos")

    def test_history_and_periods_are_present(self) -> None:
        state = self.state()
        self.assertEqual([b["prior_variants"] for b in state["history"]["bar_by_variant"]], [0, 1, 2])
        self.assertEqual(set(state["periods"]), set(PAIRS))
        self.assertEqual({c["name"] for c in state["cost_scenarios"]}, {"optimistic", "base", "conservative", "stress", "base_2x"})


class RedesignDataTests(DashboardTestCase):
    """The read-only extensions the multi-page layout needs."""

    def feather(self, pair: str, frame: pd.DataFrame) -> None:
        path = self.root / "user_data" / "data" / "binance" / f"{pair.replace('/', '_')}-1h.feather"
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_feather(path)

    def test_data_health_counts_duplicate_timestamps_and_invalid_candles(self) -> None:
        dates = list(pd.date_range(end=pd.Timestamp(NOW), periods=6, freq="1h", tz="UTC"))
        dates[3] = dates[2]  # one duplicated timestamp
        frame = pd.DataFrame({"date": dates, "open": 1.0, "high": 2.0, "low": 1.0, "close": 1.5, "volume": 1.0})
        frame.loc[0, "high"] = 0.5      # high < low
        frame.loc[1, "close"] = -1.0    # value <= 0
        frame.loc[4, "open"] = float("nan")
        self.feather("BTC/USDT", frame)
        row = next(r for r in self.state()["data_health"] if r["pair"] == "BTC/USDT")
        self.assertEqual((row["duplicate_timestamps"], row["invalid_candles"]), (1, 3))

    def test_a_clean_file_reports_zero_and_a_file_without_ohlc_reports_none(self) -> None:
        dates = pd.date_range(end=pd.Timestamp(NOW), periods=5, freq="1h", tz="UTC")
        self.feather("BTC/USDT", pd.DataFrame({"date": dates, "open": 1.0, "high": 2.0, "low": 1.0, "close": 1.5}))
        self.feather("ETH/USDT", pd.DataFrame({"date": dates}))
        rows = {r["pair"]: r for r in self.state()["data_health"]}
        self.assertEqual((rows["BTC/USDT"]["duplicate_timestamps"], rows["BTC/USDT"]["invalid_candles"]), (0, 0))
        self.assertIsNone(rows["ETH/USDT"]["invalid_candles"])  # unknown, not "zero"

    def test_cells_carry_the_metrics_that_used_to_stay_in_the_database(self) -> None:
        hid = self.hypothesis(1)
        self.experiment(hid, "BTC/USDT", "exploration", "rejected", metrics={
            "net_profit_excl_best_trade__base": 12.5, "net_profit_excl_best_trade__stress": -3.0,
            "benchmark_cash_return_pct": 0.0, "lookahead_has_bias": False, "recursive_is_stable": True,
            "max_drawdown_pct__stress": 40.0, "trades__stress": 31,
        })
        cell = self.state()["hypotheses"][0]["cells"][0]
        self.assertEqual(cell["profit_excl_best_by_cost"]["base"], 12.5)
        self.assertEqual(cell["profit_excl_best_by_cost"]["stress"], -3.0)
        self.assertIsNone(cell["profit_excl_best_by_cost"]["optimistic"])
        self.assertEqual((cell["benchmark_cash_pct"], cell["lookahead_has_bias"], cell["recursive_is_stable"]), (0.0, False, True))
        self.assertEqual((cell["drawdown_by_cost"]["stress"], cell["trades_by_cost"]["stress"]), (40.0, 31))
        self.assertIn("decided_at_utc", cell)

    def test_missing_lookahead_and_recursive_metrics_are_none_not_false(self) -> None:
        hid = self.hypothesis(1)
        self.experiment(hid, "BTC/USDT", "exploration", "rejected")
        cell = self.state()["hypotheses"][0]["cells"][0]
        self.assertIsNone(cell["lookahead_has_bias"])
        self.assertIsNone(cell["recursive_is_stable"])

    def test_the_experiment_list_has_every_run_with_its_decision_and_whether_it_is_current(self) -> None:
        hid = self.hypothesis(1)
        old = self.experiment(hid, "BTC/USDT", "exploration", "rejected")
        registry.add_experiment(
            self.conn, experiment_id="rerun", hypothesis_id=hid, strategy_file="x.py", strategy_sha256="a" * 64,
            cost_scenario="multi", split="exploration", command="cmd", created_at_utc=iso(NOW + timedelta(minutes=1)), pair="BTC/USDT",
        )
        registry.set_experiment_status(self.conn, "rerun", "completed")
        registry.record_decision(self.conn, experiment_id="rerun", decision="inconclusive", reasons=[], gates_sha256="x",
                                 decided_at_utc=iso(NOW + timedelta(minutes=2)))
        registry.add_experiment(
            self.conn, experiment_id="broken", hypothesis_id=hid, strategy_file="x.py", strategy_sha256="b" * 64,
            cost_scenario="multi", split="exploration", command="cmd", created_at_utc=iso(NOW - timedelta(days=1)), pair="ETH/USDT",
        )
        registry.set_experiment_status(self.conn, "broken", "failed")
        items = {item["id"]: item for item in self.state()["experiments"]["items"]}
        self.assertEqual(set(items), {old, "rerun", "broken"})
        self.assertFalse(items[old]["current"])
        self.assertTrue(items["rerun"]["current"])
        self.assertEqual((items["rerun"]["decision"], items["rerun"]["decided_at_utc"]), ("inconclusive", iso(NOW + timedelta(minutes=2))))
        self.assertEqual(items["rerun"]["strategy_sha256"], "a" * 64)
        self.assertEqual(items["rerun"]["command"], "cmd")
        self.assertEqual(items["broken"]["status"], "failed")
        self.assertIsNone(items["broken"]["decision"])  # a failed run has no gate decision
        self.assertEqual(self.state()["experiments"]["items"][0]["id"], "rerun")  # newest first

    def write_review(self, folder: str, **files: str) -> None:
        directory = self.root / "research" / "experiments" / folder
        directory.mkdir(parents=True, exist_ok=True)
        for name, text in files.items():
            (directory / name.replace("_", ".")).write_text(text, encoding="utf-8")

    def test_reviewer_reports_are_read_verbatim_and_missing_ones_are_none(self) -> None:
        self.write_review("H-001-exploration", validator_md="# Validator\n\n- ok <b>x</b>\n", quant_md="q",
                          facts_json=json.dumps({"hypothesis_id": "H-001"}))
        self.write_review("not-a-review", validator_md="ignored")
        reviews = self.state()["reviews"]
        self.assertEqual(set(reviews), {"H-001"})
        entry = reviews["H-001"]["exploration"]
        self.assertEqual(entry["validator"]["text"], "# Validator\n\n- ok <b>x</b>\n")  # exactly as written
        self.assertFalse(entry["validator"]["truncated"])
        self.assertIsNone(entry["risk"])
        self.assertEqual(entry["facts"], {"hypothesis_id": "H-001"})

    def test_long_reviews_and_facts_are_size_limited(self) -> None:
        self.write_review("H-002-validation", risk_md="x" * (dashboard.REVIEW_TEXT_LIMIT + 5),
                          facts_json=json.dumps({"blob": "y" * dashboard.FACTS_LIMIT}))
        entry = self.state()["reviews"]["H-002"]["validation"]
        self.assertEqual((len(entry["risk"]["text"]), entry["risk"]["truncated"], entry["risk"]["chars"]),
                         (dashboard.REVIEW_TEXT_LIMIT, True, dashboard.REVIEW_TEXT_LIMIT + 5))
        self.assertTrue(entry["facts"]["truncated"])
        self.assertNotIn("blob", entry["facts"])

    def test_proposals_are_read_with_title_rationale_parameters_and_sources(self) -> None:
        directory = self.root / "research" / "proposals"
        directory.mkdir(parents=True)
        (directory / "H-009.json").write_text(json.dumps({
            "title": "T", "rationale": "R" * (dashboard.PROPOSAL_TEXT_LIMIT + 10), "parameters": {"a": 1},
            "sources": [{"title": "S", "url": "https://example.test/x"}, "not a dict"], "ex_ante_rule": "ignored here",
        }), encoding="utf-8")
        (directory / "H-010.json").write_text("{broken", encoding="utf-8")
        proposals = self.state()["proposals"]
        self.assertEqual(set(proposals), {"H-009"})
        self.assertEqual((proposals["H-009"]["title"], proposals["H-009"]["parameters"]), ("T", {"a": 1}))
        self.assertEqual(len(proposals["H-009"]["rationale"]), dashboard.PROPOSAL_TEXT_LIMIT)
        self.assertEqual(proposals["H-009"]["sources"], [{"title": "S", "url": "https://example.test/x"}])

    def test_per_agent_totals_and_the_activity_feed_use_only_recorded_timestamps(self) -> None:
        hid = self.hypothesis(1)
        self.experiment(hid, "BTC/USDT", "exploration", "rejected")
        self.agent_run("completed", NOW - timedelta(hours=5), agent="validator")
        self.agent_run("failed", NOW - timedelta(hours=1), agent="validator")
        self.agent_run("completed", NOW - timedelta(hours=2), agent="risk")
        self.cycle_file("cycle-1.md", NOW - timedelta(hours=3), "completed")
        state = self.state()
        by = {row["agent"]: row for row in state["agents"]["by_agent"]}
        self.assertEqual((by["validator"]["runs"], by["validator"]["last_status"]), (2, "failed"))
        self.assertAlmostEqual(by["validator"]["total_cost_usd"], 0.4)
        self.assertEqual(by["risk"]["runs"], 1)
        feed = state["activity"]
        self.assertEqual({e["kind"] for e in feed}, {"hypothesis", "experiment", "decision", "agent", "cycle"})
        moments = [dashboard._parse_time(e["at"]) for e in feed]
        self.assertEqual(moments, sorted(moments, reverse=True))  # newest first
        self.assertTrue(all(e["at"] for e in feed))
        self.assertTrue(any(e["kind"] == "agent" and e["status"] == "failed" for e in feed))

    def test_the_activity_feed_is_capped(self) -> None:
        for number in range(dashboard.ACTIVITY_LIMIT + 10):
            self.agent_run("completed", NOW - timedelta(minutes=number))
        self.assertEqual(len(self.state()["activity"]), dashboard.ACTIVITY_LIMIT)

    def test_the_database_entry_names_its_file(self) -> None:
        self.assertEqual(self.state()["database"], {"found": True, "path": "research/lab.sqlite"})
        self.db_path = self.root / "nowhere" / "lab.sqlite"
        self.assertEqual(self.state()["database"], {"found": False, "path": None})

    def test_a_missing_database_still_has_the_new_empty_sections(self) -> None:
        self.db_path = self.root / "nowhere" / "lab.sqlite"
        state = self.state()
        self.assertEqual((state["experiments"]["items"], state["agents"]["by_agent"]), ([], []))
        self.assertEqual((state["reviews"], state["proposals"], state["activity"]), ({}, {}, []))
        json.dumps(state, allow_nan=False)


class ContractTests(DashboardTestCase):
    """Server x client: every path the page reads must be in what the server emits."""

    @staticmethod
    def has(state: dict, path: str) -> bool:
        node = state
        for key in path.split("."):
            if not isinstance(node, dict) or key not in node:
                return False
            node = node[key]
        return True

    def test_the_page_and_the_server_list_the_same_contract(self) -> None:
        import re

        page = dashboard.ASSET_PATH.read_text(encoding="utf-8")
        listed = re.search(r"const CONTRACT = \[(.*?)\];", page, re.S).group(1)
        self.assertEqual(tuple(re.findall(r"'([^']+)'", listed)), dashboard.STATE_CONTRACT)

    def test_a_populated_state_has_every_path_the_page_reads(self) -> None:
        hid = self.hypothesis(1)
        self.all_pairs(hid, "exploration", "rejected")
        self.agent_run("completed", NOW)
        state = self.state()
        self.assertEqual([p for p in dashboard.STATE_CONTRACT if not self.has(state, p)], [])

    def test_an_empty_state_has_every_path_too(self) -> None:
        self.db_path = self.root / "nowhere" / "lab.sqlite"
        state = self.state()
        self.assertEqual([p for p in dashboard.STATE_CONTRACT if not self.has(state, p)], [])

    def test_the_served_api_state_has_every_path(self) -> None:
        self.hypothesis(1)
        server = dashboard.create_server(lambda: self.state(), 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            conn.request("GET", "/api/state", headers={"Host": f"127.0.0.1:{port}"})
            served = json.loads(conn.getresponse().read())
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual([p for p in dashboard.STATE_CONTRACT if not self.has(served, p)], [])

    def test_experiment_items_carry_what_the_table_and_filters_use(self) -> None:
        hid = self.hypothesis(1)
        self.experiment(hid, "BTC/USDT", "exploration", "rejected", reasons=["max_drawdown[base]: FAIL (80% <= 25.0%)"])
        item = self.state()["experiments"]["items"][0]
        for field in ("id", "hypothesis_id", "pair", "split", "status", "decision", "created_at_utc", "reasons", "current"):
            self.assertIn(field, item)
        self.assertEqual(item["reasons"], ["max_drawdown[base]: FAIL (80% <= 25.0%)"])

    def test_the_largest_gap_says_where_it_is(self) -> None:
        dates = list(pd.date_range("2024-01-01", periods=10, freq="1h", tz="UTC")) + list(pd.date_range("2024-01-03", periods=5, freq="1h", tz="UTC"))
        path = self.root / "user_data" / "data" / "binance" / "BTC_USDT-1h.feather"
        path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"date": dates, "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0}).to_feather(path)
        row = next(r for r in self.state()["data_health"] if r["pair"] == "BTC/USDT")
        self.assertEqual(row["largest_gap_after"], "2024-01-01T09:00:00Z")

    def test_long_agent_results_keep_their_real_length(self) -> None:
        self.agent_run("completed", NOW, excerpt="z" * 1500)
        run = self.state()["agents"]["recent"][0]
        self.assertEqual((len(run["excerpt"]), run["excerpt_chars"]), (1000, 1500))


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

    def test_the_page_is_one_file_with_a_hash_route_per_module(self) -> None:
        page = dashboard.ASSET_PATH.read_text(encoding="utf-8")
        for route in ("overview", "research", "trades", "experiments", "strategies", "portfolio", "risk", "data"):
            self.assertIn(f"id: '{route}'", page)
        self.assertIn("hashchange", page)
        # the embedded state, the bundled chart library and the page's own script
        self.assertEqual(page.count("<script"), 3)

    def test_the_trades_view_is_inlined_and_as_strict_as_the_page(self) -> None:
        import re

        view = dashboard.TRADES_VIEW_PATH.read_text(encoding="utf-8")
        for forbidden in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "<script src"):
            self.assertNotIn(forbidden, view)
        # the only address in it is the attribution link the chart library's license asks for
        self.assertEqual(set(re.findall(r"https?://[^\s'\"`)<>]+", view)), {"https://www.tradingview.com/"})
        page = dashboard.render_page(self.state(), nonce="abc", live=True)
        for leftover in ("__TRADES_VIEW__", "__VENDOR_CHARTS__", "__STATE__", "__NONCE_ATTR__", "__LIVE__"):
            self.assertNotIn(leftover, page)
        self.assertIn("function pageTrades", page)
        self.assertIn("Lightweight Charts", page)
        self.assertEqual(page.count('<script nonce="abc">'), 2)  # library and page, both under the CSP nonce

    def test_the_page_does_not_read_or_compute_metrics_the_lab_lacks(self) -> None:
        import re

        page = dashboard.ASSET_PATH.read_text(encoding="utf-8")
        for name in ("sharpe", "sortino", "cagr", "win_rate", "profit_factor", "expectancy"):
            # The page may SAY these are not computed; it must not read them from the state.
            self.assertIsNone(re.search(rf"\.{name}\b|\[['\"]{name}['\"]\]", page), name)

    def test_the_exported_page_embeds_the_state_for_every_route(self) -> None:
        hid = self.hypothesis(1)
        self.experiment(hid, "BTC/USDT", "exploration", "rejected")
        out = dashboard.export_html(self.root / "out" / "d.html", self.state())
        page = out.read_text(encoding="utf-8")
        self.assertIn('"items":[{', page)
        self.assertIn(f'"id":"{hid}-exploration-BTC-USDT"', page)
        self.assertIn("const LIVE = false;", page)

    def test_the_page_inserts_text_only_with_text_nodes(self) -> None:
        page = dashboard.ASSET_PATH.read_text(encoding="utf-8")
        for forbidden in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval("):
            self.assertNotIn(forbidden, page)


class TradesPayloadTests(DashboardTestCase):
    def export(self, pair: str = "BTC/USDT", n: int = 2) -> str:
        base = 1_700_000_000_000
        trades = [
            {"pair": pair, "open_timestamp": base + i * 7_200_000, "close_timestamp": base + i * 7_200_000 + 3_600_000,
             "open_rate": 100.0, "close_rate": 103.0 if i % 2 == 0 else 98.0, "profit_ratio": 0.03 if i % 2 == 0 else -0.02,
             "profit_abs": 3.0 if i % 2 == 0 else -2.0, "stake_amount": 100.0, "exit_reason": "roi", "enter_tag": "t",
             "trade_duration": 60, "min_rate": 99.0, "max_rate": 104.0, "initial_stop_loss_abs": 90.0}
            for i in range(n)
        ] + [{"pair": "ETH/USDT", "open_timestamp": base, "close_timestamp": base + 1000}]
        stats = {"trades": trades, "timeframe": "1h", "sharpe": 0.5, "profit_factor": 1.5, "total_trades": n,
                 "winrate": 0.5, "max_relative_drawdown": 0.02, "starting_balance": 100.0}
        archive = self.root / "export.zip"
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("r.json", json.dumps({"strategy": {"S": stats}}))
        return "export.zip"

    def candles(self, pair: str = "BTC/USDT") -> None:
        import pandas as pd

        folder = self.root / "user_data" / "data" / "binance"
        folder.mkdir(parents=True)
        dates = pd.date_range("2023-11-10", periods=24 * 12, freq="1h", tz="UTC")
        pd.DataFrame({"date": dates, "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 5.0}).to_feather(
            folder / f"{pair.replace('/', '_')}-1h.feather")

    def payload(self, experiment_id: str):
        return dashboard.trades_payload(self.root, self.db_path, experiment_id)

    def test_it_returns_this_pairs_trades_with_stats_and_candles_marked_simulated(self) -> None:
        hid = self.hypothesis(1)
        eid = self.experiment(hid, "BTC/USDT", "exploration", "rejected", artifact=self.export())
        self.candles()
        status, body = self.payload(eid)
        self.assertEqual(status, 200)
        self.assertEqual(body["origin"], "simulated")
        self.assertEqual([t["n"] for t in body["trades"]], [1, 2])  # the ETH trade in the same export is not ours
        self.assertEqual(body["stats"]["sharpe"], 0.5)
        self.assertEqual(len(body["candles"][0]), 6)
        self.assertIsNone(body["candles_error"])
        json.dumps(body, allow_nan=False)

    def test_missing_candles_are_reported_not_invented(self) -> None:
        hid = self.hypothesis(1)
        eid = self.experiment(hid, "BTC/USDT", "exploration", "rejected", artifact=self.export())
        status, body = self.payload(eid)
        self.assertEqual((status, body["candles"]), (200, []))
        self.assertIn("no candle file", body["candles_error"])

    def test_unknown_runs_and_missing_results_are_404(self) -> None:
        hid = self.hypothesis(1)
        no_artifact = self.experiment(hid, "ETH/USDT", "exploration", "rejected")
        self.assertEqual(self.payload("nope")[0], 404)
        self.assertEqual(self.payload(no_artifact)[0], 404)

    def test_an_artifact_path_outside_the_project_is_refused(self) -> None:
        hid = self.hypothesis(1)
        outside = Path(self.tmp.name).parent / "outside.zip"
        with zipfile.ZipFile(outside, "w") as z:
            z.writestr("r.json", json.dumps({"strategy": {"S": {"trades": []}}}))
        try:
            eid = self.experiment(hid, "BTC/USDT", "exploration", "rejected", artifact="../outside.zip")
            status, body = self.payload(eid)
            self.assertEqual(status, 404)
            self.assertIn("outside", body["error"])
        finally:
            outside.unlink(missing_ok=True)


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

    def test_every_response_says_when_the_server_made_it(self) -> None:
        self.assertIn("served_at", json.loads(self.request("GET", "/api/state")[2]))

    def test_the_trades_endpoint_validates_its_input_and_stays_get_only(self) -> None:
        calls = []
        self.server.trades = lambda eid: (calls.append(eid) or (200, {"ok": eid}))
        self.assertEqual(self.request("GET", "/api/trades?experiment=H-001-exploration-BTC-USDT")[0], 200)
        self.assertEqual(calls, ["H-001-exploration-BTC-USDT"])
        for bad in ("/api/trades", "/api/trades?experiment=", "/api/trades?experiment=../x", "/api/trades?experiment=a%20b"):
            self.assertEqual(self.request("GET", bad)[0], 400, bad)
        self.assertEqual(self.request("POST", "/api/trades?experiment=x")[0], 405)
        self.assertEqual(self.request("GET", "/api/trades?experiment=x", host="evil.example")[0], 403)

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
