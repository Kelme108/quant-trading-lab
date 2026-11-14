"""Agent pipeline for the proxy markets (plan item 4 of research/reviews/2026-11-14-veredito-1m-5m.md).

One cycle = one new rule:
 1. b3/proxy_program.py status: the weekly cap (3), the 15-rules-without-validation stop and the project stop;
 2. the proxy-research agent writes research/proxies/proposals/P-NNN.json from a context file with
    EXPLORATION facts only; the proposal is checked (scope, 30-120 minute hold, sources);
 3. the proxy-developer agent writes b3/proxy_rules/p<NNN>_<name>.py and its synthetic test;
 4. static screen (b3.strategy_check.check_proxy_rule_source), causality and live-window parity on synthetic
    sessions in a fresh process, the rule's test and tests/b3;
 5. commit of the proposal, context, rule and test BEFORE any read (ex ante);
 6. exploration on the proposal's markets; validation, read once, only where exploration passed; the final
    test stays locked (owner); scoreboard; commit of the results.
After every agent call the working tree is compared with the one before: anything outside the expected files
aborts the cycle. An agent is a text producer; gates_proxies.json decides.

    python -m b3.proxy_pipeline status
    python -m b3.proxy_pipeline cycle [--max 1]
    python -m b3.proxy_pipeline check P-008        (step 4 alone)
Pause: create ops/state/STOP_PROXY_CYCLES.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
import tempfile
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from b3 import proxy_program as prog

ROOT = prog.ROOT
LOG = ROOT / "research" / "proxies" / "pipeline_log.jsonl"
STOP_FILE = ROOT / "ops" / "state" / "STOP_PROXY_CYCLES"
LOCK = Path(tempfile.gettempdir()) / "trade-initial-proxy-pipeline.lock"
TRAILER = "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"


class CycleError(RuntimeError):
    pass


def log(event: str, **kw) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "event": event} | kw,
                            default=str) + "\n")
    print(event, json.dumps(kw, default=str)[:400], flush=True)


def changed_paths() -> set[str]:
    out = subprocess.run(["git", "status", "--porcelain", "-uall"], cwd=ROOT, capture_output=True, text=True,
                         encoding="utf-8", check=True).stdout
    return {line[3:].strip().strip('"').replace("\\", "/") for line in out.splitlines() if line.strip()}


def guard(before: set[str], allowed: set[str], who: str) -> None:
    allowed = allowed | {LOG.relative_to(ROOT).as_posix()}
    new = {p for p in changed_paths() - before if "__pycache__" not in p and not p.endswith(".pyc")
           and ".pytest_cache" not in p}
    extra = new - allowed
    if extra:
        raise CycleError(f"{who} changed files outside {sorted(allowed)}: {sorted(extra)}")


def run_agent(name: str, prompt: str, budget: float, timeout_s: float) -> dict:
    from lab.agents import build_argv, parse_output
    argv = build_argv(name, budget)
    done = subprocess.run(argv, input=prompt, cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout_s, check=False)
    data = parse_output(done.stdout)
    log("agent", agent=name, exit=done.returncode, cost_usd=data.get("total_cost_usd"),
        turns=data.get("num_turns"), is_error=data.get("is_error"), result=str(data.get("result", ""))[:600])
    if done.returncode != 0 or data.get("is_error"):
        raise CycleError(f"{name} failed: {str(data.get('result', ''))[:300]} {done.stderr[:300]}")
    return data


def py(*args: str, timeout: float = 3600) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout, check=False)


# ---------------------------------------------------------------------------------------------
# Step 4: checks of an implemented rule (run in a fresh process: `check P-NNN`)
# ---------------------------------------------------------------------------------------------

def synthetic_sessions(symbol: str, days: int = 45, seed: int = 3, tf: int = 5):
    import pandas as pd
    from b3.markets import market
    m = market(symbol)
    rng = random.Random(seed)
    d, rows, prev, step = date(2026, 1, 5), [], 5000.0, 0.5
    n = 0
    while n < days:
        if d.weekday() < 5:
            n += 1
            t = datetime.combine(d, m.open, m.zone)
            end = datetime.combine(d, m.close, m.zone)
            while t + timedelta(minutes=tf) <= end:
                o = prev + step * rng.randint(-3, 3)
                c = o + step * rng.randint(-6, 6)
                rows.append((pd.Timestamp(t.astimezone(timezone.utc)), o, max(o, c) + step * rng.randint(0, 3),
                             min(o, c) - step * rng.randint(0, 3), c, float(rng.randint(50, 500))))
                prev, t = c, t + timedelta(minutes=tf)
        d += timedelta(days=1)
    return pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])


def check_rule(rule_id: str) -> list[str]:
    from b3.backtest import run
    from b3.checks import causality_problems, window_parity_problems
    from b3.markets import market
    from b3.proxy_rules import RULES, rule_files
    from b3.strategy_check import check_proxy_rule_source
    files = [p for p in rule_files() if p.stem.startswith(f"p{rule_id[2:]}_")]
    if len(files) != 1:
        return [f"expected one file b3/proxy_rules/p{rule_id[2:]}_*.py, found {len(files)}"]
    problems = check_proxy_rule_source(files[0], rule_id)
    if problems or rule_id not in RULES:
        return problems or [f"{rule_id} is not in the registry"]
    proposal = json.loads((prog.PROPOSALS / f"{rule_id}.json").read_text(encoding="utf-8"))
    rule = RULES[rule_id]
    if rule.timeframe_min != proposal["timeframe_min"]:
        problems.append(f"timeframe {rule.timeframe_min} differs from the proposal's {proposal['timeframe_min']}")
    days = max(45, rule.warmup // max(1, int(390 / rule.timeframe_min)) + 20)
    for sym in proposal["markets"]:
        frame = synthetic_sessions(sym, days=days, tf=rule.timeframe_min)
        strat = rule.on(sym)()
        problems += [f"{sym}: {p}" for p in causality_problems(strat, frame)]
        problems += [f"{sym}: {p}" for p in window_parity_problems(strat, frame, samples=80)]
        res = run(frame, strat, market(sym).cost("base"))
        if res.positions_held_overnight:
            problems.append(f"{sym}: held {res.positions_held_overnight} positions overnight on synthetic data")
    return problems


# ---------------------------------------------------------------------------------------------
# The cycle
# ---------------------------------------------------------------------------------------------

def commit(paths: list[str], message: str) -> None:
    from lab.gitops import commit_paths
    commit_paths(ROOT, paths, message + TRAILER)


def cycle() -> str:
    cfg = prog.load_program()
    st = prog.status(program=cfg)
    if not st.can_register:
        log("program_stop", reasons=st.reasons, notices=st.notices)
        return "stopped"
    rid = prog.next_rule_id()
    ctx = prog.write_context(rid, st, cfg)
    out = prog.PROPOSALS / f"{rid}.json"
    rel = lambda p: p.relative_to(ROOT).as_posix()  # noqa: E731
    before = changed_paths()
    a = cfg["agents"]
    run_agent("proxy-research", (
        f"Rule id: {rid}\nContext file: {rel(ctx)}\nOutput path: {rel(out)}\n"
        "Read the context file first. Write exactly one JSON file at the output path."), a["research_budget_usd"], a["timeout_s"])
    guard(before, {rel(out)}, "proxy-research")
    if not out.exists():
        raise CycleError(f"proxy-research wrote no {rel(out)}")
    p = json.loads(out.read_text(encoding="utf-8"))
    scope = json.loads((ROOT / "b3/config/scope_proxies.json").read_text(encoding="utf-8"))
    problems = prog.validate_proposal(p, rid, cfg, scope["markets"])
    if problems:
        p |= {"status": "invalid", "problems": problems}
        out.write_text(json.dumps(p, indent=1), encoding="utf-8")
        commit([rel(out), rel(ctx)], f"exp(proxies): {rid} proposal rejected by the format check")
        log("proposal_invalid", rule=rid, problems=problems)
        return "invalid"
    p |= {"status": "registered", "registered_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    out.write_text(json.dumps(p, indent=1, ensure_ascii=False), encoding="utf-8")
    rule_file = ROOT / "b3" / "proxy_rules" / f"{p['file_stem']}.py"
    test_file = ROOT / "tests" / "b3" / "proxy_rules" / f"test_p{rid[2:]}.py"
    before = changed_paths()
    run_agent("proxy-developer", (
        f"Proposal: {rel(out)}\nRule file: {rel(rule_file)}\nClass name: {p['class_name']}\nTest file: {rel(test_file)}\n"
        "Implement the rule exactly as the proposal states."), a["developer_budget_usd"], a["timeout_s"])
    guard(before, {rel(rule_file), rel(test_file)}, "proxy-developer")
    chk = py("-m", "b3.proxy_pipeline", "check", rid, timeout=1800)
    tests = py("-m", "pytest", rel(test_file), "tests/b3", "-q", timeout=1800)
    if chk.returncode != 0 or tests.returncode != 0:
        log("implementation_rejected", rule=rid, check=chk.stdout[-1500:] + chk.stderr[-500:],
            tests=tests.stdout[-1500:])
        p |= {"status": "implementation_failed"}
        out.write_text(json.dumps(p, indent=1, ensure_ascii=False), encoding="utf-8")
        for f in (rule_file, test_file):          # never leave a failing rule in the registry
            if f.exists():
                f.unlink()
        commit([rel(out), rel(ctx)], f"exp(proxies): {rid} implementation failed the checks (rule not run)")
        return "implementation_failed"
    commit([rel(out), rel(ctx), rel(rule_file), rel(test_file)],
           f"exp(proxies): register {rid} {p['title'][:60]} ({', '.join(p['markets'])}, {p['timeframe_min']}m; agent proposal, ex ante)")
    log("registered", rule=rid, markets=p["markets"], title=p["title"])

    before_results = set((ROOT / "research/proxies/results").glob("*.json"))
    r = py("-m", "b3.proxy_research", "run", rid, "--symbols", ",".join(p["markets"]), "--split", "exploration")
    log("exploration", rule=rid, out=r.stdout[-2000:], err=r.stderr[-800:])
    if r.returncode != 0:
        raise CycleError(f"exploration of {rid} failed: {r.stderr[-500:]}")
    passed = [row["symbol"] for row in prog.ledger_rows()
              if row["rule"] == rid and row["split"] == "exploration" and row["decision"] == "passed"]
    if passed:
        v = py("-m", "b3.proxy_research", "run", rid, "--symbols", ",".join(passed), "--split", "validation")
        log("validation", rule=rid, out=v.stdout[-2000:], err=v.stderr[-800:])
    py("-m", "b3.proxy_report")
    new = sorted(set((ROOT / "research/proxies/results").glob("*.json")) - before_results)
    commit([rel(f) for f in new] + ["research/proxies/ledger.jsonl", "research/proxies/SCOREBOARD.md",
                                    "research/proxies/scoreboard.json", rel(LOG)],
           f"exp(proxies): {rid} exploration on {', '.join(p['markets'])}" + (f"; validation on {', '.join(passed)}" if passed else ""))
    return "done"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    c = sub.add_parser("cycle")
    c.add_argument("--max", type=int, default=1)
    k = sub.add_parser("check")
    k.add_argument("rule")
    a = ap.parse_args(argv)
    if a.cmd == "status":
        print(json.dumps(asdict(prog.status()), indent=1))
        return 0
    if a.cmd == "check":
        problems = check_rule(a.rule)
        print("\n".join(problems) or "ok")
        return 1 if problems else 0
    if STOP_FILE.exists():
        print(f"paused: {STOP_FILE} exists")
        return 0
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        print(f"another proxy pipeline holds {LOCK}; not starting a second one")
        return 2
    try:
        os.write(fd, str(os.getpid()).encode())
        for _ in range(a.max):
            try:
                outcome = cycle()
            except CycleError as e:
                log("cycle_error", error=str(e))
                return 1
            if outcome == "stopped":
                break
        return 0
    finally:
        os.close(fd)
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
