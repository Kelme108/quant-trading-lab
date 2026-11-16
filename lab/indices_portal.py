"""Portal data for the index-proxy research (docs/plano-portal-proxies.md): one JSON for GET /api/indices.

Read-only: it reads research/proxies/*, b3/config/* and the pipeline log, and asks git (read-only) when a
proposal was committed. Every number comes from those files; nothing is recomputed from prices. Text written
by agents is clipped and treated as untrusted by the page (textContent only).
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROXIES = ROOT / "research" / "proxies"
SCENARIOS = ("optimistic", "base", "conservative", "stress")
SPLITS = ("exploration", "validation", "final_test")
TEXT_LIMIT = 4000
TRADE_FILE = re.compile(r"^(recalc/)?P-\d{3}-[A-Z0-9]{2,10}-(exploration|validation|final_test)(-[0-9T-]{17})?\.json$")
CYCLE_HOURS = 3

# The page reads these paths; a test keeps the list equal to the page's IX_CONTRACT.
INDICES_CONTRACT = (
    "generated_at", "program", "funnel", "summary", "board", "rules", "cycles", "markets", "measurements", "alerts",
)

# P-001..P-007 were written by hand (b3/strategies/proxies.py, 2026-11-14); a short description for the page.
BUILTIN = {
    "P-001": ("Rompimento da faixa dos primeiros 30 minutos", "Entra no primeiro fechamento fora da faixa dos 30 primeiros minutos, stop do outro lado, uma entrada por dia (Crabel; Zarattini, Barbon e Aziz 2024)."),
    "P-002": ("Primeira meia hora prevê a última", "O retorno do fechamento anterior até 30 min após a abertura dá a direção dos últimos 30 min (Gao, Han, Li e Zhou 2018)."),
    "P-003": ("Momentum fora da área de ruído", "Compra acima e vende abaixo da área de ruído em volta da abertura, revisando a cada meia hora; sai ao voltar para dentro ou cruzar a VWAP (Zarattini, Aune e Barbon 2024)."),
    "P-004": ("Movimento do dia prevê a última meia hora", "O retorno do fechamento anterior até 30 min antes do fim dá a direção dos últimos 30 min (Baltussen, Da, Lammers e Martens 2021)."),
    "P-005": ("Tendência pela VWAP em 1 minuto", "Comprado acima da VWAP da sessão, vendido abaixo, em barras de 1 minuto (Zarattini e Aziz 2023)."),
    "P-006": ("Direção da primeira vela de 5 minutos", "Segue a direção da primeira vela de 5 minutos, stop na mínima ou máxima dela, até o fim do dia (Zarattini e Aziz 2023)."),
    "P-007": ("P-004 só depois de um dia agitado", "A mesma regra da P-004, só quando o dia anterior foi agitado (amplitude no terço superior dos 20 dias anteriores)."),
}

_cache: dict = {}


# ---------------------------------------------------------------------------------------------
# readers
# ---------------------------------------------------------------------------------------------

def _json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _jsonl(path: Path) -> list[dict]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _clip(value, limit: int = TEXT_LIMIT) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= limit else text[:limit] + "…"


def _git_added_all(folder: Path, root: Path) -> dict[str, dict]:
    """{file name: {commit, at}} of the commit that first added each file under `folder`, in ONE git call,
    cached for 10 minutes; empty outside git."""
    key = ("git", str(folder))
    hit = _cache.get(key)
    if hit and time.monotonic() - hit[0] < 600:
        return hit[1]
    out: dict[str, dict] = {}
    try:
        text = subprocess.run(["git", "log", "--diff-filter=A", "--name-only", "--format=@%h %cI", "--",
                               folder.relative_to(root).as_posix()], cwd=root, capture_output=True, text=True,
                              timeout=20).stdout
        commit = None
        for line in text.splitlines():
            if line.startswith("@"):
                h, at = line[1:].split(" ", 1)
                commit = {"commit": h, "at": at}
            elif line.strip() and commit:
                out[Path(line.strip()).name] = commit          # git log is newest first: keep the oldest add
    except (OSError, ValueError, subprocess.SubprocessError):
        out = {}
    _cache[key] = (time.monotonic(), out)
    return out


def _results(root: Path) -> list[dict]:
    out = []
    for f in sorted((root / "research" / "proxies" / "results").glob("*.json")):
        d = _json(f)
        if isinstance(d, dict) and d.get("rule") and d.get("split"):
            d["_file"] = f.name
            out.append(d)
    return out


def _metrics(m: dict | None) -> dict | None:
    if not m:
        return None
    keys = ("trades", "trades_per_year", "mean_gross_pct", "mean_net_pct", "net_return_pct", "net_return_excl_best_pct",
            "max_drawdown_pct", "profit_factor", "win_rate_pct", "daily_sharpe_annualised", "positive_years_share",
            "long_trades", "short_trades", "median_hold_min")
    out = {k: m.get(k) for k in keys}
    if out.get("profit_factor") == float("inf"):
        out["profit_factor"] = None
    out["per_year_return_pct"] = m.get("per_year_return_pct") or {}
    out["exit_reasons"] = m.get("exit_reasons") or {}
    return out


def _read(d: dict, root: Path) -> dict:
    trades = root / "research" / "proxies" / "trades" / d["_file"]
    recalc = root / "research" / "proxies" / "trades" / "recalc" / f"{d['rule']}-{d['symbol']}-{d['split']}.json"
    cost = d.get("cost_round_trip_base_pct") or 0.01
    base = d["scenarios"].get("base") or {}
    return {
        "rule": d["rule"], "symbol": d["symbol"], "split": d["split"], "file": d["_file"],
        "read_at": d.get("read_at_utc"), "start": str(d.get("start_utc", ""))[:10], "end": str(d.get("end_utc", ""))[:10],
        "decision": d["gates"]["decision"], "fails": d["gates"].get("fails", []), "bar_pct": d["gates"].get("net_bar_pct"),
        "prior_variants": d.get("prior_variants"), "cost_base_pct": cost,
        "stop_slippage_base_pct": d.get("stop_slippage_base_pct"),
        "days_skipped_incomplete": d.get("days_skipped_incomplete"),
        "gross_x_cost": (base.get("mean_gross_pct") / cost) if base.get("mean_gross_pct") is not None and cost else None,
        "scenarios": {s: _metrics(d["scenarios"].get(s)) for s in SCENARIOS},
        "trades_file": d["_file"] if trades.exists() else (f"recalc/{recalc.name}" if recalc.exists() else None),
        "trades_recalculated": not trades.exists() and recalc.exists(),
    }


# ---------------------------------------------------------------------------------------------
# sections
# ---------------------------------------------------------------------------------------------

def _program(root: Path, now: datetime) -> dict:
    """The ACTIVE agent program (WIN/WDO since 2026-11-16, b3/config/b3_program.json; the proxy one before)."""
    lane = "b3" if (_json(root / "b3" / "config" / "b3_program.json") or {}).get("approved_by_owner") is True else "proxies"
    cfg = _json(root / "b3" / "config" / ("b3_program.json" if lane == "b3" else "proxy_program.json")) or {}
    lane_dir = root / "research" / ("b3" if lane == "b3" else "proxies")
    try:
        from b3 import proxy_program as prog
        st = prog.status(now.date(), program=cfg, props=prog.proposals(lane_dir / "proposals"),
                         ledger=prog.ledger_rows(lane_dir / "ledger.jsonl"))
        status = {k: getattr(st, k) for k in ("counted_rules", "registered_this_week", "validation_passes",
                                               "final_test_passes", "project_deadline", "exchange_data_deadline",
                                               "can_register", "reasons", "notices")}
    except Exception as error:  # the page still renders the rest
        status = {"error": f"{type(error).__name__}: {error}"}
    stop = root / "ops" / "state" / "STOP_PROXY_CYCLES"
    paused = None
    if stop.exists():
        try:
            paused = _clip(stop.read_text(encoding="utf-8").strip(), 500) or "arquivo de pausa criado à mão"
        except OSError:
            paused = "arquivo de pausa presente"
    started = cfg.get("started")
    return {
        "config": {k: cfg.get(k) for k in ("started", "first_counted_rule", "max_new_rules_per_week",
                                           "stop_after_rules_without_validation_pass", "project_stop", "exchange_data",
                                           "scope", "agents")},
        "lane": lane, "lane_label": "WIN e WDO (B3, conta demo da Clear)" if lane == "b3" else "Substitutos (índices dos EUA e DAX)",
        "ended": [{"lane": "proxies", "label": "Substitutos", "ended_on": "2026-11-16", "rules": "P-008, P-009, P-011"}] if lane == "b3" else [],
        "status": status, "paused": paused, "stop_file": "ops/state/STOP_PROXY_CYCLES",
        "days_since_start": (now.date() - date.fromisoformat(started)).days if started else None,
        "today": now.date().isoformat(),
    }


def _board(reads: list[dict]) -> list[dict]:
    latest: dict = {}
    for r in sorted(reads, key=lambda x: x["read_at"] or ""):
        latest[(r["rule"], r["symbol"], r["split"])] = r
    rows: dict = {}
    for (rule, sym, split), r in latest.items():
        row = rows.setdefault((rule, sym), {"rule": rule, "symbol": sym})
        b, c = r["scenarios"]["base"] or {}, r["scenarios"]["conservative"] or {}
        row[split] = {"decision": r["decision"], "fails": r["fails"], "bar_pct": r["bar_pct"], "file": r["file"],
                      "trades": b.get("trades"), "trades_per_year": b.get("trades_per_year"),
                      "mean_gross_pct": b.get("mean_gross_pct"), "gross_x_cost": r["gross_x_cost"],
                      "net_base_pct": b.get("net_return_pct"), "net_conservative_pct": c.get("net_return_pct"),
                      "max_drawdown_base_pct": b.get("max_drawdown_pct"), "positive_years_share": b.get("positive_years_share"),
                      "start": r["start"], "end": r["end"]}
    order = {s: i for i, s in enumerate(SPLITS)}
    for row in rows.values():
        reached = [s for s in SPLITS if s in row]
        row["furthest"] = max(reached, key=order.get) if reached else None
        row["passed_all_read"] = all(row[s]["decision"] == "passed" for s in reached)
    return sorted(rows.values(), key=lambda r: (r["rule"], r["symbol"]))


def _funnel(ledger: list[dict]) -> list[dict]:
    out = []
    for split in SPLITS:
        pairs = {(r["rule"], r["symbol"]) for r in ledger if r.get("split") == split}
        passed = {(r["rule"], r["symbol"]) for r in ledger if r.get("split") == split and r.get("decision") == "passed"}
        out.append({"split": split, "read": len(pairs), "passed": len(passed)})
    return out


def _rules(root: Path, reads: list[dict]) -> list[dict]:
    try:
        from b3.proxy_rules import RULES
    except Exception:
        RULES = {}
    props = {p.stem: _json(p) for p in sorted((root / "research" / "proxies" / "proposals").glob("P-[0-9][0-9][0-9].json"))}
    ids = sorted(set(BUILTIN) | set(props) | {r["rule"] for r in reads})
    added = _git_added_all(root / "research" / "proxies" / "proposals", root) if props else {}
    out = []
    for rid in ids:
        cls = RULES.get(rid)
        p = props.get(rid) if isinstance(props.get(rid), dict) else None
        my = sorted([r for r in reads if r["rule"] == rid], key=lambda r: (r["symbol"], SPLITS.index(r["split"]), r["read_at"] or ""))
        item = {
            "id": rid, "origin": "agent" if p else "builtin",
            "name": getattr(cls, "name", None), "timeframe_min": getattr(cls, "timeframe_min", None),
            "params": {k: (v if isinstance(v, (int, float, str, bool)) or v is None else str(v))
                       for k, v in (getattr(cls, "params", {}) or {}).items()},
            "title": BUILTIN[rid][0] if rid in BUILTIN else _clip((p or {}).get("title"), 300),
            "summary": BUILTIN[rid][1] if rid in BUILTIN else None,
            "markets": sorted({r["symbol"] for r in my}) or ((p or {}).get("markets") or []),
            "reads": my,
        }
        if p:
            reg = added.get(f"{rid}.json")
            item["proposal"] = {
                "status": p.get("status"), "registered_at": p.get("registered_at_utc"), "committed": reg,
                "problems": [_clip(x, 500) for x in (p.get("problems") or [])][:10],
                "markets": p.get("markets") or [], "timeframe_min": p.get("timeframe_min"),
                "mechanism": _clip(p.get("mechanism")), "ex_ante_rule": _clip(p.get("ex_ante_rule")),
                "why_gross_beats_3x_cost": _clip(p.get("why_gross_beats_3x_cost")),
                "novelty_vs_tried": _clip(p.get("novelty_vs_tried")),
                "expected_trades_per_year": p.get("expected_trades_per_year"),
                "expected_median_hold_min": p.get("expected_median_hold_min"),
                "parameters": {str(k)[:80]: _clip(v, 200) for k, v in list((p.get("parameters") or {}).items())[:40]},
                "sources": [{"title": _clip(s.get("title"), 300), "url": _clip(s.get("url"), 500)}
                            for s in (p.get("sources") or [])[:10] if isinstance(s, dict)],
                "rule_file": f"b3/proxy_rules/{p.get('file_stem')}.py" if p.get("file_stem") else None,
                "test_file": f"tests/b3/proxy_rules/test_p{rid[2:]}.py",
            }
        else:
            item["proposal"] = None
        decisions = [r["decision"] for r in my]
        item["best"] = ("passed_final" if any(r["split"] == "final_test" and r["decision"] == "passed" for r in my) else
                        "passed_validation" if any(r["split"] == "validation" and r["decision"] == "passed" for r in my) else
                        "passed_exploration" if any(r["split"] == "exploration" and r["decision"] == "passed" for r in my) else
                        "rejected" if decisions else (item["proposal"] or {}).get("status") or "not_run")
        out.append(item)
    return out


def _cycles(root: Path, now: datetime) -> dict:
    events = _jsonl(root / "research" / "proxies" / "pipeline_log.jsonl")
    cycles, cur, stops = [], None, []
    for e in events:
        kind = e.get("event")
        if kind == "program_stop":
            stops.append({"at": e.get("at_utc"), "reasons": [_clip(x, 300) for x in e.get("reasons", [])]})
            continue
        if kind == "paused" and cur is None and cycles:           # the pause follows the error that caused it
            cycles[-1]["steps"].append({"at": e.get("at_utc"), "event": kind, "text": _clip(e.get("reason"), 500)})
            cycles[-1]["paused"] = True
            continue
        # logs written before 2026-11-15 have no cycle_end: a new proposal starts a new cycle
        if cur is not None and kind == "agent" and e.get("agent") == "proxy-research" and cur["steps"]:
            cur["outcome"] = "done" if any(s["event"] == "exploration" for s in cur["steps"]) else "interrupted"
            cur["ended"] = cur["steps"][-1]["at"]
            cycles.append(cur)
            cur = None
        if cur is None:
            cur = {"rule": None, "started": e.get("at_utc"), "steps": [], "cost_usd": 0.0, "outcome": "running"}
        cur["steps"].append({"at": e.get("at_utc"), "event": kind, "agent": e.get("agent"),
                             "cost_usd": e.get("cost_usd"), "is_error": e.get("is_error"),
                             "text": _clip(e.get("result") or e.get("error") or e.get("out") or e.get("title")
                                           or ", ".join(e.get("problems", []) or []) or e.get("reason"), 1500)})
        cur["cost_usd"] += float(e.get("cost_usd") or 0)
        cur["rule"] = e.get("rule") or cur["rule"]
        if kind in ("cycle_end", "cycle_error", "proposal_invalid", "paused"):
            if kind == "cycle_error":
                cur["outcome"] = "error"
            elif kind == "proposal_invalid":
                cur["outcome"] = "invalid"
            elif kind == "cycle_end":
                cur["outcome"] = e.get("outcome") or "done"
            cur["ended"] = e.get("at_utc")
            if kind != "proposal_invalid":
                cycles.append(cur)
                cur = None
    if cur is not None:
        cycles.append(cur)
    by_day: dict = {}
    for c in cycles:
        day = (c.get("started") or "")[:10]
        by_day[day] = by_day.get(day, 0.0) + c["cost_usd"]
    times = [e.get("at_utc") for e in events if e.get("at_utc")]
    last = max(times) if times else None
    log_tail = []
    try:
        log_tail = [_clip(x, 400) for x in (root / "ops" / "state" / "proxy-cycle.log").read_text(
            encoding="utf-8", errors="replace").splitlines()[-30:]]
    except OSError:
        pass
    return {"items": list(reversed(cycles)), "program_stops": stops[-20:], "program_stop_count": len(stops),
            "total_cost_usd": round(sum(c["cost_usd"] for c in cycles), 4),
            "cost_by_day": [{"day": d, "cost_usd": round(v, 4)} for d, v in sorted(by_day.items())],
            "errors": sum(1 for c in cycles if c["outcome"] == "error"), "last_event_at": last,
            "every_hours": CYCLE_HOURS, "log_tail": log_tail}


def _markets(root: Path) -> list[dict]:
    try:
        from b3.markets import MARKETS
    except Exception:
        MARKETS = {}
    scope = _json(root / "b3" / "config" / "scope_proxies.json") or {}
    dq = _json(root / "research" / "proxies" / "data_quality.json") or {}
    ticks = _json(root / "research" / "proxies" / "tick_fidelity.json") or {}
    anatomy = _json(root / "research" / "proxies" / "anatomy.json") or []
    moves: dict = {}
    for a in anatomy if isinstance(anatomy, list) else []:
        moves.setdefault(a.get("symbol"), {})[a.get("tf")] = {
            k: v.get("median_over_cost") for k, v in (a.get("horizons") or {}).items()}
    out = []
    for sym, m in MARKETS.items():
        out.append({
            "symbol": sym, "stands_for": m.stands_for, "tz": m.tz, "open": m.open.strftime("%H:%M"),
            "close": m.close.strftime("%H:%M"), "currency": m.currency,
            "cost_base_pct": 100 * m.base_round_trip, "cost_conservative_pct": 200 * m.base_round_trip,
            "stop_slippage_base_pct": 100 * m.stop_slippage_frac,
            "in_scope": sym in (scope.get("markets") or []),
            "out_of_scope_reason": (scope.get("out_of_scope") or {}).get(sym),
            "data_quality": dq.get(sym), "ticks": ticks.get(sym) if isinstance(ticks.get(sym), dict) else None,
            "move_over_cost": moves.get(sym, {}),
        })
    return out


def _measurements(root: Path) -> dict:
    ev = _json(root / "research" / "proxies" / "event_anatomy.json") or {}
    cands = ("E1_fomc_pre_drift_long", "E2_fomc_15min_continuation", "E3_fomc_30min_continuation",
             "E4_macro_morning_continuation", "E5_de40_release_continuation")
    by_market = []
    for m in ev.get("markets", []):
        by_market.append({"symbol": m.get("symbol"), "event_days": m.get("event_days"),
                          "fomc_move_size": m.get("fomc_move_size"),
                          "macro_morning_move_size": m.get("macro_morning_move_size"),
                          "release_move_size": m.get("release_move_size"),
                          "candidates": {c: {k: m[c].get(k) for k in ("n", "mean_gross_pct", "x_cost", "t", "hit")}
                                         for c in cands if c in m}})
    events_cfg = _json(root / "b3" / "config" / "events_us.json") or {}
    return {"events": {"decision": ev.get("decision"), "markets": by_market, "written": ev.get("written"),
                       "sources": {k: v.get("sources") for k, v in (events_cfg.get("events") or {}).items()},
                       "counts": {k: len(v.get("dates") or []) for k, v in (events_cfg.get("events") or {}).items()}},
            "scope": _json(root / "b3" / "config" / "scope_proxies.json"),
            "gates": _json(root / "b3" / "config" / "gates_proxies.json")}


def _alerts(program: dict, board: list[dict], cycles: dict, now: datetime) -> list[dict]:
    out = []
    st = program.get("status") or {}
    for rule, sym in st.get("validation_passes") or []:
        final = next((r.get("final_test") for r in board if r["rule"] == rule and r["symbol"] == sym), None)
        if not final:
            out.append({"level": "warn", "kind": "final_test_waiting", "rule": rule, "symbol": sym,
                        "text": f"{rule} passou a validação em {sym}: o teste final espera o seu desbloqueio."})
    if program.get("paused"):
        out.append({"level": "bad", "kind": "paused", "text": f"Pipeline pausado: {program['paused']}",
                    "action": f"apague {program['stop_file']} para retomar"})
    recent = [c for c in cycles.get("items", []) if c["outcome"] == "error" and c.get("ended")
              and now - datetime.fromisoformat(c["ended"]) < timedelta(hours=24)]
    if recent:
        out.append({"level": "warn", "kind": "cycle_error", "rule": recent[0].get("rule"),
                    "text": f"{len(recent)} ciclo(s) com erro nas últimas 24 h; último: {recent[0]['steps'][-1]['text'][:200]}"})
    for key, label in (("exchange_data_deadline", "Prazo dos dados de bolsa (demo de corretora ou histórico)"),
                       ("project_deadline", "Parada do projeto se nenhuma regra passar o teste final")):
        d = st.get(key)
        if d:
            left = (date.fromisoformat(d) - now.date()).days
            if left <= 7:
                out.append({"level": "warn" if left >= 0 else "bad", "kind": key, "days_left": left,
                            "text": f"{label}: {d} ({'vence em ' + str(left) + ' dia(s)' if left >= 0 else 'vencido'})."})
    if st and st.get("can_register") is False:
        reasons = st.get("reasons") or []
        if any("project stop" in r or "none passed validation" in r for r in reasons):
            out.append({"level": "bad", "kind": "program_stopped", "text": "Programa de agentes encerrado: " + "; ".join(reasons)})
    return out


def clean(value):
    """NaN and infinities (Sharpe of one day, profit factor without losses) become null: strict JSON."""
    if isinstance(value, float):
        return value if value == value and value not in (float("inf"), float("-inf")) else None
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    return value


def build_indices(root: Path = ROOT, now: datetime | None = None) -> dict:
    return clean(_build(root, now))


def _build(root: Path, now: datetime | None) -> dict:
    now = now or datetime.now(timezone.utc)
    ledger = _jsonl(root / "research" / "proxies" / "ledger.jsonl")
    reads = [_read(d, root) for d in _results(root)]
    board = _board(reads)
    program = _program(root, now)
    cycles = _cycles(root, now)
    rules = _rules(root, reads)
    explored = [r for r in board if "exploration" in r]
    gross = [r["exploration"]["gross_x_cost"] for r in explored if r["exploration"].get("gross_x_cost") is not None]
    bars = [r["exploration"]["bar_pct"] for r in explored if r["exploration"].get("bar_pct") is not None]
    funnel = _funnel(ledger)
    summary = {
        "rules": len({r["rule"] for r in board}), "pairs_explored": len(explored),
        "passed_exploration": funnel[0]["passed"], "passed_validation": funnel[1]["passed"],
        "passed_final": funnel[2]["passed"], "reads": len(ledger),
        "current_bar_pct": max(bars) if bars else None,
        "next_bar_pct": (1.0 * (1 + 0.1 * len(explored))) if explored else None,
        "pairs_at_3x_cost": sum(1 for g in gross if g >= 3), "pairs_positive_gross": sum(1 for g in gross if g > 0),
        "agent_rules": sum(1 for r in rules if r["origin"] == "agent"),
        "agent_cost_usd": cycles["total_cost_usd"],
    }
    return {"generated_at": now.isoformat(timespec="seconds"), "program": program, "funnel": funnel,
            "summary": summary, "board": board, "rules": rules, "cycles": cycles, "markets": _markets(root),
            "measurements": _measurements(root), "alerts": _alerts(program, board, cycles, now)}


def cached_indices(root: Path = ROOT, ttl_s: float = 30.0) -> dict:
    hit = _cache.get(("indices", str(root)))
    if hit and time.monotonic() - hit[0] < ttl_s:
        return hit[1]
    data = build_indices(root)
    _cache[("indices", str(root))] = (time.monotonic(), data)
    return data


def trades_file(name: str, root: Path = ROOT) -> tuple[int, dict]:
    """(status, body) for GET /api/indices/trades?file=NAME: one read's base-scenario trade list."""
    if not TRADE_FILE.fullmatch(name or ""):
        return 400, {"error": "bad file name"}
    data = _json(root / "research" / "proxies" / "trades" / name)
    if not isinstance(data, dict):
        return 404, {"error": "no trade list for this read"}
    return 200, {"file": name, "columns": data.get("columns"), "rows": data.get("rows", []),
                 "recalculated": bool(data.get("recalculated")), "note": data.get("note"),
                 "base_now": data.get("base_now"), "decision_now": data.get("decision_now")}
