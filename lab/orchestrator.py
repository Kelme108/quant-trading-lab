"""The research cycle: propose -> implement -> run -> decide -> review -> portfolio.

Control flow and every approval live here and in lab/gates.py and
lab/portfolio.py, as plain deterministic Python. The agents (lab/agents.py)
only write text: a proposal, a strategy file, a review. Nothing an agent says
can approve a strategy.

Safety rules enforced here:
- After every agent step, lab/guard.py checks that the agent created exactly the
  files expected of it and touched no protected file. A violation stops the
  whole cycle, is never retried, and protected files are restored from HEAD.
- Generated strategy code is screened (lab/strategy_check.py) and must pass the
  full unit-test suite before it can be run.
- The validation split runs only after exploration passed on every enabled pair;
  the final test split is refused by lab/runner.py while it is locked.
- A cycle stops at the first failure or when a budget (hypotheses, variants per
  family, agent spend) would be exceeded.
"""

from __future__ import annotations

import argparse
import re
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from lab import agents, context, experiment, guard, portfolio, proposals, registry, runner, strategy_check

ROOT = Path(__file__).parents[1]
BUDGET_PATH = Path(__file__).parent / "config" / "budget.json"


class StepFailed(RuntimeError):
    """A step failed in a way that ends the cycle."""


class BudgetExhausted(StepFailed):
    """A hypothesis, variant or spending limit would be exceeded."""


class GuardAbort(StepFailed):
    """An agent touched something it should not have. Never retried."""


