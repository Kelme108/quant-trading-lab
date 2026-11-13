"""How often would a dry-run bot of a hypothesis go 2 days without a CLOSED trade, and would it reach day 14 / 30 under
that rule? Base-cost exploration trade lists only (no validation, no holdout). Window: the last 365 days of the
exploration, where all 26 pairs have data. Source of section 2.1 of research/reviews/2026-11-13-plano-evolucao-day-trade.md.

Usage: python research/tools/inactivity_gaps.py [H-104 H-101 ...]
"""

from __future__ import annotations

import bisect
import math
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lab.knowledge import _trades  # noqa: E402

END = datetime(2024, 7, 4, 23, tzinfo=timezone.utc)
START = END - timedelta(days=365)
DEFAULT = ["H-104", "H-101", "H-102", "H-035", "H-100", "H-043", "H-103", "H-123"]


def load(conn):
    latest, decision = {}, {}
    for r in conn.execute("SELECT hypothesis_id, pair, artifact_path FROM experiments WHERE split = 'exploration' "
                          "AND status = 'completed' AND artifact_path IS NOT NULL ORDER BY created_at_utc"):
        latest[(r[0], r[1])] = r[2]
    for r in conn.execute("SELECT e.hypothesis_id, e.pair, d.decision FROM decisions d JOIN experiments e "
                          "ON e.id = d.experiment_id WHERE e.split = 'exploration' ORDER BY d.decided_at_utc"):
        decision[(r[0], r[1])] = r[2]
    return latest, decision


def closes(latest, hypothesis_id):
    out = {}
    for (h, pair), artifact in latest.items():
        path = ROOT / artifact
        if h == hypothesis_id and path.is_file():
            trades, _ = _trades(path)
            out[pair] = [datetime.fromisoformat(str(t["close_date"]).replace("Z", "+00:00")) for t in trades]
    return out


def in_window(times):
    return sorted(t for t in times if START <= t <= END)


def p_quiet(times, days=2.0, step_h=1):
    """Share of start hours with no close in [s, s + days)."""
    n = zero = 0
    s = START
    while s + timedelta(days=days) <= END:
        i = bisect.bisect_left(times, s)
        n += 1
        zero += not (i < len(times) and times[i] < s + timedelta(days=days))
        s += timedelta(hours=step_h)
    return zero / n


def survive(times, horizon_days, gap_days=2.0):
    """Share of starts (every 6 h) where the bot never goes `gap_days` without a close during `horizon_days`."""
    ok = n = 0
    s, g, hz = START, timedelta(days=gap_days), timedelta(days=horizon_days)
    while s + hz <= END:
        i, j = bisect.bisect_left(times, s), bisect.bisect_left(times, s + hz)
        pts = [s, *times[i:j], s + hz]
        n += 1
        ok += all(b - a < g for a, b in zip(pts, pts[1:]))
        s += timedelta(hours=6)
    return ok / n


def longest_gap(times):
    pts = [START, *times, END]
    return max((b - a).total_seconds() / 86400 for a, b in zip(pts, pts[1:]))


def main(argv):
    conn = sqlite3.connect(f"file:{ROOT / 'research' / 'lab.sqlite'}?mode=ro", uri=True)
    latest, decision = load(conn)
    print("| hypothesis | pairs | trades/day | 2 days without a close (measured) | Poisson | reach day 14 | reach day 30 | longest gap (days) |")
    print("|---|---|--:|--:|--:|--:|--:|--:|")
    for h in argv or DEFAULT:
        by_pair = closes(latest, h)
        if not by_pair:
            print(f"| {h} | no exploration runs | | | | | | |")
            continue
        candidates = [p for p in by_pair if decision.get((h, p)) == "candidate_for_portfolio"]
        for label, pairs in ((f"all {len(by_pair)}", list(by_pair)), (f"{len(candidates)} candidates", candidates)):
            times = in_window([t for p in pairs for t in by_pair[p]])
            if not times:
                continue
            rate = len(times) / 365.0
            print(f"| {h} | {label} | {rate:.2f} | {p_quiet(times):.1%} | {math.exp(-2 * rate):.1%} | "
                  f"{survive(times, 14):.1%} | {survive(times, 30):.1%} | {longest_gap(times):.1f} |")


if __name__ == "__main__":
    main(sys.argv[1:])
