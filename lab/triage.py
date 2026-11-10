"""Deterministic triage of collected ideas. No agent, no backtest, no result of any kind is read.

An idea is dropped for a stated reason or queued with a score. Every criterion is declared here and applied before
anything is run, so the queue cannot be ordered by how well an idea happened to do on the history:

drop when
  - the timeframe is not 1h or 1d (the lab only runs those; 1d means daily signals executed on 1h);
  - the longest lookback cannot be loaded (4500 bars on 1h, 200 days on 1d: the daily state needs a warm-up of about
    twice the lookback, protocol v3 section 2.0);
  - the text asks for short selling, leverage, margin, derivatives, martingale/pyramiding or position-sizing hooks
    (forbidden by lab/strategy_check.py);
  - the expected trades per year per pair cannot reach the 30-trade minimum in the exploration window with a margin;
  - it repeats a tried hypothesis or an earlier idea (content-word overlap), or its family is at the variant cap.

score (higher is better, maximum 4.5): distinctness from everything tried (0 to 1) + simplicity (1 for up to 3 free
parameters, 0.5 up to 6) + 1 when the parameters are textbook values fixed in advance + 0.5 for a paper as source +
the margin of expected trades over the requirement (0 to 1).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from lab import intake, registry, runner
from lab.strategy_check import MAX_STARTUP_CANDLES

ROOT = Path(__file__).parents[1]
MAX_LOOKBACK = {"15m": MAX_STARTUP_CANDLES, "1h": MAX_STARTUP_CANDLES, "1d": 200}
TRADES_MARGIN = 1.3          # expected trades must exceed the requirement by 30%
MIN_GROSS_MOVE_PCT = 0.45    # the scout's expected average gross move per trade must be at least 1.5x the 0.30% base round trip
OVERLAP_LIMIT = 0.55         # Jaccard overlap of content words above which an idea repeats a tried rule
SCORE_MAX = 4.5

FORBIDDEN_PATTERNS = (
    (re.compile(r"\b(short[- ]?sell\w*|shorting|go(?:ing)? short|short position\w*|enter_short|venda a descoberto)\b", re.I), "short selling"),
    (re.compile(r"\b(leverag\w*|alavanc\w*|margin trad\w*|on margin|borrow\w*)\b", re.I), "leverage or margin"),
    (re.compile(r"\b(futures?|perpetuals?|options?|derivatives?|funding rate)\b", re.I), "derivatives"),
    (re.compile(r"\b(martingale|pyramid\w*|average down|scale[- ]in|adjust_trade_position)\b", re.I), "position scaling"),
    (re.compile(r"\b(position siz\w*|custom_stake_amount|kelly|volatility target\w*|risk parity)\b", re.I), "position sizing"),
)


def minimum_trades(path: Path = ROOT / "lab" / "config" / "gates.json") -> int:
    return int(json.loads(path.read_text(encoding="utf-8"))["minimum_trades"]["value"])


def exploration_years(splits: dict | None = None) -> float:
    """Average exploration length over the enabled pairs, in years."""
    import pandas as pd

    splits = splits if splits is not None else runner.load_splits()
    spans = []
    for pair in runner.enabled_pairs():
        window = splits["pairs"][pair]["exploration"]
        spans.append((pd.Timestamp(window["end_utc"]) - pd.Timestamp(window["start_utc"])).days / 365.25)
    return sum(spans) / len(spans)


# A forbidden word that is itself ruled out ("no pyramiding", "without leverage", "long only, never short selling")
# describes a rule that is fine. Look a few words back for a negation within the same clause.
NEGATION = re.compile(r"\b(no|not|never|without|nor|neither|non|sem|nunca|nao|n\u00e3o)\b(?:(?!\b(?:but|however|except|then|mas|porem)\b)[^.;:]){0,25}$", re.I)


def _asserted(pattern: re.Pattern, text: str) -> bool:
    """True when the forbidden pattern appears in `text` at least once without a negation just before it."""
    for match in pattern.finditer(text):
        if not NEGATION.search(text[max(0, match.start() - 30):match.start()]):
            return True
    return False


def forbidden_topics(*texts: str) -> list[str]:
    found = []
    for pattern, label in FORBIDDEN_PATTERNS:
        if any(_asserted(pattern, text) for text in texts) and label not in found:
            found.append(label)
    return found


def required_trades_per_year(min_trades: int, years: float) -> float:
    return min_trades / years * TRADES_MARGIN


def triage_idea(
    idea: dict, *, tried_rules: list[tuple[str, str]], family_counts: dict[str, int], family_cap: int,
    min_trades: int, years: float,
) -> dict:
    """{'state': 'queued'|'dropped', 'reasons': [...], 'score': float|None, 'overlap': float, 'overlap_with': str|None}.

    `tried_rules` is (label, rule text) for every registered hypothesis and every earlier queued idea."""
    reasons: list[str] = []
    if idea["timeframe"] not in MAX_LOOKBACK:
        reasons.append(f"timeframe {idea['timeframe']} is not run by the lab")
    elif idea["longest_lookback"] > MAX_LOOKBACK[idea["timeframe"]]:
        reasons.append(
            f"longest lookback {idea['longest_lookback']} exceeds {MAX_LOOKBACK[idea['timeframe']]} "
            f"{'days' if idea['timeframe'] == '1d' else 'bars'}"
        )
    topics = forbidden_topics(idea["rule_summary"], idea["mechanism"], idea["title"])
    if topics:
        reasons.append("forbidden by the lab: " + ", ".join(topics))
    needed = required_trades_per_year(min_trades, years)
    if idea["expected_trades_per_year"] < needed:
        reasons.append(
            f"expected {idea['expected_trades_per_year']:g} trades/year/pair is below the {needed:.1f} needed "
            f"for {min_trades} trades in {years:.1f} years"
        )
    move = idea.get("expected_gross_move_pct")
    if move is not None and move < MIN_GROSS_MOVE_PCT:
        reasons.append(
            f"expected gross move {move:g}% per trade is below {MIN_GROSS_MOVE_PCT:g}% (1.5x the base round trip): the cost would eat it"
        )
    family = idea["family_hint"]
    if family_counts.get(family, 0) >= family_cap:
        reasons.append(f"family {family} is at the cap of {family_cap} variants")

    words = intake.tokens(idea["rule_summary"])
    best, best_label = 0.0, None
    for label, text in tried_rules:
        overlap = intake.jaccard(words, intake.tokens(text))
        if overlap > best:
            best, best_label = overlap, label
    if best >= OVERLAP_LIMIT:
        reasons.append(f"repeats {best_label} (word overlap {best:.2f})")

    if reasons:
        return {"state": "dropped", "reasons": reasons, "score": None, "overlap": best, "overlap_with": best_label}
    simplicity = 1.0 if idea["free_parameters"] <= 3 else 0.5 if idea["free_parameters"] <= 6 else 0.0
    margin = min(1.0, (idea["expected_trades_per_year"] - needed) / needed) if needed > 0 else 1.0
    score = (
        (1.0 - best) + simplicity + (1.0 if idea["fixed_parameters"] else 0.0)
        + (0.5 if idea["source_type"] == "paper" else 0.0) + margin
    )
    return {"state": "queued", "reasons": [], "score": round(score, 4), "overlap": best, "overlap_with": best_label}


def run_triage(conn, budget: dict, splits: dict | None = None) -> list[dict]:
    """Triage every idea in state 'new', in id order, and record the outcome. Earlier queued ideas count as tried."""
    min_trades, years = minimum_trades(), exploration_years(splits)
    cap = int(budget["max_variants_per_family"])
    family_counts: dict[str, int] = {}
    tried: list[tuple[str, str]] = []
    for hypothesis in registry.list_hypotheses(conn):
        family_counts[hypothesis["family"]] = family_counts.get(hypothesis["family"], 0) + 1
        tried.append((hypothesis["id"], hypothesis["ex_ante_rule"]))
    for row in registry.list_ideas(conn):
        if row["state"] in ("queued", "registered"):
            tried.append((row["id"], row["rule_summary"]))
    outcomes = []
    for row in registry.list_ideas(conn, "new"):
        result = triage_idea(
            dict(row), tried_rules=tried, family_counts=family_counts, family_cap=cap, min_trades=min_trades, years=years,
        )
        registry.set_idea_state(conn, row["id"], result["state"], "; ".join(result["reasons"]), result["score"])
        if result["state"] == "queued":
            tried.append((row["id"], row["rule_summary"]))
        outcomes.append({"idea_id": row["id"], **result})
    return outcomes


def pick(conn, limit: int) -> list[dict]:
    """The best queued ideas by score (ties by id): what a cycle may register next."""
    queued = [dict(row) for row in registry.list_ideas(conn, "queued")]
    queued.sort(key=lambda r: (-(r["score"] or 0.0), r["id"]))
    return queued[:limit]
