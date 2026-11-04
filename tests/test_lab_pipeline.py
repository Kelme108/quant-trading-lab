import functools
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).parent
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS.parent))

from lab import archive, calibrate, checks, guard, orchestrator, pipeline, registry  # noqa: E402
from test_lab_orchestrator import BUDGET, LabTestCase, PAIRS, SCOUT_IDEAS, git, now  # noqa: E402

CHECKS_OK = {p: {"smoke_ok": True, "lookahead_has_bias": False, "recursive_is_stable": True} for p in PAIRS}


def queue_idea(conn, number: int, idea: dict | None = None, score: float = 3.0) -> str:
    idea = dict(idea or SCOUT_IDEAS[0])
    idea["title"] = f"{idea['title']} {number}"
    idea_id = f"I-{number:03d}"
    registry.add_idea(conn, idea_id=idea_id, run_id="S", idea=idea, rule_hash=idea_id, created_at_utc=now())
    registry.set_idea_state(conn, idea_id, "queued", "", score)
    return idea_id


class PipelineTestCase(LabTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.checks_result = CHECKS_OK
        self.checks_calls: list[str] = []
        self.reviewed: list[str] = []
        self.explore_calls: list[str] = []
        self.explore_outcome = "explored"
        self.pipe = self.make_pipeline()

    def fake_checks(self, name, **kwargs):
        self.checks_calls.append(name)
        return self.checks_result

    def fake_explore(self, conn, hid, **kwargs):
        self.explore_calls.append(hid)
        if self.explore_outcome == "dropped_trades":
            registry.set_hypothesis_status(conn, hid, "dropped: fewer than 30 trades")
            return {"outcome": "dropped_trades", "counts": {p: 12 for p in PAIRS}, "exposure": None, "status": "dropped: fewer than 30 trades"}
        self.lab.run_split(hid, "exploration")
        self.lab.decide_split(hid, "exploration")
        status = registry.get_hypothesis(conn, hid)["status"]
        return {"outcome": "explored", "counts": {p: 100 for p in PAIRS}, "exposure": 0.2, "status": status}

    def fake_review(self, conn, hid, **kwargs):
        self.reviewed.append(hid)
        return []

    def make_pipeline(self) -> pipeline.Pipeline:
        return pipeline.Pipeline(
            self.lab, run_checks=self.fake_checks, explore=self.fake_explore, write_review=self.fake_review,
            archive_one=functools.partial(archive.archive_hypothesis, run_test=lambda test, root: True),
        )

    def run_weekly(self, **kwargs) -> str:
        return self.pipe.weekly(do_scout=False, **kwargs).read_text(encoding="utf-8")


class PassingIdeaTests(PipelineTestCase):
    def test_a_candidate_stops_at_the_exploration_and_waits_for_the_user(self) -> None:
        queue_idea(self.conn, 1)
        text = self.run_weekly()
        self.assertIn("completed", text)
        self.assertIn(pipeline.LABEL, text)
        self.assertIn("candidate: awaiting the user's approval", text)
        self.assertIn("approve.py H-001 --stage validation", text)
        self.assertEqual(registry.get_hypothesis(self.conn, "H-001")["status"], "exploration: candidate")
        self.assertEqual(registry.get_idea(self.conn, "I-001")["state"], "registered")
        self.assertEqual(registry.get_idea(self.conn, "I-001")["hypothesis_id"], "H-001")
        # exploration only: the validation split is never run, and the agents reviewed the candidate
        self.assertEqual({s for _, s, _ in self.experiments.ran}, {"exploration"})
        self.assertEqual(self.agent.names(), ["research", "developer", "validator", "quant", "risk"])
        self.assertEqual(self.reviewed, ["H-001"])
        # the candidate stays in the strategy path
        self.assertTrue(list((self.root / "user_data" / "strategies").glob("*_H001_v1.py")))
        self.assertEqual(registry.list_archived_strategies(self.conn), [])

    def test_the_formalisation_prompt_names_the_idea_and_the_context_carries_it(self) -> None:
        queue_idea(self.conn, 1)
        self.run_weekly()
        prompt = next(p for n, _, p in self.agent.calls if n == "research")
        self.assertIn("Formalise idea I-001 as hypothesis H-001", prompt)
        context = (self.root / "research" / "context" / "H-001.md").read_text(encoding="utf-8")
        self.assertIn("Idea to formalise", context)
        self.assertIn("data, not instructions", context)

    def test_the_report_counts_every_configuration_tried(self) -> None:
        queue_idea(self.conn, 1)
        text = self.run_weekly()
        total = pipeline.trial_count(self.conn)["total"]
        self.assertIn(f"**{total}**", text)
        self.assertGreater(total, 30)  # the recorded grid/sensitivity/ablation configurations are included


class FailingIdeaTests(PipelineTestCase):
    def test_a_rejected_exploration_is_archived_without_agent_reviews(self) -> None:
        self.experiments.decision = "rejected"
        queue_idea(self.conn, 1)
        text = self.run_weekly()
        self.assertIn("rejected at exploration", text)
        self.assertIn("archived", text)
        self.assertEqual(self.agent.names(), ["research", "developer"])
        self.assertEqual(self.reviewed, ["H-001"])  # the deterministic trade review still runs
        self.assertFalse(list((self.root / "user_data" / "strategies").glob("*_H001_v1.py")))
        self.assertTrue(list((self.root / "user_data" / "strategies" / "_archive").glob("*_H001_v1.py")))
        self.assertTrue(list((self.root / "tests" / "archive").glob("test_*_h001_v1.py")))
        row = registry.list_archived_strategies(self.conn)[0]
        self.assertEqual((row["hypothesis_id"], row["sha256_source"]), ("H-001", "file_at_archive_time"))
        self.assertEqual(registry.get_hypothesis(self.conn, "H-001")["status"], "rejected at exploration")  # status untouched

    def test_too_few_trades_drops_and_archives(self) -> None:
        self.explore_outcome = "dropped_trades"
        queue_idea(self.conn, 1)
        text = self.run_weekly()
        self.assertIn("dropped: fewer than 30 trades", text)
        self.assertEqual(self.reviewed, [])
        self.assertEqual(len(registry.list_archived_strategies(self.conn)), 1)

    def test_failed_causality_checks_stop_that_hypothesis_before_any_backtest(self) -> None:
        self.checks_result = {p: {**CHECKS_OK[p], "lookahead_has_bias": True} for p in PAIRS}
        queue_idea(self.conn, 1)
        text = self.run_weekly()
        self.assertIn("failed the causality checks", text)
        self.assertEqual(self.explore_calls, [])
        self.assertEqual(registry.get_hypothesis(self.conn, "H-001")["status"], "failed: causality checks")
        self.assertEqual(len(registry.list_archived_strategies(self.conn)), 1)

    def test_an_idea_that_cannot_be_formalised_is_dropped_and_the_run_goes_on(self) -> None:
        queue_idea(self.conn, 1, score=4.0)
        queue_idea(self.conn, 2, score=3.0)
        calls = {"n": 0}

        def bad_then_good(prompt: str) -> None:
            calls["n"] += 1
            if calls["n"] <= 2:  # both attempts for the first idea
                self.agent.write(re.search(r"Write the proposal to (\S+)\.", prompt).group(1), "{not json")
            else:
                self.agent.good_research(prompt)

        self.agent.handlers["research"] = bad_then_good
        text = self.run_weekly()
        self.assertEqual(registry.get_idea(self.conn, "I-001")["state"], "dropped")
        self.assertIn("could not be formalised", registry.get_idea(self.conn, "I-001")["state_reason"])
        self.assertEqual(registry.get_idea(self.conn, "I-002")["state"], "registered")
        self.assertIn("not formalised", text)
        self.assertIn("completed", text)

    def test_an_implementation_that_never_passes_marks_the_hypothesis_failed_and_continues(self) -> None:
        queue_idea(self.conn, 1)
        self.lab._run_test_suite = lambda: (False, "tests fail")
        text = self.run_weekly()
        self.assertIn("implementation failed", text)
        self.assertEqual(registry.get_hypothesis(self.conn, "H-001")["status"], "failed: implementation")
        self.assertIn("completed", text)

    def test_a_rejected_implementation_is_set_aside_so_the_next_idea_is_not_blocked_by_its_test(self) -> None:
        queue_idea(self.conn, 1, score=4.0)
        queue_idea(self.conn, 2, score=3.0)
        tests_dir = self.root / "tests"
        # the suite fails exactly while H-001's broken test sits in tests/ (as a real failing test would)
        self.lab._run_test_suite = lambda: (not list(tests_dir.glob("test_*_h001_v1.py")), "H-001 test fails")
        self.run_weekly()
        self.assertEqual(registry.get_hypothesis(self.conn, "H-001")["status"], "failed: implementation")
        self.assertNotEqual(registry.get_hypothesis(self.conn, "H-002")["status"], "failed: implementation")
        self.assertFalse(list((self.root / "user_data" / "strategies").glob("*_H001_v1.py")))
        self.assertFalse(list(tests_dir.glob("test_*_h001_v1.py")))
        kept = sorted(p.name for p in (self.root / "research" / "rejected" / "H-001").iterdir())
        self.assertEqual(len(kept), 2)
        self.assertTrue(all(name.endswith(".py.rejected") for name in kept))

    def test_an_unexpected_exploration_error_fails_that_hypothesis_and_the_run_goes_on(self) -> None:
        queue_idea(self.conn, 1, score=4.0)
        queue_idea(self.conn, 2, score=3.0)
        original = self.fake_explore

        def crash_first(conn, hid, **kwargs):
            if hid == "H-001":
                raise RuntimeError("docker is not running")
            return original(conn, hid, **kwargs)

        self.pipe.explore = crash_first
        text = self.run_weekly()
        self.assertIn("completed", text)
        self.assertIn("exploration failed", text)
        self.assertIn("docker is not running", text)
        self.assertEqual(registry.get_hypothesis(self.conn, "H-001")["status"], "failed: exploration")
        self.assertEqual(registry.get_hypothesis(self.conn, "H-002")["status"], "exploration: candidate")
        self.assertEqual(len(registry.list_archived_strategies(self.conn)), 1)  # H-001 left the strategy path

    def test_the_report_names_the_pair_and_gate_that_rejected(self) -> None:
        self.pipe.explore = lambda conn, hid, **kw: (
            registry.set_hypothesis_status(conn, hid, "rejected at exploration"),
            {"outcome": "explored", "counts": {p: 50 for p in PAIRS}, "exposure": 0.2, "status": "rejected at exploration",
             "failed_gates": {"ETH/USDT": ["net_profit[base]", "net_profit[conservative]"]}},
        )[1]
        queue_idea(self.conn, 1)
        text = self.run_weekly()
        self.assertIn("failed gates: ETH/USDT net_profit[base], net_profit[conservative]", text)

    def test_an_unexpected_error_outside_a_hypothesis_still_writes_the_report(self) -> None:
        def broken_triage():
            raise KeyError("malformed idea row")

        self.lab.triage_ideas = broken_triage
        text = self.run_weekly()
        self.assertIn("STOPPED - KeyError", text)


class StoppingTests(PipelineTestCase):
    def test_a_guard_violation_stops_the_whole_run_and_says_so(self) -> None:
        queue_idea(self.conn, 1, score=4.0)
        queue_idea(self.conn, 2, score=3.0)

        def sneaky(prompt: str) -> None:
            self.agent.good_developer(prompt)
            self.agent.write("user_data/strategies/SmaTrendBaseline.py", "tampered\n")

        self.agent.handlers["developer"] = sneaky
        text = self.run_weekly()
        self.assertIn("STOPPED - GuardAbort", text)
        self.assertEqual(registry.get_idea(self.conn, "I-002")["state"], "queued")  # never touched
        self.assertEqual(self.explore_calls, [])

    def test_the_agent_spend_cap_stops_the_run(self) -> None:
        queue_idea(self.conn, 1)
        self.lab = self.make_lab(budget={**BUDGET, "max_agent_budget_usd_per_cycle": 1.0})
        self.pipe = self.make_pipeline()
        text = self.run_weekly()
        self.assertIn("STOPPED - BudgetExhausted", text)

    def test_the_number_of_new_hypotheses_is_capped(self) -> None:
        for number in (1, 2, 3, 4):
            queue_idea(self.conn, number, score=5.0 - number)
        self.lab = self.make_lab(budget={**BUDGET, "max_hypotheses_per_cycle": 2, "max_agent_budget_usd_per_cycle": 100.0})
        self.pipe = self.make_pipeline()
        self.run_weekly(max_new=10)
        self.assertEqual(len(registry.list_hypotheses(self.conn)), 2)
        self.assertEqual([i["state"] for i in registry.list_ideas(self.conn)], ["registered", "registered", "queued", "queued"])

    def test_scouting_runs_first_and_its_ideas_are_triaged(self) -> None:
        self.lab.splits = {"pairs": {p: {"exploration": {"start_utc": "2018-01-01T00:00:00Z", "end_utc": "2024-12-31T00:00:00Z"}} for p in PAIRS}}
        self.pipe = self.make_pipeline()
        text = self.pipe.weekly(scout_count=2, max_new=1).read_text(encoding="utf-8")
        self.assertEqual(self.agent.names()[0], "scout")
        self.assertIn("Scout: 2 idea(s) collected", text)
        self.assertEqual(len(registry.list_hypotheses(self.conn)), 1)


class ChecksTests(unittest.TestCase):
    def test_passed_needs_every_pair_clean_and_unknown_counts_as_failed(self) -> None:
        self.assertTrue(checks.passed(CHECKS_OK))
        self.assertFalse(checks.passed({}))
        for key, bad in (("smoke_ok", False), ("lookahead_has_bias", True), ("lookahead_has_bias", None),
                         ("recursive_is_stable", False), ("recursive_is_stable", None)):
            broken = {**CHECKS_OK, "BTC/USDT": {**CHECKS_OK["BTC/USDT"], key: bad}}
            self.assertFalse(checks.passed(broken), (key, bad))


class FakeBacktest:
    def __init__(self, trades_per_pair: int) -> None:
        self.n = trades_per_pair

    def __call__(self, **kwargs):
        return {"status": "completed", "artifact_path": "x.zip"}

    def read_trades(self, path):
        return [{"open_date": f"2020-01-{1 + i % 28:02d} {i % 24:02d}:00:00+00:00", "profit_ratio": 0.04 if i % 3 == 0 else -0.01}
                for i in range(self.n)]


class FakeExplorer:
    def __init__(self, decision: str = "candidate_for_portfolio") -> None:
        self.decision, self.exposures = decision, []

    def freqtrade_version(self) -> str:
        return "fake"

    def run_experiment(self, conn, *, hypothesis_id, strategy_name, strategy_file, pair, split_name, timestamp, splits,
                       version, notes="", exposure=1.0, timeframe="1h"):
        self.exposures.append(exposure)
        experiment_id = f"{timestamp}-{hypothesis_id.lower()}-{split_name}-{pair.replace('/', '-').lower()}"
        registry.add_experiment(conn, experiment_id=experiment_id, hypothesis_id=hypothesis_id, strategy_file=strategy_file,
                                strategy_sha256="0" * 64, cost_scenario="multi", split=split_name, command="",
                                created_at_utc=now(), pair=pair)
        return experiment_id

    def decide_experiment(self, conn, experiment_id, hypothesis_id):
        return self.decision, ["fake"]


class CalibrateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.conn = registry.connect(Path(self.tmp.name) / "lab.sqlite")
        registry.add_hypothesis(self.conn, hypothesis_id="H-001", family="F", ex_ante_rule="r", proposed_at_utc=now(),
                                data_visible_at_proposal="d", status="proposed")
        self.splits = {"pairs": {p: {"exploration": {"timerange": "1-2", "start_utc": "2018-01-01T00:00:00Z", "end_utc": "2024-01-01T00:00:00Z"}} for p in PAIRS}}

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def run_calibration(self, trades: int, explorer: FakeExplorer):
        fake = FakeBacktest(trades)
        return calibrate.calibrate_and_explore(
            self.conn, "H-001", strategy_name="S_H001_v1", strategy_file="user_data/strategies/S_H001_v1.py",
            root=Path(self.tmp.name), splits=self.splits, backtest=fake, read_trades=fake.read_trades,
            experiments=explorer, pairs=list(PAIRS),
        )

    def test_fewer_than_30_trades_drops_the_hypothesis_without_running_the_experiment(self) -> None:
        explorer = FakeExplorer()
        result = self.run_calibration(29, explorer)
        self.assertEqual(result["outcome"], "dropped_trades")
        self.assertEqual(explorer.exposures, [])
        row = registry.get_hypothesis(self.conn, "H-001")
        self.assertEqual(row["status"], "dropped: fewer than 30 trades")
        self.assertIn("not retuned", row["notes"])

    def test_enough_trades_calibrates_one_exposure_for_every_pair_and_records_the_decision_status(self) -> None:
        explorer = FakeExplorer()
        result = self.run_calibration(60, explorer)
        self.assertEqual(result["outcome"], "explored")
        self.assertEqual(len(explorer.exposures), 3)
        self.assertEqual(len(set(explorer.exposures)), 1)
        self.assertEqual(explorer.exposures[0], result["exposure"])
        self.assertEqual(registry.get_hypothesis(self.conn, "H-001")["status"], "exploration: candidate")
        self.assertIn("Calibrated exposure", registry.get_hypothesis(self.conn, "H-001")["notes"])

    def test_a_rejected_decision_sets_the_matching_status(self) -> None:
        self.run_calibration(60, FakeExplorer("rejected"))
        self.assertEqual(registry.get_hypothesis(self.conn, "H-001")["status"], "rejected at exploration")

    def test_the_failing_gates_are_returned_per_pair(self) -> None:
        explorer = FakeExplorer("rejected")
        explorer.decide_experiment = lambda conn, eid, hid: ("rejected", [
            "lookahead: pass (has_bias=False)",
            "net_profit[base]: FAIL (net_profit_quote=-0.1 <= required 1.0000, after 0 prior variant(s) in family)",
            "minimum_trades[stress]: inconclusive (20 < 30)",
        ])
        result = self.run_calibration(60, explorer)
        self.assertEqual(result["failed_gates"], {p: ["net_profit[base]", "minimum_trades[stress]"] for p in PAIRS})

    def test_a_failed_calibration_backtest_is_reported(self) -> None:
        result = calibrate.calibrate_and_explore(
            self.conn, "H-001", strategy_name="S", strategy_file="f", root=Path(self.tmp.name), splits=self.splits,
            backtest=lambda **kw: {"status": "failed"}, read_trades=lambda p: [], experiments=FakeExplorer(), pairs=list(PAIRS))
        self.assertEqual(result["outcome"], "failed")


class ArchiveTests(unittest.TestCase):
    TEST_SOURCE = (
        "from pathlib import Path\n"
        "ROOT = Path(__file__).parents[1]\n"
        "path = ROOT / \"user_data\" / \"strategies\" / \"Thing_H007_v1.py\"\n"
    )

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.conn = registry.connect(self.root / "lab.sqlite")
        registry.add_hypothesis(self.conn, hypothesis_id="H-007", family="Thing", ex_ante_rule="r", proposed_at_utc=now(),
                                data_visible_at_proposal="d", status="rejected at exploration")
        (self.root / "user_data" / "strategies").mkdir(parents=True)
        (self.root / "tests").mkdir()
        self.strategy = self.root / "user_data" / "strategies" / "Thing_H007_v1.py"
        self.strategy.write_text("# strategy\n", encoding="utf-8")
        self.test = self.root / "tests" / "test_thing_h007_v1.py"
        self.test.write_text(self.TEST_SOURCE, encoding="utf-8")

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def test_retarget_moves_the_root_and_the_strategy_folder(self) -> None:
        text = archive.retarget_test(self.TEST_SOURCE)
        self.assertIn("parents[2]", text)
        self.assertIn('"strategies" / "_archive" / "Thing_H007_v1.py"', text)
        self.assertEqual(archive.retarget_test(text), text)  # idempotent

    def test_archiving_moves_both_files_records_the_sha_and_changes_no_status(self) -> None:
        result = archive.archive_hypothesis(self.conn, "H-007", root=self.root, run_test=lambda t, r: True)
        self.assertTrue(result["archived"])
        self.assertFalse(self.strategy.exists())
        self.assertEqual((self.root / "user_data" / "strategies" / "_archive" / "Thing_H007_v1.py").read_text(encoding="utf-8"), "# strategy\n")
        self.assertIn("parents[2]", (self.root / "tests" / "archive" / "test_thing_h007_v1.py").read_text(encoding="utf-8"))
        row = registry.list_archived_strategies(self.conn)[0]
        import hashlib
        archived = self.root / "user_data" / "strategies" / "_archive" / "Thing_H007_v1.py"
        self.assertEqual(row["strategy_sha256"], hashlib.sha256(archived.read_bytes()).hexdigest())
        self.assertEqual(registry.get_hypothesis(self.conn, "H-007")["status"], "rejected at exploration")

    def test_a_failing_archived_test_puts_everything_back(self) -> None:
        original_test_bytes, original_strategy_bytes = self.test.read_bytes(), self.strategy.read_bytes()
        result = archive.archive_hypothesis(self.conn, "H-007", root=self.root, run_test=lambda t, r: False)
        self.assertFalse(result["archived"])
        self.assertEqual(self.strategy.read_bytes(), original_strategy_bytes)
        self.assertEqual(self.test.read_bytes(), original_test_bytes)  # byte for byte
        self.assertEqual(registry.list_archived_strategies(self.conn), [])

    def test_nothing_to_archive_is_reported(self) -> None:
        self.strategy.unlink()
        self.assertFalse(archive.archive_hypothesis(self.conn, "H-007", root=self.root)["archived"])


class TrialCountTests(unittest.TestCase):
    def test_total_is_registered_hypotheses_plus_the_recorded_extra_configurations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            conn = registry.connect(Path(tmp) / "lab.sqlite")
            ledger = Path(tmp) / "ledger.json"
            ledger.write_text(json.dumps({"extra_configurations": [{"what": "a", "n": 9}, {"what": "b", "n": 4}]}), encoding="utf-8")
            registry.add_hypothesis(conn, hypothesis_id="H-001", family="F", ex_ante_rule="r", proposed_at_utc=now(),
                                    data_visible_at_proposal="d", status="proposed")
            self.assertEqual(pipeline.trial_count(conn, ledger), {"hypotheses": 1, "extra": 13, "total": 14})
            conn.close()

    def test_the_real_ledger_matches_the_audit_report(self) -> None:
        extra = sum(i["n"] for i in json.loads(pipeline.TRIAL_LEDGER.read_text(encoding="utf-8"))["extra_configurations"])
        self.assertEqual(extra, 30)  # 17 hypotheses + 30 = the 47 rules counted in the audit report at H-017


if __name__ == "__main__":
    unittest.main()
