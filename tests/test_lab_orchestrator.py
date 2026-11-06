import copy
import json
import re
import subprocess
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timezone
from pathlib import Path

from lab import agents, guard, orchestrator, registry

import pin_pairs  # noqa: E402

setUpModule, tearDownModule = pin_pairs.module_fixtures()


PAIRS = ("BTC/USDT", "ETH/USDT", "BNB/USDT")

PROPOSAL = {
    "hypothesis_id": "H-001",
    "family": "TrendFilter",
    "title": "Slow trend filter with volatility gate",
    "ex_ante_rule": (
        "Enter long when the close is above the 400-candle simple moving average; exit when the "
        "close falls below it. Stop-loss at 10 percent. Evaluated on closed candles only. Warm-up: 400 bars."
    ),
    "parameters": {"sma_length": 400, "stoploss": -0.10},
    "rationale": (
        "Trend persistence in liquid crypto has been documented over multi-week horizons; a slow "
        "filter trades rarely, so round-trip costs are small against the expected move."
    ),
    "novelty_vs_tried": "Far fewer trades than the breakout baselines; a different mechanism.",
    "sources": [{"title": "Time series momentum", "url": "https://example.org/paper"}],
    "timeframe": "1h",
    "data_visible_at_proposal": "BTC, ETH, BNB 1h through 2026-10-20",
}

STRATEGY = '''
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class {stem}(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False
    minimal_roi = {{"0": 100.0}}
    stoploss = -0.10
    startup_candle_count = 400

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["sma"] = dataframe["close"].rolling(400).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["close"] > dataframe["sma"], "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["close"] < dataframe["sma"], "exit_long"] = 1
        return dataframe
'''

BUDGET = {
    "max_hypotheses_per_cycle": 3,
    "max_variants_per_family": 3,
    "agent_budget_usd_per_call": 2.0,
    "max_agent_budget_usd_per_cycle": 12.0,
    "agent_timeout_seconds": 10,
}


def window(start: str, end: str) -> dict:
    return {"start_utc": start, "end_utc": end, "timerange": "1-2"}


