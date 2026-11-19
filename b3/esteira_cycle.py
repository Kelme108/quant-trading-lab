"""Unattended conveyor cycle (b3/config/esteira_b3.json, owner 2026-11-17 'tudo aprovado'; it replaces the
one-rule agent cycle of b3/proxy_pipeline.py for WIN/WDO).

One cycle = one batch:
 1. limits: families screened today (UTC) < max_families_per_day and the agents' cost today + one call's budget
    <= max_agent_cost_usd_per_day; the pause file; one cycle at a time;
 2. a context file with the conveyor's EXPLORATION summary (research/b3/esteira/context/B-NNN.md);
 3. the esteira-research agent writes b3/families/b<NNN>_agent.py with 5-10 families on the ids given; the working
    tree is compared before/after: anything else written aborts the cycle;
 4. static check (imports, names; whole file thrown away if it fails), then, in a fresh process with a time
    limit, every family is loaded, its limits checked and its signal run with the look-ahead and window checks on
    SYNTHETIC sessions; a family failing is recorded as rejected and never screened;
 5. commit of the batch file and its context BEFORE any read (ex ante);
 6. `b3.esteira.screen` on the batch's ids (exploration, real data, the same checks again before any read),
    commit of the run, ledger, families list and selected list.

    python -m b3.esteira_cycle status
    python -m b3.esteira_cycle cycle
    python -m b3.esteira_cycle precheck b3/families/b002_agent.py
Pause: create ops/state/STOP_ESTEIRA.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from b3 import esteira as es
from b3.calendar import SP_TZ

ROOT = es.ROOT
OUT = es.OUT
LOG = OUT / "cycle_log.jsonl"
CONTEXT_DIR = OUT / "context"
REJECTED_DIR = OUT / "rejected_files"
STOP_FILE = ROOT / "ops" / "state" / "STOP_ESTEIRA"
LOCK = Path(tempfile.gettempdir()) / "trade-initial-esteira-cycle.lock"
TRAILER = "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
AGENT = "esteira-research"
AGENT_BUDGET_USD = 3.0
AGENT_TIMEOUT_S = 1500
BATCH_MAX, BATCH_MIN = 10, 5
MAX_CONSECUTIVE_ERRORS = 2

ALLOWED_IMPORTS = {"numpy", "pandas", "math", "__future__", "b3.esteira"}
FORBIDDEN_NAMES = {"open", "exec", "eval", "compile", "__import__", "getattr", "setattr", "delattr", "globals",
                   "locals", "vars", "input", "breakpoint", "os", "sys", "subprocess", "pathlib", "Path", "socket",
                   "shutil", "pickle", "importlib", "builtins", "__builtins__", "exit", "quit"}
# numpy/pandas calls that touch files (a family computes from ctx only)
FORBIDDEN_ATTRS = {"load", "save", "savez", "savez_compressed", "fromfile", "tofile", "loadtxt", "savetxt",
                   "genfromtxt", "memmap", "ctypeslib", "DataSource", "lib", "testing", "f2py", "distutils"}


class CycleError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(event: str, **kw) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"at_utc": _now(), "event": event} | kw, default=str) + "\n")
    print(event, json.dumps(kw, default=str)[:400], flush=True)


def _log_rows() -> list[dict]:
    if not LOG.exists():
        return []
    return [json.loads(x) for x in LOG.read_text(encoding="utf-8").splitlines() if x.strip()]


# ---------------------------------------------------------------------------------------------
# Limits and ids
# ---------------------------------------------------------------------------------------------

def sp_day(at_utc: str):
    return datetime.fromisoformat(at_utc).astimezone(SP_TZ).date()


def today_sp():
    return datetime.now(SP_TZ).date()


def cost_today(rows: list[dict] | None = None, day=None) -> float:
    """Agent cost of the Sao Paulo calendar day (owner 2026-11-18)."""
    day = day or today_sp()
    return float(sum(r.get("cost_usd") or 0.0 for r in (rows if rows is not None else _log_rows())
                     if r.get("event") == "agent" and r.get("at_utc") and sp_day(r["at_utc"]) == day))


def families_today(done: dict | None = None, day=None) -> int:
    day = day or today_sp()
    done = es.screened_ids() if done is None else done
    return sum(1 for r in done.values() if r.get("screened_at_utc") and sp_day(r["screened_at_utc"]) == day)


def room(cfg: dict, done: dict | None = None, rows: list[dict] | None = None) -> tuple[int, list[str]]:
    """How many families this cycle may ask for (0 = stop), and why not more."""
    lim = cfg["limits"]
    why = []
    left = lim["max_families_per_day"] - families_today(done)
    if left < BATCH_MIN:
        why.append(f"daily family limit: {lim['max_families_per_day'] - left}/{lim['max_families_per_day']} screened today")
    spent = cost_today(rows)
    if spent + AGENT_BUDGET_USD > lim["max_agent_cost_usd_per_day"]:
        why.append(f"daily agent cost: US${spent:.2f} spent, one call may cost up to US${AGENT_BUDGET_USD:.2f}, "
                   f"limit US${lim['max_agent_cost_usd_per_day']:.2f}")
    return (0 if why else min(BATCH_MAX, left)), why


def _id_num(fid: str) -> int:
    m = re.fullmatch(r"E-(\d{3,})", fid)
    return int(m.group(1)) if m else 0


def next_ids(k: int) -> list[str]:
    used = {_id_num(f) for f in es.screened_ids()}
    for path in list(es.FAMILY_DIR.glob("*.py")) + list(REJECTED_DIR.glob("*.py")):
        used |= {int(x) for x in re.findall(r"\"E-(\d{3,})\"", path.read_text(encoding="utf-8", errors="replace"))}
    start = max(used | {0}) + 1
    return [f"E-{i:03d}" for i in range(start, start + k)]


def next_batch() -> int:
    nums = [int(m.group(1)) for p in list(es.FAMILY_DIR.glob("b*_agent.py")) + list(REJECTED_DIR.glob("b*_agent.py"))
            if (m := re.match(r"b(\d+)_agent", p.stem))]
    return max(nums + [1]) + 1          # batch 1 is the assistant's e001_batch1.py


# ---------------------------------------------------------------------------------------------
# Context for the agent (exploration only)
# ---------------------------------------------------------------------------------------------

def screened_summary() -> list[dict]:
    """Per family and market: the best variant on exploration and why it failed (from the run reports)."""
    out = []
    for path in sorted((OUT / "runs").glob("*.json")):
        rep = json.loads(path.read_text(encoding="utf-8"))
        for fid, f in rep.get("families", {}).items():
            row = {"family": fid, "title": f.get("title"), "hypothesis": f.get("hypothesis"), "markets": {}}
            if f.get("rejected"):
                row["rejected"] = f["rejected"]
            for mk, m in f.get("markets", {}).items():
                rows = m.get("rows") or []
                checks = {k: v for k, v in m.items() if k.endswith("_check")}
                if not rows:
                    row["markets"][mk] = {"checks_failed": checks} if checks else {}
                    continue
                best = rows[0]
                me = best["measured"]
                row["markets"][mk] = {"variants": m.get("variants"), "passed_screen": m.get("passed_screen"),
                                      "best": best["variant"], "trades_per_year": me.get("trades_per_year"),
                                      "mean_net_brl": me.get("mean_net_brl"), "hit_rate": me.get("hit_rate"),
                                      "positive_slices": me.get("positive_slices"), "fails": best.get("fails")}
            out.append(row)
    return out


def _older_rule_titles() -> list[str]:
    titles = []
    for d in (ROOT / "research" / "b3" / "proposals",):
        for p in sorted(d.glob("P-*.json")):
            try:
                j = json.loads(p.read_text(encoding="utf-8"))
                titles.append(f"{j.get('rule_id', p.stem)}: {j.get('title', '')}")
            except (json.JSONDecodeError, OSError):
                continue
    try:
        fams = json.loads((ROOT / "b3" / "config" / "pattern_search_b3.json").read_text(encoding="utf-8"))["families"]
        titles += [f"pattern search {k}" for k in fams if not k.startswith("_")]
    except (OSError, KeyError, json.JSONDecodeError):
        pass
    return titles


def _fmt(x, nd=2):
    return "-" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def write_context(batch: int, ids: list[str], cfg: dict) -> Path:
    ex, sc = cfg["default_exit"], cfg["screen"]
    lines = [f"# Conveyor batch B-{batch:03d}: context (generated {_now()})", "",
             f"Write {len(ids)} families with ids {', '.join(ids)}.", "",
             "## Fixed for every family",
             f"- Markets {cfg['markets']}, timeframes {cfg['timeframes_min']} minutes; split: EXPLORATION only.",
             f"- Default exit (you do not write it): target R${ex['target_brl']:g}, stop R${ex['stop_brl']:g}, "
             f"time limit {ex['max_hold_min']} min, replayed on 1-minute bars; entry at the open of the minute after "
             f"the signal bar's close; one position at a time; at most {cfg['max_entries_per_session']} entries per session.",
             "- Contracts: WIN tick 5 points = R$1; WDO tick 0.5 point = R$5. R$30 is 150 WIN points (30 ticks) but "
             "only 6 WDO ticks, and the WDO round-trip cost is about R$6, so WDO families need a move far larger "
             "than WIN's to survive this exit: give `markets=(\"WIN\",)` unless the idea is about the dollar.",
             f"- Screen: >= {sc['min_trades_per_year']} trades/year; mean net per trade > R${sc['mean_net_brl_measured_gt']:g} "
             f"at the measured cost; >= {sc['min_positive_slices']} of {sc['time_slices']} time slices positive; "
             f"plateau: >= 2/3 of one-step neighbours positive; best variant per family; overlap <= "
             f"{sc['max_overlap_with_selected']} with rules already selected.",
             "- Checks before any result: no look-ahead (prefix cuts) and the 21-session window.", "",
             "## Families already screened (exploration, best variant per market)", "",
             "| id | title | market | best variant | trades/yr | net R$/trade | hit | +slices | fails |",
             "|---|---|---|---|---|---|---|---|---|"]
    summ = screened_summary()
    for r in summ:
        if r.get("rejected"):
            lines.append(f"| {r['family']} | {r['title']} | - | rejected: {'; '.join(r['rejected'])[:120]} | | | | | |")
        for mk, m in r["markets"].items():
            if "best" not in m:
                lines.append(f"| {r['family']} | {r['title']} | {mk} | check failed | | | | | |")
                continue
            lines.append(f"| {r['family']} | {r['title']} | {mk} | {m['best'].replace('|', ' ')} |{_fmt(m['trades_per_year'], 0)} | "
                         f"{_fmt(m['mean_net_brl'])} | {_fmt(m['hit_rate'])} | {m['positive_slices']} | "
                         f"{', '.join(m['fails'] or []) or 'passed'} |")
    lines += ["", "Hypotheses of the screened families (do not repeat them):", ""]
    lines += [f"- {r['family']} {r['title']}: {r['hypothesis']}" for r in summ]
    lines += ["", "## Older rules (agent lane P-NNN and the pattern search): do not repeat these mechanisms", ""]
    lines += [f"- {t}" for t in _older_rule_titles()]
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    path = CONTEXT_DIR / f"B-{batch:03d}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------------------------
# Checks of the agent's file
# ---------------------------------------------------------------------------------------------

def static_problems(source: str) -> list[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f"syntax error: {e}"]
    why = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in ALLOWED_IMPORTS and a.name not in ALLOWED_IMPORTS:
                    why.append(f"import {a.name} not allowed")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod not in ALLOWED_IMPORTS and mod.split(".")[0] not in ALLOWED_IMPORTS - {"b3.esteira"}:
                why.append(f"from {mod} import not allowed")
            if mod == "b3.esteira" and any(a.name != "Family" for a in node.names):
                why.append("from b3.esteira only Family may be imported")
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            why.append(f"name {node.id} not allowed")
        elif isinstance(node, ast.Attribute) and (node.attr.startswith("__") or node.attr in FORBIDDEN_ATTRS
                                                  or node.attr.startswith("read_")
                                                  or (node.attr.startswith("to_") and node.attr != "to_numpy")):
            why.append(f"attribute {node.attr} not allowed")
    return sorted(set(why))


def synthetic_frame(n_days: int = 30, per_day: int = 20, seed: int = 1):
    """Random-walk SESSIONS (not market data) to run a family's code before it sees real bars."""
    from b3 import pattern_search as ps
    rng = np.random.default_rng(seed)
    n = n_days * per_day
    c = 100000 + np.cumsum(rng.choice([-10, -5, 0, 5, 10], n)).astype(float)
    o = np.r_[c[0], c[:-1]]
    h, l = np.maximum(o, c) + 5, np.minimum(o, c) - 5
    day = np.repeat(np.arange(n_days), per_day)
    bar = np.tile(np.arange(per_day), n_days)
    times = pd.Timestamp("2026-01-05T12:00:00Z") + pd.to_timedelta(day, "D") + pd.to_timedelta(bar * 5, "min")
    dates = (pd.Timestamp("2026-01-05") + pd.to_timedelta(day, "D")).date
    df = pd.DataFrame({"time": times, "open": o, "high": h, "low": l, "close": c, "volume": rng.integers(100, 1000, n),
                       "local_date": dates, "minute_of_day": 540 + bar * 5, "bar_in_day": bar,
                       "minutes_to_close": (per_day - bar - 1) * 5.0, "wdo_close": 5000.0})
    df["day_open"] = df.groupby("local_date")["open"].transform("first")
    now = times.astype("int64").to_numpy() + 5 * es.MIN_NS
    nxt = np.r_[day[1:] == day[:-1], False]
    return ps.Frame(5, df, None, None, day, now, np.ones(n, bool), np.zeros(n, bool), nxt)


