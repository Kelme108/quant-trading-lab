"""MetaTrader 5 adapter implementing live.core.broker.Broker.

Runs only on Windows, with the MT5 terminal installed on the same host. The
`MetaTrader5` module is injected (tests pass a fake), so importing this file
never needs the terminal.

Design notes (each has a test in tests/live/test_mt5_adapter.py):
- Contract specs are read from the server (`symbol_info`), never hard-coded.
- Bar times: MT5 returns them in TRADE SERVER time. `server_utc_offset_hours`
  (required in the config) converts them to UTC so the engine's closed-candle
  filter works. `estimate_server_offset()` helps confirm the value.
- Every order goes through `order_check` before `order_send`. The stop-loss is
  attached to the position ON THE SERVER (`sl`), never kept only in Python.
- Exits always close BY POSITION TICKET. On a hedging account a plain sell
  would open a short; by default this adapter can never open a short.
  `allow_short=True` (demo only, enforced by live/run.py) lets a non-reduce
  SELL open a short with its stop above, and a reduce BUY close SELL tickets.
- Idempotency: `magic` identifies this engine, `comment` carries the client id
  (hashed when longer than MT5 allows). `send` checks the deal history before
  sending, so a resend after a restart does not duplicate.
- Requote / price-changed are retried with a fresh price (nothing executed).
  Timeout / connection loss raise, so the engine asks `find_fill`.
- Server-originated exits (stop-loss, stop-out, manual close in the terminal)
  are delivered by `drain_fills` with client id `deal-<ticket>`; the journal
  de-duplicates on that key, so a restart never double counts.
"""

from __future__ import annotations

import hashlib
import logging
import time as _time
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from live.core.models import (
    AccountState, Bar, Fill, OrderRequest, OrderResult, Position, SymbolSpec,
)

log = logging.getLogger("live.mt5")
UTC = timezone.utc

COMMENT_MAX = 31

TIMEFRAMES = {1: "TIMEFRAME_M1", 5: "TIMEFRAME_M5", 15: "TIMEFRAME_M15", 30: "TIMEFRAME_M30",
              60: "TIMEFRAME_H1", 240: "TIMEFRAME_H4", 1440: "TIMEFRAME_D1"}

# Defaults equal the MetaTrader5 package constants; the module's own values win.
_DEFAULTS = {
    "TRADE_ACTION_DEAL": 1, "TRADE_ACTION_REMOVE": 8, "TRADE_ACTION_SLTP": 6,
    "ORDER_TYPE_BUY": 0, "ORDER_TYPE_SELL": 1,
    "ORDER_FILLING_FOK": 0, "ORDER_FILLING_IOC": 1, "ORDER_FILLING_RETURN": 2,
    "ORDER_TIME_GTC": 0,
    "POSITION_TYPE_BUY": 0, "POSITION_TYPE_SELL": 1,
    "DEAL_TYPE_BUY": 0, "DEAL_TYPE_SELL": 1,
    "DEAL_ENTRY_IN": 0, "DEAL_ENTRY_OUT": 1, "DEAL_ENTRY_INOUT": 2, "DEAL_ENTRY_OUT_BY": 3,
    "DEAL_REASON_EXPERT": 3,
    "ACCOUNT_TRADE_MODE_DEMO": 0, "ACCOUNT_MARGIN_MODE_RETAIL_HEDGING": 2,
    "SYMBOL_FILLING_FOK": 1, "SYMBOL_FILLING_IOC": 2,
}

