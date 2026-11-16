import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from lab import agents, registry


def completed(stdout: str, returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(["claude"], returncode, stdout=stdout, stderr=stderr)


GOOD_OUTPUT = json.dumps(
    {"result": "done", "is_error": False, "total_cost_usd": 0.42, "num_turns": 7, "session_id": "abc"}
)


class BuildArgvTests(unittest.TestCase):
    def argv(self, name: str, budget: float = 2.0) -> list[str]:
        return agents.build_argv(name, budget, claude_path="claude")

    def after(self, argv: list[str], flag: str) -> list[str]:
        """The values following a flag, up to the next flag."""
        values = []
        for item in argv[argv.index(flag) + 1:]:
            if item.startswith("--"):
                break
            values.append(item)
        return values

    def test_scout_and_research_run_on_the_stronger_model_the_rest_on_the_default(self) -> None:
        for name in agents.AGENT_SPECS:
            expected = "opus" if name in ("scout", "research", "proxy-research") else agents.DEFAULT_MODEL
            self.assertEqual(self.after(self.argv(name), "--model"), [expected], name)
            frontmatter = (agents.ROOT / ".claude" / "agents" / f"{name}.md").read_text(encoding="utf-8")
            self.assertIn(f"model: {expected}\n", frontmatter, name)

    def test_every_call_is_headless_json_budgeted_and_unsaved(self) -> None:
        for name in agents.AGENT_SPECS:
            argv = self.argv(name)
            self.assertIn("-p", argv)
            self.assertEqual(self.after(argv, "--agent"), [name])
            self.assertEqual(self.after(argv, "--output-format"), ["json"])
            self.assertEqual(self.after(argv, "--max-budget-usd"), ["2"])
            self.assertIn("--no-session-persistence", argv)

    def test_the_prompt_is_never_on_the_command_line(self) -> None:
        self.assertNotIn("prompt", " ".join(self.argv("research")).lower().replace("--", ""))

    def test_the_developer_may_only_run_the_unit_tests_in_bash(self) -> None:
        allow = self.after(self.argv("developer"), "--allowedTools")
        self.assertIn("Bash(python -m unittest *)", allow)
        self.assertNotIn("Bash", allow)

    def test_only_the_developer_gets_bash_or_edit(self) -> None:
        for name, spec in agents.AGENT_SPECS.items():
            tools = set(spec["tools"])
            if name in ("developer", "proxy-developer"):
                self.assertTrue({"Bash", "Edit"} <= tools)
            else:
                self.assertFalse({"Bash", "Edit"} & tools, name)

    def test_only_research_and_scout_can_use_the_web(self) -> None:
        for name, spec in agents.AGENT_SPECS.items():
            has_web = bool({"WebSearch", "WebFetch"} & set(spec["tools"]))
            self.assertEqual(has_web, name in ("research", "scout", "proxy-research"), name)

    def test_the_proxy_developer_may_only_run_pytest_and_the_proxy_researcher_sees_no_result(self) -> None:
        allow = self.after(self.argv("proxy-developer"), "--allowedTools")
        self.assertIn("Bash(python -m pytest *)", allow)
        self.assertNotIn("Bash", allow)
        deny = agents.AGENT_SPECS["proxy-research"]["deny"]
        for path in ("./research/proxies/results/**", "./research/proxies/ledger.jsonl",
                     "./research/proxies/SCOREBOARD.md", "./b3/config/splits_proxies.json",
                     "./research/proxies/trades/**", "./research/b3/results/**", "./research/b3/trades/**",
                     "./research/b3/ledger.jsonl", "./b3/config/splits_b3.json"):
            self.assertIn(f"Read({path})", deny)

    def test_the_scout_is_denied_every_kind_of_result(self) -> None:
        deny = self.after(self.argv("scout"), "--disallowedTools")
        for blocked in ("Read(./research/experiments/**)", "Read(./research/audit/**)", "Read(./research/lab.sqlite)",
                        "Read(./research/grids/**)", "Read(./research/dossiers/**)", "Read(./research/baselines/**)"):
            self.assertIn(blocked, deny)

    def test_the_research_agent_is_denied_experiment_results(self) -> None:
        deny = self.after(self.argv("research"), "--disallowedTools")
        self.assertIn("Read(./research/experiments/**)", deny)
        self.assertIn("Read(./research/lab.sqlite)", deny)

    def test_agents_without_deny_rules_get_no_disallowed_tools_flag(self) -> None:
        self.assertNotIn("--disallowedTools", self.argv("quant"))

    def test_unknown_agent_is_an_error(self) -> None:
        with self.assertRaises(ValueError):
            self.argv("mystery")

    def test_a_missing_cli_is_an_error(self) -> None:
        from unittest import mock

        with mock.patch.object(agents.shutil, "which", return_value=None):
            with self.assertRaises(agents.AgentError):
                agents.build_argv("research", 1.0)

    def test_every_agent_has_a_definition_file_matching_its_tools(self) -> None:
        root = Path(__file__).parents[1] / ".claude" / "agents"
        for name, spec in agents.AGENT_SPECS.items():
            text = (root / f"{name}.md").read_text(encoding="utf-8")
            frontmatter = text.split("---")[1]
            self.assertIn(f"name: {name}", frontmatter)
            declared = next(
                line.split(":", 1)[1] for line in frontmatter.splitlines() if line.startswith("tools:")
            )
            self.assertEqual({t.strip() for t in declared.split(",")}, set(spec["tools"]), name)


class RunAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.conn = registry.connect(Path(self.tmp.name) / "lab.sqlite")

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def call(self, run, **kwargs):
        return agents.run_agent(
            self.conn, "research", "the prompt", purpose="test", budget_usd=1.0, timeout_s=5,
            claude_path="claude", run=run, **kwargs,
        )

    def last_run(self):
        return self.conn.execute("SELECT * FROM agent_runs ORDER BY id DESC LIMIT 1").fetchone()

    def test_success_returns_and_records_cost(self) -> None:
        seen = {}

        def run(argv, **kwargs):
            seen.update(kwargs)
            return completed(GOOD_OUTPUT)

        result = self.call(run, hypothesis_id="H-001")
        self.assertEqual((result.text, result.cost_usd, result.num_turns), ("done", 0.42, 7))
        self.assertEqual(seen["input"], "the prompt")
        self.assertEqual(seen["timeout"], 5)
        row = self.last_run()
        self.assertEqual((row["status"], row["cost_usd"], row["hypothesis_id"]), ("completed", 0.42, "H-001"))

    def test_an_error_result_is_a_failure_that_keeps_its_cost(self) -> None:
        output = json.dumps({"result": "budget exceeded", "is_error": True, "total_cost_usd": 1.0})
        with self.assertRaises(agents.AgentError):
            self.call(lambda argv, **kw: completed(output))
        self.assertEqual((self.last_run()["status"], self.last_run()["cost_usd"]), ("failed", 1.0))

    def test_a_nonzero_exit_is_a_failure(self) -> None:
        with self.assertRaises(agents.AgentError):
            self.call(lambda argv, **kw: completed(GOOD_OUTPUT, returncode=1))
        self.assertEqual(self.last_run()["status"], "failed")

    def test_output_that_is_not_json_is_a_failure(self) -> None:
        with self.assertRaises(agents.AgentError):
            self.call(lambda argv, **kw: completed("Traceback...", returncode=1, stderr="boom"))
        self.assertIn("boom", self.last_run()["result_excerpt"])

    def test_a_timeout_is_a_failure(self) -> None:
        def run(argv, **kwargs):
            raise subprocess.TimeoutExpired(argv, 5)

        with self.assertRaises(agents.AgentError):
            self.call(run)
        self.assertIn("timed out", self.last_run()["result_excerpt"])

    def test_cost_since_adds_up_the_recorded_calls(self) -> None:
        self.call(lambda argv, **kw: completed(GOOD_OUTPUT))
        self.call(lambda argv, **kw: completed(GOOD_OUTPUT))
        self.assertAlmostEqual(registry.agent_cost_since(self.conn, "0"), 0.84)
        self.assertEqual(registry.agent_cost_since(self.conn, "9999"), 0.0)


if __name__ == "__main__":
    unittest.main()
