"""Portfolio selection by consistency and diversification, never by return.

A strategy that clears lab/gates.py has only earned the right to be
considered here. It is included only if it
  1. holds `candidate_for_portfolio` in EVERY (enabled pair, required split)
     cell, so one lucky pair is not enough;
  2. earns a similar profit per day in every cell (min/max ratio), so a great
     result on one pair next to a barely positive one is excluded;
  3. is not too correlated with a strategy already included, so ten variations
     of one idea do not pass for diversification.

Candidates are considered in registration order, never ranked by performance,
so the greedy correlation rule cannot favor the best-looking backtest. An empty
portfolio is a valid, expected outcome. Standard library only.

The final_test split is never read. Once splits.json unlocks it, no new
snapshot can be created, so the composition cannot be adjusted after the final
test has been observed.
"""

from __future__ import annotations

import hashlib
import json
import statistics
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from lab import registry, runner

ROOT = Path(__file__).parents[1]
CRITERIA_PATH = Path(__file__).parent / "config" / "portfolio.json"
PORTFOLIO_DIR = ROOT / "research" / "portfolio"

class PortfolioFrozenError(RuntimeError):
    """Raised when something tries to build a portfolio after final_test unlocked."""


def load_criteria(criteria_path: Path = CRITERIA_PATH) -> dict:
    return json.loads(criteria_path.read_text(encoding="utf-8"))


def criteria_sha256(criteria_path: Path = CRITERIA_PATH) -> str:
    return hashlib.sha256(criteria_path.read_bytes()).hexdigest()


# --- daily return series -------------------------------------------------------

def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def daily_returns_from_trades(
    trades: list[dict], start_day: date, end_day: date
) -> dict[date, float]:
    """Daily return for every UTC day in [start_day, end_day], zeros included.

    Each trade's profit_ratio is spread evenly over the calendar days from
    open_date to close_date inclusive, not booked on the close day. Booking on
    the close day would make two strategies that hold the same rally look
    uncorrelated whenever they close on different days. The spread is an
    approximation of mark-to-market (it ignores the path inside a trade); a
    trade that crosses the window edge loses the part outside the window.
    """
    series: dict[date, float] = {}
    day = start_day
    while day <= end_day:
        series[day] = 0.0
        day += timedelta(days=1)

    for trade in trades:
        open_day = _utc(trade["open_date"]).date()
        close_day = _utc(trade["close_date"]).date()
        if close_day < open_day:
            raise ValueError(f"trade closes before it opens: {trade['open_date']} -> {trade['close_date']}")
        span = (close_day - open_day).days + 1
        share = trade["profit_ratio"] / span
        for offset in range(span):
            held_day = open_day + timedelta(days=offset)
            if held_day in series:
                series[held_day] += share
    return series


def pearson(xs: list[float], ys: list[float]) -> float | None:
    """Pearson correlation, or None when it is undefined (a constant series)."""
    try:
        return statistics.correlation(xs, ys)
    except statistics.StatisticsError:
        return None


def pooled_correlation(
    first: dict[tuple[str, date], float],
    second: dict[tuple[str, date], float],
    min_overlap_days: int,
) -> float | None:
    """Correlation over the (pair, day) keys both series share; None when
    fewer than min_overlap_days are shared or the correlation is undefined."""
    shared = sorted(set(first) & set(second))
    if len(shared) < min_overlap_days:
        return None
    return pearson([first[key] for key in shared], [second[key] for key in shared])


def consistency_ratio(per_day_profits: list[float]) -> float:
    """min/max of the per-cell profit per day; 0.0 if any cell is not profitable."""
    if not per_day_profits:
        return 0.0
    low, high = min(per_day_profits), max(per_day_profits)
    if low <= 0 or high <= 0:
        return 0.0
    return low / high


# --- selection -----------------------------------------------------------------

@dataclass
class Candidate:
    hypothesis_id: str
    family: str
    eligibility_failures: list[str]
    per_day_profits: list[float]
    # Pooled over every required cell, keyed by (pair, UTC day). None when any
    # cell's trade export is unavailable: correlation is then undefined.
    daily_returns: dict[tuple[str, date], float] | None


