"""Published contract specifications of WIN and WDO, and a cross-check against the server.

The live adapter reads tick size and tick value from the MT5 server (`symbol_info`); these
published values exist only to catch a server or broker that reports something different, and to
run the backtester before any account exists. A mismatch is a stop sign, not something to fix
silently.
"""

from __future__ import annotations

from dataclasses import dataclass

from live.core.models import SymbolSpec


@dataclass(frozen=True)
class Instrument:
    root: str
    name: str
    point_value_brl: float   # BRL per 1.0 price point per contract
    tick_size: float         # minimum price increment, in points
    source: str

    @property
    def tick_value_brl(self) -> float:
        return self.point_value_brl * self.tick_size

    def points_to_brl(self, points: float, contracts: float = 1.0) -> float:
        return points * self.point_value_brl * contracts


INSTRUMENTS: dict[str, Instrument] = {
    "WIN": Instrument(
        root="WIN", name="Futuro Mini de Ibovespa", point_value_brl=0.20, tick_size=5.0,
        source="B3, 'What is mini index (WIN)': one point is worth BRL 0.20 (20% of IND); "
               "tick of 5 points. Confirm with symbol_info on the account (F1.1).",
    ),
    "WDO": Instrument(
        root="WDO", name="Futuro Mini de Dolar Comercial", point_value_brl=10.0, tick_size=0.5,
        source="US$ 10,000 contract quoted in BRL per US$ 1,000: one point is BRL 10, minimum "
               "tick 0.5 point = BRL 5 (Toro, citing the B3 specification). Confirm with symbol_info.",
    ),
}


def instrument_for(symbol: str) -> Instrument:
    """WINZ26, WIN$N, WDOZ26... -> the instrument of its root."""
    root = symbol[:3].upper()
    try:
        return INSTRUMENTS[root]
    except KeyError as exc:
        raise ValueError(f"{symbol}: unknown B3 root {root!r}; expected one of {sorted(INSTRUMENTS)}") from exc


def check_server_spec(spec: SymbolSpec, tolerance: float = 1e-9) -> list[str]:
    """Differences between what the server reports and the published specification (empty = same)."""
    inst = instrument_for(spec.symbol)
    problems = []
    if abs(spec.tick_size - inst.tick_size) > tolerance:
        problems.append(f"{spec.symbol}: server tick_size {spec.tick_size} != published {inst.tick_size}")
    if abs(spec.tick_value - inst.tick_value_brl) > tolerance:
        problems.append(f"{spec.symbol}: server tick_value {spec.tick_value} != published {inst.tick_value_brl}")
    if spec.volume_min != 1.0 or spec.volume_step != 1.0:
        problems.append(f"{spec.symbol}: volume_min/step {spec.volume_min}/{spec.volume_step}, expected whole contracts")
    return problems
