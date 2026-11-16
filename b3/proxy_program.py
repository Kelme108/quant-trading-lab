"""The agent research programs (plan item 4 and the project stop criterion): how many agent-proposed rules may still
be registered, when the program stops, the proposal format, and the context file the research agent reads
(EXPLORATION facts only: validation and final-test numbers never reach it).

Two lanes (LANES): "proxies" (b3/config/proxy_program.json, 2026-11-14..16, ended) and "b3" (WIN/WDO from the Clear
demo, b3/config/b3_program.json, from 2026-11-16; owner decision D5 a of docs/plano-b3-reuso.md). active_lane() is the
one b3/proxy_pipeline.py runs. Rule ids (P-NNN) and the rule registry b3/proxy_rules/ are shared by both lanes.

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
LANES = {
    "proxies": {"program": PROGRAM_PATH, "proposals": PROPOSALS, "context": CONTEXT_DIR, "results": RESULTS,
                "ledger": LEDGER, "scope": ROOT / "b3" / "config" / "scope_proxies.json", "dir": ROOT / "research" / "proxies"},
    "b3": {"program": ROOT / "b3" / "config" / "b3_program.json", "proposals": ROOT / "research" / "b3" / "proposals",
           "context": ROOT / "research" / "b3" / "context", "results": ROOT / "research" / "b3" / "results",
           "ledger": ROOT / "research" / "b3" / "ledger.jsonl", "scope": ROOT / "b3" / "config" / "scope_b3.json",
           "dir": ROOT / "research" / "b3"},
}


def active_lane() -> str:
    """b3 once its program is approved (2026-11-16); the proxy program ended then."""
    path = LANES["b3"]["program"]
    try:
        return "b3" if json.loads(path.read_text(encoding="utf-8")).get("approved_by_owner") is True else "proxies"
    except (OSError, ValueError):
        return "proxies"


def lane_of(program: dict) -> str:
    return program.get("lane", "proxies")

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
    paths = LANES[lane_of(cfg)]
    today = today or datetime.now(timezone.utc).date()
    props = proposals(paths["proposals"]) if props is None else props
    ledger = ledger_rows(paths["ledger"]) if ledger is None else ledger
    first = _num(cfg["first_counted_rule"])
    # only rules that were registered and run count; invalid, failed or interrupted proposals never read any data
    counted = [p for p in props if _num(p["rule_id"]) >= first and p.get("status") == "registered"]
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
    if today >= xd and not cfg["exchange_data"].get("met"):
        notices.append(f"exchange-data deadline {xd} reached: without a BR broker demo or bought history, "
                       "research continues on the proxies only (plan item 1)")
    return Status(str(today), sorted(ids), week, val, fin, str(deadline), str(xd), not reasons, reasons, notices)


def next_rule_id(props: list[dict] | None = None, builtin: list[str] | None = None) -> str:
    from b3.proxy_rules import RULES
    used = [_num(r) for r in (builtin if builtin is not None else list(RULES))]
    if props is None:                          # the registry is shared: count proposals of every lane
        props = [p for lane in LANES.values() for p in proposals(lane["proposals"])]
    used += [_num(p["rule_id"]) for p in props]
    return f"P-{max(used) + 1:03d}"


def assigned_timeframe(rule_id: str, program: dict | None = None) -> int | None:
    """Owner 2026-11-16: half of the new WIN/WDO rules on a 1-minute clock, half on 5 minutes, alternating from the
    first counted rule (P-013 is 1 minute, P-014 5 minutes, ...). None when the program has no alternation."""
    cfg = program or load_program()
    alt = cfg.get("scope", {}).get("alternate_timeframes_min")
    if not alt:
        return None
    k = _num(rule_id) - _num(cfg.get("first_counted_rule", rule_id))
    return int(alt[k % len(alt)]) if k >= 0 else None


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
    least = sc.get("min_expected_trades_per_year")
    if least and p["expected_trades_per_year"] < least:
        problems.append(f"expected_trades_per_year must be at least {least} per market (owner: rules with many trades)")
    want = assigned_timeframe(rule_id, cfg)
    if want is not None and p["timeframe_min"] != want:
        problems.append(f"timeframe_min must be {want} for {rule_id} (owner: new rules alternate 1 and 5 minutes)")
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


def _exploration_table(results: Path = RESULTS) -> list[str]:
    from b3.proxy_rules import RULES
    latest: dict = {}
    if results.exists():
        for f in sorted(results.glob("*-exploration-*.json")):
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


FACTS_B3 = """\
Exploration facts for WIN and WDO (research/b3/anatomy.json, data_quality.json; EXPLORATION split only,
2021-11-16 to 2024-06-30, Clear demo continuous $N series, Sao Paulo session 09:00-18:25 WIN / 18:30 WDO, 17:55 /
18:00 in the US summers of 2022 and 2023):
- Costs per round trip (b3/costs.py, 1 contract): WIN ~0.011% of the notional in the base scenario (BRL 0.25 fees +
  1 tick per side), ~0.02% conservative; WDO ~0.0235% base (the 0.5-point tick is ~0.009% of the price), ~0.045%
  conservative. A stop fill pays 1 more tick (2 conservative).
- Median move vs the base cost: WIN 5 min 4.7x, 15 min 8x, 30 min 11.4x, 60 min 16.5x, 120 min 23.8x; WDO 5 min
  1.6x, 15 min 2.8x, 30 min 3.9x, 60 min 5.6x, 120 min 8.2x. WDO needs long holds or rare, large moves.
