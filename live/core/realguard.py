"""Gate between this code and real money.

`trading_blockers()` returns the list of reasons trading must NOT proceed
(empty list = allowed). Real orders need ALL of:
  1. env LIVE_MODE=real
  2. live config has allow_real=true AND its SHA-256 equals the hash the user
     recorded in the .sha256 file
  3. the account is a real one AND its id equals env LIVE_ACCOUNT_ID
  4. the strategy hash is approved in the registry (caller passes the verdict)
In any other mode, a real account is refused outright.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping


def file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def trading_blockers(env: Mapping[str, str], config_path: str | Path,
                     sha_path: str | Path, account_is_demo: bool, account_id: str,
                     strategy_approved: bool) -> list[str]:
    mode = env.get("LIVE_MODE", "demo").strip().lower()
    if mode != "real":
        return ["real_account_in_non_real_mode"] if not account_is_demo else []

    why: list[str] = []
    cfg, sha = Path(config_path), Path(sha_path)
    try:
        allow = bool(json.loads(cfg.read_text(encoding="utf-8")).get("allow_real", False))
    except (OSError, ValueError):
        allow = False
    if not allow:
        why.append("config_allow_real_false")
    try:
        recorded = sha.read_text(encoding="utf-8").strip().lower()
        if not cfg.exists() or recorded != file_sha256(cfg):
            why.append("config_sha_mismatch")
    except OSError:
        why.append("config_sha_missing")
    if account_is_demo:
        why.append("account_is_demo_but_mode_real")
    expected = env.get("LIVE_ACCOUNT_ID", "")
    if not expected or account_id != expected:
        why.append("account_id_mismatch")
    if not strategy_approved:
        why.append("strategy_not_approved")
    return why
