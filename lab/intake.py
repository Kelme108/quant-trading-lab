"""Strict validation and ingestion of the scout agent's strategy ideas.

An idea is a RULE described in words, found in a paper, an article or a repository's documentation. It is data produced
by an agent that reads the web, so it is held to a fixed schema with length caps; unknown keys are rejected and the
source must be an https URL. No third-party code is ever copied, run or stored: the developer agent later
reimplements the rule from scratch, and the source licence is only recorded for attribution.

An idea carries no backtest result. `expected_trades_per_year` is the scout's design estimate, used by lab/triage.py
as a cheap pre-filter and checked for real by the calibration step (fewer than 30 trades on a pair drops the
hypothesis).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Callable

from lab import registry
from lab.proposals import FAMILY, HTTPS_URL

ROOT = Path(__file__).parents[1]
INTAKE_DIR = ROOT / "research" / "intake"

REQUIRED_KEYS = (
    "title", "source", "rule_summary", "mechanism", "timeframe", "longest_lookback", "free_parameters",
    "fixed_parameters", "expected_trades_per_year", "family_hint",
)
SOURCE_KEYS = ("type", "url", "title", "license")
SOURCE_TYPES = ("paper", "blog", "repo")
TIMEFRAMES = ("1h", "1d")  # 1d = daily signals via the closed daily candle, executed on 1h
TEXT_LIMITS = {"title": (5, 120), "rule_summary": (60, 1500), "mechanism": (40, 1000)}
CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")

STOPWORDS = frozenset(
    "the and for with when this that then than from into over under above below close open high low price prices "
    "bar bars day days daily hour hours candle candles long only entry enter exit exits buy sell use used uses using "
    "above below cross crosses crossing rule signal signals trade trades position positions period periods value "
    "values average moving each per any all are was were will can not but its their they also may more less".split()
)


def intake_path(name: str, directory: Path = INTAKE_DIR) -> Path:
    return directory / f"{name}.json"


def load_idea(path: Path) -> tuple[dict | None, list[str]]:
    if not path.is_file():
        return None, [f"{path.name} was not written"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return None, [f"{path.name} is not valid JSON: {error}"]
    if not isinstance(data, dict):
        return None, [f"{path.name} must contain a JSON object"]
    return data, []


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_idea(idea: dict) -> list[str]:
    """Every problem found; an empty list means the idea is acceptable."""
    errors: list[str] = []
    unknown = sorted(set(idea) - set(REQUIRED_KEYS))
    if unknown:
        errors.append(f"unknown key(s): {unknown}")
    missing = [key for key in REQUIRED_KEYS if key not in idea]
    if missing:
        errors.append(f"missing key(s): {missing}")
        return errors

    for key, (low, high) in TEXT_LIMITS.items():
        value = idea[key]
        if not isinstance(value, str) or not low <= len(value.strip()) <= high:
            errors.append(f"{key} must be text of {low}-{high} characters")
        elif CONTROL.search(value):
            errors.append(f"{key} contains control characters")

    source = idea["source"]
    if not isinstance(source, dict) or set(source) != set(SOURCE_KEYS):
        errors.append(f"source must be an object with exactly {list(SOURCE_KEYS)}")
    else:
        if source["type"] not in SOURCE_TYPES:
            errors.append(f"source.type must be one of {list(SOURCE_TYPES)}")
        if not isinstance(source["url"], str) or not HTTPS_URL.match(source["url"]):
            errors.append("source.url must be an https URL")
        if not isinstance(source["title"], str) or not 3 <= len(source["title"]) <= 200:
            errors.append("source.title must be 3-200 characters")
        if not isinstance(source["license"], str) or not 2 <= len(source["license"].strip()) <= 60:
            errors.append("source.license must be 2-60 characters (use 'unknown' or 'none' when there is none)")

    if idea["timeframe"] not in TIMEFRAMES:
        errors.append(f"timeframe must be one of {list(TIMEFRAMES)}")
    if not _is_int(idea["longest_lookback"]) or not 1 <= idea["longest_lookback"] <= 100000:
        errors.append("longest_lookback must be an integer number of bars (1 to 100000)")
    if not _is_int(idea["free_parameters"]) or not 0 <= idea["free_parameters"] <= 30:
        errors.append("free_parameters must be an integer from 0 to 30")
    if not isinstance(idea["fixed_parameters"], bool):
        errors.append("fixed_parameters must be true or false")
    trades = idea["expected_trades_per_year"]
    if isinstance(trades, bool) or not isinstance(trades, (int, float)) or not 0 <= trades <= 1000:
        errors.append("expected_trades_per_year must be a number from 0 to 1000")
    if not isinstance(idea["family_hint"], str) or not FAMILY.match(idea["family_hint"]):
        errors.append("family_hint must be 3-40 letters/digits, starting with a letter")
    return errors


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9% ]+", " ", text.lower())).strip()


def rule_hash(idea: dict) -> str:
    return hashlib.sha256(normalise(idea["rule_summary"]).encode("utf-8")).hexdigest()


def tokens(text: str) -> frozenset[str]:
    """Content words of a rule, for the overlap measure used to spot a re-proposed mechanism."""
    return frozenset(w for w in normalise(text).split() if len(w) >= 3 and w not in STOPWORDS and not w.isdigit())


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def ingest_file(conn, path: Path, run_id: str, now: Callable[[], str]) -> tuple[str | None, list[str]]:
    """Validate one idea file and add it to the queue as 'new'. Returns (idea id, []) or (None, reasons)."""
    idea, errors = load_idea(path)
    if idea is None:
        return None, errors
    errors = validate_idea(idea)
    if errors:
        return None, errors
    digest = rule_hash(idea)
    for row in registry.list_ideas(conn):
        if row["rule_hash"] == digest:
            return None, [f"same rule text as {row['id']}"]
        if row["source_url"] == idea["source"]["url"] and row["title"].strip().lower() == idea["title"].strip().lower():
            return None, [f"same source and title as {row['id']}"]
    idea_id = registry.next_idea_id(conn)
    registry.add_idea(conn, idea_id=idea_id, run_id=run_id, idea=idea, rule_hash=digest, created_at_utc=now())
    return idea_id, []


def ingest_run(conn, paths: list[Path], run_id: str, now: Callable[[], str]) -> list[dict]:
    """Ingest every idea file a scout call wrote (missing files are fine: the scout may find fewer ideas)."""
    outcomes = []
    for path in paths:
        if not path.is_file():
            continue
        idea_id, reasons = ingest_file(conn, path, run_id, now)
        outcomes.append({"file": path.name, "idea_id": idea_id, "rejected": reasons})
    return outcomes
