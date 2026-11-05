"""Immutable value objects shared by the engine and every broker adapter.

Long-only by design (decision recorded in live/DECISIONS.md): a Position
volume is always > 0, and a "sell" order only ever reduces a position.
All datetimes are timezone-aware UTC. A Bar's `time` is its OPEN time.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Bar:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass(frozen=True)
class SymbolSpec:
    """Contract specification. Adapters must read it from the server."""

    symbol: str
    tick_size: float
    tick_value: float  # account currency per tick per contract
    volume_min: float = 1.0
    volume_step: float = 1.0
    volume_max: float = 1000.0


@dataclass(frozen=True)
class Position:
    symbol: str
    volume: float
    entry_price: float
    stop_loss: float | None = None


@dataclass(frozen=True)
class Signal:
    action: str  # "enter" | "exit" | "hold"
    stop_price: float | None = None
    reason: str = ""


@dataclass(frozen=True)
class OrderRequest:
    client_id: str
    symbol: str
    side: str  # "buy" | "sell"
    volume: float
    stop_loss: float | None = None
    reduce_only: bool = False
    reason: str = ""


@dataclass(frozen=True)
class Fill:
    client_id: str
    symbol: str
    side: str
    volume: float
    price: float
    time: datetime
    cost: float = 0.0
    pnl: float | None = None  # net realised PnL, set only on closing fills
    reason: str = ""


@dataclass(frozen=True)
class OrderResult:
    accepted: bool
    client_id: str
    fill: Fill | None = None
    retcode: str = ""
    message: str = ""


@dataclass(frozen=True)
class AccountState:
    balance: float
    equity: float
    is_demo: bool
    account_id: str = ""
