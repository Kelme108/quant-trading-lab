"""`Trade.get_trades_proxy` for the strategies' confirm_trade_entry, fed by b3/freqtrade_adapter.py."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, ClassVar


@dataclass
class Trade:
    pair: str
    open_date_utc: datetime
    open_rate: float
    enter_tag: str | None = None
    fee_open: float = 0.0
    fee_close: float = 0.0
    is_open: bool = True
    close_date_utc: datetime | None = None
    close_rate: float | None = None
    exit_reason: str | None = None
    stop_loss: float | None = None
    is_short: bool = False
    leverage: float = 1.0
    amount: float = 1.0

    _registry: ClassVar[Callable | None] = None     # set by the adapter: callable(pair) -> list[Trade]

    @property
    def open_date(self) -> datetime:
        return self.open_date_utc

    @property
    def close_date(self) -> datetime | None:
        return self.close_date_utc

    def calc_profit_ratio(self, rate: float) -> float:
        return rate / self.open_rate * (1 - self.fee_close) / (1 + self.fee_open) - 1.0

    @classmethod
    def get_trades_proxy(cls, pair: str | None = None, is_open: bool | None = None, **_kw) -> list["Trade"]:
        trades = list(cls._registry(pair)) if cls._registry else []
        if is_open is not None:
            trades = [t for t in trades if t.is_open == is_open]
        return trades