def precheck(path: Path, ids: list[str] | None = None) -> dict:
    """Run in a fresh process. Returns {"file": [...problems of the whole file], "families": {id: [...]}}."""
    cfg = es.load_config()
    src = path.read_text(encoding="utf-8")
    probs = static_problems(src)
    if probs:
        return {"file": probs, "families": {}}
    try:
        fams = es.load_families(path.parent) if path.parent == es.FAMILY_DIR else []
        fams = [f for f in fams if f.id in set(re.findall(r"\"(E-\d{3,})\"", src))]
    except Exception as e:                                  # noqa: BLE001 - any import failure rejects the file
        return {"file": [f"import failed: {type(e).__name__}: {e}"], "families": {}}
    out: dict = {"file": [], "families": {}}
    got = [f.id for f in fams]
    if ids is not None and sorted(got) != sorted(ids):
        out["file"].append(f"family ids {got} differ from the ids given {ids}")
    if not fams:
        out["file"].append("no FAMILIES defined")
    fr = synthetic_frame()
    for f in fams:
        why = es.validate_family(f, cfg)
        if f.author != "agent":
            why.append("author must be 'agent'")
        if not why:
            try:
                for p in f.variants():
                    es.directions(f, fr, p)
                why += es.check_family(f, fr, cfg["checks"]["causality_cuts"], cfg["checks"]["window_sessions"])
            except Exception as e:                          # noqa: BLE001
                why.append(f"signal raised {type(e).__name__}: {str(e)[:200]}")
        out["families"][f.id] = why
    return out


