"""The weekly pipeline: scout -> triage -> formalise -> implement -> causality checks -> calibrate -> explore ->
trade review -> agent review -> archive the failures. It STOPS at the exploration: reading the validation split and
freezing a dry-run need the user's approval (research/tools/approve.py), and nothing here asks for either.

usage: python -m lab.pipeline weekly [--scout-count 5] [--max-new 3] [--no-scout] [--expand-data]

Rules it keeps: at most `max_hypotheses_per_cycle` hypotheses per run; a guard violation or an exhausted spend cap
stops the whole run and says so; any other failure marks that one hypothesis as failed and the run goes on. The N of
the Deflated Sharpe Ratio (every configuration ever tried) is printed in the report. Every number comes from code,
never from an agent.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from lab import archive, calibrate, checks, orchestrator, registry, tradereport, triage
from lab.orchestrator import BudgetExhausted, GuardAbort, StepFailed, _now, _stamp

ROOT = Path(__file__).parents[1]
TRIAL_LEDGER = Path(__file__).parent / "config" / "trial_ledger.json"
LABEL = "Provisório: limites PROPOSED; sem evidência prospectiva; dados históricos semi-contaminados."
CANDIDATE_STATUS = "exploration: candidate"


def trial_count(conn, path: Path = TRIAL_LEDGER) -> dict:
    """N for the Deflated Sharpe Ratio: registered hypotheses plus the configurations listed in the trial ledger."""
    extra = sum(int(item["n"]) for item in json.loads(path.read_text(encoding="utf-8"))["extra_configurations"])
    registered = len(registry.list_hypotheses(conn))
    return {"hypotheses": registered, "extra": extra, "total": registered + extra}


class Pipeline:
    def __init__(self, lab: orchestrator.Lab, *, run_checks=checks.run_checks, explore=calibrate.calibrate_and_explore,
                 write_review=tradereport.write_report, archive_one=archive.archive_hypothesis, expand_data=None) -> None:
        self.lab = lab
        self.conn = lab.conn
        self.root = lab.root
        self.run_checks = run_checks
        self.explore = explore
        self.write_review = write_review
        self.archive_one = archive_one
        self.expand_data = expand_data

    # -- git ------------------------------------------------------------------

    def _commit(self, paths: list[str], message: str) -> None:
        """Stage exactly these paths (creations, changes and removals) and commit if anything is staged."""
        for path in paths:
            subprocess.run(["git", "add", "-A", "--", path], cwd=self.root, capture_output=True)
        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=self.root).returncode != 0:
            subprocess.run(["git", "commit", "-q", "-m", message], cwd=self.root, check=True, capture_output=True)

    def _hypothesis_paths(self, hid: str, strategy_name: str | None) -> list[str]:
        low = hid.lower()
        found = [
            f"research/proposals/{hid}.json", f"research/context/{hid}.md",
            f"research/audit/trade-review/{hid}-exploration.json", f"research/audit/trade-review/{hid}-exploration.md",
        ]
        if strategy_name:
            found.append(f"research/baselines/checks-{strategy_name}.json")
        for pattern in (f"research/experiments/*-{low}-*", f"research/experiments/{hid}-*", f"research/manifests/*-{low}-*"):
            found += [self.lab._rel(p) for p in sorted(self.root.glob(pattern))]
        return found

    # -- one idea -----------------------------------------------------------------

    def process_idea(self, idea: dict) -> dict:
        """Formalise, implement, check, calibrate, explore and review one queued idea. Never reads validation."""
        lab = self.lab
        row = {"idea": idea["id"], "hypothesis": None, "outcome": "", "detail": ""}
        try:
            hid = lab.propose(idea_id=idea["id"])
        except (GuardAbort, BudgetExhausted):
            raise
        except StepFailed as error:
            registry.set_idea_state(self.conn, idea["id"], "dropped", f"could not be formalised: {error}"[:300])
            return {**row, "outcome": "not formalised", "detail": str(error)[:200]}
        row["hypothesis"] = hid
        name = None
        try:
            lab.implement(hid)
            name, strategy_file = lab.find_strategy(hid)
            timeframe = orchestrator.strategy_timeframe(self.root / strategy_file)
        except (GuardAbort, BudgetExhausted):
            raise
        except StepFailed as error:
            registry.set_hypothesis_status(self.conn, hid, "failed: implementation")
            return {**row, "outcome": "implementation failed", "detail": str(error)[:200]}

        outcome, detail = self._check_and_explore(hid, name, strategy_file, timeframe)
        status = registry.get_hypothesis(self.conn, hid)["status"]
        archived = {"archived": False, "paths": [], "reason": ""}
        if status == CANDIDATE_STATUS:
            outcome = "candidate: awaiting the user's approval to read the validation"
            try:
                lab.review(hid, "exploration")
            except (GuardAbort, BudgetExhausted):
                raise
            except StepFailed as error:
                detail += f"; agent review failed: {str(error)[:120]}"
        else:
            archived = self.archive_one(self.conn, hid, root=self.root)
            detail += "; archived" if archived["archived"] else f"; not archived ({archived['reason']})"
        lab._sync_ledger()
        registry.dump_sql(self.conn, self.root / "research" / "registry-dump.sql")
        self._commit(
            self._hypothesis_paths(hid, name) + archived["paths"] + ["research/hypothesis-ledger.md", "research/registry-dump.sql"],
            f"pipeline({hid}): {outcome}",
        )
        return {**row, "outcome": outcome, "detail": detail, "status": status}

    def _check_and_explore(self, hid: str, name: str, strategy_file: str, timeframe: str) -> tuple[str, str]:
        result = self.run_checks(name, timeframe=timeframe, root=self.root)
        if not checks.passed(result):
            registry.set_hypothesis_status(self.conn, hid, "failed: causality checks")
            brief = {pair: {k: v for k, v in cell.items() if k != "lookahead_row"} for pair, cell in result.items()}
            return "failed the causality checks", json.dumps(brief)[:300]
        cal = self.explore(self.conn, hid, strategy_name=name, strategy_file=strategy_file, timeframe=timeframe, root=self.root)
        if cal["outcome"] == "failed":
            registry.set_hypothesis_status(self.conn, hid, "failed: calibration")
            return "calibration failed", cal.get("reason", "")
        if cal["outcome"] != "explored":
            return cal["status"], f"calibration trades {cal['counts']}"
        try:
            self.write_review(self.conn, hid, root=self.root)
        except ValueError:
            pass
        return cal["status"], f"exposure {cal['exposure']}; calibration trades {cal['counts']}"

    # -- the weekly run ---------------------------------------------------------------

    def weekly(self, *, scout_count: int = 5, max_new: int | None = None, do_scout: bool = True) -> Path:
        lab = self.lab
        lab.cycle_start, lab.proposed_this_cycle = _now(), 0
        rows, scouted, triaged, stopped = [], [], [], ""
        try:
            if self.expand_data is not None:
                self.expand_data()
            if do_scout:
                scouted = lab.scout(scout_count)
            triaged = lab.triage_ideas()
            limit = min(max_new or lab.budget["max_hypotheses_per_cycle"], lab.budget["max_hypotheses_per_cycle"])
            for idea in triage.pick(self.conn, limit):
                rows.append(self.process_idea(idea))
        except (GuardAbort, BudgetExhausted, StepFailed) as error:
            stopped = f"{type(error).__name__}: {error}"
        return self.write_report(rows, scouted, triaged, stopped)

    def write_report(self, rows: list[dict], scouted: list[dict], triaged: list[dict], stopped: str) -> Path:
        lab = self.lab
        spent = registry.agent_cost_since(self.conn, lab.cycle_start)
        trials = trial_count(self.conn)
        by_state: dict[str, int] = {}
        for idea in registry.list_ideas(self.conn):
            by_state[idea["state"]] = by_state.get(idea["state"], 0) + 1
        candidates = [r for r in rows if r["outcome"].startswith("candidate")]
        outcome = "STOPPED - " + stopped if stopped else "completed (stops at the exploration by design)"
        lines = [
            f"# Pipeline cycle {lab.cycle_start}", "", LABEL, "",
            f"- Outcome: {outcome}",
            f"- Agent spend this cycle: {spent:.2f} USD (cap {lab.budget['max_agent_budget_usd_per_cycle']:.2f})",
            f"- N of the Deflated Sharpe Ratio (configurations ever tried): **{trials['total']}** "
            f"({trials['hypotheses']} registered hypotheses + {trials['extra']} recorded grid/sensitivity/ablation configurations)",
            f"- Scout: {sum(1 for o in scouted if o['idea_id'])} idea(s) collected, {sum(1 for o in scouted if not o['idea_id'])} file(s) rejected",
            f"- Triage this run: {sum(1 for t in triaged if t['state'] == 'queued')} queued, {sum(1 for t in triaged if t['state'] == 'dropped')} dropped",
            "- All ideas by state: " + (", ".join(f"{k} {v}" for k, v in sorted(by_state.items())) or "none"), "",
            "| Idea | Hypothesis | Outcome | Detail |", "|---|---|---|---|",
        ]
        for r in rows:
            lines.append(f"| {r['idea']} | {r.get('hypothesis') or '-'} | {r['outcome']} | {r['detail'].replace('|', '/')} |")
        if not rows:
            lines.append("| none | | | |")
        lines += ["", "## Dropped by the triage this run", ""]
        dropped = [t for t in triaged if t["state"] == "dropped"]
        lines += [f"- {t['idea_id']}: {'; '.join(t['reasons'])}" for t in dropped] or ["- none"]
        lines += ["", "## Waiting for you", ""]
        if candidates:
            for r in candidates:
                hid = r["hypothesis"]
                lines.append(
                    f"- {hid} passed the exploration gates on every pair. To spend its single validation read: "
                    f"`python research/tools/approve.py {hid} --stage validation`, then "
                    f"`python research/tools/validate_once.py {hid} --exposure <the calibrated exposure in its notes>`."
                )
        else:
            lines.append("- Nothing: no hypothesis passed the exploration in this run.")
        lines.append("")
        path = self.root / "research" / "pipeline" / f"cycle-{_stamp()}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")
        self._commit([self.lab._rel(path)], f"pipeline: weekly cycle report {path.stem}")
        return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m lab.pipeline", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    weekly = sub.add_parser("weekly", help="run one weekly cycle (stops at the exploration)")
    weekly.add_argument("--scout-count", type=int, default=5)
    weekly.add_argument("--max-new", type=int, default=None)
    weekly.add_argument("--no-scout", action="store_true", help="skip the scout and work the existing queue")
    weekly.add_argument("--expand-data", action="store_true", help="download/extend candles first (needs Docker)")
    args = parser.parse_args(argv)
    lab = orchestrator.Lab(registry.connect())
    pipeline = Pipeline(lab, expand_data=orchestrator.expand_data if args.expand_data else None)
    print(pipeline.weekly(scout_count=args.scout_count, max_new=args.max_new, do_scout=not args.no_scout))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