RETCODES = {
    10004: "REQUOTE", 10006: "REJECT", 10007: "CANCEL", 10008: "PLACED", 10009: "DONE",
    10010: "DONE_PARTIAL", 10011: "ERROR", 10012: "TIMEOUT", 10013: "INVALID",
    10014: "INVALID_VOLUME", 10015: "INVALID_PRICE", 10016: "INVALID_STOPS",
    10017: "TRADE_DISABLED", 10018: "MARKET_CLOSED", 10019: "NO_MONEY",
    10020: "PRICE_CHANGED", 10021: "PRICE_OFF", 10022: "INVALID_EXPIRATION",
    10023: "ORDER_CHANGED", 10024: "TOO_MANY_REQUESTS", 10025: "NO_CHANGES",
    10026: "SERVER_DISABLES_AT", 10027: "CLIENT_DISABLES_AT", 10028: "LOCKED",
    10029: "FROZEN", 10030: "INVALID_FILL", 10031: "CONNECTION", 10032: "ONLY_REAL",
    10033: "LIMIT_ORDERS", 10034: "LIMIT_VOLUME", 10035: "INVALID_ORDER",
    10036: "POSITION_CLOSED", 10038: "INVALID_CLOSE_VOLUME", 10039: "CLOSE_ORDER_EXIST",
    10040: "LIMIT_POSITIONS", 10041: "REJECT_CANCEL", 10042: "LONG_ONLY", 10043: "SHORT_ONLY",
    10044: "CLOSE_ONLY", 10045: "FIFO_CLOSE",
}
OK_SEND = {10009, 10010}
RETRY_PRICE = {10004, 10020, 10021}
UNKNOWN_OUTCOME = {10012, 10031}


def retcode_name(code: int) -> str:
    return RETCODES.get(code, f"RETCODE_{code}")


def comment_for(client_id: str) -> str:
    """MT5 comments are short; long client ids are replaced by a stable hash."""
    if len(client_id) <= COMMENT_MAX:
        return client_id
    return "h:" + hashlib.sha1(client_id.encode()).hexdigest()[: COMMENT_MAX - 2]


class MT5Unavailable(ConnectionError):
    """The terminal is not reachable after the reconnect attempts."""


