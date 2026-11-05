"""RiskManager: vetoes or approves each OrderRequest and says why.

Exits (reduce_only) are never blocked by limits, lockouts, the calendar or
the kill switch: getting out must always be possible. Only malformed exits
(more than the open volume, wrong volume step) are rejected.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from live.core.models import OrderRequest, SymbolSpec


@dataclass(frozen=True)
class RiskConfig:
    max_contracts_per_symbol: float = 2
    max_entries_per_day: int = 10
    max_daily_loss: float = 300.0
    max_weekly_loss: float = 900.0
    require_stop: bool = True
    long_only: bool = True
    max_data_age_bars: float = 2.0  # last closed bar older than N x timeframe


@dataclass(frozen=True)
class RiskContext:
    now: datetime
    phase: str                 # closed | no_entry | entry | flatten
    spec: SymbolSpec
    ref_price: float           # last closed price, used to check the stop side
    position_volume: float
    entries_today: int
    lockout_day: bool
    lockout_week: bool
    killswitch_active: bool
    safe_mode: bool
    data_age_bars: float       # (now - end of last closed bar) / timeframe


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reasons: tuple[str, ...] = ()


def _on_grid(value: float, origin: float, step: float) -> bool:
    n = round((value - origin) / step)
    return abs(origin + n * step - value) <= step * 1e-6


class RiskManager:
    def __init__(self, cfg: RiskConfig | None = None) -> None:
        self.cfg = cfg or RiskConfig()

    def check(self, req: OrderRequest, ctx: RiskContext) -> RiskDecision:
        c, s = self.cfg, ctx.spec
        why: list[str] = []

        # Volume validity applies to every order.
        if req.volume < s.volume_min or req.volume > s.volume_max:
            why.append("volume_out_of_range")
        elif not _on_grid(req.volume, s.volume_min, s.volume_step):
            why.append("volume_step")

        if req.reduce_only:
            if req.volume > ctx.position_volume + 1e-9:
                why.append("exit_larger_than_position")
            return RiskDecision(not why, tuple(why))

        # ---- entries only ----
        if req.side != "buy" and c.long_only:
            why.append("long_only")
        if ctx.killswitch_active:
            why.append("killswitch")
        if ctx.safe_mode:
            why.append("safe_mode")
        if ctx.phase != "entry":
            why.append(f"outside_entry_window:{ctx.phase}")
        if ctx.lockout_day:
            why.append("daily_loss_limit")
        if ctx.lockout_week:
            why.append("weekly_loss_limit")
        if ctx.position_volume + req.volume > c.max_contracts_per_symbol + 1e-9:
            why.append("max_contracts")
        if ctx.entries_today >= c.max_entries_per_day:
            why.append("max_entries_per_day")
        if ctx.data_age_bars > c.max_data_age_bars:
            why.append("stale_data")
        if c.require_stop and req.stop_loss is None:
            why.append("no_stop")
        if req.stop_loss is not None:
            if not _on_grid(req.stop_loss, 0.0, s.tick_size):
                why.append("stop_not_on_tick")
            if req.stop_loss >= ctx.ref_price:
                why.append("stop_wrong_side")
        return RiskDecision(not why, tuple(why))
