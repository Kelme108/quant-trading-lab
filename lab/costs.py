"""Cost scenarios from research/validation-protocol-v2.md.

Freqtrade's backtester does not model slippage or spread; it only accepts a
single `--fee` ratio, applied on both entry and exit. So "effective fee per
side" fed to Freqtrade is fee + slippage + spread/2, but the three
components are kept separate everywhere else (manifest, registry) so a
reader can see what was assumed instead of a single opaque number.

These are sensitivity scenarios, not measured Binance costs. Do not present
them as historical fact.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostScenario:
    name: str
    fee_per_side: float
    slippage_per_side: float
    spread_total: float

    @property
    def effective_fee_per_side(self) -> float:
        """Fee passed to Freqtrade's --fee, folding in slippage and half the spread.

        Freqtrade applies --fee on both entry and exit, so the per-side cost
        must already include this side's share of the spread (half of the
        round-trip spread).
        """
        return self.fee_per_side + self.slippage_per_side + (self.spread_total / 2)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "fee_per_side": self.fee_per_side,
            "slippage_per_side": self.slippage_per_side,
            "spread_total": self.spread_total,
            "effective_fee_per_side": self.effective_fee_per_side,
        }


# Values transcribed from research/validation-protocol-v2.md, "Cost scenarios", with the owner's amendment of
# 2026-11-06: fee 0.075% per side (Binance spot fee with the BNB discount) instead of 0.10%; slippage and spread
# unchanged. Hypotheses decided before that date were judged with the 0.10% fee.
# Conservative and stress give ranges in the protocol; the lower bound of each
# range is used here as the single fixed value for a reproducible command. The
# upper bound is noted so a reader can see the range was not silently dropped.
SCENARIOS: dict[str, CostScenario] = {
    "optimistic": CostScenario(
        name="optimistic",
        fee_per_side=0.00075,
        slippage_per_side=0.0000,
        spread_total=0.0000,
    ),
    "base": CostScenario(
        name="base",
        fee_per_side=0.00075,
        slippage_per_side=0.0005,
        spread_total=0.0005,
    ),
    "conservative": CostScenario(
        # protocol range: slippage 10-20 bps/side, spread 10 bps; lower bound used.
        name="conservative",
        fee_per_side=0.00075,
        slippage_per_side=0.0010,
        spread_total=0.0010,
    ),
    "stress": CostScenario(
        # protocol range: slippage 25-50 bps/side, spread 25 bps; lower bound used.
        name="stress",
        fee_per_side=0.00075,
        slippage_per_side=0.0025,
        spread_total=0.0025,
    ),
}

# Not part of the four required gate scenarios. The protocol's "conservative" scenario costs 0.25% per side, only
# 1.5x the base (0.15% per side, fee 0.075% since 2026-11-06), so it is NOT a doubling. "base_2x" doubles every component
# of the base scenario, so its effective per-side cost (0.30%) and round-trip cost are exactly twice the base's.
SCENARIOS["base_2x"] = CostScenario(
    name="base_2x",
    fee_per_side=0.0015,
    slippage_per_side=0.0010,
    spread_total=0.0010,
)

REQUIRED_SCENARIO_NAMES = ("optimistic", "base", "conservative", "stress")


def get_scenario(name: str) -> CostScenario:
    try:
        return SCENARIOS[name]
    except KeyError as exc:
        raise ValueError(
            f"unknown cost scenario '{name}'; expected one of {REQUIRED_SCENARIO_NAMES}"
        ) from exc


def all_required_scenarios(lane: str = "spot") -> list[CostScenario]:
    return [lane_scenario(name, lane) for name in REQUIRED_SCENARIO_NAMES]


def lane_scenario(name: str, lane: str = "spot") -> CostScenario:
    """The scenario for a market lane (lab/lanes.py): spot is SCENARIOS as it is; futures keeps the same slippage and
    spread and only swaps the fee for the futures fee (docs/faixa-futuros.md, section 2)."""
    scenario = get_scenario(name)
    if lane == "spot" or name == "base_2x":
        return scenario
    from lab import lanes  # local import: lanes has no dependency on costs, and costs stays importable alone

    return CostScenario(name=scenario.name, fee_per_side=lanes.get(lane).fee_per_side,
                        slippage_per_side=scenario.slippage_per_side, spread_total=scenario.spread_total)


def round_trip_cost(scenario: CostScenario) -> float:
    """Fraction of the stake lost to costs by a trade with zero price change: 1 - (1-f)/(1+f), f per side.

    This is how Freqtrade applies --fee (entry cost = stake*(1+f), exit proceeds = value*(1-f)); verified against
    exported trades to 1e-10 (docs/harness-fase0.md)."""
    f = scenario.effective_fee_per_side
    return 1.0 - (1.0 - f) / (1.0 + f)


def cost_table() -> list[dict]:
    """Per-side and round-trip cost of every scenario, with its multiple of the base scenario."""
    base = SCENARIOS["base"]
    rows = []
    for name in (*REQUIRED_SCENARIO_NAMES, "base_2x"):
        scenario = SCENARIOS[name]
        rows.append({
            "scenario": name,
            "fee": scenario.fee_per_side,
            "slippage_per_side": scenario.slippage_per_side,
            "spread_total": scenario.spread_total,
            "effective_per_side": scenario.effective_fee_per_side,
            "round_trip": round_trip_cost(scenario),
            "x_base": scenario.effective_fee_per_side / base.effective_fee_per_side,
        })
    return rows