SPLITS = {
    "pairs": {
        pair: {
            "exploration": window("2020-01-01T00:00:00Z", "2020-03-01T00:00:00Z"),
            "validation": window("2020-03-02T00:00:00Z", "2020-04-01T00:00:00Z"),
        }
        for pair in PAIRS
    },
    "final_test": {"final_test_unlocked": False, "timerange": "9-"},
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


SCOUT_IDEAS = [
    {
        "title": "Fifty day breakout with a monthly trend filter",
        "source": {"type": "paper", "url": "https://example.org/a", "title": "A paper", "license": "unknown"},
        "rule_summary": "Enter long when the daily close is above the highest close of the previous fifty days and the thirty day average is rising; exit when the close falls under the lowest close of the previous twenty days.",
        "mechanism": "Slow investors react late to news so large moves persist, and trend followers are paid for providing liquidity to them.",
        "timeframe": "1d", "longest_lookback": 50, "free_parameters": 3, "fixed_parameters": True,
        "expected_trades_per_year": 12, "family_hint": "FiftyDayBreakout",
    },
    {
        "title": "Volume surge after a quiet week",
        "source": {"type": "blog", "url": "https://example.org/b", "title": "A blog", "license": "none"},
        "rule_summary": "Buy at the next hourly open when the hourly volume is four times its seventy two hour average right after a week of low realised volatility, and sell after one hundred and twenty hours or on a five percent stop.",
        "mechanism": "Quiet markets hide accumulation; a volume surge shows that informed buyers are crossing the spread and the move tends to continue for days.",
        "timeframe": "1h", "longest_lookback": 168, "free_parameters": 4, "fixed_parameters": False,
        "expected_trades_per_year": 20, "family_hint": "VolumeSurge",
    },
]


class FakeAgent:
    """Stands in for agents.run_agent. Each agent name has a handler that
    writes whatever that test wants; the default handlers behave correctly."""

    def __init__(self, root: Path, cost: float = 1.0) -> None:
        self.root = root
        self.cost = cost
        self.calls: list[tuple[str, str, str]] = []
        self.handlers = {
            "research": self.good_research,
            "scout": self.good_scout,
            "developer": self.good_developer,
            "validator": self.good_review,
            "quant": self.good_review,
            "risk": self.good_review,
        }

    def write(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def good_research(self, prompt: str) -> None:
        target = re.search(r"Write the proposal to (\S+)\.", prompt).group(1)
        proposal = copy.deepcopy(PROPOSAL)
        proposal["hypothesis_id"] = Path(target).stem
        self.write(target, json.dumps(proposal))

    def good_scout(self, prompt: str) -> None:
        paths = re.search(r"Write the idea files to (.+?) \(only", prompt).group(1).split(", ")
        for path, idea in zip(paths, SCOUT_IDEAS):  # two ideas, however many files were allowed
            self.write(path, json.dumps(idea))

    def good_developer(self, prompt: str) -> None:
        strategy, stem, test = re.search(
            r"Strategy file: (\S+) \(class (\S+)\)\. Test file: (\S+)\.", prompt
        ).groups()
        self.write(strategy, STRATEGY.format(stem=stem))
        self.write(test, "import unittest\n")

    def good_review(self, prompt: str) -> None:
        self.write(re.search(r"Write (\S+)\.$", prompt).group(1), "report")

    def __call__(self, conn, name, prompt, *, purpose, budget_usd, timeout_s, hypothesis_id=None):
        self.calls.append((name, purpose, prompt))
        self.handlers[name](prompt)
        registry.record_agent_run(
            conn, agent=name, purpose=purpose, status="completed", started_at_utc=now(),
            hypothesis_id=hypothesis_id, cost_usd=self.cost,
        )
        return agents.AgentResult("ok", self.cost, 1, 0.1, None)

    def names(self) -> list[str]:
        return [name for name, _, _ in self.calls]


class FakeExperiments:
    """Stands in for lab.experiment: records rows and decisions, runs nothing."""

    class ExperimentFailed(RuntimeError):
        pass

    def __init__(self, decision: str = "candidate_for_portfolio", fail: bool = False) -> None:
        self.decision = decision
        self.fail = fail
        self.ran: list[tuple[str, str, str]] = []

    def freqtrade_version(self) -> str:
        return "fake"

    def run_experiment(self, conn, *, hypothesis_id, strategy_name, strategy_file, pair,
                       split_name, timestamp, splits, version, notes="", timeframe="1h"):
        if self.fail:
            raise self.ExperimentFailed("backtest exploded")
        experiment_id = f"{timestamp}-{hypothesis_id.lower()}-{split_name}-{pair.replace('/', '-').lower()}"
        # A real backtest takes minutes, so two runs never share a second; the fake runs instantly,
        # so a re-run inside the same second needs its own suffix to keep experiments.id unique.
        if conn.execute("SELECT 1 FROM experiments WHERE id = ?", (experiment_id,)).fetchone():
            experiment_id += f"-r{len(self.ran)}"
        registry.add_experiment(
            conn, experiment_id=experiment_id, hypothesis_id=hypothesis_id,
            strategy_file=strategy_file, strategy_sha256="0" * 64, cost_scenario="multi",
            split=split_name, command="", created_at_utc=now(), pair=pair,
        )
        registry.record_metrics(conn, experiment_id, {"trades__base": 100, "net_profit_quote__base": 10.0})
        registry.set_experiment_status(conn, experiment_id, "completed")
        self.ran.append((hypothesis_id, split_name, pair))
        return experiment_id

    def decide_experiment(self, conn, experiment_id, hypothesis_id):
        registry.record_decision(
            conn, experiment_id=experiment_id, decision=self.decision, reasons=["fake"],
            gates_sha256="x", decided_at_utc=now(),
        )
        return self.decision, ["fake"]


def git(args: list[str], cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


class LabTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        git(["init", "-q"], self.root)
        git(["config", "user.email", "test@example.com"], self.root)
        git(["config", "user.name", "Test"], self.root)
        for relative in (
            "docker-compose.yml", "user_data/config.dryrun.json", "research/validation-protocol-v2.md",
            "lab/config/gates.json", "research/proposals/.gitkeep", "tests/.gitkeep",
            "user_data/strategies/SmaTrendBaseline.py",
            "user_data/strategies/DonchianBreakoutBaseline.py",
            "user_data/strategies/BollingerMeanReversionBaseline.py",
        ):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("original\n", encoding="utf-8")
        git(["add", "-A", "."], self.root)
        git(["commit", "-q", "-m", "initial"], self.root)

        self.conn = registry.connect(Path(self.tmp.name) / "lab.sqlite")
        self.agent = FakeAgent(self.root)
        self.experiments = FakeExperiments()
        self.lab = self.make_lab()

    def make_lab(self, budget: dict | None = None) -> orchestrator.Lab:
        lab = orchestrator.Lab(
            self.conn, root=self.root, budget=budget or dict(BUDGET),
            agent_runner=self.agent, experiments=self.experiments, splits=SPLITS,
        )
        lab._run_test_suite = lambda: (True, "")
        lab._smoke_check = lambda stem: (True, "")
        return lab

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()


class ProposeTests(LabTestCase):
    def test_a_valid_proposal_is_registered_and_committed(self) -> None:
        hypothesis_id = self.lab.propose()
        self.assertEqual(hypothesis_id, "H-001")
        row = registry.get_hypothesis(self.conn, "H-001")
        self.assertEqual(row["family"], "TrendFilter")
        self.assertEqual(row["status"], "proposed")
        self.assertIn("H-001", (self.root / "research" / "hypothesis-ledger.md").read_text(encoding="utf-8"))
        self.assertIn("exp(H-001)", git(["log", "--oneline", "-1"], self.root))
        self.assertEqual(guard.changed_files(self.root), [])

    def test_an_invalid_proposal_gets_one_retry_with_the_errors(self) -> None:
        attempts = {"n": 0}

        def sometimes_bad(prompt: str) -> None:
            attempts["n"] += 1
            if attempts["n"] == 1:
                target = re.search(r"Write the proposal to (\S+)\.", prompt).group(1)
                bad = copy.deepcopy(PROPOSAL)
                bad["hypothesis_id"] = "H-001"
                del bad["rationale"]
                self.agent.write(target, json.dumps(bad))
            else:
                self.agent.good_research(prompt)

        self.agent.handlers["research"] = sometimes_bad
        self.assertEqual(self.lab.propose(), "H-001")
        self.assertEqual(self.agent.names(), ["research", "research"])
        self.assertIn("rationale", self.agent.calls[1][2])

    def test_a_proposal_that_stays_invalid_registers_nothing(self) -> None:
        self.agent.handlers["research"] = lambda prompt: self.agent.write(
            re.search(r"Write the proposal to (\S+)\.", prompt).group(1), "{not json"
        )
        with self.assertRaises(orchestrator.StepFailed):
            self.lab.propose()
        self.assertEqual(registry.list_hypotheses(self.conn), [])
        self.assertEqual(len(self.agent.calls), 2)

    def test_a_family_at_its_cap_is_refused(self) -> None:
        for number in range(3):
            registry.add_hypothesis(
                self.conn, hypothesis_id=f"H-{number + 1:03d}", family="TrendFilter",
                ex_ante_rule="r", proposed_at_utc=now(), data_visible_at_proposal="t",
            )
        with self.assertRaises(orchestrator.StepFailed):
            self.lab.propose()
        self.assertEqual(len(registry.list_hypotheses(self.conn)), 3)

    def test_the_context_file_hides_validation_numbers(self) -> None:
        registry.add_hypothesis(
            self.conn, hypothesis_id="H-001", family="Old", ex_ante_rule="old rule",
            proposed_at_utc=now(), data_visible_at_proposal="t",
        )
        self.experiments.run_experiment(
            self.conn, hypothesis_id="H-001", strategy_name="Old", strategy_file="x.py",
            pair="BTC/USDT", split_name="validation", timestamp="20260101T000000Z",
            splits=SPLITS, version="v",
        )
        self.lab.propose()
        text = (self.root / "research" / "context" / "H-002.md").read_text(encoding="utf-8")
        self.assertIn("numbers withheld on purpose", text)
        self.assertNotIn("net profit=10.0", text)


class GuardTests(LabTestCase):
    def test_writing_a_stray_file_aborts_the_step(self) -> None:
        def sneaky(prompt: str) -> None:
            self.agent.good_research(prompt)
            self.agent.write("lab/injected.py", "x")

        self.agent.handlers["research"] = sneaky
        with self.assertRaises(orchestrator.GuardAbort):
            self.lab.propose()
        self.assertEqual(registry.list_hypotheses(self.conn), [])
        status = self.conn.execute("SELECT status FROM agent_runs ORDER BY id DESC LIMIT 1").fetchone()
        self.assertEqual(status["status"], "guard_violation")

    def test_a_protected_file_is_restored_and_the_step_aborts(self) -> None:
        def tamper(prompt: str) -> None:
            self.agent.good_research(prompt)
            self.agent.write("docker-compose.yml", "tampered\n")

        self.agent.handlers["research"] = tamper
        with self.assertRaises(orchestrator.GuardAbort):
            self.lab.propose()
        self.assertEqual((self.root / "docker-compose.yml").read_text(encoding="utf-8"), "original\n")

    def test_a_guard_violation_is_never_retried(self) -> None:
        self.agent.handlers["research"] = lambda prompt: self.agent.write("lab/injected.py", "x")
        with self.assertRaises(orchestrator.GuardAbort):
            self.lab.propose()
        self.assertEqual(len(self.agent.calls), 1)

    def test_preexisting_uncommitted_work_does_not_trip_the_guard(self) -> None:
        (self.root / "lab").mkdir(exist_ok=True)
        (self.root / "lab" / "work_in_progress.py").write_text("x", encoding="utf-8")
        self.assertEqual(self.lab.propose(), "H-001")


class ImplementTests(LabTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.lab.propose()

    def test_strategy_and_test_are_written_screened_and_committed(self) -> None:
        stem = self.lab.implement("H-001")
        self.assertEqual(stem, "TrendFilter_H001_v1")
        self.assertTrue((self.root / "user_data/strategies/TrendFilter_H001_v1.py").is_file())
        self.assertEqual(registry.get_hypothesis(self.conn, "H-001")["status"], "implemented")
        self.assertIn("strategy TrendFilter_H001_v1 implemented", git(["log", "--oneline", "-1"], self.root))

    def test_a_strategy_that_fails_the_static_screen_gets_one_retry(self) -> None:
        calls = {"n": 0}

        def first_bad(prompt: str) -> None:
            calls["n"] += 1
            strategy, stem, test = re.search(
                r"Strategy file: (\S+) \(class (\S+)\)\. Test file: (\S+)\.", prompt
            ).groups()
            source = STRATEGY.format(stem=stem)
            if calls["n"] == 1:
                source = "import os\n" + source
            self.agent.write(strategy, source)
            self.agent.write(test, "import unittest\n")

        self.agent.handlers["developer"] = first_bad
        self.assertEqual(self.lab.implement("H-001"), "TrendFilter_H001_v1")
        self.assertIn("import of 'os'", self.agent.calls[-1][2])

    def test_a_strategy_that_keeps_failing_the_screen_is_rejected(self) -> None:
        def always_bad(prompt: str) -> None:
            strategy, stem, test = re.search(
                r"Strategy file: (\S+) \(class (\S+)\)\. Test file: (\S+)\.", prompt
            ).groups()
            self.agent.write(strategy, "import os\n" + STRATEGY.format(stem=stem))
            self.agent.write(test, "import unittest\n")

        self.agent.handlers["developer"] = always_bad
        with self.assertRaises(orchestrator.StepFailed):
            self.lab.implement("H-001")
        self.assertEqual(registry.get_hypothesis(self.conn, "H-001")["status"], "proposed")

    def test_a_failing_test_suite_is_rejected(self) -> None:
        self.lab._run_test_suite = lambda: (False, "FAILED (failures=1)")
        with self.assertRaises(orchestrator.StepFailed):
            self.lab.implement("H-001")
        self.assertEqual(self.agent.names().count("developer"), 2)

    def test_a_strategy_the_real_engine_cannot_run_is_rejected_with_its_error(self) -> None:
        self.lab._smoke_check = lambda stem: (False, "AttributeError: module 'talib' has no attribute 'FOO'")
        with self.assertRaises(orchestrator.StepFailed):
            self.lab.implement("H-001")
        self.assertEqual(self.agent.names().count("developer"), 2)
        self.assertIn("talib", self.agent.calls[-1][2])
        self.assertEqual(registry.get_hypothesis(self.conn, "H-001")["status"], "proposed")

    def test_the_smoke_check_failure_can_be_fixed_on_the_retry(self) -> None:
        results = iter([(False, "boom"), (True, "")])
        self.lab._smoke_check = lambda stem: next(results)
        self.assertEqual(self.lab.implement("H-001"), "TrendFilter_H001_v1")
        self.assertEqual(self.agent.names().count("developer"), 2)

    def test_editing_an_existing_file_aborts(self) -> None:
        def edits_baseline(prompt: str) -> None:
            self.agent.good_developer(prompt)
            self.agent.write("user_data/strategies/SmaTrendBaseline.py", "tampered\n")

        self.agent.handlers["developer"] = edits_baseline
        with self.assertRaises(orchestrator.GuardAbort):
            self.lab.implement("H-001")
        baseline = self.root / "user_data/strategies/SmaTrendBaseline.py"
        self.assertEqual(baseline.read_text(encoding="utf-8"), "original\n")

    def test_writing_a_different_test_file_than_asked_aborts(self) -> None:
        def wrong_test_name(prompt: str) -> None:
            self.agent.good_developer(prompt)
            self.agent.write("tests/test_something_else.py", "x")

        self.agent.handlers["developer"] = wrong_test_name
        with self.assertRaises(orchestrator.GuardAbort):
            self.lab.implement("H-001")


class RunAndDecideTests(LabTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.lab.propose()
        self.lab.implement("H-001")

    def test_exploration_runs_every_enabled_pair(self) -> None:
        ids = self.lab.run_split("H-001", "exploration")
        self.assertEqual(len(ids), 3)
        self.assertEqual({pair for _, _, pair in self.experiments.ran}, set(PAIRS))

    def test_validation_is_refused_until_exploration_passed_everywhere(self) -> None:
        with self.assertRaises(orchestrator.StepFailed):
            self.lab.run_split("H-001", "validation")
        self.assertEqual(self.experiments.ran, [])

    def test_validation_is_refused_after_a_rejected_exploration(self) -> None:
        self.experiments.decision = "rejected"
        self.lab.run_split("H-001", "exploration")
        self.assertEqual(set(self.lab.decide_split("H-001", "exploration").values()), {"rejected"})
        with self.assertRaises(orchestrator.StepFailed):
            self.lab.run_split("H-001", "validation")
        self.assertEqual(registry.get_hypothesis(self.conn, "H-001")["status"], "rejected at exploration")

    def test_the_final_test_split_cannot_be_run_here(self) -> None:
        with self.assertRaises(orchestrator.StepFailed):
            self.lab.run_split("H-001", "final_test")

    def test_deciding_twice_does_not_decide_again(self) -> None:
        self.lab.run_split("H-001", "exploration")
        self.lab.decide_split("H-001", "exploration")
        before = self.conn.execute("SELECT COUNT(*) AS n FROM decisions").fetchone()["n"]
        self.lab.decide_split("H-001", "exploration")
        after = self.conn.execute("SELECT COUNT(*) AS n FROM decisions").fetchone()["n"]
        self.assertEqual(before, after)

    def test_a_failed_backtest_stops_with_a_step_failure(self) -> None:
        self.experiments.fail = True
        with self.assertRaises(orchestrator.StepFailed):
            self.lab.run_split("H-001", "exploration")

    def test_find_strategy_prefers_the_hypothesis_file(self) -> None:
        self.assertEqual(
            self.lab.find_strategy("H-001"),
            ("TrendFilter_H001_v1", "user_data/strategies/TrendFilter_H001_v1.py"),
        )

    def test_find_strategy_falls_back_to_the_archive(self) -> None:
        archive = self.lab.root / "user_data" / "strategies" / "_archive"
        archive.mkdir(parents=True, exist_ok=True)
        (archive / "Gone_H077_v1.py").write_text("# archived", encoding="utf-8")
        self.assertEqual(self.lab.find_strategy("H-077"),
                         ("Gone_H077_v1", "user_data/strategies/_archive/Gone_H077_v1.py"))

    def test_an_unknown_hypothesis_has_no_strategy(self) -> None:
        with self.assertRaises(orchestrator.StepFailed):
            self.lab.find_strategy("H-099")


class ValidationGateTests(LabTestCase):
    """The validation split can be read only once and only with the user's recorded approval."""

    def setUp(self) -> None:
        super().setUp()
        self.lab.propose()
        self.lab.implement("H-001")
        self.lab.run_split("H-001", "exploration")
        self.lab.decide_split("H-001", "exploration")

    def test_validation_is_refused_without_an_approval(self) -> None:
        with self.assertRaises(orchestrator.ApprovalRequired):
            self.lab.run_split("H-001", "validation")
        self.assertNotIn("validation", {s for _, s, _ in self.experiments.ran})

    def test_an_approval_for_another_stage_or_hypothesis_does_not_count(self) -> None:
        registry.add_approval(self.conn, hypothesis_id="H-001", stage="dryrun", approved_by="u", note="", created_at_utc=now())
        with self.assertRaises(orchestrator.ApprovalRequired):
            self.lab.run_split("H-001", "validation")

    def test_with_the_approval_validation_runs(self) -> None:
        registry.add_approval(self.conn, hypothesis_id="H-001", stage="validation", approved_by="u", note="", created_at_utc=now())
        self.assertEqual(len(self.lab.run_split("H-001", "validation")), 3)

    def test_an_approval_is_recorded_once(self) -> None:
        kwargs = dict(hypothesis_id="H-001", stage="validation", approved_by="u", note="", created_at_utc=now())
        self.assertTrue(registry.add_approval(self.conn, **kwargs))
        self.assertFalse(registry.add_approval(self.conn, **kwargs))
        with self.assertRaises(ValueError):
            registry.add_approval(self.conn, **{**kwargs, "stage": "live"})

    def test_test_hypothesis_stops_before_validation_and_says_so(self) -> None:
        row = self.lab.test_hypothesis("H-001")
        self.assertEqual(row["validation"], "awaiting the user's approval")
        self.assertNotIn("validation", {s for _, s, _ in self.experiments.ran})


class CycleTests(LabTestCase):
    def setUp(self) -> None:
        super().setUp()
        patcher = mock.patch.object(registry, "has_approval", return_value=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_cycle_without_the_users_approval_never_reads_the_validation(self) -> None:
        with mock.patch.object(registry, "has_approval", return_value=False):
            text = self.lab.cycle(1).read_text(encoding="utf-8")
        self.assertIn("awaiting the user's approval", text)
        self.assertIn("completed", text)
        self.assertEqual({s for _, s, _ in self.experiments.ran}, {"exploration"})
        self.assertEqual(self.agent.names().count("validator"), 1)

    def test_a_full_cycle_runs_both_splits_reviews_and_builds_a_portfolio(self) -> None:
        report = self.lab.cycle(1)
        text = report.read_text(encoding="utf-8")
        self.assertIn("completed", text)
        self.assertIn("H-001", text)
        self.assertEqual(
            self.agent.names(),
            ["research", "developer"] + ["validator", "quant", "risk"] * 2,
        )
        self.assertEqual({s for _, s, _ in self.experiments.ran}, {"exploration", "validation"})
        self.assertIn("['H-001']", text)
        self.assertEqual(guard.changed_files(self.root), [])

    def test_a_rejected_exploration_skips_validation_and_gives_an_empty_portfolio(self) -> None:
        self.experiments.decision = "rejected"
        text = self.lab.cycle(1).read_text(encoding="utf-8")
        self.assertEqual({s for _, s, _ in self.experiments.ran}, {"exploration"})
        self.assertIn("| not run |", text)
        self.assertIn("empty", text)
        self.assertEqual(self.agent.names().count("validator"), 1)

    def test_the_cycle_stops_at_the_first_failure_and_says_so(self) -> None:
        self.experiments.fail = True
        text = self.lab.cycle(3).read_text(encoding="utf-8")
        self.assertIn("STOPPED", text)
        self.assertIn("backtest exploded", text)
        self.assertEqual(len(registry.list_hypotheses(self.conn)), 1)
        self.assertEqual(registry.get_hypothesis(self.conn, "H-001")["status"], "failed")
        self.assertIn("No portfolio snapshot", text)

    def test_the_number_of_hypotheses_is_capped_by_the_budget(self) -> None:
        self.lab = self.make_lab(dict(BUDGET, max_hypotheses_per_cycle=1, max_agent_budget_usd_per_cycle=100.0))
        self.lab.cycle(10)
        self.assertEqual(len(registry.list_hypotheses(self.conn)), 1)

    def test_agent_spending_is_capped_per_cycle(self) -> None:
        # One hypothesis costs 8 calls of 1 USD; a second would pass the 12 USD cap.
        self.lab = self.make_lab(dict(BUDGET, max_agent_budget_usd_per_cycle=10.0))
        text = self.lab.cycle(3).read_text(encoding="utf-8")
        self.assertIn("BudgetExhausted", text)
        self.assertLessEqual(len(registry.list_hypotheses(self.conn)), 2)
        spent = registry.agent_cost_since(self.conn, self.lab.cycle_start)
        self.assertLessEqual(spent, 10.0)

    def test_a_guard_violation_inside_a_cycle_stops_it(self) -> None:
        self.agent.handlers["developer"] = lambda prompt: self.agent.write("lab/injected.py", "x")
        text = self.lab.cycle(2).read_text(encoding="utf-8")
        self.assertIn("GuardAbort", text)
        self.assertEqual(self.agent.names(), ["research", "developer"])

    def test_every_hypothesis_stays_in_the_report_including_rejected_ones(self) -> None:
        self.experiments.decision = "rejected"
        self.lab = self.make_lab(dict(BUDGET, max_agent_budget_usd_per_cycle=100.0))
        text = self.lab.cycle(2).read_text(encoding="utf-8")
        for hypothesis in ("H-001", "H-002"):
            self.assertIn(hypothesis, text)



class StrategyTimeframeTests(unittest.TestCase):
    def test_reads_the_declared_timeframe_and_defaults_to_1h(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            four = Path(directory) / "A_H900_v1.py"
            four.write_text('class A:\n    timeframe = "4h"\n', encoding="utf-8")
            none = Path(directory) / "B_H901_v1.py"
            none.write_text("class B:\n    pass\n", encoding="utf-8")
            self.assertEqual(orchestrator.strategy_timeframe(four), "4h")
            self.assertEqual(orchestrator.strategy_timeframe(none), "1h")


LONG_SPLITS = {
    "pairs": {pair: {"exploration": window("2018-01-01T00:00:00Z", "2024-12-31T00:00:00Z")} for pair in PAIRS},
}


class ScoutTests(LabTestCase):
    def test_the_scout_writes_ideas_that_are_queued_and_committed(self) -> None:
        outcomes = self.lab.scout(count=3)
        self.assertEqual([o["idea_id"] for o in outcomes], ["I-001", "I-002"])
        self.assertEqual(self.agent.names(), ["scout"])
        self.assertEqual([r["state"] for r in registry.list_ideas(self.conn)], ["new", "new"])
        self.assertEqual(registry.list_hypotheses(self.conn), [])  # an idea is not a hypothesis
        self.assertIn("idea intake", git(["log", "--oneline", "-1"], self.root))
        self.assertEqual(guard.changed_files(self.root), [])

    def test_the_scout_context_has_rule_text_but_no_results(self) -> None:
        self.lab.propose()
        self.lab.scout(count=2)
        context_file = next((self.root / "research" / "context").glob("scout-*.md"))
        text = context_file.read_text(encoding="utf-8")
        self.assertIn("Rules already tried", text)
        self.assertIn("H-001", text)
        for forbidden in ("net profit", "drawdown", "rejected", "candidate"):
            self.assertNotIn(forbidden, text.lower())

    def test_an_invalid_idea_file_is_reported_and_not_queued(self) -> None:
        def one_bad_one_good(prompt: str) -> None:
            paths = re.search(r"Write the idea files to (.+?) \(only", prompt).group(1).split(", ")
            self.agent.write(paths[0], json.dumps({**SCOUT_IDEAS[0], "timeframe": "4h"}))
            self.agent.write(paths[1], json.dumps(SCOUT_IDEAS[1]))

        self.agent.handlers["scout"] = one_bad_one_good
        outcomes = self.lab.scout(count=2)
        self.assertIsNone(outcomes[0]["idea_id"])
        self.assertTrue(outcomes[0]["rejected"])
        self.assertEqual(outcomes[1]["idea_id"], "I-001")

    def test_a_scout_that_writes_outside_the_intake_folder_aborts(self) -> None:
        def sneaky(prompt: str) -> None:
            self.agent.good_scout(prompt)
            self.agent.write("user_data/strategies/Smuggled_H001_v1.py", "print('x')")

        self.agent.handlers["scout"] = sneaky
        with self.assertRaises(orchestrator.GuardAbort):
            self.lab.scout(count=2)

    def test_a_scout_that_writes_more_files_than_allowed_aborts(self) -> None:
        def too_many(prompt: str) -> None:
            self.agent.good_scout(prompt)
            self.agent.write("research/intake/extra-99.json", "{}")

        self.agent.handlers["scout"] = too_many
        with self.assertRaises(orchestrator.GuardAbort):
            self.lab.scout(count=2)

    def test_count_is_bounded(self) -> None:
        for bad in (0, 11):
            with self.assertRaises(orchestrator.StepFailed):
                self.lab.scout(count=bad)

    def test_scouting_respects_the_agent_spend_cap(self) -> None:
        lab = self.make_lab(budget={**BUDGET, "max_agent_budget_usd_per_cycle": 1.0})
        with self.assertRaises(orchestrator.BudgetExhausted):
            lab.scout(count=2)

    def test_triage_queues_and_drops_without_any_agent_call(self) -> None:
        self.lab.scout(count=2)
        calls_before = len(self.agent.calls)
        self.lab.splits = LONG_SPLITS
        outcomes = self.lab.triage_ideas()
        self.assertEqual(len(self.agent.calls), calls_before)
        self.assertEqual({o["idea_id"]: o["state"] for o in outcomes}, {"I-001": "queued", "I-002": "queued"})


if __name__ == "__main__":
    unittest.main()
