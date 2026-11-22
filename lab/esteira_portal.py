"""Portal section 'Esteira' (owner 2026-11-22: "pode criar a secao Esteira no portal").

Reads files only, never writes, never runs a backtest and never reads validation or the final test:
- research/b3/esteira/cycle_log.jsonl   the hourly cycle (agent cost, batches, screen, exit menus, limits, pauses)
- research/b3/esteira/families.jsonl    families registered and screened
- research/b3/esteira/runs/*.json       screen runs (per-variant fails -> why families are cut)
- research/b3/esteira/selected.json     survivors of the screen
- {research/b3,ops/state}/exit_menu/*.json and exit_brl/*.json   exit menus (S1-S4 in V, B1-B5 in BRL)
- b3/config/esteira_b3.json, exit_menu.json, exit_brl.json, gates_b3.json
All numbers are exploration-split figures the conveyor already wrote; this module only regroups them.
"""
from __future__ import annotations

import glob
import json
import math
import re
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = Path(tempfile.gettempdir()) / "trade-initial-esteira-cycle.lock"
FAIL_LABELS = {
    "plateau": "planalto: vizinhos da grade sem resultado positivo",
    "positive_slices": "menos de 5 de 8 fatias de tempo positivas",
    "mean_net_measured": "resultado médio ≤ 0 no custo medido",
    "trades_per_year": "menos de 500 trades por ano",
    "same_bet_as_selected": "mesma aposta de uma já selecionada",
}


def _json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
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
        except ValueError:
            continue
    return out


def _lines(path: Path) -> int:
    try:
        with path.open("rb") as fh:
            return sum(chunk.count(b"\n") for chunk in iter(lambda: fh.read(1 << 20), b""))
    except OSError:
        return 0


def clean(x):
    """JSON-safe: NaN and infinities become None."""
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    if isinstance(x, dict):
        return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    return x


def _clip(text, n: int = 400) -> str:
    text = str(text or "").strip()
    return text if len(text) <= n else text[: n - 1] + "…"


def _sp():
    try:
        from b3.esteira_cycle import SP_TZ
        return SP_TZ
    except Exception:  # noqa: BLE001 - the page still renders with a fixed offset
        return timezone(timedelta(hours=-3))


def budget_day(at_utc: str, start_hour: int, tz) -> str:
    """Same rule as b3.esteira_cycle.budget_day: Sao Paulo days that start at `start_hour` (21 = one budget per night)."""
    return (datetime.fromisoformat(at_utc).astimezone(tz) - timedelta(hours=start_hour)).date().isoformat()


# ---------------------------------------------------------------------------------------------
# cycles and budget
# ---------------------------------------------------------------------------------------------

def _screen_counts(text: str) -> tuple[int, int]:
    """(variants, passed) summed over the screen's lines 'E-158 WIN: 18 variants, 0 pass the screen, ...'."""
    variants = passed = 0
    for line in str(text or "").splitlines():
        try:
            head, rest = line.split(": ", 1)
            parts = rest.split(", ")
            variants += int(parts[0].split()[0])
            passed += int(parts[1].split()[0])
        except (ValueError, IndexError):
            continue
    return variants, passed


