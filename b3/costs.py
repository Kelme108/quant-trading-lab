"""Cost scenarios for WIN and WDO day trades, in BRL per contract and ticks of slippage.

STATUS: HYPOTHESIS. These values are estimates written down before any B3 account exists:
- WIN exchange fees: about BRL 0.50 per contract round trip in the first volume tier (Genial,
  "Custo real do day trade"), i.e. 0.25 per side; doubled in the conservative and stress cases.
- WDO exchange fees: NOT confirmed (the B3 fee tables could not be read automatically); 1.00 per
  side is a placeholder.
- Brokerage: zero on mini contracts at most brokers; the broker's own table decides.
- Slippage: 0 / 1 / 2 / 4 ticks per side. A market order on WIN usually fills at the touch, so 1
  tick per side is already the half-spread plus a little.
They are replaced by values MEASURED on the demo account's deal history (plan, F3.4). Fees already
include PIS/COFINS and ISS (B3 fee rules page). Income tax (20% of the monthly net day-trade profit)
is not a cost here; b3/metrics.py reports it separately.
"""

from __future__ import annotations

from dataclasses import dataclass

from b3.instruments import INSTRUMENTS, Instrument

STATUS = "hypothesis (2026-11-12); replace with the demo account's measured fees and slippage (F3.4)"
REQUIRED_SCENARIOS = ("optimistic", "base", "conservative", "stress")


@dataclass(frozen=True)
class B3Cost:
    name: str
    fees_per_side_brl: float          # B3 emolumentos + registration, per contract
    brokerage_per_side_brl: float     # broker commission, per contract
    slippage_ticks_per_side: float
    # Share of the traded notional paid per side (0.0001 = 0.01%). Zero for WIN and WDO, whose costs are fixed BRL per
    # contract; used by the proxy markets (b3/markets.py), whose costs are quoted as a share of the price.
    notional_frac_per_side: float = 0.0
    # Extra adverse move on a STOP fill, as a share of the fill price (0.00005 = 0.005%). A stop is a market order
    # sent when the price touches it; in the ticks the price jumps past it (research/proxies/tick_fidelity.json:
    # p99 jump 0.009-0.013% on the index CFDs), while the bar replay fills exactly at the stop. Owner decision
    # 2026-11-14 (review 2026-11-14-veredito-1m-5m, option a). Zero for WIN/WDO, whose stops already pay
    # `slippage_ticks_per_side`.
    stop_slippage_frac: float = 0.0
    # Extra ticks paid on a STOP fill on top of `slippage_ticks_per_side` (WIN/WDO research lane, b3/markets.py
    # B3Market: 0 / 1 / 2 / 4 by scenario; plan docs/plano-b3-reuso.md F1, owner 2026-11-16).
    stop_extra_ticks: float = 0.0

    def stop_fill(self, touched: float, side: str, tick_size: float) -> float:
        """Price of a stop fill: the touched price (stop, or the open when the bar gapped through it) moved against
        the position by the slippage ticks (plus `stop_extra_ticks`) and by `stop_slippage_frac`. `side` is the
        position's side."""
        extra = ((self.slippage_ticks_per_side + self.stop_extra_ticks) * tick_size
                 + self.stop_slippage_frac * touched)
        return touched - extra if side == "long" else touched + extra

    def cash_cost(self, inst: Instrument, price: float, contracts: float = 1.0) -> float:
        """Cash paid on one side of a fill: fixed fees per contract plus the share of the notional."""
        return contracts * (self.cash_per_side_brl + self.notional_frac_per_side * price * inst.point_value_brl)

    @property
    def cash_per_side_brl(self) -> float:
        """What live/brokers/paper.py calls cost_per_contract_per_side."""
        return self.fees_per_side_brl + self.brokerage_per_side_brl

    def round_trip_brl(self, inst: Instrument, contracts: float = 1.0) -> float:
        return 2 * contracts * (self.cash_per_side_brl + self.slippage_ticks_per_side * inst.tick_value_brl)

    def round_trip_points(self, inst: Instrument) -> float:
        return self.round_trip_brl(inst) / inst.point_value_brl


def _scenarios(fee: float, fee_hi: float) -> dict[str, B3Cost]:
    return {
        "optimistic": B3Cost("optimistic", fee, 0.0, 0.0),
        "base": B3Cost("base", fee, 0.0, 1.0),
        "conservative": B3Cost("conservative", fee_hi, 0.0, 2.0),
        "stress": B3Cost("stress", fee_hi, 0.0, 4.0),
    }


COSTS: dict[str, dict[str, B3Cost]] = {
    "WIN": _scenarios(0.25, 0.50),
    "WDO": _scenarios(1.00, 1.50),
}


def get_cost(root: str, scenario: str) -> B3Cost:
    try:
        return COSTS[root.upper()][scenario]
    except KeyError as exc:
        raise ValueError(f"no cost scenario {scenario!r} for {root!r}; expected {REQUIRED_SCENARIOS}") from exc


def cost_table() -> list[dict]:
    """Round trip of every scenario, in BRL, points and percent of a reference contract value."""
    reference_price = {"WIN": 172_000.0, "WDO": 5_600.0}   # mid-November 2026, for the % column only
    rows = []
    for root, scenarios in COSTS.items():
        inst = INSTRUMENTS[root]
        notional = reference_price[root] * inst.point_value_brl
        for name in REQUIRED_SCENARIOS:
            c = scenarios[name]
            rt = c.round_trip_brl(inst)
            rows.append({"root": root, "scenario": name, "round_trip_brl": rt,
                         "round_trip_points": c.round_trip_points(inst),
                         "round_trip_pct_of_notional": 100 * rt / notional})
    return rows
