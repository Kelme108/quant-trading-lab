"""Keep the list of open-source trading projects fresh, and learn which sources actually produce ideas.

Two jobs, both deterministic (no agent, no backtest):

1. `refresh_catalog`: search GitHub (public API, no key) for trading, bot, quant, AI-trading and day-trading projects,
   merge them into research/sources-catalog.json, and write research/sources-new.md with the repositories that appeared
   or gained stars since the last refresh. The scout reads that file next to research/sources-queue.md.
2. `yield_table`: for every source the scout has used, how many ideas it gave, how many became hypotheses and how many of
   those cleared the exploration gates on at least one pair. It is part of the learnings digest, so the scout spends
   its time on sources that produce, and stops returning to the ones that never did.

Only metadata is stored (name, stars, description, licence, dates). No third-party code is fetched.
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from lab import registry

ROOT = Path(__file__).parents[1]
CATALOG = "research/sources-catalog.json"
NEW_REPORT = "research/sources-new.md"
QUERIES = [
    "topic:trading-bot", "topic:algorithmic-trading", "topic:freqtrade-strategies", "topic:ai-trading",
    "topic:trading-strategies", "topic:crypto-trading-bot", "topic:quantitative-trading", "topic:day-trading",
    "topic:scalping", "topic:freqtrade", "topic:llm trading", "topic:reinforcement-learning trading",
    "topic:machine-learning trading crypto", "ai trading agent", "intraday trading strategy", "crypto trading strategy backtest",
]
RISING_GAIN = 0.10            # a repository whose stars grew by 10% since the last refresh is "rising"


def _fetch(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "trading-lab-sources", "Accept": "application/vnd.github+json"})
    return json.load(urllib.request.urlopen(request, timeout=30))


def search(query: str, *, min_stars: int, fetch=_fetch) -> list[dict]:
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
        {"q": f"{query} stars:>{min_stars}", "sort": "stars", "per_page": 30})
    return [{
        "name": item["full_name"], "stars": item["stargazers_count"], "desc": (item["description"] or "")[:160],
        "pushed": item["pushed_at"][:10], "license": (item["license"] or {}).get("spdx_id"), "lang": item["language"],
    } for item in fetch(url).get("items", [])]


def refresh_catalog(root: Path = ROOT, *, fetch=_fetch, sleep=time.sleep, now: datetime | None = None, pause: float = 7.0) -> dict:
    """Merge a fresh GitHub survey into the catalog; returns {'total', 'new', 'rising', 'failed_queries'}."""
    now = now or datetime.now(timezone.utc)
    path = root / CATALOG
    old = {r["name"]: r for r in json.loads(path.read_text(encoding="utf-8"))["repos"]} if path.is_file() else {}
    queries = list(QUERIES) + [f"trading created:>{(now - timedelta(days=120)).date()}"]   # young projects
    seen, failed = {}, []
    for query in queries:
        try:
            for repo in search(query, min_stars=50 if "created:" in query else 150, fetch=fetch):
                seen[repo["name"]] = repo
        except Exception:
            failed.append(query)
        sleep(pause)
    new, rising = [], []
    merged = dict(old)
    for name, repo in seen.items():
        before = old.get(name)
        repo = {**repo, "first_seen": (before or {}).get("first_seen", now.date().isoformat())}
        if before is None:
            new.append(repo)
        elif before["stars"] and repo["stars"] >= before["stars"] * (1 + RISING_GAIN):
            rising.append({**repo, "stars_before": before["stars"]})
        merged[name] = repo
    ordered = sorted(merged.values(), key=lambda r: -r["stars"])
    path.write_text(json.dumps({"refreshed_utc": now.isoformat(), "repos": ordered}, indent=1, ensure_ascii=False), encoding="utf-8")
    lines = [f"# New and rising trading projects (GitHub survey of {now.date()})", "",
             "Metadata only. Open a repository's README or strategy description, restate any RULE in your own words (never copy code), "
             "and record its licence. Skip libraries with no rules. A project's popularity is not evidence that its rule works.", ""]
    for title, group in (("New since the last survey", sorted(new, key=lambda r: -r["stars"])),
                         ("Rising (stars up at least 10%)", sorted(rising, key=lambda r: -r["stars"]))):
        lines += [f"## {title}", ""]
        lines += [f"- https://github.com/{r['name']} ({r['stars']} stars, {r['license'] or 'no licence'}, pushed {r['pushed']}): {r['desc']}"
                  for r in group[:25]] or ["- none"]
        lines.append("")
    (root / NEW_REPORT).write_text("\n".join(lines), encoding="utf-8")
    return {"total": len(ordered), "new": len(new), "rising": len(rising), "failed_queries": failed}


def source_key(url: str) -> str:
    """github.com/owner/repo for repositories, the host name for everything else."""
    match = re.match(r"https?://(?:www\.)?github\.com/([^/]+/[^/#?]+)", url or "", re.I)
    if match:
        return "github:" + match.group(1).lower()
    host = re.match(r"https?://([^/]+)", url or "")
    return host.group(1).lower().removeprefix("www.") if host else "unknown"


def yield_table(conn) -> list[dict]:
    """One row per source: ideas, registered hypotheses, and hypotheses with a pair that cleared the exploration gates."""
    passing = defaultdict(int)
    for row in registry.list_latest_decisions(conn):
        if row["split"] == "exploration" and row["decision"] == "candidate_for_portfolio":
            passing[row["hypothesis_id"]] = 1
    table: dict[str, dict] = {}
    for idea in registry.list_ideas(conn):
        entry = table.setdefault(source_key(idea["source_url"]), {"source": source_key(idea["source_url"]), "ideas": 0, "registered": 0, "passing": 0})
        entry["ideas"] += 1
        if idea["hypothesis_id"]:
            entry["registered"] += 1
            entry["passing"] += passing.get(idea["hypothesis_id"], 0)
    return sorted(table.values(), key=lambda e: (-e["passing"], -e["registered"], -e["ideas"]))


def yield_markdown(conn, limit: int = 15) -> str:
    rows = yield_table(conn)
    if not rows:
        return ""
    lines = ["### Sources used so far (ideas collected, hypotheses registered, hypotheses with a pair passing exploration)",
             "| source | ideas | registered | passing |", "|---|--:|--:|--:|"]
    lines += [f"| {r['source']} | {r['ideas']} | {r['registered']} | {r['passing']} |" for r in rows[:limit]]
    lines += ["", "Spend your time on sources that produced, widen the search where they did not, and never return to a source "
                  "whose ideas all failed unless you read a rule there you have not collected yet.", ""]
    return "\n".join(lines)


def run_and_commit(pipeline) -> str:
    summary = refresh_catalog(pipeline.root)
    pipeline._commit([CATALOG, NEW_REPORT], f"sources: GitHub survey refreshed ({summary['total']} projects, {summary['new']} new, {summary['rising']} rising)")
    return json.dumps(summary)