def cycles(rows: list[dict], n: int = 40) -> list[dict]:
    """The log grouped into cycles (each ends at a 'cycle_end' row), newest first."""
    out, cur = [], None
    for r in rows:
        ev, at = r.get("event"), r.get("at_utc")
        if cur is None:
            cur = {"start": at, "end": None, "outcome": None, "cost_usd": 0.0, "batch": None, "registered": 0,
                   "variants": 0, "passed": 0, "selected": [], "exit_v": None, "exit_brl": None, "notes": []}
        if ev == "agent":
            cur["cost_usd"] += float(r.get("cost_usd") or 0.0)
            if r.get("is_error"):
                cur["notes"].append("agente com erro")
        elif ev == "registered":
            cur["batch"] = r.get("batch")
            cur["registered"] = len(r.get("families") or [])
            if r.get("rejected"):
                cur["notes"].append(f"{len(r['rejected'])} família(s) recusada(s) na checagem")
        elif ev == "screen":
            v, p = _screen_counts(r.get("out"))
            cur["variants"] += v
            cur["passed"] += p
        elif ev == "batch_done":
            cur["batch"] = r.get("batch", cur["batch"])
            cur["selected"] = r.get("selected") or []
        elif ev in ("exit_menu", "exit_brl"):
            key = "exit_v" if ev == "exit_menu" else "exit_brl"
            cur[key] = {"ok": r.get("exit") == 0, "picks": len(r.get("picks") or [])}
        elif ev == "batch_rejected":
            cur["notes"].append("lote recusado: " + _clip("; ".join(r.get("problems") or []), 160))
        elif ev == "limit":
            for why in r.get("reasons") or []:
                m = re.search(r"US\$([\d.]+) spent.*limit US\$([\d.]+)", str(why))
                cur["notes"].append(f"teto da noite: US$ {m.group(1)} gastos de US$ {m.group(2)}; a próxima chamada passaria do teto"
                                    if m else _clip(why, 200))
        elif ev == "usage_limit":
            cur["notes"].append("limite de uso do Claude: " + _clip(r.get("detail"), 120))
        elif ev == "time_budget":
            cur["notes"].append(f"tempo do ciclo esgotado ({r.get('minutes')} min)")
        elif ev in ("paused_by_file", "paused"):
            cur["notes"].append("pausada pelo arquivo STOP_ESTEIRA")
        elif ev == "cycle_error":
            cur["notes"].append("erro: " + _clip(r.get("error"), 200))
        # one hourly run may hold several cycles; these events end the run without a 'cycle_end' row
        terminal = {"usage_limit": "limite de uso", "cycle_error": "erro", "time_budget": "tempo esgotado",
                    "paused_by_file": "pausada", "paused": "pausada"}
        if ev == "cycle_end" or ev in terminal:
            cur["end"], cur["outcome"] = at, r.get("outcome") if ev == "cycle_end" else terminal[ev]
            cur["cost_usd"] = round(cur["cost_usd"], 2)
            out.append(cur)
            cur = None
    if cur is not None:           # a cycle still running (no cycle_end yet)
        cur["cost_usd"] = round(cur["cost_usd"], 2)
        cur["outcome"] = "em andamento"
        out.append(cur)
    return out[::-1][:n]


def nights(rows: list[dict], start_hour: int, tz, n: int = 10) -> list[dict]:
    by: dict[str, dict] = {}
    for r in rows:
        if not r.get("at_utc"):
            continue
        d = by.setdefault(budget_day(r["at_utc"], start_hour, tz), {"cost_usd": 0.0, "agent_calls": 0, "batches": 0, "families": 0})
        if r.get("event") == "agent":
            d["cost_usd"] += float(r.get("cost_usd") or 0.0)
            d["agent_calls"] += 1
        elif r.get("event") == "registered":
            d["batches"] += 1
            d["families"] += len(r.get("families") or [])
    return [{"day": k, **{kk: (round(vv, 2) if isinstance(vv, float) else vv) for kk, vv in v.items()}}
            for k, v in sorted(by.items(), reverse=True)[:n]]


# ---------------------------------------------------------------------------------------------
# screen and exit menus
# ---------------------------------------------------------------------------------------------