class MT5Broker:
    def __init__(self, mt5: Any, *, magic: int, server_utc_offset_hours: float,
                 path: str | None = None, login: int | None = None,
                 password: str | None = None, server: str | None = None,
                 deviation_points: int = 20, price_retries: int = 3,
                 reconnect_attempts: int = 5, history_lookback_days: int = 7,
                 sleep: Callable[[float], None] = _time.sleep,
                 now: Callable[[], datetime] = lambda: datetime.now(UTC),
                 alert: Callable[[str], None] | None = None, allow_short: bool = False) -> None:
        self.mt5, self.magic = mt5, int(magic)
        self.allow_short = bool(allow_short)
        self.offset = timedelta(hours=server_utc_offset_hours)
        self._creds = {"path": path, "login": login, "password": password, "server": server}
        self.deviation, self.price_retries = deviation_points, price_retries
        self.reconnect_attempts, self.lookback = reconnect_attempts, timedelta(days=history_lookback_days)
        self._sleep, self._now, self._alert_cb = sleep, now, alert
        self._results: dict[str, OrderResult] = {}
        self._queue: list[Fill] = []
        self._delivered: set[int] = set()
        self._started = now()

    # ---------- plumbing ----------
    def _c(self, name: str) -> int:
        return getattr(self.mt5, name, _DEFAULTS[name])

    def _alert(self, msg: str) -> None:
        log.warning(msg)
        if self._alert_cb:
            self._alert_cb(msg)

    def connect(self) -> None:
        kw = {k: v for k, v in self._creds.items() if v not in (None, "")}
        if "login" in kw:
            kw["login"] = int(kw["login"])
        if not self.mt5.initialize(**kw):
            raise MT5Unavailable(f"initialize failed: {self.mt5.last_error()}")
        if self.mt5.account_info() is None:
            raise MT5Unavailable(f"no account logged in: {self.mt5.last_error()}")
        log.info("MT5 connected (credentials not logged)")

    def shutdown(self) -> None:
        try:
            self.mt5.shutdown()
        except Exception:  # shutting down must never raise
            pass

    def _ensure(self) -> None:
        info = self.mt5.terminal_info()
        if info is not None and getattr(info, "connected", True):
            return
        for attempt in range(1, self.reconnect_attempts + 1):
            self.shutdown()
            try:
                self.connect()
                self._alert(f"MT5 reconnected after {attempt} attempt(s)")
                return
            except MT5Unavailable as exc:
                log.warning("reconnect %d/%d failed: %s", attempt, self.reconnect_attempts, exc)
                self._sleep(min(60.0, 2.0 ** attempt))
        self._alert(f"MT5 unreachable after {self.reconnect_attempts} attempts")
        raise MT5Unavailable("terminal unreachable")

    def _to_utc(self, server_epoch: float) -> datetime:
        return datetime.fromtimestamp(server_epoch, UTC) - self.offset

    def _to_server(self, dt: datetime) -> datetime:
        # history_* functions take naive datetimes interpreted as server time
        return (dt.astimezone(UTC) + self.offset).replace(tzinfo=None)

    # ---------- account / market data ----------
    def account(self) -> AccountState:
        self._ensure()
        a = self.mt5.account_info()
        return AccountState(float(a.balance), float(a.equity),
                            a.trade_mode == self._c("ACCOUNT_TRADE_MODE_DEMO"), str(a.login))

    def is_hedging(self) -> bool:
        return self.mt5.account_info().margin_mode == self._c("ACCOUNT_MARGIN_MODE_RETAIL_HEDGING")

    def _symbol_info(self, symbol: str):
        self._ensure()
        if not self.mt5.symbol_select(symbol, True):
            raise ValueError(f"symbol {symbol} not available on this server")
        info = self.mt5.symbol_info(symbol)
        if info is None:
            raise ValueError(f"symbol {symbol}: no symbol_info")
        return info

    def symbol_spec(self, symbol: str) -> SymbolSpec:
        i = self._symbol_info(symbol)
        return SymbolSpec(symbol, float(i.trade_tick_size), float(i.trade_tick_value),
                          float(i.volume_min), float(i.volume_step), float(i.volume_max))

    def bars(self, symbol: str, timeframe_min: int, count: int) -> list[Bar]:
        if timeframe_min not in TIMEFRAMES:
            raise ValueError(f"unsupported timeframe {timeframe_min} min")
        self._symbol_info(symbol)
        rates = self.mt5.copy_rates_from_pos(symbol, getattr(self.mt5, TIMEFRAMES[timeframe_min]), 0, count)
        if rates is None:
            raise ConnectionError(f"copy_rates_from_pos({symbol}) failed: {self.mt5.last_error()}")
        return [Bar(self._to_utc(int(r["time"])), float(r["open"]), float(r["high"]),
                    float(r["low"]), float(r["close"]), float(r["tick_volume"])) for r in rates]

    def last_price(self, symbol: str) -> float:
        self._ensure()
        tick = self.mt5.symbol_info_tick(symbol)
        if tick is None:
            raise ConnectionError(f"no tick for {symbol}")
        return float(tick.bid)

    def estimate_server_offset(self, symbol: str) -> float | None:
        """Hours between server time and UTC, from the last tick (needs an active market)."""
        self._ensure()
        tick = self.mt5.symbol_info_tick(symbol)
        if tick is None or not tick.time:
            return None
        diff_h = (tick.time - self._now().timestamp()) / 3600.0
        rounded = round(diff_h * 2) / 2
        return rounded if abs(diff_h - rounded) < 0.1 else None

    # ---------- positions ----------
    def _own_positions(self, symbol: str | None = None) -> list:
        self._ensure()
        raw = self.mt5.positions_get(symbol=symbol) if symbol else self.mt5.positions_get()
        if raw is None:
            raise ConnectionError(f"positions_get failed: {self.mt5.last_error()}")
        return [p for p in raw if p.magic == self.magic]

    def positions(self) -> list[Position]:
        """One aggregated Position per symbol (hedging tickets are summed).
        A SELL ticket with our magic should never exist; it is reported with a
        negative volume so the engine's reconciliation flags it (safe mode)."""
        agg: dict[str, list] = {}
        for p in self._own_positions():
            agg.setdefault(p.symbol, []).append(p)
        out = []
        for symbol, ps in agg.items():
            sign = lambda p: 1.0 if p.type == self._c("POSITION_TYPE_BUY") else -1.0  # noqa: E731
            vol = sum(sign(p) * p.volume for p in ps)
            gross = sum(p.volume for p in ps)
            entry = sum(p.price_open * p.volume for p in ps) / gross if gross else 0.0
            sls = [p.sl for p in ps if p.sl]
            out.append(Position(symbol, round(vol, 8), entry, min(sls) if sls else None))
        return out

    # ---------- orders ----------
    def _filling(self, info) -> int:
        fm = int(getattr(info, "filling_mode", 0))
        if fm & self._c("SYMBOL_FILLING_FOK"):
            return self._c("ORDER_FILLING_FOK")
        if fm & self._c("SYMBOL_FILLING_IOC"):
            return self._c("ORDER_FILLING_IOC")
        return self._c("ORDER_FILLING_RETURN")

    def _deals(self, since: datetime | None = None) -> list:
        self._ensure()
        start = since or (self._now() - self.lookback)
        raw = self.mt5.history_deals_get(self._to_server(start), self._to_server(self._now() + timedelta(days=1)))
        return list(raw or ())

    def _fill_from_deals(self, client_id: str, deals: list, reason: str = "") -> Fill | None:
        mine = [d for d in deals if d.magic == self.magic and d.comment == comment_for(client_id)]
        if not mine:
            return None
        vol = sum(d.volume for d in mine)
        price = sum(d.price * d.volume for d in mine) / vol
        side = "buy" if mine[0].type == self._c("DEAL_TYPE_BUY") else "sell"
        cost = -sum(getattr(d, "commission", 0.0) + getattr(d, "fee", 0.0) for d in mine)
        closing = any(d.entry in (self._c("DEAL_ENTRY_OUT"), self._c("DEAL_ENTRY_OUT_BY")) for d in mine)
        pnl = (sum(d.profit + getattr(d, "swap", 0.0) for d in mine) - cost) if closing else None
        return Fill(client_id, mine[0].symbol, side, round(vol, 8), price,
                    self._to_utc(max(d.time for d in mine)), cost=cost, pnl=pnl, reason=reason)

    def find_fill(self, client_id: str) -> Fill | None:
        return self._fill_from_deals(client_id, self._deals())

    def _check_and_send(self, request: dict, symbol: str, side: str) -> tuple[bool, int, str]:
        """order_check + order_send with fresh-price retries. Raises on unknown outcome."""
        for attempt in range(self.price_retries + 1):
            tick = self.mt5.symbol_info_tick(symbol)
            if tick is None:
                raise ConnectionError(f"no tick for {symbol}")
            request["price"] = float(tick.ask if side == "buy" else tick.bid)
            check = self.mt5.order_check(request)
            if check is None:
                raise ConnectionError(f"order_check returned None: {self.mt5.last_error()}")
            if check.retcode != 0:
                return False, check.retcode, f"order_check: {getattr(check, 'comment', '')}"
            res = self.mt5.order_send(request)
            if res is None:
                raise ConnectionError(f"order_send returned None: {self.mt5.last_error()}")
            if res.retcode in OK_SEND:
                return True, res.retcode, ""
            if res.retcode in UNKNOWN_OUTCOME:
                raise TimeoutError(f"order_send {retcode_name(res.retcode)}")
            if res.retcode in RETRY_PRICE and attempt < self.price_retries:
                log.info("retry %s after %s", request.get("comment"), retcode_name(res.retcode))
                continue
            return False, res.retcode, getattr(res, "comment", "")
        return False, 0, "retries exhausted"

    def send(self, req: OrderRequest) -> OrderResult:
        if req.client_id in self._results:
            return self._results[req.client_id]
        self._ensure()
        prior = self.find_fill(req.client_id)          # sent before a restart?
        if prior is not None:
            res = OrderResult(True, req.client_id, prior, retcode="ALREADY_FILLED")
            self._results[req.client_id] = res
            return res
        res = self._execute(req)
        if res.accepted or res.retcode not in ("CONNECTION", "TIMEOUT"):
            self._results[req.client_id] = res
        if not res.accepted:
            log.warning("order %s rejected: %s %s", req.client_id, res.retcode, res.message)
        return res

    def _base_request(self, symbol: str, volume: float, side: str, comment: str, info) -> dict:
        return {
            "action": self._c("TRADE_ACTION_DEAL"), "symbol": symbol, "volume": float(volume),
            "type": self._c("ORDER_TYPE_BUY") if side == "buy" else self._c("ORDER_TYPE_SELL"),
            "deviation": self.deviation, "magic": self.magic, "comment": comment,
            "type_time": self._c("ORDER_TIME_GTC"), "type_filling": self._filling(info),
        }

    def _execute(self, req: OrderRequest) -> OrderResult:
        try:
            info = self._symbol_info(req.symbol)
        except ValueError as exc:
            return OrderResult(False, req.client_id, retcode="UNKNOWN_SYMBOL", message=str(exc))
        comment = comment_for(req.client_id)
        if self.allow_short:
            if req.reduce_only:
                close_type = "POSITION_TYPE_BUY" if req.side == "sell" else "POSITION_TYPE_SELL"
                ok, code, msg = self._close_volume(req.symbol, req.volume, comment, info, close_type)
                if code == -1:
                    return OrderResult(False, req.client_id, retcode="NO_POSITION", message=msg)
            else:
                if req.stop_loss is None:
                    return OrderResult(False, req.client_id, retcode="NO_STOP",
                                       message="entries need a server-side stop")
                if self._own_positions(req.symbol):
                    return OrderResult(False, req.client_id, retcode="ALREADY_OPEN",
                                       message="one position per symbol")
                request = self._base_request(req.symbol, req.volume, req.side, comment, info)
                request["sl"] = float(req.stop_loss)
                if req.take_profit is not None:
                    request["tp"] = float(req.take_profit)
                ok, code, msg = self._check_and_send(request, req.symbol, req.side)
        elif req.side == "buy":
            if req.reduce_only:
                return OrderResult(False, req.client_id, retcode="INVALID", message="buy cannot reduce (long only)")
            if req.stop_loss is None:
                return OrderResult(False, req.client_id, retcode="NO_STOP",
                                   message="entries need a server-side stop")
            request = self._base_request(req.symbol, req.volume, "buy", comment, info)
            request["sl"] = float(req.stop_loss)
            if req.take_profit is not None:
                request["tp"] = float(req.take_profit)
            ok, code, msg = self._check_and_send(request, req.symbol, "buy")
        else:
            ok, code, msg = self._close_volume(req.symbol, req.volume, comment, info)
            if code == -1:
                return OrderResult(False, req.client_id, retcode="NO_POSITION", message=msg)
        if not ok:
            return OrderResult(False, req.client_id, retcode=retcode_name(code), message=msg)
        fill = self.find_fill(req.client_id)
        for _ in range(3):  # the deal can take a moment to reach the history
            if fill is not None:
                break
            self._sleep(0.5)
            fill = self.find_fill(req.client_id)
        if fill is None:  # accepted but the deal is not in history yet: let the engine recover
            raise TimeoutError(f"{req.client_id}: accepted, deal not visible yet")
        return OrderResult(True, req.client_id, replace(fill, reason=req.reason),
                           retcode=retcode_name(code))

    def _close_volume(self, symbol: str, volume: float, comment: str, info,
                      close_type: str = "POSITION_TYPE_BUY") -> tuple[bool, int, str]:
        """Close `volume` of our tickets of `close_type` one by one, BY TICKET (never opens a new position).
        BUY tickets are closed with a sell, SELL tickets (allow_short) with a buy."""
        tickets = [p for p in self._own_positions(symbol) if p.type == self._c(close_type)]
        side = "sell" if close_type == "POSITION_TYPE_BUY" else "buy"
        have = sum(p.volume for p in tickets)
        if not tickets or volume > have + 1e-9:
            return False, -1, f"close {volume} but open {have}"
        left, last = volume, (True, 10009, "")
        for p in sorted(tickets, key=lambda p: p.ticket):
            if left <= 1e-9:
                break
            part = min(left, p.volume)
            request = self._base_request(symbol, part, side, comment, info)
            request["position"] = p.ticket
            last = self._check_and_send(request, symbol, side)
            if not last[0]:
                return last
            left = round(left - part, 8)
        return last

    def modify_stop(self, symbol: str, stop: float) -> tuple[bool, str]:
        """Move the server stop of our tickets on `symbol` to `stop` (TRADE_ACTION_SLTP; the take-profit is kept).
        Only TIGHTENS: a ticket whose stop already sits at or past `stop` in its favour is left alone.
        Returns (all accepted, message). Sends no deal: the position's volume is never changed here."""
        self._ensure()
        msgs, ok = [], True
        for p in self._own_positions(symbol):
            is_buy = p.type == self._c("POSITION_TYPE_BUY")
            cur = float(p.sl or 0.0)
            if cur and ((is_buy and stop <= cur + 1e-9) or (not is_buy and stop >= cur - 1e-9)):
                continue
            r = self.mt5.order_send({"action": self._c("TRADE_ACTION_SLTP"), "symbol": symbol, "position": p.ticket,
                                     "sl": float(stop), "tp": float(getattr(p, "tp", 0.0) or 0.0), "magic": self.magic})
            if r is None or r.retcode not in OK_SEND:
                ok = False
                msgs.append(f"ticket {p.ticket}: {retcode_name(r.retcode) if r is not None else self.mt5.last_error()}"
                            f" {getattr(r, 'comment', '')}")
        return ok, "; ".join(msgs)

    def cancel_all(self) -> None:
        self._ensure()
        for o in self.mt5.orders_get() or ():
            if o.magic == self.magic:
                r = self.mt5.order_send({"action": self._c("TRADE_ACTION_REMOVE"), "order": o.ticket})
                if r is None or r.retcode not in OK_SEND:
                    self._alert(f"cancel of order {o.ticket} failed: {getattr(r, 'retcode', None)}")

    def close_all(self, reason: str = "") -> None:
        stamp = int(self._now().timestamp())
        for p in self._own_positions():
            is_buy = p.type == self._c("POSITION_TYPE_BUY")
            if not is_buy and not self.allow_short:
                self._alert(f"unexpected SELL ticket {p.ticket} {p.symbol}; not touched")
                continue
            side = "sell" if is_buy else "buy"
            cid = f"ca-{p.ticket}-{stamp}"
            info = self._symbol_info(p.symbol)
            request = self._base_request(p.symbol, p.volume, side, comment_for(cid), info)
            request["position"] = p.ticket
            try:
                ok, code, msg = self._check_and_send(request, p.symbol, side)
            except (ConnectionError, TimeoutError) as exc:
                self._alert(f"close_all {p.symbol} ticket {p.ticket}: outcome unknown ({exc})")
                continue
            if not ok:
                self._alert(f"close_all {p.symbol} ticket {p.ticket} failed: {retcode_name(code)} {msg}")
                continue
            fill = self.find_fill(cid)
            if fill is not None:
                self._queue.append(replace(fill, reason=reason or "close_all"))

    def drain_fills(self) -> list[Fill]:
        """Close-all fills plus exits the SERVER made (stop-loss, stop-out, manual),
        each once. Our own `send` deals carry reason EXPERT and are skipped."""
        out, self._queue = self._queue, []
        deals = self._deals()
        our_positions = {d.position_id for d in deals
                         if d.magic == self.magic and d.entry == self._c("DEAL_ENTRY_IN")}
        for d in sorted(deals, key=lambda d: d.ticket):
            if d.ticket in self._delivered or d.position_id not in our_positions:
                continue
            if d.entry not in (self._c("DEAL_ENTRY_OUT"), self._c("DEAL_ENTRY_OUT_BY")):
                continue
            if d.reason == self._c("DEAL_REASON_EXPERT"):
                continue
            self._delivered.add(d.ticket)
            cost = -(getattr(d, "commission", 0.0) + getattr(d, "fee", 0.0))
            side = "buy" if d.type == self._c("DEAL_TYPE_BUY") else "sell"    # a short's stop is a buy
            out.append(Fill(f"deal-{d.ticket}", d.symbol, side, float(d.volume), float(d.price),
                            self._to_utc(d.time), cost=cost,
                            pnl=d.profit + getattr(d, "swap", 0.0) - cost, reason=f"server:{d.reason}"))
        return out
