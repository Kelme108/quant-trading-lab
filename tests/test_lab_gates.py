import unittest

from lab import gates


def make_metrics(**overrides) -> dict:
    """A baseline metrics dict that passes every gate, for tests to perturb."""
    metrics = {
        "lookahead_has_bias": False,
        "recursive_is_stable": True,
        "benchmark_cash_return_pct": 0.0,
        "benchmark_buy_and_hold_return_pct": 12.0,
    }
    for scenario in ("optimistic", "base", "conservative", "stress"):
        metrics[f"trades__{scenario}"] = 40
        metrics[f"net_profit_quote__{scenario}"] = 10.0
        metrics[f"max_drawdown_pct__{scenario}"] = 5.0
        metrics[f"max_relative_drawdown_pct__{scenario}"] = 5.0
    metrics["net_profit_excl_best_trade__base"] = 4.0
    metrics.update(overrides)
    return metrics


class GatesDecisionTests(unittest.TestCase):
    def test_passing_metrics_yield_candidate(self) -> None:
        decision, reasons = gates.decide(make_metrics())
        self.assertEqual(decision, gates.DECISION_CANDIDATE)
        self.assertTrue(reasons)

    def test_lookahead_bias_detected_rejects(self) -> None:
        decision, reasons = gates.decide(make_metrics(lookahead_has_bias=True))
        self.assertEqual(decision, gates.DECISION_REJECTED)
        self.assertTrue(any("lookahead" in r and "FAIL" in r for r in reasons))

    def test_recursive_instability_rejects(self) -> None:
        decision, _ = gates.decide(make_metrics(recursive_is_stable=False))
        self.assertEqual(decision, gates.DECISION_REJECTED)

    def test_zero_trades_is_inconclusive_never_candidate(self) -> None:
        metrics = make_metrics()
        for scenario in ("optimistic", "base", "conservative", "stress"):
            metrics[f"trades__{scenario}"] = 0
        decision, _ = gates.decide(metrics)
        self.assertEqual(decision, gates.DECISION_INCONCLUSIVE)

    def test_29_trades_is_inconclusive_one_below_threshold(self) -> None:
        metrics = make_metrics()
        metrics["trades__base"] = 29
        decision, reasons = gates.decide(metrics)
        self.assertEqual(decision, gates.DECISION_INCONCLUSIVE)
        self.assertTrue(any("29" in r for r in reasons))

    def test_30_trades_clears_the_minimum(self) -> None:
        metrics = make_metrics()
        for scenario in ("optimistic", "base", "conservative", "stress"):
            metrics[f"trades__{scenario}"] = 30
        decision, _ = gates.decide(metrics)
        self.assertEqual(decision, gates.DECISION_CANDIDATE)

    def test_rejection_takes_priority_over_inconclusive(self) -> None:
        """If both a hard failure (lookahead bias) and a soft one (low trade
        count) are present, the result must be rejected, not inconclusive."""
        metrics = make_metrics(lookahead_has_bias=True)
        metrics["trades__base"] = 5
        decision, _ = gates.decide(metrics)
        self.assertEqual(decision, gates.DECISION_REJECTED)

    def test_negative_net_profit_in_base_rejects(self) -> None:
        decision, reasons = gates.decide(make_metrics(**{"net_profit_quote__base": -1.0}))
        self.assertEqual(decision, gates.DECISION_REJECTED)
        self.assertTrue(any("net_profit[base]" in r and "FAIL" in r for r in reasons))

    def test_negative_net_profit_in_optimistic_does_not_reject_by_itself(self) -> None:
        """Only base and conservative are required positive per gates.json;
        optimistic and stress are not gating on net profit sign."""
        decision, _ = gates.decide(make_metrics(**{"net_profit_quote__optimistic": -5.0}))
        self.assertEqual(decision, gates.DECISION_CANDIDATE)

    def test_profit_concentrated_in_one_trade_rejects(self) -> None:
        """Net profit is positive only because of a single trade; once that
        trade is excluded the strategy is net negative. Must reject, even
        though trades__base and net_profit_quote__base look fine alone."""
        metrics = make_metrics(**{"net_profit_excl_best_trade__base": -3.0})
        decision, reasons = gates.decide(metrics)
        self.assertEqual(decision, gates.DECISION_REJECTED)
        self.assertTrue(
            any("profit_excluding_best_trade" in r and "FAIL" in r for r in reasons)
        )

    def test_drawdown_over_ceiling_rejects(self) -> None:
        decision, reasons = gates.decide(make_metrics(**{"max_relative_drawdown_pct__base": 30.0}))
        self.assertEqual(decision, gates.DECISION_REJECTED)
        self.assertTrue(any("max_drawdown[base]" in r and "FAIL" in r for r in reasons))

    def test_drawdown_exactly_at_ceiling_passes(self) -> None:
        decision, _ = gates.decide(make_metrics(**{"max_relative_drawdown_pct__base": 25.0}))
        self.assertEqual(decision, gates.DECISION_CANDIDATE)

    def test_missing_benchmark_rejects(self) -> None:
        metrics = make_metrics()
        del metrics["benchmark_buy_and_hold_return_pct"]
        decision, reasons = gates.decide(metrics)
        self.assertEqual(decision, gates.DECISION_REJECTED)
        self.assertTrue(any("benchmark_comparison" in r and "FAIL" in r for r in reasons))

    def test_underperforming_benchmark_does_not_reject(self) -> None:
        """Reporting against buy-and-hold is required; beating it is not."""
        decision, _ = gates.decide(make_metrics(benchmark_buy_and_hold_return_pct=500.0))
        self.assertEqual(decision, gates.DECISION_CANDIDATE)

    def test_missing_metric_entirely_rejects_rather_than_crashing(self) -> None:
        decision, reasons = gates.decide({})
        self.assertEqual(decision, gates.DECISION_REJECTED)
        self.assertTrue(reasons)

    def test_no_approved_for_live_value_exists(self) -> None:
        gates_config = gates.load_gates()
        self.assertNotIn("approved", " ".join(gates_config["decision_values"]["allowed"]).lower())
        self.assertEqual(
            set(gates_config["decision_values"]["allowed"]),
            {"rejected", "inconclusive", "candidate_for_portfolio"},
        )