def load_budget(path: Path = BUDGET_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def strategy_timeframe(strategy_file: Path) -> str:
    """The `timeframe = "..."` constant a strategy file declares (1h when absent)."""
    found = re.search(r'^\s*timeframe\s*=\s*"([0-9]+[mhdw])"', strategy_file.read_text(encoding="utf-8"), re.M)
    return found.group(1) if found else "1h"


def _hypothesis_number(hypothesis_id: str) -> int:
    return int(hypothesis_id.rsplit("-", 1)[1])


class Lab:
    def __init__(
        self,
        conn,
        *,
        root: Path = ROOT,
        budget: dict | None = None,
        agent_runner: Callable = agents.run_agent,
        experiments=experiment,
        splits: dict | None = None,
    ) -> None:
        self.conn = conn
        self.root = root
        self.budget = budget or load_budget()
        self.agent_runner = agent_runner
        self.experiments = experiments
        self.splits = splits
        self.cycle_start = _now()
        self.proposed_this_cycle = 0

    # -- plumbing ------------------------------------------------------------

    def _splits(self) -> dict:
        return self.splits if self.splits is not None else runner.load_splits()

    def _rel(self, path: Path) -> str:
        return str(path.relative_to(self.root)).replace("\\", "/")

    def _commit(self, paths: list[str], message: str) -> None:
        """Commit exactly `paths` (those that exist) if they changed."""
        existing = [p for p in paths if (self.root / p).exists()]
        if not existing:
            return
        subprocess.run(["git", "add", "--", *existing], cwd=self.root, check=True, capture_output=True)
        staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=self.root)
        if staged.returncode != 0:
            subprocess.run(
                ["git", "commit", "-q", "-m", message], cwd=self.root, check=True, capture_output=True
            )

    def _sync_ledger(self) -> None:
        registry.sync_ledger_markdown(self.conn, self.root / "research" / "hypothesis-ledger.md")

    def _ensure_agent_budget(self) -> None:
        spent = registry.agent_cost_since(self.conn, self.cycle_start)
        per_call = self.budget["agent_budget_usd_per_call"]
        cap = self.budget["max_agent_budget_usd_per_cycle"]
        if spent + per_call > cap:
            raise BudgetExhausted(
                f"agent spend {spent:.2f} USD plus one more call (up to {per_call:.2f}) would "
                f"exceed the cycle cap of {cap:.2f} USD"
            )

    def agent_step(
        self,
        name: str,
        prompt: str,
        *,
        purpose: str,
        hypothesis_id: str | None,
        expected_paths: set[str],
    ) -> agents.AgentResult:
        """Run an agent, then verify it created exactly `expected_paths` (and
        possibly fewer) and nothing else. Raises GuardAbort on any deviation."""
        self._ensure_agent_budget()
        baseline = guard.snapshot(self.root)
        try:
            result = self.agent_runner(
                self.conn,
                name,
                prompt,
                purpose=purpose,
                budget_usd=self.budget["agent_budget_usd_per_call"],
                timeout_s=self.budget["agent_timeout_seconds"],
                hypothesis_id=hypothesis_id,
            )
        except agents.AgentError as error:
            raise StepFailed(str(error)) from error

        try:
            guard.enforce(name, self.root, baseline)
            stray = [
                path
                for path in guard.changed_since(baseline, self.root)
                if path.replace("\\", "/") not in expected_paths
            ]
            if stray:
                raise guard.GuardViolation(
                    f"agent '{name}' changed files outside what this step expects: {stray}"
                )
        except guard.GuardViolation as violation:
            for path in guard.check_protected_files_unchanged(self.root):
                subprocess.run(["git", "checkout", "HEAD", "--", path], cwd=self.root, check=False)
            registry.record_agent_run(
                self.conn,
                agent=name,
                hypothesis_id=hypothesis_id,
                purpose=purpose,
                status="guard_violation",
                started_at_utc=_now(),
                result_excerpt=str(violation),
            )
            raise GuardAbort(str(violation)) from violation
        return result

    # -- propose -------------------------------------------------------------

    def _guidance(self) -> str:
        """Optional owner direction for the research agent; empty when the file is absent."""
        path = self.root / "research" / "guidance.md"
        return path.read_text(encoding="utf-8") if path.is_file() else ""

    def propose(self) -> str:
        """Ask the research agent for one hypothesis; register it before any test."""
        if self.proposed_this_cycle >= self.budget["max_hypotheses_per_cycle"]:
            raise BudgetExhausted("max_hypotheses_per_cycle reached")

        hypothesis_id = registry.next_hypothesis_id(self.conn)
        context_path = self.root / "research" / "context" / f"{hypothesis_id}.md"
        context_path.parent.mkdir(parents=True, exist_ok=True)
        context_path.write_text(
            context.research_context(
                self.conn,
                hypothesis_id=hypothesis_id,
                budget=self.budget,
                hypotheses_proposed_this_cycle=self.proposed_this_cycle,
                guidance=self._guidance(),
            ),
            encoding="utf-8",
        )

        proposal_file = proposals.proposal_path(hypothesis_id, self.root / "research" / "proposals")
        proposal_rel = self._rel(proposal_file)
        prompt = (
            f"Propose hypothesis {hypothesis_id}. Read {self._rel(context_path)} first, then follow "
            f"your instructions. Write the proposal to {proposal_rel}."
        )
        feedback = ""
        for attempt in (1, 2):
            self.agent_step(
                "research",
                prompt + feedback,
                purpose=f"propose attempt {attempt}",
                hypothesis_id=hypothesis_id,
                expected_paths={proposal_rel},
            )
            data, errors = proposals.load_proposal(proposal_file)
            if data is not None:
                errors = proposals.validate_proposal(
                    data,
                    expected_id=hypothesis_id,
                    enabled_timeframes=runner.enabled_timeframes(),
                    variants_in_family=lambda family: registry.count_variants_in_family(self.conn, family),
                    max_variants_per_family=self.budget["max_variants_per_family"],
                )
            if not errors:
                break
            feedback = (
                f"\n\nYour previous proposal was rejected by validation. Rewrite {proposal_rel} "
                "fixing exactly these problems:\n- " + "\n- ".join(errors)
            )
        else:
            raise StepFailed(f"{hypothesis_id}: proposal invalid after a retry: {errors}")

        registry.add_hypothesis(
            self.conn,
            hypothesis_id=hypothesis_id,
            family=data["family"],
            ex_ante_rule=data["ex_ante_rule"],
            proposed_at_utc=_now(),
            data_visible_at_proposal=data["data_visible_at_proposal"],
            status="proposed",
            notes=data["title"],
        )
        self._sync_ledger()
        self.proposed_this_cycle += 1
        self._commit(
            [proposal_rel, self._rel(context_path), "research/hypothesis-ledger.md"],
            f"exp({hypothesis_id}): proposal registered - {data['title']}",
        )
        return hypothesis_id

    # -- implement -----------------------------------------------------------

    def strategy_names(self, hypothesis_id: str) -> tuple[str, str, str]:
        """(class/file stem, strategy file, test file) for a new hypothesis."""
        data, errors = proposals.load_proposal(
            proposals.proposal_path(hypothesis_id, self.root / "research" / "proposals")
        )
        if data is None:
            raise StepFailed(f"{hypothesis_id}: no usable proposal: {errors}")
        number = _hypothesis_number(hypothesis_id)
        stem = f"{data['family']}_H{number:03d}_v1"
        return (
            stem,
            f"user_data/strategies/{stem}.py",
            f"tests/test_{data['family'].lower()}_h{number:03d}_v1.py",
        )

    def _run_test_suite(self) -> tuple[bool, str]:
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=900,
        )
        return completed.returncode == 0, (completed.stdout + completed.stderr)[-1500:]

    def _smoke_check(self, stem: str) -> tuple[bool, str]:
        """A 120-day backtest over the END of the first pair's exploration window,
        to confirm the real Freqtrade engine can load and run the strategy.

        The window must come after years of earlier candles: Freqtrade needs
        `startup_candle_count` candles before the first candle it trades, and a
        window at the start of the history has none. Such a check once forced a
        strategy to shorten its 4800-candle average to pass it, silently
        changing the rule being tested.
        """
        pair = runner.enabled_pairs()[0]
        end = int(self._splits()["pairs"][pair]["exploration"]["timerange"].split("-")[1])
        return runner.smoke_backtest(
            strategy=stem, pair=pair, timerange=f"{end - 120 * 86400}-{end}"
        )

    def implement(self, hypothesis_id: str) -> str:
        """Have the developer agent write the strategy and its test; accept it
        only if it passes the static screen and the whole test suite."""
        stem, strategy_file, test_file = self.strategy_names(hypothesis_id)
        proposal_rel = f"research/proposals/{hypothesis_id}.json"
        prompt = (
            f"Implement hypothesis {hypothesis_id} from {proposal_rel}. Strategy file: "
            f"{strategy_file} (class {stem}). Test file: {test_file}."
        )
        feedback = ""
        problems: list[str] = []
        for attempt in (1, 2):
            self.agent_step(
                "developer",
                prompt + feedback,
                purpose=f"implement attempt {attempt}",
                hypothesis_id=hypothesis_id,
                expected_paths={strategy_file, test_file},
            )
            problems = []
            strategy_path = self.root / strategy_file
            if not strategy_path.is_file() or not (self.root / test_file).is_file():
                problems.append("both the strategy file and the test file must be written")
            else:
                problems += strategy_check.check_strategy_source(
                    strategy_path,
                    expected_hypothesis_id=hypothesis_id,
                    allowed_timeframes=tuple(runner.enabled_timeframes()),
                )
            if not problems:
                passed, output = self._run_test_suite()
                if not passed:
                    problems.append("the unit-test suite fails:\n" + output)
            if not problems:
                loads, output = self._smoke_check(stem)
                if not loads:
                    problems.append(
                        "the real Freqtrade engine fails to load or run the strategy "
                        "(the unit tests stub TA-Lib and Freqtrade, so use only calls that "
                        "exist in the real libraries):\n" + output
                    )
            if not problems:
                break
            feedback = (
                "\n\nYour previous attempt was rejected. Fix exactly these problems in the same "
                "two files:\n- " + "\n- ".join(problems)
            )
        else:
            raise StepFailed(f"{hypothesis_id}: implementation rejected after a retry: {problems}")

        registry.set_hypothesis_status(self.conn, hypothesis_id, "implemented")
        self._sync_ledger()
        self._commit(
            [strategy_file, test_file, "research/hypothesis-ledger.md"],
            f"exp({hypothesis_id}): strategy {stem} implemented",
        )
        return stem

    # -- run / decide --------------------------------------------------------

    def find_strategy(self, hypothesis_id: str) -> tuple[str, str]:
        """(strategy name, strategy file) of a hypothesis: the newest
        <Family>_H<NNN>_v<N>.py, or a baseline file named after its family."""
        number = _hypothesis_number(hypothesis_id)
        found = sorted((self.root / "user_data" / "strategies").glob(f"*_H{number:03d}_v*.py"))
        if found:
            return found[-1].stem, self._rel(found[-1])
        hypothesis = registry.get_hypothesis(self.conn, hypothesis_id)
        if hypothesis is not None:
            baseline = self.root / "user_data" / "strategies" / f"{hypothesis['family']}.py"
            if baseline.is_file():
                return baseline.stem, self._rel(baseline)
        raise StepFailed(f"{hypothesis_id}: no strategy file found")

    def run_split(self, hypothesis_id: str, split: str) -> list[str]:
        """Run the hypothesis on `split` for every enabled pair."""
        if split not in ("exploration", "validation"):
            raise StepFailed(f"only exploration and validation can be run here, not '{split}'")
        pairs = runner.enabled_pairs()
        if split == "validation" and not self.exploration_passed(hypothesis_id):
            raise StepFailed(
                f"{hypothesis_id}: validation needs exploration to pass on every enabled pair first"
            )
        name, strategy_file = self.find_strategy(hypothesis_id)
        timeframe = strategy_timeframe(self.root / strategy_file)
        stamp = _stamp()
        version = self.experiments.freqtrade_version()
        ids = []
        try:
            for pair in pairs:
                ids.append(
                    self.experiments.run_experiment(
                        self.conn,
                        hypothesis_id=hypothesis_id,
                        strategy_name=name,
                        strategy_file=strategy_file,
                        pair=pair,
                        split_name=split,
                        timestamp=stamp,
                        splits=self._splits(),
                        version=version,
                        timeframe=timeframe,
                    )
                )
        except self.experiments.ExperimentFailed as error:
            raise StepFailed(str(error)) from error
        return ids

    def exploration_passed(self, hypothesis_id: str) -> bool:
        latest = {
            row["pair"]: row["decision"]
            for row in registry.list_latest_decisions(self.conn)
            if row["hypothesis_id"] == hypothesis_id and row["split"] == "exploration"
        }
        return all(
            latest.get(pair) == "candidate_for_portfolio" for pair in runner.enabled_pairs()
        )

    def decide_split(self, hypothesis_id: str, split: str) -> dict[str, str]:
        """Apply the gates to the latest experiment of each pair that has no
        verdict yet. Returns {pair: decision} for every pair of the split."""
        decisions: dict[str, str] = {}
        for pair, row in registry.latest_experiments(self.conn, hypothesis_id, split).items():
            existing = registry.get_latest_decision(self.conn, row["id"])
            if existing is not None:
                decisions[pair] = existing["decision"]
                continue
            try:
                decision, _ = self.experiments.decide_experiment(self.conn, row["id"], hypothesis_id)
            except self.experiments.ExperimentFailed as error:
                raise StepFailed(str(error)) from error
            decisions[pair] = decision

        if decisions:
            values = set(decisions.values())
            if values == {"candidate_for_portfolio"}:
                status = f"{split}: candidate"
            elif "rejected" in values:
                status = f"rejected at {split}"
            else:
                status = f"inconclusive at {split}"
            registry.set_hypothesis_status(self.conn, hypothesis_id, status)
            self._sync_ledger()
        return decisions

    # -- review --------------------------------------------------------------

    def review(self, hypothesis_id: str, split: str) -> Path:
        """Write the facts files, then run the three reviewers one after another
        (validator first: it must not be anchored on the others)."""
        directory = context.write_review_facts(self.conn, hypothesis_id, split, self.root)
        directory_rel = self._rel(directory)
        _, strategy_file = self.find_strategy(hypothesis_id)
        written = [f"{directory_rel}/{name}" for name in sorted(p.name for p in directory.iterdir())]
        for name in ("validator", "quant", "risk"):
            report = f"{directory_rel}/{name}.md"
            self.agent_step(
                name,
                f"Review directory: {directory_rel}/. Strategy file: {strategy_file}. "
                f"Proposal: research/proposals/{hypothesis_id}.json. Write {report}.",
                purpose=f"review {split}",
                hypothesis_id=hypothesis_id,
                expected_paths={report},
            )
            written.append(report)
        self._commit(written, f"exp({hypothesis_id}): {split} review and facts")
        return directory

    # -- portfolio -----------------------------------------------------------

    def build_portfolio(self) -> dict:
        snapshot = portfolio.build_portfolio(self.conn, splits=self._splits(), root=self.root)
        path = portfolio.write_snapshot(snapshot, self.root / "research" / "portfolio")
        self._commit([self._rel(path)], f"portfolio: snapshot {path.stem}")
        snapshot["_path"] = self._rel(path)
        return snapshot

    # -- the cycle -----------------------------------------------------------

    def test_hypothesis(self, hypothesis_id: str, row: dict | None = None) -> dict:
        """implement -> explore -> (review) -> validate -> (review).

        `row` is the cycle-report row, filled in as each step finishes so a
        failure part-way still leaves what was already decided. Raises
        StepFailed on a failure."""
        if row is None:
            row = {"id": hypothesis_id, "exploration": {}, "validation": None}
        self.implement(hypothesis_id)
        self.run_split(hypothesis_id, "exploration")
        row["exploration"] = self.decide_split(hypothesis_id, "exploration")
        self.review(hypothesis_id, "exploration")
        if self.exploration_passed(hypothesis_id):
            self.run_split(hypothesis_id, "validation")
            row["validation"] = self.decide_split(hypothesis_id, "validation")
            self.review(hypothesis_id, "validation")
        return row

    def cycle(self, max_experiments: int) -> Path:
        """Up to `max_experiments` hypotheses (never more than the budget allows),
        stopping at the first failure. Always writes the cycle report."""
        self.cycle_start = _now()
        self.proposed_this_cycle = 0
        wanted = min(max_experiments, self.budget["max_hypotheses_per_cycle"])
        rows: list[dict] = []
        failure = ""
        try:
            for _ in range(wanted):
                hypothesis_id = self.propose()
                row = {"id": hypothesis_id, "exploration": {}, "validation": None}
                rows.append(row)
                self.test_hypothesis(hypothesis_id, row)
        except StepFailed as error:
            failure = f"{type(error).__name__}: {error}"
            if rows:
                registry.set_hypothesis_status(self.conn, rows[-1]["id"], "failed")
                self._sync_ledger()

        snapshot = None
        if not failure:
            try:
                snapshot = self.build_portfolio()
            except (portfolio.PortfolioFrozenError, OSError) as error:
                failure = f"portfolio: {error}"
        return self.write_cycle_report(rows, failure, snapshot)

    def write_cycle_report(self, rows: list[dict], failure: str, snapshot: dict | None) -> Path:
        spent = registry.agent_cost_since(self.conn, self.cycle_start)
        lines = [
            f"# Cycle {self.cycle_start}",
            "",
            f"- Agent spend this cycle: {spent:.2f} USD (cap {self.budget['max_agent_budget_usd_per_cycle']:.2f})",
            f"- Outcome: {'STOPPED - ' + failure if failure else 'completed'}",
            "",
            "| Hypothesis | Family | Exploration (per pair) | Validation (per pair) |",
            "|---|---|---|---|",
        ]
        for row in rows:
            hypothesis = registry.get_hypothesis(self.conn, row["id"])
            family = hypothesis["family"] if hypothesis else "?"
            explore = "; ".join(f"{p}: {d}" for p, d in row.get("exploration", {}).items()) or "not run"
            validate = (
                "; ".join(f"{p}: {d}" for p, d in row["validation"].items())
                if row.get("validation")
                else "not run"
            )
            lines.append(f"| {row['id']} | {family} | {explore} | {validate} |")
        if not rows:
            lines.append("| none | | | |")
        lines.append("")
        if snapshot is not None:
            included = [e["hypothesis_id"] for e in snapshot["included"]]
            lines.append(f"Portfolio snapshot `{snapshot['_path']}`: "
                         f"{included if included else 'empty (no strategy qualified)'}")
        else:
            lines.append("No portfolio snapshot was produced for this cycle.")
        lines.append("")

        path = self.root / "research" / "experiments" / f"cycle-{_stamp()}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")
        dump = registry.dump_sql(self.conn, self.root / "research" / "registry-dump.sql")
        self._commit(
            [self._rel(path), "research/hypothesis-ledger.md", self._rel(dump)],
            f"cycle report {path.stem}",
        )
        return path


