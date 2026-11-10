"""H-001 for the dry-run: the SmaTrendBaseline reference strategy, unchanged, under the H-001 name the freeze needs.

The rule is the one in SmaTrendBaseline.py (SMA20 crossing above SMA50 with the close above SMA200, exit on the opposite cross,
stop -10%, 1h chart, long only). This file adds nothing to it. The baseline file is protected, so instead of copying it
this class inherits it and REFUSES TO LOAD if the baseline's SHA-256 is not the one recorded below: a change to the baseline
can then never reach a frozen bot unnoticed. Owner request 2026-11-10 (H-001 in dry-run; exposure 0.20 from the lab's
bootstrap on its exploration trades).
"""

import hashlib
from pathlib import Path

from SmaTrendBaseline import SmaTrendBaseline

_BASELINE_SHA256 = "0edc921c5e0b507dcf7b9128aeebb54e624d68d6e4f5d13e8874218e6fadebcc"
_actual = hashlib.sha256((Path(__file__).parent / "SmaTrendBaseline.py").read_bytes()).hexdigest()
if _actual != _BASELINE_SHA256:
    raise RuntimeError(f"SmaTrendBaseline.py changed (sha256 {_actual[:12]}); H-001 dry-run refuses to load")


class SmaTrendBaseline_H001_v1(SmaTrendBaseline):
    """Same rule, same numbers, as the baseline."""
