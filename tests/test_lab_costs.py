import unittest

from lab import costs


class CostScenarioTests(unittest.TestCase):
    def test_four_required_scenarios_exist(self) -> None:
        self.assertEqual(
            set(costs.REQUIRED_SCENARIO_NAMES),
            {"optimistic", "base", "conservative", "stress"},
        )
        for name in costs.REQUIRED_SCENARIO_NAMES:
            self.assertIn(name, costs.SCENARIOS)

    def test_optimistic_has_no_slippage_or_spread(self) -> None:
        scenario = costs.get_scenario("optimistic")
        self.assertEqual(scenario.slippage_per_side, 0.0)
        self.assertEqual(scenario.spread_total, 0.0)
        self.assertAlmostEqual(scenario.effective_fee_per_side, 0.0010)

    def test_scenarios_are_monotonically_more_expensive(self) -> None:
        ordered = [costs.get_scenario(name) for name in costs.REQUIRED_SCENARIO_NAMES]
        effective_fees = [s.effective_fee_per_side for s in ordered]
        self.assertEqual(effective_fees, sorted(effective_fees))
        # Strictly increasing: no two scenarios collapse to the same cost.
        self.assertEqual(len(effective_fees), len(set(effective_fees)))

    def test_effective_fee_folds_in_half_the_spread(self) -> None:
        scenario = costs.get_scenario("base")
        expected = scenario.fee_per_side + scenario.slippage_per_side + scenario.spread_total / 2
        self.assertAlmostEqual(scenario.effective_fee_per_side, expected)

    def test_as_dict_reports_components_separately(self) -> None:
        scenario = costs.get_scenario("conservative")
        payload = scenario.as_dict()
        self.assertEqual(
            set(payload),
            {"name", "fee_per_side", "slippage_per_side", "spread_total", "effective_fee_per_side"},
        )
        self.assertEqual(payload["name"], "conservative")

    def test_unknown_scenario_raises(self) -> None:
        with self.assertRaises(ValueError):
            costs.get_scenario("optimistic-plus")

    def test_all_required_scenarios_returns_four(self) -> None:
        scenarios = costs.all_required_scenarios()
        self.assertEqual(len(scenarios), 4)
        self.assertEqual([s.name for s in scenarios], list(costs.REQUIRED_SCENARIO_NAMES))


if __name__ == "__main__":
    unittest.main()
