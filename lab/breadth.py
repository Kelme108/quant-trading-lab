"""Breadth rule for a multi-pair universe (lab/config/breadth.json): how many pairs must pass, and where."""

from __future__ import annotations

import json
import math
from pathlib import Path

PATH = Path(__file__).parent / "config" / "breadth.json"


def load(path: Path = PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def exploration_min_pairs(n_pairs: int, config: dict | None = None) -> int:
    """K of N: 3 of 3, 6 of 9 with the shipped config."""
    config = config if config is not None else load()
    k = max(int(config["exploration_min_pairs_floor"]), math.ceil(float(config["exploration_min_pairs_fraction"]) * n_pairs))
    return min(n_pairs, k)


def validation_min_pairs(config: dict | None = None) -> int:
    config = config if config is not None else load()
    return int(config["validation_min_pairs"])


def causality_check_pairs(enabled: list[str], config: dict | None = None) -> list[str]:
    """The enabled pairs the causality checks run on (all enabled pairs when none of the configured ones is enabled)."""
    config = config if config is not None else load()
    chosen = [p for p in enabled if p in config.get("causality_check_pairs", [])]
    return chosen or list(enabled)
