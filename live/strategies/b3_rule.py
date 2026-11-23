"""A WIN/WDO research rule (b3/strategies, b3/proxy_rules) run by the live engine on a DEMO account.

Owner, 2026-11-16: "Continue o motor de validar estratégias, mas quero apenas demonstração de como está se
portando no demo". This is that demonstration: the rule's own code, unchanged, fed with the demo terminal's
bars of the tradable contract. It is NOT evidence: a demonstration trade never enters the research ledger,
the gates or a validation read. live/run.py refuses it on any account that is not a demo.

What it keeps identical to the backtester (b3/backtest.py):
- only bars inside the regular session (the research data is session-only, b3.markets.session_only);
- the rule's own SessionRules through its B3SessionCalendar (entry window and flatten time);
- the decision on the closed bar; the order goes out right after that close (the backtest fills at the
  next bar's open, the same instant);
- a stop on the server for every entry.
What differs: real fills, real spread and slippage, and the tradable contract (e.g. WINZ26) instead of the
continuous series, so indicators that span a roll see the real gap.
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from live.core.models import Bar, Position, Signal

SKIP_COLUMNS = {"time", "open", "high", "low", "close", "volume", "local_date", "minute_of_day", "bar_in_day",
                "day_open", "minutes_to_close"}


def load_rule(rule_id: str, market: str):
    """The rule class bound to `market` (WIN or WDO), exactly as the research runner builds it."""
    from b3.proxy_rules import RULES
    if rule_id not in RULES:
        raise SystemExit(f"unknown B3 rule {rule_id!r}")
    cls = RULES[rule_id]
    return cls.on(market) if getattr(cls, "symbol", "") != market else cls


class B3RuleStrategy:
    """live.core.engine.Strategy around a B3Strategy / ProxyStrategy instance."""

    def __init__(self, rule_id: str, market: str, snapshot_file: str | Path | None = None, symbol: str = "",
                 take_profit: dict | None = None, esteira: dict | None = None) -> None:
        # Optional DEMO overlay (owner 2026-11-17: "na faixa de 20, 30 ja esta adequado"): exit as soon as the open
        # position's profit, on the last closed bar, reaches take_profit["brl"]. {"brl": 25, "brl_per_point": 0.2}.
        # The rule's own code and hash are untouched; this is a demonstration setting, not a research result.
        self.take_profit = take_profit
        self.rule_id, self.market = rule_id, market
        self.snapshot_file, self.symbol = (Path(snapshot_file) if snapshot_file else None), symbol
        if esteira:                                    # a conveyor family variant + exit-menu exit (b3/esteira_live.py)
            from b3.esteira_live import build
            self.rule = build(rule_id, market, int(esteira["tf"]), dict(esteira["params"]), str(esteira["exit"]),
                              other_market_ok=bool(esteira.get("other_market_ok", False)))()
        else:
            self.rule = load_rule(rule_id, market)()
        self.name = f"demo-{rule_id}-{market}"
        self.hash = self.rule.hash                    # the same hash the research ledger records
        self.timeframe_min = int(self.rule.timeframe_min)
        self.warmup = int(self.rule.warmup)
        self.calendar = self.rule.calendar            # B3SessionCalendar with the rule's own SessionRules
        self.fetch_bars = self.warmup * 2 + 200       # raw bars to ask for: auctions and gaps are dropped below

    def session_bars(self, bars: list[Bar]) -> list[Bar]:
        tf = timedelta(minutes=self.timeframe_min)
        out = []
        for b in bars:
            s = self.calendar.session(b.time.astimezone(self.calendar.tz).date())
            if s is not None and s.open <= b.time and b.time + tf <= s.close:
                out.append(b)
        return out

    def signal(self, bars: list[Bar], position: Position | None) -> Signal:
        kept = self.session_bars(bars)
        if not kept or kept[-1] is not bars[-1]:
            return Signal("hold", reason="bar outside the regular session")
        window = kept[-self.warmup - 4:]
        sig = self.rule.signal(window, position)
        if self.take_profit and position is not None and position.volume:
            side = 1.0 if position.volume > 0 else -1.0
            points = side * (window[-1].close - position.entry_price)
            profit = points * float(self.take_profit["brl_per_point"]) * abs(position.volume)
            if profit >= float(self.take_profit["brl"]):
                sig = Signal("exit", reason=f"demo_take_profit_{self.take_profit['brl']:g}_brl")
        if self.snapshot_file is not None:
            try:
                self._snapshot(window, position, sig)
            except Exception:              # the portal's picture must never stop the robot
                pass
        return sig

    def _snapshot(self, window: list[Bar], position: Position | None, sig: Signal) -> None:
        """What the portal draws (lab/demo_b3.py): today's session bars, the position and the last decision with the
        rule's own indicator values on the last bar. Written atomically after every closed bar."""
        from b3.strategy import bars_to_frame
        last = self.rule.prepare(bars_to_frame(window)).iloc[-1]
        ind = {}
        for k, v in last.items():
            if k not in SKIP_COLUMNS and isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v)):
                ind[str(k)] = float(v)
        day = window[-1].time.astimezone(self.calendar.tz).date()
        s = self.calendar.session(day)
        today = [b for b in window if b.time.astimezone(self.calendar.tz).date() == day]
        prev = [b for b in window if b.time.astimezone(self.calendar.tz).date() < day]
        out = {
            "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "rule": self.rule_id, "market": self.market, "symbol": self.symbol, "strategy_hash": self.hash,
            "timeframe_min": self.timeframe_min, "day": day.isoformat(),
            "session": {k: getattr(s, k).isoformat() for k in ("open", "entry_start", "entry_end", "flatten_at", "close")} if s else None,
            "prev_close": prev[-1].close if prev else None,
            "bars": [[int(b.time.timestamp()), b.open, b.high, b.low, b.close, b.volume] for b in today],
            "position": {"volume": position.volume, "entry_price": position.entry_price, "stop": position.stop_loss} if position else None,
            "last_signal": {"bar": int(window[-1].time.timestamp()), "action": sig.action, "reason": sig.reason, "stop": sig.stop_price,
                            "close": window[-1].close},
            "indicators": ind,
        }
        self.snapshot_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.snapshot_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(out), encoding="utf-8")
        os.replace(tmp, self.snapshot_file)