# ---------------------------------------------------------------------------------------------
# The cycle
# ---------------------------------------------------------------------------------------------

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


def run_agent(prompt: str) -> dict:
    from lab.agents import build_argv, parse_output
    done = subprocess.run(build_argv(AGENT, AGENT_BUDGET_USD), input=prompt, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=AGENT_TIMEOUT_S, check=False)
    data = parse_output(done.stdout)
    log("agent", agent=AGENT, exit=done.returncode, cost_usd=data.get("total_cost_usd"), turns=data.get("num_turns"),
        is_error=data.get("is_error"), result=str(data.get("result", ""))[:800])
    if done.returncode != 0 or data.get("is_error"):
        text = f"{data.get('result', '')} {done.stderr}"
        if is_usage_limit(text):
            raise UsageLimit(text.strip()[:300])
        raise CycleError(f"{AGENT} failed: {str(data.get('result', ''))[:300]} {done.stderr[:300]}")
    return data


class UsageLimit(Exception):
    """The Claude plan's usage window is used up: not a fault of the conveyor. The hour is skipped, it never counts
    towards the automatic pause (2026-11-18: a 5-hour limit at 12:29 paused the conveyor for the whole afternoon)."""


def is_usage_limit(text: str) -> bool:
    t = text.lower()
    return ("hit your" in t and "limit" in t) or "usage limit" in t or "rate limit" in t or "resets " in t


