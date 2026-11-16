"""Order-path smoke strategy. NOT a trading strategy; demo accounts only.

Enters on the first closed bar with no position, exits on the next closed bar,
always with a server-side stop `stop_ticks` ticks below the last close. It
exists to exercise connect -> order -> stop -> fill -> journal on the MT5 demo.
`live/run.py` refuses to run it unless the account is a demo.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

from live.core.models import Bar, Position, Signal

CODE_HASH = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


class SmokeStrategy:
    name = "smoke"
    warmup = 2

    def __init__(self, timeframe_min: int, tick_size: float, stop_ticks: int = 50) -> None:
        self.timeframe_min, self.tick_size, self.stop_ticks = timeframe_min, tick_size, stop_ticks
        params = f"{timeframe_min}:{tick_size}:{stop_ticks}".encode()
        self.hash = hashlib.sha256(CODE_HASH.encode() + params).hexdigest()[:12]

    def stop_for(self, close: float) -> float:
        raw = close - self.stop_ticks * self.tick_size
        n = math.floor(raw / self.tick_size + 1e-9)
        return round(n * self.tick_size, 10)

    def signal(self, bars: list[Bar], position: Position | None) -> Signal:
        if position is None:
            return Signal("enter", stop_price=self.stop_for(bars[-1].close), reason="smoke entry")
        return Signal("exit", reason="smoke exit after one bar")
