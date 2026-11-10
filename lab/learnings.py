"""What the lab has learned so far, rebuilt from the registry before every scout and research step.

The agents read this digest so they do not start from zero: what was tried, which mechanisms came close, how big the
average move per trade was against the cost, and why the rest failed. It is built ONLY from the exploration split
(the in-sample sandbox, already visible to the research agent hypothesis by hypothesis). Validation, holdout and
forward results are never read here, so the digest cannot leak them.

Gross move per trade (percent of the traded notional) is recovered from two cost scenarios of the same run: the
optimistic and the base scenario differ only by slippage, 2 x 0.05% per round trip, so
    traded_notional = (net_optimistic - net_base) / 0.0010
    net_edge_per_trade = net_base / traded_notional           (stake-weighted average, after the base cost)
    gross_move_per_trade = net_edge_per_trade + base round trip (0.30%).
Hypotheses judged under the old 0.10% fee carry 0.05% more cost per round trip; the figure is a guide, not a gate.
"""

from __future__ import annotations

import json
import re
import statistics
from collections import Counter, defaultdict

from lab import registry

SLIPPAGE_GAP = 0.0010          # optimistic -> base: 2 x 0.05% slippage per round trip
BASE_ROUND_TRIP_PCT = 0.30
MAX_ROWS = 45


def _pair_figures(metrics: dict) -> dict | None:
    trades = metrics.get("trades__base")
    net_base, net_opt = metrics.get("net_profit_quote__base"), metrics.get("net_profit_quote__optimistic")
    if not trades or net_base is None or net_opt is None:
        return None
    gap = net_opt - net_base
    figures = {"trades": float(trades), "net_base": float(net_base)}
    if gap > 1e-9:
        notional = gap / SLIPPAGE_GAP
        net_pct = 100.0 * float(net_base) / notional
        figures["net_edge_pct"] = net_pct
        figures["gross_pct"] = net_pct + BASE_ROUND_TRIP_PCT
    return figures


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def _fmt(value: float | None, digits: int = 2) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def hypothesis_rows(conn) -> list[dict]:
    """One row per hypothesis that has exploration results: medians over its pairs."""
    ideas = {row["hypothesis_id"]: row for row in registry.list_ideas(conn) if row["hypothesis_id"]}
    cells: dict[str, dict[str, object]] = defaultdict(dict)
    for row in registry.list_latest_decisions(conn):
        if row["split"] == "exploration":
            cells[row["hypothesis_id"]][row["pair"]] = row  # ordered by creation: the latest wins
    rows = []
    for hypothesis in registry.list_hypotheses(conn):
        hid = hypothesis["id"]
        pairs = cells.get(hid)
        if not pairs:
            continue
        figures = [f for f in (_pair_figures(registry.get_metrics(conn, r["experiment_id"])) for r in pairs.values()) if f]
        reasons: Counter = Counter()
        for r in pairs.values():
            for text in json.loads(r["reasons_json"] or "[]"):
                if "FAIL" in text:
                    reasons[re.split(r"[\[:]", text)[0].strip()] += 1
        idea = ideas.get(hid)
        rows.append({
            "id": hid, "family": hypothesis["family"], "timeframe": idea["timeframe"] if idea else "?",
            "pairs": len(pairs), "passing": sum(1 for r in pairs.values() if r["decision"] == "candidate_for_portfolio"),
            "trades": _median([f["trades"] for f in figures]),
            "gross_pct": _median([f["gross_pct"] for f in figures if "gross_pct" in f]),
            "net_pct": _median([f["net_edge_pct"] for f in figures if "net_edge_pct" in f]),
            "status": str(hypothesis["status"]), "fails": reasons,
        })
    return rows


def digest(conn) -> str:
    rows = hypothesis_rows(conn)
    if not rows:
        return "## What the lab has learned\n\nNo exploration results yet.\n"
    measured = [r for r in rows if r["gross_pct"] is not None]
    lines = [
        "## What the lab has learned so far (exploration data only; rebuilt from the registry every run)",
        "",
        f"{len(rows)} hypotheses have exploration results. Move per trade = average gross move as a percent of the traded "
        "notional (before cost); the base round trip costs 0.30%, the conservative one 0.45%. A rule needs a gross move "
        "clearly above 0.45% per trade to survive.",
        "",
    ]
    if measured:
        above = [r for r in measured if r["gross_pct"] >= 0.45]
        lines += [
            f"- {len(above)} of {len(measured)} measured hypotheses had a median gross move of at least 0.45% per trade; "
            f"{sum(1 for r in measured if r['passing'])} had at least one pair clearing the exploration gates.",
        ]
        by_tf: dict[str, list[dict]] = defaultdict(list)
        for r in measured:
            by_tf[r["timeframe"]].append(r)
        for tf, group in sorted(by_tf.items()):
            lines.append(
                f"- Chart {tf}: {len(group)} hypotheses, median gross move per trade "
                f"{_fmt(_median([r['gross_pct'] for r in group]))}%, median trades per pair {_fmt(_median([r['trades'] for r in group]), 0)}, "
                f"{sum(1 for r in group if r['passing'])} with a passing pair."
            )
    total_fails: Counter = Counter()
    for r in rows:
        total_fails.update(r["fails"])
    if total_fails:
        lines += ["", "Most common gate failures (pair-level): " + "; ".join(f"{k} x{v}" for k, v in total_fails.most_common(6)) + "."]
    ordered = sorted(measured, key=lambda r: -(r["net_pct"] if r["net_pct"] is not None else -9))
    lines += ["", "### Closest to working (best median net edge per trade after base cost)",
              "| id | family | chart | pairs passing | trades/pair | gross move % | net edge % | status |", "|---|---|---|---|---|---|---|---|"]
    for r in ordered[:12]:
        lines.append(f"| {r['id']} | {r['family']} | {r['timeframe']} | {r['passing']}/{r['pairs']} | {_fmt(r['trades'], 0)} | "
                     f"{_fmt(r['gross_pct'])} | {_fmt(r['net_pct'])} | {r['status'][:40]} |")
    lines += ["", "### Weakest (worst net edge per trade): the mechanisms to avoid repeating",
              "| id | family | chart | trades/pair | gross move % | net edge % |", "|---|---|---|---|---|---|"]
    for r in ordered[::-1][:12]:
        lines.append(f"| {r['id']} | {r['family']} | {r['timeframe']} | {_fmt(r['trades'], 0)} | {_fmt(r['gross_pct'])} | {_fmt(r['net_pct'])} |")
    lines += ["", "Use this to aim higher, not to copy: a mechanism that came close is a reason to look for a stronger trigger "
              "of the same kind (a volatility or volume filter, a better session, a cleaner exit), never to repeat the rule.", ""]
    return "\n".join(lines)
