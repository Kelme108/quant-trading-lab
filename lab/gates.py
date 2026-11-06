"""Deterministic approval logic. No LLM, no agent, ever decides here.

decide() takes metrics (as stored in the registry) plus the frozen
lab/config/gates.json and returns one of:
  - "rejected"
  - "inconclusive"
  - "candidate_for_portfolio"
There is no "approved for live" value; this lab never produces one.

A candidate is only eligible for portfolio.py; passing these per-experiment
gates is necessary, not sufficient, for inclusion in a portfolio.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

GATES_PATH = Path(__file__).parent / "config" / "gates.json"

DECISION_REJECTED = "rejected"
DECISION_INCONCLUSIVE = "inconclusive"
DECISION_CANDIDATE = "candidate_for_portfolio"


def gates_sha256(gates_path: Path = GATES_PATH) -> str:
    return hashlib.sha256(gates_path.read_bytes()).hexdigest()


def load_gates(gates_path: Path = GATES_PATH) -> dict:
    return json.loads(gates_path.read_text(encoding="utf-8"))


def required_net_profit(gates: dict, variants_tested_in_family: int) -> float:
    """Net profit (quote currency) a scenario must strictly exceed.

    base_threshold_quote * (1 + per_variant_increase * variants_tested_in_family),
    so every earlier variant in the same family makes approval harder. See the
    `_rationale` field in gates.json for why.
    """
    if variants_tested_in_family < 0:
        raise ValueError("variants_tested_in_family cannot be negative")
    net_profit = gates["net_profit"]
    increase = net_profit["multiple_testing_penalty"]["per_variant_increase"]
    return net_profit["base_threshold_quote"] * (1 + increase * variants_tested_in_family)


def decide(
    metrics: dict,
    gates: dict | None = None,
    variants_tested_in_family: int = 0,
) -> tuple[str, list[str]]:
    """Evaluate one split's metrics against the gates.

    `metrics` is expected to carry, per required cost scenario (see
    gates["required_cost_scenarios"]), keys of the form:
      trades__<scenario>
      net_profit_quote__<scenario>
      net_profit_excl_best_trade__<scenario>
      max_relative_drawdown_pct__<scenario>
    plus scenario-independent keys:
      lookahead_has_bias (bool)
      recursive_is_stable (bool)
      benchmark_cash_return_pct, benchmark_buy_and_hold_return_pct (reported only)

    Returns (decision, reasons). `reasons` always lists every gate that was
    checked and whether it passed, so a rejection or an inconclusive result
    is traceable without re-deriving it from the raw metrics.

    `variants_tested_in_family` is the number of hypotheses in the same
    family registered before this one (registry.count_prior_variants); it
    raises the net-profit bar per gates.json's multiple_testing_penalty.
    """
    if gates is None:
        gates = load_gates()

    reasons: list[str] = []
    passed = True
    inconclusive = False

    required_scenarios = gates["required_cost_scenarios"]

    # --- lookahead (mandatory, scenario-independent) ---
    lookahead_ok = metrics.get("lookahead_has_bias") is False
    reasons.append(
        f"lookahead: {'pass' if lookahead_ok else 'FAIL'} "
        f"(has_bias={metrics.get('lookahead_has_bias')!r})"
    )
    if not lookahead_ok:
        passed = False

    # --- recursive (mandatory, scenario-independent) ---
    recursive_ok = metrics.get("recursive_is_stable") is True
    reasons.append(
        f"recursive: {'pass' if recursive_ok else 'FAIL'} "
        f"(is_stable={metrics.get('recursive_is_stable')!r})"
    )
    if not recursive_ok:
        passed = False

    # --- minimum trades per scenario ---
    min_trades = gates["minimum_trades"]["value"]
    for scenario in required_scenarios:
        trades = metrics.get(f"trades__{scenario}")
        if trades is None:
            reasons.append(f"minimum_trades[{scenario}]: FAIL (no trade count recorded)")
            passed = False
            continue
        if trades < min_trades:
            reasons.append(
                f"minimum_trades[{scenario}]: inconclusive ({trades} < {min_trades})"
            )
            inconclusive = True
        else:
            reasons.append(f"minimum_trades[{scenario}]: pass ({trades} >= {min_trades})")

    # --- net profit above the penalized bar in base and conservative ---
    required_profit = required_net_profit(gates, variants_tested_in_family)
    for scenario in gates["net_profit"]["required_positive_in_scenarios"]:
        net_profit = metrics.get(f"net_profit_quote__{scenario}")
        if net_profit is None:
            reasons.append(f"net_profit[{scenario}]: FAIL (no net profit recorded)")
            passed = False
            continue
        ok = net_profit > required_profit
        reasons.append(
            f"net_profit[{scenario}]: {'pass' if ok else 'FAIL'} "
            f"(net_profit_quote={net_profit} {'>' if ok else '<='} required {required_profit:.4f}, "
            f"after {variants_tested_in_family} prior variant(s) in family)"
        )
        if not ok:
            passed = False

    # --- profit excluding the single best trade, base scenario ---
    if gates["profit_excluding_best_trade"]["required_positive"]:
        excl_best = metrics.get("net_profit_excl_best_trade__base")
        if excl_best is None:
            reasons.append("profit_excluding_best_trade[base]: FAIL (not recorded)")
            passed = False
        else:
            ok = excl_best > 0
            reasons.append(
                f"profit_excluding_best_trade[base]: {'pass' if ok else 'FAIL'} "
                f"(value={excl_best})"
            )
            if not ok:
                passed = False

    # --- max drawdown ceiling per scenario ---
    max_dd_ratio = gates["max_drawdown"]["max_ratio"]
    for scenario in gates["max_drawdown"].get("scenarios", required_scenarios):
        # Worst peak-to-trough fall of the account, not Freqtrade's max_drawdown_account:
        # that one is taken at the point of largest ABSOLUTE loss and understates a
        # compounding whole-balance run (H-007 BNB: 25.1% vs 51.3%).
        drawdown_pct = metrics.get(f"max_relative_drawdown_pct__{scenario}")
        if drawdown_pct is None:
            reasons.append(f"max_drawdown[{scenario}]: FAIL (not recorded)")
            passed = False
            continue
        ok = (drawdown_pct / 100.0) <= max_dd_ratio
        reasons.append(
            f"max_drawdown[{scenario}]: {'pass' if ok else 'FAIL'} "
            f"({drawdown_pct}% {'<=' if ok else '>'} {max_dd_ratio * 100}%)"
        )
        if not ok:
            passed = False

    # --- benchmark comparison: must be reported, not required to beat ---
    cash_reported = metrics.get("benchmark_cash_return_pct") is not None
    bh_reported = metrics.get("benchmark_buy_and_hold_return_pct") is not None
    if gates["benchmark_comparison"]["required_to_report"]:
        if not (cash_reported and bh_reported):
            reasons.append("benchmark_comparison: FAIL (cash and/or buy-and-hold not reported)")
            passed = False
        else:
            reasons.append(
                "benchmark_comparison: reported "
                f"(cash={metrics.get('benchmark_cash_return_pct')}%, "
                f"buy_and_hold={metrics.get('benchmark_buy_and_hold_return_pct')}%); "
                "beating the benchmark is not required"
            )

    if not passed:
        decision = DECISION_REJECTED
    elif inconclusive:
        decision = DECISION_INCONCLUSIVE
    else:
        decision = DECISION_CANDIDATE

    return decision, reasons