def _id_number(hypothesis_id: str) -> int:
    return int(hypothesis_id.rsplit("-", 1)[1])


def select(candidates: list[Candidate], criteria: dict) -> dict:
    """Apply the consistency and correlation criteria. Pure: no I/O."""
    min_ratio = criteria["consistency"]["min_ratio"]
    max_correlation = criteria["correlation"]["max_abs_correlation"]
    min_overlap = criteria["correlation"]["min_overlap_days"]

    included: list[Candidate] = []
    evaluations: list[dict] = []

    for candidate in sorted(candidates, key=lambda c: _id_number(c.hypothesis_id)):
        evaluation: dict = {
            "hypothesis_id": candidate.hypothesis_id,
            "family": candidate.family,
            "included": False,
            "reasons": [],
            "consistency_ratio": None,
            "correlations": {},
        }
        evaluations.append(evaluation)

        if candidate.eligibility_failures:
            evaluation["reasons"] = list(candidate.eligibility_failures)
            continue

        ratio = consistency_ratio(candidate.per_day_profits)
        evaluation["consistency_ratio"] = ratio
        if ratio < min_ratio:
            evaluation["reasons"].append(
                f"inconsistent across cells: min/max profit per day is {ratio:.3f}, "
                f"below the required {min_ratio}"
            )
            continue

        blocked = False
        for other in included:
            if candidate.daily_returns is None or other.daily_returns is None:
                correlation = None
            else:
                correlation = pooled_correlation(
                    candidate.daily_returns, other.daily_returns, min_overlap
                )
            evaluation["correlations"][other.hypothesis_id] = correlation
            if correlation is None:
                evaluation["reasons"].append(
                    f"correlation with {other.hypothesis_id} is undefined "
                    f"(constant series, fewer than {min_overlap} shared days, or no trade export)"
                )
                blocked = True
            elif abs(correlation) > max_correlation:
                evaluation["reasons"].append(
                    f"correlation with {other.hypothesis_id} is {correlation:.3f}, "
                    f"above the allowed {max_correlation}"
                )
                blocked = True
        if blocked:
            continue

        included.append(candidate)
        evaluation["included"] = True
        evaluation["reasons"].append(
            "eligible in every required cell, consistent across cells, "
            "and not too correlated with an included strategy"
        )

    weight = 1.0 / len(included) if included else 0.0
    return {
        "included": [
            {"hypothesis_id": c.hypothesis_id, "family": c.family, "weight": weight}
            for c in included
        ],
        "evaluations": evaluations,
    }


# --- reading the registry --------------------------------------------------------

def split_window(splits: dict, pair: str, split: str) -> tuple[str, str]:
    """(start_utc, end_utc) of an exploration or validation split for a pair."""
    try:
        entry = splits["pairs"][pair][split]
    except KeyError:
        raise KeyError(f"splits.json has no '{split}' boundaries for {pair}") from None
    return entry["start_utc"], entry["end_utc"]