class MultipleTestingPenaltyTests(unittest.TestCase):
    def test_required_profit_grows_linearly_with_prior_variants(self) -> None:
        gates_config = gates.load_gates()
        base = gates_config["net_profit"]["base_threshold_quote"]
        step = gates_config["net_profit"]["multiple_testing_penalty"]["per_variant_increase"]
        self.assertAlmostEqual(gates.required_net_profit(gates_config, 0), base)
        self.assertAlmostEqual(gates.required_net_profit(gates_config, 5), base * (1 + step * 5))
        self.assertGreater(
            gates.required_net_profit(gates_config, 6),
            gates.required_net_profit(gates_config, 5),
        )

    def test_same_profit_passes_with_no_prior_variants_but_fails_after_many(self) -> None:
        gates_config = gates.load_gates()
        bar_with_none = gates.required_net_profit(gates_config, 0)
        bar_with_many = gates.required_net_profit(gates_config, 10)
        between = (bar_with_none + bar_with_many) / 2
        metrics = make_metrics(
            **{"net_profit_quote__base": between, "net_profit_quote__conservative": between}
        )

        decision_fresh, _ = gates.decide(metrics, variants_tested_in_family=0)
        decision_crowded, reasons = gates.decide(metrics, variants_tested_in_family=10)

        self.assertEqual(decision_fresh, gates.DECISION_CANDIDATE)
        self.assertEqual(decision_crowded, gates.DECISION_REJECTED)
        self.assertTrue(any("net_profit[base]" in r and "FAIL" in r for r in reasons))
        self.assertTrue(any("10 prior variant" in r for r in reasons))

    def test_profit_exactly_at_the_bar_does_not_pass(self) -> None:
        """The bar is a strict inequality, like the old `> 0` rule."""
        gates_config = gates.load_gates()
        bar = gates.required_net_profit(gates_config, 0)
        metrics = make_metrics(
            **{"net_profit_quote__base": bar, "net_profit_quote__conservative": bar}
        )
        decision, _ = gates.decide(metrics)
        self.assertEqual(decision, gates.DECISION_REJECTED)

    def test_negative_variant_count_is_an_error(self) -> None:
        with self.assertRaises(ValueError):
            gates.required_net_profit(gates.load_gates(), -1)


class GatesHashTests(unittest.TestCase):
    def test_gates_sha256_is_stable_for_same_file(self) -> None:
        first = gates.gates_sha256()
        second = gates.gates_sha256()
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)


if __name__ == "__main__":
    unittest.main()
