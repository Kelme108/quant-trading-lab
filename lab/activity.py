"""Expected activity of a dry-run bot, measured from its OWN exploration trades (owner decision D1, 2026-11-13).

Why: the rule "retire after 2 days without a closed trade" assumed trades arrive evenly. They do not: the lab's best day
trade rules fire on high-volume bars, and volume is high on every pair at once, so trades come in bursts and vanish in
calm weeks. Measured on the exploration trades (research/reviews/2026-11-13-plano-evolucao-day-trade.md, 2.1): H-104 on
26 pairs averages 2.1 closed trades a day yet goes 2 days without one in 24% of windows (an even, Poisson pace would give
1.6%), and a bot of it would reach the 14-day judgement in 8% of starts. Under that rule no rule of this kind can ever
be judged, however good.

The replacement compares what the bot DID with what its own backtest says it SHOULD do over the same number of days,
bursts included because they are measured, not assumed:
- from the exploration trade lists of the bot's pairs (base scenario, the latest exploration run per pair), over the
  last `WINDOW_DAYS` days in which every one of those pairs has exploration data, count the closed trades in every
  window of T days (T = 1..HORIZON_DAYS, a window starting every STEP_HOURS hours) and keep the 1st and 5th percentile;
- record the longest stretch without a closed trade in that period.
This is computed when the bot is frozen and stored in its freeze record, before the bot runs: it cannot be tuned on
the dry-run. lab/dryrun.py then discards a bot whose closed-trade count after T days is below the 1st percentile, or
whose stretch without a trade is longer than the longest one of its exploration, and warns below the 5th percentile.
Only exploration data is read (never the validation or the holdout).
"""

from __future__ import annotations

import bisect
from datetime import datetime, timedelta, timezone
from pathlib import Path

from lab import runner

ROOT = Path(__file__).parents[1]
WINDOW_DAYS = 365
HORIZON_DAYS = 60
STEP_HOURS = 6
MIN_WINDOW_DAYS = 60
PERCENTILES = (1, 5)


def _ts(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def exploration_closes(conn, hypothesis_id: str, pairs: list[str], root: Path = ROOT,
                       read_trades=runner.read_trades) -> dict[str, list[datetime]]:
    """Close times of the latest completed exploration run of each pair (its base-scenario trade list)."""
    out: dict[str, list[datetime]] = {}
    for pair in pairs:
        row = conn.execute(
            "SELECT artifact_path FROM experiments WHERE hypothesis_id = ? AND pair = ? AND split = 'exploration' "
            "AND status = 'completed' AND artifact_path IS NOT NULL ORDER BY created_at_utc DESC LIMIT 1",
            (hypothesis_id, pair)).fetchone()
        if row is None:
            raise ValueError(f"{hypothesis_id}: no completed exploration run for {pair}")
        trades = read_trades(Path(root) / row[0])
        out[pair] = sorted(d for d in (_ts(t.get("close_date")) for t in trades) if d)
    return out


def _quantile(sorted_values: list[int], pct: float) -> int:
    """Lower nearest-rank percentile: the value at or below which `pct`% of the windows fall (conservative for a floor)."""
    if not sorted_values:
        return 0
    return sorted_values[int(pct / 100.0 * (len(sorted_values) - 1))]


def expectation(closes_by_pair: dict[str, list[datetime]], windows: dict[str, tuple[datetime, datetime]], *,
                window_days: int = WINDOW_DAYS, horizon_days: int = HORIZON_DAYS, step_hours: int = STEP_HOURS) -> dict:
    """The activity record stored in a freeze. `windows` maps each pair to its exploration (start, end)."""
    start = max(_ts(a) for a, _ in windows.values())
    end = min(_ts(b) for _, b in windows.values())
    start = max(start, end - timedelta(days=window_days))
    span = (end - start).total_seconds() / 86400.0
    if span < MIN_WINDOW_DAYS:
        raise ValueError(f"only {span:.0f} days of exploration common to every pair; {MIN_WINDOW_DAYS} needed")
    times = sorted(t for closes in closes_by_pair.values() for t in closes if start <= t <= end)
    points = [start, *times, end]
    gaps = sorted((b - a).total_seconds() / 86400.0 for a, b in zip(points, points[1:]))
    quantiles: dict[str, dict[str, int]] = {str(p): {} for p in PERCENTILES}
    step = timedelta(hours=step_hours)
    for days in range(1, horizon_days + 1):
        horizon = timedelta(days=days)
        counts, s = [], start
        while s + horizon <= end:
            counts.append(bisect.bisect_left(times, s + horizon) - bisect.bisect_left(times, s))
            s += step
        counts.sort()
        for p in PERCENTILES:
            quantiles[str(p)][str(days)] = _quantile(counts, p)
    return {
        "method": "closed trades of the exploration runs of these pairs (base scenario), windows of T days every "
                  f"{step_hours} h over the last {window_days} days common to every pair; lower nearest-rank percentiles",
        "pairs": sorted(closes_by_pair),
        "window_utc": [start.isoformat(), end.isoformat()],
        "closed_trades_in_window": len(times),
        "trades_per_day": len(times) / span,
        "max_gap_days": gaps[-1],
        "p99_gap_days": gaps[int(0.99 * (len(gaps) - 1))],
        "closed_trades_percentile_by_days": quantiles,
    }


def expectation_for(conn, hypothesis_id: str, pairs: list[str], root: Path = ROOT, splits: dict | None = None,
                    read_trades=runner.read_trades) -> dict:
    splits = splits if splits is not None else runner.load_splits()
    windows = {p: (splits["pairs"][p]["exploration"]["start_utc"], splits["pairs"][p]["exploration"]["end_utc"]) for p in pairs}
    return expectation(exploration_closes(conn, hypothesis_id, pairs, root, read_trades), windows)


def floor_for(record: dict, days_running: float, pct: int = 1) -> int | None:
    """Fewest closed trades the exploration says a bot running `days_running` days should have, at percentile `pct`.
    None before one full day. Past the last horizon, the last value is scaled by the extra days (rounded down)."""
    table = (record.get("closed_trades_percentile_by_days") or {}).get(str(pct))
    if not table or days_running is None or days_running < 1:
        return None
    days = int(days_running)
    last = max(int(k) for k in table)
    if days <= last:
        return int(table[str(days)])
    return int(table[str(last)] * days / last)