def screen_fails(root: Path) -> dict:
    """Per-variant screen fails over every screen run (latest run per variant wins)."""
    latest: dict[str, list[str]] = {}
    for path in sorted(glob.glob(str(root / "research" / "b3" / "esteira" / "runs" / "*.json"))):
        run = _json(Path(path)) or {}
        for fam in (run.get("families") or {}).values():
            for m in (fam.get("markets") or {}).values():
                for row in m.get("rows") or []:
                    latest[row["variant"]] = row.get("fails") or []
    counts: dict[str, int] = {}
    passed = 0
    for fails in latest.values():
        if not fails:
            passed += 1
        for f in fails:
            counts[f] = counts.get(f, 0) + 1
    total = len(latest)
    return {"variants": total, "passed": passed,
            "fails": [{"key": k, "label": FAIL_LABELS.get(k, k), "count": c, "share": c / total if total else None}
                      for k, c in sorted(counts.items(), key=lambda kv: -kv[1])]}


def exit_picks(root: Path, exits: dict) -> dict:
    """Every exit-menu pick (V menu and BRL menu, all runs; latest wins per variant+exit)."""
    rows, runs, versions = {}, 0, 0
    paths = []
    for menu, sub in (("V", "exit_menu"), ("R$", "exit_brl")):
        for base in (root / "research" / "b3" / sub, root / "ops" / "state" / sub):
            paths += [(menu, Path(p)) for p in glob.glob(str(base / "2*.json"))]
    for menu, path in sorted(paths, key=lambda mp: mp[1].name):
        rep = _json(path)
        if not isinstance(rep, dict):
            continue
        runs += 1
        versions += int(rep.get("n_versions_read") or 0)
        for fid, fam in (rep.get("families") or {}).items():
            for mk, m in fam.items():
                if mk == "title" or not isinstance(m, dict) or not m.get("pick"):
                    continue
                p, me = m["pick"], m["pick"].get("measured") or {}
                net, rnd, p90 = me.get("mean_net_brl"), p.get("random_mean_net_brl"), p.get("measured_p90_mean_net_brl")
                rows[(p["variant"], p["exit"])] = {
                    "family": fid, "title": fam.get("title"), "market": mk, "menu": menu, "variant": p["variant"],
                    "exit": p["exit"], "exit_what": (exits.get(p["exit"]) or {}).get("what"),
                    "trades": me.get("trades"), "trades_per_year": me.get("trades_per_year"), "hit": me.get("hit_rate"),
                    "net": net, "p90": p90, "random": rnd, "net_per_year": me.get("net_per_year_brl"),
                    "positive_slices": me.get("positive_slices"), "neighbours": p.get("positive_neighbour_share"),
                    "candidates": m.get("candidates"), "run": rep.get("run"),
                    "good": bool(p90 is not None and p90 > 0 and net is not None and rnd is not None and net > rnd),
                }
    allp = list(rows.values())
    good = sorted((r for r in allp if r["good"]), key=lambda r: (-(r["hit"] or 0), -(r["net"] or 0)))
    return {"runs": runs, "versions_read": versions, "picks": len(allp), "good": len(good), "top": good[:80]}


def _gates(root: Path) -> dict:
    g = _json(root / "b3" / "config" / "gates_b3.json") or {}
    keep = ("cost_basis", "multiple_testing", "minimum_trades", "max_drawdown_pct", "positive_years_share",
            "net_without_best_trade_positive")
    return {k: g.get(k) for k in keep} | {"revised": _clip(g.get("_revised_2026_11_21"), 900)}


# ---------------------------------------------------------------------------------------------
# state
# ---------------------------------------------------------------------------------------------

