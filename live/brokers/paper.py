"""Deterministic paper broker for tests, replays and the demo dry-run.

Fill model (the same one the B3 backtester must use, see Etapa 3):
- an order sent at time t (the close of bar k) fills at the OPEN of the bar
  that starts at t, if the history already holds it (replay); otherwise at
  the last closed price (live paper);
- adverse slippage of `slippage_ticks` ticks, plus a cost per contract and
  per side;
- the stop is checked on every newly closed bar: it fills at the stop, or at
  the open if the bar gapped through it.
`bars()` deliberately returns the bar that starts at `now` (it holds the
future in a replay), so the engine's closed-candle filter is exercised.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from live.core.clock import Clock
from live.core.models import (
    AccountState, Bar, Fill, OrderRequest, OrderResult, Position, SymbolSpec,
)


@dataclass(frozen=True)
class PaperConfig:
    cost_per_contract_per_side: float = 0.0
    slippage_ticks: float = 1.0
    balance: float = 10_000.0
    stop_slippage_frac: float = 0.0   # extra adverse share of the price on stop fills (b3.costs.B3Cost)
    stop_extra_ticks: float = 0.0     # extra ticks on stop fills, on top of slippage_ticks (b3.costs.B3Cost)


@dataclass
class _Pos:
    volume: float
    entry_price: float
    entry_cost: float
    stop: float | None
    entered_at: datetime
    tp: float | None = None


class PaperBroker:
    def __init__(self, clock: Clock, specs: dict[str, SymbolSpec],
                 cfg: PaperConfig | None = None, allow_short: bool = False) -> None:
        self.clock, self.specs, self.cfg = clock, specs, cfg or PaperConfig()
        self.allow_short = allow_short     # a non-reduce "sell" opens a short; a reduce "buy" covers it
        self._bars: dict[str, list[Bar]] = {}
        self._tf: dict[str, int] = {}
        self._pos: dict[str, _Pos] = {}
        self._results: dict[str, OrderResult] = {}
        self._queue: list[Fill] = []
        self._scanned: dict[str, datetime] = {}
        self._realized = 0.0
        self.fail_next_send_after_fill = False  # test hook: simulate a timeout

    # ---- data ----
    def load_bars(self, symbol: str, bars: list[Bar], timeframe_min: int) -> None:
        self._bars[symbol], self._tf[symbol] = list(bars), timeframe_min

    def _visible(self, symbol: str) -> list[Bar]:
        now = self.clock.now()
        return [b for b in self._bars.get(symbol, []) if b.time <= now]

    def _closed(self, symbol: str) -> list[Bar]:
        tf, now = timedelta(minutes=self._tf[symbol]), self.clock.now()
        return [b for b in self._bars.get(symbol, []) if b.time + tf <= now]

    def bars(self, symbol: str, timeframe_min: int, count: int) -> list[Bar]:
        assert timeframe_min == self._tf[symbol], "paper broker holds one timeframe"
        return self._visible(symbol)[-count:]

    def symbol_spec(self, symbol: str) -> SymbolSpec:
        return self.specs[symbol]

    def last_price(self, symbol: str) -> float:
        return self._closed(symbol)[-1].close

    # ---- fills ----
    def _exec_price(self, symbol: str, side: str) -> float:
        now, spec = self.clock.now(), self.specs[symbol]
        opening = next((b for b in self._bars[symbol] if b.time == now), None)
        base = opening.open if opening else self.last_price(symbol)
        slip = self.cfg.slippage_ticks * spec.tick_size
        return base + slip if side == "buy" else base - slip

    def _gross(self, symbol: str, entry: float, exit_: float, volume: float) -> float:
        s = self.specs[symbol]
        return (exit_ - entry) / s.tick_size * s.tick_value * volume     # volume < 0 for a short

    def _close_part(self, symbol: str, volume: float, price: float, client_id: str,
                    reason: str) -> Fill:
        p = self._pos[symbol]
        sign = 1.0 if p.volume > 0 else -1.0
        frac = volume / abs(p.volume)
        entry_cost = p.entry_cost * frac
        exit_cost = self.cfg.cost_per_contract_per_side * volume
        pnl = self._gross(symbol, p.entry_price, price, sign * volume) - entry_cost - exit_cost
        self._realized += pnl
        p.entry_cost -= entry_cost
        p.volume = round(p.volume - sign * volume, 8)
        if abs(p.volume) <= 1e-9:
            del self._pos[symbol]
        return Fill(client_id, symbol, "sell" if sign > 0 else "buy", volume, price, self.clock.now(),
                    cost=exit_cost, pnl=pnl, reason=reason)

    def send(self, req: OrderRequest) -> OrderResult:
        if req.client_id in self._results:
            return self._results[req.client_id]
        res = self._execute(req)
        self._results[req.client_id] = res
        if self.fail_next_send_after_fill and res.accepted:
            self.fail_next_send_after_fill = False
            raise TimeoutError("simulated timeout after execution")
        return res

    def _execute(self, req: OrderRequest) -> OrderResult:
        spec = self.specs.get(req.symbol)
        if spec is None:
            return OrderResult(False, req.client_id, retcode="UNKNOWN_SYMBOL")
        if req.volume < spec.volume_min or req.volume > spec.volume_max:
            return OrderResult(False, req.client_id, retcode="INVALID_VOLUME")
        pos = self._pos.get(req.symbol)
        price = self._exec_price(req.symbol, req.side)
        if self.allow_short:
            if req.reduce_only:
                want = "sell" if pos is not None and pos.volume > 0 else "buy"
                if pos is None or req.side != want or req.volume > abs(pos.volume) + 1e-9:
                    return OrderResult(False, req.client_id, retcode="NO_POSITION")
                return OrderResult(True, req.client_id,
                                   self._close_part(req.symbol, req.volume, price, req.client_id, req.reason))
            if pos is not None:
                return OrderResult(False, req.client_id, retcode="ALREADY_OPEN")
            cost = self.cfg.cost_per_contract_per_side * req.volume
            sign = 1.0 if req.side == "buy" else -1.0
            self._pos[req.symbol] = _Pos(sign * req.volume, price, cost, req.stop_loss, self.clock.now(), req.take_profit)
            self._scanned.pop(req.symbol, None)
            return OrderResult(True, req.client_id, Fill(
                req.client_id, req.symbol, req.side, req.volume, price, self.clock.now(),
                cost=cost, reason=req.reason))
        if req.side == "buy":
            if pos is not None:
                return OrderResult(False, req.client_id, retcode="ALREADY_OPEN")
            cost = self.cfg.cost_per_contract_per_side * req.volume
            self._pos[req.symbol] = _Pos(req.volume, price, cost, req.stop_loss,
                                         self.clock.now(), req.take_profit)
            self._scanned.pop(req.symbol, None)
            return OrderResult(True, req.client_id, Fill(
                req.client_id, req.symbol, "buy", req.volume, price, self.clock.now(),
                cost=cost, reason=req.reason))
        if pos is None or req.volume > pos.volume + 1e-9:
            return OrderResult(False, req.client_id, retcode="NO_POSITION")
        fill = self._close_part(req.symbol, req.volume, price, req.client_id, req.reason)
        return OrderResult(True, req.client_id, fill)

    def find_fill(self, client_id: str) -> Fill | None:
        r = self._results.get(client_id)
        return r.fill if r and r.accepted else None

    # ---- server-side events ----
    def sync(self) -> None:
        """Check stops on bars that closed since the last call. Call it before
        each engine step (the live adapter gets this for free from the server)."""
        for symbol, p in list(self._pos.items()):
            if p.stop is None:
                continue
            tf = timedelta(minutes=self._tf[symbol])
            last = self._scanned.get(symbol, p.entered_at - tf)
            for b in self._closed(symbol):
                if b.time <= last or b.time < p.entered_at:
                    continue
                self._scanned[symbol] = b.time
                long = p.volume > 0
                if (long and b.low <= p.stop) or (not long and b.high >= p.stop):
                    price = min(b.open, p.stop) if long else max(b.open, p.stop)
                    slip = ((self.cfg.slippage_ticks + self.cfg.stop_extra_ticks) * self.specs[symbol].tick_size
                            + self.cfg.stop_slippage_frac * price)
                    fill = self._close_part(
                        symbol, abs(p.volume), price - slip if long else price + slip,
                        f"stop-{symbol}-{int(b.time.timestamp())}", "stop_loss")
                    self._queue.append(replace(fill, time=b.time + tf))
                    break
                if p.tp is not None and ((long and b.high >= p.tp) or (not long and b.low <= p.tp)):
                    price = max(b.open, p.tp) if long else min(b.open, p.tp)       # a limit: at the target or better
                    fill = self._close_part(symbol, abs(p.volume), price, f"tp-{symbol}-{int(b.time.timestamp())}",
                                            "take_profit")
                    self._queue.append(replace(fill, time=b.time + tf))
                    break

    def drain_fills(self) -> list[Fill]:
        out, self._queue = self._queue, []
        return out

    def modify_stop(self, symbol: str, stop: float) -> tuple[bool, str]:
        """Tighten the stop of the open position (never loosens). Mirrors MT5Broker.modify_stop."""
        p = self._pos.get(symbol)
        if p is None:
            return False, "no position"
        if p.stop is not None and ((p.volume > 0 and stop <= p.stop) or (p.volume < 0 and stop >= p.stop)):
            return True, "not tighter"
        last = self.last_price(symbol)
        if (p.volume > 0 and stop >= last) or (p.volume < 0 and stop <= last):
            return False, "INVALID_STOPS: stop beyond the current price"
        p.stop = float(stop)
        return True, ""

    def cancel_all(self) -> None:  # market-only broker: nothing is ever pending
        return None

    def close_all(self, reason: str = "") -> None:
        for symbol, p in list(self._pos.items()):
            price = self._exec_price(symbol, "sell" if p.volume > 0 else "buy")
            cid = f"closeall-{symbol}-{int(self.clock.now().timestamp())}"
            self._queue.append(self._close_part(symbol, abs(p.volume), price, cid,
                                                reason or "close_all"))

    # ---- account ----
    def positions(self) -> list[Position]:
        return [Position(s, p.volume, p.entry_price, p.stop) for s, p in self._pos.items()]

    def account(self) -> AccountState:
        unreal = sum(self._gross(s, p.entry_price, self.last_price(s), p.volume)
                     for s, p in self._pos.items())
        bal = self.cfg.balance + self._realized
        return AccountState(bal, bal + unreal, True, "paper")
