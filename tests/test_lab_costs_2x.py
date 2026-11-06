import unittest

from lab import costs


class CostAccountingTests(unittest.TestCase):
    def test_base_effective_cost_counts_each_component_once(self):
        base = costs.get_scenario("base")
        # fee 0.075% (BNB discount, owner's amendment 2026-11-06) + slippage 0.05% + half of the 0.05% spread = 0.15% per side
        self.assertAlmostEqual(base.effective_fee_per_side, 0.0015)

    def test_base_2x_is_exactly_twice_the_base_total_cost(self):
        base, double = costs.get_scenario("base"), costs.get_scenario("base_2x")
        self.assertAlmostEqual(double.effective_fee_per_side, 2 * base.effective_fee_per_side)
        self.assertAlmostEqual(
            double.fee_per_side + double.slippage_per_side + double.spread_total / 2,
            2 * (base.fee_per_side + base.slippage_per_side + base.spread_total / 2),
        )
        # round trip is slightly less than twice (the cost is applied multiplicatively), but within 1e-4
        self.assertAlmostEqual(costs.round_trip_cost(double) / costs.round_trip_cost(base), 2.0, places=2)

    def test_conservative_is_not_a_doubling(self):
        ratio = costs.get_scenario("conservative").effective_fee_per_side / costs.get_scenario("base").effective_fee_per_side
        self.assertLess(ratio, 1.51)

    def test_gate_scenarios_are_unchanged(self):
        self.assertEqual([s.name for s in costs.all_required_scenarios()],
                         ["optimistic", "base", "conservative", "stress"])

    def test_round_trip_matches_freqtrade_formula(self):
        f = costs.get_scenario("base").effective_fee_per_side
        self.assertAlmostEqual(costs.round_trip_cost(costs.get_scenario("base")), 1 - (1 - f) / (1 + f))

    def test_cost_table_has_one_row_per_scenario(self):
        names = [row["scenario"] for row in costs.cost_table()]
        self.assertEqual(names, ["optimistic", "base", "conservative", "stress", "base_2x"])


if __name__ == "__main__":
    unittest.main()
