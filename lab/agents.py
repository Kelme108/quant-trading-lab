"""Run one of the project's subagents (.claude/agents/<name>.md) headlessly.

Each call is `claude -p --agent <name>` with the prompt on stdin (never on the
command line, so nothing in it can be re-parsed by a shell), a fixed tool set,
a per-call spending cap, and no saved session. What an agent may write is not
enforced here: lab/guard.py checks the working tree after every call.

An agent is a text producer, never a decision maker: approval and rejection
live in lab/gates.py and lab/portfolio.py.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from lab import registry

ROOT = Path(__file__).parents[1]
DEFAULT_MODEL = "sonnet"
# Owner's request (2026-11-06): the agents that design and implement the rule run on the stronger model;
# the others stay on the default. Costs more per call; the per-call and per-cycle caps still apply.
AGENT_MODELS: dict[str, str] = {"scout": "opus", "research": "opus",  # developer back on sonnet 2026-11-09: same error rate, ~3x cheaper
                                "proxy-research": "opus", "esteira-research": "opus"}

# tools: the built-in tools the agent gets at all (--tools).
# allow: tool rules pre-approved so a headless run never stops on a prompt;
#        anything else that would prompt is denied automatically.
# deny:  read rules the agent must not get past (--disallowedTools). The
#        research agent designs the next hypothesis, so it must not see
#        validation results: each one it read would make the validation split
#        one more thing the lab is fitted to.
AGENT_SPECS: dict[str, dict[str, list[str]]] = {
    "research": {
        "tools": ["Read", "Grep", "Glob", "WebSearch", "WebFetch", "Write"],
        "allow": ["WebSearch", "WebFetch", "Write"],
        "deny": [
            "Read(./research/experiments/**)",
            "Read(./research/portfolio/**)",
            "Read(./user_data/backtest_results/**)",
            "Read(./reports/**)",
            "Read(./research/lab.sqlite)",
            # Historical records that still describe the invalidated one-trade results.
            "Read(./research/manifests/**)",
            "Read(./research/command-log.md)",
            "Read(./research/validation-run-*.md)",
            "Read(./research/validation-protocol.md)",
        ],
    },
    # The scout collects strategy ideas (rules in words) from the web. It sees no result of any kind: not the
    # experiments, not the audit reports, dossiers, grids or baselines. It writes only research/intake/*.json.
    "scout": {
        "tools": ["Read", "Grep", "Glob", "WebSearch", "WebFetch", "Write"],
        "allow": ["WebSearch", "WebFetch", "Write"],
        "deny": [
            "Read(./research/experiments/**)",
            "Read(./research/portfolio/**)",
            "Read(./research/audit/**)",
            "Read(./research/dossiers/**)",
            "Read(./research/baselines/**)",
            "Read(./research/grids/**)",
            "Read(./research/pipeline/**)",
            "Read(./user_data/backtest_results/**)",
            "Read(./reports/**)",
            "Read(./research/lab.sqlite)",
            "Read(./research/manifests/**)",
            "Read(./research/command-log.md)",
            "Read(./research/validation-run-*.md)",
            "Read(./docs/relatorio-*.md)",
        ],
    },
    "developer": {
        "tools": ["Read", "Grep", "Glob", "Write", "Edit", "Bash"],
        "allow": ["Write", "Edit", "Bash(python -m unittest *)"],
        "deny": [],
    },
    # Proxy-market lane (b3/proxy_pipeline.py, plan item 4 of research/reviews/2026-11-14-veredito-1m-5m.md).
    # The proxy researcher sees exploration diagnostics only: no result file (they hold validation and final-test
    # reads), no ledger, no scoreboard, no review, no splits file (it names the rules that reached the final test).
    "proxy-research": {
        "tools": ["Read", "Grep", "Glob", "WebSearch", "WebFetch", "Write"],
        "allow": ["WebSearch", "WebFetch", "Write"],
        "deny": [
            "Read(./research/proxies/results/**)",
            "Read(./research/proxies/ledger.jsonl)",
            "Read(./research/proxies/SCOREBOARD.md)",
            "Read(./research/proxies/scoreboard.json)",
            "Read(./research/proxies/pipeline_log.jsonl)",
            "Read(./research/reviews/**)",
            "Read(./b3/config/splits_proxies.json)",
            "Read(./research/command-log.md)",
            "Read(./research/experiments/**)",
            "Read(./research/lab.sqlite)",
            # trade lists hold validation and final-test reads too (proxies since 2026-11-15)
            "Read(./research/proxies/trades/**)",
            # WIN/WDO lane (2026-11-16): the same blindness
            "Read(./research/b3/results/**)",
            "Read(./research/b3/trades/**)",
            "Read(./research/b3/ledger.jsonl)",
            "Read(./b3/config/splits_b3.json)",
        ],
    },
    # Strategy conveyor (b3/esteira_cycle.py, owner 2026-11-17): writes families as one Python file. It sees the
    # conveyor's EXPLORATION summary through its context file, never a validation or final-test read.
    "esteira-research": {
        "tools": ["Read", "Grep", "Glob", "WebSearch", "WebFetch", "Write"],
        "allow": ["WebSearch", "WebFetch", "Write"],
        "deny": [
            "Read(./research/b3/results/**)",
            "Read(./research/b3/trades/**)",
            "Read(./research/b3/ledger.jsonl)",
            "Read(./research/b3/esteira/trades/**)",
            "Read(./b3/config/splits_b3.json)",
            "Read(./research/proxies/results/**)",
            "Read(./research/proxies/trades/**)",
            "Read(./research/reviews/**)",
            "Read(./research/command-log.md)",
            "Read(./research/experiments/**)",
            "Read(./research/lab.sqlite)",
            "Read(./live/**)",
        ],
    },
    "proxy-developer": {
        "tools": ["Read", "Grep", "Glob", "Write", "Edit", "Bash"],
        "allow": ["Write", "Edit", "Bash(python -m pytest *)"],
        "deny": ["Read(./research/proxies/results/**)", "Read(./research/proxies/ledger.jsonl)",
                 "Read(./research/proxies/trades/**)", "Read(./research/b3/results/**)", "Read(./research/b3/trades/**)",
                 "Read(./research/b3/ledger.jsonl)"],
    },
    "quant": {"tools": ["Read", "Grep", "Glob", "Write"], "allow": ["Write"], "deny": []},
    "risk": {"tools": ["Read", "Grep", "Glob", "Write"], "allow": ["Write"], "deny": []},
    "validator": {"tools": ["Read", "Grep", "Glob", "Write"], "allow": ["Write"], "deny": []},
}


class AgentError(RuntimeError):
    """The agent call failed (non-zero exit, unreadable output, or an error result)."""


@dataclass
class AgentResult:
    text: str
    cost_usd: float
    num_turns: int
    duration_s: float
    session_id: str | None


def build_argv(
    name: str, budget_usd: float, claude_path: str | None = None, model: str | None = None
) -> list[str]:
    """The exact command line for an agent call (the prompt is sent on stdin)."""
    if name not in AGENT_SPECS:
        raise ValueError(f"unknown agent '{name}'; expected one of {sorted(AGENT_SPECS)}")
    spec = AGENT_SPECS[name]
    executable = claude_path or shutil.which("claude")
    if executable is None:
        raise AgentError("the `claude` CLI was not found on PATH")
    return [
        executable,
        "-p",
        "--agent", name,
        "--model", model or AGENT_MODELS.get(name, DEFAULT_MODEL),
        "--output-format", "json",
        "--permission-mode", "acceptEdits",
        "--tools", *spec["tools"],
        "--allowedTools", *spec["allow"],
        *(["--disallowedTools", *spec["deny"]] if spec["deny"] else []),
        "--max-budget-usd", f"{budget_usd:g}",
        "--no-session-persistence",
    ]


def parse_output(stdout: str) -> dict:
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise AgentError(f"agent output is not JSON: {error}; first 300 chars: {stdout[:300]!r}") from error
    if not isinstance(data, dict):
        raise AgentError("agent output is not a JSON object")
    return data


def run_agent(
    conn,
    name: str,
    prompt: str,
    *,
    purpose: str,
    budget_usd: float,
    timeout_s: float,
    hypothesis_id: str | None = None,
    claude_path: str | None = None,
    run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> AgentResult:
    """Run the agent, record the call (cost, turns, status) in the registry, and
    return its result. Raises AgentError on any failure, after recording it."""
    started = datetime.now(timezone.utc)
    clock = time.monotonic()

    def record(status: str, data: dict | None = None, excerpt: str = "") -> None:
        data = data or {}
        registry.record_agent_run(
            conn,
            agent=name,
            hypothesis_id=hypothesis_id,
            purpose=purpose,
            status=status,
            started_at_utc=started.isoformat(),
            cost_usd=data.get("total_cost_usd"),
            num_turns=data.get("num_turns"),
            duration_s=time.monotonic() - clock,
            session_id=data.get("session_id"),
            result_excerpt=excerpt or str(data.get("result", "")),
        )

    argv = build_argv(name, budget_usd, claude_path)
    try:
        completed = run(
            argv,
            input=prompt,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        record("failed", excerpt=f"timed out after {timeout_s}s")
        raise AgentError(f"{name} timed out after {timeout_s}s") from error

    try:
        data = parse_output(completed.stdout)
    except AgentError as error:
        record("failed", excerpt=f"exit {completed.returncode}: {error}; stderr: {completed.stderr[:500]}")
        raise

    if completed.returncode != 0 or data.get("is_error"):
        record("failed", data)
        raise AgentError(
            f"{name} failed (exit {completed.returncode}): {str(data.get('result', ''))[:500]}"
        )

    record("completed", data)
    return AgentResult(
        text=str(data.get("result", "")),
        cost_usd=float(data.get("total_cost_usd") or 0.0),
        num_turns=int(data.get("num_turns") or 0),
        duration_s=time.monotonic() - clock,
        session_id=data.get("session_id"),
    )
