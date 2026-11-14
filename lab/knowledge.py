"""The lab's knowledge base for the agents: what its own trades say about DAY TRADING, plus curated outside evidence.

Owner direction 2026-11-12: day trade only (positions closed within the day), strategies that are good AND trade a lot,
and agents that learn from every result ("retroalimentar"). Two parts, both rebuilt before every scout and research step
(through lab/learnings.py):

1. `daytrade_section`: a scoreboard built from the REAL TRADE LISTS of every hypothesis's exploration runs (the base-cost
   backtest zip of each pair): trades per year per pair, holding time, mean gross and net move per trade, breadth and the
   2022-2024 bear years. It shows the trade-off that decides the owner's goal (frequency against move per trade) and which
   rules came closest. Exploration split only, like the rest of the digest: validation, holdout and dry-run results are
   never read, so nothing leaks.
2. `evidence_section`: research/knowledge/evidence.md, a curated, sourced summary of published evidence on intraday crypto
   (what is documented to exist after costs, and what is not). Written by hand; agents read it, never edit it.

`python -m lab.knowledge` writes research/knowledge/scoreboard.md, the full table for the owner.
"""

from __future__ import annotations

import json
import statistics as st
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from lab import registry

ROOT = Path(__file__).parents[1]
EVIDENCE = "research/knowledge/evidence.md"
SCOREBOARD = "research/knowledge/scoreboard.md"
DAY_HOURS = 24.0              # a rule is day trade when 95% of its positions close within this many hours
FREQUENT = 100                # trades per year per pair the owner's goal asks for (guidance 2026-11-10 (e))
BANDS = [(0, 25), (25, 50), (50, 100), (100, 200), (200, 10 ** 9)]
_cache: dict = {}


def _years(split: dict) -> float:
    a, b = (datetime.fromisoformat(split[k].replace("Z", "+00:00")) for k in ("start_utc", "end_utc"))
    return max((b - a).days / 365.25, 1e-9)


def _trades(zip_path: Path) -> tuple[list[dict], str | None]:
    with zipfile.ZipFile(zip_path) as zf:
        name = [n for n in zf.namelist() if n.endswith(".json") and "_config" not in n and "meta" not in n][0]
        strategy = list(json.load(zf.open(name))["strategy"].values())[0]
    return strategy["trades"], strategy.get("timeframe")


