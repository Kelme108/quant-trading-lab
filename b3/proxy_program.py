"""The proxy research program (plan items 4 and the project stop criterion, b3/config/proxy_program.json):
how many agent-proposed rules may still be registered, when the program stops, the proposal format, and the
context file the research agent reads (EXPLORATION facts only: validation and final-test numbers never reach it).

    python -m b3.proxy_program status
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRAM_PATH = ROOT / "b3" / "config" / "proxy_program.json"
PROPOSALS = ROOT / "research" / "proxies" / "proposals"
CONTEXT_DIR = ROOT / "research" / "proxies" / "context"
RESULTS = ROOT / "research" / "proxies" / "results"
LEDGER = ROOT / "research" / "proxies" / "ledger.jsonl"

PROPOSAL_KEYS = {
    "rule_id": str, "title": str, "class_name": str, "file_stem": str, "markets": list, "timeframe_min": int,
    "ex_ante_rule": str, "parameters": dict, "mechanism": str, "why_gross_beats_3x_cost": str,
    "expected_trades_per_year": int, "expected_median_hold_min": int, "novelty_vs_tried": str, "sources": list,
    "data_visible_at_proposal": str,
}
PIPELINE_KEYS = {"status", "registered_at_utc", "problems"}     # stamped by b3/proxy_pipeline.py, not the agent


def load_program(path: Path = PROGRAM_PATH) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if cfg.get("approved_by_owner") is not True:
        raise RuntimeError(f"{path.name} is not approved by the owner")
    return cfg


def _num(rule_id: str) -> int:
    m = re.fullmatch(r"P-(\d{3})", rule_id)
    if not m:
        raise ValueError(f"bad rule id {rule_id!r}")
    return int(m.group(1))


def proposals(folder: Path = PROPOSALS) -> list[dict]:
    if not folder.exists():
        return []
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(folder.glob("P-[0-9][0-9][0-9].json"))]


def ledger_rows(path: Path = LEDGER) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


@dataclass
class Status:
    today: str
    counted_rules: list[str]
    registered_this_week: int
    validation_passes: list[tuple[str, str]]
    final_test_passes: list[tuple[str, str]]
    project_deadline: str
    exchange_data_deadline: str
    can_register: bool
    reasons: list[str] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)


def status(today: date | None = None, *, program: dict | None = None, props: list[dict] | None = None,
           ledger: list[dict] | None = None) -> Status:
    cfg = program or load_program()
    today = today or datetime.now(timezone.utc).date()
    props = proposals() if props is None else props
    ledger = ledger_rows() if ledger is None else ledger
    first = _num(cfg["first_counted_rule"])
    counted = [p for p in props if _num(p["rule_id"]) >= first and p.get("status") != "invalid"]
    ids = {p["rule_id"] for p in counted}
    monday = today - timedelta(days=today.weekday())
    week = sum(1 for p in counted if p.get("registered_at_utc")
               and monday <= datetime.fromisoformat(p["registered_at_utc"]).date() <= today)
    val = sorted({(r["rule"], r["symbol"]) for r in ledger
                  if r["split"] == "validation" and r["decision"] == "passed" and r["rule"] in ids})
    fin = sorted({(r["rule"], r["symbol"]) for r in ledger if r["split"] == "final_test" and r["decision"] == "passed"})
    started = date.fromisoformat(cfg["started"])
    ps = cfg["project_stop"]
    deadline = started + timedelta(days=ps["days"])
    reasons, notices = [], []
    if not fin and (len(counted) >= ps["new_rules"] or today >= deadline):
        reasons.append(f"project stop (owner decision a): {len(counted)} new rules / {(today - started).days} days "
                       f"without a final-test pass -> the project becomes a study; the owner decides what comes next")
    if len(counted) >= cfg["stop_after_rules_without_validation_pass"] and not val:
        reasons.append(f"{len(counted)} new rules and none passed validation: stop proposing (plan item 4)")
    if week >= cfg["max_new_rules_per_week"]:
        reasons.append(f"{week} rules already registered this week (cap {cfg['max_new_rules_per_week']})")
    if val:
        notices.append(f"passed validation, final test locked until the owner unlocks it: {val}")
    xd = date.fromisoformat(cfg["exchange_data"]["deadline"])
    if today >= xd:
        notices.append(f"exchange-data deadline {xd} reached: without a BR broker demo or bought history, "
                       "research continues on the proxies only (plan item 1)")
    return Status(str(today), sorted(ids), week, val, fin, str(deadline), str(xd), not reasons, reasons, notices)


def next_rule_id(props: list[dict] | None = None, builtin: list[str] | None = None) -> str:
    from b3.proxy_rules import RULES
    used = [_num(r) for r in (builtin if builtin is not None else list(RULES))]
    used += [_num(p["rule_id"]) for p in (proposals() if props is None else props)]
    return f"P-{max(used) + 1:03d}"


def validate_proposal(p: dict, rule_id: str, program: dict | None = None, scope_markets: list[str] | None = None) -> list[str]:
    cfg = program or load_program()
    sc = cfg["scope"]
    problems = []
    for k, t in PROPOSAL_KEYS.items():
        if k not in p:
            problems.append(f"missing key {k}")
        elif not isinstance(p[k], t) or isinstance(p[k], bool):
            problems.append(f"{k} must be {t.__name__}")
    extra = set(p) - set(PROPOSAL_KEYS) - PIPELINE_KEYS
    if extra:
        problems.append(f"unknown keys {sorted(extra)}")
    if problems:
        return problems
    num = rule_id.split("-")[1]
    if p["rule_id"] != rule_id:
        problems.append(f"rule_id must be {rule_id}")
    if not re.fullmatch(rf"p{num}_[a-z0-9_]{{3,40}}", p["file_stem"]):
        problems.append(f"file_stem must look like p{num}_<snake_name>")
    if not re.fullmatch(r"[A-Z][A-Za-z0-9]{3,60}", p["class_name"]):
        problems.append("class_name must be CamelCase")
    allowed = set(sc["markets"]) & set(scope_markets or sc["markets"])
    if not p["markets"] or not set(p["markets"]) <= allowed:
        problems.append(f"markets must be a non-empty subset of {sorted(allowed)}")
    if p["timeframe_min"] not in sc["timeframes_min"]:
        problems.append(f"timeframe_min must be one of {sc['timeframes_min']}")
    lo, hi = sc["hold_min_range"]
    if not lo <= p["expected_median_hold_min"] <= hi:
        problems.append(f"expected_median_hold_min must be within {lo}-{hi} minutes")
    if len(p["ex_ante_rule"]) < 100:
        problems.append("ex_ante_rule is too short to be unambiguous")
    if not p["sources"] or not all(isinstance(s, dict) and str(s.get("url", "")).startswith("https://") for s in p["sources"]):
        problems.append("sources must be objects with an https url")
    return problems


# ---------------------------------------------------------------------------------------------
# Context for the research agent: exploration only
# ---------------------------------------------------------------------------------------------

FACTS = """\
Exploration facts (research/proxies/anatomy.json, failure_anatomy.json, event_anatomy.json, tick_fidelity.json;
all from the EXPLORATION split):
- Base round trip 0.01% of the notional on every index proxy (conservative 0.02%, which also decides). Every stop
  fill pays 0.005% more (0.01% conservative): the ticks jump past stops.
