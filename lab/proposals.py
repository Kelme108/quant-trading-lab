"""Strict validation of the research agent's proposal JSON.

The proposal is data produced by an agent that reads the web, and it is later
read by the developer agent. So it is held to a fixed schema with length caps,
unknown keys are rejected, and sources must be https URLs: it cannot grow into
a channel for arbitrary instructions, and a malformed one is stopped before a
hypothesis is registered (a hypothesis must be registered before any test).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

from lab.strategy_check import MAX_STARTUP_CANDLES

ROOT = Path(__file__).parents[1]
PROPOSALS_DIR = ROOT / "research" / "proposals"

REQUIRED_KEYS = (
    "hypothesis_id",
    "family",
    "title",
    "ex_ante_rule",
    "parameters",
    "rationale",
    "novelty_vs_tried",
    "sources",
    "timeframe",
    "data_visible_at_proposal",
)

WARMUP = re.compile(r"warm-?up\s*:?\s*(\d[\d,._]*)\s*(?:bars|candles)", re.IGNORECASE)
FAMILY = re.compile(r"^[A-Za-z][A-Za-z0-9]{2,39}$")
HYPOTHESIS_ID = re.compile(r"^H-\d{3}$")
HTTPS_URL = re.compile(r"^https://[A-Za-z0-9.-]+(:\d+)?(/[^\s]*)?$")

# (min, max) length in characters for each text field.
TEXT_LIMITS = {
    "title": (5, 120),
    "ex_ante_rule": (60, 3000),
    "rationale": (60, 2000),
    "novelty_vs_tried": (30, 1500),
    "data_visible_at_proposal": (5, 300),
}


def proposal_path(hypothesis_id: str, directory: Path = PROPOSALS_DIR) -> Path:
    return directory / f"{hypothesis_id}.json"


def load_proposal(path: Path) -> tuple[dict | None, list[str]]:
    """(proposal, []) when the file is a JSON object, else (None, [reason])."""
    if not path.is_file():
        return None, [f"{path.name} was not written"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return None, [f"{path.name} is not valid JSON: {error}"]
    if not isinstance(data, dict):
        return None, [f"{path.name} must contain a JSON object"]
    return data, []


def validate_proposal(
    proposal: dict,
    *,
    expected_id: str,
    enabled_timeframes: list[str],
    variants_in_family: Callable[[str], int],
    max_variants_per_family: int,
) -> list[str]:
    """Every problem found; an empty list means the proposal is acceptable."""
    errors: list[str] = []

    unknown = sorted(set(proposal) - set(REQUIRED_KEYS))
    if unknown:
        errors.append(f"unknown key(s): {unknown}")
    missing = [key for key in REQUIRED_KEYS if key not in proposal]
    if missing:
        errors.append(f"missing key(s): {missing}")
        return errors

    if proposal["hypothesis_id"] != expected_id or not HYPOTHESIS_ID.match(str(proposal["hypothesis_id"])):
        errors.append(f"hypothesis_id must be exactly '{expected_id}'")

    family = proposal["family"]
    if not isinstance(family, str) or not FAMILY.match(family):
        errors.append("family must be 3-40 letters/digits, starting with a letter")
    elif variants_in_family(family) >= max_variants_per_family:
        errors.append(
            f"family '{family}' already has {variants_in_family(family)} variant(s); "
            f"the cap is {max_variants_per_family}. Propose something structurally different."
        )

    for key, (low, high) in TEXT_LIMITS.items():
        value = proposal[key]
        if not isinstance(value, str) or not low <= len(value.strip()) <= high:
            errors.append(f"{key} must be text of {low}-{high} characters")

    parameters = proposal["parameters"]
    if not isinstance(parameters, dict) or not parameters or len(parameters) > 30:
        errors.append("parameters must be a non-empty object with at most 30 entries")
    else:
        for name, value in parameters.items():
            if not isinstance(name, str) or not re.match(r"^[A-Za-z_][A-Za-z0-9_]{0,39}$", name):
                errors.append(f"parameter name '{name}' is not a simple identifier")
            if not isinstance(value, (bool, int, float, str)):
                errors.append(f"parameter '{name}' must be a number, a boolean or a short string")
            elif isinstance(value, str) and len(value) > 60:
                errors.append(f"parameter '{name}' string value is too long")

    # Feasibility BEFORE registration: a lookback the engine cannot load would otherwise be
    # registered, consume a variant, and fail at the first backtest (H-006).
    rule = proposal["ex_ante_rule"] if isinstance(proposal["ex_ante_rule"], str) else ""
    stated = WARMUP.search(rule)
    if not stated:
        errors.append("ex_ante_rule must state the warm-up as 'Warm-up: N bars' (the longest lookback including slope lags)")
    elif int(re.sub(r"[,._]", "", stated.group(1))) > MAX_STARTUP_CANDLES:
        errors.append(f"warm-up above {MAX_STARTUP_CANDLES} bars is not loadable by Freqtrade on 1h; shorten the lookbacks")
    if isinstance(parameters, dict):
        for name, value in parameters.items():
            if isinstance(value, int) and not isinstance(value, bool) and value > MAX_STARTUP_CANDLES:
                errors.append(f"parameter '{name}' = {value} is above {MAX_STARTUP_CANDLES} bars; Freqtrade cannot load that much 1h history")

    if proposal["timeframe"] not in enabled_timeframes:
        errors.append(f"timeframe must be one of {enabled_timeframes}")

    sources = proposal["sources"]
    if not isinstance(sources, list) or not 1 <= len(sources) <= 10:
        errors.append("sources must be a list of 1-10 entries")
    else:
        for index, source in enumerate(sources):
            if not isinstance(source, dict) or set(source) != {"title", "url"}:
                errors.append(f"sources[{index}] must have exactly 'title' and 'url'")
                continue
            if not isinstance(source["title"], str) or not 3 <= len(source["title"]) <= 200:
                errors.append(f"sources[{index}].title must be 3-200 characters")
            if not isinstance(source["url"], str) or not HTTPS_URL.match(source["url"]):
                errors.append(f"sources[{index}].url must be an https URL")

    return errors