def commit(paths: list[str], message: str) -> None:
    from lab.gitops import commit_paths
    commit_paths(ROOT, paths, message + TRAILER)


def _py(*args: str, timeout: float) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout, check=False)


def _rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def _reject_families(ids_why: dict[str, list[str]], batch: int, source: str) -> None:
    for fid, why in ids_why.items():
        es._append(OUT / "families.jsonl", {"family": fid, "title": None, "code_hash": None, "run": f"precheck-B-{batch:03d}",
                                            "screened_at_utc": _now(), "author": "agent", "rejected": why,
                                            "file": source})


def cycle() -> str:
    cfg = es.load_config()
    k, why = room(cfg)
    if not k:
        log("limit", reasons=why)
        return "limit"
    batch = next_batch()
    ids = next_ids(k)
    ctx = write_context(batch, ids, cfg)
    out = es.FAMILY_DIR / f"b{batch:03d}_agent.py"
    before = changed_paths()
    try:
        run_agent(f"Batch id: B-{batch:03d}\nFamily ids (exactly these, in order): {', '.join(ids)}\n"
                  f"Context file: {_rel(ctx)}\nOutput path: {_rel(out)}\n"
                  "Read the context file first. Write exactly one Python file at the output path.")
    except UsageLimit:
        if out.exists() and _rel(out) not in before:
            out.unlink()                                    # a half-written batch is redone from scratch next run
        raise
    guard(before, {_rel(out)}, AGENT)
    if not out.exists():
        raise CycleError(f"{AGENT} wrote no {_rel(out)}")
    chk = _py("-m", "b3.esteira_cycle", "precheck", _rel(out), "--ids", ",".join(ids), timeout=900)
    try:
        res = json.loads(chk.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        res = {"file": [f"precheck crashed or timed out: {chk.stderr[-400:]}"], "families": {}}
    if res["file"]:
        REJECTED_DIR.mkdir(parents=True, exist_ok=True)
        dest = REJECTED_DIR / out.name
        out.replace(dest)
        _reject_families({i: res["file"] for i in ids}, batch, _rel(dest))
        commit([_rel(dest), _rel(ctx), _rel(OUT / "families.jsonl")],
               f"exp(esteira): batch B-{batch:03d} rejected by the file check (not run)")
        log("batch_rejected", batch=batch, problems=res["file"])
        return "rejected"
    bad = {fid: w for fid, w in res["families"].items() if w}
    good = [fid for fid, w in res["families"].items() if not w]
    if bad:
        _reject_families(bad, batch, _rel(out))
    commit([_rel(out), _rel(ctx), _rel(OUT / "families.jsonl")],
           f"exp(esteira): register batch B-{batch:03d} ({len(good)} families, {len(bad)} rejected by the checks; "
           "agent, ex ante)")
    log("registered", batch=batch, families=good, rejected=bad)
    if not good:
        return "all_rejected"
    sc = _py("-m", "b3.esteira", "screen", *sum((["--family", g] for g in good), []), timeout=5400)
    log("screen", batch=batch, exit=sc.returncode, out=sc.stdout[-2500:], err=sc.stderr[-800:])
    if sc.returncode != 0:
        raise CycleError(f"screen of batch B-{batch:03d} failed: {sc.stderr[-500:]}")
    runs = [Path(x.strip()) for x in sc.stdout.splitlines() if x.strip().endswith(".json") and "runs" in x]
    paths = [_rel(OUT / "ledger.jsonl"), _rel(OUT / "families.jsonl"), _rel(OUT / "selected.json"), _rel(LOG)]
    paths += [_rel(p if p.is_absolute() else ROOT / p) for p in runs]
    selected = [s["variant"] for s in es._selected() if s.get("run") and any(s["run"] in str(r) for r in runs)]
    commit(paths, f"exp(esteira): batch B-{batch:03d} screened on exploration: "
                  f"{len(selected)} selected" + (f" ({', '.join(selected)})" if selected else ""))
    log("batch_done", batch=batch, screened=good, selected=selected)
    exit_menu(good)
    return "done"


def exit_menu(ids: list[str]) -> None:
    """Owner 2026-11-18 ('teste tudo, stop loss, take profit, novas estrategias'): every new family also runs the exit
    menu (b3/config/exit_menu.json). It writes under ops/state/exit_menu only; a failure is logged, never a cycle error."""
    if not ids:
        return
    args = ["-m", "b3.exit_menu", "run"] + [x for i in ids for x in ("--family", i)]
    try:
        done = _py(*args, timeout=3600)
        picks = [ln for ln in done.stdout.splitlines() if " pick " in ln]
        log("exit_menu", exit=done.returncode, families=ids, picks=picks, out=done.stdout[-300:], err=done.stderr[-300:])
    except Exception as e:                                  # noqa: BLE001
        log("exit_menu", exit=-1, families=ids, error=repr(e)[:300])


def after_error(error: Exception) -> None:
    log("cycle_error", error=str(error)[:1500])
    ends = [r["event"] for r in _log_rows() if r["event"] in ("cycle_error", "cycle_end")]
    if ends[-MAX_CONSECUTIVE_ERRORS:] == ["cycle_error"] * MAX_CONSECUTIVE_ERRORS:
        STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
        STOP_FILE.write_text(f"paused automatically {_now()} after {MAX_CONSECUTIVE_ERRORS} cycle errors in a row; "
                             f"last: {error}\n", encoding="utf-8")
        log("paused", reason=f"{MAX_CONSECUTIVE_ERRORS} consecutive cycle errors")


def status() -> dict:
    cfg = es.load_config()
    k, why = room(cfg)
    st = es.status()
    return {"paused": STOP_FILE.exists(), "families_today": families_today(), "agent_cost_today_usd": round(cost_today(), 2),
            "next_batch_size": k, "limit_reasons": why, "families_screened": st["families_screened"],
            "variants_read": st["variants_read"], "selected": [s["variant"] for s in st["selected"]]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="b3.esteira_cycle")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    c = sub.add_parser("cycle")
    c.add_argument("--max", type=int, default=1)
    c.add_argument("--minutes", type=float, default=None, help="start no new batch after this many minutes")
    p = sub.add_parser("precheck")
    p.add_argument("file")
    p.add_argument("--ids")
    a = ap.parse_args(argv)
    if a.cmd == "status":
        print(json.dumps(status(), indent=1))
        return 0
    if a.cmd == "precheck":
        res = precheck(ROOT / a.file, a.ids.split(",") if a.ids else None)
        print(json.dumps(res))
        return 0
    if STOP_FILE.exists():
        print(f"paused: {STOP_FILE} exists")
        return 0
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        print(f"another conveyor cycle holds {LOCK}; not starting a second one")
        return 2
    try:
        os.write(fd, str(os.getpid()).encode())
        t0 = datetime.now(timezone.utc)
        for _ in range(a.max):
            if a.minutes is not None and (datetime.now(timezone.utc) - t0).total_seconds() > a.minutes * 60:
                log("time_budget", minutes=a.minutes)
                break
            if STOP_FILE.exists():
                log("paused_by_file")
                break
            try:
                outcome = cycle()
            except UsageLimit as e:
                log("usage_limit", detail=str(e)[:300])     # skip this hour; the next hourly run tries again
                print(f"usage limit, skipping this run: {e}")
                return 0
            except Exception as e:                          # noqa: BLE001 - record, maybe pause, never retry here
                after_error(e)
                return 1
            log("cycle_end", outcome=outcome)
            if outcome == "limit":
                break
        return 0
    finally:
        os.close(fd)
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
