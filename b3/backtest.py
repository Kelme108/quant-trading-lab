"""Bar backtester for B3 futures with the SAME fill rules as live/brokers/paper.py + live/core/engine.py.

Replay model (one step at the close of every bar k, time `now = open_k + timeframe`):
1. server-side stop (PaperBroker.sync): if a position is open and bar k started at or after the
   entry, a long is stopped when low_k <= stop and fills at min(open_k, stop) minus slippage; a
   short when high_k >= stop, at max(open_k, stop) plus slippage. The fill is stamped `now`.
2. engine step at `now`, by session phase (B3SessionCalendar):
   closed  -> nothing;
   flatten -> close any position at the execution price (below), reason end_of_day_flatten;
   otherwise -> optional account loss limits (day / week, realised + unrealised at the last close,
   as in Engine._check_lockouts), then the strategy's decision on bar k:
     exit with a position -> close at the execution price;
     enter / enter_short while flat -> risk checks as live/core/risk.py, then open.
   Execution price = open of the bar that starts exactly at `now` (or the last close if none does),
   moved against the order by `slippage_ticks_per_side` ticks.
Costs: cash cost per contract per side (fees + brokerage, plus `notional_frac_per_side` of the fill's
notional for the proxy markets) on entry and on exit; slippage is in the price. PnL = points x point
value x contracts - costs (BRL for WIN/WDO, the quote currency for a proxy market).

The parity test (tests/b3/test_parity.py) replays the same bars through the real Engine with a
PaperBroker and requires identical fills, so this file cannot drift from the live path unnoticed.
Shorts are backtester-only until the live engine supports them (plan F3); the parity test covers
longs.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import timedelta

import pandas as pd

from b3.costs import B3Cost
from b3.instruments import Instrument
from b3.strategy import ENTER_LONG, ENTER_SHORT, EXIT, B3Strategy
from live.core.models import Position


@dataclass(frozen=True)
class BacktestConfig:
    contracts: float = 1.0
    allow_short: bool = True
    require_stop: bool = True
    max_contracts: float | None = None
    max_entries_per_day: int | None = None
    max_daily_loss_brl: float | None = None
    max_weekly_loss_brl: float | None = None


@dataclass(frozen=True)
class Trade:
    symbol: str
    side: str                  # long | short
    contracts: float
    entry_time: pd.Timestamp   # fill time (UTC)
    entry_price: float
    stop_price: float | None
    exit_time: pd.Timestamp
    exit_price: float
    points: float              # signed in the trade's favour
    gross_brl: float
    cost_brl: float
    net_brl: float
    entry_reason: str
    exit_reason: str


@dataclass
class BacktestResult:
    strategy_name: str
    strategy_hash: str
    cost: B3Cost
    config: BacktestConfig
    trades: list[Trade] = field(default_factory=list)
    fills: list[dict] = field(default_factory=list)      # journal-like, for the parity test
    vetoes: Counter = field(default_factory=Counter)
    positions_held_overnight: int = 0

    def trades_frame(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(t) for t in self.trades])


@dataclass
class _Open:
    symbol: str
    side: str
    volume: float
    entry_price: float
    entry_cost: float
    stop: float | None
    entered_at: pd.Timestamp
    entry_reason: str
    entry_day: str


def _on_grid(value: float, step: float) -> bool:
    n = round(value / step)
    return abs(n * step - value) <= step * 1e-6


def run(frame: pd.DataFrame, strategy: B3Strategy, cost: B3Cost,
        config: BacktestConfig | None = None, instrument: Instrument | None = None) -> BacktestResult:
    cfg = config or BacktestConfig()
    inst = instrument or strategy.instrument()
    cal = strategy.calendar
    tf = timedelta(minutes=strategy.timeframe_min)
    tick, tick_value = inst.tick_size, inst.tick_value_brl
    slip = cost.slippage_ticks_per_side * tick

    data = frame.reset_index(drop=True)
    if not data["time"].is_monotonic_increasing or data["time"].duplicated().any():
        raise ValueError("bars must be sorted by time with no duplicates")
    prepared = strategy.prepare(data)
    rows = list(prepared.itertuples(index=False, name="Row"))
    times = list(data["time"])
    opens = data["open"].to_numpy()
    starts_at = {t: i for i, t in enumerate(times)}
    symbols = list(data["contract"]) if "contract" in data.columns else [strategy.root] * len(data)

    res = BacktestResult(strategy.name, strategy.hash, cost, cfg)
    pos: _Open | None = None
    realized_day: Counter = Counter()
    realized_week: Counter = Counter()
    entries_day: Counter = Counter()
    locked_days: set[str] = set()
    locked_weeks: set[str] = set()

    def sign(side: str) -> int:
        return 1 if side == "long" else -1

    def exec_price(now, k: int, order_side: str) -> float:
        j = starts_at.get(now)
        base = opens[j] if j is not None else rows[k].close
        return base + slip if order_side == "buy" else base - slip

    def close(now, price: float, reason: str) -> None:
        nonlocal pos
        p = pos
        pts = (price - p.entry_price) * sign(p.side)
        gross = pts / tick * tick_value * p.volume
        exit_cost = cost.cash_cost(inst, price, p.volume)
        pnl = gross - p.entry_cost - exit_cost
        res.fills.append({"time": now, "side": "sell" if p.side == "long" else "buy", "volume": p.volume,
                          "price": price, "pnl": pnl, "reason": reason, "symbol": p.symbol})
        res.trades.append(Trade(p.symbol, p.side, p.volume, p.entered_at, p.entry_price, p.stop, now, price,
                                pts, gross, p.entry_cost + exit_cost, pnl, p.entry_reason, reason))
        realized_day[cal.day_key(now)] += pnl
        realized_week[cal.week_key(now)] += pnl
        if cal.day_key(now) != p.entry_day:
            res.positions_held_overnight += 1
        pos = None

    for k, row in enumerate(rows):
        bar_time = times[k]
        now = bar_time + tf

        # 1. server-side stop on the bar that just closed
        if pos is not None and pos.stop is not None and bar_time >= pos.entered_at:
            if pos.side == "long" and row.low <= pos.stop:
                close(now, min(row.open, pos.stop) - slip, "stop_loss")
            elif pos.side == "short" and row.high >= pos.stop:
                close(now, max(row.open, pos.stop) + slip, "stop_loss")

        # 2. engine step
        phase = cal.phase(now.to_pydatetime())
        if phase == "closed":
            continue
        if phase == "flatten":
            if pos is not None:
                close(now, exec_price(now, k, "sell" if pos.side == "long" else "buy"), "end_of_day_flatten")
            continue

        day_key, week_key = cal.day_key(now), cal.week_key(now)
        if cfg.max_daily_loss_brl is not None or cfg.max_weekly_loss_brl is not None:
            unreal = 0.0
            if pos is not None:
                unreal = (row.close - pos.entry_price) * sign(pos.side) / tick * tick_value * pos.volume
            hit = False
            if (cfg.max_daily_loss_brl is not None and day_key not in locked_days
                    and realized_day[day_key] + unreal <= -cfg.max_daily_loss_brl):
                locked_days.add(day_key)
                hit = True
            if (cfg.max_weekly_loss_brl is not None and week_key not in locked_weeks
                    and realized_week[week_key] + unreal <= -cfg.max_weekly_loss_brl):
                locked_weeks.add(week_key)
                hit = True
            if hit and pos is not None:
                close(now, exec_price(now, k, "sell" if pos.side == "long" else "buy"), "loss_limit")

        if k + 1 < strategy.warmup:
            continue
        position = None
        if pos is not None:
            position = Position(pos.symbol, pos.volume * sign(pos.side), pos.entry_price, pos.stop)
        sig = strategy.decide(row, position)

        if sig.action == EXIT and pos is not None:
            close(now, exec_price(now, k, "sell" if pos.side == "long" else "buy"), sig.reason)
        elif sig.action in (ENTER_LONG, ENTER_SHORT) and pos is None:
            side = "long" if sig.action == ENTER_LONG else "short"
            why = []
            if side == "short" and not cfg.allow_short:
                why.append("long_only")
            if phase != "entry":
                why.append(f"outside_entry_window:{phase}")
            if day_key in locked_days:
                why.append("daily_loss_limit")
            if week_key in locked_weeks:
                why.append("weekly_loss_limit")
            if cfg.max_contracts is not None and cfg.contracts > cfg.max_contracts + 1e-9:
                why.append("max_contracts")
            if cfg.max_entries_per_day is not None and entries_day[day_key] >= cfg.max_entries_per_day:
                why.append("max_entries_per_day")
            if cfg.require_stop and sig.stop_price is None:
                why.append("no_stop")
            if sig.stop_price is not None:
                if not _on_grid(sig.stop_price, tick):
                    why.append("stop_not_on_tick")
                if (side == "long" and sig.stop_price >= row.close) or (side == "short" and sig.stop_price <= row.close):
                    why.append("stop_wrong_side")
            if why:
                for w in why:
                    res.vetoes[w] += 1
                continue
            entries_day[day_key] += 1
            price = exec_price(now, k, "buy" if side == "long" else "sell")
            entry_cost = cost.cash_cost(inst, price, cfg.contracts)
            pos = _Open(symbols[k], side, cfg.contracts, price, entry_cost, sig.stop_price, now,
                        sig.reason, day_key)
            res.fills.append({"time": now, "side": "buy" if side == "long" else "sell", "volume": cfg.contracts,
                              "price": price, "pnl": None, "reason": sig.reason, "symbol": symbols[k]})

    if pos is not None:   # data ended with an open position: close at the last close, flagged
        k = len(rows) - 1
        close(times[k] + tf, rows[k].close, "end_of_data")
    return res