def collect_candidates(
    conn,
    *,
    required_pairs: list[str],
    splits: dict,
    criteria: dict,
    root: Path = ROOT,
) -> list[Candidate]:
    """One Candidate per hypothesis that has at least one decision in a required split.

    Where a (pair, split) cell has several experiments, the latest one counts.
    Rows for any split outside criteria["required_splits"] (in particular
    final_test) are ignored entirely.
    """
    required_splits = criteria["required_splits"]
    required_cells = [(pair, split) for pair in required_pairs for split in required_splits]

    by_hypothesis: dict[str, dict[tuple[str, str], object]] = {}
    families: dict[str, str] = {}
    for row in registry.list_latest_decisions(conn):
        if row["split"] not in required_splits:
            continue
        families[row["hypothesis_id"]] = row["family"]
        by_hypothesis.setdefault(row["hypothesis_id"], {})[(row["pair"], row["split"])] = row

    candidates: list[Candidate] = []
    for hypothesis_id, cells in by_hypothesis.items():
        failures: list[str] = []
        for pair, split in required_cells:
            row = cells.get((pair, split))
            if row is None:
                failures.append(f"{pair}/{split}: no decision recorded")
            elif row["decision"] != criteria["required_decision"]:
                failures.append(
                    f"{pair}/{split}: decision is '{row['decision']}', "
                    f"required '{criteria['required_decision']}'"
                )

        per_day_profits: list[float] = []
        returns: dict[tuple[str, date], float] | None = {}
        if not failures:
            for pair, split in required_cells:
                row = cells[(pair, split)]
                metrics = registry.get_metrics(conn, row["experiment_id"])
                profit = metrics.get("net_profit_quote__base")
                start_utc, end_utc = split_window(splits, pair, split)
                days = (_utc(end_utc) - _utc(start_utc)).total_seconds() / 86400
                if profit is None:
                    failures.append(f"{pair}/{split}: no base-scenario net profit recorded")
                    continue
                per_day_profits.append(profit / days)

                artifact = (root / row["artifact_path"]) if row["artifact_path"] else None
                if returns is None or artifact is None or not artifact.is_file():
                    returns = None
                    continue
                series = daily_returns_from_trades(
                    runner.read_trades(artifact), _utc(start_utc).date(), _utc(end_utc).date()
                )
                for day, value in series.items():
                    returns[(pair, day)] = value

        candidates.append(
            Candidate(
                hypothesis_id=hypothesis_id,
                family=families[hypothesis_id],
                eligibility_failures=failures,
                per_day_profits=per_day_profits,
                daily_returns=returns,
            )
        )
    return candidates


def build_portfolio(
    conn,
    *,
    splits: dict | None = None,
    scenarios: dict | None = None,
    criteria_path: Path = CRITERIA_PATH,
    root: Path = ROOT,
    now: datetime | None = None,
) -> dict:
    """Select the portfolio and return the snapshot dict (nothing is written)."""
    if splits is None:
        splits = runner.load_splits()
    if splits["final_test"].get("final_test_unlocked") is True:
        raise PortfolioFrozenError(
            "final_test is unlocked in lab/config/splits.json; the portfolio "
            "composition can no longer change. Use the latest existing snapshot."
        )

    criteria = load_criteria(criteria_path)
    required_pairs = runner.enabled_pairs(scenarios)
    candidates = collect_candidates(
        conn, required_pairs=required_pairs, splits=splits, criteria=criteria, root=root
    )
    selection = select(candidates, criteria)

    created = now or datetime.now(timezone.utc)
    return {
        "created_at_utc": created.isoformat(),
        "criteria_sha256": criteria_sha256(criteria_path),
        "final_test_unlocked_at_selection": False,
        "required_pairs": required_pairs,
        "required_splits": criteria["required_splits"],
        **selection,
    }


def write_snapshot(snapshot: dict, directory: Path = PORTFOLIO_DIR) -> Path:
    """Write research/portfolio/<timestamp>.json. Never overwrites: a second
    snapshot in the same second raises FileExistsError."""
    directory.mkdir(parents=True, exist_ok=True)
    stamp = _utc(snapshot["created_at_utc"]).strftime("%Y%m%dT%H%M%SZ")
    path = directory / f"{stamp}.json"
    with path.open("x", encoding="utf-8") as handle:
        json.dump(snapshot, handle, indent=2)
        handle.write("\n")
    return path


def main() -> int:
    conn = registry.connect()
    snapshot = build_portfolio(conn)
    path = write_snapshot(snapshot)
    print(f"snapshot written to {path}")
    print(f"included: {[entry['hypothesis_id'] for entry in snapshot['included']] or 'none (empty portfolio)'}")
    for evaluation in snapshot["evaluations"]:
        verdict = "INCLUDED" if evaluation["included"] else "excluded"
        print(f"  {evaluation['hypothesis_id']} ({evaluation['family']}): {verdict}")
        for reason in evaluation["reasons"]:
            print(f"    - {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