def rows(conn, root: Path = ROOT) -> list[dict]:
    """One row per hypothesis with exploration trade lists. Cached while the set of exploration runs is unchanged."""
    runs = conn.execute(
        "SELECT hypothesis_id, pair, artifact_path, strategy_file, created_at_utc FROM experiments "
        "WHERE split = 'exploration' AND status = 'completed' AND artifact_path IS NOT NULL ORDER BY created_at_utc").fetchall()
    key = (str(root), len(runs), runs[-1]["created_at_utc"] if runs else None)
    if _cache.get("key") == key:
        return _cache["rows"]
    try:
        splits = json.loads((root / "lab" / "config" / "splits.json").read_text(encoding="utf-8"))["pairs"]
    except (OSError, ValueError, KeyError):
        splits = {}
    latest: dict[tuple[str, str], dict] = {}
    for r in runs:
        latest[(r["hypothesis_id"], r["pair"])] = dict(r)          # the latest run per (hypothesis, pair)
    decisions = {(d["hypothesis_id"], d["pair"]): d["decision"] for d in registry.list_latest_decisions(conn) if d["split"] == "exploration"}
    hypotheses = {h["id"]: h for h in registry.list_hypotheses(conn)}
    by_h: dict[str, list[dict]] = defaultdict(list)
    for (hid, _), r in latest.items():
        by_h[hid].append(r)
    out = []
    for hid, group in by_h.items():
        per_pair, durations, gross, net, yearly, tf = [], [], [], [], defaultdict(float), None
        for r in group:
            path = root / r["artifact_path"]
            if not path.is_file() or r["pair"] not in splits:
                continue
            try:
                trades, tf = _trades(path)
            except (OSError, ValueError, KeyError, IndexError, zipfile.BadZipFile):
                continue
            pair_net = [100.0 * t["profit_ratio"] for t in trades]
            for t, n in zip(trades, pair_net):
                yearly[str(t["open_date"])[:4]] += n
            durations += [t["trade_duration"] for t in trades]
            # a short (futures lane) gains when the price falls: its gross move is the opposite sign
            gross += [(-100.0 if t.get("is_short") else 100.0) * (t["close_rate"] / t["open_rate"] - 1.0) for t in trades]
            net += pair_net
            per_pair.append({"per_year": len(trades) / _years(splits[r["pair"]]["exploration"]), "net_sum": sum(pair_net),
                             "passing": decisions.get((hid, r["pair"])) == "candidate_for_portfolio"})
        if not net:
            continue
        durations.sort()
        h = hypotheses.get(hid)
        row = {
            "id": hid, "family": h["family"] if h else "?", "status": str(h["status"]) if h else "?", "timeframe": tf or "?",
            "strategy": Path(group[-1]["strategy_file"]).stem, "pairs": len(per_pair), "trades": len(net),
            "trades_per_year_pair": st.median(p["per_year"] for p in per_pair),
            "hold_median_min": st.median(durations), "hold_p95_h": durations[int(0.95 * (len(durations) - 1))] / 60.0,
            "gross_pct": st.mean(gross), "net_pct": st.mean(net), "win_pct": 100.0 * sum(1 for n in net if n > 0) / len(net),
            "pairs_net_positive": sum(1 for p in per_pair if p["net_sum"] > 0), "pairs_passing": sum(1 for p in per_pair if p["passing"]),
            "bear_2022_2024_pct": sum(yearly.get(y, 0.0) for y in ("2022", "2023", "2024")),
        }
        row["day_trade"] = row["hold_p95_h"] <= DAY_HOURS
        row["frequent"] = row["trades_per_year_pair"] >= FREQUENT
        out.append(row)
    out.sort(key=lambda r: int(r["id"].split("-")[1]) if r["id"].split("-")[-1].isdigit() else 0)
    _cache.update(key=key, rows=out)
    return out


