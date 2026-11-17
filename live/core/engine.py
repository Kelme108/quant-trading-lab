"""Engine: closed candle -> signal -> risk -> order -> journal.

Safety properties (each one has a test):
- decisions use CLOSED candles only (the forming candle is dropped here, not
  trusted to the broker);
- a bar is processed once (journal key), orders are write-ahead logged and
  carry a deterministic client id, so a restart or a resend never duplicates;
- journal position vs broker position are reconciled every step; a mismatch
  or an order of unknown outcome puts the engine in safe mode (no entries);
- limit breaches lock entries for the rest of the day/week (persisted in the
  journal, so a restart does not unlock) and flatten;
- the kill switch and the end-of-day flatten always win.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Callable, Protocol

from live.core.broker import Broker
from live.core.clock import B3Calendar, Clock
from live.core.journal import Journal
from live.core.killswitch import KillSwitch
from live.core.models import Bar, Fill, OrderRequest, Position, Signal
from live.core.risk import RiskContext, RiskManager

log = logging.getLogger("live.engine")


class Strategy(Protocol):
    name: str
    hash: str            # frozen identity of the code+params (recorded in the registry)
    timeframe_min: int
    warmup: int          # closed bars needed before the first signal

    def signal(self, bars: list[Bar], position: Position | None) -> Signal: ...


class Engine:
    def __init__(self, broker: Broker, strategy: Strategy, clock: Clock,
                 calendar: B3Calendar, journal: Journal, risk: RiskManager,
                 killswitch: KillSwitch, symbols: list[str], volume: float = 1.0,
                 alert: Callable[[str], None] | None = None) -> None:
        self.broker, self.strategy, self.clock, self.cal = broker, strategy, clock, calendar
        self.journal, self.risk, self.ks = journal, risk, killswitch
        self.symbols, self.volume = list(symbols), volume
        self._alert_cb = alert
        self._sticky_safe = False
        self._mismatch_seen: set[str] = set()
        self.safe_reason = ""

    # ---------- helpers ----------
    def _alert(self, msg: str) -> None:
        log.warning(msg)
        self.journal.log("alert", message=msg)
        if self._alert_cb:
            self._alert_cb(msg)

    def _mismatches(self) -> dict[str, tuple[float, float]]:
        broker = {p.symbol: p.volume for p in self.broker.positions()}
        out = {}
        for s in set(self.symbols) | set(broker):
            j, b = self.journal.net_volume(s), broker.get(s, 0.0)
            if abs(j - b) > 1e-9:
                out[s] = (j, b)
        return out

    @property
    def safe_mode(self) -> bool:
        return self._sticky_safe or bool(self._mismatches())

    def _record_fill(self, f: Fill) -> None:
        self.journal.log("fill", f.symbol, key=f.client_id, side=f.side, volume=f.volume,
                         price=f.price, cost=f.cost, pnl=f.pnl, reason=f.reason,
                         fill_time=f.time.isoformat())

    def _drain(self) -> None:
        for f in self.broker.drain_fills():
            self._record_fill(f)

    def _unrealized(self) -> float:
        total = 0.0
        for p in self.broker.positions():
            s = self.broker.symbol_spec(p.symbol)
            total += ((self.broker.last_price(p.symbol) - p.entry_price)
                      / s.tick_size * s.tick_value * p.volume)
        return total

    def start(self) -> None:
        """Call once at startup: reconcile with the broker before trading."""
        self.journal.log("start", strategy_hash=self.strategy.hash,
                         symbols=self.symbols, volume=self.volume)
        mm = self._mismatches()
        if mm:
            self._alert(f"reconciliation mismatch at start (journal, broker): {mm}")

    # ---------- main step ----------
    def step(self) -> list[str]:
        """One pass. Returns short action tags (for tests and the console)."""
        now, acts = self.clock.now(), []
        self._drain()

        if self.ks.active():
            if self.journal.log("killswitch", key=self.ks.token(), reason=self.ks.reason()):
                self._alert(f"KILL SWITCH: {self.ks.reason()}")
            self.broker.cancel_all()
            self.broker.close_all("killswitch")
            self._drain()
            return ["killswitch"]

        phase = self.cal.phase(now)
        if phase == "closed":
            return acts
        if phase == "flatten":
            if self.broker.positions():
                self.broker.close_all("end_of_day_flatten")
                self._drain()
                self.journal.log("flatten", key=self.cal.day_key(now) + ":eod")
                acts.append("flatten")
            return acts

        mm = self._mismatches()
        sig = repr(sorted(mm.items()))
        if mm and sig not in self._mismatch_seen:
            self._mismatch_seen.add(sig)
            self._alert(f"reconciliation mismatch (journal, broker): {mm}")
        if self.safe_mode:
            return ["safe_mode"]

        self._check_lockouts(now, acts)
        self._take_profit(acts)
        for symbol in self.symbols:
            self._process_symbol(symbol, now, phase, acts)
        return acts

    def _take_profit(self, acts: list[str]) -> None:
        """DEMO overlay (strategy.take_profit = {"brl": N}): close the robot's position at once when its unrealized
        profit reaches N BRL, checked on every pass (not only on bar closes). Owner 2026-11-17."""
        tp = getattr(self.strategy, "take_profit", None)
        if not tp or not self.broker.positions():
            return
        if self._unrealized() >= float(tp["brl"]):
            self.broker.close_all("demo_take_profit")
            self._drain()
            acts.append("take_profit")

    def _check_lockouts(self, now, acts: list[str]) -> None:
        cfg = self.risk.cfg
        un = self._unrealized()
        day = self.journal.realized_pnl(self.cal.day_start_utc(now)) + un
        week = self.journal.realized_pnl(self.cal.week_start_utc(now)) + un
        hit = False
        if day <= -cfg.max_daily_loss and self.journal.log(
                "lockout", key="day:" + self.cal.day_key(now), pnl=day):
            self._alert(f"daily loss limit hit ({day:.2f}); entries locked for the day")
            hit = True
        if week <= -cfg.max_weekly_loss and self.journal.log(
                "lockout", key="week:" + self.cal.week_key(now), pnl=week):
            self._alert(f"weekly loss limit hit ({week:.2f}); entries locked for the week")
            hit = True
        if hit and self.broker.positions():
            self.broker.close_all("loss_limit")
            self._drain()
            acts.append("loss_limit_flatten")

    def _process_symbol(self, symbol: str, now, phase: str, acts: list[str]) -> None:
        st = self.strategy
        tf = timedelta(minutes=st.timeframe_min)
        raw = self.broker.bars(symbol, st.timeframe_min, getattr(st, "fetch_bars", st.warmup + 5))
        closed = [b for b in raw if b.time + tf <= now]      # drop the forming candle
        if len(closed) < st.warmup:
            return
        last = closed[-1]
        bar_key = f"{symbol}:{int(last.time.timestamp())}"
        if self.journal.has("bar", bar_key):
            return
        age = (now - (last.time + tf)) / tf
        pos = next((p for p in self.broker.positions() if p.symbol == symbol), None)

        try:
            sig = st.signal(closed, pos)
        except Exception as exc:  # a broken strategy must not trade
            self._alert(f"strategy error on {symbol}: {exc!r}")
            self.journal.log("bar", symbol, key=bar_key, error=repr(exc))
            return
        self.journal.log("signal", symbol, key=bar_key, action=sig.action,
                         stop=sig.stop_price, reason=sig.reason, close=last.close,
                         strategy_hash=st.hash)

        if sig.action == "exit" and pos:
            side = "sell" if pos.volume > 0 else "buy"          # a short (demo only) is bought back
            self._send(OrderRequest(self._cid(symbol, last, "X"), symbol, side,
                                    abs(pos.volume), reduce_only=True, reason=sig.reason),
                       self._ctx(symbol, now, phase, last, age, pos))
            acts.append("exit")
        elif sig.action in ("enter", "enter_short") and not pos:
            # "enter_short" opens a short; RiskConfig.long_only (the default) vetoes it
            side = "buy" if sig.action == "enter" else "sell"
            res = self._send(OrderRequest(self._cid(symbol, last, "E"), symbol, side,
                                          self.volume, stop_loss=sig.stop_price,
                                          reason=sig.reason),
                             self._ctx(symbol, now, phase, last, age, pos))
            acts.append("enter" if res else "veto")
        self.journal.log("bar", symbol, key=bar_key)

    def _cid(self, symbol: str, last: Bar, tag: str) -> str:
        return f"{self.strategy.hash[:6]}-{symbol}-{int(last.time.timestamp())}-{tag}"

    def _ctx(self, symbol, now, phase, last, age, pos) -> RiskContext:
        return RiskContext(
            now=now, phase=phase, spec=self.broker.symbol_spec(symbol),
            ref_price=last.close, position_volume=pos.volume if pos else 0.0,
            entries_today=self.journal.entries_sent(self.cal.day_start_utc(now)),
            lockout_day=self.journal.has("lockout", "day:" + self.cal.day_key(now)),
            lockout_week=self.journal.has("lockout", "week:" + self.cal.week_key(now)),
            killswitch_active=self.ks.active(), safe_mode=self.safe_mode, data_age_bars=age)

    def _send(self, req: OrderRequest, ctx: RiskContext) -> bool:
        """Risk check, write-ahead log, send, record. True if a fill was recorded."""
        if self.journal.has("order_sent", req.client_id):
            return False                                      # already handled (restart)
        dec = self.risk.check(req, ctx)
        if not dec.approved:
            self.journal.log("veto", req.symbol, key=req.client_id,
                             reasons=list(dec.reasons), side=req.side)
            return False
        self.journal.log("order_sent", req.symbol, key=req.client_id, side=req.side,
                         volume=req.volume, stop=req.stop_loss,
                         reduce_only=req.reduce_only, reason=req.reason)
        try:
            res = self.broker.send(req)
        except Exception as exc:                              # timeout / disconnect
            fill = self.broker.find_fill(req.client_id)
            if fill is not None:
                self.journal.log("order_recovered", req.symbol, key=req.client_id)
                self._record_fill(fill)
                return True
            self._sticky_safe = True
            self.safe_reason = f"order {req.client_id} outcome unknown: {exc!r}"
            self.journal.log("order_unknown", req.symbol, key=req.client_id, error=repr(exc))
            self._alert(self.safe_reason)
            return False
        if not res.accepted:
            self.journal.log("order_rejected", req.symbol, key=req.client_id,
                             retcode=res.retcode, message=res.message)
            self._alert(f"order rejected {req.client_id}: {res.retcode} {res.message}")
            return False
        self._record_fill(res.fill)
        return True