- The 11 proxy rules P-001..P-011, re-read on WIN and WDO (table below), made at most ~0.03% gross per trade; P-004
  (rest-of-day momentum, last half hour) passed WIN exploration and did not repeat on validation. WDO lost on
  almost every rule.
- The 47 crypto strategies on 15-minute candles (Freqtrade, long only, built for 24-hour markets) were screened on
  both contracts (research/b3/crypto_screen.json, exploration only): 56 of 94 reads made no trade at all, none passed
  the gates. Owner 2026-11-16: only 1, 5 and 15-minute rules, focus on 1 and 5 minutes.
- 1-minute bars exist for the whole period (scope allows a 1-minute entry clock).
- Frequency vs edge on WIN exploration (base cost): P-005 VWAP trend 1m ~4,480 trades/yr, -0.0135% gross per trade,
  -85% net; P-003 noise area ~420/yr, +0.003%; P-001 opening range ~247/yr, +0.014%; P-004 rest of day ~246/yr,
  +0.031% (the only exploration pass). Frequent rules die on the round trip (~0.011% WIN, ~0.0235% WDO): a rule with
  2+ trades per session needs a mechanism whose AVERAGE trade still moves 3x the cost, e.g. by trading only the
  sessions' active windows, by holding 10-60 minutes instead of 1-5, or by filtering for conditions where the move
  is large. Flipping on every small signal (P-005) is what fails.
"""


def write_context(rule_id: str, st: Status | None = None, program: dict | None = None) -> Path:
    cfg = program or load_program()
    if lane_of(cfg) == "b3":
        return _write_context_b3(rule_id, st or status(program=cfg), cfg)
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


def _write_context_b3(rule_id: str, st: Status, cfg: dict) -> Path:
    paths = LANES["b3"]
    variants = len({(r["rule"], r["symbol"]) for r in ledger_rows(paths["ledger"]) if r["split"] == "exploration"})
    sc = cfg["scope"]
    screen = []
    sp = paths["dir"] / "crypto_screen.json"
    if sp.exists():
        data = json.loads(sp.read_text(encoding="utf-8"))
        rows = sorted([r for r in data.get("rows", []) if r.get("mean_gross_pct") is not None and r.get("gross_over_cost") is not None],
                      key=lambda r: -r["gross_over_cost"])[:12]
        screen = ["## Crypto strategies on WIN/WDO: highest gross per trade (exploration only)", "",
                  "| Strategy | Market | Trades | Gross/trade | Gross / base cost |", "|---|---|---|---|---|"]
        screen += [f"| {r['strategy']} | {r['symbol']} | {r['trades']} | {r['mean_gross_pct']:.4f}% | {r['gross_over_cost']:.1f}x |"
                   for r in rows]
    text = "\n".join([
        f"# Context for {rule_id} ({datetime.now(timezone.utc).isoformat(timespec='seconds')})", "",
        "WIN (mini Ibovespa) and WDO (mini dollar) futures, real B3 data from the Clear demo (b3/markets.py B3_MARKETS, "
        "b3/b3_data.py). Engine: b3/backtest.py (the fill rules of the live robot); runner b3/proxy_research.py, b3 lane.",
        f"Scope: markets {sc['markets']}, timeframe {sc['timeframes_min']} minutes, median hold "
        f"{sc['hold_min_range'][0]}-{sc['hold_min_range'][1]} minutes, long and short, a stop on every entry, flat "
        "before the session close (never overnight). Rules are written like b3/strategies/proxies.py and bound to a "
        "market with .on(\"WIN\"); self.market.tick_size is 5 points (WIN) or 0.5 point (WDO).",
        f"Gates (b3/config/gates_b3.json): >= 30 trades; compounded net > 1% x (1 + 0.1 x variants) in base AND "
        f"conservative cost; net without the best trade > 0; drawdown <= 25%; >= 60% positive years. Rule x market "
        f"pairs already read on WIN/WDO exploration: {variants}, so the bar is now {1 + 0.1 * variants:.1f}% and every "
        "market you list raises it by 0.1% for all later rules: list only the markets your mechanism is about.",
        f"Program: {len(st.counted_rules)} agent rules so far ({', '.join(st.counted_rules) or 'none'}); the program "
        f"stops after {cfg['stop_after_rules_without_validation_pass']} rules with no validation pass.", "",
        *([f"**Timeframe of {rule_id}: {assigned_timeframe(rule_id, cfg)} minutes, fixed.** Owner 2026-11-16: half of the "
           "new rules on a 1-minute clock and half on 5 minutes, alternating; a proposal on any other timeframe is "
           "refused.", ""] if assigned_timeframe(rule_id, cfg) is not None else []),
        *([f"**Frequency: at least {sc['min_expected_trades_per_year']} trades per year per market (about 2 per session), "
           "fixed.** Owner 2026-11-16: 'quero regras com bastante trades'. A proposal expecting fewer is refused. The hard "
           "part (see the frequency facts below): the frequent rules tried so far made LESS per trade than the round trip.", ""]
          if sc.get("min_expected_trades_per_year") else []),
        FACTS_B3, "## Rules already explored on WIN/WDO (exploration split only; the crypto strategies are below)", "",
        *[ln for ln in _exploration_table(paths["results"]) if not ln.startswith("| C-")], "", *screen, "",
    ])
    paths["context"].mkdir(parents=True, exist_ok=True)
    path = paths["context"] / f"{rule_id}.md"
    path.write_text(text, encoding="utf-8")
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["status"])
    ap.parse_args(argv)
    print(json.dumps(asdict(status(program=load_program(LANES[active_lane()]["program"]))), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
