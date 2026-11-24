"""Operator commands for one running robot: a small JSON file the portal writes and the ENGINE consumes.

Why a file and not a call to the broker: when somebody closes a position behind the engine's back the journal and the
broker disagree, the engine enters safe mode and the portal keeps showing a position that no longer exists. Here the
engine itself executes the command with its own broker, so the fill goes through the journal like any other exit.

    live/commands/<robot>.json     {"id": "<unique>", "action": "close|pause|resume|close_stop|stop", "at": "<utc iso>"}

The portal only ever writes this file (atomically); the engine reads it every step, journals a `command` event keyed by
the id (so a command is executed once even if the engine dies between acting and deleting the file) and then removes it.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

ACTIONS = ("close", "pause", "resume", "close_stop", "stop")


def new_id() -> str:
    return uuid.uuid4().hex


def write_command(path: str | Path, action: str, cid: str | None = None, source: str = "portal") -> str:
    """Write the pending command atomically (temp file + replace). Returns its id."""
    if action not in ACTIONS:
        raise ValueError(f"unknown action {action!r}")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    cid = cid or new_id()
    tmp = p.with_name(p.name + f".{cid}.tmp")
    tmp.write_text(json.dumps({"id": cid, "action": action, "source": source,
                               "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}), encoding="utf-8")
    os.replace(tmp, p)
    return cid


def read_command(path: str | Path) -> dict | None:
    """The pending command, or None (missing, unreadable, malformed or unknown action: never acted on)."""
    try:
        cmd = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(cmd, dict) or cmd.get("action") not in ACTIONS or not isinstance(cmd.get("id"), str) or not cmd["id"]:
        return None
    return cmd


class Control:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def peek(self) -> dict | None:
        return read_command(self.path)

    def done(self, cmd: dict) -> None:
        """Remove the file only if it still holds the command just handled (a newer one stays)."""
        now = read_command(self.path)
        if now is not None and now["id"] != cmd["id"]:
            return
        try:
            self.path.unlink()
        except OSError:
            pass
