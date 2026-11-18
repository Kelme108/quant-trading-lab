"""In-memory stand-in for the `MetaTrader5` package, enough for the adapter tests.

Times are TRADE SERVER epochs (server = UTC + offset), like the real package.
Hooks: `send_retcodes` (queue of retcodes for the next order_send calls),
`check_retcode`, `connected`, `send_returns_none`, `hide_deals`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import SimpleNamespace

TIMEFRAME_M1, TIMEFRAME_M5, TIMEFRAME_M15, TIMEFRAME_M30 = 1, 5, 15, 30
TIMEFRAME_H1, TIMEFRAME_H4, TIMEFRAME_D1 = 16385, 16388, 16408
TRADE_ACTION_DEAL, TRADE_ACTION_REMOVE = 1, 8
ORDER_TYPE_BUY, ORDER_TYPE_SELL = 0, 1
ORDER_FILLING_FOK, ORDER_FILLING_IOC, ORDER_FILLING_RETURN = 0, 1, 2
ORDER_TIME_GTC = 0
POSITION_TYPE_BUY, POSITION_TYPE_SELL = 0, 1
DEAL_TYPE_BUY, DEAL_TYPE_SELL = 0, 1
DEAL_ENTRY_IN, DEAL_ENTRY_OUT, DEAL_ENTRY_INOUT, DEAL_ENTRY_OUT_BY = 0, 1, 2, 3
DEAL_REASON_CLIENT, DEAL_REASON_EXPERT, DEAL_REASON_SL = 0, 3, 4
ACCOUNT_TRADE_MODE_DEMO, ACCOUNT_TRADE_MODE_REAL = 0, 2
ACCOUNT_MARGIN_MODE_RETAIL_NETTING, ACCOUNT_MARGIN_MODE_RETAIL_HEDGING = 0, 2
SYMBOL_FILLING_FOK, SYMBOL_FILLING_IOC = 1, 2


@dataclass
class FakeMT5:
    server_offset_h: float = 2.0
    hedging: bool = False
    trade_mode: int = ACCOUNT_TRADE_MODE_DEMO
    login: int = 5012345
    bid: float = 100.0
    spread: float = 0.1
    tick_size: float = 0.01
    tick_value: float = 0.01
    filling_mode: int = SYMBOL_FILLING_IOC
    commission: float = -0.5
    now_utc: datetime = field(default_factory=lambda: datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc))
    connected: bool = True
    check_retcode: int = 0
    send_retcodes: list = field(default_factory=list)
    send_returns_none: bool = False
    hide_deals: bool = False
    rates: dict = field(default_factory=dict)
    initialize_calls: list = field(default_factory=list)
    sent: list = field(default_factory=list)

    def __post_init__(self) -> None:
        self._positions: dict[int, SimpleNamespace] = {}
        self._deals: list[SimpleNamespace] = []
        self._orders: list[SimpleNamespace] = []
        self._ticket = 1000

    # ---- helpers ----
    def _server_epoch(self) -> int:
        return int(self.now_utc.timestamp() + self.server_offset_h * 3600)

    def _next(self) -> int:
        self._ticket += 1
        return self._ticket

    def _deal(self, symbol, dtype, entry, volume, price, magic, comment, position_id,
              profit=0.0, reason=DEAL_REASON_EXPERT):
        d = SimpleNamespace(ticket=self._next(), symbol=symbol, type=dtype, entry=entry,
                            volume=volume, price=price, magic=magic, comment=comment,
                            position_id=position_id, profit=profit, swap=0.0,
                            commission=self.commission * volume, fee=0.0,
                            time=self._server_epoch(), reason=reason)
        self._deals.append(d)
        return d

    # ---- module API ----
    def initialize(self, **kw):
        self.initialize_calls.append(kw)
        return self.connected

    def shutdown(self):
        return None

    def last_error(self):
        return (1, "fake error")

    def terminal_info(self):
        return SimpleNamespace(connected=True, build=6295) if self.connected else None

    def account_info(self):
        if not self.connected:
            return None
        return SimpleNamespace(login=self.login, trade_mode=self.trade_mode, balance=10_000.0,
                               equity=10_000.0, currency="USD",
                               margin_mode=ACCOUNT_MARGIN_MODE_RETAIL_HEDGING if self.hedging
                               else ACCOUNT_MARGIN_MODE_RETAIL_NETTING)

    def symbol_select(self, symbol, enable=True):
        return symbol != "NOPE"

    def symbol_info(self, symbol):
        return SimpleNamespace(name=symbol, trade_tick_size=self.tick_size,
                               trade_tick_value=self.tick_value, volume_min=0.01,
                               volume_step=0.01, volume_max=100.0, filling_mode=self.filling_mode)

    def symbol_info_tick(self, symbol):
        return SimpleNamespace(bid=self.bid, ask=round(self.bid + self.spread, 8),
                               time=self._server_epoch())

    def copy_rates_from_pos(self, symbol, timeframe, start, count):
        return self.rates.get(symbol, [])[-count:]

    def positions_get(self, symbol=None):
        return tuple(p for p in self._positions.values() if symbol is None or p.symbol == symbol)

    def orders_get(self):
        return tuple(self._orders)

    def history_deals_get(self, date_from, date_to):
        return () if self.hide_deals else tuple(self._deals)

    def order_check(self, request):
        return SimpleNamespace(retcode=self.check_retcode, comment="check")

    def order_send(self, request):
        self.sent.append(dict(request))
        if self.send_returns_none:
            return None
        if request["action"] == TRADE_ACTION_REMOVE:
            self._orders = [o for o in self._orders if o.ticket != request["order"]]
            return SimpleNamespace(retcode=10009, comment="removed")
        if request["action"] == 6:                    # TRADE_ACTION_SLTP: move the stop of one ticket
            if self.send_retcodes and self.send_retcodes[0] != 10009:
                return SimpleNamespace(retcode=self.send_retcodes.pop(0), comment="injected")
            self._positions[request["position"]].sl = request["sl"]
            return SimpleNamespace(retcode=10009, comment="sltp")
        if self.send_retcodes:
            code = self.send_retcodes.pop(0)
            if code != 10009:
                return SimpleNamespace(retcode=code, comment="injected", deal=0)
        symbol, vol, price = request["symbol"], request["volume"], request["price"]
        if "position" in request:                     # close by ticket
            p = self._positions[request["position"]]
            d = self._deal(symbol, DEAL_TYPE_SELL if p.type == POSITION_TYPE_BUY else DEAL_TYPE_BUY,
                           DEAL_ENTRY_OUT, vol, price, request["magic"], request["comment"],
                           p.ticket, profit=(price - p.price_open) * vol)
            p.volume = round(p.volume - vol, 8)
            if p.volume <= 1e-9:
                del self._positions[p.ticket]
            return SimpleNamespace(retcode=10009, deal=d.ticket, price=price, volume=vol)
        ptype = POSITION_TYPE_BUY if request["type"] == ORDER_TYPE_BUY else POSITION_TYPE_SELL
        existing = next((p for p in self._positions.values() if p.symbol == symbol), None)
        if not self.hedging and existing is not None:
            if existing.type == ptype:
                existing.price_open = (existing.price_open * existing.volume + price * vol) / (existing.volume + vol)
                existing.volume += vol
            else:  # netting: an opposite deal reduces the position
                existing.volume = round(existing.volume - vol, 8)
                if existing.volume <= 1e-9:
                    del self._positions[existing.ticket]
            d = self._deal(symbol, request["type"], DEAL_ENTRY_OUT if existing.type != ptype else DEAL_ENTRY_IN,
                           vol, price, request["magic"], request["comment"], existing.ticket)
            return SimpleNamespace(retcode=10009, deal=d.ticket, price=price, volume=vol)
        ticket = self._next()
        self._positions[ticket] = SimpleNamespace(ticket=ticket, symbol=symbol, type=ptype, volume=vol,
                                                  price_open=price, sl=request.get("sl", 0.0),
                                                  magic=request["magic"], comment=request["comment"])
        d = self._deal(symbol, request["type"], DEAL_ENTRY_IN, vol, price, request["magic"],
                       request["comment"], ticket)
        return SimpleNamespace(retcode=10009, deal=d.ticket, price=price, volume=vol)

    # ---- server-side events for tests ----
    def trigger_stop(self, ticket: int, price: float) -> None:
        p = self._positions.pop(ticket)
        self._deal(p.symbol, DEAL_TYPE_SELL, DEAL_ENTRY_OUT, p.volume, price, p.magic,
                   f"[sl {price}]", p.ticket, profit=(price - p.price_open) * p.volume,
                   reason=DEAL_REASON_SL)

    def add_foreign_position(self, symbol: str, volume: float) -> None:
        t = self._next()
        self._positions[t] = SimpleNamespace(ticket=t, symbol=symbol, type=POSITION_TYPE_BUY, volume=volume,
                                             price_open=self.bid, sl=0.0, magic=0, comment="manual")


# The real package exposes its constants on the module object that gets injected.
for _name, _value in list(globals().items()):
    if _name.isupper() and isinstance(_value, int):
        setattr(FakeMT5, _name, _value)
