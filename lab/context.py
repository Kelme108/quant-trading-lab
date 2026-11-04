"""Plain-text material the agents read, written by the orchestrator.

Agents cannot read the SQLite registry, and they should not decide what the
numbers are, so everything they need is rendered here from the registry and the
Freqtrade export.

Two rules shape the research context:
- Validation numbers are never shown. A research agent that designs the next
  hypothesis after seeing validation results turns the validation split into
  one more training set. Exploration results are shown, which is how the lab
  learns; the multiple-testing penalty in gates.json prices that in.
- Cost facts are computed from lab/costs.py, not typed, so they cannot drift.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from lab import costs, registry, runner

ROOT = Path(__file__).parents[1]


def cost_facts() -> str:
    lines = [
        "| scenario | cost per side | round trip (entry + exit) |",
        "|---|---|---|",
    ]
    for scenario in costs.all_required_scenarios():
        per_side = scenario.effective_fee_per_side
        lines.append(f"| {scenario.name} | {per_side:.3%} | {2 * per_side:.3%} |")
    return "\n".join(lines)


def _exploration_summary(conn, hypothesis_id: str) -> list[str]:
    cells: dict[str, object] = {}
    for row in registry.list_latest_decisions(conn):
        if row["hypothesis_id"] == hypothesis_id and row["split"] == "exploration":
            cells[row["pair"]] = row  # list is ordered by creation time: the latest wins
    lines = []
    for pair, row in sorted(cells.items()):
        metrics = registry.get_metrics(conn, row["experiment_id"])
        lines.append(
            f"  - {pair}: {row['decision']}; base-cost trades={metrics.get('trades__base')}, "
            f"net profit={metrics.get('net_profit_quote__base')}, "
            f"max drawdown%={metrics.get('max_drawdown_pct__base')}, "
            f"buy-and-hold%={metrics.get('benchmark_buy_and_hold_return_pct')}"
        )
    return lines


def _validation_was_run(conn, hypothesis_id: str) -> bool:
    """True once a validation experiment exists, decided or not."""
    return bool(registry.latest_experiments(conn, hypothesis_id, "validation"))


def research_context(
    conn,
    *,
    hypothesis_id: str,
    budget: dict,
    hypotheses_proposed_this_cycle: int,
    guidance: str = "",
) -> str:
    """Markdown the research agent reads before proposing `hypothesis_id`.

    `guidance` is the owner's free-text research direction (research/guidance.md). It steers
    WHAT to look for; it never changes a gate, a limit or the protocol."""
    pairs = ", ".join(runner.enabled_pairs())
    timeframes = ", ".join(runner.enabled_timeframes())
    cap = budget["max_variants_per_family"]

    families: dict[str, int] = {}
    entries: list[str] = []
    for hypothesis in registry.list_hypotheses(conn):
        families[hypothesis["family"]] = families.get(hypothesis["family"], 0) + 1
        invalid = str(hypothesis["status"]).startswith("invalid")
        summary = [] if invalid else _exploration_summary(conn, hypothesis["id"])
        entries.append(
            f"### {hypothesis['id']} - {hypothesis['family']} ({hypothesis['status']})\n"
            f"Rule: {hypothesis['ex_ante_rule']}\n"
            + (
                "Exploration results (corrected harness):\n" + "\n".join(summary)
                if summary
                else (
                    "Result invalidated: the implementation that was tested did not match the "
                    "rule (harness flaw, since fixed). Numbers withheld; the idea itself is untested."
                    if invalid
                    else "Not tested under the corrected harness (no usable results exist)."
                )
            )
            + f"\nValidation: {'run (numbers withheld on purpose)' if _validation_was_run(conn, hypothesis['id']) else 'not run'}"
        )

    family_lines = [
        f"- {family}: {count} of {cap} allowed variants used"
        + (" (CAP REACHED: do not reuse this family)" if count >= cap else "")
        for family, count in sorted(families.items())
    ] or ["- none yet"]

    return "\n".join(
        [
            f"# Research context for {hypothesis_id}",
            "",
            "## Scope",
            f"- Pairs: {pairs}. Timeframe: {timeframes}. Spot, long only, one open trade at a time, whole balance per trade.",
            "- Splits: exploration then validation per pair; a final test exists but is locked and empty. You see exploration results only.",
            f"- This is hypothesis {hypotheses_proposed_this_cycle + 1} of at most {budget['max_hypotheses_per_cycle']} for this cycle.",
            "",
            "## Cost scenarios (the backtest charges these on every entry and every exit)",
            cost_facts(),
            "",
            "Net profit must be positive at the base AND conservative cost, and it must exceed a bar that rises with every earlier variant in the family. "
            "A strategy that is profitable only at the optimistic cost has no edge after costs.",
            "",
            "## Families and their variant caps",
            *family_lines,
            "",
            *(["## Direction from the owner (steers the search; does not change any gate or limit)", guidance.strip(), ""] if guidance.strip() else []),
            "## Hypotheses already tried",
            *(entries or ["none"]),
            "",
        ]
    )


def _write_trades_csv(trades: list[dict], path: Path) -> None:
    fields = ["open_date", "close_date", "trade_duration", "profit_ratio", "profit_abs", "exit_reason"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(trades)


def _close(first: float, second: float) -> bool:
    return abs(first - second) <= 1e-6 * max(1.0, abs(first), abs(second))


def write_review_facts(conn, hypothesis_id: str, split: str, root: Path = ROOT) -> Path:
    """Write facts.json, crosscheck.json and trades-<pair>.csv for the latest
    experiments of a hypothesis and split, and return the review directory."""
    directory = root / "research" / "experiments" / f"{hypothesis_id}-{split}"
    directory.mkdir(parents=True, exist_ok=True)

    facts: dict = {"hypothesis_id": hypothesis_id, "split": split, "pairs": {}}
    crosscheck: dict = {}

    for pair, experiment in registry.latest_experiments(conn, hypothesis_id, split).items():
        slug = pair.replace("/", "-").lower()
        metrics = registry.get_metrics(conn, experiment["id"])
        decision = registry.get_latest_decision(conn, experiment["id"])
        facts["pairs"][pair] = {
            "experiment_id": experiment["id"],
            "manifest": f"research/manifests/{experiment['id']}.yaml",
            "trades_csv": f"trades-{slug}.csv",
            "metrics": metrics,
            "decision": decision["decision"] if decision else None,
            "decision_reasons": json.loads(decision["reasons_json"]) if decision else None,
        }

        artifact = root / experiment["artifact_path"] if experiment["artifact_path"] else None
        if artifact is None or not artifact.is_file():
            crosscheck[pair] = {"error": "no export zip recorded for this experiment"}
            continue
        trades = runner.read_trades(artifact)
        _write_trades_csv(trades, directory / f"trades-{slug}.csv")
        from_list = sum(float(t["profit_abs"]) for t in trades)
        stored_profit = metrics.get("net_profit_quote__base")
        stored_trades = metrics.get("trades__base")
        starting_balance = runner.read_starting_balance(artifact)
        excl_recomputed = runner.compounded_profit_excluding_best(trades, starting_balance)
        excl_stored = metrics.get("net_profit_excl_best_trade__base")
        crosscheck[pair] = {
            "trades_stored": stored_trades,
            "trades_in_export": len(trades),
            "net_profit_stored": stored_profit,
            "net_profit_from_trade_list": from_list,
            "net_profit_excl_best_stored": excl_stored,
            "net_profit_excl_best_recomputed": excl_recomputed,
            "excl_best_method": (
                "starting_balance * product(1 + profit_ratio) over every trade except the one "
                "with the highest profit_ratio, minus starting_balance (compounded; NOT total "
                "profit minus the best trade's profit_abs, because with a whole-balance stake the "
                "best trade also enlarges every later trade)"
            ),
            "starting_balance": starting_balance,
            "matches": bool(
                stored_trades == len(trades)
                and stored_profit is not None
                and _close(float(stored_profit), from_list)
                and excl_stored is not None
                and _close(float(excl_stored), excl_recomputed)
            ),
        }

    (directory / "facts.json").write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")
    (directory / "crosscheck.json").write_text(json.dumps(crosscheck, indent=2) + "\n", encoding="utf-8")
    return directory
