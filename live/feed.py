"""Live picture of one contract for the portal (lab/demo_b3.py, page #/b3-demo): today's 1-minute session bars
INCLUDING the forming one, the last bid/ask, and the engine's own position with its open result.

Written by live/run.py every `feed_every_s` seconds (default 5) when the config names a `feed_file`. Read-only on
the broker: no order, no change. A failure here is logged and never stops the engine.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

FEED_BARS = 700          # more than one session of 1-minute bars (09:00-18:30 is 570)


def build_feed(broker, strategy, symbol: str, now: datetime) -> dict:
    cal = strategy.calendar
    tz = cal.tz
    bars = broker.bars(symbol, 1, FEED_BARS)

    def in_session(b) -> bool:
        s = cal.session(b.time.astimezone(tz).date())
        return s is not None and s.open <= b.time < s.close

    session = [b for b in bars if in_session(b)]
    day = session[-1].time.astimezone(tz).date() if session else now.astimezone(tz).date()
    today = [b for b in session if b.time.astimezone(tz).date() == day]
    tick = broker.mt5.symbol_info_tick(symbol)
    bid, ask = (float(tick.bid), float(tick.ask)) if tick is not None else (None, None)
    last = float(getattr(tick, "last", 0) or 0) if tick is not None else 0.0
    if not last:
        last = today[-1].close if today else None
    pos = next((p for p in broker.positions() if p.symbol == symbol), None)
    position = None
    if pos is not None:
        spec = broker.symbol_spec(symbol)
        mark = (bid if pos.volume > 0 else ask) or last
        position = {"volume": pos.volume, "entry_price": pos.entry_price, "stop": pos.stop_loss,
                    "open_result_brl": round((mark - pos.entry_price) / spec.tick_size * spec.tick_value * pos.volume, 2)
                    if mark else None, "mark": mark}
    return {"updated_at": now.astimezone(timezone.utc).isoformat(timespec="seconds"), "symbol": symbol,
            "day": day.isoformat(), "bid": bid, "ask": ask, "last": last, "position": position,
            "bars_1m": [[int(b.time.timestamp()), b.open, b.high, b.low, b.close, b.volume] for b in today]}


def write_feed(path: str | Path, feed: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(feed), encoding="utf-8")
    os.replace(tmp, p)