# --- data expansion ---------------------------------------------------------------

def expand_data(timerange: str = "20170101-") -> int:
    """Download/extend candles for every enabled pair and timeframe, validate
    them with the documented gap tolerance, and report. It never touches
    splits.json: boundaries are fixed timestamps, so newly appended candles
    land in the (locked) final-test window and change no earlier result."""
    pairs = runner.enabled_pairs()
    timeframes = runner.enabled_timeframes()
    completed = runner.run_compose(
        [
            "download-data",
            "--config", f"{runner.CONTAINER_USER_DATA}/config.dryrun.json",
            "--pairs", *pairs,
            "--timeframes", *timeframes,
            "--timerange", timerange,
            "--data-format-ohlcv", "feather",
        ]
    )
    if completed.returncode != 0:
        print(completed.stdout[-1500:], completed.stderr[-1500:])
        return 1

    sys.path.insert(0, str(ROOT / "research"))
    import validate_ohlcv

    tolerance = runner.max_gap_hours()
    status = 0
    for pair in pairs:
        for timeframe in timeframes:
            path = experiment.feather_path(pair, timeframe)
            report = validate_ohlcv.validate(path, timeframe=timeframe, max_gap_hours=tolerance)
            print(
                f"{pair} {timeframe}: {report['first_candle_utc']} -> {report['last_candle_utc']}, "
                f"{report['rows']} candles, gaps={report['gaps']} (largest "
                f"{report['largest_gap_missing_hours']}h), valid={report['valid']}"
            )
            if not report["valid"]:
                status = 1
    return status