- Median move vs the base cost: 5 min 3.6-6.4x, 15 min 6.3-10.9x, 30 min 8.8-15x, 60 min 12-21x (USTEC and US2000
  move most). A rule captures a small fraction of the move: P-001..P-007 made 0.002-0.03% gross per trade
  (0.2-3x cost) except P-001/P-003 on USTEC (5-6x, only 1.5 years of exploration).
- Longs made more than shorts in almost every index rule (part of it is the market's rise, not the rule).
- The previous day's volatility did not separate good and bad days in a stable way (P-007 failed).
- Scheduled events (FOMC 14:00 NY, CPI and payrolls 08:30 NY, b3/config/events_us.json) move the indices 15-125x
  the cost, but none of 5 fixed directional rules on them (pre-FOMC drift, FOMC reaction continuation at 15 and
  30 minutes, CPI/NFP morning continuation, DE40 release continuation) reached 3x the cost on two markets.
- 1-minute rules and FX are out of scope; so is USDBRL.
"""


def _exploration_table() -> list[str]:
    from b3.proxy_rules import RULES
    latest: dict = {}
    if RESULTS.exists():
        for f in sorted(RESULTS.glob("*-exploration-*.json")):
            d = json.loads(f.read_text(encoding="utf-8"))
            if d.get("split") == "exploration":
                latest[(d["rule"], d["symbol"])] = d
    lines = ["| Rule | Name | TF | Market | Exploration decision | Trades/yr | Gross/trade (base) |", "|---|---|---|---|---|---|---|"]
    for (rule, sym), d in sorted(latest.items()):
        b = d["scenarios"]["base"]
        name = RULES[rule].name if rule in RULES else d.get("strategy", "")
        lines.append(f"| {rule} | {name} | {RULES[rule].timeframe_min if rule in RULES else '?'}m | {sym} | "
                     f"{d['gates']['decision']} | {b.get('trades_per_year', 0):.0f} | {b.get('mean_gross_pct', 0):.4f}% |")
    return lines


def write_context(rule_id: str, st: Status | None = None, program: dict | None = None) -> Path:
    cfg = program or load_program()
    st = st or status(program=cfg)
    variants = len({(r["rule"], r["symbol"]) for r in ledger_rows() if r["split"] == "exploration"})
    sc = cfg["scope"]
    text = "\n".join([
        f"# Context for {rule_id} ({datetime.now(timezone.utc).isoformat(timespec='seconds')})", "",
        "Proxy markets for WIN/WDO-like day trading (b3/markets.py). Engine: b3/backtest.py; runner b3/proxy_research.py.",
        f"Scope: markets {sc['markets']}, timeframe {sc['timeframes_min']} minutes, median hold "
        f"{sc['hold_min_range'][0]}-{sc['hold_min_range'][1]} minutes, long and short, a stop on every entry, flat "
        "before the session close (never overnight).",
        f"Gates (b3/config/gates_proxies.json): >= 30 trades; compounded net > 1% x (1 + 0.1 x variants) in base AND "
        f"conservative cost; net without the best trade > 0; drawdown <= 25%; >= 60% positive years. Rule x market "
        f"pairs already read on exploration: {variants}, so the bar is now {1 + 0.1 * variants:.1f}% and every market "
        "you list raises it by 0.1% for all later rules: list only the markets your mechanism is about.",
        f"Program: {len(st.counted_rules)} agent rules so far ({', '.join(st.counted_rules) or 'none'}); the program "
        f"stops after {cfg['stop_after_rules_without_validation_pass']} rules with no validation pass.", "",
        FACTS, "## Rules already explored (exploration split only)", "", *_exploration_table(), "",
    ])
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    path = CONTEXT_DIR / f"{rule_id}.md"
    path.write_text(text, encoding="utf-8")
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["status"])
    ap.parse_args(argv)
    print(json.dumps(asdict(status()), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
