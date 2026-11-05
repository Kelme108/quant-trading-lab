"""Shared fixtures for the live-layer tests: a replayable WIN session.

Time map (America/Sao_Paulo = UTC-3, Wednesday 2026-11-04):
bar k opens at T0 + 5k min (T0 = 09:00 BRT) and closes at T0 + 5(k+1).
`Rig.after(k)` = the moment bar k has just closed.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from live.brokers.paper import PaperBroker, PaperConfig
from live.core.clock import B3Calendar, FakeClock
from live.core.engine import Engine
from live.core.journal import Journal
from live.core.killswitch import KillSwitch
from live.core.models import Bar, Position, Signal, SymbolSpec
from live.core.risk import RiskConfig, RiskManager

UTC = timezone.utc
T0 = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)  # 09:00 BRT
TF = 5
SYMBOL = "WINZ26"
SPEC = SymbolSpec(SYMBOL, tick_size=5.0, tick_value=1.0, volume_min=1.0, volume_step=1.0)
BASE = 130000.0


def make_bars(closes, start=T0, tf=TF, base=BASE) -> list[Bar]:
    bars, prev = [], base
    for i, c in enumerate(closes):
        o = prev
        bars.append(Bar(start + timedelta(minutes=tf * i), o, max(o, c) + 5,
                        min(o, c) - 5, c, 100.0))
        prev = c
    return bars


def pad(closes, total=130):
    return list(closes) + [closes[-1]] * (total - len(closes))


class RisingStrategy:
    """Enter after two consecutive higher closes (stop 100 pts below); exit on a lower close."""

    name, hash, timeframe_min, warmup = "rising", "abcdef123456", TF, 3
    stop_points = 100.0

    def signal(self, bars: list[Bar], position: Position | None) -> Signal:
        a, b, c = bars[-3].close, bars[-2].close, bars[-1].close
        if position is None:
            if c > b > a:
                return Signal("enter", stop_price=c - self.stop_points, reason="rising")
            return Signal("hold")
        return Signal("exit", reason="lower close") if c < b else Signal("hold")


# Scenario A: one clean round trip. Entry signal after bar 4, exit after bar 6.
SCENARIO_A = pad([BASE] * 3 + [130050, 130100, 130150, 130100])
# Scenario B: entry after bar 5, stopped out in bar 6 (-22 BRL), rising again from bar 8.
SCENARIO_B = pad([BASE] * 4 + [130050, 130100, 129900, 130000, 130050, 130100])


class Rig:
    def __init__(self, tmp_path, closes, risk: RiskConfig | None = None,
                 paper: PaperConfig | None = None, strategy=None, n_bars=None,
                 calendar: B3Calendar | None = None) -> None:
        bars = make_bars(closes)
        if n_bars is not None:
            bars = bars[:n_bars]
        self.clock = FakeClock(T0)
        self.broker = PaperBroker(self.clock, {SYMBOL: SPEC}, paper or PaperConfig(0.5, 1.0))
        self.broker.load_bars(SYMBOL, bars, TF)
        self.strategy = strategy or RisingStrategy()
        self.cal = calendar or B3Calendar()
        self.risk = RiskManager(risk or RiskConfig())
        self.journal = Journal(tmp_path / "journal.sqlite", self.clock, self.strategy.name)
        self.ks = KillSwitch(tmp_path / "STOP")
        self.alerts: list[str] = []
        self.engine = self.new_engine()

    def new_engine(self) -> Engine:
        return Engine(self.broker, self.strategy, self.clock, self.cal, self.journal,
                      self.risk, self.ks, [SYMBOL], volume=1.0, alert=self.alerts.append)

    def after(self, k: int) -> list[str]:
        """Move the clock to the close of bar k and run one engine step."""
        self.clock.set(T0 + timedelta(minutes=TF * (k + 1)))
        self.broker.sync()
        return self.engine.step()

    def run(self, first: int, last: int) -> list[list[str]]:
        return [self.after(k) for k in range(first, last + 1)]

    def kinds(self, kind: str) -> list[dict]:
        return self.journal.events(kind)

    def with_risk(self, **kw) -> RiskConfig:
        return replace(RiskConfig(), **kw)