# --- CLI --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m lab.orchestrator", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("expand-data", help="download/extend candles and validate them")
    sub.add_parser("propose", help="ask the research agent for one hypothesis")
    for name, help_text in (
        ("implement", "have the developer agent write a strategy"),
        ("run", "run a hypothesis on a split for every enabled pair"),
        ("decide", "apply the gates to a split's experiments"),
        ("review", "run the validator, quant and risk agents on a split"),
    ):
        command = sub.add_parser(name, help=help_text)
        command.add_argument("hypothesis")
        if name != "implement":
            command.add_argument("--split", choices=("exploration", "validation"), default="exploration")
    sub.add_parser("portfolio", help="select the portfolio and write a snapshot")
    cycle = sub.add_parser("cycle", help="run propose -> ... -> portfolio")
    cycle.add_argument("--max-experiments", type=int, default=1)
    sub.add_parser("status", help="show hypotheses, latest decisions and agent spend")

    args = parser.parse_args(argv)
    if args.command == "expand-data":
        return expand_data()

    lab = Lab(registry.connect())
    try:
        if args.command == "propose":
            print(lab.propose())
        elif args.command == "implement":
            print(lab.implement(args.hypothesis))
        elif args.command == "run":
            print("\n".join(lab.run_split(args.hypothesis, args.split)))
        elif args.command == "decide":
            print(json.dumps(lab.decide_split(args.hypothesis, args.split), indent=2))
        elif args.command == "review":
            print(lab.review(args.hypothesis, args.split))
        elif args.command == "portfolio":
            snapshot = lab.build_portfolio()
            print(f"{snapshot['_path']}: "
                  f"{[e['hypothesis_id'] for e in snapshot['included']] or 'empty portfolio'}")
        elif args.command == "cycle":
            print(lab.cycle(args.max_experiments))
        elif args.command == "status":
            for hypothesis in registry.list_hypotheses(lab.conn):
                print(f"{hypothesis['id']} {hypothesis['family']:30s} {hypothesis['status']}")
            print(f"agent spend (all time): {registry.agent_cost_since(lab.conn, '0'):.2f} USD")
    except StepFailed as error:
        print(f"STOPPED: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
