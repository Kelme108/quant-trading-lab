"""Kill switch: a sentinel file. While it exists the engine cancels orders,
flattens positions and opens nothing. The engine never deletes it; only the
operator does, on purpose.

Trigger from a shell:   python -m live.core.killswitch live/STOP "motivo"
"""

from __future__ import annotations

import sys
from pathlib import Path


class KillSwitch:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def active(self) -> bool:
        return self.path.exists()

    def token(self) -> str:
        """Changes on each new activation (file mtime), so each is logged once."""
        return str(self.path.stat().st_mtime_ns) if self.active() else ""

    def reason(self) -> str:
        try:
            return self.path.read_text(encoding="utf-8").strip()
        except OSError:
            return ""

    def trigger(self, reason: str = "manual") -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(reason, encoding="utf-8")


if __name__ == "__main__":
    KillSwitch(sys.argv[1] if len(sys.argv) > 1 else "live/STOP").trigger(
        sys.argv[2] if len(sys.argv) > 2 else "manual")
    print("kill switch ativado")