def esteira_state(root: Path = ROOT, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    tz = _sp()
    cfg = _json(root / "b3" / "config" / "esteira_b3.json") or {}
    lim = cfg.get("limits") or {}
    start_hour = int(lim.get("budget_day_starts_at_hour", 0) or 0)
    cap = lim.get("max_agent_cost_usd_per_day")
    log = _jsonl(root / "research" / "b3" / "esteira" / "cycle_log.jsonl")
    tonight = budget_day(now.isoformat(), start_hour, tz)
    spent = sum(float(r.get("cost_usd") or 0.0) for r in log
                if r.get("event") == "agent" and r.get("at_utc") and budget_day(r["at_utc"], start_hour, tz) == tonight)
    stop = root / "ops" / "state" / "STOP_ESTEIRA"
    paused = None
    if stop.exists():
        try:
            paused = _clip(stop.read_text(encoding="utf-8"), 300) or "arquivo de pausa presente"
        except OSError:
            paused = "arquivo de pausa presente"
    fams = _jsonl(root / "research" / "b3" / "esteira" / "families.jsonl")
    today_sp = now.astimezone(tz).date().isoformat()
    exits = {}
    for name in ("exit_menu.json", "exit_brl.json"):
        exits.update((_json(root / "b3" / "config" / name) or {}).get("exits") or {})
    selected = _json(root / "research" / "b3" / "esteira" / "selected.json") or []
    last = log[-1] if log else {}
    return clean({
        "generated_at_utc": now.isoformat(timespec="seconds"),
        "status": {
            "paused": paused, "cycle_running": LOCK.exists(),
            "last_event": {"at_utc": last.get("at_utc"), "event": last.get("event"), "outcome": last.get("outcome")},
            "budget": {"day": tonight, "starts_at_hour": start_hour, "spent_usd": round(spent, 2), "cap_usd": cap,
                       "per_call_usd": 3.0},
            "families_per_day": lim.get("max_families_per_day"),
            "families_today": sum(1 for f in fams if str(f.get("screened_at_utc", ""))[:10] and
                                  datetime.fromisoformat(f["screened_at_utc"]).astimezone(tz).date().isoformat() == today_sp),
            "agent_model": "sonnet",
        },
        "totals": {
            "families": len(fams), "families_rejected": sum(1 for f in fams if f.get("rejected")),
            "last_family": fams[-1].get("family") if fams else None,
            "screen_reads": _lines(root / "research" / "b3" / "esteira" / "ledger.jsonl"),
            "exit_reads": _lines(root / "research" / "b3" / "exit_menu" / "ledger.jsonl")
                          + _lines(root / "ops" / "state" / "exit_menu" / "ledger.jsonl")
                          + _lines(root / "research" / "b3" / "exit_brl" / "ledger.jsonl")
                          + _lines(root / "ops" / "state" / "exit_brl" / "ledger.jsonl"),
        },
        "screen_rules": {k: v for k, v in (cfg.get("screen") or {}).items() if not k.startswith("_")},
        "default_exit": {k: v for k, v in (cfg.get("default_exit") or {}).items() if not k.startswith("_")},
        "screen": screen_fails(root),
        "selected": [{"variant": s.get("variant"), "status": s.get("status"), "selected_at_utc": s.get("selected_at_utc"),
                      "trades_per_year": (s.get("measured") or {}).get("trades_per_year"),
                      "hit": (s.get("measured") or {}).get("hit_rate"), "net": (s.get("measured") or {}).get("mean_net_brl")}
                     for s in selected if isinstance(s, dict)],
        "exits": {k: {"what": v.get("what"), "stop": v.get("stop"), "target": v.get("target"), "hold_min": v.get("hold_min")}
                  for k, v in exits.items()},
        "exit_picks": exit_picks(root, exits),
        "gates": _gates(root),
        "cycles": cycles(log),
        "nights": nights(log, start_hour, tz),
        "note": "docs/cerebro/decisoes/2026-11-21-auditoria-backtest-demo.md",
    })


_cache: dict = {"at": 0.0, "value": None, "root": None}
_lock = threading.Lock()


def cached_state(root: Path = ROOT, ttl: float = 30.0) -> dict:
    """esteira_state behind a short cache: a few open tabs do not re-read the runs on every poll."""
    with _lock:
        if _cache["value"] is None or _cache["root"] != root or time.monotonic() - _cache["at"] > ttl:
            _cache.update(value=esteira_state(root), at=time.monotonic(), root=root)
        return _cache["value"]