def _f(value, digits=2) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def daytrade_section(conn, root: Path = ROOT) -> str:
    data = rows(conn, root)
    head = "## Day-trade scoreboard (the owner's goal; real exploration trades of every hypothesis, base cost)"
    if not data:
        return head + "\n\nNo exploration trade lists yet.\n"
    day = [r for r in data if r["day_trade"]]
    frequent = [r for r in day if r["frequent"]]
    winners = [r for r in frequent if r["net_pct"] > 0]
    lines = [head, "",
             f"{len(data)} hypotheses have exploration trade lists. {len(day)} are day trade (95% of positions closed within {DAY_HOURS:.0f}h). "
             f"{len(frequent)} of those trade at least {FREQUENT} times a year per pair, and {len(winners)} of THOSE had a positive mean net "
             "move per trade after the base cost (0.30% round trip). That empty corner is what the owner wants filled.", "",
             "### Frequency against move per trade (day-trade rules only)",
             "| trades per year per pair | rules | median gross % per trade | best gross % | with net > 0 |", "|---|--:|--:|--:|--:|"]
    for lo, hi in BANDS:
        band = [r for r in day if lo <= r["trades_per_year_pair"] < hi]
        label = f"{lo}+" if hi > 10 ** 8 else f"{lo}-{hi}"
        lines.append(f"| {label} | {len(band)} | {_f(st.median(r['gross_pct'] for r in band) if band else None)} | "
                     f"{_f(max((r['gross_pct'] for r in band), default=None))} | {sum(1 for r in band if r['net_pct'] > 0)} |")
    if frequent:
        lines += ["", f"Lesson: the frequent rules (>= {FREQUENT} trades/yr/pair) had a mean gross move of at most "
                  f"{max(r['gross_pct'] for r in frequent):.2f}% per trade (median {st.median(r['gross_pct'] for r in frequent):.2f}%): "
                  "their triggers fire on noise, and the 0.30% round trip eats them. A frequent rule needs a trigger that is rare "
                  "per bar but common across bars of many pairs, or a mechanism with a documented intraday edge (see the evidence section)."]
    close = sorted((r for r in day if r["trades_per_year_pair"] >= 20), key=lambda r: -r["net_pct"])[:10]
    lines += ["", "### Closest to the goal (day trade, at least 20 trades/yr/pair, best mean net per trade)",
              "| id | strategy | chart | trades/yr/pair | median hold (min) | gross % | net % | pairs net>0 | 2022-24 net % | status |",
              "|---|---|---|--:|--:|--:|--:|--:|--:|---|"]
    for r in close:
        lines.append(f"| {r['id']} | {r['strategy']} | {r['timeframe']} | {r['trades_per_year_pair']:.0f} | {r['hold_median_min']:.0f} | "
                     f"{r['gross_pct']:.2f} | {r['net_pct']:.2f} | {r['pairs_net_positive']}/{r['pairs']} | {r['bear_2022_2024_pct']:.0f} | {r['status'][:30]} |")
    noise = sorted((r for r in frequent if r["gross_pct"] <= 0.10), key=lambda r: r["gross_pct"])
    if noise:
        lines += ["", "### Frequent rules whose trigger was noise (mean gross move <= 0.10% per trade): do not propose a variant of these",
                  "; ".join(f"{r['id']} {r['strategy']} ({r['gross_pct']:.2f}%)" for r in noise)]
    slow = sorted((r for r in data if not r["day_trade"] and r["net_pct"] > 0), key=lambda r: -r["net_pct"])[:5]
    if slow:
        lines += ["", "Out of scope but informative: the best net per trade came from SLOW rules that hold for days ("
                  + ", ".join(f"{r['id']} {r['hold_median_min'] / 60:.0f}h median hold, {r['net_pct']:.2f}%" for r in slow)
                  + "). The owner does not want them; their mechanism (trend persistence over days) may still supply a regime filter for an intraday entry."]
    return "\n".join(lines) + "\n"


def evidence_section(root: Path = ROOT) -> str:
    path = root / EVIDENCE
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8").strip() + "\n"


def scoreboard_markdown(conn, root: Path = ROOT) -> str:
    data = rows(conn, root)
    lines = ["# Placar de day trade (exploração, custo base)", "",
             "Gerado por `python -m lab.knowledge` a partir das listas de trades da exploração de cada hipótese. Bruto e líquido são a média "
             "por trade, em % do valor operado; edge/ano = líquido por trade x trades por ano por par. Day trade = 95% das posições fechadas em até 24h.", "",
             "| id | estratégia | gráfico | day trade | trades/ano/par | hold mediano (min) | p95 (h) | bruto % | líquido % | acerto % | pares líquido>0 | pares aprovados | 2022-24 % | edge/ano/par % | status |",
             "|---|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|"]
    for r in sorted(data, key=lambda r: -(r["net_pct"] * r["trades_per_year_pair"])):
        lines.append(f"| {r['id']} | {r['strategy']} | {r['timeframe']} | {'sim' if r['day_trade'] else 'não'} | {r['trades_per_year_pair']:.0f} | "
                     f"{r['hold_median_min']:.0f} | {r['hold_p95_h']:.1f} | {r['gross_pct']:.2f} | {r['net_pct']:.2f} | {r['win_pct']:.0f} | "
                     f"{r['pairs_net_positive']}/{r['pairs']} | {r['pairs_passing']} | {r['bear_2022_2024_pct']:.0f} | "
                     f"{r['net_pct'] * r['trades_per_year_pair']:.1f} | {r['status'][:40]} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    connection = registry.connect()
    target = ROOT / SCOREBOARD
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(scoreboard_markdown(connection), encoding="utf-8")
    print(target)
